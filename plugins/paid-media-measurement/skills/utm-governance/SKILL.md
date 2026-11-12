---
name: utm-governance
description: Define a consistent UTM parameter and campaign naming convention for paid media across Google Ads, Microsoft Ads, Meta, LinkedIn, TikTok, email, and other channels, audit existing URLs and campaign names for violations (mixed case, missing parameters, inconsistent values, untagged links, conflicts with auto-tagging), generate account-level tracking templates and URL suffixes, and produce fix lists so GA4 channel grouping and reports are clean. Use whenever the user asks about UTMs, campaign naming conventions, tracking templates, why paid traffic shows as direct, unassigned, or organic in GA4, why reports are messy or campaigns cannot be matched across platforms, or wants a link builder or naming standard, even if they only say our tracking links are a mess.
---

# UTM Governance

Inconsistent tagging fragments reports: "Facebook," "facebook," and "fb" become three sources, untagged paid links fall into direct, and nobody can join ad platform data to analytics. A short, enforced convention fixes this for good and costs little. This skill defines the convention, finds violations, and generates the templates that apply it automatically.

## Principle: automate tagging, constrain values, keep it short
Hand-typed UTMs drift. Prefer platform ValueTrack and dynamic parameters set once at account level, a fixed list of allowed values for source and medium, lowercase everywhere, and a naming scheme that carries only the information reporting needs.

## Inputs
- Platforms and channels in use for the client
- Existing tracking templates, URL suffixes, final URLs, and campaign names (exports or connector pulls)
- GA4 source, medium, and campaign reports for 90 days, including channel grouping and unassigned or direct volume
- Any existing team convention in `clients/<slug>/context.md` or a shared standards file

## Process
1. **Check GA4 channel grouping.** Medium values must match GA4's default channel rules (for example cpc for paid search, paid-social for paid social, email, display) so paid traffic lands in the right channel. Note any custom channel groups.
2. **Define the convention:**
   - `utm_source`: the platform or sender, lowercase, from a fixed list (google, bing, facebook, instagram, linkedin, tiktok, newsletter, and so on)
   - `utm_medium`: from a fixed list matching GA4 grouping (cpc, paid-social, display, email, and so on)
   - `utm_campaign`: the campaign name, lowercase with hyphens, structured and parseable (for example `client-objective-theme-geo-yyyymm` as the team prefers), with no spaces, no special characters
   - `utm_content`: ad or creative identifier, used for tests
   - `utm_term`: keyword for search where used
   Keep the campaign naming in the ad platform identical or deterministically derived from the UTM campaign so data joins cleanly.
3. **Prefer dynamic values:** Google Ads ValueTrack parameters in an account-level tracking template or final URL suffix; Microsoft Advertising URL options; Meta URL parameters with dynamic macros (campaign name, ad set name, ad name, ids); LinkedIn and TikTok macros. Provide copy-ready strings per platform. Note platform specifics: auto-tagging must stay on for Google, and manual UTMs must be set so they do not override the click id data unintentionally (GA4 prioritizes the imported Google Ads data when linked; document the chosen behavior).
4. **Audit what exists.** Crawl or export URLs from ads and campaigns, parse parameters, and flag: uppercase and mixed case, spaces and encoded characters, missing source or medium, wrong medium for the channel, inconsistent source names for the same platform, duplicates, hard-coded UTMs conflicting with templates, UTMs on internal links (which overwrite session sources), redirects that strip parameters, and campaign names that do not match the platform naming.
5. **Quantify the damage.** Sessions and conversions currently landing in direct, unassigned, or the wrong channel that likely belong to paid, using the share of paid clicks versus paid sessions as a rough cross-check.
6. **Generate fixes:** a corrected template per platform, a violations table with the exact change per row, and a rename plan if campaign names must change (flag that renaming mid-flight splits historical reporting and note a mapping table to bridge it).
7. **Add governance.** One-page standard for the team: allowed values, naming pattern, who approves new values, the pre-launch check, and a quarterly audit cadence. Include the link builder template as a spreadsheet with data validation lists.

## Output
Save to `clients/<slug>/outputs/YYYY-MM/utm-governance.md`, the violations table and link builder as `.xlsx`.
```
Bottom line (2 sentences): current tagging health and the biggest reporting impact.
Convention: parameter table with allowed values and examples.
Platform templates: copy-ready strings.
Violations table: URL or campaign, issue, fix.
Impact estimate.
Rollout steps and owner; [NEEDS APPROVAL] for live account changes.
```

## Rules
- Do not recommend changing live tracking templates without noting the effect on historical comparisons and testing on one campaign first.
- Keep auto-tagging and click id passing intact.
- Never include personal data in UTM values.
- Read-only; produce templates and fix lists for humans to apply.
