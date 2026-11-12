---
name: lsa-setup-checklist
description: Plan, set up, and optimize Google Local Services Ads (LSA) for eligible local businesses such as home services, legal, and other supported categories, covering eligibility and category selection, Google Guarantee or Screened verification steps, background checks and licensing and insurance documents, service area and job type configuration, business hours, budget and weekly lead targets, profile and photo quality, review strategy, lead response workflow and call handling, lead dispute process for invalid leads, conversion and CRM tracking, and ongoing optimization. Use whenever the user asks about Local Services Ads, Google Guaranteed or Google Screened, LSA setup or audit, why LSA leads are poor or costly, how to dispute LSA leads, or whether a local client should run LSA, even if they only say the Google Guaranteed ads.
---

# LSA Setup Checklist

Local Services Ads sit above regular search results, charge per lead rather than per click, and are ranked by factors such as proximity, review quality, responsiveness, and business hours, not by bids alone. Success depends on getting verified, building a strong profile, and answering leads fast. A good setup and weekly discipline matter more than clever bidding.

## Principle: operations drive LSA results
LSA performance is as much about phone answering, review volume, and profile completeness as about budget. The setup plan covers the operational work the client must do, not only the account configuration.

## Inputs
- Client business details: legal name, address, service areas, services and job types, licenses, insurance, years in business, employees, hours, phone handling process
- Category availability in the client's markets and any existing LSA account data (leads, spend, cost per lead, booked jobs, disputes, ratings, reviews)
- `clients/<slug>/context.md`: goals, allowable cost per lead and cost per booked job, budget, capacity
- CRM or call records to compare LSA leads to outcomes

## Process
1. **Eligibility and category check.** Confirm LSA is available for the client's category and service areas; verify licensing requirements by state and category; identify the badge type (Google Guaranteed, Google Screened, or a category-specific program) and its requirements. If unavailable, recommend alternatives and stop.
2. **Verification checklist.** Business and owner details, background checks for owners and technicians as required, license numbers, proof of insurance, and any category-specific documents; list lead times, because verification can take weeks, and assign owners and dates.
3. **Service configuration.** Select job types the client wants and can serve profitably, and remove the rest (a plumber who does not want sewer jobs should exclude them). Set service areas by ZIP or city, matching the real operating area and travel economics. Set business hours accurately (ads show and leads route only within hours, and responsiveness is measured).
4. **Budget and bidding.** Convert the target number of leads per week and allowable cost per lead into a weekly budget; use the platform's bid strategy options (maximize leads or a set cost per lead where available); note that cost per lead varies by market and job type, and set expectations accordingly. Revisit after the first two to four weeks of data.
5. **Profile quality.** Business name consistency with Google Business Profile, photos of the team, vehicles, and work, an accurate description, service list, years in business, and a short intro. Ensure consistency between the LSA profile, Google Business Profile, and website.
6. **Reviews strategy.** Review count, rating, and recency affect ranking. Define a repeatable request process after completed jobs (timing, channel, link), and respond to reviews. Do not incentivize or gate reviews; follow Google's policies.
7. **Lead handling workflow.** Set up call and message notifications; define who answers, within how many minutes, and what the script is; use the LSA app for messaging; mark leads as booked, not booked, or wrong, since this feedback trains the system; and set after-hours handling. Track speed to answer, because it affects ranking and conversion.
8. **Dispute process.** Define which leads can be disputed (spam, wrong service, outside service area, duplicates, unavailable job types) and the deadline (disputes must be filed within a limited window after the lead; verify the current window), with a weekly routine to review and file disputes with evidence such as call recordings.
9. **Tracking and measurement.** Capture LSA leads in the CRM with a source tag, connect to reporting, record booked jobs and revenue, and compute cost per booked job versus other channels. Link the LSA account to the Google Ads manager account where applicable.
10. **Ongoing optimization routine.** Weekly: budget pacing and lead volume, dispute review, response times, review requests, hours and service areas, and ranking factors; monthly: cost per booked job, comparison to search campaigns, job type profitability, and seasonality adjustments.
11. **Coordinate with search.** Avoid conflicting messaging and double counting; consider brand and non-brand search overlap and whether LSA should be budgeted separately from search.

## Output
Save to `clients/<slug>/outputs/YYYY-MM/lsa-plan.md` (or audit variant) with a task checklist suitable for the task system.
```
Bottom line (2 sentences): eligibility, expected path, and the biggest operational dependency.
Verification checklist with owners and dates.
Configuration table: job types, service areas, hours, budget.
Profile and review plan.
Lead handling and dispute SOP.
Tracking and reporting plan.
Weekly and monthly optimization routine.
Risks and open items.
```

## Rules
- Do not invent eligibility or program details; verify current Google requirements and program names before advising, and note the date checked.
- Never advise gaming reviews, misrepresenting business details, or using unlicensed technicians.
- Read-only planning; humans submit applications and change settings.
- Where the client is a regulated profession (for example legal), check the category's rules and the client's professional advertising rules before launch.
