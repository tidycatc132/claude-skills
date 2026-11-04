#!/usr/bin/env python3
"""retainer-roadmap: the launched site's three-month SEO/GEO roadmap and its Month 1 ClickUp plan.

Commands (paths are relative to --root, the client's working folder, default "."):
  scaffold --slug S [--date D] [--keywords P|none] [--competitors P|none] [--force]
           write roadmap/<slug>/<slug>-seo-roadmap.md from the build's files
  check    <roadmap.md | clickup-tasks.json>
           check a roadmap (sources, carry-over, build keywords, no structured data)
           or a Month 1 plan against its task list
  month1   --slug S [--date D] [--list NAME]
           write roadmap/<slug>/<slug>-month-1-tasks.md and <slug>-clickup-tasks.json
  created  <clickup-tasks.json> --list-id ID --task N=CLICKUP_ID [...]
           record the ClickUp ids after the tasks were created
  contract blueprint|keywords|index <file>  print what this skill reads (for contracts)
  contract --validate <fixture.json>      accept a contract fixture
Standard library only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

TABLE_HEADER = "| Month | Task | Description | Priority | Est. hours | Owner | Source |"
M1_HEADER = "| # | Name | Description | Priority | Est. time | Owner | Source |"
MONTHS = ("1", "2", "3")
PRIORITIES = ("high", "medium", "low")
OWNERS = ("SEO", "Content", "AM", "Dev")
CARRY = "launch carry-over"
SPACE = "Client Monthly Work"
CLICKUP_PRIORITY = {"high": "high", "medium": "normal", "low": "low"}
DEPT_OWNER = {"Content": "Content", "SEO": "SEO", "Design": "Dev", "Development": "Dev",
              "Account Management": "AM"}
DONE_STATUSES = ("done", "closed", "complete", "completed", "resolved")
FORBIDDEN = re.compile(r"structured data|\bschema\b|schema markup|json-ld|rich (?:result|snippet)", re.I)
AUTHORITY = re.compile(r"\b(reviews?|citations?|cited|cite|listings?|links?|backlinks?|referring domains?)\b", re.I)
AUTHORITY_SECTIONS = ("Strengths to Learn From", "Weaknesses to Exploit", "Priority Opportunities", "Action Plan")
CARRY_CUES = [("sitemap", "Submit the XML sitemap to Search Console and Bing"),
              ("indexing", "Request indexing for the homepage and top priority pages"),
              ("ga4", "Confirm GA4 and Search Console are connected"),
              ("seo-drift-monitor", "Take a baseline with seo-drift-monitor"),
              ("core web vitals", "Capture Core Web Vitals"),
              ("business profile", "Update the Google Business Profile website link")]


# ---------------------------------------------------------------- small helpers

def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")


def die(msg: str) -> None:
    print(f"STOP: {msg}")
    sys.exit(2)


def header(text: str, key: str) -> str:
    m = re.search(rf"(?m)^{re.escape(key)}\s*(.*?)\s*$", text)
    return m.group(1) if m else ""


def section(text: str, heading: str, level: int = 2) -> str:
    """Body of the first heading that starts with `heading` at this level, up to the next heading
    of the same or a higher level."""
    hashes = "#" * level
    m = re.search(rf"(?m)^{hashes} {re.escape(heading)}.*$", text)
    if not m:
        return ""
    rest = text[m.end():]
    n = re.search(rf"(?m)^#{{1,{level}}} ", rest)
    return rest[: n.start()] if n else rest


def cells(line: str) -> list[str]:
    parts = re.split(r"(?<!\\)\|", line.strip())
    return [c.strip().replace("\\|", "|") for c in parts[1:-1]]


def table(text: str, head: str | None = None) -> list[dict]:
    """Rows of the first markdown table in text (or the one whose header line is `head`)."""
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        if not ln.startswith("|"):
            continue
        if head and ln.strip() != head:
            continue
        cols = cells(ln)
        out = []
        for row in lines[i + 2:]:
            if not row.startswith("|"):
                break
            vals = cells(row)
            if len(vals) == len(cols):
                out.append(dict(zip(cols, vals)))
        return out
    return []


def esc(s: str) -> str:
    return s.replace("|", "\\|").replace("\n", " ").strip()


def newest(folder: Path, pattern: str) -> Path | None:
    files = sorted(p for p in folder.glob(pattern) if re.search(r"\d{4}-\d{2}-\d{2}", p.name))
    return max(files, key=lambda p: re.findall(r"\d{4}-\d{2}-\d{2}", p.name)[-1]) if files else None


def rel(p: Path | None, root: Path) -> str:
    if p is None:
        return "none"
    try:
        return p.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return p.as_posix()


def hours(h: float) -> str:
    return ("%g" % h)


def human_time(h: float) -> str:
    mins = int(round(h * 60))
    hh, mm = divmod(mins, 60)
    return " ".join(x for x in (f"{hh}h" if hh else "", f"{mm}m" if mm else "") if x) or "0m"


# ---------------------------------------------------------------- readers (producer formats)

def read_blueprint(text: str) -> dict:
    ko = section(text, "Keyword Opportunity")
    tiers, more = {}, {}
    for n in (1, 2, 3):
        body = section(ko, f"Tier {n}", 3)
        tiers[f"Tier {n}"] = [r for r in table(body) if r.get("Keyword")]
        m = re.search(r"(\d+) more", body)
        more[f"Tier {n}"] = int(m.group(1)) if m else 0
    gs = section(text, "Growth Strategy")
    phase = lambda n: re.sub(r"\n{3,}", "\n\n", section(gs, f"Phase {n}", 3)).strip()  # noqa: E731
    arch = section(text, "Site Architecture and Content Plan")
    return {"Client:": header(text, "Client:"), "Keyword Opportunity": tiers, "### Phase 2": phase(2),
            "### Phase 3": phase(3), "_more": more, "_sources": re.findall(r"(?m)^Source: (.+)$", text),
            "_sitemap": table(arch)}


def read_calendar(text: str) -> list[dict]:
    body = section(text, "Content Calendar")
    keys = ["Month", "Page", "Primary keyword", "Format", "Why now"]
    return [{k: r.get(k, "") for k in keys} for r in table(body) if r.get("Primary keyword")]


def read_index(text: str) -> dict:
    pages = []
    for block in re.split(r"(?m)^### ", text)[1:]:
        title = block.splitlines()[0].strip()
        url = re.search(r"(?m)^- URL:\s*(\S+)", block)
        pr = re.search(r"(?m)^- Priority:\s*(.+?)\s*$", block)
        if url:
            pages.append({"page": title, "url": url.group(1), "priority": pr.group(1) if pr else ""})
    redirects = table(section(text, "Redirects", 3)) if "### Redirects" in text else []
    return {"client": header(text, "Client:"), "pages": pages, "redirects": redirects}


def read_qa(text: str) -> dict:
    """A staging QA or launch check report: findings table, re-run marks, result, base URL."""
    fh = "| # | Page URL | Department | Severity | Finding | Fix |"
    rh = "| Finding ID | Status | Page URL | Department | Severity | Finding |"
    findings = [{"id": r["#"], "page": r["Page URL"], "department": r["Department"],
                 "severity": r["Severity"], "finding": r["Finding"], "fix": r["Fix"]}
                for r in table(text, fh) if r.get("#", "none") != "none"]
    rerun = table(text, rh) if "## Re-run Status" in text else None
    res = re.findall(r"(?m)^RESULT: (.+?)\s*$", text)
    live = re.sub(r"\s*\(saved pages:.*\)$", "", header(text, "Live:"))
    return {"findings": findings, "rerun": rerun, "result": res[-1] if res else "", "live": live,
            "checked": header(text, "Checked:")}


def read_feedback(text: str) -> dict:
    rows = table(text, "| # | Feedback | Source | Page URL | Class | Department | Action | Task |")
    notes = {}
    for m in re.finditer(r"(?m)^- #(\d+) [^:]*?: PM/AM: (.+?)\s*$", section(text, "Scope Changes")):
        notes[m.group(1)] = m.group(2)
    return {"week": header(text, "Week:"), "date": header(text, "Date:"),
            "items": [dict(r, note=notes.get(r["#"], "")) for r in rows]}


def read_competitors(text: str) -> dict:
    land = table(section(text, "Competitive Landscape"))
    gap = None
    for r in land:
        if "referring domain" in r.get("Metric", "").lower():
            cols = [c for c in r if c != "Metric"]
            num = lambda v: float(re.sub(r"[^\d.]", "", v) or "nan")  # noqa: E731
            own, rivals = num(r[cols[0]]), [(num(r[c]), c) for c in cols[1:]]
            rivals = [x for x in rivals if x[0] == x[0]]
            if rivals and own == own and own < max(rivals)[0]:
                best = max(rivals)
                gap = {"own": r[cols[0]], "own_site": cols[0], "best": r[best[1]], "best_site": best[1]}
    evidence = []
    for sec in AUTHORITY_SECTIONS:
        body = section(text, sec)
        n = 0
        for ln in body.splitlines():
            m = re.match(r"^\s*(?:[-*]|\d+\.)\s+(.+)$", ln)
            if not m:
                continue
            n += 1
            line = m.group(1).strip()
            if not AUTHORITY.search(line):
                continue
            if gap and re.search(r"\b(links?|backlinks?|referring domains?)\b", line, re.I) and not re.search(
                    r"\b(reviews?|citations?|cited|cite|listings?)\b", line, re.I):
                continue  # the referring-domain row already covers it
            evidence.append({"section": sec, "n": n, "text": line})
    return {"gap": gap, "evidence": evidence}


def read_status(path: Path | None) -> dict:
    if not path or not path.exists():
        return {}
    try:
        data = json.loads(read(path))
    except json.JSONDecodeError:
        die(f"{path.name} is not valid JSON")
    if not isinstance(data, dict) or not isinstance(data.get("tasks"), list):
        die(f"{path.name} must be an object with a `tasks` list (the Week 5 sweep's BugHerd status file)")
    return {t.get("finding_id", ""): t for t in data["tasks"] if isinstance(t, dict) and t.get("finding_id")}


# ---------------------------------------------------------------- gathering the build's files

class Inputs:
    def __init__(self, root: Path, slug: str, keywords: str | None = None, competitors: str | None = None):
        self.root, self.slug = root, slug
        self.bp_path = root / "blueprint" / slug / f"{slug}-growth-blueprint.md"
        self.ix_path = root / "handoff" / slug / f"{slug}-dev-handoff-index.md"
        for p, what in ((self.bp_path, "Growth Blueprint"), (self.ix_path, "dev handoff index")):
            if not p.exists():
                die(f"the {what} {rel(p, root)} is missing. Write it first; the roadmap is built from it.")
        self.bp = read_blueprint(read(self.bp_path))
        self.ix = read_index(read(self.ix_path))
        self.client = self.bp["Client:"] or self.ix["client"] or slug
        self.kw_path = self._pick(keywords, "research/keyword-research", r"research/keyword-research/[^;\s]+\.md")
        self.co_path = self._pick(competitors, "seo-reports/competitor-analysis",
                                  r"seo-reports/competitor-analysis/[^;\s]+\.md")
        self.calendar = read_calendar(read(self.kw_path)) if self.kw_path else []
        self.comp = read_competitors(read(self.co_path)) if self.co_path else {"gap": None, "evidence": []}
        qa = root / "qa" / slug
        self.staging_path = newest(qa, f"{slug}-staging-qa-*.md")
        self.staging = read_qa(read(self.staging_path)) if self.staging_path else None
        self.status_path = qa / f"{slug}-bugherd-status.json"
        self.status = read_status(self.status_path)
        self.launch_path = newest(qa, f"{slug}-launch-check-*.md")
        self.launch = read_qa(read(self.launch_path)) if self.launch_path else None
        lt = qa / f"{slug}-launch-bugherd-tasks.json"
        try:
            self.launch_tasks = {t["finding_id"]: t for t in json.loads(read(lt))} if lt.exists() else {}
        except (json.JSONDecodeError, KeyError, TypeError):
            die(f"{rel(lt, root)} is not the launch check's task list")
        self.warnings = []
        if self.kw_path and "Content Calendar" in read(self.kw_path) and not self.calendar:
            self.warnings.append(f"{rel(self.kw_path, root)} has a Content Calendar but no rows with `Month`, `Page` "
                                 "and `Primary keyword` columns; no calendar tasks were made")
        if self.co_path and not self.comp["gap"] and not self.comp["evidence"]:
            self.warnings.append(f"{rel(self.co_path, root)}: no Referring domains row and no review, citation, "
                                 "listing or link lines found; no authority tasks were made")
        self.feedback = []
        fb = root / "feedback" / slug
        for p in sorted(fb.glob("*-feedback.md")) if fb.is_dir() else []:
            f = read_feedback(read(p))
            if f["week"] == "5":
                self.feedback.append((p, f))

    def _pick(self, given: str | None, folder: str, pattern: str) -> Path | None:
        if given:
            if given == "none":
                return None
            p = self.root / given
            if not p.exists():
                die(f"{given} does not exist")
            return p
        for src in self.bp["_sources"]:
            for m in re.findall(pattern, src):
                if (self.root / m).exists() and not m.endswith("-scored.md"):
                    return self.root / m
        d = self.root / folder
        return newest(d, "*.md") if d.is_dir() else None

    def r(self, p: Path | None) -> str:
        return rel(p, self.root)

    def build_urls(self) -> list[str]:
        return [p["url"] for p in self.ix["pages"] if p["priority"].lower() == "build"]

    def build_keywords(self) -> list[str]:
        return [r["Keyword"].lower() for r in self.bp["Keyword Opportunity"]["Tier 1"]]


def task(month, name, desc, prio, est, owner, source, key=None):
    return {"Month": str(month), "Task": name, "Description": desc, "Priority": prio,
            "Est. hours": hours(est), "Owner": owner, "Source": source, "_key": key or source}


def forbidden_skip(text: str, source: str, skipped: list[str] | None) -> bool:
    if FORBIDDEN.search(text):
        if skipped is not None:
            skipped.append(f"- {source}: markup work of this kind is not part of the process or the retainer plan.")
        return True
    return False


def qa_items(I: Inputs, skipped: list[str] | None = None) -> list[dict]:
    """Open items from the newest staging QA (minus tasks done or closed in BugHerd) and the newest
    launch check (its findings are what is still open on the live site)."""
    out = []
    if I.staging:
        src = I.r(I.staging_path)
        for f in I.staging["findings"]:
            st = I.status.get(f["id"], {})
            if st.get("status", "").lower() in DONE_STATUSES:
                continue
            if forbidden_skip(f"{f['finding']} {f['fix']}", f"{src} > {f['id']}", skipped):
                continue
            why = (f"Deferred at the Week 5 sweep: {st['deferred']}." if st.get("deferred")
                   else f"Still open after the staging QA of {I.staging['checked']}.")
            out.append(_qa_task(f, why, f"{src} > {f['id']}"))
    if I.launch:
        src = I.r(I.launch_path)
        for f in I.launch["findings"]:
            if forbidden_skip(f"{f['finding']} {f['fix']}", f"{src} > {f['id']}", skipped):
                continue
            bh = I.launch_tasks.get(f["id"], {}).get("bugherd_task_id")
            out.append(_qa_task(f, f"Open on the launch check of {I.launch['checked']}"
                                   + (f" (BugHerd #{bh})." if bh else "."), f"{src} > {f['id']}"))
    return out


def _qa_task(f: dict, why: str, source: str) -> dict:
    minor = f["severity"].upper() == "MINOR"
    page = f["page"]
    return task(2 if minor else 1, f"{page}: {f['fix'].rstrip('.')}", f"{f['finding']} {why}",
                "low" if minor else "high", 1, DEPT_OWNER.get(f["department"], "Dev"), source, key=f["id"])


def feedback_items(I: Inputs, skipped: list[str] | None = None) -> list[dict]:
    out = []
    for p, f in I.feedback:
        for it in f["items"]:
            if it["Class"] != "Scope Change":
                continue
            if forbidden_skip(f"{it['Feedback']} {it['Action']} {it['note']}", f"{I.r(p)} > #{it['#']}", skipped):
                continue
            desc = f"The client asked: {it['Feedback']}"
            if it["note"]:
                desc += f" PM/AM note: {it['note']}."
            src = f"{I.r(p)} > #{it['#']}"
            out.append(task(1, it["Action"], desc, "medium", 1, "AM", src))
    return out


def carry_over(I: Inputs) -> list[dict]:
    live = (I.launch or {}).get("live") or ""
    site = live or "the live site"
    top = [r.get("URL", "") for r in I.bp["_sitemap"] if r.get("Priority", "").lower().startswith("high")]
    top = [u for u in top if u in I.build_urls()] or ["/"] + [u for u in I.build_urls() if u != "/"][:4]
    if "/" not in top:
        top = ["/"] + top
    descs = [f"Submit {live.rstrip('/') + '/sitemap.xml' if live else 'the live sitemap.xml'} in Google Search "
             "Console and Bing Webmaster Tools, and check both read it without errors.",
             f"Use URL Inspection in Search Console to request indexing for {', '.join(top)}.",
             "Check that GA4 records visits from the live domain and that the Search Console property is verified "
             "for it, and that the two are linked.",
             f"Snapshot every Build page on {site} with seo-drift-monitor so later changes can be compared.",
             f"Record LCP, INP and CLS for {', '.join(top[:3])} on mobile and desktop.",
             f"Point the Google Business Profile website link at {live or 'the live homepage'}."]
    est = [0.5, 1, 0.5, 1, 1, 0.5]
    return [task(1, name, d, "high", e, "SEO", CARRY, key=f"carry:{cue}")
            for (cue, name), d, e in zip(CARRY_CUES, descs, est)]


def redirect_items(I: Inputs) -> list[dict]:
    src = I.r(I.ix_path)
    return [task(1, f"Choose a 301 target for {r['Old URL']}",
                 f"The dev handoff index has no New URL for it ({r.get('Note', '')}). Pick the closest launched page "
                 "and ask Dev to add the redirect.", "high", 0.5, "SEO", f"{src} > Redirects: {r['Old URL']}")
            for r in I.ix["redirects"] if r.get("New URL", "").upper() == "NO TARGET"]


def keyword_items(I: Inputs) -> tuple[list[dict], list[str]]:
    rows, skipped = [], []
    bp, kwp, ixp = I.r(I.bp_path), I.r(I.kw_path), I.r(I.ix_path)
    tiers = I.bp["Keyword Opportunity"]
    tier_of = {}
    for n in (3, 2, 1):
        for r in tiers[f"Tier {n}"]:
            tier_of[r["Keyword"].lower()] = (n, r)
    build_kw, build_urls = set(I.build_keywords()), set(I.build_urls())
    months = []
    for c in I.calendar:
        if c["Month"] not in months:
            months.append(c["Month"])
    planned_kw, planned_url = set(), set()
    for c in I.calendar:
        kw, page = c["Primary keyword"].strip(), c["Page"].strip()
        src = f"{kwp} > Content Calendar: {c['Month']}: {kw}"
        url = page.split()[0] if page.startswith("/") else page
        refresh = "refresh" in page.lower()
        if kw.lower() in build_kw and not refresh:
            skipped.append(f"- {src}: \"{kw}\" is already the main keyword of a page built for launch (Tier 1); "
                           "not planned as new content.")
            continue
        if url in build_urls and not refresh:
            skipped.append(f"- {src}: {url} was built for launch.")
            planned_kw.add(kw.lower())
            continue
        n = tier_of.get(kw.lower(), (0, None))[0]
        month = months.index(c["Month"]) + 1
        if month > 3:
            skipped.append(f"- {src}: the calendar's month {month} is after this three-month plan; SEO adds it to the "
                           "next roadmap.")
            planned_kw.add(kw.lower())
            continue
        name = f"Refresh {url}" if refresh else f"Write and publish {url} ({c['Format']})"
        desc = (f"Keyword: {kw}. Why now: {c['Why now']}. "
                + ("Update the launched page for this keyword." if refresh
                   else "Brief it with content-brief, then write it with seo-content-writer."))
        sources = [src] + ([f"{bp} > Tier {n}: {kw}"] if n in (2, 3) else [])
        rows.append(task(month, name, desc, "high" if n == 2 else "medium", 3 if refresh else 6, "Content",
                         "; ".join(sources)))
        planned_kw.add(kw.lower())
        planned_url.add(url)
    for p in I.ix["pages"]:
        if p["priority"].lower() == "build" or p["url"] in planned_url:
            continue
        rows.append(task(2, f"Write and publish {p['page']} ({p['url']})",
                         f"In the dev handoff index as {p['priority'] or 'not Build'}; it was not built for launch.",
                         "medium", 6, "Content", f"{ixp} > {p['page']}"))
    for n, month, prio, verb in ((2, 2, "medium", "Choose the page that targets"), (3, 3, "low", "Plan content for")):
        for r in tiers[f"Tier {n}"]:
            kw = r["Keyword"]
            if kw.lower() in planned_kw:
                continue
            facts = ", ".join(x for x in (f"{r.get('Monthly searches')} searches a month" if r.get("Monthly searches") else "",
                                          f"difficulty {r.get('Difficulty')}" if r.get("Difficulty") else "") if x)
            rows.append(task(month, f"{verb} \"{kw}\"",
                             f"Keyword: {kw}{f' ({facts})' if facts else ''}. Tier {n} in the Growth Blueprint and not "
                             "in the content calendar: decide whether a launched page takes it or new content is needed.",
                             prio, 2, "SEO", f"{bp} > Tier {n}: {kw}"))
        if I.bp["_more"].get(f"Tier {n}"):
            skipped.append(f"- {bp} > Tier {n}: more: {I.bp['_more'][f'Tier {n}']} more Tier {n} keyword(s) are in the "
                           "keyword report but not in the Blueprint table; SEO picks any to add.")
    return rows, skipped


def authority_items(I: Inputs) -> list[dict]:
    if not I.co_path:
        return []
    cp, out = I.r(I.co_path), []
    g = I.comp["gap"]
    if g:
        out.append(task(2, "Start local link building",
                        f"Referring domains: {g['own']} for {g['own_site']} against {g['best']} for {g['best_site']}. "
                        "Earn links from local directories, partners, sponsorships and press.", "medium", 4, "SEO",
                        f"{cp} > Competitive Landscape: Referring domains"))
    for e in I.comp["evidence"]:
        if FORBIDDEN.search(e["text"]):
            continue
        out.append(task(3, "[WRITE: the authority task this evidence calls for]", f"Evidence: {e['text']}",
                        "medium", 2, "SEO", f"{cp} > {e['section']} #{e['n']}"))
    return out


def skeleton(I: Inputs) -> tuple[list[dict], list[str]]:
    kw_rows, skipped = keyword_items(I)
    rows = carry_over(I) + qa_items(I, skipped) + redirect_items(I) + feedback_items(I, skipped) + kw_rows \
        + authority_items(I)
    order = {p: i for i, p in enumerate(PRIORITIES)}
    rows = sorted(enumerate(rows), key=lambda x: (x[1]["Month"], order[x[1]["Priority"]], x[0]))
    return [r for _, r in rows], skipped


# ---------------------------------------------------------------- scaffold

def roadmap_path(root: Path, slug: str) -> Path:
    return root / "roadmap" / slug / f"{slug}-seo-roadmap.md"


def render_roadmap(I: Inputs, date: str) -> str:
    rows, skipped = skeleton(I)
    launch = f"{I.r(I.launch_path)} (RESULT: {I.launch['result']})" if I.launch else "none"
    fb = "; ".join(I.r(p) for p, _ in I.feedback) or "none"
    head = [f"Client: {I.client}", f"Date: {date}", f"Growth blueprint: {I.r(I.bp_path)}",
            f"Keyword research: {I.r(I.kw_path)}", f"Competitor analysis: {I.r(I.co_path)}",
            f"Dev handoff index: {I.r(I.ix_path)}", f"Staging QA: {I.r(I.staging_path)}",
            f"BugHerd status: {I.r(I.status_path) if I.status_path.exists() else 'none'}",
            f"Launch check: {launch}", f"Week 5 feedback: {fb}",
            f"Live site: {(I.launch or {}).get('live') or 'unknown'}", "",
            f"# SEO/GEO Roadmap: {I.client}", "", "## Summary", "",
            "[WRITE: three to five sentences for the retainer team: what launched, what Month 1 fixes and starts, "
            "what Months 2 and 3 build on, using the Blueprint's Phase 2 and Phase 3.]", "", "## Roadmap", "",
            TABLE_HEADER, "|---|---|---|---|---|---|---|"]
    for r in rows:
        head.append("| " + " | ".join(esc(r[k]) for k in ("Month", "Task", "Description", "Priority", "Est. hours",
                                                           "Owner", "Source")) + " |")
    head += ["", "## Not Planned", ""] + (skipped or ["- none"]) + [""]
    return "\n".join(head)


def cmd_scaffold(a) -> int:
    root = Path(a.root)
    I = Inputs(root, a.slug, a.keywords, a.competitors)
    out = roadmap_path(root, a.slug)
    text = render_roadmap(I, a.date)
    if out.exists() and not a.force:
        die(f"{rel(out, root)} already exists and may hold SEO's edits. Re-run with --force to rebuild it from the "
            "files (edits are lost), or edit it and run check.")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    n = text.count("\n| ") - 1
    writes = text.count("[WRITE")
    print(f"WROTE {rel(out, root)}: {n} tasks, {writes} [WRITE] slot(s) to fill")
    print(f"Inputs: keyword research {I.r(I.kw_path)}; competitor analysis {I.r(I.co_path)}; staging QA "
          f"{I.r(I.staging_path)}; launch check {I.r(I.launch_path)}; Week 5 feedback rounds {len(I.feedback)}")
    for w_ in I.warnings:
        print(f"WARN: {w_}")
    print("Next: write the Summary and every [WRITE] task, adjust months, priorities and hours, then run check.")
    return 0


# ---------------------------------------------------------------- check

def parse_roadmap(text: str) -> tuple[list[dict], str]:
    rows = table(text, TABLE_HEADER)
    return rows, section(text, "Not Planned")


def source_paths(src: str) -> list[str]:
    return [part.split(" > ")[0].strip() for part in src.split(";") if part.strip()]


def check_roadmap(path: Path, root: Path, complete: bool = True) -> list[str]:
    text = read(path)
    errs = []
    rows, not_planned = parse_roadmap(text)
    if TABLE_HEADER not in text:
        return [f"the table header must be exactly `{TABLE_HEADER}`"]
    if not rows:
        errs.append("the roadmap table has no tasks")
    if "[WRITE" in text:
        errs.append(f"{text.count('[WRITE')} [WRITE] slot(s) are still unfilled")
    for m in FORBIDDEN.finditer(text):
        line = text[: m.start()].count("\n") + 1
        errs.append(f"line {line}: \"{m.group(0)}\" - the roadmap never plans structured data or schema work")
    for ln in not_planned.splitlines():
        if ln.startswith("- ") and ln.strip() != "- none":
            m = re.match(r"^- (.+?): (\S.*)$", ln.strip())
            if not m or " > " not in m.group(1) and m.group(1) != CARRY:
                errs.append(f"Not Planned line '{ln.strip()[:70]}' must be `- <Source>: <reason>`")
    summary = section(text, "Summary").strip()
    if not summary:
        errs.append("## Summary is empty")
    build_kw = []
    slug = path.name.split("-seo-roadmap")[0]
    bp = root / "blueprint" / slug / f"{slug}-growth-blueprint.md"
    if bp.exists():
        build_kw = [r["Keyword"].lower() for r in read_blueprint(read(bp))["Keyword Opportunity"]["Tier 1"]]
    carry = []
    for i, r in enumerate(rows, 1):
        where = f"row {i} ({r['Task'][:50]})"
        if r["Month"] not in MONTHS:
            errs.append(f"{where}: Month is '{r['Month']}', use 1, 2 or 3")
        if r["Priority"] not in PRIORITIES:
            errs.append(f"{where}: Priority is '{r['Priority']}', use high, medium or low")
        if r["Owner"] not in OWNERS:
            errs.append(f"{where}: Owner is '{r['Owner']}', use SEO, Content, AM or Dev")
        try:
            h = float(r["Est. hours"])
            if h < 0 or (h == 0 and not r["Description"].startswith("Already done")):
                raise ValueError
        except ValueError:
            errs.append(f"{where}: Est. hours '{r['Est. hours']}' must be a number above 0")
        if not r["Source"].strip():
            errs.append(f"{where}: Source is empty; name the file and row the task came from")
        for sp in source_paths(r["Source"]):
            if sp != CARRY and not (root / sp).is_file():
                errs.append(f"{where}: Source file '{sp}' does not exist in the working folder")
        if r["Source"] == CARRY:
            carry.append(r)
        if r["Owner"] == "Content" and not re.match(r"(?i)(refresh|update)\b", r["Task"]) \
                and not re.search(r"\b(?:QA|CE)-[0-9a-f]{8}\b", r["Source"]):
            blob = f"{r['Task']} {r['Description']}".lower()
            for kw in build_kw:
                if re.search(rf"(?<![\w-]){re.escape(kw)}(?![\w-])", blob):
                    errs.append(f"{where}: \"{kw}\" is already a build page's main keyword; plan new content on "
                                "another keyword, or make it a Refresh of the launched page")
    for cue, name in CARRY_CUES:
        hit = [r for r in carry if cue in f"{r['Task']} {r['Description']}".lower()]
        if not hit:
            errs.append(f"launch carry-over task missing: \"{name}\" (Source `{CARRY}`)")
        elif any(r["Month"] != "1" for r in hit):
            errs.append(f"launch carry-over task \"{name}\" must be in Month 1")
    # every item the files call for is planned or explained (roadmap mode; Month 1 mode adds new ones)
    if not complete:
        return errs
    try:
        I = Inputs(root, slug, _hdr_pick(text, "Keyword research:"), _hdr_pick(text, "Competitor analysis:"))
        want, _ = skeleton(I)
        have = " ;; ".join(r["Source"] for r in rows) + " ;; " + not_planned
        for w in want:
            if w["Source"] == CARRY:
                continue
            key = w["Source"].split(";")[0].strip()
            if key not in have:
                errs.append(f"\"{w['Task'][:60]}\" ({key}) is missing: keep its row, or move it to ## Not Planned as "
                            f"`- {key}: <reason>`")
    except SystemExit:
        errs.append("could not re-read the build's files to compare (see STOP above)")
    return errs


def _hdr_pick(text: str, key: str) -> str | None:
    v = header(text, key)
    return v or None


def check_plan(path: Path, root: Path) -> list[str]:
    errs = []
    try:
        plan = json.loads(read(path))
    except json.JSONDecodeError as e:
        return [f"{path.name} is not valid JSON: {e}"]
    md = path.with_name(path.name.replace("-clickup-tasks.json", "-month-1-tasks.md"))
    if not md.exists():
        return [f"{md.name} is missing beside the plan"]
    rows = table(read(md), M1_HEADER)
    tasks = plan.get("tasks", [])
    if plan.get("space") != SPACE:
        errs.append(f"space must be '{SPACE}'")
    if len(rows) != len(tasks):
        errs.append(f"task list has {len(rows)} rows but the plan has {len(tasks)} tasks")
    for i, (r, t) in enumerate(zip(rows, tasks), 1):
        args = t.get("call", {}).get("args", {})
        if t.get("call", {}).get("tool") != "clickup_create_task":
            errs.append(f"task {i}: tool must be clickup_create_task")
        if r["#"] != str(i) or args.get("name") != r["Name"]:
            errs.append(f"task {i}: name differs from the task list row")
        if args.get("priority") != CLICKUP_PRIORITY.get(r["Priority"]):
            errs.append(f"task {i}: priority {args.get('priority')} does not match {r['Priority']}")
        if t.get("source") != r["Source"]:
            errs.append(f"task {i}: source differs from the task list row")
        if not str(args.get("time_estimate", "")).isdigit():
            errs.append(f"task {i}: time_estimate must be whole minutes")
        if FORBIDDEN.search(json.dumps(args)):
            errs.append(f"task {i}: mentions structured data or schema")
        if args.get("assignees"):
            errs.append(f"task {i}: assignees are set at creation by the SEO, never stored in the plan")
    return errs


def cmd_check(a) -> int:
    root, p = Path(a.root), Path(a.root) / a.file
    if not p.exists():
        p = Path(a.file)
    if not p.exists():
        die(f"{a.file} does not exist")
    errs = check_plan(p, root) if p.suffix == ".json" else check_roadmap(p, root)
    if errs:
        print(f"CHECK FAIL {p.name}")
        for e in errs:
            print(f"  - {e}")
        return 1
    if p.suffix == ".json":
        print(f"CHECK PASS {p.name}: plan matches the Month 1 task list row for row")
    else:
        rows, _ = parse_roadmap(read(p))
        by = {m: sum(1 for r in rows if r["Month"] == m) for m in MONTHS}
        print(f"CHECK PASS {p.name}: {len(rows)} tasks (Month 1 {by['1']}, Month 2 {by['2']}, Month 3 {by['3']}), "
              "every task has a Source, launch carry-over present, no build keyword planned as new content")
    return 0


# ---------------------------------------------------------------- Month 1 mode

def fixed_ids(I: Inputs) -> set[str]:
    out = set()
    if I.launch and I.launch["rerun"]:
        out |= {r["Finding ID"] for r in I.launch["rerun"] if r.get("Status") == "FIXED"}
    out |= {k for k, v in I.status.items() if v.get("status", "").lower() in DONE_STATUSES}
    if I.launch and I.launch_path:
        # a launch finding from an earlier report that the newest launch check no longer lists is fixed
        out |= {r["Finding ID"] for r in (I.launch["rerun"] or []) if r.get("Status") == "FIXED"}
    return out


def cmd_month1(a) -> int:
    root = Path(a.root)
    rp = roadmap_path(root, a.slug)
    if not rp.exists():
        die(f"{rel(rp, root)} is missing. Write the roadmap first (roadmap mode), then Month 1.")
    errs = check_roadmap(rp, root, complete=False)
    if errs:
        print("STOP: the roadmap fails its check; fix it first:")
        for e in errs:
            print(f"  - {e}")
        return 2
    I = Inputs(root, a.slug, _hdr_pick(read(rp), "Keyword research:"), _hdr_pick(read(rp), "Competitor analysis:"))
    rows, not_planned = parse_roadmap(read(rp))
    fixed = fixed_ids(I)
    keep, left = [], []
    for r in rows:
        if r["Month"] != "1":
            continue
        ids = re.findall(r"\b(?:QA|CE)-[0-9a-f]{8}\b", r["Source"])
        if ids and all(i in fixed for i in ids):
            left.append(f"- {r['Task']} ({r['Source']}): fixed since the roadmap ({', '.join(ids)})")
            continue
        if r["Description"].startswith("Already done"):
            left.append(f"- {r['Task']} ({r['Source']}): already done")
            continue
        keep.append(dict(r, _new=False))
    have = " ;; ".join(r["Source"] for r in rows) + " ;; " + not_planned
    for t in qa_items(I, []) + feedback_items(I, []):
        if t["Month"] != "1":
            continue
        ident = t["_key"] if re.match(r"(?:QA|CE)-", t["_key"]) else t["Source"]
        if ident in have:
            continue
        keep.append(dict(t, _new=True))
    if not keep:
        die("no Month 1 tasks are left to create")
    list_name = a.list or I.client
    out_md = root / "roadmap" / a.slug / f"{a.slug}-month-1-tasks.md"
    out_js = root / "roadmap" / a.slug / f"{a.slug}-clickup-tasks.json"
    old, prev = {}, {}
    if out_js.exists():
        try:
            prev = json.loads(read(out_js))
            for t in prev.get("tasks", []):
                if t.get("clickup_task_id"):
                    old[(t["source"], t["call"]["args"]["name"])] = t["clickup_task_id"]
        except json.JSONDecodeError:
            pass
    launch = f"{I.r(I.launch_path)} (RESULT: {I.launch['result']})" if I.launch else "none"
    lines = [f"Client: {I.client}", f"Date: {a.date}", f"Roadmap: {rel(rp, root)}", f"Launch check: {launch}",
             f"ClickUp: {SPACE} > {list_name}", f"ClickUp plan: {rel(out_js, root)}", "",
             f"# Month 1 Tasks: {I.client}", "", M1_HEADER, "|---|---|---|---|---|---|---|"]
    same_list = prev.get("list") == list_name
    plan = {"client": I.client, "space": SPACE, "list": list_name,
            "list_id": prev.get("list_id", "") if same_list else "",
            "approved_by": prev.get("approved_by", "") if same_list else "", "tasks": []}
    for n, r in enumerate(keep, 1):
        desc = r["Description"] + (" New since the roadmap." if r["_new"] else "")
        h = float(r["Est. hours"])
        lines.append("| " + " | ".join(esc(x) for x in (str(n), r["Task"], desc, r["Priority"], human_time(h),
                                                          r["Owner"], r["Source"])) + " |")
        md_desc = f"{desc}\n\nOwner: {r['Owner']}\nSource: {r['Source']}\nRoadmap: {rel(rp, root)}"
        plan["tasks"].append({"n": n, "source": r["Source"], "clickup_task_id": old.pop((r["Source"], r["Task"]), ""),
                              "call": {"tool": "clickup_create_task",
                                       "args": {"list_id": plan["list_id"], "name": r["Task"], "markdown_description": md_desc,
                                                "priority": CLICKUP_PRIORITY[r["Priority"]],
                                                "time_estimate": str(int(round(h * 60))),
                                                "tags": ["month 1", r["Owner"].lower()]}}})
    lines += ["", "## Left Out", ""] + (left or ["- none"]) + [""]
    out_md.write_text("\n".join(lines), encoding="utf-8")
    out_js.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    errs = check_plan(out_js, root)
    if errs:
        print("CHECK FAIL after writing the plan:", *errs, sep="\n  - ")
        return 1
    new = sum(1 for r in keep if r["_new"])
    print(f"WROTE {rel(out_md, root)} and {rel(out_js, root)}: {len(keep)} tasks ({new} new since the roadmap, "
          f"{len(left)} left out)")
    for line in lines[9:9 + len(keep) + 2]:
        print(line)
    for (src, name), cid in old.items():
        print(f"NOTE: ClickUp task {cid} ({name}; {src}) is no longer in Month 1; close or keep it by hand.")
    print(f"PREVIEW ONLY: nothing is in ClickUp yet. Show this list to the SEO; after they say go, create the "
          f"tasks in {SPACE} > {list_name}, then run created.")
    return 0


def cmd_created(a) -> int:
    p = Path(a.root) / a.plan
    plan = json.loads(read(p))
    ids = {}
    for t in a.task:
        n, _, cid = t.partition("=")
        if not n.isdigit() or not cid:
            die(f"--task '{t}' must be N=CLICKUP_ID")
        ids[int(n)] = cid
    if len(set(ids.values())) != len(ids):
        die("the same ClickUp id is given for two tasks")
    taken = {t["clickup_task_id"]: t["n"] for t in plan["tasks"] if t["clickup_task_id"]}
    for n, cid in ids.items():
        if cid in taken and taken[cid] != n:
            die(f"ClickUp id {cid} is already recorded for task {taken[cid]}")
    for t in plan["tasks"]:
        if t["n"] in ids:
            if t["clickup_task_id"] and t["clickup_task_id"] != ids[t["n"]]:
                die(f"task {t['n']} already has ClickUp id {t['clickup_task_id']}; it was created before")
            t["clickup_task_id"] = ids[t["n"]]
        if a.list_id:
            t["call"]["args"]["list_id"] = a.list_id
    if a.list_id:
        plan["list_id"] = a.list_id
    if a.approved_by:
        plan["approved_by"] = a.approved_by
    p.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    left = [t["n"] for t in plan["tasks"] if not t["clickup_task_id"]]
    print(f"RECORDED {len(ids)} ClickUp id(s) in {p.name}; not yet created: {left or 'none'}")
    return 0


# ---------------------------------------------------------------- contracts

def cmd_contract(a) -> int:
    if a.validate:
        data = json.loads(read(Path(a.validate)))
        if isinstance(data, list):
            bad = [r for r in data if not r.get("Primary keyword") or not r.get("Month")]
            if not data or bad:
                die("calendar rows need `Month` and `Primary keyword`")
            print(f"OK keywords: {len(data)} calendar rows")
        elif "Keyword Opportunity" in data:
            ko = data["Keyword Opportunity"]
            if not all(isinstance(ko.get(f"Tier {n}"), list) for n in (1, 2, 3)):
                die("Keyword Opportunity needs Tier 1, Tier 2 and Tier 3 lists")
            if not ko["Tier 1"] or not all(r.get("Keyword") for t in ko.values() for r in t):
                die("every tier row needs a Keyword, and Tier 1 cannot be empty")
            print(f"OK blueprint: tiers {[len(ko[f'Tier {n}']) for n in (1, 2, 3)]}")
        elif "read_on" in data:
            ts = data.get("tasks")
            if not isinstance(ts, list) or not all(isinstance(t, dict) and {"finding_id", "status", "deferred"} <= set(t)
                                                   for t in ts):
                die("every status task needs finding_id, status and deferred")
            print(f"OK BugHerd status: {len(ts)} tasks, {sum(1 for t in ts if t['deferred'])} deferred")
        elif "### Redirects" in data:
            if not data.get("Build") or not all({"Old URL", "New URL"} <= set(r) for r in data["### Redirects"]):
                die("index needs Build pages and redirect rows with Old URL and New URL")
            print(f"OK index: {len(data['Build'])} Build pages, {len(data['Post-Launch'])} Post-Launch, "
                  f"{len(data['### Redirects'])} redirects")
        elif "Live:" in data:
            if data.get("RESULT:") not in ("LIVE OK", "LIVE ISSUES"):
                die("RESULT: must be LIVE OK or LIVE ISSUES")
            if not isinstance(data.get("tasks"), list):
                die("the launch check needs its task list `tasks`")
            for f in data.get("## Findings") or []:
                if not re.match(r"QA-[0-9a-f]{8}$", f.get("id", "")) or f.get("severity") not in (
                        "CRITICAL", "MAJOR", "MINOR") or f.get("department") not in DEPT_OWNER:
                    die(f"launch finding {f.get('id')} needs a QA- id, a severity and a department")
            print(f"OK launch check: {len(data.get('## Findings') or [])} findings, {data['RESULT:']}")
        elif "Week:" in data and "Class" in data:
            if data["Week:"] != "5":
                die("only Week 5 feedback feeds the roadmap")
            scope = [r for r in data["Class"] if r.get("Class") == "Scope Change"]
            print(f"OK feedback: {len(data['Class'])} items, {len(scope)} Scope Change")
        else:
            die("unknown fixture shape")
        return 0
    text = read(Path(a.file))
    if a.kind == "blueprint":
        d = read_blueprint(text)
        out = {k: d[k] for k in ("Client:", "Keyword Opportunity", "### Phase 2", "### Phase 3")}
    elif a.kind == "index":
        d = read_index(text)
        out = {"Build": [p["url"] for p in d["pages"] if p["priority"].lower() == "build"],
               "Post-Launch": [{"page": p["page"], "url": p["url"]} for p in d["pages"]
                               if p["priority"].lower() != "build"],
               "### Redirects": d["redirects"]}
    else:
        out = read_calendar(text)
    print(json.dumps(out, indent=2))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    today = dt.date.today().isoformat()
    s = sub.add_parser("scaffold")
    s.add_argument("--slug", required=True)
    s.add_argument("--root", default=".")
    s.add_argument("--date", default=today)
    s.add_argument("--keywords")
    s.add_argument("--competitors")
    s.add_argument("--force", action="store_true")
    c = sub.add_parser("check")
    c.add_argument("file")
    c.add_argument("--root", default=".")
    m = sub.add_parser("month1")
    m.add_argument("--slug", required=True)
    m.add_argument("--root", default=".")
    m.add_argument("--date", default=today)
    m.add_argument("--list")
    k = sub.add_parser("created")
    k.add_argument("plan")
    k.add_argument("--root", default=".")
    k.add_argument("--list-id", default="")
    k.add_argument("--approved-by", default="")
    k.add_argument("--task", action="append", default=[])
    t = sub.add_parser("contract")
    t.add_argument("kind", nargs="?", choices=["blueprint", "keywords", "index"])
    t.add_argument("file", nargs="?")
    t.add_argument("--validate")
    a = ap.parse_args()
    if a.cmd == "contract" and not a.validate and not (a.kind and a.file):
        ap.error("contract needs blueprint|keywords <file>, or --validate <fixture>")
    return {"scaffold": cmd_scaffold, "check": cmd_check, "month1": cmd_month1, "created": cmd_created,
            "contract": cmd_contract}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
