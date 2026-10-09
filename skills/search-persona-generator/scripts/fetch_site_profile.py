#!/usr/bin/env python3
"""Fetch a website and extract the evidence needed to build search personas.

Usage:
    python3 fetch_site_profile.py URL [--max-pages 12] [--timeout 15] [--out FILE]

Writes a JSON "site profile" (to --out, default stdout) with:
    status          ok | partial | unreachable
    site            canonical base URL, host
    organization    name, description, phone, email, addresses, service areas (from JSON-LD / text)
    pages[]         url, title, meta_description, h1, h2, h3, jsonld_types, ctas, text_excerpt
    services[]      service-like phrases harvested from nav links, headings and JSON-LD
    errors[]        per-URL fetch/parse problems (never raises)

Standard library only. Never follows links off the starting host.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

USER_AGENT = (
    "Mozilla/5.0 (compatible; SkillSiteProfiler/1.0; +https://example.com/bot) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

# Link-path keywords that usually lead to pages describing what the business sells.
PRIORITY_KEYWORDS = [
    ("service", 10), ("services", 10), ("solution", 8), ("solutions", 8),
    ("product", 8), ("products", 8), ("what-we-do", 9), ("practice", 7),
    ("treatment", 7), ("program", 6), ("pricing", 7), ("plans", 6),
    ("about", 6), ("industries", 6), ("locations", 5), ("areas", 5),
    ("faq", 5), ("why", 4), ("process", 4), ("how-it-works", 6),
]
SKIP_PATTERNS = re.compile(
    r"(login|signin|sign-in|cart|checkout|privacy|terms|cookie|wp-admin|feed|\.pdf$|\.jpg$|\.png$|\.svg$|"
    r"mailto:|tel:|javascript:|#|\?s=|/tag/|/category/|/author/|/page/\d+)",
    re.I,
)
CTA_WORDS = re.compile(
    r"\b(get a quote|free quote|free estimate|book|schedule|request|call now|contact us|get started|"
    r"start now|sign up|try (it )?free|buy now|order|consultation|demo|learn more)\b",
    re.I,
)
PHONE_RE = re.compile(r"(\+?1[\s.-]?)?\(?\b\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b")
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")


class PageParser(HTMLParser):
    """Collects title, meta description, headings, links, JSON-LD and visible text."""

    SKIP_TAGS = {"script", "style", "noscript", "svg", "template", "iframe"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.meta_description = ""
        self.headings: dict[str, list[str]] = {"h1": [], "h2": [], "h3": []}
        self.links: list[tuple[str, str]] = []  # (href, anchor text)
        self.jsonld: list[str] = []
        self.text_parts: list[str] = []
        self.ctas: list[str] = []
        self._stack: list[str] = []
        self._current_heading: str | None = None
        self._heading_buf: list[str] = []
        self._link_href: str | None = None
        self._link_buf: list[str] = []
        self._in_jsonld = False
        self._jsonld_buf: list[str] = []
        self._in_nav = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self._stack.append(tag)
        if tag == "nav" or (a.get("role") == "navigation"):
            self._in_nav += 1
        if tag == "meta" and (a.get("name") or "").lower() == "description":
            self.meta_description = (a.get("content") or "").strip()
        elif tag in ("h1", "h2", "h3"):
            self._current_heading = tag
            self._heading_buf = []
        elif tag == "a" and a.get("href"):
            self._link_href = a["href"]
            self._link_buf = []
        elif tag == "script" and (a.get("type") or "").lower() == "application/ld+json":
            self._in_jsonld = True
            self._jsonld_buf = []
        elif tag in ("br", "p", "div", "li", "section", "article", "tr"):
            self.text_parts.append("\n")

    def handle_endtag(self, tag):
        if self._stack and self._stack[-1] == tag:
            self._stack.pop()
        elif tag in self._stack:
            while self._stack and self._stack.pop() != tag:
                pass
        if tag == "nav" and self._in_nav:
            self._in_nav -= 1
        if tag in ("h1", "h2", "h3") and self._current_heading == tag:
            text = clean(" ".join(self._heading_buf))
            if text:
                self.headings[tag].append(text)
            self._current_heading = None
        elif tag == "a" and self._link_href is not None:
            anchor = clean(" ".join(self._link_buf))
            self.links.append((self._link_href, anchor))
            if anchor and CTA_WORDS.search(anchor):
                self.ctas.append(anchor)
            self._link_href = None
        elif tag == "script" and self._in_jsonld:
            self.jsonld.append("".join(self._jsonld_buf))
            self._in_jsonld = False

    def handle_data(self, data):
        if self._in_jsonld:
            self._jsonld_buf.append(data)
            return
        if any(t in self.SKIP_TAGS for t in self._stack):
            return
        if "title" in self._stack and "head" in self._stack or (
            "title" in self._stack and "body" not in self._stack
        ):
            self.title_parts.append(data)
            return
        if self._current_heading:
            self._heading_buf.append(data)
        if self._link_href is not None:
            self._link_buf.append(data)
        self.text_parts.append(data)

    @property
    def title(self) -> str:
        return clean(" ".join(self.title_parts))

    @property
    def text(self) -> str:
        raw = "".join(self.text_parts)
        raw = re.sub(r"[ \t\r\f\v]+", " ", raw)
        raw = re.sub(r"\n\s*\n+", "\n", raw)
        return raw.strip()


def clean(s: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(s or "")).strip()


def fetch(url: str, timeout: int) -> tuple[str | None, str, str | None]:
    """Return (html_text, final_url, error)."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,*/*;q=0.8"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            ctype = resp.headers.get("Content-Type", "")
            if "html" not in ctype and "xml" not in ctype and ctype:
                return None, resp.geturl(), f"non-html content-type: {ctype}"
            body = resp.read(2_000_000)
            charset = resp.headers.get_content_charset() or "utf-8"
            return body.decode(charset, errors="replace"), resp.geturl(), None
    except urllib.error.HTTPError as e:
        return None, url, f"HTTP {e.code}"
    except Exception as e:  # noqa: BLE001 - we want to record anything
        return None, url, f"{type(e).__name__}: {e}"


