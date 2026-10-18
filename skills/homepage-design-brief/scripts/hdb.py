"""Shared parsing for the homepage-design-brief scripts (standard library only)."""
from __future__ import annotations

import re
from pathlib import Path

# seo-content-writer's homepage section markers, in page order (FAQ is optional)
KNOWN = ["Hero", "Why Us", "Services Overview", "Proof", "About Snapshot",
         "Service Area", "Process", "FAQ", "Final CTA"]
MARKER = re.compile(r"(?im)^\s*<!--\s*section:\s*([^>]+?)\s*-->\s*$")
HEADING = re.compile(r"(?m)^(#{1,3})\s+(.+?)\s*$")
FLAG = re.compile(r"\[(?:NEEDS INPUT|CLIENT INPUT NEEDED|NEEDS SOURCE)\b[^\]]*\]")
NUMBERED = re.compile(r"\[CLIENT INPUT NEEDED #(\d+)")


def read(path) -> str:
    return Path(path).read_text(encoding="utf-8").replace("\r\n", "\n")


def flags(text: str) -> list[str]:
    """Open flags in order, each once; numbered client-input slots count once per number."""
    out, seen = [], set()
    for m in FLAG.finditer(text):
        f = m.group(0)
        n = NUMBERED.match(f)
        key = ("#" + n.group(1)) if n else f
        if key not in seen:
            seen.add(key)
            out.append(f)
    return out


def sections(md: str) -> tuple[list[dict], str]:
    """Split the homepage into sections. Returns (sections, mode).

    mode "markers": split on the writer's `<!-- section: X -->` comments.
    mode "headings": no markers (an editor removed them); split on the H1 and each H2.
    Each section: name, heading, flags, words, links."""
    marks = list(MARKER.finditer(md))
    parts = []
    if marks:
        mode = "markers"
        for i, m in enumerate(marks):
            end = marks[i + 1].start() if i + 1 < len(marks) else len(md)
            parts.append((m.group(1).strip(), md[m.end():end]))
    else:
        mode = "headings"
        hs = [h for h in HEADING.finditer(md) if len(h.group(1)) <= 2]
        for i, h in enumerate(hs):
            end = hs[i + 1].start() if i + 1 < len(hs) else len(md)
            parts.append((h.group(2).strip(), md[h.start():end]))
    out = []
    for name, body in parts:
        if mode == "markers" and name.lower() == "sources":
            continue
        # the writer's Sources list is not a page section
        body = re.split(r"(?m)^##\s+Sources\s*$", body)[0]
        if mode == "headings" and name.lower() == "sources":
            continue
        h = HEADING.search(body)
        text = FLAG.sub(" ", body)
        out.append({
            "name": name,
            "heading": h.group(2).strip() if h else "",
            "flags": flags(body),
            "words": len(re.findall(r"[A-Za-z0-9']+", re.sub(r"\(/[^)]*\)|<!--.*?-->", " ", text))),
            "links": len(re.findall(r"\]\([^)]+\)", body)),
        })
    return out, mode


def md_sections(md: str) -> dict[str, str]:
    """`## Heading` -> body text, for the brief."""
    out, cur, buf = {}, None, []
    for line in md.split("\n"):
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            if cur is not None:
                out[cur] = "\n".join(buf)
            cur, buf = m.group(1), []
        elif cur is not None:
            buf.append(line)
    if cur is not None:
        out[cur] = "\n".join(buf)
    return out


def table_rows(body: str) -> list[list[str]]:
    rows = []
    for line in body.split("\n"):
        s = line.strip()
        if s.startswith("|") and s.endswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            if all(re.fullmatch(r":?-{3,}:?", c) for c in cells if c):
                continue
            rows.append(cells)
    return rows
