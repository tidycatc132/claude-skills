#!/usr/bin/env python3
"""PreToolUse hook (Edit|Write|Bash): keep the agent from weakening its own sensors.

Principle: "It is unacceptable to remove or edit tests." The agent may ADD evals, fixtures and
contracts, and may edit them while they are still uncommitted (new work). Once committed they are
frozen: changing them needs a human decision. The harness itself (scripts, hooks, settings, agents,
commands) is frozen outright, and skills_backlog.json may only have `passes`/`notes` changed.

Unlock (human only, deliberate): create an empty file named `.harness-unlock` in the repo root, or
export HARNESS_UNLOCK=1. Remove it when the change is done.

Exit 2 = block; stderr goes back to Claude as the reason. Hooks are guardrails, not a security
boundary: the Stop gate re-checks the git diff, which also catches bypasses through Bash.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import common as C  # noqa: E402

FROZEN = ("scripts/", ".claude/hooks/", ".claude/agents/", ".claude/commands/", "dist/", ".harness/")
FROZEN_FILES = (".claude/settings.json", "init.sh", "Makefile")
FROZEN_WHEN_TRACKED = ("evals/", "fixtures/", "contracts/")


def unlocked() -> bool:
    return os.environ.get("HARNESS_UNLOCK") == "1" or (C.ROOT / ".harness-unlock").exists()


def rel(path: str) -> str | None:
    p = Path(path)
    p = p if p.is_absolute() else C.ROOT / p
    try:
        return p.resolve().relative_to(C.ROOT).as_posix()
    except ValueError:
        return None


def classify(relpath: str) -> str | None:
    """Return a reason string if this path is protected right now, else None."""
    if relpath in FROZEN_FILES or relpath.startswith(FROZEN):
        return "it is part of the harness itself (sensors and guardrails)"
    if relpath.startswith(FROZEN_WHEN_TRACKED) and C.is_tracked(relpath):
        return "it is a committed eval, fixture or contract (the definition of 'correct')"
    return None


def block(msg: str) -> None:
    print(msg, file=sys.stderr)
    sys.exit(2)


def explain(relpath: str, why: str) -> str:
    return (
        f"Blocked: {relpath} is protected because {why}. Do not edit it to make a check pass. "
        "Fix the skill instead. If this file genuinely has to change, tell the user what and why, "
        "and ask them to create `.harness-unlock` (they remove it afterwards)."
    )


def check_backlog_edit(data: dict) -> None:
    ti = data.get("tool_input", {})
    path = C.BACKLOG
    try:
        old_text = C.read_text(path) if path.exists() else "{}"
        if data.get("tool_name") == "Write":
            new_text = ti.get("content", "")
        else:
            old_s, new_s = ti.get("old_string", ""), ti.get("new_string", "")
            new_text = old_text.replace(old_s, new_s) if ti.get("replace_all") else old_text.replace(old_s, new_s, 1)
        old = json.loads(old_text).get("skills", [])
        new = json.loads(new_text).get("skills", [])
    except (json.JSONDecodeError, OSError):
        block("Blocked: that edit would leave skills_backlog.json as invalid JSON (or it could not be parsed). Make a smaller edit.")
        return
    import check_backlog as B  # noqa: E402

    problems = B.immutable_diff(old, new)
    if problems:
        block(
            "Blocked: skills_backlog.json is human-owned except for `passes` and `notes`.\n  - "
            + "\n  - ".join(problems)
            + "\nSet `passes` to true only after every gate passes for that skill; ask the user to change anything else."
        )


BASH_WRITE = (
    r"(?:>>?|\btee(?:\s+-a)?)\s*['\"]?(?:\./)?(?P<p1>{paths})",
    r"\b(?:rm|mv|cp|install|truncate|chmod|sed\s+-i\S*|perl\s+-pi\S*)\b[^;&|\n]*?\s['\"]?(?:\./)?(?P<p2>{paths})",
    r"\bgit\s+(?:checkout|restore|reset|clean|stash)\b[^;&|\n]*?\s['\"]?(?:\./)?(?P<p3>{paths})",
)


def check_bash(cmd: str) -> None:
    prefixes = list(FROZEN) + list(FROZEN_WHEN_TRACKED) + list(FROZEN_FILES)
    paths = "|".join(re.escape(p) + (r"[^\s'\";|&)]*" if p.endswith("/") else "") for p in prefixes)
    for pat in BASH_WRITE:
        for m in re.finditer(pat.format(paths=paths), cmd):
            token = next(v for k, v in m.groupdict().items() if v)
            why = classify(token)
            if why:
                block(explain(token, why) + " (detected a shell command that writes to it)")


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    if unlocked():
        return 0
    tool = data.get("tool_name", "")
    ti = data.get("tool_input", {}) or {}
    if tool in ("Edit", "Write", "MultiEdit"):
        fp = ti.get("file_path", "")
        r = rel(fp) if fp else None
        if r is None:
            return 0
        if r == "skills_backlog.json":
            check_backlog_edit(data)
            return 0
        why = classify(r)
        if why:
            block(explain(r, why))
    elif tool == "Bash":
        check_bash(ti.get("command", ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
