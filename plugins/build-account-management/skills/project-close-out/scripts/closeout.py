#!/usr/bin/env python3
"""Close-out package for a launched website build.

Commands (run from the client's working folder):

  facts    --slug S [options]            print every fact the package uses, as JSON
  scaffold --slug S [options] [--force]  write the three close-out files with every
                                         script-made table filled and [WRITE: ...] slots
  check    --slug S [options]            check the three files; ends RESULT: PASS or FAIL
  contract golive|roadmap|index <file>   print what this skill reads from a go-live email,
                                         a roadmap or a dev handoff index, as JSON
  contract --validate <fixture.json>     accept a contract fixture (go-live email, roadmap,
                                         launch check, case study, feedback, BugHerd status)

Options (give the same ones to scaffold and check):
  --root DIR            working folder (default .)
  --launch YYYY-MM-DD   launch date; else the go-live email's Launch: line
  --date YYYY-MM-DD     written date (default today)
  --am "Name"           the Account Manager who signs and is the main contact
  --cadence "text"      reporting and check-in rhythm (default: monthly report and call)
  --clickup-list "Space > List"   where the monthly tasks live

Exit codes: 0 PASS or written, 1 FAIL or refused, 2 usage.
Standard library only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILLS = HERE.parent.parent
ROADMAP_PY = SKILLS / "retainer-roadmap" / "scripts" / "roadmap.py"
CASE_STUDY_PY = SKILLS / "case-study" / "scripts" / "case_study.py"

DONE = ("done", "closed", "archived")  # week-5-handoff-check: anything else is open
SIGN_ROLE = "Account Manager, WISE Digital Partners"
DEFAULT_CADENCE = "a monthly report and a monthly check-in call"
DEFAULT_SPACE = "Client Monthly Work"
GROUPS = ["Homepage", "Service Pages", "Location Pages", "About Page", "Contact Page", "Resource Pages",
          "Blog Posts", "Pages Without a Template"]

SUMMARY_HEADER = ["Client:", "Launch:", "Written:", "Go-live email:", "Launch check:", "Roadmap:", "Case study:"]
SUMMARY_SECTIONS = ["Build Complete", "What We Built", "Strategic Decisions", "Content Produced",
                    "Outstanding Items", "Roadmap"]
EMAIL_HEADER = ["Client:", "To:", "Launch:", "Account manager:"]
HANDOFF_HEADER = ["Client:", "Launch:", "Written:", "Roadmap:", "ClickUp:"]
HANDOFF_SECTIONS = ["Client Quick Reference", "Month 1 Priorities", "Content Status", "Google Business Profile",
                    "Technical Debt", "Communication Preferences", "ClickUp Location"]

NUMBER_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
                "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
                "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20}
PAGES_RX = re.compile(r"\b(\d+|" + "|".join(NUMBER_WORDS) + r")\b((?:[ \t]+[A-Za-z-]+){0,2})[ \t]+pages?\b", re.I)
WORDS_RX = re.compile(r"\b(\d[\d,]*)\s+(?:new\s+)?words\b", re.I)
INTERNAL = [
    (re.compile(r"\bQA\b"), "QA"), (re.compile(r"bugherd", re.I), "BugHerd"),
    (re.compile(r"clickup", re.I), "ClickUp"), (re.compile(r"\b(?:QA|CE)-[0-9a-f]{6,}"), "a finding id"),
    (re.compile(r"\bcritical\b|\bmajor\b|\bminor\b", re.I), "a severity"),
    (re.compile(r"\bNO-GO\b|\bGO\b"), "GO/NO-GO"), (re.compile(r"\bhand-?off\b", re.I), "handoff"),
    (re.compile(r"\bdeferr", re.I), "deferred"), (re.compile(r"carry-?over", re.I), "carry-over"),
    (re.compile(r"seo-drift-monitor|drift monitor", re.I), "seo-drift-monitor"),
    (re.compile(r"\btier [123]\b", re.I), "keyword tiers"), (re.compile(r"\bSOW\b"), "SOW"),
    (re.compile(r"scope change", re.I), "scope change"), (re.compile(r"technical debt", re.I), "technical debt"),
    (re.compile(r"\bdev index\b|dev handoff", re.I), "dev index"), (re.compile(r"\bLIVE (?:OK|ISSUES)\b"), "launch check result"),
]
SCHEMA_RX = re.compile(r"structured data|\bschemas?\b|json-?ld|rich (?:result|snippet)s?|\bmarkup\b|star ratings? in (?:search|google)", re.I)
UNNAMED = {"live chat": re.compile(r"\bchat\b", re.I), "Juvo": re.compile(r"\bjuvo\b", re.I)}
REPORT_RX = re.compile(r"\breport", re.I)
CHECKIN_RX = re.compile(r"check-?in|\bcall\b|\bmeeting\b", re.I)
CONTACT_RX = re.compile(r"(?:main|first|primary|day-to-day|go-to)\s+(?:point of\s+)?contact|point of contact", re.I)
MONTHS_RX = re.compile(r"\b(?:next|first|coming)\s+(?:three|3)\s+months\b|\bthree-month\b|\b3-month\b", re.I)
TYPE_WORDS = {"service": "Service Pages", "location": "Location Pages", "area": "Location Pages", "about": "About Page",
              "team": "About Page", "contact": "Contact Page", "home": "Homepage", "resource": "Resource Pages",
              "blog": "Blog Posts", "guide": "Resource Pages"}
MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
               "October", "November", "December"]


def die(msg: str) -> None:
    print(f"REFUSED: {msg}")
    sys.exit(1)


def read(p: Path | None) -> str:
    try:
        return p.read_text(encoding="utf-8") if p and p.is_file() else ""
    except OSError:
        return ""


def header(text: str, key: str) -> str:
    m = re.search(rf"(?m)^{re.escape(key)}[ \t]*(.*?)\s*$", text)
    return m.group(1).strip() if m else ""


def section(text: str, name: str, level: str = "##") -> str:
    m = re.search(rf"(?m)^{level} {re.escape(name)}\s*$", text)
    if not m:
        return ""
    rest = text[m.end():]
    n = re.search(rf"(?m)^#{{1,{len(level)}}} ", rest)
    return rest[: n.start()] if n else rest


def cells(line: str) -> list[str]:
    return [c.strip() for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]


def table(text: str, head: str | None = None) -> list[dict]:
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        if ln.strip().startswith("|") and (head is None or ln.strip() == head):
            cols = cells(ln)
            rows = []
            for row in lines[i + 2:]:
                if not row.strip().startswith("|"):
                    break
                v = cells(row)
                rows.append(dict(zip(cols, v + [""] * (len(cols) - len(v)))))
            return rows
    return []


def newest(folder: Path, pattern: str) -> Path | None:
    files = [p for p in folder.glob(pattern) if re.search(r"\d{4}-\d{2}-\d{2}", p.name)] if folder.is_dir() else []
    return max(files, key=lambda p: re.findall(r"\d{4}-\d{2}-\d{2}", p.name)[-1]) if files else None


def untag(s: str) -> str:
    return re.sub(r"\s*\[[a-z ,]+\]\s*$", "", s).strip()


def fmt(n: int) -> str:
    return f"{n:,}"


def word_count(md: str) -> int:
    """Same rule as case-study: drop comments and tags, keep link text, count tokens with a letter or digit."""
    md = re.sub(r"<!--.*?-->", " ", md, flags=re.S)
    md = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", md)
    md = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", md)
    md = re.sub(r"<[^>]+>", " ", md)
    return sum(1 for w in re.split(r"\s+", md) if re.search(r"[A-Za-z0-9]", w))


def esc(s: str) -> str:
    return s.replace("|", "\\|").replace("\n", " ").strip()


# ---------------------------------------------------------------- readers

def read_index(text: str) -> dict:
    pages, group = [], None
    for block in re.split(r"(?m)^(?=##+ )", text):
        m = re.match(r"(#+) (.+)", block)
        if not m:
            continue
        if len(m.group(1)) == 2:
            group = m.group(2).strip()
            continue
        if len(m.group(1)) != 3 or not group or group == "Global":
            continue
        f = {k: header(block, f"- {k}:") for k in ("Page", "URL", "Content file", "Priority", "Status")}
        if f["Page"]:
            pages.append(dict(f, group=group))
    redirects = table(section(text, "Redirects", "###"), "| Old URL | New URL | Note |")
    last = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
    return {"pages": pages, "redirects": redirects, "result": last[-1] if last else ""}


def read_qa(text: str) -> dict:
    fh = "| # | Page URL | Department | Severity | Finding | Fix |"
    findings = [{"id": r["#"], "page": r["Page URL"], "department": r["Department"], "severity": r["Severity"],
                 "finding": r["Finding"], "fix": r["Fix"]} for r in table(text, fh) if r.get("#", "none") != "none"]
    rerun = table(text, "| Finding ID | Status | Page URL | Department | Severity | Finding |")
    res = re.findall(r"(?m)^RESULT: (.+?)\s*$", text)
    live = re.sub(r"\s*\(saved pages:.*\)$", "", header(text, "Live:"))
    return {"findings": findings, "rerun": rerun, "result": res[-1] if res else "", "live": live,
            "checked": header(text, "Checked:")}


def read_feedback(text: str) -> dict:
    rows = table(text, "| # | Feedback | Source | Page URL | Class | Department | Action | Task |")
    notes = {m.group(1): m.group(2) for m in
             re.finditer(r"(?m)^- #(\d+) .*?: PM/AM: (.+?)\s*$", section(text, "Scope Changes"))}
    return {"week": header(text, "Week:"), "date": header(text, "Date:"),
            "items": [dict(r, note=notes.get(r["#"], "")) for r in rows]}


def read_golive(text: str) -> dict:
    warnings = [ln for ln in text.splitlines() if ln.startswith("WARNING:")]
    out = {k: header(text, k) for k in ("Client:", "To:", "Week 5 handoff:", "Pages launching:", "Launch:",
                                        "Integrations:", "Subject:")}
    out["warnings"] = warnings
    return out


def read_roadmap(text: str) -> dict:
    head = "| Month | Task | Description | Priority | Est. hours | Owner | Source |"
    rows = table(text, head)
    out = {k: header(text, k) for k in ("Client:", "Date:", "Launch check:", "Live site:")}
    out["has_table"] = head in text
    out["rows"] = rows
    out["not_planned"] = [ln[2:].strip() for ln in section(text, "Not Planned").splitlines() if ln.startswith("- ")]
    return out


def read_context(text: str) -> dict:
    snap = {}
    for ln in section(text, "Snapshot").splitlines():
        m = re.match(r"- ([A-Za-z ]+): (.+)$", ln)
        if m:
            snap[m.group(1).strip()] = untag(m.group(2))
    bullets = [untag(ln[2:]) for ln in text.splitlines() if ln.startswith("- ")]
    comms = [b for b in bullets if re.search(r"\bprefer|communicat", b, re.I)]
    gbp = [b for b in bullets if re.search(r"google business profile|\bGBP\b", b, re.I)]
    conv = [b for b in (untag(ln[2:]) for ln in section(text, "Goals and Conversion").splitlines()
                        if ln.startswith("- ")) if re.match(r"(Primary|Second|Main) ", b)]
    return {"client": header(text, "Client:"), "snapshot": snap, "communication": comms, "gbp": gbp,
            "conversions": conv}


def read_voice(text: str) -> str:
    for r in table(section(text, "Tone Matrix")):
        if r.get("Context", "").strip().lower().startswith("email"):
            return f"{r.get('Tone shift', '')} | {r.get('Example line', '')}"
    return ""


def run_sibling(script: Path, args: list[str], root: Path) -> tuple[bool | None, str]:
    """Run a sibling skill's check. None means the script is not installed next to this skill."""
    if not script.is_file():
        return None, f"{script.parent.parent.name}'s check script is not installed next to this skill"
    try:
        p = subprocess.run([sys.executable, str(script)] + args, cwd=root, capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired) as e:
        return False, f"could not run {script.name}: {e}"
    out = (p.stdout + p.stderr).strip().splitlines()
    fails = [ln.strip() for ln in out if re.search(r"\bFAIL\b", ln)]
    return p.returncode == 0, (fails[0] if fails else (out[-1] if out else ""))[:220]


