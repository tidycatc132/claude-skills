#!/usr/bin/env python3
"""Launch check: the same QA, run by Dev against the production site right after deployment.

Used through qa.py (`scan --launch`, `report --launch`, `created --launch`, `check` on a
launch report, `redirects <index>`, `launch-check <report>`); not run on its own.

Per Build page of the dev handoff index: 200 over HTTPS, no noindex, canonical on the production
domain, no links or assets on the staging domain, meta title, description and H1 still the index
values. Site-wide: every `### Redirects` row answers 301 or 308 to its New URL, robots.txt blocks
no Build page, /sitemap.xml exists and lists every Build page. Every finding is Development's.
Standard library only.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import qa as Q

DEPT = "Development"
TICKS = [
    "Forms submit, and the test entry reaches the client's notification inbox",
    "Live chat loads and a test message arrives",
    "Analytics firing: a visit shows in GA4 Realtime",
    "Juvo snippet installed",
    "SSL certificate valid: the padlock shows and the certificate does not expire within 30 days",
]
REDIRECTS_HEADER = "| Old URL | New URL | Note |"
LIVE_OK, LIVE_ISSUES = "LIVE OK", "LIVE ISSUES"
CURL_HINT = "curl -s -o /dev/null -w '%{url_effective} %{http_code} %{redirect_url}\\n' <old URL>"


# --------------------------------------------------------------------------- #
# Readers
# --------------------------------------------------------------------------- #
def parse_redirects(text: str) -> dict:
    """The index's `### Redirects` table. present: the section exists; none: `No existing site`."""
    m = re.search(r"(?m)^### Redirects\s*$", text)
    if not m:
        return {"present": False, "none": False, "rows": []}
    rest = text[m.end():]
    n = re.search(r"(?m)^#{2,3} ", rest)
    sec = rest[: n.start()] if n else rest
    rows = []
    for r in Q.parse_table(sec, REDIRECTS_HEADER):
        if len(r) >= 2 and r[0]:
            rows.append({"Old URL": r[0], "New URL": r[1], "Note": r[2] if len(r) > 2 else ""})
    return {"present": True, "none": "no existing site" in sec.lower() and not rows, "rows": rows}


def redirects_json(path: str, text: str) -> list[dict]:
    return [{"file": path, **r} for r in parse_redirects(text)["rows"]]


def redirect_key(url: str) -> str:
    """Host (without www) plus the path and query exactly as written."""
    u = urllib.parse.urlsplit(url if "://" in url else "https://x" + url)
    h = (u.hostname or "").lower()
    h = h[4:] if h.startswith("www.") else h
    return h + (u.path or "/") + ("?" + u.query if u.query else "")


def parse_saved_redirects(text: str) -> dict:
    """Lines `<old URL> <status> <location>` (what CURL_HINT prints), keyed by redirect_key."""
    out = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2 or not parts[1].isdigit():
            continue
        loc = parts[2] if len(parts) > 2 and parts[2] != "-" else ""
        out[redirect_key(parts[0])] = {"status": int(parts[1]), "location": loc}
    return out


def robots_groups(text: str) -> list[tuple[str, list[tuple[str, str]]]]:
    """Rule sets to test: Googlebot's own group if robots.txt has one, and the `*` group. Each
    crawler obeys only the most specific group that names it, so the two are never merged."""
    groups, agents, in_rules = {}, [], False
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if ":" not in line:
            continue
        k, v = (x.strip() for x in line.split(":", 1))
        k = k.lower()
        if k == "user-agent":
            if in_rules:
                agents, in_rules = [], False
            agents.append(v.lower())
            groups.setdefault(v.lower(), [])
        elif k in ("allow", "disallow"):
            in_rules = True
            for a in agents:
                groups.setdefault(a, []).append((k, v))
    out = []
    if "googlebot" in groups:
        out.append(("Googlebot", groups["googlebot"]))
    if "*" in groups:
        out.append(("all crawlers", groups["*"]))
    return out


def robots_blocks(rules: list[tuple[str, str]], path: str) -> str | None:
    """The Disallow rule that blocks path (longest match wins; Allow wins a tie), else None."""
    best = None
    for kind, pat in rules:
        if not pat:
            continue
        rx = "^" + re.escape(pat).replace(r"\*", ".*")
        if rx.endswith(r"\$"):
            rx = rx[:-2] + "$"
        if re.match(rx, path):
            key = (len(pat), kind == "allow")
            if best is None or key > best[0]:
                best = (key, kind, pat)
    return best[2] if best and best[1] == "disallow" else None


def sitemap_locs(text: str) -> tuple[list[str], bool]:
    locs = [Q.html.unescape(x.strip()) for x in re.findall(r"<loc>\s*(.*?)\s*</loc>", text, re.S | re.I)]
    return locs, bool(re.search(r"<sitemapindex\b", text, re.I))


