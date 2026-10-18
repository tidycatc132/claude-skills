#!/usr/bin/env python3
"""Merge new client information into a kickoff client context, and check the result.

Usage:
  python3 update_context.py apply kickoff/<slug> --plan plan.json [--dry-run]
  python3 update_context.py check kickoff/<slug>
  python3 update_context.py updates <updates file> [--json]
  python3 update_context.py outline <slug>-context.md
  python3 update_context.py outline --validate outline.json

apply   snapshots the context to kickoff/<slug>/history/, applies the plan's changes, fills answered
        gap questions, appends the change log, rewrites the missing items file, then runs check.
        --dry-run validates the plan and writes nothing.
check   verifies headings unchanged, no fact lost, every change logged, tags valid, the missing
        items file complete and its agenda consistent, and no password copied. Prints one
        `| Check | Result | Detail |` table and `RESULT: PASS` or `RESULT: FAIL` (exit 0 or 1).
updates validates an updates file (the input format other skills write for this one).
outline prints a kickoff context as JSON (the contract with new-build-kickoff), or validates one.

Standard library only.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

HEADINGS = ["Snapshot", "Business Overview", "Services", "Customers and Service Area",
            "Goals and Conversion", "Differentiators and Proof", "Competitors", "Website Today",
            "Scope Summary", "Open Items", "Sources"]
UNTAGGED = {"Open Items", "Sources"}
KICKOFF_TAGS = {"transcript", "site", "sow", "notes", "user", "maps"}
SOURCE_KINDS = {"intake", "call", "client", "user"}
TAGS = KICKOFF_TAGS | SOURCE_KINDS
CHANGES = ["added", "updated", "resolved-gap", "conflict"]
LOG_HEADER = "| Date | Source | Section | Change | Before | After |"
GAP_SECTION = "Gap Questions"

INTAKE_ITEMS = ["Primary contact", "Website approver", "Business name, address, phone and hours",
                "Logo files", "Brand guidelines", "Photos", "Testimonials or reviews", "Team members",
                "Certifications, awards and memberships", "Legal or compliance language",
                "Sites they like", "Things to avoid", "Gap question answers"]
INTAKE_STATUSES = ["received", "partial", "missing", "none", "n/a"]
INTAKE_OPEN = {"partial", "missing"}
PLATFORMS = ["Domain", "Hosting", "Website login", "Google Analytics", "Google Search Console",
             "Google Business Profile", "Google Tag Manager", "Google Ads", "Meta ads", "Microsoft Ads",
             "CRM, forms or call tracking"]
PAID_PLATFORMS = {"Google Ads", "Meta ads", "Microsoft Ads"}
ACCESS_STATUSES = ["confirmed", "invite sent", "needs help", "someone else manages it", "not set up",
                   "not sure", "no answer", "n/a"]
ACCESS_DONE = {"confirmed", "n/a"}

UPDATES_COLUMNS = ["#", "Section", "Fact", "Evidence"]
UPDATES_SECTIONS = HEADINGS[:9] + ["Platform Access", "Intake Items"]
UPDATES_KINDS = {"call", "client"}

TAG_RE = re.compile(r"\s\[([a-z]+(?:,\s*[a-z]+)*)\]\s*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SECRET_RE = re.compile(r"(?i)\b(password|passcode|passwd|pwd|login|credentials?)\b[^\n|]{0,30}?"
                       r"(\bis\b|:|=)\s*\S+\s*/\s*\S*[\d#!@$%^&*]\S*|\b(password|passcode|passwd|pwd)\s*(is|:|=)\s*\S+")


# ---------- parsing ----------

def squash(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8").replace("\r\n", "\n")


def parse_context(text: str) -> tuple[str, list[str], dict[str, list[str]]]:
    """Returns (client, heading order, lines per heading). Lines keep their text, minus trailing blanks."""
    lines = text.split("\n")
    client = ""
    if lines and lines[0].startswith("Client:"):
        client = lines[0][len("Client:"):].strip()
    order, secs, cur = [], {}, None
    for ln in lines:
        m = re.match(r"^## (.+?)\s*$", ln)
        if m:
            cur = m.group(1)
            order.append(cur)
            secs[cur] = []
        elif cur is not None:
            secs[cur].append(ln)
    for k in secs:
        while secs[k] and not secs[k][-1].strip():
            secs[k].pop()
        while secs[k] and not secs[k][0].strip():
            secs[k].pop(0)
    return client, order, secs


def render_context(text: str, secs: dict[str, list[str]], order: list[str]) -> str:
    head = text.split("\n## ", 1)[0].rstrip("\n")
    out = [head, ""]
    for h in order:
        out.append(f"## {h}")
        out.extend(secs[h])
        out.append("")
    return "\n".join(out).rstrip("\n") + "\n"


def bullets(secs: dict[str, list[str]]) -> list[tuple[str, str]]:
    return [(h, squash(ln[2:])) for h, ls in secs.items() for ln in ls if ln.startswith("- ")]


def tags_of(fact: str) -> set[str] | None:
    m = TAG_RE.search(fact)
    return {t.strip() for t in m.group(1).split(",")} if m else None


def esc(s: str) -> str:
    return s.replace("|", "\\|")


def split_row(line: str) -> list[str]:
    body = line.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|") and not body.endswith("\\|"):
        body = body[:-1]
    cells = re.split(r"(?<!\\)\|", body)
    return [c.strip().replace("\\|", "|") for c in cells]


def read_table(text: str, header: str) -> list[list[str]] | None:
    lines = text.split("\n")
    for i, ln in enumerate(lines):
        if squash(ln) == header:
            rows = []
            for row in lines[i + 2:]:
                if not row.strip().startswith("|"):
                    break
                rows.append(split_row(row))
            return rows
    return None


def paths(folder: Path) -> dict[str, Path]:
    slug = folder.name
    return {"slug": slug, "context": folder / f"{slug}-context.md", "log": folder / f"{slug}-change-log.md",
            "missing": folder / f"{slug}-missing-items.md", "gaps": folder / f"{slug}-gap-questions.md",
            "paid": folder / f"{slug}-paid-media-brief.md", "inventory": folder / f"{slug}-url-inventory.csv",
            "history": folder / "history"}


# ---------- missing items ----------

def default_missing(p: dict) -> tuple[dict, dict]:
    intake = {i: ["missing", ""] for i in INTAKE_ITEMS}
    access = {a: ["no answer", ""] for a in PLATFORMS}
    if not p["paid"].exists():
        for a in PAID_PLATFORMS:
            access[a] = ["n/a", "no paid media in scope"]
    inv = p["inventory"]
    if inv.exists() and len([ln for ln in read(inv).split("\n") if ln.strip()]) <= 1:
        access["Website login"] = ["n/a", "no current website"]
    return intake, access


def load_missing(p: dict) -> tuple[dict, dict]:
    intake, access = default_missing(p)
    if p["missing"].exists():
        text = read(p["missing"])
        for row in read_table(text, "| Item | Status | Note |") or []:
            if len(row) == 3 and row[0] in intake:
                intake[row[0]] = [row[1], row[2]]
        for row in read_table(text, "| Platform | Status | Note |") or []:
            if len(row) == 3 and row[0] in access:
                access[row[0]] = [row[1], row[2]]
    return intake, access


def agenda(intake: dict, access: dict) -> list[str]:
    out = []
    for name in INTAKE_ITEMS:
        st, note = intake[name]
        if st in INTAKE_OPEN:
            out.append(f"{name}: {st}" + (f" ({note})" if note else ""))
    for name in PLATFORMS:
        st, note = access[name]
        if st not in ACCESS_DONE:
            out.append(f"{name}: {st}" + (f" ({note})" if note else ""))
    return out


def render_missing(client: str, stamp: str, intake: dict, access: dict) -> str:
    out = [f"Client: {client}", "", f"# Missing items for {client}", "", f"Last updated: {stamp}", "",
           "## Intake Items", "", "| Item | Status | Note |", "|---|---|---|"]
    out += [f"| {esc(n)} | {intake[n][0]} | {esc(intake[n][1])} |" for n in INTAKE_ITEMS]
    out += ["", "## Platform Access", "", "| Platform | Status | Note |", "|---|---|---|"]
    out += [f"| {esc(n)} | {access[n][0]} | {esc(access[n][1])} |" for n in PLATFORMS]
    out += ["", "## Kickoff Call Agenda", ""]
    items = agenda(intake, access)
    out += [f"{i}. {t}" for i, t in enumerate(items, 1)] if items else ["Nothing missing."]
    return "\n".join(out) + "\n"


# ---------- apply ----------

def find_bullet(lines: list[str], before: str) -> tuple[int | None, str]:
    want = squash(re.sub(r"^-\s+", "", before))
    idx = [i for i, ln in enumerate(lines) if ln.startswith("- ")]
    exact = [i for i in idx if squash(lines[i][2:]) == want]
    if len(exact) == 1:
        return exact[0], ""
    part = [i for i in idx if want and want in squash(lines[i][2:])]
    if len(part) == 1:
        return part[0], ""
    if not part:
        return None, "no bullet in that section matches it"
    return None, f"{len(part)} bullets match it; quote more of the bullet"


def status_entry(val, allowed: list[str], what: str, errors: list[str]) -> list[str] | None:
    st, note = (val, "") if isinstance(val, str) else (val.get("status", ""), val.get("note", ""))
    if st not in allowed:
        errors.append(f"{what}: status '{st}' is not one of {allowed}")
        return None
    if SECRET_RE.search(note or ""):
        errors.append(f"{what}: the note looks like it holds a password; leave it out")
        return None
    return [st, squash(note or "")]


def apply(folder: Path, plan_path: Path, dry: bool) -> int:
    p = paths(folder)
    errors: list[str] = []
    if not p["context"].exists():
        print(f"ERROR: {p['context']} not found")
        return 1
    try:
        plan = json.loads(read(plan_path))
    except (OSError, json.JSONDecodeError) as e:
        print(f"ERROR: cannot read plan {plan_path}: {e}")
        return 1
    kind, date, src = plan.get("source", ""), plan.get("date", ""), plan.get("source_file", "")
    if kind not in SOURCE_KINDS:
        errors.append(f"plan source '{kind}' must be one of {sorted(SOURCE_KINDS)}")
    if not DATE_RE.match(str(date)):
        errors.append(f"plan date '{date}' must be YYYY-MM-DD")
    if not src:
        errors.append("plan source_file is required (the file name the information came from)")
    text = read(p["context"])
    client, order, secs = parse_context(text)
    if order != HEADINGS:
        errors.append(f"context headings are {order}, expected {HEADINGS}")
    log_rows: list[list[str]] = []
    label = f"{kind}: {Path(src).name}"
    for n, ch in enumerate(plan.get("changes", []), 1):
        where = f"change {n}"
        c, sec = ch.get("change", ""), ch.get("section", "")
        fact = squash(re.sub(r"^-\s+", "", ch.get("fact", "")))
        if c not in CHANGES:
            errors.append(f"{where}: change '{c}' must be one of {CHANGES}")
            continue
        if sec not in secs:
            errors.append(f"{where}: section '{sec}' is not a context heading")
            continue
        if sec == "Sources":
            errors.append(f"{where}: the Sources bullet is added by the script; drop this change")
            continue
        if not fact:
            errors.append(f"{where}: fact is empty")
            continue
        if SECRET_RE.search(fact):
            errors.append(f"{where}: the fact looks like it holds a password; leave it out")
            continue
        if sec not in UNTAGGED:
            if fact.startswith("GAP:"):
                errors.append(f"{where}: a change never writes a new GAP: bullet")
                continue
            t = tags_of(fact)
            if t is None:
                fact = f"{fact} [{kind}]"
                t = {kind}
            if not t <= TAGS:
                errors.append(f"{where}: unknown tag(s) {sorted(t - TAGS)}")
                continue
            if kind not in t:
                errors.append(f"{where}: the fact's tag must include [{kind}]")
                continue
        if c == "conflict":
            if not fact.startswith("CONFLICT:"):
                errors.append(f"{where}: a conflict fact starts with CONFLICT:")
                continue
            if len(tags_of(fact) or set()) < 2 and sec not in UNTAGGED:
                errors.append(f"{where}: a CONFLICT: bullet ends with the tags of both sources, e.g. [transcript, {kind}]")
                continue
        elif fact.startswith("CONFLICT:"):
            errors.append(f"{where}: a CONFLICT: bullet uses change 'conflict'")
            continue
        lines = secs[sec]
        if c == "added" or (c == "conflict" and not ch.get("before")):
            if any(squash(ln[2:]) == fact for ln in lines if ln.startswith("- ")):
                errors.append(f"{where}: that bullet is already in {sec}")
                continue
            lines.append(f"- {fact}")
            log_rows.append([date, label, sec, c, "", fact])
            continue
        before = ch.get("before", "")
        befores = before if isinstance(before, list) else [before]
        if not all(befores):
            errors.append(f"{where}: '{c}' needs 'before', the existing bullet it replaces")
            continue
        if len(befores) > 1 and c != "updated":
            errors.append(f"{where}: only 'updated' may replace several bullets with one")
            continue
        hits, bad = [], False
        for b in befores:
            i, why = find_bullet(lines, b)
            if i is None or i in hits:
                errors.append(f"{where}: before '{b[:60]}': {why or 'matches the same bullet twice'} in {sec}")
                bad = True
                break
            hits.append(i)
        if bad:
            continue
        olds = [squash(lines[i][2:]) for i in hits]
        if c == "resolved-gap" and not olds[0].startswith("GAP:"):
            errors.append(f"{where}: resolved-gap replaces a GAP: bullet, but the match is '{olds[0][:60]}'")
            continue
        lines[hits[0]] = f"- {fact}"
        for i in sorted(hits[1:], reverse=True):
            del lines[i]
        log_rows += [[date, label, sec, c, old, fact] for old in olds]
    # gap question answers
    answers = plan.get("answers", {}) or {}
    gtext = read(p["gaps"]) if p["gaps"].exists() else None
    if answers and gtext is None:
        errors.append(f"answers given but {p['gaps'].name} not found")
    elif answers:
        glines = gtext.split("\n")
        for q, ans in answers.items():
            ans = squash(ans)
            if SECRET_RE.search(ans):
                errors.append(f"answer {q}: looks like it holds a password; leave it out")
                continue
            qi = next((i for i, ln in enumerate(glines) if re.match(rf"^{re.escape(str(q))}\.\s", ln)), None)
            if qi is None or qi + 1 >= len(glines) or not glines[qi + 1].startswith("Answer:"):
                errors.append(f"answer {q}: question {q} with an Answer: line not found in {p['gaps'].name}")
                continue
            if glines[qi + 1].strip() != "Answer:":
                errors.append(f"answer {q}: question {q} already has an answer")
                continue
            if not tags_of(ans):
                ans = f"{ans} [{kind}]"
            glines[qi + 1] = f"Answer: {ans}"
            log_rows.append([date, label, GAP_SECTION, "resolved-gap", f"Q{q} (no answer)", f"Q{q}: {ans}"])
        gtext = "\n".join(glines)
    # missing items
    intake, access = load_missing(p)
    for name, val in (plan.get("intake", {}) or {}).items():
        if name not in intake:
            errors.append(f"intake item '{name}' is not one of {INTAKE_ITEMS}")
            continue
        e = status_entry(val, INTAKE_STATUSES, f"intake item '{name}'", errors)
        if e:
            intake[name] = e
    for name, val in (plan.get("access", {}) or {}).items():
        if name not in access:
            errors.append(f"platform '{name}' is not one of {PLATFORMS}")
            continue
        e = status_entry(val, ACCESS_STATUSES, f"platform '{name}'", errors)
        if e:
            access[name] = e
    if errors:
        print("PLAN REJECTED, nothing written. Fix the plan and rerun:")
        for e in errors:
            print(f"- {e}")
        return 1
    src_bullet = f"{Path(src).name} ({kind}, {date})"
    if not any(squash(ln[2:]) == src_bullet for ln in secs["Sources"] if ln.startswith("- ")):
        secs["Sources"].append(f"- {src_bullet}")
        log_rows.append([date, label, "Sources", "added", "", src_bullet])
    if dry:
        print(f"PLAN OK: {len(log_rows)} change(s) would be logged. Nothing written (--dry-run).")
        return 0
    p["history"].mkdir(exist_ok=True)
    n = len(list(p["history"].glob(f"{p['slug']}-context-*.md"))) + 1
    shutil.copyfile(p["context"], p["history"] / f"{p['slug']}-context-{n:02d}.md")
    p["context"].write_text(render_context(text, secs, order), encoding="utf-8")
    if gtext is not None and answers:
        p["gaps"].write_text(gtext, encoding="utf-8")
    if p["log"].exists():
        log = read(p["log"]).rstrip("\n") + "\n"
    else:
        log = f"Client: {client}\n\n# Change log for {client}\n\n{LOG_HEADER}\n|---|---|---|---|---|---|\n"
    log += "".join("| " + " | ".join(esc(c) for c in r) + " |\n" for r in log_rows)
    p["log"].write_text(log, encoding="utf-8")
    p["missing"].write_text(render_missing(client, f"{date} from {label}", intake, access), encoding="utf-8")
    print(f"Applied {len(log_rows)} change(s); snapshot history/{p['slug']}-context-{n:02d}.md")
    return check(folder)


# ---------- check ----------

def check(folder: Path) -> int:
    p = paths(folder)
    res: list[tuple[str, bool, str]] = []
    if not p["context"].exists():
        print(f"ERROR: {p['context']} not found")
        return 1
    text = read(p["context"])
    client, order, secs = parse_context(text)
    snaps = sorted(p["history"].glob(f"{p['slug']}-context-*.md")) if p["history"].is_dir() else []
    res.append(("headings unchanged", order == HEADINGS and bool(client),
                "11 headings in order" if order == HEADINGS else f"found {order}"))
    if not snaps:
        res.append(("snapshot", False, "no history/ snapshot; run apply instead of editing by hand"))
    log_text = read(p["log"]) if p["log"].exists() else ""
    rows = read_table(log_text, LOG_HEADER) if log_text else None
    res.append(("change log", rows is not None, f"{len(rows or [])} row(s)" if rows is not None else
                "missing, or header is not exactly " + LOG_HEADER))
    rows = rows or []
    bad = []
    for r in rows:
        if len(r) != 6:
            bad.append(f"row with {len(r)} cells")
            continue
        d, s, sec, c, b, a = r
        if not DATE_RE.match(d):
            bad.append(f"date '{d}'")
        if s.split(":")[0] not in SOURCE_KINDS:
            bad.append(f"source '{s}'")
        if c not in CHANGES:
            bad.append(f"change '{c}'")
        if c == "resolved-gap" and sec != GAP_SECTION and not b.startswith("GAP:"):
            bad.append(f"resolved-gap before is not a GAP: bullet ({b[:40]})")
        if c == "conflict" and not a.startswith("CONFLICT:"):
            bad.append(f"conflict after does not start with CONFLICT: ({a[:40]})")
        if c == "added" and b:
            bad.append("added row has a Before value")
    res.append(("log rows valid", not bad, "; ".join(bad[:4]) or "dates, sources and change types valid"))
    befores = {squash(r[4]) for r in rows if len(r) == 6}
    afters = {squash(r[5]) for r in rows if len(r) == 6}
    now = {b for _, b in bullets(secs)}
    lost, unlogged, scope_moved = [], [], []
    first = None
    for s in snaps:
        _, _, ssecs = parse_context(read(s))
        first = first or ssecs
        lost += [b for _, b in bullets(ssecs) if b not in now and b not in befores]
    if first:
        start = {b for _, b in bullets(first)}
        unlogged = [b for b in now if b not in start and b not in afters]
        keep = [ln for ln in first.get("Scope Summary", []) if not ln.startswith("- ") and ln.strip()]
        cur = [ln for ln in secs.get("Scope Summary", []) if not ln.startswith("- ") and ln.strip()]
        scope_moved = [ln for ln in keep if ln not in cur]
    res.append(("no fact lost", not lost, "; ".join(x[:50] for x in sorted(set(lost))[:3]) or "every earlier bullet kept or logged as Before"))
    res.append(("every change logged", not unlogged, "; ".join(x[:50] for x in unlogged[:3]) or "every new bullet appears as After"))
    res.append(("scope lines unchanged", not scope_moved, "; ".join(scope_moved[:2]) or "SOW pages, services and quote as kickoff wrote them"))
    badtags = []
    for h, b in bullets(secs):
        if h in UNTAGGED or b.startswith("GAP:"):
            continue
        t = tags_of(b)
        if t is None or not t <= TAGS:
            badtags.append(f"{h}: {b[:50]}")
        elif b.startswith("CONFLICT:") and b in afters and len(t) < 2:
            badtags.append(f"{h}: CONFLICT needs both sources' tags: {b[:40]}")
    res.append(("tags valid", not badtags, "; ".join(badtags[:3]) or "every fact ends with a known tag"))
    mtext = read(p["missing"]) if p["missing"].exists() else ""
    mi = read_table(mtext, "| Item | Status | Note |") if mtext else None
    ma = read_table(mtext, "| Platform | Status | Note |") if mtext else None
    mbad, mdetail = [], ""
    if mi is None or ma is None:
        mbad.append("file or its tables missing")
    else:
        if [r[0] for r in mi] != INTAKE_ITEMS:
            mbad.append("intake items differ from the fixed list")
        if [r[0] for r in ma] != PLATFORMS:
            mbad.append("platforms differ from the fixed list")
        mbad += [f"{r[0]}: status '{r[1]}'" for r in mi if len(r) != 3 or r[1] not in INTAKE_STATUSES]
        mbad += [f"{r[0]}: status '{r[1]}'" for r in ma if len(r) != 3 or r[1] not in ACCESS_STATUSES]
        if not mbad:
            want = agenda({r[0]: r[1:] for r in mi}, {r[0]: r[1:] for r in ma})
            sec = mtext.split("## Kickoff Call Agenda", 1)
            got = [re.sub(r"^\d+\.\s+", "", ln) for ln in (sec[1] if len(sec) > 1 else "").split("\n")
                   if re.match(r"^\d+\.\s", ln)]
            if [squash(x) for x in got] != [squash(x) for x in want]:
                mbad.append("Kickoff Call Agenda does not match the open items in the tables")
            mdetail = f"{len(want)} agenda item(s)"
    res.append(("missing items", not mbad, "; ".join(mbad[:3]) or mdetail))
    leaks = []
    for f in (p["context"], p["log"], p["missing"], p["gaps"]):
        if f.exists():
            leaks += [f"{f.name}:{i}" for i, ln in enumerate(read(f).split("\n"), 1) if SECRET_RE.search(ln)]
    res.append(("no passwords", not leaks, ", ".join(leaks[:3]) or "nothing that looks like a login"))
    print("| Check | Result | Detail |")
    print("|---|---|---|")
    for name, ok, detail in res:
        print(f"| {name} | {'PASS' if ok else 'FAIL'} | {esc(detail)} |")
    ok = all(r[1] for r in res)
    print(f"RESULT: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


# ---------- updates files and outline ----------

def parse_updates(path: Path) -> tuple[dict, list[str]]:
    text = read(path)
    errs, head = [], {}
    for key in ("Client", "Source", "Date", "From"):
        m = re.search(rf"(?m)^{key}:\s*(.+?)\s*$", text)
        head[key] = m.group(1) if m else ""
        if not m:
            errs.append(f"missing '{key}:' line")
    if head["Source"] and head["Source"] not in UPDATES_KINDS:
        errs.append(f"Source '{head['Source']}' must be one of {sorted(UPDATES_KINDS)}")
    if head["Date"] and not DATE_RE.match(head["Date"]):
        errs.append(f"Date '{head['Date']}' must be YYYY-MM-DD")
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
            errs.append(f"row {r[0]}: section '{r[1]}' is not one of {UPDATES_SECTIONS}")
        if not r[2] or not r[3]:
            errs.append(f"row {r[0]}: Fact and Evidence must not be empty")
        out.append(dict(zip(UPDATES_COLUMNS, r)))
    if not out and rows is not None:
        errs.append("no update rows")
    return {"Client": head["Client"], "Source": head["Source"], "Date": head["Date"], "From": head["From"],
            "rows": out}, errs


def outline(text: str) -> dict:
    client, order, secs = parse_context(text)
    data: dict = {"client": client, "headings": order}
    for h in HEADINGS:
        data[f"## {h}"] = [squash(ln[2:]) for ln in secs.get(h, []) if ln.startswith("- ")]
    m = re.search(r"(?m)^SOW pages:\s*(\S+)", text)
    data["SOW pages:"] = m.group(1) if m else ""
    allb = [b for _, b in bullets(secs)]
    data["GAP:"] = [b for b in allb if b.startswith("GAP:")]
    data["CONFLICT:"] = [b for b in allb if b.startswith("CONFLICT:")]
    data["tags"] = sorted({t for b in allb for t in (tags_of(b) or set())})
    return data


def validate_outline(data: dict) -> list[str]:
    errs = []
    if data.get("headings") != HEADINGS:
        errs.append(f"headings {data.get('headings')} differ from {HEADINGS}")
    for k in [f"## {h}" for h in HEADINGS] + ["SOW pages:", "GAP:", "CONFLICT:"]:
        if k not in data:
            errs.append(f"missing key '{k}'")
    unknown = set(data.get("tags", [])) - TAGS
    if unknown:
        errs.append(f"unknown tags {sorted(unknown)}")
    return errs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("apply")
    a.add_argument("folder")
    a.add_argument("--plan", required=True)
    a.add_argument("--dry-run", action="store_true")
    c = sub.add_parser("check")
    c.add_argument("folder")
    u = sub.add_parser("updates")
    u.add_argument("file")
    u.add_argument("--json", action="store_true")
    o = sub.add_parser("outline")
    o.add_argument("file", nargs="?")
    o.add_argument("--validate")
    args = ap.parse_args()
    if args.cmd == "apply":
        return apply(Path(args.folder), Path(args.plan), args.dry_run)
    if args.cmd == "check":
        return check(Path(args.folder))
    if args.cmd == "updates":
        data, errs = parse_updates(Path(args.file))
        if args.json:
            print(json.dumps(data, indent=2))
        for e in errs:
            print(f"ERROR: {e}", file=sys.stderr)
        if not args.json:
            print("UPDATES OK" if not errs else "UPDATES INVALID")
        return 1 if errs else 0
    if args.validate:
        errs = validate_outline(json.loads(read(Path(args.validate))))
        for e in errs:
            print(f"ERROR: {e}", file=sys.stderr)
        print("OUTLINE OK" if not errs else "OUTLINE INVALID")
        return 1 if errs else 0
    if not args.file:
        ap.error("outline needs a context file or --validate")
    print(json.dumps(outline(read(Path(args.file))), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
