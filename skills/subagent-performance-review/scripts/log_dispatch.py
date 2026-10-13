#!/usr/bin/env python3
"""Append one dispatch record to the JSONL dispatch log and say whether a review is due.

Usage:
  python3 scripts/log_dispatch.py --log subagent_dispatch_log.jsonl --agent NAME --task TEXT
          --outcome accepted|accepted_with_fixes|rejected|abandoned|blocked
          [--task-type TYPE] [--complexity 1|2|3] [--rework-rounds N] [--scope-violations N]
          [--fabrication] [--tool-errors N] [--duration-s N] [--notes TEXT] [--dispatched-at ISO]

Creates the log if it does not exist. dispatch_id is d-NNNN, one higher than the
last record. Prints the agent's record count in the last 30 days and whether that
reaches the five needed for a review. Standard library only.
"""
import argparse
import datetime as dt
import json
import os
import re
import sys

OUTCOMES = ["accepted", "accepted_with_fixes", "rejected", "abandoned", "blocked"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--log", required=True)
    ap.add_argument("--agent", required=True)
    ap.add_argument("--task", required=True)
    ap.add_argument("--outcome", required=True, choices=OUTCOMES)
    ap.add_argument("--task-type", default="unspecified")
    ap.add_argument("--complexity", type=int, default=2, choices=[1, 2, 3])
    ap.add_argument("--rework-rounds", type=int, default=0)
    ap.add_argument("--scope-violations", type=int, default=0)
    ap.add_argument("--fabrication", action="store_true")
    ap.add_argument("--tool-errors", type=int, default=0)
    ap.add_argument("--duration-s", type=int, default=0)
    ap.add_argument("--notes", default="")
    ap.add_argument("--dispatched-at", help="ISO timestamp; default now (UTC)")
    args = ap.parse_args()

    rows = []
    if os.path.exists(args.log):
        with open(args.log, encoding="utf-8") as fh:
            rows = [json.loads(l) for l in fh if l.strip()]
    last = 0
    for r in rows:
        m = re.match(r"d-(\d+)$", str(r.get("dispatch_id", "")))
        if m:
            last = max(last, int(m.group(1)))
    now = dt.datetime.now(dt.timezone.utc)
    ts = args.dispatched_at or now.strftime("%Y-%m-%dT%H:%M:%SZ")
    rec = {"dispatch_id": f"d-{last + 1:04d}", "agent": args.agent, "dispatched_at": ts, "task": args.task,
           "task_type": args.task_type, "complexity": args.complexity, "outcome": args.outcome,
           "rework_rounds": args.rework_rounds, "scope_violations": args.scope_violations,
           "fabrication": bool(args.fabrication), "tool_errors": args.tool_errors,
           "duration_s": args.duration_s, "notes": args.notes}
    with open(args.log, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec) + "\n")
    cutoff = now - dt.timedelta(days=30)
    n = 0
    for r in rows + [rec]:
        if r.get("agent") != args.agent:
            continue
        s = r["dispatched_at"].replace("Z", "+00:00")
        try:
            d = dt.datetime.fromisoformat(s)
        except ValueError:
            continue
        if d.tzinfo is None:
            d = d.replace(tzinfo=dt.timezone.utc)
        if d >= cutoff:
            n += 1
    print(f"logged {rec['dispatch_id']} for {args.agent}: {args.outcome}")
    print(f"{args.agent} has {n} dispatches in the last 30 days; review {'is due (5 or more)' if n >= 5 else 'needs ' + str(5 - n) + ' more'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
