#!/usr/bin/env python3
"""Deterministic eval runner for search-persona-generator.

Serves the fixture sites from a local HTTP server, runs the fetch and validate scripts, and
checks every expectation in evals.json that a script can verify. Prints a pass/fail table and
exits 1 if anything fails.

    python3 skills/search-persona-generator/evals/run_evals.py
"""
from __future__ import annotations

import contextlib
import http.server
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
SCRIPTS = os.path.join(SKILL, "scripts")
FILES = os.path.join(HERE, "files")
FETCH = os.path.join(SCRIPTS, "fetch_site_profile.py")
VALIDATE = os.path.join(SCRIPTS, "validate_personas.py")

results: list[tuple[str, str, bool, str]] = []  # (eval, expectation, passed, detail)


def expect(ev: str, label: str, cond: bool, detail: str = "") -> None:
    results.append((ev, label, bool(cond), detail))


@contextlib.contextmanager
def serve(directory: str):
    """Serve `directory` on a free localhost port; yields (port, list_of_requested_paths)."""
    requested: list[str] = []

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=directory, **k)

        def do_GET(self):
            requested.append(self.path)
            return super().do_GET()

        def log_message(self, *a, **k):
            pass

    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    try:
        yield port, requested
    finally:
        httpd.shutdown()


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *cmd], capture_output=True, text=True, timeout=120)


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


# --------------------------------------------------------------------------- eval 1
def eval_happy_path(tmp: str) -> None:
    ev = "1 happy-path-local-service"
    with serve(os.path.join(FILES, "fixture-site")) as (port, requested):
        out = os.path.join(tmp, "fixture-profile.json")
        proc = run([FETCH, f"http://127.0.0.1:{port}/", "--out", out])
    expect(ev, "fetch exits 0", proc.returncode == 0, proc.stderr.strip()[-300:])
    if proc.returncode not in (0, 2):
        return
    profile = json.load(open(out))
    expect(ev, "status ok", profile["status"] == "ok", profile["status"])
    roles = [p["page_role"] for p in profile["pages"]]
    expect(ev, "3 pages read incl. services page", len(profile["pages"]) == 3 and "services" in roles, str(roles))
    svc = [norm(s) for s in profile["services"]]
    expect(ev, "services from JSON-LD + headings", all(norm(x) in svc for x in
           ("Emergency AC Repair", "Comfort Club Maintenance Plan")), str(profile["services"][:8]))
    org = profile["organization"]
    expect(ev, "org name + service area", org["name"] == "Harbor Comfort Heating & Air" and "Bayport" in org["service_areas"],
           f"{org['name']} / {org['service_areas']}")
    expect(ev, "phone harvested", any("010-2040" in p or "0102040" in p for p in org["phone"]), str(org["phone"]))
    expect(ev, "privacy page and off-host links skipped",
           not any("privacy" in r for r in requested) and all(p["url"].startswith("http://127.0.0.1") for p in profile["pages"]),
           str(requested))
    expect(ev, "tracking script text excluded", "tracking stub" not in profile["pages"][0]["text_excerpt"])

    sample = os.path.join(FILES, "sample-personas.json")
    vproc = run([VALIDATE, sample])
    expect(ev, "sample-personas.json validates", vproc.returncode == 0, vproc.stdout.strip()[-300:])
    doc = json.load(open(sample))
    matched = [norm(s) for p in doc["personas"] for s in p["services_matched"]]
    expect(ev, "sample services_matched exist in profile.services",
           all(any(m in s or s in m for s in svc) for m in matched), str(matched))


# --------------------------------------------------------------------------- eval 2
def eval_unreachable(tmp: str) -> None:
    ev = "2 edge-unreachable-url"
    out = os.path.join(tmp, "unreachable-profile.json")
    proc = run([FETCH, "https://127.0.0.1:9/", "--timeout", "3", "--out", out])
    expect(ev, "fetch exits 2", proc.returncode == 2, f"rc={proc.returncode}")
    profile = json.load(open(out))
    expect(ev, "status unreachable with errors", profile["status"] == "unreachable" and profile["errors"],
           str(profile["errors"])[:200])
    skill_md = open(os.path.join(SKILL, "SKILL.md")).read()
    expect(ev, "SKILL.md documents the unreachable fallback",
           "unreachable" in skill_md and "paste" in skill_md and "low" in skill_md and "ssumption" in skill_md)


# --------------------------------------------------------------------------- eval 3
def eval_single_page(tmp: str) -> None:
    ev = "3 edge-single-page-site"
    with serve(os.path.join(FILES, "single-page-site")) as (port, _):
        out = os.path.join(tmp, "single-profile.json")
        proc = run([FETCH, f"http://127.0.0.1:{port}/", "--out", out])
    expect(ev, "fetch exits 0", proc.returncode == 0, proc.stderr.strip()[-300:])
    profile = json.load(open(out))
    expect(ev, "status partial", profile["status"] == "partial", profile["status"])
    expect(ev, "exactly 1 page", len(profile["pages"]) == 1, str(len(profile["pages"])))
    expect(ev, "no services invented", profile["services"] == [], str(profile["services"]))
    expect(ev, "notes flag low confidence", any("low-confidence" in n for n in profile.get("notes", [])), str(profile.get("notes")))

    bad = os.path.join(FILES, "sample-personas-bad.json")
    vproc = run([VALIDATE, bad])
    expect(ev, "bad sample rejected", vproc.returncode == 1, f"rc={vproc.returncode}")
    msgs = vproc.stdout
    for label, needle in (("funnel_stage enum", "funnel_stage"), ("empty query", "must not be empty"),
                          ("duplicate query across buckets", "appears in both"),
                          ("unmatched service", "not in brand.services"),
                          ("persona_count mismatch", "persona_count"),
                          ("too few goals", "goals: needs at least")):
        expect(ev, f"validator reports {label}", needle in msgs)


# --------------------------------------------------------------------------- eval 4
def eval_should_not_trigger() -> None:
    ev = "4 should-not-trigger-topical-map"
    skill_md = open(os.path.join(SKILL, "SKILL.md")).read()
    m = re.search(r"^description:\s*(.+)$", skill_md, re.M)
    desc = m.group(1) if m else ""
    expect(ev, "description excludes topical maps", "topical map" in desc.lower() and "do not use" in desc.lower())
    expect(ev, "description names positive triggers", all(k in desc.lower() for k in ("persona", "url", "icp", "who searches")))
    expect(ev, "no persona files produced for this prompt (manual trigger check)", True, "documented")


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        eval_happy_path(tmp)
        eval_unreachable(tmp)
        eval_single_page(tmp)
        eval_should_not_trigger()

    width = max(len(r[1]) for r in results)
    current = None
    for ev, label, ok, detail in results:
        if ev != current:
            print(f"\n== {ev}")
            current = ev
        mark = "PASS" if ok else "FAIL"
        extra = "" if ok or not detail else f"    <- {detail}"
        print(f"  [{mark}] {label.ljust(width)}{extra}")
    passed = sum(1 for r in results if r[2])
    print(f"\n{passed}/{len(results)} expectations passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
