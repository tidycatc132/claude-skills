#!/usr/bin/env python3
"""Week 5 staging review: the client's edits to the staging site, by email and/or BugHerd guest tasks.

Imported by feedback.py, which routes a plan with "week": 5 and a report with `Week: 5` here.
It classes each edit (Mechanical, Strategic, Scope Change, plus Question and Approval), writes
feedback/<slug>/<date>-feedback.md and feedback/<slug>/<date>-bugherd-tasks.json in
staging-site-qa's task format, and checks both. Standard library only.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import feedback as F

CLASSES = ["Mechanical", "Strategic", "Scope Change", "Question", "Approval"]
TASK_CLASSES = ("Mechanical", "Strategic")
DEPARTMENTS = ["Content", "SEO", "Design", "Development", "Account Management"]
MECH_DEPTS = ("Content", "Design", "Development")
DEFAULT_COLUMNS = {"Content": "Copy Review", "SEO": "SEO Review", "Design": "Design Review",
                   "Development": "Dev Ready"}
SEVERITIES = ["CRITICAL", "MAJOR", "MINOR"]
BUGHERD_SEVERITY = {"CRITICAL": "critical", "MAJOR": "important", "MINOR": "minor"}
# staging-site-qa's task keys, in its order; week-5-handoff-check reads both files with one reader.
TASK_KEYS = ["finding_id", "status", "create", "bugherd_task_id", "page_url", "department", "column",
             "assignee", "severity", "bugherd_severity", "title", "description"]
TABLE_COLUMNS = ["#", "Feedback", "Source", "Page URL", "Class", "Department", "Action", "Task"]
TABLE_HEADER = "| " + " | ".join(TABLE_COLUMNS) + " |"
SECTIONS = ["Summary", "Feedback Items", "SEO Review", "Scope Changes", "Reply Draft"]
SEO_HOLD = "Status: SEO decides the items below before they are built"
SEO_CLEAR = "- No Strategic edits."
SCOPE_CLEAR = "- No Scope Changes."
PAGE_WORDS = ("site-wide", "new page")
# Clients are guests on the BugHerd project, so task text never carries internal wording.
INTERNAL_TASK = re.compile(r"\b(budget|invoice|retainer|billable|margin|out of scope|scope change|internal note|"
                           r"upsell|change order|mechanical|strategic|pm/am)\b", re.I)
INTERNAL_REPLY = [r"\bMechanical\b", r"\bStrategic\b", r"\bScope Change\b", r"(?i)punch list", r"\bCRITICAL\b",
                  r"\bMAJOR\b", r"\bMINOR\b", r"\b(?:CE|QA)-[0-9a-f]{8}\b", r"\bCopy Review\b", r"\bDesign Review\b",
                  r"\bDev Ready\b", r"(?i)\bPM/AM\b"]
FIX_RE = re.compile(r"(?i)\b(fix|fixed|fixing|correct|corrected|correcting|update|updated|updating|swap|swapped|"
                    r"swapping|replace|replaced|change|changed|changing)\b")
STRATEGIC_WORDS = re.compile(r"(?i)\b(heading|headline|title|H1|CTA|button|service description)\b")
CALL_RE = re.compile(r"(?i)\bcall\b")
HOLD_RE5 = re.compile(r"(?i)\b(review|reviewing|look at|looking at|consider|whether|SEO|come back|get back|call)\b")


def short_hash(*parts: str) -> str:
    return hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:8]


def path_of(url: str) -> str:
    m = re.match(r"^https?://[^/]+(/[^?#]*)?", url.strip())
    p = (m.group(1) if m else url.strip()) or "/"
    return p if p.endswith("/") or "." in p.rsplit("/", 1)[-1] else p + "/"


# ---------- working folder ----------

def info(kdir: Path, bugherd_arg: str | None = None) -> dict:
    """What a Week 5 run reads: the dev index URLs, routing, the staging URL, the QA report, the Week 5 email."""
    slug, root = kdir.name, kdir.parent.parent
    idx = root / "handoff" / slug / f"{slug}-dev-handoff-index.md"
    urls = re.findall(r"(?m)^- URL:\s*(\S+)\s*$", F.read(idx)) if idx.exists() else []
    routing = root / "qa" / "routing.md"
    cols, people, project = dict(DEFAULT_COLUMNS), {}, ""
    if routing.exists():
        rt = F.read(routing)
        m = re.search(r"(?m)^BugHerd project:\s*(.+?)\s*$", rt)
        project = m.group(1) if m else ""
        for ln in rt.split("\n"):
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            if len(cells) >= 2 and cells[0] in DEFAULT_COLUMNS:
                if cells[1] and not set(cells[1]) <= set("-: "):
                    cols[cells[0]] = cells[1]
                if len(cells) >= 3 and cells[2]:
                    people[cells[0]] = cells[2]
    reports = sorted((root / "qa" / slug).glob(f"{slug}-staging-qa-*.md"))
    qa = reports[-1] if reports else None
    staging = staging_line(F.read(qa)) if qa else ""
    email = root / "emails" / slug / f"{slug}-week-5-email.md"
    em_text = F.read(email) if email.exists() else ""
    rb = F.email_header(em_text)["Reply by:"] if em_text else ""
    bh_path, bh_tasks = None, []
    if bugherd_arg:
        bh_path = Path(bugherd_arg)
        bh_tasks = load_bugherd(bh_path)
    return {"slug": slug, "root": root, "index": rel(root, idx) if idx.exists() else "",
            "urls": urls, "columns": cols, "assignees": people, "project": project,
            "routing": rel(root, routing) if routing.exists() else "",
            "qa": rel(root, qa) if qa else "", "staging": staging,
            "email": rel(root, email) if email.exists() else "", "reply_by": rb if F.DATE_RE.match(rb) else "",
            "email_text": em_text, "bugherd": bh_path, "bugherd_tasks": bh_tasks}


def staging_line(text: str) -> str:
    """The base URL from staging-site-qa's `Staging: <base URL> (saved pages: ...)` header line."""
    m = re.search(r"(?m)^Staging:\s*(https?://[^/\s]+)", text)
    return m.group(1) if m else ""


