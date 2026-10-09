#!/usr/bin/env python3
"""Validate skills: structure, frontmatter, references, env-coupling, evals.

Usage:
  validate_skill.py <skill> [<skill> ...]   validate named skills
  validate_skill.py --all                   validate every skill
  validate_skill.py --changed               validate skills with uncommitted changes (git)
  --strict                                  also enforce ship rules (no placeholders,
                                            evals present and big enough)
  --quiet                                   hide warnings

Exit code 1 when any error is found. Messages are written for an LLM to act on.
"""
from __future__ import annotations

import argparse
import json
import os
import py_compile
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FORBIDDEN_NAME_WORDS = ("claude", "anthropic")
ENV_PATHS = re.compile(r"(/mnt/skills|/mnt/user-data|/home/claude|/Users/[A-Za-z0-9_.-]+|/tmp/outputs)")
PLACEHOLDER = re.compile(r"\b(?:TODO|FIXME|TBD|XXX)\b|(?i:lorem ipsum)|<placeholder>|\[your [a-z ]+ here\]")
TRIGGER_CUE = re.compile(r"(use (this skill )?(when|whenever|any time)|trigger|when the user|whenever the user)", re.I)
BOUNDARY_CUE = re.compile(r"(do not use|don't use|not for|instead use|use .{1,40} instead)", re.I)
REF_TOKEN = re.compile(r"(?<![\w/.-])((?:references|scripts|assets)/[A-Za-z0-9_./*-]+)")
MD_LINK = re.compile(r"\]\(([^)\s#]+)(?:#[^)]*)?\)")

MAX_BODY_ERROR = int(os.environ.get("HARNESS_MAX_BODY_LINES", "500"))
MAX_BODY_WARN = int(os.environ.get("HARNESS_WARN_BODY_LINES", "400"))
MIN_EVALS = int(os.environ.get("HARNESS_MIN_TRIGGER", "4"))  # per side (should / should-not)


def strip_trailing_punct(token: str) -> str:
    return token.rstrip(".,;:)`'\"")


def check_references(skill_dir: Path, body: str, r: C.Report) -> None:
    refs: set[str] = set()
    for m in REF_TOKEN.finditer(body):
        refs.add(strip_trailing_punct(m.group(1)))
    for m in MD_LINK.finditer(body):
        target = m.group(1)
        if re.match(r"^[a-z][a-z0-9+.-]*:", target) or target.startswith(("/", "#")):
            continue
        refs.add(strip_trailing_punct(target))
    for ref in sorted(refs):
        if "*" in ref or "<" in ref or "{" in ref:
            continue
        if not (skill_dir / ref).exists():
            r.error(
                f"SKILL.md references '{ref}' but that file does not exist inside the skill folder. "
                "Create it or fix the path (paths are relative to the skill folder)."
            )
    # orphan files in references/ (warn only)
    ref_dir = skill_dir / "references"
    if ref_dir.is_dir():
        for f in sorted(p for p in ref_dir.rglob("*") if p.is_file()):
            rel = f.relative_to(skill_dir).as_posix()
            if rel not in refs and f.name not in body:
                r.warn(f"'{rel}' is never mentioned in SKILL.md, so Claude won't know to load it.")


def check_text_files(skill_dir: Path, r: C.Report, strict: bool) -> None:
    for f in sorted(p for p in skill_dir.rglob("*") if p.is_file()):
        rel = f.relative_to(skill_dir).as_posix()
        if "__pycache__" in f.parts or f.suffix == ".pyc":
            continue
        suffix = f.suffix.lower()
        if suffix not in C.TEXT_SUFFIXES:
            continue
        text = C.read_text(f)
        # hard-coded environment paths
        for i, line in enumerate(text.splitlines(), 1):
            if "harness:allow-path" in line:
                continue
            m = ENV_PATHS.search(line)
            if m:
                r.error(
                    f"{rel}:{i} hard-codes the environment path '{m.group(1)}'. Skills move between "
                    "Claude.ai, Claude Code and plugins; use paths relative to the skill folder or "
                    "the working directory (add 'harness:allow-path' on the line if it is intentional)."
                )
        # syntax checks
        if suffix == ".py":
            try:
                with tempfile.TemporaryDirectory() as td:
                    py_compile.compile(str(f), cfile=os.path.join(td, "x.pyc"), doraise=True)
            except py_compile.PyCompileError as e:
                r.error(f"{rel} has a Python syntax error: {str(e).strip().splitlines()[-1]}")
        elif suffix == ".sh":
            p = subprocess.run(["bash", "-n", str(f)], capture_output=True, text=True)
            if p.returncode != 0:
                r.error(f"{rel} has a shell syntax error: {p.stderr.strip().splitlines()[-1] if p.stderr.strip() else 'bash -n failed'}")
        elif suffix == ".json":
            try:
                json.loads(text)
            except json.JSONDecodeError as e:
                r.error(f"{rel} is not valid JSON: {e}")
        # placeholders in prose (ship rule)
        if suffix == ".md":
            for i, line in enumerate(text.splitlines(), 1):
                if PLACEHOLDER.search(line):
                    msg = f"{rel}:{i} contains placeholder text ('{PLACEHOLDER.search(line).group(0)}'). Replace it with real content before shipping."
                    (r.error if strict else r.warn)(msg)


