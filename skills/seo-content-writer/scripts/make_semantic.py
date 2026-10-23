#!/usr/bin/env python3
"""Write `article-semantic.md`: the page's content wrapped in HTML5 semantic tags, for a CMS or
page builder that accepts markdown with HTML (the second version of the content).

Usage:
  python3 make_semantic.py ARTICLE.md [--metadata METADATA.md] [--out ARTICLE-SEMANTIC.md]
  python3 make_semantic.py --check ARTICLE-SEMANTIC.md      validate nesting and ids, exit 1 on errors

Markdown stays markdown (paragraphs, lists, tables, links, H3s). HTML is used only where markdown
cannot express the tag or the attribute: the landmarks and their ids, aria-labelledby, microdata,
rel="author" and <time datetime>. Every tag sits on its own line with a blank line on each side,
so a CommonMark renderer parses the markdown between the tags.

Structure produced:
  <main id="main-content">
    <article id="<slug>" itemscope itemtype="https://schema.org/Article">
      <header class="article-header">     h1 (itemprop headline), byline (rel=author, <time>), intro,
                                           Key Takeaways <section>, Table of Contents <nav>
      <section id=".." aria-labelledby>   one per question H2; H3s inside stay markdown
      <section ... class="cta">            the call-to-action section (the last question H2)
      <section ... FAQPage microdata>      each FAQ H3 as a Question/Answer <article>
      <footer class="article-footer">     Sources <section>, Article Summary <section> (from metadata.md)
    </article>
  </main>

A client page's `<!-- section: Name -->` markers become `data-section="name"` attributes
(Hero on the header), as make_html.py does. Standard library only.
"""
from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

UTILITY = {"key takeaways", "frequently asked questions", "faq", "faqs", "sources", "references",
           "sources and references"}
FAQ_TITLES = {"frequently asked questions", "faq", "faqs"}
SOURCE_TITLES = {"sources", "references", "sources and references"}
MARKER = re.compile(r"^\s*<!--\s*section:\s*([^>]+?)\s*-->\s*$")


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:60] or "section"


def inline(s: str) -> str:
    """Markdown inline syntax to HTML, for text that must sit inside an HTML tag."""
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*([^*]+)\*(?![\w*])", r"<em>\1</em>", s)
    return s


def byline_html(line: str) -> str:
    """`By [Name](url), creds · Updated 2026-10-23` -> author link with rel/itemprop and a <time>."""
    s = line.strip().strip("*").strip()
    s = html.escape(s, quote=False)
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)",
               lambda m: f'<a rel="author" href="{m.group(2)}" itemprop="author">{m.group(1)}</a>', s, count=1)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\b(\d{4}-\d{2}-\d{2})\b", r'<time datetime="\1" itemprop="dateModified">\1</time>', s, count=1)
    return f'<p class="byline">{s}</p>'


def strip_blank(lines: list[str]) -> list[str]:
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def split_h3(body: list[str]) -> tuple[list[str], list[tuple[str, list[str]]]]:
    """Body lines of an H2 -> (lines before the first H3, [(h3 title, lines)])."""
    pre, items, cur = [], [], None
    for l in body:
        m = re.match(r"^###\s+(.*)$", l)
        if m:
            cur = (m.group(1).strip(), [])
            items.append(cur)
        elif cur is None:
            pre.append(l)
        else:
            cur[1].append(l)
    return pre, items