# ---------------------------------------------------------------- inputs

class Inputs:
    def __init__(self, a):
        self.root = Path(a.root)
        self.slug = s = a.slug
        R = self.root
        self.p_context = R / "kickoff" / s / f"{s}-context.md"
        self.p_index = R / "handoff" / s / f"{s}-dev-handoff-index.md"
        if not self.p_context.is_file():
            die(f"{self.rel(self.p_context)} is missing: run new-build-kickoff first")
        if not self.p_index.is_file():
            die(f"{self.rel(self.p_index)} is missing: run dev-handoff-index first")
        self.context = read_context(read(self.p_context))
        self.client = self.context["client"] or s
        self.index = read_index(read(self.p_index))
        self.p_golive = R / "emails" / s / f"{s}-go-live-email.md"
        self.golive = read_golive(read(self.p_golive)) if self.p_golive.is_file() else None
        self.launch = a.launch or ""
        self.launch_from = "given" if a.launch else ""
        if not self.launch and self.golive:
            m = re.search(r"\d{4}-\d{2}-\d{2}", self.golive["Launch:"])
            if m:
                self.launch, self.launch_from = m.group(0), self.rel(self.p_golive)
        if not self.launch:
            die("no launch date: the go-live email has none (or is missing). Ask the PM and pass --launch YYYY-MM-DD")
        self.date = a.date or dt.date.today().isoformat()
        qa = R / "qa" / s
        self.p_staging = newest(qa, f"{s}-staging-qa-*.md")
        self.staging = read_qa(read(self.p_staging)) if self.p_staging else None
        self.p_launchcheck = newest(qa, f"{s}-launch-check-*.md")
        self.launchcheck = read_qa(read(self.p_launchcheck)) if self.p_launchcheck else None
        self.p_status = qa / f"{s}-bugherd-status.json"
        self.status = {}
        if self.p_status.is_file():
            try:
                self.status = {t["finding_id"]: t for t in json.loads(read(self.p_status)).get("tasks", [])}
            except (json.JSONDecodeError, KeyError, TypeError, AttributeError):
                die(f"{self.rel(self.p_status)} is not a BugHerd status file")
        self.feedback = []
        fb = R / "feedback" / s
        for p in sorted(fb.glob("*-feedback.md")) if fb.is_dir() else []:
            f = read_feedback(read(p))
            if f["week"] == "5":
                self.feedback.append((p, f))
        self.p_roadmap = R / "roadmap" / s / f"{s}-seo-roadmap.md"
        self.roadmap = read_roadmap(read(self.p_roadmap)) if self.p_roadmap.is_file() else None
        self.p_month1 = R / "roadmap" / s / f"{s}-month-1-tasks.md"
        self.p_plan = R / "roadmap" / s / f"{s}-clickup-tasks.json"
        self.plan = None
        if self.p_plan.is_file():
            try:
                self.plan = json.loads(read(self.p_plan))
            except json.JSONDecodeError:
                self.plan = None
        self.p_case = R / "case-study" / s / f"{s}-case-study.md"
        self.case = {k: header(read(self.p_case), k) for k in ("Feature consent:", "Launch:")} if self.p_case.is_file() else None
        kits = sorted((R / "client-reference").glob("*/voice.md")) if (R / "client-reference").is_dir() else []
        pick = [k for k in kits if k.parent.name == s] or kits[:1]
        self.p_voice = pick[0] if pick else None
        self.voice = read_voice(read(self.p_voice)) if self.p_voice else ""
        self.p_blueprint = R / "blueprint" / s / f"{s}-growth-blueprint.md"
        self.am = a.am or ""
        self.cadence = a.cadence or DEFAULT_CADENCE
        self.clickup_given = a.clickup_list or ""
        self.warnings: list[str] = []
        self._counts()

    def rel(self, p: Path | None) -> str:
        if p is None:
            return "none"
        try:
            return p.resolve().relative_to(self.root.resolve()).as_posix()
        except ValueError:
            return p.as_posix()

    # counts -------------------------------------------------------
    def _counts(self):
        built, missing, later = [], [], []
        for p in self.index["pages"]:
            if p["Priority"].lower() != "build":
                later.append(p)
                continue
            f = self.root / p["Content file"] if p["Content file"] else None
            if f and f.is_file():
                built.append(dict(p, words=word_count(read(f))))
            else:
                missing.append(p)
        for p in missing:
            self.warnings.append(f"Build page {p['Page']} has no content file ({p['Content file'] or 'none named'}); "
                                 "it is left out of the counts")
        self.built, self.later = built, later
        self.by_type = {}
        for p in built:
            self.by_type[p["group"]] = self.by_type.get(p["group"], 0) + 1
        self.words = sum(p["words"] for p in built)
        targeted = [r for r in self.index["redirects"] if r.get("New URL", "").startswith("/")]
        failing = set()
        if self.launchcheck:
            for f in self.launchcheck["findings"]:
                if self.status.get(f["id"], {}).get("status", "").lower() not in DONE:
                    failing.add(f["page"].rstrip("/"))
        def old_path(u: str) -> str:
            return re.sub(r"^https?://[^/]+", "", u).rstrip("/")
        self.redirect_failing = [r for r in targeted if old_path(r["Old URL"]) in failing or r["Old URL"].rstrip("/") in failing]
        self.redirected = [r for r in targeted if r not in self.redirect_failing]
        self.no_target = [r for r in self.index["redirects"] if not r.get("New URL", "").startswith("/")]

    def live_url(self) -> str:
        if self.launchcheck and self.launchcheck["live"]:
            return self.launchcheck["live"].split()[0]
        w = self.context["snapshot"].get("Website", "")
        return ("https://" + w) if w and not w.startswith("http") else (w or "unknown")

    def contact(self) -> str:
        c = self.context["snapshot"].get("Primary contact") or self.context["snapshot"].get("Contact") or ""
        return c.split(",")[0].strip()

    # roadmap lookups ---------------------------------------------
    @staticmethod
    def _names(needle: str, text: str) -> re.Match | None:
        return re.search(re.escape(needle) + r"(?![\w/#-])", text) if needle else None

    def roadmap_task_for(self, needle: str) -> str:
        if not self.roadmap:
            return "not in a roadmap (no roadmap yet)"
        for r in self.roadmap["rows"]:
            if self._names(needle, r.get("Source", "")):
                return f'Roadmap Month {r["Month"]}: "{r["Task"]}"'
        for ln in self.roadmap["not_planned"]:
            m = self._names(needle, ln)
            if m:
                reason = re.sub(r"^[^:]*?:\s*", "", ln[m.end():], count=1) if ":" in ln[m.end():] else ln
                return "Roadmap: Not Planned (" + reason.strip().rstrip(".") + ")"
        return "not in the roadmap"

    def in_roadmap(self, needle: str) -> bool:
        return bool(self.roadmap) and any(self._names(needle, r.get("Source", "")) for r in self.roadmap["rows"])

    # outstanding --------------------------------------------------
    def tech_items(self) -> list[dict]:
        """QA and launch-check items still open, and old URLs without a 301 target."""
        out = []
        if self.staging:
            src = self.rel(self.p_staging)
            for f in self.staging["findings"]:
                st = self.status.get(f["id"], {})
                if st.get("status", "").lower() in DONE:
                    continue
                why = (f"Deferred at the Week 5 sweep: {st['deferred']}" if st.get("deferred")
                       else f"Still open after the staging QA of {self.staging['checked']}")
                out.append({"id": f["id"], "kind": "staging", "source": f"{src} > {f['id']}",
                            "text": f"{f['id']} {f['page']} ({f['severity']}, {f['department']}): {f['finding']} {why}."})
        if self.launchcheck:
            src = self.rel(self.p_launchcheck)
            for f in self.launchcheck["findings"]:
                st = self.status.get(f["id"], {})
                if st.get("status", "").lower() in DONE:
                    continue
                out.append({"id": f["id"], "kind": "launch", "source": f"{src} > {f['id']}",
                            "text": f"{f['id']} {f['page']} ({f['severity']}, {f['department']}): {f['finding']} "
                                    f"Open on the launch check of {self.launchcheck['checked']}."})
        seen = {it["id"] for it in out}
        for fid, st in self.status.items():
            if fid in seen or st.get("status", "").lower() in DONE or not fid.startswith("CE-"):
                continue
            why = f"Deferred at the Week 5 sweep: {st['deferred']}" if st.get("deferred") else "Still open in BugHerd"
            out.append({"id": fid, "kind": "client-edit", "source": f"{self.rel(self.p_status)} > {fid}",
                        "text": f"{fid} (client edit, BugHerd #{st.get('bugherd_task_id', '?')}): {st.get('title', '')} {why}."})
        for r in self.no_target:
            out.append({"id": r["Old URL"], "kind": "redirect", "source": f"{self.rel(self.p_index)} > Redirects: {r['Old URL']}",
                        "text": f"{r['Old URL']}: no 301 target in the dev handoff index ({r.get('Note', '').strip() or 'SEO to decide'})."})
        return out

    def scope_items(self) -> list[dict]:
        out = []
        for p, f in self.feedback:
            for it in f["items"]:
                if it.get("Class") != "Scope Change":
                    continue
                note = f" PM/AM: {it['note'].rstrip('.')}." if it["note"] else ""
                out.append({"id": f"{self.rel(p)} > #{it['#']}", "kind": "scope", "source": f"{self.rel(p)} > #{it['#']}",
                            "text": f"Scope Change #{it['#']} ({self.rel(p)}): {it['Feedback']}{note}"})
        return out

    def outstanding_lines(self) -> list[str]:
        lines = []
        for it in self.tech_items() + self.scope_items():
            needle = it["source"] if it["kind"] == "scope" else it["id"]
            lines.append(f"- {it['text']} {self.roadmap_task_for(needle)}.")
        return lines or ["- none"]

    # build complete ----------------------------------------------
    def build_complete(self) -> list[tuple[str, str, str]]:
        rows = []
        if not self.golive:
            rows.append(("Go-live email written", "no", f"{self.rel(self.p_golive)} not found"))
        elif self.golive["warnings"]:
            rows.append(("Go-live email written", "no",
                         f"{self.rel(self.p_golive)} still has a warning on top: {self.golive['warnings'][0][9:].strip()}"))
        else:
            rows.append(("Go-live email written", "yes", f"{self.rel(self.p_golive)} (Launch: {self.golive['Launch:']})"))
        if not self.launchcheck:
            rows.append(("Launch check LIVE OK, or every issue closed or deferred", "no", "no launch check report in qa/"))
        else:
            src = f"{self.rel(self.p_launchcheck)} (RESULT: {self.launchcheck['result'] or 'none'})"
            open_ = [f for f in self.launchcheck["findings"]
                     if self.status.get(f["id"], {}).get("status", "").lower() not in DONE]
            if self.launchcheck["result"] == "LIVE OK" and not any(f["severity"].upper() in ("CRITICAL", "MAJOR") for f in open_):
                rows.append(("Launch check LIVE OK, or every issue closed or deferred", "yes", src))
            else:
                # a CRITICAL finding on the live site is never "deferred", wherever it is planned
                planned = [f["id"] for f in open_ if f["severity"].upper() != "CRITICAL"
                           and (self.in_roadmap(f["id"]) or self.status.get(f["id"], {}).get("deferred"))]
                left = [f["id"] + (" (CRITICAL)" if f["severity"].upper() == "CRITICAL" else "")
                        for f in open_ if f["id"] not in planned]
                if left or not self.launchcheck["result"]:
                    rows.append(("Launch check LIVE OK, or every issue closed or deferred", "no",
                                 f"{src}; not closed or deferred: {', '.join(left) or 'no RESULT line'}"))
                else:
                    rows.append(("Launch check LIVE OK, or every issue closed or deferred", "yes",
                                 f"{src}; {len(planned)} open, each deferred to the roadmap: {', '.join(planned)}"
                                 if planned else src))
        if not self.roadmap:
            rows.append(("Roadmap written", "no", f"{self.rel(self.p_roadmap)} not found"))
        else:
            ok, why = run_sibling(ROADMAP_PY, ["check", self.rel(self.p_roadmap)], self.root)
            if ok is None:
                ok = self.roadmap["has_table"] and bool(self.roadmap["rows"])
                why = f"table read only ({why})"
            rows.append(("Roadmap written", "yes" if ok else "no", f"{self.rel(self.p_roadmap)}: {why}"))
        if not self.case:
            rows.append(("Case study written", "no", f"{self.rel(self.p_case)} not found"))
        else:
            ok, why = run_sibling(CASE_STUDY_PY, ["check", "--slug", self.slug, "--launch", self.launch], self.root)
            consent = self.case["Feature consent:"] or "unknown"
            if ok is None:
                ok, why = True, f"written, not checked ({why})"
            rows.append(("Case study written", "yes" if ok else "no",
                         f"{self.rel(self.p_case)}: {why}; feature consent: {consent}"))
        return rows

    def clickup(self) -> tuple[str, str]:
        if self.clickup_given:
            return self.clickup_given, "given by the PM"
        if isinstance(self.plan, dict) and self.plan.get("list"):
            return f"{self.plan.get('space') or DEFAULT_SPACE} > {self.plan['list']}", self.rel(self.p_plan)
        return f"{DEFAULT_SPACE} > {self.client}", "default, not confirmed: the list named after the client"

    def month_rows(self, m: str) -> list[dict]:
        return [r for r in (self.roadmap["rows"] if self.roadmap else []) if r.get("Month") == m]

    def facts(self) -> dict:
        return {
            "client": self.client, "slug": self.slug, "launch": self.launch, "launch_from": self.launch_from,
            "live_site": self.live_url(), "contact": self.contact(), "am": self.am or "not named",
            "pages_built": len(self.built), "pages_by_type": self.by_type, "words_written": self.words,
            "old_urls_redirected": len(self.redirected), "no_target_redirects": len(self.no_target),
            "post_launch_pages": [f"{p['Page']} ({p['URL']})" for p in self.later],
            "go_live_email": self.rel(self.p_golive) if self.golive else "none",
            "integrations": self.golive["Integrations:"] if self.golive else "none named",
            "launch_check": self.rel(self.p_launchcheck), "staging_qa": self.rel(self.p_staging),
            "roadmap": self.rel(self.p_roadmap) if self.roadmap else "none",
            "roadmap_months": {m: len(self.month_rows(m)) for m in ("1", "2", "3")},
            "case_study": self.rel(self.p_case) if self.case else "none",
            "voice_email_row": self.voice or "none", "cadence": self.cadence,
            "communication": self.context["communication"], "clickup": self.clickup()[0],
            "outstanding": self.outstanding_lines(), "warnings": self.warnings,
        }


