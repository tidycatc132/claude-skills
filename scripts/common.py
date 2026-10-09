#!/usr/bin/env python3
"""Shared helpers for the skills harness. Standard library only."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
ROOT = Path(
    os.environ.get("HARNESS_ROOT")
    or os.environ.get("CLAUDE_PROJECT_DIR")
    or SCRIPTS_DIR.parent
).resolve()

SKILLS_DIR = ROOT / "skills"
EVALS_DIR = ROOT / "evals"
CONTRACTS_DIR = ROOT / "contracts"
BACKLOG = ROOT / "skills_backlog.json"
RESULTS_DIR = ROOT / ".harness" / "results"

TEXT_SUFFIXES = {".md", ".txt", ".py", ".sh", ".json", ".csv", ".yaml", ".yml", ".html", ".js", ".ts", ".css"}


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #
@dataclass
class Report:
    """Collects errors and warnings for one subject (a skill, a contract...)."""

    subject: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    @property
    def ok(self) -> bool:
        return not self.errors

    def lines(self, show_warnings: bool = True) -> list[str]:
        out = [f"  ERROR  {self.subject}: {m}" for m in self.errors]
        if show_warnings:
            out += [f"  warn   {self.subject}: {m}" for m in self.warnings]
        return out


def print_reports(reports: list[Report], show_warnings: bool = True) -> None:
    for r in reports:
        for line in r.lines(show_warnings):
            print(line)
    n_err = sum(len(r.errors) for r in reports)
    n_warn = sum(len(r.warnings) for r in reports)
    print(f"{len(reports)} checked, {n_err} error(s), {n_warn} warning(s)")


# --------------------------------------------------------------------------- #
# Skills
# --------------------------------------------------------------------------- #
def unquote(val: str) -> str:
    val = val.strip()
    if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
        inner = val[1:-1]
        if val[0] == '"':
            inner = inner.replace('\\"', '"').replace("\\\\", "\\")
        return inner
    return val


def parse_frontmatter(text: str) -> tuple[dict | None, str]:
    """Parse the leading ---/--- block. Handles plain, quoted and folded scalars."""
    m = re.match(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", text, re.S)
    if not m:
        return None, text
    body = text[m.end():]
    data: dict[str, str] = {}
    key: str | None = None
    for line in m.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        mm = re.match(r"^([A-Za-z0-9_-]+):[ \t]*(.*)$", line)
        if mm and not line.startswith((" ", "\t")):
            key, val = mm.group(1), mm.group(2).strip()
            data[key] = "" if val in (">", ">-", ">+", "|", "|-", "|+") else unquote(val)
        elif key is not None:
            data[key] = (data[key] + " " + line.strip()).strip()
    return data, body


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def list_skill_dirs() -> list[Path]:
    if not SKILLS_DIR.is_dir():
        return []
    return sorted(
        p for p in SKILLS_DIR.iterdir()
        if p.is_dir() and not p.name.startswith((".", "_"))
    )


def load_skill(skill_dir: Path) -> dict:
    """Return {'name', 'description', 'body', 'dir', 'frontmatter'} (best effort)."""
    md = skill_dir / "SKILL.md"
    fm, body = (None, "")
    if md.exists():
        fm, body = parse_frontmatter(read_text(md))
    fm = fm or {}
    return {
        "dir": skill_dir,
        "dirname": skill_dir.name,
        "name": fm.get("name", skill_dir.name),
        "description": fm.get("description", ""),
        "body": body,
        "frontmatter": fm,
    }


def resolve_skill(arg: str) -> Path | None:
    """Accept a skill name, 'skills/<name>', or any path inside a skill dir."""
    p = Path(arg)
    if not p.is_absolute():
        cand = SKILLS_DIR / arg
        if cand.is_dir():
            return cand
        p = (Path.cwd() / arg)
    p = p.resolve()
    try:
        rel = p.relative_to(SKILLS_DIR)
    except ValueError:
        return None
    return SKILLS_DIR / rel.parts[0] if rel.parts else None


def skill_for_path(path: str | Path) -> Path | None:
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    try:
        rel = p.resolve().relative_to(SKILLS_DIR)
    except ValueError:
        return None
    if not rel.parts or rel.parts[0].startswith((".", "_")):
        return None
    return SKILLS_DIR / rel.parts[0]


# --------------------------------------------------------------------------- #
# Git helpers (all optional: the harness degrades gracefully without git)
# --------------------------------------------------------------------------- #
def git(*args: str) -> tuple[int, str]:
    try:
        p = subprocess.run(
            ["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=30
        )
        return p.returncode, p.stdout
    except (OSError, subprocess.TimeoutExpired):
        return 127, ""


def is_git_repo() -> bool:
    rc, out = git("rev-parse", "--is-inside-work-tree")
    return rc == 0 and out.strip() == "true"


def has_commits() -> bool:
    return git("rev-parse", "--verify", "HEAD")[0] == 0


def is_tracked(relpath: str) -> bool:
    if not is_git_repo():
        return False
    return git("ls-files", "--error-unmatch", "--", relpath)[0] == 0


def changed_paths() -> list[str] | None:
    """Paths changed vs HEAD (staged, unstaged, untracked). None when not a git repo."""
    if not is_git_repo():
        return None
    rc, out = git("status", "--porcelain", "-uall")
    if rc != 0:
        return None
    paths = []
    for line in out.splitlines():
        if len(line) < 4:
            continue
        p = line[3:]
        if " -> " in p:
            p = p.split(" -> ", 1)[1]
        paths.append(p.strip().strip('"'))
    return paths


def changed_skill_dirs() -> list[Path] | None:
    paths = changed_paths()
    if paths is None:
        return None
    names = []
    for p in paths:
        parts = Path(p).parts
        if len(parts) >= 2 and parts[0] == "skills" and not parts[1].startswith((".", "_")):
            names.append(parts[1])
        elif len(parts) >= 2 and parts[0] == "evals" and not parts[1].startswith((".", "_")):
            names.append(parts[1])
    return [SKILLS_DIR / n for n in sorted(set(names)) if (SKILLS_DIR / n).is_dir()]


# --------------------------------------------------------------------------- #
# JSON helpers
# --------------------------------------------------------------------------- #
def load_json(path: Path):
    return json.loads(read_text(path))


def die(msg: str, code: int = 1) -> None:
    print(msg, file=sys.stderr)
    sys.exit(code)
