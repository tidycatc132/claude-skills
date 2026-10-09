#!/usr/bin/env python3
"""Turn a seed-topic text file into a topical-map CSV on stdout.

Usage: make_map.py seeds.txt > topic_map.csv
Columns: topic, keyword, page_type, priority
"""
import csv
import math
import re
import sys

QUESTION = ("how", "what", "why", "when", "which", "can", "should", "is", "are")
BLOG_WORDS = ("guide", "tips", "vs", "checklist")


def classify(topic: str) -> str:
    """Rules, in order (see references/page-types.md): location, then blog, then service."""
    low = topic.lower()
    if (
        "near me" in low
        or re.search(r"\bin [A-Z][a-z]+", topic)      # "... in Ann Arbor"
        or re.search(r"\b(city|county)\b", low)
        or re.search(r"\b[A-Z]{2}$", topic)           # "... Ann Arbor MI"
    ):
        return "location"
    words = low.split()
    if (words and words[0] in QUESTION) or any(w in words for w in BLOG_WORDS):
        return "blog"
    return "service"


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: make_map.py seeds.txt", file=sys.stderr)
        return 2
    try:
        with open(sys.argv[1], encoding="utf-8") as f:
            seeds = [l.strip() for l in f if l.strip() and not l.lstrip().startswith("#")]
    except OSError as e:
        print(f"cannot read seeds: {e}", file=sys.stderr)
        return 1
    if not seeds:
        print("no seed topics found", file=sys.stderr)
        return 1
    w = csv.writer(sys.stdout, lineterminator="\n")
    w.writerow(["topic", "keyword", "page_type", "priority"])
    n = len(seeds)
    for i, s in enumerate(seeds):
        topic = " ".join(s.split())
        keyword = re.sub(r"\s+", " ", topic.lower())
        priority = 1 + min(2, math.floor(3 * i / n))
        w.writerow([topic.title() if topic == topic.lower() else topic, keyword, classify(topic), priority])
    return 0


if __name__ == "__main__":
    sys.exit(main())
