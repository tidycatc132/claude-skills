#!/usr/bin/env python3
"""Facts and checks for the Week 6 go-live confirmation email.

Run from the client's working folder. Standard library only.

  golive_email.py facts --slug <slug> [options]
      Reads the Week 5 handoff, the dev handoff index, the client context and
      the voice file, and prints the warning lines, the header block to copy,
      the page counts, the contact, the voice's email row and the rules.

  golive_email.py check --slug <slug> [options]
      Rewrites the warning lines at the top of
      emails/<slug>/<slug>-go-live-email.md (adds, refreshes or removes them),
      then checks the header, the body and the sign-off. Exit 1 on any FAIL.

  options (give the same ones to facts and check):
      --launch "YYYY-MM-DD[ HH:MM]"   agreed launch date (and time); omit if none
      --integrations "a; b; c"        what goes live, as the PM named it
      --contact "Name"                client contact when the context has none
      --sender "Name"                 who signs; omit for the default sign-off
      --role "Project Manager"        sender's role (default Account Manager)

  golive_email.py contract handoff <week-5-handoff.md>   JSON of what is read
  golive_email.py contract index <dev-handoff-index.md>  JSON of what is read
  golive_email.py contract --validate <file.json>        accept either JSON
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

FIRM = "WISE Digital Partners"
DEFAULT_ROLE = "Account Manager"
MAX_BODY_WORDS = 199  # "under 200 words"

NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
    "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
    "nineteen": 19, "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
}
PAGES_RE = re.compile(
    r"\b(\d+|" + "|".join(NUMBER_WORDS) + r")\b((?:[ \t]+[A-Za-z-]+){0,2})[ \t]+pages?\b",
    re.I,
)

# Integration families. A family may appear in the email only if the PM named
# something in it; everything the PM named must appear.
INTEGRATIONS = {
    "forms": re.compile(r"\bforms?\b", re.I),
    "live chat": re.compile(r"\bchat\b", re.I),
    "analytics": re.compile(r"analytics|\bGA4\b|\btracking\b|tag manager", re.I),
    "Juvo": re.compile(r"\bjuvo\b", re.I),
    "booking": re.compile(r"\bbooking\b|\bscheduler\b|\bscheduling\b", re.I),
}

INTERNAL = [
    (re.compile(r"\bQA\b"), "QA"),
    (re.compile(r"bugherd", re.I), "BugHerd"),
    (re.compile(r"\bseverit(y|ies)\b", re.I), "severity"),
    (re.compile(r"\bcritical\b", re.I), "CRITICAL"),
    (re.compile(r"\bmajor\b", re.I), "MAJOR"),
    (re.compile(r"\bminor\b", re.I), "MINOR"),
    (re.compile(r"\bNO-GO\b", re.I), "NO-GO"),
    (re.compile(r"\bGO\b"), "GO"),
    (re.compile(r"\bhand-?off\b", re.I), "handoff"),
    (re.compile(r"\bdev index\b", re.I), "dev index"),
    (re.compile(r"\bdeferred\b", re.I), "deferred"),
    (re.compile(r"\bnoindex\b", re.I), "noindex"),
    (re.compile(r"\btoggles?\b", re.I), "toggle"),
    (re.compile(r"\bfinal sweep\b", re.I), "final sweep"),
]
SCHEMA = re.compile(r"structured data|\bschema\b|rich (results|snippets)|json-ld|\bmarkup\b", re.I)

# Things the body must say (pattern, what it is for).
MUST_SAY = [
    (re.compile(r"\bready\b", re.I), "says the site is ready"),
    (re.compile(r"\bdesign\b", re.I), "recap names the new design"),
    (re.compile(r"\bcontent\b|\bcopy\b|\bwords\b|\bwriting\b", re.I), "recap names the new content"),
    (re.compile(r"\b(check|test|review|go through|look over)\w*\s+(every|each|all)\b(\s+\w+){0,3}\s+pages?\b", re.I), "after launch: we check every page"),
    (re.compile(r"\bsitemap\b", re.I), "after launch: we submit the sitemap"),
    (re.compile(r"\bindex(ed|ing|es)?\b", re.I), "after launch: we watch indexing"),
    (re.compile(r"\bmonthly\b", re.I), "monthly work starts after launch"),
    (re.compile(r"\bsummary\b|\bclose-out\b|\bwrap-up\b", re.I), "a close-out summary follows"),
    (re.compile(r"\bplan\b|\broadmap\b", re.I), "a plan for the monthly work follows"),
]
HEADER_KEYS = ["Client:", "To:", "Week 5 handoff:", "Pages launching:", "Launch:", "Integrations:"]


class Stop(Exception):
    pass


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8").replace("\r\n", "\n")


def strip_sources(v: str) -> str:
    return re.sub(r"\s*\[[^\]]*\]\s*$", "", v).strip()


def paths(slug: str) -> dict[str, Path]:
    return {
        "handoff": Path(f"handoff/{slug}/{slug}-week-5-handoff.md"),
        "index": Path(f"handoff/{slug}/{slug}-dev-handoff-index.md"),
        "context": Path(f"kickoff/{slug}/{slug}-context.md"),
        "voice": Path(f"client-reference/{slug}/voice.md"),
        "email": Path(f"emails/{slug}/{slug}-go-live-email.md"),
    }


# --------------------------------------------------------------------------- #
# Readers
# --------------------------------------------------------------------------- #
def parse_handoff(text: str) -> dict:
    lines = [ln.rstrip() for ln in text.split("\n")]
    nonempty = [ln for ln in lines if ln.strip()]
    last = nonempty[-1].strip() if nonempty else ""
    head = {}
    for ln in lines:
        if ln.startswith("#"):
            break
        m = re.match(r"^(Client|Checked):\s*(.*)$", ln)
        if m:
            head[m.group(1) + ":"] = m.group(2).strip()
    blocking, in_block = [], False
    for ln in lines:
        if ln.startswith("## "):
            in_block = ln.strip() == "## Blocking"
            continue
        if in_block and ln.startswith("- "):
            blocking.append(ln[2:].strip())
    return {
        "Client:": head.get("Client:", ""),
        "Checked:": head.get("Checked:", ""),
        "## Blocking": blocking,
        "GO": last == "GO",
        "last line": last,
    }


def parse_index(text: str) -> list[dict]:
    pages, group, cur = [], "", None
    for ln in text.split("\n"):
        if ln.startswith("## "):
            if cur:
                pages.append(cur)
                cur = None
            group = ln[3:].strip()
            if group in ("Global", "Design Assets", "Blocking"):
                break
            continue
        if ln.startswith("### "):
            if cur:
                pages.append(cur)
            cur = {"Group": group, "Page": ln[4:].strip(), "URL": "", "Priority": ""}
            continue
        if cur is not None:
            m = re.match(r"^- (Page|URL|Priority):\s*(.*)$", ln)
            if m:
                cur[m.group(1)] = m.group(2).strip()
    if cur:
        pages.append(cur)
    return [p for p in pages if p["Group"]]


def group_label(group: str) -> str:
    return "Other" if group == "Pages Without a Template" else group


def build_counts(pages: list[dict]) -> tuple[int, list[tuple[str, int]]]:
    order: list[str] = []
    counts: dict[str, int] = {}
    for p in pages:
        if p["Priority"] != "Build":
            continue
        g = group_label(p["Group"])
        if g not in counts:
            order.append(g)
            counts[g] = 0
        counts[g] += 1
    return sum(counts.values()), [(g, counts[g]) for g in order]


def parse_context(text: str) -> tuple[str, str]:
    name = contact = ""
    for ln in text.split("\n"):
        m = re.match(r"^- Name:\s*(.+)$", ln)
        if m and not name:
            name = strip_sources(m.group(1))
        m = re.match(r"^- (?:Primary contact|Contact):\s*(.+)$", ln)
        if m and not contact:
            contact = strip_sources(m.group(1)).split(",")[0].split(" (")[0].strip()
    if not name:
        m = re.search(r"^Client:\s*(.+)$", text, re.M)
        name = m.group(1).strip() if m else ""
    return name, contact


def voice_email_row(text: str) -> str:
    for ln in text.split("\n"):
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) >= 2 and cells[0].lower() == "email":
            return " | ".join(cells[1:])
    return ""


def split_integrations(raw: str | None) -> list[str]:
    if not raw:
        return []
    parts = re.split(r"[;,]|\band\b", raw)
    out = []
    for p in parts:
        p = re.sub(r"^(the|a|an)\s+", "", p.strip(" .").strip(), flags=re.I)
        if p:
            out.append(p)
    return out


def families(items: list[str]) -> set[str]:
    out = set()
    for it in items:
        for fam, rx in INTEGRATIONS.items():
            if rx.search(it):
                out.add(fam)
    return out


def parse_launch(raw: str | None) -> tuple[dt.date | None, str]:
    if not raw:
        return None, ""
    m = re.match(r"^\s*(\d{4}-\d{2}-\d{2})(?:[ T](\d{1,2}:\d{2}))?\s*$", raw)
    if not m:
        raise Stop(f"--launch must be YYYY-MM-DD or 'YYYY-MM-DD HH:MM', got {raw!r}")
    d = dt.date.fromisoformat(m.group(1))
    return d, (m.group(2) or "")


# --------------------------------------------------------------------------- #
# Facts
# --------------------------------------------------------------------------- #
def gather(args) -> dict:
    p = paths(args.slug)
    if not p["index"].exists():
        raise Stop(f"No dev handoff index at {p['index']}. Run dev-handoff-index first: the page count comes from it.")
    pages = parse_index(read(p["index"]))
    total, groups = build_counts(pages)
    if total == 0:
        raise Stop(f"{p['index']} lists no Build pages; the page count cannot be stated.")
    if not p["context"].exists():
        raise Stop(f"No client context at {p['context']}. Run new-build-kickoff first.")
    client, contact = parse_context(read(p["context"]))
    if args.contact:
        contact = args.contact.strip()

    warnings: list[str] = []
    if not p["handoff"].exists():
        state = "missing"
        warnings.append(
            f"WARNING: No Week 5 handoff at {p['handoff']}. Run week-5-handoff-check; "
            "send this email only once that final sweep ends GO."
        )
    else:
        h = parse_handoff(read(p["handoff"]))
        state = h["last line"] or "empty"
        if h["last line"] == "NO-GO":
            n = len(h["## Blocking"])
            warnings.append(
                f"WARNING: The Week 5 handoff ends NO-GO (checked {h['Checked:'] or 'date unknown'}, "
                f"{n} blocking item{'s' if n != 1 else ''}). Do not send this email until a new final sweep ends GO."
            )
        elif h["last line"] != "GO":
            state = "no result line"
            warnings.append(
                f"WARNING: {p['handoff']} does not end GO or NO-GO. Re-run week-5-handoff-check before sending."
            )

    idx_lines = [ln.strip() for ln in read(p["index"]).split("\n") if ln.strip()]
    if not idx_lines or idx_lines[-1] != "GO":
        warnings.append(
            f"WARNING: {p['index']} does not end GO, so some Build pages may not be ready. "
            "Check the page count with the PM before sending."
        )

    launch_date, launch_time = parse_launch(args.launch)
    launch_hdr = "client to confirm"
    if launch_date:
        launch_hdr = launch_date.isoformat() + (f" {launch_time}" if launch_time else "")
    items = split_integrations(args.integrations)
    voice = read(p["voice"]) if p["voice"].exists() else ""
    header = [
        f"Client: {client}",
        f"To: {contact or 'unknown'}",
        f"Week 5 handoff: {p['handoff'].as_posix()} ({state})",
        f"Pages launching: {total} (" + ", ".join(f"{g} {n}" for g, n in groups) + ")",
        f"Launch: {launch_hdr}",
        "Integrations: " + (", ".join(items) if items else "none named"),
    ]
    role = (args.role or DEFAULT_ROLE).strip()
    signoff = ([args.sender.strip()] if args.sender else []) + [f"{role}, {FIRM}"]
    return {
        "paths": p, "client": client, "contact": contact, "state": state,
        "warnings": warnings, "header": header, "total": total, "groups": groups,
        "build_pages": [x["Page"] for x in pages if x["Priority"] == "Build"],
        "held_pages": [x["Page"] for x in pages if x["Priority"] != "Build"],
        "launch_date": launch_date, "launch_time": launch_time, "items": items,
        "families": families(items), "voice_row": voice_email_row(voice),
        "voice_file": p["voice"].as_posix() if voice else "", "signoff": signoff,
    }


def long_date(d: dt.date) -> str:
    return f"{d.strftime('%A')}, {d.strftime('%B')} {d.day}"


def cmd_facts(args) -> int:
    f = gather(args)
    out = []
    if f["warnings"]:
        out += ["Warnings (the check writes these at the top of the file, above the header):"]
        out += ["  " + w for w in f["warnings"]]
    else:
        out += ["Warnings: none (the Week 5 handoff ends GO)"]
    out += ["", "Header (copy exactly, then a blank line, then the Subject line):"]
    out += ["  " + h for h in f["header"]]
    out += ["", f"Contact: {f['contact'] or 'unknown'}" + ("" if f["contact"] else " (ask the PM who the email goes to)")]
    out += [f"First name for the greeting: {f['contact'].split()[0] if f['contact'] else 'unknown'}"]
    out += [f"Build pages ({f['total']}): " + "; ".join(f["build_pages"])]
    out += ["Not in this launch (do not count or name): " + ("; ".join(f["held_pages"]) or "none")]
    allowed = sorted({str(f["total"])} | {str(n) for _, n in f["groups"]})
    out += [f"Page numbers the email may use: {', '.join(allowed)} (the total {f['total']} must appear)"]
    if f["launch_date"]:
        t = f" at {f['launch_time']}" if f["launch_time"] else ""
        out += [f"Launch: agreed, state it as {long_date(f['launch_date'])}{t}"]
    else:
        out += ["Launch: no date agreed; ask the client to confirm they are ready to go live"]
    out += ["Integrations to list: " + (", ".join(f["items"]) or "none: name no integration")]
    out += [f"Voice ({f['voice_file']}): {f['voice_row']}" if f["voice_row"] else "Voice: no voice.md email row; plain, warm, short sentences"]
    out += ["Sign-off (last lines): " + " / ".join(f["signoff"])]
    print("\n".join(out))
    return 0


# --------------------------------------------------------------------------- #
# Check
# --------------------------------------------------------------------------- #
def number_value(tok: str) -> int:
    return int(tok) if tok.isdigit() else NUMBER_WORDS[tok.lower()]


def cmd_check(args) -> int:
    f = gather(args)
    path: Path = f["paths"]["email"]
    if not path.exists():
        raise Stop(f"No email at {path}. Write it first.")
    lines = read(path).split("\n")
    # Rewrite the warning block: drop any old WARNING lines and leading blanks.
    i = 0
    while i < len(lines) and (lines[i].startswith("WARNING:") or not lines[i].strip()):
        i += 1
    rest = lines[i:]
    new = (f["warnings"] + [""] if f["warnings"] else []) + rest
    text = "\n".join(new).rstrip("\n") + "\n"
    path.write_text(text, encoding="utf-8")

    results: list[tuple[bool, str]] = []

    def chk(ok: bool, label: str) -> None:
        results.append((bool(ok), label))

    # Header
    got_header = rest[: len(f["header"])]
    for want, got in zip(f["header"], got_header + [""] * len(f["header"])):
        chk(want == got, f"header line {want!r}" + ("" if want == got else f" (found {got!r})"))
    chk(f["contact"] != "", "contact known (To: is not unknown)")
    after = rest[len(f["header"]):]
    j = 0
    while j < len(after) and not after[j].strip():
        j += 1
    subj = after[j] if j < len(after) else ""
    chk(subj.startswith("Subject: ") and len(subj) > len("Subject: "), "Subject line after the header")
    body_lines = after[j + 1:]
    body = "\n".join(body_lines).strip()
    email_text = subj[len("Subject: "):] + "\n" + body

    words = len(body.split())
    chk(0 < words <= MAX_BODY_WORDS, f"body under 200 words ({words})")

    first = next((ln.strip() for ln in body_lines if ln.strip()), "")
    if f["contact"]:
        fname = f["contact"].split()[0]
        chk(first == f"Hi {fname},", f"greeting 'Hi {fname},'" + ("" if first == f"Hi {fname}," else f" (found {first!r})"))

    tail = [ln.strip() for ln in body_lines if ln.strip()][-len(f["signoff"]):]
    chk(tail == f["signoff"], "sign-off " + " / ".join(f["signoff"]) + ("" if tail == f["signoff"] else f" (found {' / '.join(tail)})"))

    # Page numbers
    allowed = {f["total"]} | {n for _, n in f["groups"]}
    seen = [(number_value(m.group(1)), m.group(0)) for m in PAGES_RE.finditer(email_text)]
    wrong = [s for v, s in seen if v not in allowed]
    chk(any(v == f["total"] for v, _ in seen), f"total page count {f['total']} stated")
    chk(not wrong, "page numbers match the dev handoff index" + ("" if not wrong else f" (wrong: {wrong})"))
    held = [pg for pg in f["held_pages"] if pg and re.search(re.escape(pg), email_text, re.I)]
    chk(not held, "no page outside this launch named" + ("" if not held else f" ({held})"))

    # Launch
    if f["launch_date"]:
        ld = long_date(f["launch_date"])
        chk(ld.lower() in email_text.lower(), f"agreed launch date '{ld}' stated")
        if f["launch_time"]:
            hh, mm = f["launch_time"].split(":")
            h = int(hh)
            h12 = h % 12 or 12
            ap = "am" if h < 12 else "pm"
            mins = "" if mm == "00" else f":{mm}"
            forms = [rf"\b{h}:{mm}\b", rf"\b{hh}:{mm}\b", rf"\b{h12}{mins}\s?{ap}\b", rf"\b{h12}{mins}\s?{ap[0]}\.m\.", rf"\b{h12}:{mm}\s?{ap}\b"]
            hit = any(re.search(x, email_text, re.I) for x in forms)
            chk(hit, f"agreed launch time {f['launch_time']} stated")
    else:
        chk(re.search(r"\bconfirm", body, re.I) is not None, "asks the client to confirm they are ready")

    # Integrations
    named = f["families"]
    for item in f["items"]:
        fams = families([item])
        ok = item.lower() in email_text.lower() or any(INTEGRATIONS[x].search(email_text) for x in fams)
        chk(ok, f"named integration '{item}' listed")
    for fam, rx in INTEGRATIONS.items():
        if fam in named:
            continue
        m = rx.search(email_text)
        chk(m is None, f"no unnamed integration ({fam})" + ("" if m is None else f" (found {m.group(0)!r})"))

    # Must-say topics
    for rx, label in MUST_SAY:
        chk(rx.search(body) is not None, label)

    # Never
    m = SCHEMA.search(email_text)
    chk(m is None, "no structured data or schema claim" + ("" if m is None else f" (found {m.group(0)!r})"))
    hits = [lab for rx, lab in INTERNAL if rx.search(email_text)]
    chk(not hits, "no internal terms" + ("" if not hits else f" (found: {', '.join(hits)})"))
    links = re.findall(r"https?://\S+", email_text)
    chk(not links, "no links (the site is not live yet)" + ("" if not links else f" (found {links})"))

    for w in f["warnings"]:
        print(w)
    fails = 0
    for ok, label in results:
        print(("  PASS  " if ok else "  FAIL  ") + label)
        fails += 0 if ok else 1
    print(f"{len(results) - fails}/{len(results)} checks passed" + (", warnings written at the top" if f["warnings"] else ""))
    return 1 if fails else 0


# --------------------------------------------------------------------------- #
# Contract readers
# --------------------------------------------------------------------------- #
def cmd_contract(args) -> int:
    if args.validate:
        data = json.loads(read(Path(args.validate)))
        if isinstance(data, dict):
            for k in ("## Blocking", "GO"):
                if k not in data:
                    raise Stop(f"handoff JSON lacks {k!r}")
            if not isinstance(data["GO"], bool):
                raise Stop("'GO' must be true or false")
            print(f"handoff ok: {'GO' if data['GO'] else 'not GO'}, {len(data['## Blocking'])} blocking item(s)")
            return 0
        if isinstance(data, list):
            for k in ("Page", "Priority"):
                if not all(isinstance(x, dict) and k in x for x in data):
                    raise Stop(f"index JSON lacks {k!r} on some page")
            total, groups = build_counts([{"Group": x.get("Group", ""), **x} for x in data])
            if total == 0:
                raise Stop("index JSON has no Build pages")
            print(f"index ok: {total} Build page(s) in {len(groups)} group(s)")
            return 0
        raise Stop("unrecognised contract JSON")
    if not args.kind or not args.file:
        raise Stop("contract needs 'handoff <file>' or 'index <file>' or '--validate <json>'")
    text = read(Path(args.file))
    data = parse_handoff(text) if args.kind == "handoff" else parse_index(text)
    print(json.dumps(data, indent=2))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("facts", "check"):
        sp = sub.add_parser(name)
        sp.add_argument("--slug", required=True)
        sp.add_argument("--launch")
        sp.add_argument("--integrations")
        sp.add_argument("--contact")
        sp.add_argument("--sender")
        sp.add_argument("--role")
    cp = sub.add_parser("contract")
    cp.add_argument("kind", nargs="?", choices=["handoff", "index"])
    cp.add_argument("file", nargs="?")
    cp.add_argument("--validate")
    args = ap.parse_args(argv)
    try:
        return {"facts": cmd_facts, "check": cmd_check, "contract": cmd_contract}[args.cmd](args)
    except Stop as e:
        print(f"STOP: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
