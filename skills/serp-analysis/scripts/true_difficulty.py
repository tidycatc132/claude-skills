#!/usr/bin/env python3
"""Compute True Difficulty (0-100) from five labeled inputs, or return NOT_SCORED.

Usage
  python3 scripts/true_difficulty.py difficulty_inputs.json [--stability-from serp_stability.json]
                                      [--out true_difficulty.json]

Input `difficulty_inputs.json`:
  {
    "query": "...", "locale": "US", "language": "en", "device": "desktop", "engine": "google",
    "inputs": {
      "top10_authority":      {"value": 72, "label": "User-provided", "source": "...", "observed_at": "2026-10-10"},
      "page_authority_links": {"value": 60, "label": "Measured", ...},
      "content_quality_bar":  {"value": 65, "label": "Estimated", ...},
      "backlinks_required":   {"value": 55, "label": "Estimated", ...},
      "serp_stability":       {"value": "unknown", "label": "Unknown", "source": "..."}
    }
  }
  Each value is 0-100 (higher = harder) or "unknown"/null. A value may also be a bare number.

--stability-from fills `serp_stability` from the `stability_input_suggested` field of a
serp_compare.py result when the sheet leaves it unknown (label becomes Calculated).

Weights: top10_authority 25%, page_authority_links 20%, content_quality_bar 20%,
backlinks_required 20%, serp_stability 15%. If any input is unknown the result is NOT_SCORED with
the missing inputs listed; no partial score is ever produced. Score = round(sum(value x weight)).
Bands: 0-29 Low, 30-59 Medium, 60-79 High, 80-100 Very High.
Exit 0 on success, 2 on bad input. Standard library only.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

WEIGHTS = [
    ("top10_authority", 0.25, "Top-10 authority"),
    ("page_authority_links", 0.20, "Page authority / links"),
    ("content_quality_bar", 0.20, "Content quality bar"),
    ("backlinks_required", 0.20, "Backlinks required"),
    ("serp_stability", 0.15, "SERP stability"),
]
LABELS = {"measured", "user-provided", "calculated", "estimated", "proxy", "unknown"}


def band(score: int) -> str:
    if score >= 80:
        return "Very High"
    if score >= 60:
        return "High"
    if score >= 30:
        return "Medium"
    return "Low"


def parse_value(v):
    if isinstance(v, dict):
        v = v.get("value")
    if v is None:
        return None
    if isinstance(v, str):
        s = v.strip().lower()
        if s in ("", "unknown", "n/a", "na", "none", "null"):
            return None
        try:
            v = float(s)
        except ValueError:
            raise ValueError(f"value {v!r} is not a number or 'unknown'")
    if isinstance(v, bool):
        raise ValueError("value must be a number, not a boolean")
    v = float(v)
    if not 0 <= v <= 100:
        raise ValueError(f"value {v} is outside 0-100")
    return v


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs")
    ap.add_argument("--stability-from", metavar="SERP_STABILITY_JSON")
    ap.add_argument("--out", default="true_difficulty.json")
    args = ap.parse_args()

    try:
        sheet = json.loads(Path(args.inputs).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"true_difficulty: cannot read {args.inputs}: {e}", file=sys.stderr)
        return 2
    raw_inputs = sheet.get("inputs", sheet)
    if not isinstance(raw_inputs, dict):
        print("true_difficulty: 'inputs' must be an object", file=sys.stderr)
        return 2

    inputs: dict[str, dict] = {}
    errors: list[str] = []
    for key, _w, _name in WEIGHTS:
        rec = raw_inputs.get(key)
        rec = dict(rec) if isinstance(rec, dict) else {"value": rec}
        try:
            val = parse_value(rec.get("value"))
        except ValueError as e:
            errors.append(f"{key}: {e}")
            val = None
        label = str(rec.get("label", "")).strip() or ("Unknown" if val is None else "Estimated")
        if label.lower() not in LABELS:
            errors.append(f"{key}: label {label!r} must be one of Measured, User-provided, Calculated, Estimated, Proxy, Unknown")
        inputs[key] = {"value": val, "label": label, "source": rec.get("source", ""), "observed_at": rec.get("observed_at", "")}
    if errors:
        for e in errors:
            print(f"true_difficulty: {e}", file=sys.stderr)
        return 2

    notes: list[str] = []
    if args.stability_from and inputs["serp_stability"]["value"] is None:
        try:
            st = json.loads(Path(args.stability_from).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            print(f"true_difficulty: cannot read {args.stability_from}: {e}", file=sys.stderr)
            return 2
        sug = st.get("stability_input_suggested")
        if sug is None:
            inputs["serp_stability"]["source"] = f"{args.stability_from}: verdict {st.get('verdict')}, {st.get('missing_reason') or 'no suggestion'}"
            notes.append("serp_stability stays unknown: the comparison had a single source.")
        else:
            inputs["serp_stability"].update(
                value=float(sug), label="Calculated",
                source=f"{args.stability_from}: verdict {st.get('verdict')} ({st.get('top5_common')}/5 top-5 URLs in common, same number one = {st.get('same_number_one')})",
            )
    if inputs["serp_stability"]["value"] is None and not inputs["serp_stability"]["source"]:
        inputs["serp_stability"]["source"] = "no second snapshot or rank history"

    missing = [k for k, _w, _n in WEIGHTS if inputs[k]["value"] is None]
    for k in missing:
        inputs[k]["label"] = "Unknown"
    result = {
        "query": sheet.get("query", ""),
        "locale": sheet.get("locale", ""),
        "language": sheet.get("language", ""),
        "device": sheet.get("device", ""),
        "engine": sheet.get("engine", ""),
        "weights": {k: w for k, w, _n in WEIGHTS},
        "inputs": inputs,
        "missing_inputs": missing,
        "label": "Calculated",
        "notes": notes,
    }
    if missing:
        result.update(score_state="NOT_SCORED", arithmetic=[
            f"{n}: {('unknown' if inputs[k]['value'] is None else inputs[k]['value'])} x {w:.2f}" for k, w, n in WEIGHTS
        ] + ["NOT_SCORED: " + ", ".join(missing) + " unknown; a partial score is never computed"])
        Path(args.out).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(f"score_state=NOT_SCORED missing_inputs={missing}; wrote {args.out}")
        return 0

    exact = sum(inputs[k]["value"] * w for k, w, _n in WEIGHTS)
    score = int(exact + 0.5)
    lines = [f"{n}: {inputs[k]['value']:g} x {w:.2f} = {inputs[k]['value'] * w:.2f}" for k, w, n in WEIGHTS]
    lines.append(f"sum = {exact:.2f} -> True Difficulty = {score}/100 ({band(score)}), label Calculated")
    result.update(score_state="SCORED", exact=round(exact, 2), score=score, band=band(score), arithmetic=lines)
    Path(args.out).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"score_state=SCORED score={score}/100 ({band(score)}) exact={exact:.2f}; wrote {args.out}")
    for l in lines:
        print("  " + l)
    return 0


if __name__ == "__main__":
    sys.exit(main())