def normalize_url(url: str) -> str:
    url = url.strip()
    if not re.match(r"^https?://", url, re.I):
        url = "https://" + url
    parts = urllib.parse.urlsplit(url)
    path = parts.path or "/"
    return urllib.parse.urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, parts.query, ""))


def same_host(a: str, b: str) -> bool:
    ha = urllib.parse.urlsplit(a).netloc.lower().removeprefix("www.")
    hb = urllib.parse.urlsplit(b).netloc.lower().removeprefix("www.")
    return ha == hb


def score_link(href: str, anchor: str, in_nav_hint: bool) -> int:
    path = urllib.parse.urlsplit(href).path.lower()
    score = 0
    for kw, w in PRIORITY_KEYWORDS:
        if kw in path or kw in anchor.lower():
            score += w
    depth = path.strip("/").count("/")
    score -= depth * 2
    if in_nav_hint:
        score += 3
    return score


def parse_jsonld(blocks: list[str]) -> list[dict]:
    out: list[dict] = []
    for raw in blocks:
        raw = raw.strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if isinstance(item, dict):
                graph = item.get("@graph")
                if isinstance(graph, list):
                    out.extend(g for g in graph if isinstance(g, dict))
                else:
                    out.append(item)
    return out


def types_of(item: dict) -> list[str]:
    t = item.get("@type", [])
    return [t] if isinstance(t, str) else [x for x in t if isinstance(x, str)]


