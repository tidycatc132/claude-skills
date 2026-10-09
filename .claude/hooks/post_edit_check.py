#!/usr/bin/env python3
"""PostToolUse hook (Edit|Write): fast sensors right after a skill file changes.

Runs the non-strict validator for the touched skill, plus any contract the skill takes part in
(so changing a pipeline skill's interface immediately surfaces the downstream breakage).
Only ERRORS are reported; warnings stay out of the way (see validate_skill.py for those).
Exit 2 puts stderr in front of Claude so it self-corrects before moving on.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import check_contracts as CC  # noqa: E402
import common as C  # noqa: E402
import validate_skill as V  # noqa: E402


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    fp = (data.get("tool_input") or {}).get("file_path", "")
    if not fp:
        return 0
    errors: list[str] = []
    skill = C.skill_for_path(fp)
    contracts = CC.load_contracts()
    if skill and skill.is_dir():
        errors += [f"[{skill.name}] {e}" for e in V.validate(skill, strict=False).errors]
        chosen = CC.select(contracts, skill=skill.name)
    else:
        chosen = CC.select(contracts, file=fp)
    for p, c in chosen:
        errors += [f"[{p.stem}] {e}" for e in CC.check_contract(p, c).errors]
    if not errors:
        return 0
    rel = Path(fp)
    print(
        f"Skill checks failed after editing {rel.name}. Fix these before continuing:\n  - "
        + "\n  - ".join(errors[:12])
        + ("\n  - ...and more (run: python3 scripts/validate_skill.py --changed)" if len(errors) > 12 else ""),
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
