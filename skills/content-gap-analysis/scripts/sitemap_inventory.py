#!/usr/bin/env python3
"""Count each site's coverage by URL section from saved sitemap XML files.

Usage
  python3 scripts/sitemap_inventory.py --site you=sitemap_you.xml --site pipeline-pro.com=sitemap_pipeline-pro.xml
                                       [--site NAME=FILE ...] [--since YYYY-MM-DD]
                                       [--out coverage_inventory.csv] [--out-md coverage_inventory.md]

Each file is a saved `<urlset>` (or a `<sitemapindex>`, in which case its child sitemap URLs are
listed for you to fetch and pass in as further files). Fetch remote sitemaps first and save them;
this script reads local files only.

Output `coverage_inventory.csv` columns: `site`, `section` (first path segment, `root` for the
homepage), `url_count`, `with_lastmod_pct`, `latest_lastmod`, `recent_count` (lastmod on or after
--since, blank when --since is not given). The markdown has one site-by-section matrix plus per-site
totals. Counts are Measured (sitemap). Exit 0 on success, 2 on bad input. Standard library only.
"""
from __future__ import annotations

import argparse
import csv
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlsplit



def _beside(primary: str, default_name: str, given: str | None) -> str:
    """Default output path: next to the primary input file unless an explicit path was given."""
    if given is not None:
        return given
    return str(Path(primary).resolve().parent / default_name)

def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def parse(path: Path) -> tuple[str, list[tuple[str, str]]]:
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as e:
        raise ValueError(f"{path} is not valid XML: {e}")
    kind = local(root.tag)
    entries = []
    for child in root:
        if local(child.tag) not in ("url", "sitemap"):
            continue
        loc = lastmod = ""
        for el in child:
            if local(el.tag) == "loc":
                loc = (el.text or "").strip()
            elif local(el.tag) == "lastmod":
                lastmod = (el.text or "").strip()[:10]
        if loc:
            entries.append((loc, lastmod))
    if kind not in ("urlset", "sitemapindex"):
        raise ValueError(f"{path}: root element is <{kind}>, expected <urlset> or <sitemapindex>")
    return kind, entries


def section(url: str) -> str:
    path = urlsplit(url).path.strip("/")
    if not path:
        return "root"
    return path.split("/", 1)[0]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--site", action="append", default=[], metavar="NAME=FILE", help="repeatable")
    ap.add_argument("--since", help="count URLs with lastmod on or after this date (YYYY-MM-DD)")
    ap.add_argument("--out", default=None, help="default: coverage_inventory.csv next to the first sitemap")
    ap.add_argument("--out-md", default=None, help="default: coverage_inventory.md next to the first sitemap")
    args = ap.parse_args()
    if not args.site:
        print("sitemap_inventory: give at least one --site NAME=FILE", file=sys.stderr)
        return 2
    first = args.site[0].split("=", 1)[-1].strip()
    args.out = _beside(first, "coverage_inventory.csv", args.out)
    args.out_md = _beside(first, "coverage_inventory.md", args.out_md)

    rows = []
    totals = {}
    indexes = {}
    for spec in args.site:
        if "=" not in spec:
            print(f"sitemap_inventory: --site needs NAME=FILE, got {spec!r}", file=sys.stderr)
            return 2
        name, file = (s.strip() for s in spec.split("=", 1))
        try:
            kind, entries = parse(Path(file))
        except (OSError, ValueError) as e:
            print(f"sitemap_inventory: {e}", file=sys.stderr)
            return 2
        if kind == "sitemapindex":
            indexes[name] = [loc for loc, _ in entries]
            continue
        by_sec: dict[str, list[tuple[str, str]]] = defaultdict(list)
        for loc, lm in entries:
            by_sec[section(loc)].append((loc, lm))
        for sec in sorted(by_sec, key=lambda s: (-len(by_sec[s]), s)):
            items = by_sec[sec]
            lms = [lm for _, lm in items if lm]
            recent = sum(1 for lm in lms if args.since and lm >= args.since) if args.since else ""
            rows.append({
                "site": name, "section": sec, "url_count": len(items),
                "with_lastmod_pct": f"{len(lms) / len(items) * 100:.0f}",
                "latest_lastmod": max(lms) if lms else "",
                "recent_count": recent,
            })
        all_lms = [lm for _, lm in entries if lm]
        totals[name] = {"urls": len(entries), "sections": len(by_sec), "latest": max(all_lms) if all_lms else "",
                        "identical_lastmod": len(all_lms) > 3 and len(set(all_lms)) == 1}

    cols = ["site", "section", "url_count", "with_lastmod_pct", "latest_lastmod", "recent_count"]
    with Path(args.out).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    sites = [n for n in totals]
    sections = sorted({r["section"] for r in rows}, key=lambda s: (s == "root", s))
    L = ["## Coverage inventory (Measured from sitemaps)", ""]
    L.append("| Section | " + " | ".join(sites) + " |")
    L.append("|---|" + "---:|" * len(sites))
    lookup = {(r["site"], r["section"]): r for r in rows}
    for sec in sections:
        L.append(f"| /{sec}/ | " + " | ".join(str(lookup[(s, sec)]["url_count"]) if (s, sec) in lookup else "0" for s in sites) + " |")
    L.append("| **Total URLs** | " + " | ".join(str(totals[s]["urls"]) for s in sites) + " |")
    L.append("")
    for s in sites:
        t = totals[s]
        warn = " (every lastmod identical: untrustworthy)" if t["identical_lastmod"] else ""
        L.append(f"- {s}: {t['urls']} URLs in {t['sections']} sections, latest lastmod {t['latest'] or 'none'}{warn}")
    if args.since:
        L.append("")
        L.append(f"Recent URLs (lastmod >= {args.since}): " + "; ".join(
            f"{s} {sum(int(r['recent_count']) for r in rows if r['site'] == s)}" for s in sites))
    for name, children in indexes.items():
        L.append("")
        L.append(f"{name} is a sitemap index with {len(children)} child sitemaps; fetch and pass them in: " + ", ".join(children[:20]))
    Path(args.out_md).write_text("\n".join(L) + "\n", encoding="utf-8")
    print("; ".join(f"{s}: {totals[s]['urls']} URLs / {totals[s]['sections']} sections" for s in sites) + f"; wrote {args.out} and {args.out_md}")
    for name, children in indexes.items():
        print(f"{name}: sitemap index with {len(children)} children (not counted)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
