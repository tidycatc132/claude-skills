#!/usr/bin/env python3
"""Small cases for ptdb.py: a filled brief passes, and each broken rule fails. Run after changing ptdb.py.

Usage: python3 selftest_ptdb.py     (standard library only; builds an invented client in a temp folder)
"""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PTDB = HERE / "ptdb.py"
SLUG = "wrenfield-glass"

FILES = {
    "content/home/article.md": "<!-- section: Hero -->\n# Glass Repair in Wrenfield\n\nText.\n\n<!-- section: Why Us -->\n## Why?\n\nText.\n",
    "content/window-repair/article.md": "| Field | Value |\n| --- | --- |\n| URL slug | /services/window-repair/ |\n\n# Window Repair\n\nIntro text here.\n\n## What breaks?\n\nText. [NEEDS INPUT: repair warranty]\n\n## How do I book?\n\n[Book](/book/)\n",
    "content/about/article.md": (
        "<!-- section: Hero -->\n# About Wrenfield Glass\n\nText.\n\n<!-- section: Company Story -->\n## Story?\n\nText.\n\n"
        "<!-- section: Team -->\n## Team?\n\n[NEEDS INPUT: team names]\n\n<!-- section: Final CTA -->\n## Book?\n\n[Book](/book/)\n"
    ),
    "client-reference/wrenfieldglass/brand.md": "# Brand\n\n- Primary colour: Slate #34495E\n- \"Clear and honest, like the glass we fit.\"\n",
    f"design/{SLUG}/{SLUG}-homepage-design-brief.md": "# Homepage Design Brief: Wrenfield Glass\n\n## Brand Cues\n\n- Slate #34495E [kit: brand.md]\n",
    f"feedback/{SLUG}/2026-10-18-feedback.md": (
        "## Feedback Items\n\n| # | Feedback | Type | Affects | Impact | Action | Owner |\n| --- | --- | --- | --- | --- | --- | --- |\n"
        "| 1 | Go with Option A. | approval | homepage design: Option A | none | Take Option A forward | Design |\n"
    ),
}

FILLS = {
    "service": {
        "map": "| 1 | Opening answer | Answer the page question | all | article.md > H1 and opening |\n"
               "| 2 | Question sections | One question per section | all | article.md > H2s |\n"
               "| 3 | Booking | Book the job | all | article.md > last H2 |",
    },
}


def fill(text: str, option: str | None) -> str:
    rel = f"Same booking route and primary call to action as homepage {option} [homepage brief]" if option else \
        "Homepage direction not chosen yet; this section waits on the choice"
    text = re.sub(r"\| 1 \| <fill> \| <fill> \| <fill> \| <fill> \|", FILLS["service"]["map"], text)
    text = text.replace("| <fill> |", "| Says what the section is for |")
    text = text.replace("- Consistent: <fill>", "- Consistent: section order and the booking route")
    text = text.replace("- Varies: <fill>", "- Varies: the number of question sections")
    out, sub = [], ""
    for ln in text.splitlines():
        if ln.startswith("### "):
            sub = ln[4:]
        if ln == "- <fill>":
            ln = {
                "Repeating Blocks": "- The booking section closes every page",
                "Content Length": "- The template holds from two to six question sections",
                "CTAs": "- Booking link at the top and in the last section",
                "Brand Reference": "- Slate #34495E as the primary colour [kit: brand.md]",
                "Responsive Priorities": "- Mobile first: the booking link sits in the first screen",
                "Homepage Relationship": f"- {rel}",
            }[sub]
        out.append(ln)
    return "\n".join(out) + "\n"


def run(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(PTDB), *args, "--slug", SLUG, "--root", str(root)],
                          capture_output=True, text=True)


