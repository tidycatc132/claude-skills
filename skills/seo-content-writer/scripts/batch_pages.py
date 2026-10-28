#!/usr/bin/env python3
"""Batch mode for seo-content-writer: which briefs still need a page, and the end-of-run table.

Usage:
  python3 batch_pages.py plan BRIEFS_DIR [--content content]
  python3 batch_pages.py summary BRIEFS_DIR [--content content] [--out content/batch-summary.md]

plan     lists every brief in BRIEFS_DIR (older versions named `<id>.v<N>.md` are skipped) with the
         page folder it writes to and the action: `write` when `<content>/<url-slug>/article.md`
         does not exist yet, `skip (exists)` when it does. Exit 1 when two briefs map to one folder.
summary  prints and writes the table `| Page | Brief | VERDICT | Open flags |`, one row per brief,
         read from each page's `qa/<url-slug>/qa_report.md` (`NOT WRITTEN` when the page is missing, `NO QA`
         when the page has no report). Below the table it names any page whose brief lists open
         client inputs but whose report is `READY` (a client input was filled without a source).
         Exit 1 when a row is `NOT WRITTEN`, `NO QA` or `FIX`, or a page needs that confirmation.

The url-slug is the last segment of the brief's `page_url:` (or `URL:`) line, `home` for `/`,
else the primary keyword hyphenated, else the brief's file name. Standard library only.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

OLD_VERSION = re.compile(r"\.v\d+\.md$")
SLOT = re.compile(r"\[CLIENT INPUT NEEDED #\d+:[^\]]*\]")


def field(text: str, *names: str) -> str:
    for name in names:
        m = re.search(rf"(?im)^\W*{name}\W*\s*:\s*\**\s*(.+?)\s*\**\s*$", text)
        if m:
            return m.group(1).strip().strip("\"'")
    return ""


def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def page_slug(brief: Path, text: str) -> str:
    url = field(text, "page_url", "url")
    if url.startswith("/") or url.startswith("http"):
        path = re.sub(r"^https?://[^/]+", "", url).split("?")[0].strip("/")
        return path.split("/")[-1] if path else "home"
    if re.search(r"(?im)^\W*(?:page[ _]type|format)\W*\s*:\s*\**\s*home\s?page\b", text):
        return "home"
    kw = field(text, "primary_keyword", "primary keyword", "target keyword", "keyword")
    return slugify(kw) if kw else slugify(brief.stem)


def page_type(text: str) -> str:
    fmt = field(text, "format", "page type", "page_type").lower()
    m = re.match(r"(home\s?page|about|contact|location)", fmt)
    if m:
        return "homepage" if m.group(1).startswith("home") else m.group(1)
    return fmt or "article"


def briefs(folder: Path) -> list[tuple[Path, str, str, str]]:
    out = []
    for p in sorted(folder.glob("*.md")):
        if OLD_VERSION.search(p.name):
            continue
        text = p.read_text(encoding="utf-8")
        out.append((p, text, page_slug(p, text), page_type(text)))
    return out


def open_inputs(text: str) -> int:
    n = field(text, "client_inputs_open")
    return int(n) if n.isdigit() else len(set(SLOT.findall(text)))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["plan", "summary"])
    ap.add_argument("briefs_dir")
    ap.add_argument("--content", default="content", help="folder that holds content/<url-slug>/ (default: content)")
    ap.add_argument("--out", help="summary file (default: <content>/batch-summary.md)")
    a = ap.parse_args()

    folder, content = Path(a.briefs_dir), Path(a.content)
    if not folder.is_dir():
        print(f"briefs folder not found: {folder}", file=sys.stderr)
        return 2
    rows = briefs(folder)
    if not rows:
        print(f"no briefs (*.md) in {folder}", file=sys.stderr)
        return 2

    if a.mode == "plan":
        seen: dict[str, str] = {}
        clash = []
        out = ["| # | Brief | Page | Page type | Open client inputs | Action |", "| --- | --- | --- | --- | --- | --- |"]
        n_write = 0
        for i, (p, text, slug, ptype) in enumerate(rows, 1):
            if slug in seen:
                clash.append(f"{p.name} and {seen[slug]} both write content/{slug}/")
            seen[slug] = p.name
            exists = (content / slug / "article.md").is_file()
            n_write += not exists
            out.append(f"| {i} | {p.name} | {content.as_posix()}/{slug}/ | {ptype} | {open_inputs(text)} | "
                       f"{'skip (exists)' if exists else 'write'} |")
        print("\n".join(out))
        print(f"\n{n_write} to write, {len(rows) - n_write} already written.")
        for c in clash:
            print(f"CLASH: {c}; give each brief its own page_url before writing.")
        return 1 if clash else 0

    out = ["| Page | Brief | VERDICT | Open flags |", "| --- | --- | --- | --- |"]
    bad, confirm = 0, []
    for p, text, slug, _ in rows:
        page = content / slug
        qa = (content.parent / "qa" / slug if content.name == "content" else page) / "qa_report.md"  # where check_draft.py writes it
        if not qa.is_file() and (page / "qa_report.md").is_file():
            qa = page / "qa_report.md"  # a page written before the report moved out of the page folder
        if not (page / "article.md").is_file():
            verdict, flags = "NOT WRITTEN", "-"
        elif not qa.is_file():
            verdict, flags = "NO QA", "-"
        else:
            report = qa.read_text(encoding="utf-8")
            vm = re.search(r"(?m)^VERDICT:\s*(\w+)", report)
            fm = re.search(r"Open flags:\s*(\d+)", report)
            verdict, flags = (vm.group(1) if vm else "NO QA"), (fm.group(1) if fm else "-")
            if verdict == "READY" and open_inputs(text):
                confirm.append(f"{page.as_posix()}/ is READY but its brief lists {open_inputs(text)} open client "
                               "input(s): confirm each was filled from a client file, or put the flag back.")
        bad += verdict in ("NOT WRITTEN", "NO QA", "FIX")
        out.append(f"| {page.as_posix()}/ | {p.name} | {verdict} | {flags} |")
    text = "\n".join(out) + "\n" + "".join(f"\nCONFIRM: {c}" for c in confirm) + ("\n" if confirm else "")
    print(text)
    dest = Path(a.out) if a.out else content / "batch-summary.md"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8")
    print(f"wrote {dest}")
    return 1 if bad or confirm else 0


if __name__ == "__main__":
    sys.exit(main())
