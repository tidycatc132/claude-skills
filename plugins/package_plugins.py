#!/usr/bin/env python3
"""Build one upload-ready zip per plugin for the claude.ai org admin page.

Use this when syncing the marketplace from GitHub fails: an org admin uploads each zip under
Organization settings > Plugins & skills > Add > Upload a plugin, and later uses the row's
"Upload new version" for updates. Every change to a plugin means rebuilding and re-uploading it.

Each archive is dist/plugins/<plugin>.zip with the plugin folder's contents at the zip root
(.claude-plugin/plugin.json, skills/<name>/SKILL.md, ...), the layout the upload expects.
Zips are deterministic (fixed timestamps, sorted entries), so an unchanged plugin rebuilds to
identical bytes.

Gates, all of which must pass before anything is written:
  - plugins/catalog.py --check (marketplace, folders, plugin.json names, READMEs in step);
  - every skill passes scripts/validate_skill.py (non-strict: shipped skills have no evals);
  - each finished zip is re-read and checked: plugin.json at the root with a matching name,
    every skills/<name>/SKILL.md has name == folder and a description, nothing else at the
    root but .claude-plugin/, skills/ and README.md.

Combined zips (COMBINED below) merge every plugin of one marketplace category into a single
upload, e.g. dist/plugins/website-build.zip holds all the build-* skills. Upload either the
combined zip or its separate plugins, never both, or each skill shows up twice.

Usage:
  python3 plugins/package_plugins.py               build every plugin, plus the combined zips
  python3 plugins/package_plugins.py agency-tools  build only the named plugins
  python3 plugins/package_plugins.py --out DIR     write the zips to DIR instead of dist/plugins
"""
from __future__ import annotations

import argparse
import io
import json
import subprocess
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "scripts"))
import common as C  # noqa: E402  (read-only use of the harness helpers)
import validate_skill as V  # noqa: E402

MARKET = ROOT / ".claude-plugin" / "marketplace.json"
DEFAULT_OUT = ROOT / "dist" / "plugins"
SKIP_PARTS = {"__pycache__", ".git", "node_modules", ".DS_Store"}
SKIP_SUFFIXES = {".pyc", ".pyo"}
ALLOWED_ROOT = {".claude-plugin", "skills", "README.md"}
FIXED_TIME = (2020, 1, 1, 0, 0, 0)

# combined plugin name -> (marketplace category it gathers, description)
COMBINED = {
    "website-build": ("build", "Every WISE website build skill in one plugin: shared build skills plus "
                               "Account Management, SEO & Content and Development."),
}


def plugin_files(folder: Path) -> list[Path]:
    return sorted(
        f for f in folder.rglob("*")
        if f.is_file()
        and not (set(f.relative_to(folder).parts) & SKIP_PARTS)
        and f.suffix not in SKIP_SUFFIXES
    )


def write_entry(zf: zipfile.ZipFile, arc: str, data: bytes, executable: bool = False) -> None:
    info = zipfile.ZipInfo(arc, date_time=FIXED_TIME)
    info.external_attr = (0o100000 | (0o755 if executable else 0o644)) << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    zf.writestr(info, data)


