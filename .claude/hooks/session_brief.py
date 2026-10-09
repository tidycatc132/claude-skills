#!/usr/bin/env python3
"""SessionStart hook (startup, resume, clear, compact): the 'get your bearings' ritual, automated.

stdout becomes context for Claude. Keeps it short: the non-negotiable rules, how a skill starts,
what is currently red, and the tail of progress.md.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import common as C  # noqa: E402

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"


def run(script: str, *args: str) -> str:
    env = dict(os.environ, HARNESS_ROOT=str(C.ROOT), PYTHONDONTWRITEBYTECODE="1")
    try:
        p = subprocess.run([sys.executable, str(SCRIPTS / script), *args], cwd=C.ROOT, capture_output=True, text=True, timeout=60, env=env)
        return (p.stdout + p.stderr).strip()
    except Exception as e:  # never break session start
        return f"(could not run {script}: {e})"


def main() -> int:
    lines = [
        "SKILLS HARNESS - reminders (re-injected at session start / after compaction)",
        "- One skill per session, built fresh from a plain-language description with /new-skill <description>.",
        "- Never model a new skill on an existing one; read sibling descriptions only to write the boundary sentence.",
        "- Never edit committed evals/, fixtures/, contracts/, scripts/ or .claude/ to make a check pass. Fix the skill.",
        "- Done means: validator strict + contracts + overlap green, then /verify-skill for behavior, then commit.",
        "- Hooks run the cheap gates for you; read their messages and fix, do not argue with them.",
        "",
        "Skills on disk: " + (", ".join(d.name for d in C.list_skill_dirs()) or "none yet"),
    ]
    red = [l for l in run("validate_skill.py", "--changed", "--quiet").splitlines() if "ERROR" in l]
    if red:
        lines.append("Currently failing (changed skills):")
        lines += red[:8]
    prog = C.ROOT / "progress.md"
    if prog.exists():
        tail = [l for l in C.read_text(prog).splitlines() if l.strip()][-12:]
        if tail:
            lines += ["", "Recent progress.md entries:"] + tail
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
