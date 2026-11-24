---
name: ga4-event-tracking
description: Sets up GA4 goal and conversion event tracking through Google Tag Manager for a launched WISE website build. A script reads the dev handoff index and the newest launch check, then writes a tracking plan and a GTM container file Dev imports in one step, with a fixed generic event set (form leads, calls, emails, directions, contact-page clicks), key events and a live-hostname guard so staging visits never count. After Dev publishes, it checks every Build page for the container, a doubled GA4 tag, the conversion links and the form. Use when SEO or Dev asks to set up goal tracking events, add event tracking to GA4 via Tag Manager, make the GTM container or import file, track conversions, or check the tracking is installed. Do NOT use for the post-deployment launch check (use staging-site-qa), the dev handoff index (use dev-handoff-index), the roadmap or Month 1 tasks (use retainer-roadmap), technical SEO audits (use technical-seo-checker), or Google Ads conversion tracking (use google-ads-audit).
---

# GA4 event tracking

Week 6, Step 5, run by SEO and Dev once the site is live. The same generic set of events goes on every build, so nothing is designed by hand: a script turns the build's own files into a GTM container file that Dev imports, a plan that tells Dev and SEO exactly what to click, and, after publishing, a page-by-page check. Your job is to collect two IDs, run the script, and report what it found. Never write or edit the plan or the container file yourself.

## Inputs

All paths are relative to the client's working folder; `<slug>` is the client folder name.

| Input | From | What is read |
|---|---|---|
| `handoff/<slug>/<slug>-dev-handoff-index.md` | dev-handoff-index | `Client:`; each page block's `Page`, `URL`, `Priority` and internal links; the `## Contact Page` URL; under `### Analytics and tracking`, the conversion point lines (`tel:` and `mailto:` links and contact forms, by page). Only `Build` pages are checked. |
| newest `qa/<slug>/<slug>-launch-check-<date>.md` | staging-site-qa, optional | the `Live:` line (the live address) |
| GA4 Measurement ID | SEO, at run time, required | `--measurement-id G-XXXXXXXXXX` |
| GTM container ID | Dev, at run time | `--gtm-id GTM-XXXXXXX`; optional for `plan`, required for `site` |
| Live address | at run time, only with no launch check | `--site https://<domain>` |
| Thank-you page | at run time, optional | `--thank-you /thank-you/` when sent forms land on a thank-you page |
| GA4 already on the site | at run time, optional | `--no-google-tag` when the site or a CMS plugin already loads GA4 and must keep doing so |

## Outputs

- `tracking/<slug>/<slug>-tracking-plan.md`: header lines (`Client:`, `Index:`, `Live:`, `Measurement ID:`, `GTM container:`, `Google tag:`, `Lead event:`, `Container file:`, `Written:`), any `WARNING:` lines, then `## Events` (`| Event | Fires when | Parameters | Key event | On this site |`), `## GTM Container`, `## Install (Dev)`, `## GA4 Settings (SEO)`, `## Test`, `## Sign-off`, `## Not Covered`.
- `tracking/<slug>/<slug>-gtm-container.json`: a GTM container export (`exportFormatVersion` 2) with the `GA4 Measurement ID` constant, the Google tag (unless `--no-google-tag`), one GA4 event tag per event and their triggers, all named `WISE - ...`.
- After publishing, `tracking/<slug>/<slug>-tracking-check-<YYYY-MM-DD>.md`: `## Pages` (`| Page | URL | GTM container | GA4 loaded twice | Conversion links | Result |`), `## Issues`, `## Notes`, `## Still to Test by Hand`, last line `RESULT: TRACKING OK` or `RESULT: TRACKING ISSUES`.

The event set, triggers and every rule the scripts apply are in `references/event-set.md`. Load it when someone asks why an event is or isn't there, or what a check result means.

## Steps

Run the script as one plain `python3` command per call from the working folder, with paths as arguments: no `&&`, `|`, `cd` or loops. Read files with the file-reading tools.

1. **Collect the IDs.** Take the GA4 Measurement ID (starts `G-`) and, if given, the GTM container ID (starts `GTM-`) from the request. If there is no Measurement ID, ask for it in one question and stop; do not make one up and do not run `plan` without it. A `UA-` or `GTM-` value is not a Measurement ID: say so and ask again. Note a thank-you page, a live address or "GA4 is already on the site" if the request names one.
2. **Write the plan and the container file.** `python3 <skill-folder>/scripts/tracking.py plan --slug <slug> --measurement-id <G-...> [--gtm-id <GTM-...>] [--site <url>] [--thank-you <path>] [--no-google-tag]`. If it stops because the index is missing, tell them to run dev-handoff-index first. Read every `WARNING:` it prints.
3. **Check them.** `python3 <skill-folder>/scripts/tracking.py check --slug <slug>`. It must end `RESULT: PASS`. A FAIL means the files were changed by hand or the run was interrupted: run `plan` again, never edit the files.
4. **Report.** Give both paths, list the events with the key events marked, and repeat each warning in plain words (for example: no live address, so staging visits will count until `plan` is re-run with `--site`). Tell Dev to follow the plan's Install section (import with Merge, Preview, Publish) and SEO to follow its GA4 Settings section. Say you did not touch GTM or GA4 and nothing is live until Dev publishes.
5. **After Dev publishes**, when asked to check the tracking: `python3 <skill-folder>/scripts/tracking.py site --plan tracking/<slug>/<slug>-tracking-plan.md [--gtm-id <GTM-...>] [--saved <folder>]`. Without `--saved` it loads each Build page from the live address; with it, it reads saved pages (`index.html`, `<path>/index.html`). If it stops for a missing GTM ID, ask Dev for it. Report the result line first, then each issue with its page and fix, then the hand tests still to do in Preview and DebugView. `RESULT: TRACKING OK` does not prove events arrive; only those hand tests do.

## Rules

- The event set is the same for every site. Do not add, rename or drop events, or change which ones are key events, in the files. Live chat, Juvo, call-tracking numbers, ecommerce and ad-platform conversions are not covered; say so if asked.
- You only write files. Never claim the container is imported, published or firing, or that key events are marked in GA4, unless the person tells you a person did it.
