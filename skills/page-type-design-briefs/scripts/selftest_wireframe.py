#!/usr/bin/env python3
"""Small cases for wireframe.py: wireframes build from a passing brief, and hand edits that break a rule fail.

Usage: python3 selftest_wireframe.py     (standard library only; reuses selftest_ptdb's invented client)
"""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import selftest_ptdb as T  # noqa: E402
import wireframe as W  # noqa: E402

WF = HERE / "wireframe.py"


def run(root: Path, mode: str, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(WF), mode, "--slug", T.SLUG, "--root", str(root), *extra],
                          capture_output=True, text=True)


def main() -> int:
    fails = 0

    def say(ok: bool, name: str, detail: str = "") -> None:
        nonlocal fails
        fails += not ok
        print(("ok    " if ok else "WRONG ") + name + ("" if ok else f"\n{detail}"))

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for rel, body in T.FILES.items():
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(body, encoding="utf-8")
        T.run(root, "scaffold", "--client", "Wrenfield Glass", "--date", "2026-10-20")
        brief = root / "design" / T.SLUG / f"{T.SLUG}-page-type-design-briefs.md"
        scaffold = brief.read_text(encoding="utf-8")

        r = run(root, "build")
        say(r.returncode == 1 and "Finish the brief first" in r.stderr
            and not list((root / "design" / T.SLUG).glob("*-wireframe.html")), "unfinished brief: refused, nothing written", r.stderr)

        brief.write_text(T.fill(scaffold, "Option A"), encoding="utf-8")
        r = run(root, "build")
        svc = root / "design" / T.SLUG / f"{T.SLUG}-service-wireframe.html"
        about = root / "design" / T.SLUG / f"{T.SLUG}-about-wireframe.html"
        say(r.returncode == 0 and svc.exists() and about.exists() and "RESULT: PASS" in r.stdout,
            "filled brief: one wireframe per page type, check passes", r.stdout + r.stderr)
        page = svc.read_text(encoding="utf-8")
        say(re.findall(r'data-section="([^"]+)"', page) == ["Opening answer", "Question sections", "Booking"],
            "service sections follow the Content Map", page)
        say("[NEEDS INPUT: repair warranty]" in page and "What breaks?" in page, "real copy and flags carried", page)
        say("#34495E" in page and "Slate" not in page, "sourced colour used, nothing else from the brief", page)
        say(re.search(r'data-section="Booking"[^>]*data-cta="yes"', page) is not None, "CTA section marked from the CTAs bullets", page)

        good = page
        for name, bad in [
            ("stray colour fails", good.replace("#e6e6e6", "#ff6600", 1)),
            ("script fails", good.replace("</body>", "<script>x()</script></body>")),
            ("outside link fails", good.replace('<span class="wf-link">Book</span>', '<a href="https://example.com">Book</a>', 1)),
            ("section order fails", good.replace('data-section="Opening answer"', 'data-section="Booking x"', 1)),
            ("lost copy fails", good.replace("What breaks?", "What fails?")),
        ]:
            svc.write_text(bad, encoding="utf-8")
            r = run(root, "check")
            say(r.returncode == 1 and "RESULT: FAIL" in r.stdout, name, r.stdout)
        svc.write_text(good, encoding="utf-8")

        stray = root / "design" / T.SLUG / f"{T.SLUG}-resource-wireframe.html"
        stray.write_text(good, encoding="utf-8")
        r = run(root, "check")
        say(r.returncode == 1, "wireframe for a type the brief lacks fails", r.stdout)
        stray.unlink()

        for rel in ("client-reference/wrenfieldglass/brand.md", f"design/{T.SLUG}/{T.SLUG}-homepage-design-brief.md"):
            p = root / rel
            p.write_text(p.read_text(encoding="utf-8").replace(" #34495E", ""), encoding="utf-8")
        brief.write_text(T.fill(scaffold, "Option A").replace(
            "- Slate #34495E as the primary colour [kit: brand.md]",
            "- GAP: brand.md names Slate but gives no colour value; the AM asks the client"), encoding="utf-8")
        r = run(root, "build", "--only", "service")
        greys = {h.lower() for h in W.GREYS}
        hexes = {h.lower() for h in re.findall(r"#[0-9A-Fa-f]{6}\b", svc.read_text(encoding="utf-8"))}
        say(hexes <= greys, "no tagged colour in the brief: greys only", str(hexes - greys) + r.stdout + r.stderr)

    # assignment of page blocks to Content Map rows
    blocks = W.page_blocks("# T\n\nIntro.\n\n## Key Takeaways\n\n- a\n\n## Q1?\n\nx\n\n## Q2?\n\ny\n\n"
                           "## Frequently Asked Questions\n\n### F?\n\nz\n\n## How do I book?\n\nb\n\n## Sources\n\n1. s\n")
    rows = [{"section": s, "source": src} for s, src in [
        ("Opening answer", "article.md > H1 and opening"), ("Key Takeaways", "article.md > Key Takeaways"),
        ("Question sections", "article.md > H2 question sections"), ("FAQ", "article.md > Frequently Asked Questions"),
        ("Booking", "article.md > last H2")]]
    got, notes = W.assign(rows, blocks)
    say(got == [[0], [1], [2, 3], [4], [5]] and not notes, "blocks: anchors, the run between them, Sources left out", str(got))
    got, notes = W.assign([rows[0], rows[1], rows[4]], blocks)
    say(got == [[0], [1, 2, 3, 4], [5]] and notes, "blocks no row names join the row before them", str((got, notes)))

    # two rows with no heading of their own: the blocks go to the row that names a run of sections
    faq_named = [rows[0], rows[1], rows[2], {"section": "FAQ", "source": "article.md > FAQ"}, rows[4]]
    got, _ = W.assign(faq_named, blocks)
    say(got[2] == [2, 3, 4] and got[3] == [], "unmatched FAQ row gets nothing, no split by position", str(got))
    extra = rows[:3] + [{"section": "Guarantee", "source": "article.md > Follow-up guarantee"}] + rows[3:]
    got, _ = W.assign(extra, blocks)
    say(got[2] == [2, 3] and got[3] == [], "row naming a heading the page lacks gets no copy", str(got))

    # colours: tagged, not a GAP, not a refused colour, role from the bullet
    body = ("### Brand Reference\n\n- Navy `#1B2A41` for headings [kit: brand.md]\n"
            "- No red `#CC0000` anywhere [kit: brand.md]\n- Amber #F2A900 for the call to action [kit: brand.md]\n"
            "- GAP: body text colour #444444 not confirmed\n- Slate #5B6770 for body text\n")
    say(W.colours(body) == {"heading": ("#1B2A41", "Navy `#1B2A41` for headings [kit: brand.md]"),
                            "cta": ("#F2A900", "Amber #F2A900 for the call to action [kit: brand.md]")},
        "colours: only tagged role colours", str(W.colours(body)))
    for bullet, want in [
        ("Red `#C8102E` must not be used for buttons or headings [kit: brand.md]", {}),
        ("Primary Forest Green `#2E5E3A`, accent Goldenrod `#E0A526` for buttons [kit: brand.md]",
         {"heading": "#2E5E3A", "cta": "#E0A526"}),
        ("Cream `#F7F3EA` page background, behind the body text [kit: brand.md]", {}),
        ("Old teal `#2A9D8F` is retired; the call to action uses Amber `#F2A900` [kit: brand.md]", {"cta": "#F2A900"}),
        ("Amber `#F2A900` for calls to action only, \"never for text or backgrounds\" [kit: brand.md]", {"cta": "#F2A900"}),
    ]:
        got = {k: v[0] for k, v in W.colours("### Brand Reference\n\n- " + bullet + "\n").items()}
        say(got == want, "colour role read from its own clause: " + bullet[:40], str(got))
    cta = W.cta_sections("### CTAs\n\n- The Hero carries no call to action; the Booking section closes the page [article]\n",
                         [{"section": "Hero"}, {"section": "Booking"}])
    say(cta == {"Booking"}, "a CTA bullet that says a section has none does not mark it", str(cta))

    print(f"{fails} wrong")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
