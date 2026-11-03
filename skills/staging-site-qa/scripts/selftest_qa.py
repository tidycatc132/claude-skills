#!/usr/bin/env python3
"""Self-test for qa.py on the invented Quillfeather Plumbing fixtures (no network, no screenshots).

Run from the repo root: python3 skills/staging-site-qa/scripts/selftest_qa.py
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
QA = HERE / "qa.py"
REPO = HERE.parents[2]
FIX = REPO / "fixtures" / "staging-site-qa" / "quillfeather"
SLUG = "quillfeather-plumbing"
BASE = "https://quillfeather.staging-wise.site"
results = []


def run(cwd, *args):
    return subprocess.run([sys.executable, str(QA), *args], cwd=cwd, capture_output=True, text=True, timeout=120)


def ok(name, cond, detail=""):
    results.append((name, bool(cond), detail))


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="sqa-"))
    try:
        w = tmp / "w"
        shutil.copytree(FIX / "base", w)
        qa = w / "qa" / SLUG
        r = run(w, "scan", "--slug", SLUG, "--base-url", BASE, "--saved", "staging", "--date", "2026-11-03", "--no-screens")
        ok("scan exits 0", r.returncode == 0, r.stderr)
        r = run(w, "report", "--slug", SLUG)
        ok("report exits 0 and check passes", r.returncode == 0 and "CHECK PASS" in r.stdout, r.stdout + r.stderr)
        rep = (qa / f"{SLUG}-staging-qa-2026-11-03.md").read_text()
        want = {
            "QA-76c273e5": "| /about/ | SEO | MAJOR |",
            "QA-65f2ee1c": "| /services/drain-cleaning/ | Content | CRITICAL |",
            "QA-81660a68": "| / | SEO | MAJOR |",
            "QA-9b522990": "| /contact/ | Development | MAJOR |",
            "QA-d1bfad17": "| /services/water-heater-repair/ | Development | CRITICAL |",
            "QA-dcc6e684": "| /services/drain-cleaning/ | SEO | MAJOR |",
            "QA-2fd83d99": "| /contact/ | Content | CRITICAL |",
        }
        for fid, cells in want.items():
            ok(f"first run finds {fid}", f"| {fid} {cells}" in rep)
        ok("no extra findings on first run", rep.count("\n| QA-") == 9, str(rep.count("\n| QA-")))
        ok("noindex is a launch toggle", "- /: noindex on staging" in rep and "noindex" not in rep.split("## Findings")[1].split("## Launch Toggles")[0])
        ok("result NOT READY", rep.strip().endswith("RESULT: NOT READY"))
        ok("structured data line once", rep.count("Structured data: not in the current process") == 1)
        tasks = json.loads((qa / f"{SLUG}-bugherd-tasks.json").read_text())
        ok("tasks all NEW and created", all(t["status"] == "NEW" and t["create"] for t in tasks) and len(tasks) == 9)
        ok("routing columns and assignees", {t["department"]: (t["column"], t["assignee"]) for t in tasks}.get("SEO") == ("SEO Review", "Sam Ortiz"))
        ok("pipe kept escaped", "About Us \\| Quillfeather Plumbing" in rep)

        # review notes: a design row without valid evidence is rejected
        (qa / f"{SLUG}-review-notes.md").write_text(
            "## Design Findings\n\n| Page URL | Severity | Finding | Fix | Evidence |\n|---|---|---|---|---|\n"
            "| /about/ | MAJOR | The hero looks crowded. | Add space. | qa/quillfeather-plumbing/screens/about-mobile.png |\n")
        r = run(w, "report", "--slug", SLUG)
        ok("design finding without a screenshot is rejected", r.returncode == 1 and "not a screenshot from this scan" in r.stderr, r.stderr)
        (qa / f"{SLUG}-review-notes.md").write_text(
            "## Design Findings\n\n| Page URL | Severity | Finding | Fix | Evidence |\n|---|---|---|---|---|\n"
            "| /services/drain-cleaning/ | MINOR | The header photo is the wrong size. | Upload the 1600 x 900 WebP. | asset checklist: Service header photo (2): 1600 x 900, WebP |\n\n"
            "## AM Items\n\n- The client has not sent the crew photo.\n")
        r = run(w, "report", "--slug", SLUG)
        rep2 = (qa / f"{SLUG}-staging-qa-2026-11-03.md").read_text()
        ok("asset checklist evidence accepted", r.returncode == 0 and "| Design | MINOR |" in rep2 and "(asset checklist: Service header photo" in rep2, r.stdout + r.stderr)
        ok("AM item listed, not a task", "- The client has not sent the crew photo." in rep2 and "crew photo." not in (qa / f"{SLUG}-bugherd-tasks.json").read_text())
        (qa / f"{SLUG}-review-notes.md").unlink()
        run(w, "report", "--slug", SLUG)

        # check catches a tampered result line
        p = qa / f"{SLUG}-staging-qa-2026-11-03.md"
        good = p.read_text()
        p.write_text(good.replace("RESULT: NOT READY", "RESULT: READY"))
        r = run(w, "check", str(p))
        ok("check rejects a wrong result line", r.returncode == 1)
        p.write_text(good)

        # re-run against the earlier report
        shutil.copytree(FIX / "after-fixes" / "staging-after", w / "staging-after")
        run(w, "scan", "--slug", SLUG, "--base-url", BASE, "--saved", "staging-after", "--date", "2026-11-04", "--no-screens")
        r = run(w, "report", "--slug", SLUG)
        rr = (qa / f"{SLUG}-staging-qa-2026-11-04.md").read_text()
        ok("re-run counts", "Re-run: 7 FIXED, 2 OPEN, 1 NEW" in rr, r.stdout)
        ok("re-run marks FIXED", "| QA-76c273e5 | FIXED |" in rr)
        ok("re-run marks OPEN", "| QA-81660a68 | OPEN |" in rr)
        ok("re-run marks NEW placeholder", "| QA-daf2e19b | NEW | /services/water-heater-repair/ | Content | CRITICAL |" in rr)
        tasks = json.loads((qa / f"{SLUG}-bugherd-tasks.json").read_text())
        ok("re-run creates only NEW", [t["finding_id"] for t in tasks if t["create"]] == ["QA-daf2e19b"])
        run(w, "report", "--slug", SLUG)
        rr2 = (qa / f"{SLUG}-staging-qa-2026-11-04.md").read_text()
        ok("same-day report twice is stable", rr2 == rr)

        # recorded BugHerd ids: a same-day re-run never creates those tasks again
        r = run(w, "created", "--slug", SLUG, "QA-daf2e19b=9001")
        ok("created records the id", r.returncode == 0 and "0 still to create" in r.stdout, r.stdout + r.stderr)
        run(w, "scan", "--slug", SLUG, "--base-url", BASE, "--saved", "staging-after", "--date", "2026-11-04", "--no-screens")
        r = run(w, "report", "--slug", SLUG)
        tasks = json.loads((qa / f"{SLUG}-bugherd-tasks.json").read_text())
        t = next(t for t in tasks if t["finding_id"] == "QA-daf2e19b")
        ok("same-day re-run keeps the id and does not re-create", t["bugherd_task_id"] == "9001" and not t["create"] and r.returncode == 0, r.stdout)
        ok("theme and menu staging URLs are one launch toggle",
           "theme, menu or file URL(s) use the staging domain" in rr and "wp-content/themes" not in rr.split("## Launch Toggles")[0])
        ok("svg <title> is not the meta title", 'meta title is "Menu"' not in rep)

        # live mode against a local server
        import http.server
        import threading
        import functools
        class Quiet(http.server.SimpleHTTPRequestHandler):
            def log_message(self, *args):
                pass
        h = functools.partial(Quiet, directory=str(w / "staging"))
        srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        lw = tmp / "live"
        shutil.copytree(FIX / "base", lw, ignore=shutil.ignore_patterns("staging"))
        env_base = f"http://127.0.0.1:{srv.server_address[1]}"
        import os
        os.environ["NO_PROXY"] = os.environ["no_proxy"] = "127.0.0.1"
        r = run(lw, "scan", "--slug", SLUG, "--base-url", env_base, "--date", "2026-11-03", "--no-screens")
        r2 = run(lw, "report", "--slug", SLUG)
        srv.shutdown()
        lrep = (lw / "qa" / SLUG / f"{SLUG}-staging-qa-2026-11-03.md").read_text() if r2.returncode in (0, 1) else ""
        ok("live mode: missing page by 404", "| QA-d1bfad17 | /services/water-heater-repair/ | Development | CRITICAL | The page is missing on staging (HTTP 404)" in lrep, r.stdout + r.stderr + r2.stdout)
        ok("live mode: HTTP staging is one site finding", lrep.count("not HTTPS") == 1)
        ok("live mode: same meta title finding", "| QA-76c273e5 | /about/ | SEO | MAJOR |" in lrep)

        # readers: Sources is not a section to check; addresses only near-misses
        sys.path.insert(0, str(HERE))
        import qa as Q  # noqa: E402
        a = Q.parse_article("## What we do\n\ntext\n\n## Sources\n\n- x\n")
        ok("Sources heading is not checked", a["H2"] == ["What we do"])
        ctx = Q.parse_context("- Phone: 503-555-0147 [intake]\n- Address: 2210 NE Alder Street, Portland [intake]\n- Owner cell 503-555-0999\n")
        ok("labelled contact lines win", ctx["phones"] == ["5035550147"])
        k = Q.addr_key("2210 Northeast Alder Street")
        ok("Northeast equals NE", k in ctx["addresses"], k + str(ctx["addresses"]))
        ok("unrelated number-street text ignored", not Q.near_miss(Q.addr_key("1998 Our Way"), ctx["addresses"]))
        ok("typo in house number caught", Q.near_miss(Q.addr_key("2201 NE Alder Street"), ctx["addresses"]))

        # unreachable staging stops and writes nothing
        u = tmp / "u"
        shutil.copytree(FIX / "base", u, ignore=shutil.ignore_patterns("staging"))
        r = run(u, "scan", "--slug", SLUG, "--base-url", "https://quillfeather.staging-wise.invalid", "--no-screens")
        ok("unreachable staging stops", r.returncode == 2 and "STOP" in r.stderr and not (u / "qa" / SLUG).exists(), r.stderr)
        r = run(tmp, "scan", "--slug", SLUG, "--base-url", BASE, "--saved", "x")
        ok("missing index stops", r.returncode == 2 and "dev-handoff-index" in r.stderr)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [x for x in results if not x[1]]
    for name, passed, detail in results:
        if not passed:
            print(f"FAIL {name}: {detail[:400]}")
    print(f"selftest_qa: {len(results) - len(bad)}/{len(results)} passed")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
