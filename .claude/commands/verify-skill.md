---
description: Behavioral verification for one skill - trigger evals, output evals, and an independent review
argument-hint: "<skill-id>"
---

Verify the behavior of the skill `$ARGUMENTS`. These checks cost model calls, so run them once the cheap gates are green, not on every edit.

1. Cheap gates first. If any fail, stop and fix them:
   ```
   python3 scripts/validate_skill.py $ARGUMENTS --strict
   python3 scripts/check_contracts.py --skill $ARGUMENTS
   python3 scripts/check_overlap.py
   ```
2. Trigger evals (real routing, with all sibling skills present):
   ```
   python3 scripts/run_trigger_evals.py --skill $ARGUMENTS --runs 2
   ```
   For every miss, decide whether the DESCRIPTION is wrong (fix it) or the eval prompt is wrong (tell the user; evals are frozen once committed). Do not paper over a miss by stuffing keywords into the description.
3. Output evals:
   ```
   python3 scripts/run_output_evals.py --skill $ARGUMENTS --judge
   ```
   Fix the skill, not the assertions. If the skill changed legitimately, show the user the diff of the produced output before anything is re-recorded with `--record`.
4. Independent review. Spawn the `skill-reviewer` subagent for `$ARGUMENTS` (a fresh context that did not write the skill and cannot edit). Treat each BLOCKER as a failing gate. List its CONCERNS for the user.
5. Report in this shape, nothing longer:
   - Trigger: x/y correct (misses listed)
   - Output: cases passed / total (failures listed)
   - Review: PASS or FAIL with the blockers
   - Your recommendation: ship, fix, or ask the user

If trigger or output evals error out (not logged in, timeouts), say so plainly and report only what actually ran. Do not claim a pass for checks that did not run.
