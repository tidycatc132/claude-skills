#!/usr/bin/env python3
"""Fill the WISE Digital Audit template from an audit JSON file.

Usage:
    python3 fill_audit.py audit.json OUTPUT.xlsx [--template assets/audit-template.csv]

Writes OUTPUT.xlsx in the template's exact layout (and OUTPUT.csv next to it).
Cells are located by their labels in the template, not by fixed coordinates,
so small template edits do not break the filler. Exits non-zero with a list of
problems if the JSON is incomplete or inconsistent.
"""
import argparse
import csv
import json
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

DIRECTORY_TOTAL = 21

# Left and right result tables: label in the template -> JSON key.
# The result sits two columns to the right of the label.
SEO_ROWS = {
    "Website Platform": "website_platform",
    "URL Structure": "url_structure",
    "Meta Titles": "meta_titles",
    "Meta Descriptions": "meta_descriptions",
    "Headers / H Tags": "headers",
    "Structured Data": "structured_data",
    "Page Word Count": "page_word_count",
    "New Content Monthly": "new_content_monthly",
    "Duplicate Websites": "duplicate_websites",
    "Duplicate Content": "duplicate_content",
    "Backlinks": "backlinks",
    "Internal Link Building": "internal_link_building",
    "External Link Building": "external_link_building",
    "Domain Authority": "domain_authority",
    "Domain Age": "domain_age",
}
UI_ROWS = {
    "SSL Secured": "ssl_secured",
    "ADA Compliant": "ada_compliant",
    "Privacy/Consent Compliance": "privacy_consent",
    "Look & Feel": "look_and_feel",
    "Tone & Voice": "tone_and_voice",
    "Original Content (Photos, Videos, etc)": "original_content",
    "Clear Customer Journey": "clear_customer_journey",
    "Clear Conversion Path (CTAs)": "clear_conversion_path",
    "Effective Conversion Pages": "effective_conversion_pages",
    "Overall Test Results": "cwv_overall",
    "- Desktop Page Optimization": "desktop_optimization",
    "- Desktop Speed (load time in seconds)": "desktop_speed_seconds",
    "- Mobile Page Optimization": "mobile_optimization",
    "- Mobile Speed (4G load time in seconds)": "mobile_speed_seconds",
}
# Header label -> (section, key). The value goes in the cell directly below.
UNDER_HEADER = {
    "# of Core Pages": ("content", "core_pages"),
    "# of Blog Posts": ("content", "blog_posts"),
    "AI-Written Blogs": ("content", "ai_written_blogs"),
    "Google (Gemini)": ("ai_visibility", "gemini"),
    "ChatGPT": ("ai_visibility", "chatgpt"),
    "Google Analytics": ("tracking", "google_analytics"),
    "Google Tag Manager": ("tracking", "google_tag_manager"),
    "# of Business Locations": ("tracking", "business_locations"),
    "Google Ads": ("tracking", "google_ads"),
    "Meta Ads": ("tracking", "meta_ads"),
    "Other Ads": ("tracking", "other_ads"),
}
REVIEW_COLUMNS = {"Google Business Profile": "gbp", "Yelp": "yelp", "Facebook": "facebook"}

RED = PatternFill("solid", fgColor="F8D7DA")
GREEN = PatternFill("solid", fgColor="D4EDDA")
BAD = {"incorrect", "no", "fail"}
GOOD = {"correct", "yes", "pass"}
# For these checks "Yes" is the bad answer.
INVERTED = {"Duplicate Websites", "Duplicate Content", "AI-Written Blogs"}


def norm(text):
    return " ".join(str(text).split()).rstrip(":").strip()


