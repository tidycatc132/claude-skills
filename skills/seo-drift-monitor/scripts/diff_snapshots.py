#!/usr/bin/env python3
"""Diff two SEO snapshots (from snapshot.py) and report what drifted.

Usage
  python3 diff_snapshots.py BASELINE.json CURRENT.json [--csv drift_changes.csv]
                            [--report drift_report.md] [--fail-on critical|high|medium|low|none]

Outputs
  drift_changes.csv  columns `severity,category,subject,field,before,after,note`
                     severity: critical|high|medium|low|info
                     category: ranking|index|status|title|meta_description|canonical|robots|schema|h1|content|page
                     subject:  a page URL, a keyword, or `*` for a site-wide finding
  drift_report.md    verdict line, counts, one table per category, likely causes
  stdout             the verdict and counts

Exit code: 0, or 3 when --fail-on names a severity that occurred (for CI gates).
The rules are documented in ../references/drift-rules.md; keep both in sync.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

SEVERITIES = ["critical", "high", "medium", "low", "info"]
CATEGORIES = ["ranking", "index", "status", "title", "meta_description", "canonical", "robots", "schema", "h1", "content", "page"]
COLUMNS = ["severity", "category", "subject", "field", "before", "after", "note"]
NOT_RANKING = 100          # positions beyond this count as not ranking
MASS_TITLE_MIN = 3         # changed titles needed to call it a site-wide overwrite
MASS_TITLE_SHARE = 0.25    # ...and at least this share of compared pages
TITLE_SEPARATORS = re.compile(r"\s+(?:\||-|–|—|::|:|·|»)\s+")


class Findings:
    def __init__(self) -> None:
        self.rows: list[dict] = []

    def add(self, severity: str, category: str, subject: str, field: str, before, after, note: str) -> None:
        assert severity in SEVERITIES and category in CATEGORIES
        self.rows.append({
            "severity": severity, "category": category, "subject": subject, "field": field,
            "before": fmt(before), "after": fmt(after), "note": note,
        })


def fmt(v) -> str:
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, list):
        return "|".join(str(x) for x in v)
    return str(v)


def rank_pos(entry: dict | None) -> int | None:
    if not entry:
        return None
    p = entry.get("position")
    if p is None or p <= 0 or p > NOT_RANKING:
        return None
    return int(p)


def title_suffix(title: str) -> str:
    parts = TITLE_SEPARATORS.split(title)
    return parts[-1].strip() if len(parts) > 1 else ""


def diff_index(b: dict, c: dict, f: Findings) -> None:
    bi, ci = b.get("indexed_count"), c.get("indexed_count")
    if bi is None or ci is None:
        return
    if ci < bi:
        drop = (bi - ci) / bi if bi else 1.0
        sev = "critical" if drop >= 0.25 else "high" if drop >= 0.10 else "low"
        f.add(sev, "index", "*", "indexed_count", bi, ci, f"indexed pages fell {drop:.0%}")
    elif ci > bi:
        f.add("info", "index", "*", "indexed_count", bi, ci, "indexed pages rose")


def diff_rankings(b: dict, c: dict, f: Findings) -> None:
    br, cr = b.get("rankings", {}), c.get("rankings", {})
    for kw in sorted(set(br) | set(cr)):
        bp, cp = rank_pos(br.get(kw)), rank_pos(cr.get(kw))
        if kw not in br:
            f.add("info", "ranking", kw, "position", None, cp, "keyword is new to tracking")
            continue
        if kw not in cr:
            if bp is not None:
                f.add("medium", "ranking", kw, "position", bp, None, "keyword missing from current rankings file; re-export or confirm it was dropped from tracking")
            continue
        if bp is None and cp is None:
            continue
        if bp is not None and cp is None:
            f.add("high", "ranking", kw, "position", bp, None, f"stopped ranking (was #{bp}, now outside top {NOT_RANKING})")
            continue
        if bp is None:
            f.add("info", "ranking", kw, "position", None, cp, f"started ranking at #{cp}")
            continue
        delta = cp - bp
        if delta > 0:
            left_page_one = bp <= 10 < cp
            sev = "high" if delta >= 10 else "medium" if (delta >= 3 or left_page_one) else "low"
            note = f"dropped {delta} place(s)" + (" and left page one" if left_page_one else "")
            f.add(sev, "ranking", kw, "position", bp, cp, note)
        elif delta < 0:
            f.add("info", "ranking", kw, "position", bp, cp, f"improved {-delta} place(s)")
        bu, cu = (br[kw].get("url") or ""), (cr[kw].get("url") or "")
        if bu and cu and bu.rstrip("/") != cu.rstrip("/"):
            f.add("medium", "ranking", kw, "url", bu, cu, "a different URL ranks now (cannibalisation or redirect)")


def diff_page(url: str, bp: dict, cp: dict, f: Findings) -> bool:
    """Returns True when the page's title was compared and changed (feeds the mass-title check)."""
    bs, cs = bp.get("status"), cp.get("status")
    if cp.get("fetch_error") and not bp.get("fetch_error"):
        f.add("high", "page", url, "fetch_error", "", cp["fetch_error"], "page could not be fetched in the current snapshot")
        return False
    if bs == 200 and cs != 200:
        sev = "critical" if (cs or 0) >= 400 or cs == 0 else "high"
        f.add(sev, "status", url, "status", bs, cs, "page no longer returns 200; field comparison skipped")
        return False
    if bs != 200 and cs == 200:
        f.add("info", "status", url, "status", bs, cs, "page returns 200 again; no baseline fields to compare")
        return False
    if bs != 200 and cs != 200:
        if bs != cs:
            f.add("low", "status", url, "status", bs, cs, "still not 200")
        return False
    if cp.get("redirect_to") and not bp.get("redirect_to"):
        f.add("medium", "status", url, "redirect_to", "", cp["redirect_to"], "URL now redirects")

    # robots
    if not bp.get("noindex") and cp.get("noindex"):
        f.add("critical", "robots", url, "noindex", False, True, f"page became noindex ({cp.get('robots') or cp.get('x_robots_tag') or 'robots directive'}); it will drop out of the index")
    elif bp.get("noindex") and not cp.get("noindex"):
        f.add("info", "robots", url, "noindex", True, False, "page is indexable again; confirm this was intended")
    if not bp.get("nofollow") and cp.get("nofollow"):
        f.add("medium", "robots", url, "nofollow", False, True, "page became nofollow")

    # canonical
    bc, cc = bp.get("canonical", ""), cp.get("canonical", "")
    if bc != cc:
        if bc and not cc:
            f.add("medium", "canonical", url, "canonical", bc, cc, "canonical tag removed")
        elif not bc and cc:
            self_ref = cc.rstrip("/") == url.rstrip("/")
            f.add("low" if self_ref else "medium", "canonical", url, "canonical", bc, cc, "canonical added" + ("" if self_ref else " and points elsewhere"))
        else:
            other_host = urlparse(cc).netloc != urlparse(url).netloc
            f.add("high", "canonical", url, "canonical", bc, cc, "canonical now points to another host (staging or dev leaked?)" if other_host else "canonical changed to a different URL")

    # title
    title_changed = False
    bt, ct = bp.get("title", ""), cp.get("title", "")
    if bt != ct:
        title_changed = True
        if not ct:
            f.add("high", "title", url, "title", bt, ct, "title removed")
        else:
            f.add("medium", "title", url, "title", bt, ct, "title changed")

    # meta description
    bm, cm = bp.get("meta_description", ""), cp.get("meta_description", "")
    if bm != cm:
        if not cm:
            f.add("medium", "meta_description", url, "meta_description", bm, cm, "meta description removed")
        elif not bm:
            f.add("info", "meta_description", url, "meta_description", bm, cm, "meta description added")
        else:
            f.add("low", "meta_description", url, "meta_description", bm, cm, "meta description changed")

    # h1
    bh, ch = bp.get("h1", []), cp.get("h1", [])
    if bh != ch:
        if not ch:
            f.add("medium", "h1", url, "h1", bh, ch, "H1 removed")
        elif len(ch) > 1 and len(bh) <= 1:
            f.add("low", "h1", url, "h1", bh, ch, f"page now has {len(ch)} H1s")
        else:
            f.add("low", "h1", url, "h1", bh, ch, "H1 changed")

    # schema
    bsch, csch = set(bp.get("schema_types", [])), set(cp.get("schema_types", []))
    removed, added = sorted(bsch - csch), sorted(csch - bsch)
    if removed:
        f.add("high", "schema", url, "schema_types", sorted(bsch), sorted(csch), "structured data removed: " + ", ".join(removed))
    if added:
        f.add("info", "schema", url, "schema_types", sorted(bsch), sorted(csch), "structured data added: " + ", ".join(added))

    # content
    bw, cw = bp.get("word_count", 0) or 0, cp.get("word_count", 0) or 0
    if bw >= 100 and cw < bw:
        drop = (bw - cw) / bw
        if drop >= 0.5:
            f.add("medium", "content", url, "word_count", bw, cw, f"visible text shrank {drop:.0%}")
        elif drop >= 0.25:
            f.add("low", "content", url, "word_count", bw, cw, f"visible text shrank {drop:.0%}")
    if bp.get("lang", "") != cp.get("lang", ""):
        f.add("low", "content", url, "lang", bp.get("lang", ""), cp.get("lang", ""), "html lang attribute changed")
    if (bp.get("hreflang_count") or 0) > 0 and (cp.get("hreflang_count") or 0) == 0:
        f.add("medium", "content", url, "hreflang_count", bp.get("hreflang_count"), 0, "hreflang alternates removed")
    return title_changed


