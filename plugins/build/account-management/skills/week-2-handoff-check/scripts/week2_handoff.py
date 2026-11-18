#!/usr/bin/env python3
"""End-of-Week-2 go/no-go check for a website build.

Usage:
  python3 week2_handoff.py run FOLDER [--slug SLUG] [--date YYYY-MM-DD] [--dry-run]
  python3 week2_handoff.py sitemap REPORT.md            print the pages the check reads from a sitemap report (JSON)
  python3 week2_handoff.py sitemap --validate FILE.json check a JSON file has that shape
  python3 week2_handoff.py page CONTENT_DIR             print what the check reads from one page folder (JSON)
  python3 week2_handoff.py page --validate FILE.json

`run` reads the client's working folder, checks every Week 2 deliverable and writes
handoff/<slug>/<slug>-week-2-handoff.md: a `| Item | Required | Status | Path | Note |` table,
the blocking and non-blocking lists, and a last line of GO or NO-GO. It never edits any other file.
Exit 0 on GO, 1 on NO-GO, 2 on a usage error. Status values: present, missing, stale, n/a.
Standard library only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import zipfile
from pathlib import Path

BLUEPRINT_SECTIONS = ["Executive Summary", "Business and Market Overview", "Competitive Analysis",
                      "Strategic Positioning", "Keyword Opportunity", "Site Architecture and Content Plan",
                      "Growth Strategy", "Measurement and Next Steps"]
STRATEGY_SUBSECTIONS = ["Phase 1", "Phase 2", "Phase 3", "Trajectory"]
BRIEFING_SECTIONS = ["Executive Summary", "Key Strategic Bets", "Numbers the AM Should Know",
                     "Anticipated Client Questions", "Calibration Framing"]
DESIGN_SECTIONS = ["Page Types", "Open Questions", "Hand-off", "Sources"]
DECK_HIT_CHECKS = ["em-dashes", "prescribe", "figures", "quotes"]
PAGE_FILES = ["article.md", "metadata.md", "article.html", "qa_report.md", "handoff.md"]
GOOD_BRIEF = {"DONE", "DONE_WITH_CONCERNS"}
# URL-map rows the content step never writes, read from the URL path only (a bakery's /cookies/ page
# is a real page): legal and utility pages, the blog archive and posts.
NOT_WRITTEN = re.compile(r"(?i)^/(blog(/.*)?|privacy([-_].*)?|terms([-_].*)?|cookie[-_]policy|cookies[-_]policy"
                         r"|legal(/.*)?|404|sitemap([-_.].*)?)/?$")
FLAG = re.compile(r"\[(NEEDS INPUT|NEEDS SOURCE|CLIENT INPUT NEEDED)\b[^\]]*\]")
COUNT_LINE = re.compile(r"countable pages (\d+) / SOW cap (\d+|Unknown)", re.I)
OWNERS = {
    "week1": "PM, week-1-handoff-check",
    "competitor": "SEO, competitor-analysis",
    "blueprint": "SEO, growth-blueprint",
    "deck": "SEO, blueprint-deck",
    "sitemap": "SEO, site-structure-optimizer",
    "brief": "Content, content-brief",
    "page": "Content, seo-content-writer",
    "design": "Design, page-type-design-briefs",
    "email": "AM, week-2-client-email",
    "feedback": "AM, client-feedback",
}


class Row:
    def __init__(self, item: str, required: bool, path: str):
        self.item, self.required, self.path = item, required, path
        self.status, self.note = "present", ""

    def set(self, status: str, note: str = "") -> "Row":
        self.status, self.note = status, note
        return self

    @property
    def blocking(self) -> bool:
        return self.required and self.status in ("missing", "stale")


# ---------- small readers

def read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def rel(root: Path, p: Path) -> str:
    try:
        return p.relative_to(root).as_posix()
    except ValueError:
        return p.as_posix()


def line_value(text: str, key: str) -> str:
    m = re.search(rf"(?im)^\s*{re.escape(key)}\s*:\s*(.+?)\s*$", text)
    return m.group(1) if m else ""


def h2s(text: str) -> list[str]:
    return [m.group(1).strip() for m in re.finditer(r"(?m)^##\s+(.+?)\s*$", text)]


def sections(text: str) -> dict[str, str]:
    """`##` heading -> its body, up to the next `##` heading."""
    parts = re.split(r"(?m)^##\s+(.+?)\s*$", text)
    return {parts[i].strip(): parts[i + 1] for i in range(1, len(parts) - 1, 2)}


def table_after(text: str, header_start: str) -> list[list[str]]:
    """Data rows of the first table whose header line starts with `header_start`."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if re.sub(r"\s+", " ", line.strip()).lower().startswith(header_start.lower()):
            rows = []
            for row in lines[i + 1:]:
                s = row.strip()
                if not s.startswith("|"):
                    break
                if re.fullmatch(r"\|[\s:|-]+\|", s):
                    continue
                rows.append([c.strip() for c in s.strip("|").split("|")])
            return rows
    return []


