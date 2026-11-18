#!/usr/bin/env python3
"""Design QA and dev prep: check the page templates against the page-type design briefs.

Run from the client's working folder:
  dqa.py scan --slug <slug> [--kit <dir>]      what the briefs, pages, kit and inventory hold
  dqa.py template --slug <slug> --client <name> [--date YYYY-MM-DD] [--force]
                                               write a blank design inventory for the designer
  dqa.py run --slug <slug> --client <name> [--date YYYY-MM-DD] [--kit <dir>]
                                               write design/<slug>/<slug>-design-qa-devprep.md
  dqa.py briefs <briefs.md> [--validate]       the page-type briefs as this skill reads them (JSON)

Standard library only. Exit 0 on PASS, 1 on FAIL or a missing input.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

TYPE_SECTIONS = ["Service Pages", "Location Pages", "About Page", "Contact Page", "Resource Pages"]
INV_LISTS = ["Colours", "Fonts", "Images", "Icon Set", "Spacing", "Interactive Elements"]
CHECKLIST = [("Images", "Images"), ("Icon Set", "Icon set"), ("Fonts", "Fonts"),
             ("Colours", "Colour palette"), ("Spacing", "Spacing"),
             ("Interactive Elements", "Interactive elements")]
FILL = "<fill>"
HEX = re.compile(r"#(?:[0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})(?![0-9A-Za-z])")


def hex6(h: str) -> str:
    h = h.lower().lstrip("#")
    return "#" + ("".join(c * 2 for c in h) if len(h) == 3 else h)


def has_word(term: str, text: str) -> bool:
    return re.search(rf"(?i)(?<!\w){re.escape(term)}(?!\w)", text) is not None
DIMS = re.compile(r"\b\d+\s*[x×]\s*\d+\b")
BRIEF_KEYS = ["page_type", "pages", "Content Map", "CTAs", "Responsive Priorities", "H2 sections"]


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8") if p.is_file() else ""


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", s.lower())).strip()


def blocks(text: str, level: int) -> list[tuple[str, str]]:
    mark = "#" * level + " "
    out: list[tuple[str, str]] = []
    cur, buf = None, []
    for ln in text.split("\n"):
        if ln.startswith(mark):
            if cur is not None:
                out.append((cur, "\n".join(buf)))
            cur, buf = ln[len(mark):].strip(), []
        elif ln.startswith("#" * (level - 1) + " ") and level > 1 and not ln.startswith(mark):
            if cur is not None:
                out.append((cur, "\n".join(buf)))
            cur, buf = None, []
        elif cur is not None:
            buf.append(ln)
    if cur is not None:
        out.append((cur, "\n".join(buf)))
    return out


def bullets(body: str) -> list[str]:
    return [ln[2:].strip() for ln in body.split("\n") if ln.startswith("- ")]


def table_rows(body: str) -> list[dict[str, str]]:
    lines = [ln for ln in body.split("\n") if ln.strip().startswith("|")]
    if len(lines) < 2:
        return []
    head = [c.strip() for c in lines[0].strip().strip("|").split("|")]
    rows = []
    for ln in lines[2:]:
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) == len(head):
            rows.append(dict(zip(head, cells)))
    return rows


# ---------- page-type design briefs ----------

def read_briefs(path: Path) -> dict:
    text = read(path)
    types = []
    for name, body in blocks(text, 2):
        if name not in TYPE_SECTIONS:
            continue
        subs = dict(blocks("\n" + body, 3))
        pages = re.findall(r"`([^`]+/article\.md)`", subs.get("Pages", ""))
        sections = [r.get("Section", "") for r in table_rows(subs.get("Content Map", "")) if r.get("Section")]
        cta_text = subs.get("CTAs", "")
        cta_sections = [s for s in sections if has_word(s, cta_text)]
        h2 = re.search(r"(?m)^H2 sections:\s*(\d+)(?:\s+to\s+(\d+))?", subs.get("Content Length", ""))
        types.append({
            "page_type": name,
            "pages": pages,
            "Content Map": sections,
            "CTAs": cta_sections,
            "Responsive Priorities": bullets(subs.get("Responsive Priorities", "")),
            "H2 sections": int(h2.group(2) or h2.group(1)) if h2 else None,
        })
    return {"file": path.as_posix(), "## Page Types": types}


def h2_count(text: str) -> int:
    return len([h for h in re.findall(r"(?m)^## (.+)$", text) if h.strip().lower() != "sources"])


def words_of(text: str) -> int:
    t = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
    t = re.sub(r"\]\([^)]*\)", "]", t)
    t = re.sub(r"[#*_>|`\[\]]", " ", t)
    return len(t.split())


def longest_page(root: Path, pages: list[str]) -> dict | None:
    best = None
    for rel in pages:
        text = read(root / rel)
        if not text:
            continue
        info = {"page": rel, "h2": h2_count(text), "words": words_of(text)}
        if best is None or (info["h2"], info["words"]) > (best["h2"], best["words"]):
            best = info
    return best


def page_desc(lp: dict) -> str:
    if not lp["words"]:
        return f"{lp['page']} ({lp['h2']} H2 sections)"
    return f"{lp['page']} ({lp['h2']} H2 sections, {lp['words']} words)"


def find_kit(root: Path, kit: str | None) -> Path | None:
    if kit:
        p = root / kit
        return p if p.is_dir() else None
    base = root / "client-reference"
    dirs = sorted(d for d in base.iterdir() if d.is_dir()) if base.is_dir() else []
    return dirs[0] if len(dirs) == 1 else None


def brand_text(root: Path, kit: Path | None, brief_path: Path) -> tuple[str, list[str]]:
    files = []
    if kit:
        files += [kit / n for n in ("brand.md", "style.md") if (kit / n).is_file()]
    files.append(brief_path)
    return "\n".join(read(f) for f in files), [f.relative_to(root).as_posix() for f in files if f.is_file()]


# ---------- design inventory ----------

def read_inventory(path: Path) -> dict:
    text = read(path)
    head = text.split("\n## ", 1)[0]
    src = re.search(r"(?m)^Source:\s*(.+)$", head)
    inv = {"file": path.as_posix(), "source": src.group(1).strip() if src else "", "templates": [], "lists": {},
           "fill_left": FILL in text}
    for name, body in blocks(text, 2):
        if name.startswith("Template:"):
            t = {"page_type": name.split(":", 1)[1].strip(), "frame": "", "holds": None, "holds_raw": "",
                 "sections": [], "ctas": []}
            fr = re.search(r"(?m)^Frame:\s*(.*)$", body)
            t["frame"] = fr.group(1).strip() if fr else ""
            ho = re.search(r"(?m)^Holds H2 sections:\s*(.*)$", body)
            t["holds_raw"] = ho.group(1).strip() if ho else ""
            if re.fullmatch(r"\d+", t["holds_raw"]):
                t["holds"] = int(t["holds_raw"])
            in_sections = False
            for ln in body.split("\n"):
                if re.match(r"^Sections:\s*$", ln):
                    in_sections = True
                    continue
                if in_sections and ln.startswith("- "):
                    layer, _, target = ln[2:].partition("->")
                    t["sections"].append({"layer": layer.strip(), "brief_section": target.strip()})
                    continue
                if in_sections and ln.strip():
                    in_sections = False
            ct = re.search(r"(?m)^CTAs after:\s*(.*)$", body)
            if ct:
                t["ctas"] = [c.strip() for c in ct.group(1).split(",") if c.strip()]
            inv["templates"].append(t)
        elif name in INV_LISTS:
            inv["lists"][name] = bullets(body)
    return inv


def blank_inventory(client: str, date: str, briefs: dict) -> str:
    out = [f"Client: {client}", "Source: designer", f"Filled: {date}", "",
           f"# Design Inventory: {client}", "",
           "Replace each placeholder with what the template has, one line per item. Holds H2 sections takes a "
           "number or `no limit`. Sections lists the containers top to bottom as `layer name -> brief section`; "
           "write `-> global` for header, footer or navigation and `-> none` for a layer with no section in the "
           "brief. CTAs after names brief sections, comma separated.", ""]
    for t in briefs["## Page Types"]:
        out += [f"## Template: {t['page_type']}", "", f"Frame: {FILL}",
                f"Holds H2 sections: {FILL}", "Sections:"]
        out += [f"- {FILL} -> {s}" for s in t["Content Map"]]
        out += [f"CTAs after: {FILL}", ""]
    hints = {
        "Colours": f"- {FILL}: {FILL}",
        "Fonts": f"- {FILL}: {FILL}",
        "Images": f"- {FILL}: {FILL}",
        "Icon Set": f"- {FILL}",
        "Spacing": f"- {FILL}",
        "Interactive Elements": f"- {FILL}: {FILL}",
    }
    guide = {
        "Colours": "Each colour as `#hex: where it is used`.",
        "Fonts": "Each family as `Family weights: where the files come from` (Google Fonts, Adobe Fonts, font files).",
        "Images": "Each image as `name: width x height, format` (an SVG needs no size).",
        "Icon Set": "The icon library and style.",
        "Spacing": "The base unit and the spacing between sections.",
        "Interactive Elements": "Each element as `name: what it does`.",
    }
    for name in INV_LISTS:
        out += [f"## {name}", "", guide[name], "", hints[name], ""]
    return "\n".join(out).rstrip() + "\n"


# ---------- checks ----------

def run_checks(root: Path, briefs: dict, inv: dict, brand: str) -> list[tuple[str, str, str, str]]:
    rows: list[tuple[str, str, str, str]] = []
    by_type = {t["page_type"]: t for t in inv["templates"]}
    if inv["fill_left"]:
        rows.append(("All", "Inventory filled", "FAIL", "the inventory still has <fill> lines"))
    else:
        rows.append(("All", "Inventory filled", "PASS", inv["source"] or "source not stated"))
    for bt in briefs["## Page Types"]:
        name = bt["page_type"]
        t = by_type.get(name)
        if not t:
            rows.append((name, "Template exists", "FAIL", f"no `## Template: {name}` in the inventory"))
            continue
        rows.append((name, "Template exists", "PASS", t["frame"] or "frame not named"))
        mapped = [s for s in t["sections"] if norm(s["brief_section"]) not in ("global", "none", "")]
        mapped_names = [norm(s["brief_section"]) for s in mapped]
        missing = [s for s in bt["Content Map"] if norm(s) not in mapped_names]
        rows.append((name, "Brief sections have containers", "FAIL" if missing else "PASS",
                     ("no container for " + ", ".join(missing)) if missing
                     else f"{len(bt['Content Map'])} of {len(bt['Content Map'])}"))
        known = {norm(s) for s in bt["Content Map"]}
        empty = [s["layer"] for s in t["sections"]
                 if norm(s["brief_section"]) in ("none", "") or
                 (norm(s["brief_section"]) != "global" and norm(s["brief_section"]) not in known)]
        rows.append((name, "Containers have content", "FAIL" if empty else "PASS",
                     ("no brief section for " + ", ".join(empty)) if empty else "every container maps to a brief section"))
        order = [norm(s) for s in bt["Content Map"]]
        seen = [order.index(n) for n in mapped_names if n in order]
        rows.append((name, "Section order", "PASS" if seen == sorted(seen) else "FLAG",
                     "same order as the brief" if seen == sorted(seen) else "containers are not in the brief's order"))
        lp = longest_page(root, bt["pages"])
        if not lp and bt["H2 sections"] is not None:
            lp = {"page": "the brief's Content Length", "h2": bt["H2 sections"], "words": 0}
        if not lp:
            rows.append((name, "Holds the longest page", "FAIL", "none of the brief's pages exist in content/ "
                         "and the brief gives no H2 sections line"))
        elif t["holds_raw"].lower() == "no limit":
            rows.append((name, "Holds the longest page", "PASS",
                         f"no limit; longest is {page_desc(lp)}"))
        elif t["holds"] is None:
            rows.append((name, "Holds the longest page", "FAIL", "`Holds H2 sections:` is not a number or no limit"))
        else:
            ok = t["holds"] >= lp["h2"]
            rows.append((name, "Holds the longest page", "PASS" if ok else "FAIL",
                         f"holds {t['holds']}; longest is {page_desc(lp)}"))
        want = [norm(s) for s in bt["CTAs"]]
        have = [norm(c) for c in t["ctas"]]
        miss = [s for s in bt["CTAs"] if norm(s) not in have]
        extra = [c for c in t["ctas"] if norm(c) not in want]
        if miss:
            rows.append((name, "CTA placement", "FAIL", "no CTA after " + ", ".join(miss)))
        elif extra:
            rows.append((name, "CTA placement", "FLAG", "CTA the brief does not place: " + ", ".join(extra)))
        else:
            rows.append((name, "CTA placement", "PASS",
                         ", ".join(t["ctas"]) if t["ctas"] else "the brief places no CTA"))
    for name in by_type:
        if name not in [b["page_type"] for b in briefs["## Page Types"]]:
            rows.append((name, "Template exists", "FLAG", "template for a page type the briefs do not cover"))
    lists = inv["lists"]
    brand_hex = {hex6(h) for h in HEX.findall(brand)}
    hexes = [h for ln in lists.get("Colours", []) for h in HEX.findall(ln)]
    unsourced = [h for h in hexes if hex6(h) not in brand_hex]
    if not hexes:
        rows.append(("All", "Colours sourced", "FAIL", "no colours listed"))
    elif unsourced:
        rows.append(("All", "Colours sourced", "FLAG", "not in the brand sources: " + ", ".join(unsourced)))
    else:
        rows.append(("All", "Colours sourced", "PASS", f"{len(hexes)} of {len(hexes)} in the brand sources"))
    fams = []
    for ln in lists.get("Fonts", []):
        fam = re.split(r"\s\d|:", ln, maxsplit=1)[0].strip()
        if fam:
            fams.append(fam)
    fonts_out = [f for f in fams if not has_word(f, brand)]
    if not fams:
        rows.append(("All", "Fonts sourced", "FAIL", "no fonts listed"))
    elif fonts_out:
        rows.append(("All", "Fonts sourced", "FLAG", "not in the brand sources: " + ", ".join(fonts_out)))
    else:
        rows.append(("All", "Fonts sourced", "PASS", ", ".join(fams)))
    gaps = []
    for ln in lists.get("Colours", []):
        if not HEX.search(ln):
            gaps.append(f"{ln} (no hex value)")
    for ln in lists.get("Images", []):
        if not DIMS.search(ln) and not re.search(r"(?i)\bsvg\b", ln):
            gaps.append(f"{ln.split(':', 1)[0]} (no width x height)")
    for ln in lists.get("Fonts", []):
        if ":" not in ln or not ln.split(":", 1)[1].strip():
            gaps.append(f"{ln} (no font source)")
    for ln in lists.get("Interactive Elements", []):
        if ":" not in ln or not ln.split(":", 1)[1].strip():
            gaps.append(f"{ln} (no behaviour)")
    for name in ("Images", "Icon Set", "Spacing"):
        if not lists.get(name):
            gaps.append(f"{name} (empty)")
    rows.append(("All", "Asset details complete", "FAIL" if gaps else "PASS",
                 "; ".join(gaps) if gaps else "every asset has its details"))
    return rows


def write_report(client: str, date: str, inv_rel: str, inv: dict, briefs: dict,
                 rows: list[tuple[str, str, str, str]]) -> tuple[str, bool]:
    ok = not any(r[2] == "FAIL" for r in rows)
    out = [f"Client: {client} · Checked: {date} · Inventory: {inv_rel} (source: {inv['source'] or 'not stated'})", "",
           f"# Design QA and Dev Prep: {client}", "", "## Results", "",
           "| Template | Check | Result | Detail |", "|---|---|---|---|"]
    out += [f"| {a} | {b} | {c} | {d.replace('|', '/')} |" for a, b, c, d in rows]
    fails = [r for r in rows if r[2] == "FAIL"]
    flags = [r for r in rows if r[2] == "FLAG"]
    out += ["", "## To Fix", ""]
    out += [f"{i}. {r[0]}, {r[1]}: {r[3]}. Design." for i, r in enumerate(fails, 1)] or ["- Nothing to fix."]
    out += ["", "## To Confirm", ""]
    out += [f"{i}. {r[0]}, {r[1]}: {r[3]}. Design confirms." for i, r in enumerate(flags, 1)] or ["- Nothing to confirm."]
    out += ["", "## Mobile-First Priorities", ""]
    for t in briefs["## Page Types"]:
        out += [f"### {t['page_type']}", ""]
        out += [f"- {b}" for b in t["Responsive Priorities"]] or ["- The brief lists no responsive priorities."]
        out.append("")
    unsourced = {h.lower() for r in rows if r[1] == "Colours sourced" and r[2] == "FLAG" for h in HEX.findall(r[3])}
    out += ["## Asset Checklist", ""]
    for key, label in CHECKLIST:
        out += [f"### {label}", ""]
        items = inv["lists"].get(key, [])
        lines = []
        for it in items:
            note = " (not in the brand sources; Design confirms)" if key == "Colours" and \
                any(h.lower() in unsourced for h in HEX.findall(it)) else ""
            lines.append(f"- {it}{note}")
        out += lines or ["- None listed."]
        out.append("")
    out.append(f"RESULT: {'PASS' if ok else 'FAIL'}")
    return "\n".join(out) + "\n", ok


# ---------- commands ----------

def paths(slug: str) -> dict[str, Path]:
    d = Path("design") / slug
    return {"briefs": d / f"{slug}-page-type-design-briefs.md", "inv": d / f"{slug}-design-inventory.md",
            "out": d / f"{slug}-design-qa-devprep.md"}


def today(a) -> str:
    return a.date or dt.date.today().isoformat()


def cmd_scan(a) -> int:
    root, p = Path("."), paths(a.slug)
    if not p["briefs"].is_file():
        print(f"MISSING: {p['briefs'].as_posix()} (write it first with page-type-design-briefs)")
        return 1
    b = read_briefs(p["briefs"])
    print(f"briefs: {p['briefs'].as_posix()}")
    for t in b["## Page Types"]:
        lp = longest_page(root, t["pages"])
        print(f"- {t['page_type']}: {len(t['pages'])} page(s)")
        print(f"    content map: {', '.join(t['Content Map'])}")
        print(f"    CTA sections named in CTAs: {', '.join(t['CTAs']) or 'none'}")
        if lp:
            print(f"    longest page: {lp['page']} ({lp['h2']} H2 sections, {lp['words']} words)")
    kit = find_kit(root, a.kit)
    _, files = brand_text(root, kit, p["briefs"])
    print("brand sources: " + ", ".join(files))
    if p["inv"].is_file():
        inv = read_inventory(p["inv"])
        print(f"inventory: {p['inv'].as_posix()} (source: {inv['source'] or 'not stated'})"
              + ("; still has <fill> lines" if inv["fill_left"] else ""))
        print("templates: " + (", ".join(t["page_type"] for t in inv["templates"]) or "none"))
    else:
        print(f"inventory: none at {p['inv'].as_posix()}")
    return 0


def cmd_template(a) -> int:
    p = paths(a.slug)
    if not p["briefs"].is_file():
        print(f"MISSING: {p['briefs'].as_posix()} (write it first with page-type-design-briefs)")
        return 1
    if p["inv"].is_file() and not a.force:
        print(f"EXISTS: {p['inv'].as_posix()} (pass --force to replace it)")
        return 1
    p["inv"].parent.mkdir(parents=True, exist_ok=True)
    p["inv"].write_text(blank_inventory(a.client, today(a), read_briefs(p["briefs"])), encoding="utf-8")
    print(f"wrote {p['inv'].as_posix()}: the designer fills every {FILL}, then run `run`")
    return 0


def cmd_run(a) -> int:
    root, p = Path("."), paths(a.slug)
    for key in ("briefs", "inv"):
        if not p[key].is_file():
            print(f"MISSING: {p[key].as_posix()}")
            return 1
    briefs = read_briefs(p["briefs"])
    if not briefs["## Page Types"]:
        print(f"FAIL: no page-type sections in {p['briefs'].as_posix()}")
        return 1
    inv = read_inventory(p["inv"])
    brand, _ = brand_text(root, find_kit(root, a.kit), p["briefs"])
    rows = run_checks(root, briefs, inv, brand)
    text, ok = write_report(a.client, today(a), p["inv"].as_posix(), inv, briefs, rows)
    p["out"].write_text(text, encoding="utf-8")
    print(f"wrote {p['out'].as_posix()}")
    for r in rows:
        if r[2] != "PASS":
            print(f"{r[2]}  {r[0]}, {r[1]}: {r[3]}")
    print(f"RESULT: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def cmd_briefs(a) -> int:
    p = Path(a.file)
    if a.validate:
        try:
            data = json.loads(read(p))
        except json.JSONDecodeError as e:
            print(f"FAIL: {e}")
            return 1
        types = data.get("## Page Types") or []
        bad = [k for k in BRIEF_KEYS for t in types if k not in t]
        if not types or bad:
            print(f"FAIL: missing {'## Page Types' if not types else sorted(set(bad))}")
            return 1
        print("OK")
        return 0
    if not p.is_file():
        print(f"FAIL: {p} does not exist")
        return 1
    print(json.dumps(read_briefs(p), indent=2, ensure_ascii=False))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan")
    s.add_argument("--slug", required=True)
    s.add_argument("--kit")
    t = sub.add_parser("template")
    t.add_argument("--slug", required=True)
    t.add_argument("--client", required=True)
    t.add_argument("--date")
    t.add_argument("--force", action="store_true")
    r = sub.add_parser("run")
    r.add_argument("--slug", required=True)
    r.add_argument("--client", required=True)
    r.add_argument("--date")
    r.add_argument("--kit")
    b = sub.add_parser("briefs")
    b.add_argument("file")
    b.add_argument("--validate", action="store_true")
    a = ap.parse_args(argv)
    if getattr(a, "date", None) and not re.match(r"^\d{4}-\d{2}-\d{2}$", a.date):
        ap.error("--date must be YYYY-MM-DD")
    return {"scan": cmd_scan, "template": cmd_template, "run": cmd_run, "briefs": cmd_briefs}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