def harvest_org(jsonld_items: list[dict], text: str) -> dict:
    org: dict = {"name": "", "description": "", "phone": [], "email": [], "addresses": [], "service_areas": [],
                 "jsonld_types": sorted({t for i in jsonld_items for t in types_of(i)})}
    for item in jsonld_items:
        ts = types_of(item)
        if any(t.endswith(("Organization", "Business", "LocalBusiness", "Store", "Dentist", "Attorney", "Plumber",
                           "HVACBusiness", "MedicalBusiness", "Restaurant", "Hotel")) for t in ts) or "name" in item:
            org["name"] = org["name"] or clean(str(item.get("name", "")))
            org["description"] = org["description"] or clean(str(item.get("description", "")))
            tel = item.get("telephone")
            if tel:
                org["phone"].append(clean(str(tel)))
            addr = item.get("address")
            for a in (addr if isinstance(addr, list) else [addr]):
                if isinstance(a, dict):
                    org["addresses"].append(clean(", ".join(str(a.get(k, "")) for k in
                                                            ("streetAddress", "addressLocality", "addressRegion",
                                                             "postalCode") if a.get(k))))
                elif isinstance(a, str):
                    org["addresses"].append(clean(a))
            area = item.get("areaServed")
            for ar in (area if isinstance(area, list) else [area]):
                if isinstance(ar, dict):
                    org["service_areas"].append(clean(str(ar.get("name", ""))))
                elif isinstance(ar, str):
                    org["service_areas"].append(clean(ar))
    org["phone"] = dedupe(org["phone"] + PHONE_RE_matches(text))[:3]
    org["email"] = dedupe(EMAIL_RE.findall(text))[:3]
    org["addresses"] = dedupe([a for a in org["addresses"] if a])
    org["service_areas"] = dedupe([a for a in org["service_areas"] if a])
    return org


def PHONE_RE_matches(text: str) -> list[str]:
    return [clean(m.group(0)) for m in PHONE_RE.finditer(text)]


def dedupe(items: list[str]) -> list[str]:
    seen, out = set(), []
    for i in items:
        k = i.lower()
        if i and k not in seen:
            seen.add(k)
            out.append(i)
    return out


def harvest_services(pages: list[dict], jsonld_items: list[dict], nav_anchors: list[str]) -> list[str]:
    cands: list[str] = []
    for item in jsonld_items:
        if any(t in ("Service", "Product", "Offer") for t in types_of(item)):
            cands.append(clean(str(item.get("name", ""))))
        offers = item.get("hasOfferCatalog") or item.get("makesOffer")
        for o in (offers if isinstance(offers, list) else [offers]):
            if isinstance(o, dict):
                cands.append(clean(str(o.get("name", ""))))
                for li in (o.get("itemListElement") or []):
                    if isinstance(li, dict):
                        inner = li.get("itemOffered") if isinstance(li.get("itemOffered"), dict) else li
                        cands.append(clean(str(inner.get("name", ""))))
    for p in pages:
        if p.get("page_role") in ("services", "home"):
            cands.extend(p.get("h2", [])[:12])
            cands.extend(p.get("h3", [])[:12])
    cands.extend(nav_anchors)
    cands = [c for c in cands if c and 2 <= len(c.split()) <= 8 and not CTA_WORDS.search(c)]
    return dedupe(cands)[:40]


def page_role(url: str, home_url: str) -> str:
    if url.rstrip("/") == home_url.rstrip("/"):
        return "home"
    path = urllib.parse.urlsplit(url).path.lower()
    for role, kws in (("services", ("service", "solution", "product", "what-we-do", "treatment", "practice")),
                      ("about", ("about", "team", "story", "why")),
                      ("pricing", ("pricing", "plans", "cost")),
                      ("locations", ("location", "areas", "cities", "near")),
                      ("faq", ("faq", "question"))):
        if any(k in path for k in kws):
            return role
    return "other"


