#!/usr/bin/env python3
"""Pre-publish QA pass for an article written by the seo-content-writer skill.

Usage:
  python3 check_draft.py ARTICLE.md [--brief BRIEF.md] [--keyword "target keyword"]
                         [--out QA_REPORT.md]
                         [--page-type homepage|about|contact|location]
                         [--client-dir DIR] [--facts FILE ...]

Reads `article.md` (its `| Field | Value |` metadata table at the top, then the
page), runs the mechanical checks from references/qa-checklist.md, prints a
`| Check | Result | Detail |` table and writes it, with a VERDICT line, to
`qa/<url-slug>/qa_report.md` for `content/<url-slug>/article.md` (else beside
the article). The report is a working file, not part of the page folder.

VERDICT: FIX          one or more checks FAILed; fix the draft and rerun
VERDICT: NEEDS_INPUT  no FAILs, but the draft carries [NEEDS SOURCE: ...] or
                      [NEEDS INPUT: ...] flags a human must resolve
VERDICT: READY        no FAILs and no open flags

Client page modes (--page-type homepage, about, contact or location, or a brief
whose page type or format names one of them, `page_url: /` for a homepage,
`/about/` or `/contact/` for those pages): no byline check, the per-section
statistic and keyword repetition are WARNs, and the page must carry its `<!-- section: ... -->` markers
in order (PAGE_SECTIONS), a Final CTA with a route, and no client fact (phone,
email, address, hours, quoted testimonial, rating, review count, founding year,
credential word) that the brief, --client-dir files or --facts files do not
state. Homepage, About and Location pages also need proof or a flag in their
proof section; a Contact page needs its form fields listed and its phone, email,
address and hours given or flagged.

Exit code 1 on FIX, else 0. Standard library only.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

UTILITY_H2 = {
    "key takeaways", "frequently asked questions", "faq", "faqs", "sources",
    "references", "about the author", "sources and references",
}
PRONOUN_START = re.compile(
    r"^(it|its|it's|this|that|these|those|they|their|such|the former|the latter|he|she)\b",
    re.I,
)
LEAD_IN = re.compile(
    r"^(in this (section|article|post|guide)|let's|let us|when it comes to|have you ever|"
    r"before we|it's important to|it is important to|as we (all )?know|in today's|"
    r"if you're wondering|you might be wondering|we'll|we will|read on|keep reading|"
    r"so,|well,|great question)",
    re.I,
)
UNATTRIBUTED = re.compile(
    r"\b(studies (show|suggest|have shown)|research (shows|suggests|has shown)|experts (say|agree|recommend)|"
    r"many people (believe|think|say)|it is (widely )?(said|believed|known)|according to experts|"
    r"some (say|experts))\b",
    re.I,
)
VAGUE = re.compile(
    r"\b(significantly|dramatically|a lot|much (faster|cheaper|better|longer|more)|"
    r"countless|numerous studies)\b",
    re.I,
)
DECISION_Q = re.compile(r"^(is|are|does|do|can|should|will|would|could|has|have)\b", re.I)
VERDICT_WORD = re.compile(r"^(yes|no|not|usually|rarely|always|never|generally|in most|repair|replace|keep|switch|choose|neither|either|most|many|some|few|all|sometimes|partly)\b", re.I)
FIGURE = re.compile(r"\d\s?%|\$\s?\d|\d\.\d|\b\d+\s?(ppm|percent)\b", re.I)
ATTRIBUTION = re.compile(
    r"according to|\(|\breports?\b|\breported\b|\brecords?\b|\bpricing\b|\bprice list\b|\bsays?\b|\bsaid\b|\bdata\b|"
    r"\bsurvey\b|\bstudy\b|\bwarranty\b|\bper\b|\bfound\b|\bshows?\b|\bpublishe[sd]\b|\binterview\b|\bestimates?\b",
    re.I,
)
BAD_ANCHOR = re.compile(
    r"\[(click here|here|learn more|read more|this page|this article|this link|more)\]\(", re.I
)
PLACEHOLDER = re.compile(r"\b(TODO|TBD|FIXME|lorem ipsum|XX%|\$XX)\b|\[insert", re.I)
# open gaps: the writer's own flags, and the numbered client-input slots a content brief carries
FLAG = re.compile(r"\[(?:NEEDS (?:SOURCE|INPUT)|CLIENT INPUT NEEDED #\d+):[^\]]*\]")
BYLINE_BAD = re.compile(r"\b(admin|staff writer|editorial team|our team|guest author)\b", re.I)
LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
NUMBER = re.compile(r"(?<![\w.])\$?\d[\d,]*(?:\.\d+)?%?")
STOP = {"a", "an", "the", "of", "to", "for", "in", "on", "and", "or", "is", "do", "does", "how", "what", "why", "can", "i",
        # question words: "how long" / "how much" / "how often" are carried by the H1, not repeated in prose
        "long", "much", "often", "many", "when", "where", "which", "who", "should", "are", "will", "my", "it", "if",
        "with", "be", "need", "there", "than", "your", "you", "get", "at", "by", "from", "that", "this"}
HOMEPAGE_SECTIONS = ["Hero", "Why Us", "Services Overview", "Proof", "About Snapshot",
                     "Service Area", "Process", "Final CTA"]
# client pages: section markers in order, the label used in the report, and the section that must carry proof
PAGE_SECTIONS = {
    "homepage": HOMEPAGE_SECTIONS,
    "about": ["Hero", "Company Story", "Mission and Values", "Team", "Credentials", "Final CTA"],
    "contact": ["Hero", "Contact Form", "Phone and Email", "Address and Hours", "Map", "Final CTA"],
    "location": ["Hero", "How We Serve", "Local Services", "Local Proof", "Directions", "Final CTA"],
}
PAGE_LABEL = {"homepage": "Homepage", "about": "About page", "contact": "Contact page", "location": "Location page"}
PROOF_SECTION = {"homepage": "Proof", "about": "Credentials", "location": "Local Proof"}
EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")
MARKER = re.compile(r"(?im)^\s*<!--\s*section:\s*([^>]+?)\s*-->\s*$")
PHONE = re.compile(r"\(?\b\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}\b")
HOURS = re.compile(r"(?i)\b\d{1,2}(?::\d{2})?\s?(?:a\.?m\.?|p\.?m\.?)(?![a-z])|"
                   r"\b(?:mon|tue|tues|wed|thu|thur|thurs|fri|sat|sun)(?:day)?s?\s?(?:-|–|to|through)\s?"
                   r"(?:mon|tue|tues|wed|thu|thur|thurs|fri|sat|sun)(?:day)?\b")
STREET = re.compile(r"\b\d{2,6}\s+(?:[NSEW]\.?\s+)?(?:[A-Z0-9][\w.'-]*\s+){1,4}?"
                    r"(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Court|Ct|"
                    r"Parkway|Pkwy|Place|Pl|Highway|Hwy|Circle|Cir|Trail|Suite|Ste)\b\.?")
QUOTE = re.compile(r"[\"“]([^\"”\n]{20,})[\"”]")
# credential and proof words: each one on the page must also appear in the brief or client files
CREDENTIAL = re.compile(
    r"(?i)\b(licensed|licen[cs]e (?:no\.?|number|#)|certified|certification|accredited|accreditation|insured|bonded|"
    r"award[- ]winning|awards?|top[- ]rated|best[- ]rated|five[- ]star|5[- ]star|\d(?:\.\d)?[- ]star|stars?\b|★|"
    r"\d+\+? (?:google |online |verified )?review(?:s|ers?)|\d(?:\.\d)?\s*(?:out of 5|/\s?5)|rated \d(?:\.\d)?|"
    r"bbb|better business bureau|a\+ rating|board member|"
    r"enrolled agent|proadvisor|chamber of commerce|years of experience|family[- ]owned|veteran[- ]owned|"
    r"woman[- ]owned|locally owned|guarantee[ds]?|warrant(?:y|ies)|since (?:19|20)\d\d|founded in (?:19|20)\d\d)")


# sections that say what must NOT be said, or what is still missing or to be checked, never vouch for a fact:
# a compliance file's Prohibited Claims, a voice file's Banned Words, and a content brief's Client Inputs
# Needed, Concerns, Format Requirements, Writer QA Checklist and Research Log
NOT_FACTS = re.compile(r"(?i)prohibit|banned|never|avoid|do not|don't|not allowed|unapproved|"
                       r"client inputs? needed|concerns?|format requirements|qa checklist|research log")


def fact_text(text: str) -> str:
    """Text that states client facts: open slots and flags removed, and NOT_FACTS sections dropped."""
    out, skip, level = [], False, 0
    for line in text.splitlines():
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            if skip and len(m.group(1)) > level:
                continue
            skip, level = bool(NOT_FACTS.search(m.group(2))), len(m.group(1))
        if not skip:
            out.append(line)
    return FLAG.sub(" ", "\n".join(out))


def norm_text(s: str) -> str:
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"').replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", re.sub(r"[^\w$%+★'\- ]+", " ", s.lower())).strip()


def page_type_of(brief: str, given: str | None) -> str:
    """homepage, about, contact or location (a client page with a section map), else "" (an article)."""
    if given:
        return given.lower() if given.lower() in PAGE_SECTIONS else ""
    m = re.search(r"(?im)^\W*(?:page[ _]type|format)\W*\s*:\s*\**\s*(home\s?page|about|contact|location)\b", brief)
    if m:
        return {"homepage": "homepage", "home page": "homepage"}.get(m.group(1).lower(), m.group(1).lower())
    m = re.search(r"(?im)^\W*(?:url|page_url)\W*\s*:\s*\**\s*(/[^\s*]*)\s*$", brief)
    url = m.group(1).strip("/").lower() if m else None
    if url == "":
        return "homepage"
    return {"about": "about", "about-us": "about", "contact": "contact", "contact-us": "contact"}.get(url or "", "")


def homepage_checks(md: str, sections: list, facts: str, add, page_type: str = "homepage") -> None:
    """The client-page rules from references/homepage.md and references/client-pages.md that a script can check."""
    order = PAGE_SECTIONS[page_type]
    label = PAGE_LABEL[page_type]
    found = [m.group(1).strip() for m in MARKER.finditer(md)]
    want = [x.lower() for x in order]
    core = [f for f in found if f.lower() in want]
    missing = [x for x in order if x.lower() not in [c.lower() for c in core]]
    dupes = sorted({c for c in core if [x.lower() for x in core].count(c.lower()) > 1})
    in_order = [c.lower() for c in core] == [w for w in want if w in [c.lower() for c in core]]
    detail = "; ".join(filter(None, [
        f"missing: {', '.join(missing)}" if missing else "",
        f"repeated: {', '.join(dupes)}" if dupes else "",
        "" if in_order else "out of order: " + " > ".join(core)]))
    add(f"{label} sections in order", not missing and not dupes and in_order, detail)

    # the page text by section marker, flags removed (a flag is the right way to name a missing fact)
    by_sec: dict[str, str] = {}
    cur = ""
    for line in md.splitlines():
        m = MARKER.match(line)
        if m:
            cur = m.group(1).strip().lower()
            continue
        if re.match(r"(?i)^##\s+(sources|references|sources and references)\s*$", line.strip()):
            cur = "sources"
        by_sec[cur] = by_sec.get(cur, "") + line + "\n"
    page = "\n".join(t for k, t in by_sec.items() if k != "sources")
    page_noflag = FLAG.sub(" ", page)

    nfacts = norm_text(facts)
    fact_digits = re.sub(r"\D", "", facts)
    untraced = []
    for m in PHONE.finditer(page_noflag):
        if re.sub(r"\D", "", m.group(0)) not in fact_digits:
            untraced.append(f"phone {m.group(0)}")
    for m in EMAIL.finditer(page_noflag):
        if m.group(0).lower() not in facts.lower():
            untraced.append(f"email {m.group(0)}")
    for rx, label in ((HOURS, "hours"), (STREET, "address")):
        for m in rx.finditer(page_noflag):
            if norm_text(m.group(0)) not in nfacts:
                untraced.append(f"{label} '{m.group(0)}'")
    for m in QUOTE.finditer(page_noflag):
        q = norm_text(m.group(1))
        if len(q.split()) >= 5 and q not in nfacts:
            untraced.append(f"quote '{m.group(1)[:50]}'")
    # blockquotes, joined across lines: the quoted words (or the whole quote when unmarked) must be in a file
    for bq in re.findall(r"(?m)(?:^\s*>.*\n?)+", page_noflag):
        text = " ".join(l.strip().lstrip(">").strip() for l in bq.splitlines())
        qm = re.search(r"[\"“](.+?)[\"”]", text)
        q = norm_text(qm.group(1) if qm else re.split(r"\s[-—–]\s", text)[0])
        if len(q.split()) >= 5 and q not in nfacts:
            untraced.append(f"blockquote '{text[:50]}'")
    fact_nums = set(re.findall(r"\d+(?:\.\d+)?", facts))
    for m in CREDENTIAL.finditer(page_noflag):
        w = m.group(0)
        nums = re.findall(r"\d+(?:\.\d+)?", w)
        if nums and re.search(r"(?i)star|review|rat|out of|/", w):
            # a rating or review count: the number must sit next to star/rating/review in a file
            ok = all(re.search(rf"(?is)(?<![\d.]){re.escape(n)}(?![\d.]).{{0,40}}(star|rating|review)|"
                               rf"(star|rating|review).{{0,40}}(?<![\d.]){re.escape(n)}(?![\d.])", facts) for n in nums)
        elif nums:  # "since 2015": the year must be in a file
            ok = all(n in fact_nums for n in nums)
        else:     # a word: its stem must be in a file ("licensed" is backed by "License #...")
            key = norm_text(w)
            ok = (key if " " in key or len(key) <= 6 else key[:6]) in nfacts
        if not ok:
            untraced.append(f"'{w}'")
    untraced = list(dict.fromkeys(untraced))
    add("Client facts trace to the brief or client files", not untraced,
        "not in any file (delete or flag): " + "; ".join(untraced[:10]) if untraced else "")

    if page_type in PROOF_SECTION:
        name = PROOF_SECTION[page_type]
        proof = by_sec.get(name.lower(), "")
        add(f"{name} section carries proof or a flag",
            bool(re.search(r"\d|[\"“]|^\s*>", proof, re.M) or FLAG.search(proof)),
            "" if proof.strip() else f"no {name} section")
    if page_type == "contact":
        form = by_sec.get("contact form", "")
        n_fields = len(re.findall(r"(?m)^\s*(?:[-*+]|\d+[.)])\s+\S", form))
        add("Contact form lists its fields", n_fields >= 3, f"{n_fields} fields listed (list each field as a bullet)")
        pe, ah = by_sec.get("phone and email", ""), by_sec.get("address and hours", "")
        gaps = [what for what, ok in (
            ("phone", PHONE.search(pe) or re.search(r"(?i)\[[^\]]*phone", pe)),
            ("email", EMAIL.search(pe) or re.search(r"(?i)\[[^\]]*e-?mail", pe)),
            ("address", STREET.search(ah) or re.search(r"(?i)\[[^\]]*address|\bno (?:public |walk-in )?(?:office|storefront|street address)", ah)),
            ("hours", HOURS.search(ah) or re.search(r"(?i)\[[^\]]*hours", ah))) if not ok]
        add("Contact details given or flagged", not gaps, "missing, give or flag: " + ", ".join(gaps) if gaps else "")
    cta = by_sec.get("final cta", "")
    has_route = bool(LINK.search(cta) or PHONE.search(cta) or FLAG.search(cta))
    add("Final CTA gives a route", has_route, "" if has_route else "no link, phone or flag in the Final CTA section")


META_FIELDS = ["Meta title", "Meta description", "H1", "URL slug", "Primary question",
               "Target keyword", "Key takeaways", "Article summary"]


def sentences(text: str) -> list[str]:
    t = re.sub(r"\b(U\.S|e\.g|i\.e|etc|vs|Dr|Mr|Ms|Mrs|St|No|approx)\.", lambda m: m.group(0).replace(".", "§"), text)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"“(\[*])", t.strip())
    return [p.replace("§", ".") for p in parts if p.strip()]


def strip_md(s: str) -> str:
    s = LINK.sub(r"\1", s)
    s = re.sub(r"[*_`]", "", s)
    return s.strip()


def split_meta(md: str) -> tuple[str, str]:
    """The `| Field | Value |` metadata table at the top of article.md, and the article below it."""
    m = re.match(r"﻿?\s*((?:\|[^\n]*(?:\n|\Z))+)", md)
    return (m.group(1), md[m.end():]) if m else ("", md)


def parse(md: str):
    """Return (h1 list, sections). A section = dict(level, title, blocks, line)."""
    lines = md.splitlines()
    h1s, sections = [], []
    cur = {"level": 1, "title": "", "blocks": [], "line": 1}
    para: list[str] = []

    def flush():
        if para:
            cur["blocks"].append(("p", " ".join(x.strip() for x in para)))
            para.clear()

    for i, raw in enumerate(lines, 1):
        line = raw.rstrip()
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            flush()
            lvl, title = len(m.group(1)), strip_md(m.group(2))
            if lvl == 1:
                h1s.append(title)
                cur = {"level": 1, "title": title, "blocks": [], "line": i}
                sections.append(cur)
            else:
                cur = {"level": lvl, "title": title, "blocks": [], "line": i}
                sections.append(cur)
            continue
        s = line.strip()
        if not s:
            flush()
        elif s.startswith("|"):
            flush()
            if not re.match(r"^\|[\s:|-]+\|$", s):
                cur["blocks"].append(("row", s))
        elif re.match(r"^([-*+]|\d+[.)])\s+", s):
            flush()
            cur["blocks"].append(("li", re.sub(r"^([-*+]|\d+[.)])\s+", "", s)))
        elif s.startswith(">"):
            flush()
            cur["blocks"].append(("quote", s.lstrip("> ")))
        else:
            para.append(s)
    flush()
    return h1s, sections


MONTHS = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?"


def undated(text: str) -> str:
    """Remove URLs and dates (ISO and written) so their digits are not read as figures."""
    text = re.sub(r"https?://\S+|\b[\w.-]+\.(?:gov|com|org|net|us|edu)/\S*", " ", text)
    text = re.sub(r"\b\d{4}-\d{2}(?:-\d{2})?\b", " ", text)
    return re.sub(rf"(?i)\b{MONTHS}\s+\d{{1,2}},?\s+\d{{4}}\b|\b\d{{1,2}}\s+{MONTHS}\s+\d{{4}}\b", " ", text)


def heading_coverage(title: str, words: list[str]) -> float:
    """Share of the heading's content terms found (by stem prefix) in `words`."""
    terms = [t for t in dict.fromkeys(re.findall(r"[a-z0-9]+", title.lower())) if t not in STOP and len(t) > 2]
    if not terms:
        return 1.0
    def found(t: str) -> bool:
        return any(w == t or (len(t) > 3 and len(w) > 3 and (w.startswith(t[:-1]) or t.startswith(w))) for w in words)
    return sum(1 for t in terms if found(t)) / len(terms)


