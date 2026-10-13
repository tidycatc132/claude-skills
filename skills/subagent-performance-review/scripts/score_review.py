#!/usr/bin/env python3
"""Score one sub-agent's dispatch history and decide the review verdict.

Usage:
  python3 scripts/score_review.py --log subagent_dispatch_log.jsonl --agent NAME
          [--as-of YYYY-MM-DD] [--window-days 30] [--prior review_NAME.json] [--out-dir DIR]

Reads the JSONL dispatch log, keeps the agent's records inside the window,
computes the four scored dimensions, the composite, caps, trend, per-task-type
table, merge candidate, and the verdict. Writes review_NAME.json and
review_NAME.md into --out-dir (default: the log's folder). Standard library only.

Exit codes: 0 ok, 1 bad input.
"""
import argparse
import collections
import itertools
import datetime as dt
import json
import os
import sys

OUTCOMES = {"accepted", "accepted_with_fixes", "rejected", "abandoned", "blocked"}
WEIGHTS = {"acceptance": 0.40, "adherence": 0.25, "efficiency": 0.20, "reliability": 0.15}
MIN_SAMPLE = 5
MIN_TREND = 6
VERDICT_TEXT = {
    "promote": "Promote: copy the definition into the new role and keep the current position filled.",
    "retain": "Retain: no change to the definition. Review again next window.",
    "improvement_plan": "Improvement plan: rewrite the weak instructions, write the plan into the definition, re-review in 30 days.",
    "reassign": "Reassign: narrow the description to the task types it is good at and route the rest elsewhere.",
    "merge": "Merge: fold this agent's scope into the stronger sibling's description and retire this file.",
    "replace": "Replace: retire the definition and write a new one at the same name today.",
    "insufficient_data": "Insufficient data: no action. Keep dispatching and logging until five dispatches exist in the window.",
}


def parse_ts(s):
    s = s.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    d = dt.datetime.fromisoformat(s)
    if d.tzinfo is None:
        d = d.replace(tzinfo=dt.timezone.utc)
    return d


