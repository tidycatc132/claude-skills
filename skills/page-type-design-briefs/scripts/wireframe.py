#!/usr/bin/env python3
"""Template wireframes: one grey-box HTML file per page type, built from a finished brief.

Usage (run from the client's working folder; paths are relative to it):
  python3 wireframe.py build --slug SLUG [--only TYPE] [--root .] [--kit DIR] [--type URL_SLUG=TYPE ...]
  python3 wireframe.py check --slug SLUG [same options]

build  needs design/<slug>/<slug>-page-type-design-briefs.md to pass `ptdb.py check`. For every page
       type in the brief it writes design/<slug>/<slug>-<page-type>-wireframe.html: one <section> per
       Content Map row, in the brief's order, labelled with the row's number and section name and
       holding the real copy of the longest page of that type (a section that page lacks takes its
       copy from the longest page that has it). Neutral greys only, unless the type's Brand Reference
       gives a tagged colour for headings, body text or the call to action. Inline CSS, no scripts,
       images, fonts or outside links, so an HTML-to-Figma plugin imports it as plain frames. Then it
       runs check on what it wrote.
check  verifies every wireframe against the brief and the pages. Exit 1 on any FAIL.

Standard library only.
"""
from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ptdb  # noqa: E402

GREYS = {"#ffffff": "page", "#f2f2f2": "canvas", "#e6e6e6": "label", "#cccccc": "line",
         "#999999": "dashed", "#666666": "note", "#333333": "heading", "#222222": "text"}
ROLES = [
    ("cta", re.compile(r"(?i)\bcalls? to action\b|\bCTAs?\b|\bbuttons?\b")),
    ("heading", re.compile(r"(?i)\bheadings?\b|\bheadlines?\b")),
    ("text", re.compile(r"(?i)\bbody text\b|\bbody copy\b|\btext colou?r\b|\bparagraphs?\b")),
    ("heading", re.compile(r"(?i)\bprimary\b|\bmain colou?r\b")),
]
REFUSE = re.compile(r"(?i)\b(?:no|never|not|avoid|banned|don't|do not|retired|old|former|legacy|background|backgrounds)\b")
GENERIC = re.compile(r"(?i)\bH2s?\b|\bquestions?\b|\bsections\b|\bremaining\b|\bbody\b")
LINK = re.compile(r"\[([^\]]+)\]\(([^)]*)\)")
FORBIDDEN = [
    (re.compile(r"(?i)<script\b"), "a script"),
    (re.compile(r"(?i)<img\b|<svg\b|<video\b|<iframe\b"), "an image or embed"),
    (re.compile(r"(?i)<link\b|@import|@font-face|url\("), "an outside file or font"),
    (re.compile(r"(?i)\bhref="), "a link target"),
]
CSS = """
*{box-sizing:border-box}
body{margin:0;background:#f2f2f2;color:TEXT;font-family:Arial,Helvetica,sans-serif;line-height:1.5}
.wf-meta{padding:16px 24px;background:#333333;color:#ffffff}
.wf-meta p{margin:4px 0}
main{max-width:1200px;margin:0 auto;padding:24px}
.wf-section{margin:0 0 24px;padding:24px;background:#ffffff;border:2px dashed #999999}
.wf-section[data-cta="yes"]{border-style:solid}
.wf-label{display:inline-block;margin:0 0 8px;padding:2px 8px;background:#e6e6e6;color:#333333}
.wf-section[data-cta="yes"] .wf-label{background:CTA;color:ONCTA}
.wf-purpose,.wf-from{margin:0 0 12px;color:#666666}
.wf-item{margin:12px 0;padding:12px;border:1px solid #cccccc}
.wf-flag{padding:2px 6px;border:1px dashed #666666;background:#e6e6e6;color:#222222}
.wf-link{text-decoration:underline}
h1,h2,h3,h4{color:HEADING}
table{border-collapse:collapse}td,th{padding:4px 8px;border:1px solid #cccccc}
"""


# ---------------------------------------------------------------- the brief

def type_sections(brief: str) -> dict[str, str]:
    """page type -> that type's section body in the brief."""
    names = {v: k for k, v in ptdb.HEADINGS.items()}
    return {names[h]: body for h, body in ptdb.blocks(brief, 2) if h in names}


def sub(body: str, name: str) -> str:
    return dict(ptdb.blocks(body, 3)).get(name, "")