def load_grid(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    width = max(len(r) for r in rows)
    return [r + [""] * (width - len(r)) for r in rows]


def find(grid, label, start_row=0, col=None):
    want = norm(label).lower()
    for r in range(start_row, len(grid)):
        for c, cell in enumerate(grid[r]):
            if (col is None or c == col) and norm(cell).lower() == want:
                return r, c
    return None


def put(grid, r, c, value):
    while c >= len(grid[r]):
        grid[r].append("")
    grid[r][c] = "" if value is None else str(value)


def fill(grid, data, problems):
    def need(section, key):
        sec = data.get(section, {})
        if key not in sec or sec[key] in (None, ""):
            problems.append(f"missing {section}.{key}")
            return ""
        return sec[key]

    # Header: date and company.
    hit = next(((r, c) for r in range(len(grid)) for c, v in enumerate(grid[r])
                if v.strip().upper().startswith("DIGITAL AUDIT")), None)
    if hit:
        put(grid, *hit, f"DIGITAL AUDIT  {need('prospect', 'audit_date')}")
    hit = find(grid, "[Company Name]")
    if hit:
        put(grid, *hit, need("prospect", "company_name"))
    hit = find(grid, "[url]")
    if hit:
        put(grid, *hit, need("prospect", "url"))

    for table, section in ((SEO_ROWS, "seo"), (UI_ROWS, "ui")):
        for label, key in table.items():
            hit = find(grid, label)
            if not hit:
                problems.append(f"template label not found: {label}")
                continue
            put(grid, hit[0], hit[1] + 2, need(section, key))

    for label, (section, key) in UNDER_HEADER.items():
        hit = find(grid, label)
        if not hit:
            problems.append(f"template label not found: {label}")
            continue
        put(grid, hit[0] + 1, hit[1], need(section, key))
    # "Other" appears twice (AI visibility and ads); the AI one is in the Gemini row.
    gem = find(grid, "Google (Gemini)")
    if gem:
        for c in range(gem[1], len(grid[gem[0]])):
            if norm(grid[gem[0]][c]) == "Other":
                put(grid, gem[0] + 1, c, need("ai_visibility", "other"))

    # Reviews: stars row then review-count row.
    for label, key in REVIEW_COLUMNS.items():
        hit = find(grid, label)
        if not hit:
            problems.append(f"template label not found: {label}")
            continue
        rev = data.get("reviews", {}).get(key, {})
        stars, count = rev.get("stars"), rev.get("count")
        if stars is None or count is None:
            problems.append(f"missing reviews.{key}.stars/count")
        if str(stars).lower() == "unknown" or str(count).lower() == "unknown":
            put(grid, hit[0] + 1, hit[1], "Unknown")
            put(grid, hit[0] + 2, hit[1], "Unknown")
            continue
        put(grid, hit[0] + 1, hit[1], f"{stars if stars is not None else 0} - Stars")
        put(grid, hit[0] + 2, hit[1], f"{count if count is not None else 0} - Reviews")

    # Directory listings.
    d = data.get("directories", {})
    inaccurate, not_found = d.get("inaccurate"), d.get("not_found")
    if inaccurate is None or not_found is None:
        problems.append("missing directories.inaccurate/not_found")
        inaccurate, not_found = inaccurate or 0, not_found or 0
    if inaccurate + not_found > DIRECTORY_TOTAL:
        problems.append(f"directories: inaccurate + not_found exceeds {DIRECTORY_TOTAL}")
    rate = round(100 * (inaccurate + not_found) / DIRECTORY_TOTAL)
    for label, value in (("Inaccurate", f"{inaccurate}/{DIRECTORY_TOTAL}"),
                         ("Not Found", f"{not_found}/{DIRECTORY_TOTAL}"),
                         ("Error Rate", f"{rate}%")):
        hit = find(grid, label)
        if hit:
            put(grid, hit[0] + 1, hit[1], value)

    # Keyword groups (5 rows under the header) and total.
    groups = data.get("keyword_groups", [])
    if len(groups) != 5:
        problems.append(f"keyword_groups must have 5 entries, got {len(groups)}")
    hdr = find(grid, "Keyword Groups")
    total = 0
    if hdr:
        for i, g in enumerate(groups[:5]):
            r = hdr[0] + 1 + i
            put(grid, r, hdr[1], g.get("keyword", ""))
            put(grid, r, hdr[1] + 1, g.get("searches_per_month", 0))
            put(grid, r, hdr[1] + 2, g.get("city", ""))
            total += int(g.get("searches_per_month") or 0)
    hit = find(grid, "Total Monthly Searches")
    if hit:
        put(grid, hit[0], hit[1] + 1, total)

    # Observations: prospect-facing only, one per row under the header.
    obs = data.get("observations", [])
    if not 3 <= len(obs) <= 5:
        problems.append(f"observations must have 3-5 entries, got {len(obs)}")
    hdr = find(grid, "Key Observations & Concerns")
    if hdr:
        for i, text in enumerate(obs[:5]):
            put(grid, hdr[0] + 1 + i, hdr[1], text)

    # Rankings breakdown: 25 rows under the "Keywords" header.
    ranks = data.get("rankings", [])
    if len(ranks) != 25:
        problems.append(f"rankings must have 25 entries, got {len(ranks)}")
    hdr = find(grid, "Keywords", start_row=find(grid, "Search Rankings Breakdown")[0]
               if find(grid, "Search Rankings Breakdown") else 0)
    maps_hits = organic_hits = 0
    if hdr:
        maps_col = find(grid, "Top 3 (Maps)", start_row=hdr[0])[1]
        org_col = find(grid, "1st Page (Organic)", start_row=hdr[0])[1]
        for i, row in enumerate(ranks[:25]):
            r = hdr[0] + 1 + i
            put(grid, r, hdr[1], row.get("keyword", ""))
            put(grid, r, hdr[1] + 1, row.get("city", ""))
            m, o = row.get("maps_position"), row.get("organic_position")
            put(grid, r, maps_col, m if m else "-")
            put(grid, r, org_col, o if o else "-")
            maps_hits += 1 if m and int(m) <= 3 else 0
            organic_hits += 1 if o and int(o) <= 10 else 0
    # The template puts each count in the first filled cell below its label.
    for label, value in (("Top 3 Maps Rankings", maps_hits), ("Top 10 Organic Rankings", organic_hits)):
        hit = find(grid, label)
        if hit:
            r, c = hit
            target = next((rr for rr in range(r + 1, min(r + 4, len(grid)))
                           if c < len(grid[rr]) and grid[rr][c].strip()), r + 1)
            put(grid, target, c, value)


def colour(label, value):
    v = norm(value).lower()
    if not v:
        return None
    bad, good = (GOOD, BAD) if label in INVERTED else (BAD, GOOD)
    if v in bad:
        return RED
    if v in good:
        return GREEN
    return None


def save(grid, out_xlsx):
    wb = Workbook()
    ws = wb.active
    ws.title = "WISE Digital Audit"
    bold_labels = {norm(k) for k in list(SEO_ROWS) + list(UI_ROWS) + list(UNDER_HEADER)}
    for r, row in enumerate(grid, start=1):
        for c, value in enumerate(row, start=1):
            cell = ws.cell(row=r, column=c)
            if value != "" and value.lstrip("-").replace(".", "", 1).isdigit():
                cell.value = float(value) if "." in value else int(value)
            else:
                cell.value = value
            cell.alignment = Alignment(wrap_text=True, vertical="top")
            left = norm(row[c - 3]) if c >= 3 else ""
            fill_ = colour(left, value)
            if fill_:
                cell.fill = fill_
            if norm(value) in bold_labels or norm(value).endswith(("Content", "Performance", "Result")):
                cell.font = Font(bold=True)
    for col, width in zip("ABCDEFG", (34, 16, 18, 4, 40, 16, 18)):
        ws.column_dimensions[col].width = width
    Path(out_xlsx).parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_xlsx)
    with open(Path(out_xlsx).with_suffix(".csv"), "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(grid)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("audit_json")
    ap.add_argument("output_xlsx")
    ap.add_argument("--template", default=str(Path(__file__).resolve().parent.parent / "assets" / "audit-template.csv"))
    args = ap.parse_args()
    data = json.loads(Path(args.audit_json).read_text(encoding="utf-8"))
    grid = load_grid(args.template)
    problems = []
    fill(grid, data, problems)
    save(grid, args.output_xlsx)
    if problems:
        print("Saved with problems to fix:\n- " + "\n- ".join(problems), file=sys.stderr)
        sys.exit(1)
    print(f"Saved {args.output_xlsx} and {Path(args.output_xlsx).with_suffix('.csv')}")


if __name__ == "__main__":
    main()
