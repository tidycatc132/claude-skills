#!/usr/bin/env python3
"""Self-test for dqa.py. Run from the repo root: python3 skills/design-qa-dev-prep/scripts/selftest_dqa.py"""
from __future__ import annotations

import io
import os
import shutil
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import dqa  # noqa: E402

REPO = HERE.parents[2]
FIX = REPO / "fixtures" / "design-qa-dev-prep" / "larchmont"
SLUG = "larchmont-electric"
INV = Path("design") / SLUG / f"{SLUG}-design-inventory.md"
OUT = Path("design") / SLUG / f"{SLUG}-design-qa-devprep.md"
results: list[tuple[bool, str]] = []


def check(ok: bool, name: str) -> None:
    results.append((bool(ok), name))


def call(*argv: str) -> tuple[int, str]:
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = dqa.main(list(argv))
    return code, buf.getvalue()


def run(inv_text: str | None, *extra: str) -> tuple[int, str, str]:
    with tempfile.TemporaryDirectory() as d:
        root = Path(d) / "w"
        shutil.copytree(FIX / "base", root)
        if inv_text is not None:
            (root / INV).write_text(inv_text, encoding="utf-8")
        cwd = os.getcwd()
        os.chdir(root)
        try:
            code, out = call("run", "--slug", SLUG, "--client", "Larchmont Electric", "--date", "2026-10-29", *extra)
            report = (root / OUT).read_text(encoding="utf-8") if (root / OUT).is_file() else ""
        finally:
            os.chdir(cwd)
    return code, out, report


def inv(name: str) -> str:
    return (FIX / "inventories" / f"{name}.md").read_text(encoding="utf-8")


def row(report: str, template: str, name: str, result: str) -> bool:
    return f"| {template} | {name} | {result} |" in report


# designer inventory: PASS with one colour FLAG
code, out, rep = run(inv("designer-pass"))
check(code == 0 and rep.rstrip().endswith("RESULT: PASS"), "designer inventory passes")
check(row(rep, "All", "Colours sourced", "FLAG") and "#EEF2F6" in rep, "unsourced colour is a FLAG")
check("| FAIL |" not in rep, "no FAIL rows on the designer inventory")
check(row(rep, "All", "Asset details complete", "PASS"), "SVG logo needs no pixel size")
check(row(rep, "Service Pages", "Holds the longest page", "PASS") and "no limit" in rep, "no limit holds any page")
check(rep.index("## Asset Checklist") > rep.index("## Mobile-First Priorities"), "asset checklist is the last section")
check("(not in the brand sources; Design confirms)" in rep, "flagged colour marked in the palette")
sample = (REPO / "fixtures" / "contracts" / "design-qa-dev-prep-sample.md").read_text(encoding="utf-8")
check(rep == sample, "run reproduces the contract sample exactly")

# Figma inventory with every kind of failure
code, out, rep = run(inv("figma-fails"))
check(code == 1 and rep.rstrip().endswith("RESULT: FAIL"), "figma inventory fails")
for template, name, needle in [
    ("Service Pages", "Brief sections have containers", "FAQ"),
    ("Service Pages", "Containers have content", "Testimonials Strip"),
    ("Service Pages", "Holds the longest page", "ev-charger-installation"),
    ("Service Pages", "CTA placement", "Opening answer"),
    ("Contact Page", "Template exists", "Contact Page"),
    ("All", "Asset details complete", "Testimonial headshots"),
]:
    line = next((ln for ln in rep.split("\n") if ln.startswith(f"| {template} | {name} | FAIL |")), "")
    check(needle in line, f"FAIL {template} / {name} names {needle}")
check(rep.count(". Design.") == 6, "six fixes listed for Design")

# blank inventory fails until filled
with tempfile.TemporaryDirectory() as d:
    root = Path(d) / "w"
    shutil.copytree(FIX / "base", root)
    cwd = os.getcwd()
    os.chdir(root)
    try:
        code, _ = call("template", "--slug", SLUG, "--client", "Larchmont Electric", "--date", "2026-10-29")
        blank = (root / INV).read_text(encoding="utf-8")
        code2, _ = call("template", "--slug", SLUG, "--client", "Larchmont Electric")
    finally:
        os.chdir(cwd)
check(code == 0 and "## Template: Service Pages" in blank and "-> Phone and Email" in blank, "template lists templates and sections")
check(code2 == 1, "template will not overwrite without --force")
code, out, rep = run(blank)
check(code == 1 and row(rep, "All", "Inventory filled", "FAIL"), "blank inventory fails Inventory filled")

# order, extra CTA, unknown template
text = inv("designer-pass")
swapped = text.replace("- Takeaways List -> Key Takeaways\n- Question Block (repeats) -> Question sections",
                       "- Question Block (repeats) -> Question sections\n- Takeaways List -> Key Takeaways")