# ---------------------------------------------------------------- rendering

def hours_sum(rows: list[dict]) -> str:
    t = 0.0
    for r in rows:
        try:
            t += float(r.get("Est. hours", "0") or 0)
        except ValueError:
            pass
    return f"{t:g}"


def render_summary(I: Inputs) -> str:
    lc = f"{I.rel(I.p_launchcheck)} (RESULT: {I.launchcheck['result'] or 'none'})" if I.launchcheck else "none"
    L = [f"Client: {I.client}", f"Launch: {I.launch}", f"Written: {I.date}",
         f"Go-live email: {I.rel(I.p_golive) if I.golive else 'none'}", f"Launch check: {lc}",
         f"Roadmap: {I.rel(I.p_roadmap) if I.roadmap else 'none'}",
         f"Case study: {I.rel(I.p_case) if I.case else 'none'}", "",
         f"# Project Close-Out Summary: {I.client}", "", "## Build Complete", "",
         "| # | Item | Done | Evidence |", "|---|---|---|---|"]
    bc = I.build_complete()
    for n, (item, done, ev) in enumerate(bc, 1):
        L.append(f"| {n} | {item} | {done} | {esc(ev)} |")
    L += ["", f"Build complete: {sum(1 for r in bc if r[1] == 'yes')} of {len(bc)}. This table reports; it does not hold "
          "the package back.", "", "## What We Built", "",
          f"Pages: {len(I.built)} (" + ", ".join(f"{g} {n}" for g, n in I.by_type.items()) + ")", "",
          "| Page type | Page | URL |", "|---|---|---|"]
    L += [f"| {p['group']} | {esc(p['Page'])} | {p['URL']} |" for p in I.built]
    L += ["", f"Old URLs redirected: {len(I.redirected)}; not answering on the live site yet: {len(I.redirect_failing)}; "
          f"without a 301 target: {len(I.no_target)}"]
    L.append("Not built for launch: " + ("; ".join(f"{p['Page']} ({p['URL']}, {p['Priority']})" for p in I.later)
                                        if I.later else "none"))
    L += ["", "## Strategic Decisions", "",
          "[WRITE: 3 to 5 bullets, each a decision the build made and why, ending with its source file "
          f"in brackets, from {I.rel(I.p_blueprint) if I.p_blueprint.is_file() else 'the Growth Blueprint'} "
          "(Strategic Positioning, Site Architecture and Content Plan, Growth Strategy) and the client context's "
          "Scope Summary]", "", "## Content Produced", "", "| Page | URL | Words |", "|---|---|---|"]
    L += [f"| {esc(p['Page'])} | {p['URL']} | {fmt(p['words'])} |" for p in I.built]
    L += [f"| Total | {len(I.built)} pages | {fmt(I.words)} |", "", "## Outstanding Items", ""]
    L += I.outstanding_lines()
    L += ["", "## Roadmap", ""]
    if I.roadmap:
        L.append(f"Roadmap: {I.rel(I.p_roadmap)}")
        for m in ("1", "2", "3"):
            rows = I.month_rows(m)
            L.append(f"- Month {m}: {len(rows)} tasks, {hours_sum(rows)} hours")
        L.append(f"Month 1 tasks: {I.rel(I.p_month1) if I.p_month1.is_file() else 'not made yet (retainer-roadmap Month 1 mode, after this close-out)'}")
    else:
        L.append("Roadmap: none yet. Run retainer-roadmap before the retainer starts.")
    return "\n".join(L) + "\n"


