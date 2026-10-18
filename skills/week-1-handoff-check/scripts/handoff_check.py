#!/usr/bin/env python3
"""Week 1 handoff check: is every Week 1 file present and complete before Week 2?

Usage:
  handoff_check.py run <working-folder> [--slug S] [--kit DIR] [--content DIR]
                       [--signoff "<who>, <date>"] [--date YYYY-MM-DD] [--dry-run]
  handoff_check.py inventory <url-inventory.csv>

`run` reads the client's working folder (the folder holding kickoff/, client-reference/,
research/, seo-reports/, content/, design/, emails/, welcome-email/, feedback/), writes
handoff/<slug>/<slug>-week-1-handoff.md (not with --dry-run) and prints the same report.
Its last line is GO or NO-GO. Exit 0 on GO, 1 on NO-GO, 2 on a usage error.

`inventory` checks that a URL inventory CSV has the header new-build-kickoff writes
(`url`, `title`, `page_type`, `status`, `source`). Exit 0 when it does.

Standard library only. Status values: present, missing, stale, n/a.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
import sys
from pathlib import Path

INVENTORY_COLUMNS = ["url", "title", "page_type", "status", "source"]
CONTEXT_HEADINGS = ["Snapshot", "Scope Summary", "Open Items", "Sources"]
PACKAGE_HEADINGS = ["Services Priority", "Audiences", "Service Area Tiers", "Voice and Design Direction",
                    "Competitors", "Topics to Own", "Goals and Success Measures", "Scope Decisions", "Open Items"]
CALL_BRIEF_HEADINGS = ["Call Goals", "What We Know", "Questions to Settle", "Scope to Confirm",
                       "Access to Confirm", "Relationship Notes"]
DESIGN_HEADINGS = ["Goals", "Audience", "Brand Cues", "Design References", "Section Map", "Imagery",
                   "Must-Haves", "Do-Nots", "Open Questions", "Sources"]
MISSING_HEADINGS = ["Intake Items", "Platform Access", "Kickoff Call Agenda"]
KIT_FILES = ["brand.md", "voice.md", "style.md", "audience.md", "compliance.md"]
CONTENT_FILES = ["article.md", "metadata.md", "article.html", "qa_report.md", "handoff.md"]
PAID_RE = re.compile(r"\b(paid media|ppc|google ads|meta ads|microsoft ads|paid search|paid social)\b", re.I)
CAP_RE = re.compile(r"countable pages\W*(\d+)\s*/\s*SOW cap\W*(\d+|unknown)", re.I)
MARKER_RE = re.compile(r"<!--\s*section:\s*(.+?)\s*-->")
OPTION_RE = re.compile(r"^\s*[^:\n]{1,60}:\s*https?://\S+\s*$")

OWNERS = {
    "kickoff": "AM, new-build-kickoff",
    "welcome": "AM, welcome-email",
    "update": "AM, client-context-update",
    "access": "Dev",
    "brief": "AM, kickoff-call-brief",
    "call": "AM, kickoff-call-processing",
    "kit": "SEO, client-reference-kit",
    "kw": "SEO, keyword-research",
    "sitemap": "SEO, site-structure-optimizer",
    "cbrief": "SEO, content-brief",
    "content": "SEO, seo-content-writer",
    "editor": "SEO editor",
    "design": "Design, homepage-design-brief",
    "email": "AM, week-1-client-email",
    "feedback": "AM, client-feedback",
}


class Row:
    def __init__(self, item: str, required: bool, path: str, owner: str):
        self.item, self.required, self.path, self.owner = item, required, path, owner
        self.status, self.note = "present", ""

    def set(self, status: str, note: str = "") -> "Row":
        self.status, self.note = status, note
        return self

    @property
    def blocking(self) -> bool:
        return self.required and self.status in ("missing", "stale")


def read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def headings(text: str) -> list[str]:
    return [m.group(1).strip() for m in re.finditer(r"^##\s+(.+?)\s*$", text, re.M)]


def lacking(text: str, wanted: list[str]) -> list[str]:
    have = {h.lower() for h in headings(text)}
    return [h for h in wanted if h.lower() not in have]


def table_rows(text: str, header_start: str) -> list[list[str]]:
    """Data rows of the first markdown table whose header line starts with header_start."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith(header_start):
            out = []
            for row in lines[i + 2:]:
                if not row.strip().startswith("|"):
                    break
                out.append([c.strip() for c in row.strip().strip("|").split("|")])
            return out
    return []


