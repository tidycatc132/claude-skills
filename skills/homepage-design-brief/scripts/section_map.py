#!/usr/bin/env python3
"""List the sections of an edited homepage, in order, as the start of the brief's Section Map.

Usage:
  section_map.py <article.md>            skeleton Section Map rows plus the open flags
  section_map.py <article.md> --json     the same as JSON
  section_map.py --known <markers.json>  confirm every marker key in a JSON object is one this skill maps

Exit 1 when the page has no sections, or (with --known) when a marker is not one this skill knows.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hdb  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("article", nargs="?")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--known")
    a = ap.parse_args()

    if a.known:
        keys = list(json.loads(hdb.read(a.known)).keys())
        names = [m.group(1).strip() for k in keys for m in [hdb.MARKER.match(k)] if m]
        bad = [k for k in keys if not hdb.MARKER.match(k)] + [n for n in names if n not in hdb.KNOWN]
        for n in names:
            print(f"maps: {n}")
        if bad:
            print("unknown markers: " + ", ".join(bad), file=sys.stderr)
            return 1
        return 0

    if not a.article:
        ap.error("give the article path, or --known")
    secs, mode = hdb.sections(hdb.read(a.article))
    if not secs:
        print("no sections found: the page has no section markers and no H1 or H2 headings", file=sys.stderr)
        return 1
    if mode == "headings":
        print("WARN: no <!-- section: ... --> markers; sections were taken from the H1 and H2 headings. "
              "Name each Section Map row after the homepage section it plays (Hero, Why Us, ...).", file=sys.stderr)
    unknown = [s["name"] for s in secs if mode == "markers" and s["name"] not in hdb.KNOWN]
    if unknown:
        print("WARN: markers this skill does not know: " + ", ".join(unknown) + " (map them like any other section)",
              file=sys.stderr)
    if a.json:
        print(json.dumps({"mode": mode, "sections": secs}, indent=2))
        return 0
    print(f"Sections ({mode}): {len(secs)}\n")
    print("| # | Section | Purpose | Layout idea | Content source |")
    print("| --- | --- | --- | --- | --- |")
    for i, s in enumerate(secs, 1):
        print(f"| {i} | {s['name']} |  |  | article.md > {s['name']} |")
    print()
    for i, s in enumerate(secs, 1):
        extra = f", {len(s['flags'])} open flag(s)" if s["flags"] else ""
        print(f"{i}. {s['name']}: heading \"{s['heading']}\", about {s['words']} words, {s['links']} link(s){extra}")
    allf = hdb.flags(hdb.read(a.article))
    if allf:
        print("\nOpen flags to copy verbatim into Open Questions:")
        for f in allf:
            print(f"- {f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
