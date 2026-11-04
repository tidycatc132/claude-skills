#!/usr/bin/env python3
"""Case study narrative and showcase design brief for a launched website build.

Run from the client's working folder (or pass --root). Standard library only.

  case_study.py scaffold --slug <slug> [--launch YYYY-MM-DD] [--client-slug X] [--date YYYY-MM-DD] [--force]
      Writes case-study/<slug>/<slug>-case-study.md and
      case-study/<slug>/<slug>-case-study-design-brief.md with every count, table and
      colour filled from the build's files and [WRITE: ...] slots for the prose.
  case_study.py check --slug <slug> [--launch ...] [--client-slug X]
      Checks both files against the sources. Prints a table and RESULT: PASS or RESULT: FAIL.
  case_study.py counts --slug <slug> [...]
      Prints the counts and inputs found, as JSON.
  case_study.py index <dev-handoff-index.md> | quotes <quote-bank.md> | kit <kit-folder>
               | keywords <keyword-report.md> | inventory <url-inventory.csv>
      Print, as JSON, what this skill reads from one producer file (contracts).
      With --validate FILE.json, check such a JSON file instead.
  case_study.py contract <case-study.md>
      Print the narrative's header lines, headings and quick stats as JSON.

Exit codes: 0 PASS or written, 1 FAIL or refused, 2 usage error.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import json
import re
import sys
from pathlib import Path

GROUPS = ["Homepage", "Service Pages", "Location Pages", "About Page", "Contact Page",
          "Resource Pages", "Pages Without a Template"]
GROUP_WORDS = {"Homepage": ("homepage", "homepage"), "Service Pages": ("service page", "service pages"),
               "Location Pages": ("location page", "location pages"), "About Page": ("About page", "About pages"),
               "Contact Page": ("Contact page", "Contact pages"), "Resource Pages": ("resource page", "resource pages"),
               "Pages Without a Template": ("other page", "other pages")}
PAGE_KEYS = ["Page", "URL", "Content file", "Template", "Priority", "Status"]
REDIRECT_KEYS = ["Old URL", "New URL", "Note"]
QUOTE_KEYS = ["#", "Quote", "Speaker", "Timestamp", "Use for"]
SECTIONS = ["Client Snapshot", "The Challenge", "The Approach", "What We Built", "Results",
            "In Their Words", "Quick Stats"]
BRIEF_SECTIONS = ["Pages to Screenshot", "Before and After", "Brand Colours", "Callout Stats",
                  "Layout Suggestion"]
HEADER = ["Client:", "Launch:", "Written:", "Feature consent:", "Approved quotes:", "Metrics:"]
BRIEF_HEADER = ["Client:", "Case study:", "Live site:", "Colours from:"]
HYPE = ["revolutionary", "game-changing", "game changer", "game-changer", "cutting-edge", "cutting edge",
        "world-class", "world class", "best-in-class", "state-of-the-art", "skyrocket", "skyrocketed",
        "explosive", "unprecedented", "seamless", "seamlessly", "synergy", "next-level", "next level",
        "transformative", "transformed", "supercharge", "supercharged", "unparalleled", "incredible",
        "amazing", "stunning", "jaw-dropping", "breathtaking", "dramatically", "massive", "massively",
        "unrivalled", "unrivaled", "leading-edge", "turbocharge", "rockstar", "ninja", "10x",
        "best ever", "second to none", "unmatched"]
PROMISE = re.compile(r"(?i)\branks? (first|#1|number one|at the top)\b|\b(#1|number one) (on|in) google\b|\bwill (rise|grow|increase|double|bring|deliver|rank)\b|"
                     r"\b(doubled|tripled|quadrupled)\b|\b\d+(\.\d+)?x\b|\bguarantee")
STRUCTURED = re.compile(r"(?i)structured data|schema|json-ld|rich snippet|rich result")
INTERNAL = re.compile(r"(?i)\bbugherd\b|\bQA\b|\bNO-GO\b|\bP[0-3]\b|\bSOW\b|\bclickup\b|\.md\b|"
                      r"\bkickoff/|\bhandoff/|\bTier [123]\b|\bseverit")
HEX = re.compile(r"#([0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})(?![0-9A-Za-z])")
NUM = re.compile(r"(?<![\w#$.,/:-])\$?(\d[\d,.\-/:]*\d|\d)%?(?![A-Za-z_\d])")
WRITE = "[WRITE:"
QUOTE_NEEDED = "QUOTE NEEDED:"
FIXED_NUMBERS = {"90"}
RETIRED = re.compile(r"(?i)retired|do not use|don't use|never use|no longer")


# ---------------------------------------------------------------- helpers

def read(p: Path) -> str:
    return p.read_text(encoding="utf-8") if p.exists() else ""


def norm_space(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def qnorm(s: str) -> str:
    s = s.replace("\u2019", "'").replace("\u2018", "'")
    return " ".join(re.sub(r"[^a-z0-9']+", " ", s.lower()).split())


def header_value(text: str, key: str) -> str | None:
    for ln in text.splitlines():
        if ln.startswith(key):
            return ln[len(key):].strip()
    return None


def table_rows(lines: list[str]) -> list[list[str]]:
    rows = []
    for ln in lines:
        s = ln.strip()
        if not s.startswith("|"):
            if rows:
                break
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
            continue
        rows.append(cells)
    return rows


def section(text: str, heading: str, level: int = 2) -> list[str] | None:
    """Lines under `## heading` (level 2) or `### heading` up to the next heading of that level or higher."""
    lines = text.splitlines()
    mark = "#" * level + " " + heading
    for i, ln in enumerate(lines):
        if ln.strip() == mark:
            out = []
            for nx in lines[i + 1:]:
                m = re.match(r"^(#+) ", nx)
                if m and len(m.group(1)) <= level:
                    break
                out.append(nx)
            return out
    return None


def numbers(text: str) -> list[str]:
    out = []
    for m in NUM.finditer(text):
        tok = m.group(1)
        out.append(tok)
    return out


def num_forms(tok: str) -> set[str]:
    forms = {tok}
    if re.fullmatch(r"\d{1,3}(,\d{3})+(\.\d+)?", tok):
        forms.add(tok.replace(",", ""))
    if re.fullmatch(r"\d+", tok) and len(tok) > 3:
        forms.add(f"{int(tok):,}")
    return forms


def number_pool(texts: list[str]) -> set[str]:
    pool = set()
    for t in texts:
        for tok in numbers(t):
            pool |= num_forms(tok)
        t = HEX.sub(" ", t)
        t = re.sub(r"\+?\d[\d().\- ]{8,}\d", " ", t)  # phone numbers
        for m in re.finditer(r"\d[\d,.]*\d|\d", t):  # bare digits anywhere, e.g. inside "10-page"
            pool |= num_forms(m.group(0))
    return pool


def word_count(md: str) -> int:
    md = re.sub(r"<!--.*?-->", " ", md, flags=re.S)
    md = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", md)
    md = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", md)
    md = re.sub(r"<[^>]+>", " ", md)
    return sum(1 for w in re.split(r"\s+", md) if re.search(r"[A-Za-z0-9]", w))


def fmt(n: int) -> str:
    return f"{n:,}"


# ---------------------------------------------------------------- producer readers

def parse_index(text: str) -> dict:
    out = {g: [] for g in GROUPS}
    out["### Redirects"] = []
    group = None
    page = None
    for ln in text.splitlines():
        m2 = re.match(r"^## (.+)$", ln)
        if m2:
            group = m2.group(1).strip() if m2.group(1).strip() in GROUPS else None
            page = None
            continue
        if group and ln.startswith("### "):
            page = {k: "" for k in PAGE_KEYS}
            out[group].append(page)
            continue
        if group and page is not None:
            m = re.match(r"^- ([A-Za-z ]+): ?(.*)$", ln)
            if m and m.group(1) in PAGE_KEYS:
                page[m.group(1)] = m.group(2).strip()
    red = section(text, "Redirects", 3) or []
    rows = table_rows(red)
    if rows and rows[0][:3] == REDIRECT_KEYS:
        for r in rows[1:]:
            if len(r) >= 3:
                out["### Redirects"].append(dict(zip(REDIRECT_KEYS, r[:3])))
    return out


def validate_index(data: dict) -> list[str]:
    errs = []
    for g in GROUPS + ["### Redirects"]:
        if g not in data or not isinstance(data[g], list):
            errs.append(f"missing list '{g}'")
    for g in GROUPS:
        for p in data.get(g, []):
            for k in PAGE_KEYS:
                if k not in p:
                    errs.append(f"{g}: page missing '{k}'")
            if p.get("Priority") not in ("Build", "Post-Launch"):
                errs.append(f"{g}: {p.get('Page')} Priority must be Build or Post-Launch")
    for r in data.get("### Redirects", []):
        for k in REDIRECT_KEYS:
            if k not in r:
                errs.append(f"redirect missing '{k}'")
    if not any(data.get(g) for g in GROUPS):
        errs.append("no pages")
    return errs


def parse_quotes(text: str) -> list[dict]:
    rows = table_rows(text.splitlines())
    if not rows or rows[0] != QUOTE_KEYS:
        return []
    return [dict(zip(QUOTE_KEYS, r)) for r in rows[1:] if len(r) == len(QUOTE_KEYS)]


def validate_quotes(data) -> list[str]:
    errs = []
    if not isinstance(data, list) or not data:
        return ["expected a non-empty list of quotes"]
    for i, q in enumerate(data, 1):
        for k in QUOTE_KEYS:
            if k not in q:
                errs.append(f"quote {i} missing '{k}'")
        if not re.fullmatch(r"\d{2}:\d{2}:\d{2}", str(q.get("Timestamp", ""))):
            errs.append(f"quote {i} Timestamp is not HH:MM:SS")
    return errs


def parse_keywords(text: str) -> list[dict]:
    blk = text.split("\ntargets:", 1)[1] if "\ntargets:" in text else ""
    out, seen = [], set()
    for m in re.finditer(r"^\s*primary_keyword:\s*(.+?)\s*$", blk, re.M):
        k = m.group(1).split(" #")[0].strip()
        if k and k not in seen:
            seen.add(k)
            out.append({"primary_keyword": k})
    return out


def parse_inventory(text: str) -> list[dict]:
    return [{"url": r.get("url", ""), "title": r.get("title", "")} for r in csv.DictReader(io.StringIO(text))]


def colour_lines(text: str, source: str) -> tuple[list[dict], list[dict]]:
    keep, retired = [], []
    for ln in text.splitlines():
        if not HEX.search(ln):
            continue
        raw = ln.strip().lstrip("-*").strip()
        for m in HEX.finditer(raw):
            hx = "#" + m.group(1).upper()
            name = raw[:m.start()].strip(" `:-")
            name = re.sub(r"(?i)^[a-z ]*colou?rs?:\s*|^retired, do not use:\s*", "", name).strip(" `:-")
            use = raw[m.end():].strip(" `:-,")
            use = re.sub(r"\s*\[(internal|site|search)\].*$", "", use).strip(" .")
            item = {"Colour": name or "unnamed", "Hex": hx, "Use": use or "not stated", "Source": source}
            (retired if RETIRED.search(raw) else keep).append(item)
    return keep, retired


def parse_kit(folder: Path, rel: str = "") -> dict:
    out = {"brand.md": [], "style.md": [], "Retired, do not use": []}
    for f in ("brand.md", "style.md"):
        k, r = colour_lines(read(folder / f), f"{rel}{f}" if rel else f)
        out[f] = k
        out["Retired, do not use"] += r
    return out


def validate_list(keys: list[str]):
    def v(data) -> list[str]:
        if not isinstance(data, list) or not data:
            return ["expected a non-empty list"]
        return [f"item {i} missing '{k}'" for i, d in enumerate(data, 1) for k in keys if not d.get(k)]
    return v


def validate_kit(data: dict) -> list[str]:
    errs = []
    for k in ("brand.md", "style.md", "Retired, do not use"):
        if k not in data or not isinstance(data[k], list):
            errs.append(f"missing list '{k}'")
            continue
        for c in data[k]:
            if not re.fullmatch(r"#[0-9A-F]{3}([0-9A-F]{3})?", c.get("Hex", "")):
                errs.append(f"{k}: bad hex {c.get('Hex')}")
    return errs


# ---------------------------------------------------------------- gather

class Inputs:
    pass


def newest(paths: list[Path]) -> Path | None:
    paths = sorted(paths, key=lambda p: p.name)
    return paths[-1] if paths else None


def find_slug(root: Path, slug: str | None) -> str:
    if slug:
        return slug
    cands = sorted(p.parent.name for p in root.glob("handoff/*/*-dev-handoff-index.md"))
    if len(cands) == 1:
        return cands[0]
    raise SystemExit("usage: pass --slug (found %s)" % (", ".join(cands) or "no dev handoff index"))


def gather(root: Path, slug: str, launch: str | None, client_slug: str | None) -> Inputs:
    I = Inputs()
    I.root, I.slug = root, slug
    rel = lambda p: p.relative_to(root).as_posix() if p else "none"
    I.rel = rel
    I.ctx_p = root / f"kickoff/{slug}/{slug}-context.md"
    I.inv_p = root / f"kickoff/{slug}/{slug}-url-inventory.csv"
    I.qb_p = root / f"kickoff/{slug}/{slug}-quote-bank.md"
    I.bp_p = root / f"blueprint/{slug}/{slug}-growth-blueprint.md"
    I.idx_p = root / f"handoff/{slug}/{slug}-dev-handoff-index.md"
    I.appr_p = root / f"case-study/{slug}/{slug}-approvals.md"
    I.met_p = root / f"case-study/{slug}/{slug}-metrics.md"
    I.out_p = root / f"case-study/{slug}/{slug}-case-study.md"
    I.brief_p = root / f"case-study/{slug}/{slug}-case-study-design-brief.md"
    I.kw_p = newest([p for p in root.glob("research/keyword-research/*.md") if "\ntargets:" in read(p)])
    kits = sorted(p for p in root.glob("client-reference/*") if p.is_dir())
    if client_slug:
        I.kit_d = root / "client-reference" / client_slug
    elif len(kits) == 1:
        I.kit_d = kits[0]
    else:
        I.kit_d = None
    I.kit_many = len(kits) > 1 and not client_slug
    I.ctx, I.idx_t, I.bp = read(I.ctx_p), read(I.idx_p), read(I.bp_p)
    I.client = header_value(I.ctx, "Client:") or ""
    snap = section(I.ctx, "Snapshot") or []
    def snap_val(k):
        for ln in snap:
            m = re.match(rf"^- {k}: (.*?)(\s*\[[^\]]*\])?\s*$", ln)
            if m:
                return m.group(1).strip()
        return ""
    I.website = snap_val("Website")
    I.area = snap_val("Service area")
    contact = snap_val("Primary contact")
    I.contact = contact.split(",")[0].strip() if contact else ""
    # launch date
    I.launch_src = "given"
    if not launch:
        em = read(root / f"emails/{slug}/{slug}-go-live-email.md")
        v = header_value(em, "Launch:") or ""
        m = re.search(r"\d{4}-\d{2}-\d{2}", v)
        launch = m.group(0) if m else None
        I.launch_src = f"emails/{slug}/{slug}-go-live-email.md" if launch else "none"
    I.launch = launch or "not given"
    # live base URL
    lc = newest(list(root.glob(f"qa/{slug}/{slug}-launch-check-*.md")))
    live = header_value(read(lc), "Live:") if lc else None
    if live:
        live = live.split()[0]
    if not live and I.website:
        live = I.website if I.website.startswith("http") else "https://" + I.website
    I.live = (live or "").rstrip("/")
    # index
    I.index = parse_index(I.idx_t)
    I.build = []
    I.post = []
    for g in GROUPS:
        for p in I.index[g]:
            p = dict(p, group=g)
            (I.build if p["Priority"] == "Build" else I.post).append(p)
    I.built, I.unwritten = [], []
    I.words = 0
    for p in I.build:
        cf = p["Content file"]
        f = root / cf if cf and cf != "none" else None
        if f and f.exists():
            n = word_count(read(f))
            p["words"] = n
            I.words += n
            I.built.append(p)
        else:
            I.unwritten.append(p)
    I.by_type = {}
    for p in I.built:
        I.by_type[p["group"]] = I.by_type.get(p["group"], 0) + 1
    I.redirects = [r for r in I.index["### Redirects"] if r["New URL"].startswith("/")]
    I.no_target = [r for r in I.index["### Redirects"] if not r["New URL"].startswith("/")]
    # old site
    inv = read(I.inv_p)
    I.inventory = list(csv.DictReader(io.StringIO(inv))) if inv else []
    # keywords
    I.keywords = [k["primary_keyword"] for k in parse_keywords(read(I.kw_p) if I.kw_p else "")]
    # quotes and approvals
    I.quotes = parse_quotes(read(I.qb_p))
    appr = read(I.appr_p)
    I.featured = (header_value(appr, "Featured:") or "not asked").lower() if appr else "not asked"
    I.approved_by = header_value(appr, "Approved by:") or ""
    nums = header_value(appr, "Approved quotes:") or ""
    I.approved_ids = [x for x in re.findall(r"\d+", nums)]
    I.approved = [q for q in I.quotes if q["#"] in I.approved_ids]
    # metrics
    I.metrics_t = read(I.met_p)
    I.metrics_rows = []
    if I.metrics_t:
        rows = table_rows(I.metrics_t.splitlines())
        I.metrics_rows = rows[1:] if rows else []
    I.measured = header_value(I.metrics_t, "Measured:") or ""
    # colours
    I.colours, I.retired, I.colour_src = [], [], "none"
    if I.kit_d and I.kit_d.is_dir():
        kit = parse_kit(I.kit_d, rel(I.kit_d) + "/")
        I.colours = kit["brand.md"] + kit["style.md"]
        I.retired = kit["Retired, do not use"]
        if I.colours:
            I.colour_src = rel(I.kit_d) + "/brand.md" if kit["brand.md"] else rel(I.kit_d) + "/style.md"
    if not I.colours:
        pal = section(I.idx_t, "Colour palette", 3) or []
        k, _r = colour_lines("\n".join(pal), rel(I.idx_p) + " (Colour palette)")
        for c in k:
            if c["Colour"] == "unnamed":
                c["Colour"] = "from the design asset checklist"
        I.colours = k
        if k:
            I.colour_src = rel(I.idx_p) + " (Asset Checklist, Colour palette)"
    return I


def counts(I: Inputs) -> dict:
    c = {"pages_built": len(I.built), "pages_by_type": I.by_type, "words_written": I.words,
         "keywords_targeted": len(I.keywords), "old_urls_redirected": len(I.redirects),
         "old_site_pages": len(I.inventory), "post_launch_pages": len(I.post)}
    return c


def count_values(I: Inputs) -> set[str]:
    c = counts(I)
    vals = {c["pages_built"], c["words_written"], c["keywords_targeted"], c["old_urls_redirected"],
            c["old_site_pages"]} | set(c["pages_by_type"].values())
    out = set()
    for v in vals:
        out |= num_forms(str(v))
    return out | FIXED_NUMBERS


def metric_values(I: Inputs) -> set[str]:
    out = set()
    for r in I.metrics_rows:
        for cell in r[1:]:
            for tok in numbers(cell):
                out |= num_forms(tok)
    return out


# ---------------------------------------------------------------- render

def stat_lines(I: Inputs) -> list[str]:
    c = counts(I)
    out = [f"- {c['pages_built']} pages built and launched",
           f"- {fmt(c['words_written'])} words of new page copy"]
    if c["keywords_targeted"]:
        out.append(f"- {c['keywords_targeted']} target keywords researched and mapped to pages")
    if c["old_urls_redirected"]:
        out.append(f"- {c['old_urls_redirected']} old URLs redirected to their new pages")
    loc = c["pages_by_type"].get("Location Pages", 0)
    svc = c["pages_by_type"].get("Service Pages", 0)
    if svc:
        out.append(f"- {svc} dedicated service pages")
    if loc:
        out.append(f"- {loc} new location pages")
    if c["old_site_pages"] and len(out) < 6:
        out.append(f"- {c['old_site_pages']} pages on the old site, replaced in full")
    return out[:6]


def type_phrase(I: Inputs) -> str:
    parts = []
    for g in GROUPS:
        n = I.by_type.get(g, 0)
        if n:
            one, many = GROUP_WORDS[g]
            parts.append(f"{n} {one if n == 1 else many}")
    if len(parts) > 1:
        return ", ".join(parts[:-1]) + " and " + parts[-1]
    return parts[0] if parts else "no pages"


def consent_line(I: Inputs) -> str:
    if I.featured == "yes":
        return f"confirmed ({I.approved_by})" if I.approved_by else "confirmed"
    return "not confirmed"


def render_narrative(I: Inputs, today: str) -> str:
    c = counts(I)
    met = f"{I.rel(I.met_p)} (measured {I.measured})" if I.metrics_t else "none yet (launch version)"
    out = [f"Client: {I.client}", f"Launch: {I.launch}", f"Written: {today}",
           f"Feature consent: {consent_line(I)}",
           f"Approved quotes: {', '.join(I.approved_ids) if I.approved_ids else 'none'}",
           f"Metrics: {met}", "",
           f"> AM: confirm {I.client} agrees to be featured as a WISE case study before this is published "
           "or shared outside WISE. Delete this note and the lines above it when you publish.", "",
           "# [WRITE: headline, one line, specific to this client and what changed; no hype]", "",
           "## Client Snapshot", "",
           f"- Client: {I.client}",
           f"- Website: {I.live or 'not given'}",
           f"- Service area: {I.area or 'not given'}",
           f"- Launched: {I.launch}",
           f"- Old site: {c['old_site_pages']} pages" if I.inventory else "- Old site: none",
           f"- Build: {c['pages_built']} pages", "",
           "[WRITE: two sentences on who the client is and who they serve, from the client context]", "",
           "## The Challenge", "",
           "[WRITE: what the old site lacked and why it mattered to the business, from the context's Website Today, "
           "the Growth Blueprint's Business and Market Overview and the client's own words if a quote is approved]", "",
           "## The Approach", "",
           "[WRITE: the positioning and strategy we chose and why, from the Growth Blueprint's Strategic Positioning "
           "and Growth Strategy and the reference kit's brand.md]", "",
           "## What We Built", "",
           f"- {c['pages_built']} pages: {type_phrase(I)}",
           f"- {fmt(c['words_written'])} words of new page copy across those pages"]
    if c["keywords_targeted"]:
        out.append(f"- {c['keywords_targeted']} target keywords mapped to the pages")
    if c["old_urls_redirected"]:
        out.append(f"- {c['old_urls_redirected']} old URLs redirected to their new pages")
    out += ["", "[WRITE: one short paragraph on the new design and content, naming specific pages]", "", "## Results", ""]
    if I.metrics_t:
        out.append(f"[WRITE: the results measured on {I.measured}, using only the figures in {I.rel(I.met_p)}; "
                   "copy each figure exactly, no percentages or totals the file does not state]")
    else:
        out.append(f"It is too early to report results: the site launched on {I.launch}. "
                   "[WRITE: what we will measure at 90 days, from the Growth Blueprint's Measurement and Next Steps]")
    out += ["", "## In Their Words", ""]
    if I.approved:
        out.append("[WRITE: pick one approved quote below, keep it word for word as a > line, then a line "
                   "with an em dash, the speaker and the business; delete the others]")
        for q in I.approved:
            out += ["", f"> \"{q['Quote']}\"", "", f"\u2014 {q['Speaker']}, {I.client}"]
    else:
        who = I.contact or "the client"
        out.append(f"{QUOTE_NEEDED} no quote is approved for public use yet. Suggested question for the AM to ask "
                   f"{who}: \"[WRITE: one open question about the new site, ending in a question mark]\"")
    out += ["", "## Quick Stats", ""] + stat_lines(I)
    return "\n".join(out) + "\n"


def screenshot_rows(I: Inputs) -> list[str]:
    rows = ["| Page | Page type | Live URL |", "|---|---|---|"]
    seen = set()
    for p in I.built:
        if p["group"] in seen:
            continue
        seen.add(p["group"])
        rows.append(f"| {p['Page']} | {GROUP_WORDS[p['group']][0]} | {I.live}{p['URL']} |")
    return rows


def before_after_rows(I: Inputs) -> list[str]:
    rows = ["| Old page | Old URL | New page | Live URL |", "|---|---|---|---|"]
    titles = {r.get("url", "").rstrip("/"): r.get("title", "") for r in I.inventory}
    names = {p["URL"]: p["Page"] for p in I.build}
    home = [r for r in I.inventory if re.fullmatch(r"https?://[^/]+/?", r.get("url", ""))]
    if home and "/" in names:
        rows.append(f"| {home[0].get('title') or 'Home'} | {home[0]['url']} | {names['/']} | {I.live}/ |")
    for r in I.redirects:
        old = r["Old URL"]
        rows.append(f"| {titles.get(old.rstrip('/'), '') or 'old page'} | {old} | {names.get(r['New URL'], r['New URL'])} | "
                    f"{I.live}{r['New URL']} |")
    return rows


def colour_rows(I: Inputs) -> list[str]:
    if not I.colours:
        return ["GAP: no brand colours in the reference kit or the dev handoff index; ask Design for the palette."]
    rows = ["| Colour | Hex | Use | Source |", "|---|---|---|---|"]
    rows += [f"| {c['Colour']} | {c['Hex']} | {c['Use']} | {c['Source']} |" for c in I.colours]
    return rows


def render_brief(I: Inputs) -> str:
    out = [f"Client: {I.client}", f"Case study: {I.rel(I.out_p)}", f"Live site: {I.live or 'not given'}",
           f"Colours from: {I.colour_src}", "",
           f"# Showcase design brief: {I.client}", "",
           "## Pages to Screenshot", "",
           "Desktop and mobile, full page, from the live site.", ""] + screenshot_rows(I) + [
           "", "## Before and After", "",
           "The old pages are no longer live: take the before shots from a saved copy or the Internet Archive "
           "(web.archive.org) for the old URL.", ""] + before_after_rows(I) + [
           "", "## Brand Colours", ""] + colour_rows(I)
    if I.retired:
        out += ["", "Not to use: " + ", ".join(f"{c['Hex']} ({c['Colour']})" for c in I.retired) + ", marked retired in the kit."]
    out += ["", "## Callout Stats", "",
            "[WRITE: keep 3 or 4 of these, copied from the case study's Quick Stats]"] + stat_lines(I)[:4] + [
            "", "## Layout Suggestion", "",
            "[WRITE: a layout for the showcase page or slide: hero shot, before and after pairs, the callout stats, "
            "the quote or its slot, in WISE's showcase style]"]
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- check

def body_of(text: str) -> str:
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        if ln.startswith("# "):
            return "\n".join(lines[i:])
    return ""


def bullets(lines: list[str] | None) -> list[str]:
    return [ln.strip()[2:].strip() for ln in (lines or []) if ln.strip().startswith(("- ", "* "))]


def first_number(s: str) -> str | None:
    n = numbers(s)
    return n[0] if n else None


def run_check(I: Inputs) -> tuple[list[tuple[str, str, str]], bool]:
    rows: list[tuple[str, str, str]] = []
    def add(name, ok, detail):
        rows.append((name, "PASS" if ok else "FAIL", detail))
    text, brief = read(I.out_p), read(I.brief_p)
    if not I.idx_t or not I.ctx:
        add("inputs", False, "dev handoff index or client context missing")
        return rows, False
    if not text:
        add("case study", False, f"{I.rel(I.out_p)} missing; run scaffold")
        return rows, False
    # header
    want = [f"Client: {I.client}", f"Launch: {I.launch}", None, f"Feature consent: {consent_line(I)}",
            f"Approved quotes: {', '.join(I.approved_ids) if I.approved_ids else 'none'}", None]
    lines = text.splitlines()
    bad = []
    for i, key in enumerate(HEADER):
        got = lines[i] if i < len(lines) else ""
        if not got.startswith(key) or (want[i] and got != want[i]):
            bad.append(want[i] or key)
    add("header", not bad, "6 header lines match the sources" if not bad else "expected: " + "; ".join(bad))
    body = body_of(text)
    pre = text[: len(text) - len(body)] if body else text
    note = [ln for ln in pre.splitlines() if ln.startswith("> AM:") and "featured" in ln.lower()]
    add("consent note", bool(note), "AM note above the headline" if note else "missing the '> AM:' note about agreeing to be featured above the headline")
    heads = re.findall(r"^## (.+)$", body, re.M)
    h1 = re.findall(r"^# (.+)$", body, re.M)
    ok = heads == SECTIONS and len(h1) == 1
    add("sections", ok, "headline and 7 sections in order" if ok else f"want one '# ' headline and {SECTIONS}; got {len(h1)} headline(s) and {heads}")
    left = [ln.strip()[:60] for ln in text.splitlines() if WRITE in ln]
    add("placeholders", not left, "none left" if not left else f"{len(left)} [WRITE: ...] slot(s) left: {left[0]}")
    # numbers
    allowed_counts = count_values(I)
    srcs = [I.ctx, I.bp, I.idx_t, read(I.inv_p), I.metrics_t, read(I.kw_p) if I.kw_p else "", I.launch]
    if I.kit_d:
        srcs += [read(I.kit_d / "brand.md"), read(I.kit_d / "style.md")]
    srcs += [q["Quote"] for q in I.approved]
    pool = number_pool(srcs) | allowed_counts
    stray = sorted({n for n in numbers(body) if not (num_forms(n) & pool)})
    add("numbers", not stray, "every number is a count or in a source file" if not stray else "not a count or in any source: " + ", ".join(stray))
    # each count next to its noun
    tc = {"service": I.by_type.get("Service Pages", 0), "location": I.by_type.get("Location Pages", 0),
          "resource": I.by_type.get("Resource Pages", 0), "about": I.by_type.get("About Page", 0),
          "contact": I.by_type.get("Contact Page", 0)}
    ctx_nums = number_pool([I.ctx])
    wrong = []
    for m in re.finditer(r"(?i)(?<![\w,.])(\d[\d,]*)\s+(?:new |dedicated |local |more )?(service|location|resource|about|contact)\s+pages?\b", body):
        if m.group(1).replace(",", "") != str(tc[m.group(2).lower()]):
            wrong.append(m.group(0))
    for pat, want in ((r"(\d[\d,]*)\s+(?:new |more |old )?(?:target |primary )?keywords?\b", {str(len(I.keywords))}),
                      (r"(\d[\d,]*)\s+(?:old )?(?:URLs?|pages?) (?:were |are )?redirect", {str(len(I.redirects))}),
                      (r"(\d[\d,]*)\s+words\b", {str(I.words)}),
                      (r"(?<![\w,.])(\d[\d,]*)\s+(?:new |live |launched )?pages?\b(?!\s+redirect)",
                       {str(len(I.built)), str(len(I.inventory))} | {n for n in ctx_nums if n.isdigit()})):
        for m in re.finditer("(?i)" + pat, body):
            if m.group(1).replace(",", "") not in want:
                wrong.append(m.group(0))
    add("counts by noun", not wrong, "each count matches its noun" if not wrong else "count does not match what it counts: " + "; ".join(wrong[:4]))
    # what we built
    wwb = "\n".join(section(body, "What We Built") or [])
    c = counts(I)
    need = [str(c["pages_built"]), fmt(c["words_written"])]
    miss = [n for n in need if not re.search(rf"(?<![\d,]){re.escape(n)}(?![\d,])", wwb) and
            not re.search(rf"(?<![\d,]){re.escape(n.replace(',', ''))}(?![\d,])", wwb)]
    add("what we built", not miss, f"{c['pages_built']} pages, {fmt(c['words_written'])} words" if not miss else "missing the count(s): " + ", ".join(miss))
    # quick stats
    qs = bullets(section(body, "Quick Stats"))
    okv = allowed_counts | metric_values(I)
    badqs = [b for b in qs if not first_number(b) or not (num_forms(first_number(b)) & okv)]
    ok = 4 <= len(qs) <= 6 and not badqs
    add("quick stats", ok, f"{len(qs)} stats, each a count" + (" or a measured figure" if I.metrics_t else "") if ok else
        f"need 4 to 6 bullets, each led by a count or a metrics-file figure; {len(qs)} bullets" + (f", bad: {badqs[0][:50]}" if badqs else ""))
    # results
    res = "\n".join(section(body, "Results") or [])
    if I.metrics_t:
        mv = metric_values(I)
        used = [n for n in numbers(res) if num_forms(n) & mv]
        strayr = [n for n in numbers(res) if not (num_forms(n) & (mv | number_pool([I.metrics_t, I.launch]) | FIXED_NUMBERS))]
        ok = bool(used) and not strayr
        add("results", ok, f"{len(used)} measured figure(s) from the metrics file" if ok else
            ("no figure from the metrics file" if not used else "figures not in the metrics file: " + ", ".join(strayr)))
    else:
        low = res.lower()
        strayr = [n for n in numbers(res) if not (num_forms(n) & (number_pool([I.launch]) | FIXED_NUMBERS))]
        ok = "too early" in low and re.search(r"\b90\b", res) and "%" not in res and not strayr
        add("results", bool(ok), "says it is too early and names the 90-day measures" if ok else
            "at launch, Results says it is too early, names what is measured at 90 days, and has no other figures" +
            (f" (stray: {', '.join(strayr)})" if strayr else ""))
    # quote
    itw = "\n".join(section(body, "In Their Words") or [])
    nb = qnorm(body)
    leaked = [q["#"] for q in I.quotes if q not in I.approved and len(qnorm(q["Quote"]).split()) >= 4 and qnorm(q["Quote"]) in nb]
    used_q = [q for q in I.approved if qnorm(q["Quote"]) in qnorm(itw)]
    if leaked:
        add("quote", False, "quote(s) not approved for public use appear: #" + ", #".join(leaked))
    elif I.approved:
        okq = bool(used_q) and any(ln.startswith(">") for ln in itw.splitlines()) and \
            any(q["Speaker"] in itw for q in used_q) and QUOTE_NEEDED not in itw
        add("quote", okq, f"approved quote #{used_q[0]['#']} word for word" if okq else
            "use one approved quote word for word as a > line with the speaker's name")
    else:
        line = [ln for ln in itw.splitlines() if ln.startswith(QUOTE_NEEDED)]
        okq = bool(line) and "?" in line[0] and not any(ln.startswith(">") for ln in itw.splitlines())
        add("quote", okq, "placeholder with a suggested question" if okq else
            f"no approved quote: write the '{QUOTE_NEEDED}' line with a suggested question ending in ?")
    # voice
    def hype_in(t):
        low = t.lower()
        return sorted({h for h in HYPE if re.search(rf"(?<![a-z]){re.escape(h)}(?![a-z])", low)})
    hy = hype_in(body) + [f"{h} (brief)" for h in hype_in(brief)]
    hy += sorted({m.group(0) for m in PROMISE.finditer(body + "\n" + brief)})
    add("no hype", not hy, "no hype words or promises" if not hy else "hype or promise wording: " + ", ".join(hy))
    sd = STRUCTURED.findall(body + "\n" + brief)
    add("no structured data", not sd, "no structured data or schema claim" if not sd else "remove: " + ", ".join(sorted(set(sd))))
    it = sorted(set(m.group(0) for m in INTERNAL.finditer(body)))
    add("no internal terms", not it, "client-facing wording" if not it else "internal terms: " + ", ".join(it))
    wc = word_count(body)
    add("length", wc <= 900, f"{wc} words" if wc <= 900 else f"{wc} words; keep the narrative under 900")
    # brief
    if not brief:
        add("design brief", False, f"{I.rel(I.brief_p)} missing; run scaffold")
        return rows, all(r[1] == "PASS" for r in rows)
    bl = brief.splitlines()
    want = [f"Client: {I.client}", f"Case study: {I.rel(I.out_p)}", f"Live site: {I.live or 'not given'}",
            f"Colours from: {I.colour_src}"]
    badb = [w for i, w in enumerate(want) if i >= len(bl) or bl[i] != w]
    bheads = re.findall(r"^## (.+)$", brief, re.M)
    okb = not badb and bheads == BRIEF_SECTIONS
    add("brief layout", okb, "header and 5 sections in order" if okb else
        (f"header expected: {'; '.join(badb)}" if badb else f"sections must be {BRIEF_SECTIONS}"))
    tabs_bad = []
    for name, want_rows in (("Pages to Screenshot", screenshot_rows(I)), ("Before and After", before_after_rows(I)),
                            ("Brand Colours", colour_rows(I))):
        got = [ln.strip() for ln in (section(brief, name) or []) if ln.strip().startswith(("|", "GAP:"))]
        if got != want_rows:
            tabs_bad.append(name)
    add("brief tables", not tabs_bad, "screenshot, before/after and colour tables match the sources" if not tabs_bad
        else "regenerate (do not edit) the table(s): " + ", ".join(tabs_bad))
    hexes = {"#" + m.group(1).upper() for m in HEX.finditer(brief)}
    okhex = {c["Hex"] for c in I.colours} | {c["Hex"] for c in I.retired}
    badhex = sorted(hexes - okhex)
    add("brief colours", not badhex, "every colour is from the brand sources" if not badhex else "colours no source lists: " + ", ".join(badhex))
    cs = bullets(section(brief, "Callout Stats"))
    qsn = set()
    for b in qs:
        if first_number(b):
            qsn |= num_forms(first_number(b))
    badc = [b for b in cs if not first_number(b) or not (num_forms(first_number(b)) & qsn)]
    okc = 3 <= len(cs) <= 6 and not badc
    add("callout stats", okc, f"{len(cs)} stats, all from Quick Stats" if okc else
        f"need 3 to 6 bullets, each a Quick Stats figure; {len(cs)} bullets" + (f", bad: {badc[0][:50]}" if badc else ""))
    lay = [ln for ln in (section(brief, "Layout Suggestion") or []) if ln.strip()]
    okl = bool(lay) and not any(WRITE in ln for ln in lay)
    add("layout", okl, "written" if okl else "write the layout suggestion")
    leftb = [ln for ln in bl if WRITE in ln]
    if leftb:
        add("brief placeholders", False, f"{len(leftb)} [WRITE: ...] slot(s) left in the brief")
    return rows, all(r[1] == "PASS" for r in rows)


# ---------------------------------------------------------------- commands

def report_inputs(I: Inputs) -> list[str]:
    def st(p, required=False):
        return I.rel(p) if p and p.exists() else ("MISSING" if required else "none")
    out = [f"client context: {st(I.ctx_p, True)}", f"dev handoff index: {st(I.idx_p, True)}",
           f"URL inventory: {st(I.inv_p)}", f"quote bank: {st(I.qb_p)}", f"growth blueprint: {st(I.bp_p)}",
           f"keyword research: {I.rel(I.kw_p) if I.kw_p else 'none'}",
           f"reference kit: {I.rel(I.kit_d) if I.kit_d and I.kit_d.is_dir() else ('several, pass --client-slug' if I.kit_many else 'none')}",
           f"approvals: {st(I.appr_p)} (feature consent: {consent_line(I)}; approved quotes: {', '.join(I.approved_ids) or 'none'})",
           f"metrics: {st(I.met_p)}", f"launch: {I.launch} ({I.launch_src})", f"live site: {I.live or 'not given'}",
           f"colours: {len(I.colours)} from {I.colour_src}"]
    for p in I.unwritten:
        out.append(f"WARNING: Build page {p['Page']} ({p['URL']}) has no content file; it is not counted. Re-run dev-handoff-index if it was built.")
    return out


def cmd_scaffold(a) -> int:
    root = Path(a.root).resolve()
    slug = find_slug(root, a.slug)
    I = gather(root, slug, a.launch, a.client_slug)
    for ln in report_inputs(I):
        print(ln)
    if not I.ctx or not I.idx_t:
        print("REFUSED: the client context and the dev handoff index are both needed; nothing written.")
        return 1
    if I.featured == "no":
        print(f"REFUSED: {I.rel(I.appr_p)} says Featured: no. The client declined to be featured; nothing written.")
        return 1
    if I.launch == "not given":
        print("REFUSED: no launch date. Pass --launch YYYY-MM-DD (ask the PM), or write the go-live email first; nothing written.")
        return 1
    if (I.out_p.exists() or I.brief_p.exists()) and not a.force:
        print(f"REFUSED: {I.rel(I.out_p)} or the design brief already exists; pass --force to start again (it overwrites the prose).")
        return 1
    today = a.date or dt.date.today().isoformat()
    I.out_p.parent.mkdir(parents=True, exist_ok=True)
    I.out_p.write_text(render_narrative(I, today), encoding="utf-8")
    I.brief_p.write_text(render_brief(I), encoding="utf-8")
    print(json.dumps(counts(I)))
    print(f"WROTE {I.rel(I.out_p)}")
    print(f"WROTE {I.rel(I.brief_p)}")
    return 0


def cmd_check(a) -> int:
    root = Path(a.root).resolve()
    slug = find_slug(root, a.slug)
    I = gather(root, slug, a.launch, a.client_slug)
    if I.featured == "no":
        print(f"RESULT: FAIL ({I.rel(I.appr_p)} says Featured: no)")
        return 1
    rows, ok = run_check(I)
    print("| Check | Result | Detail |")
    print("|---|---|---|")
    for r in rows:
        print(f"| {r[0]} | {r[1]} | {r[2].replace('|', '/')} |")
    print("RESULT: PASS" if ok else "RESULT: FAIL")
    return 0 if ok else 1


def cmd_counts(a) -> int:
    root = Path(a.root).resolve()
    slug = find_slug(root, a.slug)
    I = gather(root, slug, a.launch, a.client_slug)
    out = counts(I)
    out["keywords"] = I.keywords
    out["inputs"] = report_inputs(I)
    print(json.dumps(out, indent=2))
    return 0


def cmd_reader(a) -> int:
    kind = a.cmd
    if a.validate:
        data = json.loads(Path(a.validate).read_text(encoding="utf-8"))
        errs = {"index": validate_index, "quotes": validate_quotes, "kit": validate_kit,
                "keywords": validate_list(["primary_keyword"]), "inventory": validate_list(["url", "title"])}[kind](data)
        if errs:
            print("INVALID: " + "; ".join(errs[:10]), file=sys.stderr)
            return 1
        print(f"VALID {kind}")
        return 0
    if not a.path:
        print("usage: give a file (or --validate FILE.json)", file=sys.stderr)
        return 2
    p = Path(a.path)
    if kind == "index":
        data = parse_index(read(p))
        errs = validate_index(data)
    elif kind == "quotes":
        data = parse_quotes(read(p))
        errs = validate_quotes(data)
    elif kind == "keywords":
        data = parse_keywords(read(p))
        errs = validate_list(["primary_keyword"])(data)
    elif kind == "inventory":
        data = parse_inventory(read(p))
        errs = validate_list(["url", "title"])(data)
    else:
        data = parse_kit(p)
        errs = validate_kit(data)
    if errs:
        print("INVALID: " + "; ".join(errs[:10]), file=sys.stderr)
        return 1
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0


def cmd_contract(a) -> int:
    text = read(Path(a.path))
    if not text:
        print("missing file", file=sys.stderr)
        return 1
    out = {k: header_value(text, k) for k in HEADER}
    body = body_of(text)
    out["headings"] = re.findall(r"^## (.+)$", body, re.M)
    out["Quick Stats"] = bullets(section(body, "Quick Stats"))
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("scaffold", "check", "counts"):
        s = sub.add_parser(name)
        s.add_argument("--slug")
        s.add_argument("--root", default=".")
        s.add_argument("--launch")
        s.add_argument("--client-slug")
        if name == "scaffold":
            s.add_argument("--date")
            s.add_argument("--force", action="store_true")
    for name in ("index", "quotes", "kit", "keywords", "inventory"):
        s = sub.add_parser(name)
        s.add_argument("path", nargs="?")
        s.add_argument("--validate")
    s = sub.add_parser("contract")
    s.add_argument("path")
    a = ap.parse_args()
    if getattr(a, "launch", None) and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", a.launch or ""):
        print("usage: --launch must be YYYY-MM-DD", file=sys.stderr)
        return 2
    return {"scaffold": cmd_scaffold, "check": cmd_check, "counts": cmd_counts, "contract": cmd_contract}.get(
        a.cmd, cmd_reader)(a)


if __name__ == "__main__":
    sys.exit(main())
