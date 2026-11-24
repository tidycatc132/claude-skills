---
name: launch-readiness-checklist
description: Run a pre-launch verification of a new or relaunched paid media campaign across strategy, account setup, targeting, budget, bidding, conversion tracking, UTMs, ad and asset approval, policy status, landing page, and reporting, producing a pass, fail, or blocked status for each item with evidence and a go or no-go recommendation. Use whenever a campaign is about to launch, the user asks for a launch checklist, QA of a campaign build, pre-flight check, go-live review, or asks if a campaign is ready, even if they only say can we turn this on.
---

# Launch Readiness Checklist

Launch mistakes are cheap to catch before spend begins and expensive after. This skill is the single gate between a finished build and live spend: it checks the build against the plan, verifies the tracking really works, and issues a go or no-go with evidence for every line.

## Principle: verify, do not assume
A checkbox ticked from memory is worth nothing. Each item gets a status of PASS, FAIL, or BLOCKED (cannot be verified yet), with the evidence or the reason. Any FAIL on a critical item stops the launch.

## Inputs
- The approved media plan and campaign build sheet
- Account access or exports of the built campaigns (read-only)
- `clients/<slug>/context.md`: goals, budgets, restrictions, approval contacts
- Landing page URLs, conversion definitions, UTM convention

## Checklist
Critical items are marked [C]; a fail on any blocks launch.
1. **Plan match.** Campaign names, goals, geos, languages, budgets, schedules, and structure match the approved plan. [C]
2. **Budget and billing.** Daily budgets and caps correct, payment method active, no accidental shared budgets, monthly cap understood. [C]
3. **Targeting.** Locations (presence versus interest setting), exclusions, audiences, devices, ad schedule, languages, network settings (search partners and display expansion on or off by intent). [C]
4. **Bidding.** Strategy and targets match the plan and the volume rule; learning phase expectations noted.
5. **Keywords and negatives.** Match types, shared negative lists applied, brand and competitor handling, no cross-campaign conflicts.
6. **Ads and assets.** Complete responsive sets, character limits met, no placeholders, sitelinks and extensions present, correct final URLs, creative specs correct, copy approved by the client. [C]
7. **Policy status.** No disapprovals or limited statuses; restricted-category prerequisites done; precheck findings resolved. [C]
8. **Landing pages.** Live, fast, mobile-friendly, match the ads, form and phone work end to end with a real test submission. [C]
9. **Conversion tracking.** Primary conversions fire once on the right event, values and currency correct, deduplicated, imported to the right goals, test conversion seen in the platform and in analytics. [C]
10. **UTMs and auto-tagging.** Parameters follow the convention and survive redirects.
11. **Integrations.** CRM or lead routing receives the test lead with source data; call tracking numbers swap correctly.
12. **Audience and data policies.** Consent and privacy requirements met, no sensitive data in pixels.
13. **Reporting.** Dashboard or report points at the new campaigns, naming consistent, baseline and success metrics recorded.
14. **Monitoring plan.** Who checks spend and disapprovals in the first 24 hours, day 3, and day 7; alert thresholds set.
15. **Approvals.** Client sign-off on budget, copy, and start date recorded. [C]

## Process
Work through each item against the live build or exports. Run any count or consistency check (character limits, naming, budget totals) in code. For each result record status and evidence. Do not enable campaigns, edit settings, or submit forms; produce fixes as instructions for the owner.

## Output
Save to `clients/<slug>/outputs/YYYY-MM/launch-checklist-<campaign>.md`.
```
GO / NO-GO with a one-line reason.
Checklist table: item, critical flag, status, evidence, owner for fixes.
Blockers, ordered.
Items verified after launch (tracking confirmation at 24 hours, first search terms review).
```

## Rules
- BLOCKED is not PASS. List what is needed to verify it.
- Never recommend GO with an open FAIL on a critical item.
- A test conversion must be observed, not inferred from tag presence.
- Record the date and time of checks; a launch check goes stale if edits follow it.