def main() -> int:
    fails = 0
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for rel, body in FILES.items():
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(body, encoding="utf-8")
        r = run(root, "scaffold", "--client", "Wrenfield Glass", "--date", "2026-10-20")
        assert r.returncode == 0, r.stderr
        brief = root / "design" / SLUG / f"{SLUG}-page-type-design-briefs.md"
        good = fill(brief.read_text(encoding="utf-8"), "Option A")

        def case(name: str, text: str, expect_pass: bool, setup=None) -> None:
            nonlocal fails
            if setup:
                setup()
            brief.write_text(text, encoding="utf-8")
            res = run(root, "check", str(brief))
            ok = (res.returncode == 0) == expect_pass
            print(("ok    " if ok else "WRONG ") + name)
            if not ok:
                fails += 1
                print(res.stdout)

        case("filled brief passes", good, True)
        case("<fill> left fails", good.replace("Booking link at the top", "<fill>"), False)
        case("visual instruction fails", good.replace("Booking link at the top", "Sticky booking button at the top"), False)
        case("px size fails", good.replace("first screen", "first 600px"), False)
        case("invented hex fails", good.replace("Slate #34495E as", "Slate #34495E and #FF0000 as", 1), False)
        case("untagged brand cue fails", good.replace("as the primary colour [kit: brand.md]", "as the primary colour", 1), False)
        case("missing flag fails", good.replace("[NEEDS INPUT: team names]", "team names"), False)
        case("missing page fails", good.replace("- `content/about/article.md`\n", ""), False)
        case("wrong length line fails", good.replace("Words: ", "Words: 1 to "), False)
        case("about map out of order fails", re.sub(r"\| 2 \| Company Story \|(.*)\n\| 3 \| Team \|(.*)",
                                                    r"| 2 | Team |\2\n| 3 | Company Story |\1", good), False)
        case("misquote fails", good.replace("Same booking route", "\"Clear and honest like our glass\" and same booking route", 1), False)
        case("extra section fails", good.replace("## Open Questions", "## Resource Pages\n\n## Open Questions"), False)

        (root / f"feedback/{SLUG}/2026-10-18-feedback.md").unlink()
        r = run(root, "scaffold", "--client", "Wrenfield Glass", "--date", "2026-10-20", "--force")
        nochoice = fill(brief.read_text(encoding="utf-8"), None)
        case("no option chosen passes", nochoice, True)
        case("guessed option fails", nochoice.replace("waits on the choice", "waits on the choice; Option A looks likely"), False)
        # option_from_rows edge cases
        sys.path.insert(0, str(HERE))
        import ptdb
        H = {"Type": "approval", "Affects": "homepage design", "Impact": "none"}
        for name, rows, want in [
            ("option named only in the quote", [dict(H, Feedback="Go ahead with Option A.")], "Option A"),
            ("two options means not chosen", [dict(H, Affects="homepage design: Option A", Feedback="A"),
                                              dict(H, Affects="homepage design: Option B", Feedback="B")], None),
            ("question reopens the choice", [dict(H, Type="question", Feedback="Can we look at both again?")], None),
            ("change request is not a pick", [dict(H, Type="design", Impact="low", Affects="homepage design: Option B", Feedback="x")], None),
        ]:
            got = ptdb.option_from_rows(rows)[0]
            ok = got == want
            fails += not ok
            print(("ok    " if ok else "WRONG ") + name + ("" if ok else f" (got {got})"))
        # a page with no markers, no brief and no telling URL is UNKNOWN until --type is passed
        (root / "content/mystery").mkdir()
        (root / "content/mystery/article.md").write_text("# Something\n\n## What?\n\nText.\n", encoding="utf-8")
        r1 = run(root, "scan")
        r2 = subprocess.run([sys.executable, str(PTDB), "scan", "--slug", SLUG, "--root", str(root), "--type", "mystery=resource"],
                            capture_output=True, text=True)
        ok = r1.returncode == 1 and "UNKNOWN TYPE" in r1.stderr and r2.returncode == 0
        fails += not ok
        print(("ok    " if ok else "WRONG ") + "unknown type stops until --type")
    print(f"{fails} wrong")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
