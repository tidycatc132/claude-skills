#!/usr/bin/env python3
"""Compute the Opportunity Score, tier, Quick Win value and backlog bucket for each scored gap.

Usage
  python3 scripts/score_gaps.py gap_scores.csv [--out gap_priority.csv] [--out-md gap_priority.md]

Input CSV: one row per gap with the five factor scores (integers 1-5, higher is better for the gap):
  `gap`, `demand`, `density`, `relevance`, `effort`, `conversion`
  Other columns (for example `competitor`, `volume`, `evidence`) are carried through unchanged.
  Anchors (references/gap-analysis-frameworks.md): demand 1 = under 100/mo, 5 = over 5,000;
  density 1 = every competitor covers it, 5 = no one does; relevance 1 = tangential, 5 = core;
  effort 1 = new capability needed, 5 = quick; conversion 1 = top-funnel, 5 = transactional.

Output adds: `score` = 0.25 demand + 0.20 density + 0.25 relevance + 0.15 effort + 0.15 conversion
(2 decimals); `tier` P0 (4.0-5.0), P1 (3.0-3.9), P2 (2.0-2.9), P3 (1.0-1.9);
`quick_win` = demand + relevance + effort + density - 12 (range -8 to +8);
`quick_win_label` strong (4+), moderate (2-3), weak (0-1), avoid (negative);
`bucket` Quick Wins (P0, or P1 with a strong quick win), Strategic Builds (other P1),
Long-term (P2, P3); `arithmetic` showing the sum. Rows are sorted by score, then quick win.
Exit 0 on success, 2 on bad input. Standard library only.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


def _beside(primary: str, default_name: str, given: str | None) -> str:
    """Default output path: next to the primary input file unless an explicit path was given."""
    if given is not None:
        return given
    return str(Path(primary).resolve().parent / default_name)

FACTORS = [("demand", 0.25), ("density", 0.20), ("relevance", 0.25), ("effort", 0.15), ("conversion", 0.15)]


def tier(score: float) -> str:
    if score >= 4.0:
        return "P0"
    if score >= 3.0:
        return "P1"
    if score >= 2.0:
        return "P2"
    return "P3"


def qw_label(v: int) -> str:
    if v >= 4:
        return "strong"
    if v >= 2:
        return "moderate"
    if v >= 0:
        return "weak"
    return "avoid"


def bucket(t: str, qw: int) -> str:
    if t == "P0":
        return "Quick Wins"
    if t == "P1":
        return "Quick Wins" if qw >= 4 else "Strategic Builds"
    return "Long-term"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scores_csv")
    ap.add_argument("--out", default=None, help="default: gap_priority.csv next to the input")
    ap.add_argument("--out-md", default=None, help="default: gap_priority.md next to the input")
    args = ap.parse_args()
    args.out = _beside(args.scores_csv, "gap_priority.csv", args.out)
    args.out_md = _beside(args.scores_csv, "gap_priority.md", args.out_md)
    p = Path(args.scores_csv)
    try:
        with p.open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    except OSError as e:
        print(f"score_gaps: cannot read {p}: {e}", file=sys.stderr)
        return 2
    if not rows:
        print("score_gaps: no data rows", file=sys.stderr)
        return 2
    header = [h.strip() for h in rows[0].keys() if h]
    missing = [c for c in ["gap"] + [f for f, _ in FACTORS] if c not in header]
    if missing:
        print(f"score_gaps: missing columns {missing}", file=sys.stderr)
        return 2

    out = []
    for n, r in enumerate(rows, 2):
        r = {k.strip(): (v or "").strip() for k, v in r.items() if k}
        if not r.get("gap"):
            continue
        vals = {}
        for f, _ in FACTORS:
            try:
                v = int(float(r[f]))
            except ValueError:
                print(f"score_gaps: line {n} ({r['gap']}): {f}={r[f]!r} is not a number", file=sys.stderr)
                return 2
            if not 1 <= v <= 5:
                print(f"score_gaps: line {n} ({r['gap']}): {f}={v} must be 1-5", file=sys.stderr)
                return 2
            vals[f] = v
        score = sum(vals[f] * w for f, w in FACTORS)
        score_r = round(score + 1e-9, 2)
        t = tier(score_r)
        qw = vals["demand"] + vals["relevance"] + vals["effort"] + vals["density"] - 12
        arith = " + ".join(f"{w:.2f}x{vals[f]}" for f, w in FACTORS) + f" = {score_r:.2f} -> {t}; quick win = {vals['demand']} + {vals['relevance']} + {vals['effort']} + {vals['density']} - 12 = {qw}"
        rec = dict(r)
        rec.update(score=f"{score_r:.2f}", tier=t, quick_win=str(qw), quick_win_label=qw_label(qw), bucket=bucket(t, qw), arithmetic=arith)
        rec["_sort"] = (-score_r, -qw)
        out.append(rec)
    out.sort(key=lambda x: x["_sort"])
    cols = header + ["score", "tier", "quick_win", "quick_win_label", "bucket", "arithmetic"]
    cols = list(dict.fromkeys(cols))
    with Path(args.out).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in out:
            w.writerow({c: r.get(c, "") for c in cols})

    L = ["## Opportunity scoring (Calculated)", ""]
    L.append("| Gap | Demand (25%) | Density (20%) | Relevance (25%) | Effort (15%) | Conversion (15%) | Score | Tier | Quick Win | Bucket |")
    L.append("|---|---:|---:|---:|---:|---:|---:|---|---|---|")
    for r in out:
        L.append(f"| {r['gap']} | {r['demand']} | {r['density']} | {r['relevance']} | {r['effort']} | {r['conversion']} | {r['score']} | {r['tier']} | {r['quick_win']} ({r['quick_win_label']}) | {r['bucket']} |")
    L.append("")
    for b in ("Quick Wins", "Strategic Builds", "Long-term"):
        items = [r for r in out if r["bucket"] == b]
        L.append(f"### {b} ({len(items)})")
        for r in items:
            extra = f" — {r['competitor']}" if r.get("competitor") else ""
            promoted = " (P1 promoted on a strong quick win)" if b == "Quick Wins" and r["tier"] == "P1" else ""
            L.append(f"- {r['gap']}{extra}: {r['arithmetic']}{promoted}")
        if not items:
            L.append("- none")
        L.append("")
    Path(args.out_md).write_text("\n".join(L) + "\n", encoding="utf-8")
    counts = {b: sum(1 for r in out if r["bucket"] == b) for b in ("Quick Wins", "Strategic Builds", "Long-term")}
    print(f"{len(out)} gaps scored: {counts}; wrote {args.out} and {args.out_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
