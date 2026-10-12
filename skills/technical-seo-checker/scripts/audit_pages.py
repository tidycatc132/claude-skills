#!/usr/bin/env python3
"""Run the deterministic technical SEO checks on saved pages, robots.txt and a sitemap.

Usage
  python3 scripts/audit_pages.py --manifest manifest.csv [--robots robots.txt] [--sitemap sitemap.xml]
                                 [--out-csv page_checks.csv] [--out-json audit_facts.json]
                                 [--out-md audit_findings.md]

`manifest.csv` columns: `url`, `file` (saved raw HTML, relative to the manifest's folder; empty when
the response had no body), `status` (HTTP status of the final response), optional `final_url`,
`hops` (redirects followed), `x_robots_tag`. Save pages with curl (raw HTML, not a rendered copy).

Checks (scope robots | sitemap | url), each with area, status (pass | warn | fail | info | na),
severity (P0 | P1 | P2 | none), evidence and fix:
  robots: file present, sitemap declared, assets (css/js) blocked, wildcard query block, AI-bot
          policy per bot (info), manifest URLs blocked for Googlebot (P0 if also in the sitemap)
  sitemap: valid XML, url count, lastmod share, identical lastmods, each sitemap URL vs manifest
          (missing from manifest, non-200, redirecting, noindex), indexable pages missing from it
  url: http_status, redirect_hops, title, meta_robots (+ X-Robots-Tag), canonical, viewport,
       h1_count, html_lang, hreflang (self reference, x-default), jsonld (count, types, validity),
       mixed_content, internal_links_to_errors
Severity follows references/http-status-codes.md: P0 blocks indexing (5xx, accidental noindex,
robots block of an important page), P1 suppresses performance (chains, 404s from internal links,
missing viewport, mixed content), P2 hygiene. Core Web Vitals are not checked here: they come from
the PageSpeed Insights API and are scored by hand.
Exit 0 on success, 2 on bad input. Standard library only.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit

AI_BOTS = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "anthropic-ai", "Claude-SearchBot", "Claude-User",
           "Google-Extended", "PerplexityBot", "Perplexity-User", "CCBot", "Googlebot", "Bingbot"]
RESOURCE_TAGS = {"img": "src", "script": "src", "link": "href", "iframe": "src", "video": "src", "audio": "src", "source": "src"}


# --------------------------------------------------------------------------- #
# HTML facts
# --------------------------------------------------------------------------- #
class Facts(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self._in_title = False
        self._in_jsonld = False
        self._jsonld_buf: list[str] = []
        self.jsonld_raw: list[str] = []
        self.meta_robots: list[str] = []
        self.meta_description = ""
        self.viewport = ""
        self.canonical = ""
        self.hreflang: list[tuple[str, str]] = []
        self.h1_count = 0
        self.lang = ""
        self.links: list[str] = []
        self.resources: list[str] = []
        self.words = 0
        self._in_body = False
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "html":
            self.lang = a.get("lang", "")
        elif tag == "title":
            self._in_title = True
        elif tag == "meta":
            name = a.get("name", "").lower()
            if name == "robots":
                self.meta_robots.append(a.get("content", ""))
            elif name == "description":
                self.meta_description = a.get("content", "")
            elif name == "viewport":
                self.viewport = a.get("content", "")
        elif tag == "link":
            rel = a.get("rel", "").lower().split()
            if "canonical" in rel:
                self.canonical = a.get("href", "")
            if "alternate" in rel and a.get("hreflang"):
                self.hreflang.append((a["hreflang"], a.get("href", "")))
        elif tag == "script" and "ld+json" in a.get("type", "").lower():
            self._in_jsonld = True
            self._jsonld_buf = []
        elif tag == "h1":
            self.h1_count += 1
        elif tag == "a" and a.get("href"):
            self.links.append(a["href"])
        elif tag == "body":
            self._in_body = True
        if tag in ("script", "style") and not self._in_jsonld:
            self._skip += 1
        if tag in RESOURCE_TAGS and a.get(RESOURCE_TAGS[tag]):
            if tag != "link" or any(r in ("stylesheet", "preload", "icon") for r in a.get("rel", "").lower().split()):
                self.resources.append(a[RESOURCE_TAGS[tag]])

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag == "script":
            if self._in_jsonld:
                self.jsonld_raw.append("".join(self._jsonld_buf))
                self._in_jsonld = False
            elif self._skip:
                self._skip -= 1
        elif tag == "style" and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        elif self._in_jsonld:
            self._jsonld_buf.append(data)
        elif self._in_body and not self._skip:
            self.words += len(data.split())


def norm(url: str) -> str:
    p = urlsplit(url.strip())
    host = p.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    path = p.path.rstrip("/") or "/"
    return f"{host}{path}" + (f"?{p.query}" if p.query else "")


# --------------------------------------------------------------------------- #
# robots.txt
# --------------------------------------------------------------------------- #
def parse_robots(text: str) -> tuple[list[dict], list[str]]:
    groups: list[dict] = []
    sitemaps: list[str] = []
    cur: dict | None = None
    expecting_agents = False
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, val = (s.strip() for s in line.split(":", 1))
        k = key.lower()
        if k == "sitemap":
            sitemaps.append(val)
        elif k == "user-agent":
            if cur is None or not expecting_agents:
                cur = {"agents": [], "rules": []}
                groups.append(cur)
            cur["agents"].append(val.lower())
            expecting_agents = True
        elif k in ("allow", "disallow") and cur is not None:
            cur["rules"].append((k, val))
            expecting_agents = False
        elif k == "crawl-delay" and cur is not None:
            cur["crawl_delay"] = val
            expecting_agents = False
    return groups, sitemaps


def rule_matches(pattern: str, path: str) -> bool:
    if pattern == "":
        return False
    anchored = pattern.endswith("$")
    pat = pattern[:-1] if anchored else pattern
    rx = "^" + "".join(".*" if ch == "*" else re.escape(ch) for ch in pat) + ("$" if anchored else "")
    return re.match(rx, path) is not None


def group_for(groups: list[dict], agent: str) -> dict | None:
    a = agent.lower()
    for g in groups:
        if a in g["agents"]:
            return g
    for g in groups:
        if "*" in g["agents"]:
            return g
    return None


def robots_decision(groups: list[dict], agent: str, path: str) -> tuple[str, str]:
    g = group_for(groups, agent)
    if g is None:
        return "unspecified", ""
    best = None
    for kind, pat in g["rules"]:
        if pat == "" and kind == "disallow":
            continue
        if rule_matches(pat, path):
            score = (len(pat), kind == "allow")
            if best is None or score > best[0]:
                best = (score, kind, pat)
    if best is None:
        return "allowed", ""
    return ("allowed" if best[1] == "allow" else "blocked"), f"{best[1]}: {best[2]}"


# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--robots")
    ap.add_argument("--sitemap")
    ap.add_argument("--out-csv", default="page_checks.csv")
    ap.add_argument("--out-json", default="audit_facts.json")
    ap.add_argument("--out-md", default="audit_findings.md")
    args = ap.parse_args()

    mpath = Path(args.manifest)
    try:
        with mpath.open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    except OSError as e:
        print(f"audit_pages: cannot read manifest: {e}", file=sys.stderr)
        return 2
    if not rows or not {"url", "file", "status"} <= {c.strip() for c in rows[0].keys() if c}:
        print("audit_pages: manifest needs columns url, file, status", file=sys.stderr)
        return 2

    checks: list[dict] = []

    def add(scope, url, area, check, status, severity, evidence, fix=""):
        checks.append({"scope": scope, "url": url, "area": area, "check": check, "status": status,
                       "severity": severity, "evidence": evidence, "fix": fix})

    pages: dict[str, dict] = {}
    for r in rows:
        r = {k.strip(): (v or "").strip() for k, v in r.items() if k}
        if not r.get("url"):
            continue
        try:
            status = int(r["status"]) if r["status"] else None
        except ValueError:
            print(f"audit_pages: status {r['status']!r} for {r['url']} is not a number", file=sys.stderr)
            return 2
        try:
            hops = int(r["hops"]) if r.get("hops") else 0
        except ValueError:
            hops = 0
        fact = {"url": r["url"], "status": status, "final_url": r.get("final_url") or r["url"], "hops": hops,
                "x_robots_tag": r.get("x_robots_tag", ""), "file": r.get("file", ""), "html": None}
        if fact["file"]:
            fp = (mpath.parent / fact["file"])
            if not fp.exists():
                print(f"audit_pages: saved page {fp} for {r['url']} does not exist", file=sys.stderr)
                return 2
            parser = Facts()
            parser.feed(fp.read_text(encoding="utf-8", errors="replace"))
            types: list[str] = []
            invalid = 0
            for blob in parser.jsonld_raw:
                try:
                    data = json.loads(blob)
                except json.JSONDecodeError:
                    invalid += 1
                    continue
                items = data if isinstance(data, list) else [data]
                for it in items:
                    if isinstance(it, dict):
                        t = it.get("@type", "")
                        types.extend(t if isinstance(t, list) else [t])
                        for g in it.get("@graph", []) if isinstance(it.get("@graph"), list) else []:
                            if isinstance(g, dict):
                                tt = g.get("@type", "")
                                types.extend(tt if isinstance(tt, list) else [tt])
            mixed = [res for res in parser.resources if res.lower().startswith("http://")]
            fact["html"] = {
                "title": " ".join(parser.title.split()), "meta_description": parser.meta_description,
                "meta_robots": parser.meta_robots, "viewport": parser.viewport, "canonical": parser.canonical,
                "hreflang": parser.hreflang, "h1_count": parser.h1_count, "lang": parser.lang,
                "jsonld_count": len(parser.jsonld_raw), "jsonld_types": [t for t in types if t], "jsonld_invalid": invalid,
                "mixed_content": mixed, "internal_links": [urljoin(r["url"], l) for l in parser.links], "word_count": parser.words,
            }
        pages[r["url"]] = fact

    by_key = {norm(u): p for u, p in pages.items()}
    host = urlsplit(next(iter(pages))).netloc if pages else ""

    # ---- robots.txt
    groups: list[dict] = []
    robots_facts: dict = {"present": False}
    if args.robots:
        rp = Path(args.robots)
        if not rp.exists():
            print(f"audit_pages: robots file {rp} does not exist", file=sys.stderr)
            return 2
        text = rp.read_text(encoding="utf-8", errors="replace")
        groups, sitemaps = parse_robots(text)
        robots_facts = {"present": True, "size_bytes": len(text.encode()), "groups": groups, "sitemaps": sitemaps, "ai_bots": {}}
        add("robots", f"https://{host}/robots.txt", "crawlability", "file_present", "pass", "none", f"{len(groups)} user-agent group(s), {len(text.encode())} bytes")
        if sitemaps:
            absolute = all(s.startswith("http") for s in sitemaps)
            add("robots", f"https://{host}/robots.txt", "crawlability", "sitemap_declared", "pass" if absolute else "warn", "none" if absolute else "P2",
                "; ".join(sitemaps), "" if absolute else "Use an absolute sitemap URL")
        else:
            add("robots", f"https://{host}/robots.txt", "crawlability", "sitemap_declared", "fail", "P2", "no Sitemap: line", "Add `Sitemap: https://<host>/sitemap.xml`")
        star = group_for(groups, "*")
        asset_rules = [pat for kind, pat in (star["rules"] if star else []) if kind == "disallow" and re.search(r"(\.css|\.js|/assets?/|/static/|/_next/|/wp-includes/)", pat)]
        if asset_rules:
            add("robots", f"https://{host}/robots.txt", "crawlability", "assets_blocked", "fail", "P1", "Disallow rules touch CSS/JS paths: " + ", ".join(asset_rules), "Allow CSS and JS so Google can render the page")
        else:
            add("robots", f"https://{host}/robots.txt", "crawlability", "assets_blocked", "pass", "none", "no CSS/JS paths disallowed")
        wild = [pat for kind, pat in (star["rules"] if star else []) if kind == "disallow" and "?" in pat]
        if wild:
            add("robots", f"https://{host}/robots.txt", "crawlability", "query_block", "warn", "P2", "wildcard rule blocks parameterized URLs: " + ", ".join(wild), "Confirm no indexable page needs a query string")
        for bot in AI_BOTS:
            decision, rule = robots_decision(groups, bot, "/")
            robots_facts["ai_bots"][bot] = decision
            add("robots", f"https://{host}/robots.txt", "crawlability", f"ai_bot_{bot}", "info", "none", f"{decision} for / ({rule or 'no matching rule'})")

    # ---- sitemap
    sitemap_urls: list[tuple[str, str]] = []
    sitemap_facts: dict = {"present": False}
    if args.sitemap:
        sp = Path(args.sitemap)
        if not sp.exists():
            print(f"audit_pages: sitemap file {sp} does not exist", file=sys.stderr)
            return 2
        try:
            root = ET.parse(sp).getroot()
            kind = root.tag.rsplit("}", 1)[-1].lower()
            for child in root:
                loc = lastmod = ""
                for el in child:
                    t = el.tag.rsplit("}", 1)[-1].lower()
                    if t == "loc":
                        loc = (el.text or "").strip()
                    elif t == "lastmod":
                        lastmod = (el.text or "").strip()
                if loc:
                    sitemap_urls.append((loc, lastmod))
            valid = kind in ("urlset", "sitemapindex")
        except ET.ParseError as e:
            valid, kind = False, f"parse error: {e}"
        sm = f"https://{host}/sitemap.xml"
        sitemap_facts = {"present": True, "kind": kind, "url_count": len(sitemap_urls),
                         "with_lastmod": sum(1 for _, lm in sitemap_urls if lm)}
        add("sitemap", sm, "crawlability", "xml_valid", "pass" if valid else "fail", "none" if valid else "P1",
            f"<{kind}> with {len(sitemap_urls)} URLs" if valid else str(kind), "" if valid else "Fix the XML so it opens with <urlset> or <sitemapindex>")
        if valid and kind == "urlset":
            lms = [lm for _, lm in sitemap_urls if lm]
            share = len(lms) / len(sitemap_urls) * 100 if sitemap_urls else 0
            if len(lms) > 3 and len(set(lms)) == 1:
                add("sitemap", sm, "crawlability", "lastmod", "warn", "P2", f"all {len(lms)} lastmod values identical ({lms[0]})", "Set lastmod only when content changes")
            elif share < 100:
                add("sitemap", sm, "crawlability", "lastmod", "warn", "P2", f"{share:.0f}% of URLs carry lastmod", "Add lastmod to every URL, updated only on real changes")
            else:
                add("sitemap", sm, "crawlability", "lastmod", "pass", "none", "every URL carries lastmod")
            non_indexable = 0
            for loc, _ in sitemap_urls:
                p = by_key.get(norm(loc))
                if p is None:
                    add("sitemap", loc, "crawlability", "sitemap_url_status", "na", "none", "not in the manifest; not fetched", "Fetch it to confirm it returns 200 and is indexable")
                    continue
                robots_meta = " ".join(p["html"]["meta_robots"]).lower() if p["html"] else ""
                if p["status"] is None or p["status"] >= 400:
                    non_indexable += 1
                    add("sitemap", loc, "crawlability", "sitemap_url_status", "fail", "P1", f"sitemap lists a URL returning {p['status']}", "Remove it from the sitemap or redirect it to the equivalent page")
                elif p["hops"] >= 1 and norm(p["final_url"]) != norm(loc):
                    non_indexable += 1
                    add("sitemap", loc, "crawlability", "sitemap_url_status", "fail", "P1", f"sitemap URL redirects ({p['hops']} hop(s)) to {p['final_url']}", "List the final URL instead")
                elif "noindex" in robots_meta or "noindex" in p["x_robots_tag"].lower():
                    non_indexable += 1
                    add("sitemap", loc, "crawlability", "sitemap_url_status", "fail", "P1", "sitemap lists a noindex URL", "Remove it from the sitemap, or remove the noindex if the page should rank")
                else:
                    add("sitemap", loc, "crawlability", "sitemap_url_status", "pass", "none", f"{p['status']}, indexable")
            sitemap_facts["sample_non_indexable"] = non_indexable
            in_sitemap = {norm(loc) for loc, _ in sitemap_urls}
            for u, p in pages.items():
                robots_meta = " ".join(p["html"]["meta_robots"]).lower() if p["html"] else ""
                if norm(u) not in in_sitemap and p["status"] == 200 and p["hops"] == 0 and "noindex" not in robots_meta and "noindex" not in p["x_robots_tag"].lower() and not urlsplit(u).query:
                    add("sitemap", u, "crawlability", "missing_from_sitemap", "warn", "P2", "indexable 200 page not listed in the sitemap", "Add it to the sitemap")

    sitemap_keys = {norm(loc) for loc, _ in sitemap_urls}

    # ---- per URL
    for u, p in pages.items():
        path = urlsplit(u).path + (f"?{urlsplit(u).query}" if urlsplit(u).query else "")
        st = p["status"]
        if st is None:
            add("url", u, "indexability", "http_status", "na", "none", "no status in manifest")
        elif st >= 500:
            add("url", u, "indexability", "http_status", "fail", "P0", f"{st} server error", "Fix the origin or CDN error; retest")
        elif st >= 400:
            add("url", u, "indexability", "http_status", "fail", "P1" if norm(u) in sitemap_keys else "P2", f"{st}", "Restore, redirect to the equivalent page, or return 410 and remove internal links")
        elif st >= 300:
            add("url", u, "indexability", "http_status", "warn", "P2", f"final status {st}", "Follow the redirect to the final URL")
        else:
            add("url", u, "indexability", "http_status", "pass", "none", f"{st}")
        if p["hops"] >= 2:
            add("url", u, "url_structure", "redirect_hops", "fail", "P1", f"{p['hops']} redirects to {p['final_url']}", "Point the source and all internal links straight at the final URL")
        elif p["hops"] == 1:
            add("url", u, "url_structure", "redirect_hops", "pass", "none", f"1 redirect to {p['final_url']}")
        else:
            add("url", u, "url_structure", "redirect_hops", "pass", "none", "no redirect")
        if groups:
            decision, rule = robots_decision(groups, "Googlebot", path)
            if decision == "blocked":
                important = norm(u) in sitemap_keys
                add("url", u, "crawlability", "robots_blocked", "fail" if important else "warn", "P0" if important else "P2",
                    f"blocked for Googlebot by {rule}" + (" and listed in the sitemap" if important else ""),
                    "Allow the path or remove it from the sitemap" if important else "Confirm the block is intentional")
            else:
                add("url", u, "crawlability", "robots_blocked", "pass", "none", f"{decision} for Googlebot")
        h = p["html"]
        if not h:
            continue
        t = h["title"]
        if not t:
            add("url", u, "indexability", "title", "fail", "P1", "no <title>", "Add a unique 10-60 character title")
        elif len(t) > 60 or len(t) < 10:
            add("url", u, "indexability", "title", "warn", "P2", f"{len(t)} characters: {t[:70]}", "Keep the title between 10 and 60 characters")
        else:
            add("url", u, "indexability", "title", "pass", "none", f"{len(t)} characters")
        robots_all = ", ".join(h["meta_robots"]) + (f"; X-Robots-Tag: {p['x_robots_tag']}" if p["x_robots_tag"] else "")
        noindex = "noindex" in robots_all.lower()
        if noindex:
            important = norm(u) in sitemap_keys or not urlsplit(u).query
            add("url", u, "indexability", "meta_robots", "fail" if important else "warn", "P0" if important else "P2",
                f"noindex ({robots_all})" + (" on a sitemap URL" if norm(u) in sitemap_keys else ""),
                "Remove the noindex if the page should rank; otherwise drop it from the sitemap and internal navigation")
        else:
            add("url", u, "indexability", "meta_robots", "pass", "none", robots_all or "no robots directive (indexable)")
        can = h["canonical"]
        if not can:
            add("url", u, "indexability", "canonical", "warn", "P2", "no canonical tag", "Add a self-referencing canonical")
        elif norm(urljoin(u, can)) == norm(p["final_url"]) or norm(urljoin(u, can)) == norm(u):
            add("url", u, "indexability", "canonical", "pass", "none", "self-referencing")
        else:
            add("url", u, "indexability", "canonical", "fail", "P1", f"canonical points to {can}", "Point the canonical at this URL unless it is a true duplicate")
        if h["viewport"]:
            add("url", u, "mobile", "viewport", "pass", "none", h["viewport"])
        else:
            add("url", u, "mobile", "viewport", "fail", "P1", "no viewport meta tag", "Add <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">")
        if h["h1_count"] == 1:
            add("url", u, "indexability", "h1_count", "pass", "none", "one H1")
        else:
            add("url", u, "indexability", "h1_count", "warn", "P2", f"{h['h1_count']} H1 tags", "Use exactly one H1")
        if h["lang"]:
            add("url", u, "international", "html_lang", "pass", "none", h["lang"])
        else:
            add("url", u, "international", "html_lang", "warn", "P2", "no lang attribute on <html>", "Add lang=\"<code>\" to <html>")
        if h["hreflang"]:
            codes = [c.lower() for c, _ in h["hreflang"]]
            self_ref = any(norm(urljoin(u, href)) == norm(u) for _, href in h["hreflang"])
            problems = []
            if not self_ref:
                problems.append("no self-referencing hreflang")
            if "x-default" not in codes:
                problems.append("no x-default")
            add("url", u, "international", "hreflang", "fail" if not self_ref else ("warn" if problems else "pass"),
                "P1" if not self_ref else ("P2" if problems else "none"),
                f"{len(codes)} alternates ({', '.join(codes)})" + ("; " + "; ".join(problems) if problems else ""),
                "Add the self-referencing alternate and x-default, and confirm return tags on the other locales" if problems else "")
        else:
            add("url", u, "international", "hreflang", "na", "none", "no hreflang (single-locale page)")
        if h["jsonld_invalid"]:
            add("url", u, "structured_data", "jsonld", "fail", "P1", f"{h['jsonld_invalid']} JSON-LD block(s) do not parse", "Fix the JSON")
        elif h["jsonld_count"]:
            add("url", u, "structured_data", "jsonld", "pass", "none", f"{h['jsonld_count']} block(s): {', '.join(h['jsonld_types'])}")
        else:
            add("url", u, "structured_data", "jsonld", "warn", "P2", "no JSON-LD in raw HTML", "Verify the rendered DOM before reporting no schema; add Article, Product, FAQ or Organization markup as fits")
        if h["mixed_content"]:
            add("url", u, "security", "mixed_content", "fail", "P1", f"{len(h['mixed_content'])} http:// resource(s): {', '.join(h['mixed_content'][:3])}", "Serve every resource over https")
        else:
            add("url", u, "security", "mixed_content", "pass", "none", "no http:// resources")
        broken = []
        for link in h["internal_links"]:
            if urlsplit(link).netloc.lower().removeprefix("www.") != host.lower().removeprefix("www."):
                continue
            tgt = by_key.get(norm(link))
            if tgt and tgt["status"] is not None and tgt["status"] >= 400:
                broken.append(f"{link} ({tgt['status']})")
        if broken:
            add("url", u, "indexability", "internal_links_to_errors", "fail", "P1", "; ".join(broken), "Update the links to live equivalents")
        else:
            add("url", u, "indexability", "internal_links_to_errors", "pass", "none", "no internal links to known 4xx/5xx URLs")

    cols = ["scope", "url", "area", "check", "status", "severity", "evidence", "fix"]
    with Path(args.out_csv).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(checks)

    facts = {"host": host, "manifest": str(mpath), "pages": {u: {k: v for k, v in p.items() if k != "file"} for u, p in pages.items()},
             "robots": robots_facts, "sitemap": sitemap_facts,
             "issue_counts": {sev: sum(1 for c in checks if c["severity"] == sev and c["status"] in ("fail", "warn")) for sev in ("P0", "P1", "P2")}}
    Path(args.out_json).write_text(json.dumps(facts, indent=2) + "\n", encoding="utf-8")

    icon = {"pass": "✅", "warn": "⚠️", "fail": "❌", "info": "ℹ️", "na": "N/A"}
    L = [f"## Deterministic checks for {host} (Measured from saved files)", ""]
    for sev in ("P0", "P1", "P2"):
        items = [c for c in checks if c["severity"] == sev and c["status"] in ("fail", "warn")]
        L.append(f"### {sev} ({len(items)})")
        for c in items:
            L.append(f"- {icon[c['status']]} `{c['check']}` {c['url']}: {c['evidence']}" + (f" → {c['fix']}" if c["fix"] else ""))
        if not items:
            L.append("- none")
        L.append("")
    if robots_facts.get("ai_bots"):
        L.append("### AI crawler policy (robots.txt, for /)")
        L.append("| Bot | Decision |")
        L.append("|---|---|")
        for bot, d in robots_facts["ai_bots"].items():
            L.append(f"| {bot} | {d} |")
        L.append("")
    L.append("### Per-area tally")
    L.append("| Area | Pass | Warn | Fail | N/A |")
    L.append("|---|---:|---:|---:|---:|")
    for area in ("crawlability", "indexability", "mobile", "security", "url_structure", "structured_data", "international"):
        sub = [c for c in checks if c["area"] == area]
        L.append(f"| {area} | {sum(1 for c in sub if c['status'] == 'pass')} | {sum(1 for c in sub if c['status'] == 'warn')} | {sum(1 for c in sub if c['status'] == 'fail')} | {sum(1 for c in sub if c['status'] == 'na')} |")
    L.append("| performance | not checked here: use the PageSpeed Insights API | | | |")
    Path(args.out_md).write_text("\n".join(L) + "\n", encoding="utf-8")
    ic = facts["issue_counts"]
    print(f"{len(pages)} URLs, {len(checks)} checks: P0={ic['P0']} P1={ic['P1']} P2={ic['P2']}; wrote {args.out_csv}, {args.out_json}, {args.out_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
