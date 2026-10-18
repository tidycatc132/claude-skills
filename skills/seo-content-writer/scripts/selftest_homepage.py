#!/usr/bin/env python3
"""Self-test for check_draft.py's homepage client-fact check. Standard library only.

Usage: python3 selftest_homepage.py   (exit 0 when every case behaves as expected)

Each case writes a brief, a client file and a one-line Proof claim into a temporary folder,
runs check_draft.py in homepage mode, and reads the "Client facts trace" row of qa_report.md.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAGE = """<!-- section: Hero -->
# Roofing Company in Boise

Juniper Ridge Roofing repairs and replaces roofs in Boise. [Book an inspection](/free-inspection/)

<!-- section: Why Us -->
## Why choose Juniper Ridge Roofing?

Juniper Ridge Roofing is owner-run.

<!-- section: Services Overview -->
## What does Juniper Ridge Roofing do?

Juniper Ridge Roofing does roof repair and replacement.

<!-- section: Proof -->
## Why trust Juniper Ridge Roofing?

{claim}

<!-- section: About Snapshot -->
## Who runs Juniper Ridge Roofing?

Dana Whitfield runs Juniper Ridge Roofing.

<!-- section: Service Area -->
## Where does Juniper Ridge Roofing work?

Juniper Ridge Roofing works in Boise.

<!-- section: Process -->
## How does Juniper Ridge Roofing work?

Juniper Ridge Roofing inspects, quotes and installs.

<!-- section: Final CTA -->
## How do I book Juniper Ridge Roofing?

[Book an inspection](/free-inspection/) with Juniper Ridge Roofing.
"""
BRIEF = "Client: Juniper Ridge Roofing\nPage type: homepage\nTarget keyword: roofing company boise\n\n{extra}\n"

CASES = [
    # (name, brief extra, client file text, proof claim, expected PASS?)
    ("credential stated in a client file", "", "# Brand\n\n- Idaho contractor license RCE-1234, licensed since 2015\n",
     "Juniper Ridge Roofing is licensed (license RCE-1234).", True),
    ("credential nowhere", "", "# Brand\n\n- Owner: Dana Whitfield\n", "Juniper Ridge Roofing is licensed.", False),
    ("credential only in a brief's Client Inputs Needed", "## Client Inputs Needed\n\n1. Contractor license number once issued.\n",
     "# Brand\n", "Juniper Ridge Roofing is licensed.", False),
    ("credential only in a brief's Concerns", "## Concerns\n\n- No license or certification is on file.\n",
     "# Brand\n", "Juniper Ridge Roofing is licensed and certified.", False),
    ("credential only in a Writer QA Checklist", "## Writer QA Checklist\n\n- [ ] No licensed or insured claim without a file.\n",
     "# Brand\n", "Juniper Ridge Roofing is insured.", False),
    ("credential only in a slot", "Proof: [CLIENT INPUT NEEDED #2: license number]\n", "# Brand\n",
     "Juniper Ridge Roofing is licensed.", False),
    ("credential only in compliance Prohibited Claims", "",
     "# Compliance\n\n## Prohibited Claims\n\n- Never say award-winning or licensed until verified.\n",
     "Juniper Ridge Roofing is award-winning.", False),
    ("rating stated in a client file", "", "# Brand\n\n- About 47 Google reviews, rated 4.9\n",
     "Juniper Ridge Roofing is rated 4.9 by about 47 Google reviews.", True),
    ("rating invented", "", "# Brand\n\n- Founded 2015 with 5 trucks\n", "Juniper Ridge Roofing is a 5-star roofer.", False),
]


def run(extra: str, client: str, claim: str) -> bool:
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "client").mkdir()
        (root / "client" / "brand.md").write_text(client, encoding="utf-8")
        (root / "brief.md").write_text(BRIEF.format(extra=extra), encoding="utf-8")
        (root / "article.md").write_text(PAGE.format(claim=claim), encoding="utf-8")
        subprocess.run([sys.executable, str(HERE / "check_draft.py"), str(root / "article.md"), "--brief",
                        str(root / "brief.md"), "--client-dir", str(root / "client")], capture_output=True, text=True)
        report = (root / "qa_report.md").read_text(encoding="utf-8")
    row = next(l for l in report.splitlines() if l.startswith("| Client facts trace"))
    return "| PASS |" in row


def main() -> int:
    bad = 0
    for name, extra, client, claim, want in CASES:
        got = run(extra, client, claim)
        ok = got == want
        bad += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {name}: expected {'PASS' if want else 'FAIL'}, got {'PASS' if got else 'FAIL'}")
    print(f"{len(CASES) - bad}/{len(CASES)} as expected")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
