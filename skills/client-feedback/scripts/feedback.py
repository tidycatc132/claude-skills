#!/usr/bin/env python3
"""Sort client feedback on the Week 1 or Week 2 deliverables into a feedback file, an updates file and a reply draft.

Usage:
  python3 feedback.py scope kickoff/<slug> [--week 2]
  python3 feedback.py render kickoff/<slug> --feedback <client text file> --plan feedback-plan.json [--dry-run]
  python3 feedback.py check kickoff/<slug> --feedback <client text file> --report feedback/<slug>/<file>-feedback.md
  python3 feedback.py updates-json kickoff/<slug> --feedback <client text file> --plan feedback-plan.json
  python3 feedback.py nudge kickoff/<slug> --plan nudge-plan.json --today YYYY-MM-DD [--email <week-2 email>] [--dry-run]
  python3 feedback.py contract week-2-email <email.md> | contract blueprint <blueprint.md> | contract --validate <file.json>

scope         prints the scope source from <slug>-context.md as JSON (source, SOW pages, services, quote lines).
render        validates the plan against the client's text and the scope source, writes
              feedback/<slug>/<date>-feedback.md and, when the plan has facts,
              feedback/<slug>/<date>-feedback-updates.md, then runs check. --dry-run writes nothing.
check         re-reads the written files and prints a `| Check | Result | Detail |` table and
              `RESULT: PASS` or `RESULT: FAIL` (exit 0 or 1).
updates-json  prints the updates the plan would write as JSON (keys Client, Source, Date, From, rows).
nudge         when the Week 2 email's `Reply by:` date has passed with no Week 2 feedback logged, checks the
              nudge plan and writes feedback/<slug>/<today>-week-2-nudge.md, then checks it.
contract      prints, as JSON, what this skill reads from a Week 2 email's header (`Client:`, `Send date:`,
              `Reply by:`) or a Growth Blueprint (its `##` sections); --validate checks such a JSON file.

A plan with "week": 2 is a reply to the Week 2 email (Growth Blueprint, deck and page content): it reads
blueprint/<slug>/<slug>-growth-blueprint.md, content/<url-slug>/article.md and, when present,
emails/<slug>/<slug>-week-2-email.md from the working folder (the parent of kickoff/).

Standard library only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

TYPES = ["content", "design", "scope", "question", "approval"]
TYPES_W2 = ["content", "design", "strategy", "scope", "question", "approval"]
AFFECTS = ["homepage copy", "homepage design", "site scope", "client context", "timeline",
           "platform access", "intake items", "other"]
AFFECTS_W2 = AFFECTS + ["blueprint", "page"]
# The Growth Blueprint's sections (growth-blueprint) and the deck slides built from each (blueprint-deck).
BLUEPRINT_SECTIONS = ["Executive Summary", "Business and Market Overview", "Competitive Analysis",
                      "Strategic Positioning", "Keyword Opportunity", "Site Architecture and Content Plan",
                      "Growth Strategy", "Measurement and Next Steps"]
DECK_SLIDES = {2: "The Diagnosis", 3: "What This Costs You", 6: "Where You Stand Today",
               7: "Who You're Up Against", 8: "Which Competitors Actually Matter", 9: "What You'll Rank For",
               10: "Why Your Top Keyword Isn't Month One", 12: "How You'll Be Positioned",
               13: "The Site We're Building", 14: "What We're Not Doing", 16: "What Has To Be True",
               17: "How We'll Measure This", 19: "What Happens Next"}
SECTION_SLIDES = {"Executive Summary": [2], "Business and Market Overview": [3, 6],
                  "Competitive Analysis": [3, 7, 8], "Strategic Positioning": [12],
                  "Keyword Opportunity": [9, 10], "Site Architecture and Content Plan": [13],
                  "Growth Strategy": [10, 14], "Measurement and Next Steps": [16, 17, 19]}
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
REPORT_SECTIONS_W2 = ["Summary", "Feedback Items", "Scope Check", "SEO Review", "Reply Draft"]
SEO_HOLD = "Status: hold the reply until SEO signs off the items below"
SEO_CLEAR = "- No strategy items; the reply can go once the AM has read it."

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
MAX_NUDGE_WORDS = 150
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
W2_NAMES_RE = re.compile(r"(?i)\b(blueprint|deck)\b")
STRATEGY_WORDS = re.compile(r"(?i)\b(blueprint|deck|priorit\w*|keywords?|positioning|sitemap|strategy|direction)\b")
DONE_RE = re.compile(r"(?i)\b(we've|we have|i've|i have)\s+(already\s+)?(updated|changed|reworked|switched|moved|swapped|reordered|rewritten|dropped|removed)\b")
COMMIT_RE = re.compile(r"(?i)\b(we'll|we will|i'll|i will)\s+(update|change|rework|switch|move|swap|reorder|rewrite|lead with|make)\b")
HOLD_W2_RE = re.compile(r"(?i)\b(review|reviewed|reviewing|look at|looking at|consider|considering|whether|SEO|come back|get back)\b")
PROCEED_RE = re.compile(r"(?i)\b(go ahead|going ahead|move ahead|moving ahead|proceed|proceeding|carry on|carrying on|keep going|start on|starting on|begin|move forward|moving forward)\b")


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
    return {"client": client, "slug": slug, "kdir": str(kdir), "source": source, "sow_pages": pages,
            "sow_pages_line": f"SOW pages: {pages}",
            "included_services": TAG_END_RE.sub("", svc.group(1)).strip() if svc else "",
            "scope_quotes": [TAG_END_RE.sub("", q).strip() for q in quotes],
            "scope_bullets": bullets, "context_text": text}


def scope_dir(scope: dict) -> Path:
    return Path(scope["kdir"])


EMAIL_KEYS = ["Client:", "Send date:", "Reply by:"]


def email_header(text: str) -> dict:
    """The Week 2 email's header lines this skill reads (week-2-client-email writes them)."""
    out = {}
    for k in EMAIL_KEYS:
        m = re.search(rf"(?m)^{re.escape(k)}[ \t]*(.*?)\s*$", text)
        out[k] = m.group(1) if m else ""
    return out


