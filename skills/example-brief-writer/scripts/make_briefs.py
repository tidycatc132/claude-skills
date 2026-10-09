#!/usr/bin/env python3
"""Turn a topical-map CSV into markdown content briefs.

Usage:
  make_briefs.py topic_map.csv --out-dir briefs     write one file per row
  make_briefs.py topic_map.csv --stdout             print all briefs, separated by ---
"""
import argparse
import csv
import re
import sys
from pathlib import Path

COLUMNS = ["topic", "keyword", "page_type", "priority"]
OUTLINES = {
    "service": (900, ["What it is", "Who it is for", "How it works", "What affects the price", "FAQs", "Next step"]),
    "location": (700, ["Service area", "Local proof", "Services offered here", "FAQs", "Contact"]),
    "blog": (1200, ["Quick answer", "Key points", "Common mistakes", "FAQs", "Related reading"]),
}
CHECKLIST = [
    "The target keyword appears in the title and the first paragraph",
    "Each H2 can be answered on its own",
    "Every claim has a source or is marked for the client to confirm",
]


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "page"


def read_rows(path: str) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header != COLUMNS:
            raise ValueError(f"header {header} does not match the expected columns {COLUMNS}")
        rows = []
        for n, r in enumerate(reader, 2):
            if len(r) != len(COLUMNS):
                raise ValueError(f"line {n} has {len(r)} cells, expected {len(COLUMNS)}")
            row = dict(zip(COLUMNS, r))
            for col in ("topic", "keyword"):
                if not row[col].strip():
                    raise ValueError(f"line {n}: '{col}' is empty")
            if row["page_type"] not in OUTLINES:
                raise ValueError(f"line {n}: page_type '{row['page_type']}' is not one of {sorted(OUTLINES)}")
            if row["priority"] not in ("1", "2", "3"):
                raise ValueError(f"line {n}: priority '{row['priority']}' is not 1, 2 or 3")
            rows.append(row)
    if not rows:
        raise ValueError("the CSV has no data rows")
    return rows


def render(row: dict) -> str:
    words, h2s = OUTLINES[row["page_type"]]
    lines = [
        f"# Brief: {row['topic']}",
        "",
        f"- Target keyword: {row['keyword']}",
        f"- Page type: {row['page_type']}",
        f"- Priority: {row['priority']}",
        f"- Word count target: {words}",
        "",
        "## Outline",
        "",
    ]
    lines += [f"{i}. {h}" for i, h in enumerate(h2s, 1)]
    lines += ["", "## Checklist", ""] + [f"- [ ] {c}" for c in CHECKLIST]
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv_path")
    ap.add_argument("--out-dir", default="briefs")
    ap.add_argument("--stdout", action="store_true")
    args = ap.parse_args()
    try:
        rows = read_rows(args.csv_path)
    except (OSError, ValueError) as e:
        print(f"cannot read topical map: {e}", file=sys.stderr)
        return 1
    rows.sort(key=lambda r: int(r["priority"]))
    if args.stdout:
        print("\n---\n".join(render(r) for r in rows))
        return 0
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for r in rows:
        (out / f"{r['priority']}-{slug(r['topic'])}.md").write_text(render(r), encoding="utf-8")
    print(f"wrote {len(rows)} briefs to {out}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
