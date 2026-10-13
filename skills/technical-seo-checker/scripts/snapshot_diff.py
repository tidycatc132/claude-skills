#!/usr/bin/env python3
"""Diff two technical-seo-snapshot/1 JSON files for the same URL and judge each change.

Usage
  python3 scripts/snapshot_diff.py before.json after.json [--out snapshot_diff.md] [--out-json snapshot_diff.json]

Both files follow the snapshot format in references/data-collection.md §10 (`schema`, `url`,
`captured_at`, `cwv.field.*`, `cwv.lab.*`, `http.*`, `indexability.*`, `scores.*`).

Rules: delta = after - before, shown as arithmetic, labeled Calculated. Core Web Vitals bands:
LCP good <= 2500 ms, needs improvement <= 4000, poor above; INP 200 / 500 ms; CLS 0.1 / 0.25;
TTFB 800 / 1800 ms. Verdict per metric: Improved, Regressed or Unchanged; lab values within
+/-10% are Unchanged (lab noise). Status, header and indexability fields report flips. Field
CrUX is a 28-day rolling p75, so the report says when the after capture is less than 28 days
after the before capture. Exit 0 on success, 2 on bad input. Standard library only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


def _beside(primary: str, default_name: str, given: str | None) -> str:
    """Default output path: next to the primary input file unless an explicit path was given."""
    if given is not None:
        return given
    return str(Path(primary).resolve().parent / default_name)

BANDS = {"lcp_ms": (2500, 4000), "inp_ms": (200, 500), "cls": (0.1, 0.25), "ttfb_ms": (800, 1800), "tbt_ms": (200, 600)}
LOWER_IS_BETTER = {"lcp_ms", "inp_ms", "cls", "ttfb_ms", "tbt_ms", "hops", "html_errors", "sample_non_indexable"}
HIGHER_IS_BETTER = {"perf_score", "crawlability", "indexability", "performance", "mobile", "security", "url_structure",
                    "structured_data", "international", "overall"}


def band(metric: str, v):
    if v is None or metric not in BANDS:
        return ""
    good, ni = BANDS[metric]
    return "Good" if v <= good else ("Needs Improvement" if v <= ni else "Poor")


def get(d: dict, path: str):
    cur = d
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def fmt(v):
    if v is None:
        return "null"
    if isinstance(v, float):
        return f"{v:g}"
    return str(v)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("before")
    ap.add_argument("after")
    ap.add_argument("--out", default=None, help="default: snapshot_diff.md next to the after snapshot")
    ap.add_argument("--out-json", default=None, help="default: snapshot_diff.json next to the after snapshot")
    args = ap.parse_args()
    args.out = _beside(args.after, "snapshot_diff.md", args.out)
    args.out_json = _beside(args.after, "snapshot_diff.json", args.out_json)
    try:
        b = json.loads(Path(args.before).read_text(encoding="utf-8"))
        a = json.loads(Path(args.after).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"snapshot_diff: {e}", file=sys.stderr)
        return 2
    for name, s in (("before", b), ("after", a)):
        if not str(s.get("schema", "")).startswith("technical-seo-snapshot/"):
            print(f"snapshot_diff: {name} snapshot has schema {s.get('schema')!r}, expected technical-seo-snapshot/1", file=sys.stderr)
            return 2
    if b.get("url") != a.get("url"):
        print(f"snapshot_diff: snapshots are for different URLs ({b.get('url')} vs {a.get('url')})", file=sys.stderr)
        return 2

    rows = []

    def numeric(field: str, path: str, lab: bool = False):
        bv, av = get(b, path), get(a, path)
        metric = path.rsplit(".", 1)[-1]
        if bv is None and av is None:
            return
        if bv is None or av is None:
            rows.append({"field": field, "before": fmt(bv), "after": fmt(av), "delta": "n/a", "band_change": "", "verdict": "Not comparable (one side null)"})
            return
        delta = av - bv
        pct = (delta / bv * 100) if bv else None
        bb, ab = band(metric, bv), band(metric, av)
        if lab and pct is not None and abs(pct) <= 10:
            verdict = "Unchanged (lab noise, within 10%)"
        elif delta == 0:
            verdict = "Unchanged"
        elif metric in LOWER_IS_BETTER:
            verdict = "Improved" if delta < 0 else "Regressed"
        elif metric in HIGHER_IS_BETTER:
            verdict = "Improved" if delta > 0 else "Regressed"
        else:
            verdict = "Changed"
        rows.append({"field": field, "before": fmt(bv), "after": fmt(av), "delta": f"{fmt(av)} - {fmt(bv)} = {fmt(round(delta, 4))}" + (f" ({pct:+.0f}%)" if pct is not None else ""),
                     "band_change": f"{bb} -> {ab}" if bb and ab and bb != ab else (bb or ""), "verdict": verdict})

    def flip(field: str, path: str, good_when=None):
        bv, av = get(b, path), get(a, path)
        if bv == av:
            rows.append({"field": field, "before": fmt(bv), "after": fmt(av), "delta": "", "band_change": "", "verdict": "Unchanged"})
            return
        verdict = "Changed"
        if good_when is not None:
            verdict = "Improved" if good_when(av) and not good_when(bv) else ("Regressed" if good_when(bv) and not good_when(av) else "Changed")
        rows.append({"field": field, "before": fmt(bv), "after": fmt(av), "delta": f"{fmt(bv)} -> {fmt(av)}", "band_change": "", "verdict": verdict})

    for m in ("lcp_ms", "inp_ms", "cls", "ttfb_ms"):
        numeric(f"field {m}", f"cwv.field.{m}")
    for m in ("lcp_ms", "cls", "tbt_ms", "ttfb_ms", "perf_score"):
        numeric(f"lab {m}", f"cwv.lab.{m}", lab=True)
    flip("http.final_status", "http.final_status", good_when=lambda v: v == 200)
    numeric("http.hops", "http.hops")
    flip("http.hsts", "http.hsts", good_when=lambda v: bool(v))
    flip("indexability.meta_robots", "indexability.meta_robots", good_when=lambda v: not v or "noindex" not in str(v).lower())
    flip("indexability.canonical", "indexability.canonical")
    flip("indexability.self_canonical", "indexability.self_canonical", good_when=lambda v: v is True)
    numeric("sitemap.sample_non_indexable", "sitemap.sample_non_indexable")
    numeric("html_errors", "html_errors")
    for s in ("crawlability", "indexability", "performance", "mobile", "security", "url_structure", "structured_data", "international", "overall"):
        numeric(f"score {s}", f"scores.{s}")

    notes = []
    try:
        d0 = datetime.fromisoformat(str(b.get("captured_at", "")).replace("Z", "+00:00"))
        d1 = datetime.fromisoformat(str(a.get("captured_at", "")).replace("Z", "+00:00"))
        days = (d1 - d0).days
        if days < 28:
            notes.append(f"Only {days} days between captures: field CrUX is a 28-day rolling p75, so field metrics show partial movement, not the full effect.")
    except ValueError:
        notes.append("captured_at could not be parsed on one snapshot; the 28-day CrUX caveat could not be checked.")
    notes.append("Lab values within +/-10% are reported Unchanged; for a firmer read run PSI three times and use the median.")
    notes.append("If other changes shipped in the same window, compare against an unchanged control URL and report delta-vs-control.")

    counts = {k: sum(1 for r in rows if r["verdict"].startswith(k)) for k in ("Improved", "Regressed", "Unchanged")}
    L = [f"## Before/after diff for {a.get('url')} (Calculated)", "",
         f"Before: {b.get('captured_at')} · After: {a.get('captured_at')} · sources: {', '.join(a.get('sources', []) or [])}", "",
         "| Field | Before | After | Delta | Band change | Verdict |", "|---|---:|---:|---|---|---|"]
    for r in rows:
        L.append(f"| {r['field']} | {r['before']} | {r['after']} | {r['delta']} | {r['band_change']} | {r['verdict']} |")
    L.append("")
    L.append(f"Summary: {counts['Improved']} improved, {counts['Regressed']} regressed, {counts['Unchanged']} unchanged.")
    for n in notes:
        L.append(f"- {n}")
    Path(args.out).write_text("\n".join(L) + "\n", encoding="utf-8")
    Path(args.out_json).write_text(json.dumps({"url": a.get("url"), "before": b.get("captured_at"), "after": a.get("captured_at"),
                                               "rows": rows, "counts": counts, "notes": notes, "label": "Calculated"}, indent=2) + "\n", encoding="utf-8")
    print(f"{len(rows)} fields compared: improved={counts['Improved']} regressed={counts['Regressed']} unchanged={counts['Unchanged']}; wrote {args.out} and {args.out_json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
