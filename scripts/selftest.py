#!/usr/bin/env python3
"""Self-test: do the sensors actually fire?

Böckeler's open question for harness engineering: "if sensors never fire, is that a sign of high
quality or inadequate detection?" This script answers it for THIS harness. It generates a tiny
synthetic skill pair (a producer and a consumer joined by a contract) in a temp repo, injects one
known defect at a time, and asserts that the right gate turns red with a useful message (and that
a clean copy stays green). It never reads `skills/`, so it works on an empty repo. Run it after
touching any script, hook or rule. init.sh runs it at the start of every session.

  selftest.py          verbose
  selftest.py --quiet  failures and summary only
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
SCRIPTS = KIT / "scripts"
HOOKS = KIT / ".claude" / "hooks"
sys.path.insert(0, str(SCRIPTS))

results: list[tuple[str, bool, str]] = []
_tmp_roots: list[Path] = []


# --------------------------------------------------------------------------- #
# synthetic fixture: aa-producer -> bb-consumer, joined by contracts/aa-to-bb.json
# --------------------------------------------------------------------------- #
PRODUCER = "aa-producer"
CONSUMER = "bb-consumer"
UNBUILT = "cc-outline"
TM = f"skills/{PRODUCER}/SKILL.md"
BW = f"skills/{CONSUMER}/SKILL.md"
PRODUCER_SCRIPT = f"skills/{PRODUCER}/scripts/make.py"
CONSUMER_SCRIPT = f"skills/{CONSUMER}/scripts/use.py"
CONTRACT = "contracts/aa-to-bb.json"
CSV_FIXTURE = "fixtures/contracts/inventory.csv"
BOUNDARY = f" Do NOT use for writing part sheets from an existing inventory CSV (use {CONSUMER}) or for ordering parts."

PRODUCER_MD = f"""---
name: {PRODUCER}
description: Turn a plain-text list of part names into an inventory CSV, i.e. a spreadsheet of parts with a kind on each row. Use when the user provides part names and wants an inventory CSV or parts spreadsheet.{BOUNDARY}
---

# Producer

Turns part names into the CSV that `{CONSUMER}` consumes.

## Output
A CSV with exactly these columns, in this order: `item`, `kind`.

## Steps
1. Run `python3 scripts/make.py <parts.txt> > inventory.csv`.
2. Read `references/kinds.md` if a part's `kind` looks wrong.

## Rules
- Never rename or reorder columns.
"""

PRODUCER_REF = "# Kinds\n\n`kind` is `alpha` for single parts and `beta` for plural part names.\n"

PRODUCER_PY = '''#!/usr/bin/env python3
"""Turn a plain-text list of part names into an inventory CSV on stdout."""
import csv
import sys


def kind(item: str) -> str:
    if item.endswith("s"):
        return "beta"
    return "alpha"


def main() -> int:
    items = [l.strip() for l in open(sys.argv[1], encoding="utf-8") if l.strip() and not l.startswith("#")]
    w = csv.writer(sys.stdout, lineterminator="\\n")
    w.writerow(["item", "kind"])
    for it in items:
        w.writerow([it, kind(it)])
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

CONSUMER_MD = f"""---
name: {CONSUMER}
description: Turn an inventory CSV of parts (columns item, kind) into one markdown part sheet per row. Use when the user has an inventory CSV, or the output of {PRODUCER}, and asks for part sheets. Do NOT use to build the inventory CSV from part names (use {PRODUCER}) or to order parts.
---

# Consumer

Consumes the CSV produced by `{PRODUCER}`.

## Input
A CSV whose header is exactly `item`, `kind`. If it does not match, stop and tell the user.

## Steps
1. Run `python3 scripts/use.py <inventory.csv>`.
2. Read `references/sheet.md` to change the sheet layout.

