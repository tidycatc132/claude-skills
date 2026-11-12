---
name: campaign-build-sheet
description: Convert an approved search campaign plan, keyword research, and ad copy into an import-ready build sheet for Google Ads Editor or Microsoft Advertising Editor, with campaigns, ad groups, keywords with match types, negative keywords, responsive search ads, assets (sitelinks, callouts, snippets, calls), location and schedule settings, budgets, bid strategy, final URLs with tracking parameters, consistent naming, and automated validation. Use whenever the user asks to build a campaign, create the campaign structure, set up a new Google Ads or Microsoft Ads campaign, prepare the Editor import, convert keyword research into ad groups, or says build it out after a plan or keyword list is approved, even if they do not say build sheet.
---

# Campaign Build Sheet

Campaign builds fail in small, avoidable ways: a keyword in the wrong match type, an ad over the character limit, a missing negative, a URL without tracking, a campaign set to the wrong location option. A validated, import-ready sheet makes the build fast and repeatable and gives the reviewer something concrete to approve.

## Principle: the sheet is the deliverable and the validator is part of it
Produce the sheet in the format the platform's Editor imports, then run automated checks before handing it over. A human applies it after the launch gate. Never write to a live account.

## Inputs
- Approved media plan or brief: goal, budget, geo, schedule, bidding approach
- Keyword research output (groups, intent tiers, match types, landing pages)
- Ad copy output (RSA assets by ad group, with compliance flags resolved)
- Negative keyword list from keyword research and any existing account negatives
- `clients/<slug>/context.md`: naming conventions, geo, restrictions, conversion actions, tracking parameters, brand rules
- Existing account structure, if extending an account, to avoid duplicates

## Process
1. **Define the structure.** Campaigns by intent and business priority (for example, brand, high-intent services, mid-intent comparison, competitor if approved), ad groups by tight keyword themes with one matching landing page. Keep the count manageable for the budget so each campaign can gather data; say if you merged groups for that reason.
2. **Apply naming conventions** consistently: platform, client, campaign type, intent or service, geo, and date or version where the team uses them. Names should be sortable and parseable by reporting.
3. **Set campaign settings explicitly:** network (search partners and display expansion off by default unless justified), location targeting using the presence option for local service businesses unless there is a reason to include interest, location exclusions, languages, devices and bid adjustments if any, ad schedule, delivery, budget, bid strategy appropriate to conversion volume, target values from the context file, conversion goals linked to the primary actions, and start and end dates.
4. **Build keywords** with the planned match types, one theme per ad group, no cross-ad-group duplicates, and a record of which are brand versus non-brand.
5. **Build negatives** at account list, campaign, and ad group levels per the plan, with a collision check against the active keywords.
6. **Build ads:** import the RSA assets with pinning only where flagged, final URLs, display paths, and tracking templates or URL suffixes per the UTM convention. Use final URL expansion rules deliberately.
7. **Build assets:** sitelinks (with descriptions), callouts, structured snippets, call assets with the tracked number, location assets, lead forms or promotions where relevant, and image assets for campaign types that use them.
8. **Validate in code** and fail the build on errors: character limits for every text field, URL format and reachability, duplicate keywords, keyword and negative collisions, ad groups without ads or with fewer than the minimum assets, missing final URLs, budget totals against the plan, naming convention conformance, disallowed characters, and required columns for the Editor import format. Output a validation report with counts of errors and warnings.
9. **Create a launch summary** page: what is being built, budget, targets, and everything a reviewer needs to approve in one screen.

## Output
Save to `clients/<slug>/outputs/YYYY-MM/build-<campaign>.xlsx` with one tab per entity type in the Editor's import layout, plus a `Validation` tab and a `Summary` tab. Also save the CSV exports the Editor needs.
```
Bottom line (2 sentences): what is built and what is pending.
Path to the build sheet and the validation result (errors, warnings).
Decisions for the reviewer: judgment calls, assumptions, merges made.
Next step: launch readiness checklist.
```

## Rules
- Never import or apply the sheet to a live account. Mark the build `[NEEDS APPROVAL]` and route it through the launch readiness checklist and policy review.
- Do not paper over validation errors. Either fix them or report them.
- Keep structure as simple as the budget supports; do not create dozens of ad groups for a small account.
- Use only copy and claims that passed the creative and compliance steps.
