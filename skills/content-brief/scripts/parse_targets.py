#!/usr/bin/env python3
"""Read the `targets:` block from a keyword-research report and print it as JSON.

Usage:
  python3 parse_targets.py REPORT.md [--id TARGET_ID] [--out targets.json]
  python3 parse_targets.py --validate TARGETS.json

REPORT.md is the saved keyword-research report. Its last block is

  targets:
    - id: frozen-pipes-what-to-do
      primary_keyword: frozen pipes what to do
      secondary_keywords: [how to thaw frozen pipes, frozen pipes burst]
      metrics: {volume: 880, kd: 14, source: Measured}
      ...

Output: a JSON list of target objects with the keys `id`, `primary_keyword`,
`secondary_keywords`, `intent`, `funnel`, `format`, `cluster`, `pillar_url`,
`geo_candidate`, `geo_answer_format`, `metrics`, `why_now`. Numbers stay
numbers, `true`/`false` become booleans, `N/A` stays the string "N/A",
trailing `# comments` are dropped. With --id, only that target is printed
(exit 2 if it is missing, listing the ids that exist).

--validate checks a JSON list against the same keys and enums and exits 1 on
any problem. Standard library only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

KEYS = ["id", "primary_keyword", "secondary_keywords", "intent", "funnel", "format", "cluster",
        "pillar_url", "geo_candidate", "geo_answer_format", "metrics", "why_now"]
ENUMS = {
    "intent": {"Informational", "Navigational", "Commercial", "Transactional"},
    "funnel": {"TOFU", "MOFU", "BOFU"},
    "geo_answer_format": {"direct answer", "steps", "comparison table", "definition plus example", "FAQ block", "N/A"},
}
METRIC_SOURCES = {"Measured", "User-provided", "Calculated", "Estimated"}


def scalar(v: str):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    if v.lower() == "true":
        return True
    if v.lower() == "false":
        return False
    if re.fullmatch(r"-?\d+", v.replace(",", "")) and v != "N/A":
        return int(v.replace(",", ""))
    if re.fullmatch(r"-?\d+\.\d+", v):
        return float(v)
    return v


def split_top(s: str) -> list[str]:
    """Split on commas not inside brackets or braces."""
    out, depth, cur = [], 0, ""
    for ch in s:
        if ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur)
    return out


def value(v: str):
    v = v.strip()
    if v.startswith("[") and v.endswith("]"):
        return [value(x) for x in split_top(v[1:-1]) if x.strip()]
    if v.startswith("{") and v.endswith("}"):
        d = {}
        for part in split_top(v[1:-1]):
            if ":" in part:
                k, _, val = part.partition(":")
                d[k.strip()] = value(val)
        return d
    return scalar(v)


def strip_comment(line: str) -> str:
    # a ' #' outside brackets starts a comment
    depth = 0
    for i, ch in enumerate(line):
        if ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
        elif ch == "#" and depth == 0 and (i == 0 or line[i - 1] in " \t"):
            return line[:i].rstrip()
    return line.rstrip()


def parse(text: str) -> list[dict]:
    lines = text.replace("\r\n", "\n").split("\n")
    start = next((i for i, l in enumerate(lines) if re.match(r"^\s*targets:\s*$", l)), None)
    if start is None:
        raise ValueError("no `targets:` block found; ask keyword-research to save the report with it")
    items: list[dict] = []
    cur: dict | None = None
    for raw in lines[start + 1:]:
        if raw.strip().startswith("```"):
            break
        line = strip_comment(raw)
        if not line.strip():
            continue
        if not raw.startswith((" ", "\t", "-")):
            break  # next top-level content ends the block
        m = re.match(r"^\s*-\s+([A-Za-z_]+)\s*:\s*(.*)$", line)
        if m:
            cur = {m.group(1): value(m.group(2))}
            items.append(cur)
            continue
        m = re.match(r"^\s+([A-Za-z_]+)\s*:\s*(.*)$", line)
        if m and cur is not None:
            cur[m.group(1)] = value(m.group(2))
    return items


def problems(items: list[dict]) -> list[str]:
    out = []
    if not isinstance(items, list) or not items:
        return ["no targets"]
    seen = set()
    for n, t in enumerate(items, 1):
        tid = t.get("id", f"#{n}")
        for k in KEYS:
            if k not in t:
                out.append(f"{tid}: missing `{k}`")
        for k, allowed in ENUMS.items():
            if k in t and t[k] not in allowed:
                out.append(f"{tid}: `{k}` is {t[k]!r}, expected one of {sorted(allowed)}")
        if not isinstance(t.get("secondary_keywords", []), list):
            out.append(f"{tid}: `secondary_keywords` is not a list")
        m = t.get("metrics")
        if isinstance(m, dict):
            if m.get("source") not in METRIC_SOURCES:
                out.append(f"{tid}: metrics.source is {m.get('source')!r}")
        elif "metrics" in t:
            out.append(f"{tid}: `metrics` is not a mapping")
        if tid in seen:
            out.append(f"{tid}: duplicate id")
        seen.add(tid)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("report", nargs="?")
    ap.add_argument("--id")
    ap.add_argument("--out")
    ap.add_argument("--validate", metavar="TARGETS_JSON")
    a = ap.parse_args()

    if a.validate:
        items = json.loads(Path(a.validate).read_text(encoding="utf-8"))
        bad = problems(items)
        for b in bad:
            print(f"ERROR {b}", file=sys.stderr)
        print(f"{len(items)} target(s), {len(bad)} problem(s)")
        return 1 if bad else 0

    if not a.report:
        ap.error("REPORT.md is required unless --validate is given")
    try:
        items = parse(Path(a.report).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        print(f"ERROR {e}", file=sys.stderr)
        return 2
    for b in problems(items):
        print(f"WARN {b}", file=sys.stderr)
    if a.id:
        hit = [t for t in items if t.get("id") == a.id]
        if not hit:
            print(f"ERROR no target with id {a.id!r}; ids: {', '.join(str(t.get('id')) for t in items)}", file=sys.stderr)
            return 2
        items = hit
    text = json.dumps(items, indent=2, ensure_ascii=False) + "\n"
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text, encoding="utf-8")
        print(f"wrote {a.out} ({len(items)} target(s))")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