def content_map(body: str) -> list[dict[str, str]]:
    rows = []
    for ln in sub(body, "Content Map").splitlines():
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) == 5 and cells[0].isdigit():
            rows.append(dict(zip(["n", "section", "purpose", "on", "source"], cells)))
    return rows


def pages_listed(body: str) -> list[str]:
    return re.findall(r"(?m)^- `([^`]+)`", sub(body, "Pages"))


def colours(body: str) -> dict[str, tuple[str, str]]:
    """role -> (hex, the Brand Reference bullet it came from). Tagged bullets only, never a GAP line.
    Each colour is read in its own clause (the bullet cut at `;` and `,`): a clause that bans, retires or
    sets a background skips its colour, and a clause naming no role leaves it unused."""
    out: dict[str, tuple[str, str]] = {}
    for b in ptdb.bullets(sub(body, "Brand Reference")):
        if b.startswith("GAP") or not ptdb.TAG.search(b):
            continue
        for clause in re.split(r"[;,]", unquoted(b)):
            for m in ptdb.HEX.finditer(clause):
                if REFUSE.search(clause):
                    continue
                for role, rx in ROLES:
                    if rx.search(clause):
                        if role not in out:
                            out[role] = (m.group(0).upper(), b)
                        break
    return out


def unquoted(s: str) -> str:
    return re.sub(r"\"[^\"]*\"|“[^”]*”", " ", s)


def cta_sections(body: str, rows: list[dict[str, str]]) -> set[str]:
    clauses = [c for b in ptdb.bullets(sub(body, "CTAs")) for c in re.split(r"[;,.]", b.lower())
               if not re.search(r"\b(?:no|not|never|without)\b", c)]
    return {r["section"] for r in rows
            if any(re.search(rf"(?<![\w-]){re.escape(r['section'].lower())}(?![\w-])", c) for c in clauses)}


# ---------------------------------------------------------------- the pages

def page_blocks(text: str) -> list[dict]:
    """The page cut into blocks: by section markers when it has them, else the opening and each H2."""
    text = re.split(r"(?m)^## Sources\s*$", text)[0]
    if ptdb.MARKER.search(text):
        parts = ptdb.MARKER.split(text)
        out = [{"key": parts[i].strip(), "heading": parts[i].strip(), "md": parts[i + 1].strip()}
               for i in range(1, len(parts), 2)]
        if parts[0].strip() and out:
            out[0]["md"] = parts[0].strip() + "\n\n" + out[0]["md"]
        return out
    chunks = re.split(r"(?m)^(?=## )", text)
    out = [{"key": "opening", "heading": "H1 and opening", "md": chunks[0].strip()}]
    for c in chunks[1:]:
        head = c.splitlines()[0][3:].strip()
        out.append({"key": head, "heading": head, "md": c.strip()})
    return out


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", "", s.lower()).strip()


def anchor(row: dict[str, str], blocks: list[dict]) -> int | None:
    spec = row["source"].split(">", 1)[-1].strip()
    want = [norm(spec), norm(row["section"])]
    if re.search(r"(?i)\bH1\b|\bopening\b|\bintro", spec) and blocks and blocks[0]["key"] == "opening":
        return 0
    if re.search(r"(?i)\blast H2\b|\bclosing\b", spec):
        return len(blocks) - 1 if len(blocks) > 1 else None
    for i, b in enumerate(blocks):
        if norm(b["heading"]) in want:
            return i
    for i, b in enumerate(blocks):
        h = norm(b["heading"])
        if any(len(w) >= 4 and (w in h or h in w) for w in want if w):
            return i
    return None


def assign(rows: list[dict[str, str]], blocks: list[dict]) -> tuple[list[list[int]], list[str]]:
    """Content Map rows -> block indexes. Anchored rows take their block. Between two anchors, the blocks
    go to the first row there whose source names a run of sections (`H2 question sections`); a row whose
    source names a heading the page lacks gets nothing. Blocks no row takes join the row before them."""
    anchors: list[int | None] = []
    last = -1
    for r in rows:
        a = anchor(r, blocks)
        anchors.append(a if a is not None and a > last else None)
        if anchors[-1] is not None:
            last = anchors[-1]
    got: list[list[int]] = [[a] if a is not None else [] for a in anchors]
    notes: list[str] = []
    i = 0
    while i <= len(rows):
        j = i
        while j < len(rows) and anchors[j] is None:
            j += 1
        lo = anchors[i - 1] if i > 0 else -1
        hi = anchors[j] if j < len(rows) else len(blocks)
        free = list(range(lo + 1, hi))
        run = list(range(i, j))
        taker = next((r for r in run if GENERIC.search(rows[r]["source"].split(">", 1)[-1])), None)
        if taker is not None:
            got[taker] = free
        elif free:
            home = i - 1 if i > 0 else j
            if home < len(rows):
                got[home] = sorted(got[home] + free)
                notes.append(f"{', '.join(blocks[f]['heading'] for f in free)} placed under {rows[home]['section']}")
        i = j + 1
    return got, notes


