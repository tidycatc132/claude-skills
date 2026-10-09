#!/usr/bin/env python3
"""Shared machinery for the eval runners: sandboxes, headless `claude -p` runs, assertions.

Design rules
  * Evals run in a throwaway directory that contains ONLY the skills under test in
    .claude/skills/. The harness's own CLAUDE.md, hooks and settings are not loaded
    (--setting-sources project + a clean cwd), so results reflect the skill, not the repo.
  * Permissions are deny-by-default (--permission-mode dontAsk) with a short allow-list.
  * Computational assertions decide pass/fail. Rubric (LLM-judge) assertions run in a
    separate, tool-less `claude -p` session so the author never grades itself.
"""
from __future__ import annotations

import csv
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

DEFAULT_ALLOWED = "Skill,Read,Write,Edit,Glob,Grep,Bash(python3 *),Bash(ls *),Bash(cat *),Bash(mkdir *)"


def claude_bin() -> str | None:
    return os.environ.get("HARNESS_CLAUDE_BIN") or shutil.which("claude")


# --------------------------------------------------------------------------- #
# Sandbox
# --------------------------------------------------------------------------- #
def make_sandbox(skill_dirs: list[Path]) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="harness-eval-"))
    dst = tmp / ".claude" / "skills"
    dst.mkdir(parents=True)
    for d in skill_dirs:
        shutil.copytree(d, dst / d.name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return tmp


# --------------------------------------------------------------------------- #
# Running claude
# --------------------------------------------------------------------------- #
@dataclass
class RunResult:
    ok: bool                      # process ran and produced a result event
    text: str = ""                # final assistant text
    tool_uses: list[tuple[str, dict]] = field(default_factory=list)
    error: str = ""
    cost_usd: float | None = None

    def skills_invoked(self, known: list[str]) -> set[str]:
        found = set()
        for name, inp in self.tool_uses:
            if name != "Skill":
                continue
            blob = json.dumps(inp)
            for k in known:
                if re.search(rf"(^|[^a-z0-9-]){re.escape(k)}($|[^a-z0-9-])", blob):
                    found.add(k)
        return found


def run_claude(
    prompt: str,
    cwd: Path,
    *,
    allowed: str = DEFAULT_ALLOWED,
    no_tools: bool = False,
    model: str | None = None,
    budget: float | None = None,
    timeout: int = 240,
) -> RunResult:
    exe = claude_bin()
    if not exe:
        return RunResult(False, error="`claude` CLI not found on PATH (set HARNESS_CLAUDE_BIN).")
    cmd = [
        exe, "-p", prompt,
        "--output-format", "stream-json", "--verbose",
        "--setting-sources", "project",
        "--permission-mode", "dontAsk",
        "--no-session-persistence",
    ]
    if no_tools:
        cmd += ["--tools", ""]
    else:
        cmd += ["--allowedTools", allowed]
    if model:
        cmd += ["--model", model]
    if budget:
        cmd += ["--max-budget-usd", str(budget)]
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return RunResult(False, error=f"timed out after {timeout}s")
    except OSError as e:
        return RunResult(False, error=str(e))

    res = RunResult(False)
    for line in p.stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") == "assistant":
            for blk in (ev.get("message") or {}).get("content", []) or []:
                if isinstance(blk, dict) and blk.get("type") == "tool_use":
                    res.tool_uses.append((blk.get("name", ""), blk.get("input") or {}))
        elif ev.get("type") == "result":
            res.ok = not ev.get("is_error", False)
            res.text = ev.get("result") or ""
            res.cost_usd = ev.get("total_cost_usd")
            if ev.get("is_error"):
                res.error = (res.text or "claude reported an error")[:300]
    if not res.ok and not res.error:
        res.error = (p.stderr.strip() or "no result event in output (not logged in? try `claude -p hi`)")[:300]
    return res


# --------------------------------------------------------------------------- #
# Assertions
# --------------------------------------------------------------------------- #
@dataclass
class Check:
    ok: bool | None   # None = needs judge
    label: str
    detail: str = ""


def _target_text(a: dict, outdir: Path, stdout: str) -> tuple[str | None, str]:
    t = a.get("target", a.get("path", "stdout"))
    if t == "stdout":
        return stdout, "stdout"
    p = outdir / t
    if not p.exists():
        return None, t
    return C.read_text(p), t


def evaluate(assertions: list[dict], outdir: Path, stdout: str = "") -> list[Check]:
    out: list[Check] = []
    for a in assertions:
        kind = a.get("type", "")
        label = a.get("label") or kind
        try:
            out.append(_evaluate_one(a, kind, label, outdir, stdout))
        except Exception as e:  # malformed assertion should fail loudly, not crash the run
            out.append(Check(False, label, f"assertion could not be evaluated: {e}"))
    return out


def _evaluate_one(a: dict, kind: str, label: str, outdir: Path, stdout: str) -> Check:
    if kind == "file_exists":
        ok = (outdir / a["path"]).exists()
        return Check(ok, label, "" if ok else f"{a['path']} was not created")
    if kind == "file_absent":
        ok = not (outdir / a["path"]).exists()
        return Check(ok, label, "" if ok else f"{a['path']} should not exist")

    if kind in ("contains", "not_contains", "regex", "not_regex", "max_words", "min_words", "max_lines"):
        text, where = _target_text(a, outdir, stdout)
        if text is None:
            return Check(False, label, f"{where} was not created")
        if kind == "contains":
            ok = a["text"] in text
            return Check(ok, label, "" if ok else f"{where} lacks {a['text']!r}")
        if kind == "not_contains":
            ok = a["text"] not in text
            return Check(ok, label, "" if ok else f"{where} contains forbidden {a['text']!r}")
        if kind == "regex":
            ok = re.search(a["pattern"], text, re.M | re.S) is not None
            return Check(ok, label, "" if ok else f"{where} does not match /{a['pattern']}/")
        if kind == "not_regex":
            m = re.search(a["pattern"], text, re.M | re.S)
            return Check(m is None, label, "" if m is None else f"{where} matches forbidden /{a['pattern']}/ at {m.group(0)[:40]!r}")
        words = len(text.split())
        if kind == "max_words":
            return Check(words <= a["n"], label, f"{where} has {words} words (max {a['n']})" if words > a["n"] else "")
        if kind == "min_words":
            return Check(words >= a["n"], label, f"{where} has {words} words (min {a['n']})" if words < a["n"] else "")
        lines = len(text.splitlines())
        return Check(lines <= a["n"], label, f"{where} has {lines} lines (max {a['n']})" if lines > a["n"] else "")

    if kind in ("csv_columns", "csv_min_rows", "csv_enum", "csv_no_empty"):
        p = outdir / a["path"]
        if not p.exists():
            return Check(False, label, f"{a['path']} was not created")
        rows = list(csv.reader(io.StringIO(C.read_text(p))))
        if not rows:
            return Check(False, label, f"{a['path']} is empty")
        header, data = rows[0], rows[1:]
        if kind == "csv_columns":
            ok = header == a["columns"]
            return Check(ok, label, "" if ok else f"header {header} != {a['columns']}")
        if kind == "csv_min_rows":
            ok = len(data) >= a["n"]
            return Check(ok, label, "" if ok else f"{len(data)} data rows (min {a['n']})")
        col = a["column"]
        if col not in header:
            return Check(False, label, f"column {col!r} not in header {header}")
        i = header.index(col)
        if kind == "csv_enum":
            bad = sorted({r[i] for r in data if len(r) > i and r[i] not in a["values"]})
            return Check(not bad, label, "" if not bad else f"{col} has values outside {a['values']}: {bad}")
        empty = [n for n, r in enumerate(data, 2) if len(r) <= i or not r[i].strip()]
        return Check(not empty, label, "" if not empty else f"{col} empty on lines {empty[:5]}")

    if kind in ("json_valid", "json_has_keys"):
        p = outdir / a["path"]
        if not p.exists():
            return Check(False, label, f"{a['path']} was not created")
        try:
            data = json.loads(C.read_text(p))
        except json.JSONDecodeError as e:
            return Check(False, label, f"{a['path']} is not valid JSON: {e}")
        if kind == "json_valid":
            return Check(True, label)
        items = data if isinstance(data, list) else [data]
        missing = [k for k in a["keys"] if not all(isinstance(i, dict) and k in i for i in items)]
        return Check(not missing, label, "" if not missing else f"missing keys: {missing}")

    if kind == "rubric":
        return Check(None, label, json.dumps(a.get("criteria", [])))
    return Check(False, label, f"unknown assertion type {kind!r}")


# --------------------------------------------------------------------------- #
# LLM judge (separate session, no tools)
# --------------------------------------------------------------------------- #
def judge(criteria: list[str], material: str, model: str | None = None) -> tuple[bool, str]:
    tmp = Path(tempfile.mkdtemp(prefix="harness-judge-"))
    try:
        prompt = (
            "You are a strict reviewer. Judge ONLY against the criteria. Reply with one JSON object and nothing else: "
            '{"verdict":"pass"|"fail","reasons":["..."]}. Fail if any criterion is not clearly met.\n\n'
            "CRITERIA:\n" + "\n".join(f"- {c}" for c in criteria) + "\n\nOUTPUT UNDER REVIEW:\n" + material[:30000]
        )
        r = run_claude(prompt, tmp, no_tools=True, model=model, timeout=180)
        if not r.ok:
            return False, f"judge error: {r.error}"
        m = re.search(r"\{.*\}", r.text, re.S)
        if not m:
            return False, "judge returned no JSON"
        try:
            v = json.loads(m.group(0))
        except json.JSONDecodeError:
            return False, "judge returned invalid JSON"
        return v.get("verdict") == "pass", "; ".join(map(str, v.get("reasons", [])))[:300]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
