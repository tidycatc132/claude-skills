#!/usr/bin/env python3
"""Self-test for dev_index.py on copies of the invented Thistlewood Roofing fixture.

Run from the repository root: python3 skills/dev-handoff-index/scripts/selftest_dev_index.py
File modification times are set explicitly, so holds and releases do not depend on copy order.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "dev_index.py"
ROOT = HERE.parents[2]
FIX = ROOT / "fixtures" / "dev-handoff-index" / "thistlewood"
SLUG = "thistlewood-roofing"
INDEX = f"handoff/{SLUG}/{SLUG}-dev-handoff-index.md"

results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))


def make(*variants: str) -> Path:
    d = Path(tempfile.mkdtemp(prefix="dhi-"))
    shutil.copytree(FIX / "base", d, dirs_exist_ok=True)
    for v in variants:
        shutil.copytree(FIX / "variants" / v, d, dirs_exist_ok=True)
    # every file old, feedback files newer: held pages stay held until touched
    for p in d.rglob("*"):
        if p.is_file():
            os.utime(p, (1_000_000, 1_000_000))
    for p in (d / "feedback" / SLUG).glob("*.md"):
        os.utime(p, (2_000_000, 2_000_000))
    return d


def touch(d: Path, rel: str, t: int = 3_000_000) -> None:
    os.utime(d / rel, (t, t))


def run(d: Path) -> tuple[int, str, str]:
    p = subprocess.run([sys.executable, str(SCRIPT), "run", "--date", "2026-10-28"], cwd=d,
                       capture_output=True, text=True)
    text = (d / INDEX).read_text(encoding="utf-8") if (d / INDEX).exists() else ""
    return p.returncode, p.stdout, text


def status(text: str, page: str) -> str:
    m = re.search(r"### " + re.escape(page) + r"\n(?:[ -][^\n]*\n|\n)*?- Status: ([^\n]*)", text)
    return m.group(1) if m else ""


def main() -> int:
    temps = []
    try:
        d = make(); temps.append(d)
        rc, out, t = run(d)
        check("base: NO-GO, exit 1", rc == 1 and t.rstrip().endswith("\nNO-GO"), out[-200:])
        check("base: summary counts", "Pages: 4 READY, 2 WAITING ON CLIENT CHANGES, 2 NOT WRITTEN, 0 NO TEMPLATE" in t)
        check("held by page: Affects", status(t, "Roof Repair").startswith("WAITING ON CLIENT CHANGES (feedback/"),
              status(t, "Roof Repair"))
        check("held by Impact pages list", status(t, "Redmond Roofer").startswith("WAITING ON CLIENT CHANGES"))
        check("Impact none does not hold", status(t, "About") == "READY")
        check("older feedback file ignored", status(t, "Contact") == "READY")
        check("not written page", status(t, "Gutter Installation") == "NOT WRITTEN")
        check("post-launch not blocking", "Storm Damage Roof Guide" not in t.split("## Blocking")[1]
              and "- Priority: Post-Launch" in t)
        check("meta title keeps its pipe",
              "- Meta title: Roof Repair in Redmond: Leaks, Flashing and Storm Damage | Thistlewood Roofing" in t)
        check("internal link with anchor", "  - /services/roof-repair/ (anchor: roof repair)" in t)
        check("link to old URL flagged", "/gallery/ (anchor: past projects) NOT IN SITEMAP, no redirect target" in t)
        check("redirect from map", "| https://thistlewoodroofing.com/about-us/ | /about/ |" in t)
        check("NO TARGET row", "| https://thistlewoodroofing.com/gallery/ | NO TARGET |" in t)
        check("kept URLs get no redirect row", "| https://thistlewoodroofing.com/contact/ |" not in t
              and "| https://thistlewoodroofing.com/ |" not in t)
        check("structured data line", "Structured data: not in the current process" in t)
        check("conversion routes", "- Contact: contact form (section: Contact Form)" in t
              and "- Contact: mailto:office@thistlewoodroofing.com" in t)
        check("no design QA yet", "Design QA and dev prep: not run yet" in t and "## Design Assets" not in t)

        touch(d, "content/roof-repair/article.md")
        rc, out, t = run(d)
        check("release after rewrite", status(t, "Roof Repair") == "READY", status(t, "Roof Repair"))
        check("other hold stays", status(t, "Redmond Roofer").startswith("WAITING"))

        d = make("complete"); temps.append(d)
        touch(d, "content/roof-repair/article.md")
        rc, out, t = run(d)
        check("complete: GO, exit 0", rc == 0 and t.rstrip().endswith("\nGO"), out[-300:])
        check("complete: counts", "Pages: 6 READY, 1 WAITING ON CLIENT CHANGES, 1 NOT WRITTEN, 0 NO TEMPLATE" in t)
        check("complete: old index replaced", "Pages: 4 READY" not in t)
        check("asset checklist copied", "- #2F4A3A forest green, #F4EFE6 cream, #1F1F1F text" in t
              and "### Interactive elements" in t)
        rc2, _, t2 = run(d)
        check("rerun is identical", rc2 == rc and t2 == t)

        d = make("complete"); temps.append(d)
        qa = d / "design" / SLUG / f"{SLUG}-design-qa-devprep.md"
        qa.write_text(qa.read_text(encoding="utf-8").replace("RESULT: PASS", "RESULT: FAIL"), encoding="utf-8")
        rc, out, t = run(d)
        check("design QA FAIL blocks", rc == 1 and "Design QA and dev prep:" in t.split("## Blocking")[1])

        d = make("complete"); temps.append(d)
        b = d / "design" / SLUG / f"{SLUG}-page-type-design-briefs.md"
        b.write_text(b.read_text(encoding="utf-8").replace("- `content/about/article.md`\n", ""), encoding="utf-8")
        rc, out, t = run(d)
        check("no template blocks", status(t, "About") == "NO TEMPLATE" and rc == 1
              and "### About" in t.split("## Pages Without a Template")[1])

        d = make("complete"); temps.append(d)
        (d / "content" / "gutter-installation" / "metadata.md").unlink()
        rc, out, t = run(d)
        check("article without metadata is not written",
              status(t, "Gutter Installation") == "NOT WRITTEN (article.md has no metadata.md)", status(t, "Gutter Installation"))

        d = make("newsite"); temps.append(d)
        rc, out, t = run(d)
        check("no existing site", "No existing site" in t and "NO TARGET" not in t)
        check("week 2 not cleared blocks", rc == 1 and re.search(r"- Week 2 handoff:[^\n]*NO-GO", t) is not None)

        d = make(); temps.append(d)
        (d / "kickoff" / SLUG / f"{SLUG}-url-inventory.csv").unlink()
        rc, out, t = run(d)
        check("missing inventory blocks", rc == 1 and "URL inventory:" in t.split("## Blocking")[1])

        # readers used by the contracts
        p = subprocess.run([sys.executable, str(SCRIPT), "sitemap",
                            str(FIX / "base/seo-reports/site-structure-optimizer/2026-10-14-thistlewood-roofing.md")],
                           capture_output=True, text=True)
        check("sitemap reader", p.returncode == 0 and p.stdout.count('"Old URL"') == 2
              and p.stdout.count('"Priority"') == 8, p.stdout[:200])
        p = subprocess.run([sys.executable, str(SCRIPT), "sitemap", str(FIX / "base/handoff" / SLUG / f"{SLUG}-week-2-handoff.md")],
                           capture_output=True, text=True)
        check("sitemap reader refuses a file with no URL map", p.returncode == 1)
    finally:
        for d in temps:
            shutil.rmtree(d, ignore_errors=True)

    bad = [r for r in results if not r[1]]
    for name, ok, detail in results:
        if not ok:
            print(f"FAIL {name}: {detail}")
    print(f"selftest: {len(results) - len(bad)}/{len(results)} passed")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