def front_matter(text: str) -> dict[str, str]:
    m = re.match(r"---\s*\n(.*?)\n---", text, re.S)
    if not m:
        return {}
    out = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith((" ", "\t")):
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def rel(root: Path, p: Path) -> str:
    try:
        return p.relative_to(root).as_posix()
    except ValueError:
        return p.as_posix()


def check_inventory(p: Path) -> str:
    """Empty string when the CSV has the kickoff header, else the problem."""
    try:
        with p.open(newline="", encoding="utf-8") as f:
            header = next(csv.reader(f), [])
    except OSError as e:
        return f"cannot read: {e}"
    header = [h.strip() for h in header]
    if header != INVENTORY_COLUMNS:
        return "header is " + (",".join(header) or "empty") + "; expected " + ",".join(INVENTORY_COLUMNS)
    return ""


def file_row(root: Path, item: str, required: bool, p: Path, owner: str, need_headings=None,
             need_text=None) -> Row:
    r = Row(item, required, rel(root, p), owner)
    if not p.is_file():
        return r.set("missing", f"not found; owner {owner}")
    text = read(p)
    if not text.strip():
        return r.set("missing", f"empty file; owner {owner}")
    gaps = lacking(text, need_headings or [])
    for label, pattern in (need_text or []):
        if not re.search(pattern, text, re.M):
            gaps.append(label)
    if gaps:
        return r.set("missing", "incomplete, lacks " + "; ".join(gaps) + f"; owner {owner}")
    return r


def find_slug(root: Path, slug: str | None) -> str:
    kroot = root / "kickoff"
    if slug:
        return slug
    found = sorted(d.name for d in kroot.iterdir() if d.is_dir() and (d / f"{d.name}-context.md").is_file()) \
        if kroot.is_dir() else []
    if len(found) == 1:
        return found[0]
    if not found:
        raise SystemExit("ERROR: no kickoff/<slug>/<slug>-context.md under " + str(root) +
                         "; new-build-kickoff has not run here, or this is not the client's working folder")
    raise SystemExit("ERROR: several kickoff folders (" + ", ".join(found) + "); pass --slug")


def latest(files: list[Path]) -> Path | None:
    return sorted(files, key=lambda p: p.name)[-1] if files else None


