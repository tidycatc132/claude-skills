#!/usr/bin/env python3
"""Check that .claude-plugin/marketplace.json still matches skills/.

Website build plugins use the repo root as their source and list skill folders
under skills/, so a new or renamed skill must be added to the marketplace by hand.
This check fails when:
  - a folder in skills/ is in no plugin, or in more than one;
  - a listed skill path does not exist or has no SKILL.md;
  - a root-sourced plugin lists no skills (Claude Code would then load every
    skill in skills/ for it).

Usage: python3 plugins/check_marketplace.py   (exit 0 = in sync)
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
    errors = []
    owner = {}
    for plugin in market["plugins"]:
        if plugin.get("source") not in ("./", "."):
            continue
        listed = plugin.get("skills") or []
        if not listed:
            errors.append(f"{plugin['name']}: root-sourced plugin lists no skills (would load all of skills/)")
        for path in listed:
            folder = (ROOT / path).resolve()
            if not (folder / "SKILL.md").is_file():
                errors.append(f"{plugin['name']}: {path} has no SKILL.md")
                continue
            owner.setdefault(folder.name, []).append(plugin["name"])
    for skill in sorted(p.name for p in (ROOT / "skills").iterdir() if (p / "SKILL.md").is_file()):
        plugins = owner.get(skill, [])
        if not plugins:
            errors.append(f"{skill}: in skills/ but in no plugin")
        elif len(plugins) > 1:
            errors.append(f"{skill}: in more than one plugin ({', '.join(plugins)})")
    for e in errors:
        print("FAIL", e)
    print(f"{'OK' if not errors else 'RED'}: {len(owner)} skills mapped to plugins, {len(errors)} problem(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
