#!/usr/bin/env python3
"""Sort client feedback on Week 1 deliverables into a feedback file, an updates file and a reply draft.

Usage:
  python3 feedback.py scope kickoff/<slug>
  python3 feedback.py render kickoff/<slug> --feedback <client text file> --plan feedback-plan.json [--dry-run]
  python3 feedback.py check kickoff/<slug> --feedback <client text file> --report feedback/<slug>/<file>-feedback.md
  python3 feedback.py updates-json kickoff/<slug> --feedback <client text file> --plan feedback-plan.json

scope         prints the scope source from <slug>-context.md as JSON (source, SOW pages, services, quote lines).
render        validates the plan against the client's text and the scope source, writes
              feedback/<slug>/<date>-feedback.md and, when the plan has facts,
              feedback/<slug>/<date>-feedback-updates.md, then runs check. --dry-run writes nothing.
check         re-reads the written files and prints a `| Check | Result | Detail |` table and
              `RESULT: PASS` or `RESULT: FAIL` (exit 0 or 1).
updates-json  prints the updates the plan would write as JSON (keys Client, Source, Date, From, rows).

Standard library only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

TYPES = ["content", "design", "scope", "question", "approval"]
AFFECTS = ["homepage copy", "homepage design", "site scope", "client context", "timeline",
           "platform access", "intake items", "other"]
IMPACTS = ["none", "low", "medium", "high"]
OWNERS = ["AM", "Content", "Design", "SEO", "Dev"]
VERDICTS = ["outside", "unclear", "within"]
VERDICT_TEXT = {
    "outside": ("outside scope", "The build follows the scope source until a signed change order."),
    "unclear": ("to confirm", "The AM confirms with Sales before anything is promised; the build follows the scope source until then."),
    "within": ("within scope", "Fits the current scope."),
}
TABLE_COLUMNS = ["#", "Feedback", "Type", "Affects", "Impact", "Action", "Owner"]
TABLE_HEADER = "| " + " | ".join(TABLE_COLUMNS) + " |"
REPORT_SECTIONS = ["Summary", "Feedback Items", "Scope Check", "Reply Draft"]

CONTEXT_HEADINGS = ["Snapshot", "Business Overview", "Services", "Customers and Service Area",
                    "Goals and Conversion", "Differentiators and Proof", "Competitors", "Website Today",
                    "Scope Summary"]
UPDATES_SECTIONS = CONTEXT_HEADINGS + ["Platform Access", "Intake Items"]
UPDATES_COLUMNS = ["#", "Section", "Fact", "Evidence"]
UPDATES_HEADER = "| " + " | ".join(UPDATES_COLUMNS) + " |"
INTAKE_ITEMS = ["Primary contact", "Website approver", "Business name, address, phone and hours",
                "Logo files", "Brand guidelines", "Photos", "Testimonials or reviews", "Team members",
                "Certifications, awards and memberships", "Legal or compliance language",
                "Sites they like", "Things to avoid", "Gap question answers"]
INTAKE_STATUSES = ["received", "partial", "missing", "none", "n/a"]
PLATFORMS = ["Domain", "Hosting", "Website login", "Google Analytics", "Google Search Console",
             "Google Business Profile", "Google Tag Manager", "Google Ads", "Meta ads", "Microsoft Ads",
             "CRM, forms or call tracking"]
# A client can't confirm access; only WISE can, so `confirmed` never comes from client feedback.
CLIENT_ACCESS_STATUSES = ["invite sent", "needs help", "someone else manages it", "not set up",
                          "not sure", "no answer", "n/a"]

SIGNOFF_TITLE = "Account Manager, WISE Digital Partners"
AM_PLACEHOLDER = "[AM name]"
MAX_QUOTE = 300
MAX_REPLY_WORDS = 300
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TAG_END_RE = re.compile(r"\[[a-z]+(?:,\s*[a-z]+)*\]\s*$")

BANNED_REPLY = ["thrilled", "delighted", "excited", "don't hesitate", "do not hesitate", "world-class",
                "best-in-class", "rest assured", "as per", "per our", "touch base", "circle back",
                "no problem", "absolutely", "guarantee", "synergy"]
INTERNAL_LABELS = [r"\bGAP\b", r"\bCONFLICT\b", r"\bSCOPE\b", r"\bR\d+\b", r"scope source", r"change log",
                   r"intake item", r"updates file", r"client context", r"feedback table"]
SCOPE_WORDS = re.compile(r"(?i)change order|\bquote\b|\bestimate\b")
AGREE_RE = re.compile(r"(?i)\b(we'll|we will|happy to|we can|can)\s+(add|build|create|include|set up)\b")
HOLD_RE = re.compile(r"(?i)(\bnot\b|n't\b|\bchange order\b|\bquote\b|\bestimate\b|\bcost\b|\bwhether\b|\boutside\b|\bbeyond\b)")
ASK_SECRET_RE = re.compile(r"(?i)\bsend\b[^.?!\n]{0,20}\b(password|passcode|login details|credentials)\b")
SECRET_RE = re.compile(r"(?i)\b(password|passcode|pin|login|username|user name|pw|pwd|pass|code)\s*(?:is\s+|:\s*|=\s*|\s)([^\s,;]+)")
SECRET_PAIR_RE = re.compile(r"(?i)\b(?:login|username|user|account)\b[^\n]{0,30}?[:=]\s*(\S+)\s*/\s*(\S+)")
SECRET_STOP = {"the", "a", "an", "attached", "below", "above", "required", "here", "in", "on", "same", "my", "our",
               "is", "to", "for", "and", "or", "thing", "it", "that", "this", "you", "we", "of", "by", "with"}
HEADER_LINE_RE = re.compile(r"^(From|To|Cc|Bcc|Date|Sent|Subject|Reply-To):", re.I)
HISTORY_RE = re.compile(r"^(On .{5,200} wrote:\s*$|-{2,}\s*Original Message|_{5,}|From:\s)", re.I)
SMALL_TALK_RE = re.compile(r"(?i)^(hope\b|how are you|how's (your|the|things|it)|how was your)")


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8").replace("\r\n", "\n")


def norm(s: str) -> str:
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = s.replace("—", "-").replace("–", "-")
    return re.sub(r"\s+", " ", s).strip().lower()


def own_text(raw: str) -> str:
    """The client's own words: email headers at the top, quoted history and '>' lines removed."""
    lines = raw.split("\n")
    i = 0
    while i < len(lines) and (HEADER_LINE_RE.match(lines[i]) or (not lines[i].strip() and i < 8 and any(
            HEADER_LINE_RE.match(x) for x in lines[:i]))):
        i += 1
    out = []
    for ln in lines[i:]:
        if HISTORY_RE.match(ln.strip()) and out:
            break
        if ln.lstrip().startswith(">"):
            continue
        out.append(ln)
    return "\n".join(out).strip()


