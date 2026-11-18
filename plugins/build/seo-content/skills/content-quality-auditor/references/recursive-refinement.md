# Recursive Refinement Loop (CORE-EEAT)

Use only when the user asks to improve a draft toward a target score (for example "get this to Good", "fix and rescore"). Score, find the weakest dimensions, revise, rescore. Stop early when the band is met. **Never more than 3 rounds.** The loop tunes scores; it never changes how vetoes, Unknowns, or the 59 cap work.

## Preconditions

- The baseline audit is complete (coverage 100%). With any applicable `unknown`, the result is `NEEDS_INPUT`; resolve the evidence first, do not loop on an interval.
- No veto fails. With exactly one verified veto, fix the veto first (it is the top fix) and rescore; do not tune other dimensions while a veto stands. With 2+ verified vetoes the result is `DONE` / `BLOCK`: no rounds.
- Revisions are the user's content. Only edit a draft the user gave you, and never invent data, quotes, credentials, reviews, or citations to lift an item; leave a clearly marked placeholder ("[add your measured result]") instead.

## Target band

State it before round 1. Default: **Good** (raw >= 75) on the profile-weighted total. If the user names another floor, use it.

## The loop

```
round = 0
score the draft (full 80-item pass) → raw, final, verdict
if 2+ vetoes fail: DONE + BLOCK, exit (no rounds)
if 1 veto fails: fix the veto, rescore, then continue
while final < target_floor AND round < 3:
    round += 1
    1. Rank dimensions by weighted contribution (dimension score x profile weight), ascending; take the 3 lowest
    2. Revise only those 3 dimensions (surgical edits; leave passing dimensions alone; no full rewrite)
    3. Rerun the full 80-item score → new raw/final
    4. If any veto now fails, stop the loop and report it (1 veto → FIX with 59 cap; 2+ → BLOCK)
stop when: band met OR round == 3 OR a round produced no gain
```

Pick the weakest dimensions by weighted contribution, not raw dimension score: a low score in a high-weight dimension costs more. Weights are in [scoring-rules.md](scoring-rules.md).

## Stop conditions

| Condition | Outcome |
|---|---|
| final >= target floor | Report the final score; status and verdict come from the truth table (SHIP still requires no fails) |
| 3 rounds done, still below band | `DONE_WITH_CONCERNS` / `FIX`; best score plus remaining weak dimensions in `open_loops` |
| A veto fails at any point | Stop; 1 veto → `DONE_WITH_CONCERNS` / `FIX` (cap 59); 2+ → `DONE` / `BLOCK` |
| A round produces no score gain | Stop early; note the plateau in `open_loops` |

## Per-round trail

```
Round 1: raw 64 → weakest [Ept .05 x 60 = 3.0, A .05 x 70 = 3.5, R .15 x 70 = 10.5] → revised → 71
Round 2: raw 71 → weakest [R .15 x 73.3 = 11.0, E .20 x 70 = 14.0, Exp .20 x 72.5 = 14.5] → revised → 78 (band met, stop)
```

After the loop, emit the standard handoff with the final round's `cap_applied`, `raw_overall_score`, and `final_overall_score`, and add `refinement_rounds: <n>` to `open_loops` so a later re-audit knows how much tuning already happened.

Learned-rejection memory (pre-deducting points for patterns rejected in past audits) is not part of this loop.
