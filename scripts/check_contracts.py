#!/usr/bin/env python3
"""Contract tests between chained skills (producer -> consumer).

A contract lives in contracts/<name>.json:

{
  "name": "topic-map-to-brief",
  "version": 1,
  "producer": "example-topic-map",
  "consumer": "example-brief-writer",
  "format": "csv",                                  # csv | json
  "fixture": "fixtures/contracts/topic-map.csv",    # frozen sample of the producer's output
  "columns": ["topic", "keyword", "page_type"],     # csv: exact header, in order
  "required_non_empty": ["topic", "keyword"],       # csv: cells that must be filled
  "enums": {"page_type": ["service", "blog"]},      # csv: allowed values per column
  "min_rows": 1,
  "keys": ["..."],                                  # json: required keys (top-level or per item)
  "producer_cmd": "python3 skills/x/scripts/make.py fixtures/contracts/seeds.txt",
  "producer_output_equals_fixture": true,           # run producer_cmd, require stdout == fixture
  "consumer_cmd": "python3 skills/y/scripts/use.py {fixture}"   # must exit 0 on the fixture
}

What is checked:
  1. fixture exists and matches the declared shape
  2. both SKILL.md files (and references/) mention every column/key in `backticks`,
     so renaming a column in docs but not in the contract (or vice versa) is caught
  3. producer_cmd output matches the fixture (optional) and the declared header
  4. consumer_cmd accepts the fixture

Usage:
  check_contracts.py --all
  check_contracts.py --skill <name>      contracts where <name> is producer or consumer
  check_contracts.py --file <path>       contract file, or any file inside a producer/consumer skill
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402


def load_contracts() -> list[tuple[Path, dict]]:
    out = []
    if C.CONTRACTS_DIR.is_dir():
        for p in sorted(C.CONTRACTS_DIR.glob("*.json")):
            try:
                out.append((p, C.load_json(p)))
            except json.JSONDecodeError as e:
                out.append((p, {"_invalid": str(e)}))
    return out


def skill_text(skill: str) -> str:
    d = C.SKILLS_DIR / skill
    chunks = []
    if (d / "SKILL.md").exists():
        chunks.append(C.read_text(d / "SKILL.md"))
    ref = d / "references"
    if ref.is_dir():
        for f in sorted(ref.rglob("*.md")):
            chunks.append(C.read_text(f))
    return "\n".join(chunks)


def run_cmd(cmd: str, fixture_rel: str) -> subprocess.CompletedProcess:
    argv = shlex.split(cmd.replace("{fixture}", fixture_rel))
    if argv and argv[0] in ("python", "python3"):
        argv[0] = sys.executable
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    return subprocess.run(argv, cwd=C.ROOT, capture_output=True, text=True, timeout=60, env=env)


def norm(s: str) -> str:
    return s.replace("\r\n", "\n").strip() + "\n"


def check_csv(c: dict, text: str, r: C.Report, label: str) -> None:
    rows = list(csv.reader(io.StringIO(text)))
    if not rows:
        r.error(f"{label} is empty.")
        return
    header, data = rows[0], rows[1:]
    want = c.get("columns", [])
    if want and header != want:
        missing = [x for x in want if x not in header]
        extra = [x for x in header if x not in want]
        r.error(
            f"{label} header {header} does not match contract columns {want}"
            + (f" (missing: {missing})" if missing else "")
            + (f" (unexpected: {extra})" if extra else "")
            + (" (same columns, different order)" if not missing and not extra else "")
            + ". If the schema change is intentional, ask the user to approve updating the contract."
        )
        return
    if len(data) < c.get("min_rows", 1):
        r.error(f"{label} has {len(data)} data rows; contract requires at least {c.get('min_rows', 1)}.")
    idx = {h: i for i, h in enumerate(header)}
    for ln, row in enumerate(data, 2):
        if len(row) != len(header):
            r.error(f"{label} line {ln} has {len(row)} cells; header has {len(header)}.")
            continue
        for col in c.get("required_non_empty", []):
            if col in idx and not row[idx[col]].strip():
                r.error(f"{label} line {ln}: column '{col}' must not be empty.")
        for col, allowed in c.get("enums", {}).items():
            if col in idx and row[idx[col]] not in allowed:
                r.error(f"{label} line {ln}: '{row[idx[col]]}' is not an allowed value for '{col}' ({allowed}).")


def check_json(c: dict, text: str, r: C.Report, label: str) -> None:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        r.error(f"{label} is not valid JSON: {e}")
        return
    items = data if isinstance(data, list) else [data]
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            r.error(f"{label} item {i} is not an object.")
            continue
        for k in c.get("keys", []):
            if k not in item:
                r.error(f"{label} item {i} is missing key '{k}'.")


def check_contract(path: Path, c: dict) -> C.Report:
    name = c.get("name") or path.stem
    r = C.Report(f"contract:{name}")
    if "_invalid" in c:
        r.error(f"{path.name} is not valid JSON: {c['_invalid']}")
        return r
    for key in ("producer", "consumer", "format", "fixture"):
        if key not in c:
            r.error(f"{path.name} is missing required key '{key}'.")
    if not r.ok:
        return r
    fmt = c["format"]
    if fmt not in ("csv", "json"):
        r.error(f"unsupported format '{fmt}' (use csv or json).")
        return r
    for role in ("producer", "consumer"):
        if not (C.SKILLS_DIR / c[role]).is_dir():
            r.error(f"{role} skill '{c[role]}' does not exist under skills/.")
    fixture = C.ROOT / c["fixture"]
    if not fixture.exists():
        r.error(f"fixture '{c['fixture']}' does not exist.")
        return r
    if not r.ok:
        return r
    ftext = C.read_text(fixture)
    (check_csv if fmt == "csv" else check_json)(c, ftext, r, f"fixture {c['fixture']}")

    # docs <-> contract sync
    fields = c.get("columns") or c.get("keys") or []
    for role in ("producer", "consumer"):
        txt = skill_text(c[role])
        for f in fields:
            if f"`{f}`" not in txt:
                r.error(
                    f"{role} skill '{c[role]}' never mentions `{f}` in backticks in SKILL.md/references. "
                    f"Contract '{name}' says it is part of the interface; document it (or update the contract with user approval)."
                )

    # live producer
    if c.get("producer_cmd"):
        try:
            p = run_cmd(c["producer_cmd"], c["fixture"])
            if p.returncode != 0:
                r.error(f"producer_cmd failed (exit {p.returncode}): {p.stderr.strip()[:300]}")
            else:
                if fmt == "csv":
                    check_csv(c, p.stdout, r, "producer_cmd output")
                else:
                    check_json(c, p.stdout, r, "producer_cmd output")
                if c.get("producer_output_equals_fixture") and norm(p.stdout) != norm(ftext):
                    r.error(
                        "producer_cmd output differs from the frozen fixture. If the producer changed on purpose, "
                        "show the diff to the user and ask them to re-approve the fixture."
                    )
        except (OSError, subprocess.TimeoutExpired) as e:
            r.error(f"producer_cmd could not run: {e}")

    # live consumer
    if c.get("consumer_cmd"):
        try:
            p = run_cmd(c["consumer_cmd"], c["fixture"])
            if p.returncode != 0:
                r.error(
                    f"consumer_cmd rejected the producer's fixture (exit {p.returncode}): {p.stderr.strip()[:300]}"
                )
            elif not p.stdout.strip():
                r.error("consumer_cmd produced no output for the fixture.")
        except (OSError, subprocess.TimeoutExpired) as e:
            r.error(f"consumer_cmd could not run: {e}")
    return r


def select(contracts, skill: str | None = None, file: str | None = None):
    if skill:
        return [(p, c) for p, c in contracts if skill in (c.get("producer"), c.get("consumer"))]
    if file:
        fp = Path(file)
        fp = fp if fp.is_absolute() else C.ROOT / fp
        try:
            rel = fp.resolve().relative_to(C.ROOT)
        except ValueError:
            return []
        if rel.parts and rel.parts[0] == "contracts":
            return [(p, c) for p, c in contracts if p.resolve() == fp.resolve()]
        if rel.parts and rel.parts[0] == "fixtures":
            return [(p, c) for p, c in contracts if (C.ROOT / c.get("fixture", "")).resolve() == fp.resolve()]
        sk = C.skill_for_path(fp)
        if sk:
            return [(p, c) for p, c in contracts if sk.name in (c.get("producer"), c.get("consumer"))]
    return []


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--skill")
    ap.add_argument("--file")
    args = ap.parse_args()
    contracts = load_contracts()
    if args.skill:
        chosen = select(contracts, skill=args.skill)
    elif args.file:
        chosen = select(contracts, file=args.file)
    else:
        chosen = contracts
    if not chosen:
        print("no matching contracts")
        return 0
    reports = [check_contract(p, c) for p, c in chosen]
    C.print_reports(reports)
    return 0 if all(r.ok for r in reports) else 1


if __name__ == "__main__":
    sys.exit(main())