def front_matter(text: str) -> dict[str, str]:
    m = re.match(r"﻿?---\s*\n(.*?)\n---", text, re.S)
    out: dict[str, str] = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line and not line[:1].isspace():
                k, v = line.split(":", 1)
                out[k.strip().lower()] = v.strip().strip("\"'")
    return out


def last_named(folder: Path, pattern: str = "*.md") -> list[Path]:
    return sorted(folder.glob(pattern), key=lambda p: p.name) if folder.is_dir() else []


def date_of(value: str) -> dt.date | None:
    m = re.search(r"\d{4}-\d{2}-\d{2}", value or "")
    try:
        return dt.date.fromisoformat(m.group(0)) if m else None
    except ValueError:
        return None


def url_slug(url: str) -> str:
    path = re.sub(r"^https?://[^/]+", "", url.strip()).split("?")[0].split("#")[0].strip("/")
    return path.split("/")[-1] if path else "home"


def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


# ---------- the sitemap report

def parse_sitemap(text: str) -> dict:
    counts = COUNT_LINE.findall(text)
    pages = []
    for cells in table_after(text, "| Page | URL |"):
        if len(cells) < 2 or not cells[1]:
            continue
        name, url = cells[0], cells[1]
        out_of_scope = "(not in SOW scope)" in " ".join(cells)
        path = "/" + re.sub(r"^https?://[^/]+", "", url.strip()).split("?")[0].split("#")[0].strip("/")
        skip = bool(NOT_WRITTEN.match(path))
        pages.append({"page": name, "url": url, "url_slug": url_slug(url),
                      "not_in_sow_scope": out_of_scope, "checked": not skip})
    last = counts[-1] if counts else None
    return {
        "countable pages N / SOW cap M": [int(last[0]), None if last[1].lower() == "unknown" else int(last[1])] if last else None,
        "(not in SOW scope)": [p["page"] for p in pages if p["not_in_sow_scope"]],
        "pages": pages,
    }


def find_sitemap(root: Path) -> tuple[Path | None, dict]:
    for p in reversed(last_named(root / "seo-reports" / "site-structure-optimizer")):
        data = parse_sitemap(read(p))
        if data["countable pages N / SOW cap M"] and data["pages"]:
            return p, data
    return None, {}


# ---------- briefs and pages

def brief_slug(path: Path, fm: dict[str, str], text: str) -> str:
    url = fm.get("page_url") or line_value(text, "page_url") or fm.get("url", "")
    if url.startswith(("/", "http")):
        return url_slug(url)
    if re.match(r"home\s?page", fm.get("format", ""), re.I):
        return "home"
    kw = fm.get("primary_keyword", "")
    return slugify(kw) if kw else slugify(path.stem)


def load_briefs(root: Path) -> dict[str, tuple[Path, dict[str, str]]]:
    out: dict[str, tuple[Path, dict[str, str]]] = {}
    for p in last_named(root / "research" / "content-briefs"):
        if re.search(r"\.v\d+\.md$", p.name):
            continue  # an older version kept beside the current brief
        text = read(p)
        fm = front_matter(text)
        out.setdefault(brief_slug(p, fm, text), (p, fm))
    return out