def build(md: str, cells: dict[str, str]) -> str:
    md = re.sub(r"\A---\n.*?\n---\n", "", md, flags=re.S)
    lines = md.splitlines()
    h1, pre, chunks, cur = "", [], [], None
    pending, hero = "", ""
    client_page = False
    for l in lines:
        mk = MARKER.match(l)
        if mk:
            pending, client_page = slug(mk.group(1)), True
            continue
        if re.match(r"^#\s+", l) and not h1:
            h1 = re.sub(r"^#\s+", "", l).strip()
            hero, pending = pending, ""
            continue
        m = re.match(r"^##\s+(.*)$", l)
        if m:
            cur = {"title": m.group(1).strip(), "body": [], "marker": pending}
            pending = ""
            chunks.append(cur)
        elif cur is None:
            pre.append(l)
        else:
            cur["body"].append(l)

    byline, intro = "", []
    for l in pre:
        if not byline and re.match(r"^\s*\**by\b", l, re.I):
            byline = l
        else:
            intro.append(l)
    intro = strip_blank(intro)

    ds = lambda name: f' data-section="{name}"' if name else ""
    body_chunks = [c for c in chunks if c["title"].lower() not in UTILITY]
    takeaways = next((c for c in chunks if c["title"].lower() == "key takeaways"), None)
    faq = next((c for c in chunks if c["title"].lower() in FAQ_TITLES), None)
    sources = next((c for c in chunks if c["title"].lower() in SOURCE_TITLES), None)

    # the CTA: a client page's Final CTA section, else the last question H2 (output-spec.md puts the CTA last)
    cta = None
    if body_chunks:
        last = body_chunks[-1]
        if not client_page or last["marker"] == "final-cta":
            cta = last

    o: list[str] = []
    o += [f'<main id="main-content">', "",
          f'<article id="{slug(h1)}" itemscope itemtype="https://schema.org/Article">', "",
          f'<header class="article-header"{ds(hero)}>', "",
          f'<h1 itemprop="headline">{inline(h1)}</h1>', ""]
    if byline:
        o += [byline_html(byline), ""]
    if intro:
        o += [*intro, ""]
    if takeaways:
        o += ['<section class="key-takeaways" aria-labelledby="key-takeaways-heading">', "",
              '<h2 id="key-takeaways-heading">Key Takeaways</h2>', "",
              *strip_blank(list(takeaways["body"])), "", "</section>", ""]
    toc_items = [c for c in chunks if c["title"].lower() not in {"key takeaways"} | SOURCE_TITLES]
    if not client_page and len(toc_items) >= 3:
        o += ['<nav class="table-of-contents" aria-labelledby="toc-heading">', "",
              '<h2 id="toc-heading">Table of Contents</h2>', ""]
        o += [f"{i}. [{c['title']}](#{slug(c['title'])})" for i, c in enumerate(toc_items, 1)]
        o += ["", "</nav>", ""]
    o += ["</header>", ""]

    for c in chunks:
        if c is takeaways or c is sources:
            continue
        sid = slug(c["title"])
        if c is faq:
            pre_faq, items = split_h3(c["body"])
            o += [f'<section id="{sid}" aria-labelledby="{sid}-heading"{ds(c["marker"])} '
                  f'itemscope itemtype="https://schema.org/FAQPage">', "",
                  f'<h2 id="{sid}-heading">{inline(c["title"])}</h2>', ""]
            if strip_blank(pre_faq):
                o += [*pre_faq, ""]
            for q, ans in items:
                o += ['<article itemprop="mainEntity" itemscope itemtype="https://schema.org/Question">', "",
                      f'<h3 itemprop="name">{inline(q)}</h3>', "",
                      '<div itemprop="acceptedAnswer" itemscope itemtype="https://schema.org/Answer">', "",
                      '<div itemprop="text">', "", *strip_blank(list(ans)), "", "</div>", "", "</div>", "",
                      "</article>", ""]
            o += ["</section>", ""]
            continue
        cls = ' class="cta"' if c is cta else ""
        o += [f'<section id="{sid}"{cls} aria-labelledby="{sid}-heading"{ds(c["marker"])}>', "",
              f'<h2 id="{sid}-heading">{inline(c["title"])}</h2>', "",
              *strip_blank(list(c["body"])), "", "</section>", ""]

    summary = cells.get("Article summary", "")
    if sources or summary:
        o += ['<footer class="article-footer">', ""]
        if sources:
            o += ['<section class="sources" aria-labelledby="sources-heading">', "",
                  f'<h2 id="sources-heading">{inline(sources["title"])}</h2>', "",
                  *strip_blank(list(sources["body"])), "", "</section>", ""]
        if summary:
            o += ['<section class="summary" aria-labelledby="summary-heading">', "",
                  '<h2 id="summary-heading">Article Summary</h2>', "", summary, "", "</section>", ""]
        o += ["</footer>", ""]
    o += ["</article>", "", "</main>"]
    return "\n".join(o) + "\n"


OPEN = re.compile(r"^<(main|article|header|footer|section|nav|aside|div)\b([^>]*)>$")
CLOSE = re.compile(r"^</(main|article|header|footer|section|nav|aside|div)>$")
HEAD = re.compile(r"^<h([1-6])\b([^>]*)>(.*)</h[1-6]>$")


