#!/usr/bin/env python3
"""Trigger evals: does Claude invoke the right skill for each prompt?

For every evals/<skill>/trigger.json
    {"should_trigger": [...prompts], "should_not_trigger": [...prompts]}
each prompt is run through headless `claude -p` in a sandbox that holds ALL skills (so
collisions with siblings are real), and we check whether the Skill tool was invoked for the
target skill. should_not_trigger prompts should include near-neighbours that belong to a
sibling skill.

Usage:
  run_trigger_evals.py [--skill NAME ...] [--runs 1] [--jobs 4] [--min-pass 0.9]
                       [--model sonnet] [--only-skills NAME ...] [--dry-run]

Exit: 0 all thresholds met; 1 below threshold; 2 runs errored (auth, timeout...) and
--allow-errors not given. Results are written to .harness/results/ (gitignored).
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402
import evalkit as E  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--skill", action="append", help="limit to these skills (repeatable)")
    ap.add_argument("--runs", type=int, default=1, help="runs per prompt; majority vote")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--min-pass", type=float, default=0.9)
    ap.add_argument("--model")
    ap.add_argument("--budget", type=float, help="max USD per run")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--allow-errors", action="store_true")
    args = ap.parse_args()

    all_dirs = C.list_skill_dirs()
    names = [d.name for d in all_dirs]
    targets = [n for n in names if (C.EVALS_DIR / n / "trigger.json").exists()]
    if args.skill:
        targets = [n for n in targets if n in args.skill]
    cases = []
    for n in targets:
        data = C.load_json(C.EVALS_DIR / n / "trigger.json")
        for p in data.get("should_trigger", []):
            cases.append((n, True, str(p)))
        for p in data.get("should_not_trigger", []):
            cases.append((n, False, str(p)))
    if not cases:
        print("no trigger evals found")
        return 0
    if args.dry_run:
        for n, should, p in cases:
            print(f"  {'SHOULD    ' if should else 'SHOULD NOT'} {n}: {p[:90]}")
        print(f"{len(cases)} cases across {len(targets)} skill(s); runs per case: {args.runs}")
        return 0
    if not E.claude_bin():
        print("`claude` CLI not found; install Claude Code or set HARNESS_CLAUDE_BIN.", file=sys.stderr)
        return 2

    sandbox = E.make_sandbox(all_dirs)

    def one(case):
        n, should, prompt = case
        votes, errs = 0, []
        for _ in range(args.runs):
            r = E.run_claude(prompt, sandbox, allowed="Skill", model=args.model, budget=args.budget, timeout=180)
            if not r.ok and not r.tool_uses:
                errs.append(r.error)
                continue
            invoked = n in r.skills_invoked(names)
            votes += 1 if invoked == should else 0
        good = args.runs - len(errs)
        if good == 0:
            return case, "ERROR", errs[0] if errs else "error"
        return case, ("PASS" if votes * 2 > good else "FAIL"), ""

    t0 = time.time()
    try:
        with ThreadPoolExecutor(max_workers=args.jobs) as ex:
            results = list(ex.map(one, cases))
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)

    exit_code = 0
    per_skill: dict[str, dict] = {}
    for (n, should, p), status, detail in results:
        s = per_skill.setdefault(n, {"pass": 0, "fail": 0, "error": 0, "failures": []})
        s[status.lower()] += 1
        if status == "FAIL":
            s["failures"].append(f"{'should have triggered' if should else 'should NOT have triggered'}: {p[:80]}")
        if status == "ERROR":
            s["failures"].append(f"error: {detail}")
    for n, s in per_skill.items():
        total = s["pass"] + s["fail"]
        rate = s["pass"] / total if total else 0.0
        flag = "ok " if rate >= args.min_pass and not s["error"] else "BAD"
        print(f"[{flag}] {n}: {s['pass']}/{total} correct ({rate:.0%}), {s['error']} errored")
        for f in s["failures"]:
            print(f"        - {f}")
        if total and rate < args.min_pass:
            exit_code = max(exit_code, 1)
        if s["error"] and not args.allow_errors:
            exit_code = 2
    C.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = C.RESULTS_DIR / f"trigger-{time.strftime('%Y%m%d-%H%M%S')}.json"
    out.write_text(json.dumps(per_skill, indent=2))
    print(f"{len(cases)} cases in {time.time() - t0:.0f}s; results: {out.relative_to(C.ROOT)}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