def read_page(folder: Path) -> dict:
    qa, handoff = read(folder / "qa_report.md"), read(folder / "handoff.md")
    vm = re.search(r"(?m)^VERDICT:\s*([A-Z_]+)", qa)
    fm = re.search(r"Open flags:\s*(\d+)", qa)
    flags = sorted({m.group(0) for m in FLAG.finditer(handoff)})
    return {
        "content/<url-slug>/": folder.name + "/",
        "VERDICT:": vm.group(1) if vm else "",
        "qa_report.md": {"open_flags": int(fm.group(1)) if fm else None},
        "handoff.md": flags,
        "files_missing": [f for f in PAGE_FILES if not (folder / f).is_file()],
    }


# ---------- the checks

def check_week1(root: Path, slug: str) -> Row:
    p = root / "handoff" / slug / f"{slug}-week-1-handoff.md"
    r = Row("Week 1 handoff", True, rel(root, p))
    if not p.is_file():
        return r.set("missing", f"no Week 1 handoff check on file; run week-1-handoff-check first ({OWNERS['week1']})")
    lines = [ln.strip() for ln in read(p).splitlines() if ln.strip()]
    last = lines[-1] if lines else ""
    if last != "GO":
        return r.set("missing", f"the Week 1 check ends {last or 'with nothing'}, not GO: clear its blocking items "
                                f"and run it again ({OWNERS['week1']})")
    checked = line_value(read(p), "Checked")
    return r.set("present", f"GO, checked {checked}" if checked else "GO")


def check_competitor(root: Path, slug: str) -> Row:
    hits = [p for p in last_named(root / "seo-reports" / "competitor-analysis") if read(p).strip()]
    if not hits:
        return Row("Competitor report", True, "seo-reports/competitor-analysis/").set(
            "missing", f"no saved competitor report ({OWNERS['competitor']})")
    return Row("Competitor report", True, rel(root, hits[-1]))


def check_blueprint(root: Path, slug: str) -> tuple[Row, str]:
    p = root / "blueprint" / slug / f"{slug}-growth-blueprint.md"
    r = Row("Growth Blueprint", True, rel(root, p))
    text = read(p)
    if not p.is_file():
        return r.set("missing", f"not written ({OWNERS['blueprint']})"), ""
    found = [h for h in h2s(text) if h in BLUEPRINT_SECTIONS]
    problems = []
    if found != BLUEPRINT_SECTIONS:
        lacking = [s for s in BLUEPRINT_SECTIONS if s not in found]
        problems.append("lacks " + ", ".join(lacking) if lacking else "sections out of order")
    body = sections(text)
    no_source = [s for s in BLUEPRINT_SECTIONS if s in body and not re.search(r"(?m)^Source:", body[s])]
    if no_source:
        problems.append("no Source: line in " + ", ".join(no_source))
    subs = re.findall(r"(?m)^###\s+(.+?)\s*$", body.get("Growth Strategy", ""))
    lacking_subs = [s for s in STRATEGY_SUBSECTIONS if not any(x.startswith(s) for x in subs)]
    if "Growth Strategy" in body and lacking_subs:
        problems.append("Growth Strategy lacks " + ", ".join(lacking_subs))
    if "[WRITE:" in text:
        problems.append(f"{text.count('[WRITE:')} [WRITE: ...] placeholder(s) left")
    if problems:
        return r.set("missing", "incomplete: " + "; ".join(problems) + f" ({OWNERS['blueprint']})"), text
    open_flags = len(re.findall(r"\[NEEDS INPUT", text))
    date = line_value(text, "Date")
    note = f"dated {date}" if date else ""
    if open_flags:
        note += f"{'; ' if note else ''}{open_flags} [NEEDS INPUT] line(s) open"
    return r.set("present", note), text