## Rules
- One sheet per row.
"""

CONSUMER_REF = "# Sheet layout\n\nEach sheet shows the `item` and its `kind`.\n"

CONSUMER_PY = '''#!/usr/bin/env python3
"""Print one part sheet per row of an inventory CSV; exit 1 if the header is wrong."""
import csv
import sys

COLUMNS = ["item", "kind"]


def main() -> int:
    with open(sys.argv[1], newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    if not rows or rows[0] != COLUMNS:
        print(f"expected header {COLUMNS}, got {rows[0] if rows else 'nothing'}", file=sys.stderr)
        return 1
    for item, kind in rows[1:]:
        print(f"# {item}\\nkind: {kind}\\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

SEEDS = "widget\nbolts\ngear\n"
CSV_TEXT = "item,kind\nwidget,alpha\nbolts,beta\ngear,alpha\n"

CONTRACT_JSON = {
    "name": "aa-to-bb",
    "version": 1,
    "producer": PRODUCER,
    "consumer": CONSUMER,
    "format": "csv",
    "fixture": CSV_FIXTURE,
    "columns": ["item", "kind"],
    "required_non_empty": ["item"],
    "enums": {"kind": ["alpha", "beta"]},
    "min_rows": 1,
    "producer_cmd": f"python3 {PRODUCER_SCRIPT} fixtures/contracts/parts.txt",
    "producer_output_equals_fixture": True,
    "consumer_cmd": f"python3 {CONSUMER_SCRIPT} {{fixture}}",
}

PRODUCER_TRIGGER = {
    "should_trigger": [
        "Make an inventory CSV from the part names in parts.txt",
        "Here are some part names: widget, bolts, gear. Build me an inventory spreadsheet.",
        "Turn this list of parts into a CSV with a kind per row",
        "I have part names in a text file, give me the inventory CSV",
        "Classify these part names into an inventory spreadsheet",
    ],
    "should_not_trigger": [
        "Write part sheets for each row of inventory.csv",
        "Turn the inventory CSV into sheets a technician can read",
        "Order ten more widgets from the supplier",
        "Proofread this paragraph for me",
        "Make a chart of my sales",
        "What is the capital of France?",
    ],
}

CONSUMER_TRIGGER = {
    "should_trigger": [
        "Write part sheets for each row of inventory.csv",
        "I have the inventory CSV from earlier. Generate a sheet for every part.",
        "Turn this inventory CSV into part sheets",
        "Make a sheet per row of this CSV: item, kind",
        "Prepare part sheets for all the alpha parts in the inventory",
    ],
    "should_not_trigger": [
        "Here are part names: widget, bolts. Build me an inventory CSV.",
        "Classify these part names into a spreadsheet",
        "Order ten more widgets from the supplier",
        "Proofread this paragraph for me",
        "Brief me on today's top news",
        "Make a chart of my sales",
    ],
}

PRODUCER_OUTPUTS = {
    "cases": [
        {
            "id": "basic-map",
            "prompt": f"Use the {PRODUCER} skill to turn parts.txt into inventory.csv.",
            "fixtures": [{"src": f"fixtures/{PRODUCER}/parts.txt", "dest": "parts.txt"}],
            "assertions": [
                {"type": "csv_columns", "path": "inventory.csv", "columns": ["item", "kind"]},
                {"type": "csv_enum", "path": "inventory.csv", "column": "kind", "values": ["alpha", "beta"]},
            ],
        }
    ]
}

CONSUMER_OUTPUTS = {
    "cases": [
        {
            "id": "basic-sheets",
            "prompt": f"Use the {CONSUMER} skill to write part sheets for inventory.csv.",
            "fixtures": [{"src": f"fixtures/{CONSUMER}/inventory.csv", "dest": "inventory.csv"}],
            "assertions": [{"type": "contains", "target": "stdout", "text": "widget"}],
        }
    ]
}

BACKLOG = {
    "skills": [
        {"id": PRODUCER, "summary": "Turn part names into an inventory CSV", "archetype": "pipeline-stage", "depends_on": [], "passes": True, "notes": ""},
        {"id": CONSUMER, "summary": "Turn an inventory CSV into part sheets", "archetype": "pipeline-stage", "depends_on": [PRODUCER], "passes": True, "notes": ""},
        {"id": UNBUILT, "summary": "Turn one part sheet into an outline", "archetype": "pipeline-stage", "depends_on": [CONSUMER], "passes": False, "notes": ""},
    ]
}


def write(root: Path, rel: str, content) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content if isinstance(content, str) else json.dumps(content, indent=2) + "\n", encoding="utf-8")


def base_tree() -> Path:
    """A self-contained mini repo: two chained skills, their evals, fixtures, contract and backlog."""
    base = Path(tempfile.mkdtemp(prefix="selftest-base-"))
    _tmp_roots.append(base)
    write(base, TM, PRODUCER_MD)
    write(base, f"skills/{PRODUCER}/references/kinds.md", PRODUCER_REF)
    write(base, PRODUCER_SCRIPT, PRODUCER_PY)
    write(base, BW, CONSUMER_MD)
    write(base, f"skills/{CONSUMER}/references/sheet.md", CONSUMER_REF)
    write(base, CONSUMER_SCRIPT, CONSUMER_PY)
    write(base, f"evals/{PRODUCER}/trigger.json", PRODUCER_TRIGGER)
    write(base, f"evals/{PRODUCER}/outputs.json", PRODUCER_OUTPUTS)
    write(base, f"evals/{CONSUMER}/trigger.json", CONSUMER_TRIGGER)
    write(base, f"evals/{CONSUMER}/outputs.json", CONSUMER_OUTPUTS)
    write(base, f"fixtures/{PRODUCER}/parts.txt", SEEDS)
    write(base, f"fixtures/{CONSUMER}/inventory.csv", CSV_TEXT)
    write(base, "fixtures/contracts/parts.txt", SEEDS)
    write(base, CSV_FIXTURE, CSV_TEXT)
    write(base, CONTRACT, CONTRACT_JSON)
    write(base, "skills_backlog.json", BACKLOG)
    write(base, "CLAUDE.md", "# test\n")
    write(base, "progress.md", "# progress\n- baseline\n")
    return base


BASE: Path | None = None


# --------------------------------------------------------------------------- #
# plumbing
# --------------------------------------------------------------------------- #
def fresh(git: bool = False) -> Path:
    root = Path(tempfile.mkdtemp(prefix="selftest-"))
    _tmp_roots.append(root)
    shutil.rmtree(root)
    shutil.copytree(BASE, root)
    if git:
        genv = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
        for cmd in (["git", "init", "-q"], ["git", "add", "-A"], ["git", "-c", "commit.gpgsign=false", "commit", "-qm", "baseline"]):
            subprocess.run(cmd, cwd=root, env=genv, capture_output=True, check=True)
    return root


def run(script: str, *args: str, root: Path, stdin: str | None = None, hook: bool = False, env: dict | None = None) -> tuple[int, str]:
    path = (HOOKS if hook else SCRIPTS) / script
    e = dict(os.environ, HARNESS_ROOT=str(root), PYTHONDONTWRITEBYTECODE="1")
    e.pop("CLAUDE_PROJECT_DIR", None)
    e.pop("HARNESS_UNLOCK", None)
    if env:
        e.update(env)
    p = subprocess.run([sys.executable, str(path), *args], cwd=root, capture_output=True, text=True, input=stdin, env=e, timeout=120)
    return p.returncode, p.stdout + p.stderr


def edit(root: Path, rel: str, old: str, new: str) -> None:
    p = root / rel
    s = p.read_text()
    assert old in s, f"selftest bug: {old!r} not found in {rel}"
    p.write_text(s.replace(old, new, 1))


def edit_all(root: Path, rels: list[str], old: str, new: str) -> None:
    """Replace every occurrence in each file (docs mention contract columns in several places)."""
    hit = False
    for rel in rels:
        p = root / rel
        s = p.read_text()
        if old in s:
            p.write_text(s.replace(old, new))
            hit = True
    assert hit, f"selftest bug: {old!r} not found in any of {rels}"


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, bool(ok), detail))


def expect(name: str, got: tuple[int, str], rc: int, needle: str | None = None) -> None:
    code, out = got
    ok = code == rc and (needle is None or needle.lower() in out.lower())
    check(name, ok, "" if ok else f"expected rc={rc}" + (f" and output containing {needle!r}" if needle else "") + f"; got rc={code}; output: {out.strip()[-300:]}")


def hook_input(tool: str, **tool_input) -> str:
    return json.dumps({"tool_name": tool, "tool_input": tool_input, "session_id": "t1", "hook_event_name": "x"})


VALIDATE = ("validate_skill.py", "--all", "--strict", "--quiet")


# --------------------------------------------------------------------------- #
# tests
# --------------------------------------------------------------------------- #
def t_baseline() -> None:
    r = fresh()
    expect("baseline: strict validation is green", run(*VALIDATE, root=r), 0)
    expect("baseline: contracts are green", run("check_contracts.py", "--all", root=r), 0)
    expect("baseline: overlap check is green", run("check_overlap.py", "--quiet", root=r), 0)
    expect("baseline: backlog gate is green", run("check_backlog.py", root=r), 0)
    expect("baseline: --next names the unbuilt skill", run("check_backlog.py", "--next", root=r), 0, UNBUILT)
    e = fresh()
    for item in ("skills", "evals", "contracts", "fixtures"):
        shutil.rmtree(e / item)
        (e / item).mkdir()
    write(e, "skills_backlog.json", {"skills": []})
    expect("baseline: an empty repo (no skills, empty backlog) is green", run(*VALIDATE, root=e), 0, "no skills")
    expect("baseline: empty backlog -> --next prints none", run("check_backlog.py", "--next", root=e), 0, "none")


def t_validator() -> None:
    def case(label: str, mutate, needle: str, strict: bool = True, rc: int = 1) -> None:
        r = fresh()
        mutate(r)
        args = ("validate_skill.py", "--all") + (("--strict",) if strict else ())
        expect(f"validator: {label}", run(*args, root=r), rc, needle)

    case("uppercase name", lambda r: edit(r, TM, f"name: {PRODUCER}", "name: Aa-Producer"), "kebab-case")
    case("name differs from folder", lambda r: edit(r, TM, f"name: {PRODUCER}", "name: something-else"), "must match the folder")
    case("name contains 'claude'", lambda r: (edit(r, TM, f"name: {PRODUCER}", "name: claude-producer")), "must not contain 'claude'")
    case("description over 1024 chars", lambda r: edit(r, TM, "Do NOT use for", "x" * 1100 + " Do NOT use for"), "limit is 1024")
    case("angle brackets in description", lambda r: edit(r, TM, "Turn a plain-text", "Turn a <b>plain-text"), "angle brackets")
    case("missing description", lambda r: edit(r, TM, "description:", "descriptionx:"), "missing 'description'")
    case("no frontmatter", lambda r: (r / TM).write_text("# no frontmatter\n"), "no YAML frontmatter")
    case("reference to a missing file", lambda r: edit(r, TM, "## Rules", "See references/nope.md for more.\n\n## Rules"), "does not exist")
    case("hard-coded environment path", lambda r: edit(r, TM, "## Rules", "Files live in /mnt/skills/user/x.\n\n## Rules"), "hard-codes")
    case("environment path with allow marker", lambda r: edit(r, TM, "## Rules", "Files live in /mnt/skills/user/x. harness:allow-path\n\n## Rules"), "", rc=0)
    case("python syntax error in script", lambda r: (r / PRODUCER_SCRIPT).write_text("def broken(:\n"), "syntax error")
    case("invalid JSON asset", lambda r: (r / f"skills/{PRODUCER}/references/x.json").write_text("{nope"), "not valid JSON")
    case("SKILL.md body over the line limit", lambda r: edit(r, TM, "## Rules", "line\n" * 520 + "\n## Rules"), "lines (limit")
    case("TODO placeholder fails strict", lambda r: edit(r, TM, "## Rules", "TODO write this part\n\n## Rules"), "placeholder")
    case("TODO placeholder only warns when not strict", lambda r: edit(r, TM, "## Rules", "TODO write this part\n\n## Rules"), "placeholder", strict=False, rc=0)
    case("missing trigger evals fails strict", lambda r: (r / f"evals/{PRODUCER}/trigger.json").unlink(), "trigger.json is missing")
    case("missing trigger evals only warns when not strict", lambda r: (r / f"evals/{PRODUCER}/trigger.json").unlink(), "trigger.json is missing", strict=False, rc=0)
    case("missing output evals fails strict", lambda r: (r / f"evals/{PRODUCER}/outputs.json").unlink(), "outputs.json is missing")

    def few(r: Path) -> None:
        p = r / f"evals/{PRODUCER}/trigger.json"
        d = json.loads(p.read_text())
        d["should_not_trigger"] = d["should_not_trigger"][:2]
        p.write_text(json.dumps(d))

    case("too few should_not_trigger prompts", few, "need at least")

    def dup(r: Path) -> None:
        p = r / f"evals/{PRODUCER}/trigger.json"
        d = json.loads(p.read_text())
        d["should_not_trigger"][0] = d["should_trigger"][0]
        p.write_text(json.dumps(d))

    case("duplicate trigger prompts", dup, "duplicate")

    def dupname(r: Path) -> None:
        shutil.copytree(r / f"skills/{CONSUMER}", r / "skills/zz-copy")
        edit(r, "skills/zz-copy/SKILL.md", f"name: {CONSUMER}", f"name: {PRODUCER}")

    case("duplicate frontmatter names", dupname, "must be unique", strict=False)


def t_contracts() -> None:
    def case(label: str, mutate, needle: str, rc: int = 1) -> None:
        r = fresh()
        mutate(r)
        expect(f"contracts: {label}", run("check_contracts.py", "--all", root=r), rc, needle)

    case("fixture column order changed", lambda r: edit(r, CSV_FIXTURE, "item,kind", "kind,item"), "same columns, different order")
    case("fixture missing a column", lambda r: edit(r, CSV_FIXTURE, "item,kind", "item"), "missing: ['kind']")
    case("fixture value outside enum", lambda r: edit(r, CSV_FIXTURE, "widget,alpha", "widget,gamma"), "not an allowed value")
    case("fixture has an empty required cell", lambda r: edit(r, CSV_FIXTURE, "widget,alpha", ",alpha"), "must not be empty")
    case("consumer docs drop a contract column", lambda r: edit_all(r, [BW, f"skills/{CONSUMER}/references/sheet.md"], "`kind`", "kind"), "never mentions `kind`")
    case("producer docs drop a contract column", lambda r: edit_all(r, [TM, f"skills/{PRODUCER}/references/kinds.md"], "`item`", "item"), "never mentions `item`")
    case("producer script renames a column", lambda r: edit(r, PRODUCER_SCRIPT, '"kind"]', '"knd"]'), "producer_cmd output")
    case(
        "producer behaviour change vs the frozen fixture",
        lambda r: edit(r, PRODUCER_SCRIPT, 'return "alpha"', 'return "beta"'),
        "differs from the frozen fixture",
    )
    case("consumer rejects the fixture", lambda r: edit(r, CONSUMER_SCRIPT, 'COLUMNS = ["item", "kind"]', 'COLUMNS = ["item", "kind", "extra"]'), "consumer_cmd rejected")
    case("contract points at a missing skill", lambda r: edit(r, CONTRACT, f'"consumer": "{CONSUMER}"', '"consumer": "ghost"'), "does not exist")
    case("contract file is not valid JSON", lambda r: (r / "contracts/bad.json").write_text("{"), "not valid JSON")


def t_overlap() -> None:
    r = fresh()
    d = r / "skills/zeta-map"
    shutil.copytree(r / f"skills/{PRODUCER}", d)
    edit(r, "skills/zeta-map/SKILL.md", f"name: {PRODUCER}", "name: zeta-map")
    edit(r, "skills/zeta-map/SKILL.md", BOUNDARY, "")
    expect("overlap: near-duplicate description without a boundary", run("check_overlap.py", "--quiet", root=r), 1, "overlaps")

    r = fresh()
    edit_all(r, [BW], PRODUCER, "the inventory skill")
    expect("overlap: overlapping siblings must name each other", run("check_overlap.py", "--quiet", root=r), 1, "never names it")


def t_backlog() -> None:
    r = fresh()
    b = json.loads((r / "skills_backlog.json").read_text())
    b["skills"][2]["passes"] = True
    (r / "skills_backlog.json").write_text(json.dumps(b))
    expect("backlog: passes=true without a skill on disk fails", run("check_backlog.py", root=r), 1, "does not exist")

    r = fresh()
    b = json.loads((r / "skills_backlog.json").read_text())
    b["skills"][0]["passes"] = False
    (r / "skills_backlog.json").write_text(json.dumps(b))
    expect("backlog: passes=true with an unmet dependency fails", run("check_backlog.py", root=r), 1, "depends_on")

    r = fresh()
    (r / f"evals/{CONSUMER}/trigger.json").unlink()
    expect("backlog: passes=true without evals fails", run("check_backlog.py", root=r), 1, "strict validation fails")

    r = fresh()
    edit(r, CSV_FIXTURE, "widget,alpha", "widget,gamma")
    expect("backlog: passes=true with a broken contract fails", run("check_backlog.py", root=r), 1, "contract")

    r = fresh()
    b = json.loads((r / "skills_backlog.json").read_text())
    b["skills"][2]["depends_on"] = ["ghost"]
    (r / "skills_backlog.json").write_text(json.dumps(b))
    expect("backlog: unknown dependency is rejected", run("check_backlog.py", root=r), 1, "unknown skill")

    r = fresh(git=True)
    b = json.loads((r / "skills_backlog.json").read_text())
    b["skills"][2]["summary"] = "changed behind your back"
    (r / "skills_backlog.json").write_text(json.dumps(b))
    expect("backlog: structure edits are caught against git HEAD", run("check_backlog.py", "--against-git", root=r), 1, "only ['notes', 'passes'] may change")


def t_assertions() -> None:
    import evalkit as E

    d = Path(tempfile.mkdtemp(prefix="selftest-assert-"))
    _tmp_roots.append(d)
    (d / "m.csv").write_text("topic,keyword,page_type,priority\nA,a,service,1\nB,,blog,2\n")
    (d / "o.md").write_text("Hello world TODO fix\n")
    (d / "j.json").write_text('[{"a": 1}, {"a": 2, "b": 3}]')
    (d / "bad.json").write_text("{")

    def one(a: dict, stdout: str = "") -> bool | None:
        return E.evaluate([a], d, stdout)[0].ok

    cases = [
        ("file_exists pass", {"type": "file_exists", "path": "m.csv"}, True),
        ("file_exists fail", {"type": "file_exists", "path": "zzz"}, False),
        ("file_absent pass", {"type": "file_absent", "path": "zzz"}, True),
        ("file_absent fail", {"type": "file_absent", "path": "m.csv"}, False),
        ("csv_columns pass", {"type": "csv_columns", "path": "m.csv", "columns": ["topic", "keyword", "page_type", "priority"]}, True),
        ("csv_columns fail", {"type": "csv_columns", "path": "m.csv", "columns": ["topic", "keyword"]}, False),
        ("csv_min_rows pass", {"type": "csv_min_rows", "path": "m.csv", "n": 2}, True),
        ("csv_min_rows fail", {"type": "csv_min_rows", "path": "m.csv", "n": 3}, False),
        ("csv_enum pass", {"type": "csv_enum", "path": "m.csv", "column": "page_type", "values": ["service", "blog"]}, True),
        ("csv_enum fail", {"type": "csv_enum", "path": "m.csv", "column": "page_type", "values": ["service"]}, False),
        ("csv_no_empty fail", {"type": "csv_no_empty", "path": "m.csv", "column": "keyword"}, False),
        ("csv_no_empty pass", {"type": "csv_no_empty", "path": "m.csv", "column": "topic"}, True),
        ("contains pass", {"type": "contains", "target": "o.md", "text": "world"}, True),
        ("contains fail", {"type": "contains", "target": "o.md", "text": "planet"}, False),
        ("not_contains pass", {"type": "not_contains", "target": "o.md", "text": "planet"}, True),
        ("not_contains fail", {"type": "not_contains", "target": "o.md", "text": "world"}, False),
        ("regex pass", {"type": "regex", "target": "o.md", "pattern": "^Hello"}, True),
        ("not_regex fail", {"type": "not_regex", "target": "o.md", "pattern": "TODO"}, False),
        ("contains on missing file fails", {"type": "contains", "target": "nope.md", "text": "x"}, False),
        ("max_words fail", {"type": "max_words", "target": "o.md", "n": 2}, False),
        ("min_words pass", {"type": "min_words", "target": "o.md", "n": 2}, True),
        ("json_valid pass", {"type": "json_valid", "path": "j.json"}, True),
        ("json_valid fail", {"type": "json_valid", "path": "bad.json"}, False),
        ("json_has_keys fail (key missing on one item)", {"type": "json_has_keys", "path": "j.json", "keys": ["a", "b"]}, False),
        ("json_has_keys pass", {"type": "json_has_keys", "path": "j.json", "keys": ["a"]}, True),
        ("rubric is deferred to the judge", {"type": "rubric", "criteria": ["x"]}, None),
        ("unknown type fails loudly", {"type": "wat"}, False),
        ("malformed assertion fails loudly", {"type": "csv_columns", "path": "m.csv"}, False),
    ]
    for label, a, want in cases:
        got = one(a)
        check(f"assertions: {label}", got is want, f"got {got!r}, wanted {want!r}")
    check("assertions: stdout target works", one({"type": "contains", "target": "stdout", "text": "yes"}, "yes please") is True)


def t_package() -> None:
    r = fresh()
    code, out = run("package_skill.py", PRODUCER, root=r)
    z = r / f"dist/{PRODUCER}.zip"
    check("package: builds zip and .skill for a passing skill", code == 0 and z.exists() and (r / f"dist/{PRODUCER}.skill").exists(), out)
    if z.exists():
        names = zipfile.ZipFile(z).namelist()
        check("package: archive root is the skill folder", f"{PRODUCER}/SKILL.md" in names and not any("__pycache__" in n for n in names), str(names))
        h1 = hashlib.sha256(z.read_bytes()).hexdigest()
        z.unlink()
        run("package_skill.py", PRODUCER, root=r)
        check("package: output is deterministic", hashlib.sha256(z.read_bytes()).hexdigest() == h1)
        check("package: evals are not shipped inside the skill", not any(n.startswith(f"{PRODUCER}/evals") for n in names))
    r = fresh()
    edit(r, TM, f"name: {PRODUCER}", "name: Bad_Name")
    expect("package: refuses to package a skill that fails the gates", run("package_skill.py", PRODUCER, root=r), 1, "refusing to package")


def t_hooks() -> None:
    # --- protect_paths (PreToolUse)
    r = fresh(git=True)

    def pp(tool: str, env=None, **ti) -> tuple[int, str]:
        return run("protect_paths.py", root=r, stdin=hook_input(tool, **ti), hook=True, env=env)

    expect("hook protect: editing a committed eval is blocked", pp("Edit", file_path=str(r / f"evals/{PRODUCER}/trigger.json"), old_string="a", new_string="b"), 2, "protected")
    expect("hook protect: editing a committed fixture is blocked", pp("Write", file_path=str(r / CSV_FIXTURE), content="x"), 2, "protected")
    expect("hook protect: editing a committed contract is blocked", pp("Write", file_path=str(r / CONTRACT), content="{}"), 2, "protected")
    expect("hook protect: creating a NEW eval is allowed", pp("Write", file_path=str(r / "evals/new-skill/trigger.json"), content="{}"), 0)
    expect("hook protect: creating a NEW contract is allowed", pp("Write", file_path=str(r / "contracts/new.json"), content="{}"), 0)
    expect("hook protect: editing a skill is allowed", pp("Edit", file_path=str(r / TM), old_string="a", new_string="b"), 0)
    expect("hook protect: harness scripts are frozen", pp("Write", file_path=str(r / "scripts/validate_skill.py"), content="x"), 2, "harness itself")
    expect("hook protect: hooks are frozen", pp("Write", file_path=str(r / ".claude/hooks/stop_gate.py"), content="x"), 2, "harness itself")
    expect("hook protect: settings are frozen", pp("Write", file_path=str(r / ".claude/settings.json"), content="{}"), 2, "harness itself")
    expect("hook protect: files outside the repo are ignored", pp("Write", file_path="/tmp/whatever.txt", content="x"), 0)
    expect("hook protect: bash redirect into a committed eval is blocked", pp("Bash", command=f"echo '{{}}' > evals/{PRODUCER}/trigger.json"), 2, "shell command")
    expect("hook protect: bash sed -i on a committed fixture is blocked", pp("Bash", command=f"sed -i 's/a/b/' {CSV_FIXTURE}"), 2, "shell command")
    expect("hook protect: bash rm of scripts is blocked", pp("Bash", command="rm -rf scripts/validate_skill.py"), 2, "shell command")
    expect("hook protect: bash git checkout over an eval is blocked", pp("Bash", command=f"git checkout HEAD -- evals/{PRODUCER}/trigger.json"), 2, "shell command")
    expect("hook protect: running a script is allowed", pp("Bash", command="python3 scripts/validate_skill.py --all > /tmp/out.txt"), 0)
    expect("hook protect: reading a protected file is allowed", pp("Bash", command=f"cat evals/{PRODUCER}/trigger.json"), 0)
    expect("hook protect: writing a new bash redirect elsewhere is allowed", pp("Bash", command="echo hi > progress.md"), 0)
    (r / ".harness-unlock").write_text("")
    expect("hook protect: .harness-unlock lifts the block", pp("Write", file_path=str(r / "scripts/validate_skill.py"), content="x"), 0)
    (r / ".harness-unlock").unlink()
    expect("hook protect: HARNESS_UNLOCK=1 lifts the block", pp("Write", env={"HARNESS_UNLOCK": "1"}, file_path=str(r / "scripts/validate_skill.py"), content="x"), 0)

    # backlog edits
    bpath = str(r / "skills_backlog.json")
    cur = json.loads((r / "skills_backlog.json").read_text())
    flipped = json.loads(json.dumps(cur)); flipped["skills"][2]["passes"] = True
    expect("hook protect: flipping `passes` is allowed", pp("Write", file_path=bpath, content=json.dumps(flipped)), 0)
    noted = json.loads(json.dumps(cur)); noted["skills"][2]["notes"] = "hello"
    expect("hook protect: editing `notes` is allowed", pp("Write", file_path=bpath, content=json.dumps(noted)), 0)
    changed = json.loads(json.dumps(cur)); changed["skills"][2]["summary"] = "x"
    expect("hook protect: editing `summary` is blocked", pp("Write", file_path=bpath, content=json.dumps(changed)), 2, "summary")
    changed = json.loads(json.dumps(cur)); changed["skills"][2]["depends_on"] = []
    expect("hook protect: dropping a dependency is blocked", pp("Write", file_path=bpath, content=json.dumps(changed)), 2, "depends_on")
    added = json.loads(json.dumps(cur)); added["skills"].append({"id": "sneaky", "summary": "s", "depends_on": [], "passes": True})
    expect("hook protect: adding a skill to the backlog is blocked", pp("Write", file_path=bpath, content=json.dumps(added)), 2, "added")
    removed = json.loads(json.dumps(cur)); removed["skills"].pop()
    expect("hook protect: removing a skill from the backlog is blocked", pp("Write", file_path=bpath, content=json.dumps(removed)), 2, "removed")
    expect("hook protect: an Edit that flips only `passes` is allowed", pp("Edit", file_path=bpath, old_string='"passes": false', new_string='"passes": true'), 0)
    expect("hook protect: an Edit that breaks the JSON is blocked", pp("Edit", file_path=bpath, old_string='"passes": false', new_string='"passes": '), 2, "invalid JSON")

    # --- post_edit_check (PostToolUse)
    r = fresh(git=True)
    pe = lambda path: run("post_edit_check.py", root=r, stdin=hook_input("Edit", file_path=str(path)), hook=True)
    expect("hook post-edit: clean skill passes silently", pe(r / TM), 0)
    edit(r, TM, f"name: {PRODUCER}", "name: Wrong Name")
    expect("hook post-edit: broken frontmatter is reported with exit 2", pe(r / TM), 2, "kebab-case")
    edit(r, TM, "name: Wrong Name", f"name: {PRODUCER}")
    edit(r, PRODUCER_SCRIPT, '"kind"]', '"knd"]')
    expect("hook post-edit: changing a pipeline producer surfaces the contract break", pe(r / PRODUCER_SCRIPT), 2, "contract")
    expect("hook post-edit: editing a non-skill file is ignored", pe(r / "progress.md"), 0)

    # --- stop_gate (Stop)
    r = fresh(git=True)
    sg = lambda sid="s1", env=None: run("stop_gate.py", root=r, stdin=json.dumps({"session_id": sid, "stop_hook_active": False}), hook=True, env=env)
    code, out = sg()
    check("hook stop: nothing changed -> allows the stop silently", code == 0 and not out.strip(), out)
    edit(r, TM, "## Rules", "TODO write this part\n\n## Rules")
    code, out = sg()
    check("hook stop: failing gate blocks with a JSON decision", code == 0 and '"decision": "block"' in out and "placeholder" in out, out)
    code, out = sg()
    check("hook stop: still blocked on the second attempt", '"decision": "block"' in out, out)
    code, out = sg()
    check("hook stop: gives up after the cap and logs the failure", code == 0 and not out.strip() and (r / "failure_log.md").exists() and "gave up" in (r / "failure_log.md").read_text(), out)
    edit(r, TM, "TODO write this part\n\n", "")
    code, out = sg("s2")
    check("hook stop: green again -> allows the stop", code == 0 and not out.strip(), out)

    r = fresh(git=True)
    edit(r, f"evals/{PRODUCER}/trigger.json", "Make an inventory CSV from the part names in parts.txt", "Make an inventory CSV")
    code, out = sg("s3")
    check("hook stop: tampering with a committed eval is caught even without the edit hook", '"decision": "block"' in out and "protected files were modified" in out, out)
    (r / ".harness-unlock").write_text("")
    code, out = sg("s4")
    check("hook stop: .harness-unlock lets a human-approved eval change through", '"decision": "block"' not in out, out)

    # --- session_brief
    r = fresh(git=True)
    code, out = run("session_brief.py", root=r, hook=True)
    check("hook session: brief names /new-skill and the rules", code == 0 and "/new-skill" in out and "never edit" in out.lower(), out)


# --------------------------------------------------------------------------- #
def main() -> int:
    global BASE
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    BASE = base_tree()
    try:
        for t in (t_baseline, t_validator, t_contracts, t_overlap, t_backlog, t_assertions, t_package, t_hooks):
            try:
                t()
            except Exception as e:  # a crashing test is a failing test
                check(f"{t.__name__} crashed", False, f"{type(e).__name__}: {e}")
    finally:
        for p in _tmp_roots:
            shutil.rmtree(p, ignore_errors=True)
    failed = [r for r in results if not r[1]]
    for name, ok, detail in results:
        if ok and not args.quiet:
            print(f"  ok    {name}")
        elif not ok:
            print(f"  FAIL  {name}\n        {detail}")
    print(f"selftest: {len(results) - len(failed)}/{len(results)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