def rel(root: Path, p: Path) -> str:
    try:
        return p.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return p.as_posix()


def load_bugherd(p: Path) -> list[dict]:
    """The client's BugHerd tasks as saved: a JSON list of {task_id, url, description, requester, created_at}."""
    if not p.exists():
        raise SystemExit(f"ERROR: {p} not found")
    try:
        data = json.loads(F.read(p))
    except json.JSONDecodeError as e:
        raise SystemExit(f"PLAN REJECTED\n- {p} is not valid JSON: {e}")
    if not isinstance(data, list):
        raise SystemExit(f"PLAN REJECTED\n- {p} must be a JSON list of the client's tasks")
    out = []
    for n, t in enumerate(data, 1):
        if not isinstance(t, dict) or not str(t.get("task_id", "")).strip() or not str(t.get("description", "")).strip():
            raise SystemExit(f"PLAN REJECTED\n- {p} task {n} needs task_id and description")
        out.append({"task_id": str(t["task_id"]).strip(), "url": str(t.get("url", "")).strip(),
                    "description": str(t["description"]), "requester": str(t.get("requester", "")),
                    "created_at": str(t.get("created_at", ""))})
    return out


def staging_base(plan: dict, w5: dict) -> str:
    base = str(plan.get("staging_url", "")).strip().rstrip("/") or w5["staging"]
    if not base:
        for t in w5["bugherd_tasks"]:
            m = re.match(r"^(https?://[^/]+)", t["url"])
            if m:
                return m.group(1)
    return base


def page_url(base: str, page: str) -> str:
    return base + ("/" if page in PAGE_WORDS else page)


def client_texts(raw: str, w5: dict) -> dict:
    """The client's own words by source: `email` and `bugherd:<task_id>`."""
    texts = {"email": F.own_text(raw)} if raw else {}
    for t in w5["bugherd_tasks"]:
        texts[f"bugherd:{t['task_id']}"] = t["description"]
    return texts


def all_own(texts: dict) -> str:
    return "\n\n".join(texts.values())


def source_cell(src: str) -> str:
    return "email" if src == "email" else "BugHerd #" + src.split(":", 1)[1]


def finding_id(page: str, quote: str) -> str:
    return "CE-" + short_hash(page, F.norm(quote))


# ---------- plan ----------

