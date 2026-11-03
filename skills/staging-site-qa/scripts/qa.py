#!/usr/bin/env python3
"""Staging site QA for a website build: checks staging against the build's own files.

Commands (run from the client's working folder, or pass --root):
  scan     fetch (or read saved) Build pages, run every check, take screenshots
           -> qa/<slug>/<slug>-qa-scan.json
  report   merge the scan with qa/<slug>/<slug>-review-notes.md (optional), the
           routing and the newest earlier report -> the dated report and
           qa/<slug>/<slug>-bugherd-tasks.json, then run check
  check    validate a report and its task file
  index | article | devprep   print what this skill reads from a producer file
           (JSON); with --validate, accept such JSON (used by the contracts)

Standard library only. Screenshots use Playwright when it is installed (Python
package, or Node with the playwright module); without it the scan says so.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import html
import json
import os
import re
import shutil
import ssl
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

DEPARTMENTS = ["Content", "SEO", "Design", "Development"]
SEVERITIES = ["CRITICAL", "MAJOR", "MINOR"]
DEFAULT_COLUMNS = {
    "Content": "Copy Review",
    "SEO": "SEO Review",
    "Design": "Design Review",
    "Development": "Dev Ready",
}
BUGHERD_SEVERITY = {"CRITICAL": "critical", "MAJOR": "important", "MINOR": "minor"}
TABLE_HEADER = "| # | Page URL | Department | Severity | Finding | Fix |"
RERUN_HEADER = "| Finding ID | Status | Page URL | Department | Severity | Finding |"
STRUCTURED = "Structured data: not in the current process"
INTERNAL_WORDS = re.compile(
    r"\b(budget|invoice|retainer|billable|margin|out of scope|scope change|internal note|upsell)\b", re.I
)
PLACEHOLDER_RES = [
    re.compile(r"lorem ipsum|dolor sit amet", re.I),
    re.compile(r"\[(?:insert|add|placeholder|client|" + "to" + r"do|" + "t" + r"bd)\b[^\]]{0,60}\]", re.I),
    re.compile(r"\{\{[^}]{0,40}\}\}"),
    re.compile(r"\b(?:placeholder|sample|dummy) (?:text|copy|image)\b", re.I),
]
PHONE_RE = re.compile(r"(?<![\d-])(?:\+?1[\s.-]?)?\(?(\d{3})\)?[\s.-]?(\d{3})[\s.-](\d{4})(?![\d-])")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
SUFFIX = {
    "street": "st", "avenue": "ave", "road": "rd", "boulevard": "blvd", "drive": "dr", "lane": "ln",
    "court": "ct", "place": "pl", "parkway": "pkwy", "highway": "hwy", "way": "way", "terrace": "ter",
    "north": "n", "south": "s", "east": "e", "west": "w", "northeast": "ne", "northwest": "nw",
    "southeast": "se", "southwest": "sw",
}
ADDRESS_RE = re.compile(
    r"(?<![#\w])\d{2,6}\s+(?:[NSEW]{1,2}\.?\s+|(?:North|South|East|West|Northeast|Northwest|Southeast|Southwest)\s+)?(?:[A-Z0-9][\w'.-]*\s+){0,4}?"
    r"(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Place|Pl|Parkway|Pkwy|Highway|Hwy|Way|Terrace|Ter)\b\.?"
)
PAGE_EXT_OK = ("", ".html", ".htm", ".php")


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #
def norm(s: str) -> str:
    s = html.unescape(s or "")
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = s.replace("–", "-").replace("—", "-").replace("\xa0", " ")
    return re.sub(r"\s+", " ", s).strip()


def loose(s: str) -> str:
    s = norm(s).lower()
    s = re.sub(r"[^\w\s]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def norm_path(p: str) -> str:
    p = urllib.parse.urlsplit(p).path or "/"
    p = urllib.parse.unquote(p)
    if not p.startswith("/"):
        p = "/" + p
    if p.endswith("/index.html"):
        p = p[: -len("index.html")]
    last = p.rsplit("/", 1)[-1]
    if not p.endswith("/") and "." not in last:
        p += "/"
    return p.lower()


def page_key(path: str) -> str:
    k = path.strip("/").replace("/", "-")
    return k or "home"


def finding_id(page: str, check: str, detail: str) -> str:
    raw = f"{norm_path(page) if page.startswith('/') else page}|{check}|{loose(detail)}"
    return "QA-" + hashlib.sha1(raw.encode()).hexdigest()[:8]


def phone_digits(s: str) -> str | None:
    d = re.sub(r"\D", "", s)
    if len(d) == 11 and d.startswith("1"):
        d = d[1:]
    return d if len(d) == 10 else None


def fmt_phone(d: str) -> str:
    return f"{d[:3]}-{d[3:6]}-{d[6:]}"


def addr_key(s: str) -> str:
    s = re.sub(r"\b([nsew])\.\s*([nsew])\.", r"\1\2", s.lower())
    words = re.sub(r"[^\w\s]", " ", s).split()
    return " ".join(SUFFIX.get(w, w) for w in words)


def near_miss(k: str, known: list[str]) -> bool:
    """A page address is compared only when it looks like the client's: same house number or
    same street words. Other number-plus-street text on a page is not treated as an address."""
    num, words = k.split(" ", 1)[0], set(k.split()[1:])
    for c in known:
        cn, cw = c.split(" ", 1)[0], set(c.split()[1:])
        if num == cn or (words and words <= cw | {"st", "ave", "rd", "way"} and len(words & cw) >= 2):
            return True
    return False


def die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    sys.exit(code)


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")


# --------------------------------------------------------------------------- #
# Producer readers (also used by the contracts)
# --------------------------------------------------------------------------- #
def parse_index(text: str) -> dict:
    """Pages of a dev handoff index, plus its last line."""
    pages, cur, in_links = [], None, False
    for line in text.split("\n"):
        if line.startswith("### "):
            cur = {"Page": line[4:].strip(), "URL": "", "Content file": "none", "Meta title": "none",
                   "Meta description": "none", "H1": "none", "Internal links": [], "Priority": "Build",
                   "Status": ""}
            pages.append(cur)
            in_links = False
            continue
        if line.startswith("## "):
            cur, in_links = None, False
            continue
        if cur is None:
            continue
        m = re.match(r"^- (Page|URL|Content file|Template|Meta title|Meta description|H1|Internal links|Priority|Status): ?(.*)$", line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            in_links = key == "Internal links"
            if key == "Internal links":
                continue
            cur[key] = val
            continue
        m = re.match(r"^  - (\S+) \(anchor: (.*?)\)(.*)$", line)
        if in_links and m:
            cur["Internal links"].append({"target": m.group(1), "anchor": m.group(2),
                                          "flag": m.group(3).strip()})
    pages = [p for p in pages if p.get("URL")]
    lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
    return {"pages": pages, "last_line": lines[-1] if lines else ""}


def index_json(path: str, text: str) -> list[dict]:
    out = []
    for p in parse_index(text)["pages"]:
        out.append({
            "file": path, "Page": p["Page"], "URL": p["URL"], "Content file": p["Content file"],
            "Meta title": p["Meta title"], "Meta description": p["Meta description"], "H1": p["H1"],
            "Internal links": p["Internal links"], "Priority": p["Priority"], "Status": p["Status"],
        })
    return out


MD_LINK = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)\s]+)\)")


def strip_md(s: str) -> str:
    s = MD_LINK.sub(r"\1", s)
    s = re.sub(r"[*_`]", "", s)
    return norm(s)


def parse_article(text: str) -> dict:
    h2s, sections, cur_marker = [], [], None
    current = None
    for line in text.split("\n"):
        m = re.match(r"^<!--\s*section:\s*(.+?)\s*-->\s*$", line)
        if m:
            cur_marker = m.group(1)
            continue
        if line.startswith("## "):
            head = strip_md(line[3:])
            h2s.append(head)
            current = {"heading": head, "marker": cur_marker, "lines": []}
            sections.append(current)
            cur_marker = None
            continue
        if line.startswith("# "):
            current = None
            continue
        if current is not None:
            current["lines"].append(line)
    cta = None
    for s in sections:
        if (s["marker"] or "").lower() == "final cta":
            cta = s
    if cta is None:
        rest = [s for s in sections if s["heading"].lower() != "sources"]
        cta = rest[-1] if rest else None
    cta_out = None
    if cta:
        links = [{"anchor": strip_md(a), "target": t} for a, t in MD_LINK.findall("\n".join(cta["lines"]))]
        cta_out = {"heading": cta["heading"], "links": links,
                   "marked": (cta["marker"] or "").lower() == "final cta"}
    return {"H2": [h for h in h2s if h.lower() != "sources"], "cta": cta_out}


def article_json(path: str, text: str) -> dict:
    a = parse_article(text)
    return {"article.md": path, "H2": a["H2"], "<!-- section: Final CTA -->": a["cta"]}


def parse_devprep(text: str) -> dict:
    lines = text.split("\n")
    out, grab, images, in_img = [], False, [], False
    for line in lines:
        if line.startswith("## "):
            grab = line.strip() == "## Asset Checklist"
            in_img = False
            continue
        if not grab:
            continue
        if line.startswith("### "):
            in_img = line.strip() == "### Images"
        if line.startswith("RESULT:"):
            break
        out.append(line.rstrip())
        if in_img and line.startswith("- "):
            images.append(line[2:].strip())
    while out and not out[-1]:
        out.pop()
    while out and not out[0]:
        out.pop(0)
    res = ""
    for line in reversed([l.strip() for l in lines if l.strip()]):
        if line.startswith("RESULT:"):
            res = line.split(":", 1)[1].strip()
            break
    return {"checklist": out, "images": images, "result": res}


def devprep_json(path: str, text: str) -> dict:
    d = parse_devprep(text)
    return {"file": path, "## Asset Checklist": d["checklist"], "### Images": d["images"], "RESULT:": d["result"]}


def parse_context(text: str) -> dict:
    """Contact details from the `- Phone:`, `- Email:` and `- Address:` lines when the context has
    them (first listed first); otherwise from anywhere in the file."""
    def labelled(label):
        return "\n".join(re.findall(rf"^- {label}s?:\s*(.+)$", text, re.M | re.I))
    pt, et, at = labelled("Phone") or text, labelled("Email") or text, labelled("Address") or text
    phones = list(dict.fromkeys(d for m in PHONE_RE.finditer(pt) if (d := phone_digits(m.group(0)))))
    emails = list(dict.fromkeys(e.lower() for e in EMAIL_RE.findall(et)))
    addrs = list(dict.fromkeys(addr_key(m.group(0)) for m in ADDRESS_RE.finditer(at)))
    website = ""
    m = re.search(r"^- Website:\s*(\S+)", text, re.M)
    if m:
        w = m.group(1)
        if "://" not in w:
            w = "https://" + w
        host = urllib.parse.urlsplit(w).hostname or ""
        website = host[4:] if host.startswith("www.") else host
    name = ""
    m = re.search(r"^Client:\s*(.+)$", text, re.M)
    if m:
        name = m.group(1).strip()
    return {"phones": phones, "emails": emails, "addresses": addrs, "website": website, "name": name}


def parse_routing(text: str) -> dict:
    cols, people, project = dict(DEFAULT_COLUMNS), {}, ""
    m = re.search(r"^BugHerd project:\s*(.+)$", text, re.M)
    if m:
        project = m.group(1).strip()
    for line in text.split("\n"):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and cells[0] in DEPARTMENTS:
            if cells[1] and not set(cells[1]) <= set("-: "):
                cols[cells[0]] = cells[1]
            if len(cells) >= 3 and cells[2]:
                people[cells[0]] = cells[2]
    return {"columns": cols, "assignees": people, "project": project}


# --------------------------------------------------------------------------- #
# HTML reading
# --------------------------------------------------------------------------- #
class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = None
        self.meta = {}
        self.links = []          # <link rel href>
        self.anchors = []        # dict href text in_main
        self.images = []         # dict src alt in_main width height
        self.assets = []         # other src/href urls
        self.h1, self.h2 = [], []
        self.text_parts, self.main_parts = [], []
        self._stack = []
        self._main = 0
        self._skip = 0
        self._cap = []           # open capture buffers: [kind, buffer, extra]
        self._svg = 0
        self.has_main = False
        self.raw = ""

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag in ("script", "style", "template"):
            self._skip += 1
            if tag == "script" and a.get("src"):
                self.assets.append(a["src"])
            return
        if tag == "svg":
            self._svg += 1
        if tag == "main":
            self._main += 1
            self.has_main = True
        if tag == "title" and (self._svg or self.title is not None):
            pass
        elif tag == "title":
            self._cap.append(["title", [], None])
        elif tag in ("h1", "h2"):
            self._cap.append([tag, [], None])
        elif tag == "a":
            self._cap.append(["a", [], {"href": a.get("href", ""), "in_main": self._main > 0}])
        elif tag == "meta":
            key = (a.get("name") or a.get("property") or "").lower()
            if key:
                self.meta[key] = a.get("content", "")
        elif tag == "link":
            self.links.append({"rel": a.get("rel", "").lower(), "href": a.get("href", "")})
        elif tag == "img":
            self.images.append({"src": a.get("src", ""), "alt": a.get("alt"), "has_alt": "alt" in a,
                                "in_main": self._main > 0, "width": a.get("width", ""),
                                "height": a.get("height", "")})
            for c in self._cap:
                if c[0] == "a" and a.get("alt"):
                    c[1].append(a["alt"])
        elif tag in ("source",) and a.get("srcset"):
            self.assets.append(a["srcset"].split()[0])
        elif tag in ("iframe", "video", "audio", "embed") and a.get("src"):
            self.assets.append(a["src"])
        if tag not in ("br", "img", "meta", "link", "input", "hr", "source"):
            self._stack.append(tag)

    def handle_endtag(self, tag):
        if tag in ("script", "style", "template"):
            self._skip = max(0, self._skip - 1)
            return
        if tag == "svg":
            self._svg = max(0, self._svg - 1)
        if tag == "main":
            self._main = max(0, self._main - 1)
        for i in range(len(self._cap) - 1, -1, -1):
            kind = self._cap[i][0]
            if kind == tag or (kind == "title" and tag == "title"):
                kind, buf, extra = self._cap.pop(i)
                txt = norm(" ".join(buf))
                if kind == "title":
                    self.title = txt
                elif kind == "h1":
                    self.h1.append(txt)
                elif kind == "h2":
                    self.h2.append(txt)
                elif kind == "a":
                    self.anchors.append({"href": extra["href"], "text": txt, "in_main": extra["in_main"]})
                break

    def handle_data(self, data):
        if self._skip:
            return
        for c in self._cap:
            c[1].append(data)
        if not any(c[0] == "title" for c in self._cap):
            self.text_parts.append(data)
            if self._main:
                self.main_parts.append(data)

    @property
    def text(self):
        return norm(" ".join(self.text_parts))

    @property
    def main_text(self):
        return norm(" ".join(self.main_parts))


def image_size(data: bytes):
    try:
        if data[:8] == b"\x89PNG\r\n\x1a\n":
            return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big"), "PNG"
        if data[:6] in (b"GIF87a", b"GIF89a"):
            return int.from_bytes(data[6:8], "little"), int.from_bytes(data[8:10], "little"), "GIF"
        if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
            chunk = data[12:16]
            if chunk == b"VP8X":
                return 1 + int.from_bytes(data[24:27], "little"), 1 + int.from_bytes(data[27:30], "little"), "WebP"
            if chunk == b"VP8 ":
                return int.from_bytes(data[26:28], "little") & 0x3FFF, int.from_bytes(data[28:30], "little") & 0x3FFF, "WebP"
            if chunk == b"VP8L":
                b = data[21:25]
                w = 1 + (((b[1] & 0x3F) << 8) | b[0])
                h = 1 + (((b[3] & 0xF) << 10) | (b[2] << 2) | ((b[1] & 0xC0) >> 6))
                return w, h, "WebP"
        if data[:2] == b"\xff\xd8":
            i = 2
            while i < len(data) - 9:
                if data[i] != 0xFF:
                    i += 1
                    continue
                marker = data[i + 1]
                if marker in (0xC0, 0xC1, 0xC2):
                    return int.from_bytes(data[i + 7:i + 9], "big"), int.from_bytes(data[i + 5:i + 7], "big"), "JPEG"
                i += 2 + int.from_bytes(data[i + 2:i + 4], "big")
        if data.lstrip()[:5] in (b"<svg ", b"<?xml") or b"<svg" in data[:300]:
            return None, None, "SVG"
    except (IndexError, ValueError):
        pass
    return None, None, ""


# --------------------------------------------------------------------------- #
# Fetching
# --------------------------------------------------------------------------- #
class Site:
    def __init__(self, base_url: str, saved: Path | None, user: str = "", password: str = ""):
        self.base = base_url.rstrip("/")
        parts = urllib.parse.urlsplit(self.base)
        self.scheme = parts.scheme
        self.host = (parts.hostname or "").lower()
        self.saved = saved
        self.auth = None
        if user:
            self.auth = "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode()
        self.cache = {}

    def saved_file(self, path: str) -> Path | None:
        rel = urllib.parse.unquote(urllib.parse.urlsplit(path).path).lstrip("/")
        cands = []
        if rel == "" or rel.endswith("/"):
            cands = [rel + "index.html"]
        else:
            cands = [rel, rel + ".html", rel + "/index.html"]
        for c in cands:
            p = self.saved / c
            if p.is_file():
                return p
        return None

    def get(self, path_or_url: str, want_body=True) -> dict:
        # Bodies are always read: a link check must not cache an empty page under the page's own URL.
        want_body = True
        url = path_or_url if "://" in path_or_url else self.base + path_or_url
        if url in self.cache:
            return self.cache[url]
        if self.saved is not None:
            f = self.saved_file(urllib.parse.urlsplit(url).path)
            res = {"status": 200 if f else 404, "body": f.read_bytes() if f else b"", "final": url,
                   "headers": {}, "file": str(f) if f else ""}
            self.cache[url] = res
            return res
        req = urllib.request.Request(url, headers={"User-Agent": "staging-site-qa/1.0"})
        if self.auth and (urllib.parse.urlsplit(url).hostname or "").lower() == self.host:
            req.add_header("Authorization", self.auth)
        try:
            with urllib.request.urlopen(req, timeout=25, context=ssl.create_default_context()) as r:
                body = r.read() if want_body else b""
                res = {"status": r.status, "body": body, "final": r.geturl(),
                       "headers": {k.lower(): v for k, v in r.headers.items()}}
        except urllib.error.HTTPError as e:
            res = {"status": e.code, "body": b"", "final": url, "headers": {}}
        except (urllib.error.URLError, OSError, ValueError) as e:
            res = {"status": 0, "body": b"", "final": url, "headers": {}, "error": str(getattr(e, "reason", e))}
        self.cache[url] = res
        return res


# --------------------------------------------------------------------------- #
# Checks
# --------------------------------------------------------------------------- #
class Findings:
    def __init__(self):
        self.items = []
        self.seen = set()

    def add(self, page, check, detail, dept, sev, finding, fix, evidence=""):
        fid = finding_id(page, check, detail)
        if fid in self.seen:
            return
        self.seen.add(fid)
        self.items.append({"finding_id": fid, "page": page, "check": check, "detail": detail,
                           "department": dept, "severity": sev, "finding": finding, "fix": fix,
                           "evidence": evidence, "source": "script"})


def internal_path(href: str, site: Site, prod: str) -> str | None:
    href = href.strip()
    if not href or href.startswith(("#", "tel:", "mailto:", "javascript:", "sms:", "data:")):
        return None
    parts = urllib.parse.urlsplit(href)
    host = (parts.hostname or "").lower()
    if host and host not in (site.host, prod, "www." + prod):
        return None
    if not parts.path and not host:
        return None
    return parts.path or "/"


def check_page(pg: dict, site: Site, prod: str, ctx: dict, art: dict | None, F: Findings,
               index_paths: set, notes: list, toggles: list, images_out: list, rels: dict):
    path = pg["URL"]
    res = site.get(path)
    if res["status"] == 404 or (site.saved is not None and res["status"] != 200):
        why = "not in the saved pages" if site.saved is not None else "HTTP 404"
        F.add(path, "page-missing", "", "Development", "CRITICAL",
              f"The page is missing on staging ({why}).",
              f"Build and publish {path} from the approved page content.")
        return None
    if res["status"] == 0:
        F.add(path, "http-status", "unreachable", "Development", "CRITICAL",
              f"The page could not be loaded ({res.get('error', 'no response')}).",
              "Make the page load on staging.")
        return None
    if res["status"] != 200:
        F.add(path, "http-status", str(res["status"]), "Development", "CRITICAL",
              f"The page returns HTTP {res['status']}.", "Make the page return 200.")
        return None
    if site.saved is None and norm_path(urllib.parse.urlsplit(res["final"]).path or "/") != norm_path(path):
        F.add(path, "page-missing", "", "Development", "CRITICAL",
              f"The page is missing on staging (it redirects to {res['final']}).",
              f"Build and publish {path} from the approved page content.")
        return None
    if site.saved is None and site.scheme == "https" and urllib.parse.urlsplit(res["final"]).scheme != "https":
        F.add(path, "https", "", "Development", "MAJOR", "The page loads over HTTP, not HTTPS.",
              "Serve the page over HTTPS and redirect HTTP to it.")
    p = PageParser()
    p.raw = res["body"].decode("utf-8", errors="replace")
    p.feed(p.raw)
    p.close()
    rels[path] = res.get("file", "")
    rels.setdefault("_raw", []).append(p.raw.lower())

    # Meta title, description, H1
    if pg["Meta title"] != "none":
        if not p.title:
            F.add(path, "meta-title", pg["Meta title"], "SEO", "CRITICAL", "The page has no meta title.",
                  f'Set the meta title to "{pg["Meta title"]}".')
        elif norm(p.title) != norm(pg["Meta title"]):
            F.add(path, "meta-title", pg["Meta title"], "SEO", "MAJOR",
                  f'The meta title is "{p.title}"; the approved title is "{pg["Meta title"]}".',
                  f'Set the meta title to "{pg["Meta title"]}".')
    if pg["Meta description"] != "none":
        md = p.meta.get("description", "")
        if not md:
            F.add(path, "meta-description", pg["Meta description"], "SEO", "MAJOR",
                  "The page has no meta description.",
                  f'Set the meta description to "{pg["Meta description"]}".')
        elif norm(md) != norm(pg["Meta description"]):
            F.add(path, "meta-description", pg["Meta description"], "SEO", "MAJOR",
                  f'The meta description is "{norm(md)}"; the approved one is "{pg["Meta description"]}".',
                  f'Set the meta description to "{pg["Meta description"]}".')
    if pg["H1"] != "none":
        if not p.h1:
            F.add(path, "h1", pg["H1"], "SEO", "CRITICAL", "The page has no H1.", f'Add the H1 "{pg["H1"]}".')
        elif not any(norm(h) == norm(pg["H1"]) for h in p.h1):
            F.add(path, "h1", pg["H1"], "SEO", "MAJOR",
                  f'The H1 is "{p.h1[0]}"; the approved H1 is "{pg["H1"]}".', f'Change the H1 to "{pg["H1"]}".')
        if len(p.h1) > 1:
            F.add(path, "h1-multiple", str(len(p.h1)), "SEO", "MINOR", f"The page has {len(p.h1)} H1 headings.",
                  f'Keep one H1 ("{pg["H1"]}") and make the others H2 or plain text.')

    # Canonical
    canon = [l["href"] for l in p.links if "canonical" in l["rel"].split()]
    want = (f"https://{prod}" if prod else "") + path
    if not canon:
        F.add(path, "canonical", "", "SEO", "MAJOR", "The page has no canonical tag.",
              f"Add a canonical tag pointing to {want}.")
    else:
        c = urllib.parse.urlsplit(urllib.parse.urljoin(site.base + path, canon[0]))
        chost = (c.hostname or "").lower()
        bad = None
        if norm_path(c.path or "/") != norm_path(path):
            bad = f"The canonical tag points to {canon[0]}, not to this page."
        elif chost == site.host:
            toggles.append(f"{path}: canonical uses the staging domain ({canon[0]}). It must read {want} on the live site; check it on launch day. (Development)")
        elif prod and chost not in (prod, "www." + prod):
            bad = f"The canonical tag points at another domain ({canon[0]})."
        if bad:
            F.add(path, "canonical", "", "SEO", "MAJOR", bad, f"Point the canonical tag at {want}.")

    # Sections and CTA
    if art:
        page_h2 = [loose(h) for h in p.h2]
        present = []
        for h in art["H2"]:
            if loose(h) in page_h2:
                present.append(h)
            else:
                F.add(path, "h2-missing", h, "Content", "CRITICAL", f'The section "{h}" is missing.',
                      f'Add the "{h}" section from the approved page content.')
        order = sorted(present, key=lambda h: page_h2.index(loose(h)))
        if order != present:
            F.add(path, "h2-order", " / ".join(art["H2"]), "Content", "MAJOR",
                  "The sections are not in the approved order.",
                  "Put the sections in this order: " + "; ".join(f'"{h}"' for h in present) + ".")
    main_anchors = [a for a in p.anchors if a["in_main"]] if p.has_main else p.anchors
    cta_targets = set()
    if art and art["cta"]:
        for link in art["cta"]["links"]:
            t = link["target"]
            cta_targets.add((norm_path(t) if t.startswith("/") else t.lower(), loose(link["anchor"])))
            if t.startswith(("tel:", "mailto:")):
                ok = any(a["href"].lower().replace(" ", "") == t.lower().replace(" ", "")
                         or (t.startswith("tel:") and a["href"].startswith("tel:")
                             and phone_digits(a["href"]) == phone_digits(t)) for a in main_anchors)
            else:
                ok = any(internal_path(a["href"], site, prod) is not None
                         and norm_path(internal_path(a["href"], site, prod)) == norm_path(t) for a in main_anchors)
            if not ok:
                F.add(path, "cta", f"{t} {link['anchor']}", "Content", "MAJOR",
                      f'The call to action "{link["anchor"]}" ({t}) is missing from the page.',
                      f'Add the "{link["anchor"]}" link to {t} in the "{art["cta"]["heading"]}" section.')

    # Internal links from the index
    for link in pg["Internal links"]:
        if link["flag"]:
            continue
        t = norm_path(link["target"])
        if (t, loose(link["anchor"])) in cta_targets:
            continue
        hits = [a for a in main_anchors
                if (ip := internal_path(a["href"], site, prod)) is not None and norm_path(ip) == t]
        if not hits:
            F.add(path, "link-missing", f"{link['target']} {link['anchor']}", "SEO", "MAJOR",
                  f'The link to {link["target"]} with the text "{link["anchor"]}" is missing.',
                  f'Add the link to {link["target"]} with the text "{link["anchor"]}".')
        elif not any(loose(a["text"]) == loose(link["anchor"]) for a in hits):
            F.add(path, "link-anchor", f"{link['target']} {link['anchor']}", "SEO", "MINOR",
                  f'The link to {link["target"]} uses the text "{hits[0]["text"]}"; the approved text is "{link["anchor"]}".',
                  f'Change the link text to "{link["anchor"]}".')

    # Broken internal links and staging-domain references
    for a in p.anchors:
        ip = internal_path(a["href"], site, prod)
        if ip is None:
            continue
        ext = os.path.splitext(ip.rstrip("/"))[1].lower()
        if ext not in PAGE_EXT_OK:
            continue
        tp = norm_path(ip)
        if site.saved is not None:
            if site.saved_file(tp) is None:
                if tp in index_paths:
                    F.add(path, "link-broken", tp, "Development", "MAJOR",
                          f"The link to {tp} is broken: that page is not on staging.",
                          f"Publish {tp} or remove the link.")
                else:
                    notes.append(f"Link from {path} to {tp} not checked (not in the saved pages or the index).")
        else:
            r = site.get(urllib.parse.urljoin(site.base + path, a["href"]).split("#")[0], want_body=False)
            if r["status"] != 200:
                F.add(path, "link-broken", tp, "Development", "MAJOR",
                      f"The link to {tp} is broken (HTTP {r['status'] or 'no response'}).",
                      f"Fix the link target or publish {tp}.")
    def on_staging(u):
        return bool(site.host) and (urllib.parse.urlsplit(u).hostname or "").lower() == site.host
    # Links and images written into the page content do not change when the site URL is switched
    # at launch, so they are findings (one per page). Theme, menu and plugin URLs follow the site
    # URL setting, so they are one site-wide launch toggle.
    content_urls = [a["href"] for a in p.anchors if a["in_main"] or not p.has_main] + \
                   [i["src"] for i in p.images if i["in_main"] or not p.has_main]
    if p.meta.get("og:url"):
        content_urls.append(p.meta["og:url"])
    hits = list(dict.fromkeys(u for u in content_urls if on_staging(u)))
    if hits:
        ex = ", ".join(hits[:3]) + (f" and {len(hits) - 3} more" if len(hits) > 3 else "")
        F.add(path, "staging-domain", "page content", "Development", "MAJOR",
              f"{len(hits)} link(s) or image(s) in the page content still point at the staging domain: {ex}.",
              "Change them to relative links or the live domain.")
    other = [a["href"] for a in p.anchors] + [i["src"] for i in p.images] + p.assets + \
            [l["href"] for l in p.links if "canonical" not in l["rel"].split()]
    rels.setdefault("_site_urls", set()).update(u for u in other if on_staging(u) and u not in hits)

    # Placeholder text
    body = p.text + " " + (p.title or "")
    for i, rx in enumerate(PLACEHOLDER_RES):
        m = rx.search(body)
        if m:
            snippet = m.group(0)[:60]
            F.add(path, "placeholder", f"pattern {i}", "Content", "CRITICAL",
                  f'Placeholder text is on the page: "{snippet}".',
                  "Replace it with the approved page content.")

    # Images
    for im in p.images:
        if not im["has_alt"]:
            F.add(path, "alt", im["src"], "SEO", "MAJOR", f"The image {im['src']} has no alt text.",
                  "Add alt text that says what the image shows.")
        info = {"page": path, "src": im["src"], "alt": im["alt"], "width_attr": im["width"],
                "height_attr": im["height"], "status": "", "width": None, "height": None, "format": ""}
        ip = urllib.parse.urlsplit(im["src"])
        same = not ip.hostname or (ip.hostname or "").lower() in (site.host, prod)
        if im["src"].startswith("data:"):
            info["status"] = "inline"
        elif site.saved is not None:
            f = site.saved_file(ip.path) if same else None
            if f:
                info["status"] = "found"
                info["width"], info["height"], info["format"] = image_size(f.read_bytes()[:65536])
            else:
                info["status"] = "not checked (not in the saved pages)"
        elif same:
            r = site.get(urllib.parse.urljoin(site.base + path, im["src"]))
            if r["status"] == 200:
                info["status"] = "found"
                info["width"], info["height"], info["format"] = image_size(r["body"][:65536])
            else:
                info["status"] = f"broken (HTTP {r['status'] or 'no response'})"
                F.add(path, "image-broken", im["src"], "Design", "MAJOR",
                      f"The image {im['src']} does not load.", "Upload the image or fix its path.",
                      evidence="image request failed")
        else:
            info["status"] = "external, not checked"
        images_out.append(info)

    # Head tags
    if "viewport" not in p.meta:
        F.add(path, "viewport", "", "Development", "MAJOR", "The page has no viewport meta tag, so it will not scale on phones.",
              'Add <meta name="viewport" content="width=device-width, initial-scale=1">.')
    if not any("icon" in l["rel"].split() for l in p.links):
        if site.saved is not None or site.get("/favicon.ico", want_body=False)["status"] != 200:
            F.add(path, "favicon", "", "Development", "MINOR", "The page has no favicon.", "Add the favicon.")
    if not p.meta.get("og:title"):
        F.add(path, "og-title", "", "SEO", "MINOR", "The page has no Open Graph title.",
              "Add og:title (the meta title works).")
    if not p.meta.get("og:description"):
        F.add(path, "og-description", "", "SEO", "MINOR", "The page has no Open Graph description.",
              "Add og:description (the meta description works).")

    # noindex is a launch toggle, not a finding
    robots = (p.meta.get("robots", "") + " " + res["headers"].get("x-robots-tag", "")).lower()
    if "noindex" in robots:
        toggles.append(f"{path}: noindex on staging. Remove it at launch so the page can be indexed. (Development)")

    # Contact details
    tel_digits = {phone_digits(a["href"]) for a in p.anchors if a["href"].startswith("tel:")}
    found_phones = {d for m in PHONE_RE.finditer(p.text) if (d := phone_digits(m.group(0)))} | \
                   {d for d in tel_digits if d}
    for d in sorted(found_phones):
        if ctx["phones"] and d not in ctx["phones"]:
            F.add(path, "phone", d, "Content", "CRITICAL",
                  f"The phone number {fmt_phone(d)} does not match the client's number ({', '.join(fmt_phone(x) for x in ctx['phones'])}).",
                  f"Change it to {fmt_phone(ctx['phones'][0])}.")
        elif not ctx["phones"]:
            rels.setdefault("_am", []).append(f"No phone number in the client context; staging shows {fmt_phone(d)} on {path}. Confirm it with the client.")
    mails = {e.lower() for e in EMAIL_RE.findall(p.text)} | \
            {a["href"][7:].split("?")[0].lower() for a in p.anchors if a["href"].lower().startswith("mailto:")}
    for e in sorted(mails):
        if ctx["emails"] and e not in ctx["emails"]:
            F.add(path, "email", e, "Content", "CRITICAL",
                  f"The email address {e} does not match the client's ({', '.join(ctx['emails'])}).",
                  f"Change it to {ctx['emails'][0]}.")
        elif not ctx["emails"]:
            rels.setdefault("_am", []).append(f"No email address in the client context; staging shows {e} on {path}. Confirm it with the client.")
    for m in ADDRESS_RE.finditer(p.text):
        k = addr_key(m.group(0))
        if ctx["addresses"] and k not in ctx["addresses"] and near_miss(k, ctx["addresses"]):
            F.add(path, "address", k, "Content", "CRITICAL",
                  f'The address "{m.group(0)}" does not match the client\'s address.',
                  "Use the street address from the client's details.")
        elif not ctx["addresses"]:
            rels.setdefault("_am", []).append(f'No street address in the client context; staging shows "{m.group(0)}" on {path}. Confirm it with the client.')
    return p


# --------------------------------------------------------------------------- #
# Screenshots
# --------------------------------------------------------------------------- #
NODE_SHOT = r"""
const { chromium } = require('playwright');
(async () => {
  const jobs = JSON.parse(process.argv[2]);
  const browser = await chromium.launch();
  for (const j of jobs) {
    const ctx = await browser.newContext({ viewport: j.viewport, httpCredentials: j.auth || undefined, isMobile: j.mobile });
    const page = await ctx.newPage();
    try { await page.goto(j.url, { waitUntil: 'load', timeout: 30000 }); await page.screenshot({ path: j.out, fullPage: true }); }
    catch (e) { console.error('fail ' + j.url + ' ' + e.message); }
    await ctx.close();
  }
  await browser.close();
})();
"""


def screenshots(jobs: list[dict]) -> tuple[list[str], str]:
    if not jobs:
        return [], "no pages to capture"
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
        with sync_playwright() as pw:
            b = pw.chromium.launch()
            for j in jobs:
                c = b.new_context(viewport=j["viewport"], is_mobile=j["mobile"],
                                  http_credentials=j.get("auth"))
                pg = c.new_page()
                try:
                    pg.goto(j["url"], wait_until="load", timeout=30000)
                    pg.screenshot(path=j["out"], full_page=True)
                except Exception as e:  # noqa: BLE001
                    print(f"screenshot failed for {j['url']}: {e}", file=sys.stderr)
                c.close()
            b.close()
        return [j["out"] for j in jobs if Path(j["out"]).exists()], ""
    except ImportError:
        pass
    except Exception as e:  # noqa: BLE001
        return [], f"Playwright failed ({e})"
    node = shutil.which("node")
    if not node:
        return [], "Playwright is not available"
    with tempfile.TemporaryDirectory() as td:
        js = Path(td) / "shot.js"
        js.write_text(NODE_SHOT)
        env = dict(os.environ)
        try:
            r = subprocess.run([node, str(js), json.dumps(jobs)], capture_output=True, text=True,
                               timeout=60 + 40 * len(jobs), env=env)
        except (OSError, subprocess.TimeoutExpired) as e:
            return [], f"Playwright failed ({e})"
        if r.returncode != 0 and "Cannot find module" in r.stderr:
            return [], "Playwright is not available"
    done = [j["out"] for j in jobs if Path(j["out"]).exists()]
    return done, "" if done else "Playwright did not produce screenshots"


# --------------------------------------------------------------------------- #
# scan
# --------------------------------------------------------------------------- #
def paths_for(root: Path, slug: str) -> dict:
    return {
        "index": root / "handoff" / slug / f"{slug}-dev-handoff-index.md",
        "devprep": root / "design" / slug / f"{slug}-design-qa-devprep.md",
        "context": root / "kickoff" / slug / f"{slug}-context.md",
        "routing": root / "qa" / "routing.md",
        "qa": root / "qa" / slug,
        "scan": root / "qa" / slug / f"{slug}-qa-scan.json",
        "notes": root / "qa" / slug / f"{slug}-review-notes.md",
        "tasks": root / "qa" / slug / f"{slug}-bugherd-tasks.json",
    }


def cmd_scan(a) -> int:
    root = Path(a.root).resolve()
    P = paths_for(root, a.slug)
    if not P["index"].exists():
        die(f"STOP: no dev handoff index at {P['index'].relative_to(root)}. Run dev-handoff-index first.")
    if not P["context"].exists():
        die(f"STOP: no client context at {P['context'].relative_to(root)}.")
    if not a.base_url:
        die("STOP: give the staging base URL (--base-url), even with --saved, so staging-domain links can be found.")
    saved = None
    if a.saved:
        saved = (root / a.saved).resolve() if not os.path.isabs(a.saved) else Path(a.saved)
        if not saved.is_dir():
            die(f"STOP: saved pages folder {a.saved} does not exist.")
    password = a.password or os.environ.get("STAGING_PASSWORD", "")
    site = Site(a.base_url, saved, a.user or "", password)
    idx = parse_index(read(P["index"]))
    ctx = parse_context(read(P["context"]))
    prod = ctx["website"]
    if saved is None:
        probe = site.get("/")
        if probe["status"] in (0,) or probe["status"] in (401, 403):
            why = probe.get("error") or f"HTTP {probe['status']}"
            die(f"STOP: could not reach staging at {a.base_url} ({why}). Nothing was written. "
                "Check the URL and the staging password, or save the pages' HTML into a folder and run with --saved.")
    build = [p for p in idx["pages"] if p["Priority"].lower().startswith("build")]
    skipped = [p for p in idx["pages"] if p not in build]
    index_paths = {norm_path(p["URL"]) for p in idx["pages"]}
    F, notes, toggles, images, rels, am = Findings(), [], [], [], {}, []
    devprep = parse_devprep(read(P["devprep"])) if P["devprep"].exists() else None
    checked, missing = [], []
    for pg in build:
        art = None
        cf = pg["Content file"]
        if cf != "none" and (root / cf).exists():
            art = parse_article(read(root / cf))
        elif cf != "none":
            notes.append(f"{pg['URL']}: content file {cf} not found, so sections and CTA were not checked.")
        if pg["Status"] and not pg["Status"].startswith("READY"):
            am.append(f"{pg['Page']} ({pg['URL']}) is {pg['Status']} in the dev handoff index; confirm when its content will be final.")
        before = len(F.items)
        p = check_page(pg, site, prod, ctx, art, F, index_paths, notes, toggles, images, rels)
        if p is None:
            missing.append(pg["URL"])
        else:
            checked.append(pg["URL"])
        _ = before
    am.extend(rels.pop("_am", []))
    raw_all = " ".join(rels.pop("_raw", []))
    site_urls = sorted(rels.pop("_site_urls", set()))
    if site_urls:
        toggles.append(f"{len(site_urls)} theme, menu or file URL(s) use the staging domain (for example {site_urls[0]}). "
                       "Switch the site URL to the live domain at launch and re-check. (Development)")
    # Asset checklist: named files must be used somewhere (matched on the file stem, so resized
    # copies such as logo-300x80.png count)
    if devprep:
        for line in devprep["images"]:
            for name in re.findall(r"\b[\w-]+\.(?:svg|png|jpe?g|webp|gif)\b", line, re.I):
                if os.path.splitext(name.lower())[0] not in raw_all:
                    F.add("/", "asset-missing", name, "Design", "MAJOR",
                          f"The file {name} from the design asset checklist is not used on the site.",
                          f"Add {name} where the design places it.", evidence=f"asset checklist: {line}")
    else:
        notes.append("No design QA and dev prep file, so images were not compared with an asset checklist.")
    if site.saved is None and site.scheme != "https":
        F.add("/", "https", "site", "Development", "MAJOR", "Staging is served over HTTP, not HTTPS.",
              "Install the certificate and redirect HTTP to HTTPS.")
    if site.saved is None:
        rb = site.get("/robots.txt")
        if rb["status"] == 200 and re.search(r"^\s*Disallow:\s*/\s*$", rb["body"].decode("utf-8", "replace"), re.M | re.I):
            toggles.append("robots.txt blocks all crawlers on staging (Disallow: /). Replace it with the live robots.txt at launch. (Development)")
    # Screenshots
    shots, why = [], "turned off (--no-screens)"
    if not a.no_screens:
        sd = P["qa"] / "screens"
        sd.mkdir(parents=True, exist_ok=True)
        jobs = []
        auth = {"username": a.user, "password": password} if a.user else None
        for path in checked:
            url = Path(rels[path]).resolve().as_uri() if saved is not None and rels.get(path) else site.base + path
            for kind, vp, mob in (("desktop", {"width": 1440, "height": 900}, False),
                                  ("mobile", {"width": 390, "height": 844}, True)):
                jobs.append({"url": url, "out": str(sd / f"{page_key(path)}-{kind}.png"), "viewport": vp,
                             "mobile": mob, "auth": auth})
        shots, why = screenshots(jobs)
        if not shots and sd.exists() and not any(sd.iterdir()):
            sd.rmdir()
    if saved is not None:
        notes.append(f"Saved pages from {os.path.relpath(saved, root)}: HTTPS, HTTP status of other links and image loading were not checked.")
    for p in skipped:
        notes.append(f"{p['Page']} ({p['URL']}) skipped: priority {p['Priority']}.")
    scan = {
        "client": ctx["name"] or a.slug, "slug": a.slug, "date": a.date or dt.date.today().isoformat(),
        "base_url": site.base, "saved": os.path.relpath(saved, root) if saved else "",
        "production": prod, "index": str(P["index"].relative_to(root)),
        "index_last_line": idx["last_line"],
        "devprep": str(P["devprep"].relative_to(root)) if devprep else "",
        "asset_checklist": devprep["checklist"] if devprep else [],
        "build_pages": [p["URL"] for p in build], "checked": checked, "missing": missing,
        "skipped": [p["URL"] for p in skipped],
        "screenshots": [os.path.relpath(s, root).replace(os.sep, "/") for s in shots],
        "screenshots_note": why, "images": images, "findings": F.items, "launch_toggles": toggles,
        "am_items": am, "not_checked": notes,
    }
    P["qa"].mkdir(parents=True, exist_ok=True)
    P["scan"].write_text(json.dumps(scan, indent=2) + "\n", encoding="utf-8")
    sev = {s: sum(1 for f in F.items if f["severity"] == s) for s in SEVERITIES}
    print(f"Wrote {P['scan'].relative_to(root)}")
    print(f"Build pages: {len(build)} ({len(checked)} checked, {len(missing)} missing on staging)")
    print(f"Script findings: {sev['CRITICAL']} CRITICAL, {sev['MAJOR']} MAJOR, {sev['MINOR']} MINOR")
    print(f"Launch toggles: {len(toggles)}; AM items: {len(am)}")
    if shots:
        print(f"Screenshots: {len(shots)} in qa/{a.slug}/screens/ (look at them before writing Design findings)")
    else:
        print(f"Screenshots: none ({why}). Add no Design findings from looking at the pages.")
    return 0


# --------------------------------------------------------------------------- #
# report
# --------------------------------------------------------------------------- #
def parse_table(text: str, header: str) -> list[list[str]]:
    lines = text.split("\n")
    rows, on = [], False
    for line in lines:
        if line.strip() == header:
            on = True
            continue
        if on:
            if re.match(r"^\|[\s:|-]+\|$", line.strip()):
                continue
            if not line.startswith("|"):
                break
            cells = [c.strip() for c in line.strip()[1:-1].split(" | ")]
            rows.append(cells)
    return rows


def parse_notes(text: str, root: Path, scan: dict) -> tuple[list[dict], list[str], list[str]]:
    errors, design, am = [], [], []
    rows = parse_table(text, "| Page URL | Severity | Finding | Fix | Evidence |")
    checklist = [l[2:].strip() for l in scan.get("asset_checklist", []) if l.startswith("- ")]
    for i, r in enumerate(rows, 1):
        if len(r) != 5:
            errors.append(f"design row {i}: needs 5 cells")
            continue
        page, sev, finding, fix, ev = r
        if sev not in SEVERITIES:
            errors.append(f"design row {i}: severity {sev!r} is not CRITICAL, MAJOR or MINOR")
        if norm_path(page) not in {norm_path(p) for p in scan["build_pages"]}:
            errors.append(f"design row {i}: {page} is not a Build page in the index")
        if ev.startswith("asset checklist:"):
            line = ev.split(":", 1)[1].strip()
            if line not in checklist:
                errors.append(f"design row {i}: evidence {ev!r} is not a line of the asset checklist")
        else:
            evp = ev.strip("`")
            if evp not in scan.get("screenshots", []) or not (root / evp).exists():
                errors.append(f"design row {i}: evidence {ev!r} is not a screenshot from this scan")
        if not finding or not fix:
            errors.append(f"design row {i}: finding and fix must be filled")
        design.append({"page": page, "severity": sev, "finding": finding, "fix": fix, "evidence": ev.strip("`")})
    sec = re.search(r"^## AM Items\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    if sec:
        am = [l[2:].strip() for l in sec.group(1).split("\n") if l.startswith("- ") and l[2:].strip()]
    return design, am, errors


def earlier_report(qa: Path, slug: str, date: str) -> Path | None:
    """Newest report dated before this run. A same-day re-run compares with the same
    earlier report the first run of the day used, so running report twice changes nothing."""
    pat = re.compile(rf"^{re.escape(slug)}-staging-qa-(\d{{4}}-\d{{2}}-\d{{2}})\.md$")
    found = sorted((m.group(1), p) for p in qa.glob(f"{slug}-staging-qa-*.md") if (m := pat.match(p.name)))
    before = [p for d, p in found if d < date]
    if before:
        return before[-1]
    return None


def cell(s: str) -> str:
    return s.replace("|", "\\|").replace("\n", " ")


def cmd_report(a) -> int:
    root = Path(a.root).resolve()
    P = paths_for(root, a.slug)
    if not P["scan"].exists():
        die(f"STOP: run scan first; {P['scan'].relative_to(root)} is missing.")
    scan = json.loads(read(P["scan"]))
    date = a.date or scan["date"]
    out = P["qa"] / f"{a.slug}-staging-qa-{date}.md"
    findings = [dict(f) for f in scan["findings"]]
    am = list(scan["am_items"])
    if P["notes"].exists():
        design, am_notes, errs = parse_notes(read(P["notes"]), root, scan)
        if errs:
            print("Review notes rejected; fix qa/<slug>/<slug>-review-notes.md and run report again:", file=sys.stderr)
            for e in errs:
                print("  - " + e, file=sys.stderr)
            return 1
        for d in design:
            fid = finding_id(d["page"], "design", d["finding"])
            if any(f["finding_id"] == fid for f in findings):
                continue
            findings.append({"finding_id": fid, "page": d["page"], "check": "design", "detail": d["finding"],
                             "department": "Design", "severity": d["severity"], "finding": d["finding"],
                             "fix": d["fix"], "evidence": d["evidence"], "source": "review"})
        am.extend(am_notes)
    for f in findings:
        if f["department"] == "Design" and f.get("evidence") and "(seen in" not in f["finding"]:
            ev = f["evidence"]
            f["finding"] = f["finding"].rstrip() + (f" ({ev})" if ev.startswith(("asset checklist", "image request")) else f" (seen in {ev})")
    order = {s: i for i, s in enumerate(SEVERITIES)}
    findings.sort(key=lambda f: (order[f["severity"]], scan["build_pages"].index(f["page"]) if f["page"] in scan["build_pages"] else 99, DEPARTMENTS.index(f["department"])))
    prev_path = earlier_report(P["qa"], a.slug, date)
    prev_rows = []
    if prev_path is not None:
        prev_rows = parse_table(read(prev_path), TABLE_HEADER)
    prev = {r[0]: r for r in prev_rows if len(r) == 6}
    cur_ids = {f["finding_id"] for f in findings}
    for f in findings:
        f["status"] = ("OPEN" if f["finding_id"] in prev else "NEW") if prev_path else "NEW"
    fixed = [r for fid, r in prev.items() if fid not in cur_ids]
    routing = parse_routing(read(P["routing"])) if P["routing"].exists() else parse_routing("")

    sev = {s: sum(1 for f in findings if f["severity"] == s) for s in SEVERITIES}
    dep = {d: sum(1 for f in findings if f["department"] == d) for d in DEPARTMENTS}
    result = "NOT READY" if sev["CRITICAL"] else ("CONDITIONAL" if sev["MAJOR"] else "READY")
    shots = scan["screenshots"]
    L = [
        f"Client: {scan['client']}",
        f"Checked: {date}",
        f"Staging: {scan['base_url']}" + (f" (saved pages: {scan['saved']}/)" if scan["saved"] else ""),
        f"Dev handoff index: {scan['index']} ({scan['index_last_line'] or 'no result line'})",
        f"Design QA and dev prep: {scan['devprep'] or 'none'}",
        f"Compared with: {prev_path.relative_to(root).as_posix() if prev_path else 'none (first run)'}",
        f"Screenshots: qa/{a.slug}/screens/ ({len(shots)} files)" if shots else f"Screenshots: none ({scan['screenshots_note']})",
        "",
        f"# Staging QA: {scan['client']}",
        "",
        "## Summary",
        "",
        f"Pages checked: {len(scan['checked'])} of {len(scan['build_pages'])} Build pages ({len(scan['missing'])} missing on staging); skipped (not Build): {len(scan['skipped'])}",
        f"Open findings: {sev['CRITICAL']} CRITICAL, {sev['MAJOR']} MAJOR, {sev['MINOR']} MINOR",
        "By department: " + ", ".join(f"{d} {dep[d]}" for d in DEPARTMENTS),
    ]
    if prev_path:
        n_open = sum(1 for f in findings if f["status"] == "OPEN")
        n_new = sum(1 for f in findings if f["status"] == "NEW")
        L.append(f"Re-run: {len(fixed)} FIXED, {n_open} OPEN, {n_new} NEW")
    L += [f"AM items: {len(am)}", f"Launch toggles: {len(scan['launch_toggles'])}", STRUCTURED, "",
          "## Findings", "", TABLE_HEADER, "|---|---|---|---|---|---|"]
    for f in findings:
        L.append(f"| {f['finding_id']} | {f['page']} | {f['department']} | {f['severity']} | {cell(f['finding'])} | {cell(f['fix'])} |")
    if not findings:
        L.append("| none | | | | No open findings. | |")
    if prev_path:
        L += ["", "## Re-run Status", "", RERUN_HEADER, "|---|---|---|---|---|---|"]
        for f in findings:
            L.append(f"| {f['finding_id']} | {f['status']} | {f['page']} | {f['department']} | {f['severity']} | {cell(f['finding'])} |")
        for r in fixed:
            L.append(f"| {r[0]} | FIXED | {r[1]} | {r[2]} | {r[3]} | {r[4]} |")
    L += ["", "## Launch Toggles", ""]
    L += [f"- {t}" for t in scan["launch_toggles"]] or ["- none"]
    L += ["", "## AM Items", "", "For the Account Manager's review. Not sent to BugHerd.", ""]
    L += [f"- {x}" for x in am] or ["- none"]
    L += ["", "## Not Checked", ""]
    L += [f"- {x}" for x in scan["not_checked"]] or ["- nothing"]
    L += ["", f"RESULT: {result}", ""]
    out.write_text("\n".join(L), encoding="utf-8")

    known = {}
    if P["tasks"].exists():
        try:
            # A FIXED finding's task may already be closed, so if it comes back it gets a new task.
            known = {t["finding_id"]: t.get("bugherd_task_id", "") for t in json.loads(read(P["tasks"]))
                     if t.get("bugherd_task_id") and t.get("status") != "FIXED"}
        except (json.JSONDecodeError, KeyError, TypeError):
            known = {}
    tasks = []
    for f in findings:
        tasks.append(task_obj(f["finding_id"], f["status"], f["page"], f["department"],
                              f["severity"], f["finding"], f["fix"], scan, routing, date, known))
    for r in fixed:
        if r[2] in DEPARTMENTS and r[3] in SEVERITIES:
            tasks.append(task_obj(r[0], "FIXED", r[1], r[2], r[3], r[4].replace("\\|", "|"), "", scan,
                                  routing, date, known))
    P["tasks"].write_text(json.dumps(tasks, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out.relative_to(root).as_posix()} and {P['tasks'].relative_to(root).as_posix()}")
    print(f"Open findings: {sev['CRITICAL']} CRITICAL, {sev['MAJOR']} MAJOR, {sev['MINOR']} MINOR; AM items: {len(am)}")
    if prev_path:
        print(f"Re-run against {prev_path.name}: {len(fixed)} FIXED, {sum(1 for f in findings if f['status']=='OPEN')} OPEN, {sum(1 for f in findings if f['status']=='NEW')} NEW")
    unassigned = sorted({t["department"] for t in tasks if t["create"] and not t["assignee"]})
    if unassigned:
        print("No assignee for: " + ", ".join(unassigned) + " (add them to qa/routing.md or ask the PM)")
    print(f"BugHerd tasks to create: {sum(1 for t in tasks if t['create'])}")
    print(f"RESULT: {result}")
    return cmd_check(argparse.Namespace(report=str(out), root=str(root)))


def task_obj(fid, status, page, dept, sev, finding, fix, scan, routing, date, known):
    title = f"{page}: {finding}"
    if len(title) > 200:
        title = title[:197].rstrip() + "..."
    desc = f"{finding} {fix}".strip() + f" (Staging QA {date}, {fid})"
    return {
        "finding_id": fid, "status": status, "create": status == "NEW" and not known.get(fid),
        "bugherd_task_id": known.get(fid, ""),
        "page_url": scan["base_url"] + page if page.startswith("/") else page,
        "department": dept, "column": routing["columns"].get(dept, DEFAULT_COLUMNS[dept]),
        "assignee": routing["assignees"].get(dept, ""), "severity": sev,
        "bugherd_severity": BUGHERD_SEVERITY[sev], "title": title, "description": desc[:2000],
    }


# --------------------------------------------------------------------------- #
# check
# --------------------------------------------------------------------------- #
def cmd_check(a) -> int:
    rp = Path(a.report)
    if not rp.is_absolute():
        rp = Path(a.root).resolve() / rp
    root = Path(a.root).resolve()
    text = read(rp)
    errs = []
    m = re.match(r"^(.+)-staging-qa-(\d{4}-\d{2}-\d{2})\.md$", rp.name)
    if not m:
        errs.append("file name is not <slug>-staging-qa-<YYYY-MM-DD>.md")
        slug = ""
    else:
        slug = m.group(1)
    for head in ("Client: ", "Checked: ", "Staging: ", "Dev handoff index: ", "Compared with: ", "Screenshots: "):
        if not re.search(rf"^{re.escape(head)}", text, re.M):
            errs.append(f"header line {head.strip()} missing")
    for sec in ("## Summary", "## Findings", "## Launch Toggles", "## AM Items", "## Not Checked"):
        if f"\n{sec}\n" not in text:
            errs.append(f"section {sec} missing")
    if STRUCTURED not in text:
        errs.append("structured data line missing")
    if text.count(STRUCTURED) != 1:
        errs.append("structured data line must appear once")
    rows = [r for r in parse_table(text, TABLE_HEADER) if r and r[0] != "none"]
    shots_dir = "qa/" + slug + "/screens/"
    for r in rows:
        if len(r) != 6:
            errs.append(f"findings row {r[:1]} does not have 6 cells")
            continue
        fid, page, dep, sev, finding, fix = r
        if not re.fullmatch(r"QA-[0-9a-f]{8}", fid):
            errs.append(f"{fid}: # must be a finding id QA-xxxxxxxx")
        if dep not in DEPARTMENTS:
            errs.append(f"{fid}: department {dep!r} is not one of {DEPARTMENTS}")
        if sev not in SEVERITIES:
            errs.append(f"{fid}: severity {sev!r}")
        if not finding or not fix:
            errs.append(f"{fid}: finding and fix must be filled")
        if dep == "Design":
            ev = re.search(r"\((?:seen in (\S+)|asset checklist: .+|image request failed)\)$", finding)
            if not ev:
                errs.append(f"{fid}: Design finding without evidence (screenshot or asset checklist)")
            elif ev.group(1) and (not ev.group(1).startswith(shots_dir) or not (root / ev.group(1)).exists()):
                errs.append(f"{fid}: screenshot {ev.group(1)} does not exist")
        if "noindex" in finding.lower() and "robots" not in finding.lower():
            errs.append(f"{fid}: noindex is a launch toggle, not a finding")
    sev = {s: sum(1 for r in rows if len(r) == 6 and r[3] == s) for s in SEVERITIES}
    want = f"Open findings: {sev['CRITICAL']} CRITICAL, {sev['MAJOR']} MAJOR, {sev['MINOR']} MINOR"
    if want not in text:
        errs.append(f"summary does not match the table ({want})")
    result = "NOT READY" if sev["CRITICAL"] else ("CONDITIONAL" if sev["MAJOR"] else "READY")
    last = [l for l in text.strip().split("\n") if l.strip()][-1]
    if last != f"RESULT: {result}":
        errs.append(f"last line must be RESULT: {result}")
    rerun = parse_table(text, RERUN_HEADER)
    compared = re.search(r"^Compared with: (.+)$", text, re.M)
    if compared and not compared.group(1).startswith("none") and not rerun:
        errs.append("a re-run must have the Re-run Status table")
    for r in rerun:
        if len(r) != 6 or r[1] not in ("FIXED", "OPEN", "NEW"):
            errs.append(f"re-run row {r[:2]} must be FIXED, OPEN or NEW")
    tp = rp.parent / f"{slug}-bugherd-tasks.json"
    if not tp.exists():
        errs.append(f"{tp.name} missing")
    else:
        try:
            tasks = json.loads(read(tp))
        except json.JSONDecodeError as e:
            tasks = []
            errs.append(f"{tp.name} is not valid JSON: {e}")
        open_ids = [t["finding_id"] for t in tasks if t.get("status") != "FIXED"]
        if open_ids != [r[0] for r in rows]:
            errs.append("task file does not match the findings table row for row")
        status = {r[0]: r[1] for r in rerun}
        for t in tasks:
            for k in ("finding_id", "status", "create", "bugherd_task_id", "page_url", "department", "column",
                      "assignee", "severity", "bugherd_severity", "title", "description"):
                if k not in t:
                    errs.append(f"task {t.get('finding_id')}: key {k} missing")
            if t.get("department") not in DEPARTMENTS:
                errs.append(f"task {t.get('finding_id')}: department must not be {t.get('department')!r}")
            if INTERNAL_WORDS.search(t.get("description", "") + " " + t.get("title", "")):
                errs.append(f"task {t.get('finding_id')}: internal wording in client-visible text")
            if rerun and status.get(t["finding_id"]) != t.get("status"):
                errs.append(f"task {t['finding_id']}: status differs from the Re-run Status table")
            if t.get("create") != (t.get("status") == "NEW" and not t.get("bugherd_task_id")):
                errs.append(f"task {t['finding_id']}: create must be true only for NEW findings with no BugHerd task yet")
    if errs:
        print(f"CHECK FAIL {rp.name}")
        for e in errs:
            print("  - " + e)
        return 1
    print(f"CHECK PASS {rp.name}: {len(rows)} findings, task file matches")
    return 0


def cmd_created(a) -> int:
    """Record the BugHerd task ids that create_tasks returned, so no run creates them again."""
    root = Path(a.root).resolve()
    tp = paths_for(root, a.slug)["tasks"]
    if not tp.exists():
        die(f"STOP: {tp.relative_to(root)} does not exist; run report first.")
    tasks = json.loads(read(tp))
    by_id = {t["finding_id"]: t for t in tasks}
    bad = []
    for pair in a.pairs:
        fid, _, tid = pair.partition("=")
        if fid not in by_id or not tid.strip():
            bad.append(pair)
            continue
        by_id[fid]["bugherd_task_id"] = tid.strip()
        by_id[fid]["create"] = False
    tp.write_text(json.dumps(tasks, indent=2) + "\n", encoding="utf-8")
    left = sum(1 for t in tasks if t["create"])
    print(f"Recorded {len(a.pairs) - len(bad)} BugHerd task id(s) in {tp.relative_to(root).as_posix()}; {left} still to create")
    if bad:
        print("Not recorded (unknown finding id or empty task id): " + ", ".join(bad))
        return 1
    return 0


# --------------------------------------------------------------------------- #
# contract readers
# --------------------------------------------------------------------------- #
def cmd_reader(a, fn, validate_keys) -> int:
    if a.validate:
        data = json.loads(read(Path(a.file)))
        items = data if isinstance(data, list) else [data]
        if not items:
            die("no items")
        for it in items:
            for k in validate_keys:
                if k not in it:
                    die(f"missing key {k}")
        print(f"ok: {len(items)} item(s) with {', '.join(validate_keys)}")
        return 0
    print(json.dumps(fn(a.file, read(Path(a.file))), indent=2))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan")
    s.add_argument("--root", default=".")
    s.add_argument("--slug", required=True)
    s.add_argument("--base-url", required=True)
    s.add_argument("--saved", default="")
    s.add_argument("--user", default="")
    s.add_argument("--password", default="")
    s.add_argument("--date", default="")
    s.add_argument("--no-screens", action="store_true")
    r = sub.add_parser("report")
    r.add_argument("--root", default=".")
    r.add_argument("--slug", required=True)
    r.add_argument("--date", default="")
    c = sub.add_parser("check")
    c.add_argument("report")
    c.add_argument("--root", default=".")
    cr = sub.add_parser("created")
    cr.add_argument("--root", default=".")
    cr.add_argument("--slug", required=True)
    cr.add_argument("pairs", nargs="+", help="QA-xxxxxxxx=<BugHerd task id>")
    for name in ("index", "article", "devprep"):
        x = sub.add_parser(name)
        x.add_argument("file")
        x.add_argument("--validate", action="store_true")
    a = ap.parse_args()
    if a.cmd == "scan":
        return cmd_scan(a)
    if a.cmd == "report":
        return cmd_report(a)
    if a.cmd == "check":
        return cmd_check(a)
    if a.cmd == "created":
        return cmd_created(a)
    if a.cmd == "index":
        return cmd_reader(a, index_json, ["Page", "URL", "Content file", "Meta title", "Meta description", "H1", "Internal links", "Priority"])
    if a.cmd == "article":
        return cmd_reader(a, article_json, ["article.md", "<!-- section: Final CTA -->"])
    return cmd_reader(a, devprep_json, ["## Asset Checklist", "### Images", "RESULT:"])


if __name__ == "__main__":
    sys.exit(main())