# --------------------------------------------------------------------------- #
# Fetching without following redirects
# --------------------------------------------------------------------------- #
class _NoFollow(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D401
        return None


def head_no_follow(url: str) -> dict:
    opener = urllib.request.build_opener(_NoFollow, urllib.request.HTTPSHandler(context=ssl.create_default_context()))
    req = urllib.request.Request(url, headers={"User-Agent": "staging-site-qa/1.0 (launch check)"})
    try:
        with opener.open(req, timeout=25) as r:
            return {"status": r.status, "location": r.headers.get("Location", "")}
    except urllib.error.HTTPError as e:
        return {"status": e.code, "location": e.headers.get("Location", "") if e.headers else ""}
    except (urllib.error.URLError, OSError, ValueError) as e:
        return {"status": 0, "location": "", "error": str(getattr(e, "reason", e))}


# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
def paths_for(root: Path, slug: str) -> dict:
    P = Q.paths_for(root, slug)
    P["scan"] = root / "qa" / slug / f"{slug}-launch-scan.json"
    P["tasks"] = root / "qa" / slug / f"{slug}-launch-bugherd-tasks.json"
    return P


def newest_dated(folder: Path, slug: str, kind: str, before: str | None = None) -> Path | None:
    pat = re.compile(rf"^{re.escape(slug)}-{kind}-(\d{{4}}-\d{{2}}-\d{{2}})\.md$")
    found = sorted((m.group(1), p) for p in folder.glob(f"{slug}-{kind}-*.md") if (m := pat.match(p.name)))
    if before is not None:
        found = [x for x in found if x[0] < before]
    return found[-1][1] if found else None


# --------------------------------------------------------------------------- #
# scan --launch
# --------------------------------------------------------------------------- #
def cmd_scan(a) -> int:
    root = Path(a.root).resolve()
    P = paths_for(root, a.slug)
    if not P["index"].exists():
        Q.die(f"STOP: no dev handoff index at {P['index'].relative_to(root)}. Run dev-handoff-index first.")
    if not P["context"].exists():
        Q.die(f"STOP: no client context at {P['context'].relative_to(root)}.")
    if not a.base_url:
        Q.die("STOP: give the production base URL (--base-url), even with --saved.")
    staging_from = "given"
    staging = a.staging_url
    if not staging:
        rep = newest_dated(P["qa"], a.slug, "staging-qa") if P["qa"].is_dir() else None
        if rep is not None:
            m = re.search(r"(?m)^Staging: (\S+)", Q.read(rep))
            if m:
                staging, staging_from = m.group(1), rep.relative_to(root).as_posix()
    if not staging:
        Q.die("STOP: the staging domain is not known (no staging QA report with a Staging: line). "
              "Give it with --staging-url so staging-domain links can be found. Nothing was written.")
    staging_host = (urllib.parse.urlsplit(staging if "://" in staging else "https://" + staging).hostname or "").lower()
    saved = None
    if a.saved:
        saved = (root / a.saved).resolve() if not os.path.isabs(a.saved) else Path(a.saved)
        if not saved.is_dir():
            Q.die(f"STOP: saved pages folder {a.saved} does not exist.")
    red_file = None
    if a.redirects_file:
        red_file = (root / a.redirects_file) if not os.path.isabs(a.redirects_file) else Path(a.redirects_file)
        if not red_file.is_file():
            Q.die(f"STOP: redirect-response file {a.redirects_file} does not exist.")
    site = Q.Site(a.base_url, saved)
    if staging_host and staging_host == site.host:
        Q.die(f"STOP: {a.base_url} is the staging site. The launch check runs against the production URL.")
    idx_text = Q.read(P["index"])
    idx = Q.parse_index(idx_text)
    ctx = Q.parse_context(Q.read(P["context"]))
    if saved is None:
        probe = site.get("/")
        if probe["status"] in (0, 401, 403):
            why = probe.get("error") or f"HTTP {probe['status']}"
            Q.die(f"STOP: could not reach the live site at {a.base_url} ({why}). Nothing was written. "
                  "Check the URL, or save each page's HTML (plus robots.txt and sitemap.xml) into a folder, "
                  f"save the redirect responses with `{CURL_HINT}`, and run with --saved and --redirects-file.")
    bare = site.host[4:] if site.host.startswith("www.") else site.host
    prod_hosts = {bare, "www." + bare}
    if ctx["website"]:
        prod_hosts |= {ctx["website"], "www." + ctx["website"]}
    build = [p for p in idx["pages"] if p["Priority"].lower().startswith("build")]
    skipped = [p for p in idx["pages"] if p not in build]
    F, notes, checked, missing = Q.Findings(), [], [], []

    def on_staging(u: str) -> bool:
        return bool(staging_host) and (urllib.parse.urlsplit(u).hostname or "").lower() == staging_host

    for pg in build:
        path = pg["URL"]
        res = site.get(path)
        if res["status"] == 404 or (saved is not None and res["status"] != 200):
            why = "not in the saved pages" if saved is not None else "HTTP 404"
            F.add(path, "page-missing", "", DEPT, "CRITICAL", f"The page is missing on the live site ({why}).",
                  f"Publish {path} on the live site.")
            missing.append(path)
            continue
        if res["status"] != 200:
            why = res.get("error", "no response") if res["status"] == 0 else f"HTTP {res['status']}"
            F.add(path, "http-status", str(res["status"]), DEPT, "CRITICAL",
                  f"The page does not load on the live site ({why}).", "Make the page return 200.")
            missing.append(path)
            continue
        if saved is None and Q.norm_path(urllib.parse.urlsplit(res["final"]).path or "/") != Q.norm_path(path):
            F.add(path, "page-missing", "", DEPT, "CRITICAL",
                  f"The page is missing on the live site (it redirects to {res['final']}).",
                  f"Publish {path} at its approved address.")
            missing.append(path)
            continue
        if saved is None and urllib.parse.urlsplit(res["final"]).scheme != "https":
            F.add(path, "https", "", DEPT, "MAJOR", "The page loads over HTTP, not HTTPS.",
                  "Serve the page over HTTPS and redirect HTTP to it.")
        checked.append(path)
        p = Q.PageParser()
        p.raw = res["body"].decode("utf-8", errors="replace")
        p.feed(p.raw)
        p.close()

        metas = re.findall(r"<meta\b[^>]*>", p.raw, re.I)
        vals = [m for m in metas if re.search(r"\bname\s*=\s*[\"']?(?:robots|googlebot)\b", m, re.I)]
        robots = " ".join(vals + [res["headers"].get("x-robots-tag", "")]).lower()
        if re.search(r"\bnoindex\b|content\s*=\s*[\"']?\s*none\b", robots):
            F.add(path, "noindex", "", DEPT, "CRITICAL",
                  "The page is still set to noindex, so search engines will drop it.",
                  "Remove the noindex robots tag (and any X-Robots-Tag header) from the page.")

        if pg["Meta title"] != "none":
            if not p.title:
                F.add(path, "meta-title", pg["Meta title"], DEPT, "CRITICAL", "The page has no meta title.",
                      f'Set the meta title to "{pg["Meta title"]}".')
            elif Q.norm(p.title) != Q.norm(pg["Meta title"]):
                F.add(path, "meta-title", pg["Meta title"], DEPT, "MAJOR",
                      f'The meta title is "{p.title}"; the approved title is "{pg["Meta title"]}".',
                      f'Set the meta title to "{pg["Meta title"]}".')
        if pg["Meta description"] != "none":
            md = p.meta.get("description", "")
            if not md:
                F.add(path, "meta-description", pg["Meta description"], DEPT, "MAJOR",
                      "The page has no meta description.", f'Set the meta description to "{pg["Meta description"]}".')
            elif Q.norm(md) != Q.norm(pg["Meta description"]):
                F.add(path, "meta-description", pg["Meta description"], DEPT, "MAJOR",
                      f'The meta description is "{Q.norm(md)}"; the approved one is "{pg["Meta description"]}".',
                      f'Set the meta description to "{pg["Meta description"]}".')
        if pg["H1"] != "none":
            if not p.h1:
                F.add(path, "h1", pg["H1"], DEPT, "CRITICAL", "The page has no H1.", f'Add the H1 "{pg["H1"]}".')
            elif not any(Q.norm(h) == Q.norm(pg["H1"]) for h in p.h1):
                F.add(path, "h1", pg["H1"], DEPT, "MAJOR",
                      f'The H1 is "{p.h1[0]}"; the approved H1 is "{pg["H1"]}".', f'Change the H1 to "{pg["H1"]}".')
            if len(p.h1) > 1:
                F.add(path, "h1-multiple", str(len(p.h1)), DEPT, "MINOR", f"The page has {len(p.h1)} H1 headings.",
                      f'Keep one H1 ("{pg["H1"]}") and make the others H2 or plain text.')

        canon = [l["href"] for l in p.links if "canonical" in l["rel"].split()]
        want = f"https://{bare}{path}"
        if not canon:
            F.add(path, "canonical", "", DEPT, "MAJOR", "The page has no canonical tag.",
                  f"Add a canonical tag pointing to {want}.")
        else:
            c = urllib.parse.urlsplit(urllib.parse.urljoin(site.base + path, canon[0]))
            chost = (c.hostname or "").lower()
            bad = None
            if chost == staging_host:
                bad = f"The canonical tag points at the staging domain ({canon[0]})."
            elif chost not in prod_hosts:
                bad = f"The canonical tag points at another domain ({canon[0]})."
            elif Q.norm_path(c.path or "/") != Q.norm_path(path):
                bad = f"The canonical tag points to {canon[0]}, not to this page."
            if bad:
                F.add(path, "canonical", "", DEPT, "MAJOR", bad, f"Point the canonical tag at {want}.")

        urls = [x["href"] for x in p.anchors] + [i["src"] for i in p.images] + p.assets + \
               [l["href"] for l in p.links if "canonical" not in l["rel"].split()]
        if p.meta.get("og:url"):
            urls.append(p.meta["og:url"])
        if p.meta.get("og:image"):
            urls.append(p.meta["og:image"])
        hits = list(dict.fromkeys(u for u in urls if on_staging(u)))
        if staging_host:
            raw_rx = re.compile(r"(?:https?:)?(?:\\?/){2}(?:[\w-]+\.)*" + re.escape(staging_host) + r"[^\s\"'<>)]*", re.I)
            for u in raw_rx.findall(p.raw):
                u = u.replace("\\/", "/")
                if not any(u in h or h in u for h in hits) and u.rstrip("/") not in [c.rstrip("/") for c in canon]:
                    hits.append(u)
        if hits:
            ex = ", ".join(hits[:3]) + (f" and {len(hits) - 3} more" if len(hits) > 3 else "")
            F.add(path, "staging-domain", "live", DEPT, "MAJOR",
                  f"{len(hits)} link(s), image(s) or file(s) on the live page still point at the staging domain: {ex}.",
                  "Change them to the live domain (or relative links) and re-check the page.")

    # Redirects
    red = parse_redirects(idx_text)
    targets = [r for r in red["rows"] if r["New URL"].strip().upper() != "NO TARGET"]
    no_target = [r for r in red["rows"] if r not in targets]
    untested, red_note = [], ""
    saved_red = parse_saved_redirects(Q.read(red_file)) if red_file else None
    tested = passed = 0
    if not red["present"]:
        red_note = "no Redirects section in the index"
    elif red["none"] or not red["rows"]:
        red_note = "none in the index (no existing site)"
    elif saved is not None and saved_red is None:
        red_note = f"not tested (saved pages, no redirect-response file); {len(targets)} in the index"
        if targets:
            untested.append(f"{len(targets)} redirect(s) from the dev handoff index")
    else:
        for r in targets:
            old = r["Old URL"]
            o = urllib.parse.urlsplit(old if "://" in old else "https://" + bare + (old if old.startswith("/") else "/" + old))
            ohost = (o.hostname or "").lower()
            opath = Q.norm_path(o.path or "/")
            if saved_red is not None:
                got = saved_red.get(redirect_key(old))
                if got is None:
                    untested.append(f"the redirect for {old} (not in the redirect-response file)")
                    continue
            else:
                url = (site.base + (o.path or "/")) if ohost in prod_hosts or not ohost else old
                if o.query:
                    url += "?" + o.query
                got = head_no_follow(url)
            tested += 1
            st, loc = got["status"], got.get("location", "")
            nt = r["New URL"].strip()
            n = urllib.parse.urlsplit(nt if "://" in nt else "https://" + bare + nt)
            if st in (301, 302, 303, 307, 308) and loc:
                l = urllib.parse.urlsplit(urllib.parse.urljoin(f"https://{ohost or bare}{o.path or '/'}", loc))
                lhost = (l.hostname or "").lower()
                same_place = l.scheme == "https" and (l.path or "/") == (n.path or "/") and \
                    (lhost in prod_hosts if (n.hostname or "").lower() in prod_hosts else lhost == (n.hostname or "").lower())
            else:
                same_place = False
            if st in (301, 308) and same_place:
                passed += 1
                continue
            if st in (302, 303, 307) and same_place:
                F.add(opath, "redirect", nt, DEPT, "MAJOR",
                      f"{old} redirects to {nt} with a temporary {st}, not a permanent 301.",
                      f"Make the redirect from {opath} to {nt} a 301.")
            elif st in (301, 302, 303, 307, 308):
                F.add(opath, "redirect", nt, DEPT, "MAJOR",
                      f"{old} redirects to {loc or 'nowhere'}, not to {nt}.",
                      f"Point the 301 redirect from {opath} at {nt}.")
            else:
                why = f"HTTP {st}" if st else (got.get("error") or "no response")
                F.add(opath, "redirect", nt, DEPT, "MAJOR",
                      f"{old} does not redirect ({why}); it should answer 301 to {nt}.",
                      f"Add a 301 redirect from {opath} to {nt}.")
        red_note = f"{passed} of {tested} tested answer 301 or 308 to their New URL"
        if saved_red is not None:
            red_note += f" (from {os.path.relpath(red_file, root)})"
    for r in no_target:
        notes.append(f"Redirect for {r['Old URL']} not tested: NO TARGET in the dev handoff index (SEO to decide).")

    # robots.txt
    rb = site.get("/robots.txt")
    if rb["status"] == 200:
        rules = robots_groups(rb["body"].decode("utf-8", "replace"))
        blocked = []
        for pg in build:
            hit = [f"{who}: Disallow: {rule}" for who, rs in rules if (rule := robots_blocks(rs, pg["URL"]))]
            if hit:
                blocked.append((pg["URL"], "; ".join(hit)))
        if blocked:
            ex = ", ".join(f"{u} ({r})" for u, r in blocked[:4]) + (f" and {len(blocked) - 4} more" if len(blocked) > 4 else "")
            F.add("/robots.txt", "robots", "build pages", DEPT, "CRITICAL",
                  f"robots.txt blocks {len(blocked)} Build page(s) from search engines: {ex}.",
                  "Replace robots.txt with the live version from the dev handoff index.")
    elif saved is not None:
        untested.append("robots.txt (not in the saved pages)")
    elif rb["status"] != 404:
        notes.append(f"robots.txt answered HTTP {rb['status'] or 'no response'}; not read.")

    # sitemap.xml
    sm = site.get("/sitemap.xml")
    if sm["status"] == 200:
        locs, is_index = sitemap_locs(sm["body"].decode("utf-8", "replace"))
        if is_index:
            pages, queue, seen, unread = [], list(locs), set(), []
            while queue and len(seen) < 200:
                child = queue.pop(0)
                if child in seen:
                    continue
                seen.add(child)
                ch = (urllib.parse.urlsplit(child).hostname or "").lower()
                if on_staging(child):
                    pages.append(child)
                    continue
                if ch not in prod_hosts and ch != site.host:
                    notes.append(f"Child sitemap {child} is on another domain; its pages were not read.")
                    continue
                r = site.get(urllib.parse.urlsplit(child).path or "/")
                if r["status"] == 200:
                    sub, nested = sitemap_locs(r["body"].decode("utf-8", "replace"))
                    (queue if nested else pages).extend(sub)
                else:
                    unread.append(child)
            if queue:
                notes.append(f"Stopped after 200 child sitemaps; {len(queue)} not read.")
            locs = pages
            if unread and saved is not None:
                untested.append("child sitemap(s) " + ", ".join(unread) + " (not in the saved pages)")
            elif unread:
                notes.append("Child sitemap(s) did not load: " + ", ".join(unread) + ".")
        stag = [u for u in locs if on_staging(u)]
        listed = {Q.norm_path(u) for u in locs if (urllib.parse.urlsplit(u).hostname or "").lower() in prod_hosts | {site.host}}
        absent = [pg["URL"] for pg in build if Q.norm_path(pg["URL"]) not in listed]
        if stag:
            F.add("/sitemap.xml", "sitemap-staging", "", DEPT, "MAJOR",
                  f"The sitemap lists {len(stag)} URL(s) on the staging domain, for example {stag[0]}.",
                  "Regenerate the sitemap on the live site so every URL uses the live domain.")
        if absent and not (is_index and unread and saved is not None):
            F.add("/sitemap.xml", "sitemap-pages", "build pages", DEPT, "MAJOR",
                  f"The sitemap does not list {len(absent)} Build page(s): {', '.join(absent)}.",
                  "Add every page from the dev handoff index's sitemap list to /sitemap.xml.")
    elif saved is not None:
        untested.append("sitemap.xml (not in the saved pages)")
    else:
        F.add("/sitemap.xml", "sitemap-missing", "", DEPT, "MAJOR",
              f"There is no sitemap at /sitemap.xml (HTTP {sm['status'] or 'no response'}).",
              "Publish /sitemap.xml listing every Build page.")

    if untested:
        F.add("/", "untested", "saved", DEPT, "MAJOR",
              "These launch checks could not run from the saved pages: " + "; ".join(untested) + ".",
              f"Save them (redirects with {CURL_HINT}) and re-run the launch check.")
    if site.scheme != "https":
        F.add("/", "https", "site", DEPT, "MAJOR", "The live site is served over HTTP, not HTTPS.",
              "Install the certificate and redirect HTTP to HTTPS.")
    if saved is not None:
        notes.append(f"Saved pages from {os.path.relpath(saved, root)}: HTTPS and response headers (X-Robots-Tag) were not checked.")
    for p in skipped:
        notes.append(f"{p['Page']} ({p['URL']}) skipped: priority {p['Priority']}.")
    scan = {
        "mode": "launch", "client": ctx["name"] or a.slug, "slug": a.slug,
        "date": a.date or dt.date.today().isoformat(), "base_url": site.base,
        "saved": os.path.relpath(saved, root) if saved else "", "staging_host": staging_host,
        "staging_from": staging_from, "index": str(P["index"].relative_to(root)),
        "index_last_line": idx["last_line"], "redirects": red_note,
        "build_pages": [p["URL"] for p in build], "checked": checked, "missing": missing,
        "skipped": [p["URL"] for p in skipped], "findings": F.items, "not_checked": notes,
    }
    P["qa"].mkdir(parents=True, exist_ok=True)
    P["scan"].write_text(json.dumps(scan, indent=2) + "\n", encoding="utf-8")
    sev = {s: sum(1 for f in F.items if f["severity"] == s) for s in Q.SEVERITIES}
    print(f"Wrote {P['scan'].relative_to(root)}")
    print(f"Build pages: {len(build)} ({len(checked)} checked, {len(missing)} missing on the live site)")
    print(f"Redirects: {red_note}")
    print(f"Findings: {sev['CRITICAL']} CRITICAL, {sev['MAJOR']} MAJOR, {sev['MINOR']} MINOR")
    return 0


# --------------------------------------------------------------------------- #
# report --launch
# --------------------------------------------------------------------------- #
def task_obj(fid, status, page, sev, finding, fix, base, routing, date, known):
    title = f"{page}: {finding}"
    if len(title) > 200:
        title = title[:197].rstrip() + "..."
    desc = f"{finding} {fix}".strip() + f" (Launch check {date}, {fid})"
    return {
        "finding_id": fid, "status": status, "create": status == "NEW" and not known.get(fid),
        "bugherd_task_id": known.get(fid, ""), "page_url": base + page if page.startswith("/") else page,
        "department": DEPT, "column": routing["columns"].get(DEPT, Q.DEFAULT_COLUMNS[DEPT]),
        "assignee": routing["assignees"].get(DEPT, ""), "severity": sev,
        "bugherd_severity": Q.BUGHERD_SEVERITY[sev], "title": title, "description": desc[:2000],
    }


def cmd_report(a) -> int:
    root = Path(a.root).resolve()
    P = paths_for(root, a.slug)
    if not P["scan"].exists():
        Q.die(f"STOP: run scan --launch first; {P['scan'].relative_to(root)} is missing.")
    scan = json.loads(Q.read(P["scan"]))
    date = a.date or scan["date"]
    out = P["qa"] / f"{a.slug}-launch-check-{date}.md"
    findings = [dict(f) for f in scan["findings"]]
    order = {s: i for i, s in enumerate(Q.SEVERITIES)}
    pages = scan["build_pages"]
    findings.sort(key=lambda f: (order[f["severity"]], pages.index(f["page"]) if f["page"] in pages else len(pages)))
    prev_path = newest_dated(P["qa"], a.slug, "launch-check", before=date)
    prev = {}
    if prev_path is not None:
        prev = {r[0]: r for r in Q.parse_table(Q.read(prev_path), Q.TABLE_HEADER) if len(r) == 6 and r[0] != "none"}
    ids = {f["finding_id"] for f in findings}
    for f in findings:
        f["status"] = "OPEN" if f["finding_id"] in prev else "NEW"
    fixed = [r for fid, r in prev.items() if fid not in ids]
    routing = Q.parse_routing(Q.read(P["routing"])) if P["routing"].exists() else Q.parse_routing("")
    sev = {s: sum(1 for f in findings if f["severity"] == s) for s in Q.SEVERITIES}
    result = LIVE_ISSUES if sev["CRITICAL"] or sev["MAJOR"] else LIVE_OK
    L = [
        f"Client: {scan['client']}",
        f"Checked: {date}",
        f"Live: {scan['base_url']}" + (f" (saved pages: {scan['saved']}/)" if scan["saved"] else ""),
        f"Staging domain: {scan['staging_host']} ({scan['staging_from']})",
        f"Dev handoff index: {scan['index']} ({scan['index_last_line'] or 'no result line'})",
        f"Redirects: {scan['redirects']}",
        f"Compared with: {prev_path.relative_to(root).as_posix() if prev_path else 'none (first run)'}",
        "",
        f"# Launch Check: {scan['client']}",
        "",
        "## Summary",
        "",
        f"Pages checked: {len(scan['checked'])} of {len(pages)} Build pages ({len(scan['missing'])} missing on the live site); skipped (not Build): {len(scan['skipped'])}",
        f"Open findings: {sev['CRITICAL']} CRITICAL, {sev['MAJOR']} MAJOR, {sev['MINOR']} MINOR",
        "By department: " + ", ".join(f"{d} {len(findings) if d == DEPT else 0}" for d in Q.DEPARTMENTS),
    ]
    if prev_path:
        L.append(f"Re-run: {len(fixed)} FIXED, {sum(1 for f in findings if f['status'] == 'OPEN')} OPEN, "
                 f"{sum(1 for f in findings if f['status'] == 'NEW')} NEW")
    L += [Q.STRUCTURED, "", "## Findings", "", Q.TABLE_HEADER, "|---|---|---|---|---|---|"]
    for f in findings:
        L.append(f"| {f['finding_id']} | {f['page']} | {DEPT} | {f['severity']} | {Q.cell(f['finding'])} | {Q.cell(f['fix'])} |")
    if not findings:
        L.append("| none | | | | No open findings. | |")
    if prev_path:
        L += ["", "## Re-run Status", "", Q.RERUN_HEADER, "|---|---|---|---|---|---|"]
        for f in findings:
            L.append(f"| {f['finding_id']} | {f['status']} | {f['page']} | {DEPT} | {f['severity']} | {Q.cell(f['finding'])} |")
        for r in fixed:
            L.append(f"| {r[0]} | FIXED | {r[1]} | {r[2]} | {r[3]} | {r[4]} |")
        if not findings and not fixed:
            L.append("| none | | | | | Nothing open now or last time. |")
    L += ["", "## Dev Tick List", "", "Checked by hand on the live site; a script cannot prove these.", ""]
    L += [f"- [ ] {t}" for t in TICKS]
    L += ["", "## Not Checked", ""]
    L += [f"- {x}" for x in scan["not_checked"]] or ["- nothing"]
    L += ["", f"RESULT: {result}", ""]
    out.write_text("\n".join(L), encoding="utf-8")

    known = {}
    if P["tasks"].exists():
        try:
            old_tasks = json.loads(Q.read(P["tasks"]))
            # Every recorded id is kept (a same-day re-run must not lose them), except a finding
            # that was FIXED and is NEW again: a regression, whose old task may be closed.
            now = {f["finding_id"]: f["status"] for f in findings}
            known = {t["finding_id"]: t["bugherd_task_id"] for t in old_tasks if t.get("bugherd_task_id")
                     and not (t.get("status") == "FIXED" and now.get(t["finding_id"]) == "NEW")}
        except (json.JSONDecodeError, KeyError, TypeError):
            known = {}
    tasks = [task_obj(f["finding_id"], f["status"], f["page"], f["severity"], f["finding"], f["fix"],
                      scan["base_url"], routing, date, known) for f in findings]
    for r in fixed:
        if r[3] in Q.SEVERITIES:
            tasks.append(task_obj(r[0], "FIXED", r[1], r[3], r[4].replace("\\|", "|"), "", scan["base_url"],
                                  routing, date, known))
    P["tasks"].write_text(json.dumps(tasks, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out.relative_to(root).as_posix()} and {P['tasks'].relative_to(root).as_posix()}")
    print(f"Open findings: {sev['CRITICAL']} CRITICAL, {sev['MAJOR']} MAJOR, {sev['MINOR']} MINOR")
    if prev_path:
        print(f"Re-run against {prev_path.name}: {len(fixed)} FIXED, "
              f"{sum(1 for f in findings if f['status'] == 'OPEN')} OPEN, {sum(1 for f in findings if f['status'] == 'NEW')} NEW")
    if any(t["create"] for t in tasks) and not routing["assignees"].get(DEPT):
        print("No assignee for: Development (add it to qa/routing.md or ask Dev who takes them)")
    print(f"BugHerd tasks to create: {sum(1 for t in tasks if t['create'])} (column {routing['columns'].get(DEPT)})")
    print(f"RESULT: {result}")
    return cmd_check(out, root)


# --------------------------------------------------------------------------- #
# check (launch report)
# --------------------------------------------------------------------------- #
def cmd_check(rp: Path, root: Path) -> int:
    text = Q.read(rp)
    errs = []
    m = re.match(r"^(.+)-launch-check-(\d{4}-\d{2}-\d{2})\.md$", rp.name)
    slug = m.group(1) if m else ""
    if not m:
        errs.append("file name is not <slug>-launch-check-<YYYY-MM-DD>.md")
    for head in ("Client: ", "Checked: ", "Live: ", "Staging domain: ", "Dev handoff index: ", "Redirects: ", "Compared with: "):
        if not re.search(rf"^{re.escape(head)}", text, re.M):
            errs.append(f"header line {head.strip()} missing")
    for sec in ("## Summary", "## Findings", "## Dev Tick List", "## Not Checked"):
        if f"\n{sec}\n" not in text:
            errs.append(f"section {sec} missing")
    if text.count(Q.STRUCTURED) != 1:
        errs.append("structured data line must appear once")
    for t in TICKS:
        if f"- [ ] {t}" not in text and f"- [x] {t}" not in text:
            errs.append(f"tick list line missing: {t}")
    rows = [r for r in Q.parse_table(text, Q.TABLE_HEADER) if r and r[0] != "none"]
    for r in rows:
        if len(r) != 6:
            errs.append(f"findings row {r[:1]} does not have 6 cells")
            continue
        fid, page, dep, sev, finding, fix = r
        if not re.fullmatch(r"QA-[0-9a-f]{8}", fid):
            errs.append(f"{fid}: # must be a finding id QA-xxxxxxxx")
        if dep != DEPT:
            errs.append(f"{fid}: launch findings are Development's, not {dep!r}")
        if sev not in Q.SEVERITIES:
            errs.append(f"{fid}: severity {sev!r}")
        if not finding or not fix:
            errs.append(f"{fid}: finding and fix must be filled")
    sev = {s: sum(1 for r in rows if len(r) == 6 and r[3] == s) for s in Q.SEVERITIES}
    want = f"Open findings: {sev['CRITICAL']} CRITICAL, {sev['MAJOR']} MAJOR, {sev['MINOR']} MINOR"
    if want not in text:
        errs.append(f"summary does not match the table ({want})")
    result = LIVE_ISSUES if sev["CRITICAL"] or sev["MAJOR"] else LIVE_OK
    last = [l for l in text.strip().split("\n") if l.strip()][-1]
    if last != f"RESULT: {result}":
        errs.append(f"last line must be RESULT: {result}")
    rerun = [r for r in Q.parse_table(text, Q.RERUN_HEADER) if r and r[0] != "none"]
    comp = re.search(r"^Compared with: (.+)$", text, re.M)
    if comp and not comp.group(1).startswith("none") and "\n## Re-run Status\n" not in text:
        errs.append("a re-run must have the Re-run Status table")
    for r in rerun:
        if len(r) != 6 or r[1] not in ("FIXED", "OPEN", "NEW"):
            errs.append(f"re-run row {r[:2]} must be FIXED, OPEN or NEW")
    tp = rp.parent / f"{slug}-launch-bugherd-tasks.json"
    if not tp.exists():
        errs.append(f"{tp.name} missing")
    else:
        try:
            tasks = json.loads(Q.read(tp))
        except json.JSONDecodeError as e:
            tasks = []
            errs.append(f"{tp.name} is not valid JSON: {e}")
        if [t["finding_id"] for t in tasks if t.get("status") != "FIXED"] != [r[0] for r in rows]:
            errs.append("task file does not match the findings table row for row")
        status = {r[0]: r[1] for r in rerun}
        for t in tasks:
            for k in ("finding_id", "status", "create", "bugherd_task_id", "page_url", "department", "column",
                      "assignee", "severity", "bugherd_severity", "title", "description"):
                if k not in t:
                    errs.append(f"task {t.get('finding_id')}: key {k} missing")
            if t.get("department") != DEPT:
                errs.append(f"task {t.get('finding_id')}: department must be Development")
            if Q.INTERNAL_WORDS.search(t.get("description", "") + " " + t.get("title", "")):
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


# --------------------------------------------------------------------------- #
# Reader of a launch check report for later skills (no contract until one reads it)
# --------------------------------------------------------------------------- #
def launch_json(path: str, text: str) -> dict:
    unesc = lambda r: [c.replace("\\|", "|") for c in r]  # noqa: E731
    keys = ["Finding ID", "Status", "Page URL", "Department", "Severity", "Finding"]
    rerun = [dict(zip(keys, unesc(r))) for r in Q.parse_table(text, Q.RERUN_HEADER) if len(r) == 6]
    findings = [dict(zip(["id", "page", "department", "severity", "finding", "fix"], unesc(r)))
                for r in Q.parse_table(text, Q.TABLE_HEADER) if len(r) == 6 and r[0] != "none"]
    res = re.findall(rf"(?m)^RESULT: ({LIVE_OK}|{LIVE_ISSUES})\s*$", text)
    live = re.sub(r"\s*\(saved pages:.*\)$", "", (re.findall(r"(?m)^Live: (.+?)\s*$", text) or [""])[0])
    tasks_file = Path(path).parent / (Path(path).name.split("-launch-check-")[0] + "-launch-bugherd-tasks.json")
    tasks = json.loads(Q.read(tasks_file)) if tasks_file.exists() else []
    keep = ["finding_id", "status", "bugherd_task_id", "severity", "department"]
    return {"Live:": live, "## Findings": findings,
            "## Re-run Status": rerun if "## Re-run Status" in text else None,
            "RESULT:": res[-1] if res else "", "tasks": [{k: t.get(k) for k in keep} for t in tasks]}


if __name__ == "__main__":
    sys.exit("Run this through qa.py (scan --launch, report --launch, created --launch).")
