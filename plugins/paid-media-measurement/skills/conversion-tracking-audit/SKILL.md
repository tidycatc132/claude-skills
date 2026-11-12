---
name: conversion-tracking-audit
description: Audit a client's end-to-end conversion tracking (site events, GTM/gtag tags, GA4, Google Ads, Microsoft Ads, Meta pixel and Conversions API, LinkedIn, call tracking, form tracking, CRM and offline imports) and name the exact point where data breaks, doubles, or misleads. Use whenever conversions dropped or look wrong, platform and GA4 numbers disagree, a campaign is about to launch, call or form tracking needs setup, offline conversion import is being planned, or the user asks if the data can be trusted, even if they do not say audit. Also the required first step for any performance-drop investigation.
---

# Conversion Tracking Audit

Every optimization decision rests on conversion data. If that data is wrong, smart bidding learns the wrong lesson and reports mislead the client. This audit establishes whether the numbers can be trusted and, if not, where they fail.

## Principle: verify, label confidence, never fix live
Every finding carries a confidence label: **verified** (observed directly in the browser, network requests, or platform UI/API), or **inferred** (deduced from data patterns). This lets the reader know what to fix first and what to confirm. Never change tags, containers, or conversion settings. Write exact implementation instructions for a human or developer.

## Inputs
- Client context file (`clients/<slug>/context.md`): conversion actions that should count, platforms in use
- Site URL and the key conversion pages (form, thank-you, call button, checkout)
- Read access to GA4, ad platforms, and Tag Manager where connected
- Trailing 30 to 90 days of conversion data per platform

## Audit sequence
Work down the chain in order. Record each link as pass, partial, fail, or not checked.

**1. Site layer.** Using a browser tool, load each conversion page. Confirm what the user does and what event or page view should fire. Check for forms that submit without a page change, embedded third-party forms (iframes break tag access), click-to-call links, chat widgets, and booking tools.

**2. Tag layer.** Inspect network requests when a conversion is triggered. Check for: the tag firing at all, firing once (duplicates are common after a plugin plus a manual install), firing on the right trigger (not on page load of a form page), correct parameters (value, currency, transaction id), cross-domain handling, and consent behavior. Note the tag manager container publish history around any date of change.

**3. GA4 layer.** Key events configured and marked correctly, event counts plausible against sessions, unwanted referrals and self-referrals, internal traffic filters, attribution settings, and data-stream health.

**4. Ad platform layer.** For each platform: which conversion actions exist, which are primary versus secondary and whether that matches what bidding should optimize for, counting method (one vs every), attribution model and window, conversion value setup, enhanced conversions and match quality (Google), Conversions API deduplication with the pixel and event match quality (Meta), auto-tagging on, and imported-versus-native duplicates counting the same lead twice.

**5. Call and form layer.** Call tracking number swapping works and is scoped sensibly, call duration thresholds, form submissions reaching the CRM with source data preserved, hidden-field capture of click ids and UTMs.

**6. Offline and CRM layer.** Is lead quality or closed revenue fed back? If not, specify the loop: which identifiers to capture (GCLID, FBCLID, hashed email and phone), where they live, and the import cadence.

**7. UTM and naming governance.** Check campaign URLs for consistent source, medium, campaign naming. Flag mixed casing, missing parameters, and untagged links that fall into direct or unassigned.

## Reconciliation
Compare platform conversions to GA4 and to CRM/call records over the same dates and time zone. Some gap is normal because of attribution models, windows, and consent. Quantify the gap per platform and call it within tolerance (about 20%) or a real problem. Explain the most likely causes. Use code for the arithmetic.

## Output
```
Bottom line: Is the data trustworthy? Yes / Partial / No, and what that means for current decisions (for example, pause smart bidding target changes until fixed).

Chain status table: each link, result, confidence label (verified/inferred).

Reconciliation table: platform vs GA4 vs CRM, gap %, verdict.

Findings: ranked by impact. Each has evidence, why it matters, and exact fix steps for the implementer, marked [NEEDS APPROVAL] for live changes.

Impact on reporting: which historical numbers are unreliable and from what date.

Not checked: what could not be reached and why.
```
Save to `clients/<slug>/outputs/YYYY-MM/tracking-audit.md`.

## Rules
- If tracking is broken, say so in the first line and recommend holding optimization decisions until it is fixed.
- Do not trust a platform's "conversion tracking active" badge. Verify firing.
- Do not submit real forms or place calls on a live client site without approval. Use test modes, preview tools, or ask for a test submission.
