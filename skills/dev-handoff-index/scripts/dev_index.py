#!/usr/bin/env python3
"""Build the dev handoff index for a website build from the files the earlier weeks saved.

Usage (run from the client's working folder):
  dev_index.py run [--slug S] [--date YYYY-MM-DD]
      writes handoff/<slug>/<slug>-dev-handoff-index.md and prints the summary,
      the blocking list and the last line (GO or NO-GO). Exit 0 on GO, 1 on NO-GO, 2 on a usage error.

Readers (each prints JSON; with --validate they check a JSON file of that shape instead):
  dev_index.py sitemap <report.md>        URL map and redirect map of a site-structure-optimizer report
  dev_index.py content <content/url-slug> metadata fields and internal links of one written page
  dev_index.py briefs <briefs.md>         page type of each page file in the page-type design briefs
  dev_index.py feedback <feedback.md>     the pages a client-feedback file holds back
  dev_index.py inventory <inventory.csv>  the old URLs of a new-build-kickoff URL inventory
  dev_index.py devprep <devprep.md>       the asset checklist and RESULT line of the design QA file

Standard library only. The index is regenerated in full on every run; nothing in it is typed by hand.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

STATUSES = ["READY", "WAITING ON CLIENT CHANGES", "NOT WRITTEN", "NO TEMPLATE"]
TYPE_SECTIONS = ["Service Pages", "Location Pages", "About Page", "Contact Page", "Resource Pages"]
TEMPLATE_NAMES = {
    "Homepage": "Homepage",
    "Service Pages": "Service page",
    "Location Pages": "Location page",
    "About Page": "About page",
    "Contact Page": "Contact page",
    "Resource Pages": "Resource page",
}
GROUP_ORDER = ["Homepage"] + TYPE_SECTIONS + ["Pages Without a Template"]
META_FIELDS = ["Meta title", "Meta description", "H1", "URL slug"]
INVENTORY_COLUMNS = ["url", "title", "page_type", "status", "source"]
POST_LAUNCH = re.compile(r"post[- ]?launch|phase 2|after launch", re.I)
LINK = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
DATED = re.compile(r"^(\d{4}-\d{2}-\d{2})-")
SKILL_DIR = Path(__file__).resolve().parent.parent


# ---------- small helpers ----------

def read(p: Path) -> str:
    return p.read_text(encoding="utf-8-sig").replace("\r\n", "\n")


def norm_path(u: str) -> str:
    """Path of a URL or slug, lower case, leading and trailing slash (no trailing slash on file names)."""
    u = (u or "").strip()
    if not u:
        return ""
    path = urlparse(u).path if "://" in u else u.split("?")[0].split("#")[0]
    path = "/" + path.strip("/")
    if path != "/" and not re.search(r"\.[a-z0-9]{2,5}$", path, re.I):
        path += "/"
    return path.lower()


def split_row(line: str) -> list[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    cells = re.split(r"(?<!\\)\|", s)
    return [c.strip().replace("\\|", "|") for c in cells]


def tables(text: str) -> list[tuple[str, list[str], list[list[str]]]]:
    """Every markdown table as (nearest heading above it, header, rows)."""
    out, heading = [], ""
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        ln = lines[i]
        if re.match(r"^#{1,6} ", ln):
            heading = ln.lstrip("#").strip()
        if ln.strip().startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|?\s*:?-{3,}", lines[i + 1]):
            header = split_row(ln)
            rows = []
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(split_row(lines[i]))
                i += 1
            out.append((heading, header, rows))
            continue
        i += 1
    return out


def col(header: list[str], *names: str) -> int:
    low = [h.lower() for h in header]
    for n in names:
        if n.lower() in low:
            return low.index(n.lower())
    return -1


def latest_dated(folder: Path, suffix: str) -> Path | None:
    if not folder.is_dir():
        return None
    files = sorted(p for p in folder.iterdir() if p.is_file() and DATED.match(p.name) and p.name.endswith(suffix))
    return files[-1] if files else None


# ---------- readers ----------

def read_sitemap(report: Path) -> dict:
    url_map, redirects = [], []
    for heading, header, rows in tables(read(report)):
        ip, iu, ipr = col(header, "Page"), col(header, "URL"), col(header, "Priority")
        if not url_map and heading.lower() == "url map" and min(ip, iu, ipr) >= 0:
            ipa = col(header, "Parent")
            for r in rows:
                if len(r) < len(header) or not r[iu]:
                    continue
                url_map.append({"Page": r[ip], "URL": r[iu], "Parent": r[ipa] if ipa >= 0 else "",
                                "Priority": r[ipr]})
            continue
        io, inew = col(header, "Old URL", "Old", "From"), col(header, "New URL", "New", "To", "Target")
        if not redirects and io >= 0 and inew >= 0 and "redirect" in heading.lower():
            inote = col(header, "Note", "Type")
            for r in rows:
                if len(r) < len(header) or not r[io]:
                    continue
                redirects.append({"Old URL": r[io], "New URL": r[inew], "Note": r[inote] if inote >= 0 else ""})
    return {"report": report.as_posix(), "URL map": url_map, "Redirect map": redirects}


def read_metadata(meta: Path) -> dict:
    """The value is everything between the field cell and the last pipe, as seo-content-writer reads it,
    so a meta title like `Roof Repair | Brand` keeps its pipe."""
    fields = {}
    for k, v in re.findall(r"(?m)^\|\s*([^|]+?)\s*\|\s*(.*?)\s*\|\s*$", read(meta)):
        if k in META_FIELDS and k not in fields:
            fields[k] = v
    return fields


def read_content(folder: Path) -> dict:
    art, meta = folder / "article.md", folder / "metadata.md"
    out = {"folder": folder.as_posix(), "article.md": art.is_file(), "metadata.md": meta.is_file()}
    for f in META_FIELDS:
        out[f] = ""
    if meta.is_file():
        out.update(read_metadata(meta))
    links, routes = [], []
    if art.is_file():
        text = read(art)
        for anchor, href in LINK.findall(text):
            if href.startswith("/") and not href.startswith("//"):
                links.append({"target": href, "anchor": anchor})
            elif href.lower().startswith(("tel:", "mailto:")):
                routes.append(f"{href} (anchor: {anchor})")
        if re.search(r"<!--\s*section:\s*Contact Form\s*-->", text, re.I):
            routes.append("contact form (section: Contact Form)")
    out["Internal links"] = links
    out["Conversion routes"] = routes
    return out


def read_briefs(path: Path) -> dict:
    """Map each page file listed under a page-type section's ### Pages to that section."""
    pages, section, sub = {}, "", ""
    for ln in read(path).split("\n"):
        if ln.startswith("## "):
            section, sub = ln[3:].strip(), ""
        elif ln.startswith("### "):
            sub = ln[4:].strip()
        elif section in TYPE_SECTIONS and sub == "Pages":
            m = re.match(r"^\s*-\s+`?(content/[^`\s]+?)/(?:article\.md)?`?\s*$", ln)
            if m:
                pages[m.group(1).split("/", 1)[1]] = section
    head = read(path).split("\n", 1)[0]
    client = re.match(r"^Client:\s*(.+?)(?:\s+·.*)?$", head)
    return {"brief": path.as_posix(), "client": client.group(1).strip() if client else "",
            "## Page Types": sorted(set(pages.values()), key=TYPE_SECTIONS.index), "pages": pages}


