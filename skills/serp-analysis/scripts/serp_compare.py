#!/usr/bin/env python3
"""Compare two top-10 SERP snapshots for the same query and decide whether the SERP is volatile.

Usage
  python3 scripts/serp_compare.py serp_a.csv serp_b.csv [--label-a WebSearch] [--label-b "SE Ranking"]
                                   [--out serp_stability.json]
  python3 scripts/serp_compare.py serp_a.csv [--out serp_stability.json]
      With one snapshot the verdict is "unknown" (missing_reason: single source).

Input CSV columns: `position`, `url`, and optionally `title`. Position 1 is the top result.

Volatility rule (references/data-sources-and-corroboration.md §3): the SERP is volatile when the
two sources have a different number one, or fewer than about half of the top-5 URLs in common
(fewer than 3 of 5). Otherwise it is stable. URLs are normalized (scheme, www., trailing slash,
query and fragment ignored) before comparison.

Output `serp_stability.json` keys: source_a, source_b, top10_a, top10_b, same_number_one,
top5_common, top5_common_urls, top10_common, top10_common_urls, domains_common, verdict
(stable | volatile | unknown), missing_reason, stability_input_suggested (0-100, higher = harder;
25 stable, 75 volatile, null unknown), label (Calculated), notes.
Exit 0 on success, 2 on bad input. Standard library only.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit


def norm(url: str) -> str:
    u = url.strip()
    if not u:
        return ""
    if "://" not in u:
        u = "https://" + u
    p = urlsplit(u)
    host = p.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    path = p.path.rstrip("/") or "/"
    return f"{host}{path}"


def domain(url: str) -> str:
    return norm(url).split("/", 1)[0]


def load(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError(f"{path} has no rows")
    cols = {c.strip().lower() for c in rows[0].keys() if c}
    if "url" not in cols or "position" not in cols:
        raise ValueError(f"{path} needs columns `position` and `url`; got {sorted(cols)}")
    out = []
    for r in rows:
        r = {k.strip().lower(): (v or "").strip() for k, v in r.items() if k}
        try:
            pos = int(float(r["position"]))
        except ValueError:
            continue
        if r["url"]:
            out.append({"position": pos, "url": r["url"], "title": r.get("title", ""), "key": norm(r["url"])})
    out.sort(key=lambda r: r["position"])
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("snapshot_a")
    ap.add_argument("snapshot_b", nargs="?")
    ap.add_argument("--label-a", default=None)
    ap.add_argument("--label-b", default=None)
    ap.add_argument("--out", default="serp_stability.json")
    args = ap.parse_args()

    try:
        a = load(Path(args.snapshot_a))
        b = load(Path(args.snapshot_b)) if args.snapshot_b else None
    except (OSError, ValueError) as e:
        print(f"serp_compare: {e}", file=sys.stderr)
        return 2

    label_a = args.label_a or Path(args.snapshot_a).stem
    res = {
        "source_a": label_a,
        "source_b": None,
        "top10_a": [{"position": r["position"], "url": r["url"]} for r in a[:10]],
        "top10_b": [],
        "same_number_one": None,
        "top5_common": None,
        "top5_common_urls": [],
        "top10_common": None,
        "top10_common_urls": [],
        "domains_common": None,
        "verdict": "unknown",
        "missing_reason": "single source",
        "stability_input_suggested": None,
        "label": "Calculated",
        "notes": [],
    }
    if b is None:
        res["notes"].append(
            "Only one snapshot given. SERP stability is Unknown; True Difficulty cannot be scored until a second "
            "independent source or rank history is supplied."
        )
        Path(args.out).write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")
        print(f"verdict=unknown (single source); wrote {args.out}")
        return 0

    label_b = args.label_b or Path(args.snapshot_b).stem
    a5 = [r["key"] for r in a[:5]]
    b5 = [r["key"] for r in b[:5]]
    a10 = [r["key"] for r in a[:10]]
    b10 = [r["key"] for r in b[:10]]
    same1 = bool(a and b and a[0]["key"] == b[0]["key"])
    c5 = [k for k in a5 if k in b5]
    c10 = [k for k in a10 if k in b10]
    da = {domain(r["url"]) for r in a[:10]}
    db = {domain(r["url"]) for r in b[:10]}
    volatile = (not same1) or len(c5) < 3
    res.update(
        source_b=label_b,
        top10_b=[{"position": r["position"], "url": r["url"]} for r in b[:10]],
        same_number_one=same1,
        top5_common=len(c5),
        top5_common_urls=c5,
        top10_common=len(c10),
        top10_common_urls=c10,
        domains_common=len(da & db),
        verdict="volatile" if volatile else "stable",
        missing_reason=None,
        stability_input_suggested=75 if volatile else 25,
    )
    reasons = []
    if not same1:
        reasons.append(f"different number one ({a[0]['url']} vs {b[0]['url']})")
    if len(c5) < 3:
        reasons.append(f"only {len(c5)} of the top-5 URLs in common (fewer than 3)")
    if volatile:
        res["notes"].append("Volatile: " + "; ".join(reasons) + ". Keep both lists as separate observations in one conflict_group; do not merge or average them.")
    else:
        res["notes"].append(f"Stable: same number one and {len(c5)} of 5 top-5 URLs in common.")
    res["notes"].append("stability_input_suggested is a Calculated starting value for the 15% SERP-stability input; override only with a stated reason such as rank history.")
    Path(args.out).write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")
    print(f"verdict={res['verdict']} same_number_one={same1} top5_common={len(c5)}/5 top10_common={len(c10)}/10 "
          f"stability_input_suggested={res['stability_input_suggested']}; wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
