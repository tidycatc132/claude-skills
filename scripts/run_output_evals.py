#!/usr/bin/env python3
"""Output evals: run a skill against fixture input, then assert on what it produced.

evals/<skill>/outputs.json
{
  "cases": [
    {
      "id": "basic-map",
      "prompt": "Use the map-maker skill on seeds.txt and save topic_map.csv",
      "fixtures": [{"src": "fixtures/map-maker/seeds.txt", "dest": "seeds.txt"}],
      "allowed_tools": "optional override of the allow-list",
      "assertions": [
        {"type": "file_exists", "path": "topic_map.csv"},
        {"type": "csv_columns", "path": "topic_map.csv", "columns": ["topic", "keyword", "page_type", "priority"]},
        {"type": "rubric", "target": "topic_map.csv", "criteria": ["every keyword is a plausible search query"]}
      ]
    }
  ]
}

Assertion types: file_exists, file_absent, contains, not_contains, regex, not_regex,
max_words, min_words, max_lines (target = a file path or "stdout"), csv_columns, csv_min_rows,
csv_enum, csv_no_empty, json_valid, json_has_keys, rubric (LLM judge, only with --judge).

Modes
  (default)   run claude in a sandbox, assert on the outputs
  --record    also save the produced files as evals/<skill>/golden/<case-id>/ (human reviews first!)
  --golden    no model call: evaluate the assertions against the recorded golden outputs.
              Cheap CI check that the assertions themselves still pass on approved output.
  --judge     evaluate rubric assertions with a separate tool-less claude session
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402
import evalkit as E  # noqa: E402


def run_case(skill_dir: Path, case: dict, args) -> tuple[list[E.Check], str, Path | None, Path | None]:
    """Returns (checks, note, outdir, cleanup_dir). outdir is where outputs live (sandbox or golden)."""
    name = skill_dir.name
    if args.golden:
        gdir = C.EVALS_DIR / name / "golden" / case["id"]
        if not gdir.is_dir():
            return [E.Check(False, "golden", f"no golden output at evals/{name}/golden/{case['id']}/ (run with --record after reviewing a real run)")], "", None, None
        stdout_file = gdir / "stdout.txt"
        stdout = C.read_text(stdout_file) if stdout_file.exists() else ""
        return E.evaluate(case["assertions"], gdir, stdout), "golden", gdir, None

    deps = case.get("with_skills", [])
    dirs = [skill_dir] + [C.SKILLS_DIR / d for d in deps if (C.SKILLS_DIR / d).is_dir()]
    if args.all_skills:
        dirs = C.list_skill_dirs()
    sandbox = E.make_sandbox(dirs)
    seeded: set[str] = set()
    for fx in case.get("fixtures", []):
        src = C.ROOT / fx["src"]
        dst = sandbox / fx["dest"]
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not src.exists():
            return [E.Check(False, "fixture", f"fixture {fx['src']} does not exist")], "", sandbox, sandbox
        shutil.copyfile(src, dst)
        seeded.add(fx["dest"])
    r = E.run_claude(
        case["prompt"], sandbox,
        allowed=case.get("allowed_tools", E.DEFAULT_ALLOWED),
        model=args.model, budget=args.budget, timeout=args.timeout,
    )
    if not r.ok:
        return [E.Check(False, "run", f"claude run failed: {r.error}")], "error", sandbox, sandbox
    checks = E.evaluate(case["assertions"], sandbox, r.text)
    (sandbox / ".harness-stdout.txt").write_text(r.text)
    if args.record:
        gdir = C.EVALS_DIR / name / "golden" / case["id"]
        gdir.mkdir(parents=True, exist_ok=True)
        for f in sandbox.rglob("*"):
            rel = f.relative_to(sandbox)
            if f.is_file() and rel.parts[0] != ".claude" and rel.name != ".harness-stdout.txt" and rel.as_posix() not in seeded:
                (gdir / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(f, gdir / rel)
        (gdir / "stdout.txt").write_text(r.text)
    return checks, "run", sandbox, sandbox


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--skill", action="append")
    ap.add_argument("--case", action="append", help="only these case ids")
    ap.add_argument("--golden", action="store_true")
    ap.add_argument("--record", action="store_true")
    ap.add_argument("--judge", action="store_true")
    ap.add_argument("--all-skills", action="store_true", help="put every skill in the sandbox, not only the target")
    ap.add_argument("--model")
    ap.add_argument("--judge-model")
    ap.add_argument("--budget", type=float)
    ap.add_argument("--timeout", type=int, default=420)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not args.golden and not args.dry_run and not E.claude_bin():
        print("`claude` CLI not found; use --golden for offline checks.", file=sys.stderr)
        return 2

    failed = errored = total = skipped = 0
    for sd in C.list_skill_dirs():
        name = sd.name
        if args.skill and name not in args.skill:
            continue
        f = C.EVALS_DIR / name / "outputs.json"
        if not f.exists():
            continue
        for case in C.load_json(f).get("cases", []):
            if args.case and case["id"] not in args.case:
                continue
            total += 1
            if args.dry_run:
                print(f"  {name}/{case['id']}: {len(case['assertions'])} assertions - {case['prompt'][:70]}")
                continue
            t0 = time.time()
            checks, note, outdir, tmp = run_case(sd, case, args)
            try:
                for ck in checks:
                    if ck.ok is None:
                        if args.judge and outdir is not None:
                            crit = json.loads(ck.detail)
                            a = next(x for x in case["assertions"] if x.get("type") == "rubric" and (x.get("label") or "rubric") == ck.label)
                            tgt = a.get("target", "stdout")
                            if tgt == "stdout":
                                sf = outdir / ("stdout.txt" if args.golden else ".harness-stdout.txt")
                                material = C.read_text(sf) if sf.exists() else ""
                            else:
                                material = C.read_text(outdir / tgt) if (outdir / tgt).exists() else ""
                            ok, why = E.judge(crit, material, args.judge_model)
                            ck.ok, ck.detail = ok, why
                        else:
                            skipped += 1
                bad = [c for c in checks if c.ok is False]
                status = "PASS" if not bad else ("ERROR" if note == "error" else "FAIL")
                print(f"[{status}] {name}/{case['id']} ({note}, {time.time() - t0:.0f}s, {len(checks)} checks)")
                for c in bad:
                    print(f"        - {c.label}: {c.detail}")
                if status == "FAIL":
                    failed += 1
                elif status == "ERROR":
                    errored += 1
            finally:
                if tmp is not None:
                    shutil.rmtree(tmp, ignore_errors=True)
    if total == 0:
        print("no output evals found")
        return 0
    print(f"{total} case(s): {failed} failed, {errored} errored" + (f", {skipped} rubric check(s) skipped (use --judge)" if skipped else ""))
    return 2 if errored else (1 if failed else 0)


if __name__ == "__main__":
    sys.exit(main())