def blueprint_sections(text: str) -> dict:
    """The Blueprint's `##` sections this skill names, keyed by heading."""
    found = {}
    for m in re.finditer(r"(?ms)^## (.+?)\s*\n(.*?)(?=^## |\Z)", text):
        if m.group(1) in BLUEPRINT_SECTIONS:
            found[m.group(1)] = m.group(2).strip()
    return found


def week2_info(kdir: Path) -> dict:
    """The Week 2 files in the working folder: the Blueprint, the page folders and the Week 2 email."""
    slug, root = kdir.name, kdir.parent.parent
    bp = root / "blueprint" / slug / f"{slug}-growth-blueprint.md"
    email = root / "emails" / slug / f"{slug}-week-2-email.md"
    pages = sorted(d.name for d in (root / "content").glob("*") if (d / "article.md").exists())
    bp_text = read(bp) if bp.exists() else ""
    em_text = read(email) if email.exists() else ""
    reply_by = email_header(em_text)["Reply by:"]
    reply_by = reply_by if DATE_RE.match(reply_by) else ""
    return {"blueprint": f"blueprint/{slug}/{bp.name}" if bp.exists() else "",
            "sections": list(blueprint_sections(bp_text)),
            "pages": pages, "email": f"emails/{slug}/{email.name}" if email.exists() else "",
            "reply_by": reply_by, "text": bp_text + "\n" + em_text}


def plan_week(plan: dict) -> int:
    return 2 if str(plan.get("week", 1)) == "2" else 1


def changes_of(it: dict) -> tuple[list[str], list[int], list[str]]:
    """Blueprint sections, deck slides (derived from the sections) and page slugs an item changes."""
    ch = it.get("changes") or {}
    secs = [x for x in BLUEPRINT_SECTIONS if x in (ch.get("blueprint") or [])]
    slides = sorted({n for x in secs for n in SECTION_SLIDES[x]})
    return secs, slides, list(ch.get("pages") or [])


def impact_cell(it: dict, week: int) -> str:
    if week != 2:
        return it["impact"]
    secs, slides, pages = changes_of(it)
    parts = []
    if secs:
        parts.append("Blueprint " + ", ".join(secs))
    if slides:
        parts.append("deck slides " + ", ".join(map(str, slides)))
    if pages:
        parts.append("pages " + ", ".join(pages))
    return it["impact"] + (": " + "; ".join(parts) if parts else "")