def load_log(path):
    rows = []
    with open(path, encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError as e:
                sys.exit(f"error: line {n} is not valid JSON: {e}")
            for k in ("dispatch_id", "agent", "dispatched_at", "outcome"):
                if k not in r:
                    sys.exit(f"error: line {n} lacks required field '{k}'")
            if r["outcome"] not in OUTCOMES:
                sys.exit(f"error: line {n} outcome '{r['outcome']}' not in {sorted(OUTCOMES)}")
            r["_ts"] = parse_ts(r["dispatched_at"])
            r.setdefault("task_type", "unspecified")
            r.setdefault("complexity", 2)
            r.setdefault("rework_rounds", 0)
            r.setdefault("scope_violations", 0)
            r.setdefault("fabrication", False)
            r.setdefault("tool_errors", 0)
            rows.append(r)
    return rows


def pct(num, den):
    return round(100.0 * num / den, 1) if den else 0.0


def accept_value(r):
    return {"accepted": 1.0, "accepted_with_fixes": 0.5}.get(r["outcome"], 0.0)


def score_records(recs):
    """Four dimensions on 0-100 for a list of records. Returns dict or None when empty."""
    if not recs:
        return None
    scored = [r for r in recs if r["outcome"] != "blocked"]
    acceptance = pct(sum(accept_value(r) for r in scored), len(scored))
    adh = [0.0 if r["fabrication"] else max(0.0, 100.0 - 50.0 * min(int(r["scope_violations"]), 2)) for r in recs]
    adherence = round(sum(adh) / len(adh), 1)
    eff = [max(0.0, 100.0 - 30.0 * int(r["rework_rounds"]) - 10.0 * int(r["tool_errors"])) for r in scored] or [100.0]
    efficiency = round(sum(eff) / len(eff), 1)
    abandoned = sum(1 for r in recs if r["outcome"] == "abandoned")
    reliability = pct(len(recs) - abandoned, len(recs))
    return {"acceptance": acceptance, "adherence": adherence, "efficiency": efficiency, "reliability": reliability}


def composite_of(scores):
    return int(round(sum(WEIGHTS[k] * scores[k] for k in WEIGHTS)))


def trend_of(recs):
    if len(recs) < MIN_TREND:
        return "insufficient", None
    recs = sorted(recs, key=lambda r: r["_ts"])
    half = len(recs) // 2
    first = [r for r in recs[:half] if r["outcome"] != "blocked"]
    second = [r for r in recs[half:] if r["outcome"] != "blocked"]
    a1 = pct(sum(accept_value(r) for r in first), len(first))
    a2 = pct(sum(accept_value(r) for r in second), len(second))
    delta = round(a2 - a1, 1)
    if delta >= 15:
        return "improving", delta
    if delta <= -15:
        return "declining", delta
    return "flat", delta


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--log", required=True)
    ap.add_argument("--agent", required=True)
    ap.add_argument("--as-of", help="review date YYYY-MM-DD (default: today, UTC)")
    ap.add_argument("--window-days", type=int, default=30)
    ap.add_argument("--prior", help="previous review_NAME.json, to escalate an unmet improvement plan")
    ap.add_argument("--out-dir")
    args = ap.parse_args()

    as_of = dt.date.fromisoformat(args.as_of) if args.as_of else dt.datetime.now(dt.timezone.utc).date()
    end = dt.datetime.combine(as_of, dt.time.max, tzinfo=dt.timezone.utc)
    start = end - dt.timedelta(days=args.window_days)
    rows = load_log(args.log)
    window = [r for r in rows if start <= r["_ts"] <= end]
    recs = sorted([r for r in window if r["agent"] == args.agent], key=lambda r: r["_ts"])
    out_dir = args.out_dir or os.path.dirname(os.path.abspath(args.log))
    os.makedirs(out_dir, exist_ok=True)

    n = len(recs)
    scores = score_records(recs) or {"acceptance": 0.0, "adherence": 0.0, "efficiency": 0.0, "reliability": 0.0}
    raw = composite_of(scores) if recs else 0
    fabrications = sum(1 for r in recs if r["fabrication"])
    abandoned = sum(1 for r in recs if r["outcome"] == "abandoned")
    cap, cap_reason = None, ""
    if fabrications >= 2:
        cap, cap_reason = 39, f"{fabrications} dispatches with fabrication cap the composite at 39"
    elif fabrications == 1:
        cap, cap_reason = 59, "1 dispatch with fabrication caps the composite at 59"
    if n and abandoned / n >= 0.5:
        c = 49
        if cap is None or c < cap:
            cap, cap_reason = c, f"{abandoned} of {n} dispatches abandoned caps the composite at 49"
    composite = min(raw, cap) if cap is not None else raw
    trend, trend_delta = trend_of(recs)
    complex_accepted = sum(1 for r in recs if int(r["complexity"]) >= 3 and r["outcome"] == "accepted")

    by_type = {}
    for t, grp in itertools.groupby(sorted(recs, key=lambda r: r["task_type"]), key=lambda r: r["task_type"]):
        grp = list(grp)
        s = score_records(grp)
        by_type[t] = {"dispatches": len(grp), "share": pct(len(grp), n), "acceptance": s["acceptance"]}
    strong_types = [t for t, v in by_type.items() if v["dispatches"] >= 3 and v["acceptance"] >= 80 and v["share"] < 50]

    # merge candidate: another agent in the window that covers every task type this one has, scores 15+ higher
    merge_into = None
    if recs:
        my_types = set(by_type)
        others = collections.defaultdict(list)
        for r in window:
            if r["agent"] != args.agent:
                others[r["agent"]].append(r)
        best = None
        for name, orecs in others.items():
            if len(orecs) < MIN_SAMPLE or not my_types <= {r["task_type"] for r in orecs}:
                continue
            oc = composite_of(score_records(orecs))
            if oc >= composite + 15 and (best is None or oc > best[1]):
                best = (name, oc)
        if best and n < 8:
            merge_into = best[0]

    prior = None
    if args.prior and os.path.exists(args.prior):
        with open(args.prior, encoding="utf-8") as fh:
            prior = json.load(fh)
        jpath = os.path.join(out_dir, f"review_{args.agent}.json")
        if os.path.abspath(args.prior) == os.path.abspath(jpath) and prior.get("as_of"):
            keep = os.path.join(out_dir, f"review_{args.agent}.{prior['as_of']}.json")
            with open(keep, "w", encoding="utf-8") as fh:
                json.dump(prior, fh, indent=2)
            print(f"kept prior review as {keep}")

    if n < MIN_SAMPLE:
        verdict, reason = "insufficient_data", f"{n} dispatches in the window; {MIN_SAMPLE} are needed"
    elif composite >= 85 and fabrications == 0 and trend != "declining" and complex_accepted >= 2:
        verdict, reason = "promote", f"composite {composite}, {complex_accepted} complexity-3 tasks accepted, trend {trend}"
    elif composite >= 70:
        verdict, reason = "retain", f"composite {composite} is at or above 70"
    elif composite < 40:
        verdict, reason = "replace", f"composite {composite} is below 40" + (f" ({cap_reason})" if cap_reason else "")
    elif prior and prior.get("verdict") == "improvement_plan" and composite < int(prior.get("composite", 0)) + 10:
        verdict, reason = "replace", f"improvement plan from {prior.get('as_of')} not met: composite {prior.get('composite')} then, {composite} now"
    elif merge_into:
        verdict, reason = "merge", f"{merge_into} covers every task type here with a composite 15+ points higher and this agent has under 8 dispatches"
    elif strong_types:
        verdict, reason = "reassign", f"acceptance at or above 80 on {', '.join(strong_types)} but composite {composite} overall"
    else:
        verdict, reason = "improvement_plan", f"composite {composite} is between 40 and 69 with no task type to narrow to"

    weak = sorted(recs, key=lambda r: (accept_value(r), -int(r["rework_rounds"]) - 2 * int(r["scope_violations"]) - (5 if r["fabrication"] else 0)))[:3]
    evidence = [{"dispatch_id": r["dispatch_id"], "task": r.get("task", ""), "outcome": r["outcome"],
                 "rework_rounds": r["rework_rounds"], "scope_violations": r["scope_violations"],
                 "fabrication": r["fabrication"], "notes": r.get("notes", "")} for r in weak]
    findings = []
    if scores["acceptance"] < 70 and n:
        findings.append(f"first-pass acceptance {scores['acceptance']}%: {sum(1 for r in recs if r['outcome']=='rejected')} rejected, {sum(1 for r in recs if r['outcome']=='accepted_with_fixes')} needed fixes")
    if any(int(r["scope_violations"]) for r in recs):
        findings.append(f"scope violations in {sum(1 for r in recs if int(r['scope_violations']))} dispatches (did work the brief did not ask for)")
    if fabrications:
        findings.append(f"fabrication in {fabrications} dispatches (content not present in the sources)")
    if abandoned:
        findings.append(f"abandoned with no deliverable, {abandoned} of {n} dispatches")
    if sum(int(r["tool_errors"]) for r in recs):
        findings.append(f"{sum(int(r['tool_errors']) for r in recs)} tool errors across the window")
    if scores["efficiency"] < 70 and n:
        findings.append(f"efficiency {scores['efficiency']}: average {round(sum(int(r['rework_rounds']) for r in recs)/n,1)} rework rounds per dispatch")

    review = {
        "agent": args.agent, "as_of": as_of.isoformat(), "window_days": args.window_days,
        "window_start": start.date().isoformat(), "dispatches": n, "scores": scores,
        "composite_raw": raw, "composite": composite, "cap": cap, "cap_reason": cap_reason,
        "fabrications": fabrications, "abandoned": abandoned, "complex_accepted": complex_accepted,
        "trend": trend, "trend_delta": trend_delta, "by_task_type": by_type, "strong_types": strong_types,
        "merge_into": merge_into, "prior_verdict": prior.get("verdict") if prior else None,
        "verdict": verdict, "verdict_reason": reason, "findings": findings, "evidence": evidence,
        "re_review_date": (as_of + dt.timedelta(days=args.window_days)).isoformat(),
    }
    jpath = os.path.join(out_dir, f"review_{args.agent}.json")
    with open(jpath, "w", encoding="utf-8") as fh:
        json.dump(review, fh, indent=2)

    md = [f"# Performance review: {args.agent}", "",
          f"VERDICT: {verdict}", f"Reason: {reason}", "",
          f"Window: {start.date().isoformat()} to {as_of.isoformat()} ({args.window_days} days), {n} dispatches.", "",
          "| Dimension | Score | Weight |", "|---|---|---|"]
    for k in WEIGHTS:
        md.append(f"| {k} | {scores[k]} | {int(WEIGHTS[k]*100)}% |")
    md += [f"| composite | {composite} | raw {raw}" + (f", capped: {cap_reason}" if cap else "") + " |", "",
           f"Trend: {trend}" + (f" ({trend_delta:+} points first half to second half)" if trend_delta is not None else ""),
           f"Complexity-3 tasks accepted: {complex_accepted}", ""]
    if by_type:
        md += ["| Task type | Dispatches | Share | Acceptance |", "|---|---|---|---|"]
        md += [f"| {t} | {v['dispatches']} | {v['share']}% | {v['acceptance']}% |" for t, v in by_type.items()]
        md.append("")
    md.append("## Findings")
    md += [f"- {f}" for f in findings] or ["- No weaknesses above the thresholds."]
    md += ["", "## Evidence (weakest dispatches)"]
    md += [f"- {e['dispatch_id']} {e['outcome']}, rework {e['rework_rounds']}, scope violations {e['scope_violations']}"
           + (", fabrication" if e["fabrication"] else "") + f": {e['task']}" + (f" ({e['notes']})" if e["notes"] else "") for e in evidence] or ["- none"]
    md += ["", "## Action", VERDICT_TEXT[verdict], f"Re-review date: {review['re_review_date']}", ""]
    mpath = os.path.join(out_dir, f"review_{args.agent}.md")
    with open(mpath, "w", encoding="utf-8") as fh:
        fh.write("\n".join(md))
    print(f"VERDICT: {verdict} (composite {composite}, {n} dispatches)")
    print(f"wrote {jpath}")
    print(f"wrote {mpath}")


if __name__ == "__main__":
    main()
