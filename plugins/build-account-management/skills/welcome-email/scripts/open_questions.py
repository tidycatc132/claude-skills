#!/usr/bin/env python3
"""Read the gap questions written by new-build-kickoff and print them as JSON.

  open_questions.py <slug>-gap-questions.md          every question
  open_questions.py <slug>-gap-questions.md --open   only questions whose Answer: line is empty
  open_questions.py --validate questions.json         check a JSON list made by this script

Each item is {"number": int, "question": str, "answer": str}. The answer is the
text after `Answer:` (and any lines under it), empty when the AM left it blank.
Standard library only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

Q_RE = re.compile(r"^(\d+)\.\s+(.+?)\s*$")
A_RE = re.compile(r"^Answer:\s*(.*?)\s*$")


def parse(text: str) -> list[dict]:
    lines = text.replace("\r\n", "\n").split("\n")
    in_q = False
    items: list[dict] = []
    cur: dict | None = None
    in_answer = False
    for line in lines:
        if line.startswith("## "):
            in_q = line.strip() == "## Questions"
            cur, in_answer = None, False
            continue
        if not in_q:
            continue
        m = Q_RE.match(line)
        if m:
            cur = {"number": int(m.group(1)), "question": m.group(2), "answer": ""}
            items.append(cur)
            in_answer = False
            continue
        a = A_RE.match(line)
        if a and cur is not None:
            cur["answer"] = a.group(1)
            in_answer = True
            continue
        if cur is not None and in_answer and line.strip():
            cur["answer"] = (cur["answer"] + " " + line.strip()).strip()
        elif cur is not None and not in_answer and line.strip():
            cur["question"] = cur["question"] + " " + line.strip()
    return items


def validate(data) -> list[str]:
    errs = []
    if not isinstance(data, list):
        return ["top level must be a list"]
    for i, it in enumerate(data):
        if not isinstance(it, dict):
            errs.append(f"item {i} is not an object")
            continue
        if not isinstance(it.get("number"), int):
            errs.append(f"item {i}: number must be an integer")
        if not isinstance(it.get("question"), str) or not it.get("question", "").strip():
            errs.append(f"item {i}: question must be a non-empty string")
        if not isinstance(it.get("answer"), str):
            errs.append(f"item {i}: answer must be a string")
    return errs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", nargs="?")
    ap.add_argument("--open", action="store_true", help="only unanswered questions")
    ap.add_argument("--validate", metavar="JSON")
    args = ap.parse_args()
    if args.validate:
        errs = validate(json.loads(Path(args.validate).read_text(encoding="utf-8")))
        for e in errs:
            print(f"ERROR: {e}", file=sys.stderr)
        if errs:
            return 1
        print("OK")
        return 0
    if not args.path:
        ap.error("give a gap questions file or --validate")
    items = parse(Path(args.path).read_text(encoding="utf-8"))
    if not items:
        print("ERROR: no numbered questions under '## Questions'", file=sys.stderr)
        return 1
    if args.open:
        items = [it for it in items if not it["answer"]]
    print(json.dumps(items, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
