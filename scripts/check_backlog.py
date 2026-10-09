#!/usr/bin/env python3
"""Backlog gate for skills_backlog.json.

Schema (list under "skills"):
  id          kebab-case, equals the skill folder name
  summary     one line, human-written
  archetype   free label (pipeline-stage, audit, template-generator, ...)
  depends_on  [ids] that must pass first
  passes      false until ALL gates below pass; the agent may only flip this field (and `notes`)
  notes       free text

A skill may claim "passes": true only if:
  - skills/<id>/ exists and validates with --strict
  - evals exist (trigger.json + outputs.json) and meet the minimums
  - every contract touching it passes
  - every skill in depends_on also passes
The gate checks the *claim*, so flipping a flag cannot pass without evidence on disk.

Usage:
  check_backlog.py                 verify structure and all claims
  check_backlog.py --next          print the next buildable skill (deps satisfied) or 'none'
  check_backlog.py --status        one-line-per-skill status table
  check_backlog.py --against-git   additionally require that only passes/notes changed vs HEAD
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_contracts as CC  # noqa: E402
import common as C  # noqa: E402
import validate_skill as V  # noqa: E402

MUTABLE = {"passes", "notes"}
REQUIRED = {"id", "summary", "depends_on", "passes"}


def load_backlog() -> tuple[list[dict], str | None]:
    if not C.BACKLOG.exists():
        return [], "skills_backlog.json is missing."
    try:
        data = C.load_json(C.BACKLOG)
    except json.JSONDecodeError as e:
        return [], f"skills_backlog.json is not valid JSON: {e}"
    skills = data.get("skills")
    if not isinstance(skills, list):
        return [], "skills_backlog.json must have a top-level 'skills' list."
    return skills, None


def immutable_diff(old: list[dict], new: list[dict]) -> list[str]:
    """Differences between two backlogs outside the mutable fields (used by hook and gate)."""
    problems = []
    o = {s.get("id"): s for s in old}
    n = {s.get("id"): s for s in new}
    for sid in o.keys() - n.keys():
        problems.append(f"skill '{sid}' was removed from the backlog.")
    for sid in n.keys() - o.keys():
        problems.append(f"skill '{sid}' was added to the backlog.")
    for sid in o.keys() & n.keys():
        for k in (set(o[sid]) | set(n[sid])) - MUTABLE:
            if o[sid].get(k) != n[sid].get(k):
                problems.append(f"'{sid}'.{k} changed ({o[sid].get(k)!r} -> {n[sid].get(k)!r}); only {sorted(MUTABLE)} may change.")
    if [s.get("id") for s in old] != [s.get("id") for s in new] and not problems:
        problems.append("backlog order changed.")
    return problems


def gate(skill: dict, by_id: dict[str, dict]) -> C.Report:
    sid = skill["id"]
    r = C.Report(f"backlog:{sid}")
    d = C.SKILLS_DIR / sid
    if not d.is_dir():
        r.error(f"claims passes=true but skills/{sid}/ does not exist.")
        return r
    rep = V.validate(d, strict=True)
    for e in rep.errors:
        r.error(f"claims passes=true but strict validation fails: {e}")
    for p, c in CC.select(CC.load_contracts(), skill=sid):
        cr = CC.check_contract(p, c)
        for e in cr.errors:
            r.error(f"claims passes=true but {cr.subject} fails: {e}")
    for dep in skill.get("depends_on", []):
        if not by_id.get(dep, {}).get("passes"):
            r.error(f"claims passes=true but depends_on '{dep}' does not pass yet.")
    return r


def next_buildable(skills: list[dict]) -> dict | None:
    by_id = {s["id"]: s for s in skills}
    for s in skills:
        if s.get("passes"):
            continue
        if all(by_id.get(d, {}).get("passes") for d in s.get("depends_on", [])):
            return s
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--next", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--against-git", action="store_true")
    args = ap.parse_args()

    skills, err = load_backlog()
    if err:
        print(f"  ERROR  backlog: {err}")
        return 1

    if args.next:
        nxt = next_buildable(skills)
        if nxt:
            deps = ", ".join(nxt.get("depends_on", [])) or "none"
            print(f"{nxt['id']}: {nxt.get('summary', '')} (archetype: {nxt.get('archetype', '-')}; depends on: {deps})")
        else:
            blocked = [s["id"] for s in skills if not s.get("passes")]
            print("none" if not blocked else f"none buildable (blocked: {', '.join(blocked)})")
        return 0

    if args.status:
        for s in skills:
            mark = "PASS" if s.get("passes") else "todo"
            print(f"  [{mark}] {s['id']} - {s.get('summary', '')}")
        return 0

    reports: list[C.Report] = []
    structure = C.Report("backlog")
    ids = [s.get("id") for s in skills]
    if len(ids) != len(set(ids)):
        structure.error("duplicate ids in backlog.")
    for s in skills:
        missing = REQUIRED - set(s)
        if missing:
            structure.error(f"entry {s.get('id', '?')} is missing fields: {sorted(missing)}.")
        if not isinstance(s.get("passes"), bool):
            structure.error(f"'{s.get('id', '?')}'.passes must be true or false.")
        for dep in s.get("depends_on", []) or []:
            if dep not in ids:
                structure.error(f"'{s.get('id')}' depends on unknown skill '{dep}'.")
    reports.append(structure)

    if structure.ok:
        by_id = {s["id"]: s for s in skills}
        for s in skills:
            if s["passes"]:
                reports.append(gate(s, by_id))

    if args.against_git:
        g = C.Report("backlog-diff")
        if C.is_git_repo() and C.has_commits():
            rc, out = C.git("show", "HEAD:skills_backlog.json")
            if rc == 0:
                try:
                    for p in immutable_diff(json.loads(out).get("skills", []), skills):
                        g.error(p + " Backlog structure is human-owned; ask the user to change it.")
                except json.JSONDecodeError:
                    pass
        reports.append(g)

    C.print_reports(reports)
    return 0 if all(r.ok for r in reports) else 1


if __name__ == "__main__":
    sys.exit(main())