def read_feedback(path: Path) -> dict:
    """Pages a feedback file holds: a `page: <url-slug>` Affects or a `pages ...` list in the Impact,
    on a row whose Impact level is not none."""
    held = {}
    rows_out = []
    for heading, header, rows in tables(read(path)):
        if heading != "Feedback Items":
            continue
        ia, ii, inum = col(header, "Affects"), col(header, "Impact"), col(header, "#")
        if ia < 0 or ii < 0:
            continue
        for r in rows:
            if len(r) < len(header):
                continue
            level = r[ii].split(":", 1)[0].strip().lower()
            rows_out.append({"#": r[inum] if inum >= 0 else "", "Affects": r[ia], "Impact": r[ii]})
            if level == "none" or not level:
                continue
            slugs = []
            m = re.match(r"^page:\s*([a-z0-9][a-z0-9-]*)", r[ia].strip(), re.I)
            if m:
                slugs.append(m.group(1).lower())
            m = re.search(r"\bpages\s+([a-z0-9][a-z0-9, -]*)", r[ii], re.I)
            if m:
                slugs += [s.strip().lower() for s in m.group(1).split(",") if s.strip()]
            for s in dict.fromkeys(slugs):
                held.setdefault(s, []).append(r[inum] if inum >= 0 else "?")
    return {"file": path.as_posix(), "## Feedback Items": rows_out, "page: <url-slug>": held}


