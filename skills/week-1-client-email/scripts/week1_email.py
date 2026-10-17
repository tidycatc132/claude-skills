#!/usr/bin/env python3
"""Facts for, and checks on, the end-of-Week-1 client email.

  week1_email.py facts --content content/home --missing kickoff/<slug>/<slug>-missing-items.md
                       --send-date YYYY-MM-DD [--reply-by YYYY-MM-DD]
      Prints JSON: client, slug, out_path, flags (the copy's client-input flags, one per detail),
      asks (the exact "Still needed for the build:" lines), reply_by and reply_by_text.

  week1_email.py check <email.md> --content ... --missing ... --contact "<name>" --am "<name>"
                       --option "<name>=<url>" [--option ...] [--content-url URL]
                       [--recommended "<option name>"] --send-date YYYY-MM-DD --reply-by YYYY-MM-DD
                       [--user-date]
      Prints PASS/FAIL lines and RESULT: PASS or RESULT: FAIL (exit 1 on FAIL).

  week1_email.py contract <article.md>      JSON summary used by the seo-content-writer contract
  week1_email.py contract --validate <json>
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

CIN_RE = re.compile(r"\[CLIENT INPUT NEEDED #(\d+):\s*([^\]]+)\]")
NI_RE = re.compile(r"\[NEEDS INPUT:\s*([^\]]+)\]")
INTERNAL_PAREN_RE = re.compile(r"\s*\((?:[^()]*\b(?:open item|R\d+|GAP)\b[^()]*)\)")

INTAKE_LABELS = {
    "Primary contact": "Who your main contact for the project is",
    "Website approver": "Who approves the website",
    "Business name, address, phone and hours": "Business name, address, phone and hours",
    "Logo files": "Logo files",
    "Brand guidelines": "Brand guidelines",
    "Photos": "Photos",
    "Testimonials or reviews": "Testimonials or reviews",
    "Team members": "Team members",
    "Certifications, awards and memberships": "Certifications, awards and memberships",
    "Legal or compliance language": "Legal or compliance language",
    "Sites they like": "Websites you like",
    "Things to avoid": "Anything to avoid on the site",
    "Gap question answers": "Answers to our open questions",
}
INTAKE_ASK = {"missing", "partial"}
ACCESS_ASK = {"needs help", "someone else manages it", "not sure", "no answer"}
ACCESS_PREFIX = "- Access to"

BANNED = ["thrilled", "excited to partner", "excited to work", "delighted", "world-class",
          "cutting-edge", "best-in-class", "don't hesitate", "do not hesitate", "synergy",
          "game-changer", "your success is our priority"]

LEADS = {
    "options": "Design options:",
    "ask": "What we'd like from you by ",
    "flags": "Details the copy still needs:",
    "missing": "Still needed for the build:",
}
SIGN_TITLE = "Account Manager, WISE Digital Partners"
URL_RE = re.compile(r"https?://\S+")


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8").replace("\r\n", "\n")


def article_path(content: str) -> Path:
    p = Path(content)
    return p / "article.md" if p.is_dir() else p


def parse_flags(text: str) -> list[str]:
    seen, out = set(), []
    for m in re.finditer(r"\[(?:CLIENT INPUT NEEDED #\d+|NEEDS INPUT):[^\]]+\]", text):
        tok = m.group(0)
        c = CIN_RE.fullmatch(tok)
        key = ("n", c.group(1)) if c else ("t", NI_RE.fullmatch(tok).group(1).strip().lower())
        body = c.group(2) if c else NI_RE.fullmatch(tok).group(1)
        if key in seen:
            continue
        seen.add(key)
        body = INTERNAL_PAREN_RE.sub("", body).strip().rstrip(".")
        out.append(body[:1].upper() + body[1:])
    return out


def split_row(line: str) -> list[str]:
    cells = re.split(r"(?<!\\)\|", line.strip().strip("|"))
    return [c.replace("\\|", "|").strip() for c in cells]


def read_table(text: str, header: str) -> list[list[str]]:
    lines = text.split("\n")
    for i, ln in enumerate(lines):
        if ln.strip() == header:
            rows = []
            for row in lines[i + 2:]:
                if not row.strip().startswith("|"):
                    break
                rows.append(split_row(row))
            return rows
    return []


PLATFORMS = ["Domain", "Hosting", "Website login", "Google Analytics", "Google Search Console",
             "Google Business Profile", "Google Tag Manager", "Google Ads", "Meta ads", "Microsoft Ads",
             "CRM, forms or call tracking"]
INTAKE_STATUSES = {"received", "partial", "missing", "none", "n/a"}
ACCESS_STATUSES = {"confirmed", "invite sent", "needs help", "someone else manages it", "not set up",
                   "not sure", "no answer", "n/a"}


def parse_missing(text: str) -> tuple[str, list[str], list[str], list[str]]:
    """Returns client, intake items to ask for, platforms to ask for, and format errors."""
    errors = []
    m = re.search(r"(?m)^Client:\s*(.+)$", text)
    client = m.group(1).strip() if m else ""
    if not client:
        errors.append("no 'Client: <name>' line")
    intake, access = [], []
    for title, header, names, statuses, ask, out in (
            ("intake", "| Item | Status | Note |", INTAKE_LABELS, INTAKE_STATUSES, INTAKE_ASK, intake),
            ("access", "| Platform | Status | Note |", PLATFORMS, ACCESS_STATUSES, ACCESS_ASK, access)):
        rows = read_table(text, header)
        if not rows:
            errors.append(f"no '{header}' table")
        for r in rows:
            if len(r) < 2 or r[0] not in names:
                errors.append(f"unknown {title} row '{r[0] if r else ''}'")
            elif r[1] not in statuses:
                errors.append(f"unknown status '{r[1]}' for '{r[0]}'")
            elif r[1] in ask:
                out.append(r[0])
    return client, intake, access, errors


def asks_for(intake: list[str], access: list[str]) -> tuple[list[str], list[str]]:
    lines = [f"- {INTAKE_LABELS[i]}" for i in intake]
    if access:
        lines.append(f"{ACCESS_PREFIX}: {'; '.join(access)}")
    not_asked = [lbl for k, lbl in INTAKE_LABELS.items() if k not in intake]
    return lines, not_asked


def add_business_days(d: dt.date, n: int) -> dt.date:
    while n:
        d += dt.timedelta(days=1)
        if d.weekday() < 5:
            n -= 1
    return d


def business_days_between(a: dt.date, b: dt.date) -> int:
    n, d = 0, a
    while d < b:
        d += dt.timedelta(days=1)
        if d.weekday() < 5:
            n += 1
    return n


def date_text(d: dt.date) -> str:
    return f"{d.strftime('%A')}, {d.strftime('%B')} {d.day}"


def facts(a) -> dict:
    art = article_path(a.content)
    mpath = Path(a.missing)
    client, intake, access, errors = parse_missing(read(mpath))
    slug = mpath.parent.name
    send = dt.date.fromisoformat(a.send_date)
    reply = dt.date.fromisoformat(a.reply_by) if a.reply_by else add_business_days(send, 3)
    asks, _ = asks_for(intake, access)
    return {
        "client": client, "slug": slug, "out_path": f"emails/{slug}/{slug}-week-1-email.md",
        "flags": parse_flags(read(art)), "asks": asks,
        "errors": errors, "send_date": send.isoformat(), "reply_by": reply.isoformat(), "reply_by_text": date_text(reply),
    }


def greeting_name(contact: str) -> str:
    parts = contact.replace(",", " ").split()
    if parts and parts[0].rstrip(".").lower() == "dr" and len(parts) > 1:
        return f"Dr. {parts[-1]}"
    return parts[0] if parts else ""


def block(lines: list[str], lead_prefix: str) -> tuple[int | None, list[str]]:
    for i, ln in enumerate(lines):
        if ln.startswith(lead_prefix):
            out = []
            for row in lines[i + 1:]:
                if not row.strip():
                    break
                out.append(row)
            return i, out
    return None, []


def check(a) -> int:
    res: list[tuple[bool, str, str]] = []

    def add(ok, name, detail=""):
        res.append((bool(ok), name, detail))

    path = Path(a.email)
    if not path.exists():
        print(f"FAIL: email file not found: {path}\nRESULT: FAIL")
        return 1
    text = read(path)
    lines = text.rstrip("\n").split("\n")
    fx = facts(a)
    send = dt.date.fromisoformat(a.send_date)
    reply = dt.date.fromisoformat(a.reply_by)
    reply_txt = date_text(reply)
    options = []
    for o in a.option or []:
        if "=" not in o:
            add(False, "option argument", f"'{o}' is not name=url")
            continue
        n, u = o.split("=", 1)
        options.append((n.strip(), u.strip()))

    add(not fx["errors"], "missing items file readable", "; ".join(fx["errors"]))

    # path
    want = f"emails/{fx['slug']}/{fx['slug']}-week-1-email.md"
    add(path.as_posix().endswith(want), "output path", f"expected ...{want}")

    # header
    add(len(lines) > 3 and lines[0] == f"Client: {fx['client']}", "client line", f"line 1 must be 'Client: {fx['client']}'")
    subj = lines[1][len("Subject: "):] if len(lines) > 1 and lines[1].startswith("Subject: ") else ""
    add(subj and len(subj) <= 70, "subject line", f"line 2 'Subject: ...' of 70 characters or fewer (got {len(subj)})")
    add(fx["client"].lower() in subj.lower(), "subject names the client", fx["client"])
    add(len(lines) > 2 and lines[2] == "", "blank line 3")
    g = greeting_name(a.contact)
    add(len(lines) > 3 and lines[3] == f"Hi {g},", "greeting", f"line 4 must be 'Hi {g},'")

    # sign-off
    add(lines[-2:] == [a.am, SIGN_TITLE], "sign-off", f"last two lines: '{a.am}' then '{SIGN_TITLE}'")

    # options
    oi, orows = block(lines, LEADS["options"])
    add(oi is not None, "design options lead", f"a line '{LEADS['options']}'")
    want_rows = [f"{n}: {u}" for n, u in options]
    add(orows == want_rows, "one line per design option", f"expected {want_rows}, got {orows}")

    # content link
    if a.content_url:
        add(f"Homepage copy: {a.content_url}" in lines, "content link line", f"a line 'Homepage copy: {a.content_url}'")
    else:
        add(re.search(r"(?i)\battached\b", text), "copy attached", "with no content link, say the homepage copy is attached")

    # links
    allowed = {u for _, u in options} | ({a.content_url} if a.content_url else set())
    stray = [u.rstrip(".,)") for u in URL_RE.findall(text) if u.rstrip(".,)") not in allowed]
    add(not stray, "no other links", ", ".join(stray))

    # ask block
    ai, arows = block(lines, LEADS["ask"])
    add(ai is not None and lines[ai] == f"{LEADS['ask']}{reply_txt}:", "feedback lead with reply-by date",
        f"a line \"{LEADS['ask']}{reply_txt}:\"")
    nums = [r for r in arows if re.match(r"^\d+\. \S", r)]
    add([r.split(".")[0] for r in nums] == ["1", "2", "3"] and len(arows) == 3, "three feedback questions",
        "exactly three lines numbered 1. 2. 3. under the feedback lead")
    start = (ai or 0) + 1 + len(arows) + 1
    para = []
    for ln in lines[start:]:
        if not ln.strip():
            break
        para.append(ln)
    after = "\n".join(para)
    fallback = re.search(r"(?i)\b(hear|heard)\b", after) and reply_txt in after
    add(fallback, "fallback if no reply", f"the paragraph right after the questions has a sentence saying what happens if we haven't heard by {reply_txt}")
    if a.recommended:
        add(a.recommended in after, "recommended option named", a.recommended)
    if not a.user_date:
        bd = business_days_between(send, reply)
        add(3 <= bd <= 5, "reply-by window", f"{bd} business days after {send}; use 3 to 5")

    # flags
    fi, frows = block(lines, LEADS["flags"])
    if fx["flags"]:
        add(fi is not None, "copy details lead", f"a line '{LEADS['flags']}'")
        add(len(frows) == len(fx["flags"]) and all(r.startswith("- ") for r in frows), "one line per copy detail",
            f"{len(fx['flags'])} '- ' lines expected, got {len(frows)}")
    else:
        add(fi is None, "no copy details section", "the copy has no client-input flags")
    add("CLIENT INPUT NEEDED" not in text and "NEEDS INPUT" not in text, "no raw flags", "write the details in plain words")

    # missing
    mi, mrows = block(lines, LEADS["missing"])
    if fx["asks"]:
        add(mi is not None, "still-needed lead", f"a line '{LEADS['missing']}'")
        want_m = [x for x in fx["asks"] if not x.startswith(ACCESS_PREFIX)]
        got_m = [r for r in mrows if not r.startswith(ACCESS_PREFIX)]
        ok = len(got_m) == len(want_m) and all(r == w or r.startswith(w + ":") or r.startswith(w + " (")
                                               for r, w in zip(got_m, want_m))
        add(ok, "still-needed items", f"expected lines starting {want_m}, got {got_m}")
        acc_want = next((x for x in fx["asks"] if x.startswith(ACCESS_PREFIX)), None)
        acc_got = [r for r in mrows if r.startswith(ACCESS_PREFIX)]
        if acc_want:
            add(len(acc_got) == 1 and acc_got[0].startswith(acc_want), "access line", f"one line starting '{acc_want}'")
        else:
            add(not acc_got, "no access line", "all platform access is settled")
    else:
        add(mi is None, "no still-needed section", "nothing is missing")

    # next steps
    add(re.search(r"(?m)^Next steps: \S", text), "next steps", "a paragraph starting 'Next steps: '")

    # voice
    low = text.lower()
    hits = [b for b in BANNED if b in low]
    add(not hits, "no generic agency language", ", ".join(hits))
    add(text.count("!") <= 1, "at most one exclamation mark", str(text.count("!")))
    add(not re.search(r"(?m)^#|\*\*|^\* ", text), "plain text", "no markdown headings, bold or '* ' bullets")
    add(not re.search(r"(?i)\bpassword", text) or re.search(r"(?i)\bnever send (us )?(your )?passwords?", text),
        "no password requests", "only 'never send passwords' may mention passwords")

    # words outside lists
    body = lines[4:-2]
    prose = [ln for ln in body if not (ln.startswith("- ") or re.match(r"^\d+\. ", ln) or ln in want_rows)]
    words = len(" ".join(prose).split())
    add(words <= 250, "length", f"{words} words outside the lists; at most 250")

    # numbers
    src = read(article_path(a.content)) + read(Path(a.missing))
    src_nums = set(re.findall(r"\d+", src))
    date_nums = {str(reply.day), str(reply.year), str(send.day), str(send.year)}
    bad = []
    for ln in prose:
        for n in re.findall(r"\d+", URL_RE.sub("", ln)):
            if int(n) > 5 and n not in src_nums and n not in date_nums:
                bad.append(n)
    add(not bad, "numbers come from the files", ", ".join(sorted(set(bad))))

    fails = 0
    for ok, name, detail in res:
        print(f"{'PASS' if ok else 'FAIL'}: {name}" + ("" if ok or not detail else f" ({detail})"))
        fails += not ok
    print(f"{len(res) - fails}/{len(res)} checks passed")
    print("RESULT: PASS" if not fails else "RESULT: FAIL")
    return 1 if fails else 0


CONTRACT_KEYS = ["content/<url-slug>/", "[CLIENT INPUT NEEDED #n: ...]", "[NEEDS INPUT: ...]"]


def contract(a) -> int:
    if a.validate:
        data = json.loads(read(Path(a.path)))
        bad = [k for k in CONTRACT_KEYS if k not in data]
        if bad or not isinstance(data.get("flags"), list):
            print(f"INVALID: missing {bad or ['flags']}")
            return 1
        print("VALID")
        return 0
    text = read(Path(a.path))
    out = {
        "content/<url-slug>/": Path(a.path).parent.name + "/",
        "[CLIENT INPUT NEEDED #n: ...]": sorted({int(n) for n, _ in CIN_RE.findall(text)}),
        "[NEEDS INPUT: ...]": len(NI_RE.findall(text)),
        "flags": parse_flags(text),
    }
    print(json.dumps(out, indent=2))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--content", required=True, help="content/<url-slug>/ folder or its article.md")
        p.add_argument("--missing", required=True, help="kickoff/<slug>/<slug>-missing-items.md")
        p.add_argument("--send-date", required=True)

    f = sub.add_parser("facts")
    common(f)
    f.add_argument("--reply-by")
    c = sub.add_parser("check")
    c.add_argument("email")
    common(c)
    c.add_argument("--reply-by", required=True)
    c.add_argument("--user-date", action="store_true", help="the reply-by date came from the user")
    c.add_argument("--contact", required=True)
    c.add_argument("--am", required=True)
    c.add_argument("--option", action="append", required=True)
    c.add_argument("--content-url")
    c.add_argument("--recommended")
    k = sub.add_parser("contract")
    k.add_argument("path")
    k.add_argument("--validate", action="store_true")
    a = ap.parse_args()
    if a.cmd != "contract":
        for p in (article_path(a.content), Path(a.missing)):
            if not p.exists():
                print(f"ERROR: not found: {p}")
                return 2
    if a.cmd == "facts":
        fx = facts(a)
        if fx["errors"]:
            print("MISSING ITEMS INVALID: " + "; ".join(fx["errors"]))
            return 2
        print(json.dumps(fx, indent=2))
        return 0
    if a.cmd == "check":
        return check(a)
    return contract(a)


if __name__ == "__main__":
    sys.exit(main())