def build(root: Path, slug: str, kit: str | None, content: str | None, signoff: str | None) -> tuple[str, list[Row]]:
    k = root / "kickoff" / slug
    ctx_p = k / f"{slug}-context.md"
    ctx = read(ctx_p)
    m = re.search(r"^Client:\s*(.+?)\s*$", ctx, re.M)
    client = m.group(1) if m else slug
    rows: list[Row] = []
    log_text = read(k / f"{slug}-change-log.md")
    log_rows = table_rows(log_text, "| Date | Source |")
    log_sources = [r[1].lower() for r in log_rows if len(r) > 1]

    # 1. Kickoff files (new-build-kickoff)
    r = file_row(root, "Client context", True, ctx_p, OWNERS["kickoff"], CONTEXT_HEADINGS,
                 [("`SOW pages:` line", r"^SOW pages:")])
    call_updates = k / f"{slug}-call-updates.md"
    if r.status == "present" and call_updates.is_file() and not any(s.startswith("call") for s in log_sources):
        r.set("stale", "Kickoff Call updates not merged (no `call` row in the change log); "
                       f"run client-context-update on {rel(root, call_updates)}")
    rows.append(r)
    inv = k / f"{slug}-url-inventory.csv"
    r = Row("URL inventory", True, rel(root, inv), OWNERS["kickoff"])
    if not inv.is_file():
        r.set("missing", f"not found; owner {OWNERS['kickoff']}")
    else:
        problem = check_inventory(inv)
        if problem:
            r.set("missing", f"incomplete, {problem}; owner {OWNERS['kickoff']}")
        else:
            with inv.open(newline="", encoding="utf-8") as f:
                n = sum(1 for _ in csv.reader(f)) - 1
            if n == 0:
                r.note = "no pages listed (no existing website)"
    rows.append(r)
    rows.append(file_row(root, "Gap questions", True, k / f"{slug}-gap-questions.md", OWNERS["kickoff"]))
    rows.append(file_row(root, "Project instructions", True, k / f"{slug}-project-instructions.md", OWNERS["kickoff"]))
    rows.append(file_row(root, "Setup checklist", True, k / f"{slug}-setup-checklist.md", OWNERS["kickoff"]))
    pm = k / f"{slug}-paid-media-brief.md"
    inc = re.search(r"^Included services:\s*(.+)$", ctx, re.M)
    paid_in_scope = bool(inc and PAID_RE.search(inc.group(1)))
    if paid_in_scope or pm.is_file():
        rows.append(file_row(root, "Paid media brief", paid_in_scope, pm, OWNERS["kickoff"]))
    else:
        rows.append(Row("Paid media brief", False, rel(root, pm), OWNERS["kickoff"])
                    .set("n/a", "paid media not in the scope source's `Included services:`"))

    # 2. Welcome email
    rows.append(file_row(root, "Welcome email", True, root / "welcome-email" / slug / f"{slug}-welcome-email.md",
                         OWNERS["welcome"], need_text=[("`Subject:` line", r"^Subject:\s*\S")]))

    # 3. Gap responses processed (client-context-update)
    r = file_row(root, "Change log", True, k / f"{slug}-change-log.md", OWNERS["update"],
                 need_text=[("`| Date | Source | Section | Change | Before | After |` table",
                             r"^\|\s*Date\s*\|\s*Source\s*\|")])
    if r.status == "present" and not log_rows:
        r.set("missing", f"incomplete, change log has no rows; owner {OWNERS['update']}")
    rows.append(r)
    mi_p = k / f"{slug}-missing-items.md"
    rows.append(file_row(root, "Missing items", True, mi_p, OWNERS["update"], MISSING_HEADINGS))

    # 4. Platform access (not blocking)
    r = Row("Platform access confirmed", False, rel(root, mi_p), OWNERS["access"])
    plat = table_rows(read(mi_p), "| Platform |")
    if not plat:
        r.set("missing", "no `| Platform | Status | Note |` table to read")
    else:
        open_p = [p[0] for p in plat if len(p) > 1 and p[1].lower() not in ("confirmed", "n/a")]
        if open_p:
            r.set("missing", f"{len(open_p)} not confirmed: " + ", ".join(open_p) + "; does not block Week 2")
        else:
            r.note = "every platform confirmed or n/a"
    rows.append(r)

    # 5. Kickoff Call (kickoff-call-brief, kickoff-call-processing)
    rows.append(file_row(root, "Kickoff Call brief", True, k / f"{slug}-kickoff-call-brief.md", OWNERS["brief"],
                         CALL_BRIEF_HEADINGS))
    rows.append(file_row(root, "Call updates", True, call_updates, OWNERS["call"], ["Updates"],
                         [("`Source: call` line", r"^Source:\s*call\b")]))
    rows.append(file_row(root, "Blueprint Input Package", True, k / f"{slug}-blueprint-input-package.md",
                         OWNERS["call"], PACKAGE_HEADINGS))
    rows.append(file_row(root, "Quote bank", True, k / f"{slug}-quote-bank.md", OWNERS["call"],
                         need_text=[("`| # | Quote | Speaker | Timestamp | Use for |` table",
                                     r"^\|\s*#\s*\|\s*Quote\s*\|")]))

    # 6. Client Reference Kit
    if kit:
        kit_dir = Path(kit) if Path(kit).is_absolute() else root / kit
        kit_note = ""
    else:
        kdirs = sorted(d for d in (root / "client-reference").glob("*") if d.is_dir())
        if len(kdirs) == 1:
            kit_dir, kit_note = kdirs[0], ""
        elif not kdirs:
            kit_dir, kit_note = root / "client-reference" / "<client-slug>", "no client-reference/ folder"
        else:
            raise SystemExit("ERROR: several client-reference folders (" + ", ".join(d.name for d in kdirs) +
                             "); pass --kit")
    for name in KIT_FILES:
        r = file_row(root, f"Reference Kit {name}", True, kit_dir / name, OWNERS["kit"], ["Sources"])
        if kit_note and r.status == "missing":
            r.note = f"not found ({kit_note}); owner {OWNERS['kit']}"
        rows.append(r)

    # 7. Topic research and sitemap
    kw = latest([p for p in (root / "research" / "keyword-research").glob("*.md")])
    rows.append(file_row(root, "Keyword research", True,
                         kw or root / "research" / "keyword-research" / "<date>-<topic>.md", OWNERS["kw"],
                         need_text=[("`targets:` block", r"^targets:")]))
    rows.append(sitemap_row(root, ctx))

    # 8. Homepage brief, content, sign-off
    briefs = []
    for p in sorted((root / "research" / "content-briefs").glob("*.md")):
        if re.search(r"\.v\d+\.md$", p.name):
            continue
        if front_matter(read(p)).get("format", "").lower() == "homepage":
            briefs.append(p)
    hb = latest(briefs)
    r = Row("Homepage content brief", True,
            rel(root, hb) if hb else "research/content-briefs/<id>.md (format: homepage)", OWNERS["cbrief"])
    if not hb:
        r.set("missing", f"no brief with `format: homepage`; owner {OWNERS['cbrief']}")
    else:
        st = front_matter(read(hb)).get("status", "")
        if st not in ("DONE", "DONE_WITH_CONCERNS"):
            r.set("missing", f"incomplete, status is {st or 'not set'}; owner {OWNERS['cbrief']}")
        elif st == "DONE_WITH_CONCERNS":
            r.note = "status DONE_WITH_CONCERNS"
    rows.append(r)

    cdir = find_content(root, content)
    article = cdir / "article.md" if cdir else None
    r = Row("Homepage content", True, rel(root, cdir) + "/" if cdir else "content/home/", OWNERS["content"])
    if not cdir:
        r.set("missing", f"no homepage article.md under content/; owner {OWNERS['content']}")
    else:
        absent = [f for f in CONTENT_FILES if not (cdir / f).is_file()]
        verdict = re.search(r"^VERDICT:\s*(\w+)", read(cdir / "qa_report.md"), re.M)
        if absent:
            r.set("missing", "incomplete, lacks " + ", ".join(absent) + f"; owner {OWNERS['content']}")
        elif not verdict or verdict.group(1) not in ("READY", "NEEDS_INPUT"):
            r.set("missing", f"QA verdict is {verdict.group(1) if verdict else 'absent'}; fix and rerun check_draft.py; "
                             f"owner {OWNERS['content']}")
        else:
            flags = len(re.findall(r"\[(?:NEEDS (?:INPUT|SOURCE)|CLIENT INPUT NEEDED)[^\]]*\]", read(article)))
            r.note = f"VERDICT: {verdict.group(1)}" + (f"; {flags} open flags for the client" if flags else "")
    rows.append(r)

    dbrief_p = root / "design" / slug / f"{slug}-homepage-design-brief.md"
    dbrief = read(dbrief_p)
    r = Row("Editorial sign-off", True, rel(root, dbrief_p), OWNERS["editor"])
    review = re.search(r"^Content review:\s*(.+?)\s*$", dbrief, re.M)
    if signoff:
        r.path, r.note = "given by the user", f"signed off: {signoff}"
    elif review and review.group(1).lower().startswith("confirmed"):
        r.note = review.group(1)
    elif review:
        r.set("missing", f"design brief says `Content review: {review.group(1)}`; record the editor's sign-off")
    else:
        r.set("missing", "no record of the editor's sign-off (design brief `Content review:` line or --signoff)")
    rows.append(r)

    r = file_row(root, "Homepage design brief", True, dbrief_p, OWNERS["design"], DESIGN_HEADINGS)
    if r.status == "present" and article and article.is_file():
        page = MARKER_RE.findall(read(article))
        mapped = [row[1] for row in table_rows(dbrief, "| # | Section |") if len(row) > 1]
        low_page, low_mapped = [s.lower() for s in page], [s.lower() for s in mapped]
        if page and mapped and low_page != low_mapped:
            gone = [s for s in page if s.lower() not in low_mapped]
            extra = [s for s in mapped if s.lower() not in low_page]
            detail = "; ".join(x for x in (
                ("page sections not mapped: " + ", ".join(gone)) if gone else "",
                ("mapped sections no longer on the page: " + ", ".join(extra)) if extra else "",
            ) if x) or "section order differs"
            r.set("stale", f"Section Map does not match {rel(root, article)} ({detail}); rerun homepage-design-brief")
    rows.append(r)
    wf = root / "design" / slug / f"{slug}-homepage-wireframe.html"
    rows.append(Row("Homepage wireframe", False, rel(root, wf), OWNERS["design"])
                .set("present" if wf.is_file() else "n/a", "" if wf.is_file() else "optional, not made"))

    # 9. Week 1 email
    em_p = root / "emails" / slug / f"{slug}-week-1-email.md"
    r = file_row(root, "Week 1 client email", True, em_p, OWNERS["email"],
                 need_text=[("`Subject:` line", r"^Subject:\s*\S"), ("`Design options:` block", r"^Design options:")])
    if r.status == "present":
        em = read(em_p).split("Design options:", 1)[1].lstrip("\n").splitlines()
        opts = []
        for line in em:
            if not OPTION_RE.match(line):
                break
            opts.append(line)
        if len(opts) < 2:
            r.set("missing", f"incomplete, {len(opts)} design option link(s); Week 1 sends 2 to 3; owner {OWNERS['email']}")
        else:
            r.note = f"{len(opts)} design options"
    rows.append(r)

    # 10. Client feedback (never blocks)
    fdir = root / "feedback" / slug
    fb = latest([p for p in fdir.glob("*-feedback.md")])
    r = Row("Client feedback", False, rel(root, fb) if fb else rel(root, fdir) + "/", OWNERS["feedback"])
    if not fb:
        r.set("missing", "no reply processed yet; the handoff does not wait for it")
    else:
        unmerged = [p.name for p in sorted(fdir.glob("*-feedback-updates.md"))
                    if not any(p.name in s for s in log_sources)]
        if unmerged:
            r.set("stale", "facts not merged into the context: " + ", ".join(unmerged) +
                  "; run client-context-update; does not block Week 2")
    rows.append(r)
    return client, rows


