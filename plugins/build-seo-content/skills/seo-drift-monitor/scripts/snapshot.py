#!/usr/bin/env python3
"""Capture an SEO snapshot of a site as one JSON file.

Sources (combine freely):
  --html-dir DIR        saved pages; DIR/manifest.csv maps `url,file[,status]`
  --manifest FILE       manifest path when it is not DIR/manifest.csv
  --urls FILE           one URL per line, fetched live
  --sitemap URL         fetch an XML sitemap (or sitemap index) and crawl its <loc> URLs
  --rankings FILE       CSV with `keyword,url,position` (position blank or 0 = not ranking)
  --indexed-count N     indexed page count from Search Console or a site: query

Output: --out PATH (default seo-drift/<YYYY-MM-DD>.json). Standard library only.

Examples
  python3 snapshot.py --html-dir baseline --rankings baseline/rankings.csv --out seo-drift/baseline.json
  python3 snapshot.py --urls urls.txt --indexed-count 412 --out seo-drift/2026-10-12.json
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import sys
import time
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

SCHEMA_VERSION = 1
DEFAULT_UA = "Mozilla/5.0 (compatible; seo-drift-monitor/1.0; +https://example.invalid/bot)"
SKIP_TEXT_TAGS = {"script", "style", "noscript", "template", "svg"}


class PageParser(HTMLParser):
    """Collects the SEO-relevant parts of one HTML document."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.meta_description: str | None = None
        self.robots: str | None = None
        self.canonical: str | None = None
        self.lang: str | None = None
        self.h1: list[str] = []
        self.hreflang_count = 0
        self.jsonld_blobs: list[str] = []
        self.itemtypes: list[str] = []
        self.words = 0
        self._in_title = False
        self._in_h1 = False
        self._h1_parts: list[str] = []
        self._in_jsonld = False
        self._jsonld_parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "html" and a.get("lang"):
            self.lang = a["lang"].strip()
        elif tag == "title":
            self._in_title = True
        elif tag == "meta":
            name = a.get("name", "").strip().lower()
            if name == "description" and self.meta_description is None:
                self.meta_description = a.get("content", "").strip()
            elif name == "robots":
                self.robots = a.get("content", "").strip()
        elif tag == "link":
            rel = a.get("rel", "").lower().split()
            if "canonical" in rel and self.canonical is None:
                self.canonical = a.get("href", "").strip()
            if "alternate" in rel and a.get("hreflang"):
                self.hreflang_count += 1
        elif tag == "h1":
            self._in_h1 = True
            self._h1_parts = []
        elif tag == "script":
            if a.get("type", "").strip().lower() == "application/ld+json":
                self._in_jsonld = True
                self._jsonld_parts = []
            else:
                self._skip_depth += 1
        elif tag in SKIP_TEXT_TAGS:
            self._skip_depth += 1
        if "itemtype" in a and "itemscope" in a:
            self.itemtypes.append(a["itemtype"].strip())

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag == "h1" and self._in_h1:
            self._in_h1 = False
            text = " ".join(" ".join(self._h1_parts).split())
            if text:
                self.h1.append(text)
        elif tag == "script":
            if self._in_jsonld:
                self._in_jsonld = False
                self.jsonld_blobs.append("".join(self._jsonld_parts))
            elif self._skip_depth:
                self._skip_depth -= 1
        elif tag in SKIP_TEXT_TAGS and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data):
        if self._in_title:
            self.title_parts.append(data)
        elif self._in_jsonld:
            self._jsonld_parts.append(data)
        elif self._skip_depth == 0:
            if self._in_h1:
                self._h1_parts.append(data)
            self.words += len(data.split())


def _collect_types(node, out: set[str]) -> None:
    """Top-level @type values, descending only through @graph."""
    if isinstance(node, list):
        for item in node:
            _collect_types(item, out)
    elif isinstance(node, dict):
        t = node.get("@type")
        if isinstance(t, str):
            out.add(t.strip())
        elif isinstance(t, list):
            out.update(str(x).strip() for x in t)
        if "@graph" in node:
            _collect_types(node["@graph"], out)


