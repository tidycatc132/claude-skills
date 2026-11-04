#!/usr/bin/env python3
"""Self-test for roadmap.py on the invented Larkspur Family Dental fixtures.

Run from the repo root:  python3 skills/retainer-roadmap/scripts/selftest_roadmap.py
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SCRIPT = HERE / "roadmap.py"
FIX = REPO / "fixtures" / "retainer-roadmap" / "larkspur"
SLUG = "larkspur-dental"
RM = f"roadmap/{SLUG}/{SLUG}-seo-roadmap.md"
M1 = f"roadmap/{SLUG}/{SLUG}-month-1-tasks.md"
PLAN = f"roadmap/{SLUG}/{SLUG}-clickup-tasks.json"
results: list[tuple[bool, str]] = []


def ok(cond: bool, label: str) -> None:
    results.append((bool(cond), label))


def run(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args, "--root", str(root)] if args[0] != "contract"
                          else [sys.executable, str(SCRIPT), *args], capture_output=True, text=True, cwd=REPO)


def work(*layers: str) -> Path:
    d = Path(tempfile.mkdtemp(prefix="roadmap-"))
    for layer in layers:
        shutil.copytree(FIX / layer, d, dirs_exist_ok=True)
    return d


def rows(text: str) -> list[list[str]]:
    out = []
    for ln in text.splitlines():
        if ln.startswith("| ") and not ln.startswith("| Month") and not ln.startswith("| #"):
            out.append([c.strip() for c in re.split(r"(?<!\\)\|", ln)[1:-1]])
    return out


def fill(path: Path) -> None:
    s = path.read_text()
    s = re.sub(r"\[WRITE: three[^\]]*\]", "Larkspur launched with 13 pages. Month 1 finishes launch. Months 2 and 3 "
               "follow Phase 2 and Phase 3.", s)
    s = s.replace("[WRITE: the authority task this evidence calls for]", "Grow reviews on the service pages")
    path.write_text(s)


def edit(path: Path, old: str, new: str) -> None:
    s = path.read_text()
    assert old in s, old
    path.write_text(s.replace(old, new, 1))


def check(root: Path, f: str = RM) -> subprocess.CompletedProcess:
    return run(root, "check", f)


def main() -> int:
    # 1. scaffold from the base files
    w = work("base")
    p = run(w, "scaffold", "--slug", SLUG, "--date", "2026-11-21")
    ok(p.returncode == 0 and "WROTE" in p.stdout, "scaffold writes the roadmap")
    text = (w / RM).read_text()
    rs = rows(text)
    carry = [r for r in rs if r[6] == "launch carry-over"]
    ok(len(carry) == 6 and all(r[0] == "1" and r[3] == "high" and r[5] == "SEO" for r in carry),
       "six launch carry-over tasks in Month 1, high, SEO")
    ok(any("https://larkspurdental.com/sitemap.xml" in r[2] for r in carry), "sitemap task names the live sitemap")
    by = {re.search(r"(QA-[0-9a-f]{8}|#\d+|Tier \d: [^;|]+|Redirects: \S+|Content Calendar: \w+)", r[6]).group(1)
          if re.search(r"(QA-[0-9a-f]{8}|#\d+|Tier \d: [^;|]+|Redirects: \S+|Content Calendar: \w+)", r[6]) else r[1]: r
          for r in rs}
    r = by.get("QA-4c1e9a20")
    ok(r and r[0] == "1" and r[3] == "high" and r[5] == "Content" and "Deferred at the Week 5 sweep" in r[2],
       "deferred MAJOR staging item: Month 1, high, Content, says deferred")
    r = by.get("QA-7b3d5f11")
    ok(r and r[0] == "2" and r[3] == "low" and r[5] == "SEO", "open MINOR staging item: Month 2, low")
    ok("QA-90ae2c47" not in text, "item done in BugHerd is not planned")
    r = by.get("QA-5e2f8a33")
    ok(r and r[0] == "1" and r[5] == "Dev" and "launch check" in r[2], "open launch finding: Month 1, Dev")
    r = by.get("Redirects: https://larkspurdental.com/specials/")
    ok(r and r[0] == "1" and r[5] == "SEO", "NO TARGET redirect becomes an SEO Month 1 task")
    r = next((x for x in rs if x[6].endswith("2026-11-10-feedback.md > #2")), None)
    ok(r and r[0] == "1" and r[5] == "AM" and "PM/AM note" in r[2], "Scope Change: Month 1, AM, with the PM/AM note")
    cal = [r for r in rs if "Content Calendar" in r[6]]
    ok([r[0] for r in cal] == ["1", "2", "3"], "calendar months map to Months 1, 2, 3")
    ok(cal[0][3] == "high" and "Tier 2" in cal[0][6], "Tier 2 calendar keyword is high priority with both sources")
    ok(cal[2][3] == "medium" and "Tier 3" in cal[2][6], "Tier 3 calendar keyword is medium")
    r = [x for x in rs if "dentist boise\"" in x[1]]
    ok(r and r[0][0] == "2" and r[0][5] == "SEO", "Tier 2 keyword outside the calendar: Month 2, SEO")
    ok(any("Dental Anxiety Guide" in x[1] and x[0] == "2" for x in rs), "Post-Launch index page planned in Month 2")
    ok(any(x[1] == "Start local link building" and "14" in x[2] and "312" in x[2] for x in rs),
       "referring-domain gap becomes link building with both numbers")
    ok(text.count("[WRITE: the authority task") == 3, "three authority evidence lines left for the model")
    ok([x[0] for x in rs] == sorted(x[0] for x in rs), "rows sorted by month")

    # 2. check
    p = check(w)
    ok(p.returncode == 1 and "[WRITE] slot" in p.stdout, "check fails while [WRITE] slots remain")
    fill(w / RM)
    p = check(w)
    ok(p.returncode == 0 and "CHECK PASS" in p.stdout, "check passes once filled")
    good = (w / RM).read_text()

    def neg(old: str, new: str, want: str, label: str) -> None:
        (w / RM).write_text(good)
        edit(w / RM, old, new)
        q = check(w)
        ok(q.returncode == 1 and want in q.stdout, label)
    neg("| 1 | Capture Core Web Vitals |", "| 2 | Capture Core Web Vitals |", "must be in Month 1",
        "carry-over moved out of Month 1 fails")
    line = next(ln for ln in good.splitlines() if "Take a baseline with seo-drift-monitor" in ln)
    neg(line + "\n", "", "launch carry-over task missing", "deleted carry-over task fails")
    neg("Start local link building", "Add schema markup to every page", "never plans structured data",
        "a schema task fails")
    neg("| 3 | Write and publish /blog/are-dental-x-rays-safe/ (explainer) | Keyword: are dental x rays safe.",
        "| 3 | Write and publish /blog/are-dental-x-rays-safe/ (explainer) | Keyword: dental implants boise.",
        "already a build page's main keyword", "a build keyword planned as new content fails")
    neg("| 2 | Start local link building", "| 4 | Start local link building", "use 1, 2 or 3", "Month 4 fails")
    neg("| high | 1 | Dev |", "| urgent | 1 | Dev |", "use high, medium or low", "bad priority fails")
    neg("| 1 | Dev |", "| 1 | Tobin |", "use SEO, Content, AM or Dev", "a person's name as owner fails")
    neg("qa/larkspur-dental/larkspur-dental-launch-check-2026-11-20.md > QA-5e2f8a33",
        "qa/larkspur-dental/missing.md > QA-5e2f8a33", "does not exist", "a Source file that does not exist fails")
    qa_line = next(ln for ln in good.splitlines() if "QA-7b3d5f11" in ln)
    neg(qa_line + "\n", "", "is missing: keep its row", "a dropped item without a reason fails")
    (w / RM).write_text(good.replace(qa_line + "\n", "").replace(
        "## Not Planned\n\n- none", "## Not Planned\n\n- qa/larkspur-dental/larkspur-dental-staging-qa-2026-11-16.md > "
        "QA-7b3d5f11: the client is replacing the team photo"))
    ok(check(w).returncode == 0, "a dropped item moved to Not Planned with a reason passes")
    (w / RM).write_text(good.replace(qa_line + "\n", "").replace(
        "## Not Planned\n\n- none", "## Not Planned\n\n- qa/larkspur-dental/larkspur-dental-staging-qa-2026-11-16.md > "
        "QA-7b3d5f11"))
    q = check(w)
    ok(q.returncode == 1 and "must be `- <Source>: <reason>`" in q.stdout, "a Not Planned line without a reason fails")
    (w / RM).write_text(good)
    sit = next(ln for ln in good.splitlines() if ln.startswith("| 1 | Update the Google Business Profile"))
    edit(w / RM, sit, sit.replace("| Point the", "| Already done at launch by Dev. Point the").replace(
        "| high | 0.5 |", "| high | 0 |"))
    ok(check(w).returncode == 0, "an Already done carry-over row with 0 hours passes")
    done_text = (w / RM).read_text()
    (w / RM).write_text(good)

    # 3. overwrite guard
    p = run(w, "scaffold", "--slug", SLUG, "--date", "2026-11-21")
    ok(p.returncode == 2 and "already exists" in p.stdout and (w / RM).read_text() == good,
       "scaffold refuses to overwrite an edited roadmap")
    p = run(w, "scaffold", "--slug", SLUG, "--date", "2026-11-21", "--force")
    ok(p.returncode == 0 and "[WRITE" in (w / RM).read_text(), "--force rebuilds it")
    (w / RM).write_text(good)

    # 4. variants
    v = work("base", "variants/calendar-conflict")
    run(v, "scaffold", "--slug", SLUG, "--date", "2026-11-21")
    vt = (v / RM).read_text()
    np = vt.split("## Not Planned")[1]
    ok("Content Calendar: February: dental implants boise" in np and
       "Content Calendar: February" not in vt.split("## Not Planned")[0], "build keyword in the calendar is not planned")
    ok("Choose the page that targets \"how much do dental implants cost\"" in vt,
       "Tier 2 keyword dropped from the calendar still gets an SEO task")
    n = work("base")
    p = run(n, "scaffold", "--slug", SLUG, "--date", "2026-11-21", "--competitors", "none")
    nt = (n / RM).read_text()
    ok(p.returncode == 0 and "Competitor analysis: none" in nt and "link building" not in nt and "[WRITE: the authority"
       not in nt, "no competitor report: no authority rows")
    (n / "blueprint" / SLUG / f"{SLUG}-growth-blueprint.md").unlink()
    p = run(n, "scaffold", "--slug", SLUG, "--force")
    ok(p.returncode == 2 and "Growth Blueprint" in p.stdout, "missing Blueprint stops")
    for d in (v, n):
        shutil.rmtree(d)

    # 5. Month 1 mode on the later files
    m = work("base", "month-1")
    p = run(m, "month1", "--slug", SLUG, "--date", "2026-11-26")
    ok(p.returncode == 0 and "12 tasks (2 new since the roadmap, 1 left out)" in p.stdout, "month1 summary line")
    ok("PREVIEW ONLY" in p.stdout, "month1 says nothing is in ClickUp yet")
    mt = (m / M1).read_text()
    plan = json.loads((m / PLAN).read_text())
    mrows = rows(mt.split("## Left Out")[0])
    ok(len(mrows) == len(plan["tasks"]) == 12, "task list and plan have the same 12 rows")
    ok(all(r[1] == t["call"]["args"]["name"] and r[6] == t["source"] for r, t in zip(mrows, plan["tasks"])),
       "plan matches the task list row for row")
    ok("QA-c81d0e6b" in mt and "2026-11-14-feedback.md > #1" in mt, "new launch finding and new Scope Change added")
    ok("QA-5e2f8a33" in mt.split("## Left Out")[1] and "QA-5e2f8a33" not in mt.split("## Left Out")[0],
       "redirect fixed on the re-run is left out")
    ok(plan["space"] == "Client Monthly Work" and plan["list"] == "Larkspur Family Dental", "space and list name")
    args = plan["tasks"][0]["call"]["args"]
    ok(args["priority"] == "high" and args["time_estimate"] == "30" and "assignees" not in args
       and args["tags"] == ["month 1", "seo"], "ClickUp args: priority, minutes, tags, no assignees")
    ok(all(not t["clickup_task_id"] for t in plan["tasks"]), "nothing recorded as created")
    ok(check(m, PLAN).returncode == 0, "check passes on the plan")
    p = run(m, "month1", "--slug", SLUG, "--list", "Larkspur Dental - Retainer")
    ok(json.loads((m / PLAN).read_text())["list"] == "Larkspur Dental - Retainer", "--list names the list")
    # created
    p = run(m, "created", PLAN, "--list-id", "901", "--approved-by", "SEO", "--task", "1=abc1", "--task", "2=abc2")
    plan = json.loads((m / PLAN).read_text())
    ok(p.returncode == 0 and plan["tasks"][0]["clickup_task_id"] == "abc1" and plan["list_id"] == "901"
       and plan["tasks"][3]["call"]["args"]["list_id"] == "901", "created records ids and the list id")
    p = run(m, "created", PLAN, "--task", "1=zzz")
    ok(p.returncode == 2 and json.loads((m / PLAN).read_text())["tasks"][0]["clickup_task_id"] == "abc1",
       "created refuses a second id for a task")
    run(m, "month1", "--slug", SLUG, "--list", "Larkspur Dental - Retainer")
    ok(json.loads((m / PLAN).read_text())["tasks"][1]["clickup_task_id"] == "abc2", "month1 re-run keeps recorded ids")
    pl = json.loads((m / PLAN).read_text())
    pl["tasks"][4]["call"]["args"]["name"] = "Something else"
    (m / PLAN).write_text(json.dumps(pl))
    q = check(m, PLAN)
    ok(q.returncode == 1 and "name differs" in q.stdout, "plan check catches a row that differs")
    (m / RM).write_text(done_text.replace("2026-11-21", "2026-11-21"))
    run(m, "month1", "--slug", SLUG)
    ok("already done" in (m / M1).read_text().split("## Left Out")[1], "Already done carry-over is left out")
    (m / RM).write_text((m / RM).read_text().replace("Larkspur launched", "[WRITE: x]"))
    p = run(m, "month1", "--slug", SLUG)
    ok(p.returncode == 2 and "fails its check" in p.stdout, "month1 refuses a roadmap that fails check")
    shutil.rmtree(m)

    # 5b. review fixes: markup findings, dropped items, duplicates, odd inputs
    x = work("base")
    sq = x / "qa" / SLUG / f"{SLUG}-staging-qa-2026-11-16.md"
    edit(sq, "| QA-7b3d5f11 | /about/team/ | SEO | MINOR |",
         "| QA-0d0d0d0d | / | SEO | MAJOR | LocalBusiness schema is missing. | Add JSON-LD. |\n"
         "| QA-1e1e1e1e | /services/family-dentistry/ | Content | MAJOR | The H1 should name family dentist boise. | "
         "Put family dentist boise in the H1. |\n| QA-7b3d5f11 | /about/team/ | SEO | MINOR |")
    run(x, "scaffold", "--slug", SLUG, "--date", "2026-11-21")
    xt = (x / RM).read_text()
    ok("QA-0d0d0d0d" in xt.split("## Not Planned")[1] and "QA-0d0d0d0d" not in xt.split("## Not Planned")[0],
       "a schema finding goes to Not Planned, never into the table")
    fill(x / RM)
    q = check(x)
    ok(q.returncode == 0, "check passes with the schema finding parked and a Content QA fix naming a build keyword")
    line = next(ln for ln in (x / RM).read_text().splitlines() if "QA-7b3d5f11" in ln and ln.startswith("| "))
    (x / RM).write_text((x / RM).read_text().replace(line + "\n", "").replace(
        "## Not Planned\n\n", "## Not Planned\n\n- qa/larkspur-dental/larkspur-dental-staging-qa-2026-11-16.md > "
        "QA-7b3d5f11: the client is replacing the team photo\n", 1))
    edit(x / RM, "Month 1 finishes launch.", "Month 1 finishes launch.")
    xt = (x / RM).read_text().replace("| 2 | /about/team/", "| 1 | /about/team/")
    (x / RM).write_text(xt)
    ok(check(x).returncode == 0, "roadmap with a dropped item passes")
    edit(sq, "| QA-7b3d5f11 | /about/team/ | SEO | MINOR |", "| QA-7b3d5f11 | /about/team/ | SEO | MAJOR |")
    p = run(x, "month1", "--slug", SLUG)
    mt = (x / M1).read_text()
    ok(p.returncode == 0 and "QA-7b3d5f11" not in mt and "QA-0d0d0d0d" not in mt and "schema" not in mt.lower(),
       "month1 keeps Not Planned items and markup findings out")
    p = run(x, "created", PLAN, "--task", "1=dup", "--task", "2=dup")
    ok(p.returncode == 2 and "two tasks" in p.stdout, "created refuses one id for two tasks")
    run(x, "created", PLAN, "--list-id", "77", "--task", "1=a1")
    p = run(x, "created", PLAN, "--task", "2=a1")
    ok(p.returncode == 2 and "already recorded" in p.stdout, "created refuses an id already used by another task")
    run(x, "month1", "--slug", SLUG)
    ok(json.loads((x / PLAN).read_text())["list_id"] == "77", "month1 re-run keeps the list id")
    (x / "qa" / SLUG / f"{SLUG}-bugherd-status.json").write_text("[]")
    p = run(x, "scaffold", "--slug", SLUG, "--force")
    ok(p.returncode == 2 and "must be an object" in p.stdout, "a status file that is a list stops cleanly")
    shutil.rmtree(x)
    y = work("base")
    kw = y / "research" / "keyword-research" / "2026-10-14-larkspur-dental.md"
    edit(kw, "| March | /blog/are-dental-x-rays-safe/", "| April | /blog/tooth-sensitivity/ | why are my teeth sensitive | "
         "explainer | seasonal |\n| March | /blog/are-dental-x-rays-safe/")
    run(y, "scaffold", "--slug", SLUG)
    yt = (y / RM).read_text()
    ok("Content Calendar: March: are dental x rays safe: the calendar's month 4" in yt, "a fourth calendar month goes "
       "to Not Planned")
    edit(kw, "| Month | Page | Primary keyword | Format | Why now |", "| Month | Keyword | Format | Funnel | Why now |")
    p = run(y, "scaffold", "--slug", SLUG, "--force")
    ok("WARN:" in p.stdout and "Content Calendar" in p.stdout, "an unreadable calendar prints a WARN")
    shutil.rmtree(y)

    # 6. readers agree with the producers' own readers
    qa = REPO / "skills" / "staging-site-qa" / "scripts" / "qa.py"
    sys.path.insert(0, str(HERE))
    import roadmap as R  # noqa: E402
    for rep in (FIX / "base/qa/larkspur-dental/larkspur-dental-launch-check-2026-11-20.md",
                FIX / "month-1/qa/larkspur-dental/larkspur-dental-launch-check-2026-11-24.md",
                REPO / "fixtures/staging-site-qa/saltmarsh/after-launch-check/qa/saltmarsh-tree-care/"
                       "saltmarsh-tree-care-launch-check-2026-11-18.md"):
        if qa.exists():
            prod = json.loads(subprocess.run([sys.executable, str(qa), "launch-check", str(rep)], capture_output=True,
                                             text=True).stdout)
            mine = R.read_qa(R.read(rep))
            ids = lambda x: None if x is None else [r["Finding ID"] for r in x]  # noqa: E731
            ok(mine["findings"] == prod["## Findings"] and mine["result"] == prod["RESULT:"] and
               mine["live"] == prod["Live:"] and ids(mine["rerun"]) == ids(prod["## Re-run Status"]),
               f"launch reader matches qa.py ({rep.name})")
    fb = REPO / "skills" / "client-feedback" / "scripts" / "feedback.py"
    for f in (REPO / "fixtures/contracts/client-feedback-week-5-sample/2026-11-12-feedback.md",
              FIX / "base/feedback/larkspur-dental/2026-11-10-feedback.md"):
        if fb.exists():
            prod = json.loads(subprocess.run([sys.executable, str(fb), "contract", "week-5", str(f)],
                                             capture_output=True, text=True).stdout)
            mine = R.read_feedback(R.read(f))
            ok([(i["#"], i["Class"], i["note"]) for i in mine["items"]] ==
               [(c["#"], c["Class"], c["PM/AM note"]) for c in prod["Class"]] and mine["week"] == prod["Week:"],
               f"feedback reader matches feedback.py ({f.name})")

    # 7. contract readers reproduce their fixtures
    for kind, src, fixture in (
            ("blueprint", "evals/growth-blueprint/golden/larkspur-full/blueprint/larkspur-dental/"
                          "larkspur-dental-growth-blueprint.md", "fixtures/contracts/retainer-roadmap-blueprint.json"),
            ("keywords", "fixtures/contracts/keyword-research-report.md", "fixtures/contracts/retainer-roadmap-calendar.json")):
        p = run(Path("."), "contract", kind, src)
        ok(p.stdout.strip() == (REPO / fixture).read_text().strip(), f"contract {kind} output equals its fixture")
    shutil.rmtree(w)

    bad = [lab for good_, lab in results if not good_]
    for good_, lab in results:
        print(("PASS " if good_ else "FAIL ") + lab)
    print(f"{len(results) - len(bad)}/{len(results)} passed")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
