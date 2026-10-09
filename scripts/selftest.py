#!/usr/bin/env python3
"""Self-test: do the sensors actually fire?

Böckeler's open question for harness engineering: "if sensors never fire, is that a sign of high
quality or inadequate detection?" This script answers it for THIS harness. It copies the example
skills into a temp repo, injects one known defect at a time, and asserts that the right gate turns
red with a useful message (and that a clean copy stays green). Run it after touching any script,
hook or rule. init.sh runs it at the start of every session.

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
# plumbing
# --------------------------------------------------------------------------- #
def base_tree() -> Path:
    base = Path(tempfile.mkdtemp(prefix="selftest-base-"))
    _tmp_roots.append(base)
    for item in ("skills", "evals", "contracts", "fixtures"):
        shutil.copytree(KIT / item, base / item, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "golden"))
    shutil.copyfile(KIT / "skills_backlog.json", base / "skills_backlog.json")
    (base / "CLAUDE.md").write_text("# test\n")
    (base / "progress.md").write_text("# progress\n- baseline\n")
    return base


BASE: Path | None = None


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
TM = "skills/example-topic-map/SKILL.md"
BW = "skills/example-brief-writer/SKILL.md"


# --------------------------------------------------------------------------- #
# tests
# --------------------------------------------------------------------------- #
def t_baseline() -> None:
    r = fresh()
    expect("baseline: strict validation is green", run(*VALIDATE, root=r), 0)
    expect("baseline: contracts are green", run("check_contracts.py", "--all", root=r), 0)
    expect("baseline: overlap check is green", run("check_overlap.py", "--quiet", root=r), 0)
    expect("baseline: backlog gate is green", run("check_backlog.py", root=r), 0)
    expect("baseline: --next names the unbuilt skill", run("check_backlog.py", "--next", root=r), 0, "example-article-outline")


def t_validator() -> None:
    def case(label: str, mutate, needle: str, strict: bool = True, rc: int = 1) -> None:
        r = fresh()
        mutate(r)
        args = ("validate_skill.py", "--all") + (("--strict",) if strict else ())
        expect(f"validator: {label}", run(*args, root=r), rc, needle)

    case("uppercase name", lambda r: edit(r, TM, "name: example-topic-map", "name: Example-Topic-Map"), "kebab-case")
    case("name differs from folder", lambda r: edit(r, TM, "name: example-topic-map", "name: something-else"), "must match the folder")
    case("name contains 'claude'", lambda r: (edit(r, TM, "name: example-topic-map", "name: claude-topic-map")), "must not contain 'claude'")
    case("description over 1024 chars", lambda r: edit(r, TM, "Do NOT use for", "x" * 1100 + " Do NOT use for"), "limit is 1024")
    case("angle brackets in description", lambda r: edit(r, TM, "Turn a plain-text", "Turn a <b>plain-text"), "angle brackets")
    case("missing description", lambda r: edit(r, TM, "description:", "descriptionx:"), "missing 'description'")
    case("no frontmatter", lambda r: (r / TM).write_text("# no frontmatter\n"), "no YAML frontmatter")
    case("reference to a missing file", lambda r: edit(r, TM, "## Rules", "See references/nope.md for more.\n\n## Rules"), "does not exist")
    case("hard-coded environment path", lambda r: edit(r, TM, "## Rules", "Files live in /mnt/skills/user/x.\n\n## Rules"), "hard-codes")
    case("environment path with allow marker", lambda r: edit(r, TM, "## Rules", "Files live in /mnt/skills/user/x. harness:allow-path\n\n## Rules"), "", rc=0)
    case("python syntax error in script", lambda r: (r / "skills/example-topic-map/scripts/make_map.py").write_text("def broken(:\n"), "syntax error")
    case("invalid JSON asset", lambda r: (r / "skills/example-topic-map/references/x.json").write_text("{nope"), "not valid JSON")
    case("SKILL.md body over the line limit", lambda r: edit(r, TM, "## Rules", "line\n" * 520 + "\n## Rules"), "lines (limit")
    case("TODO placeholder fails strict", lambda r: edit(r, TM, "## Rules", "TODO write this part\n\n## Rules"), "placeholder")
    case("TODO placeholder only warns when not strict", lambda r: edit(r, TM, "## Rules", "TODO write this part\n\n## Rules"), "placeholder", strict=False, rc=0)
    case("missing trigger evals fails strict", lambda r: (r / "evals/example-topic-map/trigger.json").unlink(), "trigger.json is missing")
    case("missing trigger evals only warns when not strict", lambda r: (r / "evals/example-topic-map/trigger.json").unlink(), "trigger.json is missing", strict=False, rc=0)
    case("missing output evals fails strict", lambda r: (r / "evals/example-topic-map/outputs.json").unlink(), "outputs.json is missing")

    def few(r: Path) -> None:
        p = r / "evals/example-topic-map/trigger.json"
        d = json.loads(p.read_text())
        d["should_not_trigger"] = d["should_not_trigger"][:2]
        p.write_text(json.dumps(d))

    case("too few should_not_trigger prompts", few, "need at least")

    def dup(r: Path) -> None:
        p = r / "evals/example-topic-map/trigger.json"
        d = json.loads(p.read_text())
        d["should_not_trigger"][0] = d["should_trigger"][0]
        p.write_text(json.dumps(d))

    case("duplicate trigger prompts", dup, "duplicate")

    def dupname(r: Path) -> None:
        shutil.copytree(r / "skills/example-brief-writer", r / "skills/zz-copy")
        edit(r, "skills/zz-copy/SKILL.md", "name: example-brief-writer", "name: example-topic-map")

    case("duplicate frontmatter names", dupname, "must be unique", strict=False)


def t_contracts() -> None:
    def case(label: str, mutate, needle: str, rc: int = 1) -> None:
        r = fresh()
        mutate(r)
        expect(f"contracts: {label}", run("check_contracts.py", "--all", root=r), rc, needle)

    csvp = "fixtures/contracts/topic-map.csv"
    case("fixture column order changed", lambda r: edit(r, csvp, "topic,keyword,page_type,priority", "keyword,topic,page_type,priority"), "same columns, different order")
    case("fixture missing a column", lambda r: edit(r, csvp, "topic,keyword,page_type,priority", "topic,keyword,page_type"), "missing: ['priority']")
    case("fixture value outside enum", lambda r: edit(r, csvp, ",service,1", ",product,1"), "not an allowed value")
    case("fixture has an empty required cell", lambda r: edit(r, csvp, "Drain Cleaning,drain cleaning", "Drain Cleaning,"), "must not be empty")
    case("consumer docs drop a contract column", lambda r: edit_all(r, [BW, "skills/example-brief-writer/references/brief-template.md"], "`page_type`", "page type"), "never mentions `page_type`")
    case("producer docs drop a contract column", lambda r: edit_all(r, [TM, "skills/example-topic-map/references/page-types.md"], "`priority`", "priority"), "never mentions `priority`")
    case("producer script renames a column", lambda r: edit(r, "skills/example-topic-map/scripts/make_map.py", '"priority"]', '"prio"]'), "producer_cmd output")
    case(
        "producer behaviour change vs the frozen fixture",
        lambda r: edit(r, "skills/example-topic-map/scripts/make_map.py", 'return "service"', 'return "blog"'),
        "differs from the frozen fixture",
    )
    case("consumer rejects the fixture", lambda r: edit(r, "skills/example-brief-writer/scripts/make_briefs.py", 'COLUMNS = ["topic", "keyword", "page_type", "priority"]', 'COLUMNS = ["topic", "keyword", "page_type", "priority", "extra"]'), "consumer_cmd rejected")
    case("contract points at a missing skill", lambda r: edit(r, "contracts/topic-map-to-brief.json", '"consumer": "example-brief-writer"', '"consumer": "ghost"'), "does not exist")
    case("contract file is not valid JSON", lambda r: (r / "contracts/bad.json").write_text("{"), "not valid JSON")


def t_overlap() -> None:
    r = fresh()
    d = r / "skills/zeta-map"
    shutil.copytree(r / "skills/example-topic-map", d)
    edit(r, "skills/zeta-map/SKILL.md", "name: example-topic-map", "name: zeta-map")
    edit(r, "skills/zeta-map/SKILL.md", " Do NOT use for writing content briefs from an existing map (use example-brief-writer) or for writing articles.", "")
    expect("overlap: near-duplicate description without a boundary", run("check_overlap.py", "--quiet", root=r), 1, "overlaps")

    r = fresh()
    edit_all(r, [BW], "example-topic-map", "the map skill")
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
    (r / "evals/example-brief-writer/trigger.json").unlink()
    expect("backlog: passes=true without evals fails", run("check_backlog.py", root=r), 1, "strict validation fails")

    r = fresh()
    edit(r, "fixtures/contracts/topic-map.csv", ",service,1", ",product,1")
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
    code, out = run("package_skill.py", "example-topic-map", root=r)
    z = r / "dist/example-topic-map.zip"
    check("package: builds zip and .skill for a passing skill", code == 0 and z.exists() and (r / "dist/example-topic-map.skill").exists(), out)
    if z.exists():
        names = zipfile.ZipFile(z).namelist()
        check("package: archive root is the skill folder", "example-topic-map/SKILL.md" in names and not any("__pycache__" in n for n in names), str(names))
        h1 = hashlib.sha256(z.read_bytes()).hexdigest()
        z.unlink()
        run("package_skill.py", "example-topic-map", root=r)
        check("package: output is deterministic", hashlib.sha256(z.read_bytes()).hexdigest() == h1)
        check("package: evals are not shipped inside the skill", not any(n.startswith("example-topic-map/evals") for n in names))
    r = fresh()
    edit(r, TM, "name: example-topic-map", "name: Bad_Name")
    expect("package: refuses to package a skill that fails the gates", run("package_skill.py", "example-topic-map", root=r), 1, "refusing to package")


def t_hooks() -> None:
    # --- protect_paths (PreToolUse)
    r = fresh(git=True)

    def pp(tool: str, env=None, **ti) -> tuple[int, str]:
        return run("protect_paths.py", root=r, stdin=hook_input(tool, **ti), hook=True, env=env)

    expect("hook protect: editing a committed eval is blocked", pp("Edit", file_path=str(r / "evals/example-topic-map/trigger.json"), old_string="a", new_string="b"), 2, "protected")
    expect("hook protect: editing a committed fixture is blocked", pp("Write", file_path=str(r / "fixtures/contracts/topic-map.csv"), content="x"), 2, "protected")
    expect("hook protect: editing a committed contract is blocked", pp("Write", file_path=str(r / "contracts/topic-map-to-brief.json"), content="{}"), 2, "protected")
    expect("hook protect: creating a NEW eval is allowed", pp("Write", file_path=str(r / "evals/new-skill/trigger.json"), content="{}"), 0)
    expect("hook protect: creating a NEW contract is allowed", pp("Write", file_path=str(r / "contracts/new.json"), content="{}"), 0)
    expect("hook protect: editing a skill is allowed", pp("Edit", file_path=str(r / TM), old_string="a", new_string="b"), 0)
    expect("hook protect: harness scripts are frozen", pp("Write", file_path=str(r / "scripts/validate_skill.py"), content="x"), 2, "harness itself")
    expect("hook protect: hooks are frozen", pp("Write", file_path=str(r / ".claude/hooks/stop_gate.py"), content="x"), 2, "harness itself")
    expect("hook protect: settings are frozen", pp("Write", file_path=str(r / ".claude/settings.json"), content="{}"), 2, "harness itself")
    expect("hook protect: files outside the repo are ignored", pp("Write", file_path="/tmp/whatever.txt", content="x"), 0)
    expect("hook protect: bash redirect into a committed eval is blocked", pp("Bash", command="echo '{}' > evals/example-topic-map/trigger.json"), 2, "shell command")
    expect("hook protect: bash sed -i on a committed fixture is blocked", pp("Bash", command="sed -i 's/a/b/' fixtures/contracts/topic-map.csv"), 2, "shell command")
    expect("hook protect: bash rm of scripts is blocked", pp("Bash", command="rm -rf scripts/validate_skill.py"), 2, "shell command")
    expect("hook protect: bash git checkout over an eval is blocked", pp("Bash", command="git checkout HEAD -- evals/example-topic-map/trigger.json"), 2, "shell command")
    expect("hook protect: running a script is allowed", pp("Bash", command="python3 scripts/validate_skill.py --all > /tmp/out.txt"), 0)
    expect("hook protect: reading a protected file is allowed", pp("Bash", command="cat evals/example-topic-map/trigger.json"), 0)
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
    edit(r, TM, "name: example-topic-map", "name: Wrong Name")
    expect("hook post-edit: broken frontmatter is reported with exit 2", pe(r / TM), 2, "kebab-case")
    edit(r, TM, "name: Wrong Name", "name: example-topic-map")
    edit(r, "skills/example-topic-map/scripts/make_map.py", '"priority"]', '"prio"]')
    expect("hook post-edit: changing a pipeline producer surfaces the contract break", pe(r / "skills/example-topic-map/scripts/make_map.py"), 2, "contract")
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
    edit(r, "evals/example-topic-map/trigger.json", "Make a topical map from the seeds in seeds.txt", "Make a topical map")
    code, out = sg("s3")
    check("hook stop: tampering with a committed eval is caught even without the edit hook", '"decision": "block"' in out and "protected files were modified" in out, out)
    (r / ".harness-unlock").write_text("")
    code, out = sg("s4")
    check("hook stop: .harness-unlock lets a human-approved eval change through", '"decision": "block"' not in out, out)

    # --- session_brief
    r = fresh(git=True)
    code, out = run("session_brief.py", root=r, hook=True)
    check("hook session: brief names the next skill and the rules", code == 0 and "example-article-outline" in out and "never edit" in out.lower(), out)


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