def secrets_in(text: str) -> list[str]:
    """Values that look like a login or password the client typed, so no file repeats them."""
    vals = []
    for m in SECRET_RE.finditer(text):
        v = m.group(2).strip("\"'.!?)(")
        loose = m.group(1).lower() in ("pw", "pwd", "pass", "code")
        if len(v) < 3 or v.lower() in SECRET_STOP or (loose and v.isalpha()):
            continue
        vals.append(v)
    for m in SECRET_PAIR_RE.finditer(text):
        vals += [g.strip("\"'.!?)(") for g in m.groups() if len(g.strip("\"'.!?)(")) >= 3]
    return vals


def questions_in(text: str) -> list[str]:
    qs = []
    for para in re.split(r"\n\s*\n", text):
        para = re.sub(r"\s+", " ", para).strip()
        for sent in re.split(r"(?<=[.!?])\s+", para):
            if sent.endswith("?") and len(sent) > 6 and not SMALL_TALK_RE.match(sent):
                qs.append(sent)
    return qs


def uncovered_questions(own: str, quotes: list[str]) -> list[str]:
    return [q for q in questions_in(own)
            if not any(norm(q) in norm(x) or (len(x) >= 15 and norm(x) in norm(q)) for x in quotes)]


def numbers(text: str) -> set[str]:
    return set(re.findall(r"\d+", text))