def validate_week2_item(p: str, it: dict, w2: dict) -> list[str]:
    errs = []
    t, a, imp = it.get("type"), str(it.get("affects", "")), it.get("impact")
    head, _, detail = a.partition(":")
    head, detail = head.strip(), detail.strip()
    ch = it.get("changes") or {}
    if not isinstance(ch, dict) or set(ch) - {"blueprint", "pages"}:
        return [f"{p}: changes is an object with the lists 'blueprint' and 'pages' only"]
    for sec in ch.get("blueprint") or []:
        if sec not in BLUEPRINT_SECTIONS:
            errs.append(f"{p}: changes.blueprint '{sec}' is not a Blueprint section ({BLUEPRINT_SECTIONS})")
        elif w2["sections"] and sec not in w2["sections"]:
            errs.append(f"{p}: the Blueprint has no '## {sec}' section")
    for pg in ch.get("pages") or []:
        if pg not in w2["pages"]:
            errs.append(f"{p}: page '{pg}' has no content/{pg}/article.md (pages: {', '.join(w2['pages']) or 'none'})")
    secs, _, pages = changes_of(it)
    changing = imp != "none" and t not in ("question", "approval")
    if head == "blueprint":
        if detail not in BLUEPRINT_SECTIONS:
            errs.append(f"{p}: affects 'blueprint: <section>' names one of {BLUEPRINT_SECTIONS}")
        elif changing and detail not in secs:
            errs.append(f"{p}: affects names Blueprint '{detail}', so changes.blueprint lists it")
    if head == "page":
        if detail not in w2["pages"]:
            errs.append(f"{p}: affects 'page: <url-slug>' names a folder in content/ ({', '.join(w2['pages']) or 'none'})")
        elif changing and detail not in pages:
            errs.append(f"{p}: affects names page '{detail}', so changes.pages lists it")
    if t == "strategy":
        if head != "blueprint":
            errs.append(f"{p}: a strategy item affects 'blueprint: <section>'")
        if imp not in ("medium", "high"):
            errs.append(f"{p}: a strategy item has impact medium or high")
        if it.get("owner") != "SEO":
            errs.append(f"{p}: a strategy item is owned by SEO, who signs it off before the reply goes")
    if t == "content" and imp != "none" and not (secs or pages):
        errs.append(f"{p}: a content change names the page(s) or Blueprint section(s) it changes in changes")
    if t in ("question", "approval") and (secs or pages):
        errs.append(f"{p}: a {t} changes nothing; leave changes empty")
    if t == "scope":
        if it.get("verdict") in ("outside", "unclear") and (secs or pages):
            errs.append(f"{p}: a scope request outside or unclear changes nothing until a signed change; leave changes empty")
        if it.get("verdict") == "within" and "Site Architecture and Content Plan" not in secs:
            errs.append(f"{p}: a scope request within scope changes the Blueprint's Site Architecture and Content Plan")
    return errs


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
    if str(plan.get("week", 1)) not in ("1", "2"):
        errs.append("week is 1 (the reply to the Week 1 email) or 2 (the reply to the Week 2 email)")
    week = plan_week(plan)
    types, affects = (TYPES_W2, AFFECTS_W2) if week == 2 else (TYPES, AFFECTS)
    w2 = week2_info(scope_dir(scope)) if week == 2 else None
    if week == 1 and week2_info(scope_dir(scope))["email"] and re.search(r"(?i)\b(blueprint|deck)\b", raw):
        errs.append("the Week 2 email has gone out and this reply talks about the Blueprint or the deck: "
                    "it is the Week 2 reply, so set \"week\": 2 (references/week-2.md)")
    if w2 is not None and not w2["blueprint"]:
        errs.append(f"a Week 2 reply needs blueprint/{scope['slug']}/{scope['slug']}-growth-blueprint.md "
                    "(growth-blueprint writes it)")
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
        if t not in types:
            hint = " (strategy is for a Week 2 reply: set \"week\": 2)" if t == "strategy" else ""
            errs.append(f"{p}: type '{t}' is not one of {types}{hint}")
        if a.split(":")[0].strip() not in affects:
            errs.append(f"{p}: affects '{a}' must start with one of {affects}")
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
        if w2 is not None:
            errs += validate_week2_item(p, it, w2)
        elif "changes" in it:
            errs.append(f"{p}: changes belong to a Week 2 reply only")
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
    n_strategy = sum(1 for it in items if it.get("type") == "strategy")
    extra_text = w2["text"] if w2 else ""
    errs += [f"reply: {e}" for e in reply_problems(body, own, scope["context_text"] + "\n" + extra_text,
                                                   open_scope > 0, week, n_strategy)]
    blob = json.dumps(plan, ensure_ascii=False)
    for s in secrets:
        if s in blob:
            errs.append("the plan copies a login or password from the client's text; leave it out everywhere")
            break
    return errs


