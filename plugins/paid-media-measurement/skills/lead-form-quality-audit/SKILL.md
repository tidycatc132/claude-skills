---
name: lead-form-quality-audit
description: Audit the quality of leads from paid media and the forms that capture them, covering instant forms (Meta, LinkedIn, TikTok, Google lead form assets) and website landing page forms, by analyzing form friction and field design, spam and invalid contact rates, qualified rate, speed-to-lead, contact rate, duplicates, source and campaign differences, CRM routing, and feedback loops, then recommend form changes, filtering, and follow-up improvements. Use whenever the user says the leads are junk, low quality, fake, unqualified, or never answer the phone, asks how to improve lead quality, whether instant forms or landing pages produce better leads, how to cut spam leads, or how to qualify leads before the sales team calls, even if they only say our leads are bad.
---

# Lead Form Quality Audit

Cheap leads that never turn into customers are the most expensive thing in paid media. Lead quality is shaped by the offer, the form, the audience, and what happens in the first minutes after submission. The platform cannot see any of that unless it is told. This audit finds which of those four is failing and fixes it with the least friction.

## Principle: friction is a filter, and the right amount depends on the goal
Short forms raise volume and lower quality; added questions cut volume and raise quality. Neither is correct by default. Choose friction based on sales capacity and the cost of a bad lead, and measure outcomes past the form fill.

## Inputs
- Lead records for 60 to 90 days: timestamp, source, platform, campaign, ad set or ad group, ad, form or page, all submitted fields, and any CRM status (contacted, qualified, booked, won, lost reason)
- Form definitions: fields, order, required status, qualifying questions, consent and privacy text, thank-you flow
- Sales follow-up data: time to first contact, number of attempts, contact rate
- `clients/<slug>/context.md`: qualified lead definition, sales capacity, restrictions, goals

If CRM outcomes are missing, analyze what can be measured from the lead data alone (validity, spam patterns, duplicates, form completion) and recommend the feedback loop.

## Process
1. **Define quality** using the client's qualified lead definition. Build outcome funnel metrics by source in code: lead, contacted, qualified, booked, won, with rates and median time between stages.
2. **Measure lead validity:** invalid or disposable emails, phone numbers that fail format or carrier checks, repeated phone or email across entries, names that look auto-generated, identical or nonsensical free-text, rapid-fire submissions from the same source, and mismatch between stated geo and campaign geo. Report spam rate by campaign, ad set, placement, and form.
3. **Compare sources.** Instant forms versus landing pages, platform versus platform, campaign versus campaign, audience versus audience, creative angle versus angle. Differences in qualified rate often explain more than differences in cost per lead.
4. **Audit the form design:** number of fields; required versus optional; question order; use of qualifying questions (budget, timeline, service needed, location); dropdowns versus free text (dropdowns reduce junk); prefilled fields on instant forms (prefill reduces effort and invites careless submissions, and higher-intent options such as the review step or higher-intent form type add friction that improves quality); consent text; and whether the form promises what happens next.
5. **Audit speed-to-lead.** Time to first contact is often the biggest quality lever. Chart contact rate versus response time. Check after-hours handling, routing rules, and follow-up sequences.
6. **Audit the feedback loop.** Are qualified outcomes sent back to the ad platforms? If not, recommend the offline conversion plan.
7. **Spam and bot defenses** for website forms: honeypot fields, reCAPTCHA or invisible challenges, email and phone validation, rate limiting, and filtering rules in the CRM. For instant forms, review platform-side options and lists of exclusions.
8. **Recommend changes** with expected tradeoffs (volume down, quality up), ordered by impact over effort, and design a test: form variant A versus B, one change at a time, deciding metric qualified leads or cost per qualified lead, not raw leads.

## Output
Save to `clients/<slug>/outputs/YYYY-MM/lead-quality-audit.md` with an `.xlsx` of the funnel and validity tables.
```
Bottom line (2 sentences): where lead quality breaks and the biggest fix.
Funnel table by source: leads, spam %, contacted %, qualified %, booked %, won %, cost per qualified lead.
Form audit findings.
Speed-to-lead analysis.
Recommended changes with expected volume and quality tradeoffs.
Test plan.
Data gaps (for example, missing CRM outcomes).
```

## Rules
- Handle lead data with care: do not copy personal information into reports; aggregate and anonymize.
- Do not blame the platform before checking the offer, the form, and the follow-up speed.
- Label small-sample conclusions as directional.
- Read-only; recommend changes for humans to apply.