# ---------- kickoff folder ----------

def kickoff_files(kdir: Path) -> tuple[str, Path]:
    slug = kdir.name
    ctx = kdir / f"{slug}-context.md"
    if not ctx.exists():
        raise SystemExit(f"ERROR: {ctx} not found; new-build-kickoff runs first.")
    return slug, ctx


def scope_info(kdir: Path) -> dict:
    slug, ctx = kickoff_files(kdir)
    text = read(ctx)
    client = (re.search(r"(?m)^Client:\s*(.+?)\s*$", text) or [None, ""])[1]
    sec = re.search(r"(?ms)^## Scope Summary\s*\n(.*?)(?=^## |\Z)", text)
    body = sec.group(1) if sec else ""
    m = re.search(r"(?m)^SOW pages:\s*(\S+)(?:\s*\[([a-z, ]+)\])?", body)
    pages = m.group(1) if m else "unknown"
    tags = {t.strip() for t in (m.group(2) or "").split(",")} if m else set()
    source = "SOW" if "sow" in tags else ("deal terms" if "notes" in tags else "unknown")
    svc = re.search(r"(?m)^Included services:\s*(.+?)\s*$", body)
    quotes = [ln[1:].strip() for ln in body.split("\n") if ln.startswith(">")]
    bullets = [ln[2:].strip() for ln in body.split("\n") if ln.startswith("- ")]
    return {"client": client, "slug": slug, "source": source, "sow_pages": pages,
            "sow_pages_line": f"SOW pages: {pages}",
            "included_services": TAG_END_RE.sub("", svc.group(1)).strip() if svc else "",
            "scope_quotes": [TAG_END_RE.sub("", q).strip() for q in quotes],
            "scope_bullets": bullets, "context_text": text}


# ---------- plan ----------

