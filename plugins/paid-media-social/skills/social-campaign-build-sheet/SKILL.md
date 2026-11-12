---
name: social-campaign-build-sheet
description: Convert an approved paid social plan, audience design, ad copy, and creative into an import-ready build sheet for Meta Ads Manager (bulk import), LinkedIn Campaign Manager, and TikTok Ads Manager, with campaigns, ad sets or ad groups, ads, objectives and optimization events, budgets, schedules, placements, audiences and exclusions, URLs with UTM parameters, consistent naming, and automated validation. Use whenever the user asks to build a social campaign, set up Meta, Facebook, Instagram, LinkedIn, or TikTok ads, create the bulk upload, or says build it out after audiences and creative are approved, even if they do not say build sheet.
---

# Social Campaign Build Sheet

Social builds fail in predictable ways: wrong optimization event, ad sets that overlap and fragment budget, missing exclusions, URLs without tracking, creative in the wrong aspect ratio, copy over truncation limits. A validated build sheet makes the build repeatable and gives the reviewer one place to approve.

## Principle: simple structure, explicit settings, validated before handoff
Fewer ad sets with enough budget beat many starved ones. Every setting that affects delivery or cost is written down, not left to defaults, and the sheet is checked by code before anyone imports it. Never write to a live account.

## Inputs
- Approved media plan or brief: objective, budget, flight dates, geo, targets
- Audience design output (audiences, exclusions, funnel stage, ad set mapping)
- Ad copy and creative inventory (copy variants by angle, asset file names, formats and sizes, video lengths), with compliance flags resolved
- `clients/<slug>/context.md`: naming convention, conversion events, pixel and page IDs, restrictions, brand rules
- UTM convention from the governance skill

## Process
1. **Structure.** Campaign per objective and funnel stage; ad sets or ad groups per audience, with budget sized so each can realistically exit learning (roughly 50 optimization events per week on Meta, more on others); ads per ad set as the plan specifies (usually several distinct angles and formats, not near-duplicates). State if you merged ad sets to protect learning.
2. **Naming.** Apply the team convention: client, platform, objective, funnel stage, audience, creative angle, date or version, parseable and sortable. Names must correspond to the UTM campaign values.
3. **Settings per level:**
   - Campaign: objective, special ad category declaration if applicable, buying type, budget optimization choice, spend limits, bid strategy
   - Ad set or ad group: conversion location and optimization event, attribution setting, budget and schedule, audience with exclusions, geo and language, placements (automatic by default unless there is evidence to restrict), bid or cost control only with a reason, and frequency cap where applicable (LinkedIn, reach campaigns)
   - Ad: format, primary text, headline, description, call to action, destination URL with UTMs, instant form reference for lead gen, pixel and Conversions API event mapping, creative file name
4. **Platform specifics.** Meta: aspect ratios by placement (1:1, 4:5, 9:16), text truncation lengths, dynamic creative or Advantage+ settings chosen deliberately. LinkedIn: audience size minimums, single image or document or video formats, lead gen form fields, text limits. TikTok: vertical video specs, caption limits, Spark Ads authorization if used.
5. **Lead forms.** If using instant forms, specify fields, qualifying questions, privacy policy URL, thank-you screen, and the CRM or email routing for lead delivery. Defer form quality to the lead form audit.
6. **Validate in code and fail on errors:** character limits for every text field per placement; URL format and UTM presence and case; asset existence, dimensions, file size, video length versus the specified format; naming convention conformance; duplicate ad sets targeting overlapping audiences; budget totals versus plan; missing exclusions; optimization event not available for the chosen objective; required fields for the platform import template. Output a validation report with errors and warnings.
7. **Launch summary tab:** objective, budget, flight, audiences, creative angles, targets, and what the reviewer is approving.

## Output
Save to `clients/<slug>/outputs/YYYY-MM/social-build-<campaign>.xlsx` with tabs per entity, a `Validation` tab, and a `Summary` tab, in the platform's import layout.
```
Bottom line (2 sentences): what is built, what is pending.
Path to sheet and validation result (errors, warnings).
Reviewer decisions and assumptions (merges, defaults chosen).
Next step: launch readiness checklist and policy precheck.
```

## Rules
- Never import or publish to a live account; mark the build `[NEEDS APPROVAL]`.
- Do not paper over validation errors; fix or report.
- Special Ad Categories restrict targeting; apply the restricted setup and route to policy review.
- Use only copy and creative that cleared compliance.