def parse_html(html: str, url: str) -> dict:
    p = PageParser()
    try:
        p.feed(html)
        p.close()
    except Exception as e:  # malformed markup should degrade, not abort the snapshot
        return {"parse_error": str(e)[:200]}
    types: set[str] = set()
    for blob in p.jsonld_blobs:
        try:
            _collect_types(json.loads(blob), types)
        except json.JSONDecodeError:
            types.add("INVALID_JSON_LD")
    for it in p.itemtypes:
        types.add(it.rstrip("/").rsplit("/", 1)[-1])
    robots = (p.robots or "").lower()
    tokens = {t.strip() for t in robots.split(",")}
    title = " ".join("".join(p.title_parts).split())
    canonical = urljoin(url, p.canonical) if p.canonical else ""
    return {
        "title": title,
        "meta_description": p.meta_description or "",
        "canonical": canonical,
        "robots": p.robots or "",
        "noindex": "noindex" in tokens or "none" in tokens,
        "nofollow": "nofollow" in tokens or "none" in tokens,
        "h1": p.h1,
        "schema_types": sorted(types),
        "hreflang_count": p.hreflang_count,
        "lang": p.lang or "",
        "word_count": p.words,
    }


def empty_page() -> dict:
    """Field set for a page that returned no usable HTML (non-200)."""
    return {"title": "", "meta_description": "", "canonical": "", "robots": "", "noindex": False, "nofollow": False, "h1": [], "schema_types": [], "hreflang_count": 0, "lang": "", "word_count": 0}


def apply_x_robots(page: dict, header: str | None) -> None:
    page["x_robots_tag"] = header or ""
    if header:
        tokens = {t.strip() for t in header.lower().split(",")}
        if "noindex" in tokens or "none" in tokens:
            page["noindex"] = True
        if "nofollow" in tokens or "none" in tokens:
            page["nofollow"] = True