def validate_plan(plan: dict, scope: dict, raw: str) -> list[str]:
    errs: list[str] = []
    own = own_text(raw)
    own_n = norm(own)
    secrets = secrets_in(own)
    for k in ("date", "from", "contact", "items", "reply"):
        if k not in plan:
            errs.append(f"plan is missing '{k}'")
    if errs:
        return errs
    if not DATE_RE.match(str(plan["date"])):
        errs.append(f"date '{plan['date']}' must be YYYY-MM-DD")
    if not str(plan["contact"]).strip():
        errs.append("contact must name the person who wrote the feedback")
    items = plan["items"]
    if not isinstance(items, list) or not items:
        errs.append("items must be a non-empty list")
        items = []
    open_scope = 0
    for n, it in enumerate(items, 1):
        p = f"item {n}"
        fb = str(it.get("feedback", ""))
        if not fb.strip():
            errs.append(f"{p}: feedback is empty")
        elif norm(fb) not in own_n:
            errs.append(f"{p}: feedback is not a verbatim quote of the client's own text: \"{fb[:60]}\"")
        if len(fb) > MAX_QUOTE:
            errs.append(f"{p}: feedback quote is {len(fb)} characters; cut it to the words that matter (max {MAX_QUOTE})")
        for key in ("feedback", "action"):
            if "|" in str(it.get(key, "")) or "\n" in str(it.get(key, "")).strip():
                errs.append(f"{p}: {key} must be one line without '|'")
        t, a, imp, own_ = it.get("type"), str(it.get("affects", "")), it.get("impact"), it.get("owner")
        if t not in TYPES:
            errs.append(f"{p}: type '{t}' is not one of {TYPES}")
        if a.split(":")[0].strip() not in AFFECTS:
            errs.append(f"{p}: affects '{a}' must start with one of {AFFECTS}")
        if imp not in IMPACTS:
            errs.append(f"{p}: impact '{imp}' is not one of {IMPACTS}")
        if own_ not in OWNERS:
            errs.append(f"{p}: owner '{own_}' is not one of {OWNERS}")
        if not str(it.get("action", "")).strip():
            errs.append(f"{p}: action is empty")
        if t == "approval" and imp != "none":
            errs.append(f"{p}: an approval has impact none")
        if t == "question" and imp not in ("none", "low"):
            errs.append(f"{p}: a question has impact none or low")
        if t == "scope":
            if not a.startswith("site scope"):
                errs.append(f"{p}: a scope item affects 'site scope'")
            if imp != "high":
                errs.append(f"{p}: a scope item has impact high")
            v = it.get("verdict")
            if v not in VERDICTS:
                errs.append(f"{p}: a scope item needs verdict, one of {VERDICTS}")
            if not str(it.get("basis", "")).strip():
                errs.append(f"{p}: a scope item needs basis, one sentence comparing the request with the scope source")
            pages = it.get("pages")
            if pages is not None and not isinstance(pages, int):
                errs.append(f"{p}: pages must be a whole number or null")
            sow = scope["sow_pages"]
            if isinstance(pages, int) and sow.isdigit() and pages > int(sow) and v != "outside":
                errs.append(f"{p}: {pages} pages is more than SOW pages: {sow}, so the verdict is outside")
            if v == "within" and not sow.isdigit():
                errs.append(f"{p}: the scope source states no page count (SOW pages: {sow}), so the verdict cannot be within")
            if v in ("outside", "unclear"):
                open_scope += 1
                if own_ != "AM":
                    errs.append(f"{p}: a scope request outside or unclear is owned by the AM")
        elif "verdict" in it or "pages" in it:
            errs.append(f"{p}: only scope items carry verdict or pages")
    quotes = [str(it.get("feedback", "")) for it in items]
    for q in uncovered_questions(own, quotes):
        errs.append(f"the client's question is in no item's feedback quote: \"{q[:70]}\"")
    facts = plan.get("facts", []) or []
    conflicts = 0
    for n, f in enumerate(facts, 1):
        p = f"fact {n}"
        sec, fact, ev = f.get("section"), str(f.get("fact", "")).strip(), str(f.get("evidence", "")).strip()
        if sec not in UPDATES_SECTIONS:
            errs.append(f"{p}: section '{sec}' is not one of {UPDATES_SECTIONS}")
        if not fact or not ev:
            errs.append(f"{p}: fact and evidence must not be empty")
        if "|" in fact + ev or "\n" in fact + ev:
            errs.append(f"{p}: fact and evidence must be one line without '|'")
        if TAG_END_RE.search(fact):
            errs.append(f"{p}: leave the source tag off the fact; client-context-update adds it")
        if ev and norm(ev) not in own_n:
            errs.append(f"{p}: evidence is not a verbatim quote of the client's own text: \"{ev[:60]}\"")
        if len(ev) > MAX_QUOTE:
            errs.append(f"{p}: evidence is {len(ev)} characters (max {MAX_QUOTE})")
        extra = numbers(fact) - numbers(own) - numbers(scope["context_text"]) - numbers(str(plan["date"]))
        if extra:
            errs.append(f"{p}: number(s) {sorted(extra)} are in neither the client's text nor the context")
        if sec == "Platform Access":
            m = re.match(r"^(.+?):\s*([a-z /'-]+?)(?:[,;(]|$)", fact)
            if not m or m.group(1) not in PLATFORMS:
                errs.append(f"{p}: a Platform Access fact starts '<platform>: <status>' with a platform from {PLATFORMS}")
            elif m.group(2).strip() not in CLIENT_ACCESS_STATUSES:
                errs.append(f"{p}: status '{m.group(2).strip()}' must be one of {CLIENT_ACCESS_STATUSES} "
                            "(only WISE confirms access)")
        if sec == "Intake Items":
            m = re.match(r"^(.+?):\s*([a-z/]+)", fact)
            if not m or m.group(1) not in INTAKE_ITEMS:
                errs.append(f"{p}: an Intake Items fact starts '<item>: <status>' with an item from {INTAKE_ITEMS}")
            elif m.group(2) not in INTAKE_STATUSES:
                errs.append(f"{p}: status '{m.group(2)}' must be one of {INTAKE_STATUSES}")
        if sec == "Scope Summary" and fact.startswith("CONFLICT:"):
            conflicts += 1
            if "until a signed change" not in fact:
                errs.append(f"{p}: a scope CONFLICT says the build follows the scope source until a signed change")
    if conflicts < open_scope:
        errs.append(f"{open_scope} scope request(s) are outside or unclear but only {conflicts} Scope Summary "
                    "CONFLICT fact(s); add one per request so client-context-update logs it")
    reply = plan.get("reply") or {}
    subj, body = str(reply.get("subject", "")).strip(), str(reply.get("body", "")).strip()
    if not subj or len(subj) > 90 or "\n" in subj:
        errs.append("reply subject must be one line of at most 90 characters")
    if not body:
        errs.append("reply body is empty")
    if SIGNOFF_TITLE.lower() in body.lower():
        errs.append("leave the sign-off out of the reply body; the script adds the AM's name and title")
    errs += [f"reply: {e}" for e in reply_problems(body, own, scope["context_text"], open_scope > 0)]
    blob = json.dumps(plan, ensure_ascii=False)
    for s in secrets:
        if s in blob:
            errs.append("the plan copies a login or password from the client's text; leave it out everywhere")
            break
    return errs