def signoff(I: Inputs) -> list[str]:
    return ([I.am] if I.am else []) + [SIGN_ROLE]


def first_name(name: str) -> str:
    return name.split()[0] if name else ""


def render_email(I: Inputs) -> str:
    to = I.contact() or "unknown"
    L = [f"Client: {I.client}", f"To: {to}", f"Launch: {I.launch}", f"Account manager: {I.am or 'not named'}", "",
         "Subject: [WRITE: subject that celebrates the launch, with the client's name]", "",
         f"Hi {first_name(to) or '[WRITE: first name]'},", "",
         "[WRITE: one or two sentences celebrating the launch on the launch date, with something specific to this client]",
         "", "[WRITE: a lead-in line for the bullets]", "",
         "- [WRITE: 3 to 5 bullets, each with a real number from the counts]", "",
         ("[WRITE: the next three months in plain words, from the roadmap's Month 1 to 3 tasks]" if I.roadmap else
          "[WRITE: the next three months: say the plan for the next three months is being finalised and will follow "
          "with the first monthly report; promise nothing specific]"),
         "", f"[WRITE: the reporting and check-in rhythm: {I.cadence}]", "",
         "[WRITE: the Account Manager is the main contact from now on, and how to reach them]", "",
         "[WRITE: one line of thanks]", ""] + signoff(I)
    return "\n".join(L) + "\n"


