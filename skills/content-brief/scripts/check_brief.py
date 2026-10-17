#!/usr/bin/env python3
"""Structural gate for a content brief written to references/brief-template.md.

Usage:
  python3 check_brief.py BRIEF.md
  python3 check_brief.py BRIEF.md --front-matter-json     print the front-matter as JSON, nothing else

Checks: front-matter fields and values, format values, required sections and
their order (YMYL and refresh moves included), question headings in the
Outline, 5-8 sub-question sections, 8-15 entities, evidence rows with ids,
URLs, dates and labels, evidence ids used by the Outline, banned
instructions (invented-example wording, schema markup, character counts, tool
or skill names), client-input slot accounting, link tables, and status
consistency with the concerns. Prints a `| Check | Result | Detail |` table and
`GATE: PASS` or `GATE: FAIL`. Exit code 1 on FAIL. Standard library only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from parse_targets import EMBEDDED, PRIMARY, value  # noqa: E402

FM_KEYS = ["id", "brief_version", "status", "date", "client", "client_domain", "market", "language",
           "page_url", "mode", "existing_url", "primary_keyword", "secondary_keywords", "intent", "funnel",
           "format", "format_embedded", "format_source", "metrics", "geo_candidate", "geo_answer_format",
           "cluster", "pillar_url", "ymyl", "local", "cannibalization", "voice_source", "style_source",
           "word_range", "client_inputs_open", "source_report"]
SECTIONS = ["Page Goal", "Reader and Search Intent", "Answer Target", "Outline", "Entities and Naming", "Evidence",
            "Author, Experience and Trust", "Internal Links", "Voice and Style", "Format Requirements",
            "Title and Meta Direction", "Client Inputs Needed", "Concerns", "Writer QA Checklist", "Research Log"]
LABELS = {"Measured", "User-provided", "Calculated", "Estimated"}
SOURCE_RE = re.compile(r"^(client|default/(home-services|financial-services|legal|b2b-saas|generated))$")
CANNIBAL = {"clear", "clear (unverified)", "clear (no site)", "risk"}
SLOT = re.compile(r"\[CLIENT INPUT NEEDED #(\d+):[^\]]+\]")
# references to a slot that are not the full bracket form ("slot #3", "input #3", "[#3]")
SHORTHAND = re.compile(r"(?i)\bslot\s*#?\s*\d+\b|\binput\s*#\s*\d+|\[#\d+\]")
# instruction phrasing only; the Evidence table (verbatim source text), the embedded Voice and Style
# directives and the Research Log are not scanned
BANNED = re.compile(
    r"(?i)illustrative example|hypothetical example|typical industry (figure|range|number)s?|"
    r"(use|assume|cite) (an |the )?industry average|round numbers|json-?ld|schema markup|"
    r"\b\d+\s*characters?\b|seo-content-writer|content-brief|keyword-research skill|\bClaude\b|"
    r"\b(writing|drafting|content|SEO) (skill|agent|bot)\b|\bAI (writer|drafting tool)\b"
)
UNSCANNED = {"Research Log", "Evidence", "Voice and Style"}
GENERIC_ANCHOR = re.compile(r"^(click here|here|learn more|read more|more|this page|this article|link)$", re.I)


def split_front_matter(text: str) -> tuple[dict, str, str | None]:
    t = text.replace("\r\n", "\n")
    m = re.match(r"\A---\n(.*?)\n---\n(.*)\Z", t, re.S)
    if not m:
        return {}, t, "no front-matter block between --- lines at the top"
    fm = {}
    for line in m.group(1).split("\n"):
        mm = re.match(r"^([A-Za-z_]+)\s*:\s*(.*)$", line)
        if mm:
            fm[mm.group(1)] = value(mm.group(2))
    return fm, m.group(2), None


def sections(body: str) -> list[tuple[str, str]]:
    out, cur, buf = [], None, []
    for line in body.split("\n"):
        m = re.match(r"^## (.+?)\s*$", line)
        if m:
            if cur is not None:
                out.append((cur, "\n".join(buf)))
            cur, buf = m.group(1), []
        elif cur is not None:
            buf.append(line)
    if cur is not None:
        out.append((cur, "\n".join(buf)))
    return out


def table_rows(text: str) -> list[list[str]]:
    rows = []
    for line in text.split("\n"):
        s = line.strip()
        if s.startswith("|") and not re.match(r"^\|[\s:|-]+\|$", s):
            rows.append([c.strip() for c in s.strip("|").split("|")])
    return rows[1:] if rows else []  # drop header


def bullets(text: str) -> list[str]:
    return [re.sub(r"^\s*(?:[-*]|\d+[.)])\s+", "", l).strip() for l in text.split("\n")
            if re.match(r"^\s*(?:[-*]|\d+[.)])\s+", l)]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("brief")
    ap.add_argument("--front-matter-json", action="store_true")
    a = ap.parse_args()
    p = Path(a.brief)
    if not p.is_file():
        print(f"brief not found: {p}", file=sys.stderr)
        return 2
    text = p.read_text(encoding="utf-8")
    fm, body, fm_err = split_front_matter(text)
    if a.front_matter_json:
        if fm_err:
            print(fm_err, file=sys.stderr)
            return 1
        sys.stdout.write(json.dumps(fm, indent=2, ensure_ascii=False) + "\n")
        return 0

    rows: list[tuple[str, str, str]] = []

    def add(check: str, ok: bool, detail: str = "", warn: bool = False):
        rows.append((check, "PASS" if ok else ("WARN" if warn else "FAIL"), "" if ok else detail))

    # --- front-matter
    add("Front-matter block present", not fm_err, fm_err or "")
    missing = [k for k in FM_KEYS if k not in fm]
    add("Front-matter fields present", not missing, "missing: " + ", ".join(missing))
    g = fm.get
    bad = []
    if g("status") not in ("DONE", "DONE_WITH_CONCERNS"):
        bad.append(f"status {g('status')!r} (a NEEDS_INPUT or BLOCKED row has no brief file)")
    if g("mode") not in ("new", "refresh"):
        bad.append(f"mode {g('mode')!r}")
    if g("intent") not in ("Informational", "Navigational", "Commercial", "Transactional"):
        bad.append(f"intent {g('intent')!r}")
    if g("funnel") not in ("TOFU", "MOFU", "BOFU"):
        bad.append(f"funnel {g('funnel')!r}")
    if g("cannibalization") not in CANNIBAL:
        bad.append(f"cannibalization {g('cannibalization')!r}")
    for k in ("voice_source", "style_source"):
        if not SOURCE_RE.match(str(g(k, ""))):
            bad.append(f"{k} {g(k)!r}")
    for k in ("ymyl", "local", "geo_candidate"):
        if not isinstance(g(k), bool):
            bad.append(f"{k} is not true/false")
    if not isinstance(g("brief_version"), int) or g("brief_version", 0) < 1:
        bad.append("brief_version is not a positive integer")
    if not re.fullmatch(r"\d{3,4}-\d{3,4}", str(g("word_range", ""))):
        bad.append(f"word_range {g('word_range')!r}")
    m = g("metrics")
    if not (isinstance(m, dict) and m.get("source") in LABELS | {"N/A"}):
        bad.append("metrics is not {volume, kd, source} with a source label")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(g("date", ""))):
        bad.append(f"date {g('date')!r}")
    add("Front-matter values valid", not bad, "; ".join(bad))
    emb = g("format_embedded", [])
    fmt_ok = g("format") in PRIMARY and isinstance(emb, list) and all(e in EMBEDDED for e in emb)
    add("Format values in the enum", fmt_ok, f"format {g('format')!r}, embedded {emb!r}")

    # --- title and sections
    h1 = re.search(r"(?m)^# Content Brief: (.+)$", body)
    add("Title is '# Content Brief: <question>?'", bool(h1) and h1.group(1).strip().endswith("?"),
        h1.group(1) if h1 else "no '# Content Brief:' line")
    secs = sections(body)
    names = [n for n, _ in secs]
    want = [s for s in SECTIONS]
    if g("mode") == "refresh":
        want.insert(want.index("Page Goal") + 1, "Refresh Audit")
    if g("ymyl") is True:
        want.remove("Author, Experience and Trust")
        want.insert(0, "Author, Experience and Trust")
    add("Required sections in order", names == want,
        f"got {names}; want {want}")
    S = dict(secs)

    # --- outline
    outline = S.get("Outline", "")
    blocks = re.split(r"(?m)^(?=### )", outline)
    h2 = [(re.match(r"^### (H2(?: \(CTA\))?): (.+?)\s*$", b, re.M), b) for b in blocks if b.startswith("### ")]
    bad_h, no_first, no_ev, ev_ids, none_ver = [], [], [], set(), False
    subq = 0
    cta = 0
    for mm, b in h2:
        if not mm:
            bad_h.append(b.split("\n")[0][:60])
            continue
        kind, title = mm.group(1), mm.group(2)
        faq = title.lower() == "frequently asked questions"
        if kind == "H2 (CTA)":
            cta += 1
        elif not faq:
            subq += 1
        if not faq and not title.endswith("?"):
            bad_h.append(title[:60])
        for h3 in re.findall(r"(?m)^#### H3: (.+?)\s*$", b):
            if not (h3.endswith("?") or re.match(r"^(step\s+\d+|\d+[.):])", h3, re.I)):
                bad_h.append(h3[:60])
        if faq:
            if not re.search(r"(?m)^- Questions:", b):
                no_first.append("FAQ has no '- Questions:' line")
            continue
        fs = re.search(r"(?m)^- First sentence must state:\s*(.*)$", b)
        if not fs or not fs.group(1).strip():
            no_first.append(title[:50])
        elif kind != "H2 (CTA)" and len(SLOT.sub("", fs.group(1)).split()) < 6:
            # a slot may support the opening fact but cannot be the whole instruction
            no_first.append(f"{title[:40]} (first sentence is only a client-input slot)")
        ev = re.search(r"(?m)^- Evidence:\s*(.+)$", b)
        if not ev:
            no_ev.append(title[:50])
        else:
            ids = re.findall(r"\bE\d+\b", ev.group(1))
            ev_ids.update(ids)
            if "none verifiable" in ev.group(1).lower():
                none_ver = True
            elif not ids and kind != "H2 (CTA)":
                no_ev.append(title[:50])
    add("Outline headings are questions", not bad_h, "; ".join(bad_h[:5]))
    add("5-8 sub-question sections plus one CTA", 5 <= subq <= 8 and cta == 1, f"{subq} sub-question sections, {cta} CTA")
    add("Every section says what its first sentence must state", not no_first, "; ".join(no_first[:5]))
    add("Every section lists evidence ids or 'none verifiable'", not no_ev, "; ".join(no_ev[:5]))

    # --- entities
    ents = [r for r in table_rows(S.get("Entities and Naming", "")) if r and r[0]]
    add("8-15 entities in the naming table", 8 <= len(ents) <= 15, f"{len(ents)} rows")

    # --- evidence
    ev_rows = [r for r in table_rows(S.get("Evidence", "")) if r and r[0]]
    ev_bad, ev_defined = [], set()
    for r in ev_rows:
        if len(r) < 7:
            ev_bad.append(f"{r[0]}: {len(r)} cells, need 7")
            continue
        rid, fig, src, url, date, label = r[0], r[1], r[2], r[3], r[4], r[5]
        ev_defined.add(rid)
        if not re.fullmatch(r"E\d+", rid):
            ev_bad.append(f"id {rid!r}")
        if not (re.match(r"https?://\S+", url) or re.match(r"file:\s*\S+", url)):
            ev_bad.append(f"{rid}: URL {url!r}")
        if not re.fullmatch(r"\d{4}(-\d{2}(-\d{2})?)?|undated \(accessed \d{4}-\d{2}-\d{2}\)", date):
            ev_bad.append(f"{rid}: date {date!r}")
        if label not in LABELS:
            ev_bad.append(f"{rid}: label {label!r}")
        if not fig or not src:
            ev_bad.append(f"{rid}: empty figure or source")
    add("Evidence rows have id, URL, date and label", not ev_bad, "; ".join(ev_bad[:6]))
    undefined = sorted(ev_ids - ev_defined)
    add("Outline evidence ids exist in the Evidence table", not undefined, ", ".join(undefined))
    unused = sorted(ev_defined - ev_ids - set(re.findall(r"\bE\d+\b", S.get("Answer Target", ""))))
    add("Every evidence row supports a section", not unused, ", ".join(unused), warn=True)

    # --- banned instructions (the Research Log may name tools)
    scan = "\n".join(t for n, t in secs if n not in UNSCANNED) + "\n" + (h1.group(0) if h1 else "")
    hits = sorted({x.group(0) for x in BANNED.finditer(scan)})
    add("No banned instructions or tool names", not hits, ", ".join(hits))

    # --- slots
    slot_nums = [int(n) for n in SLOT.findall(body)]
    listed = [b for b in bullets(S.get("Client Inputs Needed", "")) if b.lower() not in ("none.", "none")]
    list_nums = [int(n) for n in re.findall(r"(?m)^\s*(\d+)[.)]\s+", S.get("Client Inputs Needed", ""))]
    uniq = sorted(set(slot_nums))
    slot_bad = []
    if uniq != list(range(1, len(uniq) + 1)):
        slot_bad.append(f"slot numbers {uniq} are not 1..N without gaps")
    if sorted(list_nums) != uniq:
        slot_bad.append(f"list items {sorted(list_nums)} do not match slots {uniq}")
    if g("client_inputs_open") != len(uniq):
        slot_bad.append(f"client_inputs_open is {g('client_inputs_open')}, {len(uniq)} slots")
    short = [x.group(0) for x in SHORTHAND.finditer(SLOT.sub("", body))]
    if short:
        slot_bad.append("shorthand slot references: " + ", ".join(sorted(set(short))[:4]))
    add("Client-input slots match the numbered list", not slot_bad, "; ".join(slot_bad))

    # --- links
    links = S.get("Internal Links", "")
    out_part = re.search(r"(?ms)^### Links from this page\s*\n(.*?)(?=^### |\Z)", links)
    in_part = re.search(r"(?ms)^### Links to this page\s*\n(.*?)(?=^### |\Z)", links)
    out_rows = table_rows(out_part.group(1)) if out_part else []
    link_bad = []
    if not out_part or not in_part:
        link_bad.append("needs '### Links from this page' and '### Links to this page'")
    for r in out_rows:
        if len(r) < 4:
            link_bad.append(f"row {r} has fewer than 4 cells")
            continue
        if "CLIENT INPUT" in r[0] or not r[0].startswith("/"):  # root-relative paths only
            link_bad.append(f"URL cell {r[0]!r}")
        if GENERIC_ANCHOR.match(r[1]):
            link_bad.append(f"generic anchor {r[1]!r}")
        if r[3].lower() not in ("live", "planned"):
            link_bad.append(f"status {r[3]!r}")
    pu, page = str(g("pillar_url", "N/A")), str(g("page_url", ""))
    if pu not in ("N/A", "") and pu.rstrip("/") != page.rstrip("/"):
        if not any(r and r[0].rstrip("/") == pu.rstrip("/") for r in out_rows):
            link_bad.append(f"pillar {pu} not linked from this page")
    add("Internal link tables complete", out_rows and not link_bad, "; ".join(link_bad[:5]) or "no outbound links")

    # --- a client voice or style source names where the file is, so the writer can open it
    vs = S.get("Voice and Style", "")
    path_bad = [f for f, k in (("voice.md", "voice_source"), ("style.md", "style_source"))
                if g(k) == "client" and not re.search(r"[\w-]+/" + re.escape(f), vs)]
    add("Client voice and style files are named with their path", not path_bad,
        "name the folder, for example project/" + ", project/".join(path_bad))

    # --- author and YMYL
    auth = S.get("Author, Experience and Trust", "")
    add("Author section names an author or a slot", bool(re.search(r"(?m)^- Author:\s*\S", auth)), "no '- Author:' line")
    if g("ymyl") is True:
        add("YMYL brief names a reviewer or a slot", bool(re.search(r"(?m)^- Reviewer:\s*\S", auth)), "no '- Reviewer:' line")

    # --- status consistency
    concerns = [c for c in bullets(S.get("Concerns", "")) if c.lower().rstrip(".") != "none"]
    ctext = " ".join(concerns).lower()
    need = []
    if str(g("voice_source", "")).startswith("default") or str(g("style_source", "")).startswith("default"):
        need.append(("default", "a default voice or style was applied"))
    if uniq:
        need.append(("client input", "there are client-input slots"))
    if g("format_source") and re.search(r"\+|,|/|\band\b", str(g("format_source"))):
        need.append(("normaliz", "the format was normalized from a combo"))
    if g("cannibalization") in ("risk", "clear (unverified)"):
        need.append(("cannibalization", f"cannibalization is {g('cannibalization')}"))
    if none_ver:
        need.append(("verifiable", "a section has no verifiable statistic"))
    missing_c = [why for key, why in need if key not in ctext]
    add("Concerns cover every status trigger", not missing_c, "add a concern because " + "; ".join(missing_c))
    st = g("status")
    if st == "DONE":
        add("Status DONE has no concerns, slots or defaults", not need and not concerns,
            "use DONE_WITH_CONCERNS: " + "; ".join(why for _, why in need) if need else "concerns listed")
    elif st == "DONE_WITH_CONCERNS":
        add("Status DONE_WITH_CONCERNS lists concerns", bool(concerns), "no concerns listed")

    # --- QA checklist and research log
    add("Writer QA Checklist has checkbox items",
        len(re.findall(r"(?m)^- \[ \] ", S.get("Writer QA Checklist", ""))) >= 8, "fewer than 8 '- [ ]' items")
    add("Research Log lists tools available", bool(re.search(r"(?im)^- Tools available:\s*\S", S.get("Research Log", ""))),
        "no '- Tools available:' line")

    fails = [r for r in rows if r[1] == "FAIL"]
    print(f"GATE: {'FAIL' if fails else 'PASS'}\n")
    print(f"Brief: `{p.name}`, status {g('status')}, {len(uniq)} client input slot(s), "
          f"{len(concerns)} concern(s). Failed: {len(fails)}. Warnings: {sum(1 for r in rows if r[1] == 'WARN')}.\n")
    print("| Check | Result | Detail |\n| --- | --- | --- |")
    for c, r, d in rows:
        print(f"| {c} | {r} | {d.replace('|', '/')} |")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
