#!/usr/bin/env python3
"""Self-test for the clickup-build-setup scripts. Invented clients only. Prints `selftest: N/N passed`."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
results: list[tuple[str, bool]] = []


def run(*args, cwd) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], cwd=cwd, capture_output=True, text=True)


def check(name: str, cond: bool) -> None:
    results.append((name, bool(cond)))
    if not cond:
        print(f"FAIL {name}")


def fake_readback(ops: dict) -> dict:
    tasks, ids = [], {}
    for n, it in enumerate(ops["items"]):
        ids[it["key"]] = f"t{n:03d}"
    waits = {}
    for d in ops["dependencies"]:
        waits.setdefault(d["task"], []).append(ids[d["waits_on"]])
    for it in ops["items"]:
        tasks.append({"id": ids[it["key"]], "name": it["name"],
                      "parent": ids[it["parent_key"]] if it["parent_key"] else None, "status": it["status"],
                      "start_date": str(it["start_ms"]) if it["start_ms"] else None,
                      "due_date": str(it["due_ms"]) if it["due_ms"] else None, "tags": list(it["tags"]),
                      "assignees": [1] if it["assignee"] else [], "waits_on": waits.get(it["key"], [])})
    return {"list_id": "900000000001", "list_url": "https://app.clickup.com/9/v/li/900000000001", "tasks": tasks}


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        plan = HERE / "plan_build.py"
        p = run(plan, "--client", "Larkspur Pet Clinic", "--code", "lpc", "--kickoff", "2026-11-16",
                "--paid-media", "no", "--person", "AM=Ana Field", cwd=tmp)
        check("plan runs", p.returncode == 0 and "PLAN: OK" in p.stdout)
        ops_path = tmp / "clickup/larkspur-pet-clinic/larkspur-pet-clinic-clickup-ops.json"
        ops = json.loads(ops_path.read_text())
        names = [it["name"] for it in ops["items"]]
        check("list name", ops["list"]["name"] == "[LPC] Larkspur Pet Clinic | Website Full Build")
        check("no paid media tasks", not any("paid media" in n.lower() for n in names))
        check("no design brief anywhere", not any("brief" in n.lower() and "design" in n.lower() for n in names))
        check("website design task", "Website Design" in names and "Homepage Design" in names)
        wd = next(it for it in ops["items"] if it["key"] == "WD")
        check("thanksgiving skipped", "2026-11-26" in ops["holidays_skipped"])
        check("WD due D19 = 2026-12-11", wd["due_date"] == "2026-12-11")
        check("dates at 09:00 UTC", all(it["due_ms"] % 86400000 == 9 * 3600000 for it in ops["items"] if it["due_ms"]))
        check("groups first", [it["level"] for it in ops["items"]] == sorted(it["level"] for it in ops["items"]))
        k1 = next(it for it in ops["items"] if it["key"] == "1")
        check("step 1 to do", k1["status"] == "to do")
        check("AM assigned", k1["assignee"] == "Ana Field")
        check("count", ops["counts"]["dependencies"] == 66 and ops["counts"]["group"] == 14)
        # an "&" in the name gives the same slug as the kickoff folder
        p = run(plan, "--client", "Fernhill Glass & Glazing", "--code", "fgg", "--kickoff", "2026-11-16",
                "--paid-media", "no", cwd=tmp)
        check("ampersand slug matches kickoff", p.returncode == 0 and
              (tmp / "clickup/fernhill-glass-and-glazing/fernhill-glass-and-glazing-clickup-ops.json").is_file())
        # check_list on a perfect readback
        rb = fake_readback(ops)
        rb_path = tmp / "rb.json"
        rb_path.write_text(json.dumps(rb))
        c = run(HERE / "check_list.py", ops_path, rb_path, cwd=tmp)
        check("readback passes", c.returncode == 0 and "RESULT: PASS" in c.stdout)
        check("plan record written", (ops_path.parent / "larkspur-pet-clinic-clickup-plan.md").is_file())
        # a date a day early fails
        bad = json.loads(json.dumps(rb))
        t = next(t for t in bad["tasks"] if t["name"] == "Website Design")
        t["due_date"] = str(int(t["due_date"]) - 29 * 3600000)  # 04:00 UTC the day before
        rb_path.write_text(json.dumps(bad))
        c = run(HERE / "check_list.py", ops_path, rb_path, cwd=tmp)
        check("day-early date fails", c.returncode == 1 and "WD Website Design: due_date 2026-12-10" in c.stdout)
        # missing dependency + duplicate task fail
        bad = json.loads(json.dumps(rb))
        next(t for t in bad["tasks"] if t["name"] == "Website Design")["waits_on"] = []
        bad["tasks"].append(dict(bad["tasks"][0], id="dup"))
        rb_path.write_text(json.dumps(bad))
        c = run(HERE / "check_list.py", ops_path, rb_path, cwd=tmp)
        check("missing dep and duplicate fail", c.returncode == 1 and "exists 2 times" in c.stdout and "does not wait on" in c.stdout)
        # pages
        rb_path.write_text(json.dumps(rb))
        report = tmp / "report.md"
        report.write_text("# Arch\n\n## 4. URL map\n\n| Page | URL | Parent | Nav location | Priority |\n|---|---|---|---|---|\n"
                          "| Home | / | - | logo | P1 |\n| About | /about | Home | main | P2 |\n"
                          "| Privacy Policy (not in SOW scope) | /privacy | Home | footer | P3 |\n"
                          "| Dental Care | /services/dental-care | Services | main | P1 |\n")
        g = run(HERE / "page_subtasks.py", "--report", report, "--ops", ops_path, "--readback", rb_path, cwd=tmp)
        check("pages planned", g.returncode == 0 and "PAGES: 3 to create, 0 already there" in g.stdout)
        out = json.loads((ops_path.parent / "larkspur-pet-clinic-page-subtasks.json").read_text())
        check("page name format", out["create"][0]["name"] == "Page: About (/about)")
        check("scope marker stripped", out["create"][1]["name"] == "Page: Privacy Policy (/privacy)")
        # rerun with one page already there
        rb2 = json.loads(json.dumps(rb))
        w25 = next(t for t in rb2["tasks"] if t["name"] == "Write the sitemap pages")
        rb2["tasks"].append({"id": "pg1", "name": "Page: About (/about)", "parent": w25["id"], "status": "internal dependency",
                             "start_date": w25["start_date"], "due_date": w25["due_date"], "tags": [], "assignees": [], "waits_on": []})
        rb_path.write_text(json.dumps(rb2))
        g = run(HERE / "page_subtasks.py", "--report", report, "--ops", ops_path, "--readback", rb_path, cwd=tmp)
        check("pages rerun skips existing", "PAGES: 2 to create, 1 already there" in g.stdout)
        c = run(HERE / "check_list.py", ops_path, rb_path, "--ids-out", tmp / "ids.json", cwd=tmp)
        check("page subtasks are not extras", c.returncode == 0)
        check("ids map rebuilt", json.loads((tmp / "ids.json").read_text())["ids"]["WD"].startswith("t"))
        # test run + paid media
        p = run(plan, "--client", "Larkspur Pet Clinic", "--code", "[LPC]", "--kickoff", "2026-11-30",
                "--paid-media", "yes", "--test-run", "--out-dir", "t", cwd=tmp)
        ops2 = json.loads((tmp / "t/larkspur-pet-clinic-clickup-ops.json").read_text())
        n2 = [it["name"] for it in ops2["items"]]
        check("test list name", ops2["list"]["name"] == "[LPC] TEST Larkspur Pet Clinic | Website Full Build")
        check("issues log", "TEST · Issues log" in n2)
        check("test tag everywhere", all("test-run" in it["tags"] for it in ops2["items"]))
        check("paid media created", "Paid Media (only if signed)" in n2 and ops2["counts"]["dependencies"] == 74)
        check("test schedule ends day 15", ops2["last_day"] == "2026-12-18")
        p = run(plan, "--client", "Larkspur Pet Clinic", "--code", "LPC", "--kickoff", "2026-11-30", "--paid-media", "no",
                "--test-run", "--list-name", "[LPC] Larkspur Pet Clinic TEST | Website Full Build", "--out-dir", "n", cwd=tmp)
        ops3 = json.loads((tmp / "n/larkspur-pet-clinic-clickup-ops.json").read_text())
        check("list name override", ops3["list"]["name"] == "[LPC] Larkspur Pet Clinic TEST | Website Full Build")
        q = run(plan, "--client", "X Co", "--code", "XCO", "--kickoff", "2026-11-30", "--paid-media", "no",
                "--list-name", "Wrong name", "--out-dir", "m", cwd=tmp)
        check("override must start with code", q.returncode == 2)
        # bad input
        for args, label in (([ "--kickoff", "2026-11-28"], "weekend kickoff"), (["--code", "ABCD"], "bad code"),
                            (["--person", "Boss=X"], "unknown role")):
            base = {"--client": "X Co", "--code": "XCO", "--kickoff": "2026-11-30"}
            argv = []
            for k, v in base.items():
                if k not in args:
                    argv += [k, v]
            q = run(plan, *argv, *args, "--paid-media", "no", cwd=tmp)
            check(f"rejects {label}", q.returncode == 2)
    passed = sum(ok for _, ok in results)
    print(f"selftest: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
