#!/usr/bin/env python3
"""Turn a sub-agent progress report into an ordered plan of ClickUp operations.

Usage
  python3 plan_ops.py agent_update.json [--out clickup_ops.json] [--preview clickup_sync_preview.md]
                      [--status-map status_map.json] [--validate]

Input  agent_update.json  (see ../references/input-format.md)
Output clickup_ops.json   {"generated_at", "source_agent", "reported_at", "ops": [...], "warnings": [...]}
       each op: {"seq", "op", "tool", "task_ref", "task_id", "args", "reason", "requires"}
       op enum: verify_task | add_comment | update_status | set_due_date | attach_file |
                upload_file | add_time_entry | add_tag | create_task
       clickup_sync_preview.md  the same plan as a human-readable checklist

Exit codes: 0 ok, 2 input invalid (messages on stderr). --validate checks the input only.
Standard library only. Nothing here talks to ClickUp; the manager agent executes the ops.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

OUTCOMES = ["completed", "in_progress", "blocked", "needs_review", "cancelled", "no_change"]
DEFAULT_STATUS_MAP = {
    "completed": ["complete", "done", "closed"],
    "in_progress": ["in progress", "in development", "active", "doing"],
    "blocked": ["blocked", "on hold", "waiting"],
    "needs_review": ["review", "in review", "ready for review", "qa"],
    "cancelled": ["cancelled", "canceled", "closed"],
    "no_change": [],
}
OUTCOME_LABEL = {
    "completed": "Completed",
    "in_progress": "In progress",
    "blocked": "Blocked",
    "needs_review": "Needs review",
    "cancelled": "Cancelled",
    "no_change": "No status change",
}
PRIORITIES = {"urgent", "high", "normal", "low"}
URL_RE = re.compile(r"https?://[^/]*clickup\.com/t/(?:\d+/)?([A-Za-z0-9_-]+)", re.I)
CUSTOM_ID_RE = re.compile(r"^[A-Z][A-Z0-9]*-\d+$")
RAW_ID_RE = re.compile(r"^(?=[a-z0-9]{6,}$)(?=.*\d)")  # ClickUp ids mix letters and digits; a plain word is a name
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$")


def parse_task_ref(ref: str) -> str | None:
    """Return a ClickUp task id for a URL, custom id or raw id; None when the ref is a name."""
    ref = (ref or "").strip()
    m = URL_RE.search(ref)
    if m:
        return m.group(1)
    if CUSTOM_ID_RE.match(ref) or RAW_ID_RE.match(ref):
        return ref
    return None


def normalise(data: dict) -> None:
    """Accept harmless transcription variants in place: ISO 'T' timestamps, numeric strings."""
    if isinstance(data.get("reported_at"), str):
        data["reported_at"] = data["reported_at"].strip().replace("T", " ")[:16]
    for it in data.get("items", []) if isinstance(data.get("items"), list) else []:
        if not isinstance(it, dict):
            continue
        for k in ("time_spent_minutes", "progress_percent"):
            v = it.get(k)
            if isinstance(v, str):
                try:
                    it[k] = float(v.strip().rstrip("m%").strip())
                except ValueError:
                    pass
        if isinstance(it.get("blockers"), str):
            it["blockers"] = [it["blockers"]]
        if isinstance(it.get("tags"), str):
            it["tags"] = [it["tags"]]
        if isinstance(it.get("due_date"), str):
            it["due_date"] = it["due_date"].strip().replace("T", " ")[:16]


def validate(data: dict) -> list[str]:
    errs: list[str] = []
    if not isinstance(data, dict):
        return ["top level must be an object"]
    normalise(data)
    if not str(data.get("source_agent", "")).strip():
        errs.append("source_agent is required (the sub-agent's name)")
    rep = str(data.get("reported_at", "")).strip()
    if not (DATE_RE.match(rep) or DATETIME_RE.match(rep)):
        errs.append("reported_at must be YYYY-MM-DD or YYYY-MM-DD HH:MM")
    items = data.get("items", [])
    new_tasks = data.get("new_tasks", [])
    if not isinstance(items, list) or not isinstance(new_tasks, list):
        return errs + ["items and new_tasks must be lists"]
    if not items and not new_tasks:
        errs.append("nothing to do: items and new_tasks are both empty")
    for i, it in enumerate(items):
        where = f"items[{i}]"
        if not isinstance(it, dict):
            errs.append(f"{where} must be an object")
            continue
        if not str(it.get("task_ref", "")).strip():
            errs.append(f"{where}.task_ref is required (task URL, custom id, id or exact task name)")
        if it.get("outcome") not in OUTCOMES:
            errs.append(f"{where}.outcome must be one of {OUTCOMES}")
        if not str(it.get("summary", "")).strip():
            errs.append(f"{where}.summary is required (one or two sentences)")
        if it.get("outcome") == "blocked" and not it.get("blockers"):
            errs.append(f"{where}: a blocked outcome needs a non-empty blockers list")
        tsm = it.get("time_spent_minutes")
        if tsm is not None and (not isinstance(tsm, (int, float)) or tsm <= 0):
            errs.append(f"{where}.time_spent_minutes must be a positive number")
        if it.get("due_date") and not DATE_RE.match(str(it["due_date"])) and not DATETIME_RE.match(str(it["due_date"])):
            errs.append(f"{where}.due_date must be YYYY-MM-DD or YYYY-MM-DD HH:MM")
        for j, a in enumerate(it.get("artifacts", []) or []):
            if not isinstance(a, dict) or not a.get("name") or not (a.get("url") or a.get("path")):
                errs.append(f"{where}.artifacts[{j}] needs name and either url or path")
    for i, nt in enumerate(new_tasks):
        where = f"new_tasks[{i}]"
        if not isinstance(nt, dict) or not str(nt.get("name", "")).strip():
            errs.append(f"{where}.name is required")
            continue
        if not (nt.get("list_id") or data.get("default_list_id") or nt.get("parent_ref")):
            errs.append(f"{where}: give list_id, a top-level default_list_id, or a parent_ref")
        if nt.get("priority") and nt["priority"] not in PRIORITIES:
            errs.append(f"{where}.priority must be one of {sorted(PRIORITIES)}")
    return errs


def comment_text(agent: str, reported_at: str, it: dict) -> str:
    lines = [f"**Update from {agent}** ({reported_at})", "", f"**Outcome:** {OUTCOME_LABEL[it['outcome']]}"]
    if it.get("progress_percent") is not None:
        lines[-1] += f" ({int(it['progress_percent'])}%)"
    lines += ["", str(it["summary"]).strip()]
    if it.get("details"):
        lines += ["", str(it["details"]).strip()]
    if it.get("blockers"):
        lines += ["", "**Blockers:**"] + [f"- {b}" for b in it["blockers"]]
    if it.get("artifacts"):
        lines += ["", "**Deliverables:**"]
        for a in it["artifacts"]:
            lines.append(f"- [{a['name']}]({a['url']})" if a.get("url") else f"- {a['name']} (attached)")
    if it.get("time_spent_minutes"):
        m = int(it["time_spent_minutes"])
        lines += ["", f"Time spent: {m // 60}h {m % 60:02d}m" if m >= 60 else f"Time spent: {m}m"]
    lines += ["", "_Posted by the managing agent on the sub-agent's behalf._"]
    return "\n".join(lines)


def time_entry_start(reported_at: str, minutes: int) -> str:
    base = reported_at if DATETIME_RE.match(reported_at) else f"{reported_at} 09:00"
    end = dt.datetime.strptime(base, "%Y-%m-%d %H:%M")
    return (end - dt.timedelta(minutes=minutes)).strftime("%Y-%m-%d %H:%M")


class Plan:
    def __init__(self) -> None:
        self.ops: list[dict] = []
        self.warnings: list[str] = []

    def add(self, op: str, tool: str, task_ref: str, task_id: str | None, args: dict, reason: str, requires: str = "") -> None:
        self.ops.append({
            "seq": len(self.ops) + 1, "op": op, "tool": tool, "task_ref": task_ref,
            "task_id": task_id, "args": args, "reason": reason, "requires": requires,
        })


def plan_item(p: Plan, agent: str, reported_at: str, it: dict, status_map: dict) -> None:
    ref = str(it["task_ref"]).strip()
    tid = parse_task_ref(ref)
    requires = "" if tid else "resolve"
    if tid:
        p.add("verify_task", "clickup_get_task", ref, tid, {"task_id": tid, "expand_statuses": True},
              "confirm the task exists and learn its valid statuses before writing")
    else:
        p.add("verify_task", "clickup_search", ref, None,
              {"keywords": ref, "filters": {"asset_types": ["task"]}},
              "task_ref is a name, not an id: find the task and fill task_id into the ops below", "resolve")
        p.warnings.append(f"'{ref}' is not a task id or URL; resolve it with clickup_search and confirm there is exactly one match before any write")
    p.add("add_comment", "clickup_create_comment", ref, tid,
          {"entity_type": "task", "entity_id": tid, "comment_text": comment_text(agent, reported_at, it), "notify_all": False},
          "record the sub-agent's report on the task", requires)
    candidates = status_map.get(it["outcome"], [])
    if candidates:
        p.add("update_status", "clickup_update_task", ref, tid,
              {"task_id": tid, "status_candidates": list(candidates)},
              f"outcome {it['outcome']}: set the first candidate that appears in available_statuses from verify_task; skip if none matches",
              requires or "status_choice")
    if it.get("due_date"):
        p.add("set_due_date", "clickup_update_task", ref, tid, {"task_id": tid, "due_date": str(it["due_date"])},
              "sub-agent reported a new target date", requires)
    for a in it.get("artifacts", []) or []:
        if a.get("url"):
            p.add("attach_file", "clickup_attach_task_file", ref, tid, {"task_id": tid, "file_url": a["url"]},
                  f"attach deliverable {a['name']}", requires)
        else:
            p.add("upload_file", "clickup_request_attachment_upload", ref, tid, {"task_id": tid, "file_path": a["path"], "file_name": a["name"]},
                  f"upload local deliverable {a['name']} (local files go through the upload request tool)", requires)
    if it.get("time_spent_minutes"):
        m = int(it["time_spent_minutes"])
        p.add("add_time_entry", "clickup_add_time_entry", ref, tid,
              {"task_id": tid, "start": time_entry_start(reported_at, m), "duration": f"{m}m", "description": f"{agent} (agent work)"},
              "log the sub-agent's time", requires)
    for tag in it.get("tags", []) or []:
        p.add("add_tag", "clickup_add_tag_to_task", ref, tid, {"task_id": tid, "tag_name": str(tag)},
              "tag requested in the report; the tag must already exist in the space", requires)


def plan_new_task(p: Plan, agent: str, reported_at: str, nt: dict, default_list: str | None) -> None:
    args: dict = {"name": str(nt["name"]).strip()}
    requires = ""
    if nt.get("list_id") or default_list:
        args["list_id"] = str(nt.get("list_id") or default_list)
    else:
        args["list_id"] = None
        requires = "list_id"
        p.warnings.append(f"new task '{args['name']}' has no list_id: read the parent task's list with clickup_get_task and fill it in")
    parent_ref = nt.get("parent_ref")
    if parent_ref:
        pid = parse_task_ref(str(parent_ref))
        args["parent"] = pid
        if not pid:
            requires = requires or "resolve"
            p.warnings.append(f"new task '{args['name']}' names parent '{parent_ref}' which is not an id; resolve it first")
    desc = str(nt.get("description", "")).strip()
    args["markdown_description"] = (desc + "\n\n" if desc else "") + f"_Created by the managing agent from {agent}'s report on {reported_at}._"
    for k in ("priority", "due_date", "status", "task_type", "time_estimate"):
        if nt.get(k):
            args[k] = str(nt[k])
    for k in ("assignees", "tags"):
        if nt.get(k):
            args[k] = [str(x) for x in nt[k]]
    p.add("create_task", "clickup_create_task", str(parent_ref or args.get("list_id") or ""), args.get("parent"), args,
          "sub-agent surfaced follow-up work that has no task yet", requires)


def write_preview(path: Path, data: dict, plan: Plan) -> None:
    lines = [f"# ClickUp sync plan: {data['source_agent']} ({data['reported_at']})", ""]
    if plan.warnings:
        lines += ["## Resolve before executing", ""] + [f"- {w}" for w in plan.warnings] + [""]
    by_ref: dict[str, list[dict]] = {}
    for op in plan.ops:
        by_ref.setdefault(op["task_ref"], []).append(op)
    for ref, ops in by_ref.items():
        head = ops[0]
        label = head["task_id"] or ref
        lines += [f"## {label}" + (f" ({ref})" if ref != label else ""), ""]
        for op in ops:
            summary = {
                "verify_task": "verify task and read valid statuses",
                "add_comment": "post comment",
                "update_status": "set status to first available of " + ", ".join(op["args"].get("status_candidates", [])),
                "set_due_date": "set due date " + str(op["args"].get("due_date")),
                "attach_file": "attach " + str(op["args"].get("file_url")),
                "upload_file": "upload " + str(op["args"].get("file_name")),
                "add_time_entry": "log time " + str(op["args"].get("duration")) + " from " + str(op["args"].get("start")),
                "add_tag": "add tag " + str(op["args"].get("tag_name")),
                "create_task": "create task '" + str(op["args"].get("name")) + "' in list " + str(op["args"].get("list_id")),
            }[op["op"]]
            flag = f" [needs: {op['requires']}]" if op["requires"] else ""
            lines.append(f"- [ ] {op['seq']}. {summary}{flag}")
        comment_ops = [o for o in ops if o["op"] == "add_comment"]
        if comment_ops:
            lines += ["", "<details><summary>comment text</summary>", "", comment_ops[0]["args"]["comment_text"], "", "</details>"]
        lines.append("")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("update", type=Path)
    ap.add_argument("--out", type=Path, default=Path("clickup_ops.json"))
    ap.add_argument("--preview", type=Path, default=Path("clickup_sync_preview.md"))
    ap.add_argument("--status-map", type=Path, help="JSON object outcome -> ordered list of status names for this workspace")
    ap.add_argument("--validate", action="store_true", help="check the input and exit")
    args = ap.parse_args()

    try:
        data = json.loads(args.update.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"error: cannot read {args.update}: {e}", file=sys.stderr)
        return 2
    errs = validate(data)
    if errs:
        print(f"{args.update} is not a valid agent update:", file=sys.stderr)
        for e in errs:
            print(f"  - {e}", file=sys.stderr)
        return 2
    if args.validate:
        print(f"{args.update}: valid ({len(data.get('items', []))} item(s), {len(data.get('new_tasks', []))} new task(s))")
        return 0

    status_map = dict(DEFAULT_STATUS_MAP)
    if args.status_map:
        try:
            custom = json.loads(args.status_map.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            print(f"error: cannot read status map {args.status_map}: {e}", file=sys.stderr)
            return 2
        for k, v in custom.items():
            if k not in OUTCOMES or not isinstance(v, list):
                print(f"error: status map key {k!r} must be an outcome with a list of statuses", file=sys.stderr)
                return 2
            status_map[k] = [str(s) for s in v]

    agent = str(data["source_agent"]).strip()
    reported_at = str(data["reported_at"]).strip()
    plan = Plan()
    for it in data.get("items", []):
        plan_item(plan, agent, reported_at, it, status_map)
    for nt in data.get("new_tasks", []):
        plan_new_task(plan, agent, reported_at, nt, data.get("default_list_id"))

    out = {
        "generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_agent": agent,
        "reported_at": reported_at,
        "ops": plan.ops,
        "warnings": plan.warnings,
    }
    args.out.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_preview(args.preview, data, plan)
    tasks = len({o["task_ref"] for o in plan.ops if o["op"] != "create_task"})
    creates = sum(1 for o in plan.ops if o["op"] == "create_task")
    print(f"planned {len(plan.ops)} op(s) across {tasks} task(s), {creates} new task(s), {len(plan.warnings)} warning(s) -> {args.out}, {args.preview}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
