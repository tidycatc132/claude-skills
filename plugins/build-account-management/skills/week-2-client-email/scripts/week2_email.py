#!/usr/bin/env python3
"""Facts and checks for the Week 2 client email (standard library only).

  week2_email.py facts --slug S [--root DIR] [--contact NAME] [--send-date D] [--reply-by D]
                       [--deck PATH] [--pdf NAME | --no-pdf]
      Validates the inputs and prints JSON: client, out_path, greeting, deck_file, pdf_file,
      reply_by, reply_by_text, bets, pages, asks.  Exit 2 when an input is missing or invalid.

  week2_email.py check EMAIL --slug S --contact NAME --am NAME [--title T] [--link URL ...]
                       [--send-date D] [--reply-by D] [--user-date] [--deck PATH] [--pdf NAME | --no-pdf]
      One row per check, then RESULT: PASS or RESULT: FAIL.

  week2_email.py contract briefing|missing FILE.md     print the parsed file as JSON
  week2_email.py contract --validate FILE.json         exit 0 when the JSON has the expected keys
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import zipfile
from pathlib import Path

TITLE = "Account Manager, WISE Digital Partners"
BRIEFING_SECTIONS = ["Executive Summary", "Key Strategic Bets", "Numbers the AM Should Know",
                     "Anticipated Client Questions", "Calibration Framing"]
ITEM_HEAD = "| Item | Status | Note |"
PLATFORM_HEAD = "| Platform | Status | Note |"
OWED_ITEM = {"missing", "partial"}
OWED_ACCESS = {"needs help", "someone else manages it", "not sure", "no answer"}
CLIENT_WORDS = {"Gap question answers": "Answers to our open questions"}
TITLES = {"dr", "mr", "mrs", "ms", "mx", "prof"}
QUESTIONS = ["Does this feel right?", "Does anything surprise you?", "Is anything missing?"]
INTERNAL = r"\b(wrong if|calibration|am briefing|briefing|internal|key strategic bets|anticipated|confirm with seo)\b|\[(needs input|client input needed|write)"
PROMISE = r"\btop\s+(?:\d+|three|five|ten)\b|\b(?:page one|first page|number one|#1)\b|\brank (?:first|number)"
FILLER = ["thrilled", "excited to", "delighted", "world-class", "cutting-edge", "best-in-class",
          "don't hesitate", "do not hesitate", "synergy", "game-changer", "game changer",
          "your success is our priority", "guarantee", "we promise"]
STOP = set("""a an and are as at be been but by can could do does for from had has have how i if in into is
it its it's just more most no not now of on or our out over so than that the their them then there these
they this to too up us was we were what when where which while who why will with would you your yours
reason first then also each very own page pages""".split())
MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
WEEKDAYS = "Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday"
FLAG = re.compile(r"\[(?:NEEDS INPUT|CLIENT INPUT NEEDED(?: #\d+)?):\s*([^\]]+)\]")


# ----------------------------------------------------------------------------- parsing
def read(p: Path) -> str:
    return p.read_text(encoding="utf-8-sig").replace("\r\n", "\n")


def sections(text: str) -> dict[str, str]:
    out, cur = {}, None
    for line in text.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            cur = m.group(1)
            out[cur] = ""
        elif cur:
            out[cur] += line + "\n"
    return out


def client_line(text: str) -> str:
    m = re.search(r"(?m)^Client:\s*(.+?)\s*$", text)
    return m.group(1) if m else ""


def parse_briefing(text: str) -> dict:
    sec = sections(text)
    out: dict = {"Client": client_line(text)}
    for name in BRIEFING_SECTIONS:
        if name not in sec:
            continue
        body = sec[name]
        if name == "Calibration Framing":
            out[name] = " ".join(body.split())
        elif name == "Key Strategic Bets":
            items = re.split(r"(?m)^\d+\.\s+", body)[1:]
            out[name] = [" ".join(x.split()) for x in items if x.strip()]
        elif name == "Anticipated Client Questions":
            out[name] = [m.group(1).strip() for m in re.finditer(r"(?m)^\d+\.\s+Q:\s*(.+)$", body)]
        else:
            out[name] = [m.group(1).strip() for m in re.finditer(r"(?m)^[-*]\s+(.+)$", body)]
    return out


def table_rows(text: str, head: str) -> list[list[str]] | None:
    lines = text.splitlines()
    norm = lambda s: re.sub(r"\s+", " ", s.strip())
    for i, line in enumerate(lines):
        if norm(line) == head:
            rows = []
            for row in lines[i + 2:]:
                if not row.strip().startswith("|"):
                    break
                cells = [c.strip() for c in row.strip().strip("|").split("|")]
                rows.append((cells + ["", "", ""])[:3])
            return rows
    return None


def parse_missing(text: str) -> dict:
    out: dict = {"Client": client_line(text)}
    items = table_rows(text, ITEM_HEAD)
    plats = table_rows(text, PLATFORM_HEAD)
    if items is not None:
        out[ITEM_HEAD] = [{"Item": a, "Status": b.lower(), "Note": c} for a, b, c in items]
    if plats is not None:
        out[PLATFORM_HEAD] = [{"Platform": a, "Status": b.lower(), "Note": c} for a, b, c in plats]
    return out


def deck_text(p: Path) -> str:
    with zipfile.ZipFile(p) as z:
        parts = [n for n in z.namelist() if re.match(r"ppt/(slides|notesSlides)/[A-Za-z]+\d+\.xml$", n)]
        texts = []
        for n in parts:
            xml = z.read(n).decode("utf-8", "replace")
            texts.append(" ".join(re.findall(r"<a:t>([^<]*)</a:t>", xml)))
    return "\n".join(texts).replace("&amp;", "&")


def page_label(folder: str) -> str:
    return "Home" if folder == "home" else " ".join(w.capitalize() for w in folder.split("-"))


# ----------------------------------------------------------------------------- dates
def parse_date(s: str) -> dt.date:
    return dt.date.fromisoformat(s)


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


def long_date(d: dt.date) -> str:
    return f"{d.strftime('%A')}, {d.strftime('%B')} {d.day}"


# ----------------------------------------------------------------------------- facts
class InputError(Exception):
    pass


def paths(a) -> dict[str, Path]:
    root = Path(a.root)
    s = a.slug
    deck = Path(a.deck) if a.deck else root / "blueprint" / s / f"{s}-growth-blueprint-deck.pptx"
    if a.deck and not deck.is_absolute() and not deck.exists():
        deck = root / a.deck
    return {
        "briefing": root / "blueprint" / s / f"{s}-am-briefing.md",
        "missing": root / "kickoff" / s / f"{s}-missing-items.md",
        "content": root / "content",
        "deck": deck,
        "out": root / "emails" / s / f"{s}-week-2-email.md",
    }


def greeting(contact: str) -> str:
    parts = contact.replace(",", " ").split()
    if not parts:
        return ""
    if parts[0].rstrip(".").lower() in TITLES and len(parts) > 1:
        t = parts[0] if parts[0].endswith(".") else parts[0] + "."
        return f"Hi {t} {parts[-1]},"
    return f"Hi {parts[0]},"


def gather(a) -> dict:
    P = paths(a)
    errs = []
    for key, label in (("deck", "Growth Blueprint deck"), ("briefing", "AM Briefing"), ("missing", "missing items file")):
        if not P[key].is_file():
            errs.append(f"{label} not found: {P[key]}")
    pages = []
    if P["content"].is_dir():
        for d in sorted(x for x in P["content"].iterdir() if x.is_dir()):
            art = d / "article.md"
            if art.is_file():
                text = read(art)
                h1 = re.search(r"(?m)^#\s+(.+?)\s*$", text)
                flags = []
                for m in FLAG.finditer(text):
                    f = " ".join(m.group(1).split())
                    if f not in flags:
                        flags.append(f)
                pages.append({"folder": d.name, "label": page_label(d.name),
                              "title": h1.group(1) if h1 else "", "flags": flags, "text": text})
    if not pages:
        errs.append(f"no page content found: {P['content']}/<url-slug>/article.md")
    if errs:
        raise InputError("\n".join(errs))

    try:
        deck = deck_text(P["deck"])
    except zipfile.BadZipFile:
        raise InputError(f"deck is not a .pptx file: {P['deck']}")
    btext = read(P["briefing"])
    brief = parse_briefing(btext)
    lack = [s for s in BRIEFING_SECTIONS if s not in brief]
    if lack:
        errs.append("AM Briefing lacks sections: " + ", ".join(lack))
    elif len(brief["Key Strategic Bets"]) < 2:
        errs.append("AM Briefing has fewer than 2 Key Strategic Bets")
    mtext = read(P["missing"])
    miss = parse_missing(mtext)
    if ITEM_HEAD not in miss or PLATFORM_HEAD not in miss:
        errs.append(f"missing items file lacks the {ITEM_HEAD} or {PLATFORM_HEAD} table")
    client = brief.get("Client") or miss.get("Client")
    if not client:
        errs.append("no Client: line in the AM Briefing or the missing items file")
    if errs:
        raise InputError("\n".join(errs))

    send = parse_date(a.send_date) if a.send_date else dt.date.today()
    reply = parse_date(a.reply_by) if a.reply_by else add_business_days(send, 4)
    if reply <= send:
        raise InputError(f"reply-by {reply} is not after the send date {send}")

    asks = []
    for r in miss[ITEM_HEAD]:
        if r["Status"] in OWED_ITEM:
            name = CLIENT_WORDS.get(r["Item"], r["Item"])
            asks.append(f"- {name} ({r['Note']})" if r["Note"] else f"- {name}")
    owed_plat = [r["Platform"] for r in miss[PLATFORM_HEAD] if r["Status"] in OWED_ACCESS]
    if owed_plat:
        asks.append("- Access to: " + "; ".join(owed_plat))
    flagged = [p["label"] for p in pages if p["flags"]]
    if flagged:
        asks.append("- Details marked in the copy for these pages: " + "; ".join(flagged))

    bets = [re.split(r"\s*Wrong if\b:?", b, flags=re.I)[0].strip() for b in brief["Key Strategic Bets"]]
    deck_file = P["deck"].name
    pdf = None if a.no_pdf else (a.pdf or P["deck"].with_suffix(".pdf").name)
    return {
        "client": client, "slug": a.slug, "out_path": str(P["out"]),
        "greeting": greeting(a.contact or ""),
        "deck_file": deck_file, "pdf_file": pdf,
        "send_date": send.isoformat(), "reply_by": reply.isoformat(), "reply_by_text": long_date(reply),
        "business_days": business_days_between(send, reply),
        "bets": bets, "pages": [{k: p[k] for k in ("folder", "label", "title", "flags")} for p in pages],
        "page_count": len(pages), "asks": asks,
        "_sources": figure_sources(brief, deck, miss),
        "_copy": [p["text"] for p in pages],
    }


def figure_sources(brief: dict, deck: str, miss: dict) -> str:
    """Text the email's figures may come from: the client-safe briefing sections, the deck (without
    its slide-number footers) and the missing-items notes. No list numbers, dates or internal framing."""
    parts = [" ".join(brief.get(k, [])) for k in ("Executive Summary", "Key Strategic Bets", "Numbers the AM Should Know")]
    parts.append(re.sub(r"Growth Blueprint\s+\d+", " ", deck))
    parts += [r["Note"] for k in (ITEM_HEAD, PLATFORM_HEAD) for r in miss.get(k, [])]
    return re.sub(r"\b\d{4}-\d{2}-\d{2}\b", " ", "\n".join(parts))


def cmd_facts(a) -> int:
    try:
        f = gather(a)
    except InputError as e:
        print("INPUT MISSING OR INVALID:\n" + str(e))
        return 2
    print(json.dumps({k: v for k, v in f.items() if not k.startswith("_")}, indent=2))
    return 0


# ----------------------------------------------------------------------------- check
def words(s: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", s.lower())


def stems(s: str) -> set[str]:
    return {w[:5] for w in words(s) if w not in STOP and len(w) >= 3 and not w.isdigit()}


FIG = re.compile(r"\$?\d[\d,]*(?:\.\d+)?%?")
NUMBER_WORDS = ("four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen "
                "seventeen eighteen nineteen twenty thirty forty fifty hundred thousand dozen").split()


def figures(text: str) -> list[str]:
    """Every digit figure, plus spelled-out numbers from four up (one to three are free)."""
    out = [m.group(0).rstrip(",").replace(",", "") for m in FIG.finditer(text)]
    out += [w for w in re.findall(r"[a-z]+", text.lower()) if w in NUMBER_WORDS]
    return out


def match_bets(recs: list[str], bets: list[str]) -> tuple[bool, str]:
    bs = [stems(b) for b in bets]
    used, notes = set(), []
    for r in recs:
        rs = stems(r)
        best = max(((len(rs & b), i) for i, b in enumerate(bs) if i not in used), default=(0, -1))
        if best[0] < 3:
            return False, f"recommendation matches no unused Key Strategic Bet: {r[:70]!r}"
        used.add(best[1])
        notes.append(f"bet {best[1] + 1}")
    return True, ", ".join(notes)


def cmd_check(a) -> int:
    try:
        f = gather(a)
    except InputError as e:
        print("INPUT MISSING OR INVALID:\n" + str(e))
        return 2
    p = Path(a.email)
    if not p.is_file():
        print(f"FAIL  file  {p} not found\nRESULT: FAIL")
        return 1
    text = read(p)
    lines = text.splitlines()
    rows: list[tuple[bool, str, str]] = []
    add = lambda ok, name, detail="": rows.append((bool(ok), name, detail))

    # header
    head = {}
    for line in lines:
        m = re.match(r"^(Client|To|Send date|Reply by|Attach|Links|Subject):\s*(.*)$", line)
        if m and m.group(1) not in head:
            head[m.group(1)] = m.group(2).strip()
    want = {"Client": f["client"], "To": a.contact, "Send date": f["send_date"], "Reply by": f["reply_by"]}
    bad = [f"{k}: {head.get(k)!r} (want {v!r})" for k, v in want.items() if head.get(k) != v]
    attach = f"{f['deck_file']} (open first)" + (f"; {f['pdf_file']} (reference copy)" if f["pdf_file"] else "")
    if head.get("Attach") != attach:
        bad.append(f"Attach: {head.get('Attach')!r} (want {attach!r})")
    links_line = "; ".join(a.link) if a.link else "none"
    if head.get("Links") != links_line:
        bad.append(f"Links: {head.get('Links')!r} (want {links_line!r})")
    add(not bad, "header", "; ".join(bad))
    subj = head.get("Subject", "")
    add(subj and len(subj) <= 90, "subject", f"{len(subj)} characters" if subj else "no Subject: line")

    # body = greeting to the end
    g = f["greeting"]
    try:
        gi = next(i for i, l in enumerate(lines) if l.strip() == g)
    except StopIteration:
        gi = None
    add(gi is not None, "greeting", "" if gi is not None else f"no line {g!r}")
    body_lines = lines[gi:] if gi is not None else lines
    body = "\n".join(body_lines)
    flat = " ".join(body.split())

    asks = set(f["asks"])
    owed = [l.strip() for l in body_lines if l.strip() in asks]
    n_words = len(body.split())
    add(n_words < 250, "word count", f"{n_words} words from the greeting to the sign-off (limit: under 250)")

    tail = [l.strip() for l in body_lines if l.strip()][-2:]
    add(tail == [a.am, a.title], "sign-off", "" if tail == [a.am, a.title] else f"last lines {tail} (want {[a.am, a.title]})")

    paras = [" ".join(x.split()) for x in re.split(r"\n\s*\n", body)]
    deck_p = [x for x in paras if f["deck_file"] in x]
    add(any(re.search(r"\bfirst\b", x, re.I) for x in deck_p), "deck is primary",
        "" if deck_p else f"{f['deck_file']} not named in the body")
    if f["pdf_file"]:
        pdf_p = [x for x in paras if f["pdf_file"] in x]
        add(any(re.search(r"\breference\b", x, re.I) for x in pdf_p), "pdf is the reference",
            "" if pdf_p else f"{f['pdf_file']} not named in the body")
    focus = [w for w, pat in (("direction", r"\bdirection\b"), ("sitemap", r"\bsitemap\b"),
                               ("page content", r"\bpage (content|copy)\b")) if not re.search(pat, flat, re.I)]
    add(not focus, "focus", "missing: " + ", ".join(focus) if focus else "")
    q = [x for x in QUESTIONS if x not in flat]
    add(not q, "feedback questions", "missing: " + " ".join(q) if q else "")

    n = flat.count(f["reply_by_text"])
    prose = " ".join(l for l in body_lines if l.strip() not in asks)
    scrub = " ".join((subj + " " + prose).split()).replace(f["reply_by_text"], "")
    mon = rf"(?:{MONTHS}|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sept?|Oct|Nov|Dec)\.?"
    other = re.findall(rf"\b{mon}\s+\d{{1,2}}(?:st|nd|rd|th)?\b|\b\d{{1,2}}(?:st|nd|rd|th)?\s+(?:of\s+)?{mon}\b"
                       rf"|\b\d{{1,2}}/\d{{1,2}}\b|\b\d{{4}}-\d{{2}}-\d{{2}}\b|\b(?:{WEEKDAYS}|tomorrow|next week)\b", scrub, re.I)
    add(n == 1 and not other, "reply-by date",
        f"{f['reply_by_text']!r} appears {n} time(s)" + (f"; other dates: {other}" if other else ""))
    if not a.user_date:
        bd = f["business_days"]
        add(3 <= bd <= 5, "reply-by window", f"{bd} business days after the send date (3 to 5)")
    walk = re.search(r"\bwalk[- ]?through\b", flat, re.I)
    add(walk, "walkthrough offer", "" if walk else "no walkthrough call offered")

    recs = [l.strip()[2:] for l in body_lines if l.strip().startswith("- ") and l.strip() not in asks]
    ok, why = (False, f"{len(recs)} recommendation bullets (want 2 or 3)") if not 2 <= len(recs) <= 3 else match_bets(recs, f["bets"])
    add(ok, "recommendations", why)

    miss_asks = [x for x in f["asks"] if x not in owed]
    add(not miss_asks, "still owed", "missing lines: " + " | ".join(miss_asks) if miss_asks else f"{len(owed)} lines")

    clean = subj + "\n" + re.sub(r"https?://\S+", " ", body)
    clean = clean.replace(f["deck_file"], " ").replace(f["pdf_file"] or "\0", " ").replace(f["reply_by_text"], " ")
    src = {x.lstrip("$") for x in figures(f["_sources"])} | {str(f["page_count"])}
    unknown = sorted({x for x in figures(clean) if x.lstrip("$") not in src})
    add(not unknown, "figures", "not in the briefing, deck or missing items: " + ", ".join(unknown) if unknown else "")

    hits = sorted({m.group(0) for m in re.finditer(INTERNAL, body, re.I)})
    add(not hits, "internal language", ", ".join(hits))
    promise = sorted({m.group(0) for m in re.finditer(PROMISE, flat, re.I)})
    add(not promise, "no promises", ", ".join(promise))
    fill = [x for x in FILLER if x in flat.lower()]
    bangs = flat.count("!")
    add(not fill and bangs <= 1, "voice", "; ".join(fill + ([f"{bangs} exclamation marks"] if bangs > 1 else [])))

    bw = words(re.sub(r"https?://\S+", " ", body))
    grams = {" ".join(bw[i:i + 8]) for i in range(len(bw) - 7)}
    reused = []
    for c in f["_copy"]:
        cw = words(c)
        reused += [" ".join(cw[i:i + 8]) for i in range(len(cw) - 7) if " ".join(cw[i:i + 8]) in grams]
    add(not reused, "copy not reused", f"8-word run from the page copy: {reused[0]!r}" if reused else "")

    urls = [u.rstrip(".,;)") for u in re.findall(r"https?://\S+", body)]
    extra = sorted(set(urls) - set(a.link))
    absent = [u for u in a.link if u not in urls]
    add(not extra and not absent, "links", "; ".join(([f"not given: {extra}"] if extra else []) + ([f"not in body: {absent}"] if absent else [])))

    for ok, name, detail in rows:
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  {detail}" if detail else ""))
    res = all(ok for ok, _, _ in rows)
    print("RESULT: PASS" if res else "RESULT: FAIL")
    return 0 if res else 1


# ----------------------------------------------------------------------------- contract
def cmd_contract(a) -> int:
    if a.validate:
        data = json.loads(read(Path(a.file)))
        if "Key Strategic Bets" in data:
            need = BRIEFING_SECTIONS
        else:
            need = [ITEM_HEAD, PLATFORM_HEAD]
        lack = [k for k in need if k not in data]
        if lack:
            print("CONTRACT INVALID: missing " + ", ".join(lack))
            return 1
        print("CONTRACT OK")
        return 0
    text = read(Path(a.file))
    data = parse_briefing(text) if a.kind == "briefing" else parse_missing(text)
    print(json.dumps(data, indent=2))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(sp):
        sp.add_argument("--slug", required=True)
        sp.add_argument("--root", default=".")
        sp.add_argument("--send-date")
        sp.add_argument("--reply-by")
        sp.add_argument("--deck")
        g = sp.add_mutually_exclusive_group()
        g.add_argument("--pdf")
        g.add_argument("--no-pdf", action="store_true")

    f = sub.add_parser("facts")
    common(f)
    f.add_argument("--contact", default="")
    c = sub.add_parser("check")
    c.add_argument("email")
    common(c)
    c.add_argument("--contact", required=True)
    c.add_argument("--am", required=True)
    c.add_argument("--title", default=TITLE)
    c.add_argument("--link", action="append", default=[])
    c.add_argument("--user-date", action="store_true")
    k = sub.add_parser("contract")
    k.add_argument("kind", nargs="?", choices=["briefing", "missing"])
    k.add_argument("file")
    k.add_argument("--validate", action="store_true")
    a = ap.parse_args()
    if a.cmd == "contract" and not a.validate and not a.kind:
        ap.error("contract needs briefing or missing, or --validate")
    return {"facts": cmd_facts, "check": cmd_check, "contract": cmd_contract}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
