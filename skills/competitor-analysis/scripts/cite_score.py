#!/usr/bin/env python3
"""Score the CITE quick comparison (Citation, Identity, Trust, Eminence) for each domain in a sheet.

Usage
  python3 scripts/cite_score.py cite_items.json [--out-csv cite_scores.csv] [--out-md cite_scores.md]

Input `cite_items.json`:
  {
    "cohort": "US small-business CRM software", "market": "US", "observed_at": "2026-10-11",
    "domains": {
      "example.com": {
        "domain_type": "Product & Service",
        "items": {"C01": "pass", "C02": {"state": "partial", "evidence": "..."}, ..., "E10": "unknown"}
      }
    }
  }
  40 item ids: C01-C10, I01-I10, T01-T10, E01-E10. States: pass | partial | fail | unknown.
  domain_type: Default | Content Publisher | Product & Service | E-commerce | Community & UGC |
  Tool & Utility | Authority & Institutional (unknown types fall back to Default).

Rules (references/cite-quick-comparison.md): pass 10, partial 5, fail 0, unknown not scored.
Dimension score = mean of scored items x 10. Weighted score = sum(dim x weight) with the
domain-type weights. Vetoes T03, T05, T09: one verified fail caps the score at 59 and adds a
Manipulation Alert; two or more means no score. Status: `scored` (full coverage),
`partial-coverage` (some unknowns, every dimension at least half observed), `N/A` (a dimension
has fewer than half its items observed), `no-score` (2+ veto fails). Unknown never counts as
partial or fail. Exit 0 on success, 2 on bad input. Standard library only.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path


def _beside(primary: str, default_name: str, given: str | None) -> str:
    """Default output path: next to the primary input file unless an explicit path was given."""
    if given is not None:
        return given
    return str(Path(primary).resolve().parent / default_name)

DIMS = ["C", "I", "T", "E"]
DIM_NAMES = {"C": "Citation", "I": "Identity", "T": "Trust", "E": "Eminence"}
ALL_IDS = [f"{d}{i:02d}" for d in DIMS for i in range(1, 11)]
VETOES = ["T03", "T05", "T09"]
POINTS = {"pass": 10, "partial": 5, "fail": 0}
WEIGHTS = {
    "Default": (0.35, 0.20, 0.25, 0.20),
    "Content Publisher": (0.40, 0.15, 0.20, 0.25),
    "Product & Service": (0.25, 0.30, 0.25, 0.20),
    "E-commerce": (0.20, 0.20, 0.35, 0.25),
    "Community & UGC": (0.35, 0.10, 0.25, 0.30),
    "Tool & Utility": (0.25, 0.30, 0.25, 0.20),
    "Authority & Institutional": (0.45, 0.20, 0.20, 0.15),
}


def rating(score: float) -> str:
    if score >= 90:
        return "Excellent"
    if score >= 75:
        return "Good"
    if score >= 60:
        return "Medium"
    if score >= 40:
        return "Low"
    return "Poor"


def norm_type(t: str) -> str:
    t = (t or "").strip()
    for k in WEIGHTS:
        if k.lower() == t.lower():
            return k
    return "Default"


def score_domain(name: str, spec: dict, errors: list[str]) -> dict:
    items_in = spec.get("items") or {}
    if not isinstance(items_in, dict):
        errors.append(f"{name}: 'items' must be an object keyed by item id")
        return {}
    bad = [k for k in items_in if k not in ALL_IDS]
    if bad:
        errors.append(f"{name}: unknown item ids {bad[:8]}")
    states: dict[str, dict] = {}
    for iid in ALL_IDS:
        rec = items_in.get(iid, "unknown")
        if isinstance(rec, str):
            rec = {"state": rec}
        st = str(rec.get("state", "unknown")).strip().lower()
        if st in ("n/a", "na", ""):
            st = "unknown"
        if st not in ("pass", "partial", "fail", "unknown"):
            errors.append(f"{name}: {iid} has invalid state {st!r}")
            st = "unknown"
        states[iid] = {"state": st, "evidence": str(rec.get("evidence", "") or "")}
    dtype_in = spec.get("domain_type", "Default")
    dtype = norm_type(dtype_in)
    weights = dict(zip(DIMS, WEIGHTS[dtype]))

    dims = {}
    na_dim = False
    any_unknown = False
    for d in DIMS:
        ids = [i for i in ALL_IDS if i.startswith(d)]
        scored = [i for i in ids if states[i]["state"] in POINTS]
        unknown = [i for i in ids if states[i]["state"] == "unknown"]
        if unknown:
            any_unknown = True
        if len(scored) < 5:
            na_dim = True
        mean = (sum(POINTS[states[i]["state"]] for i in scored) / len(scored) * 10) if scored else None
        dims[d] = {"observed": len(scored), "unknown": unknown, "score": None if mean is None else round(mean, 2),
                   "weight": weights[d], "contribution": None if mean is None else round(mean * weights[d], 2)}

    veto_fails = [v for v in VETOES if states[v]["state"] == "fail"]
    veto_unknown = [v for v in VETOES if states[v]["state"] == "unknown"]
    arithmetic = []
    for d in DIMS:
        x = dims[d]
        if x["score"] is None:
            arithmetic.append(f"{d}: 0/10 items observed, not scored")
        else:
            arithmetic.append(f"{d}: {x['observed']}/10 observed, mean x 10 = {x['score']:.2f} x {x['weight']:.2f} = {x['contribution']:.2f}")

    rec = {"domain": name, "domain_type": dtype, "dimensions": dims, "veto_fails": veto_fails,
           "veto_unknown": veto_unknown, "capped": False, "manipulation_alert": "", "score": None,
           "rating": "", "status": "", "arithmetic": arithmetic, "label": "Calculated", "items": states}
    if dtype_in and norm_type(dtype_in) == "Default" and str(dtype_in).strip().lower() != "default":
        rec["note"] = f"domain_type {dtype_in!r} not recognised; Default weights used"

    if len(veto_fails) >= 2:
        rec["status"] = "no-score"
        rec["manipulation_alert"] = f"Manipulation Alert: {len(veto_fails)} verified veto fails ({', '.join(veto_fails)}); no score reported"
        arithmetic.append(rec["manipulation_alert"])
        return rec
    if na_dim:
        rec["status"] = "N/A"
        thin = [f"{d} {dims[d]['observed']}/10" for d in DIMS if dims[d]["observed"] < 5]
        arithmetic.append("N/A: fewer than half the items observed in " + ", ".join(thin) + "; compare dimension observations, not a headline number")
        if veto_fails:
            rec["capped"] = True
            rec["manipulation_alert"] = f"Manipulation Alert: verified veto fail on {veto_fails[0]}"
        return rec
    total = sum(dims[d]["contribution"] for d in DIMS)
    raw = round(total, 1)
    final = raw
    if veto_fails:
        final = min(raw, 59.0)
        rec["capped"] = True
        rec["manipulation_alert"] = f"Manipulation Alert: verified veto fail on {veto_fails[0]} ({states[veto_fails[0]]['evidence'] or 'see evidence'})"
        arithmetic.append(f"weighted total = {raw:.1f}; one verified veto ({veto_fails[0]}) -> capped at min({raw:.1f}, 59) = {final:.1f}")
    else:
        arithmetic.append(f"weighted total = {raw:.1f}")
    rec["raw_score"] = raw
    rec["score"] = final
    rec["rating"] = rating(final)
    rec["status"] = "partial-coverage" if any_unknown else "scored"
    if veto_unknown:
        arithmetic.append(f"veto items unknown: {', '.join(veto_unknown)} (an unknown veto never triggers the cap)")
    return rec


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sheet")
    ap.add_argument("--out-csv", default=None, help="default: cite_scores.csv next to the sheet")
    ap.add_argument("--out-md", default=None, help="default: cite_scores.md next to the sheet")
    args = ap.parse_args()
    args.out_csv = _beside(args.sheet, "cite_scores.csv", args.out_csv)
    args.out_md = _beside(args.sheet, "cite_scores.md", args.out_md)
    try:
        sheet = json.loads(Path(args.sheet).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"cite_score: cannot read {args.sheet}: {e}", file=sys.stderr)
        return 2
    domains = sheet.get("domains")
    if not isinstance(domains, dict) or not domains:
        print("cite_score: 'domains' must be a non-empty object keyed by domain", file=sys.stderr)
        return 2
    errors: list[str] = []
    results = [score_domain(n, s or {}, errors) for n, s in domains.items()]
    if errors:
        for e in errors:
            print(f"cite_score: {e}", file=sys.stderr)
        return 2

    cols = ["domain", "domain_type", "C", "I", "T", "E", "coverage", "raw_score", "score", "rating", "status",
            "veto_fails", "capped", "manipulation_alert", "label"]
    with Path(args.out_csv).open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in results:
            dims = r["dimensions"]
            w.writerow([
                r["domain"], r["domain_type"],
                *["" if dims[d]["score"] is None else f"{dims[d]['score']:.1f}" for d in DIMS],
                "; ".join(f"{d} {dims[d]['observed']}/10" for d in DIMS),
                "" if r.get("raw_score") is None else f"{r['raw_score']:.1f}",
                "N/A" if r["score"] is None else f"{r['score']:.1f}",
                r["rating"] or "N/A", r["status"], "|".join(r["veto_fails"]), str(r["capped"]).lower(),
                r["manipulation_alert"], r["label"],
            ])

    L = [f"## CITE quick comparison (Calculated) — cohort: {sheet.get('cohort', 'not stated')}, market {sheet.get('market', 'not stated')}, observed {sheet.get('observed_at', 'not stated')}", ""]
    L.append("| Domain | Type | C | I | T | E | Coverage | Score | Rating | Status |")
    L.append("|---|---|---:|---:|---:|---:|---|---:|---|---|")
    for r in results:
        dims = r["dimensions"]
        L.append("| " + " | ".join([
            r["domain"], r["domain_type"],
            *["n/a" if dims[d]["score"] is None else f"{dims[d]['score']:.1f}" for d in DIMS],
            ", ".join(f"{d} {dims[d]['observed']}/10" for d in DIMS),
            "N/A" if r["score"] is None else f"{r['score']:.1f}", r["rating"] or "N/A", r["status"],
        ]) + " |")
    L.append("")
    L.append("Weights by domain type (C, I, T, E): " + "; ".join(f"{k} {v}" for k, v in WEIGHTS.items() if k in {r['domain_type'] for r in results}))
    L.append("")
    for r in results:
        L.append(f"### {r['domain']}")
        for a in r["arithmetic"]:
            L.append(f"- {a}")
        if r.get("note"):
            L.append(f"- {r['note']}")
        if r["manipulation_alert"]:
            L.append(f"- **{r['manipulation_alert']}** (add to open_loops)")
        unknown = [i for i in ALL_IDS if r["items"][i]["state"] == "unknown"]
        if unknown:
            L.append(f"- Unknown items ({len(unknown)}): {', '.join(unknown)}")
        L.append("")
    L.append("A comparable score needs full coverage; with partial-coverage or N/A rows, compare dimensions rather than headline numbers.")
    Path(args.out_md).write_text("\n".join(L) + "\n", encoding="utf-8")
    for r in results:
        print(f"{r['domain']}: status={r['status']} score={'N/A' if r['score'] is None else r['score']} rating={r['rating'] or 'N/A'} "
              f"vetoes={r['veto_fails']} capped={r['capped']}")
    print(f"wrote {args.out_csv} and {args.out_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