def is_question(title: str) -> bool:
    return title.rstrip().endswith("?")


def is_numbered(title: str) -> bool:
    return bool(re.match(r"^(step\s+\d+|\d+[.):]?)\s", title, re.I))


def brief_link_targets(brief: str) -> list[str]:
    """Paths the page must link to. A content-brief brief lists them under '### Links from this page'
    (its '### Links to this page' rows are for other pages, not this one); other briefs under any
    heading that contains 'internal link'."""
    sec = re.search(r"(?ims)^#+\s*links from this page[^\n]*\n(.*?)(?=^#|\Z)", brief) \
        or re.search(r"(?ims)^#+[^\n]*internal link[^\n]*\n(.*?)(?=^#|\Z)", brief)
    text = sec.group(1) if sec else ""
    if re.search(r"(?m)^\|", text):  # table: the URL is the first cell of each row
        text = "\n".join(l.strip().strip("|").split("|")[0] for l in text.splitlines() if l.strip().startswith("|"))
    # URL path characters (& in "/case-study/a-&-b", %, _, ., ~, +); a sentence's closing . or , is not part of it
    paths = re.findall(r"(?<![\w.])(/[a-z0-9][\w\-/&%.~+]*)", text, re.I)
    return list(dict.fromkeys(p.rstrip(".,") for p in paths))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("article", nargs="?")
    ap.add_argument("--brief")
    ap.add_argument("--keyword")
    ap.add_argument("--out")
    ap.add_argument("--page-type", choices=sorted(PAGE_SECTIONS),
                    help="switches on that client page's checks (else read from the brief)")
    ap.add_argument("--client-dir", help="client reference folder; its .md files count as client facts (client pages)")
    ap.add_argument("--facts", action="append", default=[], help="another client file that states facts (client pages)")
    ap.add_argument("--brief-only", action="store_true",
                    help="only read the brief and print what the checks will use (keyword, client, link targets)")
    a = ap.parse_args()

    brief = Path(a.brief).read_text(encoding="utf-8") if a.brief and Path(a.brief).is_file() else ""

    keyword = a.keyword
    if not keyword and brief:
        m = re.search(r"(?im)^(?:-\s*)?(?:primary(?:[ _]keyword)?|keyword|target keyword)\s*:\s*(.+)$", brief)
        if m:
            keyword = m.group(1).strip()

    if a.brief_only:
        cm = re.search(r"(?im)^\**client\**\s*:\s*\**([^(\n*]+)", brief)
        links = brief_link_targets(brief)
        print(f"keyword: {keyword or 'NOT FOUND'}\nclient: {cm.group(1).strip() if cm else 'NOT FOUND'}\n"
              f"internal links: {', '.join(links) or 'NOT FOUND'}")
        return 0 if keyword and links else 1

    if not a.article:
        ap.error("ARTICLE is required unless --brief-only is given")
    art = Path(a.article)
    if not art.is_file():
        print(f"article not found: {art}", file=sys.stderr)
        return 2
    meta, md = split_meta(art.read_text(encoding="utf-8"))
    if not keyword and meta:
        m = re.search(r"(?im)^\|\s*Target keyword\s*\|\s*(.+?)\s*\|", meta)
        if m:
            keyword = m.group(1).strip()

    page_type = page_type_of(brief, a.page_type)
    homepage = bool(page_type)  # any client page (homepage, about, contact, location) follows the client-page rules
    facts = brief
    if homepage:
        facts = fact_text(brief)
        fact_files = [Path(f) for f in a.facts]
        if a.client_dir and Path(a.client_dir).is_dir():
            fact_files += sorted(Path(a.client_dir).rglob("*.md"))
        facts += "\n" + "\n".join(fact_text(f.read_text(encoding="utf-8")) for f in fact_files if f.is_file())
        md_full = md
        md = MARKER.sub("", md)

    rows: list[tuple[str, str, str]] = []

    def add(check: str, ok: bool, detail: str, warn: bool = False):
        rows.append((check, "PASS" if ok else ("WARN" if warn else "FAIL"), detail if not ok or detail else ""))

    h1s, sections = parse(md)
    body_words = len(re.findall(r"\b\w+\b", strip_md(md)))

    # 1. exactly one H1
    add("One H1", len(h1s) == 1, f"found {len(h1s)}")
    h1 = h1s[0] if h1s else ""

    # 2. byline (articles only; a homepage has none)
    after = md.split(f"# {h1}", 1)[-1] if h1 else md
    head = [l.strip() for l in after.splitlines() if l.strip()][:4]
    by = next((l for l in head if re.match(r"^\**by\b", l, re.I)), "")
    if homepage:
        add(f"No article byline on {'a homepage' if page_type == 'homepage' else 'an ' + PAGE_LABEL[page_type] if page_type == 'about' else 'a ' + PAGE_LABEL[page_type]}", not by,
            f"remove the byline: {strip_md(by)[:60]}" if by else "")
    elif not by:
        add("Named author byline", False, "no line starting 'By ' under the H1")
    elif BYLINE_BAD.search(by):
        add("Named author byline", False, f"generic byline: {strip_md(by)[:80]}")
    else:
        add("Named author byline", True, strip_md(by)[:90])

    # 3. keyword placement (title + early body); natural use, so WARN only
    if keyword:
        toks = [t for t in re.findall(r"[a-z0-9]+", keyword.lower()) if t not in STOP]
        h1toks = set(re.findall(r"[a-z0-9]+", h1.lower()))
        has = lambda t, words: any(w == t or (len(t) > 3 and w.startswith(t)) for w in words)
        miss = [t for t in toks if not has(t, h1toks)]
        add("Keyword terms in H1", not miss, f"missing from H1: {', '.join(miss)}" if miss else "", warn=True)
        after_h1 = md.split(h1, 1)[-1] if h1 else md
        first100 = set(re.findall(r"[a-z0-9]+", strip_md(after_h1).lower())[:100])
        early = all(has(t, first100) for t in toks)
        add("Keyword terms in first 100 words", early, "" if early else "move the target phrase into the opening answer", warn=True)
        reps = len(re.findall(re.escape(keyword.lower()), md.lower()))
        limit = 3 + body_words // 600
        # on a client page the keyword is often the client's name, which the one-name rule repeats on purpose
        add("No mechanical keyword repetition", reps <= limit,
            f"exact phrase used {reps} times (limit {limit})" if reps > limit else f"{reps} exact uses", warn=homepage)
    else:
        add("Target keyword known", False, "pass --keyword or include 'Keyword:' in the brief", warn=True)

    # 4. headings phrased as questions
    content = [s for s in sections if s["level"] >= 2]
    bad_h = []
    parent_h2 = ""
    for s in content:
        t = s["title"]
        if s["level"] == 2:
            parent_h2 = t.lower()
            if t.lower() not in UTILITY_H2 and not is_question(t):
                bad_h.append(f"H2 '{t}'")
        elif s["level"] == 3 and not (is_question(t) or is_numbered(t)) and parent_h2 not in UTILITY_H2 - {"frequently asked questions", "faq", "faqs"}:
            bad_h.append(f"H3 '{t}'")
    add("H2/H3 phrased as questions", not bad_h, "; ".join(bad_h[:6]))

    qcount = sum(1 for s in content if is_question(s["title"]))
    add("5+ sub-questions under own headings", qcount >= 5, f"{qcount} question headings")

    # 5. first sentence under each heading answers directly
    weak = []
    for s in [x for x in sections if x["level"] >= 2 and x["title"].lower() not in UTILITY_H2]:
        first = next((b for b in s["blocks"] if b[0] in ("p", "li")), None)
        if not first:
            continue
        fs = strip_md(sentences(first[1])[0]) if sentences(first[1]) else ""
        if PRONOUN_START.match(fs) or LEAD_IN.match(fs) or len(fs.split()) < 5:
            weak.append(f"'{s['title'][:40]}': {fs[:60]}")
    add("First sentence is a direct answer", not weak, "; ".join(weak[:5]))

    # 5a. the first sentence names the heading's subject; a WARN, since echoing the heading word for word reads stiff
    unnamed = []
    for s in [x for x in sections if x["level"] >= 2 and is_question(x["title"])]:
        first = next((b for b in s["blocks"] if b[0] in ("p", "li")), None)
        if not first or not sentences(first[1]):
            continue
        fs_words = re.findall(r"[a-z0-9]+", strip_md(sentences(first[1])[0]).lower())
        cov = heading_coverage(s["title"], fs_words)
        if cov < 0.5:
            unnamed.append(f"'{s['title'][:45]}' ({cov:.0%} of heading terms)")
    add("First sentence restates the heading's subject", not unnamed, "; ".join(unnamed[:6]), warn=True)

    # 5b. decision questions open with a verdict word
    # Yes/no questions (auxiliary verb first, no "or") FAIL without a verdict word;
    # choice questions ("X or Y", "should I ...") only WARN, since naming the option is a verdict too.
    nov, nov_choice = [], []
    for s in [x for x in sections if x["level"] >= 2 and DECISION_Q.match(x["title"])]:
        first = next((b for b in s["blocks"] if b[0] in ("p", "li")), None)
        if not first:
            continue
        opener = strip_md(first[1])
        lead = re.findall(r"[a-z0-9]+", opener.lower())[:15]
        if not VERDICT_WORD.match(opener) or heading_coverage(s["title"], lead) < 0.5:
            item = f"'{s['title'][:45]}': {opener[:60]}"
            (nov_choice if re.search(r"\bor\b", s["title"], re.I) else nov).append(item)
    add("Yes/no questions open with a verdict and the subject", not nov, "; ".join(nov[:5]))
    add("Choice questions open with the choice", not nov_choice, "; ".join(nov_choice[:5]), warn=True)

    # 7. paragraph length 2-4 sentences
    long_p = []
    for s in sections:
        for kind, text in s["blocks"]:
            if kind == "p" and len(sentences(text)) > 4:
                long_p.append(f"'{s['title'][:30]}' ({len(sentences(text))} sentences)")
    add("Paragraphs at most 4 sentences", not long_p, "; ".join(long_p[:5]), warn=True)

    # 8. unattributed claims and vague intensifiers
    un = sorted({m.group(0) for m in UNATTRIBUTED.finditer(md)})
    add("No unattributed claims", not un, ", ".join(un))
    vg = sorted({m.group(0) for m in VAGUE.finditer(md)})
    add("No vague intensifiers", not vg, ", ".join(vg), warn=True)

    # 9. a number (or an evidence flag) in every question H2 section
    h2_text: dict[str, str] = {}
    cur_h2 = None
    for s in sections:
        if s["level"] == 2:
            cur_h2 = s["title"]
            h2_text[cur_h2] = ""
        if cur_h2 and s["level"] >= 2:
            h2_text[cur_h2] += " " + " ".join(t for _, t in s["blocks"])
    nostat = [t for t, txt in h2_text.items()
              if t.lower() not in UTILITY_H2 and not re.search(r"\d", txt) and not FLAG.search(txt)]
    # a content brief that found no verifiable statistic for a section says so ("- Evidence: none verifiable")
    # and tells the writer to explain without a number; those sections are a WARN, not a FAIL
    exempt_titles = [m.group(1) for m in re.finditer(r"(?m)^### H2: ([^\n]+?)\s*\n((?:(?!### )[^\n]*\n)*)", brief)
                     if re.search(r"(?m)^- Evidence:[^\n]*none verifiable", m.group(2))] if brief else []
    exempt = [t for t in nostat if any(heading_coverage(e, re.findall(r"[a-z0-9]+", t.lower())) >= 0.8
                                       for e in exempt_titles)]
    nostat = [t for t in nostat if t not in exempt]
    add("A statistic or evidence flag per major section", not nostat, "; ".join(f"'{t[:40]}'" for t in nostat[:6]),
        warn=homepage)
    if exempt:
        add("Sections the brief marks 'none verifiable' carry no number", False,
            "explained without a figure, as the brief says: " + "; ".join(f"'{t[:40]}'" for t in exempt[:4]), warn=True)

    # 10. sources section when the page states figures
    has_figures = bool(re.search(r"\d\s?%|\$\d|\bppm\b", md))
    has_sources = bool(re.search(r"(?im)^##\s+(sources|references|sources and references)\s*$", md))
    add("Sources section for stated figures", has_sources or not has_figures,
        "" if has_sources or not has_figures else "figures stated but no '## Sources' section")

    # 10b. every sentence, bullet or table row that states a figure names where it comes from,
    # so the passage still carries its source when quoted alone (repeats in Key Takeaways included)
    # the client's own name counts as attribution for its records and prices ("Harbor & Pine replaced 412 ...")
    cm = re.search(r"(?im)^\**client\**\s*:\s*\**([^(\n*]+)", brief + "\n" + meta)
    client = re.sub(r"\s+(plumbing|inc\.?|llc|ltd|co\.?|corp\.?|community credit union|credit union)$", "",
                    cm.group(1).strip(), flags=re.I) if cm else ""
    # figures the brief's evidence supplies ("10 to 15 years", "41 gallons") need a source in their sentence
    # too, even without a %, $ or decimal; years and evidence ids do not count
    ev_sec = re.search(r"(?ims)^#+\s*evidence[^\n]*\n(.*?)(?=^#|\Z)", brief) if brief else None
    ev_figs = {n.replace(",", "") for n in re.findall(r"(?<![\w.#E])\d[\d,]*(?:\.\d+)?", undated(ev_sec.group(1) if ev_sec else ""))
               if len(n.replace(",", "")) >= 2 and not re.fullmatch(r"(19|20)\d\d", n)}
    unattributed = []
    in_sources = False
    for s in sections:
        if s["level"] == 2:
            in_sources = s["title"].lower() in {"sources", "references", "sources and references"}
        if in_sources:
            continue
        for kind, text in s["blocks"]:
            units = [text] if kind == "row" else sentences(text)
            for u in units:
                plain = strip_md(FLAG.sub("", u))
                if re.match(r"^\**by\b", plain, re.I):  # the byline: credentials and date, not claims
                    continue
                nums = {n.replace(",", "") for n in re.findall(r"(?<![\w.])\$?(\d[\d,]*(?:\.\d+)?)", undated(plain))}
                if (FIGURE.search(plain) or nums & ev_figs) and not ATTRIBUTION.search(plain) \
                        and not (client and client.lower() in plain.lower()):
                    unattributed.append(plain[:70])
    add("Every figure names its source in the same sentence", not unattributed, "; ".join(unattributed[:5]))

    # 11. numbers not found in the brief or the Sources list (possible fabrication).
    # Figures with %, $ or a decimal FAIL; bare integers only WARN (step counts, derived values).
    if brief:
        src_m = re.search(r"(?ims)^##\s+(?:sources|references|sources and references)\s*$(.*?)(?=^##\s|\Z)", md)
        sources_txt = src_m.group(1) if src_m else ""
        norm = lambda n: n.replace(",", "").lstrip("$").rstrip("%")
        # a homepage's numbers must come from the brief or client files; its own Sources list does not vouch
        known = {norm(n) for n in NUMBER.findall(facts + ("" if homepage else "\n" + sources_txt))}
        body = md.replace(sources_txt, "") if sources_txt else md
        body = "\n".join(l for l in body.splitlines() if not re.match(r"^\**by\b", l.strip(), re.I))  # byline/date
        body = re.sub(r"(?m)^\s*\d+[.)]\s", "", body)                 # list markers
        body = re.sub(r"(?im)^#{1,6}\s+(step\s+)?\d+[.):]?\s", "", body)  # numbered headings
        body = re.sub(r"\]\([^)]*\)", "]", body)                     # link targets
        body = FLAG.sub("", body)
        unknown = sorted({n for n in NUMBER.findall(body) if norm(n) not in known}, key=str)
        hard = [n for n in unknown if "%" in n or "$" in n or "." in n]
        soft = [n for n in unknown if n not in hard]
        add("Figures (%, $, decimals) trace to the brief or Sources", not hard,
            "not in brief or Sources: " + ", ".join(hard[:15]) if hard else "")
        add("Other numbers trace to the brief or Sources", not soft,
            "confirm each (step count, date, derived or cited): " + ", ".join(soft[:15]) if soft else "", warn=True)

    # 12. links and anchors
    bad_anchor = BAD_ANCHOR.findall(md)
    add("Descriptive anchor text", not bad_anchor, ", ".join(sorted(set(b.lower() for b in bad_anchor))))
    if brief:
        targets = brief_link_targets(brief)
        hrefs = {h.rstrip("/") for _, h in LINK.findall(md)}
        missing = [t for t in dict.fromkeys(targets) if t.rstrip("/") not in hrefs
                   and not any(h.endswith(t.rstrip("/")) for h in hrefs)]
        add("Every internal link from the brief is placed", not missing, ", ".join(missing))

    # 13. a table when the brief asks for one (a content brief's own Evidence and naming tables don't count:
    # only its Format Requirements section says what the page needs)
    fr = re.search(r"(?ims)^## Format Requirements\s*$(.*?)(?=^## |\Z)", brief) if brief else None
    if brief and re.search(r"(?i)\btable\b", fr.group(1) if fr else brief):
        add("Comparison table present", bool(re.search(r"(?m)^\|.*\|\s*$", md)), "brief asks for a table")

    # 14. FAQ answers are full statements
    short = []
    in_faq = False
    for s in sections:
        if s["level"] == 2:
            in_faq = s["title"].lower() in {"frequently asked questions", "faq", "faqs"}
        elif in_faq and s["level"] == 3:
            ans = " ".join(t for k, t in s["blocks"] if k in ("p", "li"))
            if len(ans.split()) < 15 or re.match(r"^(yes|no)[.!]?$", strip_md(ans), re.I):
                short.append(s["title"][:40])
    add("FAQ answers are complete statements", not short, "; ".join(short))

    # 15. placeholders
    ph = sorted({m.group(0) for m in PLACEHOLDER.finditer(md)})
    add("No placeholder text", not ph, ", ".join(ph))

    # 16. metadata table
    if meta:
        cells = dict((k.strip(), v.strip()) for k, v in re.findall(r"(?m)^\|\s*([^|]+?)\s*\|\s*(.*?)\s*\|\s*$", meta))
        missing = [f for f in META_FIELDS if not cells.get(f)]
        add("Metadata table complete", not missing, "missing: " + ", ".join(missing) if missing else "")
        kt = cells.get("Key takeaways", "")
        n_kt = len([x for x in re.split(r"<br\s*/?>|;\s*-|\n", kt) if x.strip(" -•")])
        add("3-7 key takeaways", 3 <= n_kt <= 7, f"{n_kt} takeaways")
        n_sum = len(sentences(cells.get("Article summary", "")))
        add("Article summary is 3-4 sentences", 3 <= n_sum <= 4, f"{n_sum} sentences")
        mt = cells.get("Meta title", "").lower()
        h1t = {t for t in re.findall(r"[a-z0-9]+", h1.lower()) if t not in STOP}
        overlap = len([t for t in h1t if t in mt]) / max(1, len(h1t))
        add("Meta title built from the H1", overlap >= 0.6, f"{overlap:.0%} of H1 terms in meta title", warn=True)
        # the recipe is the H1 wording, optionally followed by the brand; words beyond those are an added
        # topic list or slogan (no character limit applies, but the title must keep the H1's single intent)
        brand = {w for w in re.findall(r"[a-z0-9]+", (client or "").lower()) if len(w) > 2} | {"plumbing", "inc", "llc"}
        cm2 = re.search(r"(?im)^\**client\**\s*:\s*\**([^(\n*|]+)", brief + "\n" + meta)
        if cm2:
            brand |= {w for w in re.findall(r"[a-z0-9]+", cm2.group(1).lower()) if len(w) > 2}
        h1w = set(re.findall(r"[a-z0-9]+", h1.lower()))
        extra = [w for w in re.findall(r"[a-z0-9]+", mt) if w not in h1w and w not in brand and w not in STOP]
        add("Meta title is the H1 plus at most the brand", len(extra) <= 3,
            f"added words: {' '.join(extra[:10])}")
    else:
        add("Metadata table complete", False, "no `| Field | Value |` table at the top of the article")

    # 16b. client page sections and the client-fact rule
    if homepage:
        homepage_checks(md_full, sections, facts, add, page_type)

    # 17. open evidence / input flags
    flags = FLAG.findall(md) + FLAG.findall(meta)
    flag_text = [m.group(0) for m in FLAG.finditer(md + "\n" + meta)]
    add("Open [NEEDS ...] flags", not flags, f"{len(flags)} open: " + "; ".join(x[:70] for x in flag_text[:6]), warn=True)

    fails = [r for r in rows if r[1] == "FAIL"]
    verdict = "FIX" if fails else ("NEEDS_INPUT" if flags else "READY")
    out = [f"VERDICT: {verdict}", "",
           f"Article: `{art.name}` ({body_words} words). Failed: {len(fails)}. "
           f"Warnings: {sum(1 for r in rows if r[1] == 'WARN')}. Open flags: {len(flags)}.", "",
           "| Check | Result | Detail |", "| --- | --- | --- |"]
    for c, r, d in rows:
        out.append(f"| {c} | {r} | {d.replace('|', '/')} |")
    text = "\n".join(out) + "\n"
    print(text)
    # the report is a working file, not a deliverable: content/<url-slug>/article.md reports to qa/<url-slug>/
    page = art.resolve().parent
    default = (page.parent.parent / "qa" / page.name if page.parent.name.lower() == "content" else page) / "qa_report.md"
    dest = Path(a.out) if a.out else default
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8")
    print(f"wrote {dest}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
