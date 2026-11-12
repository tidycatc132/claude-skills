---
name: ad-library-swipe-file
description: Collect competitor ads from public sources (Meta Ad Library, Google Ads Transparency Center, LinkedIn Ad Library, live SERP ads) and build a dated, structured swipe file that catalogs each competitor's angles, offers, calls to action, proof points, and landing page approach, then identifies gaps the client can exploit. Use whenever the user asks what competitors are advertising, wants ad inspiration or creative angles, asks who is running ads for a keyword or in a market, wants a competitive ad snapshot or quarterly competitive review, or needs input for writing new ad copy, even if they do not say swipe file or ad library.
---

# Ad Library Swipe File

Good ad strategy starts with knowing what the market already says, so the client can say something different or say the same thing better. This skill turns scattered competitor ads into a structured, dated resource that creative and strategy agents can reuse and compare over time.

## Principle: public sources only, observed vs inferred
Use only publicly visible information: ad libraries, search results, and public landing pages. Do not log in to anything, impersonate users, or scrape gated content. Label what was observed (the ad text and offer) separately from what is inferred (their strategy, targeting, or budget). Competitor budgets and results are never known; do not present estimates as facts.

## Inputs
- Client context file (`clients/<slug>/context.md`): services, geo, offers, restrictions
- Competitor list from the user, the competitive-research output, or auction insights. If none exists, derive it: search the client's top commercial keywords, record who shows ads, and separate true competitors from directories and aggregators.
- Platforms to cover (default: Google search ads, Meta, plus LinkedIn for B2B)

## Process
1. **Build the competitor set.** Five to ten real competitors. Note aggregators separately, since their ads work differently.
2. **Collect ads.** For each competitor and platform, record: platform, date seen, ad text (headline, body, description), format, call to action, offer, price or financing signals, proof points (reviews, awards, years in business, credentials), landing page URL, and whether the ad appears long-running (older ads in a library often indicate a winner) or new.
3. **Capture the landing page** for the highest-visibility ads: headline, offer, form length, trust elements, phone prominence.
4. **Tag each ad** with a primary angle from a fixed list: price, speed, trust and reviews, expertise, guarantee, convenience, local, emergency, financing, comparison, education, fear and risk, outcome. A fixed list makes patterns countable.
5. **Analyze.** Compute angle frequency by competitor and overall, most common offers, common claims, how often each competitor appears, and what is conspicuously absent.
6. **Find openings.** Angles nobody uses, claims the client can substantiate and others cannot, weak landing pages behind strong ads, markets or times where competitors are absent.
7. **Save a dated snapshot** so changes over time can be compared in future runs.

## Output
Save to `clients/<slug>/outputs/YYYY-MM/ad-swipe-file.md` plus a CSV of the raw ad records beside it.
```
Bottom line (3 sentences): how the market is advertising and the biggest opening.

Competitor table: who, platforms active, dominant angles, main offer, strongest ad.

Angle frequency chart or table.

Openings: ranked, each tied to evidence and to what the client can truthfully claim.

Swipe examples: a handful of the most instructive ads, summarized rather than reproduced at length, with source and date.

Watch list: what to re-check next quarter.

Method and gaps: sources used, what could not be seen, snapshot date.
```

## Rules
- Never recommend copying competitor ad text or claims. The swipe file feeds original messaging; claims must be substantiated for the client and pass policy review.
- Do not reproduce long passages of competitor copy; summarize the angle and offer, and link the source.
- Do not include images or likenesses of private individuals from ads in files you create.
- Record the date on every observation. Ads change weekly and an undated record cannot be trusted.
