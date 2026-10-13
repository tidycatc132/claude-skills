#!/usr/bin/env python3
"""Score a completed CORE-EEAT item sheet (80 items) and write the result + report.

Usage
  python3 scripts/score_eeat.py --template eeat_items.json [--profile P] [--target T] [--market M]
                                 [--publication-state S] [--observed-at YYYY-MM-DD]
      Write a skeleton sheet: every one of the 80 items set to "unknown". Fill it in, then score it.

  python3 scripts/score_eeat.py eeat_items.json [--out-json eeat_result.json] [--out-md eeat_report.md]
      Apply the scoring contract (references/scoring-rules.md) to the sheet and write
      `eeat_result.json` (machine-readable) and `eeat_report.md` (typed header + tables).

Input sheet (`eeat_items.json`)
  {
    "target": "https://example.com/page", "profile": "product-review", "market": "US",
    "publication_state": "live", "observed_at": "2026-10-12",
    "execution_blocked": false, "blocked_reason": "",
    "items": {
      "C01": {"state": "pass", "evidence_type": "measured", "confidence": "high",
              "source": "rendered page", "source_date": "2026-10-12", "note": "..."},
      "E02": {"state": "na", "reason": "no framework claimed"},
      ...
    }
  }
  state: pass | partial | fail | unknown | na (na only for the 18 conditional items)
  evidence_type: measured | user-provided | calculated | estimated | proxy
  confidence: high | medium | low
  A missing item is scored as unknown. Observed items without evidence_type/confidence are
  treated as estimated/low (never rounded up) and listed under warnings.

Exit codes: 0 scored, 2 invalid sheet (message on stderr). Standard library only.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path


def _beside(primary: str, default_name: str, given: str | None) -> str:
    """Default output path: next to the primary input file unless an explicit path was given."""
    if given is not None:
        return given
    return str(Path(primary).resolve().parent / default_name)

CATALOG_VERSION = "20.1.0"
RUNBOOK_VERSION = "3.0.0"
SCHEMA_VERSION = "3.0"

DIMS = ["C", "O", "R", "E", "Exp", "Ept", "A", "T"]
DIM_NAMES = {
    "C": "Contextual Clarity", "O": "Organization", "R": "Referenceability", "E": "Exclusivity",
    "Exp": "Experience", "Ept": "Expertise", "A": "Authority", "T": "Trust",
}
ITEM_NAMES = {
    "C": ["Intent Alignment", "Direct Answer", "Query Coverage", "Definition First", "Topic Scope",
          "Audience Targeting", "Semantic Coherence", "Use Case Mapping", "FAQ Coverage", "Semantic Closure"],
    "O": ["Heading Hierarchy", "Summary Box", "Data Tables", "List Formatting", "Schema Markup",
          "Section Chunking", "Visual Hierarchy", "Anchor Navigation", "Information Density", "Multimedia Structure"],
    "R": ["Data Precision", "Citation Density", "Source Hierarchy", "Evidence-Claim Mapping",
          "Methodology Transparency", "Timestamp & Versioning", "Entity Precision", "Internal Link Graph",
          "HTML Semantics", "Content Consistency"],
    "E": ["Original Data", "Novel Framework", "Primary Research", "Contrarian View", "Proprietary Visuals",
          "Gap Filling", "Practical Tools", "Depth Advantage", "Synthesis Value", "Forward Insights"],
    "Exp": ["First-Person Narrative", "Sensory Details", "Process Documentation", "Tangible Proof",
            "Usage Duration", "Problems Encountered", "Before/After Comparison", "Quantified Metrics",
            "Repeated Testing", "Limitations Acknowledged"],
    "Ept": ["Author Identity", "Credentials Display", "Professional Vocabulary", "Technical Depth",
            "Methodology Rigor", "Edge Case Awareness", "Historical Context", "Reasoning Transparency",
            "Cross-domain Integration", "Editorial Process"],
    "A": ["Backlink Profile", "Media Mentions", "Industry Awards", "Publishing Record", "Brand Recognition",
          "Social Proof", "Knowledge Graph Presence", "Entity Consistency", "Partnership Signals", "Community Standing"],
    "T": ["Legal Compliance", "Contact Transparency", "Security Standards", "Disclosure Statements",
          "Editorial Policy", "Correction & Update Policy", "Ad Experience", "Risk Disclaimers",
          "Review Authenticity", "Customer Support"],
}
ALL_IDS = [f"{d}{i:02d}" for d in DIMS for i in range(1, 11)]
CONDITIONAL = {"O03", "O05", "O10", "E01", "E02", "E03", "E04", "E05", "E10", "Exp01", "Exp02", "Exp04",
               "Exp05", "Exp07", "Exp09", "A07", "T04", "T08"}
VETOES = ["C01", "R10", "T04"]
STATES = {"pass": 10, "partial": 5, "fail": 0}
EVIDENCE_WEIGHT = {"measured": 1.0, "user-provided": 0.8, "calculated": 0.8, "estimated": 0.5, "proxy": 0.4}
CONFIDENCE_FACTOR = {"high": 1.0, "medium": 0.75, "low": 0.5}
PROFILES = {
    "product-review": [0.10, 0.10, 0.15, 0.20, 0.20, 0.05, 0.05, 0.15],
    "how-to-guide":   [0.20, 0.20, 0.10, 0.05, 0.05, 0.20, 0.05, 0.15],
    "comparison":     [0.10, 0.20, 0.25, 0.10, 0.05, 0.15, 0.05, 0.10],
    "landing-page":   [0.20, 0.10, 0.05, 0.05, 0.05, 0.05, 0.25, 0.25],
    "blog-post":      [0.25, 0.10, 0.10, 0.20, 0.10, 0.10, 0.05, 0.10],
    "faq-page":       [0.25, 0.25, 0.15, 0.05, 0.05, 0.10, 0.05, 0.10],
    "alternative":    [0.10, 0.15, 0.25, 0.05, 0.15, 0.05, 0.05, 0.20],
    "best-of":        [0.10, 0.25, 0.20, 0.15, 0.05, 0.10, 0.05, 0.10],
    "testimonial":    [0.10, 0.05, 0.15, 0.10, 0.30, 0.05, 0.05, 0.20],
}
PUBLICATION_STATES = {"draft", "staged", "live"}


def die(msg: str) -> None:
    print(f"score_eeat: {msg}", file=sys.stderr)
    sys.exit(2)


def dim_of(item_id: str) -> str:
    return item_id.rstrip("0123456789")


def item_name(item_id: str) -> str:
    d = dim_of(item_id)
    return ITEM_NAMES[d][int(item_id[len(d):]) - 1]


def band(score: int) -> str:
    if score >= 90:
        return "Excellent"
    if score >= 75:
        return "Good"
    if score >= 60:
        return "Medium"
    if score >= 40:
        return "Low"
    return "Poor"


def write_template(path: Path, args) -> None:
    sheet = {
        "target": args.target or "",
        "profile": args.profile or "",
        "market": args.market or "",
        "publication_state": args.publication_state or "",
        "observed_at": args.observed_at or "",
        "execution_blocked": False,
        "blocked_reason": "",
        "items": {
            i: ({"state": "unknown", "reason": "not yet observed", "conditional": True}
                if i in CONDITIONAL else {"state": "unknown", "reason": "not yet observed"})
            for i in ALL_IDS
        },
    }
    path.write_text(json.dumps(sheet, indent=2) + "\n", encoding="utf-8")
    print(f"template written: {path} (80 items, all unknown; na is allowed only on the 18 items marked conditional)")


def score(sheet: dict) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    profile = str(sheet.get("profile", "")).strip()
    if profile not in PROFILES:
        errors.append(f"profile must be one of {sorted(PROFILES)}; got {profile!r}")
    pub = str(sheet.get("publication_state", "")).strip()
    if pub and pub not in PUBLICATION_STATES:
        errors.append(f"publication_state must be draft, staged or live; got {pub!r}")
    raw_items = sheet.get("items") or {}
    if not isinstance(raw_items, dict):
        errors.append("'items' must be an object keyed by item id (C01 ... T10)")
        raw_items = {}
    unknown_ids = [k for k in raw_items if k not in ALL_IDS]
    if unknown_ids:
        errors.append(f"unknown item ids: {unknown_ids[:10]}")

    items: dict[str, dict] = {}
    for iid in ALL_IDS:
        rec = raw_items.get(iid)
        if rec is None:
            rec = {"state": "unknown", "reason": "item missing from sheet"}
            warnings.append(f"{iid} missing from sheet; treated as unknown")
        if isinstance(rec, str):
            rec = {"state": rec}
        state = str(rec.get("state", "unknown")).strip().lower()
        if state in ("n/a", "not applicable"):
            state = "na"
        if state not in ("pass", "partial", "fail", "unknown", "na"):
            errors.append(f"{iid}: invalid state {state!r}")
            continue
        if state == "na" and iid not in CONDITIONAL:
            errors.append(f"{iid} is unconditional and can never be na; use unknown (with a gap reason) or score it")
            continue
        if state == "na" and not str(rec.get("reason", "")).strip():
            warnings.append(f"{iid} is na without a written reason tied to its condition")
        rel = None
        if state in STATES:
            et = str(rec.get("evidence_type", "")).strip().lower()
            cf = str(rec.get("confidence", "")).strip().lower()
            if et not in EVIDENCE_WEIGHT:
                warnings.append(f"{iid}: evidence_type missing or invalid ({et!r}); treated as estimated")
                et = "estimated"
            if cf not in CONFIDENCE_FACTOR:
                warnings.append(f"{iid}: confidence missing or invalid ({cf!r}); treated as low")
                cf = "low"
            rel = EVIDENCE_WEIGHT[et] * CONFIDENCE_FACTOR[cf]
            rec = dict(rec, evidence_type=et, confidence=cf)
        items[iid] = dict(rec, state=state, reliability=rel)
    if errors:
        return {"errors": errors, "warnings": warnings}

    weights = dict(zip(DIMS, PROFILES[profile]))
    dims: dict[str, dict] = {}
    exact_total = 0.0
    lower_total = 0.0
    upper_total = 0.0
    all_complete = True
    for d in DIMS:
        ids = [i for i in ALL_IDS if dim_of(i) == d]
        applicable = [i for i in ids if items[i]["state"] != "na"]
        observed = [i for i in applicable if items[i]["state"] in STATES]
        unknown = [i for i in applicable if items[i]["state"] == "unknown"]
        pts = sum(STATES[items[i]["state"]] for i in observed)
        n = len(applicable)
        rec = {
            "name": DIM_NAMES[d], "applicable": n, "observed": len(observed), "unknown": unknown,
            "na": [i for i in ids if items[i]["state"] == "na"], "points": pts, "weight": weights[d],
        }
        if n == 0:
            rec.update(score=None, contribution=None, lower=None, upper=None)
            warnings.append(f"dimension {d} has no applicable items")
        else:
            lo = pts / n * 10
            hi = (pts + 10 * len(unknown)) / n * 10
            rec["lower"] = round(lo, 4)
            rec["upper"] = round(hi, 4)
            lower_total += lo * weights[d]
            upper_total += hi * weights[d]
            if unknown:
                all_complete = False
                rec["score"] = None
                rec["contribution"] = None
            else:
                rec["score"] = round(lo, 4)
                rec["contribution"] = round(lo * weights[d], 4)
                exact_total += lo * weights[d]
        dims[d] = rec

    applicable_total = sum(dims[d]["applicable"] for d in DIMS)
    observed_total = sum(dims[d]["observed"] for d in DIMS)
    unknown_items = [i for i in ALL_IDS if items[i]["state"] == "unknown"]
    na_items = [i for i in ALL_IDS if items[i]["state"] == "na"]
    coverage = (observed_total / applicable_total * 100) if applicable_total else 0.0
    complete = all_complete and not unknown_items

    veto_states = {v: items[v]["state"] for v in VETOES}
    veto_fails = [v for v in VETOES if items[v]["state"] == "fail"]
    veto_count = len(veto_fails)
    any_fail = any(items[i]["state"] == "fail" for i in ALL_IDS)

    raw = math.floor(exact_total + 1e-9) if complete else None
    blocked = bool(sheet.get("execution_blocked"))

    final = None
    cap_applied = False
    if blocked:
        status, verdict, score_state = "BLOCKED", "UNDECIDED", "NOT_SCORED"
        raw = None
    elif veto_count >= 2:
        status, verdict = "DONE", "BLOCK"
        score_state = "SCORED" if complete else "NOT_SCORED"
    elif not complete:
        status, verdict, score_state = "NEEDS_INPUT", "UNDECIDED", "NOT_SCORED"
    elif veto_count == 1:
        status, verdict, score_state = "DONE_WITH_CONCERNS", "FIX", "SCORED"
        final = min(raw, 59)
        cap_applied = True
    elif raw >= 75 and not any_fail:
        status, verdict, score_state = "DONE", "SHIP", "SCORED"
        final = raw
    else:
        status, verdict, score_state = "DONE_WITH_CONCERNS", "FIX", "SCORED"
        final = raw

    # confidence (complete runs only)
    confidence = "not_scored"
    mean_rel = None
    if score_state == "SCORED":
        rels = [items[i]["reliability"] for i in ALL_IDS if items[i]["reliability"] is not None]
        mean_rel = sum(rels) / len(rels) if rels else 0.0
        confidence = "high" if mean_rel >= 0.85 else ("medium" if mean_rel >= 0.60 else "low")
        weak_veto = [v for v in VETOES if items[v]["reliability"] is not None and items[v]["reliability"] < 0.60]
        if weak_veto:
            confidence = "low"
            warnings.append(f"veto evidence reliability below 0.60 on {weak_veto}; confidence capped at low")

    geo = seo = None
    if all(dims[d]["score"] is not None for d in ("C", "O", "R", "E")):
        geo = round(sum(dims[d]["score"] for d in ("C", "O", "R", "E")) / 4, 2)
    if all(dims[d]["score"] is not None for d in ("Exp", "Ept", "A", "T")):
        seo = round(sum(dims[d]["score"] for d in ("Exp", "Ept", "A", "T")) / 4, 2)

    fixes = []
    for i in ALL_IDS:
        st = items[i]["state"]
        if st in ("partial", "fail"):
            d = dim_of(i)
            n = dims[d]["applicable"]
            gain = (10 - STATES[st]) * 10 / n * weights[d] if n else 0.0
            severity = "veto" if (i in VETOES and st == "fail") else st
            fixes.append({"id": i, "item": item_name(i), "state": st, "severity": severity,
                          "weighted_points_lost": round(gain, 4)})
    sev_rank = {"veto": 0, "fail": 1, "partial": 2}
    fixes.sort(key=lambda f: (sev_rank[f["severity"]], -f["weighted_points_lost"]))

    arithmetic = []
    for d in DIMS:
        r = dims[d]
        if r["applicable"] == 0:
            arithmetic.append(f"{d}: no applicable items")
        elif r["score"] is None:
            arithmetic.append(
                f"{d}: {r['points']} observed pts, {len(r['unknown'])} unknown of {r['applicable']} applicable -> "
                f"lower {r['lower']:.4f} / upper {r['upper']:.4f} x {r['weight']:.2f}"
            )
        else:
            arithmetic.append(
                f"{d}: {r['points']}/{r['applicable']} x 10 = {r['score']:.4f} x {r['weight']:.2f} = {r['contribution']:.4f}"
            )
    if complete:
        arithmetic.append(f"exact total = {exact_total:.4f} -> raw = floor = {raw}")
    else:
        arithmetic.append(f"interval: lower = floor({lower_total:.4f}) = {math.floor(lower_total + 1e-9)}, "
                          f"upper = floor({upper_total:.4f}) = {math.floor(upper_total + 1e-9)}")
    if cap_applied:
        arithmetic.append(f"one verified veto ({veto_fails[0]}): final = min({raw}, 59) = {final}")
    elif veto_count >= 2:
        arithmetic.append(f"{veto_count} verified vetoes ({', '.join(veto_fails)}): no final score")

    result = {
        "framework": "CORE-EEAT", "catalog_version": CATALOG_VERSION, "runbook_version": RUNBOOK_VERSION,
        "schema_version": SCHEMA_VERSION,
        "target": sheet.get("target", ""), "profile": profile, "market": sheet.get("market", ""),
        "publication_state": pub, "observed_at": sheet.get("observed_at", ""),
        "item_count": len(ALL_IDS), "applicable": applicable_total, "observed": observed_total,
        "coverage_pct": round(coverage, 1),
        "unknown_items": unknown_items, "na_items": na_items,
        "status": status, "verdict": verdict, "score_state": score_state,
        "veto_states": veto_states, "veto_fails": veto_fails, "veto_count": veto_count,
        "cap_applied": cap_applied,
        "exact_total": round(exact_total, 4) if complete else None,
        "band": band(raw) if raw is not None else None,
        "interval": {"lower": math.floor(lower_total + 1e-9), "upper": math.floor(upper_total + 1e-9)},
        "geo_diagnostic": geo, "seo_diagnostic": seo,
        "mean_reliability": round(mean_rel, 4) if mean_rel is not None else None,
        "score_confidence": confidence,
        "dimensions": dims, "fix_plan": fixes, "arithmetic": arithmetic,
        "items": {i: {k: v for k, v in items[i].items() if k != "reliability"} for i in ALL_IDS},
        "warnings": warnings, "errors": [],
    }
    if score_state == "SCORED":
        result["raw_overall_score"] = raw
    if final is not None:
        result["final_overall_score"] = final
    return result


def fmt(x) -> str:
    return "omitted" if x is None else str(x)


def render_md(r: dict) -> str:
    L = []
    L.append("## CORE-EEAT Audit")
    L.append(f"**Status:** `{r['status']}`")
    L.append(f"**Verdict:** `{r['verdict']}`")
    L.append(f"**Score state:** `{r['score_state']}`")
    L.append(f"**Profile / target / observed:** {r['profile']} / {r['target']} / {r['observed_at']}")
    L.append(f"**Raw score:** {fmt(r.get('raw_overall_score'))}")
    L.append(f"**Final score:** {fmt(r.get('final_overall_score'))}")
    L.append(f"**Confidence:** {r['score_confidence']}")
    L.append("")
    L.append(f"**Context:** market {r['market']} · publication state {r['publication_state']} · catalog CORE-EEAT "
             f"{r['catalog_version']} · coverage {r['coverage_pct']}% ({r['observed']}/{r['applicable']})")
    L.append("")
    if r["unknown_items"]:
        L.append("### Unknown items")
        for i in r["unknown_items"]:
            reason = r["items"][i].get("reason") or "not observed"
            resolves = r["items"][i].get("resolves_with") or "evidence for this item"
            L.append(f"- `CORE-EEAT-{i}`: `unknown` — {reason} · resolves with {resolves}")
        L.append("")
    L.append("### Vetoes")
    L.append("| Veto | State | Evidence |")
    L.append("|---|---|---|")
    for v in VETOES:
        it = r["items"][v]
        ev = it.get("note") or it.get("source") or it.get("reason") or ""
        L.append(f"| `CORE-EEAT-{v}` | {it['state']} | {ev} |")
    L.append("")
    L.append("### Dimension scores")
    if r["score_state"] == "SCORED" or r["status"] == "DONE":
        L.append("| Dim | Applicable | Observed | Score | Weight | Contribution |")
        L.append("|---|---:|---:|---:|---:|---:|")
        for d in DIMS:
            x = r["dimensions"][d]
            sc = "n/a" if x["score"] is None else f"{x['score']:.4f}"
            ct = "n/a" if x["contribution"] is None else f"{x['contribution']:.4f}"
            L.append(f"| {d} | {x['applicable']} | {x['observed']} | {sc} | {x['weight']:.2f} | {ct} |")
        if r["exact_total"] is not None:
            L.append(f"| **Total** | | | | | {r['exact_total']:.4f} → floor {r.get('raw_overall_score')} |")
    else:
        L.append("| Dim | Applicable | Observed | Lower | Upper | Weight |")
        L.append("|---|---:|---:|---:|---:|---:|")
        for d in DIMS:
            x = r["dimensions"][d]
            lo = "n/a" if x["lower"] is None else f"{x['lower']:.4f}"
            hi = "n/a" if x["upper"] is None else f"{x['upper']:.4f}"
            L.append(f"| {d} | {x['applicable']} | {x['observed']} | {lo} | {hi} | {x['weight']:.2f} |")
        L.append(f"| **Interval (raw only)** | | | {r['interval']['lower']} | {r['interval']['upper']} | |")
    L.append("")
    L.append("Arithmetic:")
    for a in r["arithmetic"]:
        L.append(f"- {a}")
    L.append("")
    geo = "incomplete" if r["geo_diagnostic"] is None else r["geo_diagnostic"]
    seo = "incomplete" if r["seo_diagnostic"] is None else r["seo_diagnostic"]
    L.append(f"GEO diagnostic (C+O+R+E)/4 = {geo} · SEO diagnostic (Exp+Ept+A+T)/4 = {seo} — diagnostics, not totals.")
    if r["veto_count"] >= 2:
        cap = f"{r['veto_count']} vetoes → no final score"
    elif r["cap_applied"]:
        cap = f"one veto → min({r.get('raw_overall_score')}, 59) = {r.get('final_overall_score')}"
    else:
        cap = "none"
    L.append(f"Cap: {cap}")
    rel = "n/a" if r["mean_reliability"] is None else r["mean_reliability"]
    L.append(f"Confidence: mean reliability {rel} → {r['score_confidence']}")
    L.append("")
    if r["fix_plan"]:
        L.append("### Findings (ordered by severity, then weighted points lost)")
        L.append("| # | Item | State | Severity | Weighted pts lost |")
        L.append("|---|---|---|---|---:|")
        for n, f in enumerate(r["fix_plan"], 1):
            L.append(f"| {n} | `CORE-EEAT-{f['id']}` {f['item']} | {f['state']} | {f['severity']} | {f['weighted_points_lost']:.4f} |")
        L.append("")
    if r["warnings"]:
        L.append("### Scorer warnings")
        for w in r["warnings"]:
            L.append(f"- {w}")
        L.append("")
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sheet", nargs="?", help="eeat_items.json to score")
    ap.add_argument("--template", metavar="PATH", help="write a blank 80-item sheet here and exit")
    ap.add_argument("--profile")
    ap.add_argument("--target")
    ap.add_argument("--market")
    ap.add_argument("--publication-state")
    ap.add_argument("--observed-at")
    ap.add_argument("--out-json", default=None, help="default: eeat_result.json next to the sheet")
    ap.add_argument("--out-md", default=None, help="default: eeat_report.md next to the sheet")
    args = ap.parse_args()

    if args.template:
        write_template(Path(args.template), args)
        return 0
    if not args.sheet:
        die("give a sheet to score, or --template PATH to create one")
    p = Path(args.sheet)
    if not p.exists():
        die(f"{p} does not exist")
    try:
        sheet = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        die(f"{p} is not valid JSON: {e}")
    result = score(sheet)
    args.out_json = _beside(args.sheet, "eeat_result.json", args.out_json)
    args.out_md = _beside(args.sheet, "eeat_report.md", args.out_md)
    if result.get("errors"):
        for e in result["errors"]:
            print(f"score_eeat: {e}", file=sys.stderr)
        return 2
    Path(args.out_json).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    Path(args.out_md).write_text(render_md(result), encoding="utf-8")
    print(f"status={result['status']} verdict={result['verdict']} score_state={result['score_state']} "
          f"raw={fmt(result.get('raw_overall_score'))} final={fmt(result.get('final_overall_score'))} "
          f"coverage={result['coverage_pct']}% unknown={len(result['unknown_items'])} vetoes={result['veto_count']} "
          f"confidence={result['score_confidence']}")
    print(f"wrote {args.out_json} and {args.out_md}")
    for w in result["warnings"]:
        print(f"warning: {w}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
