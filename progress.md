# Progress log

Newest entries at the bottom. One entry per session: what shipped, what was hard, what the next session must know.

## 2026-10-09 Harness reoriented: no backlog, fresh skills only
- Removed the kit's example skills, their evals, fixtures and contract, and the `/next-skill` command. `skills_backlog.json` is now an empty list that the scripts still read; nothing is planned there.
- `scripts/selftest.py` generates its own synthetic skill pair, so the harness self-test runs on an empty `skills/`.
- Every skill now starts with `/new-skill <description>`. Sibling skills are read only for their `description` line, to write the boundary sentence.
- Next: build the first real skill with `/new-skill`. Expect `/verify-skill` to spend tokens on real trigger and output evals.

## 2026-10-12 seo-drift-monitor: first real skill shipped
- Shipped `skills/seo-drift-monitor`: `scripts/snapshot.py` (saved HTML via `manifest.csv`, live URLs or sitemap, `rankings.csv`, indexed count, into one JSON) and `scripts/diff_snapshots.py` (severity-rated `drift_changes.csv` + `drift_report.md` with a `VERDICT:` line and likely causes). Rules live in `references/drift-rules.md`, input sourcing in `references/data-sources.md`. No siblings yet, so the boundary sentence names job types, not skills; update it when an audit, schema or keyword skill lands.
- Evals: 8 should / 9 should-not trigger prompts; 2 output cases on a fixture site (5 pages before a bad redeploy, 6 after) with 18 deterministic assertions pinning exact CSV rows plus one rubric. Verified: trigger 17/17 (after the description edit; 16/16 before it), output 2/2 with judge, reviewer PASS with no blockers.
- What was hard: the output eval failed 2 of 3 early runs with no files written. Cause: the sandbox allow-list is `Bash(python3 *)`, `ls`, `cat`, `mkdir` only, and the model chained `head` or `cd` into the command, so the whole Bash call was denied and it gave up. Fix was one SKILL.md line: run each script as its own plain `python3` command, paths as arguments, inspect inputs with the file-reading tool. After it, 3/3 runs passed. Lesson for every future skill with scripts: say this explicitly, or the output eval is a coin flip.
- Not covered by output evals (scripts tested by hand only): `indexed_count` rules, `--fail-on` exit code 3, a URL missing from the current snapshot, `redirect_to`. A third fixture snapshot would close that; the reviewer suggested it.
- Reviewer concern deferred: "why did clicks drop last month" with no snapshots is a near-neighbour that a Search Console connector should own; no eval prompt for it yet because the right answer is debatable.
