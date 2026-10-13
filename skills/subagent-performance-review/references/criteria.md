# Review criteria

These criteria are fixed by the skill, not by the user. A manager reviewing a human looks at quality, judgement, efficiency and dependability; the same four questions apply to a sub-agent and each one maps to fields the manager can observe at the end of every dispatch.

## Dimensions (each 0 to 100)

| Dimension | Weight | Question | Formula over the window |
|---|---|---|---|
| acceptance | 40% | Was the deliverable right the first time? | mean over non-blocked dispatches of 1.0 for `accepted`, 0.5 for `accepted_with_fixes`, 0 otherwise, times 100 |
| adherence | 25% | Did it do what was asked and only that? | per dispatch 100 minus 50 per `scope_violations` (floor 0), and 0 for any dispatch with `fabrication`; mean over all dispatches |
| efficiency | 20% | How much manager time did it cost? | per non-blocked dispatch 100 minus 30 per `rework_rounds` minus 10 per `tool_errors` (floor 0); mean |
| reliability | 15% | Did it come back with something? | share of dispatches not `abandoned`, times 100 |

`blocked` means the sub-agent correctly stopped on a real blocker; it counts for reliability and is excluded from acceptance and efficiency, so stopping honestly is never punished.

Composite = 0.40 acceptance + 0.25 adherence + 0.20 efficiency + 0.15 reliability, rounded to an integer.

## Caps (vetoes)
- One dispatch with fabrication caps the composite at 59 (improvement plan at best).
- Two or more cap it at 39 (replace).
- Half or more of dispatches abandoned caps it at 49.

Fabrication is the one failure a prompt cannot fully fix, so it dominates every other signal.

## Trend
With six or more dispatches, the window is split in two halves by time and first-pass acceptance is compared. A change of 15 points or more is `improving` or `declining`; otherwise `flat`. Fewer than six dispatches: `insufficient`.

## Verdict bands (first match wins)
1. Fewer than 5 dispatches in the window: `insufficient_data`. No action.
2. Composite 85 or higher, no fabrication, trend not declining, at least 2 complexity-3 tasks `accepted`: `promote`.
3. Composite 70 or higher: `retain`.
4. Composite below 40: `replace`.
5. A prior review with verdict `improvement_plan` and the composite has not risen by 10 or more: `replace` (the plan failed).
6. Another agent in the same log covers every one of this agent's task types with a composite 15 or more points higher, and this agent has fewer than 8 dispatches: `merge`.
7. Some task type with 3 or more dispatches has acceptance 80 or higher and is under half of the volume: `reassign` (narrow it to what it is good at).
8. Otherwise: `improvement_plan`.

## Why 30 days and 5 dispatches
Thirty days matches the review cadence a manager would use for a new hire; five dispatches is the smallest sample where one bad task cannot move the composite by more than 20 points on its own. Both are arguments (`--window-days`, and the minimum is a constant in the script).
