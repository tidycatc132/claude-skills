#!/usr/bin/env python3
"""Merge saved ClickUp tool results into the readback file check_list.py and page_subtasks.py read.

  readback.py --out <slug>-clickup-readback.json --list-id ID [--list-url URL]
              --get-many FILE [FILE ...] [--filter FILE ...]

--get-many  each file is the verbatim result of a `task.get_many` call made with the query in
            references/executing.md: a JSON array of {id, name, parent, status, start_date, due_date, tags, waits_on}
--filter    each file is a verbatim `clickup_filter_tasks` result ({"tasks": [{id, assignees, ...}]}), used only
            for assignees
Prints `READBACK: <n> tasks` and exits 0; exit 2 on unreadable input.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load(p: str):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    ap.add_argument("--list-id", required=True)
    ap.add_argument("--list-url", default="")
    ap.add_argument("--get-many", nargs="+", required=True)
    ap.add_argument("--filter", nargs="*", default=[])
    a = ap.parse_args()
    try:
        rows = []
        for f in a.get_many:
            d = load(f)
            if isinstance(d, dict):
                d = [x.get("data", x) for x in d.get("tasks", [])]
            rows += d
        assignees = {}
        for f in a.filter:
            d = load(f)
            for t in d.get("tasks", d if isinstance(d, list) else []):
                assignees[t["id"]] = [x if not isinstance(x, dict) else x.get("username") or x.get("id")
                                      for x in (t.get("assignees") or [])]
    except (OSError, json.JSONDecodeError, AttributeError, KeyError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    tasks, seen = [], set()
    for r in rows:
        if not r or r.get("id") in seen:
            continue
        seen.add(r["id"])
        st = r.get("status")
        tasks.append({"id": r["id"], "name": r.get("name", ""), "parent": r.get("parent"),
                      "status": st.get("status") if isinstance(st, dict) else st,
                      "start_date": r.get("start_date"), "due_date": r.get("due_date"),
                      "tags": [t if isinstance(t, str) else t.get("name") for t in (r.get("tags") or [])],
                      "assignees": assignees.get(r["id"], r.get("assignees") or []),
                      "waits_on": r.get("waits_on") or []})
    Path(a.out).write_text(json.dumps({"list_id": a.list_id, "list_url": a.list_url, "tasks": tasks},
                                      indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {a.out}")
    print(f"READBACK: {len(tasks)} tasks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
