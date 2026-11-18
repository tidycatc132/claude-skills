#!/usr/bin/env python3
"""Build the static grey-box homepage wireframe from the edited page and the design brief.

Usage:
  make_wireframe.py <article.md> <brief.md> <out.html>

One <section data-section="..."> per article section, in page order, showing the page's own heading,
the brief's purpose and layout idea for that section, image placeholders where the layout idea asks
for a photo or image, and the section's open flags. Inline CSS only, no scripts, images, fonts or links
to other files, so HTML-to-Figma imports it as plain frames. Writes no copy of its own.
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hdb  # noqa: E402

CSS = """
*{box-sizing:border-box}body{margin:0;background:#f4f4f4;color:#222;font:16px/1.45 Arial,Helvetica,sans-serif}
header.wf{padding:16px 32px;background:#222;color:#fff;font-size:14px}
section{max-width:1200px;margin:24px auto;padding:32px;background:#fff;border:2px dashed #999}
.tag{display:inline-block;margin-bottom:12px;padding:2px 8px;background:#ddd;font-size:12px;letter-spacing:.05em;text-transform:uppercase}
h1{margin:0 0 12px;font-size:40px}h2{margin:0 0 12px;font-size:28px}
.note{margin:8px 0;color:#555;font-size:14px}
.img{display:flex;align-items:center;justify-content:center;height:280px;margin:16px 0;background:#ccc;color:#555;font-size:14px}
.flag{margin:6px 0;padding:6px 10px;background:#fff4c2;border-left:4px solid #e0b000;font-size:13px}
"""
IMAGE_WORDS = re.compile(r"(?i)\b(photo|photos|photograph|image|images|picture|video|portrait|headshot)\b")


def main() -> int:
    if len(sys.argv) != 4:
        print(__doc__, file=sys.stderr)
        return 2
    article, brief, out = sys.argv[1:]
    secs, _ = hdb.sections(hdb.read(article))
    btext = hdb.read(brief)
    client = re.match(r"^Client: (.+?) ·", btext)
    rows = hdb.table_rows(hdb.md_sections(btext).get("Section Map", ""))[1:]
    by_name = {r[1]: r for r in rows if len(r) == 5}
    e = html.escape
    parts = [f"<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
             f"<title>{e(client.group(1) if client else 'Homepage')} homepage wireframe</title>\n"
             f"<style>{CSS}</style>\n</head>\n<body>\n"
             f"<header class=\"wf\">{e(client.group(1) if client else 'Homepage')} homepage wireframe, "
             f"grey boxes only; copy comes from the edited homepage</header>"]
    for i, s in enumerate(secs, 1):
        r = by_name.get(s["name"])
        tag = "h1" if i == 1 else "h2"
        parts.append(f"<section data-section=\"{e(s['name'])}\">")
        parts.append(f"<div class=\"tag\">{i}. {e(s['name'])}</div>")
        if s["heading"]:
            parts.append(f"<{tag}>{e(s['heading'])}</{tag}>")
        if r:
            parts.append(f"<p class=\"note\"><b>Purpose:</b> {e(r[2])}</p>")
            parts.append(f"<p class=\"note\"><b>Layout:</b> {e(r[3])}</p>")
            if IMAGE_WORDS.search(r[3]):
                parts.append("<div class=\"img\">Image placeholder (see the brief's Imagery section)</div>")
        for f in s["flags"]:
            parts.append(f"<div class=\"flag\">Open: {e(f)}</div>")
        parts.append("</section>")
    parts.append("</body>\n</html>\n")
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text("\n".join(parts), encoding="utf-8")
    print(f"wrote {out}: {len(secs)} sections")
    return 0


if __name__ == "__main__":
    sys.exit(main())