def validate(plan: dict, scope: dict, raw: str, w5: dict) -> list[str]:
    errs: list[str] = []
    for k in ("date", "from", "contact", "items", "reply"):
        if k not in plan:
            errs.append(f"plan is missing '{k}'")
    if errs:
        return errs
    texts = client_texts(raw, w5)
    own = all_own(texts)
    if not texts:
        errs.append("a Week 5 plan needs the client's email (--feedback) and/or their BugHerd tasks (--bugherd)")
    if not F.DATE_RE.match(str(plan["date"])):
        errs.append(f"date '{plan['date']}' must be YYYY-MM-DD")
    if not str(plan["contact"]).strip():
        errs.append("contact must name the person who sent the edits")
    base = staging_base(plan, w5)
    if not base:
        errs.append("no staging URL: give staging_url in the plan, or run staging-site-qa first "
                    f"(qa/{w5['slug']}/{w5['slug']}-staging-qa-<date>.md has the Staging: line)")
    elif not re.match(r"^https?://[^/\s]+$", base):
        errs.append(f"staging_url '{base}' must be the site's base URL, like https://client.staging-host.site")
    items = plan["items"]
    if not isinstance(items, list) or not items:
        errs.append("items must be a non-empty list")
        items = []
    bh = {f"bugherd:{t['task_id']}": t for t in w5["bugherd_tasks"]}
    seen_ids: dict[str, int] = {}
    for n, it in enumerate(items, 1):
        p = f"item {n}"
        fb, src = str(it.get("feedback", "")), str(it.get("source", "email"))
        cls, dept, page = it.get("class"), it.get("department"), str(it.get("page", "")).strip()
        if src not in texts:
            errs.append(f"{p}: source '{src}' is not 'email' (with --feedback) or 'bugherd:<task_id>' of a saved task "
                        f"({', '.join(texts) or 'none'})")
        if not fb.strip():
            errs.append(f"{p}: feedback is empty")
        elif src in texts and F.norm(fb) not in F.norm(texts[src]):
            errs.append(f"{p}: feedback is not a verbatim quote of the client's {source_cell(src)} text: \"{fb[:60]}\"")
        if len(fb) > F.MAX_QUOTE:
            errs.append(f"{p}: feedback quote is {len(fb)} characters; cut it to the words that matter (max {F.MAX_QUOTE})")
        for key in ("feedback", "action", "pm_am_note"):
            v = str(it.get(key, ""))
            if "|" in v or "\n" in v.strip():
                errs.append(f"{p}: {key} must be one line without '|'")
        if not str(it.get("action", "")).strip():
            errs.append(f"{p}: action is empty")
        if cls not in CLASSES:
            errs.append(f"{p}: class '{cls}' is not one of {CLASSES}")
        if dept not in DEPARTMENTS:
            errs.append(f"{p}: department '{dept}' is not one of {DEPARTMENTS}")
        if cls == "Mechanical" and dept not in MECH_DEPTS:
            errs.append(f"{p}: a Mechanical edit goes to Content, Design or Development "
                        "(a title, heading or keyword change is Strategic, for SEO)")
        if cls == "Strategic" and dept != "SEO":
            errs.append(f"{p}: a Strategic edit goes to SEO, who decides it before it is built")
        if cls in ("Scope Change", "Question", "Approval") and dept != "Account Management":
            errs.append(f"{p}: a {cls} goes to Account Management (no BugHerd task)")
        if cls in TASK_CLASSES:
            if it.get("severity") not in SEVERITIES:
                errs.append(f"{p}: a {cls} edit needs severity, one of {SEVERITIES}")
        elif "severity" in it:
            errs.append(f"{p}: only Mechanical and Strategic edits carry severity")
        note = str(it.get("pm_am_note", "")).strip()
        if cls == "Scope Change" and not note:
            errs.append(f"{p}: a Scope Change needs pm_am_note, one line for the PM/AM on what to discuss or decide")
        elif cls != "Scope Change" and "pm_am_note" in it:
            errs.append(f"{p}: only a Scope Change carries pm_am_note")
        # page
        if page in PAGE_WORDS:
            if page == "new page" and cls != "Scope Change":
                errs.append(f"{p}: 'new page' is a page the build does not have, so the item is a Scope Change")
        elif not page.startswith("/"):
            errs.append(f"{p}: page is a path like /about/, 'site-wide', or 'new page' (Scope Change only)")
        elif w5["urls"] and path_of(page) not in [path_of(u) for u in w5["urls"]] and cls != "Scope Change":
            errs.append(f"{p}: page '{page}' is not in the dev handoff index ({', '.join(w5['urls'])}); "
                        "a page the build lacks is a Scope Change")
        if src in bh and bh[src]["url"] and page not in PAGE_WORDS and page.startswith("/") \
                and path_of(page) != path_of(bh[src]["url"]):
            errs.append(f"{p}: BugHerd task {src.split(':')[1]} is on {path_of(bh[src]['url'])}, not {page}")
        if cls in TASK_CLASSES:
            fid = finding_id(page, fb)
            if fid in seen_ids:
                errs.append(f"{p}: same page and quote as item {seen_ids[fid]}; make them one item")
            seen_ids[fid] = n
    # every client task and every question is covered
    for key in bh:
        if not any(str(it.get("source", "email")) == key for it in items):
            errs.append(f"BugHerd task {key.split(':')[1]} has no item: every edit the client sent gets a class")
    if "email" in texts:
        quotes = [str(it.get("feedback", "")) for it in items if str(it.get("source", "email")) == "email"]
        for q in F.uncovered_questions(texts["email"], quotes):
            errs.append(f"the client's question is in no item's feedback quote: \"{q[:70]}\"")
    fact_errs, _ = F.validate_facts(plan, scope, own, F.norm(own))
    errs += fact_errs
    reply = plan.get("reply") or {}
    subj, body = str(reply.get("subject", "")).strip(), str(reply.get("body", "")).strip()
    if not subj or len(subj) > 90 or "\n" in subj:
        errs.append("reply subject must be one line of at most 90 characters")
    if not body:
        errs.append("reply body is empty")
    if F.SIGNOFF_TITLE.lower() in body.lower():
        errs.append("leave the sign-off out of the reply body; the script adds the AM's name and title")
    classes = [it.get("class") for it in items]
    errs += [f"reply: {e}" for e in reply_problems(body, own, scope["context_text"] + "\n" + w5["email_text"], classes)]
    blob = json.dumps(plan, ensure_ascii=False)
    for s in F.secrets_in(own):
        if s in blob:
            errs.append("the plan copies a login or password from the client's text; leave it out everywhere")
            break
    return errs


