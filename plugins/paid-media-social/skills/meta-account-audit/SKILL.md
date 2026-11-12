---
name: meta-account-audit
description: Audit a Meta (Facebook and Instagram) ads account covering pixel and Conversions API health, event and attribution setup, campaign objectives and structure, learning phase status and fragmentation, audiences and exclusions, creative performance and fatigue, placements, lead form and lead quality, budget and bidding, Special Ad Category compliance, and account quality, producing a scored scorecard with quantified waste and a ranked fix list. Use whenever the user asks to audit or review a Meta, Facebook, or Instagram ads account, asks why Meta ads are underperforming or leads are junk, inherits a social ad account, or wants a paid social health check, even if they only say look at the Facebook ads.
---

# Meta Account Audit

Meta rewards simple structures, healthy conversion signals, and a steady supply of fresh creative. Most underperforming accounts fail on one of those three: broken or thin signal, too many fragmented ad sets stuck in learning, or tired creative. This audit finds which one, and proves it.

## Principle: signal first, structure second, creative third
Meta's delivery optimizes toward the conversion event it is fed. If that event is wrong, duplicated, or too rare, nothing else matters. Verify signal quality before judging anything downstream, and label downstream findings provisional if signal is suspect.

## Inputs
- Read access to the ad account (API, connector, or exports): campaigns, ad sets, ads, breakdowns by placement, age, gender, device, and creative; 90 days of performance (30 days for fast-moving accounts)
- Events Manager data: pixel events, Conversions API events, match quality, deduplication
- `clients/<slug>/context.md`: goals, target CPA, qualified lead definition, restrictions
- CRM data if the account runs lead generation

## Audit areas (in order)
1. **Signal and tracking.** Pixel plus Conversions API both present, deduplication working (event id), event match quality, which events optimize each campaign, aggregated event measurement priorities, event volume per ad set (about 50 optimization events per week per ad set is the rule of thumb for exiting learning), attribution window. Hand deeper verification to the conversion tracking audit.
2. **Objective and optimization event fit.** Is each campaign optimizing for the right outcome given volume? Flag conversion campaigns starved of events that should optimize one funnel step higher, and lead campaigns optimizing for form fills with no quality feedback.
3. **Structure and fragmentation.** Count ad sets per campaign and budget per ad set. Flag many small ad sets, learning limited status, overlapping audiences competing against each other, and campaign budget optimization versus ad set budgets used sensibly.
4. **Audiences.** Broad versus interest versus lookalike mix, first-party list freshness and size, exclusions (existing customers, converters, employees), and retargeting windows and frequency.
5. **Creative.** Ads per ad set, format mix (static, video, carousel), hook rate and hold rate for video, CTR and CPA by ad, concentration (is one ad getting most spend), age of top ads, frequency and CTR decay, and whether messaging angles differ or are minor variations. Quantify fatigue with trend lines in code.
6. **Placements and delivery.** Automatic vs manual placements, performance by placement, Audience Network or low-quality placements consuming spend, device and age or gender skews.
7. **Lead generation quality** (if applicable). Instant form type and friction, qualifying questions, spam and low-quality lead share, time to first contact, and whether lead outcomes flow back to Meta.
8. **Budget and bidding.** Bid strategy vs goal, cost caps or bid caps set realistically against history, daily spend variability, and budget changes that reset learning.
9. **Special Ad Categories and policy.** Housing, employment, credit, and social issue categories declared when required, targeting restrictions respected, ad rejections and account quality warnings.
10. **Hygiene.** Naming, UTMs and URL parameters, page and Instagram account connection, business verification, domain verification.

## Scoring and impact
Score each area 0 to 5 with one sentence of evidence. Quantify, in code, spend in learning-limited ad sets, spend on fatigued ads (above frequency and CTR thresholds relative to the ad's own history), and spend on poor-quality placements. Show ranges and the date range used.

## Output
Save to `clients/<slug>/outputs/YYYY-MM/meta-audit.md` with an `.xlsx` of supporting tables.
```
Bottom line (3 sentences): account health and the largest issue.
Scorecard: area, score, evidence.
Top findings (max 10): evidence, impact range, fix, owner, effort, [NEEDS APPROVAL] for live changes.
Quick wins vs structural fixes.
Not audited and why.
```

## Rules
- Read-only; recommend, do not edit.
- Do not judge ad sets on under 7 days or before they exit learning unless something is clearly broken.
- Do not recommend consolidating everything by reflex. Consolidate only where fragmentation is actually starving delivery.
- Cite the date range and source for every number; compute in code.