def diff_pages(b: dict, c: dict, f: Findings) -> None:
    bpages, cpages = b.get("pages", {}), c.get("pages", {})
    compared = 0
    changed_titles: list[str] = []
    for url in sorted(set(bpages) | set(cpages)):
        if url not in cpages:
            f.add("high", "page", url, "page", "present", "", "page missing from current snapshot (removed, or not crawled this run)")
            continue
        if url not in bpages:
            f.add("info", "page", url, "page", "", "present", "new page in current snapshot")
            continue
        bp, cp = bpages[url], cpages[url]
        if bp.get("status") == 200 and cp.get("status") == 200 and not cp.get("fetch_error"):
            compared += 1
        if diff_page(url, bp, cp, f):
            changed_titles.append(cpages[url].get("title", ""))
    n = len(changed_titles)
    if n >= MASS_TITLE_MIN and compared and n / compared >= MASS_TITLE_SHARE:
        suffixes = Counter(s for s in (title_suffix(t) for t in changed_titles) if s)
        common, share = (suffixes.most_common(1) or [("", 0)])[0]
        tmpl = f"; {share} now end in '{common}' (a CMS or SEO-plugin title template)" if share >= MASS_TITLE_MIN else ""
        f.add("critical", "title", "*", "title", f"{compared} compared pages", f"{n} titles rewritten", f"titles changed on {n} of {compared} pages at once{tmpl}")