# ---------------------------------------------------------------- markdown to html

def inline(s: str) -> str:
    out, pos = [], 0
    for m in re.finditer(r"\[(?:NEEDS INPUT|NEEDS SOURCE|CLIENT INPUT NEEDED #\d+):[^\]]*\]|" + LINK.pattern, s):
        out.append(html.escape(s[pos:m.start()]))
        if m.group(0).startswith("[") and LINK.fullmatch(m.group(0)):
            out.append(f'<span class="wf-link">{html.escape(m.group(1))}</span>')
        else:
            out.append(f'<span class="wf-flag">{html.escape(m.group(0))}</span>')
        pos = m.end()
    out.append(html.escape(s[pos:]))
    return re.sub(r"\*\*(.+?)\*\*|__(.+?)__", lambda m: m.group(1) or m.group(2), "".join(out))


def md_html(md: str) -> list[str]:
    out: list[str] = []
    lines = re.sub(r"<!--.*?-->", "", md, flags=re.S).splitlines()
    item_open = False
    i = 0
    while i < len(lines):
        ln = lines[i].rstrip()
        s = ln.strip()
        if not s:
            i += 1
            continue
        h = re.match(r"^(#{1,4}) (.+)$", s)
        if h:
            lvl = len(h.group(1))
            if lvl == 3:
                if item_open:
                    out.append("</div>")
                out.append('<div class="wf-item" data-component="item">')
                item_open = True
            out.append(f"<h{lvl}>{inline(h.group(2))}</h{lvl}>")
            i += 1
            continue
        if re.match(r"^([-*]|\d+\.) ", s):
            tag = "ol" if s[0].isdigit() else "ul"
            out.append(f"<{tag}>")
            while i < len(lines) and re.match(r"^([-*]|\d+\.) ", lines[i].strip()):
                out.append(f'<li data-component="item">{inline(re.sub(r"^([-*]|[0-9]+[.]) ", "", lines[i].strip()))}</li>')
                i += 1
            out.append(f"</{tag}>")
            continue
        if s.startswith("|"):
            out.append("<table>")
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
                    out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in cells) + "</tr>")
                i += 1
            out.append("</table>")
            continue
        para = []
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#{1,4} |([-*]|\d+\.) |\|)", lines[i].strip()):
            para.append(lines[i].strip().lstrip("> ").strip())
            i += 1
        out.append(f"<p>{inline(' '.join(para))}</p>")
    if item_open:
        out.append("</div>")
    return out