def read_inventory(path: Path) -> dict:
    with path.open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.reader(fh))
    if not rows or rows[0] != INVENTORY_COLUMNS:
        raise ValueError(f"{path}: header must be {','.join(INVENTORY_COLUMNS)}")
    out = []
    for r in rows[1:]:
        if not any(c.strip() for c in r):
            continue
        if len(r) != len(INVENTORY_COLUMNS):
            raise ValueError(f"{path}: row {r} has {len(r)} cells")
        out.append(dict(zip(INVENTORY_COLUMNS, r)))
    return {"file": path.as_posix(), "rows": out}


def read_devprep(path: Path) -> dict:
    lines = read(path).rstrip("\n").split("\n")
    checklist, inside = [], False
    for ln in lines:
        if ln.startswith("## "):
            inside = ln[3:].strip().lower() == "asset checklist"
            continue
        if re.match(r"^RESULT:", ln):
            inside = False
        if inside:
            checklist.append(ln)
    while checklist and not checklist[0].strip():
        checklist.pop(0)
    while checklist and not checklist[-1].strip():
        checklist.pop()
    result = ""
    for ln in reversed(lines):
        m = re.match(r"^RESULT:\s*(PASS|FAIL)\s*$", ln.strip())
        if m:
            result = m.group(1)
            break
    return {"file": path.as_posix(), "## Asset Checklist": checklist, "RESULT:": result}


def week2_result(path: Path) -> str:
    lines = [ln.strip() for ln in read(path).split("\n") if ln.strip()]
    return lines[-1] if lines else ""


# ---------- the index ----------

def find_slug(root: Path, slug: str | None) -> str:
    if slug:
        return slug
    for parent in ("design", "handoff", "kickoff"):
        d = root / parent
        if d.is_dir():
            subs = sorted(p.name for p in d.iterdir() if p.is_dir())
            if len(subs) == 1:
                return subs[0]
            if len(subs) > 1:
                raise SystemExit(f"several clients under {parent}/ ({', '.join(subs)}); pass --slug")
    raise SystemExit("no client folder under design/, handoff/ or kickoff/; pass --slug")


def content_folders(root: Path) -> dict[str, Path]:
    """URL path -> content folder, from metadata.md `URL slug`, else the folder name."""
    by_path, by_name = {}, {}
    cdir = root / "content"
    if not cdir.is_dir():
        return {}
    for d in sorted(p for p in cdir.iterdir() if p.is_dir()):
        by_name[d.name] = d
        meta = d / "metadata.md"
        if meta.is_file():
            u = read_metadata(meta).get("URL slug", "")
            if u:
                by_path.setdefault(norm_path(u), d)
    return {"paths": by_path, "names": by_name}


def match_folder(url: str, folders: dict) -> Path | None:
    p = norm_path(url)
    if p in folders.get("paths", {}):
        return folders["paths"][p]
    last = "home" if p == "/" else p.strip("/").split("/")[-1]
    return folders.get("names", {}).get(last)


def rel(root: Path, p: Path) -> str:
    return p.relative_to(root).as_posix()


