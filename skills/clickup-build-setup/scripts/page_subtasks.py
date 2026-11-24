#!/usr/bin/env python3
"""Plan one subtask per sitemap page under "Write the sitemap pages" (plan ref W2-5).

Inputs:
  --report    a site-structure-optimizer architecture report (markdown) with a table under a
              heading named `URL map`, columns `Page`, `URL`, `Parent`, `Nav location`, `Priority`
  --ops       the build's <slug>-clickup-ops.json (plan_build.py)
  --readback  the build's readback JSON (same shape check_list.py reads), to find W2-5 and the
              page subtasks that already exist

Writes <slug>-page-subtasks.json beside --ops: {"parent_id", "parent_name", "create": [...], "skipped": [...]}.
Every page except the homepage gets `Page: <Page> (<URL>)`; a page already under W2-5 is skipped.
Prints a table and `PAGES: <n> to create, <m> already there`. Exit 2 on bad input.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def split_row(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def url_map(text: str) -> list[dict]:
    lines, heading, i = text.split("\n"), "", 0
    while i < len(lines):
        ln = lines[i]
        if re.match(r"^#{1,6} ", ln):
            heading = ln.lstrip("#").strip()
        if (("url map" in heading.lower() or "url taxonomy" in heading.lower()) and ln.strip().startswith("|") and i + 1 < len(lines)
                and re.match(r"^\s*\|?\s*:?-{3,}", lines[i + 1])):
            header = [h.lower() for h in split_row(ln)]
            if "page" in header and "url" in header:
                ip, iu = header.index("page"), header.index("url")
                rows, i = [], i + 2
                while i < len(lines) and lines[i].strip().startswith("|"):
                    r = split_row(lines[i])
                    if len(r) > max(ip, iu) and r[iu]:
                        page = re.sub(r"\s*\(not in SOW scope\)", "", r[ip].replace("`", "")).strip()
                        rows.append({"page": page, "url": r[iu].strip("`")})
                    i += 1
                return rows
        i += 1
    return []


def is_home(row: dict) -> bool:
    path = re.sub(r"^https?://[^/]+", "", row["url"]) or "/"
    return path == "/" or row["page"].lower().strip() in ("home", "homepage", "home page")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--report", required=True)
    ap.add_argument("--ops", required=True)
    ap.add_argument("--readback", required=True)
    a = ap.parse_args()
    try:
        text = Path(a.report).read_text(encoding="utf-8")
        ops = json.loads(Path(a.ops).read_text(encoding="utf-8"))
        rb = json.loads(Path(a.readback).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    rows = url_map(text)
    if not rows:
        print("ERROR: no `URL map` table with Page and URL columns in the report", file=sys.stderr)
        return 2
    item = next((it for it in ops["items"] if it["key"] == "W2-5"), None)
    tasks = rb.get("tasks", [])
    parent = next((t for t in tasks if item and t["name"] == item["name"]), None)
    if not item or not parent:
        print("ERROR: 'Write the sitemap pages' (W2-5) is not in the readback; set up the list first", file=sys.stderr)
        return 2
    existing = {t["name"] for t in tasks if t.get("parent") == parent["id"]}
    create, skipped, seen = [], [], set()
    for r in rows:
        if is_home(r) or r["url"] in seen:
            continue
        seen.add(r["url"])
        name = f"Page: {r['page']} ({r['url']})"
        if name in existing:
            skipped.append(name)
            continue
        create.append({"name": name, "parent_id": parent["id"], "status": item["status"], "assignee": item["assignee"],
                       "tags": item["tags"], "position": item["position"], "department": item["department"], "start_date": item["start_date"], "due_date": item["due_date"],
                       "start_ms": item["start_ms"], "due_ms": item["due_ms"],
                       "markdown_description": f"Write the **{r['page']}** page (`{r['url']}`) from its content brief. "
                                              "Done when its article.md and metadata.md are saved."})
    out = Path(a.ops).with_name(f"{ops['slug']}-page-subtasks.json")
    out.write_text(json.dumps({"parent_id": parent["id"], "parent_name": item["name"], "create": create,
                               "skipped": skipped}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print("| Subtask | Action |\n|---|---|")
    for c in create:
        print(f"| {c['name']} | create |")
    for s in skipped:
        print(f"| {s} | already there |")
    print(f"wrote {out}")
    print(f"PAGES: {len(create)} to create, {len(skipped)} already there")
    return 0


if __name__ == "__main__":
    sys.exit(main())