def check_evals(skill_dir: Path, r: C.Report, strict: bool) -> None:
    name = skill_dir.name
    ev = C.EVALS_DIR / name
    emit = r.error if strict else r.warn
    trig = ev / "trigger.json"
    outs = ev / "outputs.json"
    if not trig.exists():
        emit(
            f"evals/{name}/trigger.json is missing. Add {MIN_EVALS}+ 'should_trigger' and {MIN_EVALS}+ "
            "'should_not_trigger' prompts (include near-neighbour prompts that belong to sibling skills)."
        )
    else:
        try:
            data = C.load_json(trig)
            s, n = data.get("should_trigger", []), data.get("should_not_trigger", [])
            if not (isinstance(s, list) and isinstance(n, list)):
                emit(f"evals/{name}/trigger.json: 'should_trigger' and 'should_not_trigger' must be lists of prompts.")
            elif len(s) < MIN_EVALS or len(n) < MIN_EVALS:
                emit(
                    f"evals/{name}/trigger.json has {len(s)} should_trigger / {len(n)} should_not_trigger prompts; "
                    f"need at least {MIN_EVALS} of each."
                )
            elif len(set(map(str.strip, map(str, s + n)))) != len(s) + len(n):
                emit(f"evals/{name}/trigger.json contains duplicate prompts.")
        except json.JSONDecodeError as e:
            r.error(f"evals/{name}/trigger.json is not valid JSON: {e}")
    if not outs.exists():
        emit(
            f"evals/{name}/outputs.json is missing. Add at least one case with a prompt, fixtures and "
            "assertions (format: README.md, 'Eval formats')."
        )
    else:
        try:
            data = C.load_json(outs)
            cases = data.get("cases", [])
            if not cases:
                emit(f"evals/{name}/outputs.json has no cases.")
            for c in cases:
                if not c.get("id") or not c.get("prompt") or not c.get("assertions"):
                    r.error(f"evals/{name}/outputs.json: every case needs 'id', 'prompt' and a non-empty 'assertions' list.")
                    break
        except json.JSONDecodeError as e:
            r.error(f"evals/{name}/outputs.json is not valid JSON: {e}")


def validate(skill_dir: Path, strict: bool = False) -> C.Report:
    name = skill_dir.name
    r = C.Report(name)
    md = skill_dir / "SKILL.md"
    if not md.exists():
        r.error("SKILL.md is missing. Every skill folder needs a SKILL.md with YAML frontmatter.")
        return r
    text = C.read_text(md)
    fm, body = C.parse_frontmatter(text)
    if fm is None:
        r.error("SKILL.md has no YAML frontmatter. Start the file with --- / name: / description: / ---.")
        return r

    # --- name
    fname = fm.get("name", "")
    if not fname:
        r.error("frontmatter is missing 'name'.")
    else:
        if not NAME_RE.match(fname):
            r.error(f"name '{fname}' must be kebab-case (lowercase letters, digits, single hyphens).")
        if len(fname) > 64:
            r.error(f"name is {len(fname)} characters; the limit is 64.")
        if fname != name:
            r.error(f"frontmatter name '{fname}' must match the folder name '{name}'.")
        for w in FORBIDDEN_NAME_WORDS:
            if w in fname:
                r.error(f"name must not contain '{w}'.")

    # --- description
    desc = fm.get("description", "")
    if not desc.strip():
        r.error("frontmatter is missing 'description'. It is the only text Claude sees when deciding to trigger the skill.")
    else:
        if len(desc) > 1024:
            r.error(f"description is {len(desc)} characters; the limit is 1024. Move detail into the body or references/.")
        if "<" in desc or ">" in desc:
            r.error("description must not contain angle brackets (< or >).")
        if len(desc) < 60:
            r.warn("description is very short; say what the skill does AND when to use it.")
        if not TRIGGER_CUE.search(desc):
            r.warn("description has no trigger cue ('Use when...', 'Trigger on...'); Claude may under-trigger it.")
        if not BOUNDARY_CUE.search(desc):
            r.warn("description names no boundary ('Do NOT use for ... (use <sibling>)'); overlapping skills fight over triggers.")

    # --- body
    lines = body.strip().splitlines()
    if not lines:
        r.error("SKILL.md body is empty.")
    else:
        if len(lines) > MAX_BODY_ERROR:
            r.error(
                f"SKILL.md body is {len(lines)} lines (limit {MAX_BODY_ERROR}). Keep SKILL.md lean and move "
                "detail into references/ files that SKILL.md tells Claude when to load."
            )
        elif len(lines) > MAX_BODY_WARN:
            r.warn(f"SKILL.md body is {len(lines)} lines; consider moving detail into references/.")
        if not any(l.startswith("#") for l in lines):
            r.warn("SKILL.md body has no headings; structure helps Claude scan it.")

    check_references(skill_dir, body, r)
    check_text_files(skill_dir, r, strict)
    check_evals(skill_dir, r, strict)
    return r


def validate_many(skill_dirs: list[Path], strict: bool = False) -> list[C.Report]:
    reports = [validate(d, strict) for d in skill_dirs]
    # suite-level: duplicate frontmatter names
    seen: dict[str, str] = {}
    for d in skill_dirs:
        n = C.load_skill(d)["name"]
        if n in seen and seen[n] != d.name:
            for rep in reports:
                if rep.subject == d.name:
                    rep.error(f"frontmatter name '{n}' is also used by skill folder '{seen[n]}'. Names must be unique.")
        seen[n] = d.name
    return reports


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("skills", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--changed", action="store_true")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    if args.all:
        dirs = C.list_skill_dirs()
    elif args.changed:
        dirs = C.changed_skill_dirs()
        if dirs is None:
            dirs = C.list_skill_dirs()
    else:
        dirs = []
        for s in args.skills:
            d = C.resolve_skill(s)
            if d is None or not d.is_dir():
                C.die(f"no such skill: {s}")
            dirs.append(d)
    if not dirs:
        print("no skills to validate")
        return 0
    reports = validate_many(dirs, args.strict)
    C.print_reports(reports, show_warnings=not args.quiet)
    return 0 if all(r.ok for r in reports) else 1


if __name__ == "__main__":
    sys.exit(main())
