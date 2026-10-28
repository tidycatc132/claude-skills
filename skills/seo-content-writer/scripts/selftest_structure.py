#!/usr/bin/env python3
"""Self-test for make_semantic.py. Standard library only.

Usage: python3 selftest_structure.py   (exit 0 when every case behaves as expected)

The semantic cases build article-semantic.md from an article and a homepage and check its nesting
with --check.
"""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PY = sys.executable

SENTENCE = "A tankless water heater lasts more than 20 years, according to the U.S. Department of Energy. "
HEAD = """# How Long Does a Tankless Water Heater Last?

By [Marcus Delgado](/about/marcus-delgado/), Master Plumber PB-1188 · Updated 2026-10-23

A tankless water heater lasts more than 20 years, according to the U.S. Department of Energy.

## Key Takeaways

- A tankless water heater lasts more than 20 years (U.S. Department of Energy).

"""
TAIL = """## How do I book a tankless water heater descaling in Portland?

Book a descaling with Harbor & Pine by calling (503) 555-0142 or at [/schedule/](/schedule/).

## Sources

1. U.S. Department of Energy, "Tankless or Demand-Type Water Heaters". Lifespan figures.
"""


def section(title: str, n_sentences: int, h3: str = "") -> str:
    body = ""
    for k in range(n_sentences):
        body += SENTENCE + ("\n\n" if k % 3 == 2 else "")
    out = f"## {title}\n\n{body.strip()}\n\n"
    if h3:
        out += f"### {h3}\n\n{(SENTENCE * 9).strip()}\n\n"
    return out


def run_qa(article: str) -> dict[str, str]:
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "article.md"
        p.write_text(article, encoding="utf-8")
        subprocess.run([PY, str(HERE / "check_draft.py"), str(p), "--keyword", "tankless water heater"],
                       capture_output=True, text=True)
        rep = (Path(d) / "qa_report.md").read_text(encoding="utf-8")
    rows = {}
    for m in re.finditer(r"(?m)^\| ([^|]+?) \| (PASS|WARN|FAIL) \|", rep):
        rows[m.group(1)] = m.group(2)
    return rows


HOMEPAGE = """<!-- section: Hero -->
# Roofing Company in Boise

Juniper Ridge Roofing repairs and replaces roofs in Boise. [Book an inspection](/free-inspection/)

<!-- section: Why Us -->
## Why choose Juniper Ridge Roofing?

Juniper Ridge Roofing is owner-run.

<!-- section: Final CTA -->
## How do I book Juniper Ridge Roofing?

[Book an inspection](/free-inspection/) with Juniper Ridge Roofing.
"""


def run_semantic(article: str, meta: str = "") -> tuple[str, str]:
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "article.md"
        p.write_text(meta + "\n" + article if meta else article, encoding="utf-8")
        r = subprocess.run([PY, str(HERE / "make_semantic.py"), str(p)], capture_output=True, text=True)
        out = (Path(d) / "article-semantic.md").read_text(encoding="utf-8")
        c = subprocess.run([PY, str(HERE / "make_semantic.py"), "--check", str(Path(d) / "article-semantic.md")],
                           capture_output=True, text=True)
    return out, r.stdout + c.stdout


def main() -> int:
    fails: list[str] = []

    def expect(name: str, ok: bool, detail: str = "") -> None:
        print(f"{'ok  ' if ok else 'FAIL'} {name}" + (f": {detail}" if detail and not ok else ""))
        if not ok:
            fails.append(name)

    # long sections are no longer capped
    long = HEAD + section("Why does a tankless water heater fail early?", 22) + TAIL
    rows = run_qa(long)
    expect("no passage-size row", not any(k.startswith("Passage") for k in rows), str(rows))

    # metadata table at the top of article.md; QA report goes to qa/<slug>/, not the page folder
    good = HEAD + section("Why does a tankless water heater fail early?", 9) + TAIL
    meta = ("| Field | Value |\n| --- | --- |\n| Meta title | Tankless Lifespan Guide |\n"
            "| Article summary | Scale is the main threat. |\n")
    with tempfile.TemporaryDirectory() as d:
        page = Path(d) / "content" / "tankless-lifespan"
        page.mkdir(parents=True)
        (page / "article.md").write_text(meta + "\n" + good, encoding="utf-8")
        subprocess.run([PY, str(HERE / "check_draft.py"), str(page / "article.md"), "--keyword", "tankless water heater"],
                       capture_output=True, text=True)
        rep = Path(d) / "qa" / "tankless-lifespan" / "qa_report.md"
        expect("QA report written to qa/<slug>/", rep.is_file() and not (page / "qa_report.md").exists())
        expect("metadata table read from article.md", "Metadata table complete | FAIL | no `" not in
               (rep.read_text(encoding="utf-8") if rep.is_file() else ""))
        subprocess.run([PY, str(HERE / "make_html.py"), str(page / "article.md")], capture_output=True, text=True)
        page_html = (page / "article.html").read_text(encoding="utf-8")
        expect("HTML title from the table, table not in body",
               "<title>Tankless Lifespan Guide</title>" in page_html and "Article summary" not in page_html.split("<body")[-1])

    # semantic version of an article
    out, log = run_semantic(good, meta)
    expect("semantic article checks OK", "SEMANTIC: OK" in log and "error" not in log.lower(), log[-300:])
    expect("metadata table not printed in the semantic version", "| Field | Value |" not in out)
    expect("main > article > header nesting",
           bool(re.search(r'(?s)<main id="main-content">\s*<article id="[^"]+" itemscope[^>]*>\s*<header class="article-header">', out)))
    expect("byline has rel=author and time", 'rel="author"' in out and '<time datetime="2026-10-23"' in out)
    expect("key takeaways section inside header",
           out.index('<section class="key-takeaways"') < out.index("</header>"))
    expect("question H2 becomes a labelled section",
           bool(re.search(r'<section id="why-does-a-tankless-water-heater-fail-early" aria-labelledby="[^"]+-heading">\s*<h2 id="[^"]+-heading">Why does a tankless water heater fail early\?</h2>', out)))
    expect("CTA section carries class cta", 'class="cta"' in out)
    expect("footer holds sources and summary",
           bool(re.search(r'(?s)<footer class="article-footer">.*class="sources".*class="summary".*</footer>\s*</article>\s*</main>', out)))
    expect("no markdown H2 left", not re.search(r"(?m)^##\s", out))
    expect("markdown list kept", bool(re.search(r"(?m)^- A tankless", out)))

    # semantic version of a homepage: markers become data-section, Hero on the header, no byline, no TOC
    out, log = run_semantic(HOMEPAGE)
    expect("homepage semantic checks OK", "SEMANTIC: OK" in log, log[-300:])
    expect("Hero marker on the header", '<header class="article-header" data-section="hero">' in out)
    expect("Final CTA is the cta section", 'class="cta" aria-labelledby="how-do-i-book-juniper-ridge-roofing-heading" data-section="final-cta"' in out)
    expect("no TOC on a client page", "table-of-contents" not in out)
    expect("markers are not printed", "<!--" not in out)

    # --check catches a broken file
    broken = out.replace("</section>\n\n</article>", "</article>", 1)
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "article-semantic.md"
        p.write_text(broken, encoding="utf-8")
        c = subprocess.run([PY, str(HERE / "make_semantic.py"), "--check", str(p)], capture_output=True, text=True)
    expect("--check fails an unclosed section", c.returncode == 1 and "closes <section>" in c.stdout, c.stdout[-200:])

    print(f"\n{len(fails)} failure(s)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
