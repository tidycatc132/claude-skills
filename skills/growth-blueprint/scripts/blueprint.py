#!/usr/bin/env python3
"""Growth Blueprint scaffold and checker for the growth-blueprint skill. Standard library only.

Run every command as its own plain python3 command, from the client's working folder
(or pass --root). Paths below are relative to that folder.

Commands
  scaffold --slug SLUG     write blueprint/<slug>/<slug>-growth-blueprint.md and
                           blueprint/<slug>/<slug>-am-briefing.md with the fixed sections,
                           the copied Keyword Opportunity and Site Architecture sections
                           already filled, a Source: line per section, and [WRITE: ...]
                           placeholders for the prose. Refuses to overwrite without --force.
  check --slug SLUG        check both files; prints a table and RESULT: PASS | NEEDS_INPUT | FAIL
                           (exit 0, 0, 1)
  keywords CSV             print the tier rows read from a keyword-research scored CSV (JSON)
  sitemap-targets CSV      print the rows read from a site-structure-optimizer targets CSV (JSON)

Input overrides (scaffold and check): --client-slug, --keywords (scored CSV),
--keyword-report, --sitemap, --sitemap-targets, --competitors.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import sys
from pathlib import Path

BLUEPRINT_SECTIONS = [
    "Executive Summary",
    "Business and Market Overview",
    "Competitive Analysis",
    "Strategic Positioning",
    "Keyword Opportunity",
    "Site Architecture and Content Plan",
    "Growth Strategy",
    "Measurement and Next Steps",
]
BUILT = ("Keyword Opportunity", "Site Architecture and Content Plan")
GROWTH_SUBSECTIONS = ["Phase 1", "Phase 2", "Phase 3", "Trajectory"]
BRIEFING_SECTIONS = [
    "Executive Summary",
    "Key Strategic Bets",
    "Numbers the AM Should Know",
    "Anticipated Client Questions",
    "Calibration Framing",
]
KIT_FILES = ["brand.md", "voice.md", "style.md", "audience.md", "compliance.md"]
KEYWORD_COLUMNS = ["keyword", "volume", "kd", "intent", "funnel", "relevance", "trend", "cpc",
                   "position", "impressions", "clicks", "source", "priority_score", "tier",
                   "intent_value", "opportunity_score", "bucket", "impact", "confidence",
                   "impact_confidence"]
TARGET_COLUMNS = ["page_slug", "primary_keyword", "secondary_keywords", "intent", "funnel_stage",
                  "pillar", "cluster_role", "geo_format", "priority_tier", "opportunity_bucket",
                  "volume", "kd", "existing_url", "source"]
TIER_TITLES = {
    1: "Tier 1: target in the new build",
    2: "Tier 2: target in months 1 to 3 after launch",
    3: "Tier 3: long-term authority, months 4 to 6 and beyond",
}
TIER_CAP = 15
UNCOUNTED = ("The home page, contact page, 404 page, privacy and terms pages and blog posts are part "
             "of the site but are not counted against the scope, so the table below lists more rows.")
ACTIONS = {"new-page": "new page", "revise": "revise", "consolidate": "consolidate"}
JARGON = [r"(?<!\d)(?<!\d )\bAM\b", r"\b(?:TOFU|MOFU|BOFU)\b", r"\bP[0-3]\b", r"\bslug\b", r"NEEDS_INPUT",
          r"\bSE Ranking\b"]
BRIEFING_MAX_WORDS = 500
NEEDS = re.compile(r"\[NEEDS INPUT:[^\]]*\]")
WRITE = re.compile(r"\[WRITE:[^\]]*\]")


class InputError(Exception):
    pass


# ---------- reading inputs ----------

def read(p: Path) -> str:
    return p.read_text(encoding="utf-8-sig").replace("\r\n", "\n")


def last_named(folder: Path, pattern: str, exclude: tuple[str, ...] = ()) -> Path | None:
    if not folder.is_dir():
        return None
    files = sorted(f for f in folder.glob(pattern) if f.is_file() and not f.name.endswith(exclude))
    return files[-1] if files else None


def last_architecture_report(folder: Path) -> Path | None:
    """The last-named sitemap report with a countable-pages line (architecture mode); linking-mode
    reports in the same folder are skipped. Falls back to the last-named report."""
    if not folder.is_dir():
        return None
    files = sorted(f for f in folder.glob("*.md") if f.is_file())
    arch = [f for f in files if COUNTABLE.search(read(f))]
    return (arch or files or [None])[-1]


def rel(root: Path, p: Path | None) -> str:
    if p is None:
        return ""
    try:
        return p.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return p.as_posix()


def find_inputs(root: Path, slug: str, a) -> dict:
    k = root / "kickoff" / slug
    cref = root / "client-reference"
    cslug = a.client_slug
    if not cslug and cref.is_dir():
        dirs = sorted(d.name for d in cref.iterdir() if d.is_dir())
        if len(dirs) == 1:
            cslug = dirs[0]
        elif slug in dirs:
            cslug = slug
    kw_report = Path(root, a.keyword_report) if a.keyword_report else last_named(
        root / "research" / "keyword-research", "*.md")
    kw_csv = Path(root, a.keywords) if a.keywords else None
    if kw_csv is None and kw_report is not None:
        cand = kw_report.with_name(kw_report.stem + "-scored.csv")
        kw_csv = cand if cand.exists() else None
    if kw_csv is None:
        kw_csv = last_named(root / "research" / "keyword-research", "*-scored.csv")
    sitemap = Path(root, a.sitemap) if a.sitemap else last_architecture_report(
        root / "seo-reports" / "site-structure-optimizer")
    targets = Path(root, a.sitemap_targets) if a.sitemap_targets else None
    if targets is None and sitemap is not None:
        cand = sitemap.with_name(sitemap.stem + "-targets.csv")
        targets = cand if cand.exists() else None
    comp = Path(root, a.competitors) if a.competitors else last_named(
        root / "seo-reports" / "competitor-analysis", "*.md")
    found = {
        "context": k / f"{slug}-context.md",
        "package": k / f"{slug}-blueprint-input-package.md",
        "quotes": k / f"{slug}-quote-bank.md",
        "keyword_report": kw_report,
        "keywords": kw_csv,
        "sitemap": sitemap,
        "targets": targets,
        "competitors": comp,
    }
    for f in KIT_FILES:
        found["kit:" + f] = (cref / cslug / f) if cslug else None
    return {key: (p if p is not None and p.exists() else None) for key, p in found.items()}


def client_name(ctx: Path | None, slug: str) -> str:
    if ctx:
        m = re.search(r"(?m)^Client:\s*(.+?)\s*$", read(ctx))
        if m:
            return m.group(1)
    return slug


def scope_cap(ctx: Path | None):
    """Return int, 'unknown', or None when the context has no SOW pages line."""
    if not ctx:
        return None
    m = re.search(r"(?mi)^\s*-?\s*SOW pages:\s*(\d+|unknown)", read(ctx))
    if not m:
        return None
    return int(m.group(1)) if m.group(1).isdigit() else "unknown"


def read_keywords(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
        header = rows[0].keys() if rows else []
    missing = [c for c in ("keyword", "volume", "kd", "intent", "tier") if c not in header]
    if missing:
        raise InputError(f"{path.name}: missing column(s) {', '.join(missing)}; expected the "
                         "scored CSV written by keyword-research")
    return rows


def read_targets(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        header = reader.fieldnames or []
        rows = list(reader)
    if header != TARGET_COLUMNS:
        raise InputError(f"{path.name}: header {header} is not the site-structure-optimizer "
                         f"targets.csv header {TARGET_COLUMNS}")
    for i, r in enumerate(rows, 2):
        if not r["page_slug"].strip() or not r["primary_keyword"].strip():
            raise InputError(f"{path.name} line {i}: page_slug and primary_keyword are required")
        if r["opportunity_bucket"] not in ACTIONS:
            raise InputError(f"{path.name} line {i}: opportunity_bucket "
                             f"'{r['opportunity_bucket']}' is not one of {sorted(ACTIONS)}")
    return rows


def norm_kw(s: str) -> str:
    return " ".join(s.lower().split())


def keyword_tiers(rows: list[dict], targets: list[dict] | None) -> dict[int, list[dict]]:
    """Tier 1 = a build page's primary keyword (targets CSV), else P0 when there is no targets CSV.
    Tier 2 = remaining P0 and P1. Tier 3 = remaining P2. P3 and N/A are left out."""
    build = {norm_kw(t["primary_keyword"]) for t in targets} if targets else None
    tiers: dict[int, list[dict]] = {1: [], 2: [], 3: []}
    for r in rows:
        p = r["tier"].strip()
        if build is not None and norm_kw(r["keyword"]) in build:
            tiers[1].append(r)
        elif build is None and p == "P0":
            tiers[1].append(r)
        elif p in ("P0", "P1"):
            tiers[2].append(r)
        elif p == "P2":
            tiers[3].append(r)
    return tiers


def table_rows(text: str) -> list[list[str]]:
    return [[c.strip() for c in ln.strip().strip("|").split("|")]
            for ln in text.splitlines() if ln.strip().startswith("|")]


def url_map(sitemap_text: str) -> list[str] | None:
    """The first markdown table in the sitemap report whose header has a URL column, verbatim."""
    lines = sitemap_text.splitlines()
    i = 0
    while i < len(lines):
        ln = lines[i].strip()
        if ln.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:|-]+\|$", lines[i + 1].strip()):
            cells = [c.strip().lower() for c in ln.strip("|").split("|")]
            block = []
            j = i
            while j < len(lines) and lines[j].strip().startswith("|"):
                block.append(lines[j].strip())
                j += 1
            if "url" in cells:
                return block
            i = j
        else:
            i += 1
    return None


COUNTABLE = re.compile(r"countable pages (\d+) / SOW cap (\d+|Unknown)", re.I)


def countable(sitemap_text: str):
    hits = COUNTABLE.findall(sitemap_text)
    if not hits:
        return None
    n, cap = hits[-1]
    return int(n), (int(cap) if cap.isdigit() else "Unknown")


# ---------- building the copied sections ----------

def build_keyword_section(inp: dict, root: Path) -> tuple[str, list[str]]:
    srcs = [rel(root, inp[k]) for k in ("keyword_report", "keywords") if inp[k]]
    if not inp["keywords"]:
        what = "the saved keyword-research report and its scored CSV" if not inp["keyword_report"] \
            else "the scored CSV saved next to " + rel(root, inp["keyword_report"])
        return f"[NEEDS INPUT: {what}; keyword tiers are copied from it, never estimated]", srcs
    rows = read_keywords(inp["keywords"])
    targets = read_targets(inp["targets"]) if inp["targets"] else None
    if inp["targets"]:
        srcs.append(rel(root, inp["targets"]))
    tiers = keyword_tiers(rows, targets)
    rule = ("Tier 1 keywords are the main keywords of pages in the new build" if targets
            else "Tier 1 keywords are the report's must-target keywords")
    out = [f"The keywords below come from our keyword research, each with its monthly searches and "
           f"its difficulty score (higher is harder to rank for). {rule}; Tier 2 keywords are the next priorities, for "
           f"the first months after launch; Tier 3 keywords build long-term authority.", ""]
    for t in (1, 2, 3):
        out += [f"### {TIER_TITLES[t]}", ""]
        if not tiers[t]:
            out += ["No keywords in this tier.", ""]
            continue
        out += ["| Keyword | Monthly searches | Difficulty | Intent |", "|---|---|---|---|"]
        for r in tiers[t][:TIER_CAP]:
            out.append(f"| {r['keyword']} | {r['volume']} | {r['kd']} | {r['intent']} |")
        extra = len(tiers[t]) - TIER_CAP
        if extra > 0:
            out.append("")
            out.append(f"{extra} more Tier {t} keywords are in the keyword research report.")
        out.append("")
    return "\n".join(out).rstrip(), srcs


def build_site_section(inp: dict, root: Path) -> tuple[str, list[str]]:
    srcs = [rel(root, inp["sitemap"])] if inp["sitemap"] else []
    if inp["context"]:
        srcs.append(rel(root, inp["context"]))
    if not inp["sitemap"]:
        return "[NEEDS INPUT: the saved site-structure-optimizer report; the sitemap is copied from it]", srcs
    text = read(inp["sitemap"])
    out = ["The sitemap below is the page plan for the new site.", ""]
    cnt = countable(text)
    cap = scope_cap(inp["context"])
    if cnt is None:
        out.append("[NEEDS INPUT: the sitemap report's countable page line; the page count is copied from it]")
    elif isinstance(cap, int):
        out.append(f"Page count: {cnt[0]} pages counted against the {cap}-page scope. {UNCOUNTED}")
    else:
        out.append(f"Page count: {cnt[0]} counted pages. {UNCOUNTED} [NEEDS INPUT: the agreed page count; "
                   f"the client context has no number to hold the sitemap to]")
    out.append("")
    um = url_map(text)
    if um is None:
        out.append("[NEEDS INPUT: a URL map table in the sitemap report]")
    else:
        out += um
    if inp["targets"]:
        srcs.append(rel(root, inp["targets"]))
        out += ["", "### Content plan", "",
                "| Page | Main keyword | Monthly searches | Difficulty | Action |", "|---|---|---|---|---|"]
        for t in read_targets(inp["targets"]):
            out.append(f"| {t['page_slug']} | {t['primary_keyword']} | {t['volume'] or 'N/A'} | "
                       f"{t['kd'] or 'N/A'} | {ACTIONS[t['opportunity_bucket']]} |")
    return "\n".join(out).rstrip(), srcs


def source_line(paths: list[str]) -> str:
    paths = [p for p in paths if p]
    return "Source: " + ("; ".join(paths) if paths else "none")


def default_sources(inp: dict, root: Path) -> dict[str, list[str]]:
    r = lambda *keys: [rel(root, inp[k]) for k in keys if inp[k]]  # noqa: E731
    kit = lambda *names: [rel(root, inp["kit:" + n]) for n in names if inp["kit:" + n]]  # noqa: E731
    return {
        "Executive Summary": r("context", "keyword_report", "sitemap", "competitors"),
        "Business and Market Overview": r("context", "package") + kit("brand.md", "audience.md", "compliance.md"),
        "Competitive Analysis": r("competitors", "package"),
        "Strategic Positioning": kit("brand.md", "voice.md", "audience.md", "style.md") + r("quotes"),
        "Growth Strategy": r("context", "package", "keyword_report", "sitemap", "competitors"),
        "Measurement and Next Steps": r("context", "package"),
    }


PROSE_HINTS = {
    "Executive Summary": "write this section last: the three to five things the client should take away, "
                         "each backed by a figure from a named source",
    "Business and Market Overview": "who the client is, services, service area, audiences, goals and the "
                                    "market, from the context and the Blueprint Input Package",
    "Competitive Analysis": "the competitors, the comparison table and the openings, from the "
                            "competitor-analysis report",
    "Strategic Positioning": "quote the positioning, differentiators, voice and audiences from the "
                             "Reference Kit; never rewrite them",
    "Measurement and Next Steps": "what will be measured and the next steps with owners",
}


def scaffold(root: Path, slug: str, inp: dict, date: str, force: bool, agency: str) -> int:
    out_dir = root / "blueprint" / slug
    bp = out_dir / f"{slug}-growth-blueprint.md"
    br = out_dir / f"{slug}-am-briefing.md"
    for p in (bp, br):
        if p.exists() and not force:
            print(f"{rel(root, p)} exists; pass --force to rewrite it from scratch", file=sys.stderr)
            return 2
    name = client_name(inp["context"], slug)
    srcs = default_sources(inp, root)
    kw_body, kw_src = build_keyword_section(inp, root)
    site_body, site_src = build_site_section(inp, root)
    parts = [f"# {name}: Growth Blueprint", "", f"Client: {name}", f"Date: {date}",
             f"Prepared by: {agency}", ""]
    for sec in BLUEPRINT_SECTIONS:
        parts += [f"## {sec}", ""]
        if sec == "Keyword Opportunity":
            parts += [kw_body, "", source_line(kw_src), ""]
            continue
        if sec == "Site Architecture and Content Plan":
            parts += [site_body, "", source_line(site_src), ""]
            continue
        if sec == "Growth Strategy":
            parts += ["### Phase 1: the new site (build)", "", "[WRITE: what the new site establishes]", "",
                      "### Phase 2: months 1 to 3", "", "[WRITE: first content push and early wins]", "",
                      "### Phase 3: months 4 to 6", "", "[WRITE: authority building]", "",
                      "### Trajectory at 3, 6 and 12 months (directional)", "",
                      "[WRITE: directional trajectory, no promised rankings or traffic]", ""]
        elif sec == "Competitive Analysis" and not inp["competitors"]:
            parts += ["[NEEDS INPUT: a saved competitor-analysis report; competitor figures are never "
                      "estimated]", ""]
        else:
            parts += [f"[WRITE: {PROSE_HINTS[sec]}]", ""]
        parts += [source_line(srcs[sec]), ""]
    out_dir.mkdir(parents=True, exist_ok=True)
    bp.write_text("\n".join(parts).rstrip() + "\n", encoding="utf-8")

    q = []
    for i in range(1, 6):
        q += [f"{i}. Q: [WRITE: question the client is likely to ask]",
              "   A: [WRITE: the answer, using the Blueprint's figures]"]
    brief = [f"# {name}: AM Briefing (internal)", "", f"Client: {name}", f"Date: {date}",
             f"Blueprint: {rel(root, bp)}", "",
             "## Executive Summary", "", "- [WRITE: 3 to 5 bullets]", "",
             "## Key Strategic Bets", "", "1. [WRITE: 3 or 4 bets, each with why]", "",
             "## Numbers the AM Should Know", "", "- [WRITE: figures copied from the Blueprint]", "",
             "## Anticipated Client Questions", ""] + q + [
             "", "## Calibration Framing", "",
             "[WRITE: how to set expectations: what is directional, what the client must provide]", ""]
    br.write_text("\n".join(brief), encoding="utf-8")

    print(f"wrote {rel(root, bp)}")
    print(f"wrote {rel(root, br)}")
    print("| Input | Path |")
    print("|---|---|")
    for key, p in inp.items():
        print(f"| {key} | {rel(root, p) if p else 'MISSING'} |")
    return 0


# ---------- checking ----------

def split_sections(text: str) -> list[tuple[str, str]]:
    out = []
    cur, buf = None, []
    for ln in text.splitlines():
        m = re.match(r"^## (.+?)\s*$", ln)
        if m:
            if cur is not None:
                out.append((cur, "\n".join(buf)))
            cur, buf = m.group(1), []
        elif cur is not None:
            buf.append(ln)
    if cur is not None:
        out.append((cur, "\n".join(buf)))
    return out


NUM = re.compile(r"\$?\d[\d,]*(?:\.\d+)?%?")
EXEMPT = [
    r"\b(?:Phase|Tier|Weeks?|Months?|Step|Q)\s+\d+(?:\s*(?:to|-|and)\s*\d+(?![,.]?\d))?(?![,.]?\d)",
    r"\b\d+(?:\s*,\s*\d+)*(?:,?\s*(?:and|or|to)\s*\d+)?(?:\s*|-)months?\b",
    r"\b\d+(?:\s*,\s*\d+)*(?:,?\s*(?:and|or|to)\s*\d+)?(?:\s*|-)weeks?\b",
    r"(?m)^\s*\d+\.\s",
    r"\d{4}-\d{2}-\d{2}",
]


def norm_num(tok: str) -> str:
    t = tok.strip("$%").replace(",", "")
    t = t.rstrip(".")
    if "." in t:
        t = t.rstrip("0").rstrip(".")
    return t


def figures(text: str) -> list[str]:
    t = NEEDS.sub(" ", text)
    t = re.sub(r"`[^`]*`", " ", t)
    t = re.sub(r"\]\([^)]*\)", "] ", t)
    t = re.sub(r"\S*(?:://|@|\.md\b|\.csv\b)\S*|(?<![\w$.])/[\w./-]*", " ", t)
    t = "\n".join(ln for ln in t.splitlines() if not ln.lstrip().startswith("#")
                  and not ln.startswith("Source:"))
    for pat in EXEMPT:
        t = re.sub(pat, " ", t, flags=re.I)
    out = []
    for m in NUM.finditer(t):
        tok = m.group(0).rstrip(",.")
        if not tok:
            continue
        if not tok.endswith("%") and PCT.match(t, m.end()):
            tok += "%"
        bare = tok.strip("$%").replace(",", "")
        if re.fullmatch(r"\d", bare) and not tok.startswith("$") and not tok.endswith("%"):
            continue
        out.append(tok)
    return out


PCT = re.compile(r"\s*(?:%|percent\b|per cent\b)", re.I)


def is_pct(text: str, m: re.Match) -> bool:
    return m.group(0).endswith("%") or bool(PCT.match(text, m.end()))


def number_set(text: str) -> set[str]:
    """Normalized numbers in a text; percentages also as 'N%' so a percentage only matches one."""
    out = set()
    for m in NUM.finditer(text):
        n = norm_num(m.group(0))
        out.add(n)
        if is_pct(text, m):
            out.add(n + "%")
    return out


def fig_key(tok: str) -> str:
    return norm_num(tok) + ("%" if tok.endswith("%") else "")


def parse_sources(body: str) -> tuple[list[str] | None, str]:
    lines = [ln for ln in body.splitlines() if ln.strip()]
    if not lines or not lines[-1].startswith("Source:"):
        return None, ""
    raw = lines[-1][len("Source:"):].strip()
    parts = [p.strip().strip("`").strip() for p in re.split(r"[;,]", raw) if p.strip()]
    return parts, raw


def norm_quote(s: str) -> str:
    s = s.replace("“", '"').replace("”", '"').replace("’", "'").replace("‘", "'")
    return " ".join(s.split())


class Report:
    def __init__(self):
        self.rows: list[tuple[str, str, str]] = []

    def add(self, check: str, ok: bool | None, detail: str = ""):
        self.rows.append((check, "pass" if ok else ("needs input" if ok is None else "FAIL"), detail))

    @property
    def failed(self):
        return any(r[1] == "FAIL" for r in self.rows)

    @property
    def needs(self):
        return any(r[1] == "needs input" for r in self.rows)


def check_blueprint(root: Path, slug: str, inp: dict, rep: Report) -> str | None:
    bp = root / "blueprint" / slug / f"{slug}-growth-blueprint.md"
    if not bp.exists():
        rep.add("blueprint file", False, f"{rel(root, bp)} not found; run scaffold first")
        return None
    text = read(bp)
    rep.add("blueprint file", True, rel(root, bp))
    secs = split_sections(text)
    names = [s for s, _ in secs]
    rep.add("sections and order", names == BLUEPRINT_SECTIONS,
            "" if names == BLUEPRINT_SECTIONS else f"found {names}; expected {BLUEPRINT_SECTIONS}")
    body = dict(secs)
    left = WRITE.findall(text)
    rep.add("no [WRITE] placeholders left", not left, "; ".join(left[:3]))

    # Source lines
    src_files: dict[str, list[Path]] = {}
    bad = []
    for name, b in secs:
        parts, raw = parse_sources(b)
        n_src = sum(1 for ln in b.splitlines() if ln.startswith("Source:"))
        if n_src > 1:
            bad.append(f"{name}: {n_src} Source: lines; keep one, at the end")
        if parts is None:
            bad.append(f"{name}: no Source: line at the end")
            continue
        if parts == ["none"] or raw.lower().startswith("none"):
            if not NEEDS.search(b):
                bad.append(f"{name}: Source: none without a [NEEDS INPUT: ...] line")
            src_files[name] = []
            continue
        files = []
        for p in parts:
            fp = root / p
            if fp.is_file():
                files.append(fp)
            else:
                bad.append(f"{name}: {p} not found")
        src_files[name] = files
    rep.add("Source: line per section, files exist", not bad, "; ".join(bad))

    # copied keyword tiers
    kw = body.get("Keyword Opportunity", "")
    if inp["keywords"]:
        rows = read_keywords(inp["keywords"])
        targets = read_targets(inp["targets"]) if inp["targets"] else None
        tiers = keyword_tiers(rows, targets)
        want = []
        for t in (1, 2, 3):
            want += [(t, r["keyword"], r["volume"], r["kd"]) for r in tiers[t][:TIER_CAP]]
        got = []
        cur = None
        for ln in kw.splitlines():
            m = re.match(r"^### Tier (\d)", ln)
            if m:
                cur = int(m.group(1))
                continue
            if cur and ln.strip().startswith("|"):
                c = [x.strip() for x in ln.strip().strip("|").split("|")]
                if len(c) >= 3 and c[0] not in ("Keyword",) and not set(c[0]) <= set("-: "):
                    got.append((cur, c[0], c[1], c[2]))
        diff = [w for w in want if w not in got] + [g for g in got if g not in want]
        rep.add("keyword tiers match the keyword report", not diff,
                "" if not diff else "differs at: " + "; ".join(f"Tier {d[0]} {d[1]}" for d in diff[:5]))
    else:
        rep.add("keyword tiers match the keyword report", None if NEEDS.search(kw) else False,
                "no scored keyword CSV" + ("" if NEEDS.search(kw) else " and no [NEEDS INPUT] line"))

    # sitemap
    site = body.get("Site Architecture and Content Plan", "")
    cap = scope_cap(inp["context"])
    if inp["sitemap"]:
        stext = read(inp["sitemap"])
        cnt = countable(stext)
        um = url_map(stext)
        missing_rows = [r for r in (um or []) if r not in [ln.strip() for ln in site.splitlines()]]
        if um is None:
            rep.add("sitemap copied from the sitemap report", None if NEEDS.search(site) else False,
                    "no URL map table in the report" + ("" if NEEDS.search(site) else
                                                        "; add a [NEEDS INPUT] line"))
        else:
            rep.add("sitemap copied from the sitemap report", not missing_rows,
                    "; ".join(missing_rows[:3]) if missing_rows else rel(root, inp["sitemap"]))
        m = re.search(r"Page count: (\d+)", site)
        if cnt is None:
            rep.add("page count within the scope cap", None, "no countable pages line in the sitemap report")
        elif not m or int(m.group(1)) != cnt[0]:
            rep.add("page count within the scope cap", False,
                    f"the Blueprint must state 'Page count: {cnt[0]}' as the sitemap report does")
        elif cap is None or cap == "unknown":
            rep.add("page count within the scope cap", None,
                    "the client context has no SOW pages number" + ("" if NEEDS.search(site) else
                                                                   "; add a [NEEDS INPUT] line"))
        else:
            rep.add("page count within the scope cap", cnt[0] <= cap,
                    f"{cnt[0]} counted pages, scope cap {cap} (context)")
    else:
        rep.add("sitemap copied from the sitemap report", None if NEEDS.search(site) else False,
                "no sitemap report" + ("" if NEEDS.search(site) else " and no [NEEDS INPUT] line"))

    # figures
    built_nums = set()
    for n in BUILT:
        built_nums |= number_set(body.get(n, ""))
    unsourced = []
    for name, b in secs:
        if name in BUILT:
            continue
        allowed = set(built_nums)
        for f in src_files.get(name, []):
            allowed |= number_set(read(f))
        for tok in figures(b):
            if fig_key(tok) not in allowed:
                unsourced.append(f"{name}: {tok}")
    rep.add("every figure appears in a named source", not unsourced, "; ".join(unsourced[:8]))

    # blockquotes verbatim
    bad_q = []
    for name, b in secs:
        corpus = " ".join(norm_quote(read(f)) for f in src_files.get(name, []))
        for ln in b.splitlines():
            if not ln.startswith(">"):
                continue
            q = ln.lstrip("> ").strip()
            m = re.search(r"[\"“](.+?)[\"”]", q)
            q = m.group(1) if m else q
            if norm_quote(q) not in corpus:
                bad_q.append(f"{name}: {q[:60]}")
    rep.add("quoted lines are verbatim from their sources", not bad_q, "; ".join(bad_q[:5]))

    # growth strategy subsections
    gs = [re.match(r"^### (.+)", ln).group(1) for ln in body.get("Growth Strategy", "").splitlines()
          if ln.startswith("### ")]
    order = [next((i for i, h in enumerate(gs) if h.startswith(w)), -1) for w in GROWTH_SUBSECTIONS]
    ok = all(i >= 0 for i in order) and order == sorted(order)
    rep.add("Growth Strategy has Phase 1, 2, 3 and Trajectory", ok, "" if ok else f"found {gs}")

    # jargon in prose
    hits = []
    for name, b in secs:
        for ln in b.splitlines():
            if ln.strip().startswith("|") or ln.startswith("Source:"):
                continue
            for pat in JARGON:
                m = re.search(pat, NEEDS.sub(" ", ln))
                if m:
                    hits.append(f"{name}: {m.group(0)}")
    rep.add("no internal jargon in client prose", not hits, "; ".join(sorted(set(hits))[:6]))

    flags = NEEDS.findall(text)
    rep.add("open [NEEDS INPUT] flags", None if flags else True, "; ".join(flags[:4]) if flags else "none")
    return text


def check_briefing(root: Path, slug: str, bp_text: str | None, rep: Report) -> None:
    br = root / "blueprint" / slug / f"{slug}-am-briefing.md"
    if not br.exists():
        rep.add("briefing file", False, f"{rel(root, br)} not found")
        return
    text = read(br)
    rep.add("briefing file", True, rel(root, br))
    secs = split_sections(text)
    names = [s for s, _ in secs]
    rep.add("briefing sections and order", names == BRIEFING_SECTIONS,
            "" if names == BRIEFING_SECTIONS else f"found {names}")
    body = dict(secs)
    left = WRITE.findall(text)
    rep.add("briefing: no [WRITE] placeholders left", not left, "; ".join(left[:3]))
    items = lambda s: [ln for ln in body.get(s, "").splitlines() if re.match(r"^(- |\d+\. )", ln)]  # noqa: E731
    n = len(items("Executive Summary"))
    rep.add("briefing: 3 to 5 summary bullets", 3 <= n <= 5, f"{n} found")
    n = len(items("Key Strategic Bets"))
    rep.add("briefing: 3 or 4 strategic bets", 3 <= n <= 4, f"{n} found")
    n = len(items("Numbers the AM Should Know"))
    rep.add("briefing: numbers listed", n >= 1, f"{n} found")
    lines = body.get("Anticipated Client Questions", "").splitlines()
    qs = [i for i, ln in enumerate(lines) if re.match(r"^\d+\. Q: \S", ln)]
    answered = [i for i in qs if any(re.match(r"^\s*A: \S", ln) for ln in lines[i + 1:i + 3])]
    rep.add("briefing: 5 client questions, each answered", len(qs) == 5 and len(answered) == 5,
            f"{len(qs)} questions, {len(answered)} answered")
    rep.add("briefing: calibration framing", bool(body.get("Calibration Framing", "").strip()))
    words = len(re.findall(r"\S+", text))
    rep.add(f"briefing: one page (at most {BRIEFING_MAX_WORDS} words)", words <= BRIEFING_MAX_WORDS,
            f"{words} words")
    if bp_text is not None:
        allowed = number_set(bp_text)
        body_text = "\n".join(b for _, b in secs)
        stray = [t for t in figures(body_text) if fig_key(t) not in allowed]
        rep.add("briefing: every figure is in the Blueprint", not stray, "; ".join(stray[:8]))


def run_check(root: Path, slug: str, inp: dict) -> int:
    rep = Report()
    for key in ("context", "package", "quotes"):
        rep.add(f"input {key}", True if inp[key] else None, rel(root, inp[key]) if inp[key] else "missing")
    missing_kit = [f for f in KIT_FILES if not inp["kit:" + f]]
    rep.add("input Reference Kit", None if missing_kit else True,
            "missing " + ", ".join(missing_kit) if missing_kit else "5 files")
    try:
        bp_text = check_blueprint(root, slug, inp, rep)
        check_briefing(root, slug, bp_text, rep)
    except InputError as e:
        rep.add("inputs readable", False, str(e))
    print("| Check | Result | Detail |")
    print("|---|---|---|")
    for c, r, d in rep.rows:
        print(f"| {c} | {r} | {d.replace('|', '/')} |")
    result = "FAIL" if rep.failed else ("NEEDS_INPUT" if rep.needs else "PASS")
    print(f"RESULT: {result}")
    return 1 if rep.failed else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("scaffold", "check"):
        s = sub.add_parser(name)
        s.add_argument("--slug", required=True)
        s.add_argument("--root", default=".")
        s.add_argument("--client-slug")
        s.add_argument("--keywords", help="keyword-research scored CSV")
        s.add_argument("--keyword-report")
        s.add_argument("--sitemap")
        s.add_argument("--sitemap-targets")
        s.add_argument("--competitors")
        if name == "scaffold":
            s.add_argument("--date", default=dt.date.today().isoformat())
            s.add_argument("--force", action="store_true")
            s.add_argument("--agency", default="WISE Digital Partners", help="the Prepared by: line")
    k = sub.add_parser("keywords")
    k.add_argument("csv")
    t = sub.add_parser("sitemap-targets")
    t.add_argument("csv")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "keywords":
            rows = read_keywords(Path(a.csv))
            tiers = keyword_tiers(rows, None)
            print(json.dumps([{"tier": n, "keyword": r["keyword"], "volume": r["volume"], "kd": r["kd"],
                               "intent": r["intent"]} for n in (1, 2, 3) for r in tiers[n]], indent=1))
            return 0
        if a.cmd == "sitemap-targets":
            print(json.dumps(read_targets(Path(a.csv)), indent=1))
            return 0
        root = Path(a.root)
        inp = find_inputs(root, a.slug, a)
        if a.cmd == "scaffold":
            return scaffold(root, a.slug, inp, a.date, a.force, a.agency)
        return run_check(root, a.slug, inp)
    except InputError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