def render_handoff(I: Inputs) -> str:
    cu, cu_src = I.clickup()
    snap = I.context["snapshot"]
    L = [f"Client: {I.client}", f"Launch: {I.launch}", f"Written: {I.date}",
         f"Roadmap: {I.rel(I.p_roadmap) if I.roadmap else 'none'}", f"ClickUp: {cu}", "",
         f"# Retainer Handoff: {I.client}", "", "## Client Quick Reference", "",
         f"- Business: {I.client}", f"- Live site: {I.live_url()}", f"- Launched: {I.launch}",
         f"- Service area: {snap.get('Service area', 'unknown')}",
         f"- Primary contact: {snap.get('Primary contact') or snap.get('Contact') or 'unknown'}",
         f"- Account Manager (main contact): {I.am or 'not named'}"]
    L += [f"- {c}" for c in I.context["conversions"]]
    L += [f"- Client context: {I.rel(I.p_context)}",
          f"- Growth Blueprint: {I.rel(I.p_blueprint) if I.p_blueprint.is_file() else 'none'}",
          f"- Voice: {I.rel(I.p_voice) if I.p_voice else 'none'}", "", "## Month 1 Priorities", ""]
    rows = I.month_rows("1")
    if rows:
        L += ["| # | Task | Owner | Priority | Est. hours |", "|---|---|---|---|---|"]
        L += [f"| {n} | {esc(r['Task'])} | {r['Owner']} | {r['Priority']} | {r['Est. hours']} |"
              for n, r in enumerate(rows, 1)]
        L += ["", "[WRITE: two or three sentences on what matters most in Month 1 and why, from the table above "
              "and the outstanding items]"]
    else:
        L.append("- No roadmap yet: run retainer-roadmap, then its Month 1 mode, before the first retainer month.")
    L += ["", "## Content Status", "",
          f"- Built for launch: {len(I.built)} pages, {fmt(I.words)} words (per page in the project summary)"]
    L.append("- Not built for launch: " + ("; ".join(f"{p['Page']} ({p['URL']}, {p['Priority']})" for p in I.later)
                                          if I.later else "none"))
    content = [r for r in (I.roadmap["rows"] if I.roadmap else []) if r.get("Owner") == "Content"]
    L.append("- Content planned in the roadmap: " + ("; ".join(f"Month {r['Month']} {r['Task']}" for r in content)
                                                    if content else "none"))
    L += ["", "## Google Business Profile", ""]
    L += [f"- {g}" for g in I.context["gbp"]] or ["- GAP: the client context records nothing about the profile; "
                                                  "the AM confirms access and the website link"]
    gbp_task = next((r for r in (I.roadmap["rows"] if I.roadmap else []) if "business profile" in r.get("Task", "").lower()), None)
    L.append(f"- Roadmap: Month {gbp_task['Month']} \"{gbp_task['Task']}\"" if gbp_task else "- Roadmap: no Business Profile task")
    L += ["", "## Technical Debt", ""]
    tech = I.tech_items()
    L += [f"- {t['text']} {I.roadmap_task_for(t['id'])}." for t in tech] or ["- none"]
    L += ["", "## Communication Preferences", ""]
    L += [f"- {c}" for c in I.context["communication"]] or ["- GAP: not recorded in the client context; the AM asks"]
    L += [f"- Reporting and check-ins: {I.cadence}", f"- Main contact at WISE: {I.am or 'the Account Manager'}"]
    L += ["", "## ClickUp Location", "", f"- List: {cu} ({cu_src})"]
    if isinstance(I.plan, dict):
        tasks = I.plan.get("tasks", [])
        made = sum(1 for t in tasks if isinstance(t, dict) and t.get("clickup_task_id"))
        L.append(f"- Month 1 tasks: {len(tasks)} planned in {I.rel(I.p_plan)}, {made} created in ClickUp")
    else:
        L.append("- Month 1 tasks: not planned yet (retainer-roadmap Month 1 mode)")
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- paths

