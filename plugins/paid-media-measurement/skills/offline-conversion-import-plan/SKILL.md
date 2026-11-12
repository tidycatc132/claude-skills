---
name: offline-conversion-import-plan
description: Design and document an offline conversion tracking loop that sends lead quality stages and closed-won revenue from a CRM or call system back to Google Ads (offline conversion import, enhanced conversions for leads), Microsoft Advertising, and Meta (Conversions API for CRM events), including identifiers to capture, field mapping, stage definitions, value rules, import cadence, privacy and consent requirements, validation, and how to switch bidding to the new signal. Use whenever the user wants ad platforms to optimize for qualified leads or sales instead of form fills, says leads are junk, wants to connect the CRM to Google or Meta ads, asks about offline conversions, GCLID or FBCLID capture, enhanced conversions for leads, or closed-loop attribution, even if they only say we need better lead quality from ads.
---

# Offline Conversion Import Plan

Bidding systems optimize for whatever conversion they are given. When that is a form fill, they find more form fills, including cheap, low-quality ones. Feeding back what happens after the lead (qualified, booked, sold, and for how much) teaches the system what a good lead looks like. The plan must be implementable by whoever owns the CRM and the website, so it is written as a specification, not a concept.

## Principle: capture the identifier first, define stages second, feed back third
The whole loop fails if the click identifier or hashed contact data is not stored with the lead at submission. Verify capture before designing anything downstream, and plan for the sales cycle length, since feedback arrives late.

## Inputs
- `clients/<slug>/context.md`: goals, lead definition, volume, platforms, sales cycle, CRM and form tools
- CRM or call platform details: system name, pipeline stages, how leads are created (forms, calls, chat, imports), who owns it, export or API options
- Website form and call tracking setup (from the tracking audit, if one exists)
- Current lead volume per month and approximate close rate

If CRM details are missing, produce the plan with the CRM-specific steps marked `[CONFIRM WITH CRM OWNER]` rather than stopping.

## Process
1. **Assess feasibility.** Monthly lead volume and expected qualified and closed counts. Platforms need enough events to learn: if closed-won volume is tiny, use an earlier stage (qualified, appointment held) as the optimization signal and send closed-won as value data, and explain why.
2. **Define the stage ladder.** Map CRM stages to conversion events, for example: lead submitted, qualified (meets criteria), appointment or estimate booked, closed-won. For each, specify the exact CRM trigger, event name per platform, whether it is a primary (optimized) or secondary (observed) action, and the value assigned (actual revenue or margin where known; modeled value per stage where not, with the derivation shown).
3. **Specify identifier capture.** On the site: store the Google click id (GCLID, plus GBRAID and WBRAID for iOS cases), Microsoft click id (MSCLKID), and Meta click and browser ids (fbclid, fbc, fbp) in hidden form fields or first-party storage at landing, persist across pages, and write them into the lead record in the CRM. For calls, specify call tracking to CRM linkage. List the exact fields to add in the CRM.
4. **Specify hashed customer data** (email, phone) where the platform supports matching without click ids: normalization and SHA-256 hashing rules, and consent requirements.
5. **Design the transport.** Options per CRM: native integration, a connector or automation tool, scheduled CSV upload, or direct API. Recommend the simplest reliable option, with cadence (daily is typical; platforms have conversion windows and upload deadlines), time zone handling, deduplication keys, and retry behavior.
6. **Deduplicate and avoid double counting.** Tag conversions with unique order or lead ids. Ensure the imported action is not also counted by the on-site tag, and that Meta's pixel and Conversions API events dedupe by event id.
7. **Privacy and consent.** Confirm lawful basis, privacy policy language, and platform policy compliance for uploading customer data. Flag healthcare, legal, and financial clients for compliance review before any data leaves the CRM, because sensitive categories restrict what may be shared.
8. **Validation plan.** Test with a small batch, check diagnostics in each platform (match rates, rejected rows), reconcile counts against the CRM, and monitor weekly.
9. **Bidding transition.** Once enough imported conversions accumulate (for example 30 or more over a rolling window), switch the primary action in the campaign goals, keep the old action as secondary during transition, and follow the bid strategy decision process. Warn that attribution lag means recent days will look under-counted.
10. **Reporting changes.** Define how reports will show leads versus qualified leads versus revenue, and how the lag is explained to the client.

## Output
Save to `clients/<slug>/outputs/YYYY-MM/offline-conversion-plan.md` with a field mapping spreadsheet (`.xlsx`: CRM field, source, platform parameter, format, example).
```
Bottom line (2 sentences): feasibility and the recommended optimization signal.
Stage ladder table.
Identifier capture spec for developers.
CRM and transport spec for the CRM owner.
Privacy and consent checklist.
Validation and monitoring plan.
Bidding transition plan.
Open items: [CONFIRM WITH CRM OWNER] list.
```

## Rules
- Never upload or send customer data. Produce specifications and templates; humans implement.
- Do not invent values for stages. Derive them from client data or label them as modeled assumptions.
- Flag consent and sensitive-category concerns prominently; do not treat privacy as an afterthought.
