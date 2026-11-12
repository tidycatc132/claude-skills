---
name: rsa-copy-generator
description: Write responsive search ad (RSA) headlines and descriptions for Google Ads and Microsoft Advertising, organized by messaging angle, mapped to the ad group's keyword theme, brand voice, and landing page, with every asset's character count verified in code, pinning only where required, and a test hypothesis attached. Use whenever the user asks for search ad copy, RSA headlines, ad variations, refreshing tired ads, writing ads for a new ad group or campaign, or ad copy tests for Google or Microsoft, even if they just say write the ads for these keywords.
---

# RSA Copy Generator

An RSA is a pool of assets the platform recombines. The quality of the pool, not any one line, determines performance: it must cover multiple angles, mirror what the searcher typed, and stay interchangeable so any headline can pair with any other without breaking sense or policy. This skill builds that pool deliberately.

## Principle: match the query, then differentiate
The searcher's words earn the click's relevance; the angle earns the click. Every ad group's pool includes headlines that echo its keyword theme, plus distinct angles that give the platform real choices. Fifteen near-duplicate headlines waste the format.

## Inputs
- The ad group's keyword theme and top queries (from keyword research or search terms)
- Landing page URL and its content (the copy must be true to the page)
- `clients/<slug>/context.md`: offers, proof points the client can substantiate, geo, restrictions, brand voice reference
- Competitor angles from any ad swipe file, to differentiate
- Existing ads and their performance, when refreshing

## Limits (verify in code, never by eye)
- Headlines: up to 15, each 30 characters maximum
- Descriptions: up to 4, each 90 characters maximum
- Display path fields: 15 characters each
Count characters with a script that reports any asset over limit. Platform rules on punctuation, capitalization, and symbols apply; check them in the same script.

## Process
1. **Read the theme and the page.** Note the exact phrases searchers use and the page's real offer, claims, and tone.
2. **Plan the angle coverage** across the headline pool:
   - Keyword echo: 3 to 4 headlines using the theme's own words, including location where relevant
   - Benefit and outcome
   - Trust and proof (years, reviews, licensing, guarantees) only if substantiated
   - Offer and price signals (free estimate, financing, specials) only if currently true
   - Urgency and availability (same day, 24/7) only if operationally true
   - Call to action
   - Objection handling
   Spread across all fifteen slots; assign each headline an angle tag.
3. **Write descriptions** that each stand alone and each carry a different job: one value proposition plus action, one proof plus differentiator, one offer plus urgency, one objection plus reassurance.
4. **Keep interchangeability.** Read random pairings aloud: no headline should depend on another for meaning, repeat the same claim in the same ad, or contradict. Avoid ending any asset with terminal punctuation that breaks combinations.
5. **Pin sparingly.** Pin only for legal or brand requirements (a required disclosure, a brand name in position 1). Pinning cuts the platform's testing room, so state the reason for every pin.
6. **Attach a test hypothesis**: what angle you expect to win and why, which metric decides it (CTR is a diagnostic; prefer conversion rate or CPA when volume allows), and the minimum run time before judging.
7. **Check compliance.** Flag any superlative, guarantee, price claim, comparative claim, trademark, or regulated-industry wording for the compliance review step. When uncertain, flag the line instead of guessing.
8. **Quality check.** Ensure no asset invents a claim, award, statistic, review count, or testimonial. If a strong angle lacks substantiation, list it as a gap for the client to supply.

## Output
Save to `clients/<slug>/outputs/YYYY-MM/rsa-<adgroup>.xlsx` (or a tab per ad group): asset text, type, angle tag, character count, pin position and reason, compliance flag. Return:
```
Bottom line (2 sentences): the angle strategy for this ad group.
The asset table, grouped by angle.
Test plan: hypothesis, metric, minimum run.
Compliance flags and unsubstantiated-claim gaps.
```

## Rules
- Do not reproduce competitor ad text. Use the swipe file for angle ideas only.
- Do not use dynamic insertion carelessly: confirm fallback text reads naturally.
- Never publish or edit ads in a live account; deliver the sheet for review and import.
- Respect the brand voice file. If none exists, note the assumption.