def reply_problems(body: str, own: str, sources: str, classes: list) -> list[str]:
    probs = []
    if not re.match(r"^(Hi|Hello|Dear) [^\n]+,\s*$", body.split("\n")[0] if body else ""):
        probs.append("first line must be the greeting, for example 'Hi Dana,'")
    words = len(re.findall(r"\b[\w'-]+\b", body))
    if words > F.MAX_REPLY_WORDS:
        probs.append(f"{words} words; keep it to {F.MAX_REPLY_WORDS}")
    low = body.lower()
    for b in F.BANNED_REPLY:
        if re.search(r"(?<![\w-])" + re.escape(b) + r"(?![\w-])", low):
            probs.append(f"uses '{b}'")
    for lab in F.INTERNAL_LABELS:
        m = re.search(lab, body if lab.startswith(r"\b") and lab[2].isupper() else low)
        if m:
            probs.append(f"internal label '{m.group(0)}' in the client's reply")
    for lab in INTERNAL_REPLY:
        m = re.search(lab, body)
        if m:
            probs.append(f"internal label '{m.group(0)}' in the client's reply")
    if F.ASK_SECRET_RE.search(body) and "never send" not in low:
        probs.append("asks the client to send a password or login; ask for an invite instead")
    sents = re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", body))
    if "Mechanical" in classes and not FIX_RE.search(body):
        probs.append("the client sent fixes we will make, so the reply confirms them (fix, correct, update, swap ...)")
    if "Strategic" in classes:
        if not (re.search(r"\bSEO\b", body) and re.search(r"(?i)\breview", body)):
            probs.append("a Strategic edit waits for SEO, so the reply says our SEO team will review it first")
        for s in sents:
            if STRATEGIC_WORDS.search(s) and F.DONE_RE.search(s):
                probs.append(f"says a Strategic edit is already made: \"{s[:80]}\"")
            elif STRATEGIC_WORDS.search(s) and F.COMMIT_RE.search(s) and not HOLD_RE5.search(s):
                probs.append(f"commits to a Strategic edit before SEO has reviewed it: \"{s[:80]}\"")
    if "Scope Change" in classes:
        if not CALL_RE.search(body):
            probs.append("a Scope Change is a conversation, so the reply offers a call about it")
        for s in sents:
            if re.search(r"(?i)\b(pages?|redesign|new feature|functionality)\b", s) and F.AGREE_RE.search(s) \
                    and not F.HOLD_RE.search(s) and not HOLD_RE5.search(s):
                probs.append(f"agrees to a Scope Change before the call: \"{s[:80]}\"")
    extra = F.numbers(body) - F.numbers(own) - F.numbers(sources)
    if extra:
        probs.append(f"number(s) {sorted(extra)} are in neither the client's text nor the context")
    return probs


# ---------- render ----------

def tasks_path(rep_path: Path) -> Path:
    return rep_path.with_name(rep_path.name.replace("-feedback.md", "-bugherd-tasks.json"))


def build_tasks(plan: dict, w5: dict, known: dict) -> list[dict]:
    base = staging_base(plan, w5)
    out = []
    for it in plan["items"]:
        if it["class"] not in TASK_CLASSES:
            continue
        page, quote, src = it["page"].strip(), it["feedback"].strip(), str(it.get("source", "email"))
        fid = finding_id(page, quote)
        dept = it["department"]
        guest_id = src.split(":", 1)[1] if src.startswith("bugherd:") else ""
        task_id = guest_id or known.get(fid, "")
        label = "Site-wide" if page == "site-wide" else page
        action = it["action"].strip().rstrip(".") + "."
        tail = " SEO reviews this before it is built." if it["class"] == "Strategic" else ""
        out.append({
            "finding_id": fid, "status": "NEW", "create": not task_id, "bugherd_task_id": task_id,
            "page_url": page_url(base, page), "department": dept,
            "column": w5["columns"].get(dept, DEFAULT_COLUMNS[dept]), "assignee": w5["assignees"].get(dept, ""),
            "severity": it["severity"], "bugherd_severity": BUGHERD_SEVERITY[it["severity"]],
            "title": f"{label}: {action}"[:200],
            "description": f"Client edit: \"{quote}\" {action}{tail} (Client edits {plan['date']}, {fid})"[:2000]})
    return out


