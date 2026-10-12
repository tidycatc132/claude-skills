#!/usr/bin/env python3
"""Turn a domain metrics CSV into the competitive landscape table with calculated shares and ranks.

Usage
  python3 scripts/benchmark.py domain_metrics.csv [--out-csv competitor_benchmark.csv] [--out-md competitor_benchmark.md]

Input CSV columns (header required; extra columns are carried through):
  `domain`, `role` (you | competitor), `authority`, `traffic`, `top10_keywords`, `backlinks`,
  `referring_domains`, optional `source`, `observed_at`.
  Empty cells or N/A mean the metric was not measured; they are never guessed.

Output CSV adds, per row: `traffic_share_pct` (traffic / sum of known traffic x 100, 1 decimal),
`rank_traffic`, `rank_authority`, `rank_top10_keywords`, `rank_referring_domains` (1 = highest),
and `label` = Calculated for the derived columns. The markdown file holds the landscape table,
the share arithmetic, and the leader per metric. Exit 0 on success, 2 on bad input.
Standard library only.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

METRICS = ["authority", "traffic", "top10_keywords", "backlinks", "referring_domains"]
REQUIRED = ["domain"] + METRICS


def num(v: str):
    s = (v or "").strip().replace(",", "")
    if not s or s.upper() in ("N/A", "NA", "UNKNOWN", "-"):
        return None
    try:
        return float(s)
    except ValueError:
        raise ValueError(f"{v!r} is not a number or N/A")


def fmt(v) -> str:
    if v is None:
        return "N/A"
    return f"{int(v):,}" if float(v).is_integer() else f"{v:,.1f}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("metrics_csv")
    ap.add_argument("--out-csv", default="competitor_benchmark.csv")
    ap.add_argument("--out-md", default="competitor_benchmark.md")
    args = ap.parse_args()

    p = Path(args.metrics_csv)
    try:
        with p.open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    except OSError as e:
        print(f"benchmark: cannot read {p}: {e}", file=sys.stderr)
        return 2
    if not rows:
        print("benchmark: the CSV has no data rows", file=sys.stderr)
        return 2
    header = [h.strip() for h in rows[0].keys() if h]
    missing = [c for c in REQUIRED if c not in header]
    if missing:
        print(f"benchmark: missing columns {missing}; need {REQUIRED}", file=sys.stderr)
        return 2

    data = []
    for r in rows:
        r = {k.strip(): (v or "").strip() for k, v in r.items() if k}
        if not r.get("domain"):
            continue
        rec = dict(r)
        try:
            for m in METRICS:
                rec[m + "_num"] = num(r.get(m, ""))
        except ValueError as e:
            print(f"benchmark: row {r['domain']}: {e}", file=sys.stderr)
            return 2
        rec["role"] = (r.get("role") or "competitor").lower()
        data.append(rec)
    if len(data) < 2:
        print("benchmark: need at least two domains to compare", file=sys.stderr)
        return 2

    known_traffic = [d["traffic_num"] for d in data if d["traffic_num"] is not None]
    total_traffic = sum(known_traffic)
    for d in data:
        if d["traffic_num"] is None or total_traffic == 0:
            d["traffic_share_pct"] = ""
        else:
            d["traffic_share_pct"] = f"{d['traffic_num'] / total_traffic * 100:.1f}"
    for m in METRICS:
        ranked = sorted([d for d in data if d[m + "_num"] is not None], key=lambda d: -d[m + "_num"])
        for i, d in enumerate(ranked, 1):
            d["rank_" + m] = str(i)
        for d in data:
            d.setdefault("rank_" + m, "")

    out_cols = header + ["traffic_share_pct", "rank_traffic", "rank_authority", "rank_top10_keywords",
                         "rank_referring_domains", "label"]
    out_cols = list(dict.fromkeys(out_cols))
    with Path(args.out_csv).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=out_cols)
        w.writeheader()
        for d in data:
            row = {c: d.get(c, "") for c in out_cols}
            row["label"] = "Calculated"
            w.writerow(row)

    you = [d for d in data if d["role"] == "you"]
    L = ["## Competitive landscape (Calculated from the metrics CSV)", ""]
    L.append("| Metric | " + " | ".join(d["domain"] + (" (you)" if d["role"] == "you" else "") for d in data) + " |")
    L.append("|---|" + "---|" * len(data))
    names = {"authority": "Authority", "traffic": "Est. monthly traffic", "top10_keywords": "Top 10 keywords",
             "backlinks": "Backlinks", "referring_domains": "Referring domains"}
    for m in METRICS:
        L.append(f"| {names[m]} | " + " | ".join(fmt(d[m + '_num']) for d in data) + " |")
    L.append("| Traffic share | " + " | ".join((d["traffic_share_pct"] + "%") if d["traffic_share_pct"] else "N/A" for d in data) + " |")
    L.append("")
    if total_traffic:
        L.append("Traffic share arithmetic: total known traffic = " + " + ".join(fmt(t) for t in known_traffic) + f" = {fmt(total_traffic)}; "
                 + "; ".join(f"{d['domain']} {fmt(d['traffic_num'])} / {fmt(total_traffic)} = {d['traffic_share_pct']}%" for d in data if d["traffic_share_pct"]))
    else:
        L.append("Traffic share: N/A (no traffic figures supplied).")
    L.append("")
    L.append("Leaders: " + "; ".join(
        f"{names[m]} = {max((d for d in data if d[m + '_num'] is not None), key=lambda d: d[m + '_num'])['domain']}"
        for m in METRICS if any(d[m + "_num"] is not None for d in data)))
    if you:
        y = you[0]
        gaps = []
        for m in METRICS:
            if y[m + "_num"] is None:
                continue
            leader = max((d for d in data if d[m + "_num"] is not None), key=lambda d: d[m + "_num"])
            if leader is not y and y[m + "_num"]:
                gaps.append(f"{names[m]}: {leader['domain']} has {leader[m + '_num'] / y[m + '_num']:.1f}x yours ({fmt(leader[m + '_num'])} vs {fmt(y[m + '_num'])})")
        if gaps:
            L.append("")
            L.append("Your gaps vs the leader: " + "; ".join(gaps))
    sources = sorted({(d.get("source", ""), d.get("observed_at", "")) for d in data if d.get("source") or d.get("observed_at")})
    if sources:
        L.append("")
        L.append("Sources: " + "; ".join(f"{s} ({o})" if o else s for s, o in sources))
    Path(args.out_md).write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"{len(data)} domains; total known traffic {fmt(total_traffic)}; wrote {args.out_csv} and {args.out_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