def paths(I: Inputs) -> dict:
    d = I.root / "closeout" / I.slug
    return {"summary": d / f"{I.slug}-project-summary.md", "email": d / f"{I.slug}-transition-email.md",
            "handoff": d / f"{I.slug}-retainer-handoff.md"}


def cmd_facts(a) -> int:
    I = Inputs(a)
    print(json.dumps(I.facts(), indent=2, ensure_ascii=False))
    return 0


def cmd_scaffold(a) -> int:
    I = Inputs(a)
    P = paths(I)
    if not a.force and any(p.exists() for p in P.values()):
        die("close-out files already exist; pass --force to rewrite them (prose is lost)")
    P["summary"].parent.mkdir(parents=True, exist_ok=True)
    P["summary"].write_text(render_summary(I), encoding="utf-8")
    P["email"].write_text(render_email(I), encoding="utf-8")
    P["handoff"].write_text(render_handoff(I), encoding="utf-8")
    f = I.facts()
    print(f"launch: {I.launch} ({I.launch_from})")
    print(f"live site: {f['live_site']}")
    print(f"counts: {f['pages_built']} pages ({', '.join(f'{g} {n}' for g, n in I.by_type.items())}), "
          f"{fmt(I.words)} words, {f['old_urls_redirected']} old URLs redirected")
    print(f"integrations (from the go-live email): {f['integrations']}")
    print(f"voice, email row: {f['voice_email_row']}")
    print("build complete:")
    for item, done, ev in I.build_complete():
        print(f"  {done:3}  {item}: {ev}")
    print("outstanding:")
    for ln in I.outstanding_lines():
        print(f"  {ln}")
    if not I.contact():
        print("WARN: no primary contact in the client context; ask the PM who the transition email goes to")
    for w in I.warnings:
        print(f"WARN: {w}")
    for p in P.values():
        print(f"WROTE {I.rel(p)}")
    return 0


# ---------------------------------------------------------------- check

def split_header(text: str, n: int) -> tuple[list[str], str]:
    lines = text.splitlines()
    return lines[:n], "\n".join(lines[n:])


def compare_scripted(expected: str, actual: str, sections: list[str], checks: list) -> None:
    """Script-made sections must be unchanged; sections with [WRITE] slots must keep their script-made lines."""
    for name in sections:
        exp, act = section(expected, name).strip(), section(actual, name).strip()
        if not act and f"## {name}" not in actual:
            checks.append((f"section {name}", False, "missing"))
            continue
        if "[WRITE" not in exp:
            checks.append((f"section {name}", exp == act, "unchanged" if exp == act else
                           "differs from what the script makes now; restore it (re-run scaffold --force into a "
                           "scratch copy to see it)"))
        else:
            keep = [ln for ln in exp.splitlines() if ln.strip() and "[WRITE" not in ln]
            lost = [ln for ln in keep if ln not in act.splitlines()]
            prose = [ln for ln in act.splitlines() if ln.strip() and ln not in keep]
            ok = not lost and bool(prose)
            checks.append((f"section {name}", ok, "script lines kept, prose written" if ok else
                           (f"script line changed: {lost[0][:80]}" if lost else "no prose written")))


