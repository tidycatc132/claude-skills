#!/usr/bin/env python3
"""Week 5 final sweep: go/no-go for deployment and the "all good to go" message to dev.

  week5_handoff.py status-template --slug S [--root DIR]
      Writes qa/S/S-bugherd-status.json with one blank entry per BugHerd task id found in
      the QA and client-edit task files, for you to fill from BugHerd. Refuses to overwrite.

  week5_handoff.py run --slug S [--root DIR] [--today YYYY-MM-DD] [--pm NAME]
      Reads the working folder, writes handoff/S/S-week-5-handoff.md (check table, blocking
      items with owners, carried items, last line GO or NO-GO) and, on GO only,
      handoff/S/S-go-live-message.md. On NO-GO an earlier go-live message written by this
      script is removed so it cannot be sent by mistake. Exit 0 on GO, 3 on NO-GO, 2 on STOP.

  week5_handoff.py contract qa <staging QA report>
  week5_handoff.py contract feedback <Week 5 feedback.md>
  week5_handoff.py contract email <Week 5 email file>
  week5_handoff.py contract --validate <json file>
      Readers used by the pipeline contracts.

Standard library only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

SEVERITIES = ["CRITICAL", "MAJOR", "MINOR"]
QA_HEADER = "| # | Page URL | Department | Severity | Finding | Fix |"
RERUN_HEADER = "| Finding ID | Status | Page URL | Department | Severity | Finding |"
FB_HEADER = "| # | Feedback | Source | Page URL | Class | Department | Action | Task |"
CLASSES = ["Mechanical", "Strategic", "Scope Change", "Question", "Approval"]
DONE_STATUSES = {"done", "closed", "archived"}
GO_MARK = "Go-live message:"
CHECKS = ["Dev handoff index", "Staging QA re-run", "Open CRITICAL", "Open MAJOR",
          "BugHerd tasks", "Week 5 email", "Client edits", "AM sign-off"]


def die(msg: str, code: int = 2) -> None:
    print(msg)
    sys.exit(code)


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def iso(s: str) -> dt.date | None:
    try:
        return dt.date.fromisoformat(s.strip())
    except ValueError:
        return None


def split_row(line: str) -> list[str]:
    body = line.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|") and not body.endswith("\\|"):
        body = body[:-1]
    cells = re.split(r"(?<!\\)\|", body)
    return [c.strip().replace("\\|", "|") for c in cells]


def table(text: str, header: str) -> list[list[str]]:
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        if ln.strip() == header:
            rows = []
            for row in lines[i + 2:]:
                if not row.strip().startswith("|"):
                    break
                rows.append(split_row(row))
            return rows
    return []


def section(text: str, heading: str) -> str | None:
    m = re.search(rf"(?m)^{re.escape(heading)}\s*$", text)
    if not m:
        return None
    rest = text[m.end():]
    n = re.search(r"(?m)^(## |RESULT: )", rest)
    return rest[: n.start()] if n else rest


def bullets(block: str | None) -> list[str]:
    if not block:
        return []
    out = [ln[2:].strip() for ln in block.splitlines() if ln.startswith("- ")]
    return [b for b in out if b.lower() not in ("none", "nothing")]


def header_value(text: str, key: str) -> str:
    m = re.search(rf"(?m)^{re.escape(key)}[ \t]*(.*?)\s*$", text)
    return m.group(1) if m else ""


def last_line(text: str) -> str:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return lines[-1] if lines else ""


# --------------------------------------------------------------------------- #
# readers
# --------------------------------------------------------------------------- #
def read_qa(path: Path) -> dict:
    text = read(path)
    res = re.findall(r"(?m)^RESULT: (READY|CONDITIONAL|NOT READY)\s*$", text)
    staging = header_value(text, "Staging:")
    staging = re.sub(r"\s*\(saved pages:.*\)$", "", staging)
    findings = [dict(zip(["id", "page", "department", "severity", "finding", "fix"], r))
                for r in table(text, QA_HEADER) if len(r) == 6 and r[0] != "none"]
    rerun = section(text, "## Re-run Status")
    rerun_rows = [dict(zip(["Finding ID", "Status", "Page URL", "Department", "Severity", "Finding"], r))
                  for r in table(text, RERUN_HEADER) if len(r) == 6]
    return {
        "_has_findings": QA_HEADER in text,
        "## Not Checked": bullets(section(text, "## Not Checked")),
        "Staging:": staging,
        "Checked": header_value(text, "Checked:"),
        "## Findings": findings,
        "## Re-run Status": rerun_rows if rerun is not None else None,
        "## Launch Toggles": bullets(section(text, "## Launch Toggles")),
        "## AM Items": bullets(section(text, "## AM Items")),
        "RESULT:": res[-1] if res else "",
    }


def read_feedback(path: Path) -> dict:
    text = read(path)
    sc = section(text, "## Scope Changes") or ""
    notes = dict(re.findall(r"(?m)^- #(\d+) [^\n]*?: PM/AM: (.+?)\s*$", sc))
    rows = [r for r in table(text, FB_HEADER) if len(r) == 8]
    return {
        "Week:": header_value(text, "Week:"),
        "Date": header_value(text, "Date:"),
        "Class": [{"#": r[0], "Page URL": r[3], "Class": r[4], "Department": r[5], "Action": r[6],
                   "Task": r[7], "PM/AM note": notes.get(r[0], "")} for r in rows],
    }


def read_email(path: Path) -> dict:
    text = read(path)
    return {"Client:": header_value(text, "Client:"), "Send date:": header_value(text, "Send date:"),
            "Reply by:": header_value(text, "Reply by:"), "No-reply line:": header_value(text, "No-reply line:")}


def read_index(path: Path) -> dict:
    text = read(path)
    pages = []
    for block in re.split(r"(?m)^### ", text)[1:]:
        f = dict(re.findall(r"(?m)^- (Page|URL|Priority|Status): (.+?)\s*$", block))
        if "URL" in f:
            pages.append(f)
    return {"last": last_line(text), "pages": pages}


def newest_dated(folder: Path, pattern: str, rx: str) -> list[tuple[dt.date, Path]]:
    out = []
    for p in folder.glob(pattern) if folder.is_dir() else []:
        m = re.search(rx, p.name)
        if m and iso(m.group(1)):
            out.append((iso(m.group(1)), p))
    return sorted(out)


def load_json_list(p: Path) -> list:
    try:
        data = json.loads(read(p))
    except (json.JSONDecodeError, OSError):
        return []
    return data if isinstance(data, list) else []


# --------------------------------------------------------------------------- #
# gather
# --------------------------------------------------------------------------- #
def gather(root: Path, slug: str) -> dict:
    g: dict = {"slug": slug}
    g["index_path"] = root / "handoff" / slug / f"{slug}-dev-handoff-index.md"
    g["context_path"] = root / "kickoff" / slug / f"{slug}-context.md"
    qa_dir = root / "qa" / slug
    g["qa_reports"] = newest_dated(qa_dir, f"{slug}-staging-qa-*.md", r"-staging-qa-(\d{4}-\d{2}-\d{2})\.md$")
    g["qa_tasks_path"] = qa_dir / f"{slug}-bugherd-tasks.json"
    g["status_path"] = qa_dir / f"{slug}-bugherd-status.json"
    g["am_path"] = qa_dir / f"{slug}-am-review.md"
    g["email_path"] = root / "emails" / slug / f"{slug}-week-5-email.md"
    fb_dir = root / "feedback" / slug
    week5 = []
    for d, p in newest_dated(fb_dir, "*-feedback.md", r"^(\d{4}-\d{2}-\d{2})-feedback\.md$"):
        if header_value(read(p), "Week:") == "5":
            week5.append((d, p))
    g["feedback"] = week5
    g["ce_task_paths"] = [p.with_name(f"{d.isoformat()}-bugherd-tasks.json") for d, p in week5
                          if p.with_name(f"{d.isoformat()}-bugherd-tasks.json").exists()]
    return g


def all_task_objects(g: dict) -> list[dict]:
    tasks = []
    if g["qa_tasks_path"].exists():
        for t in load_json_list(g["qa_tasks_path"]):
            tasks.append(dict(t, _file=g["qa_tasks_path"]))
    for p in g["ce_task_paths"]:
        for t in load_json_list(p):
            tasks.append(dict(t, _file=p))
    return tasks


# --------------------------------------------------------------------------- #
# status-template
# --------------------------------------------------------------------------- #
def cmd_status_template(a) -> int:
    root = Path(a.root).resolve()
    g = gather(root, a.slug)
    out = g["status_path"]
    if out.exists():
        die(f"STOP: {out.relative_to(root).as_posix()} already exists. Update it in place (and its read_on date) "
            "instead of starting a new one.")
    tasks = all_task_objects(g)
    entries, seen = [], set()
    for t in tasks:
        tid = str(t.get("bugherd_task_id", "")).strip()
        if tid and tid not in seen:
            seen.add(tid)
            entries.append({"bugherd_task_id": tid, "finding_id": t.get("finding_id", ""),
                            "title": t.get("title", ""), "status": "", "severity": "", "deferred": ""})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"read_on": "", "source": "", "tasks": entries}, indent=2) + "\n", encoding="utf-8")
    missing = [t["finding_id"] for t in tasks if not str(t.get("bugherd_task_id", "")).strip()
               and t.get("status") != "FIXED"]
    print(f"Wrote {out.relative_to(root).as_posix()} with {len(entries)} task id(s) from the task files.")
    print("Fill status (BugHerd's own status or column) and severity for each, add every other task on the "
          "client's BugHerd project, set read_on and source. Put a reason in deferred only when the PM defers it.")
    if missing:
        print("Not created in BugHerd yet (no bugherd_task_id): " + ", ".join(missing))
    return 0


# --------------------------------------------------------------------------- #
# run
# --------------------------------------------------------------------------- #
def cmd_run(a) -> int:
    root = Path(a.root).resolve()
    slug = a.slug
    today = iso(a.today) if a.today else dt.date.today()
    if today is None:
        die("STOP: --today must be YYYY-MM-DD.")
    g = gather(root, slug)
    rel = lambda p: p.relative_to(root).as_posix()  # noqa: E731
    msg = root / "handoff" / slug / f"{slug}-go-live-message.md"
    if msg.exists() and read(msg).startswith(GO_MARK):
        # Removed before any check, so a STOP or a NO-GO never leaves an earlier GO message behind.
        msg.unlink()
        print(f"Removed the earlier {rel(msg)}; it is written again only if this sweep is GO.")
    if not g["context_path"].exists():
        die(f"STOP: {rel(g['context_path'])} is missing; this is not a client working folder (run new-build-kickoff).")
    ctx = read(g["context_path"])
    client = header_value(ctx, "Client:") or re.sub(r"\s*\[.*\]$", "", header_value(ctx, "- Name:")) or slug
    website = re.sub(r"\s*\[.*\]$", "", header_value(ctx, "- Website:"))

    rows: dict[str, tuple[str, str, str]] = {}
    blocking: list[str] = []
    carried: list[str] = []
    housekeeping: list[str] = []
    notes: list[str] = []

    def fail(check: str, detail: str, owner: str, items: list[str] | None = None) -> None:
        rows[check] = ("FAIL", detail, owner)
        for it in items or [detail]:
            blocking.append(f"{it} (owner: {owner})" if "(owner:" not in it else it)

    # 1. dev handoff index
    index = read_index(g["index_path"]) if g["index_path"].exists() else None
    if index is None:
        fail(CHECKS[0], f"{rel(g['index_path'])} is missing (dev-handoff-index)", "PM")
    elif index["last"] != "GO":
        fail(CHECKS[0], f"{rel(g['index_path'])} ends {index['last'] or 'with no result line'}, not GO", "PM")
    else:
        rows[CHECKS[0]] = ("PASS", f"{rel(g['index_path'])} ends GO", "PM")

    # 2. staging QA re-run
    qa = None
    qa_date = None
    if not g["qa_reports"]:
        fail(CHECKS[1], "no staging QA report in qa/" + slug + "/ (staging-site-qa)", "PM")
    else:
        qa_date, qa_path = g["qa_reports"][-1]
        qa = read_qa(qa_path)
        if qa["## Re-run Status"] is None:
            fail(CHECKS[1], f"{rel(qa_path)} is a first run; re-run staging-site-qa after the fixes", "PM")
        elif not qa["RESULT:"]:
            fail(CHECKS[1], f"{rel(qa_path)} has no RESULT line", "PM")
        elif g["feedback"] and qa_date < g["feedback"][-1][0]:
            fail(CHECKS[1], f"{rel(qa_path)} ({qa_date}) is older than the client edits of {g['feedback'][-1][0]}; "
                            "re-run staging-site-qa once the edits are in", "PM")
        else:
            n = {s: sum(1 for r in qa["## Re-run Status"] if r["Status"] == s) for s in ("FIXED", "OPEN", "NEW")}
            rows[CHECKS[1]] = ("PASS", f"{rel(qa_path)}: re-run, {n['FIXED']} FIXED, {n['OPEN']} OPEN, "
                                       f"{n['NEW']} NEW (RESULT: {qa['RESULT:']})", "PM")

    # BugHerd status file
    status = None
    status_err = ""
    if g["status_path"].exists():
        try:
            status = json.loads(read(g["status_path"]))
            if not isinstance(status, dict) or not isinstance(status.get("tasks"), list):
                status, status_err = None, "is not in the status file format (read_on, source, tasks)"
        except json.JSONDecodeError as e:
            status_err = f"is not valid JSON ({e})"
    by_id: dict[str, dict] = {}
    if status:
        for e in status["tasks"]:
            if isinstance(e, dict) and str(e.get("bugherd_task_id", "")).strip():
                by_id[str(e["bugherd_task_id"]).strip()] = e

    tasks = all_task_objects(g)
    id_of = {t.get("finding_id"): str(t.get("bugherd_task_id", "")).strip() for t in tasks}

    def bugherd_note(fid: str) -> str:
        tid = id_of.get(fid, "")
        if not tid:
            return " No BugHerd task yet: create it."
        if status is None:
            return f" BugHerd #{tid}."
        st = str(by_id.get(tid, {}).get("status", "")).strip()
        return f" BugHerd #{tid}: '{st}'." if st else f" BugHerd #{tid}: status not read."

    def deferred_reason(fid: str) -> str:
        tid = id_of.get(fid, "")
        return str(by_id.get(tid, {}).get("deferred", "")).strip() if tid else ""

    # 3 and 4. open CRITICAL / MAJOR
    if qa is None or qa["## Re-run Status"] is None:
        rows[CHECKS[2]] = ("FAIL", "needs a staging QA re-run first", "PM")
        rows[CHECKS[3]] = ("FAIL", "needs a staging QA re-run first", "PM")
    else:
        crit = [f for f in qa["## Findings"] if f["severity"] == "CRITICAL"]
        if not qa["_has_findings"]:
            fail(CHECKS[2], "the newest QA report has no Findings table in staging-site-qa's format", "PM")
        elif qa["RESULT:"] == "NOT READY" and not crit:
            fail(CHECKS[2], "the report says RESULT: NOT READY but no CRITICAL row could be read; re-run "
                            "staging-site-qa", "PM")
        elif crit:
            fail(CHECKS[2], f"{len(crit)} open: " + ", ".join(f["id"] for f in crit) + " (CRITICAL cannot be deferred)",
                 ", ".join(sorted({f['department'] for f in crit})),
                 [f"{f['id']} {f['page']}: {f['finding']} CRITICAL, must be fixed before launch."
                  f"{bugherd_note(f['id'])} (owner: {f['department']})" for f in crit])
        else:
            rows[CHECKS[2]] = ("PASS", "none open", "PM")
        major = [f for f in qa["## Findings"] if f["severity"] == "MAJOR"]
        open_major = [f for f in major if not deferred_reason(f["id"])]
        for f in major:
            if deferred_reason(f["id"]):
                carried.append(f"{f['id']} {f['page']} (MAJOR, {f['department']}): {f['finding']} "
                               f"DEFERRED: {deferred_reason(f['id'])}")
        if open_major:
            fail(CHECKS[3], f"{len(open_major)} open and not deferred: " + ", ".join(f["id"] for f in open_major),
                 ", ".join(sorted({f['department'] for f in open_major})),
                 [f"{f['id']} {f['page']}: {f['finding']} MAJOR, fix it or have the PM defer it with a reason."
                  f"{bugherd_note(f['id'])} (owner: {f['department']})" for f in open_major])
        else:
            rows[CHECKS[3]] = ("PASS", "none open" if not major else f"{len(major)} deferred by the PM", "PM")
        for f in qa["## Findings"]:
            if f["severity"] == "MINOR":
                carried.append(f"{f['id']} {f['page']} (MINOR, {f['department']}): {f['finding']} "
                               "MINOR: post-launch backlog")

    # 5. BugHerd tasks
    sev_of = {t.get("finding_id"): t.get("severity") for t in tasks if t.get("finding_id")}
    minor_ids = {f for f, sv in sev_of.items() if sv == "MINOR"}
    fixed_ids = {t.get("finding_id") for t in tasks if t.get("status") == "FIXED"}
    for _, rp in g["qa_reports"]:
        fixed_ids |= {r["Finding ID"] for r in read_qa(rp)["## Re-run Status"] or [] if r["Status"] == "FIXED"}
    fixed_ids -= {f["id"] for f in (qa or {}).get("## Findings", [])}
    fid_of_tid = {str(t.get("bugherd_task_id", "")).strip(): t.get("finding_id", "") for t in tasks}
    probs: list[str] = []
    if status is None:
        why = (f"{rel(g['status_path'])} {status_err}" if status_err else
               f"BugHerd statuses not read: save {rel(g['status_path'])} (status-template, then fill it from BugHerd)")
        fail(CHECKS[4], why, "PM")
    else:
        read_on = iso(str(status.get("read_on", "")))
        newest_input = max([d for d in [qa_date] + [d for d, _ in g["feedback"]] if d], default=None)
        if read_on is None:
            probs.append(f"{rel(g['status_path'])} has no read_on date")
        elif newest_input and read_on < newest_input:
            probs.append(f"BugHerd statuses were read {read_on}, before the newest QA or client-edit file "
                         f"({newest_input}); read them again")
        elif read_on > today:
            probs.append(f"read_on {read_on} is after today ({today})")
        qa_open = {f["id"] for f in (qa or {}).get("## Findings", [])
                   if f["severity"] == "CRITICAL" or (f["severity"] == "MAJOR" and not deferred_reason(f["id"]))}
        for t in tasks:
            tid = str(t.get("bugherd_task_id", "")).strip()
            if t.get("finding_id") in qa_open:
                continue
            if not tid and t.get("status") != "FIXED":
                probs.append(f"{t.get('finding_id')} ({t.get('department')}) was never created in BugHerd; "
                             "create it or record its id")
            elif tid and tid not in by_id:
                probs.append(f"BugHerd #{tid} ({t.get('finding_id')}) is not in the status file; read its status")
        n_done = n_def = 0
        for tid, e in by_id.items():
            st = str(e.get("status", "")).strip()
            fid = str(e.get("finding_id", "")).strip() or fid_of_tid.get(tid, "")
            title = str(e.get("title", "")).strip()
            label = f"BugHerd #{tid}" + (f" ({fid})" if fid else "")
            named = label + (f' "{title}"' if title else "")
            if not st:
                probs.append(f"{label} has no status; read it from BugHerd")
            elif fid in qa_open:
                continue
            elif st.lower() in DONE_STATUSES:
                n_done += 1
            elif sev_of.get(fid) == "CRITICAL" and fid not in fixed_ids:
                dept = next((t.get("department") for t in tasks if t.get("finding_id") == fid), "") or "PM"
                probs.append(f"{named} is still '{st}' in BugHerd and is CRITICAL, which cannot be deferred "
                             f"(owner: {dept})")
            elif fid in fixed_ids:
                housekeeping.append(f"{named}: fixed in the QA re-run but still '{st}' in BugHerd; close it")
            elif str(e.get("deferred", "")).strip():
                n_def += 1
                if not fid.startswith("QA-") or fid not in {f["id"] for f in (qa or {}).get("## Findings", [])}:
                    carried.append(f"{named} ('{st}') DEFERRED: {str(e['deferred']).strip()}")
            elif fid in minor_ids or (fid not in sev_of and str(e.get("severity", "")).strip().lower() == "minor"):
                n_def += 1
                if fid not in {f["id"] for f in (qa or {}).get("## Findings", [])}:
                    carried.append(f"{named} ('{st}') MINOR: post-launch backlog")
            else:
                dept = next((t.get("department") for t in tasks if t.get("finding_id") == fid and fid), "") \
                    or "PM"
                probs.append(f"{named} is still '{st}' in BugHerd (owner: {dept})")
        if probs:
            rows[CHECKS[4]] = ("FAIL", f"{len(probs)} problem(s); {n_done} done, {n_def} deferred or post-launch",
                               "PM")
            for p in probs:
                blocking.append(p if "(owner:" in p else f"{p} (owner: PM)")
        else:
            rows[CHECKS[4]] = ("PASS", f"{len(by_id)} task(s) read {read_on}: {n_done} done, {n_def} deferred or "
                                       "post-launch", "PM")

    # 6. Week 5 email
    email = read_email(g["email_path"]) if g["email_path"].exists() else None
    send = iso(email["Send date:"]) if email else None
    reply_by = iso(email["Reply by:"]) if email else None
    if email is None:
        fail(CHECKS[5], f"{rel(g['email_path'])} is missing (week-5-client-email)", "AM")
    elif send is None or reply_by is None:
        fail(CHECKS[5], f"{rel(g['email_path'])} has no valid Send date or Reply by line", "AM")
    elif send > today:
        fail(CHECKS[5], f"send date {send} is after today ({today}); the client has not had the link yet", "AM")
    else:
        rows[CHECKS[5]] = ("PASS", f"sent {send}, reply by {reply_by}", "AM")

    # 7. client edits
    scope_notes: list[str] = []
    if g["feedback"]:
        fd, fp = g["feedback"][-1]
        rounds = [(d, p, read_feedback(p)) for d, p in g["feedback"]]
        fb = {"Class": [r for _, _, f in rounds for r in f["Class"]]}
        multi = len(rounds) > 1
        tag = lambda d, n: f"{d} #{n}" if multi else n  # noqa: E731
        bad = [tag(d, r["#"]) for d, _, f in rounds for r in f["Class"] if r["Class"] not in CLASSES]
        no_note = [tag(d, r["#"]) for d, _, f in rounds for r in f["Class"]
                   if r["Class"] == "Scope Change" and not r["PM/AM note"]]
        for d, _, f in rounds:
            for r in f["Class"]:
                if r["Class"] == "Scope Change":
                    scope_notes.append(f"#{r['#']} {r['Page URL']}: {r['Action']}. PM/AM: {r['PM/AM note'] or 'no note'}"
                                       + (f" (client edits {d})" if multi else ""))
        empty = [rel(p) for _, p, f in rounds if not f["Class"]]
        if empty:
            fail(CHECKS[6], ", ".join(empty) + " has no feedback table rows", "AM")
        elif bad or no_note:
            detail = "; ".join(x for x in [
                ("rows without a class: #" + ", #".join(bad)) if bad else "",
                ("Scope Changes without a PM/AM note: #" + ", #".join(no_note)) if no_note else ""] if x)
            fail(CHECKS[6], f"{rel(fp)}: {detail}", "AM")
        else:
            counts = {c: sum(1 for r in fb["Class"] if r["Class"] == c) for c in CLASSES}
            rows[CHECKS[6]] = ("PASS", (f"{len(rounds)} rounds, newest " if multi else "") +
                               f"{rel(fp)}: {len(fb['Class'])} edit(s) classed (" +
                               ", ".join(f"{n} {c}" for c, n in counts.items() if n) + ")" +
                               (f"; {counts['Scope Change']} Scope Change(s) with PM/AM notes"
                                if counts["Scope Change"] else ""), "AM")
    elif email is None or reply_by is None:
        fail(CHECKS[6], "no Week 5 client edits and no reply-by date to judge them by", "AM")
    elif today <= reply_by:
        fail(CHECKS[6], f"no client edits yet; the client has until {reply_by}", "AM")
    elif email["No-reply line:"].strip().lower().startswith("yes"):
        rows[CHECKS[6]] = ("PASS", f"client not verified: no reply by {reply_by}; the email said we would go "
                                   "ahead with the site as it is", "AM")
        notes.append(f"Client not verified: no reply to the staging email by {reply_by} (the email said we would "
                     "go ahead). Tell the client the launch date when it is set.")
    else:
        fail(CHECKS[6], f"no reply by {reply_by}, and the email did not say we would go ahead without one; "
                        "the AM gets the client's answer", "AM")

    # 8. AM sign-off
    am_line = ""
    if g["am_path"].exists():
        m = re.search(r"(?m)^AM sign-off: (.+?), (\d{4}-\d{2}-\d{2})\s*$", read(g["am_path"]))
        if m and iso(m.group(2)) and iso(m.group(2)) <= today:
            am_line = f"{m.group(1)}, {m.group(2)}"
    if am_line:
        rows[CHECKS[7]] = ("PASS", f"{rel(g['am_path'])}: {am_line}", "AM")
    else:
        fail(CHECKS[7], f"no 'AM sign-off: <name>, <YYYY-MM-DD>' line in {rel(g['am_path'])}", "AM")

    if qa:
        notes += [f"Not checked by the QA re-run: {x}" for x in qa["## Not Checked"]]
    go = all(rows[c][0] == "PASS" for c in CHECKS)
    result = "GO" if go else "NO-GO"

    # write the handoff
    out = root / "handoff" / slug / f"{slug}-week-5-handoff.md"
    qa_ref = (f"{rel(g['qa_reports'][-1][1])} (RESULT: {qa['RESULT:']})" if qa else "none")
    st_ref = (f"{rel(g['status_path'])} (read {status.get('read_on', '')}, {status.get('source', '') or 'source not given'})"
              if status else "none")
    fb_ref = rel(g["feedback"][-1][1]) if g["feedback"] else "none"
    L = [f"Client: {client}", f"Checked: {today.isoformat()}", f"Dev handoff index: {rel(g['index_path'])}",
         f"Staging QA: {qa_ref}", f"BugHerd status: {st_ref}",
         f"Week 5 email: {rel(g['email_path']) if email else 'none'}", f"Client edits: {fb_ref}",
         f"AM review: {rel(g['am_path']) if g['am_path'].exists() else 'none'}", "",
         f"# Week 5 final sweep: {client}", "", "## Checks", "",
         "| # | Check | Result | Detail | Owner |", "|---|---|---|---|---|"]
    for i, c in enumerate(CHECKS, 1):
        r, d, o = rows[c]
        L.append(f"| {i} | {c} | {r} | {d.replace('|', chr(92) + '|')} | {o} |")
    L += ["", "## Blocking", ""] + ([f"- {b}" for b in blocking] or ["None."])
    L += ["", "## Carried to Post-Launch", ""] + ([f"- {c}" for c in carried] or ["- none"])
    L += ["", "## Scope Changes", ""] + ([f"- {s}" for s in scope_notes] or ["- none"])
    L += ["", "## Close in BugHerd", ""] + ([f"- {h}" for h in housekeeping] or ["- none"])
    L += ["", "## Notes", ""] + ([f"- {n}" for n in notes] or ["- none"])
    L += ["", result, ""]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L), encoding="utf-8")
    print(f"Wrote {rel(out)}")
    for c in CHECKS:
        print(f"  {rows[c][0]:4}  {c}: {rows[c][1]}")

    if go:
        build = [p for p in index["pages"] if p.get("Priority", "").strip().lower() == "build"]
        later = [p for p in index["pages"] if p.get("Priority", "").strip().lower() != "build"]
        M = [f"{GO_MARK} {client}", f"Date: {today.isoformat()}", f"Final sweep: {rel(out)} (GO)",
             f"Staging: {qa['Staging:']}", f"Production: {website or 'see the context Website line'}", "",
             f"Subject: All good to go: {client}", "", "Hi team,", "",
             f"{client} is all good to go for deployment" + (f" to {website}" if website else "") +
             f". The Week 5 final sweep passed on {today.isoformat()}.", "", "Pages cleared for launch:", ""]
        M += [f"- {p.get('Page', p['URL'])}: {p['URL']}" for p in build]
        M += ["", "At launch:", ""] + ([f"- {t}" for t in qa["## Launch Toggles"]] or ["- nothing beyond the usual deployment"])
        M += ["", "Carried to post-launch (not blocking launch):", ""] + ([f"- {c}" for c in carried] or ["- none"])
        nil = [f"- {p.get('Page', p['URL'])} ({p['URL']}): {p.get('Priority', 'not Build')} priority" for p in later]
        nil += [f"- Scope Change {s}" for s in scope_notes]
        M += ["", "Not in this launch:", ""] + (nil or ["- none"])
        M += ["", "Thanks,", a.pm or "[PM name]", "Project Manager, WISE Digital Partners", ""]
        msg.write_text("\n".join(M), encoding="utf-8")
        print(f"Wrote {rel(msg)}")
    if blocking:
        print("Blocking:")
        for b in blocking:
            print(f"  - {b}")
    print(result)
    return 0 if go else 3


# --------------------------------------------------------------------------- #
# contracts
# --------------------------------------------------------------------------- #
def validate(data: dict) -> list[str]:
    errs = []
    if "RESULT:" in data:
        if data["RESULT:"] not in ("READY", "CONDITIONAL", "NOT READY"):
            errs.append("RESULT: must be READY, CONDITIONAL or NOT READY")
        if not str(data.get("Staging:", "")).startswith("http"):
            errs.append("Staging: must be a URL")
        rr = data.get("## Re-run Status")
        if not isinstance(rr, list):
            errs.append("## Re-run Status must be a list (a re-run report)")
        else:
            for r in rr:
                if not re.fullmatch(r"QA-[0-9a-f]{8}", r.get("Finding ID", "")) or r.get("Status") not in ("FIXED", "OPEN", "NEW"):
                    errs.append(f"bad Re-run Status row {r}")
                if r.get("Severity") not in SEVERITIES:
                    errs.append(f"bad severity in {r}")
        if not isinstance(data.get("## Launch Toggles"), list):
            errs.append("## Launch Toggles must be a list")
        for t in data.get("tasks", []):
            if not re.fullmatch(r"QA-[0-9a-f]{8}", str(t.get("finding_id", ""))) or t.get("severity") not in SEVERITIES \
                    or t.get("status") not in ("FIXED", "OPEN", "NEW") or "bugherd_task_id" not in t:
                errs.append(f"bad QA task {t}")
    elif "Week:" in data:
        if data["Week:"] != "5":
            errs.append("Week: must be 5")
        for r in data.get("Class", []):
            if r.get("Class") not in CLASSES:
                errs.append(f"row {r.get('#')}: unknown class {r.get('Class')}")
            if r.get("Class") == "Scope Change" and not r.get("PM/AM note"):
                errs.append(f"row {r.get('#')}: Scope Change without a PM/AM note")
        if not data.get("Class"):
            errs.append("Class rows missing")
        for t in data.get("tasks", []):
            if not re.fullmatch(r"(CE|QA)-[0-9a-f]{8}", str(t.get("finding_id", ""))):
                errs.append(f"bad task id {t.get('finding_id')}")
            if "bugherd_task_id" not in t or t.get("severity") not in SEVERITIES:
                errs.append(f"task {t.get('finding_id')}: needs bugherd_task_id and a severity")
    elif "Send date:" in data:
        s, r = iso(str(data.get("Send date:", ""))), iso(str(data.get("Reply by:", "")))
        if not data.get("Client:"):
            errs.append("Client: missing")
        if s is None or r is None or r < s:
            errs.append("Send date: and Reply by: must be dates, reply by on or after the send date")
    else:
        errs.append("unknown contract shape")
    return errs


def cmd_contract(a) -> int:
    if a.validate:
        data = json.loads(read(Path(a.kind_or_file)))
        errs = validate(data)
        for e in errs:
            print("INVALID: " + e)
        if not errs:
            print("VALID")
        return 1 if errs else 0
    p = Path(a.file)
    if a.kind_or_file == "qa":
        d = read_qa(p)
        out = {k: d[k] for k in ("Staging:", "## Findings", "## Re-run Status", "## Launch Toggles", "RESULT:")}
        tf = p.parent / (p.name.split("-staging-qa-")[0] + "-bugherd-tasks.json")
        keep = ["finding_id", "status", "bugherd_task_id", "severity", "department"]
        out["tasks"] = [{k: t.get(k) for k in keep} for t in load_json_list(tf)]
    elif a.kind_or_file == "feedback":
        d = read_feedback(p)
        tasks_path = p.with_name(p.name.replace("-feedback.md", "-bugherd-tasks.json"))
        keep = ["finding_id", "status", "create", "bugherd_task_id", "department", "column", "severity"]
        out = {"Week:": d["Week:"],
               "Class": [{k: r[k] for k in ("#", "Class", "Department", "Task", "PM/AM note")} for r in d["Class"]],
               "tasks": [{k: t.get(k) for k in keep} for t in load_json_list(tasks_path)]}
    elif a.kind_or_file == "email":
        d = read_email(p)
        out = {k: d[k] for k in ("Client:", "Send date:", "Reply by:")}
    else:
        die("contract kind must be qa, feedback or email")
    print(json.dumps(out, indent=2))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("status-template")
    t.add_argument("--slug", required=True)
    t.add_argument("--root", default=".")
    r = sub.add_parser("run")
    r.add_argument("--slug", required=True)
    r.add_argument("--root", default=".")
    r.add_argument("--today", default="")
    r.add_argument("--pm", default="")
    c = sub.add_parser("contract")
    c.add_argument("kind_or_file")
    c.add_argument("file", nargs="?", default="")
    c.add_argument("--validate", action="store_true")
    a = ap.parse_args()
    if a.cmd == "status-template":
        return cmd_status_template(a)
    if a.cmd == "run":
        return cmd_run(a)
    if not a.validate and not a.file:
        die("contract needs a kind and a file, or --validate <json file>")
    return cmd_contract(a)


if __name__ == "__main__":
    sys.exit(main())
