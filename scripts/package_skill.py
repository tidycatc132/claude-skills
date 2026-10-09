#!/usr/bin/env python3
"""Package skills into dist/<name>.zip (and a .skill copy) after the strict gates pass.

The archive root is the skill folder itself (<name>/SKILL.md, <name>/references/...), which is
what Claude.ai's skill upload and org sharing expect. Zips are deterministic (fixed timestamps,
sorted entries) so identical skills produce identical bytes.

Usage:
  package_skill.py <skill> [<skill> ...]
  package_skill.py --all
  package_skill.py --force   skip the gates (not recommended)
"""
from __future__ import annotations

import argparse
import shutil
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_contracts as CC  # noqa: E402
import common as C  # noqa: E402
import validate_skill as V  # noqa: E402

DIST = C.ROOT / "dist"
SKIP_DIRS = {"__pycache__", ".git", ".DS_Store", "node_modules"}
SKIP_SUFFIXES = {".pyc", ".pyo"}


def package(skill_dir: Path, force: bool) -> tuple[bool, str]:
    name = skill_dir.name
    if not force:
        rep = V.validate(skill_dir, strict=True)
        errs = list(rep.errors)
        for p, c in CC.select(CC.load_contracts(), skill=name):
            errs += CC.check_contract(p, c).errors
        if errs:
            return False, f"{name}: refusing to package; {len(errs)} gate error(s):\n    " + "\n    ".join(errs)
    DIST.mkdir(exist_ok=True)
    zpath = DIST / f"{name}.zip"
    files = sorted(
        f for f in skill_dir.rglob("*")
        if f.is_file() and not (set(f.relative_to(skill_dir).parts) & SKIP_DIRS) and f.suffix not in SKIP_SUFFIXES
        and f.name != ".DS_Store"
    )
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            arc = f"{name}/{f.relative_to(skill_dir).as_posix()}"
            info = zipfile.ZipInfo(arc, date_time=(2020, 1, 1, 0, 0, 0))
            mode = 0o755 if (f.stat().st_mode & 0o111) else 0o644
            info.external_attr = (0o100000 | mode) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, f.read_bytes())
    shutil.copyfile(zpath, DIST / f"{name}.skill")
    return True, f"{name}: dist/{name}.zip + dist/{name}.skill ({len(files)} files)"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("skills", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    if args.all:
        dirs = C.list_skill_dirs()
    else:
        dirs = []
        for s in args.skills:
            d = C.resolve_skill(s)
            if d is None or not d.is_dir():
                C.die(f"no such skill: {s}")
            dirs.append(d)
    if not dirs:
        print("nothing to package (name a skill or use --all)")
        return 1
    ok_all = True
    for d in dirs:
        ok, msg = package(d, args.force)
        print(("OK   " if ok else "FAIL ") + msg)
        ok_all &= ok
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
