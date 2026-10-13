# Output Format: Report, Handoff, Saved File

## 1. Conversation report (in this order)

```markdown
## CORE-EEAT Audit
**Status:** `DONE` | `DONE_WITH_CONCERNS` | `NEEDS_INPUT` | `BLOCKED`
**Verdict:** `SHIP` | `FIX` | `BLOCK` | `UNDECIDED`
**Score state:** `SCORED` | `NOT_SCORED`
**Profile / target / observed:** <profile> / <target> / <YYYY-MM-DD>
**Raw score:** <number> | omitted
**Final score:** <number> | omitted
**Confidence:** high | medium | low | not_scored

<One or two plain-language sentences: the decision, the material limitation, the single most important fix.>

**Context:** market <..> · publication state <..> · catalog CORE-EEAT 20.1.0 · coverage <x>% (<observed>/<applicable>)

### Unknown items            <- only when any applicable item is unknown
- `CORE-EEAT-<ID>`: `unknown` — <what was not observed> · resolves with <evidence needed>

### Vetoes
| Veto | State | Evidence |
|---|---|---|
| `CORE-EEAT-C01` | pass / partial / fail / unknown | ... |
| `CORE-EEAT-R10` | pass / partial / fail / unknown | ... |
| `CORE-EEAT-T04` | pass / partial / fail / na / unknown | ... |

### Dimension scores
| Dim | Applicable | Observed | Score | Weight | Contribution |
|---|---:|---:|---:|---:|---:|
(one row per dimension C, O, R, E, Exp, Ept, A, T; exact values to 4 decimals)
| **Total** | | | | | <exact> → floor <raw> |
(Incomplete runs: replace Score/Contribution with Lower/Upper columns and show the interval.)

GEO diagnostic (C+O+R+E)/4 = <..> · SEO diagnostic (Exp+Ept+A+T)/4 = <..> — diagnostics, not totals.
Cap: <none | one veto → min(raw, 59) = .. | 2+ vetoes → no final score>
Confidence: <mean reliability arithmetic → level>

### Critical evidence
<3-6 bullets: the evidence behind the verdict, each with source + date + evidence type>

### Findings (ordered by severity, then weighted points lost)
| # | Item | State | Severity | Weighted pts lost | Evidence | Fix |
|---|---|---|---|---:|---|---|
Severity order: veto > fail > partial. Weighted pts lost = (10 - points) x 10 / n_dim x weight.

### Fix plan (prioritized)
1. <veto fixes first> ...
2. <highest weighted gain next> ...
Each fix: what to change, where, expected item state after the fix, weighted gain.

### Item appendix          <- always for NEEDS_INPUT; otherwise when the user asks for detail or reproducibility
Per dimension: ID | item | state | points | source | source date | evidence type | confidence | note
`na` rows carry the condition-based reason.
```

Presentation rules:
- Lead with the decision and the material limitation; plain language first, traceability in the appendix.
- Qualify item IDs (`CORE-EEAT-T04`) whenever they appear outside a single CORE-EEAT table; never show a bare collision-prone ID in prose.
- Explain raw vs capped score when a cap applies; never imply the capped number is the observed raw quality.
- Distinguish Unknown from Fail and N/A, and state what evidence resolves each Unknown.
- Label humanizer findings and GEO/SEO views as advisory diagnostics.
- Separate fact, calculation, estimate, proxy, and recommendation. No outcome predictions.

## 2. Handoff summary (end of every run)

```yaml
status: DONE | DONE_WITH_CONCERNS | NEEDS_INPUT | BLOCKED
objective: "CORE-EEAT audit of <target> as <profile> for <market>, <publication_state>"
key_findings:
  - <evidence-backed finding, with qualified ID>
evidence:
  - type: measured | user-provided | calculated | estimated | proxy
    ref: <URL / section / export name>
    observed_at: <YYYY-MM-DD>
assumptions:
  - <explicit assumption, or none>
open_loops:
  - <every unknown item and what resolves it; refinement_rounds if the loop ran; or none>
recommended_next_skill: <one skill or none>
# auditor extension
framework: CORE-EEAT
catalog_version: 20.1.0
profile: <profile>
target: <target>
observed_at: <YYYY-MM-DD>
context: {"content_type":"<profile>","market":"<market>","publication_state":"<state>"}
evidence_coverage: <0-100>
score_state: SCORED | NOT_SCORED
score_confidence: high | medium | low | not_scored
verdict: SHIP | FIX | BLOCK | UNDECIDED
veto_count: <number of verified veto fails>
cap_applied: true | false
raw_overall_score: <n>      # omit when NOT_SCORED
final_overall_score: <n>    # omit when NOT_SCORED or 2+ vetoes
```

If verdict is `SHIP` with `score_confidence: low`, the first line of the handoff is the confidence caveat ("Provisional SHIP: evidence mix is weak (<reason>); confirm with stronger evidence.").

## 3. Saved file (only after the user says yes)

Path: `seo-reports/content-quality-auditor/YYYY-MM-DD-<topic-slug>.md` in the working directory (date = observed_at). Write it once, with the full content, in this shape:

```markdown
---
class: auditor-output
schema_version: 3.0
runbook_version: 3.0.0
catalog_version: 20.1.0
framework: CORE-EEAT
profile: product-review
---

status: DONE_WITH_CONCERNS
verdict: FIX
score_state: SCORED
objective: "Audit product review publish readiness for the US market"
target: "https://example.com/x200-robot-vacuum-review"
observed_at: 2026-10-12
context: {"content_type":"product-review","market":"US","publication_state":"live"}
key_findings:
  - title: "Affiliate buttons have no disclosure"
    severity: veto
    evidence: "Rendered desktop and mobile captures 2026-10-12; 6 affiliate links, no disclosure text"
evidence_summary: "Rendered page, author page, policy pages, backlink export; frozen 2026-10-12"
evidence_coverage: 100
score_confidence: high
open_loops: "Add disclosure above first affiliate CTA and rerun product-review profile"
recommended_next_skill: none
veto_count: 1
cap_applied: true
raw_overall_score: 78
final_overall_score: 59

<full conversation report from section 1 follows>
```

Self-check before saying it was saved:
- Frontmatter has class, schema_version, runbook_version, catalog_version, framework, profile; profile is one of the nine.
- `context` is single-line strict JSON with content_type, market, publication_state.
- `veto_count` equals the number of `severity: veto` findings; every veto finding has an evidence pointer.
- Pairings: SHIP and BLOCK ↔ DONE; FIX ↔ DONE_WITH_CONCERNS; UNDECIDED ↔ NEEDS_INPUT or BLOCKED.
- 0 vetoes: `cap_applied: false`, final = raw. 1 veto: `cap_applied: true`, final = min(raw, 59). 2+ vetoes: `cap_applied: false`, no final score.
- SCORED: coverage 100, confidence high/medium/low, raw present; SHIP requires raw >= 75.
- NOT_SCORED: both scores omitted, `score_confidence: not_scored`.
- `open_loops` is non-empty (`"none"` when closed). No credentials or unnecessary personal data.
- Read the file back after writing; only then say it was saved. Write nothing else (no veto markers, caches, or extra files).
