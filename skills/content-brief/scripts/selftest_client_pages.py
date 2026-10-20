#!/usr/bin/env python3
"""Self-test for check_brief.py's client-page checks (About, Contact, Location, homepage).

Usage:
  python3 selftest_client_pages.py [--about BRIEF] [--contact BRIEF] [--home BRIEF]
                                   [--client-dir DIR] [--home-client-dir DIR]

Each passing sample brief is changed in one way that the gate must catch (a
missing section line, an untraced email or hours, no form fields, sections out
of order) and must still pass after changes the rules allow (two H2s in one
section). It also checks that parse_targets.py maps the report's "about us" and
"contact page" rows to about-page and contact-page. Defaults are the repo's
contract samples and the saltmarsh fixture; run it after changing either script. Prints one line per case and exits 1 on any
miss. Standard library only.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
GATE = HERE / "check_brief.py"
REPO = HERE.parents[2]  # defaults resolve against the repo, from any working directory


def run(text: str, client_dir: str) -> tuple[bool, str]:
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "brief.md"
        p.write_text(text, encoding="utf-8")
        r = subprocess.run([sys.executable, str(GATE), str(p), "--client-dir", client_dir],
                           capture_output=True, text=True)
        return r.returncode == 0, r.stdout


def sub(text: str, old: str, new: str) -> str:
    if old not in text:
        raise SystemExit(f"selftest setup: {old!r} not found in the sample brief")
    return text.replace(old, new, 1)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--about", default=str(REPO / "fixtures/contracts/content-brief-about-sample.md"))
    ap.add_argument("--contact", default=str(REPO / "fixtures/contracts/content-brief-contact-sample.md"))
    ap.add_argument("--home", default=str(REPO / "fixtures/contracts/content-brief-homepage-sample.md"))
    ap.add_argument("--client-dir", default=str(REPO / "fixtures/content-brief/saltmarsh/client-reference/saltmarsh-window-co"))
    ap.add_argument("--home-client-dir",
                    default=str(REPO / "fixtures/content-brief/fernhollow/client-reference/fernhollow-landscaping"))
    ap.add_argument("--report", default=str(REPO / "fixtures/content-brief/saltmarsh/research/keyword-research/"
                                                       "2026-10-19-core-pages.md"))
    a = ap.parse_args()
    about = Path(a.about).read_text(encoding="utf-8")
    contact = Path(a.contact).read_text(encoding="utf-8")
    home = Path(a.home).read_text(encoding="utf-8")
    cd = a.client_dir

    location = about.replace("format: about-page", "format: location-page").replace("word_range: 400-800",
                                                                                  "word_range: 700-1200")
    for old, new in (("Company Story", "How We Serve"), ("Mission and Values", "How We Serve"),
                     ("Team", "Local Services"), ("Credentials", "Local Proof")):
        location = re.sub(rf"(?m)^- Section: {old}$", f"- Section: {new}", location)
    location = sub(location, "- Section: Final CTA", "- Section: Directions\n- First sentence must state: the Saltmarsh office is at "
                   "1820 Maybank Hwy, Johns Island (E5).\n- Evidence: none needed\n"
                   "### H2 (CTA): How do I book window cleaning on Johns Island?\n- Section: Final CTA")
    location = sub(location, "### H2 (CTA): How do I get a quote from Saltmarsh Window Co.?\n- Section: Directions",
                   "### H2: How do I find the Saltmarsh office on Johns Island?\n- Section: Directions")

    # (name, brief text, client dir, should pass, check name that must fail)
    cases = [
        ("about sample passes", about, cd, True, None),
        ("contact sample passes", contact, cd, True, None),
        ("homepage sample still passes", home, a.home_client_dir, True, None),
        ("location with two H2s per section passes", location, cd, True, None),
        ("about: a block without its Section line", sub(about, "- Section: Team\n", ""), cd, False,
         "About page sections in order"),
        ("about: Credentials before Team",
         sub(sub(about, "- Section: Team", "- Section: TEMP"), "- Section: Credentials", "- Section: Team")
         .replace("- Section: TEMP", "- Section: Credentials"), cd, False, "About page sections in order"),
        ("about: an award no file states", sub(about, "is fully insured", "is an award-winning, fully insured firm"),
         cd, False, "About page client facts trace to client files"),
        ("about: Credentials with no evidence or slot",
         sub(sub(about, "- Cover: [CLIENT INPUT NEEDED #1: customer reviews or testimonials the client has "
                        "permission to quote]\n- Evidence: E4", "- Evidence: none verifiable"),
             "(E4).", "."), cd, False, "Credentials section has evidence or a slot"),
        ("about: 'none needed' on Company Story", sub(about, "- Evidence: E1\n### H2: What does",
                                                      "- Evidence: none needed\n### H2: What does"), cd, False,
         "Every section lists evidence ids or 'none verifiable'"),
        ("contact: no Fields line", re.sub(r"(?m)^- Fields:.*\n", "", contact), cd, False,
         "Contact form lists its fields"),
        ("contact: only two fields", re.sub(r"(?m)^- Fields:.*$", "- Fields: name, phone", contact), cd, False,
         "Contact form lists its fields"),
        ("contact: hours the file says not to publish",
         contact.replace("[CLIENT INPUT NEEDED #1: office hours for 2027, once Dana confirms them]",
                         "Monday to Friday, 8 a.m. to 4 p.m.").replace("client_inputs_open: 1", "client_inputs_open: 0")
         .replace("1. Office hours for 2027, once Dana confirms them (why: Address and Hours)", "None."), cd, False,
         "Contact page client facts trace to client files"),
        ("contact: an email no file states", contact.replace("hello@saltmarshwindow.com", "info@saltmarshwindow.com"),
         cd, False, "Contact page client facts trace to client files"),
        ("contact: no email and no slot", sub(contact, "or email hello@saltmarshwindow.com (E1)", "(E1)"), cd, False,
         "Contact details given or slotted"),
        ("contact: Map before Address and Hours",
         sub(sub(contact, "- Section: Map", "- Section: TEMP"), "- Section: Address and Hours", "- Section: Map")
         .replace("- Section: TEMP", "- Section: Address and Hours"), cd, False, "Contact page sections in order"),
        ("contact: Final CTA with no route",
         sub(contact, "; send the request at /free-quote/ or call (843) 555-0163.", "."), cd, False,
         "Contact page Final CTA gives a route"),
        ("location: a review count no file states in Local Proof",
         sub(location, "is fully insured with", "has 212 five-star Google reviews and is fully insured with"), cd, False,
         "Location page client facts trace to client files"),
        ("contact: Final CTA path not in Links from this page",
         sub(contact, "send the request at /free-quote/ or call (843) 555-0163.", "send the request at /book-now/."),
         cd, False, "Contact page Final CTA gives a route"),
        ("homepage: Proof with no evidence or slot",
         re.sub(r"(?s)(- Section: Proof\n).*?(?=### H2: Who runs)", r"\1- First sentence must state: Fernhollow "
                r"plants for the high desert, low water and frost hardy.\n- Evidence: none verifiable\n", home),
         a.home_client_dir, False, "Proof section has evidence or a slot"),
        ("homepage: 'none needed' on Why Us", sub(home, "- Evidence: E2, E3", "- Evidence: none needed"),
         a.home_client_dir, False, "Every section lists evidence ids or 'none verifiable'"),
        ("homepage: Final CTA without hours", sub(home, ", office hours Monday to Friday, 8 a.m. to 5 p.m.", ""),
         a.home_client_dir, False, "Final CTA covers phone, address and hours"),
        ("location: Local Proof before Local Services",
         location.replace("- Section: Local Services", "- Section: TEMP").replace("- Section: Local Proof",
                                                                                 "- Section: Local Services")
         .replace("- Section: TEMP", "- Section: Local Proof"), cd, False, "Location page sections in order"),
    ]
    misses = 0
    r = subprocess.run([sys.executable, str(HERE / "parse_targets.py"), a.report, "--normalize"],
                       capture_output=True, text=True)
    got = re.findall(r'"format_primary": "([^"]+)"', r.stdout)
    good = got == ["about-page", "contact-page"]
    misses += not good
    print(f"{'ok  ' if good else 'MISS'} report rows normalize to about-page and contact-page"
          + ("" if good else f" (got {got})"))
    for name, text, cdir, want_pass, check in cases:
        ok, out = run(text, cdir)
        failed = {m.group(1) for m in re.finditer(r"(?m)^\| (.+?) \| FAIL \|", out)}
        good = ok if want_pass else (not ok and check in failed)
        misses += not good
        detail = "" if good else f" (gate {'passed' if ok else 'failed: ' + ', '.join(sorted(failed))})"
        print(f"{'ok  ' if good else 'MISS'} {name}{detail}")
    print(f"\n{len(cases) + 1 - misses}/{len(cases) + 1} passed")
    return 1 if misses else 0


if __name__ == "__main__":
    sys.exit(main())