def plain(md_line: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", inline(md_line)))).strip()


def copy_lines(md: str) -> list[str]:
    out = []
    for ln in re.sub(r"<!--.*?-->", "", md, flags=re.S).splitlines():
        s = re.sub(r"^(#{1,4}|[-*]|\d+\.|>)\s+", "", ln.strip())
        if s and not re.fullmatch(r"\|?[\s:|-]+\|?", s):
            for cell in s.strip("|").split("|") if s.startswith("|") else [s]:
                if cell.strip():
                    out.append(plain(cell.strip()))
    return out


# ---------------------------------------------------------------- building

def wireframe_path(slug: str, kind: str) -> str:
    return f"design/{slug}/{slug}-{kind}-wireframe.html"


def plan(root: Path, s: dict, brief: str) -> list[dict]:
    """Everything a wireframe holds, per page type: rows, the copy per row, colours."""
    out = []
    for kind, body in type_sections(brief).items():
        pages = [p for p in s["pages"] if p["type"] == kind and p["path"] in pages_listed(body)]
        if not pages:
            continue
        pages.sort(key=lambda p: (-p["words"], p["path"]))
        longest = pages[0]
        texts = {p["path"]: ptdb.read(root / p["path"]) for p in pages}
        rows = content_map(body)
        blocks = page_blocks(texts[longest["path"]])
        got, notes = assign(rows, blocks)
        filled = []
        for r, idx in zip(rows, got):
            src, mds = longest["path"], [blocks[k]["md"] for k in idx]
            if not idx and r["on"] != "all":
                for p in pages[1:]:
                    other = page_blocks(texts[p["path"]])
                    k = anchor(r, other)
                    if k is not None and other[k]["key"] != "opening":
                        src, mds = p["path"], [other[k]["md"]]
                        break
                else:
                    src = ""
            elif not idx:
                src = ""
            filled.append({**r, "from": src, "mds": mds})
        out.append({"type": kind, "heading": ptdb.HEADINGS[kind], "path": wireframe_path(s["slug"], kind),
                    "longest": longest, "count": len(pages), "rows": filled, "notes": notes,
                    "colours": colours(body), "cta": cta_sections(body, rows)})
    return out


def slug_id(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def render(w: dict, client: str, brief_path: str) -> str:
    c = w["colours"]
    css = (CSS.replace("TEXT", c["text"][0] if "text" in c else "#222222")
              .replace("HEADING", c["heading"][0] if "heading" in c else "#333333")
              .replace("ONCTA", "#222222" if "cta" in c else "#ffffff")
              .replace("CTA", c["cta"][0] if "cta" in c else "#666666"))
    if c:
        legend = "Colours from the brief: " + "; ".join(f"{role} {hx}" for role, (hx, _) in c.items())
    else:
        legend = "Colours: neutral greys only (the brief gives no sourced colours)"
    lp = w["longest"]
    L = ["<!DOCTYPE html>", '<html lang="en">', "<head>", '<meta charset="utf-8">',
         '<meta name="viewport" content="width=device-width, initial-scale=1">',
         f"<title>{html.escape(client)}: {w['heading']} template wireframe</title>",
         f"<style>{css}</style>", "</head>", "<body>",
         '<header class="wf-meta" data-component="wireframe-info">',
         f"<p>{html.escape(client)} · {w['heading']} template · grey-box wireframe</p>",
         f"<p>Copy from: {lp['path']} (longest of {w['count']} page{'s' if w['count'] != 1 else ''}, {lp['words']} words)</p>",
         f"<p>Brief: {brief_path} · Structure and copy only; Design decides the look.</p>",
         f"<p>{html.escape(legend)}</p>", "</header>",
         f'<main data-template="{w["type"]}">']
    for r in w["rows"]:
        sid = f"s{int(r['n']):02d}-{slug_id(r['section'])}"
        cta = ' data-cta="yes"' if r["section"] in w["cta"] else ""
        L.append(f'<section class="wf-section" id="{sid}" data-section="{html.escape(r["section"])}" '
                 f'data-component="section"{cta} aria-labelledby="{sid}-label">')
        tag = " · CTA" if cta else ""
        L.append(f'<p class="wf-label" id="{sid}-label">{int(r["n"]):02d} · {html.escape(r["section"])}{tag} · {html.escape(r["on"])}</p>')
        L.append(f'<p class="wf-purpose">{html.escape(r["purpose"])}</p>')
        if r["from"] and r["from"] != lp["path"]:
            L.append(f'<p class="wf-from">Copy from {r["from"]} (not on the longest page)</p>')
        if r["mds"]:
            L.append('<div class="wf-content">')
            for md in r["mds"]:
                if len(r["mds"]) > 1:
                    L.append('<div class="wf-item" data-component="item">')
                L += md_html(md)
                if len(r["mds"]) > 1:
                    L.append("</div>")
            L.append("</div>")
        else:
            L.append('<p class="wf-from">No copy matched this section&#x27;s Content source; check the brief&#x27;s Content Map.</p>')
        L.append("</section>")
    L += ["</main>", "</body>", "</html>"]
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- checking

def check(root: Path, s: dict, brief: str, ws: list[dict]) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []

    def add(ok: bool, name: str, detail: str = "") -> None:
        rows.append(("PASS" if ok else "FAIL", name, detail))

    for w in ws:
        p = root / w["path"]
        name = w["path"]
        page = ptdb.read(p)
        if not page:
            add(False, f"{name}: exists")
            continue
        labels = [html.unescape(x) for x in re.findall(r'<section [^>]*data-section="([^"]*)"', page)]
        want = [r["section"] for r in w["rows"]]
        add(labels == want, f"{name}: sections in Content Map order", f"found {labels}, brief has {want}")
        missing = [f"{r['section']}" for r in w["rows"]
                   if not re.search(rf'data-section="{re.escape(html.escape(r["section"]))}"[^>]*>\s*<p class="wf-label"[^>]*>{int(r["n"]):02d} · ', page)]
        add(not missing, f"{name}: every section labelled with its number and name", ", ".join(missing))
        add(w["longest"]["path"] in page, f"{name}: names the longest page", w["longest"]["path"])
        parts = re.split(r'(?=<section [^>]*data-section=")', page)
        texts = {}
        for part in parts[1:]:
            key = html.unescape(re.match(r'<section [^>]*data-section="([^"]*)"', part).group(1))
            texts[key] = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", part)))
        lost = [f"{r['section']}: {ln}" for r in w["rows"] for md in r["mds"] for ln in copy_lines(md)
                if ln not in texts.get(r["section"], "")]
        add(not lost, f"{name}: real copy from the pages, in its own section", " | ".join(lost[:4]))
        allowed = {h.lower() for h in GREYS} | {hx.lower() for hx, _ in w["colours"].values()}
        stray = sorted({h for h in ptdb.HEX.findall(page) if h.lower() not in allowed})
        add(not stray, f"{name}: greys, or colours the Brand Reference gives", ", ".join(stray))
        bad = [why for rx, why in FORBIDDEN if rx.search(page)]
        add(not bad, f"{name}: self-contained (no scripts, images, fonts or outside links)", ", ".join(bad))
    expected = {wireframe_path(s["slug"], k) for k in type_sections(brief)}
    extra = sorted(p.relative_to(root).as_posix() for p in (root / "design" / s["slug"]).glob(f"{s['slug']}-*-wireframe.html")
                   if p.relative_to(root).as_posix() not in expected and not p.name.endswith("-homepage-wireframe.html"))
    add(not extra, "no wireframe for a page type the brief does not have", ", ".join(extra))
    return rows


# ---------------------------------------------------------------- cli

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["build", "check"])
    ap.add_argument("--slug", required=True)
    ap.add_argument("--only", choices=ptdb.TYPES, help="one page type")
    ap.add_argument("--root", default=".")
    ap.add_argument("--kit")
    ap.add_argument("--type", action="append", default=[], help="url-slug=type, as given to ptdb.py")
    a = ap.parse_args()

    overrides = {}
    for o in a.type:
        k, _, v = o.partition("=")
        overrides[k] = v
    root = Path(a.root)
    s = ptdb.scan(root, a.slug, a.kit, overrides)
    brief_file = root / s["brief_path"]
    brief = ptdb.read(brief_file)
    if not brief:
        print(f"No brief at {s['brief_path']}. Write the page-type design briefs first; wireframes are built from them.",
              file=sys.stderr)
        return 2
    rep = ptdb.check(brief_file, s, root)
    if not rep.ok:
        for status, name, detail in rep.rows:
            if status == "FAIL":
                print(f"FAIL  brief: {name}" + (f"  ({detail})" if detail else ""), file=sys.stderr)
        print(f"{s['brief_path']} does not pass `ptdb.py check`. Finish the brief first; no wireframe written.",
              file=sys.stderr)
        return 1

    client = re.search(r"(?m)^Client: (.+?) · ", brief).group(1)
    ws = [w for w in plan(root, s, brief) if not a.only or w["type"] == a.only]
    if a.mode == "build":
        for w in ws:
            out = root / w["path"]
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(render(w, client, s["brief_path"]), encoding="utf-8")
            col = ", ".join(f"{role} {hx}" for role, (hx, _) in w["colours"].items()) or "greys only"
            print(f"wrote {w['path']}  sections={len(w['rows'])}  copy from {w['longest']['path']}  colours: {col}")
            for r in w["rows"]:
                if r["from"] and r["from"] != w["longest"]["path"]:
                    print(f"    {r['section']}: copy from {r['from']}")
                elif not r["from"]:
                    print(f"    {r['section']}: no copy matched its Content source (check the Content Map)")
            for n in w["notes"]:
                print(f"    {n}")
    results = check(root, s, brief, ws)
    for status, name, detail in results:
        print(f"{status}  {name}" + (f"  ({detail})" if detail and status == "FAIL" else ""))
    ok = all(r[0] == "PASS" for r in results)
    print(f"RESULT: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
