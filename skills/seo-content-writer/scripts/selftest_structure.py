#!/usr/bin/env python3
"""Self-test for the passage-size check in check_draft.py and for make_semantic.py. Standard library only.

Usage: python3 selftest_structure.py   (exit 0 when every case behaves as expected)

The passage cases write a small article into a temporary folder, run check_draft.py and read the
"Passage size" and "Passages under 100 words" rows of qa_report.md. The semantic cases build
article-semantic.md from an article and a homepage and check its nesting with --check.
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
        p.write_text(article, encoding="utf-8")
        if meta:
            (Path(d) / "metadata.md").write_text(meta, encoding="utf-8")
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

    # passage size
    good = HEAD + section("Why does a tankless water heater fail early?", 9) + TAIL
    rows = run_qa(good)
    expect("150-word block passes", rows.get("Passage size: no heading block over 300 words") == "PASS", str(rows))
    expect("150-word block is not short", rows.get("Passages under 100 words") == "PASS", str(rows))

    long = HEAD + section("Why does a tankless water heater fail early?", 22) + TAIL
    rows = run_qa(long)
    expect("330-word block FAILs", rows.get("Passage size: no heading block over 300 words") == "FAIL", str(rows))

    short = HEAD + section("Why does a tankless water heater fail early?", 2) + TAIL
    rows = run_qa(short)
    expect("30-word block WARNs", rows.get("Passages under 100 words") == "WARN", str(rows))

    with_h3 = HEAD + section("Why does a tankless water heater fail early?", 2, "What is mineral scale?") + TAIL
    rows = run_qa(with_h3)
    expect("short H2 intro before an H3 does not WARN", rows.get("Passages under 100 words") == "PASS", str(rows))

    # semantic version of an article
    out, log = run_semantic(good, "| Field | Value |\n| --- | --- |\n| Article summary | Scale is the main threat. |\n")
    expect("semantic article checks OK", "SEMANTIC: OK" in log and "error" not in log.lower(), log[-300:])
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
