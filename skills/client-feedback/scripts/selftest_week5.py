#!/usr/bin/env python3
"""Self-test for feedback.py's Week 5 staging review (week5.py).

Usage:
  python3 selftest_week5.py [--fixture DIR] [--plan FILE]

Copies the invented Wrenfield Landscaping fixture to a temporary folder, renders the reference plan
(must pass), then changes the plan, the inputs or the written files in one way the script must refuse
or fail. Run it after changing feedback.py or week5.py, together with selftest_week2.py.
Prints one line per case and exits 1 on any miss. Standard library only.
"""
from __future__ import annotations

import argparse
import copy
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "feedback.py"
REPO = HERE.parents[2]
SLUG = "wrenfield-landscaping"
BH = f"feedback/{SLUG}/2026-11-12-bugherd-client-tasks.json"
REP = f"feedback/{SLUG}/2026-11-12-feedback.md"
TASKS = f"feedback/{SLUG}/2026-11-12-bugherd-tasks.json"
TMP: list[Path] = []


def run(folder: Path, *args: str) -> tuple[int, str]:
    r = subprocess.run([sys.executable, str(SCRIPT), *args], cwd=folder, capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def setup(src: Path, plan: dict, prep=None) -> Path:
    TMP.append(Path(tempfile.mkdtemp()))
    tmp = TMP[-1]
    shutil.copytree(src, tmp, dirs_exist_ok=True)
    if prep:
        prep(tmp)
    (tmp / "feedback-plan.json").write_text(json.dumps(plan), encoding="utf-8")
    return tmp


def render(tmp: Path, email=True, bugherd=True, dry=False) -> tuple[int, str]:
    args = ["render", f"kickoff/{SLUG}", "--plan", "feedback-plan.json"]
    if email:
        args += ["--feedback", "client-email.txt"]
    if bugherd:
        args += ["--bugherd", BH]
    return run(tmp, *args + (["--dry-run"] if dry else []))


def check(tmp: Path) -> tuple[int, str]:
    return run(tmp, "check", f"kickoff/{SLUG}", "--feedback", "client-email.txt", "--report", REP)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixture", default=str(REPO / "fixtures/client-feedback/wrenfield"))
    ap.add_argument("--plan", default=str(REPO / "fixtures/client-feedback/plans/wrenfield-week-5-plan.json"))
    a = ap.parse_args()
    src, base = Path(a.fixture), json.loads(Path(a.plan).read_text(encoding="utf-8"))
    results: list[tuple[str, bool, str]] = []

    def case(name: str, ok: bool, out: str = "") -> None:
        results.append((name, ok, out))

    def refused(name: str, change, want: str, prep=None, **kw) -> None:
        plan = copy.deepcopy(base)
        change(plan)
        tmp = setup(src, plan, prep)
        rc, out = render(tmp, dry=True, **kw)
        case(name, rc == 1 and "PLAN REJECTED" in out and want in out, out)

    # 1. reference plan
    tmp = setup(src, base)
    rc, out = render(tmp)
    case("reference plan renders and passes", rc == 0 and "RESULT: PASS" in out, out)
    tasks = json.loads((tmp / TASKS).read_text(encoding="utf-8"))
    keys = ["finding_id", "status", "create", "bugherd_task_id", "page_url", "department", "column", "assignee",
            "severity", "bugherd_severity", "title", "description"]
    case("task file uses staging-site-qa's keys in order", all(list(t) == keys for t in tasks) and len(tasks) == 5)
    qa_tasks = REPO / "fixtures/staging-site-qa/quillfeather/after-fixes/qa/quillfeather-plumbing/quillfeather-plumbing-bugherd-tasks.json"
    if qa_tasks.exists():
        qa_keys = [list(t) for t in json.loads(qa_tasks.read_text(encoding="utf-8"))]
        case("the same keys as staging-site-qa's own task file", all(k == keys for k in qa_keys) and bool(qa_keys))
    cols = {t["department"]: t["column"] for t in tasks}
    case("columns from qa/routing.md (Strategic to SEO Review)",
         cols == {"Content": "Copy Review", "SEO": "SEO Review", "Design": "Design Review", "Development": "Dev Ready"})
    guest = [t for t in tasks if t["bugherd_task_id"]]
    case("guest BugHerd tasks are moved, not re-created",
         sorted(t["bugherd_task_id"] for t in guest) == ["14", "15"] and not any(t["create"] for t in guest)
         and sum(t["create"] for t in tasks) == 3)
    ref_tmp = tmp

    # 2. recording created ids and re-rendering keeps them
    fid = next(t["finding_id"] for t in tasks if t["create"])
    rc, out = run(ref_tmp, "created", TASKS, f"{fid}=101")
    rc2, out2 = render(ref_tmp)
    again = json.loads((ref_tmp / TASKS).read_text(encoding="utf-8"))
    kept = next(t for t in again if t["finding_id"] == fid)
    case("created ids are kept on a re-render", rc == 0 and rc2 == 0 and kept["bugherd_task_id"] == "101"
         and kept["create"] is False and "RESULT: PASS" in out2, out + out2)
    rc, out = run(ref_tmp, "created", TASKS, "CE-00000000=5")
    case("created refuses an unknown id", rc != 0 and "not in" in out, out)

    # 3. plan refusals
    def item(plan, n):
        return plan["items"][n - 1]
    refused("Strategic edit not owned by SEO", lambda p: item(p, 4).update(department="Content"), "goes to SEO")
    refused("Mechanical edit sent to SEO", lambda p: item(p, 3).update(department="SEO"),
            "Mechanical edit goes to Content, Design or Development")
    refused("Scope Change without a PM/AM note", lambda p: item(p, 5).pop("pm_am_note"), "needs pm_am_note")
    refused("Scope Change sent to a department", lambda p: item(p, 6).update(department="Design"),
            "goes to Account Management")
    refused("Approval with a severity", lambda p: item(p, 1).update(severity="MINOR"), "only Mechanical and Strategic")
    refused("Mechanical edit without a severity", lambda p: item(p, 2).pop("severity"), "needs severity")
    refused("BugHerd task left out", lambda p: p["items"].pop(8), "BugHerd task 15 has no item")
    refused("BugHerd quote attributed to the email", lambda p: item(p, 9).update(source="email"),
            "not a verbatim quote of the client's email text")
    refused("BugHerd item on another page", lambda p: item(p, 8).update(page="/about/"),
            "BugHerd task 14 is on /services/hardscaping/")
    refused("page outside the dev index as Mechanical", lambda p: item(p, 3).update(page="/team/"),
            "not in the dev handoff index")
    refused("'new page' that is not a Scope Change",
            lambda p: item(p, 5).update({"class": "Mechanical", "department": "Content", "severity": "MINOR"})
            or item(p, 5).pop("pm_am_note"), "'new page' is a page the build does not have")
    refused("email question left out", lambda p: p["items"].pop(6), "When will the site go live?")
    refused("unknown class", lambda p: item(p, 2).update({"class": "Typo"}), "class 'Typo'")

    def reply(text_old, text_new):
        return lambda p: p["reply"].update(body=p["reply"]["body"].replace(text_old, text_new))
    refused("reply says the heading already changed",
            reply("The new lawn care heading is a good idea.", "We've updated the lawn care heading."),
            "already made")
    refused("reply commits to the heading before SEO",
            reply("Our SEO team will review it first, because that heading is what the page is found for, and "
                  "I'll come back to you once they have.", "We'll change the heading to your wording."),
            "SEO team will review")
    refused("reply offers no call for Scope Changes",
            reply("Could we have a short call this week to talk them through? ", ""), "offers a call")
    refused("reply agrees to build the new page",
            reply("A snow removal page and a navy look for the homepage both go beyond what we agreed for this build.",
                  "We can add a snow removal page right away."), "agrees to a Scope Change")
    refused("reply uses an internal class label", reply("Thank you for", "Mechanical edits aside, thank you for"),
            "internal label 'Mechanical'")
    refused("reply invents a date", reply("I'll confirm the date as soon as we have it.",
                                          "We launch on November 20."), "number(s) ['20']")
    refused("reply confirms no fixes", lambda p: p["reply"].update(body=(
        "Hi Dana,\n\nThank you for the notes. Our SEO team will review the lawn care heading. Could we have a "
        "call about the snow removal page and the homepage colours? On launch, I'll confirm the date soon.")),
        "confirms them")

    # 4. week routing and inputs
    refused("a Week 1 plan after staging QA has run", lambda p: p.update(week=1), "set \"week\": 5")

    def no_qa(t: Path) -> None:
        shutil.rmtree(t / "qa" / SLUG)
    plan = copy.deepcopy(base)
    plan["items"] = [i for i in plan["items"] if i["source"] == "email"]
    tmp = setup(src, plan, no_qa)
    rc, out = render(tmp, bugherd=False, dry=True)
    case("no staging URL anywhere is refused", rc == 1 and "no staging URL" in out, out)
    plan["staging_url"] = "https://wrenfield.staging-wise.site"
    tmp = setup(src, plan, no_qa)
    rc, out = render(tmp, bugherd=False)
    case("email only, staging_url in the plan", rc == 0 and "RESULT: PASS" in out, out)

    plan = copy.deepcopy(base)
    plan["items"] = [i for i in plan["items"] if i["source"] != "email"]
    plan["from"] = Path(BH).name
    plan["facts"] = []
    plan["reply"]["body"] = ("Hi Dana,\n\nThank you for the two notes in BugHerd. We will swap the deck photo on the "
                             "hardscaping page for one of your patio photos and fix the estimate form on the contact "
                             "page, and I'll let you know when both are done.")
    tmp = setup(src, plan, no_qa)
    rc, out = render(tmp, email=False)
    case("BugHerd tasks only, staging host from the task URLs", rc == 0 and "RESULT: PASS" in out, out)
    rc, out = run(tmp, "check", f"kickoff/{SLUG}", "--report", REP)
    case("check finds the BugHerd export from the report header", rc == 0 and "RESULT: PASS" in out, out)

    # 5. tampered files fail the check
    def tamper(name: str, fn, want: str) -> None:
        t = setup(src, base)
        render(t)
        fn(t)
        rc, out = check(t)
        case(name, rc == 1 and want in out, out)

    def edit_tasks(fn):
        def f(t: Path) -> None:
            data = json.loads((t / TASKS).read_text(encoding="utf-8"))
            fn(data)
            (t / TASKS).write_text(json.dumps(data), encoding="utf-8")
        return f

    def edit_rep(old: str, new: str):
        def f(t: Path) -> None:
            p = t / REP
            p.write_text(p.read_text(encoding="utf-8").replace(old, new, 1), encoding="utf-8")
        return f
    tamper("internal wording in a task fails", edit_tasks(lambda d: d[0].update(
        description=d[0]["description"] + " Keep it inside the budget.")), "internal wording")
    tamper("a task key removed fails", edit_tasks(lambda d: d[1].pop("assignee")), "staging-site-qa's keys")
    tamper("a task dropped fails", edit_tasks(lambda d: d.pop()), "5 Mechanical/Strategic row(s)")
    tamper("guest task re-created fails", edit_tasks(lambda d: d[3].update(bugherd_task_id="", create=True)),
           "does not carry its id")
    tamper("Scope Change note removed fails", edit_rep(": PM/AM: A sixth page", ": A sixth page"), "Scope Changes | FAIL")
    tamper("reclassed row fails", edit_rep("| Strategic | SEO |", "| Strategic | Content |"), "cannot go to Content")
    tamper("edited quote fails", edit_rep("nice work!", "great work!"), "quotes verbatim | FAIL")

    # 6. the contract week-5-handoff-check reads (a fresh render of the reference plan)
    ref_tmp = setup(src, base)
    render(ref_tmp)
    rc, out = run(ref_tmp, "contract", "week-5", REP)
    data = json.loads(out) if rc == 0 else {}
    (ref_tmp / "c.json").write_text(out, encoding="utf-8")
    rc2, out2 = run(ref_tmp, "contract", "--validate", "c.json")
    case("contract prints the class column and tasks and validates",
         rc == 0 and rc2 == 0 and data.get("Week:") == "5" and len(data.get("Class", [])) == 9
         and len(data.get("tasks", [])) == 5, out + out2)
    if data:
        data["Class"][4]["PM/AM note"] = ""
        (ref_tmp / "c.json").write_text(json.dumps(data), encoding="utf-8")
        rc3, out3 = run(ref_tmp, "contract", "--validate", "c.json")
        case("contract without a PM/AM note is invalid", rc3 == 1 and "PM/AM note" in out3, out3)
    fx = REPO / "fixtures/contracts/client-feedback-week-5.json"
    if fx.exists():
        case("contract fixture equals this run's output", json.loads(fx.read_text(encoding="utf-8")) == json.loads(out))

    # 7. other readers of feedback files are not confused by a Week 5 file
    sys.path.insert(0, str(REPO / "skills/dev-handoff-index/scripts"))
    try:
        import dev_index  # noqa: E402
        held = dev_index.read_feedback(ref_tmp / REP)["page: <url-slug>"]
        case("dev-handoff-index reads no page holds from a Week 5 file", held == {}, str(held))
    except Exception as e:  # noqa: BLE001
        case("dev-handoff-index reads no page holds from a Week 5 file", False, repr(e))

    for t in TMP:
        shutil.rmtree(t, ignore_errors=True)
    bad = 0
    for name, ok, out in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name}")
        if not ok:
            bad += 1
            print("      " + out.strip().replace("\n", "\n      ")[:1500])
    print(f"{len(results) - bad}/{len(results)} cases")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
