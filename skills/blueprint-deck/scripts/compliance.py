"""Compliance checks on a finished .pptx, standard library only.

Reads the slide and speaker-notes XML straight from the zip, so it works on a deck built by
deck.py and on one edited by hand in PowerPoint. Checks: em-dashes, any form of "prescribe",
figures that are not in the Blueprint, and quotes that are not word for word in the quote bank.
"""
from __future__ import annotations

import posixpath
import re
import zipfile
import xml.etree.ElementTree as ET

A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
PR = "{http://schemas.openxmlformats.org/package/2006/relationships}"

EM_DASHES = "—⸺⸻"
PRESCRIBE = re.compile(r"prescri\w*", re.I)
NEEDS = re.compile(r"\[NEEDS INPUT:[^\]]*\]")
# Layout text the script writes itself: footer, page number, cover date, divider number.
CHROME_PH = {"sldNum", "dt", "ftr", "hdr", "sldImg"}


# --------------------------------------------------------------------------- reading
def _rels(z: zipfile.ZipFile, part: str) -> dict[str, tuple[str, str]]:
    d, f = posixpath.split(part)
    rp = posixpath.join(d, "_rels", f + ".rels")
    if rp not in z.namelist():
        return {}
    out = {}
    for rel in ET.fromstring(z.read(rp)).iter(f"{PR}Relationship"):
        out[rel.get("Id")] = (rel.get("Type", "").rsplit("/", 1)[-1],
                              posixpath.normpath(posixpath.join(d, rel.get("Target", ""))))
    return out


def _shape_texts(root) -> list[tuple[str, str, str]]:
    """(name, placeholder type, text) for every shape or table that holds text."""
    out = []
    for el in root.iter():
        if el.tag not in (f"{P}sp", f"{P}graphicFrame"):
            continue
        c = el.find(f".//{P}cNvPr")
        name = c.get("name", "") if c is not None else ""
        ph = el.find(f".//{P}ph")
        ptype = ph.get("type", "body") if ph is not None else ""
        paras = []
        for p in el.iter(f"{A}p"):
            paras.append("".join(t.text or "" for t in p.iter(f"{A}t")))
        text = "\n".join(paras).strip()
        if text:
            out.append((name, ptype, text))
    return out


def read_deck(path) -> list[dict]:
    """One dict per slide in presentation order: {'n', 'shapes': [(name, ph, text)], 'notes': str}."""
    with zipfile.ZipFile(path) as z:
        pres = "ppt/presentation.xml"
        rels = _rels(z, pres)
        root = ET.fromstring(z.read(pres))
        slides = []
        lst = root.find(f"{P}sldIdLst")
        for i, sid in enumerate(lst if lst is not None else [], 1):
            part = rels[sid.get(f"{R}id")][1]
            shapes = _shape_texts(ET.fromstring(z.read(part)))
            notes = ""
            for kind, target in _rels(z, part).values():
                if kind == "notesSlide" and target in z.namelist():
                    texts = _shape_texts(ET.fromstring(z.read(target)))
                    notes = "\n".join(t for _, ph, t in texts if ph not in CHROME_PH)
            slides.append({"n": i, "shapes": shapes, "notes": notes})
        return slides


# --------------------------------------------------------------------------- figures
NUM = re.compile(r"\$?\d[\d,]*(?:\.\d+)?(?:\s?%|\s?percent\b)?", re.I)
TIME_LABELS = [
    r"\b(?:phase|tier|step|slide|week|month|year|q)s?\s+\d+(?:\s*(?:to|-|–|and|or|,)\s*\d+)*\b",
    r"\b(?:[1-9]|1[0-2]|18|24)(?:\s*(?:,|to|-|–|and|or)\s*(?:[1-9]|1[0-2]|18|24))*\s*-?\s*(?:months?|weeks?)\b",
    r"\b\d{4}-\d{2}-\d{2}\b",
    r"\b\d{1,2}:\d{2}(?::\d{2})?\b",
    r"(?<![\w$.])/[\w./-]*",
    r"\S*(?:://|@)\S*",
]


def _norm(tok: str) -> str:
    pct = tok.rstrip().lower().endswith(("%", "percent"))
    money = tok.strip().startswith("$")
    t = re.sub(r"(?i)\s?(%|percent)$", "", tok.strip()).lstrip("$").replace(",", "")
    if "." in t:
        t = t.rstrip("0").rstrip(".")
    return ("$" if money else "") + t + ("%" if pct else "")


def figures(text: str) -> list[str]:
    t = NEEDS.sub(" ", text)
    for pat in TIME_LABELS:
        t = re.sub(pat, " ", t, flags=re.I)
    out = []
    for m in NUM.finditer(t):
        tok = m.group(0).strip().rstrip(",.")
        bare = re.sub(r"(?i)\s?(%|percent)$", "", tok).lstrip("$").replace(",", "")
        if re.fullmatch(r"\d", bare) and not tok.startswith("$") and not re.search(r"(?i)%|percent", tok):
            continue
        out.append(tok)
    return out


def number_set(text: str) -> set[str]:
    """Every number written in the Blueprint, normalized. Dates are left out, so a date's parts
    never vouch for a figure; a money figure only matches money and a percentage only a percentage."""
    t = re.sub(r"\b\d{4}-\d{2}-\d{2}\b", " ", text)
    return {_norm(m.group(0).strip().rstrip(",.")) for m in NUM.finditer(t)}


# --------------------------------------------------------------------------- quotes
SENT = re.compile(r"(?<=[.!?])\s+")
QUOTED = re.compile(r"[“\"]([^“”\"]{3,}?)[”\"]")


def norm_quote(s: str) -> str:
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return " ".join(s.split()).strip()