def build(root: Path, slug: str, date: str) -> tuple[str, bool, list[str], dict]:
    blocking: list[str] = []
    notes: list[str] = []

    # sources
    report = None
    sdir = root / "seo-reports" / "site-structure-optimizer"
    if sdir.is_dir():
        for p in sorted((p for p in sdir.glob("*.md") if DATED.match(p.name)), reverse=True):
            if read_sitemap(p)["URL map"]:
                report = p
                break
    sitemap = read_sitemap(report) if report else {"URL map": [], "Redirect map": []}
    if not report:
        blocking.append("Sitemap report: no saved architecture report with a URL map under "
                        "seo-reports/site-structure-optimizer/ (SEO, site-structure-optimizer)")

    w2 = root / "handoff" / slug / f"{slug}-week-2-handoff.md"
    w2_line = week2_result(w2) if w2.is_file() else ""
    if not w2.is_file():
        blocking.append(f"Week 2 handoff: {rel(root, w2)} missing (PM, week-2-handoff-check)")
    elif w2_line != "GO":
        blocking.append(f"Week 2 handoff: {rel(root, w2)} ends {w2_line or 'with no result'}, not GO "
                        "(PM, week-2-handoff-check)")

    bpath = root / "design" / slug / f"{slug}-page-type-design-briefs.md"
    briefs = read_briefs(bpath) if bpath.is_file() else {"pages": {}, "client": ""}
    if not bpath.is_file():
        blocking.append(f"Page-type design briefs: {rel(root, bpath)} missing (Design, page-type-design-briefs)")
    hpath = root / "design" / slug / f"{slug}-homepage-design-brief.md"

    dpath = root / "design" / slug / f"{slug}-design-qa-devprep.md"
    devprep = read_devprep(dpath) if dpath.is_file() else None
    if devprep and devprep["RESULT:"] != "PASS":
        blocking.append(f"Design QA and dev prep: {rel(root, dpath)} ends "
                        f"{'RESULT: ' + devprep['RESULT:'] if devprep['RESULT:'] else 'with no RESULT line'} "
                        "(Design, design-qa-dev-prep)")

    fpath = latest_dated(root / "feedback" / slug, "-feedback.md")
    feedback = read_feedback(fpath) if fpath else {"page: <url-slug>": {}}
    held = feedback["page: <url-slug>"]

    ipath = root / "kickoff" / slug / f"{slug}-url-inventory.csv"
    inventory = None
    if ipath.is_file():
        try:
            inventory = read_inventory(ipath)["rows"]
        except ValueError as e:
            blocking.append(f"URL inventory: {e} (AM, new-build-kickoff)")
    else:
        blocking.append(f"URL inventory: {rel(root, ipath)} missing (AM, new-build-kickoff)")

    client = briefs.get("client") or slug
    folders = content_folders(root)
    sitemap_paths = {norm_path(r["URL"]) for r in sitemap["URL map"]}
    redirect_by_old = {norm_path(r["Old URL"]): r for r in sitemap["Redirect map"]}

    # pages
    pages = []
    for row in sitemap["URL map"]:
        folder = match_folder(row["URL"], folders)
        info = read_content(folder) if folder else None
        priority = "Post-Launch" if POST_LAUNCH.search(row["Priority"]) else "Build"
        written = bool(info and info["article.md"] and info["metadata.md"]
                       and info["Meta title"] and info["Meta description"])
        if norm_path(row["URL"]) == "/":
            group = "Homepage" if hpath.is_file() else "Pages Without a Template"
        else:
            group = briefs["pages"].get(folder.name) if folder else None
            group = group or "Pages Without a Template"
        template = (f"{TEMPLATE_NAMES[group]} ({rel(root, hpath if group == 'Homepage' else bpath)})"
                    if group in TEMPLATE_NAMES else "none")
        detail = ""
        if not written:
            status = "NOT WRITTEN"
            if info and info["article.md"] and not info["metadata.md"]:
                detail = "article.md has no metadata.md"
            elif info and info["metadata.md"] and not (info["Meta title"] and info["Meta description"]):
                detail = "metadata.md has no Meta title or Meta description"
        elif group == "Pages Without a Template":
            status = "NO TEMPLATE"
        elif folder.name in held and (root / "content" / folder.name / "article.md").stat().st_mtime <= fpath.stat().st_mtime:
            status = "WAITING ON CLIENT CHANGES"
            detail = f"{rel(root, fpath)} row {', '.join('#' + n for n in held[folder.name])}"
        else:
            status = "READY"
        pages.append({"row": row, "folder": folder, "info": info, "priority": priority, "group": group,
                      "template": template, "status": status, "detail": detail})
        if priority == "Build" and status in ("NOT WRITTEN", "NO TEMPLATE"):
            owner = ("Content, seo-content-writer" if status == "NOT WRITTEN"
                     else "Design, page-type-design-briefs")
            blocking.append(f"Page: {row['Page']} ({row['URL']}) is {status} ({owner})")

    counts = {s: sum(1 for p in pages if p["status"] == s) for s in STATUSES}

    # write
    out = [f"Client: {client}", f"Checked: {date}"]
    out.append(f"Sitemap report: {rel(root, report) if report else 'missing'}")
    out.append(f"Week 2 handoff: {rel(root, w2)} ({w2_line or 'missing'})" if w2.is_file()
               else f"Week 2 handoff: {rel(root, w2)} (missing)")
    out.append(f"Page-type design briefs: {rel(root, bpath)}" + ("" if bpath.is_file() else " (missing)"))
    out.append(f"Design QA and dev prep: {rel(root, dpath)} (RESULT: {devprep['RESULT:'] or 'none'})" if devprep
               else "Design QA and dev prep: not run yet (design-qa-dev-prep)")
    out.append(f"Client feedback: {rel(root, fpath)}" if fpath else "Client feedback: none")
    out += ["", f"# Dev Handoff Index: {client}", ""]
    out.append("Pages: " + ", ".join(f"{counts[s]} {s}" for s in STATUSES))
    out += ["", "Every value below is copied from the file named beside it. Re-run the skill after any change; "
            "only statuses move.", ""]

    for g in GROUP_ORDER:
        members = [p for p in pages if p["group"] == g]
        if not members:
            continue
        out += [f"## {g}", ""]
        for p in members:
            r, info = p["row"], p["info"] or {}
            cfile = f"content/{p['folder'].name}/article.md" if p["folder"] and info.get("article.md") else "none"
            out.append(f"### {r['Page']}")
            out.append("")
            out.append(f"- Page: {r['Page']}")
            out.append(f"- URL: {r['URL']}")
            out.append(f"- Content file: {cfile}")
            out.append(f"- Template: {p['template']}")
            out.append(f"- Meta title: {info.get('Meta title') or 'none'}")
            out.append(f"- Meta description: {info.get('Meta description') or 'none'}")
            out.append(f"- H1: {info.get('H1') or 'none'}")
            links = info.get("Internal links") or []
            if links:
                out.append("- Internal links:")
                for ln in links:
                    flag = ""
                    t = norm_path(ln["target"])
                    if t not in sitemap_paths:
                        red = redirect_by_old.get(t)
                        flag = (f" NOT IN SITEMAP, redirects to {red['New URL']}" if red
                                else " NOT IN SITEMAP, no redirect target")
                    out.append(f"  - {ln['target']} (anchor: {ln['anchor']}){flag}")
            else:
                out.append("- Internal links: none")
            out.append(f"- Priority: {p['priority']}")
            out.append(f"- Status: {p['status']}" + (f" ({p['detail']})" if p["detail"] else ""))
            out.append("")

    # global
    out += ["## Global", "", "### Analytics and tracking", ""]
    out += global_lines("analytics")
    routes = [(p["row"]["Page"], rt) for p in pages for rt in ((p["info"] or {}).get("Conversion routes") or [])]
    if routes:
        out += ["", "Conversion points in the written pages (track each as an event):", ""]
        out += [f"- {pg}: {rt}" for pg, rt in routes]
    out += ["", "### sitemap.xml", ""]
    out += global_lines("sitemap")
    out += ["", "URLs to list at launch (Build priority):", ""]
    out += [f"- {p['row']['URL']}" for p in pages if p["priority"] == "Build"] or ["- none"]
    post = [p for p in pages if p["priority"] == "Post-Launch"]
    if post:
        out += ["", "Add when published (Post-Launch):", ""] + [f"- {p['row']['URL']}" for p in post]
    out += ["", "### robots.txt", ""]
    out += global_lines("robots")
    out += ["", "### Structured data", "", "Structured data: not in the current process", ""]
    out += ["### Redirects", ""]
    no_target = 0
    if inventory is None:
        out.append("URL inventory missing; redirects cannot be listed.")
    elif not inventory:
        out.append("No existing site")
        if sitemap["Redirect map"]:
            out.append("")
            out.append(f"The sitemap report lists {len(sitemap['Redirect map'])} redirects but the URL inventory "
                       "is empty; SEO to confirm whether an old site exists.")
    else:
        out += ["| Old URL | New URL | Note |", "|---|---|---|"]
        seen = set()
        for row in inventory:
            p = norm_path(row["url"])
            if p in sitemap_paths or p in seen:
                continue
            seen.add(p)
            red = redirect_by_old.get(p)
            if red:
                out.append(f"| {row['url']} | {red['New URL']} | {red['Note'] or '301'} |")
            else:
                no_target += 1
                out.append(f"| {row['url']} | NO TARGET | SEO to decide: not in the sitemap or the redirect map |")
        for p, red in redirect_by_old.items():
            if p not in seen and p not in sitemap_paths:
                out.append(f"| {red['Old URL']} | {red['New URL']} | {red['Note'] or '301'}; not in the URL inventory |")
        if not seen and not any(p not in sitemap_paths for p in redirect_by_old):
            out.append("| none | | every old URL keeps its address |")
    out.append("")

    if devprep:
        out += ["## Design Assets", "", f"Copied from {rel(root, dpath)}.", ""]
        out += devprep["## Asset Checklist"] or ["No asset checklist in the file."]
        out.append("")

    out += ["## Blocking", ""]
    out += [f"- {b}" for b in blocking] or ["- none"]
    if no_target:
        out += ["", f"Not blocking dev: {no_target} old URL(s) with NO TARGET; SEO picks a 301 target before launch."]
    waiting = [p["row"]["Page"] for p in pages if p["status"] == "WAITING ON CLIENT CHANGES"]
    if waiting:
        out += ([] if no_target else [""]) + [f"Not blocking dev: waiting on client changes: {', '.join(waiting)}; build them after Content "
                "rewrites the page and this index is re-run."]
    go = not blocking
    out += ["", "GO" if go else "NO-GO", ""]
    summary = {"counts": counts, "blocking": blocking, "go": go, "waiting": waiting, "no_target": no_target,
               "ready": [p["row"]["Page"] for p in pages if p["status"] == "READY" and p["priority"] == "Build"]}
    return "\n".join(out), go, blocking, summary


