# Intent taxonomy

Classify every keyword with one dominant intent and a funnel stage. When a live SERP is available (SE Ranking `DATA_getSerpResults`), what ranks beats what the words suggest.

## The four intents

| Intent | User goal | Sub-categories | Signal words | Best formats | Typical length |
|---|---|---|---|---|---|
| **Informational** | Learn or understand something | definition, how-to, explanation, comparison of concepts, troubleshooting, data lookup | what, how, why, guide, tutorial, examples, tips, ideas, meaning, fix | guide, tutorial, explainer, FAQ, checklist, video summary | 800 to 2,500 words; a definition can be 300 |
| **Navigational** | Reach a specific site, page or brand | brand, brand + product, login, support, location | brand names, login, sign in, contact, app, near [brand] | the destination page itself, a support hub | as short as the task allows |
| **Commercial** | Research before a purchase or hire | best-of, reviews, comparisons, alternatives, pricing research, "for [segment]" | best, top, review, vs, versus, alternative, compare, cost, pricing, cheap, affordable | listicle, comparison table, review, buyer's guide, pricing page | 1,200 to 3,000 words |
| **Transactional** | Do the thing now | buy, hire, book, download, sign up, local service, emergency | buy, hire, book, order, quote, near me, [city], emergency, same day, install, repair, download, free trial | service page, product page, landing page, location page | 400 to 1,200 words plus proof and a clear CTA |

Sub-category examples:

- Informational definition: "what is a tankless water heater", "keyword difficulty meaning"
- Informational how-to: "how to fix a leaking faucet", "how to write a content brief"
- Informational troubleshooting: "why does my water heater make noise"
- Navigational brand: "se ranking login", "acme plumbing reviews" (the second is also commercial for competitors)
- Commercial best-of: "best water heater for hard water", "best crm for nonprofits"
- Commercial comparison: "tankless water heater vs tank", "hubspot vs salesforce"
- Commercial pricing research: "sewer line replacement cost", "how much does seo cost"
- Transactional local service: "emergency plumber denver", "drain cleaning near me"
- Transactional purchase: "buy standing desk", "book boiler service"

## Six-stage funnel map

| Stage | Dominant intent | What the reader wants | Typical CTA | Rough conversion range |
|---|---|---|---|---|
| Awareness | Informational | Understand the problem | subscribe, read next, related guide | 0.5% to 2% |
| Interest | Informational | Understand the options | checklist, calculator, email course | 0.5% to 2% |
| Consideration | Commercial | Compare approaches and providers | comparison download, case study | 2% to 5% |
| Evaluation | Commercial | Shortlist and validate | pricing, demo, reviews, free audit | 2% to 5% |
| Decision | Transactional | Buy, book or hire | quote, call, book, buy | 5% to 15% |
| Retention | Navigational | Use, renew, get support | login, help center, upsell | n/a, measured as retention |

The ranges are planning heuristics, not measurements; label them Estimated if they appear in a report.

How the three funnel tags the script uses map onto the six stages, so the two systems never conflict:

- **TOFU** = Awareness + Interest (informational, no buying signal)
- **MOFU** = Consideration + the informational half of Evaluation (how-to with a product in view, guides, ROI, reviews, case studies)
- **BOFU** = Evaluation's commercial half + Decision (best, vs, pricing, services, hire, near me, and every transactional keyword)
- Retention (navigational) sits outside the three tags; it is tagged by intent only and rarely enters a content calendar.

## Mixed intent

Many keywords carry two intents. Rule: **answer the dominant intent first, bridge to the secondary, and mirror the SERP's format**. If the top 10 are listicles, do not publish a service page and hope.

| Pattern | Dominant + secondary | What to build |
|---|---|---|
| `best X for Y` | commercial + informational | ranked list with a short explainer of what matters for Y, then the client's fit |
| `how to X with [product]` | informational + navigational | tutorial on the product's own docs or blog, linking to the feature page |
| `X vs Y` | commercial + informational | comparison table first, honest verdict, then "when to choose each" |
| `X cost` / `how much does X cost` | commercial + transactional | price ranges with what drives them, then a quote CTA |
| `X near me` / `X [city]` | transactional + navigational | location or service page with proof, hours, map, and a call button |
| `is X worth it` | commercial + informational | balanced answer, then the deciding criteria, then the offer |
| `X examples` | informational + commercial | gallery or list, each with a takeaway, soft CTA |
| `free X template` | transactional (download) + informational | the asset above the fold, a short guide below it |

## Common misclassifications

- `best crm` is **commercial**, not informational. The reader is shopping.
- `how much does X cost` is **commercial leaning transactional**, not informational. Pricing pages and cost guides rank, not encyclopedias.
- `seo services` is **local-transactional**. Agencies rank, and a map pack usually shows.
- `seo tools` is **mixed**. Lists of tools and tool vendors share the SERP; check it before deciding.
- `[brand] reviews` is navigational for that brand's customers and commercial for everyone else. Target it only if the client is the brand or a credible reviewer.
- `what is [product category]` is informational even when the client sells it. Build the explainer, link to the product, do not swap them.
- A keyword with `near me` is transactional even without a verb.
- Questions (`why does my water heater make noise`) are informational troubleshooting even when the fix is a paid service; they are GEO candidates and MOFU bridges, not service pages.

## Verifying against the SERP

With `DATA_getSerpResults` for the keyword and market:

1. Count page types in the top 10 (service pages, listicles, guides, forums, videos, product pages).
2. The majority type is the dominant intent. Two or more types with three or more results each is mixed intent.
3. Note SERP features: map pack means local-transactional, People Also Ask and AI Overview mean informational demand and a GEO candidate, shopping results mean transactional.
4. Record the verified intent in the `intent` column and say "SERP-verified" in the report. Keywords classified from words alone are labeled Estimated.
