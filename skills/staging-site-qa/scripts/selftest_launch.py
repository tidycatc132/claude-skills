#!/usr/bin/env python3
"""Self-test for the launch check (qa.py scan/report/created --launch) on the invented Saltmarsh
Tree Care fixtures: saved pages with issues, a clean re-run, saved pages without a redirect file,
and a live run against a local server. No outside network.

Run from the repo root: python3 skills/staging-site-qa/scripts/selftest_launch.py
"""
from __future__ import annotations

import http.server
import json
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

HERE = Path(__file__).resolve().parent
QA = HERE / "qa.py"
REPO = HERE.parents[2]
FIX = REPO / "fixtures" / "staging-site-qa" / "saltmarsh"
SLUG = "saltmarsh-tree-care"
PROD = "https://saltmarshtreecare.com"
results = []


def run(cwd, *args):
    return subprocess.run([sys.executable, str(QA), *args], cwd=cwd, capture_output=True, text=True, timeout=120)


def ok(name, cond, detail=""):
    results.append((name, bool(cond), detail))


def workdir(tmp: Path, name: str) -> Path:
    w = tmp / name
    shutil.copytree(FIX / "base", w)
    for x in ("live", "live-clean"):
        shutil.copytree(FIX / x, w / x)
    for x in ("redirects.txt", "redirects-clean.txt"):
        shutil.copy(FIX / x, w / x)
    return w


