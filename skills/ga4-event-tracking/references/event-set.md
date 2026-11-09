# Event set and check rules

What `scripts/tracking.py` builds and checks. Load this to explain a result; never use it to hand-edit the files.

## Events

| Event | Trigger in GTM | Parameters | Key event |
|---|---|---|---|
| `generate_lead` | Form Submission, wait for tags and check validation on, only on the pages the index lists with a contact form (all forms, with a WARNING, when it lists none). With `--thank-you <path>`: Page View where Page Path is that path (with or without the closing slash) | `lead_type` = `form`, `form_id` = Form ID (form mode only) | yes |
| `click_to_call` | Just Links, Click URL starts with `tel:` | `lead_type` = `phone`, `link_url`, `link_text` | yes |
| `click_to_email` | Just Links, Click URL starts with `mailto:` | `lead_type` = `email`, `link_url`, `link_text` | no |
| `get_directions` | Just Links, Click URL matches Google Maps (`google.<tld>/maps`, `maps.google.`, `maps.app.goo.gl`, `goo.gl/maps`) or Apple Maps (`maps.apple.com`) | `link_url`, `link_text` | no |
| `cta_click` | Just Links, Click URL is the contact page on the live domain, and the current page is not the contact page. Left out when the index has no `## Contact Page` | `link_url`, `link_text` | no |

Why these: they are the conversion points every WISE build has (the dev handoff index already lists phone, email and form points by page, and asks for the form submit as a key event), plus the two path signals that work on any site (map clicks and clicks toward the contact page). Phone calls are a key event because for local service clients a call is the most common lead. GA4 enhanced measurement already records page views, scrolls, outbound clicks, site search, video and file downloads, so none of those are added.

Use the thank-you mode when the contact form sits in an iframe, is built by a script, or is sent by AJAX without a normal submit (Contact Form 7, WPForms or Gravity Forms in AJAX mode often are): GTM's Form Submission trigger cannot see those. The site check reports a contact page with no `<form>` element as an issue; an AJAX form still has `<form>`, so only the Preview test shows it, when `generate_lead` does not fire.

Custom dimensions to register: `lead_type` and `form_id`. Link URL and Link text are already GA4 dimensions from enhanced measurement.

## Container contents

- Constant variable `GA4 Measurement ID`; built-in variables Page URL, Page Hostname, Page Path, Click URL, Click Text, Form ID.
- Tag `WISE - Google tag (GA4)` (type `googtag`), unless `--no-google-tag`, on `WISE - Initialization (live site only)` when the live address is known, else on the built-in Initialization - All Pages.
- One `WISE - GA4 event - <event>` tag (type `gaawe`) per event, sending to the Measurement ID variable.
- Hostname guard: when the live address is known, every trigger also needs Page Hostname to match the live domain, with or without `www.`. Without a live address there is no guard and the plan warns that staging visits will count.
- Import with Merge and Rename conflicting, so a client's existing tags are kept.

## `check` rules

`RESULT: PASS` needs all of: the container file named in the plan exists and is valid JSON in export format 2; every tag fires on a trigger in the file (or the built-in Initialization trigger); every `{{variable}}` is defined or a switched-on built-in; ids are unique; the Measurement ID looks like `G-` plus letters and digits and matches the container's constant; each event sends at most 25 parameters; event names are valid GA4 names (start with a letter, letters, digits and underscores, at most 40 characters, no `google_`, `ga_` or `firebase_` prefix); the plan's Events table and the container list the same events; `generate_lead` is a key event; the Google tag is in the container exactly when the plan says so; with a live address, every trigger carries the hostname guard and the Google tag does not fire on the built-in all-hosts Initialization trigger.

## `site` rules

For every `Build` page in the index:

- ISSUE when the GTM container ID is not on the page, or the ID is there without the `gtm.js` loader.
- ISSUE when the container holds the Google tag and the page also loads the same Measurement ID directly (`gtag/js?id=` or `gtag('config', ...)`): page views count twice.
- ISSUE when the plan says the site loads GA4 itself (`--no-google-tag`) and the page does not.
- ISSUE when the page does not load (live) or was not saved (saved mode).
- ISSUE when the index lists a contact form on the page, the lead event is form submission, and the HTML has no `<form>` element.
- NOTE when the noscript iframe is missing, another GA4 property is loaded, or a `tel:` or `mailto:` link the index lists is not on the page.

`RESULT: TRACKING OK` means no ISSUE. The hand tests in GTM Preview and GA4 DebugView are still needed.
