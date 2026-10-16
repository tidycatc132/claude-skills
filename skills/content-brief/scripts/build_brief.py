#!/usr/bin/env python3
"""Validate a content brief's `brief.json` and render `brief.md` for seo-content-writer.

Usage:
  python3 build_brief.py BRIEF.json --target TARGET.json --sources FILE [FILE ...]
                         [--out BRIEF.md] [--json-out FILE|-]

BRIEF.json   the brief the model filled in (schema: references/brief-schema.md)
--target     (required) the target row(s) from parse_targets.py; the row whose `id` equals the brief's is used;
             `primary_keyword`, `metrics`, `search_intent`, `funnel` and the pillar
             link are checked against it
--sources    (required) the files the brief was built from (keyword report, client notes,
             client-reference files, saved research). Every figure in `evidence`,
             `expert_quotes`, `first_hand`, `author` and `cta` must appear in one of them
--out        where to write brief.md (default: beside BRIEF.json)
--json-out   also write the normalized brief JSON ("-" = stdout, nothing else printed)

Prints a `| Check | Result | Detail |` table and `VERDICT: READY | NEEDS_INPUT | FIX`.
FIX       a check FAILed; brief.md is still written but marked FIX
NEEDS_INPUT  no FAILs, but some fields are `needs` gaps (shown as [NEEDS ...] flags)
READY     complete
Exit code 1 on FIX, else 0. Standard library only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

REQUIRED = ["id", "client", "page_url", "page_type", "primary_keyword", "secondary_keywords",
            "search_intent", "funnel", "metrics", "primary_question", "sub_questions", "entities",
            "banned_aliases", "evidence", "expert_quotes", "author", "first_hand", "internal_links",
            "answer_format", "format_directives", "word_range", "cta", "ymyl", "source_report"]
PAGE_TYPES = {"blog article", "explainer", "guide", "how-to", "comparison", "listicle", "definition",
              "FAQ page", "service page", "product page", "location page", "cost guide"}
ANSWER_FORMATS = {"direct answer", "steps", "comparison table", "definition plus example", "FAQ block", "N/A"}
INTENTS = {"Informational", "Navigational", "Commercial", "Transactional"}
FUNNELS = {"TOFU", "MOFU", "BOFU"}
LINK_ROLES = {"pillar", "sub-topic", "sibling", "service", "booking"}
GENERIC_ANCHOR = re.compile(r"^(click here|here|learn more|read more|more|this page|this article|link)$", re.I)
OFF_SCOPE = re.compile(
    r"illustrative|hypothetical|typical (industry )?(range|figure|number)s?|round numbers|made[- ]up|"
    r"for example, say|json-?ld|schema markup|\b\d+\s*characters?\b",
    re.I,
)
FIGURE = re.compile(r"(?<![\w.])\$?\d[\d,]*(?:\.\d+)?%?")


def is_gap(v) -> bool:
    return isinstance(v, dict) and "needs" in v


def figures(text: str) -> set[str]:
    return {n.replace(",", "").lstrip("$").rstrip("%") for n in FIGURE.findall(text or "")}


def flag(kind: str, text: str) -> str:
    return f"[NEEDS {kind}: {text}]"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("brief")
    ap.add_argument("--target", required=True)
    ap.add_argument("--sources", nargs="+", required=True)
    ap.add_argument("--out")
    ap.add_argument("--json-out")
    a = ap.parse_args()

    src = Path(a.brief)
    try:
        b = json.loads(src.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"cannot read {src}: {e}", file=sys.stderr)
        return 2
    quiet = a.json_out == "-"
    rows: list[tuple[str, str, str]] = []

    def add(check: str, ok: bool, detail: str = "", warn: bool = False):
        rows.append((check, "PASS" if ok else ("WARN" if warn else "FAIL"), "" if ok else detail))

    missing = [k for k in REQUIRED if k not in b]
    add("All brief.json keys present", not missing, "missing: " + ", ".join(missing))
    g = lambda k, d=None: b.get(k, d)

    add("page_type is allowed", g("page_type") in PAGE_TYPES, f"{g('page_type')!r}; use one of {sorted(PAGE_TYPES)}")
    add("search_intent and funnel are allowed", g("search_intent") in INTENTS and g("funnel") in FUNNELS,
        f"{g('search_intent')!r} / {g('funnel')!r}")
    add("answer_format is allowed", g("answer_format") in ANSWER_FORMATS, f"{g('answer_format')!r}")
    pq = str(g("primary_question", ""))
    add("primary_question is a question", pq.strip().endswith("?"), pq[:80])

    subs = [s for s in g("sub_questions", []) if isinstance(s, str)]
    bad_subs = [s for s in subs if not s.strip().endswith("?")]
    dup = len({s.lower().strip() for s in subs}) != len(subs) or pq.lower().strip() in {s.lower().strip() for s in subs}
    add("5-8 distinct sub-questions", 5 <= len(subs) <= 8 and not bad_subs and not dup,
        f"{len(subs)} given" + (f"; not questions: {bad_subs[:3]}" if bad_subs else "") + ("; duplicates or repeats the primary question" if dup else ""))

    ents = [e for e in g("entities", []) if isinstance(e, str) and e.strip()]
    add("8-15 entities", 8 <= len(ents) <= 15, f"{len(ents)} given")

    # evidence
    ev = g("evidence", [])
    ev_bad = [i for i, e in enumerate(ev, 1)
              if not (is_gap(e) or (isinstance(e, dict) and e.get("claim") and e.get("source") and e.get("supports")))]
    add("Evidence items have claim, source and supports (or needs)", bool(ev) and not ev_bad,
        "no evidence items" if not ev else f"items {ev_bad}")
    gap_supports = [e for e in ev if isinstance(e, dict) and "needs" in e and "supports" not in e]
    ev_items_ok = [e for e in ev if isinstance(e, dict) and not is_gap(e)]
    covered = sum(1 for e in ev if isinstance(e, dict))
    add("Evidence covers most sub-questions", covered >= min(len(subs), 5),
        f"{covered} evidence items for {len(subs)} sub-questions; add sourced items or needs gaps", warn=True)

    # links
    links = g("internal_links", [])
    link_bad = [l for l in links if not (isinstance(l, dict) and str(l.get("url", "")).startswith(("/", "http"))
                                         and l.get("anchor") and l.get("role") in LINK_ROLES)]
    generic = [l.get("anchor") for l in links if isinstance(l, dict) and GENERIC_ANCHOR.match(str(l.get("anchor", "")).strip())]
    add("Internal links have url, descriptive anchor and role", bool(links) and not link_bad and not generic,
        ("no links" if not links else "") + (f" malformed: {link_bad[:2]}" if link_bad else "") + (f" generic anchors: {generic}" if generic else ""))

    # directives must be about content, not invented numbers or out-of-scope markup
    dirs = [d for d in g("format_directives", []) if isinstance(d, str)]
    off = [d for d in dirs if OFF_SCOPE.search(d)]
    add("Format directives prescribe no invented figures, schema or character limits", not off, "; ".join(x[:70] for x in off[:3]))
    wr = str(g("word_range", ""))
    add("word_range like 1400-1800", bool(re.fullmatch(r"\d{3,4}-\d{3,4}", wr)), wr)

    # target consistency
    target = None
    if a.target:
        t = json.loads(Path(a.target).read_text(encoding="utf-8"))
        if isinstance(t, list):
            target = next((x for x in t if x.get("id") == b.get("id")), {})
        else:
            target = t if t.get("id") == b.get("id") else {}
        add("Target row found for this brief id", bool(target), f"no row with id {b.get('id')!r} in {a.target}")
        add("primary_keyword matches the target", g("primary_keyword") == target.get("primary_keyword"),
            f"{g('primary_keyword')!r} vs {target.get('primary_keyword')!r}")
        add("metrics copied from the target", g("metrics") == target.get("metrics"), f"{g('metrics')} vs {target.get('metrics')}")
        add("intent and funnel match the target",
            g("search_intent") == target.get("intent") and g("funnel") == target.get("funnel"),
            f"{g('search_intent')}/{g('funnel')} vs {target.get('intent')}/{target.get('funnel')}")
        pu = str(target.get("pillar_url", "N/A"))
        if pu != "N/A" and pu.rstrip("/") != str(g("page_url", "")).rstrip("/"):
            has = any(isinstance(l, dict) and str(l.get("url", "")).rstrip("/") == pu.rstrip("/") and l.get("role") == "pillar" for l in links)
            add("Pillar from the target is linked with role pillar", has, pu)
        add("answer_format matches the target's geo_answer_format", g("answer_format") == target.get("geo_answer_format"),
            f"{g('answer_format')!r} vs {target.get('geo_answer_format')!r}", warn=True)

    # figures must come from the source files
    if a.sources:
        src_text = "\n".join(Path(p).read_text(encoding="utf-8") for p in a.sources if Path(p).is_file())
        known = figures(re.sub(r"\b\d{4}-\d{2}-\d{2}\b", " ", src_text))
        parts = []
        for e in ev_items_ok:
            parts += [str(e.get("claim", ""))]
        for q in g("expert_quotes", []):
            if isinstance(q, dict) and not is_gap(q):
                parts.append(str(q.get("quote", "")))
        for f in g("first_hand", []):
            parts.append(f if isinstance(f, str) else "")
        parts += [d for d in g("format_directives", []) if isinstance(d, str)]
        parts += [n for n in g("notes", []) if isinstance(n, str)]
        au, cta = g("author", {}), g("cta", {})
        if isinstance(au, dict) and not is_gap(au):
            parts.append(str(au.get("credentials", "")))
        if isinstance(cta, dict) and not is_gap(cta):
            parts.append(str(cta.get("text", "")) + " " + str(cta.get("route", "")))
        unknown = sorted({n for p in parts for n in figures(p) if n not in known})
        add("Every figure in evidence, quotes, author, first-hand and CTA is in a source file", not unknown,
            "not found in --sources: " + ", ".join(unknown[:12]))
    else:
        add("Source files given for the figure check", False, "pass --sources with the report and client notes", warn=True)

    # gaps -> flags
    flags: list[str] = []
    for e in ev:
        if is_gap(e) or (isinstance(e, dict) and "needs" in e):
            flags.append(flag("SOURCE", e["needs"]))
    for k, kind in (("author", "INPUT"), ("cta", "INPUT"), ("page_url", "INPUT"), ("client", "INPUT")):
        if is_gap(g(k)):
            flags.append(flag(kind, g(k)["needs"]))
    for f in g("first_hand", []):
        if is_gap(f):
            flags.append(flag("INPUT", f["needs"]))
    for q in g("expert_quotes", []):
        if is_gap(q):
            flags.append(flag("INPUT", q["needs"]))
    for l in links:
        if isinstance(l, dict) and is_gap(l.get("url")):
            flags.append(flag("INPUT", l["url"]["needs"]))
    if g("ymyl") and not g("reviewer"):
        flags.append(flag("INPUT", "compliance or expert reviewer for this YMYL page"))

    fails = [r for r in rows if r[1] == "FAIL"]
    verdict = "FIX" if fails else ("NEEDS_INPUT" if flags else "READY")

    md = render(b, flags, verdict)
    out = Path(a.out) if a.out else src.with_name("brief.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")

    if a.json_out:
        norm = json.dumps(b, indent=2, ensure_ascii=False) + "\n"
        if a.json_out == "-":
            sys.stdout.write(norm)
            return 1 if fails else 0
        Path(a.json_out).write_text(norm, encoding="utf-8")

    if not quiet:
        print(f"VERDICT: {verdict}\n")
        print(f"Brief: `{src.name}` -> `{out}`. Failed: {len(fails)}. Warnings: "
              f"{sum(1 for r in rows if r[1] == 'WARN')}. Open flags: {len(flags)}.\n")
        print("| Check | Result | Detail |\n| --- | --- | --- |")
        for c, r, d in rows:
            print(f"| {c} | {r} | {d.replace('|', '/')} |")
        for f in flags:
            print(f"- {f}")
    return 1 if fails else 0


def txt(v, kind="INPUT") -> str:
    if is_gap(v):
        return flag(kind, v["needs"])
    return "" if v is None else str(v)


def render(b: dict, flags: list[str], verdict: str) -> str:
    g = b.get
    today = dt.date.today().isoformat()
    m = g("metrics") or {}
    vol = m.get("volume", "N/A")
    vol = f"{vol:,}" if isinstance(vol, int) else vol
    L = [f"# Content Brief: {g('primary_question', '')}", "",
         f"Client: {txt(g('client'))}",
         f"Brief status: {verdict} (generated {today} by content-brief from `{g('source_report', '')}`, target `{g('id', '')}`)",
         "Approval: draft; an account lead signs off before writing starts",
         f"Page type: {g('page_type', '')}",
         f"URL: {txt(g('page_url'))}", "",
         "## Target keyword", f"- Primary: {g('primary_keyword', '')}"]
    if g("secondary_keywords"):
        L.append("- Secondary: " + ", ".join(g("secondary_keywords")))
    L += [f"- Keyword data: volume {vol}/mo, KD {m.get('kd', 'N/A')} ({m.get('source', 'N/A')}, keyword research)", "",
          "## Search intent", f"{g('search_intent', '')}, {g('funnel', '')}. {g('why_now', '')}".rstrip(), "",
          "## Primary question", g("primary_question", ""), "",
          "## Sub-questions (answer each under its own heading)"]
    L += [f"{i}. {s}" for i, s in enumerate(g("sub_questions", []), 1)]
    L += ["", "## Entities to cover", ", ".join(g("entities", [])), ""]
    if g("banned_aliases"):
        L += [f"Use the names above as the primary names. Do not switch to: {', '.join(g('banned_aliases'))}.", ""]
    L += ["## Evidence pack (use these and only these numbers)"]
    for e in g("evidence", []):
        if isinstance(e, dict) and "needs" in e:
            L.append(f"- {flag('SOURCE', e['needs'])}" + (f" Supports: {e['supports']}." if e.get("supports") else ""))
        elif isinstance(e, dict):
            url = f" ({e['url']})" if e.get("url") else ""
            L.append(f"- {e.get('source')}{url}: {e.get('claim')} Supports: {e.get('supports')}.")
    L += ["", "## Expert quote"]
    qs = g("expert_quotes", [])
    if not qs:
        L.append("None on file. Do not write a quote.")
    for q in qs:
        L.append(f"- {flag('INPUT', q['needs'])}" if is_gap(q) else f"- \"{q.get('quote')}\" ({q.get('speaker')}, {q.get('context')})")
    au = g("author")
    L += ["", "## Author",
          txt(au) if is_gap(au) else (f"{au.get('name')}, {au.get('credentials')}. Bio page: {au.get('bio_url')}"
                                      if isinstance(au, dict) else flag("INPUT", "author name, credentials and bio URL"))]
    if g("reviewer"):
        L.append(f"Reviewer: {g('reviewer')}")
    L += ["", "## First-hand experience to include"]
    fh = g("first_hand", [])
    L += [f"- {txt(f)}" for f in fh] or ["- " + flag("INPUT", "one first-hand example from the client's own work")]
    L += ["", "## Internal links (with planned anchor text)"]
    for l in g("internal_links", []):
        if isinstance(l, dict):
            L.append(f"- {str(l.get('role', '')).capitalize()}: {txt(l.get('url'))} (anchor: {l.get('anchor')})")
    L += ["", "## Formatting directives", f"- Answer format: {g('answer_format', '')}"]
    L += [f"- {d}" for d in g("format_directives", [])]
    L += [f"- Approximately {str(g('word_range', '')).replace('-', '-')} words.", "", "## CTA"]
    cta = g("cta")
    L.append(txt(cta) if is_gap(cta) else f"{cta.get('text')}: {cta.get('route')}" if isinstance(cta, dict) else str(cta))
    if g("ymyl"):
        L += ["", "## YMYL review",
              "This is a YMYL page. Credentials, sourcing and required disclosures come first; route the draft to "
              + (str(g("reviewer")) if g("reviewer") else "the client's compliance or expert reviewer") + " before publishing."]
    if g("notes"):
        L += ["", "## Notes for the writer"] + [f"- {n}" for n in g("notes")]
    L += ["", "## Open flags"] + ([f"- {f}" for f in flags] or ["None."])
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    sys.exit(main())
