#!/usr/bin/env python3
"""Check a client reference kit and print the completion summary table.

Usage:
    python3 scripts/check_kit.py client-reference/<client-slug>

Checks the five files (brand.md, voice.md, style.md, audience.md, compliance.md)
for their required H2 headings, the counted elements the spec demands, and
placeholder text. Prints a markdown table `| File | Status | Primary Sections Covered |`
to paste into the final answer, then any problems. Exit 0 when every file passes,
1 when any file fails, 2 on bad usage.

Status values:
    Complete              all checks pass, no GAP lines
    Complete, N gap(s)    all checks pass, "GAP:" appears N times (lines, bullets or table cells)
    ..., thin evidence    appended when the file's ## Sources cites fewer than two
                          tiers ([internal], [site], [search])
    FAIL                  a file, heading or count is missing, or placeholder text found
"""
from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

SPEC = {
    "brand.md": [
        "Core Positioning",
        "Offer Architecture",
        "Key Differentiators",
        "Approved Claims & Proof Points",
        "Call-to-Action Library",
    ],
    "voice.md": [
        "Voice Dimensions",
        "Tone Matrix",
        "Do / Don't Examples",
        "Reading Level & Cadence",
    ],
    "style.md": [
        "Grammar & Localization",
        "Formatting Conventions",
        "Brand Lexicon",
        "Banned Words & Clichés",
        "Citation & Linking Rules",
    ],
    "audience.md": [
        "Ideal Customer Profile",
        "Key Personas",
        "Core Pain Points",
        "Objection Handling",
    ],
    "compliance.md": [
        "Regulatory Framework",
        "Mandatory Disclaimers",
        "Prohibited Claims",
        "Review Triggers",
    ],
}
SOURCES = "Sources"

PLACEHOLDER = re.compile(
    r"\[(client|company|insert|brand|name|product|your)[^\]\n]*\]"
    r"|\bTBD\b|\bTODO\b|lorem ipsum|\{\{|\bXX%|\bX{3,}\b",
    re.I,
)


def norm(h: str) -> str:
    h = unicodedata.normalize("NFKD", h.lower().replace("’", "'"))
    h = "".join(c for c in h if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9&/]+", " ", h).strip()


def sections(text: str) -> dict[str, str]:
    """Map normalised H2 heading -> body up to the next H2."""
    out: dict[str, str] = {}
    parts = re.split(r"(?m)^##[ \t]+(.+?)[ \t]*$", text)
    for i in range(1, len(parts), 2):
        out[norm(parts[i])] = parts[i + 1]
    return out


def h3_count(body: str) -> int:
    return len(re.findall(r"(?m)^###[ \t]+\S", body))


def table_rows(body: str) -> int:
    """Data rows of the first markdown table in body (header and separator excluded)."""
    rows, started = 0, False
    for line in body.splitlines():
        s = line.strip()
        if s.startswith("|"):
            if not started:
                started = True
                continue
            if re.fullmatch(r"\|[\s:|-]+\|?", s):
                continue
            rows += 1
        elif started and s:
            break
    return rows


def items(body: str) -> int:
    """Bullets, numbered items, ### subsections or table rows, whichever is largest."""
    bullets = len(re.findall(r"(?m)^[ \t]*(?:[-*+]|\d+[.)])[ \t]+\S", body))
    return max(bullets, h3_count(body), table_rows(body))


def has_gap(body: str) -> bool:
    return re.search(r"\bGAP:", body) is not None