def reply_problems(body: str, own: str, context: str, has_open_scope: bool, week: int = 1,
                   n_strategy: int = 0) -> list[str]:
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
    if week == 2:
        if not W2_NAMES_RE.search(body):
            probs.append("a Week 2 reply names the Blueprint or the deck it answers")
        for sent in re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", body)):
            if STRATEGY_WORDS.search(sent) and DONE_RE.search(sent):
                probs.append(f"says the strategy has already changed: \"{sent[:80]}\"")
            elif n_strategy and STRATEGY_WORDS.search(sent) and COMMIT_RE.search(sent) and not HOLD_W2_RE.search(sent):
                probs.append(f"commits to a strategy change before SEO has reviewed it: \"{sent[:80]}\"")
        if n_strategy and not re.search(r"(?i)\breview", body):
            probs.append("a point changes the Blueprint's direction, so the reply says we will review it before "
                         "changing the plan")
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
    week = plan_week(plan)
    types = TYPES_W2 if week == 2 else TYPES
    count = {t: sum(1 for i in items if i["type"] == t) for t in types}
    approved = [i["affects"] for i in items if i["type"] == "approval"]
    sc = [i for i in items if i["type"] == "scope"]
    vcount = {v: sum(1 for i in sc if i["verdict"] == v) for v in VERDICTS}
    nfacts = len(plan.get("facts", []) or [])
    src_label = f"{scope['source']} ({scope['sow_pages_line']})"
    head = [f"Client: {scope['client']}", f"Date: {plan['date']}", f"From: {plan['from']}",
            f"Scope source: {src_label}"]
    w2 = week2_info(scope_dir(scope)) if week == 2 else None
    if w2:
        head += ["Week: 2", f"Blueprint: {w2['blueprint']}",
                 f"Week 2 email: {w2['email'] or 'not found'}" + (f" (reply by {w2['reply_by']})" if w2["reply_by"] else "")]
    title = "client feedback on the Week 2 Blueprint and pages" if w2 else "client feedback"
    out = head + ["", f"# {scope['client']}: {title}, {plan['date']}", "",
           "## Summary", "",
           f"- Items: {len(items)} (" + ", ".join(f"{count[t]} {t}" for t in types) + ")",
           "- Approved: " + ("; ".join(approved) if approved else "nothing yet"),
           "- Scope requests: " + ("none" if not sc else
                                   f"{vcount['outside']} outside scope, {vcount['unclear']} to confirm, "
                                   f"{vcount['within']} within scope"),
           "- Context updates: " + (f"{nfacts} facts in `{updates_name}`; merge them with client-context-update"
                                    if nfacts else "none (the client stated no new facts)")]
    strat = [n for n, i in enumerate(items, 1) if i["type"] == "strategy"]
    if w2:
        secs = [x for x in BLUEPRINT_SECTIONS if any(x in changes_of(i)[0] for i in items)]
        slides = sorted({n for i in items for n in changes_of(i)[1]})
        pages = sorted({pg for i in items for pg in changes_of(i)[2]})
        out += ["- Blueprint sections changing: " + (", ".join(secs) if secs else "none"),
                "- Deck: " + ("rebuild with blueprint-deck after the Blueprint changes; slides "
                              + ", ".join(f"{n} {DECK_SLIDES[n]}" for n in slides) if slides else "no change"),
                "- Page files changing: " + (", ".join(f"content/{pg}/article.md" for pg in pages) if pages else "none"),
                "- SEO review: " + (f"items {', '.join('#' + str(n) for n in strat)} change the Blueprint's direction; "
                                    "hold the reply until SEO signs them off" if strat else "none needed")]
    if had_secrets:
        out.append("- Left out: the client's text contains login details; none were copied into these files")
    out += ["", "## Feedback Items", "", TABLE_HEADER, "|---|---|---|---|---|---|---|"]
    for n, i in enumerate(items, 1):
        fb = re.sub(r"\s+", " ", i["feedback"]).strip()
        out.append(f"| {n} | \"{fb}\" | {i['type']} | {i['affects']} | {impact_cell(i, week)} | {i['action'].strip()} | {i['owner']} |")
    out += ["", "## Scope Check", ""]
    if not sc:
        out.append("- No scope requests.")
    for n, i in enumerate(items, 1):
        if i["type"] != "scope":
            continue
        label, follow = VERDICT_TEXT[i["verdict"]]
        pages = f" Pages requested: {i['pages']}." if i.get("pages") is not None else ""
        out.append(f"- #{n} {label}: {i['basis'].strip()}{pages} Scope source: {src_label}. {follow}")
    if w2:
        out += ["", "## SEO Review", ""]
        if strat:
            out.append(SEO_HOLD)
            out.append("")
            for n in strat:
                i = items[n - 1]
                out.append(f"- #{n} {i['affects'].partition(':')[2].strip()}: {i['action'].strip()}")
        else:
            out.append(SEO_CLEAR)
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
    week = 2 if re.search(r"(?m)^Week: 2\s*$", rep) else 1
    types, affects = (TYPES_W2, AFFECTS_W2) if week == 2 else (TYPES, AFFECTS)
    w2 = week2_info(kdir) if week == 2 else None
    heads = {k: (re.search(rf"(?m)^{k}:\s*(.+?)\s*$", rep) or [None, ""])[1] for k in ("Client", "Date", "From", "Scope source")}
    res.append(("header lines", all(heads.values()) and heads["Client"] == scope["client"],
                f"Client: {heads['Client'] or '-'}; Date: {heads['Date'] or '-'}"))
    found = re.findall(r"(?m)^## (.+?)\s*$", rep)
    res.append(("sections in order", found == (REPORT_SECTIONS_W2 if w2 else REPORT_SECTIONS), ", ".join(found)))
    rows = parse_table(rep, TABLE_HEADER)
    bad, quotes, rtypes = [], [], []
    if rows is None:
        bad.append("table header missing")
        rows = []
    for k, r in enumerate(rows, 1):
        if len(r) != 7:
            bad.append(f"row {k} has {len(r)} cells")
            continue
        quotes.append(r[1].strip('"'))
        rtypes.append(r[2])
        if r[0] != str(k):
            bad.append(f"row {k} numbered {r[0]}")
        level = r[4].split(":")[0] if w2 else r[4]
        if r[2] not in types or r[3].split(":")[0] not in affects or level not in IMPACTS or r[6] not in OWNERS:
            bad.append(f"row {k} has a value outside the enums")
        if w2:
            for pg in re.findall(r"pages ([^;]+)", r[4]):
                miss = [x.strip() for x in pg.split(",") if x.strip() not in w2["pages"]]
                if miss:
                    bad.append(f"row {k} names page(s) with no content/<url-slug>/article.md: {', '.join(miss)}")
            if r[2] == "strategy" and ("Blueprint " not in r[4] or r[6] != "SEO"):
                bad.append(f"row {k} is strategy but names no Blueprint section or is not owned by SEO")
    res.append(("feedback table", bool(rows) and not bad, "; ".join(bad[:3]) or f"{len(rows)} rows"))
    nv = [str(k) for k, q in enumerate(quotes, 1) if norm(q) not in own_n]
    res.append(("quotes verbatim", not nv, f"rows {', '.join(nv)} not in the client's text" if nv else "every Feedback cell is the client's words"))
    uncovered = uncovered_questions(own, quotes)
    res.append(("every question has a row", not uncovered, "; ".join(f'"{q[:50]}"' for q in uncovered[:2]) or "all client questions covered"))
    summ = re.search(r"(?m)^- Items: (\d+) \(" + ", ".join(rf"(\d+) {t}" for t in types) + r"\)", rep)
    want = [len(rows)] + [rtypes.count(t) for t in types]
    res.append(("summary counts", bool(summ) and [int(x) for x in summ.groups()] == want, f"table: {want}"))
    sc_sec = (re.search(r"(?ms)^## Scope Check\s*\n(.*?)(?=^## )", rep) or [None, ""])[1]
    scope_rows = [str(k) for k, t in enumerate(rtypes, 1) if t == "scope"]
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
    n_strategy = rtypes.count("strategy")
    if w2:
        seo = (re.search(r"(?ms)^## SEO Review\s*\n(.*?)(?=^## )", rep) or [None, ""])[1]
        listed_s = re.findall(r"(?m)^- #(\d+) ", seo)
        want_s = [str(k) for k, t in enumerate(rtypes, 1) if t == "strategy"]
        ok_seo = (listed_s == want_s and SEO_HOLD in seo) if want_s else SEO_CLEAR in seo
        res.append(("SEO review", ok_seo, f"{len(want_s)} strategy row(s) held for SEO" if want_s
                    else "no strategy rows; nothing held"))
        res.append(("Week 2 inputs", bool(w2["blueprint"]), f"{w2['blueprint'] or 'no Blueprint found'}; "
                    f"{len(w2['pages'])} page folder(s); Week 2 email {'found' if w2['email'] else 'not found'}"))
    reply = (re.search(r"(?ms)^## Reply Draft\s*\n(.*)\Z", rep) or [None, ""])[1].strip()
    rl = reply.split("\n")
    subj_ok = bool(rl) and rl[0].startswith("Subject: ") and len(rl[0]) <= 99
    sign_ok = len(rl) >= 2 and rl[-1] == SIGNOFF_TITLE and rl[-2].strip() != ""
    body = "\n".join(rl[2:-2]).strip() if len(rl) > 4 else ""
    probs = reply_problems(body, own, scope["context_text"] + "\n" + (w2["text"] if w2 else ""), open_scope > 0,
                           week, n_strategy)
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


