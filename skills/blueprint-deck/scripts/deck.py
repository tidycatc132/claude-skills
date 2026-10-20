#!/usr/bin/env python3
"""Growth Blueprint deck: plan scaffold, build, compliance check. Standard library only.

  deck.py scaffold --slug S [--date YYYY-MM-DD] [--force]   write the slide plan to fill in
  deck.py build    --slug S                                  check the plan, render the .pptx, run compliance
  deck.py check    --slug S [--pptx PATH]                    compliance on an existing .pptx (never edits it)
  deck.py sections FILE.json                                 read a Blueprint given as {section: text}

Common flags: --root DIR (working folder, default .), --blueprint, --quotes, --context,
--source FILE (extra file that may name team members; repeatable), --plan, --brand.
Prints a table and a final `RESULT: PASS | NEEDS_INPUT | FAIL` line.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import compliance as C  # noqa: E402
import pptx_writer as W  # noqa: E402

SECTIONS = ["Executive Summary", "Business and Market Overview", "Competitive Analysis", "Strategic Positioning",
            "Keyword Opportunity", "Site Architecture and Content Plan", "Growth Strategy",
            "Measurement and Next Steps"]

ORDER = ["cover", "diagnosis", "cost", "told-us", "divider", "stand-today", "competitors", "threats", "keywords",
         "top-keyword", "divider", "positioning", "site", "not-doing", "divider", "has-to-be-true", "measure",
         "team", "next"]
LABELS = {
    "diagnosis": "The Diagnosis", "cost": "What This Costs You", "told-us": "What You Told Us",
    "stand-today": "Where You Stand Today", "competitors": "Who You're Up Against",
    "threats": "Which Competitors Actually Matter", "keywords": "What You'll Rank For",
    "top-keyword": "Why Your Top Keyword Isn't Month One", "positioning": "How You'll Be Positioned",
    "site": "The Site We're Building", "not-doing": "What We're Not Doing",
    "has-to-be-true": "What Has To Be True", "measure": "How We'll Measure This", "team": "Your Team",
    "next": "What Happens Next",
}
DIVIDERS = [("01", "Where you stand today"), ("02", "The plan"), ("03", "Making it work")]
TIER_TIMING = {"1": "With the new site", "2": "Months 1 to 3", "3": "Months 4 to 6 and beyond"}
KW_CAP = {"1": 8, "2": 4, "3": 3}
GRADES = ["Real threat", "Overstated", "Not a competitor"]
PAGE_TYPES = ["home", "service", "location", "about", "contact", "resource", "other"]
MEASURE_COLS = ["Metric", "Baseline today", "3 months", "6 months", "12 months"]
WRITE = "[WRITE:"
LIMITS = {"headline": 100, "value": 12, "caption": 70, "body": 170, "quote": 220, "point": 150, "why": 220,
          "revisit": 120, "what": 60, "item": 100, "action": 100, "owner": 40, "timing": 40, "role": 45,
          "owns": 90, "message": 150, "keyword": 60, "name": 40, "drives": 30}


# =========================================================================== Blueprint
def md_tables(text: str) -> list[list[list[str]]]:
    """Every markdown table as a list of rows (header first, separator dropped)."""
    tables, cur = [], []
    for line in text.splitlines() + [""]:
        s = line.strip()
        if s.startswith("|") and s.endswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            if not (cur and set("".join(cells)) <= set("-: ")):
                cur.append(cells)
        elif cur:
            tables.append(cur)
            cur = []
    return [t for t in tables if len(t) >= 2]


def split_sections(text: str) -> dict[str, str]:
    parts = re.split(r"(?m)^## (.+?)\s*$", text)
    out = {}
    for i in range(1, len(parts), 2):
        out[parts[i].strip()] = parts[i + 1]
    return out


class Blueprint:
    def __init__(self, sections: dict[str, str], client: str = "", full_text: str = ""):
        self.sections = sections
        self.client = client
        self.text = full_text or "\n".join(f"## {k}\n{v}" for k, v in sections.items())

    @classmethod
    def from_file(cls, path: Path) -> "Blueprint":
        return cls.from_text(path.read_text(encoding="utf-8"))

    @classmethod
    def from_text(cls, text: str) -> "Blueprint":
        client = ""
        m = re.search(r"(?m)^Client:\s*(.+)$", text)
        if m:
            client = m.group(1).strip()
        else:
            m = re.search(r"(?m)^# (.+?):\s*Growth Blueprint", text)
            client = m.group(1).strip() if m else ""
        return cls(split_sections(text), client, text)

    def missing_sections(self) -> list[str]:
        return [s for s in SECTIONS if s not in self.sections]

    def needs(self, section: str) -> str:
        m = C.NEEDS.search(self.sections.get(section, ""))
        return m.group(0) if m else ""

    def competitor_table(self):
        t = md_tables(self.sections.get("Competitive Analysis", ""))
        return t[0] if t else None

    def keyword_rows(self) -> list[dict]:
        body = self.sections.get("Keyword Opportunity", "")
        rows = []
        for m in re.finditer(r"(?ms)^### Tier (\d)\b[^\n]*\n(.*?)(?=^### |\Z)", body):
            tier = m.group(1)
            for t in md_tables(m.group(2))[:1]:
                head = [h.lower() for h in t[0]]
                for r in t[1:]:
                    if len(r) != len(head):
                        continue
                    get = lambda key: next((r[i] for i, h in enumerate(head) if key in h), "")  # noqa: E731
                    rows.append({"keyword": get("keyword"), "searches": get("search") or get("volume"),
                                 "difficulty": get("difficulty") or get("kd"), "intent": get("intent"),
                                 "tier": tier})
        return rows

    def page_count(self):
        body = self.sections.get("Site Architecture and Content Plan", "")
        m = re.search(r"Page count:\s*(\d+)", body)
        cap = re.search(r"(\d+)-page scope", body)
        return (m.group(1) if m else None), (cap.group(1) if cap else None)

    def url_map(self):
        for t in md_tables(self.sections.get("Site Architecture and Content Plan", "")):
            if any(h.lower() == "url" for h in t[0]):
                return t
        return None


def page_type(name: str, url: str, parent: str) -> str:
    n, u = name.lower(), url.lower()
    if u == "/" or n == "home":
        return "home"
    if "contact" in n or "contact" in u:
        return "contact"
    if "location" in n or "service area" in n:
        return "location"
    if any(w in n for w in ("about", "team", "story")):
        return "about"
    if "/services/" in u or "service" in parent.lower():
        return "service"
    if any(w in u for w in ("/blog", "/resources", "/guides")):
        return "resource"
    return "other"


# =========================================================================== paths
def paths(args) -> dict[str, Path]:
    root = Path(args.root)
    s = args.slug
    out = root / "blueprint" / s
    return {
        "blueprint": Path(args.blueprint) if args.blueprint else out / f"{s}-growth-blueprint.md",
        "quotes": Path(args.quotes) if args.quotes else root / "kickoff" / s / f"{s}-quote-bank.md",
        "context": Path(args.context) if args.context else root / "kickoff" / s / f"{s}-context.md",
        "plan": Path(args.plan) if args.plan else out / f"{s}-deck-plan.json",
        "pptx": Path(getattr(args, "pptx", None) or out / f"{s}-growth-blueprint-deck.pptx"),
        "compliance": out / f"{s}-deck-compliance.md",
        "brand": Path(args.brand) if args.brand else HERE.parent / "assets" / "brand.json",
    }


def rel(p: Path, root: Path) -> str:
    try:
        return p.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return p.as_posix()


# =========================================================================== scaffold
def notes_stub(full=True) -> dict:
    n = {"say": "[WRITE: what the AM says on this slide]"}
    if full:
        n["emphasise"] = "[WRITE: the one number or point to emphasise, copied from the Blueprint]"
        n["pushback"] = "[WRITE: the likely pushback and the answer]"
    return n


def scaffold(args) -> int:
    P = paths(args)
    if not P["blueprint"].exists():
        print(f"MISSING  Blueprint: {P['blueprint']}")
        print("RESULT: FAIL")
        return 1
    if P["plan"].exists() and not args.force:
        print(f"{P['plan']} exists; pass --force to overwrite it.")
        return 1
    bp = Blueprint.from_file(P["blueprint"])
    bank, call_date = ([], "")
    if P["quotes"].exists():
        bank, call_date = C.quote_bank(P["quotes"].read_text(encoding="utf-8"))
    agency = json.loads(P["brand"].read_text(encoding="utf-8")).get("agency", "WISE Digital Partners")
    date = args.date or dt.date.today().isoformat()
    slides = []
    div = iter(DIVIDERS)

    def content(sid, **fields):
        d = {"id": sid, "eyebrow": LABELS[sid],
             "headline": "[WRITE: a full-sentence conclusion, never a topic label]"}
        d.update(fields)
        d["notes"] = notes_stub()
        return d

    stat = {"value": "[WRITE: a figure copied from the Blueprint]", "caption": "[WRITE: one-line caption]"}
    for sid in ORDER:
        if sid == "cover":
            slides.append({"id": "cover", "title": "Growth Blueprint", "prepared_for": f"Prepared for {bp.client}",
                           "by": f"By {agency}", "notes": notes_stub()})
        elif sid == "divider":
            num, head = next(div)
            slides.append({"id": "divider", "number": num, "headline": head, "notes": notes_stub()})
        elif sid == "diagnosis":
            slides.append(content(sid, stats=[dict(stat)],
                                  body=["[WRITE: explanation line 1]", "[WRITE: explanation line 2]"]))
        elif sid == "cost":
            slides.append(content(sid, stats=[dict(stat), dict(stat)], body=[]))
        elif sid == "told-us":
            slides.append(content(sid, quotes=[
                {"text": "[WRITE: a quote copied word for word from the quote bank]", "speaker": "[WRITE]",
                 "date": call_date or "[WRITE: call date]", "drives": "[WRITE: priority, positioning or what to avoid]"}
                for _ in range(3)]))
        elif sid == "stand-today":
            slides.append(content(sid, stats=[dict(stat), dict(stat)], body=[]))
        elif sid == "competitors":
            t = bp.competitor_table()
            if t:
                slides.append(content(sid, table={"columns": t[0], "rows": t[1:]}, caption=""))
            else:
                need = bp.needs("Competitive Analysis") or "[NEEDS INPUT: a saved competitor-analysis report]"
                slides.append(content(sid, needs_input=need))
        elif sid == "threats":
            if bp.competitor_table():
                slides.append(content(sid, items=[{"name": h, "grade": "[WRITE: " + " | ".join(GRADES) + "]",
                                                   "why": "[WRITE: one line of justification]"}
                                                  for h in bp.competitor_table()[0][2:]]))
            else:
                need = bp.needs("Competitive Analysis") or "[NEEDS INPUT: a saved competitor-analysis report]"
                slides.append(content(sid, needs_input=need))
        elif sid == "keywords":
            rows, more = [], 0
            counts = {}
            for r in bp.keyword_rows():
                counts[r["tier"]] = counts.get(r["tier"], 0) + 1
                if counts[r["tier"]] > KW_CAP.get(r["tier"], 3):
                    more += 1
                    continue
                rows.append([r["keyword"], r["searches"], r["difficulty"], r["intent"], f"Tier {r['tier']}",
                             TIER_TIMING.get(r["tier"], "")])
            cap = "Monthly searches and difficulty from our keyword research." + (
                f" The Blueprint lists {more} more keywords." if more else "")
            if rows:
                slides.append(content(sid, table={"columns": ["Keyword", "Monthly searches", "Difficulty", "Intent",
                                                              "Tier", "Time to result"], "rows": rows}, caption=cap))
            else:
                slides.append(content(sid, needs_input=bp.needs("Keyword Opportunity")
                                      or "[NEEDS INPUT: keyword tiers in the Blueprint]"))
        elif sid == "top-keyword":
            slides.append(content(sid, keyword="[WRITE: the client's most aspirational keyword, from the table]",
                                  tier="[WRITE: Tier 2 or Tier 3]", stats=[dict(stat)],
                                  points=["[WRITE: the trade-off in plain language]"] * 2))
        elif sid == "positioning":
            slides.append(content(sid, points=["[WRITE: proof point]"] * 2,
                                  message="[WRITE: the primary message line the homepage will carry]"))
        elif sid == "site":
            n, cap = bp.page_count()
            um = bp.url_map()
            pages = []
            if um:
                head = [h.lower() for h in um[0]]
                for r in um[1:]:
                    g = {h: r[i] for i, h in enumerate(head) if i < len(r)}
                    pages.append({"name": g.get("page", r[0]),
                                  "type": page_type(g.get("page", r[0]), g.get("url", ""), g.get("parent", ""))})
            if n:
                slides.append(content(sid, stats=[{"value": n, "caption": f"pages in the agreed {cap}-page scope"
                                                   if cap else "pages in the agreed scope"}], pages=pages))
            else:
                slides.append(content(sid, needs_input=bp.needs("Site Architecture and Content Plan")
                                      or "[NEEDS INPUT: the page count in the Blueprint]", pages=pages))
        elif sid == "not-doing":
            slides.append(content(sid, items=[{"what": "[WRITE]", "why": "[WRITE: the reason, kept whole]",
                                               "revisit": "[WRITE: what would make it worth revisiting]"}] * 2))
        elif sid == "has-to-be-true":
            it = {"item": "[WRITE]", "owner": "[WRITE: a name]", "blocks": "[WRITE: what it blocks]",
                  "needed_by": "[WRITE: when]"}
            slides.append(content(sid, client=[dict(it)], wise=[dict(it)]))
        elif sid == "measure":
            slides.append(content(sid, table={"columns": list(MEASURE_COLS), "rows": [
                ["[WRITE: metric]", "[WRITE: baseline from the Blueprint, or Not tracked yet]",
                 "[WRITE: direction]", "[WRITE: direction]", "[WRITE: direction]"]]}))
        elif sid == "team":
            people = []
            speakers = []
            for _, sp in bank:
                if sp not in speakers:
                    speakers.append(sp)
            for sp in speakers:
                people.append({"name": sp, "side": "client", "role": "[WRITE]", "owns": "[WRITE]"})
            if P["quotes"].exists():
                m = re.search(r"(?m)^Agency speakers:\s*(.+)$", P["quotes"].read_text(encoding="utf-8"))
                for nm in (m.group(1).split(",") if m else []):
                    if nm.strip():
                        people.append({"name": nm.strip(), "side": "wise", "role": "[WRITE]", "owns": "[WRITE]"})
            slides.append(content(sid, people=people))
        elif sid == "next":
            slides.append(content(sid, actions=[{"action": "[WRITE]", "owner": "[WRITE: a name]",
                                                 "timing": "[WRITE]"}] * 5))
    plan = {"client": bp.client, "date": date, "agency": agency, "slides": slides}
    P["plan"].parent.mkdir(parents=True, exist_ok=True)
    P["plan"].write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    root = Path(args.root)
    print(f"found    Blueprint: {rel(P['blueprint'], root)}")
    print(("found    " if P["quotes"].exists() else "MISSING  ") + f"quote bank: {rel(P['quotes'], root)}")
    print(("found    " if P["context"].exists() else "missing  ") + f"context (team names): {rel(P['context'], root)}")
    for sec in bp.missing_sections():
        print(f"MISSING  Blueprint section: {sec}")
    for s in slides:
        if s.get("needs_input"):
            print(f"NEEDS INPUT  {s['id']}: {s['needs_input']}")
    print(f"wrote    {rel(P['plan'], root)} ({len(slides)} slides)")
    return 0


# =========================================================================== plan checks
class Rows:
    def __init__(self):
        self.rows: list[tuple[str, str, str]] = []

    def add(self, name, state, detail=""):
        self.rows.append((name, state, detail))


def _strings(obj, path=""):
    if isinstance(obj, str):
        yield path, obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from _strings(v, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _strings(v, f"{path}[{i}]")


def check_plan(plan: dict, bp: Blueprint, sources_text: str) -> Rows:
    R = Rows()
    try:
        dt.date.fromisoformat(str(plan.get("date", "")))
    except ValueError:
        R.add("date", "FAIL", f"plan date '{plan.get('date')}' is not YYYY-MM-DD")
        return R
    slides = plan.get("slides", [])
    ids = [s.get("id") for s in slides]
    R.add("slide order", "PASS" if ids == ORDER else "FAIL",
          f"{len(ids)} slides" if ids == ORDER else f"expected {ORDER}, got {ids}")
    if ids != ORDER:
        return R
    by = {}
    for s in slides:
        by.setdefault(s["id"], s)

    left = [p for p, v in _strings(plan) if WRITE in v]
    R.add("placeholders", "PASS" if not left else "FAIL",
          "none left" if not left else f"{len(left)} [WRITE: ...] left: " + ", ".join(left[:6]))

    # headlines
    bad = []
    for s in slides:
        if s["id"] in ("cover", "divider"):
            continue
        h = (s.get("headline") or "").strip()
        label = LABELS[s["id"]].lower()
        if len(h.split()) < 4 or h.lower().rstrip(".") == label or h.endswith("?"):
            bad.append(s["id"])
    R.add("headlines", "PASS" if not bad else "FAIL",
          "every content slide states a conclusion" if not bad else
          "needs a full-sentence conclusion (4+ words, not the slide label, not a question): " + ", ".join(bad))

    # notes
    bad = []
    for i, s in enumerate(slides, 1):
        n = s.get("notes") or {}
        need = ["say", "emphasise", "pushback"]
        if any(not str(n.get(k, "")).strip() for k in need):
            bad.append(f"{i} {s['id']}")
    R.add("notes fields", "PASS" if not bad else "FAIL",
          "say, emphasise and pushback on every slide" if not bad else "incomplete on " + ", ".join(bad))

    def count(sid, key, lo, hi, label):
        n = len(by[sid].get(key) or [])
        ok = lo <= n <= hi or bool(by[sid].get("needs_input"))
        R.add(label, "PASS" if ok else "FAIL", f"{n} (needs {lo} to {hi})")

    count("diagnosis", "stats", 1, 1, "diagnosis: one stat")
    R.add("diagnosis: two lines at most", "PASS" if len(by["diagnosis"].get("body") or []) <= 2 else "FAIL",
          f"{len(by['diagnosis'].get('body') or [])} lines")
    count("cost", "stats", 2, 3, "cost: 2 to 3 stats")
    count("stand-today", "stats", 2, 3, "stand today: 2 to 3 stats")
    count("told-us", "quotes", 3, 4, "told us: 3 to 4 quotes")
    count("not-doing", "items", 2, 5, "not doing: 2 to 5 items")
    count("next", "actions", 5, 7, "next steps: 5 to 7 actions")
    count("positioning", "points", 2, 3, "positioning: 2 to 3 proof points")

    # quote attribution
    bank, call_date = C.quote_bank(sources_text.split("\n\x00QUOTES\x00\n", 1)[-1]) if "\x00QUOTES\x00" in sources_text else ([], "")
    bad = []
    for q in by["told-us"].get("quotes") or []:
        text = C.strip_marks(q.get("text", ""))
        match = [sp for qt, sp in bank if text and text in C.norm_quote(qt)]
        if not match:
            bad.append(f"'{text[:40]}' not in the quote bank")
        elif q.get("speaker", "").strip() not in match:
            bad.append(f"'{text[:40]}' is {match[0]}'s, not {q.get('speaker')}'s")
        elif call_date and q.get("date", "").strip() != call_date:
            bad.append(f"'{text[:40]}' date {q.get('date')} is not the call date {call_date}")
    R.add("quote attribution", "PASS" if not bad else "FAIL",
          "speaker and call date match the quote bank" if not bad else "; ".join(bad[:4]))

    # copied tables
    t = bp.competitor_table()
    comp = by["competitors"]
    if t is None:
        R.add("competitor table", "NEEDS_INPUT" if comp.get("needs_input") else "FAIL",
              "the Blueprint has no competitor table" + ("" if comp.get("needs_input") else
                                                          "; the slide must carry its [NEEDS INPUT: ...] line"))
        for k in ("threats",):
            if by[k].get("items") and not by[k].get("needs_input"):
                R.add("threats without a report", "FAIL", "grade competitors only from a competitor table")
    else:
        tb = comp.get("table") or {}
        same = tb.get("columns") == t[0] and tb.get("rows") == t[1:]
        R.add("competitor table", "PASS" if same else "FAIL",
              "copied from the Blueprint, client column first" if same else
              "must equal the Blueprint's competitor table cell for cell (run scaffold again to copy it)")
        items = by["threats"].get("items") or []
        bad = [i.get("name") for i in items if i.get("grade") not in GRADES]
        R.add("threat grades", "PASS" if items and not bad else "FAIL",
              f"{len(items)} graded" if items and not bad else f"grade must be one of {GRADES}: {bad}")

    kw = {(r["keyword"].lower(), r["searches"].replace(",", ""), r["difficulty"], r["tier"]) for r in bp.keyword_rows()}
    rows = (by["keywords"].get("table") or {}).get("rows") or []
    bad = []
    for r in rows:
        key = (str(r[0]).lower(), str(r[1]).replace(",", ""), str(r[2]), str(r[4]).replace("Tier ", "")) if len(r) >= 5 else None
        if key not in kw:
            bad.append(str(r[0]) if r else "?")
    if not rows:
        R.add("keyword table", "NEEDS_INPUT" if by["keywords"].get("needs_input") else "FAIL", "no keyword rows")
    else:
        R.add("keyword table", "PASS" if not bad else "FAIL",
              f"{len(rows)} rows match the Blueprint's tiers" if not bad else
              "not in the Blueprint with that volume, difficulty and tier: " + ", ".join(bad[:5]))

    n, _ = bp.page_count()
    site = by["site"]
    if n is None:
        R.add("page count", "NEEDS_INPUT" if site.get("needs_input") else "FAIL", "no `Page count:` in the Blueprint")
    else:
        val = str((site.get("stats") or [{}])[0].get("value", "")).strip()
        R.add("page count", "PASS" if val == n else "FAIL",
              f"{val} pages, as in the Blueprint" if val == n else f"callout says {val}; the Blueprint says {n}")
    bad = [p.get("name") for p in site.get("pages") or [] if p.get("type") not in PAGE_TYPES]
    R.add("page types", "PASS" if not bad else "FAIL", "" if not bad else f"type must be one of {PAGE_TYPES}: {bad}")

    tb = by["measure"].get("table") or {}
    ok = tb.get("columns") == MEASURE_COLS and len(tb.get("rows") or []) >= 2
    R.add("measure table", "PASS" if ok else "FAIL",
          f"{len(tb.get('rows') or [])} metrics, targets labelled directional" if ok else
          f"columns must be {MEASURE_COLS} with at least 2 metrics")

    htbt = by["has-to-be-true"]
    bad = []
    for side in ("client", "wise"):
        items = htbt.get(side) or []
        if not items:
            bad.append(f"no {side} items")
        for it in items:
            if any(not str(it.get(k, "")).strip() for k in ("item", "owner", "blocks", "needed_by")):
                bad.append(f"{side} item missing owner, blocks or needed_by")
    R.add("has to be true", "PASS" if not bad else "FAIL",
          "client-owned and WISE-owned items separate" if not bad else "; ".join(sorted(set(bad))))

    bad = [a.get("action", "?")[:30] for a in by["next"].get("actions") or []
           if not str(a.get("owner", "")).strip() or not str(a.get("timing", "")).strip()]
    R.add("next steps: owner and timing", "PASS" if not bad else "FAIL", "; ".join(bad))

    people = by["team"].get("people") or []
    src = " ".join(sources_text.split()).lower()

    def named(nm: str) -> bool:
        nm = " ".join(nm.split()).lower()
        return bool(nm) and re.search(r"(?<!\w)" + re.escape(nm) + r"(?!\w)", src) is not None
    unsourced = [p.get("name", "") for p in people
                 if "[needs input" not in p.get("name", "").lower() and not named(p.get("name", ""))]
    sides = {p.get("side") for p in people}
    ok = not unsourced and {"client", "wise"} <= sides
    R.add("team names", "PASS" if ok else "FAIL",
          f"{len(people)} people, every name in a source file" if ok else
          (f"not in the Blueprint, quote bank, context or --source files: {unsourced}" if unsourced else
           "needs at least one client and one WISE person (side: client | wise)"))

    nstats = sum(len(by[k].get("stats") or []) for k in ("diagnosis", "cost", "stand-today", "top-keyword", "site"))
    R.add("big numbers", "PASS" if 5 <= nstats <= 8 else "WARN", f"{nstats} stat callouts (aim for 5 to 8)")

    # fit
    over = []
    for p, v in _strings(plan):
        if p.startswith("slides") and ".notes" not in p:
            key = p.rsplit(".", 1)[-1].split("[")[0]
            key = {"text": "quote", "points": "point", "body": "body", "pages": "name"}.get(key, key)
            lim = LIMITS.get(key)
            if lim and len(v) > lim:
                over.append(f"{p} ({len(v)} > {lim} chars)")
    R.add("fits the slides", "PASS" if not over else "FAIL", "; ".join(over[:5]))
    return R


# =========================================================================== render
class Theme:
    def __init__(self, brand: dict, brand_dir: Path):
        self.c = brand["colors"]
        self.font = brand["fonts"]["heading"]
        self.body = brand["fonts"]["body"]
        self.logo = (brand_dir / brand["logo"]).read_bytes()
        w, h = brand.get("logo_size_px", [640, 264])
        self.logo_ratio = w / h


def R_(text, size=16, **kw):
    return W.Run(text, size=size, **kw)


def _eyebrow(s, T, label, x=0.7, y=0.55, dark=False):
    s.shape("chrome:accent", x, y - 0.18, 0.55, 0.06, fill=T.c["green"])
    s.text("eyebrow", x, y, 11.9, 0.3, [W.Para(R_(label, 11, bold=True, color=T.c["gray_200"] if dark else T.c["gray_400"],
                                                spacing=2.5, caps=True))])


def _headline(s, T, text, y=0.9, size=28, dark=False, w=11.9):
    s.text("headline", 0.7, y, w, 1.2, [W.Para(R_(text, size, bold=True, color=T.c["white"] if dark else T.c["gray_800"]),
                                             line=0.95)], anchor="t")


def _footer(s, T, client, n, dark=False):
    col = T.c["gray_200"] if dark else T.c["gray_400"]
    s.shape("chrome:rule", 0.7, 6.92, 11.93, 0.01, fill=T.c["gray_700"] if dark else T.c["gray_200"])
    if not dark:
        h = 0.3
        s.picture("chrome:logo", T.logo, 0.7, 7.0, h * T.logo_ratio, h)
    s.text("chrome:footer", 2.4, 7.02, 8.9, 0.3, [W.Para(R_(f"{client}  |  Growth Blueprint", 10, color=col), align="r")],
           anchor="ctr")
    s.text("chrome:pagenum", 11.6, 7.02, 1.03, 0.3, [W.Para(R_(str(n), 10, bold=True, color=col), align="r")], anchor="ctr")


def _stat_cards(s, T, stats, x, y, w, h, value_size=44, highlight_first=False):
    n = max(1, len(stats))
    gap = 0.3
    cw = (w - gap * (n - 1)) / n
    for i, st in enumerate(stats):
        cx = x + i * (cw + gap)
        s.shape("chrome:card", cx, y, cw, h, fill=T.c["green_5"], geom="roundRect", radius=6000)
        color = T.c["green_dark"] if (highlight_first and i == 0) else T.c["gray_800"]
        s.text(f"stat:{i + 1}", cx + 0.3, y + 0.25, cw - 0.6, h * 0.5,
               [W.Para(R_(str(st.get("value", "")), value_size, bold=True, color=color))], anchor="b")
        s.text(f"caption:{i + 1}", cx + 0.3, y + 0.3 + h * 0.5, cw - 0.6, h * 0.45,
               [W.Para(R_(st.get("caption", ""), 14, color=T.c["gray_400"]), line=1.1)])


def _bullets(s, T, name, lines, x, y, w, h, size=16, color=None):
    paras = [W.Para([R_("▪  ", size, color=T.c["green_dark"]), R_(t, size, color=color or T.c["gray_400"])],
                    space_after=8, line=1.1) for t in lines]
    s.text(name, x, y, w, h, paras)


def _table(s, T, name, columns, rows, x, y, w, max_h, first_col_bold=True, highlight_col=None, tier_col=None, size=None):
    n = len(rows) + 1
    row_h = min(0.48, max_h / n)
    size = size or (14 if n <= 8 else 12 if n <= 12 else 11)
    def need(i):
        cells = [str(r[i]) if i < len(r) else "" for r in [columns] + rows]
        longest_word = max((len(w) for c in cells for w in c.split()), default=4)
        return max(6, longest_word + 4, min(max(len(c) for c in cells), 22))
    weights = [need(i) for i in range(len(columns))]
    widths = [w * wt / sum(weights) for wt in weights]
    tier_fill = {"Tier 1": (T.c["green_dark"], T.c["white"]), "Tier 2": (T.c["green_10"], T.c["gray_800"]),
                 "Tier 3": (T.c["gray_100"], T.c["gray_800"])}

    def style(r, c):
        if r == 0:
            return {"fill": T.c["gray_700"], "color": T.c["white"], "bold": True, "size": min(size - 1, 12)}
        val = str(rows[r - 1][c]) if c < len(rows[r - 1]) else ""
        st = {"fill": T.c["white"] if r % 2 else T.c["gray_100"], "color": T.c["gray_800"], "size": size,
              "bold": first_col_bold and c == 0}
        if highlight_col is not None and c == highlight_col:
            st.update(fill=T.c["green_10"], bold=True)
        if tier_col is not None and c == tier_col and val in tier_fill:
            st.update(fill=tier_fill[val][0], color=tier_fill[val][1], bold=True)
        return st

    padded = [[str(r[i]) if i < len(r) else "" for i in range(len(columns))] for r in rows]
    s.table(name, x, y, widths, row_h, [list(columns)] + padded, style)


def _needs(s, T, text, y=2.4):
    s.shape("needs", 0.7, y, 11.9, 1.0, fill=T.c["gray_100"], line=T.c["gray_200"], geom="roundRect", radius=6000,
            paras=[W.Para(R_(text, 16, bold=True, color=T.c["gray_800"]))], anchor="ctr", inset=0.25)


def notes_text(n: dict) -> str:
    out = [f"Say: {n.get('say', '')}"]
    if n.get("emphasise"):
        out.append(f"Emphasise: {n['emphasise']}")
    if n.get("pushback"):
        out.append(f"Likely pushback: {n['pushback']}")
    return "\n".join(out)


def render(plan: dict, T: Theme, out: Path) -> None:
    client = plan.get("client", "")
    slides = []
    for n, d in enumerate(plan["slides"], 1):
        s = W.Slide(T.font)
        sid = d["id"]
        s.notes = notes_text(d.get("notes") or {})
        if sid == "cover":
            s.shape("chrome:panel", 8.9, 0, 4.433, 7.5, fill=(T.c["gradient_start"], T.c["gradient_end"]))
            s.shape("chrome:accent", 8.9, 0, 0.12, 7.5, fill=T.c["green"])
            s.picture("chrome:logo", T.logo, 0.7, 0.6, 1.0 * T.logo_ratio, 1.0)
            s.text("eyebrow", 0.7, 2.55, 7.6, 0.35, [W.Para(R_(plan.get("agency", ""), 12, bold=True,
                                                               color=T.c["gray_400"], spacing=2.5, caps=True))])
            s.text("title", 0.7, 2.95, 7.9, 1.2, [W.Para(R_(d.get("title", ""), 54, bold=True, color=T.c["gray_800"]))])
            s.text("subtitle", 0.7, 4.2, 7.9, 0.6, [W.Para(R_(d.get("prepared_for", ""), 24, color=T.c["gray_800"]))])
            s.text("by", 0.7, 4.8, 7.9, 0.5, [W.Para(R_(d.get("by", ""), 16, color=T.c["gray_400"]))])
            d0 = dt.date.fromisoformat(plan["date"])
            date = f"{d0.strftime('%B')} {d0.day}, {d0.year}"
            s.text("chrome:date", 0.7, 6.4, 7.9, 0.4, [W.Para(R_(date, 14, color=T.c["gray_400"]))])
            slides.append(s)
            continue
        if sid == "divider":
            s.background = (T.c["gradient_start"], T.c["gradient_end"])
            s.text("chrome:divnum", 0.7, 2.0, 4, 1.2, [W.Para(R_(d.get("number", ""), 66, bold=True, color=T.c["green_70"]))])
            s.shape("chrome:accent", 0.7, 3.35, 0.9, 0.07, fill=T.c["green"])
            s.text("headline", 0.7, 3.6, 11.5, 1.5, [W.Para(R_(d.get("headline", ""), 40, bold=True, color=T.c["white"]))])
            _footer(s, T, client, n, dark=True)
            slides.append(s)
            continue

        _eyebrow(s, T, d.get("eyebrow") or LABELS[sid])
        _headline(s, T, d.get("headline", ""))
        top = 2.3
        if d.get("needs_input") and sid not in ("site",):
            _needs(s, T, d["needs_input"])
        elif sid == "diagnosis":
            st = (d.get("stats") or [{}])[0]
            s.text("stat:1", 0.7, 2.35, 11.9, 1.9, [W.Para(R_(str(st.get("value", "")), 110, bold=True,
                                                             color=T.c["green_dark"]))], anchor="b")
            s.text("caption:1", 0.7, 4.3, 11.9, 0.5, [W.Para(R_(st.get("caption", ""), 18, bold=True, color=T.c["gray_800"]))])
            s.text("body", 0.7, 4.95, 10.5, 1.6, [W.Para(R_(t, 17, color=T.c["gray_400"]), space_after=6, line=1.1)
                                                  for t in d.get("body") or []])
        elif sid in ("cost", "stand-today"):
            body = d.get("body") or []
            h = 2.6 if body else 3.4
            _stat_cards(s, T, d.get("stats") or [], 0.7, top + 0.1, 11.9, h, highlight_first=(sid == "cost"))
            if body:
                _bullets(s, T, "body", body, 0.7, top + h + 0.35, 11.9, 1.4, size=15)
        elif sid == "told-us":
            qs = d.get("quotes") or []
            cols = 2 if len(qs) in (2, 4) else max(1, len(qs))
            rows_ = -(-len(qs) // cols) if qs else 1
            cw, ch = (11.9 - 0.3 * (cols - 1)) / cols, min(3.3, (4.4 - 0.3 * (rows_ - 1)) / rows_)
            for i, q in enumerate(qs):
                cx, cy = 0.7 + (i % cols) * (cw + 0.3), top + (i // cols) * (ch + 0.3)
                s.shape("chrome:card", cx, cy, cw, ch, fill=T.c["green_5"], geom="roundRect", radius=5000)
                s.shape("chrome:bar", cx, cy + 0.25, 0.07, ch - 0.5, fill=T.c["green"] if i == 0 else T.c["green_40"])
                s.text(f"quote:{i + 1}", cx + 0.35, cy + 0.2, cw - 0.6, ch - 0.95,
                       [W.Para(R_("“" + q.get("text", "") + "”", 16, italic=True, color=T.c["gray_800"]), line=1.1)])
                s.text(f"attr:{i + 1}", cx + 0.35, cy + ch - 0.72, cw - 0.6, 0.3,
                       [W.Para(R_(f"{q.get('speaker', '')}, kickoff call, {q.get('date', '')}", 11, bold=True,
                                  color=T.c["gray_400"]))])
                s.text(f"drives:{i + 1}", cx + 0.35, cy + ch - 0.42, cw - 0.6, 0.3,
                       [W.Para(R_("Drives: " + q.get("drives", ""), 11, color=T.c["green_dark"], bold=True))])
        elif sid == "competitors":
            tb = d["table"]
            _table(s, T, "table", tb["columns"], tb["rows"], 0.7, top, 11.9, 4.0, highlight_col=1,
                   size=14 if len(tb["rows"]) <= 7 else 12)
            if d.get("caption"):
                s.text("caption", 0.7, 6.45, 11.9, 0.35, [W.Para(R_(d["caption"], 11, color=T.c["gray_400"]))])
        elif sid == "threats":
            items = d.get("items") or []
            rh = min(1.1, 4.3 / max(1, len(items)))
            gfill = {"Real threat": (T.c["gray_700"], T.c["white"]), "Overstated": (T.c["green_10"], T.c["gray_800"]),
                     "Not a competitor": (T.c["gray_100"], T.c["gray_800"])}
            for i, it in enumerate(items):
                y = top + i * rh
                s.shape("chrome:rule", 0.7, y + rh - 0.08, 11.9, 0.01, fill=T.c["gray_200"])
                s.text(f"name:{i + 1}", 0.7, y, 3.6, rh - 0.15, [W.Para(R_(it.get("name", ""), 16, bold=True,
                                                                           color=T.c["gray_800"]))], anchor="ctr")
                f, c = gfill.get(it.get("grade"), (T.c["gray_100"], T.c["gray_800"]))
                s.shape(f"grade:{i + 1}", 4.4, y + (rh - 0.15) / 2 - 0.22, 2.2, 0.44, fill=f, geom="roundRect", radius=50000,
                        paras=[W.Para(R_(it.get("grade", ""), 12, bold=True, color=c), align="ctr")], anchor="ctr", inset=0.04)
                s.text(f"why:{i + 1}", 6.9, y, 5.7, rh - 0.15, [W.Para(R_(it.get("why", ""), 14, color=T.c["gray_400"]),
                                                                       line=1.05)], anchor="ctr")
        elif sid == "keywords":
            tb = d["table"]
            _table(s, T, "table", tb["columns"], tb["rows"], 0.7, top - 0.05, 11.9, 4.1, tier_col=4)
            if d.get("caption"):
                s.text("caption", 0.7, 6.5, 11.9, 0.35, [W.Para(R_(d["caption"], 11, color=T.c["gray_400"]))])
        elif sid == "top-keyword":
            st = (d.get("stats") or [{}])[0]
            s.shape("chrome:card", 0.7, top + 0.1, 4.6, 4.1, fill=T.c["green_5"], geom="roundRect", radius=5000)
            s.text("keyword", 1.0, top + 0.35, 4.0, 0.9, [W.Para(R_(d.get("keyword", ""), 18, bold=True, color=T.c["gray_800"]))])
            s.text("stat:1", 1.0, top + 1.25, 4.0, 1.3, [W.Para(R_(str(st.get("value", "")), 54, bold=True,
                                                                  color=T.c["green_dark"]))], anchor="b")
            s.text("caption:1", 1.0, top + 2.6, 4.0, 0.8, [W.Para(R_(st.get("caption", ""), 14, color=T.c["gray_400"]))])
            s.text("tier", 1.0, top + 3.45, 4.0, 0.5, [W.Para(R_(d.get("tier", ""), 14, bold=True, color=T.c["gray_800"]))])
            _bullets(s, T, "points", d.get("points") or [], 5.8, top + 0.2, 6.8, 4.0, size=17)
        elif sid == "positioning":
            pts = d.get("points") or []
            n_ = max(1, len(pts))
            cw = (11.9 - 0.3 * (n_ - 1)) / n_
            for i, p in enumerate(pts):
                cx = 0.7 + i * (cw + 0.3)
                s.shape("chrome:card", cx, top + 0.05, cw, 2.1, fill=T.c["green_5"], geom="roundRect", radius=5000)
                s.text(f"point:{i + 1}", cx + 0.3, top + 0.3, cw - 0.6, 1.7, [W.Para(R_(p, 16, color=T.c["gray_800"]), line=1.1)])
            s.shape("chrome:band", 0.7, top + 2.5, 11.9, 1.75, fill=(T.c["gradient_start"], T.c["gradient_end"]),
                    geom="roundRect", radius=5000)
            s.text("chrome:msglabel", 1.1, top + 2.7, 11.0, 0.35, [W.Para(R_("The homepage will say", 11, bold=True,
                                                                             color=T.c["green_70"], spacing=2, caps=True))])
            s.text("message", 1.1, top + 3.05, 11.1, 1.1, [W.Para(R_(d.get("message", ""), 22, bold=True, color=T.c["white"]),
                                                               line=1.05)])
        elif sid == "site":
            if d.get("needs_input"):
                _needs(s, T, d["needs_input"], y=top + 0.2)
            else:
                st = (d.get("stats") or [{}])[0]
                s.shape("chrome:card", 0.7, top + 0.1, 3.4, 4.1, fill=T.c["green_5"], geom="roundRect", radius=5000)
                s.text("stat:1", 0.95, top + 0.4, 2.9, 1.8, [W.Para(R_(str(st.get("value", "")), 96, bold=True,
                                                                      color=T.c["green_dark"]))], anchor="b")
                s.text("caption:1", 0.95, top + 2.35, 2.9, 1.2, [W.Para(R_(st.get("caption", ""), 15, color=T.c["gray_400"]))])
            pages = d.get("pages") or []
            fills = {"home": (T.c["gray_700"], T.c["white"]), "service": (T.c["green_dark"], T.c["white"]),
                     "location": (T.c["green_10"], T.c["gray_800"]), "about": (T.c["gray_100"], T.c["gray_800"]),
                     "contact": (T.c["white"], T.c["gray_800"]), "resource": (T.c["green_5"], T.c["gray_800"]),
                     "other": (T.c["gray_100"], T.c["gray_800"])}
            cols = 2 if len(pages) > 7 else 1
            per = -(-len(pages) // cols) if pages else 1
            ph = min(0.48, 3.7 / per)
            pw = (8.0 - 0.25 * (cols - 1)) / cols
            for i, p in enumerate(pages):
                cx = 4.55 + (i // per) * (pw + 0.25)
                cy = top + 0.1 + (i % per) * ph
                f, c = fills.get(p.get("type"), fills["other"])
                s.shape(f"page:{i + 1}", cx, cy, pw, ph - 0.07, fill=f, line=T.c["gray_200"], geom="roundRect", radius=20000,
                        paras=[W.Para([R_(p.get("name", ""), 12, bold=True, color=c),
                                       R_("   " + p.get("type", ""), 10, color=c)])], anchor="ctr", inset=0.12)
            used = [t for t in PAGE_TYPES if any(p.get("type") == t for p in pages)]
            s.text("chrome:legend", 4.55, 6.45, 8.0, 0.35, [W.Para(R_("Page types: " + ", ".join(used), 11,
                                                                     color=T.c["gray_400"]))])
        elif sid == "not-doing":
            rows = [[i.get("what", ""), i.get("why", ""), i.get("revisit", "")] for i in d.get("items") or []]
            n_ = len(rows) + 1
            _table(s, T, "table", ["What", "Why not now", "What would change that"], rows, 0.7, top, 11.9,
                   min(4.3, 0.95 * n_), size=13)
        elif sid == "has-to-be-true":
            for k, (side, title, fill) in enumerate((("client", "What we need from you", T.c["green_5"]),
                                                     ("wise", "What WISE owns", T.c["gray_100"]))):
                cx = 0.7 + k * 6.1
                s.shape("chrome:card", cx, top, 5.8, 4.4, fill=fill, geom="roundRect", radius=4000)
                s.text(f"chrome:side{k}", cx + 0.3, top + 0.2, 5.2, 0.4,
                       [W.Para(R_(title, 13, bold=True, color=T.c["green_dark"] if k == 0 else T.c["gray_400"],
                                  spacing=1.5, caps=True))])
                paras = []
                for it in d.get(side) or []:
                    paras.append(W.Para(R_(it.get("item", ""), 14, bold=True, color=T.c["gray_800"]), space_after=1))
                    paras.append(W.Para(R_(f"Owner: {it.get('owner', '')}  |  Needed: {it.get('needed_by', '')}  |  "
                                           f"Blocks: {it.get('blocks', '')}", 11, color=T.c["gray_400"]), space_after=10))
                s.text(f"items:{side}", cx + 0.3, top + 0.7, 5.2, 3.6, paras)
        elif sid == "measure":
            tb = d["table"]
            s.shape("chrome:badge", 0.7, top - 0.05, 2.6, 0.38, fill=T.c["green_10"], geom="roundRect", radius=50000,
                    paras=[W.Para(R_("Targets are directional", 11, bold=True, color=T.c["green_dark"]), align="ctr")],
                    anchor="ctr", inset=0.03)
            _table(s, T, "table", tb["columns"], tb["rows"], 0.7, top + 0.55, 11.9, 3.7, size=13)
        elif sid == "team":
            people = d.get("people") or []
            for k, side in enumerate(("client", "wise")):
                grp = [p for p in people if p.get("side") == side]
                y = top + k * 2.25
                s.text(f"chrome:team{k}", 0.7, y, 11.9, 0.35, [W.Para(R_(plan.get("client", "") if side == "client" else
                                                                         plan.get("agency", ""), 12, bold=True,
                                                                         color=T.c["gray_400"], spacing=1.5, caps=True))])
                k_ = max(2, min(4, len(grp)))
                cw = (11.9 - 0.3 * (k_ - 1)) / k_
                for i, p in enumerate(grp[:4]):
                    cx = 0.7 + i * (cw + 0.3)
                    initials = "".join(w[0] for w in re.sub(r"^(Dr|Mr|Mrs|Ms)\.?\s+", "", p.get("name", "")).split()[:2]).upper()
                    s.shape("chrome:initials", cx, y + 0.45, 0.8, 0.8, fill=T.c["green_10"], geom="ellipse",
                            paras=[W.Para(R_(initials, 16, bold=True, color=T.c["green_dark"]), align="ctr")], anchor="ctr", inset=0)
                    s.text(f"person:{side}{i + 1}", cx + 0.95, y + 0.4, cw - 0.95, 1.6,
                           [W.Para(R_(p.get("name", ""), 14, bold=True, color=T.c["gray_800"]), space_after=2),
                            W.Para(R_(p.get("role", ""), 12, bold=True, color=T.c["green_dark"]), space_after=2),
                            W.Para(R_(p.get("owns", ""), 11, color=T.c["gray_400"]), line=1.05)])
        elif sid == "next":
            acts = d.get("actions") or []
            rh = min(0.75, 4.4 / max(1, len(acts)))
            for i, a in enumerate(acts):
                y = top + i * rh
                s.shape("chrome:num", 0.7, y + (rh - 0.46) / 2, 0.46, 0.46, fill=T.c["green"] if i == 0 else T.c["gray_700"],
                        geom="ellipse", paras=[W.Para(R_(str(i + 1), 13, bold=True, color=T.c["white"]), align="ctr")],
                        anchor="ctr", inset=0)
                s.text(f"action:{i + 1}", 1.35, y, 7.0, rh, [W.Para(R_(a.get("action", ""), 17, bold=True,
                                                                      color=T.c["gray_800"]))], anchor="ctr")
                s.text(f"owner:{i + 1}", 8.5, y, 4.1, rh, [W.Para([R_(a.get("owner", ""), 13, bold=True, color=T.c["gray_800"]),
                                                                  R_("   " + a.get("timing", ""), 13, color=T.c["gray_400"])],
                                                                 align="r")], anchor="ctr")
        _footer(s, T, client, n)
        slides.append(s)
    out.parent.mkdir(parents=True, exist_ok=True)
    W.save(out, slides, T.c, T.font, f"{client}: Growth Blueprint", plan.get("agency", ""),
           f"{plan.get('date', dt.date.today().isoformat())}T00:00:00Z")


# =========================================================================== reporting
def write_report(P, root, client, res, rows, state, built: bool) -> None:
    lines = [f"# Deck compliance: {client}", "",
             f"Deck: {rel(P['pptx'], root) if built else 'not written (the build failed; any deck already there is from an earlier build)'}",
             f"Blueprint: {rel(P['blueprint'], root)}",
             f"Quote bank: {rel(P['quotes'], root)}",
             f"Checked: {dt.date.today().isoformat()}", "",
             "## Checks", "", "| Check | Result | Detail |", "|---|---|---|"]
    lines += [f"| {a} | {b} | {C._cell(c)} |" for a, b, c in rows]
    lines += ["", f"RESULT: {state}", "", "## Figures by slide", "",
              "Every figure on a slide or in its speaker notes, and whether it appears in the Blueprint.", "",
              "| Slide | Figure | In Blueprint | Where |", "|---|---|---|---|"]
    seen = {}
    for n, tok, ok, loc in (res or {}).get("figures", []):
        key = (n, tok)
        if key in seen:
            if loc not in seen[key][2]:
                seen[key][2].append(loc)
        else:
            seen[key] = [n, ok, [loc]]
    for (n, tok), (_, ok, locs) in seen.items():
        lines.append(f"| {n} | {tok} | {'yes' if ok else 'no'} | {', '.join(locs)} |")
    if not seen:
        lines.append("| - | none | - | - |")
    hits = C.hits_table(res) if res else []
    lines += ["", "## Hits", ""]
    if hits:
        lines += ["| Slide | Check | Where | Text |", "|---|---|---|---|"] + hits
    else:
        lines.append("None.")
    P["compliance"].parent.mkdir(parents=True, exist_ok=True)
    P["compliance"].write_text("\n".join(lines) + "\n", encoding="utf-8")


def print_rows(rows, state):
    w = max(len(r[0]) for r in rows)
    print(f"{'check'.ljust(w)}  result       detail")
    for a, b, c in rows:
        print(f"{a.ljust(w)}  {b.ljust(11)}  {c}")
    print(f"RESULT: {state}")


def sources_text(P, args, bank_text) -> str:
    parts = [P["blueprint"].read_text(encoding="utf-8")]
    if P["context"].exists():
        parts.append(P["context"].read_text(encoding="utf-8"))
    for s in args.source or []:
        parts.append(Path(s).read_text(encoding="utf-8"))
    return "\n".join(parts) + "\n\x00QUOTES\x00\n" + bank_text


def build(args) -> int:
    P = paths(args)
    root = Path(args.root)
    for k in ("blueprint", "plan"):
        if not P[k].exists():
            print(f"MISSING  {k}: {P[k]}" + ("  (run scaffold first)" if k == "plan" else ""))
            print("RESULT: FAIL")
            return 1
    bank_text = P["quotes"].read_text(encoding="utf-8") if P["quotes"].exists() else ""
    bp = Blueprint.from_file(P["blueprint"])
    try:
        plan = json.loads(P["plan"].read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"plan is not valid JSON: {e}")
        print("RESULT: FAIL")
        return 1
    rows = Rows()
    if not bank_text:
        rows.add("quote bank", "FAIL", f"not found at {rel(P['quotes'], root)}")
    for sec in bp.missing_sections():
        rows.add("Blueprint section", "FAIL", f"missing `{sec}`")
    rows.rows += check_plan(plan, bp, sources_text(P, args, bank_text)).rows
    brand = json.loads(P["brand"].read_text(encoding="utf-8"))
    tmp = P["pptx"].with_name(P["pptx"].stem + ".tmp.pptx")
    res = None
    if not any(r[0] in ("slide order", "date") and r[1] == "FAIL" for r in rows.rows):
        render(plan, Theme(brand, P["brand"].parent), tmp)
        res = C.check(tmp, bp.text, bank_text)
        rows.rows = C.summary_rows(res) + rows.rows
    state = C.result(rows.rows)
    built = state != "FAIL" and res is not None
    if built:
        tmp.replace(P["pptx"])
    else:
        if tmp.exists():
            tmp.unlink()
    write_report(P, root, plan.get("client", bp.client), res, rows.rows, state, built)
    print_rows(rows.rows, state)
    if built:
        print("wrote    " + rel(P["pptx"], root))
    else:
        print("deck NOT written: fix every FAIL row and build again"
              + (f" (the deck already at {rel(P['pptx'], root)} is from an earlier build and was left as it was)"
                 if P["pptx"].exists() else ""))
    print("wrote    " + rel(P["compliance"], root))
    return 0 if state != "FAIL" else 1


def check_cmd(args) -> int:
    P = paths(args)
    root = Path(args.root)
    for k in ("pptx", "blueprint", "quotes"):
        if not P[k].exists():
            print(f"MISSING  {k}: {P[k]}")
            print("RESULT: FAIL")
            return 1
    bp = Blueprint.from_file(P["blueprint"])
    res = C.check(P["pptx"], bp.text, P["quotes"].read_text(encoding="utf-8"))
    rows = C.summary_rows(res)
    rows.append(("slides", "PASS", f"{res['slides']} slides read"))
    state = C.result(rows)
    write_report(P, root, bp.client, res, rows, state, True)
    print_rows(rows, state)
    print("wrote    " + rel(P["compliance"], root))
    return 0 if state != "FAIL" else 1


def sections_cmd(args) -> int:
    data = json.loads(Path(args.file).read_text(encoding="utf-8"))
    # rebuild the markdown file so the contract runs the same parser as build
    text = f"# {data.get('Client', '')}: Growth Blueprint\n\nClient: {data.get('Client', '')}\n\n" + "".join(
        f"## {k}\n\n{v}\n\n" for k, v in data.items() if k in SECTIONS)
    bp = Blueprint.from_text(text)
    secs = bp.sections
    missing = bp.missing_sections()
    kws = bp.keyword_rows()
    n, cap = bp.page_count()
    t = bp.competitor_table()
    print(f"sections: {len(secs)} of {len(SECTIONS)}" + (f" (missing: {', '.join(missing)})" if missing else ""))
    print(f"keyword rows: {len(kws)} in tiers {sorted({r['tier'] for r in kws})}")
    print(f"page count: {n} of {cap}")
    print(f"competitor table: {len(t) - 1} rows, columns {t[0]}" if t else
          f"competitor table: none ({bp.needs('Competitive Analysis') or 'no NEEDS INPUT line either'})")
    um = bp.url_map()
    print(f"URL map: {len(um) - 1 if um else 0} pages")
    ok = not missing and kws and (n is not None or bp.needs("Site Architecture and Content Plan")) and \
        (t is not None or bp.needs("Competitive Analysis"))
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("scaffold", "build", "check"):
        p = sub.add_parser(name)
        p.add_argument("--slug", required=True)
        p.add_argument("--root", default=".")
        p.add_argument("--blueprint")
        p.add_argument("--quotes")
        p.add_argument("--context")
        p.add_argument("--plan")
        p.add_argument("--brand")
        p.add_argument("--source", action="append")
        if name == "scaffold":
            p.add_argument("--date")
            p.add_argument("--force", action="store_true")
        if name == "check":
            p.add_argument("--pptx")
    p = sub.add_parser("sections")
    p.add_argument("file")
    args = ap.parse_args()
    if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    return {"scaffold": scaffold, "build": build, "check": check_cmd, "sections": sections_cmd}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