def reply_problems(body: str, own: str, context: str, has_open_scope: bool) -> list[str]:
    probs = []
    if not re.match(r"^(Hi|Hello|Dear) [^\n]+,\s*$", body.split("\n")[0] if body else ""):
        probs.append("first line must be the greeting, for example 'Hi Tom,'")
    words = len(re.findall(r"\b[\w'-]+\b", body))
    if words > MAX_REPLY_WORDS:
        probs.append(f"{words} words; keep it to {MAX_REPLY_WORDS}")
    low = body.lower()
    for b in BANNED_REPLY:
        if re.search(r"(?<![\w-])" + re.escape(b) + r"(?![\w-])", low):
            probs.append(f"uses '{b}'")
    for lab in INTERNAL_LABELS:
        m = re.search(lab, body if lab.startswith(r"\b") and lab[2].isupper() else low)
        if m:
            probs.append(f"internal label '{m.group(0)}' in the client's reply")
    if ASK_SECRET_RE.search(body) and "never send" not in low:
        probs.append("asks the client to send a password or login; ask for an invite instead")
    if has_open_scope:
        if not SCOPE_WORDS.search(body):
            probs.append("a scope request is outside or unclear, so the reply says it is beyond the current agreement "
                         "and names the next step as a change order, quote or estimate")
        for sent in re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", body)):
            if re.search(r"(?i)\bpages?\b", sent) and AGREE_RE.search(sent) and not HOLD_RE.search(sent):
                probs.append(f"agrees to extra pages: \"{sent[:80]}\"")
    allowed = numbers(own) | numbers(context)
    extra = numbers(body) - allowed
    if extra:
        probs.append(f"number(s) {sorted(extra)} are in neither the client's text nor the context")
    return probs


# ---------- render ----------

def out_paths(kdir: Path, date: str, src: str) -> tuple[Path, Path]:
    fdir = kdir.parent.parent / "feedback" / kdir.name
    n = 1
    while True:
        stem = date if n == 1 else f"{date}-{n}"
        rep = fdir / f"{stem}-feedback.md"
        if not rep.exists():
            break
        m = re.search(r"(?m)^From:\s*(.+?)\s*$", read(rep))
        if m and m.group(1) == src:
            break
        n += 1
    return rep, fdir / f"{stem}-feedback-updates.md"


def build_updates(plan: dict, scope: dict) -> dict:
    rows = []
    for n, f in enumerate(plan.get("facts", []) or [], 1):
        rows.append({"#": str(n), "Section": f["section"], "Fact": f["fact"].strip(),
                     "Evidence": f"{plan['contact']} (email): \"{f['evidence'].strip()}\""})
    return {"Client": scope["client"], "Source": "client", "Date": plan["date"], "From": plan["from"], "rows": rows}