def check_briefing(root: Path, slug: str) -> Row:
    p = root / "blueprint" / slug / f"{slug}-am-briefing.md"
    r = Row("AM Briefing", True, rel(root, p))
    if not p.is_file():
        return r.set("missing", f"not written ({OWNERS['blueprint']})")
    text = read(p)
    lacking = [s for s in BRIEFING_SECTIONS if s not in h2s(text)]
    problems = (["lacks " + ", ".join(lacking)] if lacking else []) + (["[WRITE: ...] placeholder left"] if "[WRITE:" in text else [])
    if problems:
        return r.set("missing", "incomplete: " + "; ".join(problems) + f" ({OWNERS['blueprint']})")
    return r


def check_deck(root: Path, slug: str) -> Row:
    p = root / "blueprint" / slug / f"{slug}-growth-blueprint-deck.pptx"
    r = Row("Blueprint deck", True, rel(root, p))
    if not p.is_file():
        return r.set("missing", f"not built ({OWNERS['deck']})")
    try:
        with zipfile.ZipFile(p) as z:
            ok = "ppt/presentation.xml" in z.namelist()
    except (zipfile.BadZipFile, OSError):
        ok = False
    if not ok:
        return r.set("missing", f"not a readable .pptx; rebuild it ({OWNERS['deck']})")
    return r


def check_compliance(root: Path, slug: str, blueprint_text: str) -> Row:
    p = root / "blueprint" / slug / f"{slug}-deck-compliance.md"
    r = Row("Deck compliance", True, rel(root, p))
    if not p.is_file():
        return r.set("missing", f"no compliance file; build the deck with the script ({OWNERS['deck']})")
    text = read(p)
    result = line_value(text, "RESULT")
    checks = {row[0].lower(): row for row in table_after(text, "| Check | Result |") if len(row) >= 2}
    failing = []
    for name in DECK_HIT_CHECKS:
        row = checks.get(name)
        if not row:
            failing.append(f"no {name} row")
        elif row[1].upper() != "PASS":
            failing.append(f"{name} {row[2] if len(row) > 2 else row[1]}")
    hits = table_after(text, "| Slide | Check |")
    if result not in ("PASS", "NEEDS_INPUT") or failing or hits:
        detail = [f"RESULT: {result or 'none'}"] + failing + ([f"{len(hits)} hit(s) listed"] if hits and not failing else [])
        return r.set("missing", "; ".join(detail) + f"; fix the slide plan and rebuild ({OWNERS['deck']})")
    checked, bp_date = date_of(line_value(text, "Checked")), date_of(line_value(blueprint_text, "Date"))
    if checked and bp_date and bp_date > checked:
        return r.set("stale", f"the Blueprint is dated {bp_date} but the deck was checked {checked}: rebuild the deck "
                              f"from the current Blueprint ({OWNERS['deck']})")
    note = "zero hits"
    if result == "NEEDS_INPUT":
        open_row = checks.get("needs input")
        note += "; RESULT: NEEDS_INPUT" + (f", {open_row[2]}" if open_row and len(open_row) > 2 else "")
    return r.set("present", note)


def check_pages(root: Path, sitemap: dict) -> tuple[list[Row], list[str]]:
    briefs = load_briefs(root)
    rows, wanted = [], set()
    for pg in sitemap["pages"]:
        if not pg["checked"]:
            continue
        slug = pg["url_slug"]
        wanted.add(slug)
        folder = root / "content" / slug
        r = Row(f"Page: {pg['page']}", True, f"content/{slug}/")
        rows.append(r)
        brief = briefs.get(slug)
        page = read_page(folder) if folder.is_dir() else None
        problems = []
        if not brief:
            problems.append(f"no brief with page_url {pg['url']} in research/content-briefs/ ({OWNERS['brief']})")
        elif front_matter(read(brief[0])).get("status", "").upper() not in GOOD_BRIEF:
            st = brief[1].get("status") or "not set"
            problems.append(f"brief {brief[0].name} has status {st} ({OWNERS['brief']})")
        if page is None or "article.md" in page["files_missing"]:
            problems.append(f"page not written: no content/{slug}/article.md ({OWNERS['page']}; its batch mode writes every missing page)")
        elif page["files_missing"]:
            problems.append(f"page lacks {', '.join(page['files_missing'])} ({OWNERS['page']})")
        elif page["VERDICT:"] not in ("READY", "NEEDS_INPUT"):
            problems.append(f"VERDICT is {page['VERDICT:'] or 'missing'}, not READY or NEEDS_INPUT ({OWNERS['page']})")
        elif page["VERDICT:"] == "NEEDS_INPUT" and not page["handoff.md"]:
            problems.append("VERDICT: NEEDS_INPUT but handoff.md lists no client input to ask for: "
                            f"list each open flag in its Open Flags table ({OWNERS['page']})")
        if problems:
            r.set("missing", "; ".join(problems))
            continue
        note = f"brief {brief[0].name}; VERDICT: {page['VERDICT:']}"
        if page["handoff.md"]:
            note += f", {len(page['handoff.md'])} client input(s) listed in handoff.md"
        r.set("present", note)
    extra = sorted({f"content/{p.name}/" for p in (root / "content").glob("*/") if p.is_dir() and p.name not in wanted}
                   | {f"research/content-briefs/{b[0].name}" for s, b in briefs.items() if s not in wanted})
    return rows, extra