_GLOBAL_CACHE: dict[str, list[str]] = {}


def global_lines(key: str) -> list[str]:
    """Fixed requirement lines from assets/global-requirements.md, under `## <key>`."""
    if not _GLOBAL_CACHE:
        cur = None
        for ln in read(SKILL_DIR / "assets" / "global-requirements.md").split("\n"):
            if ln.startswith("## "):
                cur = ln[3:].strip().lower()
                _GLOBAL_CACHE[cur] = []
            elif cur and ln.strip():
                _GLOBAL_CACHE[cur].append(ln)
    return list(_GLOBAL_CACHE.get(key, []))


def cmd_run(a) -> int:
    root = Path.cwd()
    slug = find_slug(root, a.slug)
    date = a.date or dt.date.today().isoformat()
    text, go, blocking, s = build(root, slug, date)
    dest = root / "handoff" / slug / f"{slug}-dev-handoff-index.md"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8")
    print(f"Wrote {dest.relative_to(root).as_posix()}")
    print("Pages: " + ", ".join(f"{s['counts'][k]} {k}" for k in STATUSES))
    print("Ready to build now: " + (", ".join(s["ready"]) or "none"))
    if s["waiting"]:
        print("Waiting on client changes: " + ", ".join(s["waiting"]))
    if s["no_target"]:
        print(f"Old URLs with NO TARGET: {s['no_target']}")
    print("Blocking:" + ("" if blocking else " none"))
    for b in blocking:
        print(f"- {b}")
    print("GO" if go else "NO-GO")
    return 0 if go else 1


