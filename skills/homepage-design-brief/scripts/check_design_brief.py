#!/usr/bin/env python3
"""Check a homepage design brief against the edited homepage it maps.

Usage:
  check_design_brief.py <brief.md> --article <article.md> [--sources <file> ...] [--wireframe <wireframe.html>]

--sources: every file the brief draws on (client reference kit files, kickoff context, blueprint input
package). Design references and quoted wording are checked against them and the article.
Prints one PASS/FAIL line per check; exit 1 on any FAIL.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hdb  # noqa: E402

REQUIRED = ["Goals", "Audience", "Brand Cues", "Design References", "Section Map", "Imagery",
            "Must-Haves", "Do-Nots", "Open Questions", "Sources"]
TAGGED = ["Goals", "Audience", "Brand Cues", "Imagery", "Must-Haves", "Do-Nots"]
TAG = re.compile(r"\[(article|context|blueprint|user|kit: [a-z]+\.md)\b[^\]]*\]")
MAP_HEADER = ["#", "Section", "Purpose", "Layout idea", "Content source"]
REF_HEADER = ["Reference", "What the client likes", "Source"]
QUOTE = re.compile(r"\"([^\"\n]+)\"|“([^”\n]+)”")
MAX_LINES = 160


def norm(s: str) -> str:
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = re.sub(r"[*_`]", "", s)
    return re.sub(r"\s+", " ", s).strip().lower()


def bullets(body: str) -> list[str]:
    return [ln.strip()[2:].strip() for ln in body.split("\n") if re.match(r"^- \S", ln)]


def ref_name(cell: str) -> str:
    cell = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", cell)  # markdown link -> text
    cell = re.sub(r"\([^)]*\)", "", cell)                  # drop "(domain.com)"
    return re.sub(r"[*_`]", "", cell).strip()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("brief")
    ap.add_argument("--article", required=True)
    ap.add_argument("--sources", nargs="*", default=[])
    ap.add_argument("--wireframe")
    a = ap.parse_args()

    brief = hdb.read(a.brief)
    article = hdb.read(a.article)
    sources = [hdb.read(p) for p in a.sources if Path(p).exists()]
    missing_src = [p for p in a.sources if not Path(p).exists()]
    corpus = norm(article + "\n" + "\n".join(sources))
    results: list[tuple[bool, str, str]] = []

    def add(ok: bool, name: str, detail: str = "") -> None:
        results.append((ok, name, detail))

    add(not missing_src, "Source files exist", ", ".join(missing_src))

    lines = brief.split("\n")
    first = lines[0] if lines else ""
    add(bool(re.match(r"^Client: .+ · Page: .+ · Built: \d{4}-\d{2}-\d{2}\s*$", first)),
        "Header line", "first line must be `Client: <name> · Page: <path> · Built: <YYYY-MM-DD>`")
    review = re.search(r"(?m)^Content review: (confirmed|not confirmed)\b.*$", brief)
    add(bool(review), "Content review line", "add `Content review: confirmed (<who>, <date>)` or `Content review: not confirmed`")

    heads = re.findall(r"(?m)^##\s+(.+?)\s*$", brief)
    add(heads == REQUIRED, "Sections in order", f"found {heads}")
    secs = hdb.md_sections(brief)

    # Section Map: one row per article section, same order
    asecs, mode = hdb.sections(article)
    rows = hdb.table_rows(secs.get("Section Map", ""))
    header_ok = bool(rows) and rows[0] == MAP_HEADER
    body = rows[1:] if header_ok else []
    add(header_ok, "Section Map header", f"must be | {' | '.join(MAP_HEADER)} |")
    want = [s["name"] for s in asecs]
    got = [r[1] if len(r) > 1 else "" for r in body]
    if mode == "markers":
        add(got == want, "Section Map rows match the article's sections in order", f"article {want}, brief {got}")
    else:
        add(len(got) == len(want), "Section Map has one row per article section (no markers: H1 and H2 count)",
            f"article has {len(want)} sections, brief has {len(got)} rows")
    nums_ok = [r[0] for r in body] == [str(i) for i in range(1, len(body) + 1)]
    add(nums_ok, "Section Map rows numbered 1..n")
    empty = [r[1] for r in body if len(r) != 5 or not all(c.strip() for c in r)]
    add(not empty, "Section Map cells filled", ", ".join(empty))
    src_bad = [r[1] for r in body if len(r) == 5 and f"article.md > {r[1]}".lower() not in r[4].lower()]
    add(not src_bad, "Content source names the article section", ", ".join(src_bad) + " (write `article.md > <Section>`)")

    # every claim bullet carries its evidence
    untagged = []
    for s in TAGGED:
        for b in bullets(secs.get(s, "")):
            if not (TAG.search(b) or b.startswith(("GAP:", "Recommended:"))):
                untagged.append(f"{s}: {b[:60]}")
    add(not untagged, "Every bullet tagged, GAP: or Recommended:", "; ".join(untagged[:6]))

    # Design References: only sites the client named, found in the sources
    dref = secs.get("Design References", "")
    rrows = hdb.table_rows(dref)
    if rrows:
        add(rrows[0] == REF_HEADER, "Design References header", f"must be | {' | '.join(REF_HEADER)} |")
        names = [ref_name(r[0]) for r in rrows[1:] if r]
        unsourced = [n for n in names if not n or norm(n) not in norm("\n".join(sources))]
        add(bool(names) and not unsourced, "Design references appear in the client's files", ", ".join(unsourced))
    else:
        add("GAP:" in dref, "Design References: table or a GAP: line", "no table and no GAP: line")

    # Open Questions: every flag on the page, verbatim; review first when not confirmed
    oq = secs.get("Open Questions", "")
    items = re.findall(r"(?m)^\s*\d+\.\s+(.+)$", oq)
    add(bool(items), "Open Questions is a numbered list")
    flags = hdb.flags(article)
    absent = [f for f in flags if f not in oq]
    add(not absent, "Every open flag on the page is an open question, copied verbatim", "; ".join(absent[:5]))
    if review and review.group(1) == "not confirmed":
        add(bool(items) and re.search(r"(?i)review|sign-?off", items[0]) is not None,
            "Unconfirmed review is open question 1")

    # no invented wording: quoted text must exist in the article or a source
    invented = []
    for m in QUOTE.finditer(brief):
        q = (m.group(1) or m.group(2)).strip()
        if len(q.split()) >= 4 and norm(q).strip(" .,;:!?") not in corpus:
            invented.append(q[:60])
    add(not invented, "Quoted wording exists in the article or sources", "; ".join(invented[:5]))

    add(len(lines) <= MAX_LINES, f"At most {MAX_LINES} lines", f"{len(lines)} lines")
    add(not re.search(r"\b(TODO|TBD|FIXME)\b", brief), "No placeholders")

    if a.wireframe:
        html = hdb.read(a.wireframe)
        ext = re.findall(r"(?i)https?://|<script|<link|url\(|<img|<iframe|@import|src\s*=", html)
        add(not ext, "Wireframe has no external assets, scripts or images", ", ".join(sorted(set(ext))))
        add(bool(re.search(r"(?i)<style", html)), "Wireframe CSS is inline")
        ws = re.findall(r'data-section="([^"]+)"', html)
        add(ws == want, "Wireframe sections match the article in order", f"wireframe {ws}")

    fails = 0
    for ok, name, detail in results:
        print(("PASS " if ok else "FAIL ") + name + ("" if ok or not detail else f": {detail}"))
        fails += not ok
    print(f"\n{len(results) - fails}/{len(results)} checks passed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
