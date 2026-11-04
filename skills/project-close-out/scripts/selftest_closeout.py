#!/usr/bin/env python3
"""Selftest for closeout.py on temporary copies of the Larkspur Family Dental fixture.

Run from anywhere: python3 skills/project-close-out/scripts/selftest_closeout.py
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLOSEOUT = HERE / "closeout.py"
REPO = HERE.parents[2]
FX = REPO / "fixtures" / "project-close-out" / "larkspur"
S = "larkspur-dental"
SUMMARY = f"closeout/{S}/{S}-project-summary.md"
EMAIL = f"closeout/{S}/{S}-transition-email.md"
HANDOFF = f"closeout/{S}/{S}-retainer-handoff.md"
DATE = ["--date", "2026-11-24"]

results: list[tuple[str, bool, str]] = []


def case(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))


def py(script: Path, args: list[str], cwd: Path) -> tuple[int, str]:
    p = subprocess.run([sys.executable, str(script)] + args, cwd=cwd, capture_output=True, text=True, timeout=180)
    return p.returncode, p.stdout + p.stderr


def co(args: list[str], cwd: Path, script: Path = CLOSEOUT) -> tuple[int, str]:
    return py(script, args, cwd)


def tree(*variants: str, drafts: bool = False, drop: tuple[str, ...] = ()) -> Path:
    d = Path(tempfile.mkdtemp(prefix="closeout-"))
    shutil.copytree(FX / "base", d, dirs_exist_ok=True)
    for v in variants:
        shutil.copytree(FX / "variants" / v, d, dirs_exist_ok=True)
    if drafts:
        shutil.copytree(FX / "drafts", d, dirs_exist_ok=True)
    for rel in drop:
        p = d / rel
        shutil.rmtree(p) if p.is_dir() else p.unlink()
    return d


def edit(path: Path, old: str, new: str) -> None:
    t = path.read_text(encoding="utf-8")
    assert old in t, f"{old!r} not in {path.name}"
    path.write_text(t.replace(old, new, 1), encoding="utf-8")


def row(out: str, name: str) -> str:
    return next((ln for ln in out.splitlines() if ln.startswith(f"| {name} |")), "")


# ------------------------------------------------------------------ fixture integrity

d = tree()
rc, out = py(REPO / "skills/week-6-go-live-email/scripts/golive_email.py",
             ["check", "--slug", S, "--launch", "2026-11-20 09:00", "--integrations", "contact form; online booking request"], d)
case("fixture go-live email passes golive_email.py check", rc == 0, out.strip().splitlines()[-1] if out else "")
rc, out = py(REPO / "skills/retainer-roadmap/scripts/roadmap.py", ["check", f"roadmap/{S}/{S}-seo-roadmap.md"], d)
case("fixture roadmap passes roadmap.py check", rc == 0, out.strip()[:80])
rc, out = py(REPO / "skills/case-study/scripts/case_study.py", ["check", "--slug", S], d)
case("fixture case study passes case_study.py check", rc == 0 and "RESULT: PASS" in out)
rc, out = py(REPO / "skills/staging-site-qa/scripts/qa.py", ["launch-check", f"qa/{S}/{S}-launch-check-2026-11-20.md"], d)
case("fixture launch check reads with qa.py launch-check", rc == 0 and '"RESULT:"' in out)

# ------------------------------------------------------------------ scaffold on the full build

rc, out = co(["scaffold", "--slug", S] + DATE, d)
case("scaffold writes three files", rc == 0 and all((d / p).is_file() for p in (SUMMARY, EMAIL, HANDOFF)), out[-200:])
case("counts printed", "13 pages (Homepage 1, Service Pages 7, Location Pages 1, About Page 3, Contact Page 1), 1,024 words, "
     "2 old URLs redirected" in out)
summ = (d / SUMMARY).read_text()
case("launch date from the go-live email", "Launch: 2026-11-20\n" in summ)
for n, item in ((1, "Go-live email written"), (2, "Launch check LIVE OK, or every issue closed or deferred"),
                (3, "Roadmap written"), (4, "Case study written")):
    case(f"build complete row {n} yes", f"| {n} | {item} | yes |" in summ)
case("open launch finding counted as deferred to the roadmap", "each deferred to the roadmap: QA-5e2f8a33" in summ)
case("deferred staging item with its roadmap task", "Deferred at the Week 5 sweep: Client is rewriting" in summ
     and 'Roadmap Month 1: "/services/invisalign/' in summ)
case("done staging item left out", "QA-90ae2c47" not in summ)
case("NO TARGET redirect outstanding", "https://larkspurdental.com/specials/: no 301 target" in summ)
case("scope change outstanding with PM/AM note", "Scope Change #2 (feedback/larkspur-dental/2026-11-10-feedback.md)" in summ
     and "retainer content after launch. Roadmap Month 1" in summ)
case("post-launch page not counted", "Not built for launch: Dental Anxiety Guide" in summ and "| Total | 13 pages | 1,024 |" in summ)
case("roadmap month totals", "- Month 1: 11 tasks, 14 hours" in summ and "- Month 3: 4 tasks, 12 hours" in summ)
hand = (d / HANDOFF).read_text()
case("handoff: default ClickUp location marked unconfirmed", "Client Monthly Work > Larkspur Family Dental (default, not confirmed" in hand)
case("handoff: communication preference from the context", "Dana prefers email" in hand)
case("handoff: GBP lines and roadmap task", "website link still points to the old site" in hand
     and 'Roadmap: Month 1 "Update the Google Business Profile website link"' in hand)
case("handoff: technical debt has no scope change", "Scope Change" not in hand.split("## Technical Debt")[1].split("##")[0])
mail = (d / EMAIL).read_text()
case("email header", mail.startswith("Client: Larkspur Family Dental\nTo: Dana Whitfield\nLaunch: 2026-11-20\n"
                                      "Account manager: not named\n"))
rc, out = co(["check", "--slug", S], d)
case("unfilled scaffold fails check", rc == 1 and "RESULT: FAIL" in out)
rc, out = co(["scaffold", "--slug", S] + DATE, d)
case("scaffold will not overwrite without --force", rc == 1 and "REFUSED" in out)
rc, out = co(["facts", "--slug", S], d)
f = json.loads(out)
case("facts JSON", f["pages_built"] == 13 and f["words_written"] == 1024 and f["roadmap_months"] == {"1": 11, "2": 5, "3": 4})

# ------------------------------------------------------------------ good drafts pass, then each break fails its row

d = tree(drafts=True)
rc, out = co(["check", "--slug", S], d)
case("good drafts pass", rc == 0 and out.strip().endswith("RESULT: PASS"), "\n".join(ln for ln in out.splitlines() if "FAIL" in ln))

BREAKS = [
    ("page count wrong", EMAIL, "- 13 pages,", "- 14 pages,", "page counts"),
    ("number not from the files", EMAIL, "1,024 words of new copy", "1,024 words of new copy, 40% more than before", "numbers"),
    ("word total wrong", EMAIL, "1,024 words", "1,200 words", "word count stated"),
    ("internal term", EMAIL, "finish two small fixes from launch", "finish two BugHerd fixes", "no internal terms"),
    ("schema claim", EMAIL, "easy to book from.", "easy to book from, with schema markup on every page.", "no structured data"),
    ("live chat not named", EMAIL, "Just reply to this email.", "Or use the new live chat.", "only named integrations"),
    ("sign-off changed", EMAIL, "Account Manager, WISE Digital Partners", "The WISE team", "sign-off"),
    ("too few bullets", EMAIL, "- 2 old addresses that now take visitors straight to the right new page\n", "", "bullets"),
    ("launch date missing", EMAIL, "went live on November 20", "went live this month", "launch date"),
    ("no main contact", EMAIL, "your Account Manager is your main contact for anything about the site", "write to us", "main contact"),
    ("no three months", EMAIL, "For the next three months", "Soon", "next three months"),
    ("no cadence", EMAIL, "You will get a monthly report, and we will set up a monthly check-in call on a Tuesday afternoon, as you prefer.",
     "We will keep you posted.", "reporting cadence"),
    ("other link", EMAIL, "Just reply to this email.", "See https://example.com/plan.", "links"),
    ("header edited", EMAIL, "To: Dana Whitfield", "To: Dana", "email header"),
    ("summary table edited", SUMMARY, "| 4 | Case study written | yes |", "| 4 | Case study written | no |", "section Build Complete"),
    ("outstanding item removed", SUMMARY, "- https://larkspurdental.com/specials/", "- (removed) https://larkspurdental.com/specials/",
     "section Outstanding Items"),
    ("strategic decision schema", SUMMARY, "- Blog content was left", "- Schema markup was added; blog content was left",
     "summary no structured data"),
    ("handoff script line edited", HANDOFF, "| 8 | /meet-us.html", "| 8 | /meet-us", "section Month 1 Priorities"),
    ("handoff placeholder left", HANDOFF, "Finish the launch first:", "[WRITE: x] Finish the launch first:", "handoff placeholders"),
]
for name, rel, old, new, check in BREAKS:
    d = tree(drafts=True)
    edit(d / rel, old, new)
    rc, out = co(["check", "--slug", S], d)
    case(f"break: {name} fails '{check}'", rc == 1 and "| FAIL |" in row(out, check), row(out, check) or out[-300:])

d = tree(drafts=True)
p = d / EMAIL
t = p.read_text()
p.write_text(t.replace("Thank you again, Dana.", "Thank you again, Dana. " + "We are glad to have worked with you. " * 20))
rc, out = co(["check", "--slug", S], d)
case("break: email over 300 words fails 'email length'", rc == 1 and "| FAIL |" in row(out, "email length"))

# ------------------------------------------------------------------ AM name and run-time options

d = tree(drafts=True)
rc, out = co(["check", "--slug", S, "--am", "Sam Okoro"], d)
case("--am changes header and sign-off (old drafts fail)", rc == 1 and "| FAIL |" in row(out, "sign-off")
     and "| FAIL |" in row(out, "email header"))
edit(d / EMAIL, "Account manager: not named", "Account manager: Sam Okoro")
edit(d / EMAIL, "\nAccount Manager, WISE Digital Partners", "\nSam Okoro\nAccount Manager, WISE Digital Partners")
rc, out = co(["check", "--slug", S, "--am", "Sam Okoro"], d)
case("--am: name line above the role passes the email rows",
     "| PASS |" in row(out, "sign-off") and "| PASS |" in row(out, "email header"))

d = tree()
co(["scaffold", "--slug", S, "--clickup-list", "Client Monthly Work > Larkspur Family Dental (LFD)"] + DATE, d)
case("--clickup-list given", "ClickUp: Client Monthly Work > Larkspur Family Dental (LFD)" in (d / HANDOFF).read_text()
     and "(given by the PM)" in (d / HANDOFF).read_text())
d = tree()
co(["scaffold", "--slug", S, "--cadence", "a report by the 5th of each month and a call every other Tuesday"] + DATE, d)
case("--cadence printed in the handoff", "Reporting and check-ins: a report by the 5th of each month" in (d / HANDOFF).read_text())

# ------------------------------------------------------------------ variants

d = tree("clickup")
co(["scaffold", "--slug", S] + DATE, d)
h = (d / HANDOFF).read_text()
case("ClickUp location from the Month 1 plan", "- List: Client Monthly Work > Larkspur Family Dental (roadmap/larkspur-dental/larkspur-dental-clickup-tasks.json)" in h)
case("Month 1 tasks created count", "11 planned in roadmap/larkspur-dental/larkspur-dental-clickup-tasks.json, 10 created in ClickUp" in h)
case("Month 1 tasks file named in the summary", "Month 1 tasks: roadmap/larkspur-dental/larkspur-dental-month-1-tasks.md" in (d / SUMMARY).read_text())

d = tree("recheck")
co(["scaffold", "--slug", S] + DATE, d)
s2 = (d / SUMMARY).read_text()
case("newest launch check read", "Launch check: qa/larkspur-dental/larkspur-dental-launch-check-2026-11-24.md (RESULT: LIVE ISSUES)" in s2)
case("new launch finding not in the roadmap makes row 2 no",
     "| 2 | Launch check LIVE OK, or every issue closed or deferred | no |" in s2 and "not closed or deferred: QA-c81d0e6b" in s2)
case("new launch finding listed as not in the roadmap", "QA-c81d0e6b /services/sedation-dentistry/" in s2 and "not in the roadmap." in s2)
case("fixed launch finding no longer outstanding", "QA-5e2f8a33" not in s2.split("## Outstanding Items")[1])

d = tree()
st = d / f"qa/{S}/{S}-bugherd-status.json"
data = json.loads(st.read_text())
data["tasks"].append({"bugherd_task_id": "601", "finding_id": "QA-5e2f8a33", "title": "redirect", "status": "done",
                      "severity": "important", "deferred": ""})
st.write_text(json.dumps(data))
co(["scaffold", "--slug", S] + DATE, d)
case("launch finding done in BugHerd is skipped", "QA-5e2f8a33" not in (d / SUMMARY).read_text().split("## Outstanding Items")[1])

d = tree(drop=(f"roadmap/{S}", f"case-study/{S}"))
rc, out = co(["scaffold", "--slug", S] + DATE, d)
s3 = (d / SUMMARY).read_text()
case("gaps: package still written", rc == 0 and all((d / p).is_file() for p in (SUMMARY, EMAIL, HANDOFF)))
case("gaps: roadmap and case study rows no", "| 3 | Roadmap written | no |" in s3 and "| 4 | Case study written | no |" in s3)
case("gaps: launch finding not deferred anywhere makes row 2 no", "| 2 | Launch check LIVE OK, or every issue closed or deferred | no |" in s3)
case("gaps: outstanding items say no roadmap yet", "not in a roadmap (no roadmap yet)." in s3)
case("gaps: email slot promises nothing specific", "promise nothing specific" in (d / EMAIL).read_text())
case("gaps: handoff tells SEO to run retainer-roadmap", "No roadmap yet: run retainer-roadmap" in (d / HANDOFF).read_text())

d = tree()
edit(d / f"emails/{S}/{S}-go-live-email.md", "Client: Larkspur", "WARNING: the Week 5 handoff ends NO-GO.\n\nClient: Larkspur")
co(["scaffold", "--slug", S] + DATE, d)
case("go-live email with a warning makes row 1 no", "| 1 | Go-live email written | no |" in (d / SUMMARY).read_text())

d = tree(drop=(f"emails/{S}",))
rc, out = co(["scaffold", "--slug", S] + DATE, d)
case("no go-live email and no --launch: refused, nothing written", rc == 1 and "REFUSED" in out and not (d / SUMMARY).exists())
rc, out = co(["scaffold", "--slug", S, "--launch", "2026-11-20"] + DATE, d)
case("--launch without the go-live email works, row 1 no", rc == 0 and "| 1 | Go-live email written | no |" in (d / SUMMARY).read_text())

d = tree(drop=(f"handoff/{S}/{S}-dev-handoff-index.md",))
rc, out = co(["scaffold", "--slug", S] + DATE, d)
case("missing dev handoff index refused", rc == 1 and "dev-handoff-index" in out)

d = tree()
(d / "content/contact/article.md").unlink()
rc, out = co(["scaffold", "--slug", S] + DATE, d)
case("missing article warned and left out", "WARN: Build page Contact has no content file" in out and "Pages: 12 (" in (d / SUMMARY).read_text())

# sibling skills not installed: copy the script alone
iso = Path(tempfile.mkdtemp(prefix="closeout-iso-")) / "project-close-out" / "scripts"
iso.mkdir(parents=True)
shutil.copy(CLOSEOUT, iso / "closeout.py")
d = tree()
rc, out = co(["scaffold", "--slug", S] + DATE, d, script=iso / "closeout.py")
s4 = (d / SUMMARY).read_text()
case("without sibling skills: roadmap row reads the table only", "| 3 | Roadmap written | yes |" in s4 and "table read only" in s4)
case("without sibling skills: case study row says not checked", "written, not checked" in s4)

# ------------------------------------------------------------------ contracts

d = tree()
rc, out = co(["contract", "golive", f"emails/{S}/{S}-go-live-email.md"], d)
g = json.loads(out)
case("contract golive", g["Launch:"] == "2026-11-20 09:00" and g["Integrations:"] == "contact form, online booking request"
     and g["warnings"] == [])
rc, out = co(["contract", "roadmap", f"roadmap/{S}/{S}-seo-roadmap.md"], d)
r = json.loads(out)
case("contract roadmap", len(r) == 20 and r[0]["Source"] == "launch carry-over" and r[0]["Month"] == "1")
tmp = Path(tempfile.mkdtemp(prefix="closeout-fx-"))
for name, payload in (("golive", g), ("roadmap", r)):
    (tmp / f"{name}.json").write_text(json.dumps(payload))
    rc, out = co(["contract", "--validate", str(tmp / f"{name}.json")], d)
    case(f"validate own {name} JSON", rc == 0 and out.startswith("OK"))
for fx in ("staging-site-qa-launch-check.json", "client-feedback-week-5.json", "project-close-out-golive.json",
           "project-close-out-roadmap.json", "project-close-out-case-study.json"):
    rc, out = co(["contract", "--validate", str(REPO / "fixtures/contracts" / fx)], d)
    case(f"validate {fx}", rc == 0 and out.startswith("OK"), out.strip())
rc, out = py(REPO / "skills/case-study/scripts/case_study.py", ["contract", f"case-study/{S}/{S}-case-study.md"], d)
(tmp / "cs.json").write_text(out)
rc, out = co(["contract", "--validate", str(tmp / "cs.json")], d)
case("validate case_study.py contract output", rc == 0 and "case study" in out)
(tmp / "bad.json").write_text(json.dumps({"hello": 1}))
rc, out = co(["contract", "--validate", str(tmp / "bad.json")], d)
case("reject unrelated JSON", rc == 1)
rc, out = co(["contract", "--validate", str(REPO / "fixtures/week-5-handoff-check/quillfeather/regression/qa/quillfeather-plumbing/quillfeather-plumbing-bugherd-status.json")], d)
case("validate a BugHerd status file", rc == 0 and "BugHerd status" in out)

# ------------------------------------------------------------------ review round 1 cases

LC = f"qa/{S}/{S}-launch-check-2026-11-20.md"
d = tree()
edit(d / LC, "| Development | MAJOR | https://larkspurdental.com/meet-us.html", "| Development | CRITICAL | https://larkspurdental.com/meet-us.html")
co(["scaffold", "--slug", S] + DATE, d)
s5 = (d / SUMMARY).read_text()
case("CRITICAL launch finding in the roadmap still makes row 2 no",
     "| 2 | Launch check LIVE OK, or every issue closed or deferred | no |" in s5 and "QA-5e2f8a33 (CRITICAL)" in s5)

d = tree()
edit(d / LC, "| Development | MAJOR | https://larkspurdental.com/meet-us.html", "| Development | MINOR | https://larkspurdental.com/meet-us.html")
edit(d / LC, "RESULT: LIVE ISSUES", "RESULT: LIVE OK")
edit(d / f"roadmap/{S}/{S}-seo-roadmap.md", "launch-check-2026-11-20.md > QA-5e2f8a33", "launch-check-2026-11-20.md > QA-other")
co(["scaffold", "--slug", S] + DATE, d)
case("LIVE OK with a MINOR open is row 2 yes", "| 2 | Launch check LIVE OK, or every issue closed or deferred | yes |" in (d / SUMMARY).read_text())

d = tree()
st = d / f"qa/{S}/{S}-bugherd-status.json"
data = json.loads(st.read_text())
data["tasks"][2]["status"] = "archived"
data["tasks"].append({"bugherd_task_id": "520", "finding_id": "CE-2a7c41d9", "title": "/about/team/: Correct the spelling",
                      "status": "Copy Review", "severity": "minor", "deferred": "Client sends the right spelling after launch"})
data["tasks"].append({"bugherd_task_id": "521", "finding_id": "QA-11111111", "title": "x", "status": "Complete",
                      "severity": "minor", "deferred": ""})
st.write_text(json.dumps(data))
co(["scaffold", "--slug", S] + DATE, d)
s6 = (d / SUMMARY).read_text()
case("archived BugHerd task counts as done", "QA-7b3d5f11" not in s6.split("## Outstanding Items")[1])
case("deferred client-edit task is outstanding", "CE-2a7c41d9 (client edit, BugHerd #520)" in s6
     and "Deferred at the Week 5 sweep: Client sends" in s6)

d = tree()
co(["scaffold", "--slug", S] + DATE, d)
case("failing redirect not counted as redirected", "Old URLs redirected: 2; not answering on the live site yet: 1" in (d / SUMMARY).read_text())

d = tree()
rm = d / f"roadmap/{S}/{S}-seo-roadmap.md"
t = rm.read_text()
line = next(ln for ln in t.splitlines() if "> #2 |" in ln)
rm.write_text(t.replace(line + "\n", "").replace("## Not Planned\n\n- none",
              "## Not Planned\n\n- feedback/larkspur-dental/2026-11-10-feedback.md > #2: the practice decided against the page"))
co(["scaffold", "--slug", S] + DATE, d)
case("Not Planned reason read whole", "Roadmap: Not Planned (the practice decided against the page)." in (d / SUMMARY).read_text())

MORE = [
    ("page count by noun", EMAIL, "with a page for each of your 7 services", "with 3 service pages", "page counts", False),
    ("markup claim", EMAIL, "easy to book from.", "easy to book from, with FAQ markup.", "no structured data", False),
    ("spoofed link", EMAIL, "Just reply to this email.", "See https://larkspurdental.com.example.net/x.", "links", False),
    ("live site link allowed", EMAIL, "Just reply to this email.", "See https://larkspurdental.com/contact/.", "links", True),
    ("traffic figure from a roadmap description", EMAIL, "what implants cost", "what implants cost, a search made 6600 times a month",
     "numbers", False),
    ("range with a hyphen", EMAIL, "finish two small fixes", "finish 2-9 small fixes", "numbers", False),
    ("ordinal launch date", EMAIL, "went live on November 20", "went live on November 20th", "launch date", True),
    ("decision without a source", SUMMARY, "- Blog content was left for after launch, since blog writing was outside the build scope "
     "[kickoff/larkspur-dental/larkspur-dental-context.md]", "- Blog content was left for after launch", "strategic decisions", False),
]
for name, rel, old, new, check, want in MORE:
    d = tree(drafts=True)
    edit(d / rel, old, new)
    rc, out = co(["check", "--slug", S], d)
    case(f"{'allow' if want else 'break'}: {name} '{check}'", ("| PASS |" if want else "| FAIL |") in row(out, check),
         row(out, check) or out[-300:])

# ------------------------------------------------------------------ report

bad = [r for r in results if not r[1]]
for name, ok, det in results:
    if not ok or "-v" in sys.argv:
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  [{det}]" if det and not ok else ""))
print(f"selftest: {len(results) - len(bad)}/{len(results)} passed")
sys.exit(1 if bad else 0)
