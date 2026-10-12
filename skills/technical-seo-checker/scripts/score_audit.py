#!/usr/bin/env python3
"""Roll per-area scores into the overall /100 score and build the P0/P1/P2 queue.

Usage
  python3 scripts/score_audit.py area_scores.json [--checks page_checks.csv]
                                 [--out-json audit_scorecard.json] [--out-md audit_scorecard.md]

`area_scores.json` (written by hand from the evidence):
  {
    "crawlability":   {"score": 5, "top_blocker": "CSS/JS blocked", "first_fix": "Allow /assets/js/"},
    "indexability":   {"score": 3, ...},
    "performance":    {"score": null, "top_blocker": "no PSI data", "first_fix": ""},   # null = N/A
    "mobile": ..., "security": ..., "url_structure": ..., "structured_data": ..., "international": ...
  }
  A plain number is accepted instead of the object. Scores are integers 0-10; null means the area
  is N/A (excluded) and needs a reason in top_blocker.

Overall = round(sum of scored areas / (10 x number of scored areas) x 100), label Calculated,
arithmetic shown. With --checks, the fail/warn rows of page_checks.csv become the queue, grouped by
severity and ordered P0, P1, P2. Exit 0 on success, 2 on bad input. Standard library only.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

AREAS = ["crawlability", "indexability", "performance", "mobile", "security", "url_structure", "structured_data", "international"]
NAMES = {"crawlability": "Crawlability", "indexability": "Indexability", "performance": "Performance", "mobile": "Mobile",
         "security": "Security", "url_structure": "URL structure", "structured_data": "Structured data", "international": "International"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("area_scores")
    ap.add_argument("--checks")
    ap.add_argument("--out-json", default="audit_scorecard.json")
    ap.add_argument("--out-md", default="audit_scorecard.md")
    args = ap.parse_args()
    try:
        raw = json.loads(Path(args.area_scores).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"score_audit: cannot read {args.area_scores}: {e}", file=sys.stderr)
        return 2
    if not isinstance(raw, dict):
        print("score_audit: area_scores.json must be an object keyed by area", file=sys.stderr)
        return 2
    unknown = [k for k in raw if k not in AREAS]
    if unknown:
        print(f"score_audit: unknown areas {unknown}; use {AREAS}", file=sys.stderr)
        return 2

    areas = {}
    for a in AREAS:
        rec = raw.get(a)
        if rec is None:
            rec = {"score": None, "top_blocker": "not assessed", "first_fix": ""}
        if not isinstance(rec, dict):
            rec = {"score": rec}
        s = rec.get("score")
        if s is not None:
            try:
                s = int(s)
            except (TypeError, ValueError):
                print(f"score_audit: {a}: score {rec.get('score')!r} is not an integer or null", file=sys.stderr)
                return 2
            if not 0 <= s <= 10:
                print(f"score_audit: {a}: score {s} must be 0-10", file=sys.stderr)
                return 2
        areas[a] = {"score": s, "top_blocker": str(rec.get("top_blocker", "") or ""), "first_fix": str(rec.get("first_fix", "") or "")}

    scored = [a for a in AREAS if areas[a]["score"] is not None]
    if not scored:
        print("score_audit: every area is null; nothing to score", file=sys.stderr)
        return 2
    total = sum(areas[a]["score"] for a in scored)
    overall = int(total / (10 * len(scored)) * 100 + 0.5)
    arithmetic = f"({' + '.join(str(areas[a]['score']) for a in scored)}) / (10 x {len(scored)}) x 100 = {total} / {10 * len(scored)} x 100 = {total / (10 * len(scored)) * 100:.1f} -> {overall}/100"
    excluded = [a for a in AREAS if areas[a]["score"] is None]

    queue = {"P0": [], "P1": [], "P2": []}
    if args.checks:
        try:
            with Path(args.checks).open(newline="", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    if r.get("status") in ("fail", "warn") and r.get("severity") in queue:
                        queue[r["severity"]].append({k: r.get(k, "") for k in ("url", "area", "check", "status", "evidence", "fix")})
        except OSError as e:
            print(f"score_audit: cannot read {args.checks}: {e}", file=sys.stderr)
            return 2
        for sev in queue:
            queue[sev].sort(key=lambda r: (r["status"] != "fail", r["area"], r["url"]))

    result = {"areas": areas, "scored_areas": scored, "excluded_areas": excluded, "overall": overall,
              "arithmetic": arithmetic, "label": "Calculated", "queue": queue,
              "queue_counts": {k: len(v) for k, v in queue.items()}}
    Path(args.out_json).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    L = [f"## Overall technical health: {overall}/100 (Calculated)", "", f"Arithmetic: {arithmetic}", ""]
    if excluded:
        L.append("Excluded as N/A: " + "; ".join(f"{NAMES[a]} ({areas[a]['top_blocker'] or 'no reason given'})" for a in excluded))
        L.append("")
    L.append("| Area | Score | Top blocker | First fix |")
    L.append("|---|:---:|---|---|")
    for a in AREAS:
        s = areas[a]["score"]
        L.append(f"| {NAMES[a]} | {'N/A' if s is None else f'{s}/10'} | {areas[a]['top_blocker']} | {areas[a]['first_fix']} |")
    L.append("")
    if args.checks:
        L.append("## Priority queue (from page_checks.csv)")
        for sev, label in (("P0", "P0 — blocks indexing or revenue"), ("P1", "P1 — suppresses performance"), ("P2", "P2 — hygiene")):
            L.append(f"### {label} ({len(queue[sev])})")
            for r in queue[sev]:
                L.append(f"- [{r['status']}] {r['check']} on {r['url']}: {r['evidence']}" + (f" → {r['fix']}" if r["fix"] else ""))
            if not queue[sev]:
                L.append("- none")
            L.append("")
    Path(args.out_md).write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"overall={overall}/100 from {len(scored)} scored areas ({', '.join(excluded) or 'none'} excluded); queue P0={len(queue['P0'])} P1={len(queue['P1'])} P2={len(queue['P2'])}; wrote {args.out_json} and {args.out_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