def sitemap_row(root: Path, ctx: str) -> Row:
    sdir = root / "seo-reports" / "site-structure-optimizer"
    reports = [p for p in sdir.glob("*.md")]
    capped = [p for p in reports if CAP_RE.search(read(p))]
    p = latest(capped) or latest(reports)
    r = Row("Sitemap within scope page cap", True,
            rel(root, p) if p else "seo-reports/site-structure-optimizer/<date>-<site>.md", OWNERS["sitemap"])
    if not p:
        return r.set("missing", f"no saved architecture report; owner {OWNERS['sitemap']}")
    m = CAP_RE.search(read(p))
    if not m:
        return r.set("missing", "incomplete, no `countable pages N / SOW cap M` line (architecture mode); "
                                f"owner {OWNERS['sitemap']}")
    n, cap = int(m.group(1)), m.group(2).lower()
    sow = re.search(r"^SOW pages:\s*(\d+|unknown)", ctx, re.M | re.I)
    sow_v = sow.group(1).lower() if sow else "unknown"
    if cap == "unknown":
        if sow_v != "unknown":
            return r.set("stale", f"report has no cap but the context now says `SOW pages: {sow_v}`; "
                                  "rerun site-structure-optimizer")
        return r.set("present", f"countable pages {n} / SOW cap unknown: the scope source states no page count; "
                                "the AM confirms the page count")
    if n > int(cap):
        return r.set("missing", f"over the cap: countable pages {n} / SOW cap {cap}; owner {OWNERS['sitemap']}")
    if sow_v != "unknown" and sow_v != cap:
        return r.set("stale", f"report cap {cap} differs from the context's `SOW pages: {sow_v}`; "
                              "rerun site-structure-optimizer")
    return r.set("present", f"countable pages {n} / SOW cap {cap}")