def check_email(I: Inputs, text: str, checks: list) -> None:
    exp = render_email(I).splitlines()
    head = text.splitlines()[:4]
    checks.append(("email header", head == exp[:4], "matches the sources" if head == exp[:4] else
                   "first four lines must be: " + " / ".join(exp[:4])))
    lines = text.splitlines()
    subj = next((ln for ln in lines if ln.startswith("Subject:")), "")
    checks.append(("email subject", bool(subj[8:].strip()) and "[WRITE" not in subj, subj[:80] or "missing"))
    body_lines = lines[lines.index(subj) + 1:] if subj in lines else []
    while body_lines and not body_lines[0].strip():
        body_lines.pop(0)
    while body_lines and not body_lines[-1].strip():
        body_lines.pop()
    body = "\n".join(body_lines)
    words = word_count(body)
    checks.append(("email length", 0 < words < 300, f"{words} words (under 300)"))
    greet = body_lines[0] if body_lines else ""
    fn = first_name(I.contact())
    ok = bool(re.match(rf"(Hi|Hello|Dear|Good \w+),? {re.escape(fn)}\b", greet)) if fn else bool(greet)
    checks.append(("greeting", ok, greet[:60] or "missing"))
    sig = signoff(I)
    checks.append(("sign-off", body_lines[-len(sig):] == sig, " / ".join(sig)))
    bullets = [ln for ln in body_lines if re.match(r"\s*[-*] ", ln)]
    nb = [b for b in bullets if re.search(r"\d", b)]
    checks.append(("bullets", 3 <= len(bullets) <= 5 and len(nb) == len(bullets),
                   f"{len(bullets)} bullets, {len(nb)} with a number (3 to 5, each with a number)"))
    allowed = allowed_numbers(I)
    nums = [n.replace(",", "") for n in re.findall(r"(?<![\w.])\d[\d,]*(?:\.\d+)?", body)]
    bad = sorted({n for n in nums if n not in allowed})
    checks.append(("numbers", not bad, "every number is a count, the launch date or in the roadmap"
                   if not bad else f"not from the files: {', '.join(bad)}"))
    badp = []
    for m in PAGES_RX.finditer(body):
        v = m.group(1).lower()
        n = NUMBER_WORDS.get(v, int(v) if v.isdigit() else -1)
        between = m.group(2).lower()
        group = next((g for k, g in TYPE_WORDS.items() if re.search(rf"\b{k}", between)), None)
        want = {I.by_type.get(group, 0)} if group else {len(I.built)} | set(I.by_type.values())
        if n not in want:
            badp.append(m.group(0))
    checks.append(("page counts", not badp, "match the dev handoff index" if not badp else f"wrong: {badp[0]}"))
    badw = [m.group(0) for m in WORDS_RX.finditer(body) if int(m.group(1).replace(",", "")) != I.words]
    checks.append(("word count stated", not badw, f"{fmt(I.words)} if stated" if not badw else f"wrong: {badw[0]}"))
    d = dt.date.fromisoformat(I.launch)
    mn = MONTH_NAMES[d.month - 1]
    ok = re.search(rf"{mn}\s+{d.day}(?:st|nd|rd|th)?\b|\b{d.day}(?:st|nd|rd|th)?\s+(?:of\s+)?{mn}|{re.escape(I.launch)}",
                   body) is not None
    checks.append(("launch date", ok, f"{MONTH_NAMES[d.month - 1]} {d.day} named" if ok else
                   f"name the launch date, {MONTH_NAMES[d.month - 1]} {d.day}"))
    checks.append(("next three months", bool(MONTHS_RX.search(body)), "the next three months are described"
                   if MONTHS_RX.search(body) else "say what the next three months hold"))
    ok = bool(REPORT_RX.search(body)) and bool(CHECKIN_RX.search(body))
    checks.append(("reporting cadence", ok, "monthly report and check-in named" if ok else
                   "name the monthly report and the check-in"))
    checks.append(("main contact", bool(CONTACT_RX.search(body)), "AM named as main contact"
                   if CONTACT_RX.search(body) else "say the Account Manager is the main contact"))
    hits = [lab for rx, lab in INTERNAL if rx.search(body)]
    checks.append(("no internal terms", not hits, "client-facing" if not hits else f"found: {', '.join(hits)}"))
    checks.append(("no structured data", not SCHEMA_RX.search(body), "no structured data or schema claim"
                   if not SCHEMA_RX.search(body) else "remove the structured data or schema claim"))
    named = (I.golive["Integrations:"] if I.golive else "").lower()
    extra = [k for k, rx in UNNAMED.items() if rx.search(body) and not rx.search(named)]
    checks.append(("only named integrations", not extra, "none unnamed" if not extra else
                   f"not named on the go-live email: {', '.join(extra)}"))
    live_host = re.sub(r"^www\.", "", re.sub(r"^https?://", "", I.live_url()).split("/")[0].lower())
    links = []
    for u in re.findall(r"(?:https?://|\bwww\.)[^\s)>\]]+", body):
        host = re.sub(r"^www\.", "", re.sub(r"^https?://", "", u).split("/")[0].rstrip(".,").lower())
        if host != live_host:
            links.append(u)
    checks.append(("links", not links, "only the live site" if not links else f"other link: {links[0]}"))
    checks.append(("placeholders", "[WRITE" not in text, "none left" if "[WRITE" not in text else "[WRITE left"))


def allowed_numbers(I: Inputs) -> set[str]:
    s = {str(len(I.built)), str(I.words), str(len(I.redirected)), "1", "2", "3"}
    s |= {str(v) for v in I.by_type.values()}
    d = dt.date.fromisoformat(I.launch)
    s |= {str(d.year), str(d.day), f"{d.day:02d}", str(d.month)}
    extra = " ".join([I.cadence] + I.context["communication"] + [I.golive["Launch:"] if I.golive else ""])
    if I.roadmap:
        extra += " " + " ".join(r.get("Task", "") for r in I.roadmap["rows"] if r.get("Month") in ("1", "2", "3"))
    s |= {n.replace(",", "") for n in re.findall(r"\d[\d,]*(?:\.\d+)?", extra)}
    return s


