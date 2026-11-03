#!/usr/bin/env python3
"""Facts and checks for the Week 5 staging review email.

  week5_email.py facts --slug S [--root DIR] [--staging-url URL] [--send-date YYYY-MM-DD]
                       [--reply-by YYYY-MM-DD] [--contact NAME] [--protected] [--bugherd]
                       [--no-go-ahead]
      Reads kickoff/S/S-context.md, the newest qa/S/S-staging-qa-<date>.md and
      client-reference/S/voice.md, and prints the facts plus the exact block the
      email file must start with (warnings, then header). Prints STOP and exits 2
      when the email cannot be written yet.

  week5_email.py check emails/S/S-week-5-email.md [--root DIR] [--title TEXT]
      Checks a written or hand-edited email. Last line RESULT: PASS or RESULT: FAIL.

  week5_email.py contract qa <staging QA report>
  week5_email.py contract email <week 5 email file>
  week5_email.py contract --validate <json file>
      Readers used by the pipeline contracts.

Standard library only. The staging password is never an input: the AM pastes it
into the final email by hand.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

TITLE_DEFAULT = "Account Manager, WISE Digital Partners"
PASSWORD_LINE = "Password: [AM: paste the staging password here]"
MAX_WORDS = 149  # "under 150 words"
BUSINESS_DAYS = 3
RULE_DEFAULT = f"{BUSINESS_DAYS} business days"
RULE_AM = "AM's date"
HEADER_KEYS = ["Client", "To", "Send date", "Reply by", "Reply-by rule", "Staging",
               "Password", "Edits by", "No-reply line", "QA report"]
WARN_PREFIX = "WARNING (not part of the email):"
TITLES = {"dr", "mr", "mrs", "ms", "mx", "prof"}
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August",
          "September", "October", "November", "December"]

# Words from the team's side of the process that never go to the client.
INTERNAL = [
    (r"\bQA\b", "QA"),
    (r"(?i)quality assurance", "quality assurance"),
    (r"(?i)punch[ -]?list", "punch list"),
    (r"(?i)\bseverit", "severity"),
    (r"\b(?:CRITICAL|MAJOR|MINOR)\b", "a severity label"),
    (r"(?i)\bfindings\b|\bfinding\b(?! (?:any|some|it|them))", "finding"),
    (r"(?i)launch toggle", "launch toggle"),
    (r"(?i)\bnoindex\b", "noindex"),
    (r"(?i)\bAM items?\b", "AM items"),
    (r"(?i)\bhand-?off\b", "handoff"),
    (r"(?i)go-live message", "go-live message"),
    (r"(?i)\bscope change", "scope change"),
    (r"(?i)\b(?:copy review|seo review|design review|dev ready)\b", "a BugHerd column name"),
    (r"(?i)\bguest (?:access|user)", "guest access"),
    (r"(?i)\binternal\b", "internal"),
    (r"\bNOT READY\b|\bCONDITIONAL\b|RESULT:", "a QA result"),
    (r"\bPM\b|(?i:project manager)", "PM"),
]


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def parse_date(s: str) -> dt.date:
    return dt.date.fromisoformat(s.strip())


def add_business_days(d: dt.date, n: int) -> dt.date:
    while n > 0:
        d += dt.timedelta(days=1)
        if d.weekday() < 5:
            n -= 1
    return d


def written(d: dt.date) -> str:
    return f"{WEEKDAYS[d.weekday()]}, {MONTHS[d.month - 1]} {d.day}"


def strip_tags(v: str) -> str:
    return re.sub(r"\s*\[[^\]]*\]\s*$", "", v).strip()


# ---------------------------------------------------------------- readers

def read_context(p: Path) -> dict:
    text = read(p)
    out = {"name": "", "contact": ""}
    m = re.search(r"(?m)^- Name:\s*(.+)$", text)
    if m:
        out["name"] = strip_tags(m.group(1))
    else:
        m = re.search(r"(?m)^Client:\s*(.+)$", text)
        if m:
            out["name"] = m.group(1).strip()
    m = re.search(r"(?mi)^- (?:primary |main )?contact(?: name)?:\s*(.+)$", text)
    if m:
        out["contact"] = strip_tags(m.group(1))
    return out


def report_date(p: Path, slug: str) -> dt.date | None:
    m = re.fullmatch(re.escape(slug) + r"-staging-qa-(\d{4}-\d{2}-\d{2})\.md", p.name)
    if not m:
        return None
    try:
        return parse_date(m.group(1))
    except ValueError:
        return None


def latest_report(root: Path, slug: str) -> Path | None:
    d = root / "qa" / slug
    if not d.is_dir():
        return None
    dated = [(report_date(p, slug), p) for p in d.glob(f"{slug}-staging-qa-*.md")]
    dated = [x for x in dated if x[0]]
    return max(dated)[1] if dated else None


def read_qa(p: Path) -> dict:
    text = read(p)
    lines = text.splitlines()
    out = {"client": "", "checked": "", "staging": "", "result": "", "am_items": []}
    for key, field in (("Client", "client"), ("Checked", "checked"), ("Staging", "staging")):
        m = re.search(rf"(?m)^{key}:\s*(.+)$", text)
        if m:
            out[field] = m.group(1).strip()
    if out["staging"]:
        out["staging"] = out["staging"].split()[0]
    last = next((ln.strip() for ln in reversed(lines) if ln.strip()), "")
    m = re.fullmatch(r"RESULT: (READY|CONDITIONAL|NOT READY)", last)
    out["result"] = m.group(1) if m else ""
    m = re.search(r"(?ms)^## AM Items\s*$(.*?)(?=^## |^RESULT:|\Z)", text)
    if m:
        for ln in m.group(1).splitlines():
            ln = ln.strip()
            if ln.startswith("- ") and ln[2:].strip().lower() not in ("none", "none."):
                out["am_items"].append(ln[2:].strip())
    return out


def tone_row(p: Path) -> str:
    if not p.is_file():
        return ""
    text = read(p)
    m = re.search(r"(?ms)^## Tone Matrix\s*$(.*?)(?=^## |\Z)", text)
    if not m:
        return ""
    for ln in m.group(1).splitlines():
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) >= 2 and "email" in cells[0].lower() and not set(cells[0]) <= set("-: "):
            return " | ".join(cells[1:])
    return ""


# ---------------------------------------------------------------- shared

def warnings_for(root: Path, rep: Path | None, qa: dict | None) -> list[str]:
    if rep is None:
        return [f"{WARN_PREFIX} no staging QA report found in qa/. Run staging-site-qa before the client sees the site."]
    rel = rep.relative_to(root).as_posix()
    w = []
    if qa["result"] == "NOT READY":
        w.append(f"{WARN_PREFIX} the latest QA report ({rel}) ends RESULT: NOT READY. Send only after the PM clears the launch blockers.")
    elif not qa["result"]:
        w.append(f"{WARN_PREFIX} the latest QA report ({rel}) has no RESULT line. Re-run staging-site-qa.")
    if qa["am_items"]:
        n = len(qa["am_items"])
        w.append(f"{WARN_PREFIX} the latest QA report has {n} open AM item{'s' if n != 1 else ''}. Review {'them' if n != 1 else 'it'} before the client sees the link:")
        w.extend(f"{WARN_PREFIX}   - {it}" for it in qa["am_items"])
    return w


def greeting_for(contact: str) -> str:
    parts = contact.replace(",", " ").split()
    if not parts:
        return ""
    if parts[0].rstrip(".").lower() in TITLES and len(parts) > 1:
        return f"Hi {parts[0].rstrip('.')}. {parts[-1]},"
    return f"Hi {parts[0]},"


def norm_url(u: str) -> str:
    return u.strip().rstrip("/").lower()


# ---------------------------------------------------------------- facts

def cmd_facts(a) -> int:
    root = Path(a.root).resolve()
    s = a.slug
    ctx_p = root / "kickoff" / s / f"{s}-context.md"
    stops = []
    if not ctx_p.is_file():
        stops.append(f"STOP: {ctx_p.relative_to(root).as_posix()} not found. Run new-build-kickoff first.")
    rep = latest_report(root, s)
    qa = read_qa(rep) if rep else None
    staging = (a.staging_url or (qa["staging"] if qa else "")).strip()
    if not staging:
        stops.append("STOP: no staging URL. Ask the AM for it (no QA report names one).")
    elif not re.match(r"https?://", staging):
        stops.append(f"STOP: the staging URL '{staging}' does not start with http:// or https://.")
    send = parse_date(a.send_date) if a.send_date else dt.date.today()
    if a.reply_by:
        reply = parse_date(a.reply_by)
        rule = RULE_AM
        if reply <= send or reply.weekday() >= 5:
            stops.append(f"STOP: the reply-by date {reply} must be a weekday after the send date {send}.")
    else:
        reply = add_business_days(send, BUSINESS_DAYS)
        rule = RULE_DEFAULT
    if stops:
        print("\n".join(stops))
        return 2
    ctx = read_context(ctx_p)
    contact = (a.contact or ctx["contact"]).strip()
    voice_p = root / "client-reference" / s / "voice.md"
    tone = tone_row(voice_p)
    header = [
        f"Client: {ctx['name']}",
        f"To: {contact or 'unknown'}",
        f"Send date: {send.isoformat()}",
        f"Reply by: {reply.isoformat()}",
        f"Reply-by rule: {rule}",
        f"Staging: {staging}",
        f"Password: {'AM pastes by hand' if a.protected else 'not needed'}",
        f"Edits by: {'reply or BugHerd' if a.bugherd else 'reply'}",
        f"No-reply line: {'dropped' if a.no_go_ahead else 'yes'}",
        f"QA report: {rep.relative_to(root).as_posix() + ' (RESULT: ' + (qa['result'] or 'missing') + ')' if rep else 'none'}",
    ]
    warns = warnings_for(root, rep, qa)
    print(f"Client: {ctx['name'] or 'unknown (no - Name: line in the context)'}")
    print(f"Contact: {contact or 'unknown: ask the AM who the email goes to'}")
    if contact:
        print(f"Greeting: {greeting_for(contact)}")
    print(f"Staging URL: {staging}")
    print(f"Send date: {send.isoformat()} ({WEEKDAYS[send.weekday()]})")
    print(f"Reply by: {reply.isoformat()} (write it as \"{written(reply)}\"; rule: {rule})")
    print(f"Password: {'protected: put this line under the link, exactly: ' + PASSWORD_LINE if a.protected else 'not needed: say nothing about a password'}")
    print(f"Edits by: {'reply to the email, or comment in BugHerd' if a.bugherd else 'reply to the email (do not mention BugHerd)'}")
    print(f"No-reply line: {'dropped at the AM request: no go-ahead sentence' if a.no_go_ahead else 'yes: say we will go ahead with the site as it is if there is no reply by ' + written(reply)}")
    if rep:
        print(f"QA report: {rep.relative_to(root).as_posix()} (RESULT: {qa['result'] or 'missing'}, AM items: {len(qa['am_items'])})")
    else:
        print("QA report: none")
    print(f"Voice (email row): {tone or 'none (no voice.md email row)'}")
    print(f"Sign-off: <AM name>, then {TITLE_DEFAULT}")
    print()
    print("Start the email file with exactly these lines, then a blank line, then Subject:")
    print("-----")
    for ln in warns:
        print(ln)
    if warns:
        print()
    for ln in header:
        print(ln)
    print("-----")
    return 0


# ---------------------------------------------------------------- check

class Checks:
    def __init__(self):
        self.rows = []

    def add(self, name: str, ok: bool, detail: str = ""):
        self.rows.append((name, ok, detail))

    def print(self) -> int:
        print("| Check | Result | Detail |")
        print("|---|---|---|")
        for n, ok, d in self.rows:
            print(f"| {n} | {'PASS' if ok else 'FAIL'} | {d.replace('|', '/')} |")
        bad = [r for r in self.rows if not r[1]]
        print()
        print("RESULT: PASS" if not bad else "RESULT: FAIL")
        return 0 if not bad else 1


def split_email(text: str):
    lines = text.splitlines()
    warns, header, body, subject = [], {}, [], None
    order = []
    i = 0
    while i < len(lines) and (lines[i].startswith(WARN_PREFIX) or not lines[i].strip()):
        if lines[i].strip():
            warns.append(lines[i].rstrip())
        i += 1
    while i < len(lines) and lines[i].strip() and not lines[i].startswith("Subject:"):
        m = re.match(r"([A-Za-z' -]+):\s?(.*)$", lines[i])
        if m:
            header[m.group(1)] = m.group(2).strip()
            order.append(m.group(1))
        else:
            order.append(lines[i])
        i += 1
    while i < len(lines) and not lines[i].strip():
        i += 1
    if i < len(lines) and lines[i].startswith("Subject:"):
        subject = lines[i][len("Subject:"):].strip()
        i += 1
    body = lines[i:]
    return warns, header, order, subject, body


def cmd_check(a) -> int:
    f = Path(a.file).resolve()
    C = Checks()
    m = re.fullmatch(r"(.+)-week-5-email\.md", f.name)
    if not f.is_file() or not m:
        print(f"STOP: {a.file} is not an existing <slug>-week-5-email.md file.")
        return 2
    s = m.group(1)
    root = Path(a.root).resolve() if a.root else f.parents[2]
    text = read(f)
    warns, h, order, subject, body_lines = split_email(text)
    body = "\n".join(body_lines).strip()

    # header
    C.add("header lines", order == HEADER_KEYS,
          "in order: " + ", ".join(HEADER_KEYS) if order != HEADER_KEYS else "all present, in order")
    ctx_p = root / "kickoff" / s / f"{s}-context.md"
    ctx = read_context(ctx_p) if ctx_p.is_file() else {"name": "", "contact": ""}
    C.add("client name", bool(ctx["name"]) and h.get("Client") == ctx["name"],
          f"context says '{ctx['name'] or 'no context file'}', header says '{h.get('Client', '')}'")

    # dates
    send = reply = None
    try:
        send = parse_date(h.get("Send date", ""))
        reply = parse_date(h.get("Reply by", ""))
    except ValueError:
        pass
    rule = h.get("Reply-by rule", "")
    if send and reply:
        if rule == RULE_DEFAULT:
            want = add_business_days(send, BUSINESS_DAYS)
            C.add("reply-by date", reply == want, f"{BUSINESS_DAYS} business days after {send} is {want}; header has {reply}")
        elif rule == RULE_AM:
            C.add("reply-by date", reply > send and reply.weekday() < 5, f"AM's date {reply}: must be a weekday after {send}")
        else:
            C.add("reply-by date", False, f"Reply-by rule must be '{RULE_DEFAULT}' or '{RULE_AM}'")
    else:
        C.add("reply-by date", False, "Send date and Reply by must be YYYY-MM-DD")

    # warnings at the top
    rep = latest_report(root, s)
    qa = read_qa(rep) if rep else None
    want_w = warnings_for(root, rep, qa)
    C.add("warnings above the email", warns == want_w,
          "match the latest QA report" if warns == want_w else
          f"expected {len(want_w)} warning line(s) from {rep.relative_to(root).as_posix() if rep else 'no QA report'}, found {len(warns)}; copy them from facts")
    want_q = rep.relative_to(root).as_posix() + " (RESULT: " + (qa["result"] or "missing") + ")" if rep else "none"
    C.add("QA report line", h.get("QA report") == want_q, f"expected '{want_q}'")
    body_warn = [ln for ln in body_lines if ln.startswith(WARN_PREFIX)]
    C.add("no warning inside the email", not body_warn, f"{len(body_warn)} warning line(s) below Subject")

    # subject and body size
    C.add("subject", bool(subject), "a Subject: line after the header" if not subject else subject)
    words = re.findall(r"\S+", body)
    C.add("body under 150 words", 0 < len(words) <= MAX_WORDS, f"{len(words)} words (max {MAX_WORDS})")

    # greeting and sign-off
    nonblank = [ln.strip() for ln in body_lines if ln.strip()]
    to = h.get("To", "")
    g_ok = bool(nonblank) and nonblank[0].startswith("Hi ") and nonblank[0].endswith(",")
    if to and to != "unknown":
        g_ok = g_ok and nonblank[0] == greeting_for(to)
    C.add("greeting", g_ok and to != "unknown", f"expected '{greeting_for(to) if to and to != 'unknown' else 'a named contact in To:'}'")
    title = a.title or TITLE_DEFAULT
    C.add("sign-off", len(nonblank) >= 2 and nonblank[-1] == title,
          f"last line is '{title}' (the AM's name above it when known)")

    # link
    staging = h.get("Staging", "")
    urls = [u.rstrip(".,;:!?") for u in re.findall(r"https?://[^\s)\]>\"']+", body)]
    C.add("staging link", bool(staging) and any(norm_url(u) == norm_url(staging) for u in urls),
          f"body must contain {staging or 'the staging URL'}")
    other = [u for u in urls if not norm_url(u).startswith(norm_url(staging))] if staging else urls
    C.add("no other links", not other, ", ".join(other) or "only the staging site")

    # reply-by in the body, and no other dates
    if reply:
        C.add("reply-by written out", written(reply) in body, f"body must say \"{written(reply)}\"")
        stray = []
        for mm in re.finditer(r"\b(" + "|".join(MONTHS) + r")\s+(\d{1,2})\b", body):
            if (MONTHS.index(mm.group(1)) + 1, int(mm.group(2))) != (reply.month, reply.day):
                stray.append(mm.group(0))
        for wd in re.findall(r"\b(" + "|".join(WEEKDAYS) + r")\b", body):
            if wd != WEEKDAYS[reply.weekday()]:
                stray.append(wd)
        stray += re.findall(r"\b\d{1,4}[/-]\d{1,2}[/-]\d{1,4}\b", body)
        C.add("one date only", not stray, ", ".join(stray) or "only the reply-by date")

    # what the email must say
    low = body.lower()
    C.add("last check before launch", "launch" in low, "say this is the last check before launch")
    topics = {"facts": r"\bfacts?\b", "names": r"\bnames?\b", "numbers": r"\bnumbers?\b",
              "services": r"\bservices?\b", "contact details": r"\bcontact (?:details|info)"}
    miss = [k for k, rx in topics.items() if not re.search(rx, low)]
    C.add("what to look at", not miss, "missing: " + ", ".join(miss) if miss else "facts, names, numbers, services, contact details")
    C.add("reply to send edits", re.search(r"\breply\b", low) is not None, "say how to send edits: reply to this email")
    want_bh = "BugHerd" in h.get("Edits by", "")
    has_bh = "bugherd" in low
    C.add("BugHerd mention", want_bh == has_bh,
          "Edits by allows BugHerd: mention it" if want_bh else "the client has no BugHerd access: do not mention it")

    # password
    pw = h.get("Password", "")
    pw_lines = [ln.strip() for ln in body_lines if re.match(r"\s*password\b", ln, re.I)]
    if pw == "AM pastes by hand":
        C.add("password placeholder", pw_lines == [PASSWORD_LINE], f"one line, exactly: {PASSWORD_LINE}")
    elif pw == "not needed":
        C.add("password placeholder", "password" not in low, "the site is not protected: no password line")
    else:
        C.add("password placeholder", False, "Password must be 'AM pastes by hand' or 'not needed'")

    # go-ahead line
    nr = h.get("No-reply line", "")
    sentences = re.split(r"(?<=[.!?])\s+", body.replace("\n", " "))
    ga = [x for x in sentences if re.search(r"\bgo ahead\b|\bproceed\b", x, re.I)]
    if nr == "yes":
        ok = any(reply and written(reply) in x or re.search(r"\b(then|that date|by then)\b", x, re.I) for x in ga)
        C.add("no-reply line", bool(ga) and ok, "one sentence: if there is no reply by the date, we go ahead with the site as it is")
    elif nr == "dropped":
        C.add("no-reply line", not ga, "the AM dropped it: no go-ahead sentence")
    else:
        C.add("no-reply line", False, "No-reply line must be 'yes' or 'dropped'")

    # internal words
    hits = []
    for rx, label in INTERNAL:
        if re.search(rx, (subject or "") + "\n" + body):
            hits.append(label)
    C.add("no internal words", not hits, ", ".join(hits) or "none")
    return C.print()


# ---------------------------------------------------------------- contracts

def cmd_contract(a) -> int:
    if a.validate:
        data = json.loads(read(Path(a.validate)))
        if "RESULT:" in data:
            need = {"Staging:": str, "## AM Items": list, "RESULT:": str}
        else:
            need = {"Client:": str, "Send date:": str, "Reply by:": str}
        errs = [f"missing or wrong type: {k}" for k, t in need.items() if not isinstance(data.get(k), t)]
        if "RESULT:" in data and data.get("RESULT:") not in ("READY", "CONDITIONAL", "NOT READY"):
            errs.append("RESULT: must be READY, CONDITIONAL or NOT READY")
        if "Staging:" in data and not str(data.get("Staging:", "")).startswith("http"):
            errs.append("Staging: must be a URL")
        for k in ("Send date:", "Reply by:"):
            if k in data:
                try:
                    parse_date(data[k])
                except (ValueError, TypeError):
                    errs.append(f"{k} must be YYYY-MM-DD")
        if errs:
            print("\n".join(errs), file=sys.stderr)
            return 1
        print("OK")
        return 0
    if a.kind == "qa":
        q = read_qa(Path(a.path))
        out = {"Staging:": q["staging"], "## AM Items": q["am_items"], "RESULT:": q["result"]}
    elif a.kind == "email":
        _, h, _, _, _ = split_email(read(Path(a.path)))
        out = {"Client:": h.get("Client", ""), "Send date:": h.get("Send date", ""), "Reply by:": h.get("Reply by", "")}
    else:
        print("contract needs 'qa <file>', 'email <file>' or --validate <json>", file=sys.stderr)
        return 2
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("facts")
    f.add_argument("--slug", required=True)
    f.add_argument("--root", default=".")
    f.add_argument("--staging-url")
    f.add_argument("--send-date")
    f.add_argument("--reply-by")
    f.add_argument("--contact")
    f.add_argument("--protected", action="store_true")
    f.add_argument("--bugherd", action="store_true")
    f.add_argument("--no-go-ahead", action="store_true")
    c = sub.add_parser("check")
    c.add_argument("file")
    c.add_argument("--root")
    c.add_argument("--title")
    k = sub.add_parser("contract")
    k.add_argument("kind", nargs="?")
    k.add_argument("path", nargs="?")
    k.add_argument("--validate")
    a = ap.parse_args(argv)
    try:
        return {"facts": cmd_facts, "check": cmd_check, "contract": cmd_contract}[a.cmd](a)
    except ValueError as e:
        print(f"STOP: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
