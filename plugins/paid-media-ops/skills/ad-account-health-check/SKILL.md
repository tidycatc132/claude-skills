---
name: ad-account-health-check
description: Scan one or many client ad accounts (Google Ads, Microsoft Advertising, Meta, LinkedIn, TikTok) for operational health problems that stop or distort delivery, including payment and billing failures, low balance, suspended or restricted accounts, policy warnings, disapproved ads and limited-status campaigns, expired or paused campaigns that should be live, lost user access, broken or silent conversion tracking, linked-account breaks (GA4, Merchant Center, Business Profile), ended experiments and promotions, and unapproved changes in the change history, returning a prioritized status table. Use whenever the user asks for an account health check, hygiene check, are all accounts running properly, check for disapprovals or billing problems, a daily or weekly sweep across clients, or what is broken across our ad accounts, even if they do not say health.
---

# Ad Account Health Check

The cheapest paid media failures to prevent are the ones nobody noticed: a card that expired, a campaign disapproved over the weekend, a conversion tag that went silent after a site update. This sweep is fast and wide. It does not analyze performance; it finds operational problems early and routes them to the right owner.

## Principle: breadth and speed, with a clear severity order
Check every account the same way every time, report what could not be checked, and sort by urgency. A problem that stops spend or tracking outranks every optimization.

## Inputs
- List of client accounts and platform account IDs (from each `clients/<slug>/context.md`)
- Read access to each platform (API, connector, or exports), including account status, billing, user access, campaign status, ad status and policy, conversion actions and recent conversion counts, linked accounts, change history for the last 7 days
- Expected state per client: which campaigns should be live, budgets, and planned changes (from context and the pacing report)

## Checks (per account)
1. **Account status.** Active, suspended, restricted, or under policy review; any account-level warnings or required actions with deadlines.
2. **Billing.** Payment method valid and unexpired; failed payments; balance and credit; billing threshold; invoicing issues; for prepaid accounts, balance versus expected spend.
3. **Access.** Manager account link intact; required users still have access; pending invitations; changes in admin users that were not expected.
4. **Campaign status.** Campaigns that should be live but are paused, ended, or limited; zero impressions or zero spend for the last 1 to 3 days where spend is expected; budget exhausted before mid-day; learning limited or misconfigured settings that block delivery.
5. **Ad status and policy.** Disapproved ads or assets, limited approval, count versus prior day, ads missing in ad groups, extensions or assets disapproved, destination issues (landing page not working, 404, redirect loops, site down).
6. **Conversion tracking.** Conversion actions with no conversions in the last 3 to 7 days where there should be some (compare to the trailing average, using a threshold by volume), status flags such as no recent conversions or inactive tag, unexpected spikes (duplicate firing), and the primary action still set.
7. **Linked accounts.** GA4 link, Merchant Center feed status, Business Profile connections, CRM or call tracking integration status, customer match uploads freshness.
8. **Change history review.** Unexpected changes in the last 7 days (budget, bid strategy, status, targeting, new campaigns) by user, flagging changes outside the planned work or made by users not on the team.
9. **Site and landing page reachability.** Final URLs of top spend ads return success, load within a reasonable time, and show the expected content; flag a site down or an unexpected redirect.

## Severity scheme
- **Critical (same day):** account suspended, payment failed, all campaigns disapproved or stopped, conversion tracking silent on a high-volume account, landing page down
- **High (24 hours):** significant disapprovals, campaigns unintentionally paused, access lost, unexpected high-impact changes, silent tracking on lower-volume accounts
- **Medium (this week):** limited approval, linked account issues, stale lists, expiring cards within 30 days
- **Low:** hygiene items

## Output
Save to `clients/_portfolio/health-YYYY-MM-DD.md` with a CSV of the table, and per-client notes in each client's outputs folder for Critical and High items.
```
Health check | Data as of: <timestamp> | Accounts checked: N of M
Summary: X critical, Y high, Z medium; accounts clean; accounts not checked.

Table (sorted by severity): client, platform, issue, severity, evidence, recommended fix, owner.

Critical and High detail: what is wrong, exact fix, who owns it.
Not checked: account, reason (no access, API error).
```
Route items to the right owner: billing to the account manager or finance, tracking to the tracking engineer, policy to the policy reviewer, campaign status to the channel specialist.

## Rules
- Read-only; never change billing, access, campaign status, or settings.
- Report accounts you could not check explicitly; silence must not look like health.
- State the data timestamp. Do not present stale data as current.
- Do not include credentials, full card details, or personal data in outputs.
- Escalate Critical items immediately with the finding in the first line.