code, out, rep = run(swapped)
check(row(rep, "Service Pages", "Section order", "FLAG") and code == 0, "out-of-order containers are a FLAG")
extra = text.replace("CTAs after: Opening answer, Booking", "CTAs after: Opening answer, Key Takeaways, Booking")
code, out, rep = run(extra)
check(row(rep, "Service Pages", "CTA placement", "FLAG"), "CTA the brief does not place is a FLAG")
blog = text + "\n## Template: Resource Pages\n\nFrame: Blog\nHolds H2 sections: no limit\nSections:\n- Body -> none\nCTAs after:\n"
blog = blog.replace("\n## Template: Resource Pages", "\n## Template: Resource Pages", 1)
code, out, rep = run(blog)
check(row(rep, "Resource Pages", "Template exists", "FLAG"), "template with no brief is a FLAG")
nolimit = text.replace("Holds H2 sections: 4", "Holds H2 sections: 3")
code, out, rep = run(nolimit)
check(row(rep, "Contact Page", "Holds the longest page", "FAIL") and code == 1, "template smaller than the longest page fails")
nofont = text.replace("- Inter 400, 600: Google Fonts", "- Inter 400, 600:")
code, out, rep = run(nofont)
check(row(rep, "All", "Asset details complete", "FAIL") and "no font source" in rep, "font without a source fails")
newfont = text.replace("- Inter 400, 600: Google Fonts", "- Roboto 400: Google Fonts")
code, out, rep = run(newfont)
check(row(rep, "All", "Fonts sourced", "FLAG") and "Roboto" in rep, "font no source names is a FLAG")

# a blank template filled by replacing only the placeholders passes
lines = []
for ln in blank.split("\n"):
    if ln.startswith("Frame: <fill>"):
        ln = "Frame: Template / Desktop"
    elif ln.startswith("Holds H2 sections: <fill>"):
        ln = "Holds H2 sections: no limit"
    elif ln.startswith("- <fill> -> "):
        ln = "- Block " + ln.split("-> ", 1)[1] + " -> " + ln.split("-> ", 1)[1]
    elif ln.startswith("CTAs after: <fill>"):
        ln = None
    lines.append(ln)
filled, current = [], None
for ln in lines:
    if ln is not None and ln.startswith("## Template: "):
        current = ln.split(": ", 1)[1]
    if ln is None:
        ln = {"Service Pages": "CTAs after: Opening answer, Booking",
              "Contact Page": "CTAs after: Contact Form, Phone and Email"}[current]
    filled.append(ln)
filled = "\n".join(filled)
for a, b in [("- <fill>: <fill>\n\n## Fonts", "- #1B2A41: headings\n\n## Fonts"),
             ("- <fill>: <fill>\n\n## Images", "- Barlow 600: Google Fonts\n\n## Images"),
             ("- <fill>: <fill>\n\n## Icon Set", "- Hero photo: 1600 x 900, WebP\n\n## Icon Set"),
             ("- <fill>\n\n## Spacing", "- Lucide\n\n## Spacing"),
             ("- <fill>\n\n## Interactive", "- 8 px base unit\n\n## Interactive"),
             ("- <fill>: <fill>", "- FAQ List: opens and closes")]:
    filled = filled.replace(a, b, 1)
check("<fill>" not in filled, "template filled with no placeholder left")
code, out, rep = run(filled)
check(code == 0 and rep.rstrip().endswith("RESULT: PASS"), "a filled blank template can pass")

# colour and font matching are whole tokens
short = text.replace("- #1B2A41: headings, header and footer", "- #1B2: headings")
code, out, rep = run(short)
check(row(rep, "All", "Colours sourced", "FLAG") and "#1B2" in rep, "#1B2 is not #1B2A41")
check(dqa.hex6("#fff") == "#ffffff", "3-digit hex expands")
check(not dqa.has_word("Inter", "We are interested in international work"), "Inter does not match international")
named = text.replace("- #5B6770: body text", "- Slate: rgb(91, 103, 112)")
code, out, rep = run(named)
check(row(rep, "All", "Asset details complete", "FAIL") and "no hex value" in rep, "colour with no hex fails")
check(dqa.has_word("Pricing (from)", "The CTA sits after Pricing (from) on every page"), "section name ending in ) matches")

# no pages on disk: the brief's H2 sections line decides
with tempfile.TemporaryDirectory() as d:
    root = Path(d) / "w"
    shutil.copytree(FIX / "base", root)
    shutil.rmtree(root / "content" / "ev-charger-installation")
    shutil.rmtree(root / "content" / "panel-upgrades")
    (root / INV).write_text(text.replace("Holds H2 sections: no limit", "Holds H2 sections: 7"), encoding="utf-8")
    cwd = os.getcwd()
    os.chdir(root)
    try:
        code, out = call("run", "--slug", SLUG, "--client", "Larchmont Electric", "--date", "2026-10-29")
        rep = (root / OUT).read_text(encoding="utf-8")
    finally:
        os.chdir(cwd)
check(row(rep, "Service Pages", "Holds the longest page", "FAIL") and "Content Length (8 H2 sections)" in rep,
      "missing pages fall back to the brief's H2 sections")

# missing inputs
code, out, rep = run(None)
check(code == 1 and "MISSING" in out and not rep, "no inventory: nothing written")

# contract reader
brief = FIX / "base" / "design" / SLUG / f"{SLUG}-page-type-design-briefs.md"
b = dqa.read_briefs(brief)
types = {t["page_type"]: t for t in b["## Page Types"]}
check(list(types) == ["Service Pages", "Contact Page"], "briefs: page types in order")
check(types["Service Pages"]["CTAs"] == ["Opening answer", "Booking"], "briefs: CTA sections read from CTAs")
check(types["Service Pages"]["H2 sections"] == 8, "briefs: H2 sections upper bound")

fails = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS  " if ok else "FAIL  ") + n)
print(f"{len(results) - len(fails)}/{len(results)} passed")
sys.exit(1 if fails else 0)