def build_profile(start_url: str, max_pages: int, timeout: int) -> dict:
    home_url = normalize_url(start_url)
    empty_org = {"name": "", "description": "", "phone": [], "email": [], "addresses": [], "service_areas": [],
                 "jsonld_types": []}
    profile: dict = {"status": "unreachable", "site": {"input_url": start_url, "base_url": home_url,
                                                        "host": urllib.parse.urlsplit(home_url).netloc},
                     "organization": empty_org, "pages": [], "services": [], "errors": [],
                     "notes": ["Site could not be fetched; ask the user for homepage text or proceed with "
                               "low-confidence personas and an explicit assumptions list."]}

    html_text, final_url, err = fetch(home_url, timeout)
    if html_text is None and home_url.startswith("https://"):
        # Retry once over plain http for sites without TLS.
        alt = "http://" + home_url[len("https://"):]
        html_text, final_url, err2 = fetch(alt, timeout)
        if html_text is None:
            profile["errors"].append({"url": home_url, "error": err})
            profile["errors"].append({"url": alt, "error": err2})
            return profile
    elif html_text is None:
        profile["errors"].append({"url": home_url, "error": err})
        return profile

    home_url = final_url
    profile["site"]["base_url"] = home_url
    profile["site"]["host"] = urllib.parse.urlsplit(home_url).netloc

    all_jsonld: list[dict] = []
    visited: set[str] = set()
    queue: list[tuple[int, str]] = []
    nav_anchors: list[str] = []

    def process(url: str, html_text: str) -> dict:
        parser = PageParser()
        try:
            parser.feed(html_text)
        except Exception as e:  # noqa: BLE001
            profile["errors"].append({"url": url, "error": f"parse: {type(e).__name__}: {e}"})
        items = parse_jsonld(parser.jsonld)
        all_jsonld.extend(items)
        text = parser.text
        page = {
            "url": url,
            "page_role": page_role(url, home_url),
            "title": parser.title,
            "meta_description": parser.meta_description,
            "h1": dedupe(parser.headings["h1"])[:5],
            "h2": dedupe(parser.headings["h2"])[:25],
            "h3": dedupe(parser.headings["h3"])[:25],
            "jsonld_types": sorted({t for i in items for t in types_of(i)}),
            "ctas": dedupe(parser.ctas)[:10],
            "text_excerpt": text[:1500],
            "word_count": len(text.split()),
        }
        for href, anchor in parser.links:
            if SKIP_PATTERNS.search(href):
                continue
            absolute = urllib.parse.urljoin(url, href)
            absolute = urllib.parse.urlunsplit(urllib.parse.urlsplit(absolute)._replace(fragment=""))
            if not same_host(absolute, home_url) or absolute in visited:
                continue
            queue.append((score_link(absolute, anchor, True), absolute))
            if anchor and page["page_role"] == "home":
                nav_anchors.append(anchor)
        return page

    visited.add(home_url)
    profile["pages"].append(process(home_url, html_text))

    # Fetch the most promising same-host links.
    seen_q: set[str] = set()
    ranked = []
    for score, u in sorted(queue, key=lambda x: -x[0]):
        key = u.rstrip("/")
        if key not in seen_q and key != home_url.rstrip("/"):
            seen_q.add(key)
            ranked.append((score, u))
    for _score, u in ranked[: max(0, max_pages - 1)]:
        if u in visited:
            continue
        visited.add(u)
        body, final, err = fetch(u, timeout)
        if body is None:
            profile["errors"].append({"url": u, "error": err})
            continue
        profile["pages"].append(process(final, body))

    full_text = "\n".join(p["text_excerpt"] for p in profile["pages"])
    profile["organization"] = harvest_org(all_jsonld, full_text)
    if not profile["organization"]["name"]:
        home = profile["pages"][0]
        profile["organization"]["name"] = (home["h1"][0] if home["h1"] else home["title"].split("|")[0].split(" - ")[0]).strip()
    if not profile["organization"]["description"]:
        profile["organization"]["description"] = profile["pages"][0]["meta_description"]
    profile["services"] = harvest_services(profile["pages"], all_jsonld, dedupe(nav_anchors))

    roles = {p["page_role"] for p in profile["pages"]}
    profile["status"] = "ok" if (len(profile["pages"]) >= 2 and ("services" in roles or profile["services"])) else "partial"
    profile["notes"] = []
    if profile["status"] == "partial":
        profile["notes"].append("Few crawlable pages or no clear services page; treat service list as low-confidence.")
    if not all_jsonld:
        profile["notes"].append("No JSON-LD structured data found; organization details come from page text only.")
    return profile


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url")
    ap.add_argument("--max-pages", type=int, default=12, help="homepage + up to N-1 linked pages (default 12)")
    ap.add_argument("--timeout", type=int, default=15, help="per-request timeout in seconds")
    ap.add_argument("--out", help="write JSON here instead of stdout")
    args = ap.parse_args(argv)

    profile = build_profile(args.url, args.max_pages, args.timeout)
    payload = json.dumps(profile, indent=2, ensure_ascii=False)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(payload)
        print(f"[fetch_site_profile] status={profile['status']} pages={len(profile['pages'])} "
              f"services={len(profile['services'])} -> {args.out}", file=sys.stderr)
    else:
        print(payload)
    return 0 if profile["status"] != "unreachable" else 2


if __name__ == "__main__":
    sys.exit(main())
