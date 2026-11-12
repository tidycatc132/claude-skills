---
name: ad-policy-precheck
description: Review ad copy, creative descriptions, landing pages, and account setups against Google Ads, Microsoft Advertising, Meta, LinkedIn, and TikTok advertising policies before launch, flag likely disapproval or account risk with the specific policy area and a compliant rewrite, and when an ad is already disapproved, diagnose the cause and draft the appeal. Use whenever the user asks if an ad will get approved, wants a policy check, has a disapproved or limited ad or suspended account, asks about restricted content, claims, or special ad categories, or asks to draft an appeal, even if they just say Google rejected my ad.
---

# Ad Policy Precheck

A disapproval after launch costs days of delay and can put an account's standing at risk. Most violations are predictable: unsupported claims, restricted categories, misleading formatting, destination problems, or missing disclosures. This skill catches them before submission and handles appeals after.

## Principle: policy changes, so verify and cite
Platform policies change often and differ by country and industry. Look up the current policy page for the platform and category before concluding, and cite it. When the policy is ambiguous, say so and choose the conservative reading. This is a risk screen, not a guarantee of approval; the platform decides.

## Inputs
- Ad text, creative descriptions or files, landing page URL, target geography, advertiser industry
- `clients/<slug>/context.md`: licenses, certifications, restricted-category status, prior disapprovals
- For appeals: the exact disapproval message, the policy name shown, the ad and page involved

## Process (precheck)
1. **Classify the advertiser and offer** for restricted or regulated categories (health, finance, legal, housing, employment, credit, alcohol, gambling, political, supplements, weapons, adult, financial services, cannabis and CBD, data collection).
2. **Check each asset against common policy areas:**
   - Editorial and format: capitalization, punctuation, symbols, repetition, gimmicky text, phone numbers in text, unclear relevance
   - Claims: superlatives without proof, guarantees, unrealistic results, before and after, health or income claims, price claims that differ from the page
   - Misrepresentation: fake urgency, deceptive buttons, hidden fees, impersonation
   - Personal attributes and sensitive categories: implying knowledge of a person's health, finances, race, religion, orientation, or status (especially Meta and LinkedIn)
   - Trademarks and competitor names, and use of reviews or endorsements
   - Destination: working page, matching content, required disclosures, privacy policy, contact information, no malware, no mismatch with the ad
   - Special ad categories and certifications that must be applied for before launch
3. **Rate each finding** high, medium, or low risk with the policy name, the exact text or element, and the reason.
4. **Provide a compliant rewrite** for every flagged item that keeps the intent. If the claim cannot be substantiated, remove it and list what proof the client could supply.
5. **List pre-launch requirements:** certifications, verification, special category selection, disclosures, and documents.

## Process (disapproval and appeal)
1. Read the exact status and policy. Identify what triggered it (ad text, destination, account, or landing page content).
2. Diagnose, fix the cause first, and confirm the fix is live before appealing.
3. Draft the appeal: short, factual, referencing the policy name, stating what was changed or why the content complies, with supporting evidence. Never argue or complain in an appeal.
4. State what to do if the appeal fails (alternate wording, remove the claim, escalate through the platform rep) and note repeated violations can affect the account.

## Output
Save to `clients/<slug>/outputs/YYYY-MM/policy-precheck-<campaign>.md`.
```
Bottom line (2 sentences): ready to submit, or what blocks it.
Findings table: asset, issue, policy, risk, fix.
Rewrites.
Pre-launch requirements.
Appeal draft, if applicable.
Sources: policy pages consulted, with the date checked.
```

## Rules
- Never advise evading review (cloaking, rotating domains, disguised text, creating accounts to circumvent a suspension).
- Do not promise approval.
- Flag legal questions (licensing, regulated claims) for the client's counsel; this is not legal advice.
- Do not submit appeals or edit accounts; deliver drafts for a human to send.