def fetch(url: str, ua: str, timeout: int) -> tuple[int, str, dict, str]:
    """Returns (status, final_url, headers, body)."""
    req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept": "text/html,*/*;q=0.8"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read(2_000_000)
            charset = resp.headers.get_content_charset() or "utf-8"
            return resp.status, resp.geturl(), dict(resp.headers), body.decode(charset, errors="replace")
    except urllib.error.HTTPError as e:
        body = e.read(500_000) if e.fp else b""
        return e.code, url, dict(e.headers or {}), body.decode("utf-8", errors="replace")


def snapshot_live(urls: list[str], ua: str, delay: float, timeout: int, log) -> dict:
    pages: dict[str, dict] = {}
    for i, url in enumerate(urls, 1):
        try:
            status, final_url, headers, body = fetch(url, ua, timeout)
        except Exception as e:
            pages[url] = {"status": 0, "fetch_error": str(e)[:200]}
            log(f"  [{i}/{len(urls)}] {url} -> ERROR {e}")
            continue
        page = parse_html(body, final_url) if status == 200 else empty_page()
        page["status"] = status
        page["redirect_to"] = final_url if final_url.rstrip("/") != url.rstrip("/") else ""
        apply_x_robots(page, headers.get("X-Robots-Tag") or headers.get("x-robots-tag"))
        pages[url] = page
        log(f"  [{i}/{len(urls)}] {url} -> {status}")
        if delay:
            time.sleep(delay)
    return pages


def snapshot_dir(html_dir: Path, manifest: Path, log) -> dict:
    pages: dict[str, dict] = {}
    with manifest.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if not rows or "url" not in rows[0] or "file" not in rows[0]:
        sys.exit(f"error: {manifest} must have columns `url,file` (optional `status`)")
    for row in rows:
        url = row["url"].strip()
        f = html_dir / row["file"].strip()
        status = int((row.get("status") or "200").strip() or 200)
        if not f.exists():
            pages[url] = {"status": 0, "fetch_error": f"file not found: {row['file']}"}
            log(f"  {url} -> missing file {f.name}")
            continue
        html = f.read_text(encoding="utf-8", errors="replace")
        page = parse_html(html, url) if status == 200 else empty_page()
        page["status"] = status
        page["redirect_to"] = ""
        page["x_robots_tag"] = ""
        pages[url] = page
        log(f"  {url} -> {status} ({f.name})")
    return pages


def read_rankings(path: Path) -> dict:
    out: dict[str, dict] = {}
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        cols = {c.lower().strip(): c for c in (reader.fieldnames or [])}
        if "keyword" not in cols or "position" not in cols:
            sys.exit(f"error: {path} must have columns `keyword,url,position`")
        for row in reader:
            kw = (row[cols["keyword"]] or "").strip().lower()
            if not kw:
                continue
            raw = (row[cols["position"]] or "").strip()
            try:
                pos = int(float(raw)) if raw else None
            except ValueError:
                pos = None
            if pos is not None and pos <= 0:
                pos = None
            out[kw] = {"url": (row.get(cols.get("url", ""), "") or "").strip(), "position": pos}
    return out


def read_urls(path: Path) -> list[str]:
    return [l.strip() for l in path.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]


def read_sitemap(url: str, ua: str, timeout: int, log, seen: set | None = None) -> list[str]:
    seen = seen if seen is not None else set()
    if url in seen:
        return []
    seen.add(url)
    status, _, _, body = fetch(url, ua, timeout)
    if status != 200:
        log(f"  sitemap {url} -> {status}")
        return []
    locs = [re.sub(r"\s+", "", m) for m in re.findall(r"<loc>\s*(.*?)\s*</loc>", body, re.I | re.S)]
    if re.search(r"<sitemapindex", body, re.I):
        out: list[str] = []
        for child in locs:
            out.extend(read_sitemap(child, ua, timeout, log, seen))
        return out
    return locs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--html-dir", type=Path)
    ap.add_argument("--manifest", type=Path)
    ap.add_argument("--urls", type=Path)
    ap.add_argument("--sitemap")
    ap.add_argument("--rankings", type=Path)
    ap.add_argument("--indexed-count", type=int)
    ap.add_argument("--site", help="label for the site (default: host of the first URL)")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--max-pages", type=int, default=500)
    ap.add_argument("--delay", type=float, default=0.5, help="seconds between live fetches")
    ap.add_argument("--timeout", type=int, default=20)
    ap.add_argument("--user-agent", default=DEFAULT_UA)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    def log(msg: str) -> None:
        if not args.quiet:
            print(msg, file=sys.stderr)

    if not (args.html_dir or args.urls or args.sitemap or args.rankings or args.indexed_count is not None):
        ap.error("give at least one source: --html-dir, --urls, --sitemap, --rankings or --indexed-count")

    pages: dict[str, dict] = {}
    if args.html_dir:
        manifest = args.manifest or (args.html_dir / "manifest.csv")
        if not manifest.exists():
            sys.exit(f"error: no manifest at {manifest}; create a CSV with columns `url,file[,status]`")
        log(f"reading saved pages from {args.html_dir}")
        pages.update(snapshot_dir(args.html_dir, manifest, log))
    live: list[str] = []
    if args.urls:
        live.extend(read_urls(args.urls))
    if args.sitemap:
        live.extend(read_sitemap(args.sitemap, args.user_agent, args.timeout, log))
    live = list(dict.fromkeys(u for u in live if u not in pages))[: args.max_pages]
    if live:
        log(f"fetching {len(live)} page(s) live")
        pages.update(snapshot_live(live, args.user_agent, args.delay, args.timeout, log))

    rankings = read_rankings(args.rankings) if args.rankings else {}
    first = next(iter(pages), "") or next((r["url"] for r in rankings.values() if r["url"]), "")
    site = args.site or (urlparse(first).netloc if first else "")
    today = dt.date.today().isoformat()
    snap = {
        "schema_version": SCHEMA_VERSION,
        "captured_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "site": site,
        "indexed_count": args.indexed_count,
        "page_count": len(pages),
        "pages": dict(sorted(pages.items())),
        "rankings": dict(sorted(rankings.items())),
    }
    out = args.out or Path("seo-drift") / f"{today}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(snap, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    noindexed = sum(1 for p in pages.values() if p.get("noindex"))
    errors = sum(1 for p in pages.values() if p.get("status") != 200)
    print(f"snapshot written to {out}: {len(pages)} page(s), {noindexed} noindex, {errors} non-200, {len(rankings)} keyword(s), indexed_count={args.indexed_count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
