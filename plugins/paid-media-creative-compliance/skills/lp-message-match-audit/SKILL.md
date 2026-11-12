---
name: lp-message-match-audit
description: Audit a paid media landing page against the ads and keywords that send traffic to it, scoring message match, offer consistency, above-the-fold clarity, call to action, form friction, trust signals, mobile experience, and speed, then produce a prioritized fix list and a ranked backlog of conversion tests. Use whenever the user asks why a landing page converts poorly, wants a landing page review for PPC or paid social, asks about message match or Quality Score landing page experience, wants CRO recommendations for an ad campaign, or asks which landing page tests to run, even if they only say the leads from this campaign are bad or the page is not converting.
---

# Landing Page Message Match Audit

Paid traffic arrives with a specific promise in mind. When the page does not repeat that promise in the first seconds, visitors leave and the account pays for it twice, in wasted clicks and in worse relevance signals. This skill compares what the ad said with what the page delivers, then finds the friction that follows.

## Principle: the page must finish the sentence the ad started
Evaluate the page from the visitor's seat, on a phone, arriving from a specific ad and query.

## Inputs
- Landing page URL(s) and the ads or keywords that point to them (top queries, ad copy, campaign)
- Conversion rate and bounce or engagement data if available
- `clients/<slug>/context.md`: offer, audience, conversion definition, brand rules, constraints on page changes
- Page speed data (PageSpeed Insights or a measured run)

## Process
1. **Capture the ad promise:** the query, headline, offer, price, location, and call to action the visitor saw.
2. **Fetch and read the page** as rendered, including mobile. Record the above-the-fold headline, subhead, hero, primary call to action, form, phone number, and trust elements.
3. **Score each dimension 0 to 3 with evidence** (quote or point to the element):
   - Message match: headline echoes the query and ad promise
   - Offer consistency: price, discount, terms, and geography match the ad
   - Clarity in five seconds: what it is, who it is for, what to do next
   - Call to action: single primary action, visible without scrolling, specific wording
   - Form friction: field count, required versus optional, error handling, alternatives such as call or chat
   - Trust: reviews, credentials, guarantees, real photos, privacy note, near the action
   - Mobile: tap targets, readable text, sticky call button, no layout shifts
   - Speed and stability: LCP, CLS, interaction delays
   - Distractions: navigation links and competing offers that leak visitors
   - Tracking integrity: the conversion fires, UTM values survive redirects
4. **Find gaps by segment:** if several ad groups send traffic to one generic page, recommend dedicated pages or dynamic text for the highest-spend themes.
5. **Prioritize fixes** by expected impact and effort. Separate quick wins (headline match, button text, form trimming) from builds.
6. **Write the test backlog:** each item has a hypothesis, the change, the metric, and the sample size note, ready for the ad test planner.
7. **Flag compliance risks:** claims on the page that conflict with ad policy, missing disclosures, or privacy gaps.

## Output
Save to `clients/<slug>/outputs/YYYY-MM/lp-audit-<page>.md`.
```
Bottom line (3 sentences): how well the page matches the traffic and the biggest fix.
Score table: dimension, score, evidence.
Prioritized fixes with effort and impact.
Message match map: query or ad, page headline, match verdict.
Test backlog.
```

## Rules
- Base every score on observed page content, not on assumptions about intent.
- Do not recommend changes that would make the page conflict with the ads' claims or policy.
- Do not change the live page; deliver recommendations for the owner.
- State when data (speed measurements, conversion rates) was unavailable and how that limits conclusions.