def find_content(root: Path, content: str | None) -> Path | None:
    if content:
        p = Path(content) if Path(content).is_absolute() else root / content
        return p if p.is_dir() else None
    home = root / "content" / "home"
    if (home / "article.md").is_file():
        return home
    hits = [p.parent for p in sorted((root / "content").glob("*/article.md"))
            if re.search(r"<!--\s*section:\s*Hero\s*-->", read(p))]
    return hits[0] if len(hits) == 1 else None


def render(client: str, slug: str, date: str, rows: list[Row]) -> str:
    out = [f"Client: {client}", f"Checked: {date}", "", f"# Week 1 handoff check for {client}", "",
           "| Item | Required | Status | Path | Note |", "|---|---|---|---|---|"]
    for r in rows:
        note = r.note.replace("|", "/")
        out.append(f"| {r.item} | {'yes' if r.required else 'no'} | {r.status} | {r.path} | {note} |")
    block = [r for r in rows if r.blocking]
    out += ["", "## Blocking", ""]
    out += [f"- {r.item} ({r.status}): {r.note}" for r in block] or ["- None. Every required item is present."]
    follow = [r for r in rows if not r.required and r.status in ("missing", "stale")]
    out += ["", "## Not blocking", ""]
    out += [f"- {r.item} ({r.status}): {r.note}" for r in follow] or ["- None."]
    out += ["", "NO-GO" if block else "GO"]
    return "\n".join(out) + "\n"


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run")
    run.add_argument("folder")
    run.add_argument("--slug")
    run.add_argument("--kit")
    run.add_argument("--content")
    run.add_argument("--signoff")
    run.add_argument("--date", default=dt.date.today().isoformat())
    run.add_argument("--dry-run", action="store_true")
    inv = sub.add_parser("inventory")
    inv.add_argument("csv")
    a = ap.parse_args(argv)

    if a.cmd == "inventory":
        problem = check_inventory(Path(a.csv))
        print(f"INVENTORY {'INVALID: ' + problem if problem else 'OK'}")
        return 1 if problem else 0

    root = Path(a.folder)
    if not root.is_dir():
        print(f"ERROR: {root} is not a folder")
        return 2
    try:
        slug = find_slug(root, a.slug)
        if not (root / "kickoff" / slug / f"{slug}-context.md").is_file():
            print(f"ERROR: kickoff/{slug}/{slug}-context.md not found; new-build-kickoff has to run first")
            return 2
        client, rows = build(root, slug, a.kit, a.content, a.signoff)
    except SystemExit as e:
        print(e)
        return 2
    report = render(client, slug, a.date, rows)
    if not a.dry_run:
        out = root / "handoff" / slug / f"{slug}-week-1-handoff.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report, encoding="utf-8")
        print(f"Wrote {rel(root, out)}\n")
    print(report, end="")
    return 1 if any(r.blocking for r in rows) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
