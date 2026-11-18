#!/usr/bin/env python3
"""Convert `article.md` into `article.html`: semantic, static HTML for the build handoff.

Usage:
  python3 make_html.py ARTICLE.md [--metadata METADATA.md] [--out ARTICLE.html]

Structure produced (no JavaScript, every fact in the initial HTML):
  <head>   <title> from the metadata table's `Meta title`, <meta name="description">
  <article>
    <header>  the H1 and the byline paragraph
    <section class="intro">       paragraphs before the first H2
    <aside class="key-takeaways"> the `## Key Takeaways` section
    <section id="...">            one per other H2, H3 nested inside it
    <section class="sources">     the `## Sources` section
  </article>

A client page's (homepage, About, Contact, location) `<!-- section: Name -->` markers are never printed: each becomes a
`data-section="name"` attribute on the section it opens (Hero goes on <header>
and the intro), so the design brief can map content sections to layout.

Handles paragraphs, ordered and unordered lists, pipe tables, blockquotes,
links, bold, italics and inline code. Leaves [NEEDS ...] flags visible so a
draft with open flags cannot be published silently. Standard library only.
"""
from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:60] or "section"


def inline(s: str) -> str:
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*([^*]+)\*(?![\w*])", r"<em>\1</em>", s)
    s = re.sub(r"(?<!\w)_([^_]+)_(?!\w)", r"<em>\1</em>", s)
    return s


def blocks_to_html(lines: list[str]) -> list[str]:
    out: list[str] = []
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if not s:
            i += 1
            continue
        m = re.match(r"^(#{3,6})\s+(.*)$", s)
        if m:
            lvl = len(m.group(1))
            out.append(f"<h{lvl} id=\"{slug(m.group(2))}\">{inline(m.group(2))}</h{lvl}>")
            i += 1
        elif s.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(lines[i].strip())
                i += 1
            cells = [[c.strip() for c in r.strip("|").split("|")] for r in rows]
            body = [c for c in cells[1:] if not all(re.match(r"^:?-{2,}:?$", x) for x in c if x)]
            out.append("<table>")
            out.append("<thead><tr>" + "".join(f"<th scope=\"col\">{inline(c)}</th>" for c in cells[0]) + "</tr></thead>")
            out.append("<tbody>")
            for r in body:
                out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
            out.append("</tbody></table>")
        elif re.match(r"^[-*+]\s+", s) or re.match(r"^\d+[.)]\s+", s):
            ordered = bool(re.match(r"^\d", s))
            tag = "ol" if ordered else "ul"
            out.append(f"<{tag}>")
            pat = r"^\d+[.)]\s+" if ordered else r"^[-*+]\s+"
            while i < len(lines) and re.match(pat, lines[i].strip()):
                out.append(f"<li>{inline(re.sub(pat, '', lines[i].strip()))}</li>")
                i += 1
            out.append(f"</{tag}>")
        elif s.startswith(">"):
            q = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                q.append(lines[i].strip().lstrip(">").strip())
                i += 1
            out.append(f"<blockquote><p>{inline(' '.join(q))}</p></blockquote>")
        else:
            p = []
            while i < len(lines) and lines[i].strip() and not re.match(r"^(#|\||[-*+]\s|\d+[.)]\s|>)", lines[i].strip()):
                p.append(lines[i].strip())
                i += 1
            out.append(f"<p>{inline(' '.join(p))}</p>")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("article")
    ap.add_argument("--metadata")
    ap.add_argument("--out")
    a = ap.parse_args()
    art = Path(a.article)
    if not art.is_file():
        print(f"article not found: {art}", file=sys.stderr)
        return 2
    md = art.read_text(encoding="utf-8")
    md = re.sub(r"\A---\n.*?\n---\n", "", md, flags=re.S)  # drop front matter if any
    meta_path = Path(a.metadata) if a.metadata else art.with_name("metadata.md")
    cells = {}
    if meta_path.is_file():
        cells = dict((k.strip(), v.strip()) for k, v in
                     re.findall(r"(?m)^\|\s*([^|]+?)\s*\|\s*(.*?)\s*\|\s*$", meta_path.read_text(encoding="utf-8")))

    lines = md.splitlines()
    h1 = next((re.sub(r"^#\s+", "", l).strip() for l in lines if re.match(r"^#\s+", l)), "")
    title = cells.get("Meta title") or h1
    desc = cells.get("Meta description", "")

    # split into chunks by H2; a homepage section marker tags the H1 or H2 that follows it
    pre, chunks, cur = [], [], None
    pending, hero = "", ""
    for l in lines:
        mk = re.match(r"^\s*<!--\s*section:\s*([^>]+?)\s*-->\s*$", l)
        if mk:
            pending = slug(mk.group(1))
            continue
        if re.match(r"^#\s+", l):
            hero, pending = pending, ""
            continue
        m = re.match(r"^##\s+(.*)$", l)
        if m:
            cur = (m.group(1).strip(), [], pending)
            pending = ""
            chunks.append(cur)
        elif cur is None:
            pre.append(l)
        else:
            cur[1].append(l)

    byline, intro = [], []
    for l in pre:
        (byline if re.match(r"^\s*\**by\b", l, re.I) and not byline else intro).append(l)

    o = ["<!doctype html>", '<html lang="en">', "<head>", '<meta charset="utf-8">',
         '<meta name="viewport" content="width=device-width, initial-scale=1">',
         f"<title>{html.escape(title)}</title>"]
    if desc:
        o.append(f'<meta name="description" content="{html.escape(desc)}">')
    ds = lambda name: f' data-section="{name}"' if name else ""
    o += ["</head>", "<body>", "<main>", "<article>", f"<header{ds(hero)}>", f"<h1>{inline(h1)}</h1>"]
    if byline:
        o.append(f'<p class="byline">{inline(byline[0].strip().strip("*").strip())}</p>')
    o.append("</header>")
    if any(l.strip() for l in intro):
        o += [f'<section class="intro"{ds(hero)}>', *blocks_to_html(intro), "</section>"]
    for heading, body, marker in chunks:
        key = heading.lower()
        if key == "key takeaways":
            o += ['<aside class="key-takeaways" aria-labelledby="key-takeaways">',
                  f'<h2 id="key-takeaways">{inline(heading)}</h2>', *blocks_to_html(body), "</aside>"]
        elif key in ("sources", "references", "sources and references"):
            o += ['<section class="sources" aria-labelledby="sources">',
                  f'<h2 id="sources">{inline(heading)}</h2>', *blocks_to_html(body), "</section>"]
        else:
            sid = slug(heading)
            o += [f'<section id="{sid}" aria-labelledby="{sid}-h"{ds(marker)}>',
                  f'<h2 id="{sid}-h">{inline(heading)}</h2>', *blocks_to_html(body), "</section>"]
    o += ["</article>", "</main>", "</body>", "</html>"]
    dest = Path(a.out) if a.out else art.with_suffix(".html")
    dest.write_text("\n".join(o) + "\n", encoding="utf-8")
    print(f"wrote {dest} ({len(chunks)} H2 sections, {sum(1 for x in o if x.startswith('<table'))} tables)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
