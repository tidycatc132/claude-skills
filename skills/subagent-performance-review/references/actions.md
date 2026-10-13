# Acting on a verdict

Positions are files. A sub-agent is "filled" when `DIR/NAME.md` exists with a usable body. Every action below is done by `scripts/apply_action.py`; this file says what you must write for it.

## Writing a new body (improvement plan and replace)
Write the new system prompt to a file in the working directory (for example `body_NAME.md`), then pass it as `--body`. Build it from the review, finding by finding:

| Finding in `review_NAME.json` | Instruction to add |
|---|---|
| low first-pass acceptance, rejections | restate the deliverable's acceptance test inside the prompt (format, length, required sections) and require a self-check against it before reporting done |
| `accepted_with_fixes` dominant | name the recurring fix from `notes` and make it a rule |
| scope violations | list the files or areas it may touch and say every other change is forbidden; report instead of acting when the brief is unclear |
| fabrication | every fact must trace to a source it read in this dispatch; write `MISSING` or ask instead of filling gaps; cite the source next to each value |
| abandoned dispatches | on a repeated tool error, stop and report the error and partial output instead of giving up silently |
| tool errors | name the tool that failed in `notes` and give the correct usage |
| low efficiency | one round of rework is the budget; ask one clarifying question up front rather than iterating |

Keep what worked: for an improvement plan, start from the current body and change only the parts the findings point at. For a replacement, write the body fresh; the retired file stays in `retired/` for comparison. The script appends the plan section with findings, exit criteria and the re-review date itself.

## Reassign
Write a description that names only the task types with acceptance 80 or higher (`strong_types` in the review) and says which agent takes the rest. Pass it as `--description`. Tell the user which agent now owns the removed task types.

## Promote
A promotion widens scope. The new role's description should cover the complexity-3 work the agent already delivers plus the next step up (reviewing peers' output, owning a whole workflow). Use the user's role name if given, else `lead-TYPE`. The old file stays in place, so the old position is filled by the same proven definition; say that in the report.

## Merge
`--into` is the `merge_into` agent from the review. The script appends this agent's description to the target's and retires this file. Check the target's `tools` cover what the merged scope needs; if not, say so in the report and pass `--description` with a reduced scope instead of leaving a gap.

## Re-review
An improvement plan sets `re_review_date`. At that date run `score_review.py` with `--prior review_NAME.json` (the one that opened the plan). If the exit criteria are not met the verdict is `replace`; act on it the same day.