# ---------- nudge ----------

def nudge(kdir: Path, plan_path: Path, today: str, email_arg: str | None, dry_run: bool) -> int:
    scope = scope_info(kdir)
    slug, root = kdir.name, kdir.parent.parent
    email = Path(email_arg) if email_arg else root / "emails" / slug / f"{slug}-week-2-email.md"
    if not DATE_RE.match(today):
        raise SystemExit(f"ERROR: --today '{today}' must be YYYY-MM-DD")
    if not email.exists():
        raise SystemExit(f"ERROR: {email} not found; the nudge follows the Week 2 email (week-2-client-email).")
    em = read(email)
    head = email_header(em)
    reply_by = head["Reply by:"] if DATE_RE.match(head["Reply by:"]) else ""
    send_date = head["Send date:"] if DATE_RE.match(head["Send date:"]) else ""
    if not reply_by:
        raise SystemExit(f"ERROR: {email} has no 'Reply by: YYYY-MM-DD' line.")
    if today <= reply_by:
        print(f"NOT DUE: the client has until {reply_by} to reply; no nudge before that date.")
        return 1
    fdir = root / "feedback" / slug
    logged = [f for f in sorted(fdir.glob("*-feedback.md"))
              if re.search(r"(?m)^Week: 2\s*$", read(f)) and f.name[:10] >= (send_date or "")]
    if logged:
        print(f"REPLY LOGGED: {logged[-1]} already records the client's Week 2 reply; no nudge needed.")
        return 1
    plan = load_plan(plan_path)
    reply = plan.get("reply") or {}
    subj, body = str(reply.get("subject", "")).strip(), str(reply.get("body", "")).strip()
    errs = []
    if not str(plan.get("contact", "")).strip():
        errs.append("contact must name the client the Week 2 email went to")
    if not subj or len(subj) > 90 or "\n" in subj:
        errs.append("subject must be one line of at most 90 characters")
    if SIGNOFF_TITLE.lower() in body.lower():
        errs.append("leave the sign-off out of the body; the script adds the AM's name and title")
    errs += nudge_problems(body, scope["context_text"] + "\n" + em, reply_by)
    if errs:
        print("PLAN REJECTED")
        for e in errs:
            print(f"- {e}")
        return 1
    if dry_run:
        print("PLAN OK")
        return 0
    out = fdir / f"{today}-week-2-nudge.md"
    am = str(plan.get("am", "")).strip() or AM_PLACEHOLDER
    rel_email = f"emails/{slug}/{email.name}" if not email_arg else email_arg
    lines = [f"Client: {scope['client']}", f"Date: {today}", "Week: 2", f"Week 2 email: {rel_email}",
             f"Reply by: {reply_by}", "", f"# {scope['client']}: Week 2 nudge, {today}", "", "## Notes", "",
             f"- No reply to the Week 2 email by {reply_by} (today is {today}).",
             "- Week 3 proceeds with the Blueprint as is.",
             "- A reply that arrives later is sorted with client-feedback; anything that changes the Blueprint's "
             "direction goes to SEO before the reply.", "", "## Nudge Draft", "", f"Subject: {subj}", "", body, "",
             am, SIGNOFF_TITLE]
    fdir.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"WROTE {out}")
    return check_nudge(kdir, out, email, today)


MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october",
          "november", "december"]
MONTH_DAY_RE = re.compile(r"(?i)\b(" + "|".join(m[:3] for m in MONTHS) + r")[a-z]*\.?\s+(\d{1,2})\b")


def nudge_problems(body: str, sources: str, reply_by: str) -> list[str]:
    probs = []
    if reply_by:
        rb = (MONTHS[int(reply_by[5:7]) - 1][:3], int(reply_by[8:10]))
        for m in MONTH_DAY_RE.finditer(body):
            if (m.group(1).lower(), int(m.group(2))) != rb:
                probs.append(f"names the date '{m.group(0)}'; the only date a nudge gives is the missed reply-by date")
        import datetime as _dt
        rb_day = _dt.date.fromisoformat(reply_by).strftime("%A").lower()
        for m in re.finditer(r"(?i)\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", body):
            if m.group(1).lower() != rb_day:
                probs.append(f"names '{m.group(0)}'; the only day a nudge gives is the missed reply-by date")
        for m in re.finditer(r"\b\d{1,2}/\d{1,2}(?:/\d{2,4})?\b|\b\d{4}-\d{2}-\d{2}\b", body):
            if m.group(0) != reply_by:
                probs.append(f"names the date '{m.group(0)}'; the only date a nudge gives is the missed reply-by date")
        if re.search(r"(?i)\b(next week|end of (the )?week|tomorrow|by monday|this week)\b", body):
            probs.append("sets a new deadline; the only date a nudge gives is the missed reply-by date")
    if not re.match(r"^(Hi|Hello|Dear) [^\n]+,\s*$", body.split("\n")[0] if body else ""):
        probs.append("first line must be the greeting, for example 'Hi Maya,'")
    words = len(re.findall(r"\b[\w'-]+\b", body))
    if words > MAX_NUDGE_WORDS:
        probs.append(f"{words} words; keep a nudge to {MAX_NUDGE_WORDS}")
    low = body.lower()
    for b in BANNED_REPLY:
        if re.search(r"(?<![\w-])" + re.escape(b) + r"(?![\w-])", low):
            probs.append(f"uses '{b}'")
    for lab in INTERNAL_LABELS:
        m = re.search(lab, body if lab.startswith(r"\b") and lab[2].isupper() else low)
        if m:
            probs.append(f"internal label '{m.group(0)}' in the client's email")
    if not W2_NAMES_RE.search(body):
        probs.append("names the Blueprint or the deck the client has not answered yet")
    if not PROCEED_RE.search(body):
        probs.append("says the work goes ahead on the Blueprint as it stands (go ahead, move ahead, proceed)")
    if not re.search(r"(?i)\b(thoughts|feedback|questions?|comments?)\b", body):
        probs.append("still welcomes their thoughts or feedback")
    extra = numbers(body) - numbers(sources)
    if extra:
        probs.append(f"number(s) {sorted(extra)} are in neither the Week 2 email nor the context; set no new date")
    return probs


