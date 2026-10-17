#!/usr/bin/env python3
"""Build <slug>-url-inventory.csv for new-build-kickoff.

Usage:
  python3 make_inventory.py --out kickoff/<slug>/<slug>-url-inventory.csv --base https://example.com
      [--sitemap sitemap.xml] [--html-dir site/] [--urls crawl.txt] [--type URL=page_type ...]
  python3 make_inventory.py --out kickoff/<slug>/<slug>-url-inventory.csv --no-website

--sitemap   a saved sitemap.xml (or sitemap index file); its URLs are added with status `listed`.
--html-dir  a folder of saved pages; index.html maps to the base URL, about.html to /about, etc.
--urls      a text file, one URL per line, optionally `URL<TAB>title<TAB>status` (from a live crawl).
--type      override the guessed page_type for one URL (repeatable).
Standard library only. Prints the row count.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

COLUMNS = ["url", "title", "page_type", "status", "source"]
PAGE_TYPES = ["home", "about", "service", "location", "contact", "blog", "post", "legal", "other"]


def norm(url: str) -> str:
    p = urlparse(url.strip())
    path = p.path.rstrip("/") or "/"
    return f"{p.scheme or 'https'}://{p.netloc.lower()}{path}"


def guess_type(url: str) -> str:
    path = urlparse(url).path.lower().rstrip("/")
    segs = [s for s in path.split("/") if s]
    if not segs or segs[-1] in ("index.html", "home"):
        return "home"
    joined = "/".join(segs)
    if re.search(r"privacy|terms|legal|cookie|accessibility|disclaimer", joined):
        return "legal"
    if re.search(r"contact|get-in-touch|book|appointment", joined):
        return "contact"
    if re.search(r"about|our-story|team|history|who-we-are", joined):
        return "about"
    if segs[0] in ("blog", "news", "articles", "resources", "insights"):
        return "blog" if len(segs) == 1 else "post"
    if re.search(r"locations?|areas?-served|service-areas?|cities", joined):
        return "location"
    if re.search(r"services?|repair|install|replace|cleaning|treatment|consult|bookkeeping|payroll|plumb|roof", joined):
        return "service"
    return "other"


def title_of(html: str) -> str:
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--base")
    ap.add_argument("--sitemap", action="append", default=[])
    ap.add_argument("--html-dir")
    ap.add_argument("--urls")
    ap.add_argument("--type", action="append", default=[])
    ap.add_argument("--no-website", action="store_true")
    a = ap.parse_args()

    rows: dict[str, dict] = {}
    if not a.no_website:
        if not a.base:
            print("error: --base is required unless --no-website", file=sys.stderr)
            return 2
        base = a.base if "://" in a.base else f"https://{a.base}"
        if a.html_dir:
            for f in sorted(Path(a.html_dir).glob("*.htm*")):
                stem = f.stem
                url = norm(base + ("/" if stem in ("index", "home") else f"/{stem}"))
                rows[url] = {"url": url, "title": title_of(f.read_text(encoding="utf-8", errors="replace")),
                             "status": "saved", "source": "saved"}
        if a.urls:
            for line in Path(a.urls).read_text(encoding="utf-8").splitlines():
                parts = [p.strip() for p in line.split("\t")]
                if not parts[0] or parts[0].startswith("#"):
                    continue
                url = norm(parts[0] if "://" in parts[0] else base + "/" + parts[0].lstrip("/"))
                r = rows.setdefault(url, {"url": url, "title": "", "status": "listed", "source": "crawl"})
                if len(parts) > 1 and parts[1]:
                    r["title"] = parts[1]
                if len(parts) > 2 and parts[2]:
                    r["status"] = parts[2]
        for sm in a.sitemap:
            for loc in re.findall(r"<loc>\s*(.*?)\s*</loc>", Path(sm).read_text(encoding="utf-8", errors="replace")):
                if loc.lower().endswith(".xml"):
                    continue
                url = norm(loc)
                rows.setdefault(url, {"url": url, "title": "", "status": "listed", "source": "sitemap"})

    overrides = {}
    for t in a.type:
        u, _, v = t.rpartition("=")
        if v not in PAGE_TYPES:
            print(f"error: --type {t}: page_type must be one of {PAGE_TYPES}", file=sys.stderr)
            return 2
        overrides[norm(u)] = v

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        w.writeheader()
        for url in sorted(rows, key=lambda u: (urlparse(u).path != "/", u)):
            r = rows[url]
            r["page_type"] = overrides.get(url, guess_type(url))
            w.writerow({k: r[k] for k in COLUMNS})
    print(f"{len(rows)} rows written to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
