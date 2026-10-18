#!/usr/bin/env python3
"""Small cases for check_design_brief.py: a good brief passes, and each kind of fault fails its check.

Usage: selftest_brief.py   (exit 1 on any unexpected result)
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARTICLE = """<!-- section: Hero -->
# Bakery in Ashford for Sourdough and Cakes

Wren Bakery bakes sourdough and celebration cakes in Ashford.

[Order a cake](/order/) or call [NEEDS INPUT: phone number]

<!-- section: Proof -->
## What do customers say?

[NEEDS INPUT: two customer reviews, word for word]

<!-- section: Final CTA -->
## How do I order?

Use the [order form](/order/).
"""
SOURCE = """# Wren Bakery: client context
## Goals and Conversion
- Look and feel: bright, hand-made, flour-white with one red accent [transcript]
- Owner likes Larkspur Bakery: "the pages feel like a warm kitchen" [call]
"""
GOOD = """Client: Wren Bakery · Page: content/home/article.md · Built: 2026-10-17
Content review: confirmed (Ana, 2026-10-16)

# Homepage Design Brief: Wren Bakery

## Goals
- Get cake orders through the form [context]

## Audience
- Locals ordering celebration cakes [context]

## Brand Cues
- Flour-white with one red accent [context]
- GAP: no logo files; ask the owner

## Design References

| Reference | What the client likes | Source |
| --- | --- | --- |
| Larkspur Bakery | "the pages feel like a warm kitchen" | [context] |

## Section Map

| # | Section | Purpose | Layout idea | Content source |
| --- | --- | --- | --- | --- |
| 1 | Hero | Say what and where | Photo right, H1 left | article.md > Hero; waits on phone |
| 2 | Proof | Show reviews | Two quote cards | article.md > Proof |
| 3 | Final CTA | Get the order | Full-width band with the button | article.md > Final CTA |

## Imagery
- Recommended: one bread photo in the Hero

## Must-Haves
- Order button in Hero and Final CTA [article]

## Do-Nots
- GAP: the owner named nothing to avoid

## Open Questions
1. [NEEDS INPUT: phone number] (Hero). Client.
2. [NEEDS INPUT: two customer reviews, word for word] (Proof). Client.
3. Can the owner send logo files? Owner.
4. Is there any look the owner wants to avoid? Owner.

## Sources
- content/home/article.md
"""

CASES = [
    ("good brief passes", GOOD, None),
    ("reference the client never named", GOOD.replace("| Larkspur Bakery |", "| Crumb & Co |"),
     "FAIL Design references appear"),
    ("invented quoted copy", GOOD.replace("Two quote cards", 'Two quote cards under "Fresh bread every single morning"'),
     "FAIL Quoted wording"),
    ("open flag left out", GOOD.replace("2. [NEEDS INPUT: two customer reviews, word for word] (Proof). Client.\n", ""),
     "FAIL Every open flag"),
    ("section missing from the map", GOOD.replace("| 2 | Proof | Show reviews | Two quote cards | article.md > Proof |\n", "")
     .replace("| 3 | Final CTA", "| 2 | Final CTA"), "FAIL Section Map rows match"),
    ("untagged bullet", GOOD.replace("- Get cake orders through the form [context]", "- Get cake orders through the form"),
     "FAIL Every bullet tagged"),
    ("unconfirmed review not asked first",
     GOOD.replace("Content review: confirmed (Ana, 2026-10-16)", "Content review: not confirmed"),
     "FAIL Unconfirmed review is open question 1"),
    ("heading renamed", GOOD.replace("## Do-Nots", "## Avoid"), "FAIL Sections in order"),
]


def main() -> int:
    bad = 0
    with tempfile.TemporaryDirectory() as d:
        art, src, brief = Path(d, "article.md"), Path(d, "context.md"), Path(d, "brief.md")
        art.write_text(ARTICLE)
        src.write_text(SOURCE)
        for name, text, expect in CASES:
            brief.write_text(text)
            p = subprocess.run([sys.executable, str(HERE / "check_design_brief.py"), str(brief),
                                "--article", str(art), "--sources", str(src)], capture_output=True, text=True)
            ok = (p.returncode == 0) if expect is None else (p.returncode == 1 and expect in p.stdout)
            print(("ok   " if ok else "FAIL ") + name)
            if not ok:
                bad += 1
                print(p.stdout)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
