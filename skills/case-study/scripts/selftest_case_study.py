#!/usr/bin/env python3
"""Selftest for case_study.py on temporary copies of the Kestrel Garage Doors fixture.

Run from the repository root: python3 skills/case-study/scripts/selftest_case_study.py
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "case_study.py"
REPO = HERE.parents[2]
FIX = REPO / "fixtures/case-study/kestrel"
SLUG = "kestrel-garage-doors"
CS = f"case-study/{SLUG}/{SLUG}-case-study.md"
BRIEF = f"case-study/{SLUG}/{SLUG}-case-study-design-brief.md"

FILL = {
    "# [WRITE: headline": "# Kestrel Garage Doors: a phone-first site that sends repair calls to the right page",
    "[WRITE: two sentences on who": "Kestrel Garage Doors is a family-run garage door company in Boise, founded in 2012. "
        "A crew of seven technicians repairs and installs doors for homeowners in Boise, Meridian and Nampa.",
    "[WRITE: what the old site lacked": "The old site had 6 pages, no page per service and no page for Meridian or Nampa. "
        "The phone number sat only in the footer, and most repair calls come from a phone in the driveway.",
    "[WRITE: the positioning": "We built the site around the two things Kestrel does that its competitors do not: "
        "same-day spring replacement and a price quoted on the phone. Repair and spring pages came first, then a page each for Meridian and Nampa.",
    "[WRITE: one short paragraph on the new": "The Spring Replacement page answers the call that brings most new customers, "
        "and the Meridian and Nampa pages tell people in those towns that Kestrel drives out every day.",
    "[WRITE: what we will measure": "At 90 days we will measure phone calls from the site, service request forms and search clicks "
        "for the repair, spring, Meridian and Nampa pages.",
    "[WRITE: one open question": "What changed for the office in the first weeks after the new site went live?",
    "[WRITE: keep 3 or 4": None,
    "[WRITE: a layout for": "Hero: the new homepage on a phone beside the old homepage on a laptop. Then two before and after pairs, "
        "the four callout stats in a row in Signal Orange on Kestrel Blue, and the quote slot at the end.",
}


def run(*args, cwd):
    p = subprocess.run([sys.executable, str(SCRIPT), *args], cwd=cwd, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def fill(path: Path, extra: dict | None = None) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    out = []
    for ln in lines:
        hit = None
        for k, v in FILL.items():
            if k in ln:
                hit = (k, v)
                break
        if hit is None:
            out.append(ln)
            continue
        k, v = hit
        if v is None:
            continue
        if k.startswith("[WRITE: what we will") or k.startswith("[WRITE: one open"):
            start = ln.index("[WRITE:")
            end = ln.index("]", start) + 1
            out.append(ln[:start] + v + ln[end:])
        else:
            out.append(v)
    text = "\n".join(out) + "\n"
    for a, b in (extra or {}).items():
        text = text.replace(a, b)
    path.write_text(text, encoding="utf-8")


def setup(tmp: Path, variant: str | None = None, drop: list[str] | None = None) -> Path:
    d = tmp / f"{variant or 'base'}-{len(list(tmp.iterdir()))}"
    shutil.copytree(FIX / "base", d)
    if variant:
        shutil.copytree(FIX / "variants" / variant, d, dirs_exist_ok=True)
    for rel in drop or []:
        p = d / rel
        shutil.rmtree(p) if p.is_dir() else p.unlink()
    return d


def main() -> int:
    results = []

    def case(name, ok, detail=""):
        results.append((name, ok))
        print(("PASS " if ok else "FAIL ") + name + ("" if ok else f"\n     {detail[:1500]}"))

    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        d = setup(tmp)
        rc, out = run("scaffold", "--slug", SLUG, "--launch", "2026-11-18", "--date", "2026-11-20", cwd=d)
        case("scaffold writes both files", rc == 0 and (d / CS).exists() and (d / BRIEF).exists(), out)
        cnt = json.loads(next(ln for ln in out.splitlines() if ln.startswith("{")))
        case("counts: 9 Build pages with content, post-launch page left out", cnt["pages_built"] == 9 and cnt["post_launch_pages"] == 1, out)
        case("counts: pages by type", cnt["pages_by_type"] == {"Homepage": 1, "Service Pages": 4, "Location Pages": 2,
                                                              "About Page": 1, "Contact Page": 1}, out)
        case("counts: 4 redirects with a target, NO TARGET not counted", cnt["old_urls_redirected"] == 4, out)
        case("counts: 7 primary keywords, 6 old pages", cnt["keywords_targeted"] == 7 and cnt["old_site_pages"] == 6, out)
        case("counts: words over the 9 articles", cnt["words_written"] == 805, out)
        rc, out = run("scaffold", "--slug", SLUG, "--launch", "2026-11-18", cwd=d)
        case("scaffold refuses to overwrite", rc == 1 and "REFUSED" in out, out)
        rc, out = run("check", "--slug", SLUG, "--launch", "2026-11-18", cwd=d)
        case("unfilled scaffold fails on placeholders", rc == 1 and "| placeholders | FAIL" in out, out)
        brief_text = (d / BRIEF).read_text()
        case("brief: retired colour listed as not to use", "#B22222 (Barn Red)" in brief_text, brief_text)
        case("brief: homepage pair plus 4 redirect pairs", brief_text.count("https://kestrelgaragedoors.com/") >= 5
             and "| Contact Us | https://kestrelgaragedoors.com/contact-us/ | Contact |" in brief_text, brief_text)
        fill(d / CS)
        fill(d / BRIEF)
        rc, out = run("check", "--slug", SLUG, "--launch", "2026-11-18", cwd=d)
        case("filled launch version passes", rc == 0 and "RESULT: PASS" in out, out)
        good = (d / CS).read_text()
        good_brief = (d / BRIEF).read_text()

        def mutate(name, a, b, expect, target=CS):
            p = d / target
            src = good if target == CS else good_brief
            if a not in src:
                case(name, False, f"mutation anchor not found: {a}")
                return
            p.write_text(src.replace(a, b, 1), encoding="utf-8")
            rc, out = run("check", "--slug", SLUG, "--launch", "2026-11-18", cwd=d)
            case(name, rc == 1 and expect in out, out)
            p.write_text(src, encoding="utf-8")

        mutate("invented number fails", "service request forms", "service request forms (up 40 a month)", "| numbers | FAIL")
        mutate("wrong word count fails", "805 words of new page copy across", "900 words of new page copy across", "| what we built | FAIL")
        mutate("quick stat not a count fails", "- 2 new location pages", "- 3 new location pages", "| quick stats | FAIL")
        mutate("results claim at launch fails", "At 90 days we will", "Calls are up 20% already. At 90 days we will", "| results | FAIL")
        mutate("unapproved quote fails", "## In Their Words", "## In Their Words\n\n> \"We tell people the price on the phone before we roll a truck.\"", "| quote | FAIL")
        mutate("wrong type count fails", "and the Meridian and Nampa pages tell",
               "and the 3 location pages tell", "| counts by noun | FAIL")
        mutate("quick stat with the wrong noun fails", "- 2 new location pages", "- 4 new location pages", "| counts by noun | FAIL")
        mutate("ranking promise fails", "We built the site", "The site ranks first in Boise. We built the site", "| no hype | FAIL")
        mutate("multiple fails", "We built the site", "Calls doubled. We built the site", "| no hype | FAIL")
        mutate("hype word fails", "We built the site", "We built a game-changing site", "| no hype | FAIL")
        mutate("schema claim fails", "and the Meridian", "with schema markup, and the Meridian", "| no structured data | FAIL")
        mutate("internal term fails", "Repair and spring pages came first", "Repair pages passed QA first", "| no internal terms | FAIL")
        mutate("missing consent note fails", "> AM: confirm", "> Note: confirm", "| consent note | FAIL")
        mutate("section order fails", "## Quick Stats", "## Stats", "| sections | FAIL")
        mutate("header must match approvals", "Approved quotes: none", "Approved quotes: 3", "| header | FAIL")
        mutate("edited brief table fails", "| Slate | #3A4048 | body text |", "| Slate | #3A4048 | body text and buttons |", "| brief tables | FAIL", BRIEF)
        mutate("unsourced colour fails", "in Signal Orange", "in #FF00FF", "| brief colours | FAIL", BRIEF)
        mutate("callout stat not in quick stats fails", "- 805 words of new page copy\n", "- 12 awards won\n", "| callout stats | FAIL", BRIEF)

        # approved quotes
        d2 = setup(tmp, "approved")
        rc, out = run("scaffold", "--slug", SLUG, "--launch", "2026-11-18", "--date", "2026-11-25", cwd=d2)
        text = (d2 / CS).read_text()
        case("approved: header and consent from approvals file", "Feature consent: confirmed (Mira Halvorsen, 2026-11-24)" in text
             and "Approved quotes: 3, 8" in text, text)
        lines = text.splitlines()
        i = next(k for k, ln in enumerate(lines) if ln.startswith("[WRITE: pick one approved"))
        j = next(k for k, ln in enumerate(lines) if ln.startswith("## Quick Stats"))
        quote = ["> \"If we fix it today, they call us again when they want a new door.\"", "",
                 "— Gus Halvorsen, Kestrel Garage Doors", ""]
        (d2 / CS).write_text("\n".join(lines[:i] + quote + lines[j:]) + "\n")
        fill(d2 / CS)
        fill(d2 / BRIEF)
        rc, out = run("check", "--slug", SLUG, "--launch", "2026-11-18", cwd=d2)
        case("approved quote version passes", rc == 0, out)
        t2 = (d2 / CS).read_text()
        (d2 / CS).write_text(t2.replace("they call us again", "they always call us again"))
        rc, out = run("check", "--slug", SLUG, "--launch", "2026-11-18", cwd=d2)
        case("reworded approved quote fails", rc == 1 and "| quote | FAIL" in out, out)

        # metrics
        d3 = setup(tmp, "metrics")
        rc, out = run("scaffold", "--slug", SLUG, "--launch", "2026-11-18", "--date", "2027-02-20", cwd=d3)
        text = (d3 / CS).read_text()
        res = ("In the 90 days after launch, organic clicks went from 412 to 1,038 and phone calls from the site from 37 to 96. "
               "Service request forms went from 11 to 29, and the Meridian and Nampa pages earned 214 clicks.")
        lines = text.splitlines()
        lines = [res if ln.startswith("[WRITE: the results measured") else ln for ln in lines]
        i = next(k for k, ln in enumerate(lines) if ln.startswith("[WRITE: pick one approved"))
        j = next(k for k, ln in enumerate(lines) if ln.startswith("## Quick Stats"))
        lines = lines[:i] + quote + lines[j:]
        lines = [ln for ln in lines if ln != "- 2 new location pages"] + ["- 96 phone calls from the site in the first 90 days"]
        (d3 / CS).write_text("\n".join(lines) + "\n")
        fill(d3 / CS)
        fill(d3 / BRIEF)
        rc, out = run("check", "--slug", SLUG, "--launch", "2026-11-18", cwd=d3)
        case("90-day metrics version passes", rc == 0, out)
        t3 = (d3 / CS).read_text()
        (d3 / CS).write_text(t3.replace("from 412 to 1,038", "from 412 to 1,038 (up 152%)"))
        rc, out = run("check", "--slug", SLUG, "--launch", "2026-11-18", cwd=d3)
        case("computed percentage fails", rc == 1 and ("| results | FAIL" in out or "| numbers | FAIL" in out), out)

        # declined
        d4 = setup(tmp, "declined")
        rc, out = run("scaffold", "--slug", SLUG, cwd=d4)
        case("declined client: scaffold writes nothing", rc == 1 and "Featured: no" in out and not (d4 / CS).exists(), out)

        # no kit: colours from the index's palette
        d5 = setup(tmp, None, ["client-reference"])
        rc, out = run("scaffold", "--slug", SLUG, cwd=d5)
        case("no launch date: scaffold refuses", rc == 1 and "no launch date" in out and not (d5 / CS).exists(), out)
        rc, out = run("scaffold", "--slug", SLUG, "--launch", "2026-11-18", cwd=d5)
        b = (d5 / BRIEF).read_text()
        case("no kit: colours from the dev index asset checklist", "Colours from: handoff/kestrel-garage-doors/kestrel-garage-doors-dev-handoff-index.md (Asset Checklist, Colour palette)" in b
             and "#F28C28" in b, b)

        # launch date from the go-live email
        d6 = setup(tmp)
        (d6 / f"emails/{SLUG}").mkdir(parents=True)
        (d6 / f"emails/{SLUG}/{SLUG}-go-live-email.md").write_text("Client: Kestrel Garage Doors\nLaunch: 2026-11-18 at 9:00 a.m.\n\nSubject: x\n")
        rc, out = run("counts", "--slug", SLUG, cwd=d6)
        case("launch date read from the go-live email", "launch: 2026-11-18 (emails/" in out, out)

        # unwritten Build page
        d7 = setup(tmp, None, ["content/nampa-garage-doors"])
        rc, out = run("counts", "--slug", SLUG, cwd=d7)
        case("missing article: not counted, warned", '"pages_built": 8' in out and "WARNING: Build page Nampa Garage Doors" in out, out)

        # readers
        rc, out = run("index", str(FIX / "base/handoff" / SLUG / f"{SLUG}-dev-handoff-index.md"), cwd=REPO)
        data = json.loads(out)
        case("index reader", rc == 0 and len(data["Service Pages"]) == 4 and len(data["### Redirects"]) == 5
             and data["Pages Without a Template"][0]["Priority"] == "Post-Launch", out)
        rc, out = run("quotes", str(FIX / "base/kickoff" / SLUG / f"{SLUG}-quote-bank.md"), cwd=REPO)
        case("quote reader", rc == 0 and len(json.loads(out)) == 8, out)
        rc, out = run("kit", str(REPO / "fixtures/contracts/case-study-kit-sample"), cwd=REPO)
        k = json.loads(out)
        case("kit reader skips retired colours", rc == 0 and [c["Hex"] for c in k["brand.md"]] == ["#5B4B8A", "#8FB39A"]
             and k["Retired, do not use"][0]["Hex"] == "#0055A4", out)
        chk = subprocess.run([sys.executable, str(REPO / "skills/client-reference-kit/scripts/check_kit.py"),
                              str(REPO / "fixtures/contracts/case-study-kit-sample")], capture_output=True, text=True)
        case("kit sample passes client-reference-kit's checker", "missing" not in chk.stdout.lower() and "needs" not in chk.stdout.lower(), chk.stdout)
        rc, out = run("contract", str(d / CS), cwd=REPO)
        case("contract reader", rc == 0 and json.loads(out)["headings"][-1] == "Quick Stats", out)

    passed = sum(ok for _, ok in results)
    print(f"selftest: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