# ---------- reader commands ----------

READERS = {
    "sitemap": (read_sitemap, ["URL map", "Redirect map"]),
    "content": (read_content, ["Meta title", "Meta description", "H1", "URL slug", "Internal links"]),
    "briefs": (read_briefs, ["## Page Types", "pages"]),
    "feedback": (read_feedback, ["## Feedback Items", "page: <url-slug>"]),
    "inventory": (read_inventory, ["rows"]),
    "devprep": (read_devprep, ["## Asset Checklist", "RESULT:"]),
}


def cmd_read(a) -> int:
    fn, keys = READERS[a.cmd]
    p = Path(a.file)
    if a.validate:
        try:
            data = json.loads(read(p))
        except (OSError, json.JSONDecodeError) as e:
            print(f"FAIL: {e}")
            return 1
        missing = [k for k in keys if k not in data]
        if missing:
            print(f"FAIL: missing keys {missing}")
            return 1
        print("OK")
        return 0
    if a.cmd == "inventory":
        try:
            data = fn(p)
        except (OSError, ValueError) as e:
            print(f"FAIL: {e}")
            return 1
    elif not p.exists():
        print(f"FAIL: {p} does not exist")
        return 1
    else:
        data = fn(p)
    if a.cmd == "sitemap" and not data["URL map"]:
        print(f"FAIL: no URL map table (columns Page, URL, Priority) in {p}")
        return 1
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--slug")
    r.add_argument("--date", help="YYYY-MM-DD for the Checked line (default today)")
    for name in READERS:
        s = sub.add_parser(name)
        s.add_argument("file")
        s.add_argument("--validate", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "run":
        if a.date and not re.match(r"^\d{4}-\d{2}-\d{2}$", a.date):
            ap.error("--date must be YYYY-MM-DD")
        return cmd_run(a)
    return cmd_read(a)


if __name__ == "__main__":
    sys.exit(main())
