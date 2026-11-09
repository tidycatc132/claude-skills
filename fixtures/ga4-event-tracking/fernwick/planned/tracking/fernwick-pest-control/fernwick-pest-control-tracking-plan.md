Client: Fernwick Pest Control
Index: handoff/fernwick-pest-control/fernwick-pest-control-dev-handoff-index.md
Live: https://fernwickpest.com (from qa/fernwick-pest-control/fernwick-pest-control-launch-check-2026-11-12.md)
Measurement ID: G-7QX3LM2K9P
GTM container: GTM-W4K8P2Q
Google tag: in container
Lead event: form submission
Container file: tracking/fernwick-pest-control/fernwick-pest-control-gtm-container.json
Written: 2026-11-13

# Event Tracking Plan: Fernwick Pest Control

## Events

| Event | Fires when | Parameters | Key event | On this site |
|---|---|---|---|---|
| `generate_lead` | a form on the site is submitted and passes the browser's validation | `lead_type`, `form_id` | yes | Contact (Book an Inspection) |
| `click_to_call` | a visitor clicks a phone link (tel:) | `lead_type`, `link_url`, `link_text` | yes | Home, Termite Treatment, Rodent Control, Contact (tel:+19785550147) |
| `click_to_email` | a visitor clicks an email link (mailto:) | `lead_type`, `link_url`, `link_text` | no | Contact (mailto:office@fernwickpest.com) |
| `get_directions` | a visitor clicks a Google Maps or Apple Maps link | `link_url`, `link_text` | no | the index does not list map links; fires on any Google Maps or Apple Maps link |
| `cta_click` | a visitor clicks a link to the contact page /contact/ from another page | `link_url`, `link_text` | no | Home (Book an inspection); Termite Treatment (Get a termite inspection); Rodent Control (Book a rodent visit); Townsend Pest Control (Book a Townsend visit) |

GA4 enhanced measurement already records page views, scrolls, outbound clicks, site search, video plays, file downloads and form interactions; this container adds only the events above, so nothing is counted twice.

## GTM Container

`tracking/fernwick-pest-control/fernwick-pest-control-gtm-container.json` holds, all named with the prefix `WISE - `:

- Variable `GA4 Measurement ID` (constant): `G-7QX3LM2K9P`.
- Tag `WISE - Google tag (GA4)` on Initialization - All Pages: loads GA4 and sends page views.
- Tag `WISE - GA4 event - generate_lead`: fires when a form on the site is submitted and passes the browser's validation.
- Tag `WISE - GA4 event - click_to_call`: fires when a visitor clicks a phone link (tel:).
- Tag `WISE - GA4 event - click_to_email`: fires when a visitor clicks an email link (mailto:).
- Tag `WISE - GA4 event - get_directions`: fires when a visitor clicks a Google Maps or Apple Maps link.
- Tag `WISE - GA4 event - cta_click`: fires when a visitor clicks a link to the contact page /contact/ from another page.
- Every trigger, including the one that loads the Google tag, fires only on the live hostname `fernwickpest.com` (with or without www), so staging visits are never counted.
- `generate_lead` listens only on the pages the index lists with a contact form: `/contact/`. Search, newsletter and comment forms elsewhere are not counted as leads.
- Built-in variables switched on: Page URL, Page Hostname, Page Path, Click URL, Click Text, Form ID.

## Install (Dev)

1. In Google Tag Manager open the client's web container `GTM-W4K8P2Q`. Admin > Import Container.
2. Choose `tracking/fernwick-pest-control/fernwick-pest-control-gtm-container.json`. Workspace: Existing, the default workspace. Import option: Merge, then Rename conflicting tags, triggers and variables. Confirm.
3. If GA4 is already loaded another way (a Google tag or GA4 configuration tag already inside this GTM container, a hard-coded gtag.js snippet, or a CMS plugin sending the same Measurement ID), remove or pause it now, or the site counts every page view twice. The site check can only see the page code, not other tags inside GTM.
4. Make sure the container snippet is on every page: the script in the head and the noscript iframe right after the opening body tag.
5. Click Preview, open the live site, and do each test in the Test section below. Every event tag must show under Tags Fired.
6. Submit, version name `WISE event tracking 2026-11-13`, and Publish.
7. Run the site check: `python3 <skill-folder>/scripts/tracking.py site --plan tracking/fernwick-pest-control/fernwick-pest-control-tracking-plan.md`. It must end `RESULT: TRACKING OK`.

## GA4 Settings (SEO)

1. Admin > Data display > Key events > New key event: add `generate_lead`, `click_to_call`. Adding them by name now means the first conversion already counts.
2. Admin > Data display > Custom definitions > Create custom dimension, scope Event, for each parameter: `lead_type`, `form_id`. Use the parameter name as the dimension name.
3. Admin > Data collection and modification > Data streams > the web stream > Enhanced measurement: leave it on with every option on.
4. Admin > Data collection and modification > Data retention: set event data retention to 14 months.
5. Admin > Product links: link Google Search Console to the property if it is not linked yet.

## Test

Dev runs these in GTM Preview; SEO then watches each event arrive in GA4 Admin > DebugView.

| Event | How to test | Pass when |
|---|---|---|
| `generate_lead` | fill in and send a contact form with test details (say TEST in the message). If the tag does not fire, the form is probably sent by AJAX: re-run plan with --thank-you <path> | the tag shows under Tags Fired, and `generate_lead` appears in DebugView with its parameters |
| `click_to_call` | click a phone number link (on a phone, or cancel the call prompt on a computer) | the tag shows under Tags Fired, and `click_to_call` appears in DebugView with its parameters |
| `click_to_email` | click an email address link | the tag shows under Tags Fired, and `click_to_email` appears in DebugView with its parameters |
| `get_directions` | click a directions or map link, if the site has one | the tag shows under Tags Fired, and `get_directions` appears in DebugView with its parameters |
| `cta_click` | on any page except the contact page, click a button or link that goes to the contact page | the tag shows under Tags Fired, and `cta_click` appears in DebugView with its parameters |

## Sign-off

- [ ] Container imported, previewed and published (Dev)
- [ ] Site check ends `RESULT: TRACKING OK` (Dev)
- [ ] Every event seen in DebugView (SEO)
- [ ] Key events and custom dimensions added in GA4 (SEO)

## Not Covered

- Live chat, Juvo, call-tracking numbers, booking widgets inside an iframe, ecommerce and Google Ads or Meta conversions are not part of this generic set. Add them on their own only when the client has them.
