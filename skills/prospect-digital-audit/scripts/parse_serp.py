#!/usr/bin/env python3
"""Extract the prospect's Maps and organic positions from saved SE Ranking SERP results.

Usage:
    python3 -I parse_serp.py DOMAIN BUSINESS_NAME FILE [FILE ...] --out positions.json

Without --out the JSON goes to stdout. Prefer --out: shell redirection is not
needed and on Windows PowerShell it would write UTF-16.

Each FILE is a JSON SERP result (the saved output of DATA_getSerpResults or
DATA_getSerpTaskAdvancedResults). Output is a JSON list with one row per file:
    {"keyword", "location_id", "maps_position", "organic_position", "best_organic_anywhere"}

maps_position     1-3 if the domain or business name appears in the local pack, else null
organic_position  best organic rank (rank_group) of the domain if 10 or better, else null
"""
import json
import sys


def load(path):
    data = json.load(open(path, encoding="utf-8"))
    # DATA_getSerpResults wraps the task under "results"; the task endpoints return it bare.
    return data.get("results", data)


def parse(result, domain, business):
    meta = result.get("request_metadata", {})
    items = result.get("items", [])
    domain = domain.lower().removeprefix("www.")
    name = business.lower()
    maps = None
    best = None
    for item in items:
        if item.get("type") == "local_pack":
            for i, link in enumerate(item.get("links", []), start=1):
                url = (link.get("url") or "").lower()
                title = (link.get("title") or "").lower()
                if domain in url or name in title:
                    maps = maps or i
        elif item.get("type") == "organic":
            item_domain = (item.get("domain") or "").lower().removeprefix("www.")
            if item_domain == domain or item_domain.endswith("." + domain):
                rank = item.get("rank_group")
                if rank is not None and (best is None or rank < best):
                    best = rank
    return {
        "keyword": meta.get("keyword"),
        "location_id": meta.get("location_id"),
        "maps_position": maps,
        "organic_position": best if best is not None and best <= 10 else None,
        "best_organic_anywhere": best,
    }


def main():
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    args = sys.argv[1:]
    out = None
    if "--out" in args:
        i = args.index("--out")
        out = args[i + 1] if i + 1 < len(args) else sys.exit("--out needs a file path")
        del args[i:i + 2]
    domain, business, *paths = args
    rows = []
    for path in paths:
        try:
            rows.append(parse(load(path), domain, business))
        except (OSError, ValueError, KeyError) as exc:
            print(f"skipped {path}: {exc}", file=sys.stderr)
    if out:
        with open(out, "w", encoding="utf-8") as f:
            json.dump(rows, f, indent=1)
        print(f"Saved {out} ({len(rows)} rows)")
    else:
        json.dump(rows, sys.stdout, indent=1)


if __name__ == "__main__":
    main()
