# Paid media department plugins

Located at `plugins/paid-media/`. Future departments get their own sibling folder under `plugins/`. Six thematic plugin bundles (41 skills) for an agentic paid media team. They live outside `skills/` on purpose: these are drafts that have not been through the `/new-skill` harness (no trigger or output evals yet). Promote individual skills into `skills/` one per session through `/new-skill` when they are ready.

| Plugin | Skills |
|---|---|
| paid-media-ops | client-context-intake, budget-pacing-report, ad-account-health-check, ppc-weekly-optimization, ppc-anomaly-triage, wasted-spend-finder, impression-share-diagnostic, optimization-task-pusher |
| paid-media-measurement | conversion-tracking-audit, platform-vs-ga4-reconciliation, utm-governance, offline-conversion-import-plan, lead-form-quality-audit |
| paid-media-search | ppc-keyword-research, search-term-mining, campaign-build-sheet, bid-strategy-decision, google-ads-account-audit, pmax-audit, lsa-setup-checklist |
| paid-media-social | meta-account-audit, linkedin-ads-audit, social-audience-builder, social-campaign-build-sheet, creative-fatigue-check |
| paid-media-creative-compliance | rsa-copy-generator, social-ad-copy-variants, creative-brief-for-design, ad-library-swipe-file, ad-test-planner, lp-message-match-audit, ad-policy-precheck, industry-restrictions-matrix, launch-readiness-checklist |
| paid-media-strategy-reporting | allowable-cpa-calculator, media-plan-builder, budget-forecast-model, auction-insights-analysis, ppc-monthly-report, executive-summary-writer, qbr-deck-builder |

## Install (after merge)
```
/plugin marketplace add tidycatc132/claude-skills
/plugin install paid-media-ops@wise-skills
```

## Shared conventions
Client files live in `clients/<slug>/context.md` with outputs in `clients/<slug>/outputs/YYYY-MM/`. Skills are read-only against ad accounts by default; changes are marked `[NEEDS APPROVAL]`. Numbers are computed in code.