def task_cell(it: dict, tasks_by_id: dict) -> str:
    if it["class"] not in TASK_CLASSES:
        return "none"
    fid = finding_id(it["page"].strip(), it["feedback"].strip())
    t = tasks_by_id.get(fid)
    return fid + (f" (BugHerd #{t['bugherd_task_id']})" if t and t["bugherd_task_id"] else "")


def render_report(plan: dict, scope: dict, w5: dict, tasks: list[dict], tpath: Path, updates_name: str | None,
                  had_secrets: bool) -> str:
    items = plan["items"]
    root = w5["root"]
    count = {c: sum(1 for i in items if i["class"] == c) for c in CLASSES}
    depts = {d: sum(1 for i in items if i["department"] == d) for d in DEPARTMENTS}
    approved = [("Site-wide" if i["page"] == "site-wide" else i["page"]) for i in items if i["class"] == "Approval"]
    strat = [n for n, i in enumerate(items, 1) if i["class"] == "Strategic"]
    scopes = [n for n, i in enumerate(items, 1) if i["class"] == "Scope Change"]
    to_create = sum(1 for t in tasks if t["create"])
    nfacts = len(plan.get("facts", []) or [])
    head = [f"Client: {scope['client']}", f"Date: {plan['date']}", f"From: {plan['from']}",
            f"Scope source: {scope['source']} ({scope['sow_pages_line']})", "Week: 5",
            f"Staging: {staging_base(plan, w5)}",
            f"BugHerd export: {rel(root, w5['bugherd']) if w5['bugherd'] else 'none'}",
            f"Dev handoff index: {w5['index'] or 'not found'}",
            f"Week 5 email: {w5['email'] or 'not found'}" + (f" (reply by {w5['reply_by']})" if w5["reply_by"] else ""),
            f"BugHerd tasks: {rel(root, tpath)}"]
    out = head + ["", f"# {scope['client']}: client staging edits, {plan['date']}", "", "## Summary", "",
                  f"- Items: {len(items)} (" + ", ".join(f"{count[c]} {c}" for c in CLASSES) + ")",
                  "- By department: " + ", ".join(f"{d} {depts[d]}" for d in DEPARTMENTS),
                  "- Approved: " + ("; ".join(approved) if approved else "nothing stated"),
                  f"- BugHerd tasks: {len(tasks)} ({to_create} to create, {len(tasks) - to_create} already in BugHerd); "
                  "Scope Changes, Questions and Approvals get none",
                  "- SEO review: " + (f"items {', '.join('#' + str(n) for n in strat)} wait for SEO before they are built"
                                      if strat else "none needed"),
                  "- Scope Changes: " + (f"items {', '.join('#' + str(n) for n in scopes)} go to the PM/AM"
                                         if scopes else "none"),
                  "- Context updates: " + (f"{nfacts} facts in `{updates_name}`; merge them with client-context-update"
                                           if nfacts else "none (the client stated no new facts)")]
    if had_secrets:
        out.append("- Left out: the client's text contains login details; none were copied into these files")
    by_id = {t["finding_id"]: t for t in tasks}
    out += ["", "## Feedback Items", "", TABLE_HEADER, "|" + "---|" * len(TABLE_COLUMNS)]
    for n, i in enumerate(items, 1):
        fb = re.sub(r"\s+", " ", i["feedback"]).strip()
        pg = i["page"].strip()
        cell = pg if pg in PAGE_WORDS else page_url(staging_base(plan, w5), pg)
        out.append(f"| {n} | \"{fb}\" | {source_cell(str(i.get('source', 'email')))} | {cell} | {i['class']} | "
                   f"{i['department']} | {i['action'].strip()} | {task_cell(i, by_id)} |")
    out += ["", "## SEO Review", ""]
    if strat:
        out += [SEO_HOLD, ""] + [f"- #{n} {items[n - 1]['page'].strip()}: {items[n - 1]['action'].strip()}"
                                 for n in strat]
    else:
        out.append(SEO_CLEAR)
    out += ["", "## Scope Changes", ""]
    if scopes:
        out += [f"- #{n} {items[n - 1]['page'].strip()}: PM/AM: {items[n - 1]['pm_am_note'].strip()}" for n in scopes]
    else:
        out.append(SCOPE_CLEAR)
    am = str(plan.get("am", "")).strip() or F.AM_PLACEHOLDER
    out += ["", "## Reply Draft", "", f"Subject: {plan['reply']['subject'].strip()}", "",
            plan["reply"]["body"].strip(), "", am, F.SIGNOFF_TITLE]
    return "\n".join(out) + "\n"


