---
name: social-audience-builder
description: Design the audience and targeting strategy for paid social campaigns on Meta, LinkedIn, and TikTok, including prospecting layers, first-party and lookalike audiences, retargeting windows, exclusions, audience sizing, test structure, and creative-to-audience mapping, grounded in the client's customers and personas. Use whenever the user asks who to target on Facebook, Instagram, LinkedIn, or TikTok, how to structure audiences for a social campaign, how to build lookalikes or retargeting pools, what job titles or industries to target, whether an audience is too small, or how to restructure social targeting, even if they only say figure out the audience for this campaign.
---

# Social Audience Builder

On modern social platforms, creative does much of the targeting and the audience's job is to give delivery a sensible pool without choking it. Over-narrow audiences raise costs and stall learning; unplanned overlap makes ad sets bid against each other. This skill designs audience structures that learn fast and can be tested cleanly.

## Principle: start broad where the platform allows, narrow where the economics demand it
On Meta and TikTok, broad targeting with strong creative and clean signal often wins and learns fastest. On LinkedIn, professional targeting is the value, so precision matters more but audiences must still reach workable size. Choose per platform and say why.

## Inputs
- `clients/<slug>/context.md`: goals, service area, qualified lead definition, budget, restrictions
- Audience personas or customer research if they exist; otherwise derive from the site, CRM exports, and current customer data, and label the result as a hypothesis
- First-party data available: customer lists, lead lists, site visitors, video viewers, engagement, with sizes and freshness
- Budget per platform and expected conversion volume

## Process
1. **Define who actually buys.** From personas and customer data: roles, life situations, triggers, and objections, separating decision makers from influencers (important in B2B).
2. **Plan layers by funnel stage:**
   - **Prospecting:** platform-appropriate cold audiences (broad with age and geo constraints; interest or behavior layers as tests; LinkedIn job function, seniority, industry, company size, skills, and matched account lists)
   - **Lookalikes and value-based audiences:** seed from the best customers, not all leads, at a sensible seed size and percentage
   - **Engagement and warm audiences:** video viewers, page and profile engagers, lead form openers, with window lengths
   - **Retargeting:** site visitors, key page viewers, cart or form abandoners, with window lengths sized to the sales cycle
   - **Customer audiences:** for upsell, cross-sell, and exclusion
3. **Set exclusions** to avoid waste and overlap: existing customers where appropriate, recent converters, employees, and lower-funnel audiences excluded from prospecting.
4. **Size and sanity-check.** Estimate audience reach per platform and flag audiences that are too small (for example, LinkedIn audiences under about 50,000 for most campaigns, or retargeting pools too small to spend the budget) or so overlapping that they should merge. State where figures are platform estimates.
5. **Match budget to structure.** Limit the number of ad sets to what the budget and event volume can feed. If the budget cannot support more than one or two ad sets learning, say so and recommend a single broad ad set plus retargeting.
6. **Plan the test.** Which audience hypotheses are worth testing first, one variable at a time, with the metric, minimum spend, and run time to decide. Map each audience to the creative angle most likely to resonate.
7. **Handle restrictions.** For housing, employment, credit, and social issue categories, targeting options are limited; apply the restricted setup and flag for compliance review. Do not use targeting on sensitive personal attributes.

## Output
Save to `clients/<slug>/outputs/YYYY-MM/social-audiences-<platform>.md` plus a build sheet (`.xlsx`): audience name, type, definition, size estimate, exclusions, funnel stage, ad set mapping, test priority.
```
Bottom line (2 sentences): recommended structure and the reasoning.
Audience table.
Exclusion rules.
Test plan.
Warnings: size risks, restrictions, data gaps, assumptions about personas.
```

## Rules
- Label persona-derived assumptions as hypotheses until tested.
- Customer lists must have a lawful basis and comply with the platform's customer list policies and privacy rules; flag when consent is unclear.
- Read-only planning: output the build sheet, do not create audiences in live accounts.
- Hand pixel, event, and list-matching problems to the conversion tracking audit.
