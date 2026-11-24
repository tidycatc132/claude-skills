#!/usr/bin/env python3
"""Turn the build plan plus one client's details into an exact list of ClickUp operations.

Writes, in --out-dir (default clickup/<slug>/):
  <slug>-clickup-ops.json      every item to create, the date batches and the dependencies, in run order
  <slug>-clickup-preview.md    the same as a readable table, for the person to approve

Nothing is sent to ClickUp. Exit 0 and `PLAN: OK` when the plan is valid, exit 2 on bad input.

Usage:
  plan_build.py --client "Client Name" --code ABC --kickoff 2026-11-30 --paid-media no
                [--person AM="Name"] ... [--test-run] [--tag NAME] ...
                [--holiday YYYY-MM-DD] ... [--no-default-holidays] [--out-dir DIR] [--plan FILE]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_PLAN = HERE.parent / "references" / "build-plan.json"
ROLE_KEYS = ["AM", "PM", "SEO", "Editor", "Designer", "Developer", "PaidMedia"]


def fail(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(2)


def slugify(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s or "client"


def nth_weekday(year: int, month: int, weekday: int, n: int) -> dt.date:
    d = dt.date(year, month, 1)
    d += dt.timedelta(days=(weekday - d.weekday()) % 7)
    return d + dt.timedelta(weeks=n - 1)


def last_weekday(year: int, month: int, weekday: int) -> dt.date:
    d = dt.date(year + (month == 12), month % 12 + 1, 1) - dt.timedelta(days=1)
    return d - dt.timedelta(days=(d.weekday() - weekday) % 7)


def observed(d: dt.date) -> dt.date:
    if d.weekday() == 5:
        return d - dt.timedelta(days=1)
    if d.weekday() == 6:
        return d + dt.timedelta(days=1)
    return d


def default_holidays(year: int) -> set[dt.date]:
    return {
        observed(dt.date(year, 1, 1)),
        last_weekday(year, 5, 0),          # Memorial Day
        observed(dt.date(year, 7, 4)),
        nth_weekday(year, 9, 0, 1),        # Labor Day
        nth_weekday(year, 11, 3, 4),       # Thanksgiving
        observed(dt.date(year, 12, 25)),
    }


def business_days(start: dt.date, count: int, holidays: set[dt.date]) -> list[dt.date]:
    days, d = [], start
    while len(days) < count:
        if d.weekday() < 5 and d not in holidays:
            days.append(d)
        d += dt.timedelta(days=1)
    return days


def ms_at(d: dt.date, hour: int) -> int:
    return int(dt.datetime(d.year, d.month, d.day, hour, tzinfo=dt.timezone.utc).timestamp() * 1000)


def describe(task: dict, ctx: dict, role_pos: str) -> str:
    fill = lambda s: s.format(**ctx)
    lines = [f"**Plan ref:** {task['ref']} ({task['week']})", f"**Who:** {role_pos}"]
    lines.append(f"**Claude skill:** {task['skill'] or 'none, you do this yourself'}")
    if task.get("message"):
        lines += ["", "**Message to type into Claude:**", "", f"> {fill(task['message'])}"]
    lines += ["", f"**Done when:** {fill(task['done_when'])}"]
    if task.get("paid_media"):
        lines += ["", "Created because paid media is signed."]
    if ctx["test_run"]:
        lines += ["", "TEST RUN: log any problem as a subtask of `TEST · Issues log`."]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--client", required=True)
    ap.add_argument("--code", required=True, help="three-character client code, with or without brackets")
    ap.add_argument("--kickoff", required=True, help="Day 1, YYYY-MM-DD, a business day")
    ap.add_argument("--paid-media", required=True, choices=["yes", "no"])
    ap.add_argument("--person", action="append", default=[], help="ROLE=Name, ROLE one of " + ", ".join(ROLE_KEYS))
    ap.add_argument("--test-run", action="store_true")
    ap.add_argument("--tag", action="append", default=[])
    ap.add_argument("--holiday", action="append", default=[])
    ap.add_argument("--no-default-holidays", action="store_true")
    ap.add_argument("--out-dir")
    ap.add_argument("--plan", default=str(DEFAULT_PLAN))
    a = ap.parse_args()

    plan = json.loads(Path(a.plan).read_text(encoding="utf-8"))
    code = a.code.strip().strip("[]").upper()
    if not re.fullmatch(r"[A-Z0-9]{3}", code):
        fail(f"client code must be three letters or digits, got '{a.code}'")
    client = a.client.strip()
    if not client:
        fail("client name is empty")
    try:
        kickoff = dt.date.fromisoformat(a.kickoff)
    except ValueError:
        fail(f"kickoff date must be YYYY-MM-DD, got '{a.kickoff}'")
    holidays: set[dt.date] = set()
    if not a.no_default_holidays:
        for y in range(kickoff.year, kickoff.year + 2):
            holidays |= default_holidays(y)
    for h in a.holiday:
        try:
            holidays.add(dt.date.fromisoformat(h))
        except ValueError:
            fail(f"holiday must be YYYY-MM-DD, got '{h}'")
    if kickoff.weekday() >= 5 or kickoff in holidays:
        fail(f"kickoff {kickoff} is not a business day")

    people: dict[str, str | None] = {k: None for k in ROLE_KEYS}
    for p in a.person:
        if "=" not in p:
            fail(f"--person must be ROLE=Name, got '{p}'")
        k, v = p.split("=", 1)
        match = [r for r in ROLE_KEYS if r.lower() == k.strip().lower()]
        if not match:
            fail(f"unknown role '{k}' (use one of {', '.join(ROLE_KEYS)})")
        v = v.strip()
        people[match[0]] = None if v.lower() in ("", "none", "-") else v

    paid = a.paid_media == "yes"
    schedule = "test" if a.test_run else "plan"
    tasks = [t for t in plan["tasks"] if paid or not t.get("paid_media")]
    by_ref = {t["ref"]: t for t in tasks}
    all_refs = {t["ref"] for t in plan["tasks"]}
    errors: list[str] = []
    for t in tasks:
        for w in t["waits_on"]:
            if w not in by_ref:
                errors.append(f"{t['ref']} waits on {w}, which " + ("is not created in this run" if w in all_refs else "does not exist"))
    # dates
    s_key, d_key = ("test_start", "test_due") if schedule == "test" else ("start", "due")
    last = max(t[d_key] for t in tasks)
    days = business_days(kickoff, last, holidays)
    hour = plan.get("date_hour_utc", 9)
    for t in tasks:
        if t[d_key] < t[s_key]:
            errors.append(f"{t['ref']} is due before it starts")
        for w in t["waits_on"]:
            if w in by_ref and by_ref[w][d_key] > t[d_key]:
                errors.append(f"{t['ref']} is due (D{t[d_key]}) before {w}, which it waits on (D{by_ref[w][d_key]})")
    # cycles
    seen: dict[str, int] = {}

    def visit(r: str, stack: tuple) -> None:
        if seen.get(r) == 2:
            return
        if seen.get(r) == 1:
            errors.append("dependency cycle: " + " -> ".join(stack + (r,)))
            return
        seen[r] = 1
        for w in by_ref[r]["waits_on"]:
            if w in by_ref:
                visit(w, stack + (r,))
        seen[r] = 2

    for r in by_ref:
        visit(r, ())
    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        return 2

    slug = slugify(client)
    list_client = f"TEST {client}" if a.test_run else client
    list_name = plan["list_name"].format(code=code, client=list_client)
    tags = sorted({x.strip().lower() for x in a.tag if x.strip()} | ({"test-run"} if a.test_run else set()))
    ctx = {"client": client, "code": f"[{code}]", "kickoff": kickoff.isoformat(), "test_run": a.test_run}
    st = plan["statuses"]
    roles = plan["roles"]
    groups = {g["id"]: g for g in plan["groups"]}

    items: list[dict] = []

    def item(**kw) -> dict:
        kw.setdefault("tags", list(tags))
        items.append(kw)
        return kw

    def dated(key: str, s: int, d: int) -> dict:
        return {"start_day": s, "due_day": d, "start_date": days[s - 1].isoformat(), "due_date": days[d - 1].isoformat(),
                "start_ms": ms_at(days[s - 1], hour), "due_ms": ms_at(days[d - 1], hour)}

    # level 0: groups (in plan order, only those with tasks), then top-level tasks
    used_groups = [g for g in plan["groups"] if any(t["group"] == g["id"] for t in tasks)]
    for g in used_groups:
        kids = [t for t in tasks if t["group"] == g["id"]]
        s, d = min(k[s_key] for k in kids), max(k[d_key] for k in kids)
        text = f"Groups {g['summary']}.\n\nDone when every subtask is closed."
        if g["id"] == "PAID":
            text = f"Groups {g['summary']}. Created because paid media is signed.\n\nDone when every subtask is closed."
        item(key=f"G:{g['id']}", ref=g["id"], level=0, parent_key=None, name=g["name"], kind="group",
             task_type=plan["task_types"]["group"], status=st["ready"], role=None, assignee=None,
             position=None, department=None, markdown_description=text, **dated(g["id"], s, d))
    if a.test_run:
        il = plan["issues_log"]
        item(key="ISSUES", ref="ISSUES", level=0, parent_key=None, name=il["name"], kind="issues_log", task_type=None,
             status=st["ready"], role=None, assignee=None, position=None, department=None,
             markdown_description=il["description"], start_day=None, due_day=None, start_date=None, due_date=None,
             start_ms=None, due_ms=None)
    for t in tasks:
        r = roles[t["role"]]
        status = st["waiting"] if t["waits_on"] else st["ready"]
        kind = t.get("kind", "step")
        item(key=t["ref"], ref=t["ref"], level=0 if t["group"] is None else 1,
             parent_key=None if t["group"] is None else f"G:{t['group']}", name=t["name"], kind=kind,
             task_type=plan["task_types"]["milestone"] if kind == "milestone" else None, status=status,
             role=t["role"], assignee=people[t["role"]], position=r["position"], department=r["department"],
             markdown_description=describe(t, ctx, r["position"]), **dated(t["ref"], t[s_key], t[d_key]))
        for i, sub in enumerate(t.get("subtasks", []), 1):
            sub = sub if isinstance(sub, dict) else {"name": sub, "role": t["role"]}
            sr = roles[sub["role"]]
            item(key=f"{t['ref']}.{i}", ref=f"{t['ref']}.{i}", level=2 if t["group"] else 1, parent_key=t["ref"],
                 name=sub["name"], kind="substep", task_type=None, status=status, role=sub["role"],
                 assignee=people[sub["role"]], position=sr["position"], department=sr["department"],
                 markdown_description=f"Part of **{t['name']}** (plan ref {t['ref']}). Who: {sr['position']}.",
                 **dated(t["ref"], t[s_key], t[d_key]))
    items.sort(key=lambda x: x["level"])  # stable: creation order is level by level

    batches: dict[tuple, list] = {}
    for it in items:
        if it["due_ms"] is not None:
            batches.setdefault((it["start_ms"], it["due_ms"], it["start_date"], it["due_date"]), []).append(it["key"])
    date_batches = [{"start_date": k[2], "due_date": k[3], "start_ms": k[0], "due_ms": k[1], "keys": v}
                    for k, v in sorted(batches.items(), key=lambda kv: (kv[0][1], kv[0][0]))]

    # dependencies, upstream first (by due day, then plan order)
    order = {t["ref"]: i for i, t in enumerate(tasks)}
    deps = [{"task": t["ref"], "waits_on": w} for t in sorted(tasks, key=lambda t: (t[d_key], order[t["ref"]]))
            for w in t["waits_on"]]

    missing_people = [k for k in ROLE_KEYS if people[k] is None and any(it["role"] == k for it in items)]
    counts = {k: sum(1 for it in items if it["kind"] == k) for k in ("group", "milestone", "step", "substep", "issues_log")}
    ops = {
        "version": 1, "client": client, "slug": slug, "code": code, "kickoff": kickoff.isoformat(),
        "schedule": schedule, "paid_media": paid, "test_run": a.test_run, "tags": tags,
        "list": {"name": list_name, "space": plan["location"]["space"], "folder": plan["location"]["folder"]},
        "people": people, "roles_without_person": missing_people,
        "holidays_skipped": sorted(h.isoformat() for h in holidays if kickoff <= h <= days[-1]),
        "last_day": days[-1].isoformat(), "counts": {**counts, "items": len(items), "dependencies": len(deps)},
        "items": items, "date_batches": date_batches, "dependencies": deps,
    }

    out = Path(a.out_dir) if a.out_dir else Path("clickup") / slug
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{slug}-clickup-ops.json").write_text(json.dumps(ops, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    name_of = {it["key"]: it["name"] for it in items}
    md = [f"# ClickUp plan preview: {client}", "",
          f"- List: `{list_name}` in {plan['location']['space']} > {plan['location']['folder']}",
          f"- Kickoff (Day 1): {kickoff.isoformat()}; last day {days[-1].isoformat()}; schedule `{schedule}`",
          f"- Paid media: {'yes' if paid else 'no'}; tags: {', '.join(tags) if tags else 'none'}",
          f"- Holidays skipped: {', '.join(ops['holidays_skipped']) or 'none'}",
          f"- Items: {len(items)} ({counts['group']} groups, {counts['milestone']} milestones, {counts['step']} steps, "
          f"{counts['substep']} sub-steps{', 1 issues log' if counts['issues_log'] else ''}); dependencies: {len(deps)}",
          f"- No assignee for: {', '.join(roles[k]['position'] for k in missing_people) or 'nobody (every role has a person)'}",
          "", "| Ref | Task | Under | Who | Start | Due | Waits on | Status |", "|---|---|---|---|---|---|---|---|"]
    for it in items:
        if it["kind"] == "substep":
            continue
        waits = ", ".join(by_ref[it["ref"]]["waits_on"]) if it["ref"] in by_ref else ""
        who = (it["assignee"] or it["position"] or "") if it["kind"] != "group" else ""
        md.append(f"| {it['ref']} | {it['name']} | {name_of.get(it['parent_key'], '') if it['parent_key'] else ''} | {who} | "
                  f"{it['start_date'] or ''} | {it['due_date'] or ''} | {waits} | {it['status']} |")
    subs = [it for it in items if it["kind"] == "substep"]
    if subs:
        md += ["", "Sub-steps: " + "; ".join(f"{it['name']} (under {name_of[it['parent_key']]})" for it in subs) + "."]
    md += ["", "PLAN: OK"]
    (out / f"{slug}-clickup-preview.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"wrote {out / (slug + '-clickup-ops.json')}")
    print(f"wrote {out / (slug + '-clickup-preview.md')}")
    print(f"list: {list_name}")
    print(f"items: {len(items)} | groups {counts['group']} | milestones {counts['milestone']} | steps {counts['step']} | "
          f"sub-steps {counts['substep']} | issues log {counts['issues_log']} | dependencies {len(deps)} | date batches {len(date_batches)}")
    print(f"days: {kickoff.isoformat()} to {days[-1].isoformat()} ({schedule} schedule)")
    print("no assignee for: " + (", ".join(missing_people) or "none"))
    print("PLAN: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
