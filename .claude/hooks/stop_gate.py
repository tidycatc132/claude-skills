#!/usr/bin/env python3
"""Stop hook: Claude may not declare victory while the cheap gates are red.

Runs (only when skills/evals/contracts/backlog changed, per git; always when not a git repo):
  1. validate_skill.py --changed --strict      structure, references, evals present
  2. check_contracts.py --all                  pipeline interfaces still line up
  3. check_overlap.py                          no unlabeled trigger collisions
  4. check_backlog.py --against-git            `passes` claims are backed by evidence
  5. tamper check                              committed evals/fixtures/contracts/scripts untouched

Expensive gates (headless trigger/output evals, reviewer subagent) are NOT run here; use
/verify-skill. Blocks with JSON {"decision":"block","reason":...}. To avoid trapping a
legitimate pause (e.g. waiting on the user), it allows the stop after MAX_BLOCKS consecutive
blocks and records the unresolved failures in failure_log.md.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import common as C  # noqa: E402

MAX_BLOCKS = int(os.environ.get("HARNESS_MAX_STOP_BLOCKS", "2"))
SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
WATCHED = ("skills/", "evals/", "contracts/", "fixtures/", "skills_backlog.json")
TAMPER_PATHS = ["evals", "fixtures", "contracts", "scripts", ".claude/hooks", ".claude/agents", ".claude/commands", ".claude/settings.json"]


def run(script: str, *args: str) -> tuple[int, str]:
    env = dict(os.environ, HARNESS_ROOT=str(C.ROOT), PYTHONDONTWRITEBYTECODE="1")
    p = subprocess.run([sys.executable, str(SCRIPTS / script), *args], cwd=C.ROOT, capture_output=True, text=True, timeout=300, env=env)
    return p.returncode, (p.stdout + p.stderr)


def errors_only(out: str) -> list[str]:
    return [l.strip() for l in out.splitlines() if l.strip().startswith("ERROR")]


def tamper() -> list[str]:
    if (C.ROOT / ".harness-unlock").exists() or os.environ.get("HARNESS_UNLOCK") == "1":
        return []
    if not (C.is_git_repo() and C.has_commits()):
        return []
    rc, out = C.git("diff", "--name-only", "HEAD", "--", *TAMPER_PATHS)
    return [l for l in out.splitlines() if l.strip()] if rc == 0 else []


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        data = {}
    session = str(data.get("session_id", "nosession"))
    state_dir = C.ROOT / ".claude" / ".state"
    counter = state_dir / f"stop-{session}.count"

    paths = C.changed_paths()
    if paths is not None and not any(p.startswith(WATCHED) for p in paths):
        counter.unlink(missing_ok=True)
        return 0

    failures: list[str] = []
    for script, args in (
        ("validate_skill.py", ("--changed", "--strict", "--quiet")),
        ("check_contracts.py", ("--all",)),
        ("check_overlap.py", ("--quiet",)),
        ("check_backlog.py", ("--against-git",)),
    ):
        rc, out = run(script, *args)
        if rc != 0:
            failures += [f"{script}: {l}" for l in (errors_only(out) or [out.strip()[-300:]])]
    t = tamper()
    if t:
        failures.append(
            "protected files were modified: " + ", ".join(t)
            + " (evals, fixtures, contracts and the harness are frozen once committed; restore them with "
            "`git checkout -- <file>` and fix the skill instead, or ask the user to create .harness-unlock)"
        )

    if not failures:
        counter.unlink(missing_ok=True)
        return 0

    state_dir.mkdir(parents=True, exist_ok=True)
    n = int(counter.read_text()) + 1 if counter.exists() else 1
    counter.write_text(str(n))
    if n > MAX_BLOCKS:
        counter.unlink(missing_ok=True)
        log = C.ROOT / "failure_log.md"
        try:
            with log.open("a", encoding="utf-8") as f:
                f.write(f"\n## {time.strftime('%Y-%m-%d %H:%M')} - stop gate gave up after {MAX_BLOCKS} blocks\n")
                f.write("\n".join(f"- {x}" for x in failures[:10]) + "\n")
        except OSError:
            pass
        return 0

    reason = (
        "Stop gate: the skills harness found problems, so the work is not done yet.\n  - "
        + "\n  - ".join(failures[:12])
        + "\nFix them (do not edit evals, fixtures, contracts or scripts to make them pass). "
        f"If you are deliberately pausing for the user's input, say exactly what is failing and stop again "
        f"(this gate lets you stop after {MAX_BLOCKS} blocks)."
    )
    print(json.dumps({"decision": "block", "reason": reason}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
