---
name: platform-vs-ga4-reconciliation
description: Reconcile conversion and spend numbers between ad platforms (Google Ads, Microsoft Ads, Meta, LinkedIn), GA4, and the CRM or call system for the same period, quantify each gap, explain likely causes (attribution model and window differences, view-through and cross-device credit, consent mode and cookie loss, ad blockers, import delays, duplicate or missing events, bot traffic, time zone and currency differences, Conversions API match quality), and judge whether each gap is normal or a real tracking problem. Use whenever the user says numbers do not match, Google Ads shows more conversions than GA4, Meta and GA4 disagree, the client says the leads do not match what we report, or asks which source to trust, even if they never say reconciliation.
---

# Platform vs GA4 Reconciliation

Platforms and analytics tools measure the same business with different rules, so their numbers should differ. The job is not to force agreement but to know how much difference is normal, why it exists, and when a gap signals broken tracking. Clients lose trust in reports when they cannot reconcile, so this skill produces an explanation they can follow.

## Principle: align the comparison before judging the gap
Most apparent discrepancies vanish when time zone, date range, conversion definition, counting method, and attribution basis are aligned. Align first; interpret second.

## Inputs
- Ad platform exports for the period: spend, clicks, conversions by action, by conversion date and by click date where available
- GA4: sessions by source and medium, key events, conversions by source with the attribution model used
- CRM or call platform records for the same period (counts of leads by source, qualified leads, closed deals)
- Platform and account time zones and currencies; GA4 property time zone
- `clients/<slug>/context.md`: conversion definitions, tracking status

## Process
1. **Align the basis.** Same date range and time zone; convert currencies; use the same conversion definition (for example, form submissions only, excluding calls); compare platform conversions by click date versus conversion date explicitly, because they diverge with conversion lag; note platform attribution model and window versus GA4's.
2. **Compare traffic first.** Platform clicks versus GA4 sessions (and users) from that source and medium. Clicks should exceed sessions by a modest margin (bounces before load, double clicks, bots, tag blockers). A large gap points to tagging, redirects, auto-tagging, or page speed problems. Compute the ratio and compare to prior periods.
3. **Compare conversions.** Compute platform versus GA4 versus CRM counts per source and the percentage gap. Compare to the account's own historical gap: a stable gap is normal; a sudden change in the gap is the signal.
4. **Diagnose the gap using a checklist,** ordered by likelihood:
   - Attribution differences: platforms credit view-through and cross-device and use data-driven or last-click models with set windows; GA4 uses its own model and may attribute to organic or direct
   - Consent and cookies: consent mode status, share of users denying consent, modeled conversions in the platform that GA4 may not show, browser tracking prevention
   - Counting: every-conversion versus one-per-click, duplicate firing, secondary actions included in the platform total
   - Imports and lag: delayed uploads, CRM syncs, conversions recorded on later dates
   - Tag problems: missing events on some pages or devices, broken cross-domain, thank-you page reloads, conversions firing on refresh
   - Match quality: Conversions API event match quality and deduplication for Meta, enhanced conversions coverage for Google
   - Traffic quality: bots and spam submissions counted by the platform but filtered in the CRM
   - Source labeling: missing UTMs or auto-tagging causing GA4 to file paid traffic as direct, organic, or unassigned
5. **Judge each gap.** Use a working tolerance of roughly 20 percent between platform and GA4 and expect CRM counts to be lower once spam is removed; adjust by account history. Within tolerance and stable: normal. Outside tolerance or changed: investigate and name the probable cause with the evidence. Label each conclusion as verified or inferred.
6. **Recommend a source of truth by purpose.** For example: platform data for in-platform optimization, GA4 for cross-channel journey and site behavior, CRM for lead quality and revenue. Recommend which number to put in client reports and how to word the footnote.
7. **Recommend fixes** for real problems, handing deep verification to the conversion tracking audit.

## Output
Save to `clients/<slug>/outputs/YYYY-MM/reconciliation.md` with an `.xlsx` of the aligned tables.
```
Bottom line (2 sentences): are the numbers consistent enough to trust, and which gap matters.
Aligned comparison table: platform, clicks, GA4 sessions, platform conversions, GA4 conversions, CRM count, gaps.
Gap diagnosis: each gap, likely causes, evidence, verdict (normal / investigate / broken).
Source-of-truth guidance and client-facing wording.
Fix list with owners.
Assumptions and data gaps.
```

## Rules
- Never average conflicting sources into one number. Report each with its definition.
- Do not call a gap a tracking error without evidence; many gaps are model differences.
- Compute in code; state date ranges, time zones, and definitions beside every figure.
- Read-only; recommend fixes, do not change tags or settings.