def render(kdir: Path, plan: dict, scope: dict, raw: str, w5: dict, dry_run: bool) -> int:
    errs = validate(plan, scope, raw, w5)
    if errs:
        print("PLAN REJECTED")
        for e in errs:
            print(f"- {e}")
        return 1
    if dry_run:
        print("PLAN OK")
        return 0
    up = F.build_updates(plan, scope)
    rep_path, up_path = F.out_paths(kdir, plan["date"], plan["from"])
    tpath = tasks_path(rep_path)
    known = {}
    if tpath.exists():
        try:
            known = {t["finding_id"]: t.get("bugherd_task_id", "") for t in json.loads(F.read(tpath))
                     if t.get("bugherd_task_id")}
        except (json.JSONDecodeError, TypeError, KeyError):
            known = {}
    tasks = build_tasks(plan, w5, known)
    rep_path.parent.mkdir(parents=True, exist_ok=True)
    has_facts = bool(up["rows"])
    own = all_own(client_texts(raw, w5))
    rep_path.write_text(render_report(plan, scope, w5, tasks, tpath, up_path.name if has_facts else None,
                                      bool(F.secrets_in(own))), encoding="utf-8")
    tpath.write_text(json.dumps(tasks, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if has_facts:
        up_path.write_text(F.render_updates(up), encoding="utf-8")
    elif up_path.exists():
        up_path.unlink()
    print(f"WROTE {rep_path}")
    print(f"WROTE {tpath}")
    if has_facts:
        print(f"WROTE {up_path}")
    return check(kdir, raw, rep_path, w5)


# ---------- check ----------

def check(kdir: Path, raw: str, rep_path: Path, w5: dict) -> int:
    scope = F.scope_info(kdir)
    rep = F.read(rep_path)
    texts = client_texts(raw, w5)
    own = all_own(texts)
    res: list[tuple[str, bool, str]] = []
    heads = {k: (re.search(rf"(?m)^{k}:[ \t]*(.+?)\s*$", rep) or [None, ""])[1]
             for k in ("Client", "Date", "From", "Week", "Staging", "BugHerd tasks")}
    res.append(("header lines", all(heads.values()) and heads["Client"] == scope["client"] and heads["Week"] == "5",
                f"Client: {heads['Client'] or '-'}; Staging: {heads['Staging'] or '-'}"))
    found = re.findall(r"(?m)^## (.+?)\s*$", rep)
    res.append(("sections in order", found == SECTIONS, ", ".join(found)))
    rows = F.parse_table(rep, TABLE_HEADER)
    bad = []
    if rows is None:
        bad.append("table header missing")
        rows = []
    good = []
    for k, r in enumerate(rows, 1):
        if len(r) != len(TABLE_COLUMNS):
            bad.append(f"row {k} has {len(r)} cells")
            continue
        good.append(r)
        if r[0] != str(k):
            bad.append(f"row {k} numbered {r[0]}")
        if r[4] not in CLASSES or r[5] not in DEPARTMENTS:
            bad.append(f"row {k} has a class or department outside the enums")
        elif r[4] == "Strategic" and r[5] != "SEO" or r[4] == "Mechanical" and r[5] not in MECH_DEPTS \
                or r[4] not in TASK_CLASSES and r[5] != "Account Management":
            bad.append(f"row {k}: {r[4]} cannot go to {r[5]}")
        if (r[4] in TASK_CLASSES) != bool(re.match(r"^CE-[0-9a-f]{8}\b", r[7])):
            bad.append(f"row {k}: Task is a CE- id for Mechanical and Strategic edits and none otherwise")
    res.append(("feedback table", bool(rows) and not bad, "; ".join(bad[:3]) or f"{len(rows)} rows"))
    nv = []
    for k, r in enumerate(good, 1):
        src = "email" if r[2] == "email" else "bugherd:" + r[2].replace("BugHerd #", "")
        if src not in texts or F.norm(r[1].strip('"')) not in F.norm(texts[src]):
            nv.append(r[0])
    res.append(("quotes verbatim", not nv, f"rows {', '.join(nv)} not in the client's text for their source"
                if nv else "every Feedback cell is the client's words"))
    missing_bh = [t["task_id"] for t in w5["bugherd_tasks"] if not any(r[2] == f"BugHerd #{t['task_id']}" for r in good)]
    uncovered = F.uncovered_questions(texts["email"], [r[1].strip('"') for r in good if r[2] == "email"]) \
        if "email" in texts else []
    res.append(("every edit classed", not missing_bh and not uncovered,
                (f"BugHerd task(s) {', '.join(missing_bh)} have no row; " if missing_bh else "")
                + "; ".join(f'"{q[:50]}"' for q in uncovered[:2])
                or f"{len(w5['bugherd_tasks'])} BugHerd task(s) and every email question have a row"))
    classes = [r[4] for r in good]
    summ = re.search(r"(?m)^- Items: (\d+) \(" + ", ".join(rf"(\d+) {c}" for c in CLASSES) + r"\)", rep)
    want = [len(rows)] + [classes.count(c) for c in CLASSES]
    res.append(("summary counts", bool(summ) and [int(x) for x in summ.groups()] == want, f"table: {want}"))
    seo = (re.search(r"(?ms)^## SEO Review\s*\n(.*?)(?=^## )", rep) or [None, ""])[1]
    want_s = [r[0] for r in good if r[4] == "Strategic"]
    listed_s = re.findall(r"(?m)^- #(\d+) ", seo)
    res.append(("SEO review", (listed_s == want_s and SEO_HOLD in seo) if want_s else SEO_CLEAR in seo,
                f"{len(want_s)} Strategic row(s) wait for SEO" if want_s else "no Strategic rows"))
    sc = (re.search(r"(?ms)^## Scope Changes\s*\n(.*?)(?=^## )", rep) or [None, ""])[1]
    want_c = [r[0] for r in good if r[4] == "Scope Change"]
    listed_c = re.findall(r"(?m)^- #(\d+) [^\n]*?: PM/AM: \S", sc)
    res.append(("Scope Changes", listed_c == want_c if want_c else SCOPE_CLEAR in sc,
                f"{len(want_c)} Scope Change row(s), each with a PM/AM note" if want_c else "no Scope Change rows"))
    res.append(task_result(rep_path, rep, good, heads["Staging"]))
    up_path = rep_path.with_name(rep_path.name.replace("-feedback.md", "-feedback-updates.md"))
    res.append(F.updates_result(up_path, rep, F.norm(own), 0))
    secrets = F.secrets_in(own)
    blob = rep + (F.read(up_path) if up_path.exists() else "") + \
        (F.read(tasks_path(rep_path)) if tasks_path(rep_path).exists() else "")
    leaked = [s for s in secrets if s in blob]
    res.append(("no secrets copied", not leaked, "a login or password from the client's text was copied" if leaked else
                (f"{len(secrets)} left out" if secrets else "none in the client's text")))
    reply = (re.search(r"(?ms)^## Reply Draft\s*\n(.*)\Z", rep) or [None, ""])[1].strip()
    rl = reply.split("\n")
    subj_ok = bool(rl) and rl[0].startswith("Subject: ") and len(rl[0]) <= 99
    sign_ok = len(rl) >= 2 and rl[-1] == F.SIGNOFF_TITLE and rl[-2].strip() != ""
    body = "\n".join(rl[2:-2]).strip() if len(rl) > 4 else ""
    probs = reply_problems(body, own, scope["context_text"] + "\n" + w5["email_text"], classes)
    if not subj_ok:
        probs.insert(0, "no Subject: line")
    if not sign_ok:
        probs.insert(0, "sign-off must be the AM's name then the title")
    res.append(("reply draft", not probs, "; ".join(probs[:3]) or "greeting, voice, numbers and sign-off fine"))
    if len(rl) >= 2 and rl[-2].strip() == F.AM_PLACEHOLDER:
        res.append(("AM name", True, "placeholder: fill in the AM's name before sending"))
    print("| Check | Result | Detail |")
    print("|---|---|---|")
    for name, ok, detail in res:
        print(f"| {name} | {'PASS' if ok else 'FAIL'} | {detail} |")
    passed = all(ok for _, ok, _ in res)
    print(f"RESULT: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


def task_result(rep_path: Path, rep: str, rows: list[list[str]], staging: str) -> tuple[str, bool, str]:
    tpath = tasks_path(rep_path)
    if not tpath.exists():
        return ("BugHerd task file", False, f"{tpath.name} not found")
    try:
        tasks = json.loads(F.read(tpath))
    except json.JSONDecodeError as e:
        return ("BugHerd task file", False, f"not valid JSON: {e}")
    errs = []
    want = [r for r in rows if r[4] in TASK_CLASSES]
    if not isinstance(tasks, list) or len(tasks) != len(want):
        errs.append(f"{len(tasks) if isinstance(tasks, list) else '?'} task(s) for {len(want)} Mechanical/Strategic row(s)")
        tasks = tasks if isinstance(tasks, list) else []
    for t, r in zip(tasks, want):
        if not isinstance(t, dict) or list(t) != TASK_KEYS:
            errs.append(f"task for row {r[0]} does not have staging-site-qa's keys in order")
            continue
        if not r[7].startswith(t["finding_id"]):
            errs.append(f"row {r[0]} Task is not {t['finding_id']}")
        if t["department"] != r[5]:
            errs.append(f"task {t['finding_id']} department differs from row {r[0]}")
        if t["status"] != "NEW" or t["create"] != (not t["bugherd_task_id"]):
            errs.append(f"task {t['finding_id']}: status NEW, create true only without a bugherd_task_id")
        if r[2].startswith("BugHerd #") and t["bugherd_task_id"] != r[2].replace("BugHerd #", ""):
            errs.append(f"task {t['finding_id']} comes from {r[2]} but does not carry its id")
        if t["severity"] not in SEVERITIES or t["bugherd_severity"] != BUGHERD_SEVERITY.get(t["severity"]):
            errs.append(f"task {t['finding_id']}: severity values")
        if r[4] == "Strategic" and t["department"] != "SEO":
            errs.append(f"task {t['finding_id']}: a Strategic edit is an SEO task")
        if not str(t["column"]).strip():
            errs.append(f"task {t['finding_id']}: no column")
        if staging and not str(t["page_url"]).startswith(staging):
            errs.append(f"task {t['finding_id']}: page_url is not on {staging}")
        if INTERNAL_TASK.search(str(t["title"]) + " " + str(t["description"])):
            errs.append(f"task {t['finding_id']}: internal wording in client-visible text")
    named = re.search(r"(?m)^BugHerd tasks:\s*(\S+)", rep)
    if not named or not named.group(1).endswith(tpath.name):
        errs.append("the header's BugHerd tasks line does not name this file")
    return ("BugHerd task file", not errs, "; ".join(errs[:3]) or
            f"{len(tasks)} task(s) in staging-site-qa's format, {sum(1 for t in tasks if t.get('create'))} to create")


def created(tpath: Path, pairs: list[str]) -> int:
    """Record the BugHerd ids of tasks created after the go, so a re-render keeps them."""
    tasks = json.loads(F.read(tpath))
    ids = {}
    for p in pairs:
        fid, _, tid = p.partition("=")
        if not re.match(r"^CE-[0-9a-f]{8}$", fid) or not tid.strip():
            raise SystemExit(f"ERROR: '{p}' must be CE-xxxxxxxx=<BugHerd task id>")
        ids[fid] = tid.strip()
    unknown = sorted(set(ids) - {t["finding_id"] for t in tasks})
    if unknown:
        raise SystemExit(f"ERROR: not in {tpath.name}: {', '.join(unknown)}")
    for t in tasks:
        if t["finding_id"] in ids:
            t["bugherd_task_id"], t["create"] = ids[t["finding_id"]], False
    tpath.write_text(json.dumps(tasks, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"RECORDED {len(ids)} BugHerd id(s) in {tpath}; {sum(1 for t in tasks if t['create'])} still to create")
    return 0


# ---------- contract ----------

def contract(rep_path: Path) -> dict:
    """What week-5-handoff-check reads: the class column and the task file."""
    rep = F.read(rep_path)
    rows = F.parse_table(rep, TABLE_HEADER) or []
    sc = (re.search(r"(?ms)^## Scope Changes\s*\n(.*?)(?=^## )", rep) or [None, ""])[1]
    notes = dict(re.findall(r"(?m)^- #(\d+) [^\n]*?: PM/AM: (.+?)\s*$", sc))
    tpath = tasks_path(rep_path)
    tasks = json.loads(F.read(tpath)) if tpath.exists() else []
    return {"Week:": (re.search(r"(?m)^Week:\s*(\S+)", rep) or [None, ""])[1],
            "Class": [{"#": r[0], "Class": r[4], "Department": r[5], "Task": r[7],
                       "PM/AM note": notes.get(r[0], "")} for r in rows if len(r) == len(TABLE_COLUMNS)],
            "tasks": [{k: t[k] for k in ("finding_id", "status", "create", "bugherd_task_id", "department",
                                          "column", "severity")} for t in tasks]}


def validate_contract(data: dict) -> list[str]:
    bad = [k for k in ("Week:", "Class", "tasks") if k not in data]
    if bad:
        return bad
    if data["Week:"] != "5":
        bad.append("Week: 5")
    for r in data["Class"]:
        if r.get("Class") not in CLASSES:
            bad.append(f"row {r.get('#')} Class")
        if r.get("Class") == "Scope Change" and not r.get("PM/AM note"):
            bad.append(f"row {r.get('#')} PM/AM note")
    ids = {t.get("finding_id") for t in data["tasks"]}
    for r in data["Class"]:
        if r.get("Class") in TASK_CLASSES and r.get("Task", "")[:11] not in ids:
            bad.append(f"row {r.get('#')} task")
    return bad
