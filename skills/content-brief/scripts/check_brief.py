#!/usr/bin/env python3
"""Structural gate for a content brief written to references/brief-template.md.

Usage:
  python3 check_brief.py BRIEF.md [--client-dir DIR] [--facts FILE ...]
  python3 check_brief.py BRIEF.md --front-matter-json     print the front-matter as JSON, nothing else

Checks: front-matter fields and values, format values, required sections and
their order (YMYL and refresh moves included), question headings in the
Outline, 5-8 sub-question sections, 8-15 entities, evidence rows with ids,
URLs, dates and labels, evidence ids used by the Outline, banned
instructions (invented-example wording, schema markup, character counts, tool
or skill names), client-input slot accounting, link tables, and status
consistency with the concerns.

Homepage briefs (`format: homepage`) also need `page_url: /`, the Outline's
`- Section:` lines in the homepage order (Why Us, Services Overview, Proof,
About Snapshot, Service Area, Process, then the CTA as Final CTA), proof or a
slot in Proof, phone, address and hours (or slots) in Final CTA, and every
client fact in the brief (phone, address, hours, quoted testimonial, rating,
review count, founding year, credential word) found in a client file passed
with --client-dir or --facts. A writer takes the brief's facts as true, so an
untraced one would reach the page. Prints a `| Check | Result | Detail |` table and
`GATE: PASS` or `GATE: FAIL`. Exit code 1 on FAIL. Standard library only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from parse_targets import EMBEDDED, PRIMARY, value  # noqa: E402

FM_KEYS = ["id", "brief_version", "status", "date", "client", "client_domain", "market", "language",
           "page_url", "mode", "existing_url", "primary_keyword", "secondary_keywords", "intent", "funnel",
           "format", "format_embedded", "format_source", "metrics", "geo_candidate", "geo_answer_format",
           "cluster", "pillar_url", "ymyl", "local", "cannibalization", "voice_source", "style_source",
           "word_range", "client_inputs_open", "source_report"]
SECTIONS = ["Page Goal", "Reader and Search Intent", "Answer Target", "Outline", "Entities and Naming", "Evidence",
            "Author, Experience and Trust", "Internal Links", "Voice and Style", "Format Requirements",
            "Title and Meta Direction", "Client Inputs Needed", "Concerns", "Writer QA Checklist", "Research Log"]
LABELS = {"Measured", "User-provided", "Calculated", "Estimated"}
SOURCE_RE = re.compile(r"^(client|default/(home-services|financial-services|legal|b2b-saas|generated))$")
CANNIBAL = {"clear", "clear (unverified)", "clear (no site)", "risk"}
SLOT = re.compile(r"\[CLIENT INPUT NEEDED #(\d+):[^\]]+\]")
# references to a slot that are not the full bracket form ("slot #3", "input #3", "[#3]")
SHORTHAND = re.compile(r"(?i)\bslot\s*#?\s*\d+\b|\binput\s*#\s*\d+|\[#\d+\]")
# instruction phrasing only; the Evidence table (verbatim source text), the embedded Voice and Style
# directives and the Research Log are not scanned
BANNED = re.compile(
    r"(?i)illustrative example|hypothetical example|typical industry (figure|range|number)s?|"
    r"(use|assume|cite) (an |the )?industry average|round numbers|json-?ld|schema markup|"
    r"\b\d+\s*characters?\b|seo-content-writer|content-brief|keyword-research skill|\bClaude\b|"
    r"\b(writing|drafting|content|SEO) (skill|agent|bot)\b|\bAI (writer|drafting tool)\b"
)
UNSCANNED = {"Research Log", "Evidence", "Voice and Style"}
HOME_SECTIONS = ["Why Us", "Services Overview", "Proof", "About Snapshot", "Service Area", "Process"]
PHONE = re.compile(r"\(?\b\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}\b")
STREET = re.compile(r"\b\d{2,6}\s+(?:[A-Z0-9][\w.'-]*\s+){1,4}?(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|"
                    r"Drive|Dr|Lane|Ln|Way|Court|Ct|Parkway|Pkwy|Place|Pl|Highway|Hwy|Suite|Ste)\b")
DAY = r"(?:mon|tue|tues|wed|thu|thur|thurs|fri|sat|sun)(?:day)?s?"
HOURS = re.compile(r"(?i)\b\d{1,2}(?::\d{2})?\s?[ap]\.?m\b\.?|\b" + DAY + r"\s?(?:-|–|to|through)\s?" + DAY + r"\b")
QUOTED = re.compile(r"[\"“]([^\"”\n]{25,})[\"”]")
# proof and credential claims; each must also be in a client file
CLAIM = re.compile(
    r"(?i)\b(licensed|licen[cs]e (?:no\.?|number|#)\s*[a-z]*-?\d[\w-]*|(?:ccb|lic)\s*#?\s*[a-z]*-?\d[\w-]*|insured|bonded|certified|"
    r"certifications?|accredited|accreditation|award[- ]winning|awards?|top[- ]rated|best[- ]rated|five[- ]star|"
    r"\d(?:\.\d)?[- ]stars?|stars?\b|★|rated \d(?:\.\d)?|\d(?:\.\d)?\s*(?:out of 5|/\s?5)|"
    r"\d+\+? (?:google |online |verified )?reviews?|bbb|better business bureau|a\+ rating|enrolled agent|proadvisor|"
    r"board[- ]certified|member of|chamber of commerce|family[- ]owned|veteran[- ]owned|woman[- ]owned|"
    r"locally owned|guarantee[ds]?|warrant(?:y|ies)|since (?:19|20)\d\d|founded in (?:19|20)\d\d|"
    r"(?:\d+\+?|\w+) years (?:of experience|in business)|years of experience)")
# a number in a rating or review claim must sit next to star/rating/review in a client file
RATING_WORD = re.compile(r"(?i)star|review|rat|out of|/|★")
# headings and lines that say what must NOT be claimed are not facts
NOT_A_FACT = re.compile(r"(?i)\bnot yet\b|do not|don't|never|not available|prohibit|banned|avoid|pending|unapproved")
# homepage sections that may go without a statistic
NO_STAT_SECTIONS = {"services overview", "service area", "process", "final cta"}
GENERIC_ANCHOR = re.compile(r"^(click here|here|learn more|read more|more|this page|this article|link)$", re.I)


def split_front_matter(text: str) -> tuple[dict, str, str | None]:
    t = text.replace("\r\n", "\n")
    m = re.match(r"\A---\n(.*?)\n---\n(.*)\Z", t, re.S)
    if not m:
        return {}, t, "no front-matter block between --- lines at the top"
    fm = {}
    for line in m.group(1).split("\n"):
        mm = re.match(r"^([A-Za-z_]+)\s*:\s*(.*)$", line)
        if mm:
            fm[mm.group(1)] = value(mm.group(2))
    return fm, m.group(2), None


def sections(body: str) -> list[tuple[str, str]]:
    out, cur, buf = [], None, []
    for line in body.split("\n"):
        m = re.match(r"^## (.+?)\s*$", line)
        if m:
            if cur is not None:
                out.append((cur, "\n".join(buf)))
            cur, buf = m.group(1), []
        elif cur is not None:
            buf.append(line)
    if cur is not None:
        out.append((cur, "\n".join(buf)))
    return out


def table_rows(text: str) -> list[list[str]]:
    rows = []
    for line in text.split("\n"):
        s = line.strip()
        if s.startswith("|") and not re.match(r"^\|[\s:|-]+\|$", s):
            rows.append([c.strip() for c in s.strip("|").split("|")])
    return rows[1:] if rows else []  # drop header


def bullets(text: str) -> list[str]:
    return [re.sub(r"^\s*(?:[-*]|\d+[.)])\s+", "", l).strip() for l in text.split("\n")
            if re.match(r"^\s*(?:[-*]|\d+[.)])\s+", l)]


def flat(s: str) -> str:
    s = s.replace("’", "'").replace("“", '"').replace("”", '"').replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", re.sub(r"[^\w$%+'\- ]+", " ", s.lower())).strip()


def stated(text: str) -> str:
    """The lines of a client file or brief that state facts: lines, and headed parts, that say what must
    not be published (a 'Not yet available' list, prohibited claims) are dropped, and so are slots."""
    out, skip, level = [], False, 0
    for line in text.split("\n"):
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            if not (skip and len(m.group(1)) > level):
                skip, level = bool(NOT_A_FACT.search(m.group(2))), len(m.group(1))
            continue
        if not skip and not NOT_A_FACT.search(line):
            out.append(line)
    return SLOT.sub(" ", "\n".join(out))


def is_pipeline_file(f: Path) -> bool:
    """A content brief or a keyword-research report is not a client file, wherever it sits."""
    try:
        t = f.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    return bool(re.search(r"(?m)^# Content Brief:|^targets:\s*$", t))


def untraced_facts(text: str, facts: str, quotes: str = "") -> list[str]:
    """Client facts stated in `text` that the client files (`facts`, already passed through stated()) lack."""
    nf = flat(facts)
    phones = {re.sub(r"\D", "", m.group(0)) for m in PHONE.finditer(facts)}
    bad = []
    for m in PHONE.finditer(text):
        if re.sub(r"\D", "", m.group(0)) not in phones:
            bad.append(f"phone {m.group(0)}")
    for rx, label in ((STREET, "address"), (HOURS, "hours")):
        for m in rx.finditer(text):
            if flat(m.group(0)) not in nf:
                bad.append(f"{label} '{m.group(0)}'")
    for m in QUOTED.finditer(quotes):
        if flat(m.group(1)) not in nf:
            bad.append(f"quote '{m.group(1)[:40]}'")
    for m in CLAIM.finditer(text):
        w = m.group(0)
        n = re.findall(r"\d+(?:\.\d+)?", w)
        if n and RATING_WORD.search(w):  # "4.9 stars", "30 Google reviews": number beside the word in a file
            ok = all(re.search(rf"(?is)(?<![\d.]){re.escape(x)}(?![\d.]).{{0,40}}(star|rating|review)|"
                               rf"(star|rating|review).{{0,40}}(?<![\d.]){re.escape(x)}(?![\d.])", facts) for x in n)
        elif n and re.search(r"(?i)since|founded", w):  # the year beside since/founded/started/in a file
            ok = all(re.search(rf"(?i)(since|founded|started|opened|established|in)\b[^.\n]{{0,40}}\b{x}\b", facts) for x in n)
        elif n:  # a license number or "12 years in business": the whole claim must be in a file
            ok = flat(w) in nf
        else:  # a word: the whole word must be in a file ("member of" needs "member of", not "member")
            ok = re.search(rf"\b{re.escape(flat(w))}", nf) is not None
        if not ok:
            bad.append(f"'{w}'")
    return list(dict.fromkeys(bad))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("brief")
    ap.add_argument("--front-matter-json", action="store_true")
    ap.add_argument("--client-dir", help="client file folder; its .md files are where a homepage brief's client facts come from")
    ap.add_argument("--facts", action="append", default=[], help="another client file a homepage brief took facts from")
    a = ap.parse_args()
    p = Path(a.brief)
    if not p.is_file():
        print(f"brief not found: {p}", file=sys.stderr)
        return 2
    text = p.read_text(encoding="utf-8")
    fm, body, fm_err = split_front_matter(text)
    if a.front_matter_json:
        if fm_err:
            print(fm_err, file=sys.stderr)
            return 1
        sys.stdout.write(json.dumps(fm, indent=2, ensure_ascii=False) + "\n")
        return 0

    rows: list[tuple[str, str, str]] = []

    def add(check: str, ok: bool, detail: str = "", warn: bool = False):
        rows.append((check, "PASS" if ok else ("WARN" if warn else "FAIL"), "" if ok else detail))

    # --- front-matter
    add("Front-matter block present", not fm_err, fm_err or "")
    missing = [k for k in FM_KEYS if k not in fm]
    add("Front-matter fields present", not missing, "missing: " + ", ".join(missing))
    g = fm.get
    bad = []
    if g("status") not in ("DONE", "DONE_WITH_CONCERNS"):
        bad.append(f"status {g('status')!r} (a NEEDS_INPUT or BLOCKED row has no brief file)")
    if g("mode") not in ("new", "refresh"):
        bad.append(f"mode {g('mode')!r}")
    if g("intent") not in ("Informational", "Navigational", "Commercial", "Transactional"):
        bad.append(f"intent {g('intent')!r}")
    if g("funnel") not in ("TOFU", "MOFU", "BOFU"):
        bad.append(f"funnel {g('funnel')!r}")
    if g("cannibalization") not in CANNIBAL:
        bad.append(f"cannibalization {g('cannibalization')!r}")
    for k in ("voice_source", "style_source"):
        if not SOURCE_RE.match(str(g(k, ""))):
            bad.append(f"{k} {g(k)!r}")
    for k in ("ymyl", "local", "geo_candidate"):
        if not isinstance(g(k), bool):
            bad.append(f"{k} is not true/false")
    if not isinstance(g("brief_version"), int) or g("brief_version", 0) < 1:
        bad.append("brief_version is not a positive integer")
    if not re.fullmatch(r"\d{3,4}-\d{3,4}", str(g("word_range", ""))):
        bad.append(f"word_range {g('word_range')!r}")
    m = g("metrics")
    if not (isinstance(m, dict) and m.get("source") in LABELS | {"N/A"}):
        bad.append("metrics is not {volume, kd, source} with a source label")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(g("date", ""))):
        bad.append(f"date {g('date')!r}")
    add("Front-matter values valid", not bad, "; ".join(bad))
    emb = g("format_embedded", [])
    fmt_ok = g("format") in PRIMARY and isinstance(emb, list) and all(e in EMBEDDED for e in emb)
    add("Format values in the enum", fmt_ok, f"format {g('format')!r}, embedded {emb!r}")

    # --- title and sections
    h1 = re.search(r"(?m)^# Content Brief: (.+)$", body)
    add("Title is '# Content Brief: <question>?'", bool(h1) and h1.group(1).strip().endswith("?"),
        h1.group(1) if h1 else "no '# Content Brief:' line")
    secs = sections(body)
    names = [n for n, _ in secs]
    want = [s for s in SECTIONS]
    if g("mode") == "refresh":
        want.insert(want.index("Page Goal") + 1, "Refresh Audit")
    if g("ymyl") is True:
        want.remove("Author, Experience and Trust")
        want.insert(0, "Author, Experience and Trust")
    add("Required sections in order", names == want,
        f"got {names}; want {want}")
    S = dict(secs)

    # --- outline
    outline = S.get("Outline", "")
    blocks = re.split(r"(?m)^(?=### )", outline)
    h2 = [(re.match(r"^### (H2(?: \(CTA\))?): (.+?)\s*$", b, re.M), b) for b in blocks if b.startswith("### ")]
    bad_h, no_first, no_ev, ev_ids, none_ver = [], [], [], set(), False
    subq = 0
    cta = 0
    home = g("format") == "homepage"
    labels, home_blocks = [], {}
    for mm, b in h2:
        if not mm:
            bad_h.append(b.split("\n")[0][:60])
            continue
        kind, title = mm.group(1), mm.group(2)
        faq = title.lower() == "frequently asked questions"
        sec = re.search(r"(?m)^- Section:\s*(.+?)\s*$", b)
        if sec:
            labels.append(sec.group(1))
            home_blocks[sec.group(1).lower()] = b
        if kind == "H2 (CTA)":
            cta += 1
        elif not faq:
            subq += 1
        if not faq and not title.endswith("?"):
            bad_h.append(title[:60])
        for h3 in re.findall(r"(?m)^#### H3: (.+?)\s*$", b):
            if not (h3.endswith("?") or re.match(r"^(step\s+\d+|\d+[.):])", h3, re.I)):
                bad_h.append(h3[:60])
        if faq:
            if not re.search(r"(?m)^- Questions:", b):
                no_first.append("FAQ has no '- Questions:' line")
            continue
        fs = re.search(r"(?m)^- First sentence must state:\s*(.*)$", b)
        if not fs or not fs.group(1).strip():
            no_first.append(title[:50])
        elif kind != "H2 (CTA)" and len(SLOT.sub("", fs.group(1)).split()) < 6:
            # a slot may support the opening fact but cannot be the whole instruction
            no_first.append(f"{title[:40]} (first sentence is only a client-input slot)")
        ev = re.search(r"(?m)^- Evidence:\s*(.+)$", b)
        if not ev:
            no_ev.append(title[:50])
        else:
            ids = re.findall(r"\bE\d+\b", ev.group(1))
            ev_ids.update(ids)
            if "none verifiable" in ev.group(1).lower():
                none_ver = True
            elif home and "none needed" in ev.group(1).lower():
                lab = re.search(r"(?m)^- Section:\s*(.+?)\s*$", b)
                if not (lab and lab.group(1).lower() in NO_STAT_SECTIONS):
                    no_ev.append(f"{title[:40]} ('none needed' only for {', '.join(sorted(NO_STAT_SECTIONS))})")
            elif not ids and kind != "H2 (CTA)":
                no_ev.append(title[:50])
    add("Outline headings are questions", not bad_h, "; ".join(bad_h[:5]))
    add("5-8 sub-question sections plus one CTA", 5 <= subq <= 8 and cta == 1, f"{subq} sub-question sections, {cta} CTA")
    add("Every section says what its first sentence must state", not no_first, "; ".join(no_first[:5]))
    add("Every section lists evidence ids or 'none verifiable'", not no_ev, "; ".join(no_ev[:5]))

    # --- homepage: the writer's section map, proof and contact route
    if home:
        add("Homepage page_url is /", str(g("page_url", "")).strip() == "/", f"page_url {g('page_url')!r}")
        want_l = HOME_SECTIONS + (["FAQ"] if "faq" in [x.lower() for x in labels] else []) + ["Final CTA"]
        add("Homepage sections in order", [x.lower() for x in labels] == [x.lower() for x in want_l],
            f"'- Section:' lines {labels}; want {want_l}")
        cta_b = next((b for mm, b in h2 if mm and mm.group(1) == "H2 (CTA)"), "")
        add("Homepage CTA is the Final CTA", bool(re.search(r"(?m)^- Section:\s*Final CTA\s*$", cta_b)),
            "the '### H2 (CTA):' block needs '- Section: Final CTA'")
        proof = home_blocks.get("proof", "")
        add("Proof section has evidence or a slot", bool(re.search(r"\bE\d+\b", proof) or SLOT.search(proof)),
            "cite the client's proof (E-ids) or slot what is missing")
        fin = home_blocks.get("final cta", "")
        slots = " ".join(x.group(0) for x in SLOT.finditer(fin)).lower()
        gaps = [w for w, rx, words in (("phone", PHONE, ("phone", "call")), ("address", STREET, ("address",)),
                                       ("hours", HOURS, ("hours",)))
                if not rx.search(SLOT.sub(" ", fin)) and not any(x in slots for x in words)
                and not re.search(rf"(?i)\bno (?:public |street )*{w}\b", fin)]
        add("Final CTA covers phone, address and hours", not gaps,
            "give each from a client file, or a slot, or say there is none ('no public street address'): " + ", ".join(gaps))

    # --- entities
    ents = [r for r in table_rows(S.get("Entities and Naming", "")) if r and r[0]]
    add("8-15 entities in the naming table", 8 <= len(ents) <= 15, f"{len(ents)} rows")

    # --- evidence
    ev_rows = [r for r in table_rows(S.get("Evidence", "")) if r and r[0]]
    ev_bad, ev_defined = [], set()
    for r in ev_rows:
        if len(r) < 7:
            ev_bad.append(f"{r[0]}: {len(r)} cells, need 7")
            continue
        rid, fig, src, url, date, label = r[0], r[1], r[2], r[3], r[4], r[5]
        ev_defined.add(rid)
        if not re.fullmatch(r"E\d+", rid):
            ev_bad.append(f"id {rid!r}")
        if not (re.match(r"https?://\S+", url) or re.match(r"file:\s*\S+", url)):
            ev_bad.append(f"{rid}: URL {url!r}")
        if not re.fullmatch(r"\d{4}(-\d{2}(-\d{2})?)?|undated \(accessed \d{4}-\d{2}-\d{2}\)", date):
            ev_bad.append(f"{rid}: date {date!r}")
        if label not in LABELS:
            ev_bad.append(f"{rid}: label {label!r}")
        if not fig or not src:
            ev_bad.append(f"{rid}: empty figure or source")
    add("Evidence rows have id, URL, date and label", not ev_bad, "; ".join(ev_bad[:6]))
    undefined = sorted(ev_ids - ev_defined)
    add("Outline evidence ids exist in the Evidence table", not undefined, ", ".join(undefined))
    unused = sorted(ev_defined - ev_ids - set(re.findall(r"\bE\d+\b", S.get("Answer Target", ""))))
    add("Every evidence row supports a section", not unused, ", ".join(unused), warn=True)

    # --- banned instructions (the Research Log may name tools)
    scan = "\n".join(t for n, t in secs if n not in UNSCANNED) + "\n" + (h1.group(0) if h1 else "")
    hits = sorted({x.group(0) for x in BANNED.finditer(scan)})
    add("No banned instructions or tool names", not hits, ", ".join(hits))

    # --- slots
    slot_nums = [int(n) for n in SLOT.findall(body)]
    listed = [b for b in bullets(S.get("Client Inputs Needed", "")) if b.lower() not in ("none.", "none")]
    list_nums = [int(n) for n in re.findall(r"(?m)^\s*(\d+)[.)]\s+", S.get("Client Inputs Needed", ""))]
    uniq = sorted(set(slot_nums))
    slot_bad = []
    if uniq != list(range(1, len(uniq) + 1)):
        slot_bad.append(f"slot numbers {uniq} are not 1..N without gaps")
    if sorted(list_nums) != uniq:
        slot_bad.append(f"list items {sorted(list_nums)} do not match slots {uniq}")
    if g("client_inputs_open") != len(uniq):
        slot_bad.append(f"client_inputs_open is {g('client_inputs_open')}, {len(uniq)} slots")
    short = [x.group(0) for x in SHORTHAND.finditer(SLOT.sub("", body))]
    if short:
        slot_bad.append("shorthand slot references: " + ", ".join(sorted(set(short))[:4]))
    add("Client-input slots match the numbered list", not slot_bad, "; ".join(slot_bad))

    # --- links
    links = S.get("Internal Links", "")
    out_part = re.search(r"(?ms)^### Links from this page\s*\n(.*?)(?=^### |\Z)", links)
    in_part = re.search(r"(?ms)^### Links to this page\s*\n(.*?)(?=^### |\Z)", links)
    out_rows = table_rows(out_part.group(1)) if out_part else []
    link_bad = []
    if not out_part or not in_part:
        link_bad.append("needs '### Links from this page' and '### Links to this page'")
    for r in out_rows:
        if len(r) < 4:
            link_bad.append(f"row {r} has fewer than 4 cells")
            continue
        if "CLIENT INPUT" in r[0] or not r[0].startswith("/"):  # root-relative paths only
            link_bad.append(f"URL cell {r[0]!r}")
        if GENERIC_ANCHOR.match(r[1]):
            link_bad.append(f"generic anchor {r[1]!r}")
        if r[3].lower() not in ("live", "planned"):
            link_bad.append(f"status {r[3]!r}")
    pu, page = str(g("pillar_url", "N/A")), str(g("page_url", ""))
    if pu not in ("N/A", "") and pu.rstrip("/") != page.rstrip("/"):
        if not any(r and r[0].rstrip("/") == pu.rstrip("/") for r in out_rows):
            link_bad.append(f"pillar {pu} not linked from this page")
    add("Internal link tables complete", out_rows and not link_bad, "; ".join(link_bad[:5]) or "no outbound links")

    # --- a client voice or style source names where the file is, so the writer can open it
    vs = S.get("Voice and Style", "")
    path_bad = [f for f, k in (("voice.md", "voice_source"), ("style.md", "style_source"))
                if g(k) == "client" and not re.search(r"[\w-]+/" + re.escape(f), vs)]
    add("Client voice and style files are named with their path", not path_bad,
        "name the folder, for example project/" + ", project/".join(path_bad))

    # --- author and YMYL
    auth = S.get("Author, Experience and Trust", "")
    add("Author section names an author or a slot", bool(re.search(r"(?m)^- Author:\s*\S", auth)), "no '- Author:' line")
    if g("ymyl") is True:
        add("YMYL brief names a reviewer or a slot", bool(re.search(r"(?m)^- Reviewer:\s*\S", auth)), "no '- Reviewer:' line")

    # --- homepage: client facts trace to client files
    if home:
        files = [Path(f) for f in a.facts]
        bad_dir = a.client_dir and not Path(a.client_dir).is_dir()
        if a.client_dir and not bad_dir:
            # the brief and the keyword report are not client files, even when they sit in the folder
            files += [f for f in sorted(Path(a.client_dir).rglob("*.md"))
                      if f.resolve() != p.resolve() and "research" not in f.resolve().relative_to(
                          Path(a.client_dir).resolve()).parts and not is_pipeline_file(f)]
        missing_f = [str(f) for f in files if not f.is_file()] + ([f"--client-dir {a.client_dir}"] if bad_dir else [])
        facts = "\n".join(stated(f.read_text(encoding="utf-8")) for f in files if f.is_file())
        # a web Evidence row vouches for a client fact only when it is the client's own site
        dom = str(g("client_domain", "")).lower().removeprefix("www.")
        if dom and dom != "n/a":
            facts += "\n" + "\n".join(r[1] for r in ev_rows if len(r) >= 4 and re.match(
                rf"https?://(?:www\.)?{re.escape(dom)}(?:/|$)", r[3], re.I))
        # every section a writer reads, slots removed; the instruction-only parts are left out
        # Voice and Style holds directives ("don't promise guaranteed results"): its don't-lines are not facts
        scan = SLOT.sub(" ", "\n".join(
            "\n".join(l for l in t.split("\n") if not NOT_A_FACT.search(l)) if n == "Voice and Style" else t
            for n, t in secs if n not in {"Research Log", "Writer QA Checklist"}))
        bad_f = untraced_facts(scan, facts, scan)
        add("Homepage client facts trace to client files", not bad_f and not missing_f,
            ("not found: " + ", ".join(missing_f) + "; " if missing_f else "")
            + ("in no client file (slot it or pass the file with --facts): " + "; ".join(bad_f[:8]) if bad_f else ""))

    # --- status consistency
    concerns = [c for c in bullets(S.get("Concerns", "")) if c.lower().rstrip(".") != "none"]
    ctext = " ".join(concerns).lower()
    need = []
    if str(g("voice_source", "")).startswith("default") or str(g("style_source", "")).startswith("default"):
        need.append(("default", "a default voice or style was applied"))
    if uniq:
        need.append(("client input", "there are client-input slots"))
    if g("format_source") and re.search(r"\+|,|/|\band\b", str(g("format_source"))):
        need.append(("normaliz", "the format was normalized from a combo"))
    if g("cannibalization") in ("risk", "clear (unverified)"):
        need.append(("cannibalization", f"cannibalization is {g('cannibalization')}"))
    if none_ver:
        need.append(("verifiable", "a section has no verifiable statistic"))
    missing_c = [why for key, why in need if key not in ctext]
    add("Concerns cover every status trigger", not missing_c, "add a concern because " + "; ".join(missing_c))
    st = g("status")
    if st == "DONE":
        add("Status DONE has no concerns, slots or defaults", not need and not concerns,
            "use DONE_WITH_CONCERNS: " + "; ".join(why for _, why in need) if need else "concerns listed")
    elif st == "DONE_WITH_CONCERNS":
        add("Status DONE_WITH_CONCERNS lists concerns", bool(concerns), "no concerns listed")

    # --- QA checklist and research log
    add("Writer QA Checklist has checkbox items",
        len(re.findall(r"(?m)^- \[ \] ", S.get("Writer QA Checklist", ""))) >= 8, "fewer than 8 '- [ ]' items")
    add("Research Log lists tools available", bool(re.search(r"(?im)^- Tools available:\s*\S", S.get("Research Log", ""))),
        "no '- Tools available:' line")

    fails = [r for r in rows if r[1] == "FAIL"]
    print(f"GATE: {'FAIL' if fails else 'PASS'}\n")
    print(f"Brief: `{p.name}`, status {g('status')}, {len(uniq)} client input slot(s), "
          f"{len(concerns)} concern(s). Failed: {len(fails)}. Warnings: {sum(1 for r in rows if r[1] == 'WARN')}.\n")
    print("| Check | Result | Detail |\n| --- | --- | --- |")
    for c, r, d in rows:
        print(f"| {c} | {r} | {d.replace('|', '/')} |")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