def check(text: str) -> list[str]:
    """Nesting, ids and heading order of an article-semantic.md. Returns the error list."""
    errors: list[str] = []
    stack: list[str] = []
    ids: set[str] = set()
    labelled: list[tuple[int, str]] = []
    levels: list[tuple[int, int]] = []
    counts = {"main": 0, "article": 0}
    for n, raw in enumerate(text.splitlines(), 1):
        l = raw.strip()
        if re.search(r"&lt;/?[a-z]+", l):
            errors.append(f"line {n}: escaped tag text ({l[:50]})")
        m = OPEN.match(l)
        if m:
            tag, attrs = m.group(1), m.group(2)
            if tag == "main":
                counts["main"] += 1
                if stack:
                    errors.append(f"line {n}: <main> must be the outermost tag")
            elif tag == "article" and not (stack and stack[-1] == "section"):
                counts["article"] += 1
                if stack != ["main"]:
                    errors.append(f"line {n}: <article> must sit directly inside <main>")
            elif tag in ("header", "footer", "section", "nav", "aside") and "article" not in stack:
                errors.append(f"line {n}: <{tag}> outside the <article>")
            if tag == "section":
                sid = re.search(r'\bid="([^"]+)"', attrs)
                lab = re.search(r'\baria-labelledby="([^"]+)"', attrs)
                if not lab:
                    errors.append(f"line {n}: <section> without aria-labelledby")
                else:
                    labelled.append((n, lab.group(1)))
                if "class=" not in attrs and not sid:
                    errors.append(f"line {n}: <section> without an id")
            stack.append(tag)
            continue
        m = CLOSE.match(l)
        if m:
            if not stack or stack[-1] != m.group(1):
                errors.append(f"line {n}: </{m.group(1)}> closes <{stack[-1] if stack else 'nothing'}>")
                if stack:
                    stack.pop()
            else:
                stack.pop()
            continue
        m = HEAD.match(l)
        if m:
            lvl, attrs = int(m.group(1)), m.group(2)
            hid = re.search(r'\bid="([^"]+)"', attrs)
            if hid:
                ids.add(hid.group(1))
            if "article" not in stack:
                errors.append(f"line {n}: heading outside the <article>")
            levels.append((n, lvl))
            continue
        mm = re.match(r"^(#{1,6})\s", l)
        if mm:
            lvl = len(mm.group(1))
            if lvl <= 2:
                errors.append(f"line {n}: markdown H{lvl} must be an HTML heading with an id")
            levels.append((n, lvl))
    if stack:
        errors.append(f"unclosed: {' > '.join(stack)}")
    if counts["main"] != 1:
        errors.append(f"{counts['main']} <main> tags (need exactly 1)")
    if counts["article"] != 1:
        errors.append(f"{counts['article']} top-level <article> tags (need exactly 1)")
    for n, lab in labelled:
        if lab not in ids:
            errors.append(f"line {n}: aria-labelledby=\"{lab}\" names no heading id")
    prev = 0
    for n, lvl in levels:
        if lvl > prev + 1:
            errors.append(f"line {n}: heading level jumps from h{prev} to h{lvl}")
        prev = lvl
    if levels and levels[0][1] != 1:
        errors.append("the first heading is not the h1")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("article", help="article.md to convert, or the article-semantic.md to --check")
    ap.add_argument("--metadata")
    ap.add_argument("--out")
    ap.add_argument("--check", action="store_true", help="validate an article-semantic.md instead of writing one")
    a = ap.parse_args()
    src = Path(a.article)
    if not src.is_file():
        print(f"file not found: {src}", file=sys.stderr)
        return 2
    text = src.read_text(encoding="utf-8")
    if a.check:
        errs = check(text)
        for e in errs:
            print(f"ERROR: {e}")
        print("SEMANTIC: " + ("OK" if not errs else f"{len(errs)} error(s)"))
        return 1 if errs else 0
    meta_path = Path(a.metadata) if a.metadata else src.with_name("metadata.md")
    cells: dict[str, str] = {}
    if meta_path.is_file():
        cells = dict((k.strip(), v.strip()) for k, v in
                     re.findall(r"(?m)^\|\s*([^|]+?)\s*\|\s*(.*?)\s*\|\s*$", meta_path.read_text(encoding="utf-8")))
    out = build(text, cells)
    dest = Path(a.out) if a.out else src.with_name("article-semantic.md")
    dest.write_text(out, encoding="utf-8")
    errs = check(out)
    for e in errs:
        print(f"ERROR: {e}")
    print(f"wrote {dest} ({out.count('<section ')} sections) SEMANTIC: {'OK' if not errs else str(len(errs)) + ' error(s)'}")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
