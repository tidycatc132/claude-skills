---
name: client-context-intake
description: Build or validate a client's paid media context file (clients/SLUG/context.md) covering goals, target CPA/ROAS, budget, geo, offer, industry restrictions, platform account IDs, tracking status, and approver. Use whenever a paid media agent or person is about to work on a client and no complete context file exists, or when the user says onboard a client for paid media, set up client context, refresh the context file, or what do we know about this client's ads. Run this even if the user only asks for a plan, audit, or report and the context file is missing or stale, because every other paid media skill depends on it.
---

# Client Context Intake

Every paid media agent reads `clients/<slug>/context.md` before doing anything. A thin or wrong context file produces confident but wrong recommendations (for example, optimizing to a CPA target the client never agreed to). This skill creates that file, or audits and refreshes an existing one.

## Principle: draft first, flag gaps, never stall
Do not stop to interview the user. Gather what exists, fill the template, mark every unknown, and return the draft with a short list of what is needed. The user can fill gaps in one pass afterward.

## Process
1. **Find the client slug.** Lowercase, hyphenated client name. If `clients/<slug>/context.md` exists, read it and run in refresh mode (step 5).
2. **Gather from every source available, in this order:**
   - Existing files under `clients/<slug>/` (prior audits, reports, briefs)
   - Task system (ClickUp) for the client's folder, onboarding tasks, and recent comments
   - Project documents, sales notes, or onboarding docs the user points to
   - The client's website (services, offers, locations, claims, restricted-category signals)
   - Connected analytics and ad platforms, read-only, for account IDs, conversion actions, and trailing 90-day spend and results
3. **Fill the template below.** Tag each value with its source in brackets, for example `[GA4]`, `[ClickUp]`, `[website]`, `[user]`. Mark inferred values `[assumed]` and unknown values `[NEEDED]`. Untagged values are not allowed, because the next agent has to know how far to trust each one.
4. **Derive targets only when inputs exist.** If average deal value, margin, and lead-to-close rate are known, compute allowable CPA in code and show the inputs. If not, record the historical CPA as a baseline and mark the target `[NEEDED]`. Never invent a target.
5. **Refresh mode.** Compare each field to current evidence, update changed values, move the old value into a Change Log line with date, and flag anything older than 90 days as stale.
6. **Score completeness** (see below) and list the top blockers.
7. Save to `clients/<slug>/context.md`.

## Template (use exactly these headings)
```
# <Client name>: Paid Media Context
Last updated: YYYY-MM-DD | Completeness: X/12 | Next review: YYYY-MM-DD

## Business
- What they sell, service lines ranked by profit priority
- Offer(s) and proof points currently usable in ads
- Service area / geo targets and exclusions
- Seasonality and capacity limits

## Goals and targets
- Primary outcome (leads, booked calls, sales, revenue)
- Target CPA or ROAS, and how it was derived (inputs shown)
- Historical baseline: trailing 90-day spend, leads, CPA, ROAS
- Definition of a qualified lead

## Budget
- Monthly budget total and per channel, billing owner, payment method type
- Budget change rules (who can approve a raise, and the limit)

## Platforms and accounts
- Platform, account ID, manager account, access level, status
- Conversion actions that count as primary, and tracking health (verified / unverified / broken)

## Restrictions and compliance
- Industry category (legal, financial, health, housing, employment, credit, other)
- Prohibited claims, required disclosures, trademark/brand rules, Special Ad Category needs
- Brand voice and guideline file locations

## Contacts and approvals
- Client approver, WISE account manager, escalation path
- What needs client sign-off (new spend, new messaging, new landing pages)

## Open items
- [NEEDED] list, ranked by what blocks the most work

## Change log
```

## Completeness score
One point each for: business and offers, geo, primary goal, target CPA/ROAS with derivation, 90-day baseline, budget total, budget per channel, account IDs, tracking status, restrictions, approver, brand voice reference. Under 8 means other agents should proceed on labeled assumptions and surface the gaps in their output.

## Return to the user
The file path, the completeness score, and the three most important `[NEEDED]` items in one short list. Nothing else.
