#!/usr/bin/env python3
"""Check a created ClickUp list against the plan, and write the plan record.

Inputs:
  <ops.json>       written by plan_build.py
  <readback.json>  what ClickUp holds now: {"list_id", "list_url", "tasks": [...]}, each task
                   {"id", "name", "parent", "status", "start_date", "due_date", "tags", "assignees", "waits_on"}
                   (dates as millisecond strings or null; "parent" a task id or null; "waits_on" task ids)

Writes <slug>-clickup-plan.md beside ops.json (or --out) and prints the same check table.
Ends with `RESULT: PASS` (exit 0) or `RESULT: FAIL` (exit 1). Exit 2 on unreadable input.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

PAGE_PREFIX = "Page: "


def utc_day(ms) -> str | None:
    if ms in (None, "", 0, "0"):
        return None
    return dt.datetime.fromtimestamp(int(ms) / 1000, tz=dt.timezone.utc).date().isoformat()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ops")
    ap.add_argument("readback")
    ap.add_argument("--out")
    ap.add_argument("--ids-out", help="also write {list_id, ids: {item key: task id}} for the tasks found")
    a = ap.parse_args()
    try:
        ops = json.loads(Path(a.ops).read_text(encoding="utf-8"))
        rb = json.loads(Path(a.readback).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    tasks = rb.get("tasks", rb if isinstance(rb, list) else [])
    by_id = {t["id"]: t for t in tasks}
    items = ops["items"]
    pkey = {it["key"]: it for it in items}

    # match planned items to tasks by (name, parent name)
    def parent_name(t):
        p = t.get("parent")
        return by_id[p]["name"] if p in by_id else None

    found: dict[str, dict] = {}
    problems: dict[str, list[str]] = {k: [] for k in ("exist", "extra", "parent", "dates", "status", "tags", "assignees", "deps")}
    pool: dict[tuple, list] = {}
    for t in tasks:
        pool.setdefault((t["name"], parent_name(t)), []).append(t)
    for it in items:
        want_parent = pkey[it["parent_key"]]["name"] if it["parent_key"] else None
        hits = pool.get((it["name"], want_parent), [])
        if not hits:
            loose = [t for t in tasks if t["name"] == it["name"]]
            if loose:
                problems["parent"].append(f"{it['ref']} {it['name']}: under '{parent_name(loose[0]) or 'top level'}', planned under '{want_parent or 'top level'}'")
                found[it["key"]] = loose[0]
            else:
                problems["exist"].append(f"{it['ref']} {it['name']} is missing")
            continue
        if len(hits) > 1:
            problems["exist"].append(f"{it['ref']} {it['name']} exists {len(hits)} times")
        found[it["key"]] = hits[0]

    matched_ids = {t["id"] for t in found.values()}
    w25 = found.get("W2-5", {}).get("id")
    for t in tasks:
        if t["id"] in matched_ids:
            continue
        if t["name"].startswith(PAGE_PREFIX) and t.get("parent") == w25:
            continue
        problems["extra"].append(f"{t['name']} ({t['id']}) is not in the plan")

    for it in items:
        t = found.get(it["key"])
        if not t:
            continue
        for fld, want in (("start_date", it["start_date"]), ("due_date", it["due_date"])):
            got = utc_day(t.get(fld))
            if want != got:
                problems["dates"].append(f"{it['ref']} {it['name']}: {fld} {got or 'empty'}, planned {want or 'empty'}")
        if (t.get("status") or "").lower() != it["status"].lower():
            problems["status"].append(f"{it['ref']} {it['name']}: status '{t.get('status')}', planned '{it['status']}'")
        have = {x.lower() for x in (t.get("tags") or [])}
        miss = [x for x in it["tags"] if x not in have]
        if miss:
            problems["tags"].append(f"{it['ref']} {it['name']}: missing tag {', '.join(miss)}")
        if it.get("assignee") and not t.get("assignees"):
            problems["assignees"].append(f"{it['ref']} {it['name']}: no assignee, planned {it['assignee']}")

    id_of = {k: t["id"] for k, t in found.items()}
    if a.ids_out:
        Path(a.ids_out).write_text(json.dumps({"list_id": rb.get("list_id"), "ids": id_of}, indent=1) + "\n", encoding="utf-8")
    want_deps = {(d["task"], d["waits_on"]) for d in ops["dependencies"]}
    for task_ref, dep_ref in sorted(want_deps):
        if task_ref in id_of and dep_ref in id_of:
            if id_of[dep_ref] not in (found[task_ref].get("waits_on") or []):
                problems["deps"].append(f"{task_ref} does not wait on {dep_ref}")
    ref_of = {v: k for k, v in id_of.items()}
    for k, t in found.items():
        for w in t.get("waits_on") or []:
            if (k, ref_of.get(w)) not in want_deps:
                problems["deps"].append(f"{k} waits on {ref_of.get(w, w)}, which the plan does not have")

    labels = [("exist", "Every planned task exists once", len(items)),
              ("extra", "No tasks outside the plan (sitemap page subtasks allowed)", len(tasks)),
              ("parent", "Each task sits under its planned parent", len(items)),
              ("dates", "Start and due dates match the plan (UTC day)", len(items)),
              ("status", "Starting statuses match", len(items)),
              ("tags", "Tags present", len(items)),
              ("assignees", "Named people are assigned", sum(1 for it in items if it.get("assignee"))),
              ("deps", "Waiting-on dependencies match", len(want_deps))]
    rows = ["| Check | Result | Checked | Detail |", "|---|---|---|---|"]
    ok = True
    for k, label, n in labels:
        p = problems[k]
        ok &= not p
        detail = "; ".join(p[:6]) + (f"; and {len(p) - 6} more" if len(p) > 6 else "")
        rows.append(f"| {label} | {'PASS' if not p else 'FAIL'} | {n} | {detail} |")
    pages = [t for t in tasks if t["name"].startswith(PAGE_PREFIX) and t.get("parent") == w25]

    list_url = rb.get("list_url") or ""
    md = [f"# ClickUp plan: {ops['client']}", "",
          f"- List: [{ops['list']['name']}]({list_url})" if list_url else f"- List: {ops['list']['name']}",
          f"- List ID: {rb.get('list_id', 'unknown')}",
          f"- Kickoff (Day 1): {ops['kickoff']}; schedule `{ops['schedule']}`; paid media {'yes' if ops['paid_media'] else 'no'}",
          f"- Tasks read back: {len(tasks)} ({len(pages)} sitemap page subtasks)", "", "## Checks", ""] + rows
    md += ["", "## Tasks", "", "| Ref | Task | Due | Link |", "|---|---|---|---|"]
    for it in items:
        t = found.get(it["key"])
        link = f"[open](https://app.clickup.com/t/{t['id']})" if t else "missing"
        md.append(f"| {it['ref']} | {it['name']} | {it['due_date'] or ''} | {link} |")
    for t in pages:
        md.append(f"| W2-5 page | {t['name']} | {utc_day(t.get('due_date')) or ''} | [open](https://app.clickup.com/t/{t['id']}) |")
    md += ["", f"RESULT: {'PASS' if ok else 'FAIL'}"]
    out = Path(a.out) if a.out else Path(a.ops).with_name(f"{ops['slug']}-clickup-plan.md")
    out.write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(rows))
    print(f"wrote {out}")
    print(f"RESULT: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
