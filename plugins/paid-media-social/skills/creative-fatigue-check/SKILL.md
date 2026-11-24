---
name: creative-fatigue-check
description: Detect and quantify creative fatigue in paid social ads (Meta, TikTok, LinkedIn) using frequency, CTR and hook-rate decay, rising cost per result, and spend concentration measured against each ad's own baseline, then recommend which ads to retire, refresh, or keep and what to make next, with a refresh cadence. Use whenever the user says social ads are getting worse, CPA is creeping up on Meta or LinkedIn or TikTok, asks if creative is stale or fatigued, asks when to refresh ads, wants a creative performance review, or sets up a regular ad refresh schedule, even if they do not say fatigue.
---

# Creative Fatigue Check

Creative is the main lever on modern social platforms, and it wears out. Fatigue looks like targeting or bidding problems in the dashboard, so teams adjust the wrong things. This skill separates fatigue from other causes using each ad's own history and gives a clear refresh plan.

## Principle: compare an ad to itself, not to the account average
An ad's early performance is its baseline. Fatigue is measurable decay from that baseline at similar spend and audience conditions. Account-wide averages hide it, and different formats age at different rates.

## Inputs
- Daily or weekly performance by ad for at least 30 days, longer for slow accounts: spend, impressions, reach, frequency, CTR (link), hook rate and hold rate for video, CPC, results, CPA or ROAS, and the ad's launch date
- Audience size per ad set (small audiences fatigue faster)
- Creative inventory with angles, formats, and thumbnails or descriptions
- `clients/<slug>/context.md` for target CPA and creative guidelines

## Process
1. **Build each ad's trend in code:** weekly CTR, CPA, frequency, and for video, hook and hold rate, indexed to the ad's first stable week (the first week after learning, with enough volume to be meaningful).
2. **Score fatigue signals.** For each ad, count signals present: frequency rising above audience-appropriate levels (prospecting: roughly 2 to 3 within a week is a watch zone; retargeting tolerates higher), CTR down 25 to 30 percent or more from baseline, CPA up beyond about 20 to 30 percent with stable conversion rate, hook rate falling, and negative feedback or hides rising. Treat these thresholds as defaults, and state any adjustment.
3. **Rule out other causes** before blaming creative: signal or tracking change, audience or budget change that reset learning, seasonality, landing page change, auction pressure, or an audience that is small enough that frequency is simply high. Say which were checked.
4. **Classify each ad:** Healthy, Watch (one signal), Fatigued (two or more signals), Retire (fatigued and above target CPA), or Insufficient data.
5. **Check concentration.** If one or two ads take most of the spend, flag the risk of a single point of failure when they tire.
6. **Diagnose the inventory.** Count distinct angles and formats. Many ads that are minor variations of one idea fatigue together, so identify missing angles and formats.
7. **Recommend the refresh plan.** What to pause, what to keep, what to iterate (same winning angle, new hook or visual), what to test (new angles), the number of new ads needed per month at this budget, and the lead time for production so replacements arrive before the winners die.

## Output
Save to `clients/<slug>/outputs/YYYY-MM/creative-fatigue.md` with an `.xlsx` of per-ad metrics and a trend chart per top-spending ad.
```
Bottom line (2 sentences): how much spend sits in fatigued creative and the urgency.
Ad status table: ad, age, spend share, frequency, CTR change, CPA change, status.
Other causes checked.
Refresh plan: pause / keep / iterate / test, with new-ad count and delivery dates.
Brief handoff: angles and formats for the creative-copy step.
```

## Rules
- Do not retire an ad on fewer than a stable sample of impressions and conversions; mark as insufficient data.
- Read-only; recommend changes, do not pause or edit live ads.
- Do not declare fatigue from CTR alone if conversion rate and CPA are healthy, since the ad may simply be filtering for better clicks.
- Cite date ranges and sources; compute in code.