def build_zip(folder: Path, files: list[Path]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            write_entry(zf, f.relative_to(folder).as_posix(), f.read_bytes(), bool(f.stat().st_mode & 0o111))
    return buf.getvalue()


def build_combined(name: str, description: str, parts: list[Path]) -> tuple[bytes, int]:
    """One plugin holding the skills/ of every part. catalog.py --check guarantees unique skill names."""
    versions = sorted({json.loads((p / ".claude-plugin" / "plugin.json").read_text())["version"] for p in parts})
    manifest = {"name": name, "version": versions[-1], "description": description,
                "author": {"name": "WISE Digital Partners"}}
    skills = sorted(d.name for p in parts for d in (p / "skills").iterdir() if (d / "SKILL.md").is_file())
    readme = (f"# {name}\n\n{description}\n\n"
              f"This upload combines the {', '.join(p.name for p in parts)} plugins, so install either this "
              "plugin or those, not both, or each skill appears twice. It is built by plugins/package_plugins.py "
              "and is not in the marketplace.\n\n## Skills\n\n" + "".join(f"- `{s}`\n" for s in skills))
    entries: list[tuple[str, bytes, bool]] = [
        (".claude-plugin/plugin.json", (json.dumps(manifest, indent=2) + "\n").encode(), False),
        ("README.md", readme.encode(), False),
    ]
    for p in parts:
        for f in plugin_files(p):
            rel = f.relative_to(p).as_posix()
            if rel.startswith("skills/"):
                entries.append((rel, f.read_bytes(), bool(f.stat().st_mode & 0o111)))
    entries.sort(key=lambda e: e[0])
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for arc, data, ex in entries:
            write_entry(zf, arc, data, ex)
    return buf.getvalue(), len(entries)


def check_zip(data: bytes, plugin: str) -> list[str]:
    errs: list[str] = []
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        if zf.testzip() is not None:
            return [f"{plugin}: corrupt zip"]
        names = zf.namelist()
        roots = {n.split("/", 1)[0] for n in names}
        for extra in sorted(roots - ALLOWED_ROOT):
            errs.append(f"{plugin}: unexpected entry at zip root: {extra}")
        try:
            manifest = json.loads(zf.read(".claude-plugin/plugin.json"))
        except KeyError:
            return errs + [f"{plugin}: .claude-plugin/plugin.json is not at the zip root"]
        except json.JSONDecodeError as e:
            return errs + [f"{plugin}: plugin.json is not valid JSON ({e})"]
        if manifest.get("name") != plugin:
            errs.append(f"{plugin}: plugin.json name is {manifest.get('name')!r}")
        skills = sorted(n for n in names if n.startswith("skills/") and n.count("/") == 2 and n.endswith("/SKILL.md"))
        if not skills:
            errs.append(f"{plugin}: no skills/<name>/SKILL.md in the zip")
        for s in skills:
            folder = s.split("/")[1]
            fm, _ = C.parse_frontmatter(zf.read(s).decode("utf-8"))
            if not fm:
                errs.append(f"{plugin}: {s} has no frontmatter")
                continue
            if fm.get("name") != folder:
                errs.append(f"{plugin}: {s} name {fm.get('name')!r} differs from its folder")
            if not fm.get("description"):
                errs.append(f"{plugin}: {s} has no description")
    return errs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plugins", nargs="*", help="plugin names (default: every plugin in the marketplace)")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    entries = {e["name"]: e for e in C.load_json(MARKET)["plugins"]}
    wanted = args.plugins or list(entries) + list(COMBINED)
    unknown = [p for p in wanted if p not in entries and p not in COMBINED]
    if unknown:
        C.die(f"not in the marketplace: {', '.join(unknown)}")

    cat = subprocess.run([sys.executable, str(HERE / "catalog.py"), "--check"], capture_output=True, text=True)
    if cat.returncode != 0:
        print(cat.stdout + cat.stderr, end="")
        print("FAIL catalog.py --check; fix the catalog before packaging")
        return 1

    built: dict[str, tuple[bytes, int, int]] = {}
    errors: list[str] = []
    for name in wanted:
        if name in COMBINED:
            category, description = COMBINED[name]
            parts = [(ROOT / e["source"]).resolve() for e in entries.values() if e.get("category") == category]
            if not parts:
                errors.append(f"{name}: no marketplace plugins in category {category!r}")
                continue
            data, nfiles = build_combined(name, description, parts)
            errors += check_zip(data, name)
            nskills = sum(1 for p in parts for d in (p / "skills").iterdir() if (d / "SKILL.md").is_file())
            built[name] = (data, nfiles, nskills)
            continue
        folder = (ROOT / entries[name]["source"]).resolve()
        skill_dirs = sorted(d for d in (folder / "skills").iterdir() if (d / "SKILL.md").is_file())
        for d in skill_dirs:
            errors += [f"{name}/{d.name}: {e}" for e in V.validate(d, strict=False).errors]
        files = plugin_files(folder)
        data = build_zip(folder, files)
        errors += check_zip(data, name)
        built[name] = (data, len(files), len(skill_dirs))

    if errors:
        print("FAIL nothing written; " + str(len(errors)) + " problem(s):\n  " + "\n  ".join(errors))
        return 1

    args.out.mkdir(parents=True, exist_ok=True)
    for name, (data, nfiles, nskills) in built.items():
        path = args.out / f"{name}.zip"
        path.write_bytes(data)
        print(f"OK   {path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}  "
              f"{nskills} skills, {nfiles} files, {len(data) / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
