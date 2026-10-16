#!/usr/bin/env python3
"""Check a new-build-kickoff output folder, or answer two helper questions.

Usage:
  python3 check_kickoff.py --slug "Client Name"            print the client slug
  python3 check_kickoff.py --paid-media sow.md             print yes or no
  python3 check_kickoff.py kickoff/<slug> --client "Client Name" --sow sow.md [--no-website]

The full check prints one `| Check | Result | Detail |` table and a final line `RESULT: PASS` or
`RESULT: FAIL`. Exit code 0 on PASS, 1 on FAIL. Standard library only.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SEQUENCE = HERE.parent / "references" / "week-1-sequence.md"

CONTEXT_HEADINGS = ["Snapshot", "Business Overview", "Services", "Customers and Service Area",
                    "Goals and Conversion", "Differentiators and Proof", "Competitors", "Website Today",
                    "Scope Summary", "Open Items", "Sources"]
UNTAGGED_SECTIONS = {"Open Items", "Sources"}
TAGS = {"transcript", "site", "sow", "notes", "user", "maps"}
COLUMNS = ["url", "title", "page_type", "status", "source"]
PAGE_TYPES = {"home", "about", "service", "location", "contact", "blog", "post", "legal", "other"}
INV_SOURCES = {"sitemap", "crawl", "saved", "user"}
STATUSES = re.compile(r"^(covered|asked Q[1-5]|call|n/a)$")
PAID = re.compile(r"google ads|ppc|pay[- ]per[- ]click|paid (search|media|social)|meta ads|facebook ads|"
                  r"microsoft ads|bing ads|search campaigns?|ad spend|paid advertising|advertising management", re.I)
EXCLUDED_LABEL = re.compile(r"^(not included|exclusions?|excluded|out of scope)\b[^:\n]*:?", re.I)
INTAKE = re.compile(r"(?<!web )\b(address|phone number|business hours|opening hours|hours of operation|login|password|"
                    r"access to|logo|fonts?|colou?r palette|brand colou?rs|photos?|video|testimonials?|reviews?|"
                    r"team members?|bios?|certifications?|awards?|licen[cs]es?|memberships?|disclaimers?|"
                    r"legal language|compliance language|websites? you like|sites you like)\b", re.I)
FORBIDDEN_FILES = ("brand-brief", "review-baseline")


def slugify(name: str) -> str:
    s = re.sub(r"&", " and ", name.lower())
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def included_part(sow: str) -> str:
    """SOW text minus exclusions: sections headed or labelled "Not included" (and the like),
    and single lines that start with such a label."""
    keep, excluded = [], False
    for line in sow.splitlines():
        s = line.strip()
        label = re.sub(r"^[#*_\s-]+", "", s)
        if EXCLUDED_LABEL.match(label):
            excluded = not re.sub(r"[*_:\s]", "", EXCLUDED_LABEL.sub("", label, count=1))
            continue
        if s.startswith("#") or (excluded and not s):
            excluded = excluded and not s.startswith("#")
            if s.startswith("#"):
                keep.append(line)
            continue
        if not excluded:
            keep.append(line)
    return "\n".join(keep)


def has_paid_media(sow: str) -> bool:
    return bool(PAID.search(included_part(sow)))


def squash(s: str) -> str:
    return re.sub(r"[\s*_`]+", " ", s).strip().lower()


def sections(text: str) -> dict[str, list[str]]:
    out, cur = {}, None
    for line in text.splitlines():
        m = re.match(r"^##\s+(.*?)\s*$", line)
        if m:
            cur = m.group(1)
            out[cur] = []
        elif cur is not None:
            out[cur].append(line)
    return out


def check(folder: Path, client: str, sow_path: Path, no_website: bool) -> list[tuple[str, bool, str]]:
    res: list[tuple[str, bool, str]] = []
    add = lambda name, ok, detail="": res.append((name, ok, detail))
    slug = slugify(client)
    sow = sow_path.read_text(encoding="utf-8", errors="replace")
    paid = has_paid_media(sow)

    add("folder name is the slug", folder.name == slug, f"expected {slug}, got {folder.name}")
    names = ["context.md", "url-inventory.csv", "gap-questions.md", "project-instructions.md", "setup-checklist.md"]
    missing = [n for n in names if not (folder / f"{slug}-{n}").exists()]
    add("required files present", not missing, ", ".join(missing))
    pm = (folder / f"{slug}-paid-media-brief.md").exists()
    add("paid media brief matches the SOW", pm == paid,
        f"SOW includes paid media: {'yes' if paid else 'no'}; brief present: {'yes' if pm else 'no'}")
    extra = [p.name for p in folder.iterdir() if any(f in p.name for f in FORBIDDEN_FILES)] if folder.exists() else []
    add("no brand brief or review baseline", not extra, ", ".join(extra))
    stray = [p.name for p in folder.iterdir() if p.is_file() and not p.name.startswith(slug + "-")] if folder.exists() else []
    add("every file starts with the slug", not stray, ", ".join(stray))
    for p in sorted(folder.glob("*.md")) if folder.exists() else []:
        first = p.read_text(encoding="utf-8").splitlines()[:1]
        add(f"{p.name} first line", first == [f"Client: {client}"], f"got {first[0] if first else 'empty'!r}")

    ctx_p = folder / f"{slug}-context.md"
    if ctx_p.exists():
        ctx = ctx_p.read_text(encoding="utf-8")
        heads = re.findall(r"^##\s+(.*?)\s*$", ctx, re.M)
        add("context headings in order", heads == CONTEXT_HEADINGS, f"got {heads}")
        sec = sections(ctx)
        untagged = []
        for name, lines in sec.items():
            if name in UNTAGGED_SECTIONS:
                continue
            for ln in lines:
                if not ln.startswith("- ") or ln.startswith("- GAP:"):
                    continue
                m = re.search(r"\[([a-z ,]+)\]\s*$", ln)
                if not m or not {t.strip() for t in m.group(1).split(",")} <= TAGS:
                    untagged.append(ln[:60])
        add("every context fact has a source tag", not untagged, "; ".join(untagged[:4]))
        scope = "\n".join(sec.get("Scope Summary", []))
        m = re.search(r"^SOW pages: (\d+|unknown)(?:\s*\[sow\])?\s*$", scope, re.M)
        ok = bool(m) and (m.group(1) == "unknown" or re.search(rf"\b{m.group(1)}\b[^\n]*page|page[^\n]*\b{m.group(1)}\b", sow, re.I))
        add("SOW page count stated and found in the SOW", bool(ok), m.group(0) if m else "no `SOW pages:` line")
        add("included services line", bool(re.search(r"^Included services: \S", scope, re.M)))
        quotes = [re.sub(r"\s*\[sow\]\s*$", "", q[1:].strip()) for q in scope.splitlines() if q.startswith(">")]
        found = [q for q in quotes if q and squash(q) in squash(sow)]
        add("SOW quote is word for word", bool(found), "no `>` line matches the SOW text" if not found else "")

    inv_p = folder / f"{slug}-url-inventory.csv"
    if inv_p.exists():
        rows = list(csv.reader(inv_p.open(encoding="utf-8")))
        add("inventory header", bool(rows) and rows[0] == COLUMNS, f"got {rows[0] if rows else 'empty'}")
        data = rows[1:]
        bad = [r for r in data if len(r) != 5 or r[2] not in PAGE_TYPES or r[4] not in INV_SOURCES]
        add("inventory values", not bad, f"{len(bad)} bad rows" if bad else "")
        if no_website:
            add("no website means header only", not data, f"{len(data)} rows")
        else:
            add("inventory has rows", bool(data), "no URLs listed")

    gq_p = folder / f"{slug}-gap-questions.md"
    if gq_p.exists():
        sec = sections(gq_p.read_text(encoding="utf-8"))
        qlines = sec.get("Questions", [])
        qs = [(i, ln) for i, ln in enumerate(qlines) if re.match(r"^\d+\.\s", ln)]
        nums = [int(ln.split(".")[0]) for _, ln in qs]
        add("3 to 5 questions numbered 1..n", 3 <= len(qs) <= 5 and nums == list(range(1, len(qs) + 1)), f"numbers {nums}")
        noans = [n for (i, ln), n in zip(qs, nums) if i + 1 >= len(qlines) or qlines[i + 1].strip() != "Answer:"]
        add("each question followed by a blank Answer: line", not noans, f"questions {noans}")
        hits = [f"Q{n}: {INTAKE.search(ln).group(0)}" for (_, ln), n in zip(qs, nums) if INTAKE.search(ln)]
        add("no question about what the intake form collects", not hits, "; ".join(hits))
        table = [ln for ln in sec.get("Checklist Coverage", []) if re.match(r"^\|\s*R\d+\s*\|", ln)]
        ids = [re.match(r"^\|\s*(R\d+)", ln).group(1) for ln in table]
        add("coverage rows R1 to R10", ids == [f"R{i}" for i in range(1, 11)], f"got {ids}")
        stats = [ln.split("|")[3].strip() for ln in table if ln.count("|") >= 5]
        badst = [s for s in stats if not STATUSES.match(s)]
        add("coverage statuses valid", not badst and len(stats) == len(table), ", ".join(badst))
        asked = sorted(int(s[-1]) for s in stats if s.startswith("asked"))
        add("every question mapped once in coverage", asked == nums, f"asked {asked}, questions {nums}")

    pi_p = folder / f"{slug}-project-instructions.md"
    if pi_p.exists():
        pi = pi_p.read_text(encoding="utf-8")
        n = len(pi.splitlines())
        add("project instructions at most 80 lines", n <= 80, f"{n} lines")
        heads = re.findall(r"^##\s+(.*?)\s*$", pi, re.M)
        add("project instructions sections", heads == ["Client", "Project Files", "Working Rules"], f"got {heads}")

    sc_p = folder / f"{slug}-setup-checklist.md"
    if sc_p.exists():
        sc = sc_p.read_text(encoding="utf-8").lower()
        steps = [re.sub(r"\s*\(.*$", "", m) for m in re.findall(r"^\d+\.\s+(.*)$", SEQUENCE.read_text(encoding="utf-8"), re.M)]
        pos, out_of_order = 0, []
        for s in steps:
            i = sc.find(s.lower(), pos)
            if i < 0:
                out_of_order.append(s)
            else:
                pos = i
        add("checklist has the Week 1 steps in order", not out_of_order, "; ".join(out_of_order[:3]))
        if paid:
            add("checklist sends the paid media brief", "paid media brief" in sc)
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", nargs="?")
    ap.add_argument("--client")
    ap.add_argument("--sow")
    ap.add_argument("--no-website", action="store_true")
    ap.add_argument("--slug")
    ap.add_argument("--paid-media")
    a = ap.parse_args()
    if a.slug:
        print(slugify(a.slug))
        return 0
    if a.paid_media:
        print("yes" if has_paid_media(Path(a.paid_media).read_text(encoding="utf-8", errors="replace")) else "no")
        return 0
    if not (a.folder and a.client and a.sow):
        ap.error("folder, --client and --sow are required for a check")
    res = check(Path(a.folder), a.client, Path(a.sow), a.no_website)
    print("| Check | Result | Detail |\n|---|---|---|")
    for name, ok, detail in res:
        print(f"| {name} | {'PASS' if ok else 'FAIL'} | {detail if not ok else ''} |")
    passed = all(ok for _, ok, _ in res)
    print(f"RESULT: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