def rows(text: str) -> list[str]:
    return [l for l in text.split("## Findings")[1].split("\n## ")[0].splitlines() if l.startswith("| QA-")]


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="sqa-launch-"))
    try:
        w = workdir(tmp, "a")
        qa = w / "qa" / SLUG
        r = run(w, "scan", "--launch", "--slug", SLUG, "--base-url", PROD, "--saved", "live",
                "--redirects-file", "redirects.txt", "--date", "2026-11-18")
        ok("launch scan exits 0", r.returncode == 0, r.stderr)
        ok("staging domain read from the staging QA report", "Staging" not in r.stderr)
        r = run(w, "report", "--launch", "--slug", SLUG)
        ok("launch report exits 0 and check passes", r.returncode == 0 and "CHECK PASS" in r.stdout, r.stdout + r.stderr)
        rep = (qa / f"{SLUG}-launch-check-2026-11-18.md").read_text()
        rr = rows(rep)
        ok("four findings", len(rr) == 4, "\n".join(rr))
        ok("noindex is a CRITICAL Development finding",
           any("| /services/tree-pruning/ | Development | CRITICAL | The page is still set to noindex" in l for l in rr))
        ok("canonical on staging is a finding",
           any("| /contact/ | Development | MAJOR | The canonical tag points at the staging domain" in l for l in rr))
        ok("missing redirect is a finding",
           any("| /trimming.html | Development | MAJOR |" in l and "does not redirect (HTTP 404)" in l for l in rr))
        ok("staging-domain image is a finding",
           any("| /services/tree-removal/ | Development | MAJOR |" in l and "crane-removal.webp" in l for l in rr))
        ok("result LIVE ISSUES", rep.strip().endswith("RESULT: LIVE ISSUES"))
        ok("tick list has the five lines", rep.count("\n- [ ] ") == 5 and "Juvo snippet installed" in rep)
        ok("redirect header line", "Redirects: 2 of 3 tested answer 301 or 308 to their New URL (from redirects.txt)" in rep)
        ok("NO TARGET row listed as not tested", "https://saltmarshtreecare.com/gallery/ not tested: NO TARGET" in rep)
        ok("structured data line once", rep.count("Structured data: not in the current process") == 1)
        ok("no launch toggles section", "## Launch Toggles" not in rep)
        tasks = json.loads((qa / f"{SLUG}-launch-bugherd-tasks.json").read_text())
        ok("tasks: four, all Development in Dev Ready, NEW and to create",
           len(tasks) == 4 and all(t["department"] == "Development" and t["column"] == "Dev Ready"
                                   and t["status"] == "NEW" and t["create"] for t in tasks))
        ok("task page_url on the live domain", tasks[0]["page_url"] == PROD + "/services/tree-pruning/")
        ok("staging task file untouched",
           (qa / f"{SLUG}-bugherd-tasks.json").read_text() == (FIX / "base" / "qa" / SLUG / f"{SLUG}-bugherd-tasks.json").read_text())
        r = run(w, "created", "--launch", "--slug", SLUG, *[f"{t['finding_id']}={900 + i}" for i, t in enumerate(tasks)])
        ok("created --launch records ids", r.returncode == 0 and "0 still to create" in r.stdout, r.stdout + r.stderr)
        r = run(w, "launch-check", str(qa / f"{SLUG}-launch-check-2026-11-18.md"))
        d = json.loads(r.stdout) if r.returncode == 0 else {}
        ok("launch-check reader", d.get("RESULT:") == "LIVE ISSUES" and d.get("Live:") == PROD
           and len(d.get("## Findings", [])) == 4 and d["tasks"][0]["bugherd_task_id"] == "900", r.stdout[:300] + r.stderr)

        # Re-run after fixes: clean site
        r = run(w, "scan", "--launch", "--slug", SLUG, "--base-url", PROD, "--saved", "live-clean",
                "--redirects-file", "redirects-clean.txt", "--date", "2026-11-19")
        r2 = run(w, "report", "--launch", "--slug", SLUG)
        ok("clean re-run passes check", r.returncode == 0 and r2.returncode == 0 and "CHECK PASS" in r2.stdout, r.stderr + r2.stdout + r2.stderr)
        rep2 = (qa / f"{SLUG}-launch-check-2026-11-19.md").read_text()
        ok("clean re-run LIVE OK", rep2.strip().endswith("RESULT: LIVE OK"))
        ok("clean re-run: 4 FIXED", "Re-run: 4 FIXED, 0 OPEN, 0 NEW" in rep2 and rep2.count("| FIXED |") == 4)
        ok("clean re-run: redirects 3 of 3", "Redirects: 3 of 3 tested answer 301 or 308" in rep2)
        t2 = json.loads((qa / f"{SLUG}-launch-bugherd-tasks.json").read_text())
        ok("FIXED tasks keep their ids, nothing to create",
           len(t2) == 4 and all(t["status"] == "FIXED" and t["bugherd_task_id"] and not t["create"] for t in t2))

        r = run(w, "report", "--launch", "--slug", SLUG)
        t3 = json.loads((qa / f"{SLUG}-launch-bugherd-tasks.json").read_text())
        ok("same-day second run keeps the BugHerd ids", r.returncode == 0 and [t["bugherd_task_id"] for t in t3] == [t["bugherd_task_id"] for t in t2], r.stdout)
        r = run(w, "scan", "--launch", "--slug", SLUG, "--base-url", PROD, "--saved", "live-clean",
                "--redirects-file", "redirects-clean.txt", "--date", "2026-11-20")
        r2 = run(w, "report", "--launch", "--slug", SLUG)
        ok("run after a clean run passes check", r2.returncode == 0 and "CHECK PASS" in r2.stdout, r2.stdout + r2.stderr)

        # Robots groups and duplicate robots metas
        import importlib.util
        spec = importlib.util.spec_from_file_location("launch", HERE / "launch.py")
        sys.path.insert(0, str(HERE))
        L = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(L)
        g = L.robots_groups("User-agent: Googlebot\nDisallow: /\n\nUser-agent: *\nAllow: /services/\n")
        ok("Googlebot's own group is tested on its own", any(L.robots_blocks(rs, "/services/x/") for _, rs in g))
        g = L.robots_groups("User-agent: *\nDisallow: /\n\nUser-agent: Googlebot\nAllow: /\n")
        ok("the * group is tested even when Googlebot is allowed", any(L.robots_blocks(rs, "/contact/") for _, rs in g))
        w2 = workdir(tmp, "e")
        pf = w2 / "live-clean" / "contact" / "index.html"
        pf.write_text(pf.read_text().replace('<meta name="robots" content="index, follow">',
                      '<meta name="robots" content="noindex">\n<meta name="robots" content="index, follow">'))
        run(w2, "scan", "--launch", "--slug", SLUG, "--base-url", PROD, "--saved", "live-clean",
            "--redirects-file", "redirects-clean.txt", "--date", "2026-11-19")
        run(w2, "report", "--launch", "--slug", SLUG)
        rep5 = (w2 / "qa" / SLUG / f"{SLUG}-launch-check-2026-11-19.md").read_text()
        ok("noindex in the first of two robots tags is found", "| /contact/ | Development | CRITICAL | The page is still set to noindex" in rep5)

        # Saved pages with no redirect file and no sitemap: says so instead of passing
        w = workdir(tmp, "b")
        (w / "live-clean" / "sitemap.xml").unlink()
        r = run(w, "scan", "--launch", "--slug", SLUG, "--base-url", PROD, "--saved", "live-clean", "--date", "2026-11-19")
        r2 = run(w, "report", "--launch", "--slug", SLUG)
        rep3 = (w / "qa" / SLUG / f"{SLUG}-launch-check-2026-11-19.md").read_text()
        ok("untested redirects and sitemap block LIVE OK",
           r2.returncode == 0 and rep3.strip().endswith("RESULT: LIVE ISSUES")
           and "could not run from the saved pages: 3 redirect(s) from the dev handoff index; sitemap.xml (not in the saved pages)" in rep3,
           rep3[-900:])
        ok("redirects header says not tested", "Redirects: not tested (saved pages, no redirect-response file); 3 in the index" in rep3)

        # Stops
        w = workdir(tmp, "c")
        (w / "qa" / SLUG / f"{SLUG}-staging-qa-2026-11-10.md").unlink()
        r = run(w, "scan", "--launch", "--slug", SLUG, "--base-url", PROD, "--saved", "live", "--redirects-file", "redirects.txt")
        ok("no staging domain: STOP", r.returncode != 0 and "STOP: the staging domain is not known" in r.stderr
           and not (w / "qa" / SLUG / f"{SLUG}-launch-scan.json").exists(), r.stderr)
        r = run(w, "scan", "--launch", "--slug", SLUG, "--base-url", "https://saltmarsh.staging-wise.site",
                "--staging-url", "https://saltmarsh.staging-wise.site", "--saved", "live")
        ok("staging URL as base: STOP", r.returncode != 0 and "is the staging site" in r.stderr, r.stderr)
        r = run(w, "scan", "--launch", "--slug", SLUG, "--base-url", PROD, "--staging-url", "saltmarsh.staging-wise.site",
                "--saved", "live", "--redirects-file", "redirects.txt", "--date", "2026-11-18")
        ok("--staging-url works without a staging report", r.returncode == 0, r.stderr)
        r = run(w, "scan", "--slug", SLUG, "--base-url", PROD, "--saved", "live", "--redirects-file", "redirects.txt")
        ok("launch-only flags refused on a staging scan", r.returncode != 0 and "scan --launch" in r.stderr, r.stderr)

        # Live run against a local server: robots blocks a page, X-Robots-Tag, redirects, sitemap gap
        w = workdir(tmp, "d")
        site = w / "live-clean"
        (site / "robots.txt").write_text("User-agent: *\nDisallow: /services/tree-pruning/\n")
        (site / "page-sitemap.xml").write_text(
            '<?xml version="1.0"?>\n<urlset><url><loc>https://saltmarshtreecare.com/</loc></url>'
            '<url><loc>https://saltmarshtreecare.com/services/tree-removal/</loc></url>'
            '<url><loc>https://saltmarsh.staging-wise.site/contact/</loc></url></urlset>\n')
        redirects = {"/our-services/": (301, PROD + "/services/tree-removal/"),
                     "/trimming.html": (302, "/services/tree-pruning/"),
                     "/contact-us/": (301, "/about/")}

        class H(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *a, **k):
                super().__init__(*a, directory=str(site), **k)

            def log_message(self, *a):
                pass

            def end_headers(self):
                if self.path.startswith("/contact/"):
                    self.send_header("X-Robots-Tag", "noindex")
                super().end_headers()

            def do_GET(self):
                if self.path in redirects:
                    code, loc = redirects[self.path]
                    self.send_response(code)
                    self.send_header("Location", loc)
                    self.end_headers()
                    return
                super().do_GET()

        srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{srv.server_address[1]}"
        try:
            r = run(w, "scan", "--launch", "--slug", SLUG, "--base-url", base, "--date", "2026-11-20")
            r2 = run(w, "report", "--launch", "--slug", SLUG)
        finally:
            srv.shutdown()
        ok("live scan and report pass check", r.returncode == 0 and r2.returncode == 0 and "CHECK PASS" in r2.stdout,
           r.stdout + r.stderr + r2.stdout + r2.stderr)
        rep4 = (w / "qa" / SLUG / f"{SLUG}-launch-check-2026-11-20.md").read_text()
        r4 = rows(rep4)
        ok("live: robots.txt blocking a Build page is CRITICAL",
           any("| /robots.txt | Development | CRITICAL | robots.txt blocks 1 Build page(s)" in l and "/services/tree-pruning/" in l for l in r4), "\n".join(r4))
        ok("live: X-Robots-Tag noindex found", any("| /contact/ | Development | CRITICAL | The page is still set to noindex" in l for l in r4))
        ok("live: 302 is a temporary-redirect finding", any("| /trimming.html |" in l and "temporary 302" in l for l in r4))
        ok("live: wrong target is a finding", any("| /contact-us/ |" in l and "not to /contact/" in l for l in r4))
        ok("live: 301 to the right page passes", not any("/our-services/" in l for l in r4))
        ok("live: sitemap gap and staging URL",
           any("| /sitemap.xml |" in l and "does not list 2 Build page(s): /services/tree-pruning/, /contact/" in l for l in r4)
           and any("| /sitemap.xml |" in l and "staging domain" in l for l in r4))
        ok("live: plain HTTP is a finding", any("| / | Development | MAJOR | The live site is served over HTTP" in l for l in r4))
        ok("live: redirects header", "Redirects: 1 of 3 tested answer 301 or 308 to their New URL" in rep4)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    passed = sum(1 for _, c, _ in results if c)
    for name, c, detail in results:
        if not c:
            print(f"FAIL {name}\n     {detail[:600]}")
    print(f"{passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
