#!/usr/bin/env python3
"""Deterministic keyword scoring for the keyword-research skill. Standard library only.

Input: a CSV or JSON file (list of objects) with any of these columns. Column names are
matched case-insensitively; `query` is accepted as an alias of `keyword`.

    keyword      required
    volume       monthly searches (number)
    kd           keyword difficulty 0-100
    intent       informational | navigational | commercial | transactional (or I/N/C/T)
    relevance    business relevance 1-5 (a judgment call; label it Estimated unless the user gave it)
    trend        growing | stable | declining, or a number 1-5
    cpc          cost per click (number)
    position     current Google position (number, blank if not ranking)
    impressions  Search Console impressions (number) - used by --position-range
    clicks       Search Console clicks (number)
    source       Measured | User-provided | Calculated | Estimated (label for volume/kd)

Three scores, used in this fixed order:

  A. Priority Score (triage, 1-5)  weighted factor scores -> tier P0..P3
  B. Opportunity Score             (volume x intent value) / max(kd, 1) -> bucket
  C. Impact x Confidence (optional) normalized 0-1 components, needs cpc + position + trend

A score whose inputs are missing is written as N/A. Nothing is ever defaulted to a fake value.

Output: a CSV sorted by the chosen mode plus a markdown table (printed, or --md FILE).

Usage:
  python3 score_keywords.py keywords.csv --out scored.csv --md scored.md
  python3 score_keywords.py gsc.csv --position-range 5 20 --source Measured --out striking.csv
  python3 score_keywords.py --selftest
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import sys
from pathlib import Path

# ----------------------------------------------------------------------------- bands
# A. Priority Score factor weights (sum to 1.0)
W_VOLUME = 0.20
W_KD = 0.25
W_RELEVANCE = 0.30
W_INTENT = 0.15
W_TREND = 0.10

# Volume band: 1 at <=100/mo, 5 at >=10,000/mo, interpolated linearly on log10(volume)
# (100 -> 1, 1,000 -> 3, 10,000 -> 5). Linear on raw volume would score 1,000/mo as 1.4.
VOL_LOW, VOL_HIGH = 100.0, 10000.0
# KD band: 5 at KD <=20, 1 at KD >=80, linear between.
KD_EASY, KD_HARD = 20.0, 80.0

INTENT_MATCH = {"informational": 1, "navigational": 2, "commercial": 4, "transactional": 5}
TREND_SCORE = {"declining": 1, "falling": 1, "stable": 3, "flat": 3, "growing": 5, "rising": 5}

TIERS = [(4.0, "P0"), (3.0, "P1"), (2.0, "P2"), (0.0, "P3")]

# B. Opportunity Score
INTENT_VALUE = {"informational": 1, "navigational": 1, "commercial": 2, "transactional": 3}
HIGH_INTENT = {"commercial", "transactional"}
KD_LOW_MAX, KD_MED_MAX = 39, 69  # low 1-39, medium 40-69, high 70-100
BUCKET_STARS = {"Quick Win": 5, "Growth": 4, "Long-term": 3, "Research": 2, "Hold": 1}

# C. Impact x Confidence weights (each group sums to 1.0)
IMPACT_W = {"volume": 0.40, "cpc": 0.20, "funnel": 0.25, "trend": 0.15}
CONF_W = {"inverse_kd": 0.45, "position": 0.35, "authority": 0.20}
CPC_CAP = 10.0  # cpc normalized 0..1 at $0..$10+
FUNNEL_NORM = {"TOFU": 0.33, "MOFU": 0.66, "BOFU": 1.0}
POSITION_NORM = [(10, 1.0), (20, 0.8), (50, 0.5), (100, 0.3)]  # (max position, confidence)
POSITION_NONE = 0.2

# Funnel signal words
BOFU_WORDS = ("pricing", "price", "cost", "best", " vs ", "versus", "services", "service", "agency",
              "hire", "buy", "near me", "quote", "company", "companies", "contractor", "installation",
              "repair", "replacement", "emergency", "cleaning", "detection", "testing", "inspection")
MOFU_WORDS = ("how to", "guide", "roi", "case study", "review", "comparison", "compare", "checklist",
              "template", "examples", "tips")

OUT_COLUMNS = ["keyword", "volume", "kd", "intent", "funnel", "relevance", "trend", "cpc", "position",
               "impressions", "clicks", "source", "priority_score", "tier", "intent_value",
               "opportunity_score", "bucket", "impact", "confidence", "impact_confidence"]
NA = "N/A"


# ----------------------------------------------------------------------------- parsing
def _num(v) -> float | None:
    if v is None:
        return None
    s = str(v).strip().replace(",", "").replace("$", "")
    if s == "" or s.upper() in ("N/A", "NA", "NONE", "NULL", "-"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def norm_intent(v) -> str | None:
    if v is None:
        return None
    s = str(v).strip().lower()
    if not s:
        return None
    alias = {"i": "informational", "info": "informational", "n": "navigational", "nav": "navigational",
             "c": "commercial", "t": "transactional", "trans": "transactional"}
    s = alias.get(s, s)
    return s if s in INTENT_MATCH else None


def trend_score(v) -> float | None:
    if v is None:
        return None
    s = str(v).strip().lower()
    if s in TREND_SCORE:
        return float(TREND_SCORE[s])
    n = _num(s)
    if n is not None and 1 <= n <= 5:
        return n
    return None


def funnel_stage(keyword: str, intent: str | None) -> str:
    k = f" {keyword.lower()} "
    if intent in HIGH_INTENT or any(w in k for w in BOFU_WORDS):
        return "BOFU"
    if any(w in k for w in MOFU_WORDS):
        return "MOFU"
    return "TOFU"


def read_rows(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8-sig")
    if path.suffix.lower() == ".json":
        data = json.loads(text)
        rows = data if isinstance(data, list) else data.get("keywords", data.get("rows", []))
    else:
        rows = list(csv.DictReader(io.StringIO(text)))
    out = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        low = {str(k).strip().lower(): v for k, v in r.items() if k is not None}
        if "keyword" not in low and "query" in low:
            low["keyword"] = low.pop("query")
        if str(low.get("keyword", "")).strip():
            out.append(low)
    return out


# ----------------------------------------------------------------------------- scores
def volume_factor(volume: float) -> float:
    if volume <= VOL_LOW:
        return 1.0
    if volume >= VOL_HIGH:
        return 5.0
    return 1.0 + 4.0 * (math.log10(volume) - math.log10(VOL_LOW)) / (math.log10(VOL_HIGH) - math.log10(VOL_LOW))


def kd_factor(kd: float) -> float:
    if kd <= KD_EASY:
        return 5.0
    if kd >= KD_HARD:
        return 1.0
    return 1.0 + 4.0 * (KD_HARD - kd) / (KD_HARD - KD_EASY)


def priority_score(volume, kd, relevance, intent, trend) -> float | None:
    if None in (volume, kd, relevance, intent, trend):
        return None
    if not 1 <= relevance <= 5:
        return None
    s = (W_VOLUME * volume_factor(volume) + W_KD * kd_factor(kd) + W_RELEVANCE * relevance
         + W_INTENT * INTENT_MATCH[intent] + W_TREND * trend)
    return round(s, 2)


def tier_for(score: float | None) -> str:
    if score is None:
        return NA
    for floor, name in TIERS:
        if score >= floor:
            return name
    return "P3"


def opportunity_score(volume, kd, intent) -> float | None:
    if None in (volume, kd, intent):
        return None
    return round(volume * INTENT_VALUE[intent] / max(kd, 1.0), 2)


def bucket_for(kd, intent) -> str:
    if None in (kd, intent):
        return NA
    high = intent in HIGH_INTENT
    if kd <= KD_LOW_MAX:
        return "Quick Win" if high else "Research"
    if kd <= KD_MED_MAX:
        return "Growth" if high else "Hold"
    return "Long-term" if high else "Hold"


def position_conf(position: float | None) -> float:
    if position is None:
        return POSITION_NONE
    for max_pos, conf in POSITION_NORM:
        if position <= max_pos:
            return conf
    return POSITION_NONE


def impact_confidence(volume, kd, cpc, funnel, trend, position, relevance):
    """Returns (impact, confidence, product) or (None, None, None) when a required input is missing.
    Required: volume, kd, cpc, trend, position (blank position counts as 'not ranking', which is a
    known value only when the column exists at all)."""
    if None in (volume, kd, cpc, trend) or position is _MISSING_COL:
        return None, None, None
    vol_n = (volume_factor(volume) - 1.0) / 4.0
    cpc_n = min(max(cpc, 0.0), CPC_CAP) / CPC_CAP
    trend_n = (trend - 1.0) / 4.0
    impact = (IMPACT_W["volume"] * vol_n + IMPACT_W["cpc"] * cpc_n
              + IMPACT_W["funnel"] * FUNNEL_NORM[funnel] + IMPACT_W["trend"] * trend_n)
    authority = ((relevance - 1.0) / 4.0) if relevance is not None else 0.5
    conf = (CONF_W["inverse_kd"] * (1.0 - min(max(kd, 0.0), 100.0) / 100.0)
            + CONF_W["position"] * position_conf(position) + CONF_W["authority"] * authority)
    return round(impact, 3), round(conf, 3), round(impact * conf, 3)


_MISSING_COL = object()


def score_row(r: dict, has_position_col: bool) -> dict:
    keyword = str(r.get("keyword", "")).strip()
    volume = _num(r.get("volume"))
    kd = _num(r.get("kd"))
    intent = norm_intent(r.get("intent"))
    relevance = _num(r.get("relevance"))
    trend = trend_score(r.get("trend"))
    cpc = _num(r.get("cpc"))
    position = _num(r.get("position")) if has_position_col else _MISSING_COL
    funnel = funnel_stage(keyword, intent)
    pri = priority_score(volume, kd, relevance, intent, trend)
    opp = opportunity_score(volume, kd, intent)
    imp, conf, ic = impact_confidence(volume, kd, cpc, funnel, trend,
                                      position, relevance)

    def fmt(v, digits=None):
        if v is None or v is _MISSING_COL:
            return NA
        if digits is None:
            return str(int(v)) if float(v).is_integer() else str(v)
        return f"{v:.{digits}f}"

    return {
        "keyword": keyword,
        "volume": fmt(volume),
        "kd": fmt(kd),
        "intent": intent or NA,
        "funnel": funnel,
        "relevance": fmt(relevance),
        "trend": str(r.get("trend", "")).strip() or NA,
        "cpc": fmt(cpc),
        "position": fmt(position),
        "impressions": fmt(_num(r.get("impressions"))),
        "clicks": fmt(_num(r.get("clicks"))),
        "source": str(r.get("source", "")).strip() or NA,
        "priority_score": fmt(pri, 2),
        "tier": tier_for(pri),
        "intent_value": str(INTENT_VALUE[intent]) if intent else NA,
        "opportunity_score": fmt(opp, 2),
        "bucket": bucket_for(kd, intent),
        "impact": fmt(imp, 3),
        "confidence": fmt(conf, 3),
        "impact_confidence": fmt(ic, 3),
    }


# ----------------------------------------------------------------------------- ordering / output
def _sort_key_num(row: dict, col: str) -> float:
    v = _num(row.get(col))
    return -v if v is not None else float("inf")


def sort_rows(rows: list[dict], mode: str) -> list[dict]:
    if mode == "triage":
        return sorted(rows, key=lambda r: (_sort_key_num(r, "priority_score"), _sort_key_num(r, "opportunity_score"), r["keyword"]))
    if mode == "opportunity":
        return sorted(rows, key=lambda r: (_sort_key_num(r, "opportunity_score"), r["keyword"]))
    if mode == "impact":
        return sorted(rows, key=lambda r: (_sort_key_num(r, "impact_confidence"), r["keyword"]))
    if mode == "striking":
        return sorted(rows, key=lambda r: (_sort_key_num(r, "impressions"), _sort_key_num(r, "position") * -1, r["keyword"]))
    # all: tier first, then opportunity inside the tier
    return sorted(rows, key=lambda r: (_sort_key_num(r, "priority_score"), _sort_key_num(r, "opportunity_score"), r["keyword"]))


def filter_positions(rows: list[dict], lo: float, hi: float) -> list[dict]:
    out = []
    for r in rows:
        p = _num(r.get("position"))
        if p is not None and lo <= p <= hi:
            out.append(r)
    return out


def to_csv(rows: list[dict]) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=OUT_COLUMNS, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow(r)
    return buf.getvalue()


def to_markdown(rows: list[dict], mode: str) -> str:
    if mode == "striking":
        cols = ["keyword", "position", "impressions", "clicks", "funnel", "intent", "source"]
    elif mode == "impact":
        cols = ["keyword", "volume", "kd", "cpc", "position", "funnel", "impact", "confidence", "impact_confidence"]
    elif mode == "opportunity":
        cols = ["keyword", "volume", "kd", "intent", "funnel", "opportunity_score", "bucket", "stars"]
    else:
        cols = ["keyword", "volume", "kd", "intent", "funnel", "priority_score", "tier", "opportunity_score", "bucket", "stars"]
    lines = []
    if mode == "striking":
        lines.append("Striking distance: these queries already rank roughly 5 to 20, so a title rewrite, deeper content "
                     "and internal links can move them in weeks, where a new page takes months. Volume and KD are N/A "
                     "until a metrics tool supplies them; position, impressions and clicks are Measured.\n")
    lines += ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for r in rows:
        cells = []
        for c in cols:
            if c == "stars":
                n = BUCKET_STARS.get(r["bucket"])
                cells.append("★" * n if n else NA)
            else:
                cells.append(str(r.get(c, NA)))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


# ----------------------------------------------------------------------------- selftest
def selftest() -> int:
    rows = [
        {"keyword": "emergency plumber denver", "volume": "1900", "kd": "35", "intent": "transactional",
         "relevance": "5", "trend": "stable", "cpc": "38.5", "position": "14", "source": "Measured"},
        {"keyword": "how to fix a leaking faucet", "volume": "12100", "kd": "22", "intent": "informational",
         "relevance": "2", "trend": "stable", "cpc": "0.9", "position": "", "source": "Measured"},
        {"keyword": "plumber near me", "volume": "74000", "kd": "78", "intent": "T",
         "relevance": "5", "trend": "stable", "cpc": "22.1", "position": "", "source": "Measured"},
        {"keyword": "best water heater for hard water", "volume": "720", "kd": "33", "intent": "commercial",
         "relevance": "4", "trend": "growing", "cpc": "3.8", "position": "", "source": "Measured"},
        {"keyword": "plumbing services", "volume": "33100", "kd": "", "intent": "commercial",
         "relevance": "4", "trend": "declining", "cpc": "18", "position": "", "source": "Measured"},
    ]
    scored = {r["keyword"]: r for r in (score_row(x, True) for x in rows)}
    checks = []
    a = scored["emergency plumber denver"]
    # volume factor: 1 + 4*(log10(1900)-2)/2 = 3.558; kd factor: 1 + 4*45/60 = 4.0
    # 0.2*3.558 + 0.25*4 + 0.3*5 + 0.15*5 + 0.1*3 = 4.26
    checks.append(("A priority", a["priority_score"] == "4.26" and a["tier"] == "P0"))
    checks.append(("A opportunity", a["opportunity_score"] == "162.86" and a["bucket"] == "Quick Win"))
    checks.append(("A funnel", a["funnel"] == "BOFU"))
    # impact: vol_n 0.6395*0.4=0.2558, cpc 1.0*0.2=0.2, funnel 1.0*0.25=0.25, trend 0.5*0.15=0.075 -> 0.781
    # conf: 0.65*0.45=0.2925, position 14 -> 0.8*0.35=0.28, authority 1.0*0.2=0.2 -> 0.772
    checks.append(("A impact", a["impact"] == "0.781" and a["confidence"] == "0.772" and a["impact_confidence"] == "0.603"))
    b = scored["how to fix a leaking faucet"]
    # 0.2*5 + 0.25*4.867 + 0.3*2 + 0.15*1 + 0.1*3 = 1+1.2167+0.6+0.15+0.3 = 3.27
    checks.append(("B priority", b["priority_score"] == "3.27" and b["tier"] == "P1"))
    checks.append(("B bucket", b["bucket"] == "Research" and b["funnel"] == "MOFU" and b["opportunity_score"] == "550.00"))
    c = scored["plumber near me"]
    # vol 5, kd 1.133, rel 5, intent 5, trend 3 -> 1 + 0.2833 + 1.5 + 0.75 + 0.3 = 3.83
    checks.append(("C alias + priority", c["intent"] == "transactional" and c["priority_score"] == "3.83" and c["tier"] == "P1"))
    checks.append(("C long-term", c["bucket"] == "Long-term" and c["opportunity_score"] == "2846.15"))
    d = scored["best water heater for hard water"]
    # vol 1+4*(2.857-2)/2 = 2.715; kd 1+4*47/60=4.133; -> 0.543+1.033+1.2+0.6+0.5 = 3.88
    checks.append(("D priority", d["priority_score"] == "3.88" and d["tier"] == "P1" and d["bucket"] == "Quick Win"))
    e = scored["plumbing services"]
    checks.append(("E missing kd -> N/A", e["priority_score"] == NA and e["tier"] == NA
                   and e["opportunity_score"] == NA and e["bucket"] == NA and e["impact_confidence"] == NA))
    checks.append(("E funnel still computed", e["funnel"] == "BOFU"))
    # striking-distance filter and ordering
    sd = filter_positions([{"keyword": "x", "position": "4.9"}, {"keyword": "y", "position": "5"},
                           {"keyword": "z", "position": "20"}, {"keyword": "w", "position": "20.1"},
                           {"keyword": "v", "position": ""}], 5, 20)
    checks.append(("striking filter", [r["keyword"] for r in sd] == ["y", "z"]))
    ordered = sort_rows(list(scored.values()), "all")
    checks.append(("sort all", [r["keyword"] for r in ordered][:2] == ["emergency plumber denver", "best water heater for hard water"]
                   and ordered[-1]["keyword"] == "plumbing services"))
    md = to_markdown(ordered, "all")
    checks.append(("markdown", md.startswith("| keyword |") and "★★★★★" in md))
    failed = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  {'ok ' if ok else 'FAIL'} {n}")
    if failed:
        print(f"selftest: {len(failed)} of {len(checks)} checks failed: {failed}")
        return 1
    print(f"selftest: {len(checks)}/{len(checks)} passed")
    return 0


# ----------------------------------------------------------------------------- main
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", nargs="?", help="CSV or JSON file of keywords")
    ap.add_argument("--mode", choices=["all", "triage", "opportunity", "impact", "striking"], default="all",
                    help="which score orders the output (all = tier, then opportunity). striking = by impressions")
    ap.add_argument("--position-range", nargs=2, type=float, metavar=("LO", "HI"),
                    help="keep only rows whose position is within LO..HI (striking distance, e.g. 5 20)")
    ap.add_argument("--source", help="label to write into blank 'source' cells, e.g. Measured for a tool export")
    ap.add_argument("--out", help="write the scored CSV here (default: print)")
    ap.add_argument("--md", help="write the markdown table here (default: print)")
    ap.add_argument("--selftest", action="store_true", help="run the built-in checks and exit")
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()
    if not args.input:
        ap.error("an input file is required (or --selftest)")
    path = Path(args.input)
    if not path.exists():
        print(f"error: {path} does not exist", file=sys.stderr)
        return 2
    try:
        rows = read_rows(path)
    except (json.JSONDecodeError, csv.Error, UnicodeDecodeError) as e:
        print(f"error: could not parse {path}: {e}", file=sys.stderr)
        return 2
    if not rows:
        print("error: no rows with a keyword found", file=sys.stderr)
        return 2
    if args.source:
        for r in rows:
            if not str(r.get("source", "")).strip():
                r["source"] = args.source
    has_position_col = any("position" in r for r in rows)
    if args.position_range:
        rows = filter_positions(rows, *args.position_range)
        if args.mode == "all":
            args.mode = "striking"
    scored = sort_rows([score_row(r, has_position_col) for r in rows], args.mode)

    csv_text = to_csv(scored)
    md_text = to_markdown(scored, args.mode)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(csv_text, encoding="utf-8")
        print(f"wrote {args.out} ({len(scored)} rows)")
    else:
        print(csv_text)
    if args.md:
        Path(args.md).parent.mkdir(parents=True, exist_ok=True)
        Path(args.md).write_text(md_text, encoding="utf-8")
        print(f"wrote {args.md}")
    else:
        print(md_text)
    na = sum(1 for r in scored if r["priority_score"] == NA)
    if na:
        print(f"note: {na} row(s) have N/A priority_score because volume, kd, intent, relevance or trend is missing", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