def check_nudge(kdir: Path, path: Path, email: Path, today: str) -> int:
    scope = scope_info(kdir)
    text = read(path)
    res = []
    heads = {k: (re.search(rf"(?m)^{k}:\s*(.+?)\s*$", text) or [None, ""])[1]
             for k in ("Client", "Date", "Week", "Week 2 email", "Reply by")}
    res.append(("header lines", all(heads.values()) and heads["Client"] == scope["client"] and heads["Week"] == "2",
                f"Client: {heads['Client'] or '-'}; Reply by: {heads['Reply by'] or '-'}"))
    found = re.findall(r"(?m)^## (.+?)\s*$", text)
    res.append(("sections in order", found == ["Notes", "Nudge Draft"], ", ".join(found)))
    res.append(("overdue", bool(heads["Reply by"]) and heads["Date"] > heads["Reply by"],
                f"reply by {heads['Reply by'] or '-'}, nudge dated {heads['Date'] or '-'}"))
    res.append(("Week 3 note", "- Week 3 proceeds with the Blueprint as is." in text, "notes say Week 3 goes ahead"))
    draft = (re.search(r"(?ms)^## Nudge Draft\s*\n(.*)\Z", text) or [None, ""])[1].strip().split("\n")
    subj_ok = bool(draft) and draft[0].startswith("Subject: ")
    sign_ok = len(draft) >= 2 and draft[-1] == SIGNOFF_TITLE and draft[-2].strip() != ""
    body = "\n".join(draft[2:-2]).strip() if len(draft) > 4 else ""
    probs = nudge_problems(body, scope["context_text"] + "\n" + (read(email) if email.exists() else ""),
                           heads["Reply by"])
    if not subj_ok:
        probs.insert(0, "no Subject: line")
    if not sign_ok:
        probs.insert(0, "sign-off must be the AM's name then the title")
    res.append(("nudge draft", not probs, "; ".join(probs[:3]) or "greeting, voice, numbers and sign-off fine"))
    if len(draft) >= 2 and draft[-2].strip() == AM_PLACEHOLDER:
        res.append(("AM name", True, "placeholder: fill in the AM's name before sending"))
    print("| Check | Result | Detail |")
    print("|---|---|---|")
    for name, ok, detail in res:
        print(f"| {name} | {'PASS' if ok else 'FAIL'} | {detail} |")
    passed = all(ok for _, ok, _ in res)
    print(f"RESULT: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


# ---------- contract ----------

def contract(kind: str | None, file: str, validate: bool) -> int:
    if validate:
        data = json.loads(read(Path(file)))
        if "Reply by:" in data or "Send date:" in data:
            bad = [k for k in EMAIL_KEYS if k not in data] + \
                  [k for k in ("Send date:", "Reply by:") if k in data and not DATE_RE.match(str(data[k]))]
        else:
            bad = [k for k in BLUEPRINT_SECTIONS if k not in data]
        if bad:
            print("CONTRACT INVALID: missing or not YYYY-MM-DD: " + ", ".join(bad))
            return 1
        print("CONTRACT OK")
        return 0
    text = read(Path(file))
    data = email_header(text) if kind == "week-2-email" else blueprint_sections(text)
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0


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
    s.add_argument("--week", choices=["1", "2"], default="1")
    ct = sub.add_parser("contract")
    ct.add_argument("kind", nargs="?", choices=["week-2-email", "blueprint"])
    ct.add_argument("file")
    ct.add_argument("--validate", action="store_true")
    nd = sub.add_parser("nudge")
    nd.add_argument("kickoff")
    nd.add_argument("--plan", required=True)
    nd.add_argument("--today", required=True)
    nd.add_argument("--email")
    nd.add_argument("--dry-run", action="store_true")
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
    if a.cmd == "contract":
        if not a.validate and not a.kind:
            ap.error("contract needs week-2-email or blueprint, or --validate")
        return contract(a.kind, a.file, a.validate)
    kdir = Path(a.kickoff.rstrip("/"))
    if a.cmd == "scope":
        info = scope_info(kdir)
        info.pop("context_text")
        info.pop("kdir")
        if a.week == "2":
            w2 = week2_info(kdir)
            w2.pop("text")
            w2["deck_slides"] = {sec: [f"{n} {DECK_SLIDES[n]}" for n in SECTION_SLIDES[sec]] for sec in BLUEPRINT_SECTIONS}
            info["week2"] = w2
        print(json.dumps(info, indent=2, ensure_ascii=False))
        return 0
    if a.cmd == "nudge":
        return nudge(kdir, Path(a.plan), a.today, a.email, a.dry_run)
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
