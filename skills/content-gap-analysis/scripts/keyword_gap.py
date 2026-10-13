#!/usr/bin/env python3
"""Segment keyword exports into only-you / shared / only-them and flag qualified gaps.

Usage
  python3 scripts/keyword_gap.py --you kw_you.csv --competitor pipeline-pro.com=kw_pipeline-pro.csv
                                 [--competitor dealflowhq.com=kw_dealflowhq.csv ...]
                                 [--min-volume 100] [--losing-position 20]
                                 [--out keyword_segments.csv] [--out-md keyword_gap_summary.md]

Input CSVs (one per site): columns `keyword`, `position`, `volume`, optional `url`.
Positions are the site's ranking position (1 = top). Volume is monthly searches.

Output `keyword_segments.csv` columns:
  `keyword`, `volume`, `segment` (only_you | shared | only_them), `your_position`,
  `competitor_positions` (name:pos; name:pos), `best_competitor`, `best_competitor_position`,
  `best_competitor_url`, `qualified_gap` (yes when only_them and volume >= min-volume, else no),
  `battleground` (yes when shared and your position is worse than --losing-position, else no)
The summary markdown has the segment counts and the qualified gap list. No-one gaps (keywords
nobody ranks for) cannot come from exports; add them from the trend scout by hand.
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

def load(path: str) -> dict[str, dict]:
    p = Path(path)
    with p.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError(f"{p} has no rows")
    cols = {c.strip().lower() for c in rows[0].keys() if c}
    for need in ("keyword", "position", "volume"):
        if need not in cols:
            raise ValueError(f"{p} needs columns keyword, position, volume; got {sorted(cols)}")
    out: dict[str, dict] = {}
    for r in rows:
        r = {k.strip().lower(): (v or "").strip() for k, v in r.items() if k}
        kw = " ".join(r["keyword"].lower().split())
        if not kw:
            continue
        try:
            pos = int(float(r["position"])) if r["position"] else None
        except ValueError:
            raise ValueError(f"{p}: position {r['position']!r} for {kw!r} is not a number")
        try:
            vol = int(float(r["volume"].replace(",", ""))) if r["volume"] else None
        except ValueError:
            raise ValueError(f"{p}: volume {r['volume']!r} for {kw!r} is not a number")
        prev = out.get(kw)
        if prev is None or (pos is not None and (prev["position"] is None or pos < prev["position"])):
            out[kw] = {"position": pos, "volume": vol, "url": r.get("url", "")}
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--you", required=True, help="your keyword export CSV")
    ap.add_argument("--competitor", action="append", default=[], metavar="NAME=CSV", help="repeatable")
    ap.add_argument("--min-volume", type=int, default=100)
    ap.add_argument("--losing-position", type=int, default=20)
    ap.add_argument("--out", default=None, help="default: keyword_segments.csv next to your export")
    ap.add_argument("--out-md", default=None, help="default: keyword_gap_summary.md next to your export")
    args = ap.parse_args()
    args.out = _beside(args.you, "keyword_segments.csv", args.out)
    args.out_md = _beside(args.you, "keyword_gap_summary.md", args.out_md)
    if not args.competitor:
        print("keyword_gap: give at least one --competitor NAME=CSV", file=sys.stderr)
        return 2
    try:
        you = load(args.you)
        comps: dict[str, dict[str, dict]] = {}
        for spec in args.competitor:
            if "=" not in spec:
                raise ValueError(f"--competitor needs NAME=CSV, got {spec!r}")
            name, path = spec.split("=", 1)
            comps[name.strip()] = load(path.strip())
    except (OSError, ValueError) as e:
        print(f"keyword_gap: {e}", file=sys.stderr)
        return 2

    all_kw = set(you) | {k for c in comps.values() for k in c}
    rows = []
    for kw in sorted(all_kw):
        y = you.get(kw)
        hits = {n: c[kw] for n, c in comps.items() if kw in c}
        vol = None
        for src in ([y] if y else []) + list(hits.values()):
            if src and src["volume"] is not None:
                vol = src["volume"] if vol is None else max(vol, src["volume"])
        if y and hits:
            seg = "shared"
        elif y:
            seg = "only_you"
        else:
            seg = "only_them"
        best = None
        for n, h in hits.items():
            if h["position"] is None:
                continue
            if best is None or h["position"] < hits[best]["position"]:
                best = n
        ypos = y["position"] if y else None
        qualified = seg == "only_them" and vol is not None and vol >= args.min_volume
        battle = seg == "shared" and ypos is not None and ypos > args.losing_position
        rows.append({
            "keyword": kw,
            "volume": "" if vol is None else vol,
            "segment": seg,
            "your_position": "" if ypos is None else ypos,
            "competitor_positions": "; ".join(f"{n}:{h['position'] if h['position'] is not None else 'n/a'}" for n, h in hits.items()),
            "best_competitor": best or "",
            "best_competitor_position": "" if best is None else hits[best]["position"],
            "best_competitor_url": hits[best]["url"] if best else "",
            "qualified_gap": "yes" if qualified else "no",
            "battleground": "yes" if battle else "no",
        })
    order = {"only_them": 0, "shared": 1, "only_you": 2}
    rows.sort(key=lambda r: (order[r["segment"]], -(r["volume"] or 0) if isinstance(r["volume"], int) else 0, r["keyword"]))
    cols = ["keyword", "volume", "segment", "your_position", "competitor_positions", "best_competitor",
            "best_competitor_position", "best_competitor_url", "qualified_gap", "battleground"]
    with Path(args.out).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    counts = {s: sum(1 for r in rows if r["segment"] == s) for s in ("only_you", "shared", "only_them")}
    qualified = [r for r in rows if r["qualified_gap"] == "yes"]
    battles = [r for r in rows if r["battleground"] == "yes"]
    L = ["## Keyword gap segments (Measured from the exports; segmentation Calculated)", ""]
    L.append("| Segment | Meaning | Keywords | Action |")
    L.append("|---|---|---:|---|")
    L.append(f"| Only you | Content moat | {counts['only_you']} | Protect and strengthen |")
    L.append(f"| Shared | Battleground | {counts['shared']} | Improve rankings ({len(battles)} where you rank worse than {args.losing_position}) |")
    L.append(f"| Only them | Content gap | {counts['only_them']} | Prioritize and create ({len(qualified)} qualified at volume >= {args.min_volume}) |")
    L.append("| No one | Untapped | n/a from exports | Add trend-scout candidates by hand |")
    L.append("")
    L.append(f"### Qualified gaps (only them, volume >= {args.min_volume})")
    L.append("| Keyword | Volume | Best competitor | Their position | Their URL |")
    L.append("|---|---:|---|---:|---|")
    for r in qualified:
        L.append(f"| {r['keyword']} | {r['volume']} | {r['best_competitor']} | {r['best_competitor_position']} | {r['best_competitor_url']} |")
    if not qualified:
        L.append("| none | | | | |")
    L.append("")
    L.append(f"### Battleground (shared, your position worse than {args.losing_position})")
    L.append("| Keyword | Volume | Your position | Competitor positions |")
    L.append("|---|---:|---:|---|")
    for r in battles:
        L.append(f"| {r['keyword']} | {r['volume']} | {r['your_position']} | {r['competitor_positions']} |")
    if not battles:
        L.append("| none | | | |")
    below = [r for r in rows if r["segment"] == "only_them" and r["qualified_gap"] == "no"]
    if below:
        L.append("")
        L.append("Only-them keywords below the volume filter (not qualified): " + ", ".join(f"{r['keyword']} ({r['volume'] if r['volume'] != '' else 'no volume'})" for r in below))
    Path(args.out_md).write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"{len(rows)} keywords: only_you={counts['only_you']} shared={counts['shared']} only_them={counts['only_them']} "
          f"qualified_gaps={len(qualified)} battleground={len(battles)}; wrote {args.out} and {args.out_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
