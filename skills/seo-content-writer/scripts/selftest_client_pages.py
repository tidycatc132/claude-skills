#!/usr/bin/env python3
"""Self-test for the About, Contact and location checks in check_draft.py and for batch_pages.py.
Standard library only.

Usage: python3 selftest_client_pages.py   (exit 0 when every case behaves as expected)

Each check_draft case writes a brief, a client file and a small page into a temporary folder, runs
check_draft.py in that page type's mode and reads one row of qa_report.md. The batch cases build a
small briefs folder and read the plan and summary output.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLIENT = """# Brand: Copperleaf Tree Care
- Owner: Rosa Delgado, ISA Certified Arborist (certification number PN-7731A)
- Founded: 2012
- Phone: (509) 555-0142
- Email: office@copperleaftree.com
- Office: 2218 N Argonne Rd, Spokane Valley, WA 99212
"""
BRIEF = "Client: Copperleaf Tree Care\nPage type: {ptype}\nTarget keyword: {kw}\n"

ABOUT = """<!-- section: Hero -->
# About Copperleaf Tree Care

Copperleaf Tree Care prunes and removes trees in Spokane. [Request an estimate](/free-estimate/)

<!-- section: Company Story -->
## How did Copperleaf Tree Care get started?

Copperleaf Tree Care has worked on Spokane trees since 2012.

<!-- section: Mission and Values -->
## What does Copperleaf Tree Care believe?

Copperleaf Tree Care believes in pruning before removal.

<!-- section: Team -->
## Who works at Copperleaf Tree Care?

Rosa Delgado owns Copperleaf Tree Care. [NEEDS INPUT: crew names and roles]

<!-- section: Credentials -->
## What credentials does Copperleaf Tree Care hold?

{claim}

<!-- section: Final CTA -->
## How do I book Copperleaf Tree Care?

[Request an estimate](/free-estimate/) from Copperleaf Tree Care.
"""

CONTACT = """<!-- section: Hero -->
# Contact Copperleaf Tree Care

Copperleaf Tree Care answers estimate requests by phone and email.

<!-- section: Contact Form -->
## How do I request an estimate from Copperleaf Tree Care?

The Copperleaf Tree Care estimate form asks for:

- Name
- Phone
- Email

<!-- section: Phone and Email -->
## What is Copperleaf Tree Care's phone number and email?

Call Copperleaf Tree Care at (509) 555-0142 or email {email}.

<!-- section: Address and Hours -->
## Where is Copperleaf Tree Care's office and when is it open?

Copperleaf Tree Care's office is at 2218 N Argonne Rd, Spokane Valley. {hours}

<!-- section: Map -->
## Where is Copperleaf Tree Care on the map?

Copperleaf Tree Care's office at 2218 N Argonne Rd is on the map below.

<!-- section: Final CTA -->
## What happens after I contact Copperleaf Tree Care?

Copperleaf Tree Care calls back to book a [free on-site estimate](/free-estimate/).
"""

LOCATION = """<!-- section: Hero -->
# Tree Service in Spokane Valley

Copperleaf Tree Care works in Spokane Valley. [Request an estimate](/free-estimate/)

<!-- section: {second} -->
## Does Copperleaf Tree Care work in Spokane Valley?

Copperleaf Tree Care has its office in Spokane Valley.

<!-- section: {third} -->
## What does Copperleaf Tree Care do in Spokane Valley?

Copperleaf Tree Care prunes and removes trees in Spokane Valley.

<!-- section: Local Proof -->
## What do Spokane Valley customers say about Copperleaf Tree Care?

Copperleaf Tree Care in Spokane Valley: [NEEDS INPUT: a Spokane Valley review]

<!-- section: Directions -->
## How do I find Copperleaf Tree Care in Spokane Valley?

Copperleaf Tree Care is at 2218 N Argonne Rd, Spokane Valley.

<!-- section: Final CTA -->
## How do I book Copperleaf Tree Care in Spokane Valley?

