#!/usr/bin/env python3
"""Self-test for tracking.py on the invented fixtures (Fernwick Pest Control, Oakmere Bookkeeping).

Run from the repo root: python3 skills/ga4-event-tracking/scripts/selftest_tracking.py
"""
from __future__ import annotations

import http.server
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "tracking.py"
ROOT = HERE.parents[2]
FX = ROOT / "fixtures" / "ga4-event-tracking"
FW = "fernwick-pest-control"
OK = "oakmere-bookkeeping"
passed = failed = 0


def run(cwd: Path, *args: str) -> tuple[int, str]:
    p = subprocess.run([sys.executable, str(SCRIPT), *args], cwd=cwd, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def expect(cond: bool, label: str) -> None:
    global passed, failed
    if cond:
        passed += 1
    else:
        failed += 1
        print(f"FAIL {label}")


def tree(*parts: str) -> Path:
    d = Path(tempfile.mkdtemp(prefix="ga4-selftest-"))
    for part in parts:
        src = FX / part
        shutil.copytree(src, d, dirs_exist_ok=True)
    return d


def main() -> int:
    # 1. plan + check on a full index with a launch check
    d = tree("fernwick/base")
    rc, out = run(d, "plan", "--slug", FW, "--measurement-id", "G-7QX3LM2K9P", "--gtm-id", "GTM-W4K8P2Q", "--date", "2026-11-13")
    expect(rc == 0 and "WARNING" not in out, "plan runs clean")
    plan = (d / f"tracking/{FW}/{FW}-tracking-plan.md").read_text()
    cont = json.loads((d / f"tracking/{FW}/{FW}-gtm-container.json").read_text())
    expect(plan == (FX / f"fernwick/planned/tracking/{FW}/{FW}-tracking-plan.md").read_text(), "plan matches the recorded fixture")
    tags = cont["containerVersion"]["tag"]
    names = sorted(t["parameter"][1]["value"] for t in tags if t["type"] == "gaawe")
    expect(names == ["click_to_call", "click_to_email", "cta_click", "generate_lead", "get_directions"], "five events")
    expect(any(t["type"] == "googtag" for t in tags), "google tag present")
    expect(all(any("fernwickpest" in json.dumps(f) for f in t.get("filter", [])) for t in cont["containerVersion"]["trigger"]), "hostname guard on every trigger")
    rc, out = run(d, "check", "--slug", FW)
    expect(rc == 0 and "RESULT: PASS" in out, "check passes")
    trigs = {t["triggerId"]: t for t in cont["containerVersion"]["trigger"]}
    gt = next(t for t in tags if t["type"] == "googtag")
    expect(trigs.get(gt["firingTriggerId"][0], {}).get("type") == "INIT", "google tag on the guarded INIT trigger")
    form = next(t for t in trigs.values() if t["type"] == "FORM_SUBMISSION")
    expect('"^(/contact)/?$"' in json.dumps(form), "form trigger limited to the contact form page")
    g2 = json.loads(json.dumps(cont))
    for t in g2["containerVersion"]["tag"]:
        if t["type"] == "googtag":
            t["firingTriggerId"] = ["2147479573"]
    cp0 = d / f"tracking/{FW}/{FW}-gtm-container.json"
    keep = cp0.read_text()
    cp0.write_text(json.dumps(g2))
    rc, out = run(d, "check", "--slug", FW)
    expect(rc == 1 and "live-only Initialization" in out, "check catches an unguarded Google tag")
    cp0.write_text(keep)
    # tamper: drop a tag -> check fails
    cpath = d / f"tracking/{FW}/{FW}-gtm-container.json"
    bad = json.loads(cpath.read_text())
    bad["containerVersion"]["tag"] = [t for t in bad["containerVersion"]["tag"] if "cta_click" not in t["name"]]
    cpath.write_text(json.dumps(bad))
    rc, out = run(d, "check", "--slug", FW)
    expect(rc == 1 and "same events" in out, "check catches a missing tag")
    bad["containerVersion"]["variable"][0]["parameter"][0]["value"] = "G-OTHER123"
    cpath.write_text(json.dumps(bad))
    rc, out = run(d, "check", "--slug", FW)
    expect(rc == 1 and "matches the plan" in out, "check catches a changed Measurement ID")

    # 2. stops
    d2 = tree("fernwick/base")
    rc, out = run(d2, "plan", "--slug", FW)
    expect(rc == 2 and "Measurement ID" in out and not (d2 / "tracking").exists(), "no Measurement ID stops and writes nothing")
    rc, out = run(d2, "plan", "--slug", FW, "--measurement-id", "UA-12345-1")
    expect(rc == 2 and "not a GA4 Measurement ID" in out, "UA id refused")
    rc, out = run(d2, "plan", "--slug", FW, "--measurement-id", "G-7QX3LM2K9P", "--gtm-id", "W4K8P2Q")
    expect(rc == 2 and "GTM container ID" in out, "bad GTM id refused")
    rc, out = run(d2, "plan", "--slug", FW, "--measurement-id", "G-7QX3LM2K9P", "--thank-you", "/")
    expect(rc == 2 and "homepage" in out, "homepage as thank-you page refused")
    rc, out = run(d2, "plan", "--slug", "nobody", "--measurement-id", "G-7QX3LM2K9P")
    expect(rc == 2 and "dev-handoff-index" in out, "missing index stops")

    # 3. thank-you, no google tag, no contact page, no analytics section, live from --site
    d3 = tree("oakmere")
    rc, out = run(d3, "plan", "--slug", OK, "--measurement-id", "g-2bn8tr41vw", "--site", "oakmerebooks.co.uk",
                  "--thank-you", "https://oakmerebooks.co.uk/thank-you/", "--no-google-tag")
    p3 = (d3 / f"tracking/{OK}/{OK}-tracking-plan.md").read_text()
    c3 = (d3 / f"tracking/{OK}/{OK}-gtm-container.json").read_text()
    expect("Measurement ID: G-2BN8TR41VW" in p3, "id upper-cased")
    expect("Lead event: thank-you page /thank-you/" in p3 and "PAGEVIEW" in c3, "thank-you mode")
    expect("googtag" not in c3 and "already on the site" in p3, "no google tag")
    expect("`cta_click`" not in p3 and "no Contact Page" in p3, "no cta_click without contact page")
    expect("Analytics and tracking" in out, "warns about missing analytics section")
    rc, out = run(d3, "check", "--slug", OK)
    expect(rc == 0, "check passes on oakmere")

    # 4. no live address -> warning, no guard
    d4 = tree("fernwick/base")
    shutil.rmtree(d4 / "qa")
    rc, out = run(d4, "plan", "--slug", FW, "--measurement-id", "G-7QX3LM2K9P")
    p4 = (d4 / f"tracking/{FW}/{FW}-tracking-plan.md").read_text()
    expect("Live: unknown" in p4 and "staging visits will be counted" in p4, "no live address warns")
    rc, out = run(d4, "check", "--slug", FW)
    expect(rc == 0, "check passes without a live address")
    rc, out = run(d4, "site", "--plan", f"tracking/{FW}/{FW}-tracking-plan.md", "--gtm-id", "GTM-W4K8P2Q")
    expect(rc == 2 and "no live address" in out, "site without live address or saved pages stops")

    # 5. site check, saved pages
    d5 = tree("fernwick/base", "fernwick/planned")
    shutil.copytree(FX / "fernwick/live", d5 / "live")
    shutil.copytree(FX / "fernwick/live-clean", d5 / "live-clean")
    rc, out = run(d5, "site", "--plan", f"tracking/{FW}/{FW}-tracking-plan.md", "--saved", "live", "--date", "2026-11-14")
    r5 = (d5 / f"tracking/{FW}/{FW}-tracking-check-2026-11-14.md").read_text()
    expect(r5.rstrip().endswith("RESULT: TRACKING ISSUES"), "issues result")
    expect("| Termite Treatment | /services/termite-treatment/ | no |" in r5, "missing container")
    expect("| Rodent Control | /services/rodent-control/ | yes | yes |" in r5, "doubled GA4")
    expect("no <form> element" in r5, "iframe form")
    expect(r5.count("\n| ") == 7, "header and six page rows")
    rc, out = run(d5, "site", "--plan", f"tracking/{FW}/{FW}-tracking-plan.md", "--saved", "live-clean", "--date", "2026-11-15")
    r6 = (d5 / f"tracking/{FW}/{FW}-tracking-check-2026-11-15.md").read_text()
    expect(r6.rstrip().endswith("RESULT: TRACKING OK") and "- none" in r6, "clean site OK")
    rc, out = run(d5, "site", "--plan", f"tracking/{FW}/{FW}-tracking-plan.md", "--saved", "nowhere", "--date", "2026-11-16")
    r7 = (d5 / f"tracking/{FW}/{FW}-tracking-check-2026-11-16.md").read_text()
    expect("not saved" in r7 and "TRACKING ISSUES" in r7, "unsaved pages are issues")
    # tel written another way on the page still matches the index
    alt = d5 / "live-alt"
    shutil.copytree(FX / "fernwick/live-clean", alt)
    for f in alt.rglob("index.html"):
        f.write_text(f.read_text().replace('href="tel:+19785550147"', 'href="tel:978-555-0147"').replace('mailto:office@fernwickpest.com"', 'mailto:office@fernwickpest.com?subject=Inspection"'))
    rc, out = run(d5, "site", "--plan", f"tracking/{FW}/{FW}-tracking-plan.md", "--saved", "live-alt", "--date", "2026-11-19")
    r10 = (d5 / f"tracking/{FW}/{FW}-tracking-check-2026-11-19.md").read_text()
    expect("## Notes\n\n- none" in r10 and "3 of 3" in r10, "tel and mailto variants match")
    # wrong GTM id given
    rc, out = run(d5, "site", "--plan", f"tracking/{FW}/{FW}-tracking-plan.md", "--saved", "live-clean", "--gtm-id", "GTM-ZZZZ999", "--date", "2026-11-17")
    r8 = (d5 / f"tracking/{FW}/{FW}-tracking-check-2026-11-17.md").read_text()
    expect("found GTM-W4K8P2Q instead" in r8, "wrong container reported")

    # 6. site check, live over a local server
    srv_root = FX / "fernwick/live-clean"
    handler = lambda *a, **k: http.server.SimpleHTTPRequestHandler(*a, directory=str(srv_root), **k)  # noqa: E731
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        d6 = tree("fernwick/base")
        rc, out = run(d6, "plan", "--slug", FW, "--measurement-id", "G-7QX3LM2K9P", "--gtm-id", "GTM-W4K8P2Q",
                      "--site", f"http://127.0.0.1:{httpd.server_address[1]}")
        os.environ.pop("HTTPS_PROXY", None)
        env_run = subprocess.run([sys.executable, str(SCRIPT), "site", "--plan", f"tracking/{FW}/{FW}-tracking-plan.md", "--date", "2026-11-18"],
                                 cwd=d6, capture_output=True, text=True,
                                 env={**os.environ, "NO_PROXY": "127.0.0.1", "no_proxy": "127.0.0.1"})
        r9 = (d6 / f"tracking/{FW}/{FW}-tracking-check-2026-11-18.md").read_text()
        expect(r9.rstrip().endswith("RESULT: TRACKING OK"), "live run over HTTP is OK: " + env_run.stdout[-200:])
    finally:
        httpd.shutdown()

    print(f"selftest_tracking: {passed}/{passed + failed} passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