def strip_marks(s: str) -> str:
    return norm_quote(s).strip('"').strip()


def quote_bank(text: str) -> tuple[list[tuple[str, str]], str]:
    """(quote, speaker) rows and the `Call date:` of a quote bank file."""
    date = ""
    m = re.search(r"(?m)^Call date:\s*(\S+)", text)
    if m:
        date = m.group(1)
    rows = []
    header = None
    for line in text.splitlines():
        if not line.startswith("|"):
            header = None if not line.strip() else header
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if header is None:
            header = [c.lower() for c in cells]
            continue
        if set("".join(cells)) <= set("-: "):
            continue
        if "quote" in header and "speaker" in header and len(cells) == len(header):
            rows.append((cells[header.index("quote")], cells[header.index("speaker")]))
    return rows, date


# --------------------------------------------------------------------------- the check
def is_chrome(name: str, ph: str) -> bool:
    return name.startswith("chrome:") or ph in CHROME_PH


def check(deck_path, blueprint_text: str, bank_text: str) -> dict:
    slides = read_deck(deck_path)
    known = number_set(blueprint_text)
    bank, call_date = quote_bank(bank_text)
    bank_quotes = [norm_quote(q) for q, _ in bank]
    res = {"slides": len(slides), "em": [], "prescribe": [], "figures": [], "quotes": [],
           "needs_input": [], "notes_missing": []}

    def verbatim(q: str, whole: bool) -> bool:
        if q in bank_quotes:
            return True
        if whole:
            return False
        # outside a quote card, a run of whole sentences from one bank quote also counts
        for b in bank_quotes:
            sents = SENT.split(b)
            for i in range(len(sents)):
                for j in range(i + 1, len(sents) + 1):
                    if " ".join(sents[i:j]) == q:
                        return True
        return False

    for s in slides:
        n = s["n"]
        parts = [(name, ph, txt, "slide") for name, ph, txt in s["shapes"]] + [("notes", "", s["notes"], "notes")]
        if not s["notes"].strip():
            res["notes_missing"].append(n)
        for name, ph, txt, where in parts:
            loc = "notes" if where == "notes" else (name or "shape")
            for ch in EM_DASHES:
                for m in re.finditer(ch, txt):
                    res["em"].append((n, loc, _ctx(txt, m.start())))
            for m in PRESCRIBE.finditer(txt):
                res["prescribe"].append((n, loc, m.group(0)))
            for m in NEEDS.finditer(txt):
                res["needs_input"].append((n, m.group(0)))
            if is_chrome(name, ph):
                continue
            scan = txt
            if name.startswith("quote:"):
                q = strip_marks(txt)
                res["quotes"].append((n, q, verbatim(q, True)))
                continue
            if name.startswith("attr:"):
                continue
            for m in QUOTED.finditer(txt):
                q = norm_quote(m.group(1))
                if len(q.split()) >= 6:
                    res["quotes"].append((n, q, verbatim(q, False)))
                    scan = scan.replace(m.group(0), " ")
            for tok in figures(scan):
                res["figures"].append((n, tok, _norm(tok) in known, loc))
    res["call_date"] = call_date
    return res


def _ctx(text: str, i: int, w: int = 30) -> str:
    return " ".join(text[max(0, i - w): i + w].split())


def summary_rows(res: dict) -> list[tuple[str, str, str]]:
    em, pr = len(res["em"]), len(res["prescribe"])
    bad_fig = [f for f in res["figures"] if not f[2]]
    bad_q = [q for q in res["quotes"] if not q[2]]
    rows = [
        ("em-dashes", "PASS" if not em else "FAIL", f"{em} found"),
        ("prescribe", "PASS" if not pr else "FAIL", f"{pr} found"),
        ("figures", "PASS" if not bad_fig else "FAIL",
         f"{len(res['figures'])} figures, {len(bad_fig)} not in the Blueprint"
         + (": " + ", ".join(f"slide {n} {t}" for n, t, _, _ in bad_fig[:8]) if bad_fig else "")),
        ("quotes", "PASS" if not bad_q else "FAIL",
         f"{len(res['quotes'])} quotes, {len(bad_q)} not word for word in the quote bank"
         + (": " + "; ".join(f"slide {n} '{q[:60]}'" for n, q, _ in bad_q[:4]) if bad_q else "")),
        ("speaker notes", "PASS" if not res["notes_missing"] else "FAIL",
         "every slide has notes" if not res["notes_missing"] else
         "no notes on slide " + ", ".join(map(str, res["notes_missing"]))),
    ]
    if res["needs_input"]:
        rows.append(("needs input", "NEEDS_INPUT",
                     f"{len(res['needs_input'])} open: " + "; ".join(f"slide {n}" for n, _ in res["needs_input"][:6])))
    return rows


def result(rows) -> str:
    states = {r[1] for r in rows}
    if "FAIL" in states:
        return "FAIL"
    if "NEEDS_INPUT" in states:
        return "NEEDS_INPUT"
    return "PASS"


def hits_table(res: dict) -> list[str]:
    out = []
    for n, loc, ctx in res["em"]:
        out.append(f"| {n} | em-dash | {loc} | {_cell(ctx)} |")
    for n, loc, word in res["prescribe"]:
        out.append(f"| {n} | prescribe | {loc} | {_cell(word)} |")
    for n, tok, ok, loc in res["figures"]:
        if not ok:
            out.append(f"| {n} | figure not in the Blueprint | {loc} | {_cell(tok)} |")
    for n, q, ok in res["quotes"]:
        if not ok:
            out.append(f"| {n} | quote not word for word | quote | {_cell(q)} |")
    return out


def _cell(s: str) -> str:
    return str(s).replace("|", "/").replace("\n", " ")