[Request an estimate](/free-estimate/) from Copperleaf Tree Care.
"""

# (name, page type, page text, check row, expected result)
CASES = [
    ("about: stated certification", "about", ABOUT.format(claim="Rosa Delgado holds ISA certification PN-7731A."),
     "Client facts trace to the brief or client files", "PASS"),
    ("about: invented 'licensed and insured'", "about",
     ABOUT.format(claim="Copperleaf Tree Care is licensed and insured."),
     "Client facts trace to the brief or client files", "FAIL"),
    ("about: sections in order", "about", ABOUT.format(claim="[NEEDS INPUT: insurance]"),
     "About page sections in order", "PASS"),
    ("about: empty Credentials", "about", ABOUT.format(claim="Copperleaf Tree Care cares about trees."),
     "Credentials section carries proof or a flag", "FAIL"),
    ("contact: stated email", "contact", CONTACT.format(email="office@copperleaftree.com", hours="[NEEDS INPUT: office hours]"),
     "Client facts trace to the brief or client files", "PASS"),
    ("contact: invented email", "contact", CONTACT.format(email="hello@copperleaftree.com", hours="[NEEDS INPUT: office hours]"),
     "Client facts trace to the brief or client files", "FAIL"),
    ("contact: hours neither given nor flagged", "contact", CONTACT.format(email="office@copperleaftree.com", hours=""),
     "Contact details given or flagged", "FAIL"),
    ("contact: invented hours", "contact", CONTACT.format(email="office@copperleaftree.com", hours="Copperleaf Tree Care is open Monday to Friday, 8 a.m. to 5 p.m."),
     "Client facts trace to the brief or client files", "FAIL"),
    ("contact: form fields listed", "contact", CONTACT.format(email="office@copperleaftree.com", hours="[NEEDS INPUT: office hours]"),
     "Contact form lists its fields", "PASS"),
    ("location: sections in order", "location", LOCATION.format(second="How We Serve", third="Local Services"),
     "Location page sections in order", "PASS"),
    ("location: sections out of order", "location", LOCATION.format(second="Local Services", third="How We Serve"),
     "Location page sections in order", "FAIL"),
]


def run_check(tmp: Path, ptype: str, page: str, row: str) -> str:
    d = tmp / ptype
    d.mkdir(exist_ok=True)
    (d / "client").mkdir(exist_ok=True)
    (d / "client" / "brand.md").write_text(CLIENT, encoding="utf-8")
    (d / "brief.md").write_text(BRIEF.format(ptype=ptype, kw="copperleaf tree care"), encoding="utf-8")
    (d / "article.md").write_text(page, encoding="utf-8")
    subprocess.run([sys.executable, str(HERE / "check_draft.py"), str(d / "article.md"), "--brief", str(d / "brief.md"),
                    "--client-dir", str(d / "client")], capture_output=True, text=True)
    report = (d / "qa_report.md").read_text(encoding="utf-8")
    line = next((l for l in report.splitlines() if l.startswith(f"| {row} |")), "")
    return line.split("|")[2].strip() if line else "MISSING"


def batch_cases(tmp: Path) -> list[tuple[str, bool]]:
    b, c = tmp / "batch" / "briefs", tmp / "batch" / "content"
    b.mkdir(parents=True)
    (b / "home.md").write_text("---\npage_url: /\nformat: homepage\n---\n", encoding="utf-8")
    (b / "about.md").write_text("---\npage_url: /about/\nformat: about-page\nclient_inputs_open: 1\n---\n", encoding="utf-8")
    (b / "about.v1.md").write_text("---\npage_url: /about/\nformat: about-page\n---\n", encoding="utf-8")
    (b / "pruning.md").write_text("Target keyword: tree pruning spokane\nPage type: service-page\n", encoding="utf-8")
    (c / "home").mkdir(parents=True)
    (c / "home" / "article.md").write_text("# Home\n", encoding="utf-8")
    q = tmp / "batch" / "qa"  # check_draft.py writes reports for content/<slug>/ to qa/<slug>/
    q.mkdir(parents=True)
    # a page written before reports moved to qa/ keeps its report in the page folder
    (c / "home" / "qa_report.md").write_text("VERDICT: NEEDS_INPUT\n\nOpen flags: 2.\n", encoding="utf-8")
    script = str(HERE / "batch_pages.py")
    plan = subprocess.run([sys.executable, script, "plan", str(b), "--content", str(c)], capture_output=True, text=True).stdout
    out = [
        ("plan: existing homepage is skipped", "/home/ | homepage | 0 | skip (exists) |" in plan),
        ("plan: missing About page is written", "/about/ | about | 1 | write |" in plan),
        ("plan: older brief version is not a page", "about.v1.md" not in plan),
        ("plan: slug from the keyword when there is no URL", "/tree-pruning-spokane/ | service-page | 0 | write |" in plan),
    ]
    (c / "about").mkdir()
    (c / "about" / "article.md").write_text("# About\n", encoding="utf-8")
    (q / "about").mkdir()
    (q / "about" / "qa_report.md").write_text("VERDICT: READY\n\nOpen flags: 0.\n", encoding="utf-8")
    r = subprocess.run([sys.executable, script, "summary", str(b), "--content", str(c)], capture_output=True, text=True)
    summary = (c / "batch-summary.md").read_text(encoding="utf-8")
    out += [
        ("summary: header row", "| Page | Brief | VERDICT | Open flags |" in summary),
        ("summary: old-layout report in the page folder still read", "| NEEDS_INPUT | 2 |" in summary),
        ("summary: unwritten page is NOT WRITTEN", "| pruning.md | NOT WRITTEN |" in summary),
        ("summary: READY page with open client inputs needs CONFIRM", "CONFIRM:" in summary and "/about/" in summary),
        ("summary: exits 1 while pages are missing", r.returncode == 1),
    ]
    plan2 = subprocess.run([sys.executable, script, "plan", str(b), "--content", str(c)], capture_output=True, text=True).stdout
    out.append(("re-run: About page now skipped", "/about/ | about | 1 | skip (exists) |" in plan2))
    return out


def main() -> int:
    bad = 0
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        for name, ptype, page, row, want in CASES:
            got = run_check(tmp, ptype, page, row)
            ok = got == want
            bad += not ok
            print(f"{'ok  ' if ok else 'BAD '} {name}: expected {want}, got {got}")
        batch = batch_cases(tmp)
        for name, ok in batch:
            bad += not ok
            print(f"{'ok  ' if ok else 'BAD '} {name}")
    total = len(CASES) + len(batch)
    print(f"{total - bad}/{total} as expected")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
