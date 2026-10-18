#!/usr/bin/env python3
"""Open items and checker for the Kickoff Call brief.

Commands (stdlib only):
  items <kickoff/slug>                print what the brief must cover: open item groups with ids,
                                      the scope lines, the access lines and the facts it may quote
  check <kickoff/slug>                check <slug>-kickoff-call-brief.md; prints a table and RESULT
  outline <kickoff/slug>              print the parsed view of the kickoff files as JSON
  outline --validate <file.json>      exit 0 when a JSON outline has the shape this skill reads

Ids: R<n> an open requirement from `## Open Items`, Q<n> an unanswered gap question,
G<n> a `GAP:` bullet, C<n> a `CONFLICT:` bullet (both numbered in document order).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SECTIONS = [
    "Call Goals",
    "What We Know",
    "Questions to Settle",
    "Scope to Confirm",
    "Access to Confirm",
    "Relationship Notes",
]
CONTEXT_HEADINGS = [
    "Snapshot", "Business Overview", "Services", "Customers and Service Area",
    "Goals and Conversion", "Differentiators and Proof", "Competitors", "Website Today",
    "Scope Summary", "Open Items", "Sources",
]
NOT_QUOTABLE = {"Scope Summary", "Open Items", "Sources"}
INTAKE_ITEMS = [
    "Primary contact", "Website approver", "Business name, address, phone and hours", "Logo files",
    "Brand guidelines", "Photos", "Testimonials or reviews", "Team members",
    "Certifications, awards and memberships", "Legal or compliance language", "Sites they like",
    "Things to avoid",
]
PLATFORMS = [
    "Domain", "Hosting", "Website login", "Google Analytics", "Google Search Console",
    "Google Business Profile", "Google Tag Manager", "Google Ads", "Meta ads", "Microsoft Ads",
    "CRM, forms or call tracking",
]
AD_PLATFORMS = {"Google Ads", "Meta ads", "Microsoft Ads"}
MAX_LINES = 120
MAX_KNOW = 10
MAX_GOALS = 5
TAG_END = re.compile(r"\[[a-z][a-z ,]*\]\s*$")
IDS_RE = re.compile(r"^\(((?:[RQGC]\d+)(?:, [RQGC]\d+)*)\)\s+(\S.*)$")
SOURCE_TAGS = {"transcript", "site", "sow", "notes", "user", "maps", "intake", "call", "client"}
GOAL_END = re.compile(r"(\(((?:[RQGC]\d+)(?:, [RQGC]\d+)*)\)|\(access\)|\[([a-z][a-z ,]*)\])\s*$")
# An Open Items bullet is closed only when it says so right after its id or a colon:
# "R6 Competitors: answered in intake form", "R8: n/a, no current website".
CLOSED_R = re.compile(r"(?:^|:\s*)(?:answered|n/a)\b", re.I)
PLACEHOLDER = re.compile(r"\[FILL|\bTODO\b|\bTBD\b|\bFIXME\b|<[a-z ]+>")


class Fail(Exception):
    pass


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8").replace("\r\n", "\n")


def sections(text: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    cur = None
    for line in text.split("\n"):
        m = re.match(r"^## (.+?)\s*$", line)
        if m:
            cur = m.group(1)
            out.setdefault(cur, [])
        elif cur is not None:
            out[cur].append(line)
    return out


def bullets(lines: list[str]) -> list[str]:
    return [ln[2:].strip() for ln in lines if ln.startswith("- ")]


def folder_files(folder: Path) -> tuple[str, Path]:
    slug = folder.name
    ctx = folder / f"{slug}-context.md"
    if not ctx.exists():
        raise Fail(f"{ctx} not found; run new-build-kickoff first")
    return slug, ctx


def client_name(text: str) -> str:
    first = text.split("\n", 1)[0]
    if not first.startswith("Client: "):
        raise Fail("first line of the context is not 'Client: <name>'")
    return first[len("Client: "):].strip()


def parse_gap_questions(path: Path) -> tuple[dict[int, dict], dict[str, str]]:
    """Return {n: {text, answer}} and {R id: coverage status}."""
    if not path.exists():
        return {}, {}
    sec = sections(read(path))
    qs: dict[int, dict] = {}
    cur = None
    for line in sec.get("Questions", []):
        m = re.match(r"^(\d+)\.\s+(.+)$", line)
        if m:
            cur = int(m.group(1))
            qs[cur] = {"text": m.group(2).strip(), "answer": ""}
        elif cur is not None and line.startswith("Answer:"):
            qs[cur]["answer"] = line[len("Answer:"):].strip()
    cov = {}
    for line in sec.get("Checklist Coverage", []):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 3 and re.fullmatch(r"R\d+", cells[0]):
            cov[cells[0]] = cells[2]
    return qs, cov


def paid_media_status(folder: Path, slug: str, scope_bullets: list[str]) -> str:
    if (folder / f"{slug}-paid-media-brief.md").exists():
        return "in scope"
    if any(b.startswith("GAP:") and "paid media" in b.lower() for b in scope_bullets):
        return "interest only"
    return "not in scope"


def parse_agenda(path: Path) -> list[tuple[str, str]] | None:
    """Kickoff Call Agenda of the missing items file as [(item, rest)], or None without the file."""
    if not path.exists():
        return None
    out = []
    for line in sections(read(path)).get("Kickoff Call Agenda", []):
        m = re.match(r"^\d+\.\s+(.+?):\s+(.+)$", line.strip())
        if m:
            out.append((m.group(1).strip(), m.group(2).strip()))
    return out


def inventory_empty(folder: Path, slug: str) -> bool:
    inv = folder / f"{slug}-url-inventory.csv"
    if not inv.exists():
        return False
    return len([ln for ln in read(inv).split("\n") if ln.strip()]) <= 1


def build(folder: Path) -> dict:
    slug, ctx_path = folder_files(folder)
    text = read(ctx_path)
    name = client_name(text)
    sec = sections(text)
    missing = [h for h in CONTEXT_HEADINGS if h not in sec]
    if missing:
        raise Fail(f"context is missing headings: {', '.join(missing)}")
    qs, cov = parse_gap_questions(folder / f"{slug}-gap-questions.md")

    items: dict[str, dict] = {}
    g = c = 0
    for h in CONTEXT_HEADINGS:
        if h in ("Open Items", "Sources"):
            continue
        for b in bullets(sec[h]):
            kind = "G" if b.startswith("GAP:") else "C" if b.startswith("CONFLICT:") else None
            if not kind:
                continue
            if kind == "G":
                g += 1
                iid = f"G{g}"
            else:
                c += 1
                iid = f"C{c}"
            items[iid] = {"text": b, "section": h, "place": "scope" if h == "Scope Summary" else "questions"}

    answered_q = {n for n, q in qs.items() if q["answer"]}
    r_links: dict[str, int] = {}
    for b in bullets(sec["Open Items"]):
        m = re.match(r"^(R\d+)\b[:\s]*(.*)$", b)
        if not m:
            continue
        rid, rest = m.group(1), m.group(2)
        qm = re.search(r"\bQ(\d+)\b", rest) or re.search(r"\bQ(\d+)\b", cov.get(rid, ""))
        if CLOSED_R.search(rest) or cov.get(rid, "").lower() in ("covered", "n/a"):
            continue
        if qm and int(qm.group(1)) in answered_q:
            continue
        items[rid] = {"text": b, "section": "Open Items", "place": "scope" if rid == "R7" else "questions"}
        if qm and int(qm.group(1)) in qs:
            r_links[rid] = int(qm.group(1))
    for n, q in sorted(qs.items()):
        if not q["answer"]:
            items[f"Q{n}"] = {"text": q["text"], "section": "Questions", "place": "questions"}

    groups: list[list[str]] = []
    used = set()
    for iid in items:
        if iid in used:
            continue
        grp = [iid]
        if iid in r_links and f"Q{r_links[iid]}" in items:
            grp.append(f"Q{r_links[iid]}")
        if iid.startswith("Q"):
            continue  # added with its R item, or alone below
        groups.append(grp)
        used.update(grp)
    for iid in items:
        if iid.startswith("Q") and iid not in used:
            groups.append([iid])
            used.add(iid)

    scope = sec["Scope Summary"]
    pages = next((ln[len("SOW pages:"):].strip() for ln in scope if ln.startswith("SOW pages:")), None)
    if pages is None:
        raise Fail("Scope Summary has no 'SOW pages:' line")
    scope_lines = [
        f"- Page count in scope: {pages}",
        f"- Paid media: {paid_media_status(folder, slug, bullets(scope))}",
    ]

    agenda = parse_agenda(folder / f"{slug}-missing-items.md")
    if agenda is None:
        no_site = inventory_empty(folder, slug)
        no_ads = paid_media_status(folder, slug, bullets(scope)) == "not in scope"
        access = [f"- {i}: no record yet" for i in INTAKE_ITEMS]
        for p in PLATFORMS:
            if (p == "Website login" and no_site) or (p in AD_PLATFORMS and no_ads):
                continue
            access.append(f"- {p}: no record yet")
        access_source = "no missing items file yet; client-context-update writes it after the intake form"
    else:
        access = [f"- {i}: {rest}" for i, rest in agenda if i != "Gap question answers"]
        access_source = f"{slug}-missing-items.md"

    know = []
    for h in CONTEXT_HEADINGS:
        if h in NOT_QUOTABLE:
            continue
        for b in bullets(sec[h]):
            if not b.startswith(("GAP:", "CONFLICT:")) and TAG_END.search(b):
                know.append(b)

    return {
        "client": name, "slug": slug, "items": items, "groups": groups,
        "scope_lines": scope_lines, "access": access, "access_source": access_source,
        "know": know,
    }


def cmd_items(folder: Path) -> int:
    d = build(folder)
    print(f"Client: {d['client']}")
    print(f"Brief file: {folder / (d['slug'] + '-kickoff-call-brief.md')}")
    for place, title in (("questions", "Questions to Settle"), ("scope", "Scope to Confirm")):
        print(f"\n== {title}: one line per group (or per merged groups), ids of a group in this order")
        for grp in d["groups"]:
            if d["items"][grp[0]]["place"] != place:
                continue
            print(f"({', '.join(grp)})")
            for iid in grp:
                it = d["items"][iid]
                print(f"    {iid} [{it['section']}]: {it['text']}")
    print("\n== Scope to Confirm: first two lines, copy exactly")
    for ln in d["scope_lines"]:
        print(ln)
    print(f"\n== Access to Confirm: copy exactly (from {d['access_source']})")
    for ln in d["access"]:
        print(ln)
    print(f"\n== What We Know: pick at most {MAX_KNOW}, copy word for word")
    for b in d["know"]:
        print(f"- {b}")
    return 0


def check(folder: Path) -> tuple[list[tuple[str, bool, str]], bool]:
    d = build(folder)
    path = folder / f"{d['slug']}-kickoff-call-brief.md"
    rows: list[tuple[str, bool, str]] = []

    def add(name: str, ok: bool, detail: str = "") -> None:
        rows.append((name, ok, detail))

    if not path.exists():
        add("brief file exists", False, f"{path.name} not found")
        return rows, False
    text = read(path)
    lines = text.rstrip("\n").split("\n")
    add("first line is Client:", lines[0] == f"Client: {d['client']}", lines[0][:60])
    add("title line", f"# Kickoff Call brief for {d['client']}" in lines[:4],
        f"expected '# Kickoff Call brief for {d['client']}'")
    add(f"at most {MAX_LINES} lines", len(lines) <= MAX_LINES, f"{len(lines)} lines")
    heads = [ln[3:].strip() for ln in lines if ln.startswith("## ")]
    add("sections exactly, in order", heads == SECTIONS, f"found {heads}")
    sec = sections(text)
    ph = [ln for ln in lines if PLACEHOLDER.search(ln)]
    add("no placeholders", not ph, ph[0][:60] if ph else "")

    ctx_bullets = {}
    ctx_sec = sections(read(folder / f"{d['slug']}-context.md"))
    for h, body in ctx_sec.items():
        for b in bullets(body):
            ctx_bullets.setdefault(b, h)

    goals = bullets(sec.get("Call Goals", []))
    bad_goal = [b for b in goals if not GOAL_END.search(b)]
    unknown_goal_ids = []
    for b in goals:
        m = GOAL_END.search(b)
        if m and m.group(2):
            unknown_goal_ids += [i for i in m.group(2).split(", ") if i not in d["items"]]
        if m and m.group(3):
            unknown_goal_ids += [t for t in m.group(3).split(", ") if t not in SOURCE_TAGS]
    add(f"Call Goals: 1 to {MAX_GOALS} bullets", 1 <= len(goals) <= MAX_GOALS, f"{len(goals)} bullets")
    add("Call Goals end with open item ids, (access) or a source tag", not bad_goal and not unknown_goal_ids,
        (bad_goal[0][:60] if bad_goal else ", ".join(unknown_goal_ids)))

    know = bullets(sec.get("What We Know", []))
    add(f"What We Know: 1 to {MAX_KNOW} bullets", 1 <= len(know) <= MAX_KNOW, f"{len(know)} bullets")
    not_copied = [b for b in know if b not in d["know"]]
    detail = ""
    if not_copied:
        b = not_copied[0]
        where = ctx_bullets.get(b)
        detail = (f"from {where}, not quotable here: {b[:50]}" if where
                  else f"not a context bullet word for word: {b[:60]}")
    add("What We Know: tagged context facts, word for word", not not_copied, detail)
    stray = [ln for ln in sec.get("What We Know", []) if ln.strip() and not ln.startswith("- ")]
    add("What We Know: bullets only", not stray, stray[0][:60] if stray else "")

    seen: dict[str, int] = {}
    placement_errors, group_errors, empty_text = [], [], []
    group_of = {i: tuple(g) for g in d["groups"] for i in g}

    def grouped(ids: list[str]) -> bool:
        """A line's ids are one or more whole printed groups, each group's ids in printed order."""
        groups = []
        for i in ids:
            g = group_of.get(i)
            if g is None:
                return True  # reported as unknown elsewhere
            if g not in groups:
                groups.append(g)
        return all([i for i in ids if group_of.get(i) == g] == list(g) for g in groups)
    q_lines = [ln.strip() for ln in sec.get("Questions to Settle", []) if ln.strip()]
    for ln in q_lines:
        m = re.match(r"^\d+\.\s+(.*)$", ln)
        if not m:
            placement_errors.append(f"not a numbered line: {ln[:50]}")
            continue
        im = IDS_RE.match(m.group(1))
        if not im:
            placement_errors.append(f"no (ids) at the start: {ln[:50]}")
            continue
        ids = im.group(1).split(", ")
        if len(im.group(2).split()) < 4:
            empty_text.append(ln[:50])
        for i in ids:
            seen[i] = seen.get(i, 0) + 1
            if i in d["items"] and d["items"][i]["place"] != "questions":
                placement_errors.append(f"{i} belongs in Scope to Confirm")
        if not grouped(ids):
            group_errors.append(f"({', '.join(ids)})")

    s_lines = [ln.strip() for ln in sec.get("Scope to Confirm", []) if ln.strip()]
    add("Scope to Confirm: page count and paid media lines", s_lines[:2] == d["scope_lines"],
        f"expected {d['scope_lines']}")
    for ln in s_lines[2:]:
        im = IDS_RE.match(ln[2:]) if ln.startswith("- ") else None
        if not im:
            placement_errors.append(f"scope line without (ids): {ln[:50]}")
            continue
        ids = im.group(1).split(", ")
        if len(im.group(2).split()) < 4:
            empty_text.append(ln[:50])
        for i in ids:
            seen[i] = seen.get(i, 0) + 1
            if i in d["items"] and d["items"][i]["place"] != "scope":
                placement_errors.append(f"{i} belongs in Questions to Settle")
        if not grouped(ids):
            group_errors.append(f"({', '.join(ids)})")

    missing_ids = [i for i in d["items"] if seen.get(i, 0) == 0]
    dup_ids = [i for i, n in seen.items() if n > 1]
    unknown = [i for i in seen if i not in d["items"]]
    add("every open item appears", not missing_ids, ", ".join(missing_ids))
    add("no open item appears twice", not dup_ids, ", ".join(dup_ids))
    add("no closed or unknown ids", not unknown, ", ".join(unknown))
    add("ids keep the groups printed by items", not group_errors, ", ".join(group_errors))
    add("items in the right section", not placement_errors, "; ".join(placement_errors[:3]))
    add("each open item line says something", not empty_text, "; ".join(empty_text[:2]))

    a_lines = [ln.strip() for ln in sec.get("Access to Confirm", []) if ln.strip()]
    add("Access to Confirm matches the missing items", a_lines == d["access"],
        f"expected {len(d['access'])} lines from {d['access_source']}, found {len(a_lines)}")
    rel = [ln for ln in sec.get("Relationship Notes", []) if ln.strip()]
    add("Relationship Notes left blank", not rel, rel[0][:60] if rel else "")

    return rows, all(ok for _, ok, _ in rows)


def cmd_check(folder: Path) -> int:
    rows, ok = check(folder)
    print("| Check | Result | Detail |")
    print("|---|---|---|")
    for name, good, detail in rows:
        print(f"| {name} | {'PASS' if good else 'FAIL'} | {detail if not good else ''} |")
    print(f"RESULT: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


OUTLINE_KEYS = ["Client:", "## Scope Summary", "## Open Items", "## Checklist Coverage",
                "SOW pages:", "GAP:", "CONFLICT:", "Answer:"]


def cmd_outline(folder: Path) -> int:
    slug, ctx = folder_files(folder)
    text = read(ctx)
    sec = sections(text)
    qs, cov = parse_gap_questions(folder / f"{slug}-gap-questions.md")
    all_b = [b for h in CONTEXT_HEADINGS if h in sec for b in bullets(sec[h])]
    scope = sec.get("Scope Summary", [])
    out = {
        "Client:": client_name(text),
        "## Scope Summary": [ln for ln in scope if ln.strip()],
        "## Open Items": bullets(sec.get("Open Items", [])),
        "## Checklist Coverage": cov,
        "SOW pages:": next((ln[len("SOW pages:"):].strip() for ln in scope if ln.startswith("SOW pages:")), None),
        "GAP:": [b for b in all_b if b.startswith("GAP:")],
        "CONFLICT:": [b for b in all_b if b.startswith("CONFLICT:")],
        "Answer:": {str(n): q["answer"] for n, q in sorted(qs.items())},
    }
    print(json.dumps(out, indent=2))
    return 0


def cmd_validate(path: Path) -> int:
    data = json.loads(read(path))
    errs = [f"missing key {k}" for k in OUTLINE_KEYS if k not in data]
    if not errs:
        if not isinstance(data["SOW pages:"], str) or not data["SOW pages:"]:
            errs.append("SOW pages: must be a non-empty string")
        if not all(re.match(r"^R\d+\b", b) for b in data["## Open Items"]):
            errs.append("every Open Items bullet must start with an R id")
        if not all(re.fullmatch(r"R\d+", k) for k in data["## Checklist Coverage"]):
            errs.append("Checklist Coverage keys must be R ids")
        if not all(k.isdigit() for k in data["Answer:"]):
            errs.append("Answer: keys must be question numbers")
    for e in errs:
        print(e, file=sys.stderr)
    if errs:
        return 1
    print(f"OUTLINE OK: {len(data['## Open Items'])} open items, {len(data['Answer:'])} questions")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[0] not in ("items", "check", "outline"):
        print(__doc__, file=sys.stderr)
        return 2
    try:
        if argv[0] == "outline" and argv[1] == "--validate":
            return cmd_validate(Path(argv[2]))
        folder = Path(argv[1].rstrip("/"))
        return {"items": cmd_items, "check": cmd_check, "outline": cmd_outline}[argv[0]](folder)
    except Fail as e:
        print(f"ERROR: {e}", file=sys.stderr)
        if argv[0] == "check":
            print("RESULT: FAIL")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