def likely_causes(rows: list[dict]) -> list[str]:
    out: list[str] = []
    cats = Counter((r["category"], r["field"]) for r in rows if r["severity"] in ("critical", "high"))
    if any(r["subject"] == "*" and r["category"] == "title" for r in rows):
        out.append("Site-wide title rewrite: an SEO plugin or CMS title template was reset or disabled during the deploy. Restore the plugin settings or per-page title fields.")
    if cats[("robots", "noindex")]:
        out.append("Noindex appeared on live pages: a staging/dev robots setting shipped to production. Check the CMS 'discourage search engines' switch and any X-Robots-Tag header.")
    if any(r["category"] == "canonical" and "another host" in r["note"] for r in rows):
        out.append("Canonicals point at another host: the site URL setting still names the staging domain. Fix the base URL and purge caches.")
    if cats[("status", "status")]:
        out.append("Pages stopped returning 200: URLs changed or routes were dropped. Restore the pages or add 301 redirects to their replacements.")
    if cats[("schema", "schema_types")]:
        out.append("Structured data disappeared: a schema plugin was deactivated or a template lost its JSON-LD block.")
    onpage = any(r["severity"] in ("critical", "high") and r["category"] != "ranking" for r in rows)
    if cats[("ranking", "position")]:
        if onpage:
            out.append("Ranking drops: expect them to follow the on-page problems above within days; recheck rankings a week after fixing.")
        else:
            out.append("Ranking drops with no on-page change on this site: cause unclear (algorithm update, competitors, SERP features). Compare against competitors before changing the site.")
    return out