def render_updates(up: dict) -> str:
    lines = [f"Client: {up['Client']}", f"Source: {up['Source']}", f"Date: {up['Date']}", f"From: {up['From']}",
             "", "## Updates", "", UPDATES_HEADER, "|---|---|---|---|"]
    lines += [f"| {r['#']} | {r['Section']} | {r['Fact']} | {r['Evidence']} |" for r in up["rows"]]
    return "\n".join(lines) + "\n"


def render_report(plan: dict, scope: dict, updates_name: str | None, had_secrets: bool) -> str:
    items = plan["items"]
    count = {t: sum(1 for i in items if i["type"] == t) for t in TYPES}
    approved = [i["affects"] for i in items if i["type"] == "approval"]
    sc = [i for i in items if i["type"] == "scope"]
    vcount = {v: sum(1 for i in sc if i["verdict"] == v) for v in VERDICTS}
    nfacts = len(plan.get("facts", []) or [])
    src_label = f"{scope['source']} ({scope['sow_pages_line']})"
    out = [f"Client: {scope['client']}", f"Date: {plan['date']}", f"From: {plan['from']}",
           f"Scope source: {src_label}", "", f"# {scope['client']}: client feedback, {plan['date']}", "",
           "## Summary", "",
           f"- Items: {len(items)} (" + ", ".join(f"{count[t]} {t}" for t in TYPES) + ")",
           "- Approved: " + ("; ".join(approved) if approved else "nothing yet"),
           "- Scope requests: " + ("none" if not sc else
                                   f"{vcount['outside']} outside scope, {vcount['unclear']} to confirm, "
                                   f"{vcount['within']} within scope"),
           "- Context updates: " + (f"{nfacts} facts in `{updates_name}`; merge them with client-context-update"
                                    if nfacts else "none (the client stated no new facts)")]
    if had_secrets:
        out.append("- Left out: the client's text contains login details; none were copied into these files")
    out += ["", "## Feedback Items", "", TABLE_HEADER, "|---|---|---|---|---|---|---|"]
    for n, i in enumerate(items, 1):
        fb = re.sub(r"\s+", " ", i["feedback"]).strip()
        out.append(f"| {n} | \"{fb}\" | {i['type']} | {i['affects']} | {i['impact']} | {i['action'].strip()} | {i['owner']} |")
    out += ["", "## Scope Check", ""]
    if not sc:
        out.append("- No scope requests.")
    for n, i in enumerate(items, 1):
        if i["type"] != "scope":
            continue
        label, follow = VERDICT_TEXT[i["verdict"]]
        pages = f" Pages requested: {i['pages']}." if i.get("pages") is not None else ""
        out.append(f"- #{n} {label}: {i['basis'].strip()}{pages} Scope source: {src_label}. {follow}")
    am = str(plan.get("am", "")).strip() or AM_PLACEHOLDER
    out += ["", "## Reply Draft", "", f"Subject: {plan['reply']['subject'].strip()}", "",
            plan["reply"]["body"].strip(), "", am, SIGNOFF_TITLE]
    return "\n".join(out) + "\n"


# ---------- check ----------

def parse_table(text: str, header: str) -> list[list[str]] | None:
    lines = text.split("\n")
    try:
        start = lines.index(header)
    except ValueError:
        return None
    rows = []
    for ln in lines[start + 2:]:
        if not ln.startswith("|"):
            break
        rows.append([c.strip() for c in ln.strip().strip("|").split(" | ")])
    return rows