def cmd_check(a) -> int:
    I = Inputs(a)
    P = paths(I)
    checks: list[tuple[str, bool, str]] = []
    missing = [k for k, p in P.items() if not p.is_file()]
    if missing:
        for k in missing:
            checks.append((f"{k} file", False, f"{I.rel(P[k])} missing: run scaffold"))
    if "summary" not in missing:
        t = read(P["summary"])
        a_date = header(t, "Written:") or I.date
        I.date = a_date
        exp = render_summary(I)
        h, _ = split_header(t, len(SUMMARY_HEADER))
        checks.append(("summary header", h == exp.splitlines()[:len(SUMMARY_HEADER)], "matches the sources"
                       if h == exp.splitlines()[:len(SUMMARY_HEADER)] else "header lines changed or out of date"))
        compare_scripted(exp, t, SUMMARY_SECTIONS, checks)
        sd = section(t, "Strategic Decisions")
        nb = len([ln for ln in sd.splitlines() if ln.startswith("- ")])
        bl = [ln for ln in sd.splitlines() if ln.startswith("- ")]
        nosrc = [b for b in bl if not (re.search(r"\[([^\]]+)\]\s*$", b) and (I.root / re.search(r"\[([^\]]+)\]\s*$", b).group(1).split(";")[0].strip()).is_file())]
        checks.append(("strategic decisions", 3 <= nb <= 5 and not nosrc, f"{nb} bullets (3 to 5), each ending with an existing source file"
                       if not nosrc else f"bullet without an existing [source file]: {nosrc[0][:70]}"))
        checks.append(("summary no structured data", not SCHEMA_RX.search(sd), "none" if not SCHEMA_RX.search(sd)
                       else "remove the structured data or schema decision"))
        checks.append(("summary placeholders", "[WRITE" not in t, "none left" if "[WRITE" not in t else "[WRITE left"))
    if "email" not in missing:
        check_email(I, read(P["email"]), checks)
    if "handoff" not in missing:
        t = read(P["handoff"])
        I.date = header(t, "Written:") or I.date
        exp = render_handoff(I)
        h, _ = split_header(t, len(HANDOFF_HEADER))
        ok = h == exp.splitlines()[:len(HANDOFF_HEADER)]
        checks.append(("handoff header", ok, "matches the sources" if ok else "header lines changed or out of date"))
        compare_scripted(exp, t, HANDOFF_SECTIONS, checks)
        mp = section(t, "Month 1 Priorities")
        checks.append(("handoff no structured data", not SCHEMA_RX.search(mp), "none" if not SCHEMA_RX.search(mp)
                       else "remove the structured data or schema wording"))
        checks.append(("handoff placeholders", "[WRITE" not in t, "none left" if "[WRITE" not in t else "[WRITE left"))
    print("| Check | Result | Detail |")
    print("|---|---|---|")
    for name, ok, det in checks:
        print(f"| {name} | {'PASS' if ok else 'FAIL'} | {esc(det)} |")
    for w in I.warnings:
        print(f"WARN: {w}")
    good = all(ok for _, ok, _ in checks)
    print(f"RESULT: {'PASS' if good else 'FAIL'}")
    return 0 if good else 1


# ---------------------------------------------------------------- contracts

def cmd_contract(a) -> int:
    if a.validate:
        try:
            d = json.loads(read(Path(a.validate)))
        except json.JSONDecodeError as e:
            print(f"invalid JSON: {e}")
            return 1
        kinds = {
            "go-live email": ["Client:", "Launch:", "Pages launching:", "Integrations:"],
            "roadmap": ["Month", "Priority", "Est. hours", "Owner", "Source"],
            "launch check": ["Live:", "## Findings", "RESULT:"],
            "case study": ["Client:", "Launch:", "Feature consent:", "Approved quotes:"],
            "feedback": ["Week:", "Class"],
            "BugHerd status": ["read_on", "tasks"],
        }
        if isinstance(d, list):
            for kind, keys in (("roadmap", kinds["roadmap"]), ("dev index pages", ["Page", "URL", "Content file", "Priority"])):
                if d and all(isinstance(x, dict) and all(k in x for k in keys) for x in d):
                    print(f"OK {kind}")
                    return 0
            print("a list must be roadmap rows or dev index pages")
            return 1
        for kind, keys in kinds.items():
            flat = set(d) if isinstance(d, dict) else set()
            if kind == "feedback" and isinstance(d, dict) and isinstance(d.get("items"), list) and d["items"]:
                flat |= set(d["items"][0])
            if all(k in flat for k in keys):
                print(f"OK {kind}")
                return 0
        print("not a fixture this skill reads (go-live email, roadmap, launch check, case study, feedback, BugHerd status)")
        return 1
    text = read(Path(a.path))
    if not text:
        print("missing file", file=sys.stderr)
        return 1
    if a.kind == "golive":
        out = read_golive(text)
    elif a.kind == "index":
        ix = read_index(text)
        out = [{k: pg[k] for k in ("Page", "URL", "Content file", "Priority")} | {"group": pg["group"]} for pg in ix["pages"]]
    else:
        out = [{k: row.get(k, "") for k in ("Month", "Task", "Priority", "Est. hours", "Owner", "Source")}
               for row in read_roadmap(text)["rows"]]
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("facts", "scaffold", "check"):
        s = sub.add_parser(name)
        s.add_argument("--slug", required=True)
        s.add_argument("--root", default=".")
        s.add_argument("--launch")
        s.add_argument("--date")
        s.add_argument("--am")
        s.add_argument("--cadence")
        s.add_argument("--clickup-list")
        if name == "scaffold":
            s.add_argument("--force", action="store_true")
    c = sub.add_parser("contract")
    c.add_argument("kind", nargs="?", choices=["golive", "roadmap", "index"])
    c.add_argument("path", nargs="?")
    c.add_argument("--validate")
    a = ap.parse_args()
    for k in ("launch", "date"):
        v = getattr(a, k, None)
        if v and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
            ap.error(f"--{k} must be YYYY-MM-DD")
    if a.cmd == "contract" and not a.validate and not (a.kind and a.path):
        ap.error("contract needs golive|roadmap|index <file>, or --validate <fixture>")
    return {"facts": cmd_facts, "scaffold": cmd_scaffold, "check": cmd_check, "contract": cmd_contract}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