def check_design(root: Path, slug: str, sitemap: dict) -> Row:
    p = root / "design" / slug / f"{slug}-page-type-design-briefs.md"
    r = Row("Page-type design briefs", True, rel(root, p))
    if not p.is_file():
        return r.set("missing", f"not written ({OWNERS['design']})")
    text = read(p)
    lacking = [s for s in DESIGN_SECTIONS if s not in h2s(text)]
    problems = (["lacks " + ", ".join(lacking)] if lacking else []) + (["<fill> left in it"] if "<fill>" in text else [])
    if problems:
        return r.set("missing", "incomplete: " + "; ".join(problems) + f" ({OWNERS['design']})")
    planned = {pg["url_slug"] for pg in sitemap.get("pages", []) if pg["checked"]}
    written = [s for s in sorted(planned) if s != "home" and (root / "content" / s / "article.md").is_file()]
    unlisted = [f"content/{s}/" for s in written if f"content/{s}/" not in text]
    listed = sorted(set(re.findall(r"`(content/[^/`]+)/article\.md`", text)))
    # A listed sitemap page that is not written yet is already a blocking page row; only pages
    # dropped from the sitemap and deleted make the design brief stale.
    gone = [f"{x}/" for x in listed if not (root / x / "article.md").is_file() and x.split("/", 1)[1] not in planned]
    if unlisted or gone:
        parts = (["does not list " + ", ".join(unlisted)] if unlisted else []) + (["lists pages that no longer exist: " + ", ".join(gone)] if gone else [])
        return r.set("stale", "written before the pages changed: " + "; ".join(parts) + f"; rerun it ({OWNERS['design']})")
    direction = line_value(text, "Homepage direction")
    return r.set("present", f"homepage direction: {direction}" if direction else "")


def check_email(root: Path, slug: str) -> tuple[Row, str]:
    p = root / "emails" / slug / f"{slug}-week-2-email.md"
    r = Row("Week 2 client email", True, rel(root, p))
    if not p.is_file():
        return r.set("missing", f"not drafted ({OWNERS['email']})"), ""
    text = read(p)
    reply_by = line_value(text, "Reply by")
    problems = ([] if re.search(r"(?m)^Subject:", text) else ["no Subject: line"]) + \
               ([] if date_of(reply_by) else ["no Reply by: date"])
    if problems:
        return r.set("missing", "incomplete: " + "; ".join(problems) + f" ({OWNERS['email']})"), reply_by
    return r.set("present", f"reply by {date_of(reply_by)}"), str(date_of(reply_by))