def check(kdir: Path, fb_path: Path, rep_path: Path) -> int:
    scope = scope_info(kdir)
    raw = read(fb_path)
    own = own_text(raw)
    own_n = norm(own)
    secrets = secrets_in(own)
    res: list[tuple[str, bool, str]] = []
    if not rep_path.exists():
        print(f"ERROR: {rep_path} not found")
        return 1
    rep = read(rep_path)
    heads = {k: (re.search(rf"(?m)^{k}:\s*(.+?)\s*$", rep) or [None, ""])[1] for k in ("Client", "Date", "From", "Scope source")}
    res.append(("header lines", all(heads.values()) and heads["Client"] == scope["client"],
                f"Client: {heads['Client'] or '-'}; Date: {heads['Date'] or '-'}"))
    found = re.findall(r"(?m)^## (.+?)\s*$", rep)
    res.append(("sections in order", found == REPORT_SECTIONS, ", ".join(found)))
    rows = parse_table(rep, TABLE_HEADER)
    bad, quotes, types = [], [], []
    if rows is None:
        bad.append("table header missing")
        rows = []
    for k, r in enumerate(rows, 1):
        if len(r) != 7:
            bad.append(f"row {k} has {len(r)} cells")
            continue
        quotes.append(r[1].strip('"'))
        types.append(r[2])
        if r[0] != str(k):
            bad.append(f"row {k} numbered {r[0]}")
        if r[2] not in TYPES or r[3].split(":")[0] not in AFFECTS or r[4] not in IMPACTS or r[6] not in OWNERS:
            bad.append(f"row {k} has a value outside the enums")
    res.append(("feedback table", bool(rows) and not bad, "; ".join(bad[:3]) or f"{len(rows)} rows"))
    nv = [str(k) for k, q in enumerate(quotes, 1) if norm(q) not in own_n]
    res.append(("quotes verbatim", not nv, f"rows {', '.join(nv)} not in the client's text" if nv else "every Feedback cell is the client's words"))
    uncovered = uncovered_questions(own, quotes)
    res.append(("every question has a row", not uncovered, "; ".join(f'"{q[:50]}"' for q in uncovered[:2]) or "all client questions covered"))
    summ = re.search(r"(?m)^- Items: (\d+) \((\d+) content, (\d+) design, (\d+) scope, (\d+) question, (\d+) approval\)", rep)
    want = [len(rows)] + [types.count(t) for t in TYPES]
    res.append(("summary counts", bool(summ) and [int(x) for x in summ.groups()] == want, f"table: {want}"))
    sc_sec = (re.search(r"(?ms)^## Scope Check\s*\n(.*?)(?=^## )", rep) or [None, ""])[1]
    scope_rows = [str(k) for k, t in enumerate(types, 1) if t == "scope"]
    listed = re.findall(r"(?m)^- #(\d+) (outside scope|to confirm|within scope):", sc_sec)
    ok_scope = sorted(n for n, _ in listed) == sorted(scope_rows) and (scope_rows or "- No scope requests." in sc_sec)
    res.append(("scope check", bool(ok_scope), f"{len(listed)} scope line(s) for {len(scope_rows)} scope row(s)"))
    open_scope = sum(1 for _, v in listed if v in ("outside scope", "to confirm"))
    up_path = rep_path.with_name(rep_path.name.replace("-feedback.md", "-feedback-updates.md"))
    summary_names = re.search(r"(?m)^- Context updates: (\d+) facts in `(.+?)`", rep)
    if up_path.exists():
        up = read(up_path)
        uerr = []
        for k in ("Client", "Source", "Date", "From"):
            if not re.search(rf"(?m)^{k}:\s*\S", up):
                uerr.append(f"no {k}: line")
        if not re.search(r"(?m)^Source: client$", up):
            uerr.append("Source is not client")
        urows = parse_table(up, UPDATES_HEADER) or []
        if not urows:
            uerr.append("no update rows")
        conflicts = 0
        for r in urows:
            if len(r) != 4 or r[1] not in UPDATES_SECTIONS:
                uerr.append(f"row {r[:1]} malformed or bad section")
                continue
            if TAG_END_RE.search(r[2]):
                uerr.append(f"row {r[0]} fact carries a tag")
            q = re.search(r'"(.*)"\s*$', r[3])
            if not q or norm(q.group(1)) not in own_n:
                uerr.append(f"row {r[0]} evidence is not the client's words")
            if r[1] == "Scope Summary" and r[2].startswith("CONFLICT:"):
                conflicts += 1
        if conflicts < open_scope:
            uerr.append(f"{open_scope} open scope request(s), {conflicts} CONFLICT row(s)")
        if not summary_names or summary_names.group(2) != up_path.name or int(summary_names.group(1)) != len(urows):
            uerr.append("Summary does not name this updates file with its row count")
        res.append(("updates file", not uerr, "; ".join(uerr[:3]) or f"{len(urows)} rows in client-context-update's format"))
    else:
        res.append(("updates file", open_scope == 0 and "- Context updates: none" in rep,
                    "none written, and none needed" if open_scope == 0 else "open scope requests need a CONFLICT row"))
    blob = rep + (read(up_path) if up_path.exists() else "")
    leaked = [s for s in secrets if s in blob]
    res.append(("no secrets copied", not leaked, "a login or password from the client's text was copied" if leaked else
                (f"{len(secrets)} left out" if secrets else "none in the client's text")))
    reply = (re.search(r"(?ms)^## Reply Draft\s*\n(.*)\Z", rep) or [None, ""])[1].strip()
    rl = reply.split("\n")
    subj_ok = bool(rl) and rl[0].startswith("Subject: ") and len(rl[0]) <= 99
    sign_ok = len(rl) >= 2 and rl[-1] == SIGNOFF_TITLE and rl[-2].strip() != ""
    body = "\n".join(rl[2:-2]).strip() if len(rl) > 4 else ""
    probs = reply_problems(body, own, scope["context_text"], open_scope > 0)
    if not subj_ok:
        probs.insert(0, "no Subject: line")
    if not sign_ok:
        probs.insert(0, "sign-off must be the AM's name then the title")
    res.append(("reply draft", not probs, "; ".join(probs[:3]) or "greeting, voice, numbers and sign-off fine"))
    if rl and len(rl) >= 2 and rl[-2].strip() == AM_PLACEHOLDER:
        res.append(("AM name", True, "placeholder: fill in the AM's name before sending"))
    print("| Check | Result | Detail |")
    print("|---|---|---|")
    for name, ok, detail in res:
        print(f"| {name} | {'PASS' if ok else 'FAIL'} | {detail} |")
    passed = all(ok for _, ok, _ in res)
    print(f"RESULT: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


# ---------- main ----------

def load_plan(p: Path) -> dict:
    try:
        return json.loads(read(p))
    except json.JSONDecodeError as e:
        raise SystemExit(f"PLAN REJECTED\n- {p} is not valid JSON: {e}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scope")
    s.add_argument("kickoff")
    for name in ("render", "updates-json"):
        r = sub.add_parser(name)
        r.add_argument("kickoff")
        r.add_argument("--feedback", required=True)
        r.add_argument("--plan", required=True)
        if name == "render":
            r.add_argument("--dry-run", action="store_true")
    c = sub.add_parser("check")
    c.add_argument("kickoff")
    c.add_argument("--feedback", required=True)
    c.add_argument("--report", required=True)
    a = ap.parse_args()
    kdir = Path(a.kickoff.rstrip("/"))
    if a.cmd == "scope":
        info = scope_info(kdir)
        info.pop("context_text")
        print(json.dumps(info, indent=2, ensure_ascii=False))
        return 0
    if a.cmd == "check":
        return check(kdir, Path(a.feedback), Path(a.report))
    scope = scope_info(kdir)
    raw = read(Path(a.feedback))
    plan = load_plan(Path(a.plan))
    errs = validate_plan(plan, scope, raw)
    if errs:
        print("PLAN REJECTED")
        for e in errs:
            print(f"- {e}")
        return 1
    up = build_updates(plan, scope)
    if a.cmd == "updates-json":
        print(json.dumps(up, indent=2, ensure_ascii=False))
        return 0
    if a.dry_run:
        print("PLAN OK")
        return 0
    rep_path, up_path = out_paths(kdir, plan["date"], plan["from"])
    rep_path.parent.mkdir(parents=True, exist_ok=True)
    has_facts = bool(up["rows"])
    rep_path.write_text(render_report(plan, scope, up_path.name if has_facts else None,
                                      bool(secrets_in(own_text(raw)))), encoding="utf-8")
    if has_facts:
        up_path.write_text(render_updates(up), encoding="utf-8")
    elif up_path.exists():
        up_path.unlink()
    print(f"WROTE {rep_path}")
    if has_facts:
        print(f"WROTE {up_path}")
    return check(kdir, Path(a.feedback), rep_path)


if __name__ == "__main__":
    sys.exit(main())
