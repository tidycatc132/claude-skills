#!/usr/bin/env python3
"""Page-type design briefs: find the page types, scaffold the brief, check it.

Usage (run from the client's working folder; paths are relative to it):
  python3 ptdb.py scan --slug SLUG [--root .] [--kit DIR] [--type URL_SLUG=TYPE ...] [--json]
  python3 ptdb.py scaffold --slug SLUG --client NAME [--date YYYY-MM-DD] [same options as scan]
  python3 ptdb.py check BRIEF --slug SLUG [same options as scan]
  python3 ptdb.py known FIXTURE.json      (contract: section markers -> page type)
  python3 ptdb.py choice FIXTURE.json     (contract: feedback table -> chosen homepage option)
  python3 ptdb.py brief-format FIXTURE.json  (contract: content-brief front matter -> page type)

scan      lists every page in content/<url-slug>/article.md with its page type (service, location,
          about, contact, resource; the homepage is listed and left out), word count, H2 count,
          sections and open flags; the homepage design brief and its brand cues; the kit files; and
          the homepage option the client chose in feedback/<slug>/. Exit 1 when a page's type is
          unknown (pass --type url-slug=type).
scaffold  writes design/<slug>/<slug>-page-type-design-briefs.md with every computed part filled
          in and `<fill>` wherever the model writes. Refuses to overwrite a brief without --force.
check     verifies the brief against the files. Exit 1 on any FAIL.

Standard library only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

TYPES = ["service", "location", "about", "contact", "resource"]
HEADINGS = {
    "service": "Service Pages",
    "location": "Location Pages",
    "about": "About Page",
    "contact": "Contact Page",
    "resource": "Resource Pages",
}
SUBSECTIONS = [
    "Pages",
    "Content Map",
    "Repeating Blocks",
    "Content Length",
    "CTAs",
    "Brand Reference",
    "Responsive Priorities",
    "Homepage Relationship",
    "Consistent and Variable",
]
MAP_HEADER = "| # | Section | Purpose | Appears on | Content source |"
MARKER = re.compile(r"<!--\s*section:\s*(.+?)\s*-->")
FLAG = re.compile(r"\[(?:NEEDS INPUT|NEEDS SOURCE|CLIENT INPUT NEEDED #\d+):[^\]]*\]")
HEX = re.compile(r"#[0-9A-Fa-f]{6}\b|#[0-9A-Fa-f]{3}\b")
OLD_VERSION = re.compile(r"\.v\d+\.md$")
FILL = "<fill>"
NOT_CHOSEN = "direction not chosen yet"

# Markers seo-content-writer writes, and the page type each one identifies.
MARKER_TYPES = {
    "Company Story": "about",
    "Mission and Values": "about",
    "Team": "about",
    "Credentials": "about",
    "Contact Form": "contact",
    "Phone and Email": "contact",
    "Address and Hours": "contact",
    "Map": "contact",
    "How We Serve": "location",
    "Local Services": "location",
    "Local Proof": "location",
    "Directions": "location",
    "Why Us": "homepage",
    "Services Overview": "homepage",
    "Proof": "homepage",
    "About Snapshot": "homepage",
    "Service Area": "homepage",
    "Process": "homepage",
}
SHARED_MARKERS = {"Hero", "FAQ", "Final CTA"}

BRIEF_FORMATS = {
    "service-page": "service",
    "product-page": "service",
    "location-page": "location",
    "about-page": "about",
    "about": "about",
    "contact-page": "contact",
    "contact": "contact",
    "homepage": "homepage",
}
# content-brief's article formats: a page written from one of these is a resource page.
ARTICLE_FORMATS = {"explainer", "how-to", "comparison", "listicle", "definition", "cost-guide", "buyers-guide",
                   "troubleshooting", "checklist", "faq-page", "pillar-guide"}
URL_TYPES = [
    (re.compile(r"^/?about(-us)?/?$"), "about"),
    (re.compile(r"^/?contact(-us)?/?$"), "contact"),
    (re.compile(r"(^|/)(services?)/"), "service"),
    (re.compile(r"(^|/)(locations?|areas?|service-areas?|areas-we-serve)/"), "location"),
    (re.compile(r"(^|/)(blog|resources?|guides?|articles?|news|learn|insights)/"), "resource"),
]

# Words that prescribe visual design. The brief describes content structure and brand constraints.
VISUAL = [
    (re.compile(r"\b\d+(?:\.\d+)?\s?(?:px|pt|rem|em|vh|vw)\b", re.I), "a size in px/pt/rem/em"),
    (re.compile(r"\b(?:font-size|font-weight|line-height|letter-spacing|border-radius|box-shadow)\b", re.I), "a CSS property"),
    (re.compile(r"\brounded corners?\b|\bdrop shadows?\b|\bgradients?\b|\bparallax\b", re.I), "a visual effect"),
    (re.compile(r"\bcarousels?\b|\bsliders?\b|\baccordions?\b|\bhamburger\b|\banimat(?:e|ed|es|ion|ions)\b|\bhover\b", re.I), "a UI pattern"),
    (re.compile(r"\bfull[- ](?:width|bleed)\b|\b(?:one|two|three|four|1|2|3|4)[- ]columns?\b|\bgrid layout\b|\bcard grid\b|\bsticky\b", re.I), "a layout instruction"),
    (re.compile(r"\bbold\b|\bitalics?\b|\bunderlined?\b|\buppercase\b|\ball caps\b", re.I), "a type treatment"),
    (re.compile(r"\blayout idea\b", re.I), "a layout idea"),
]
TAG = re.compile(r"\[(kit: [\w.-]+|homepage brief|feedback|article|user)\]")


# ---------------------------------------------------------------- reading the working folder

def read(p: Path) -> str:
    return p.read_text(encoding="utf-8") if p.exists() else ""


def field(text: str, *names: str) -> str:
    for name in names:
        m = re.search(rf"(?im)^\W*{name}\W*\s*:\s*\**\s*(.+?)\s*\**\s*$", text)
        if m:
            return m.group(1).strip().strip("\"'")
    return ""


def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def brief_index(root: Path) -> dict[str, str]:
    """url-slug -> format, from research/content-briefs/ (content-brief's files)."""
    out: dict[str, str] = {}
    folder = root / "research" / "content-briefs"
    if not folder.is_dir():
        return out
    for p in sorted(folder.glob("*.md")):
        if OLD_VERSION.search(p.name):
            continue
        text = read(p)
        url = field(text, "page_url", "url")
        if url.startswith("/") or url.startswith("http"):
            path = re.sub(r"^https?://[^/]+", "", url).split("?")[0].strip("/")
            slug = path.split("/")[-1] if path else "home"
        else:
            kw = field(text, "primary_keyword", "primary keyword", "target keyword", "keyword")
            slug = slugify(kw) if kw else slugify(p.stem)
        out[slug] = field(text, "format", "page type", "page_type").lower()
    return out


def split_meta(md: str) -> tuple[str, str]:
    """The `| Field | Value |` metadata table at the top of article.md, and the article below it."""
    m = re.match(r"\s*((?:\|[^\n]*(?:\n|\Z))+)", md)
    return (m.group(1), md[m.end():]) if m else ("", md)


def metadata_url(page_dir: Path) -> str:
    # the table now heads article.md; pages written before 2026-10-28 keep it in metadata.md
    table = split_meta(read(page_dir / "article.md"))[0] or read(page_dir / "metadata.md")
    m = re.search(r"(?im)^\|\s*URL slug\s*\|\s*(.+?)\s*\|", table)
    return re.sub(r"^https?://[^/]+", "", m.group(1)).strip() if m else ""


def sections_of(text: str) -> list[str]:
    return [m.group(1).strip() for m in MARKER.finditer(text)]


def h2s_of(text: str) -> list[str]:
    return [h.strip() for h in re.findall(r"(?m)^## (.+)$", text) if h.strip().lower() != "sources"]


def words_of(text: str) -> int:
    t = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
    t = re.sub(r"\]\([^)]*\)", "]", t)
    t = re.sub(r"[#*_>|`\[\]]", " ", t)
    return len(t.split())


def classify(slug: str, text: str, page_dir: Path, briefs: dict[str, str], overrides: dict[str, str]) -> tuple[str, str]:
    if slug in overrides:
        return overrides[slug], "--type"
    if slug == "home":
        return "homepage", "folder name"
    kinds = {MARKER_TYPES[s] for s in sections_of(text) if s in MARKER_TYPES}
    if len(kinds) == 1:
        return kinds.pop(), "section markers"
    if len(kinds) > 1:
        return "unknown", "markers of more than one page type: " + ", ".join(sorted(kinds))
    fmt = briefs.get(slug)
    if fmt in BRIEF_FORMATS:
        return BRIEF_FORMATS[fmt], f"brief format `{fmt}`"
    if fmt in ARTICLE_FORMATS:
        return "resource", f"brief format `{fmt}`"
    url = metadata_url(page_dir)
    for rx, kind in URL_TYPES:
        if url and rx.search(url):
            return kind, f"URL slug {url}"
    return "unknown", "no markers, no brief in research/content-briefs/, no telling URL slug in the metadata table"


def find_kit(root: Path, kit: str | None) -> Path | None:
    if kit:
        p = root / kit
        return p if p.is_dir() else None
    base = root / "client-reference"
    dirs = sorted(d for d in base.iterdir() if d.is_dir()) if base.is_dir() else []
    return dirs[0] if len(dirs) == 1 else None


def parse_table(text: str, heading: str) -> list[dict[str, str]]:
    m = re.search(rf"(?ms)^## {re.escape(heading)}\s*$(.*?)(?=^## |\Z)", text)
    block = m.group(1) if m else text
    lines = [ln.strip() for ln in block.splitlines() if ln.strip().startswith("|")]
    if len(lines) < 2:
        return []
    head = [c.strip() for c in lines[0].strip("|").split("|")]
    rows = []
    for ln in lines[2:]:
        cells = [c.strip() for c in ln.strip("|").split("|")]
        if len(cells) == len(head):
            rows.append(dict(zip(head, cells)))
    return rows


OPTION = re.compile(r"(?i)\boption\s+([A-Z0-9]+)\b")


def option_from_rows(rows: list[dict[str, str]]) -> tuple[str | None, str]:
    """A pick is a `design` or `approval` row with Impact `none` on `homepage design`. The option comes
    from the Affects detail (`homepage design: Option B`), else from the only option the quote names."""
    picks, reopened = [], False
    for r in rows:
        typ = r.get("Type", "").lower()
        aff = r.get("Affects", "")
        if not re.match(r"(?i)\s*homepage design\b", aff):
            continue
        if typ == "question":
            reopened = True
            continue
        if typ not in ("design", "approval") or r.get("Impact", "").lower() != "none":
            continue
        named = OPTION.findall(aff) or OPTION.findall(r.get("Feedback", ""))
        if len({n.upper() for n in named}) == 1:
            picks.append(f"Option {named[0].upper()}")
    distinct = sorted(set(picks))
    if len(distinct) == 1:
        return distinct[0], ""
    if len(distinct) > 1:
        return None, "the client named more than one option: " + ", ".join(distinct)
    if reopened:
        return None, "the client's latest feedback asks about the homepage design without picking an option"
    return None, ""


def homepage_choice(root: Path, slug: str) -> dict:
    folder = root / "feedback" / slug
    files = sorted(folder.glob("*-feedback.md")) if folder.is_dir() else []
    note = ""
    for p in reversed(files):  # the latest feedback that picks, or reopens, the homepage design wins
        opt, why = option_from_rows(parse_table(read(p), "Feedback Items"))
        if opt:
            return {"option": opt, "file": p.relative_to(root).as_posix(), "note": ""}
        if why:
            return {"option": None, "file": p.relative_to(root).as_posix(), "note": why}
    if files:
        note = "feedback exists but names no homepage option"
    else:
        note = "no feedback file"
    return {"option": None, "file": files[-1].relative_to(root).as_posix() if files else None, "note": note}


def homepage_brief(root: Path, slug: str) -> dict:
    p = root / "design" / slug / f"{slug}-homepage-design-brief.md"
    text = read(p)
    if not text:
        return {"path": None, "brand_cues": [], "section_map": []}
    m = re.search(r"(?ms)^## Brand Cues\s*$(.*?)(?=^## |\Z)", text)
    cues = [ln.strip() for ln in (m.group(1) if m else "").splitlines() if ln.strip().startswith("-")]
    smap = [r.get("Section", "") for r in parse_table(text, "Section Map")]
    return {"path": p.relative_to(root).as_posix(), "brand_cues": cues, "section_map": smap}


def scan(root: Path, slug: str, kit_arg: str | None, overrides: dict[str, str]) -> dict:
    briefs = brief_index(root)
    pages = []
    content = root / "content"
    for d in sorted(p for p in content.iterdir() if p.is_dir()) if content.is_dir() else []:
        art = d / "article.md"
        if not art.exists():
            continue
        text = split_meta(read(art))[1]
        kind, why = classify(d.name, text, d, briefs, overrides)
        pages.append({
            "url_slug": d.name,
            "path": art.relative_to(root).as_posix(),
            "type": kind,
            "why": why,
            "words": words_of(text),
            "h2": len(h2s_of(text)),
            "sections": sections_of(text),
            "headings": h2s_of(text),
            "flags": list(dict.fromkeys(FLAG.findall(text))),
        })
    kit = find_kit(root, kit_arg)
    kit_files = sorted(p.relative_to(root).as_posix() for p in kit.glob("*.md")) if kit else []
    return {
        "slug": slug,
        "pages": pages,
        "types": [t for t in TYPES if any(p["type"] == t for p in pages)],
        "unknown": [p["url_slug"] for p in pages if p["type"] == "unknown"],
        "kit": kit.relative_to(root).as_posix() if kit else None,
        "kit_files": kit_files,
        "homepage_brief": homepage_brief(root, slug),
        "choice": homepage_choice(root, slug),
        "brief_path": f"design/{slug}/{slug}-page-type-design-briefs.md",
    }


# ---------------------------------------------------------------- computed parts

def of_type(s: dict, t: str) -> list[dict]:
    return [p for p in s["pages"] if p["type"] == t]


def rng(vals: list[int]) -> str:
    lo, hi = min(vals), max(vals)
    return f"{lo:,}" if lo == hi else f"{lo:,} to {hi:,}"


def words_line(pages: list[dict]) -> str:
    n = len(pages)
    return f"Words: {rng([p['words'] for p in pages])} ({n} page{'s' if n != 1 else ''})"


def h2_line(pages: list[dict]) -> str:
    return f"H2 sections: {rng([p['h2'] for p in pages])}"


def marked(pages: list[dict]) -> bool:
    return all(p["sections"] for p in pages)


def section_rows(pages: list[dict]) -> list[tuple[str, str]]:
    """Ordered union of the pages' markers, with how many pages carry each."""
    order: list[str] = []
    for p in pages:
        prev = -1
        for s in p["sections"]:
            if s in order:
                prev = order.index(s)
            else:
                order.insert(prev + 1, s)
                prev += 1
    n = len(pages)
    out = []
    for s in order:
        k = sum(1 for p in pages if s in p["sections"])
        out.append((s, "all" if k == n else f"{k} of {n}"))
    return out


def flag_index(s: dict) -> list[tuple[str, list[str]]]:
    idx: dict[str, list[str]] = {}
    for p in s["pages"]:
        if p["type"] in TYPES:
            for f in p["flags"]:
                idx.setdefault(f, []).append(p["path"])
    return list(idx.items())


def sources_list(s: dict) -> list[str]:
    out = [p["path"] for p in s["pages"] if p["type"] in TYPES]
    out += s["kit_files"]
    if s["homepage_brief"]["path"]:
        out.append(s["homepage_brief"]["path"])
    if s["choice"]["file"]:
        out.append(s["choice"]["file"])
    return out


def direction_line(s: dict) -> str:
    c = s["choice"]
    return f"Homepage direction: {c['option']} ({c['file']})" if c["option"] else f"Homepage direction: {NOT_CHOSEN}"


# ---------------------------------------------------------------- scaffold

def scaffold(s: dict, client: str, date: str) -> str:
    hb = s["homepage_brief"]["path"] or "none"
    L = [f"Client: {client} · Built: {date} · Homepage brief: {hb}", direction_line(s), "",
         f"# Page-Type Design Briefs: {client}", "", "## Page Types", "",
         "| Page type | Pages |", "| --- | --- |"]
    for t in s["types"]:
        L.append(f"| {t} | {len(of_type(s, t))} |")
    for t in s["types"]:
        pages = of_type(s, t)
        L += ["", f"## {HEADINGS[t]}", "", "### Pages", ""]
        L += [f"- `{p['path']}`" for p in pages]
        L += ["", "### Content Map", "", MAP_HEADER, "| --- | --- | --- | --- | --- |"]
        if marked(pages):
            for i, (sec, on) in enumerate(section_rows(pages), 1):
                L.append(f"| {i} | {sec} | {FILL} | {on} | article.md > {sec} |")
        else:
            L.append(f"| 1 | {FILL} | {FILL} | {FILL} | {FILL} |")
        L += ["", "### Repeating Blocks", "", f"- {FILL}",
              "", "### Content Length", "", words_line(pages), h2_line(pages), "", f"- {FILL}",
              "", "### CTAs", "", f"- {FILL}",
              "", "### Brand Reference", "", f"- {FILL}",
              "", "### Responsive Priorities", "", f"- {FILL}",
              "", "### Homepage Relationship", "", f"- {FILL}",
              "", "### Consistent and Variable", "", f"- Consistent: {FILL}", f"- Varies: {FILL}"]
    L += ["", "## Open Questions", ""]
    n = 0
    if not s["choice"]["option"]:
        n += 1
        L.append(f"{n}. Homepage {NOT_CHOSEN}: which homepage option did the client choose? The Homepage Relationship lines wait on it. AM.")
    if not s["homepage_brief"]["path"]:
        n += 1
        L.append(f"{n}. No homepage design brief at design/{s['slug']}/{s['slug']}-homepage-design-brief.md; the Homepage Relationship lines wait on it. Design.")
    if not s["kit"]:
        n += 1
        L.append(f"{n}. No client reference kit in client-reference/; brand colours, type and logo wait on it. AM.")
    for f, paths in flag_index(s):
        n += 1
        L.append(f"{n}. {f} ({', '.join(paths)}). Client.")
    L += ["", "## Hand-off", "", f"- Brief: {s['brief_path']}",
          "- Content files: the Pages list under each page type"]
    if s["homepage_brief"]["path"]:
        opt = s["choice"]["option"] or NOT_CHOSEN
        L.append(f"- Homepage design: {s['homepage_brief']['path']} ({opt})")
    else:
        L.append(f"- Homepage design: none yet ({NOT_CHOSEN})" if not s["choice"]["option"] else "- Homepage design: none yet")
    L += ["", "## Sources", ""] + [f"- {p}" for p in sources_list(s)]
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- check

class Report:
    def __init__(self) -> None:
        self.rows: list[tuple[str, str, str]] = []

    def add(self, ok: bool, name: str, detail: str = "") -> None:
        self.rows.append(("PASS" if ok else "FAIL", name, detail))

    @property
    def ok(self) -> bool:
        return all(r[0] == "PASS" for r in self.rows)


def blocks(text: str, level: int) -> list[tuple[str, str]]:
    mark = "#" * level
    parts = re.split(rf"(?m)^{mark} (.+?)\s*$", text)
    return [(parts[i].strip(), parts[i + 1]) for i in range(1, len(parts), 2)]


def bullets(body: str) -> list[str]:
    return [ln.strip()[2:].strip() for ln in body.splitlines() if ln.strip().startswith("- ")]


def unquote(text: str) -> str:
    return re.sub(r"\"[^\"\n]*\"|“[^”\n]*”", " ", text)


def check(brief: Path, s: dict, root: Path) -> Report:
    r = Report()
    text = read(brief)
    if not text:
        r.add(False, "brief exists", str(brief))
        return r
    lines = text.splitlines()
    sources_text = "\n".join(read(root / p) for p in sources_list(s))

    r.add(bool(re.match(r"^Client: .+ · Built: \d{4}-\d{2}-\d{2} · Homepage brief: .+$", lines[0] if lines else "")),
          "top line shape", lines[0] if lines else "")
    want_dir = direction_line(s)
    r.add(len(lines) > 1 and lines[1].strip() == want_dir, "homepage direction line", f"want: {want_dir}")
    r.add(bool(re.search(r"(?m)^# Page-Type Design Briefs: .+$", text)), "title")
    r.add(FILL not in text, "no <fill> left", f"{text.count(FILL)} left" if FILL in text else "")
    r.add("<!--" not in text, "no HTML comments")

    h2 = blocks(text, 2)
    want = ["Page Types"] + [HEADINGS[t] for t in s["types"]] + ["Open Questions", "Hand-off", "Sources"]
    got = [h for h, _ in h2]
    r.add(got == want, "sections in order, one per page type found", f"want {want}, got {got}")
    body = dict(h2)

    pt_rows = parse_table("## Page Types\n" + body.get("Page Types", ""), "Page Types")
    pt = {row.get("Page type", ""): row.get("Pages", "") for row in pt_rows}
    want_pt = {t: str(len(of_type(s, t))) for t in s["types"]}
    r.add(pt == want_pt, "Page Types table", f"want {want_pt}, got {pt}")

    for t in s["types"]:
        name = HEADINGS[t]
        pages = of_type(s, t)
        sub = blocks(body.get(name, ""), 3)
        subd = dict(sub)
        r.add([h for h, _ in sub] == SUBSECTIONS, f"{name}: fixed subsections", f"got {[h for h, _ in sub]}")
        listed = [b.strip("`") for b in bullets(subd.get("Pages", ""))]
        missing_files = [p for p in listed if not (root / p).exists()]
        r.add(not missing_files, f"{name}: every listed page file exists", ", ".join(missing_files))
        r.add(sorted(listed) == sorted(p["path"] for p in pages), f"{name}: every page of the type listed, no others",
              f"want {[p['path'] for p in pages]}")

        cm = subd.get("Content Map", "")
        rows = [ln for ln in cm.splitlines() if ln.strip().startswith("|")]
        r.add(bool(rows) and rows[0].strip() == MAP_HEADER, f"{name}: Content Map header", MAP_HEADER)
        cells = [[c.strip() for c in ln.strip().strip("|").split("|")] for ln in rows[2:]]
        cells = [c for c in cells if len(c) == 5]
        r.add(bool(cells) and [c[0] for c in cells] == [str(i) for i in range(1, len(cells) + 1)],
              f"{name}: Content Map rows numbered from 1")
        n = len(pages)
        bad_on = [c[3] for c in cells if not re.fullmatch(rf"all|[1-9]\d* of {n}", c[3])]
        r.add(not bad_on, f"{name}: Appears on is `all` or `k of {n}`", ", ".join(bad_on))
        if marked(pages):
            exp = section_rows(pages)
            r.add([(c[1], c[3]) for c in cells] == exp, f"{name}: Content Map follows the page sections",
                  "want " + "; ".join(f"{a} ({b})" for a, b in exp))

        cl = subd.get("Content Length", "")
        r.add(words_line(pages) in cl and h2_line(pages) in cl, f"{name}: computed length lines",
              f"want `{words_line(pages)}` and `{h2_line(pages)}`")
        r.add(bool(bullets(cl)), f"{name}: says how the template handles length")
        r.add(bool(bullets(subd.get("Repeating Blocks", ""))), f"{name}: repeating blocks listed")
        r.add(bool(bullets(subd.get("CTAs", ""))), f"{name}: CTA placement given")
        r.add("mobile" in subd.get("Responsive Priorities", "").lower(), f"{name}: responsive priorities start from mobile")

        br = bullets(subd.get("Brand Reference", ""))
        untagged = [b for b in br if not (b.startswith("GAP:") or TAG.search(b))]
        r.add(bool(br) and not untagged, f"{name}: every brand cue sourced or a GAP", " | ".join(untagged)[:300])
        bad_kit = [m for b in br for m in re.findall(r"\[kit: ([\w.-]+)\]", b)
                   if not s["kit"] or not (root / s["kit"] / m).exists()]
        r.add(not bad_kit, f"{name}: kit tags name kit files that exist", ", ".join(bad_kit))
        if any("[homepage brief]" in b for b in br):
            r.add(bool(s["homepage_brief"]["path"]), f"{name}: [homepage brief] tag has a homepage brief")
        if any("[feedback]" in b for b in br):
            r.add(bool(s["choice"]["file"]), f"{name}: [feedback] tag has a feedback file")
        src_hex = {h.lower() for h in HEX.findall(sources_text)}
        brand_text = subd.get("Brand Reference", "")
        if src_hex:
            r.add(any(h.lower() in src_hex for h in HEX.findall(brand_text)), f"{name}: brand colours referenced",
                  "the sources give colour values; quote at least one")
        else:
            r.add(any(b.startswith("GAP:") and re.search(r"colou?r", b, re.I) for b in br),
                  f"{name}: missing colours are a GAP", "no source gives colour values")

        hr = subd.get("Homepage Relationship", "")
        if not s["homepage_brief"]["path"]:
            r.add("GAP:" in hr, f"{name}: no homepage brief is a GAP")
        if s["choice"]["option"]:
            r.add(s["choice"]["option"].lower() in hr.lower(), f"{name}: names the chosen homepage option")
        else:
            r.add(NOT_CHOSEN in hr, f"{name}: says the homepage {NOT_CHOSEN}")
        cv = bullets(subd.get("Consistent and Variable", ""))
        r.add(any(b.startswith("Consistent:") for b in cv) and any(b.startswith("Varies:") for b in cv),
              f"{name}: consistent and varying parts")

    oq = body.get("Open Questions", "")
    missing_flags = [f for f, _ in flag_index(s) if f not in oq]
    r.add(not missing_flags, "every open flag copied into Open Questions", " | ".join(missing_flags)[:300])
    r.add(bool(re.search(r"(?m)^1\. ", oq)), "Open Questions numbered")
    if not s["choice"]["option"]:
        r.add(NOT_CHOSEN in oq, f"Open Questions says {NOT_CHOSEN}")
        r.add(not re.search(r"\bOption [A-Z0-9]\b", text), "no homepage option guessed")
    if not s["homepage_brief"]["path"]:
        r.add("homepage design brief" in oq.lower(), "missing homepage design brief asked for")
    if not s["kit"]:
        r.add("client reference kit" in oq.lower(), "missing client reference kit asked for")

    ho = body.get("Hand-off", "")
    r.add(s["brief_path"] in ho, "Hand-off names this brief")
    if s["homepage_brief"]["path"]:
        r.add(s["homepage_brief"]["path"] in ho, "Hand-off names the homepage design brief")

    srcs = [b.strip("`") for b in bullets(body.get("Sources", ""))]
    gone = [p for p in srcs if not (root / p).exists()]
    r.add(bool(srcs) and not gone, "Sources are files that exist", ", ".join(gone))

    scan_text = unquote(text.split("\n## Sources", 1)[0])
    hits = []
    for rx, what in VISUAL:
        for m in rx.finditer(scan_text):
            hits.append(f"{what}: '{m.group(0)}'")
    r.add(not hits, "no visual design prescribed", "; ".join(hits[:8]))
    stray_hex = [h for h in HEX.findall(text) if h.lower() not in {x.lower() for x in HEX.findall(sources_text)}]
    r.add(not stray_hex, "colour values come from a source", ", ".join(stray_hex))
    norm_src = re.sub(r"\s+", " ", sources_text)
    bad_q = [q for q in re.findall(r"\"([^\"\n]+)\"|“([^”\n]+)”", text)
             for q in [q[0] or q[1]] if len(q.split()) >= 4 and re.sub(r"\s+", " ", q) not in norm_src]
    r.add(not bad_q, "quoted wording is word for word from a source", " | ".join(bad_q)[:300])
    return r


# ---------------------------------------------------------------- contract helpers

def cmd_known(path: Path) -> int:
    data = json.loads(read(path))
    bad = []
    for key, kind in data.items():
        m = MARKER.fullmatch(key.strip())
        name = m.group(1) if m else key
        got = "shared" if name in SHARED_MARKERS else MARKER_TYPES.get(name, "unknown")
        if got != kind:
            bad.append(f"{key}: fixture says {kind}, this skill reads {got}")
    for b in bad:
        print(b, file=sys.stderr)
    print(f"{len(data)} markers, {len(bad)} mismatched")
    return 1 if bad else 0


def cmd_brief_format(path: Path) -> int:
    data = json.loads(read(path))
    items = data if isinstance(data, list) else [data]
    bad = 0
    for it in items:
        fmt = str(it.get("format", "")).lower()
        kind = BRIEF_FORMATS.get(fmt) or ("resource" if fmt in ARTICLE_FORMATS else "unknown")
        bad += kind == "unknown"
        print(f"{it.get('page_url', '')} format={fmt} -> {kind}")
    return 1 if bad else 0


def cmd_choice(path: Path) -> int:
    data = json.loads(read(path))
    rows = parse_table("## Feedback Items\n" + data["## Feedback Items"], "Feedback Items")
    opt, why = option_from_rows(rows)
    if not rows:
        print("no Feedback Items rows", file=sys.stderr)
        return 1
    print(f"chosen: {opt or NOT_CHOSEN}" + (f" ({why})" if why else ""))
    return 0 if opt == data.get("chosen") else 1


# ---------------------------------------------------------------- cli

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["scan", "scaffold", "check", "known", "choice", "brief-format"])
    ap.add_argument("target", nargs="?", help="brief (check) or fixture (known, choice)")
    ap.add_argument("--slug")
    ap.add_argument("--client")
    ap.add_argument("--date", default=dt.date.today().isoformat())
    ap.add_argument("--root", default=".")
    ap.add_argument("--kit", help="client-reference/<client-slug> when there is more than one")
    ap.add_argument("--type", action="append", default=[], help="url-slug=type override")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    if a.mode == "known":
        return cmd_known(Path(a.target))
    if a.mode == "choice":
        return cmd_choice(Path(a.target))
    if a.mode == "brief-format":
        return cmd_brief_format(Path(a.target))
    if not a.slug:
        ap.error("--slug is required")
    overrides = {}
    for o in a.type:
        k, _, v = o.partition("=")
        if v not in TYPES + ["homepage"]:
            ap.error(f"--type {o}: type must be one of {TYPES + ['homepage']}")
        overrides[k] = v
    root = Path(a.root)
    s = scan(root, a.slug, a.kit, overrides)

    if not s["pages"]:
        print("No pages in content/<url-slug>/article.md. Write the pages first (seo-content-writer).", file=sys.stderr)
        return 2
    if s["unknown"]:
        for p in s["pages"]:
            if p["type"] == "unknown":
                print(f"UNKNOWN TYPE  {p['path']}: {p['why']}. Pass --type {p['url_slug']}=<{'|'.join(TYPES)}>", file=sys.stderr)
        if a.mode != "scan":
            return 1
    if not s["types"] and a.mode != "scan":
        print("Only the homepage is written; it has its own brief (homepage-design-brief). No page types to brief.", file=sys.stderr)
        return 2

    if a.mode == "scan":
        if a.json:
            print(json.dumps(s, indent=2))
        else:
            print(f"client folder: {root.resolve().name}  slug: {a.slug}")
            for p in s["pages"]:
                extra = "sections: " + ", ".join(p["sections"]) if p["sections"] else "H2s: " + " / ".join(p["headings"])
                print(f"- {p['path']}  type={p['type']} ({p['why']})  words={p['words']}  h2={p['h2']}")
                print(f"    {extra}")
                for f in p["flags"]:
                    print(f"    flag: {f}")
            print(f"page types: {', '.join(s['types']) or 'none'}")
            print(f"kit: {s['kit'] or 'none'}  files: {', '.join(s['kit_files']) or 'none'}")
            hb = s["homepage_brief"]
            print(f"homepage design brief: {hb['path'] or 'none'}")
            for c in hb["brand_cues"]:
                print(f"    brand cue: {c}")
            c = s["choice"]
            print(f"homepage option: {c['option'] or NOT_CHOSEN}" + (f" ({c['file']})" if c["file"] else "")
                  + (f"; {c['note']}" if c["note"] else ""))
            print(f"brief path: {s['brief_path']}")
        return 1 if s["unknown"] else 0

    if a.mode == "scaffold":
        if not a.client:
            ap.error("--client is required")
        out = root / s["brief_path"]
        if out.exists() and not a.force:
            print(f"{out} exists; edit it, or pass --force to start again.", file=sys.stderr)
            return 1
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(scaffold(s, a.client, a.date), encoding="utf-8")
        print(f"wrote {s['brief_path']} ({out.read_text(encoding='utf-8').count(FILL)} <fill> to write)")
        return 0

    brief = Path(a.target) if a.target else root / s["brief_path"]
    if not brief.is_absolute() and a.target and not brief.exists():
        brief = root / a.target
    rep = check(brief, s, root)
    for status, name, detail in rep.rows:
        print(f"{status}  {name}" + (f"  ({detail})" if detail and status == "FAIL" else ""))
    print(f"RESULT: {'PASS' if rep.ok else 'FAIL'}")
    return 0 if rep.ok else 1


if __name__ == "__main__":
    sys.exit(main())