def check_feedback(root: Path, slug: str, reply_by: str, today: dt.date) -> Row:
    folder = root / "feedback" / slug
    replies = [p for p in last_named(folder, "*-feedback.md") if line_value(read(p), "Week") == "2"]
    if replies:
        p = replies[-1]
        r = Row("Client feedback", False, rel(root, p))
        held = re.findall(r"(?m)^- #\d+", sections(read(p)).get("SEO Review", ""))
        if held:
            return r.set("present", f"reply logged; {len(held)} strategy item(s) wait for SEO sign-off before the "
                                    "reply goes; Week 3 does not wait for them")
        return r.set("present", "reply logged; no strategy items")
    nudges = last_named(folder, "*-week-2-nudge.md")
    if nudges:
        return Row("Client feedback", False, rel(root, nudges[-1])).set(
            "present", "no reply by the reply-by date; nudge drafted, Week 3 proceeds with the Blueprint as is")
    r = Row("Client feedback", False, f"feedback/{slug}/")
    due = date_of(reply_by)
    if due and today > due:
        return r.set("missing", f"no reply logged and the reply-by date {due} has passed: draft the nudge "
                                f"({OWNERS['feedback']}); Week 3 does not wait")
    when = f" (reply due by {due})" if due else ""
    return r.set("missing", f"no reply logged yet{when}; Week 3 does not wait")


def find_slug(root: Path, given: str | None) -> str:
    if given:
        return given
    found = sorted(p.name for p in (root / "kickoff").glob("*/") if (p / f"{p.name}-context.md").is_file())
    if len(found) == 1:
        return found[0]
    raise SystemExit("ERROR: no kickoff/<slug>/<slug>-context.md found; pass --slug" if not found else
                     "ERROR: several clients under kickoff/ (" + ", ".join(found) + "); pass --slug")


def build(root: Path, slug: str, today: dt.date) -> tuple[str, list[Row]]:
    client = line_value(read(root / "kickoff" / slug / f"{slug}-context.md"), "Client") or slug
    rows = [check_week1(root, slug), check_competitor(root, slug)]
    bp_row, bp_text = check_blueprint(root, slug)
    rows += [bp_row, check_briefing(root, slug), check_deck(root, slug), check_compliance(root, slug, bp_text)]
    sm_path, sitemap = find_sitemap(root)
    if not sm_path:
        rows.append(Row("Sitemap report", True, "seo-reports/site-structure-optimizer/").set(
            "missing", "no report with a `countable pages N / SOW cap M` line and a URL map, so the pages cannot be "
                       f"compared ({OWNERS['sitemap']})"))
        page_rows, extra = [], []
    else:
        n, cap = sitemap["countable pages N / SOW cap M"]
        page_rows, extra = check_pages(root, sitemap)
        sm = Row("Sitemap report", True, rel(root, sm_path))
        skipped = [p["page"] for p in sitemap["pages"] if not p["checked"]]
        note = f"{len(page_rows)} pages to write (countable pages {n} / SOW cap {cap if cap is not None else 'Unknown'})"
        if skipped:
            note += "; not written by the content step: " + ", ".join(skipped)
        if extra:
            note += "; not in the sitemap: " + ", ".join(extra)
        seen: dict[str, str] = {}
        clashes = []
        for p in sitemap["pages"]:
            if p["checked"] and p["url_slug"] in seen:
                clashes.append(f"{seen[p['url_slug']]} and {p['url']} both map to content/{p['url_slug']}/")
            seen.setdefault(p["url_slug"], p["url"])
        if clashes:
            sm.set("missing", note + "; " + "; ".join(clashes) + f": give one of them its own last URL segment "
                   f"({OWNERS['sitemap']})")
        elif cap is not None and n > cap:
            sm.set("missing", note + f"; over the scope cap ({OWNERS['sitemap']})")
        else:
            sm.set("present", note)
        rows.append(sm)
    rows += page_rows
    rows.append(check_design(root, slug, sitemap))
    email_row, reply_by = check_email(root, slug)
    rows += [email_row, check_feedback(root, slug, reply_by, today)]
    return client, rows


