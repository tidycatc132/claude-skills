#!/usr/bin/env python3
"""Self-test for golive_email.py on the saved Quillfeather Plumbing fixtures.

Run from the repository root: python3 skills/week-6-go-live-email/scripts/selftest_golive_email.py
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SCRIPT = HERE / "golive_email.py"
FX = ROOT / "fixtures" / "week-6-go-live-email" / "quillfeather"
DRAFTS = ROOT / "fixtures" / "week-6-go-live-email" / "drafts"
SLUG = "quillfeather-plumbing"
EMAIL = Path(f"emails/{SLUG}/{SLUG}-go-live-email.md")

passed = failed = 0


def ok(cond: bool, label: str, detail: str = "") -> None:
    global passed, failed
    if cond:
        passed += 1
    else:
        failed += 1
        print(f"FAIL {label}" + (f": {detail}" if detail else ""))


def folder(handoff: str | None) -> Path:
    d = Path(tempfile.mkdtemp(prefix="golive-"))
    shutil.copytree(FX / "common", d, dirs_exist_ok=True)
    if handoff:
        shutil.copytree(FX / handoff, d, dirs_exist_ok=True)
    return d


def run(d: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=d, capture_output=True, text=True)


def put(d: Path, draft: str) -> None:
    (d / EMAIL).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(DRAFTS / draft, d / EMAIL)


def main() -> int:
    good_opts = ["--slug", SLUG, "--integrations", "the contact form and Google Analytics"]

    # GO handoff, good draft: passes, no warning written
    d = folder("go")
    p = run(d, "facts", *good_opts)
    ok(p.returncode == 0, "facts runs", p.stderr)
    ok("Warnings: none" in p.stdout, "GO: no warnings")
    ok("Pages launching: 5 (Homepage 1, Service Pages 2, About Page 1, Contact Page 1)" in p.stdout, "Build pages only, by group")
    ok("Not in this launch (do not count or name): Winter Pipe Guide" in p.stdout, "Post-Launch page held back")
    ok("To: Ade Okafor" in p.stdout, "contact parsed without its role and source")
    ok("Integrations: contact form, Google Analytics" in p.stdout, "integrations split and articles dropped")
    ok("Account Manager, WISE Digital Partners" in p.stdout, "default sign-off")
    put(d, "quillfeather-plumbing-go-live-email-good.md")
    p = run(d, "check", *good_opts)
    ok(p.returncode == 0, "good draft passes", p.stdout)
    ok(not (d / EMAIL).read_text().startswith("WARNING"), "GO: no warning at the top")

    # Bad draft: the specific rules fail, and the stale warning is removed
    put(d, "quillfeather-plumbing-go-live-email-bad.md")
    p = run(d, "check", *good_opts)
    ok(p.returncode == 1, "bad draft fails")
    for label in ["total page count 5 stated", "page numbers match", "no page outside this launch named",
                  "no unnamed integration (live chat)", "no structured data or schema claim", "no internal terms",
                  "no links", "greeting 'Hi Ade,'", "sign-off", "after launch: we watch indexing",
                  "monthly work starts after launch", "asks the client to confirm"]:
        ok(f"FAIL  {label}" in p.stdout, f"bad draft: {label} fails", p.stdout)
    ok("FAIL  no internal terms (found: QA, BugHerd, MAJOR, GO, deferred)" in p.stdout, "internal terms listed")
    ok(not (d / EMAIL).read_text().startswith("WARNING"), "stale warning removed on a GO handoff")

    # Unnamed integration: the good draft names analytics, so with only forms named it fails
    put(d, "quillfeather-plumbing-go-live-email-good.md")
    p = run(d, "check", "--slug", SLUG, "--integrations", "contact form")
    ok("FAIL  no unnamed integration (analytics)" in p.stdout, "analytics not named -> fails", p.stdout)
    p = run(d, "check", "--slug", SLUG)
    ok("FAIL  no unnamed integration (forms)" in p.stdout, "nothing named -> forms fail", p.stdout)

    # Agreed launch date, PM sender
    p = run(d, "facts", "--slug", SLUG, "--launch", "2026-11-24 10:00", "--sender", "Jordan Vale", "--role", "Project Manager")
    ok("Launch: 2026-11-24 10:00" in p.stdout, "launch header")
    ok("Tuesday, November 24 at 10:00" in p.stdout, "launch written out")
    ok("Jordan Vale / Project Manager, WISE Digital Partners" in p.stdout, "named sign-off")
    p = run(d, "check", "--slug", SLUG, "--launch", "2026-11-24", "--integrations", "contact form, Google Analytics")
    ok("FAIL  agreed launch date 'Tuesday, November 24' stated" in p.stdout, "agreed date missing -> fails")
    ok("FAIL  header line 'Launch: 2026-11-24'" in p.stdout, "launch header mismatch -> fails")
    good = (DRAFTS / "quillfeather-plumbing-go-live-email-good.md").read_text()
    dated = good.replace("Launch: client to confirm", "Launch: 2026-11-24 10:00").replace(
        "Can you confirm you are ready for us to launch? Reply with a yes and we will set the day and time with you.",
        "We go live on Tuesday, November 24 at 10am, as agreed.")
    (d / EMAIL).write_text(dated)
    opts = ["--slug", SLUG, "--launch", "2026-11-24 10:00", "--integrations", "contact form, Google Analytics"]
    p = run(d, "check", *opts)
    ok("PASS  agreed launch time 10:00 stated" in p.stdout and p.returncode == 0, "10am accepted for 10:00", p.stdout)
    (d / EMAIL).write_text(dated.replace("at 10am", "at 2pm"))
    p = run(d, "check", *opts)
    ok("FAIL  agreed launch time 10:00 stated" in p.stdout, "wrong launch time fails")
    (d / EMAIL).write_text(good.replace("we check every page on the live site", "we look at the live site"))
    p = run(d, "check", *good_opts)
    ok("FAIL  after launch: we check every page" in p.stdout, "recap's 'all 5 pages' does not satisfy the page check")
    idx = d / f"handoff/{SLUG}/{SLUG}-dev-handoff-index.md"
    keep = idx.read_text()
    idx.write_text(keep.rstrip().rsplit("\n", 1)[0] + "\nNO-GO\n")
    p = run(d, "facts", *good_opts)
    ok("does not end GO, so some Build pages may not be ready" in p.stdout, "index NO-GO warns")
    idx.write_text(keep)
    p = run(d, "facts", "--slug", SLUG, "--launch", "next Tuesday")
    ok(p.returncode == 2 and "--launch must be" in p.stderr, "bad launch value stops")
    shutil.rmtree(d)

    # NO-GO handoff: warning written above the header, draft otherwise passes
    d = folder("no-go")
    put(d, "quillfeather-plumbing-go-live-email-good.md")
    p = run(d, "check", *good_opts)
    text = (d / EMAIL).read_text()
    ok(text.startswith("WARNING: The Week 5 handoff ends NO-GO (checked 2026-11-17, 4 blocking items)."), "NO-GO warning at the top", text[:200])
    ok("Lorem" not in text and "BugHerd" not in text, "blocking items not copied into the file")
    ok("FAIL  header line 'Week 5 handoff: handoff/quillfeather-plumbing/quillfeather-plumbing-week-5-handoff.md (NO-GO)'" in p.stdout,
       "header must name NO-GO")
    run(d, "check", *good_opts)
    ok((d / EMAIL).read_text().count("WARNING:") == 1, "warning not duplicated on a re-run")
    shutil.rmtree(d)

    # Missing handoff
    d = folder(None)
    p = run(d, "facts", *good_opts)
    ok("WARNING: No Week 5 handoff at handoff/quillfeather-plumbing/quillfeather-plumbing-week-5-handoff.md" in p.stdout, "missing handoff warning")
    ok(f"Week 5 handoff: handoff/{SLUG}/{SLUG}-week-5-handoff.md (missing)" in p.stdout, "missing in header")
    # Missing index stops
    (d / f"handoff/{SLUG}/{SLUG}-dev-handoff-index.md").unlink()
    p = run(d, "facts", *good_opts)
    ok(p.returncode == 2 and "dev-handoff-index" in p.stderr, "missing index stops")
    shutil.rmtree(d)

    # Unknown contact
    d = folder("go")
    ctx = d / f"kickoff/{SLUG}/{SLUG}-context.md"
    ctx.write_text("\n".join(ln for ln in ctx.read_text().split("\n") if "Primary contact" not in ln))
    p = run(d, "facts", *good_opts)
    ok("Contact: unknown (ask the PM" in p.stdout, "unknown contact asks the PM")
    p = run(d, "facts", *good_opts, "--contact", "Ade Okafor")
    ok("To: Ade Okafor" in p.stdout, "--contact fills it")
    shutil.rmtree(d)

    # Producer drift: the Week 5 handoff the producer writes today still reads as GO
    producer = ROOT / "skills" / "week-5-handoff-check" / "scripts" / "week5_handoff.py"
    outputs = ROOT / "evals" / "week-5-handoff-check" / "outputs.json"
    if producer.exists() and outputs.exists():
        case = next(c for c in json.loads(outputs.read_text())["cases"] if c["id"] == "quillfeather-no-reply-go")
        d = Path(tempfile.mkdtemp(prefix="golive-producer-"))
        for f in case["fixtures"]:
            dst = d / f["dest"]
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(ROOT / f["src"], dst)
        subprocess.run([sys.executable, str(producer), "run", "--slug", SLUG, "--today", "2026-11-17", "--pm", "Jordan Vale"],
                       cwd=d, capture_output=True, text=True)
        made = (d / f"handoff/{SLUG}/{SLUG}-week-5-handoff.md").read_text()
        saved = (ROOT / "fixtures/contracts/week-6-go-live-email-sample/quillfeather-plumbing-week-5-handoff.md").read_text()
        ok(made == saved, "week-5-handoff-check still writes the saved handoff byte for byte")
        p = run(d, "contract", "handoff", f"handoff/{SLUG}/{SLUG}-week-5-handoff.md")
        ok(json.loads(p.stdout)["GO"] is True, "producer's GO handoff reads as GO")
        shutil.rmtree(d)
    else:
        ok(False, "week-5-handoff-check producer present")

    print(f"{passed}/{passed + failed} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