def count_check(name: str, secs: dict[str, str]) -> list[str]:
    errs: list[str] = []

    def body(h: str) -> str:
        return secs.get(norm(h), "")

    def need_table(h: str) -> None:
        if table_rows(body(h)) < 1 and not has_gap(body(h)):
            errs.append(f"{h} needs a table with at least one row (or a GAP: line)")

    if name == "brand.md":
        n = items(body("Key Differentiators"))
        if not 3 <= n <= 6:
            errs.append(f"Key Differentiators lists {n} items (need 3 to 6)")
        need_table("Approved Claims & Proof Points")
        cta = body("Call-to-Action Library").lower()
        for tier in ("high intent", "mid intent", "low intent"):
            if not re.search(r"(?m)^###[ \t]+" + tier.replace(" ", r"[ -]"), cta):
                errs.append(f"Call-to-Action Library needs a '### {tier.capitalize()}' subsection")
    elif name == "voice.md":
        n = h3_count(body("Voice Dimensions"))
        if not 3 <= n <= 4:
            errs.append(f"Voice Dimensions has {n} '###' traits (need 3 to 4)")
        n = table_rows(body("Tone Matrix"))
        if n < 3:
            errs.append(f"Tone Matrix table has {n} context rows (need 3 or more)")
        n = table_rows(body("Do / Don't Examples"))
        if n < 5:
            errs.append(f"Do / Don't Examples table has {n} pairs (need 5 or more)")
        if not re.search(r"\d", body("Reading Level & Cadence")):
            errs.append("Reading Level & Cadence states no numeric target")
    elif name == "style.md":
        if table_rows(body("Brand Lexicon")) < 1:
            errs.append("Brand Lexicon needs a table of canonical terms")
    elif name == "audience.md":
        n = h3_count(body("Key Personas"))
        if not 2 <= n <= 3:
            errs.append(f"Key Personas has {n} '###' personas (need 2 to 3)")
        n = table_rows(body("Objection Handling"))
        if not 4 <= n <= 5:
            errs.append(f"Objection Handling table has {n} rows (need 4 to 5)")
    elif name == "compliance.md":
        need_table("Regulatory Framework")
        need_table("Review Triggers")
    return errs


def check_file(path: Path, name: str) -> tuple[str, list[str], list[str]]:
    if not path.exists():
        return "FAIL", [], [f"{name} is missing"]
    text = path.read_text(encoding="utf-8")
    secs = sections(text)
    errs: list[str] = []
    covered: list[str] = []
    first = next((ln for ln in text.splitlines() if ln.strip() and not ln.startswith("#")), "")
    if not first.startswith("Client:"):
        errs.append("first text line must start 'Client:' (see references/file-specs.md)")
    for h in SPEC[name]:
        if norm(h) in secs:
            covered.append(h)
            if not secs[norm(h)].strip():
                errs.append(f"'## {h}' is empty")
        else:
            errs.append(f"missing heading '## {h}'")
    if norm(SOURCES) not in secs or not secs[norm(SOURCES)].strip():
        errs.append("missing or empty '## Sources'")
    errs += count_check(name, secs)
    for m in PLACEHOLDER.finditer(text):
        line = text.count("\n", 0, m.start()) + 1
        errs.append(f"placeholder text {m.group(0)!r} on line {line}")
    gaps = len(re.findall(r"\bGAP:", text))
    used = r"\[(internal|site|search)\](?![ \t:]*(?:none|n/?a|not|no)\b)"
    tiers = sorted(set(re.findall(used, secs.get(norm(SOURCES), ""), re.I)))
    if errs:
        status = "FAIL"
    else:
        status = "Complete"
        if gaps:
            status += f", {gaps} gap{'s' if gaps != 1 else ''}"
        if len(tiers) < 2:
            status += f", thin evidence ({tiers[0] if tiers else 'no tagged'} sources only)"
    return status, covered, errs


def main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if len(argv) != 2 or argv[1] in ("-h", "--help"):
        print(__doc__.strip())
        return 2
    kit = Path(argv[1])
    if not kit.is_dir():
        print(f"not a folder: {kit}")
        return 2
    rows, problems = [], []
    for name in SPEC:
        status, covered, errs = check_file(kit / name, name)
        rows.append(f"| `{name}` | {status} | {', '.join(covered) or 'none'} |")
        problems += [f"{name}: {e}" for e in errs]
    print("| File | Status | Primary Sections Covered |")
    print("| :--- | :--- | :--- |")
    print("\n".join(rows))
    if problems:
        print("\nProblems to fix, then run this check again:")
        print("\n".join(f"- {p}" for p in problems))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
