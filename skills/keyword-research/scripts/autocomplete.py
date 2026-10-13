#!/usr/bin/env python3
"""Seed expansion through the unofficial Google suggest endpoint. Standard library only.

WARNING: this endpoint is unofficial and undocumented. It can change or block requests at any
time, and it returns IDEAS ONLY. Nothing it prints is a search volume, difficulty or trend
figure. Label anything that comes from here as a keyword idea with no metrics (N/A).

Usage:
  python3 autocomplete.py "plumber"                 suggestions for the seed alone
  python3 autocomplete.py "plumber" --expand        plus seed + a..z and question/modifier prefixes
  python3 autocomplete.py "plumber" --hl en --gl us language and country hints
  python3 autocomplete.py "plumber" --expand --out ideas.txt

One suggestion per line, deduplicated, in the order found. Calls are spaced ~0.3 s apart.
Exit code 1 on a network failure, with a plain message on stderr.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ENDPOINT = "https://suggestqueries.google.com/complete/search"
DELAY_SECONDS = 0.3
PREFIXES = ("how", "what", "why", "best", "cheap", "is", "can")
SUFFIXES = ("vs", "near me", "cost", "for", "reviews", "pricing")
LETTERS = "abcdefghijklmnopqrstuvwxyz"
USER_AGENT = "keyword-research-skill/1.0 (autocomplete seed expansion; standard library urllib)"


def suggest(query: str, hl: str, gl: str, timeout: float = 10.0) -> list[str]:
    params = urllib.parse.urlencode({"client": "firefox", "q": query, "hl": hl, "gl": gl})
    req = urllib.request.Request(f"{ENDPOINT}?{params}", headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    data = json.loads(raw)
    if not isinstance(data, list) or len(data) < 2 or not isinstance(data[1], list):
        return []
    return [str(s).strip() for s in data[1] if str(s).strip()]


def expansions(seed: str, expand: bool) -> list[str]:
    queries = [seed]
    if expand:
        queries += [f"{seed} {c}" for c in LETTERS]
        queries += [f"{p} {seed}" for p in PREFIXES]
        queries += [f"{seed} {s}" for s in SUFFIXES]
    seen, out = set(), []
    for q in queries:
        if q not in seen:
            seen.add(q)
            out.append(q)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("seed", help="seed keyword, e.g. \"plumber\"")
    ap.add_argument("--expand", action="store_true", help="also query seed + a..z and common question/modifier prefixes")
    ap.add_argument("--hl", default="en", help="interface language (default en)")
    ap.add_argument("--gl", default="us", help="country code (default us)")
    ap.add_argument("--out", help="write suggestions to this file instead of stdout")
    args = ap.parse_args(argv)

    seed = args.seed.strip()
    if not seed:
        print("error: seed is empty", file=sys.stderr)
        return 2
    seen: set[str] = set()
    results: list[str] = []
    queries = expansions(seed, args.expand)
    for i, q in enumerate(queries):
        try:
            found = suggest(q, args.hl, args.gl)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as e:
            print(f"error: could not reach the suggest endpoint ({e}). Network may be blocked; "
                  "use a tool export or ask the user for seeds instead.", file=sys.stderr)
            return 1
        except (json.JSONDecodeError, ValueError) as e:
            print(f"error: unexpected response for {q!r}: {e}", file=sys.stderr)
            return 1
        for s in found:
            key = s.lower()
            if key not in seen:
                seen.add(key)
                results.append(s)
        if i < len(queries) - 1:
            time.sleep(DELAY_SECONDS)
    text = "\n".join(results) + ("\n" if results else "")
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"wrote {len(results)} ideas to {args.out} (ideas only, no volume)")
    else:
        sys.stdout.write(text)
        print(f"# {len(results)} ideas from {len(queries)} queries. Ideas only: no volume, KD or trend.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
