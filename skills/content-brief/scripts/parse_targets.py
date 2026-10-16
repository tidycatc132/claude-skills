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
trailing `# comments` are dropped. The optional `existing_url` key passes through.
With --normalize each row also gets `format_primary`, `format_embedded`,
`format_normalized`, `mode` (new | refresh) and `problems` (see
references/input-contract.md). With --id, only that target is printed
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


PRIMARY = {"explainer", "how-to", "comparison", "listicle", "definition", "cost-guide", "buyers-guide",
           "troubleshooting", "checklist", "service-page", "location-page", "product-page", "faq-page", "pillar-guide"}
EMBEDDED = {"faq", "comparison-table", "steps", "checklist", "cost-table"}
# alias -> (as primary, as embedded); None means it cannot sit in that position
ALIASES = {
    "explainer": ("explainer", None), "blog post": ("explainer", None), "article": ("explainer", None),
    "blog article": ("explainer", None), "guide": ("explainer", None),
    "ultimate guide": ("pillar-guide", None), "complete guide": ("pillar-guide", None),
    "pillar": ("pillar-guide", None), "pillar guide": ("pillar-guide", None),
    "comparison": ("comparison", "comparison-table"), "vs": ("comparison", "comparison-table"),
    "versus": ("comparison", "comparison-table"), "comparison table": ("comparison", "comparison-table"),
    "how-to": ("how-to", "steps"), "how to": ("how-to", "steps"), "tutorial": ("how-to", "steps"),
    "step-by-step": ("how-to", "steps"), "steps": ("how-to", "steps"),
    "listicle": ("listicle", None), "best": ("listicle", None), "top": ("listicle", None),
    "list": ("listicle", None), "roundup": ("listicle", None),
    "definition": ("definition", None), "what is": ("definition", None), "glossary": ("definition", None),
    "cost guide": ("cost-guide", "cost-table"), "pricing guide": ("cost-guide", "cost-table"),
    "price": ("cost-guide", "cost-table"), "cost table": ("cost-guide", "cost-table"),
    "buyer's guide": ("buyers-guide", None), "buyers guide": ("buyers-guide", None),
    "troubleshooting": ("troubleshooting", None), "problem": ("troubleshooting", None),
    "signs": ("troubleshooting", None),
    "checklist": ("checklist", "checklist"),
    "service page": ("service-page", None), "service": ("service-page", None), "landing page": ("service-page", None),
    "location page": ("location-page", None), "city page": ("location-page", None),
    "product page": ("product-page", None),
    "faq": ("faq-page", "faq"), "faq page": ("faq-page", "faq"), "q&a": ("faq-page", "faq"),
    "faq block": ("faq-page", "faq"),
}


def normalize_format(raw) -> tuple[str | None, list[str], bool, str | None]:
    """Return (primary, embedded, changed, problem)."""
    text = str(raw or "").strip().lower()
    if not text:
        return None, [], False, "format is empty"
    parts = [p.strip() for p in re.split(r"\s*(?:\+|,|/|\band\b)\s*", text) if p.strip()]
    primary, embedded = None, []
    for i, p in enumerate(parts):
        key = p.replace("-", " ") if p.replace("-", " ") in ALIASES else p
        if p in PRIMARY and i == 0:
            hit = (p, None)
        elif p in EMBEDDED and i > 0:
            hit = (None, p)
        else:
            hit = ALIASES.get(key) or ALIASES.get(p)
        if not hit:
            return None, [], False, f"unknown format value {p!r} in {raw!r}"
        if i == 0:
            if not hit[0]:
                return None, [], False, f"{p!r} cannot be a primary format"
            primary = hit[0]
        else:
            if not hit[1]:
                return None, [], False, f"{p!r} cannot be embedded in another format"
            embedded.append(hit[1])
    changed = len(parts) > 1  # a combo; a plain alias ("blog post" -> explainer) is not a concern
    return primary, list(dict.fromkeys(embedded)), changed, None


def infer_existing_url(t: dict, report: str) -> tuple[str | None, str | None]:
    """keyword-research marks refreshes in prose, not in the row: a Content Calendar row whose page cell
    reads '/path/ refresh', a Topic Clusters member '"keyword" ... exists (/path/)', or a pillar line
    'Pillar: "keyword" ... refresh'. Return (url, where) or (None, None)."""
    kw = str(t.get("primary_keyword") or "").strip().lower()
    if not kw:
        return None, None
    for line in report.splitlines():
        s = line.strip()
        if s.startswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            if any(c.lower() == kw for c in cells):
                for c in cells:
                    m = re.match(r"^(/\S*)\s+refresh\b", c, re.I)
                    if m:
                        return m.group(1), "content calendar"
        elif f'"{kw}"' in s.lower():
            m = re.search(r"exists \((/[^)\s]+)\)", s)
            if m:
                return m.group(1), "topic clusters"
            if re.match(r"(?i)^pillar:", s) and re.search(r"(?i)\brefresh\b", s):
                pu = str(t.get("pillar_url") or "")
                if pu.startswith("/"):
                    return pu, "topic clusters (pillar refresh)"
    return None, None


def normalize(t: dict, report: str = "") -> dict:
    out = dict(t)
    prim, emb, changed, prob = normalize_format(t.get("format"))
    out["format_primary"], out["format_embedded"], out["format_normalized"] = prim, emb, changed
    if not t.get("existing_url") or t.get("existing_url") == "N/A":
        url, where = infer_existing_url(t, report)
        if url:
            out["existing_url"], out["existing_url_source"] = url, where
    eu = out.get("existing_url")
    out["mode"] = "refresh" if eu and eu != "N/A" else "new"
    probs = []
    if not str(t.get("primary_keyword") or "").strip():
        probs.append("primary_keyword is missing")
    if prob:
        probs.append(prob)
    out["problems"] = probs
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("report", nargs="?")
    ap.add_argument("--id")
    ap.add_argument("--out")
    ap.add_argument("--validate", metavar="TARGETS_JSON")
    ap.add_argument("--normalize", action="store_true",
                    help="add format_primary, format_embedded, format_normalized, mode and problems to each row")
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
        report_text = Path(a.report).read_text(encoding="utf-8")
        items = parse(report_text)
    except (OSError, ValueError) as e:
        print(f"ERROR {e}", file=sys.stderr)
        return 2
    for b in problems(items):
        print(f"WARN {b}", file=sys.stderr)
    if a.normalize:
        items = [normalize(t, report_text) for t in items]
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
