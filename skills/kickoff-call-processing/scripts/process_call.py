#!/usr/bin/env python3
"""Turn a Kickoff Call plan into the three post-call files, and check them.

Subcommands
  transcript <file>                     parse the transcript: date, speakers, page-count mentions
  build <kickoff/slug> --transcript T --plan P [--dry-run]
                                        validate the plan, write <slug>-call-updates.md,
                                        <slug>-blueprint-input-package.md, <slug>-quote-bank.md, then check
  check <kickoff/slug> --transcript T --plan P
                                        re-check the written files (verbatim quotes, timestamps,
                                        sections, tags, conflicts, files match the plan)
  render <kickoff/slug> --transcript T --plan P
                                        print the call-updates file the plan would produce, as JSON
                                        (keys Client, Source, Date, From, rows); writes nothing
  updates <file> [--json]               parse a call-updates file (same keys)

Standard library only. Exit 0 on PASS / OK, 1 otherwise.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

CONTEXT_HEADINGS = ["Snapshot", "Business Overview", "Services", "Customers and Service Area",
                    "Goals and Conversion", "Differentiators and Proof", "Competitors", "Website Today",
                    "Scope Summary", "Open Items", "Sources"]
UPDATES_SECTIONS = CONTEXT_HEADINGS[:9] + ["Platform Access", "Intake Items"]
UPDATES_COLUMNS = ["#", "Section", "Fact", "Evidence"]
PLATFORMS = ["Domain", "Hosting", "Website login", "Google Analytics", "Google Search Console",
             "Google Business Profile", "Google Tag Manager", "Google Ads", "Meta ads", "Microsoft Ads",
             "CRM, forms or call tracking"]
ACCESS_STATUSES = ["confirmed", "invite sent", "needs help", "someone else manages it", "not set up",
                   "not sure", "no answer", "n/a"]
INTAKE_ITEMS = ["Primary contact", "Website approver", "Business name, address, phone and hours",
                "Logo files", "Brand guidelines", "Photos", "Testimonials or reviews", "Team members",
                "Certifications, awards and memberships", "Legal or compliance language",
                "Sites they like", "Things to avoid", "Gap question answers"]
INTAKE_STATUSES = ["received", "partial", "missing", "none", "n/a"]
PACKAGE_SECTIONS = ["Services Priority", "Audiences", "Service Area Tiers", "Voice and Design Direction",
                    "Competitors", "Topics to Own", "Goals and Success Measures", "Scope Decisions",
                    "Open Items"]
USE_FOR = ["services", "audience", "service-area", "voice", "design", "competitors", "proof", "topics",
           "goals", "pain-point", "homepage"]
QUOTE_COLUMNS = ["#", "Quote", "Speaker", "Timestamp", "Use for"]
MIN_QUOTES, MAX_QUOTES, MIN_QUOTE_WORDS = 8, 12, 5
NOT_DISCUSSED = "Not discussed on the call."
NO_CONFLICT = "No page count or deliverable on the call differs from the scope source."
SCOPE_SOURCE_NAMES = {"sow": "the SOW", "notes": "the signed deal terms"}

TS = r"\d{1,2}:\d{2}(?::\d{2})?"
TURN_PATTERNS = [
    re.compile(rf"^\[({TS})\]\s*([^:\n\[\]]{{1,60}}?):\s*(.*)$"),            # [00:01:02] Name: text
    re.compile(rf"^\(?({TS})\)?\s+([^:\n\[\]()]{{1,60}}?):\s*(.*)$"),          # 00:01:02 Name: text
]
NAME_FIRST = re.compile(rf"^([^:\n\[\]()]{{1,60}}?)\s*[\[(]({TS})[\])]\s*:?\s*(.*)$")  # Name (00:01:02): text
HEADER_ONLY = re.compile(rf"^([A-Z][^:\n\[\]()]{{0,58}}?)\s+({TS})\s*$")       # Name  00:01:02 (text below)
SUMMARY_START = re.compile(r"(?i)^(---+\s*$|\**\s*(dialpad\s+)?ai\s+summary|\**\s*(call\s+)?summary\s*:)")
NUMWORDS = ("one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|"
            "sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred")
NUM = rf"(?:\d+|(?:{NUMWORDS})(?:[- ](?:{NUMWORDS}))*)"
PAGE_RE = re.compile(rf"(?i)\b{NUM}(?:\s*(?:to|-|or)\s*{NUM})?\s+(?:\w+\s+)?pages?\b")
TS_LIST = re.compile(rf"\(((?:\d{{2}}:\d{{2}}:\d{{2}})(?:,\s*\d{{2}}:\d{{2}}:\d{{2}})*)\)\s*\[call\]\s*$")
TAG_RE = re.compile(r"\s\[([a-z]+(?:,\s*[a-z]+)*)\]\s*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SECRET_RE = re.compile(r"(?i)\b(password|passcode|passwd|pwd|pin|username|user name|login)\b\s*(is|:|=)\s*\S+")
MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august", "september",
          "october", "november", "december"]


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8").replace("\r\n", "\n")


def norm(s: str) -> str:
    s = (s.replace("\u2018", "'").replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')
         .replace("\u2014", "-").replace("\u2013", "-").replace("\u2026", "..."))
    return re.sub(r"\s+", " ", s).strip()


def esc(s: str) -> str:
    return s.replace("|", "\\|").replace("\n", " ")


def norm_ts(ts: str) -> str:
    parts = [int(x) for x in ts.split(":")]
    if len(parts) == 2:
        parts = [0] + parts
    return "%02d:%02d:%02d" % tuple(parts)


# ---------- transcript ----------

def parse_transcript(path: Path) -> dict:
    lines = read(path).split("\n")
    turns: list[dict] = []
    preamble: list[str] = []
    cur = None
    for ln in lines:
        s = ln.strip()
        if turns and SUMMARY_START.match(s):
            break
        m = None
        for pat in TURN_PATTERNS:
            mm = pat.match(s)
            if mm:
                m = (mm.group(1), mm.group(2), mm.group(3))
                break
        if not m:
            mm = NAME_FIRST.match(s)
            if mm:
                m = (mm.group(2), mm.group(1), mm.group(3))
        if not m:
            mm = HEADER_ONLY.match(s)
            if mm:
                m = (mm.group(2), mm.group(1), "")
        if m:
            cur = {"timestamp": norm_ts(m[0]), "speaker": norm(m[1]), "text": m[2].strip()}
            turns.append(cur)
        elif s and cur is not None:
            cur["text"] = (cur["text"] + " " + s).strip()
        elif s and not turns:
            preamble.append(s)
    for t in turns:
        t["norm"] = norm(t["text"])
    return {"turns": turns, "preamble": preamble, "name": path.name}


def guess_date(tr: dict) -> str:
    for s in tr["preamble"] + [tr["name"]]:
        m = re.search(r"(\d{4})-(\d{2})-(\d{2})", s)
        if m:
            return m.group(0)
        m = re.search(r"(?i)\b(" + "|".join(MONTHS) + r")\s+(\d{1,2}),?\s+(\d{4})", s)
        if m:
            return "%s-%02d-%02d" % (m.group(3), MONTHS.index(m.group(1).lower()) + 1, int(m.group(2)))
    return ""


def page_mentions(tr: dict) -> list[dict]:
    out = []
    for t in tr["turns"]:
        hits = [m.group(0) for m in PAGE_RE.finditer(t["norm"])]
        if hits:
            out.append({"timestamp": t["timestamp"], "speaker": t["speaker"], "text": "; ".join(hits)})
    return out


def cmd_transcript(args) -> int:
    tr = parse_transcript(Path(args.file))
    if len(tr["turns"]) < 2:
        print("TRANSCRIPT UNREADABLE: no timestamped speaker turns found. Accepted line formats: "
              "'[00:01:02] Name: text', '00:01:02 Name: text', 'Name (00:01:02): text', "
              "or a 'Name  00:01:02' line with the text below it.")
        return 1
    speakers: dict[str, int] = {}
    for t in tr["turns"]:
        speakers[t["speaker"]] = speakers.get(t["speaker"], 0) + 1
    d = guess_date(tr)
    print(f"TRANSCRIPT OK: {len(tr['turns'])} turns, {tr['turns'][0]['timestamp']} to {tr['turns'][-1]['timestamp']}")
    print(f"Call date found: {d}" if d else "Call date found: none (use the date the user gave, else today's date, and say which)")
    print("Speakers: " + ", ".join(f"{k} ({v} turns)" for k, v in speakers.items()))
    pm = page_mentions(tr)
    print("Page-count mentions (classify every one in the plan's page_mentions):")
    for m in pm:
        print(f"- {m['timestamp']} {m['speaker']}: {m['text']}")
    if not pm:
        print("- none")
    if args.turns:
        for t in tr["turns"]:
            print(f"[{t['timestamp']}] {t['speaker']}: {t['text']}")
    return 0


# ---------- context ----------

def parse_context(path: Path) -> dict:
    text = read(path)
    m = re.search(r"(?m)^Client:\s*(.+?)\s*$", text)
    sp = re.search(r"(?m)^SOW pages:\s*(\S+)(.*)$", text)
    inc = re.search(r"(?m)^Included services:.*$", text)
    pages = None
    tag = ""
    if sp:
        pages = int(sp.group(1)) if sp.group(1).isdigit() else None
        tm = TAG_RE.search(sp.group(0))
        tag = tm.group(1).split(",")[0].strip() if tm else ""
    return {"client": m.group(1) if m else "", "sow_line": sp.group(0).strip() if sp else "",
            "pages": pages, "scope_tag": tag, "included_line": inc.group(0).strip() if inc else ""}


# ---------- plan ----------

def find_turn(tr: dict, ts: str, speaker: str | None = None) -> dict | None:
    for t in tr["turns"]:
        if t["timestamp"] == ts and (speaker is None or t["speaker"] == speaker):
            return t
    return None


def check_quote(tr: dict, q: dict, where: str, errors: list[str]) -> None:
    ts, sp, quote = q.get("timestamp", ""), q.get("speaker", ""), q.get("quote", "")
    if not quote:
        errors.append(f"{where}: quote is empty")
        return
    t = find_turn(tr, ts, sp)
    if t is None:
        errors.append(f"{where}: no turn by '{sp}' at {ts} in the transcript")
    elif norm(quote) not in t["norm"]:
        errors.append(f"{where}: quote is not verbatim from {sp} at {ts} (copy it exactly, no edits or merges): \"{quote[:80]}\"")


def item_timestamps(item) -> list[str]:
    ts = item.get("timestamps", item.get("timestamp", []))
    return [ts] if isinstance(ts, str) else list(ts or [])


def validate_plan(plan: dict, tr: dict, ctx: dict) -> list[str]:
    e: list[str] = []
    speakers = {t["speaker"] for t in tr["turns"]}
    if plan.get("client") != ctx["client"]:
        e.append(f"client '{plan.get('client')}' must equal the context's Client: line '{ctx['client']}'")
    if not DATE_RE.match(str(plan.get("call_date", ""))):
        e.append("call_date must be YYYY-MM-DD")
    agency = plan.get("agency_speakers") or []
    if not agency:
        e.append("agency_speakers must list the WISE people on the call")
    for a in agency:
        if a not in speakers:
            e.append(f"agency speaker '{a}' is not a speaker in the transcript ({sorted(speakers)})")
    # updates
    ups = plan.get("updates") or []
    if not ups:
        e.append("updates is empty")
    for i, u in enumerate(ups, 1):
        w = f"updates[{i}]"
        sec, fact = u.get("section", ""), norm(u.get("fact", ""))
        if sec not in UPDATES_SECTIONS:
            e.append(f"{w}: section '{sec}' is not one of {UPDATES_SECTIONS}")
        if not fact:
            e.append(f"{w}: fact is empty")
        if TAG_RE.search(fact):
            e.append(f"{w}: fact must carry no source tag (client-context-update adds it)")
        if fact.startswith(("CONFLICT:", "GAP:")):
            e.append(f"{w}: do not write CONFLICT: or GAP: facts; list promises in page_mentions or deliverables and the script writes the conflict rows")
        if sec == "Platform Access":
            m = re.match(r"^(.+?):\s*(.+)$", fact)
            if not m or m.group(1) not in PLATFORMS or not any(m.group(2).startswith(s) for s in ACCESS_STATUSES):
                e.append(f"{w}: Platform Access fact must start '<platform>: <status>' with a platform from {PLATFORMS} and a status from {ACCESS_STATUSES}")
        if sec == "Intake Items":
            m = re.match(r"^(.+?):\s*(.+)$", fact)
            if not m or m.group(1) not in INTAKE_ITEMS or not any(m.group(2).startswith(s) for s in INTAKE_STATUSES):
                e.append(f"{w}: Intake Items fact must start '<item>: <status>' with an item from {INTAKE_ITEMS} and a status from {INTAKE_STATUSES}")
        check_quote(tr, u, w, e)
    # package
    pkg = plan.get("package") or {}
    for k in pkg:
        if k not in PACKAGE_SECTIONS:
            e.append(f"package section '{k}' is not one of {PACKAGE_SECTIONS}")
    all_ts = {t["timestamp"] for t in tr["turns"]}
    for sec in PACKAGE_SECTIONS:
        for i, it in enumerate(pkg.get(sec) or [], 1):
            w = f"package['{sec}'][{i}]"
            text = norm(it.get("text", "")) if isinstance(it, dict) else ""
            if not text:
                e.append(f"{w}: give an object with 'text' and 'timestamps'")
                continue
            if TAG_RE.search(text) or "CONFLICT:" in text:
                e.append(f"{w}: no tags and no CONFLICT: in text (the script adds [call] and writes scope conflicts)")
            tss = item_timestamps(it)
            if not tss:
                e.append(f"{w}: needs at least one timestamp of the turn(s) it comes from")
            for ts in tss:
                if ts not in all_ts:
                    e.append(f"{w}: timestamp {ts} is not a turn in the transcript")
    # quotes
    qs = plan.get("quotes") or []
    client_turns = [t for t in tr["turns"] if t["speaker"] not in agency]
    need = min(MIN_QUOTES, len(client_turns))
    if not (need <= len(qs) <= MAX_QUOTES):
        e.append(f"quotes: {len(qs)} given; need {need} to {MAX_QUOTES}")
    seen = set()
    for i, q in enumerate(qs, 1):
        w = f"quotes[{i}]"
        if q.get("speaker") in agency:
            e.append(f"{w}: quotes come from the client side, not from {q.get('speaker')}")
        if len(norm(q.get("quote", "")).split()) < MIN_QUOTE_WORDS:
            e.append(f"{w}: quote has fewer than {MIN_QUOTE_WORDS} words")
        key = norm(q.get("quote", ""))
        if key in seen:
            e.append(f"{w}: duplicate quote")
        seen.add(key)
        uf = q.get("use_for") or []
        uf = [uf] if isinstance(uf, str) else uf
        if not uf or any(x not in USE_FOR for x in uf):
            e.append(f"{w}: use_for must be one or more of {USE_FOR}")
        check_quote(tr, q, w, e)
    # page mentions
    found = {m["timestamp"] for m in page_mentions(tr)}
    given = {}
    for i, pm in enumerate(plan.get("page_mentions") or [], 1):
        w = f"page_mentions[{i}]"
        given[pm.get("timestamp")] = pm
        kind = pm.get("kind")
        if kind not in ("promise", "request", "other"):
            e.append(f"{w}: kind must be promise, request or other")
        if kind in ("promise", "request"):
            lo, hi = pm.get("low"), pm.get("high")
            if not isinstance(lo, int) or not isinstance(hi, int) or lo > hi:
                e.append(f"{w}: low and high must be whole numbers with low <= high")
            if not pm.get("said"):
                e.append(f"{w}: 'said' must say in a few words what was promised or asked")
            check_quote(tr, pm, w, e)
        elif not pm.get("note"):
            e.append(f"{w}: an 'other' mention needs a note saying why it is not a promise")
    for ts in sorted(found - set(given)):
        e.append(f"page_mentions: the page-count mention at {ts} is not classified (promise, request or other)")
    for ts in sorted(set(given) - found):
        e.append(f"page_mentions: {ts} has no page-count mention in the transcript")
    for i, d in enumerate(plan.get("deliverables") or [], 1):
        w = f"deliverables[{i}]"
        if not isinstance(d.get("in_scope"), bool):
            e.append(f"{w}: in_scope must be true or false")
        if not d.get("said"):
            e.append(f"{w}: 'said' must name the deliverable")
        check_quote(tr, d, w, e)
    for w, text in secret_texts(plan):
        if SECRET_RE.search(text):
            e.append(f"{w}: looks like a username, password or code; leave it out and name only the platform")
    return e


def secret_texts(plan: dict):
    for key in ("updates", "quotes", "page_mentions", "deliverables"):
        for i, x in enumerate(plan.get(key) or [], 1):
            for f in ("fact", "quote", "said", "note"):
                if isinstance(x, dict) and x.get(f):
                    yield f"{key}[{i}]", str(x[f])
    for sec, items in (plan.get("package") or {}).items():
        for i, it in enumerate(items or [], 1):
            if isinstance(it, dict):
                yield f"package['{sec}'][{i}]", str(it.get("text", ""))


# ---------- render ----------

def scope_name(ctx: dict) -> str:
    name = SCOPE_SOURCE_NAMES.get(ctx["scope_tag"])
    return f"the scope source ({name})" if name else "the scope source"


def conflicts(plan: dict, ctx: dict) -> list[dict]:
    out = []
    for pm in plan.get("page_mentions") or []:
        if pm.get("kind") not in ("promise", "request"):
            continue
        n = ctx["pages"]
        if n is not None and pm["low"] == pm["high"] == n:
            continue
        verb = "said" if pm["kind"] == "promise" else "asked for"
        line = ctx["sow_line"].split(" [")[0] or "no SOW pages line"
        src = (f"{scope_name(ctx)} gives no page count ({line})" if n is None
               else f"{scope_name(ctx)} says {n} pages ({line})")
        out.append({"pm": pm, "fact": f"CONFLICT: on the call {pm['speaker']} {verb} {norm(pm['said'])}; {src}; "
                                      f"the build follows the scope source until a signed change"})
    for d in plan.get("deliverables") or []:
        if d.get("in_scope"):
            continue
        out.append({"pm": d, "fact": f"CONFLICT: on the call {d['speaker']} agreed to {norm(d['said'])}, which "
                                     f"{scope_name(ctx)} does not include; the build follows the scope source "
                                     f"until a signed change"})
    return out


def evidence(q: dict) -> str:
    return f"{q['speaker']} ({q['timestamp']}): \"{norm(q['quote'])}\""


def header(plan: dict, tr: dict, extra: list[str]) -> list[str]:
    return [f"Client: {plan['client']}", f"Call date: {plan['call_date']}", f"From: {tr['name']}"] + extra


def render(plan: dict, tr: dict, ctx: dict) -> dict[str, str]:
    cf = conflicts(plan, ctx)
    # updates
    u = [f"Client: {plan['client']}", "Source: call", f"Date: {plan['call_date']}", f"From: {tr['name']}", "",
         "## Updates", "", "| " + " | ".join(UPDATES_COLUMNS) + " |", "|---|---|---|---|"]
    rows = [(x["section"], norm(x["fact"]), evidence(x)) for x in plan["updates"]]
    rows += [("Scope Summary", c["fact"], evidence(c["pm"])) for c in cf]
    u += [f"| {i} | {s} | {esc(f)} | {esc(ev)} |" for i, (s, f, ev) in enumerate(rows, 1)]
    # package
    p = header(plan, tr, [f"Scope source: {ctx['sow_line']}", "",
                          f"# Blueprint Input Package for {plan['client']}", "",
                          "Everything SEO needs from the Kickoff Call to start the Growth Blueprint. Each bullet "
                          "gives the call timestamp(s) it comes from; scope lines come from the client context."])
    pkg = plan.get("package") or {}
    for sec in PACKAGE_SECTIONS:
        p += ["", f"## {sec}"]
        items = [f"- {norm(it['text'])} ({', '.join(item_timestamps(it))}) [call]" for it in pkg.get(sec) or []]
        if sec == "Scope Decisions":
            scope = [f"- {ctx['sow_line']}"] + ([f"- {ctx['included_line']}"] if ctx["included_line"] else [])
            cl = [f"- {c['fact']} ({c['pm']['timestamp']}) [call]" for c in cf] or [f"- {NO_CONFLICT} [call]"]
            items = scope + cl + items
        p += items or [f"- {NOT_DISCUSSED} [call]"]
    # quotes
    agency = ", ".join(plan["agency_speakers"])
    q = header(plan, tr, [f"Agency speakers: {agency}", "", f"# Quote bank for {plan['client']}", "",
                          "Verbatim client quotes from the Kickoff Call, exactly as spoken.", "",
                          "| " + " | ".join(QUOTE_COLUMNS) + " |", "|---|---|---|---|---|"])
    for i, x in enumerate(plan["quotes"], 1):
        uf = x["use_for"] if isinstance(x["use_for"], list) else [x["use_for"]]
        q.append(f"| {i} | {esc(norm(x['quote']))} | {x['speaker']} | {x['timestamp']} | {', '.join(uf)} |")
    return {"call-updates": "\n".join(u) + "\n", "blueprint-input-package": "\n".join(p) + "\n",
            "quote-bank": "\n".join(q) + "\n"}


# ---------- check ----------

def read_table(text: str, head: str) -> list[list[str]] | None:
    lines = text.split("\n")
    for i, ln in enumerate(lines):
        if ln.strip() == head:
            rows = []
            for r in lines[i + 2:]:
                if not r.startswith("|"):
                    break
                cells = [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", r.strip())[1:-1]]
                rows.append(cells)
            return rows
    return None


def parse_updates(path: Path) -> tuple[dict, list[str]]:
    return parse_updates_text(read(path))


def parse_updates_text(text: str) -> tuple[dict, list[str]]:
    errs, head = [], {}
    for key in ("Client", "Source", "Date", "From"):
        m = re.search(rf"(?m)^{key}:\s*(.+?)\s*$", text)
        head[key] = m.group(1) if m else ""
        if not m:
            errs.append(f"missing '{key}:' line")
    if head["Source"] and head["Source"] != "call":
        errs.append("Source must be 'call'")
    if head["Date"] and not DATE_RE.match(head["Date"]):
        errs.append("Date must be YYYY-MM-DD")
    rows = read_table(text, "| " + " | ".join(UPDATES_COLUMNS) + " |")
    if rows is None:
        errs.append("table header must be | # | Section | Fact | Evidence |")
        rows = []
    out = []
    for r in rows:
        if len(r) != 4:
            errs.append(f"row {r[:1]} has {len(r)} cells")
            continue
        if r[1] not in UPDATES_SECTIONS:
            errs.append(f"row {r[0]}: section '{r[1]}' is not allowed")
        if not r[2] or not r[3]:
            errs.append(f"row {r[0]}: Fact and Evidence must not be empty")
        out.append(dict(zip(UPDATES_COLUMNS, r)))
    if not out:
        errs.append("no update rows")
    return {"Client": head["Client"], "Source": head["Source"], "Date": head["Date"], "From": head["From"],
            "rows": out}, errs


def run_check(folder: Path, tr: dict, plan: dict) -> int:
    slug = folder.name
    ctx = parse_context(folder / f"{slug}-context.md")
    res: list[tuple[str, bool, str]] = []
    perr = validate_plan(plan, tr, ctx)
    res.append(("plan", not perr, "; ".join(perr[:3]) or "valid"))
    want = render(plan, tr, ctx) if not perr else {}
    paths = {k: folder / f"{slug}-{k}.md" for k in ("call-updates", "blueprint-input-package", "quote-bank")}
    for k, p in paths.items():
        if not p.exists():
            res.append((k, False, f"{p.name} missing"))
        elif want and read(p) != want[k]:
            res.append((k, False, f"{p.name} differs from the plan (edited by hand?); rebuild it"))
    if paths["call-updates"].exists():
        data, ue = parse_updates(paths["call-updates"])
        bad = list(ue)
        for r in data["rows"]:
            m = re.match(r'^(.+?) \((\d{2}:\d{2}:\d{2})\): "(.*)"$', r["Evidence"])
            if not m:
                bad.append(f"row {r['#']}: Evidence must be 'Speaker (HH:MM:SS): \"quote\"'")
                continue
            t = find_turn(tr, m.group(2), m.group(1))
            if t is None or norm(m.group(3)) not in t["norm"]:
                bad.append(f"row {r['#']}: evidence not verbatim at {m.group(2)}")
        n_cf = sum(r["Fact"].startswith("CONFLICT:") for r in data["rows"])
        res.append(("call updates", not bad, "; ".join(bad[:3]) or f"{len(data['rows'])} rows, {n_cf} conflict(s)"))
    if paths["blueprint-input-package"].exists():
        text = read(paths["blueprint-input-package"])
        heads = re.findall(r"(?m)^## (.+)$", text)
        bad = [] if heads == PACKAGE_SECTIONS else [f"sections {heads} differ from {PACKAGE_SECTIONS}"]
        all_ts = {t["timestamp"] for t in tr["turns"]}
        n = 0
        for ln in text.split("\n"):
            if not ln.startswith("- "):
                continue
            n += 1
            if ln in (f"- {NOT_DISCUSSED} [call]", f"- {NO_CONFLICT} [call]"):
                continue
            if ln.startswith(("- SOW pages:", "- Included services:")) and TAG_RE.search(ln):
                continue
            m = TS_LIST.search(ln)
            if not m:
                bad.append(f"bullet without '(HH:MM:SS) [call]': {ln[:60]}")
            elif any(x.strip() not in all_ts for x in m.group(1).split(",")):
                bad.append(f"unknown timestamp in: {ln[:60]}")
        res.append(("package", not bad, "; ".join(bad[:3]) or f"{n} bullets in {len(heads)} sections"))
    if paths["quote-bank"].exists():
        text = read(paths["quote-bank"])
        rows = read_table(text, "| " + " | ".join(QUOTE_COLUMNS) + " |")
        am = re.search(r"(?m)^Agency speakers:\s*(.+)$", text)
        agency = {a.strip() for a in am.group(1).split(",")} if am else set()
        bad = [] if rows is not None else ["quote table header missing"]
        for r in rows or []:
            if len(r) != 5:
                bad.append(f"row {r[:1]} has {len(r)} cells")
                continue
            t = find_turn(tr, r[3], r[2])
            if t is None or norm(r[1]) not in t["norm"]:
                bad.append(f"quote {r[0]} not verbatim from {r[2]} at {r[3]}")
            if r[2] in agency:
                bad.append(f"quote {r[0]} is from agency speaker {r[2]}")
        res.append(("quote bank", not bad, "; ".join(bad[:3]) or f"{len(rows or [])} verbatim quotes"))
    if want:
        cf = conflicts(plan, ctx)
        pk = read(paths["blueprint-input-package"]) if paths["blueprint-input-package"].exists() else ""
        up = read(paths["call-updates"]) if paths["call-updates"].exists() else ""
        ok = pk.count("- CONFLICT:") == len(cf) and up.count("| Scope Summary | CONFLICT:") == len(cf)
        res.append(("scope conflicts", ok, f"{len(cf)} flagged against {ctx['sow_line'] or 'no SOW pages line'}"))
    print("| Check | Result | Detail |")
    print("|---|---|---|")
    for name, ok, det in res:
        print(f"| {name} | {'PASS' if ok else 'FAIL'} | {esc(det)} |")
    allok = all(ok for _, ok, _ in res)
    print(f"RESULT: {'PASS' if allok else 'FAIL'}")
    return 0 if allok else 1


# ---------- commands ----------

def load_inputs(args) -> tuple[Path, dict, dict, dict] | None:
    folder = Path(args.folder)
    slug = folder.name
    cpath = folder / f"{slug}-context.md"
    if not cpath.exists():
        print(f"NO CONTEXT: {cpath} does not exist. Run new-build-kickoff for this client first.")
        return None
    tr = parse_transcript(Path(args.transcript))
    if len(tr["turns"]) < 2:
        print("TRANSCRIPT UNREADABLE: run the transcript subcommand for the accepted formats.")
        return None
    try:
        plan = json.loads(read(Path(args.plan)))
    except (OSError, json.JSONDecodeError) as ex:
        print(f"PLAN UNREADABLE: {ex}")
        return None
    return folder, tr, parse_context(cpath), plan


def cmd_build(args) -> int:
    got = load_inputs(args)
    if not got:
        return 1
    folder, tr, ctx, plan = got
    errs = validate_plan(plan, tr, ctx)
    if errs:
        print("PLAN REJECTED, nothing written. Fix the plan and rerun:")
        for x in errs:
            print(f"- {x}")
        return 1
    if args.dry_run:
        cf = conflicts(plan, ctx)
        print(f"PLAN OK: {len(plan['updates'])} update rows, {len(cf)} scope conflict(s), {len(plan['quotes'])} quotes")
        for c in cf:
            print(f"- {c['fact']}")
        return 0
    for k, text in render(plan, tr, ctx).items():
        (folder / f"{folder.name}-{k}.md").write_text(text, encoding="utf-8")
        print(f"wrote {folder / (folder.name + '-' + k + '.md')}")
    return run_check(folder, tr, plan)


def cmd_render(args) -> int:
    got = load_inputs(args)
    if not got:
        return 1
    _folder, tr, ctx, plan = got
    errs = validate_plan(plan, tr, ctx)
    if errs:
        print("PLAN REJECTED: " + "; ".join(errs))
        return 1
    print(json.dumps(updates_data(render(plan, tr, ctx)["call-updates"]), indent=2))
    return 0


def updates_data(text: str) -> dict:
    data, _errs = parse_updates_text(text)
    return data


def cmd_check(args) -> int:
    got = load_inputs(args)
    if not got:
        return 1
    folder, tr, _ctx, plan = got
    return run_check(folder, tr, plan)


def cmd_updates(args) -> int:
    data, errs = parse_updates(Path(args.file))
    if args.json:
        print(json.dumps(data, indent=2))
        return 1 if errs else 0
    if errs:
        print("UPDATES INVALID:")
        for x in errs:
            print(f"- {x}")
        return 1
    print(f"UPDATES OK: {len(data['rows'])} rows")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("transcript")
    t.add_argument("file")
    t.add_argument("--turns", action="store_true", help="also print every parsed turn")
    for name in ("build", "check", "render"):
        b = sub.add_parser(name)
        b.add_argument("folder")
        b.add_argument("--transcript", required=True)
        b.add_argument("--plan", required=True)
        if name == "build":
            b.add_argument("--dry-run", action="store_true")
    u = sub.add_parser("updates")
    u.add_argument("file")
    u.add_argument("--json", action="store_true")
    args = ap.parse_args()
    return {"transcript": cmd_transcript, "build": cmd_build, "check": cmd_check, "render": cmd_render,
            "updates": cmd_updates}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
