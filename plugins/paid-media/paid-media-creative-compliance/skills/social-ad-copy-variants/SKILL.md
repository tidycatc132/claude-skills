---
name: social-ad-copy-variants
description: Write paid social ad copy for Meta (Facebook and Instagram), LinkedIn, and TikTok as distinct variants by messaging angle and funnel stage, including the hook, primary text, headline, description, and call to action, with platform length and truncation limits verified in code, compliance flags, brand voice adherence, and mapping to audiences and tests. Use whenever the user asks for social ad copy, Facebook or Instagram ad text, LinkedIn ad copy, TikTok captions, ad angles, hooks, ad variations for testing, or a refresh of tired social ads, even if they just say write some ads for this offer.
---

# Social Ad Copy Variants

Social ads interrupt people who were not looking for anything, so the first line carries almost all the weight. Variants must differ in angle, not in wording, or the platform and the test learn nothing. This skill produces copy that stops the scroll for a specific audience at a specific funnel stage, stays truthful, and fits each placement.

## Principle: one idea per ad, a real angle per variant
Each ad commits to one message for one audience. Variants swap the angle (problem, outcome, proof, offer, objection, curiosity, comparison, urgency), not synonyms. Quality beats volume; five distinct angles beat fifteen rewrites.

## Inputs
- Offer, audience, and funnel stage; audience personas and pain points when available
- `clients/<slug>/context.md`: brand voice, substantiated proof points, restrictions, required disclosures, prohibited claims
- Landing page or lead form the ad leads to
- Competitor angles from the ad swipe file, to differentiate
- Past performance of copy angles, when refreshing

## Platform limits (verify in code)
- Meta: primary text shows roughly 125 characters before "See more" on mobile feeds (front-load the hook); headline roughly 27 to 40 characters visible; description often not displayed; stories and reels use on-creative text instead and keep captions short. Maximum field lengths are larger than visible lengths; write for the visible portion.
- LinkedIn: introductory text roughly 150 characters visible before truncation on mobile (up to about 600 allowed); headline up to 70 characters and often truncated earlier; lead gen forms have separate offer text limits.
- TikTok: ad text up to 100 characters; the hook appears in the first seconds of video, so the video script matters more than the caption.
Platform limits change; confirm current limits when exactness matters, and report any field over the limit.

## Process
1. **Pick angles by funnel stage.** Cold audiences: problem awareness, curiosity, proof, outcome. Warm audiences: social proof, objection handling, offer. Hot audiences and retargeting: urgency, specific offer, reassurance, clear next step.
2. **Write the hook** (first line) in a variety of forms: a question that names the problem, a specific outcome, a surprising fact the client can substantiate, a direct callout of the audience ("For Michigan homeowners with..."), a short story opening. Avoid generic openers and avoid sensitive personal attribute callouts that platform policy prohibits (for example implying you know a person's health, finances, or identity).
3. **Write the body:** two to four short lines or a short paragraph that delivers one benefit, a piece of proof, and a clear next step. Use plain language at the audience's reading level; match the brand voice. For B2B, lead with the business outcome, then credibility.
4. **Write headline and description** that complement rather than repeat the primary text, and a call to action button choice that matches the next step (Learn More, Get Quote, Book Now, Sign Up, Download).
5. **Use only substantiated claims.** Do not invent statistics, awards, reviews, testimonials, or guarantees. If a strong angle lacks proof, list the missing proof for the client to supply.
6. **Map to audience and test.** Each variant lists its audience, angle tag, and the hypothesis it tests so results teach something. Group variants into a test set that changes one thing at a time when the plan calls for a test.
7. **Compliance pass.** Flag claims, superlatives, before and after language, health or financial promises, special category wording, and trademarks for policy review.
8. **Quality check in code:** lengths per field versus visible and maximum limits, duplicate openers across variants, banned terms from the context file, and consistent use of brand terms.

## Output
Save to `clients/<slug>/outputs/YYYY-MM/social-copy-<campaign>.xlsx` (and a markdown summary): platform, audience, funnel stage, angle tag, hook, primary text, headline, description, CTA, character counts, compliance flag, test mapping.
```
Bottom line (2 sentences): the angle strategy and what each tests.
Variant table grouped by angle.
Compliance flags and missing-proof gaps.
Creative handoff notes: what visual or video each hook needs.
```

## Rules
- Do not reproduce competitor copy. Use it only to find open angles.
- No fabricated claims or testimonials; no promises of results the client cannot guarantee.
- Follow special ad category and sensitive category restrictions; flag when unsure.
- Deliver for review; never publish ads.