def render(client: str, date: str, rows: list[Row]) -> str:
    out = [f"Client: {client}", f"Checked: {date}", "", f"# Week 2 handoff check for {client}", "",
           "| Item | Required | Status | Path | Note |", "|---|---|---|---|---|"]
    for r in rows:
        out.append(f"| {r.item} | {'yes' if r.required else 'no'} | {r.status} | {r.path} | {r.note.replace('|', '/')} |")
    block = [r for r in rows if r.blocking]
    out += ["", "## Blocking", ""]
    out += [f"- {r.item} ({r.status}): {r.note}" for r in block] or ["- None. Every required item is present."]
    follow = [r for r in rows if not r.required and r.status in ("missing", "stale")]
    out += ["", "## Not blocking", ""]
    out += [f"- {r.item} ({r.status}): {r.note}" for r in follow] or ["- None."]
    out += ["", "NO-GO" if block else "GO"]
    return "\n".join(out) + "\n"


# ---------- contract helpers

def validate_sitemap(data: dict) -> list[str]:
    errs = []
    cnt = data.get("countable pages N / SOW cap M")
    if not (isinstance(cnt, list) and len(cnt) == 2 and isinstance(cnt[0], int)):
        errs.append("`countable pages N / SOW cap M` must be [N, M or null]")
    if not isinstance(data.get("(not in SOW scope)"), list):
        errs.append("`(not in SOW scope)` must be a list of page names")
    pages = data.get("pages")
    if not isinstance(pages, list) or not pages:
        errs.append("`pages` must be a non-empty list")
    else:
        for p in pages:
            if not all(k in p for k in ("page", "url", "url_slug", "checked")):
                errs.append(f"page row lacks page/url/url_slug/checked: {p}")
    return errs


def validate_page(data: dict) -> list[str]:
    errs = []
    if not str(data.get("content/<url-slug>/", "")).endswith("/"):
        errs.append("`content/<url-slug>/` must be the folder name with a trailing slash")
    if data.get("VERDICT:") not in ("READY", "NEEDS_INPUT", "FIX"):
        errs.append("`VERDICT:` must be READY, NEEDS_INPUT or FIX")
    if not isinstance(data.get("qa_report.md"), dict):
        errs.append("`qa_report.md` must be an object")
    if not isinstance(data.get("handoff.md"), list):
        errs.append("`handoff.md` must be a list of flags")
    if data.get("VERDICT:") == "NEEDS_INPUT" and not data.get("handoff.md"):
        errs.append("a NEEDS_INPUT page must list its flags in handoff.md")
    return errs


def contract(kind: str, target: str, validate: bool) -> int:
    p = Path(target)
    if validate:
        try:
            data = json.loads(read(p))
        except json.JSONDecodeError as e:
            print(f"INVALID: {e}")
            return 1
        errs = validate_sitemap(data) if kind == "sitemap" else validate_page(data)
        print("\n".join(f"INVALID: {e}" for e in errs) or "OK")
        return 1 if errs else 0
    if kind == "sitemap":
        data = parse_sitemap(read(p))
    else:
        data = read_page(p)
        data.pop("files_missing")
    print(json.dumps(data, indent=2))
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run")
    run.add_argument("folder")
    run.add_argument("--slug")
    run.add_argument("--date", default=dt.date.today().isoformat())
    run.add_argument("--dry-run", action="store_true")
    for kind in ("sitemap", "page"):
        c = sub.add_parser(kind)
        c.add_argument("target")
        c.add_argument("--validate", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd in ("sitemap", "page"):
        return contract(a.cmd, a.target, a.validate)

    root = Path(a.folder)
    today = date_of(a.date)
    if not root.is_dir() or not today:
        print(f"ERROR: {root} is not a folder" if not root.is_dir() else f"ERROR: --date {a.date} is not YYYY-MM-DD")
        return 2
    try:
        slug = find_slug(root, a.slug)
    except SystemExit as e:
        print(e)
        return 2
    if not (root / "kickoff" / slug / f"{slug}-context.md").is_file():
        print(f"ERROR: kickoff/{slug}/{slug}-context.md not found; this is not a client working folder")
        return 2
    client, rows = build(root, slug, today)
    report = render(client, today.isoformat(), rows)
    if not a.dry_run:
        out = root / "handoff" / slug / f"{slug}-week-2-handoff.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report, encoding="utf-8")
        print(f"Wrote {rel(root, out)}\n")
    print(report, end="")
    return 1 if any(r.blocking for r in rows) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