def write_csv(rows: list[dict], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)


def md_cell(v: str, limit: int = 90) -> str:
    v = str(v).replace("|", "\\|").replace("\n", " ")
    return v if len(v) <= limit else v[: limit - 1] + "…"


def write_report(rows: list[dict], b: dict, c: dict, verdict: str, counts: Counter, path: Path) -> None:
    lines = [
        "# SEO drift report",
        "",
        f"Site: {c.get('site') or b.get('site') or 'unknown'}  ",
        f"Baseline: {b.get('captured_at', '?')} ({len(b.get('pages', {}))} pages, {len(b.get('rankings', {}))} keywords)  ",
        f"Current: {c.get('captured_at', '?')} ({len(c.get('pages', {}))} pages, {len(c.get('rankings', {}))} keywords)",
        "",
        f"**VERDICT: {verdict}**",
        "",
        "| severity | count |", "|---|---|",
    ]
    lines += [f"| {s} | {counts.get(s, 0)} |" for s in SEVERITIES]
    causes = likely_causes(rows)
    if causes:
        lines += ["", "## Likely causes", ""] + [f"- {x}" for x in causes]
    for cat in CATEGORIES:
        cat_rows = [r for r in rows if r["category"] == cat]
        if not cat_rows:
            continue
        lines += ["", f"## {cat.replace('_', ' ')} ({len(cat_rows)})", "", "| severity | subject | field | before | after | note |", "|---|---|---|---|---|---|"]
        lines += [f"| {r['severity']} | {md_cell(r['subject'])} | {r['field']} | {md_cell(r['before'])} | {md_cell(r['after'])} | {md_cell(r['note'], 160)} |" for r in cat_rows]
    if not rows:
        lines += ["", "No differences between the two snapshots."]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def load(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        sys.exit(f"error: cannot read snapshot {path}: {e}")
    if not isinstance(data, dict) or "pages" not in data:
        sys.exit(f"error: {path} is not a snapshot produced by snapshot.py (no 'pages' key)")
    return data


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("baseline", type=Path)
    ap.add_argument("current", type=Path)
    ap.add_argument("--csv", type=Path, default=Path("drift_changes.csv"))
    ap.add_argument("--report", type=Path, default=Path("drift_report.md"))
    ap.add_argument("--fail-on", choices=SEVERITIES[:4] + ["none"], default="none")
    args = ap.parse_args()

    b, c = load(args.baseline), load(args.current)
    f = Findings()
    diff_index(b, c, f)
    diff_pages(b, c, f)
    diff_rankings(b, c, f)
    order = {s: i for i, s in enumerate(SEVERITIES)}
    corder = {c_: i for i, c_ in enumerate(CATEGORIES)}
    rows = sorted(f.rows, key=lambda r: (order[r["severity"]], corder[r["category"]], r["subject"]))
    counts = Counter(r["severity"] for r in rows)
    if counts["critical"] or counts["high"]:
        verdict = f"REGRESSION DETECTED ({counts['critical']} critical, {counts['high']} high)"
    elif counts["medium"] or counts["low"]:
        verdict = f"MINOR DRIFT ({counts['medium']} medium, {counts['low']} low)"
    else:
        verdict = "NO REGRESSION"
    for p in (args.csv, args.report):
        p.parent.mkdir(parents=True, exist_ok=True)
    write_csv(rows, args.csv)
    write_report(rows, b, c, verdict, counts, args.report)
    print(f"VERDICT: {verdict}")
    print("  " + ", ".join(f"{s}={counts.get(s, 0)}" for s in SEVERITIES))
    print(f"  wrote {args.csv} ({len(rows)} rows) and {args.report}")
    if args.fail_on != "none":
        bad = SEVERITIES[: SEVERITIES.index(args.fail_on) + 1]
        if any(counts.get(s) for s in bad):
            return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
