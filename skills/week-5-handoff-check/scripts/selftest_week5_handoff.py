#!/usr/bin/env python3
"""Selftest for week5_handoff.py on the Quillfeather Plumbing fixtures (run from the repo root).

  python3 skills/week-5-handoff-check/scripts/selftest_week5_handoff.py
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = Path(__file__).resolve().parent / "week5_handoff.py"
FX = ROOT / "fixtures" / "week-5-handoff-check" / "quillfeather"
S = "quillfeather-plumbing"
PASSED: list[str] = []
FAILED: list[str] = []


def ok(name: str, cond: bool, info: str = "") -> None:
    (PASSED if cond else FAILED).append(name + ("" if cond else f": {info}"))


def folder(variant: str) -> Path:
    d = Path(tempfile.mkdtemp(prefix=f"w5h-{variant}-"))
    shutil.copytree(FX / "common", d, dirs_exist_ok=True)
    if variant:
        shutil.copytree(FX / variant, d, dirs_exist_ok=True)
    return d


def run(d: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args, "--root", str(d)], capture_output=True, text=True)


def sweep(d: Path, today: str = "2026-11-17") -> tuple[int, str, str]:
    r = run(d, "run", "--slug", S, "--today", today, "--pm", "Jordan Vale")
    h = d / "handoff" / S / f"{S}-week-5-handoff.md"
    return r.returncode, r.stdout, h.read_text() if h.exists() else ""


def row(handoff: str, n: int) -> str:
    m = re.search(rf"(?m)^\| {n} \| [^|]+ \| (PASS|FAIL) \|", handoff)
    return m.group(1) if m else "missing"


def status(d: Path) -> Path:
    return d / "qa" / S / f"{S}-bugherd-status.json"


def msg(d: Path) -> Path:
    return d / "handoff" / S / f"{S}-go-live-message.md"


def edit_json(p: Path, fn) -> None:
    data = json.loads(p.read_text())
    fn(data)
    p.write_text(json.dumps(data, indent=2))


def main() -> int:
    # 1. regression: NO-GO, blockers with owners, stale message removed
    d = folder("regression")
    code, out, h = sweep(d)
    ok("regression exits 3", code == 3, out)
    ok("regression ends NO-GO", h.rstrip().endswith("\nNO-GO"))
    ok("regression row 3 FAIL", row(h, 3) == "FAIL")
    ok("regression row 4 FAIL", row(h, 4) == "FAIL")
    ok("regression row 5 FAIL", row(h, 5) == "FAIL")
    ok("regression rows 1,2,6,7,8 PASS", all(row(h, n) == "PASS" for n in (1, 2, 6, 7, 8)), h)
    ok("critical owned by Content", re.search(r"QA-daf2e19b[^\n]*No BugHerd task yet[^\n]*\(owner: Content\)", h) is not None)
    ok("open CE task blocks", re.search(r"BugHerd #31 \(CE-66f3ebb0\)[^\n]*'Copy Review'[^\n]*\(owner: Content\)", h) is not None)
    ok("open QA finding listed once", h.split("## Blocking")[1].split("## Carried")[0].count("QA-dcc6e684") == 1, h)
    ok("stale go-live message removed", not msg(d).exists())
    ok("scope change listed", "#3 site-wide: Discuss an online booking calendar" in h)

    # 2. no reply after reply-by with the go-ahead line: GO
    d = folder("no-reply")
    code, out, h = sweep(d)
    ok("no-reply GO", code == 0 and h.rstrip().endswith("\nGO"), out)
    ok("client not verified noted", "client not verified: no reply by 2026-11-13" in h)
    m = msg(d).read_text() if msg(d).exists() else ""
    ok("message written", m.startswith("Go-live message: Quillfeather Plumbing"))
    ok("message lists 5 Build pages", len(re.findall(r"(?m)^- [^:\n]+: /", m.split("At launch:")[0])) == 5, m)
    ok("message has 6 launch toggles", m.count("(Development)") == 6)
    ok("message carries the deferral", "DEFERRED: The client is sending a new header photo" in m)
    ok("message lists post-launch page", "Winter Pipe Guide (/blog/winter-pipe-guide/): Post-Launch priority" in m)
    ok("message signed by the PM", "Jordan Vale\nProject Manager, WISE Digital Partners" in m)
    ok("message production domain", "deployment to quillfeatherplumbing.com" in m)

    # 3. same, but the email dropped the no-reply line: NO-GO for the AM
    d = folder("no-reply")
    e = d / "emails" / S / f"{S}-week-5-email.md"
    e.write_text(e.read_text().replace("No-reply line: yes", "No-reply line: dropped"))
    code, _, h = sweep(d)
    ok("no reply + dropped line is NO-GO", code == 3 and row(h, 7) == "FAIL" and "the AM gets the client's answer" in h)

    # 4. before the reply-by date with no feedback: waiting
    d = folder("no-reply")
    edit_json(status(d), lambda s: s.update(read_on="2026-11-12"))
    code, _, h = sweep(d, "2026-11-12")
    ok("waiting on the client", row(h, 7) == "FAIL" and "the client has until 2026-11-13" in h, h)

    # 5. go folder without a status file: BugHerd not read
    d = folder("go")
    code, _, h = sweep(d)
    ok("no status file blocks", code == 3 and row(h, 5) == "FAIL" and "BugHerd statuses not read" in h)
    ok("undeferred MAJOR blocks", row(h, 4) == "FAIL")

    # 6. status-template, then fill as the PM said: GO
    r = run(d, "status-template", "--slug", S)
    tpl = json.loads(status(d).read_text())
    ok("template lists task-file ids", [t["bugherd_task_id"] for t in tpl["tasks"]] == ["25", "31", "32"], r.stdout)
    r2 = run(d, "status-template", "--slug", S)
    ok("template refuses to overwrite", r2.returncode == 2 and "already exists" in r2.stdout)

    def fill(s):
        s.update(read_on="2026-11-17", source="PM in chat")
        for t in s["tasks"]:
            t["status"] = "done"
            if t["bugherd_task_id"] == "25":
                t.update(status="SEO Review", deferred="Client sends a new header photo after launch")
        s["tasks"] += [{"bugherd_task_id": str(i), "finding_id": "", "title": "", "status": "closed",
                        "severity": "", "deferred": ""} for i in (20, 21, 22, 23, 24, 26, 27, 28)]
    edit_json(status(d), fill)
    code, out, h = sweep(d)
    ok("filled status gives GO", code == 0, out)
    ok("deferred MAJOR passes row 4", "| 4 | Open MAJOR | PASS | 1 deferred by the PM |" in h)
    m = msg(d).read_text() if msg(d).exists() else ""
    ok("go message has scope change", "Scope Change #3 site-wide: Discuss an online booking calendar" in m)

    # 7. stale read_on (before the newest QA report)
    edit_json(status(d), lambda s: s.update(read_on="2026-11-16"))
    code, _, h = sweep(d)
    ok("stale statuses block", row(h, 5) == "FAIL" and "read them again" in h)
    ok("NO-GO removes the message", not msg(d).exists())
    edit_json(status(d), lambda s: s.update(read_on="2026-11-17"))

    # 8. a status missing for a task-file id, and a blank status
    edit_json(status(d), lambda s: s.update(tasks=[t for t in s["tasks"] if t["bugherd_task_id"] != "31"]))
    _, _, h = sweep(d)
    ok("missing task id blocks", "BugHerd #31 (CE-66f3ebb0) is not in the status file" in h)

    def blank(s):
        s["tasks"].append({"bugherd_task_id": "31", "finding_id": "CE-66f3ebb0", "title": "", "status": "",
                           "severity": "", "deferred": ""})
    edit_json(status(d), blank)
    _, _, h = sweep(d)
    ok("blank status blocks", "BugHerd #31 (CE-66f3ebb0) has no status" in h)

    # 9. hand-made open task with minor severity is post-launch; normal one blocks
    def extra(s):
        for t in s["tasks"]:
            if t["bugherd_task_id"] == "31":
                t["status"] = "done"
        s["tasks"] += [{"bugherd_task_id": "40", "finding_id": "", "title": "Footer spacing", "status": "backlog",
                        "severity": "minor", "deferred": ""}]
    edit_json(status(d), extra)
    code, _, h = sweep(d)
    ok("minor hand-made task carried", code == 0 and 'BugHerd #40 "Footer spacing" (\'backlog\') MINOR' in h, h)
    edit_json(status(d), lambda s: s["tasks"][-1].update(severity="normal"))
    code, _, h = sweep(d)
    ok("normal hand-made task blocks", code == 3 and "BugHerd #40 \"Footer spacing\" is still 'backlog'" in h)
    edit_json(status(d), lambda s: s["tasks"].pop())

    # 10. FIXED finding with an open task: close in BugHerd, not blocking
    edit_json(status(d), lambda s: [t.update(status="Dev Ready") for t in s["tasks"] if t["bugherd_task_id"] == "21"])
    tf = d / "qa" / S / f"{S}-bugherd-tasks.json"
    tasks = json.loads(tf.read_text())
    tasks.append({"finding_id": "QA-d1bfad17", "status": "FIXED", "create": False, "bugherd_task_id": "21",
                  "department": "Development", "severity": "CRITICAL"})
    tf.write_text(json.dumps(tasks))
    code, _, h = sweep(d)
    ok("fixed but open is housekeeping", code == 0 and "BugHerd #21 (QA-d1bfad17): fixed in the QA re-run but still 'Dev Ready'" in h, h)

    edit_json(status(d), lambda s: s["tasks"].append({"bugherd_task_id": "20", "finding_id": "QA-65f2ee1c",
                                                     "status": "Copy Review", "severity": "", "deferred": ""}))
    code, _, h = sweep(d)
    ok("older FIXED finding still open is housekeeping", code == 0 and "BugHerd #20 (QA-65f2ee1c): fixed in the QA re-run" in h, h)

    # 11. CE task never created
    ce = d / "feedback" / S / "2026-11-12-bugherd-tasks.json"
    edit_json(ce, lambda ts: ts[0].update(bugherd_task_id="", create=True))
    code, _, h = sweep(d)
    ok("uncreated CE task blocks", code == 3 and "CE-66f3ebb0 (Content) was never created in BugHerd" in h)

    # 11b. a CRITICAL client edit can't be deferred or downgraded in BugHerd
    edit_json(ce, lambda ts: ts[0].update(bugherd_task_id="31", create=False, severity="CRITICAL"))
    edit_json(status(d), lambda s: [t.update(status="Copy Review", deferred="PM says later")
                                    for t in s["tasks"] if t["bugherd_task_id"] == "31"])
    code, _, h = sweep(d)
    ok("deferred CRITICAL client edit blocks", code == 3 and "CRITICAL, which cannot be deferred" in h, h)
    edit_json(status(d), lambda s: [t.update(deferred="", severity="minor")
                                    for t in s["tasks"] if t["bugherd_task_id"] == "31"])
    code, _, h = sweep(d)
    ok("CRITICAL client edit marked minor in BugHerd blocks", code == 3 and "CRITICAL, which cannot be deferred" in h)
    edit_json(status(d), lambda s: [t.update(status="done") for t in s["tasks"] if t["bugherd_task_id"] == "31"])
    code, _, h = sweep(d)
    ok("done CRITICAL client edit passes", code == 0, h)
    ok("Not Checked lines in notes", "Not checked by the QA re-run: Winter Pipe Guide" in h)

    # 11c. QA re-run older than the client edits; AM sign-off dated in the future; second feedback round
    fb2 = d / "feedback" / S / "2026-11-18-feedback.md"
    fb2.write_text((d / "feedback" / S / "2026-11-12-feedback.md").read_text().replace("Date: 2026-11-12", "Date: 2026-11-18"))
    code, _, h = sweep(d, "2026-11-19")
    ok("QA older than client edits blocks", row(h, 2) == "FAIL" and "older than the client edits" in h, h)
    ok("both feedback rounds counted", "2 rounds, newest" in h and h.count("(client edits 2026-11-1") == 2, h)
    fb2.unlink()
    am0 = d / "qa" / S / f"{S}-am-review.md"
    am0.write_text(am0.read_text().replace("2026-11-09", "2026-11-30"))
    _, _, h = sweep(d)
    ok("future AM sign-off date blocks", row(h, 8) == "FAIL")
    am0.write_text(am0.read_text().replace("2026-11-30", "2026-11-09"))

    # 11d. a report that says NOT READY but whose CRITICAL row can't be read
    q = d / "qa" / S / f"{S}-staging-qa-2026-11-17.md"
    q.write_text(q.read_text().replace("RESULT: CONDITIONAL", "RESULT: NOT READY"))
    _, _, h = sweep(d)
    ok("NOT READY without a readable CRITICAL blocks", row(h, 3) == "FAIL")
    q.write_text(q.read_text().replace("| # | Page URL | Department |", "| ID | Page URL | Department |"))
    _, _, h = sweep(d)
    ok("missing Findings table blocks", row(h, 3) == "FAIL" and "no Findings table" in h)

    # 11e. a STOP still removes an earlier GO message
    d2 = folder("no-reply")
    sweep(d2)
    (d2 / "kickoff" / S / f"{S}-context.md").unlink()
    code, out, _ = sweep(d2)
    ok("STOP removes an earlier GO message", code == 2 and not msg(d2).exists(), out)

    # 12. Scope Change without a PM/AM note, AM sign-off missing, index NO-GO, first-run QA
    d = folder("no-reply")
    shutil.copytree(FX / "go" / "feedback", d / "feedback")
    fbp = d / "feedback" / S / "2026-11-12-feedback.md"
    fbp.write_text(re.sub(r"(?m)^- #3 site-wide: PM/AM: .*$", "", fbp.read_text()))
    edit_json(status(d), lambda s: s["tasks"].extend([
        {"bugherd_task_id": "31", "finding_id": "CE-66f3ebb0", "status": "done", "severity": "", "deferred": ""},
        {"bugherd_task_id": "32", "finding_id": "CE-b68a1b66", "status": "done", "severity": "", "deferred": ""}]))
    _, _, h = sweep(d)
    ok("scope change without note blocks", row(h, 7) == "FAIL" and "Scope Changes without a PM/AM note: #3" in h, h)
    am = d / "qa" / S / f"{S}-am-review.md"
    am.write_text(am.read_text().replace("AM sign-off: Riley Shaw, 2026-11-09", "AM sign-off: pending"))
    _, _, h = sweep(d)
    ok("missing AM sign-off blocks", row(h, 8) == "FAIL")
    ix = d / "handoff" / S / f"{S}-dev-handoff-index.md"
    ix.write_text(ix.read_text().rstrip()[:-2] + "NO-GO\n")
    _, _, h = sweep(d)
    ok("index NO-GO blocks", row(h, 1) == "FAIL")
    for p in (d / "qa" / S).glob(f"{S}-staging-qa-2026-11-1*.md"):
        p.unlink()
    (d / "qa" / S / f"{S}-staging-qa-2026-11-06.md").unlink()
    _, _, h = sweep(d)
    ok("first-run QA blocks", row(h, 2) == "FAIL" and "is a first run" in h, h)

    # 13. contract readers agree with the producers' own readers
    pairs = [
        (["contract", "feedback", "fixtures/contracts/client-feedback-week-5-sample/2026-11-12-feedback.md"],
         "fixtures/contracts/client-feedback-week-5.json"),
        (["contract", "email", "fixtures/contracts/week-5-client-email-sample/marrowbrook-electric-week-5-email.md"],
         "fixtures/contracts/week-5-client-email-header.json"),
        (["contract", "qa", f"fixtures/week-5-handoff-check/quillfeather/regression/qa/{S}/{S}-staging-qa-2026-11-17.md"],
         "fixtures/contracts/staging-site-qa-week-5-handoff.json"),
    ]
    for args, fixture in pairs:
        r = subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, cwd=ROOT)
        ok(f"reader matches {Path(fixture).name}", json.loads(r.stdout) == json.loads((ROOT / fixture).read_text()))
    bad = Path(tempfile.mkdtemp()) / "bad.json"
    bad.write_text(json.dumps({"Week:": "5", "Class": [{"#": "1", "Class": "Scope Change", "PM/AM note": ""}], "tasks": []}))
    r = subprocess.run([sys.executable, str(SCRIPT), "contract", "--validate", str(bad)], capture_output=True, text=True)
    ok("validate rejects a Scope Change without a note", r.returncode == 1)

    for p in PASSED:
        print("PASS", p)
    for f in FAILED:
        print("FAIL", f)
    print(f"{len(PASSED)}/{len(PASSED) + len(FAILED)} passed")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
