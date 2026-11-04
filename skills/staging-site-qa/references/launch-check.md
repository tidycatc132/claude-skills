# Launch check

The launch mode of this skill. Dev runs it right after the site is deployed, against the production base URL. It uses the same findings table, severities, finding ids, re-run marks and BugHerd path as staging QA, with these differences.

## What it reads

| Input | Required | What is read |
|---|---|---|
| Production base URL | yes | The live site root, for example `https://saltmarshtreecare.com`. Never the staging URL (the scan stops if it is). |
| `handoff/<slug>/<slug>-dev-handoff-index.md` | yes | Each `Build` page's URL, `Meta title`, `Meta description` and `H1`, and the `### Redirects` table `| Old URL | New URL | Note |` under `## Global`. |
| `kickoff/<slug>/<slug>-context.md` | yes | `Client:` and the `Website:` line (also accepted as the production domain for canonicals and sitemap URLs). |
| Newest `qa/<slug>/<slug>-staging-qa-<date>.md` | yes, or `--staging-url` | Its `Staging:` line: the staging domain to look for. |
| `qa/routing.md` | if it exists | The Development column and assignee. |
| Saved pages folder (`--saved`) | when the live site can't be reached from here | Each Build page as `<folder>/index.html`, `<folder>/contact/index.html` and so on, plus `robots.txt` and `sitemap.xml` (and any child sitemaps it names) at the folder root. |
| Redirect-response file (`--redirects-file`) | with `--saved` | One line per old URL: `<old URL> <status> <location>`, exactly what `curl -s -o /dev/null -w '%{url_effective} %{http_code} %{redirect_url}\n' <old URL>` prints. Lines starting with `#` are ignored. |

Without the redirect file, or without `robots.txt` or `sitemap.xml` in the saved folder, those checks did not run: the report says which in one MAJOR finding on `/`, so it can't read `LIVE OK` until they are saved and the check is re-run.

## Checks

Every finding is Development's: the site is live and Dev owns what changed in deployment.

| Check | What counts as a finding | Severity |
|---|---|---|
| Page exists | 404, not in the saved pages, or a redirect to another address | CRITICAL |
| HTTP status | anything other than 200, or no response | CRITICAL |
| HTTPS | the page or the base URL is plain HTTP (live only) | MAJOR |
| noindex | any meta robots or googlebot tag (every one on the page, not just the last), or an `X-Robots-Tag` header (live only), holding `noindex` or `none`. At launch this is a finding, not a toggle | CRITICAL |
| `Meta title` | missing (CRITICAL) or not the index value (MAJOR) | as stated |
| `Meta description` | missing or not the index value | MAJOR |
| `H1` | missing (CRITICAL), not the index value (MAJOR), more than one (MINOR) | as stated |
| Canonical | missing, on the staging domain, on another domain, or not this page's path | MAJOR |
| Staging domain | any link, image, script, stylesheet, `og:url` or `og:image` on the staging host, plus any staging-host URL (or subdomain) written anywhere in the HTML, such as `srcset`, inline CSS or scripts: one finding per page with a count and examples | MAJOR |
| Redirects | a `### Redirects` row with a New URL that does not answer 301 or 308 to it: no redirect, a temporary 302/303/307, or the wrong target. The finding's page is the old path. `NO TARGET` rows are listed under Not Checked for SEO | MAJOR |
| robots.txt | a `Disallow` rule that blocks a Build page, testing Googlebot's own group (if robots.txt has one) and the `*` group each on its own, as crawlers do (longest match wins; `Allow` wins a tie); one finding on `/robots.txt` | CRITICAL |
| sitemap.xml | `/sitemap.xml` missing (MAJOR); a Build page not listed (one finding); a URL on the staging domain (one finding). A sitemap index is followed to its child sitemaps on the live domain (nested indexes too, up to 200); in saved mode an unsaved child sitemap goes into the not-tested finding | MAJOR |

Old URLs on the production domain are requested on the base URL with the same path, without following the redirect; old URLs on another domain are requested as written. A redirect passes only when its target is HTTPS and its path is the New URL exactly (same case and trailing slash), so a hop that needs a second redirect is a finding. Saved responses are matched on host and path as written.

Not checked by the script, so they are the report's `## Dev Tick List` (Dev ticks them by hand): forms submit, live chat loads, analytics firing, Juvo snippet installed, SSL certificate valid.

## Files

- `qa/<slug>/<slug>-launch-scan.json`: the scan's working file.
- `qa/<slug>/<slug>-launch-check-<YYYY-MM-DD>.md`:

```
Client: <client>
Checked: <date>
Live: <production base URL> (saved pages: <folder>/)
Staging domain: <host> (<staging QA report path> | given)
Dev handoff index: <path> (<its last line>)
Redirects: <n> of <n> tested answer 301 or 308 to their New URL | not tested (...) | none in the index (no existing site)
Compared with: <earlier launch check path> | none (first run)

# Launch Check: <client>

## Summary

Pages checked: <n> of <n> Build pages (<n> missing on the live site); skipped (not Build): <n>
Open findings: <n> CRITICAL, <n> MAJOR, <n> MINOR
By department: Content 0, SEO 0, Design 0, Development <n>
Re-run: <n> FIXED, <n> OPEN, <n> NEW          (re-runs only)
Structured data: not in the current process

## Findings
| # | Page URL | Department | Severity | Finding | Fix |
## Re-run Status                                  (re-runs only)
## Dev Tick List
- [ ] Forms submit, and the test entry reaches the client's notification inbox
- [ ] Live chat loads and a test message arrives
- [ ] Analytics firing: a visit shows in GA4 Realtime
- [ ] Juvo snippet installed
- [ ] SSL certificate valid: the padlock shows and the certificate does not expire within 30 days
## Not Checked

RESULT: LIVE OK | LIVE ISSUES
```

A re-run with nothing open now or last time writes one `none` row in `## Re-run Status`. Recorded BugHerd ids are carried on every run, the same day too; only a finding that was FIXED and comes back NEW loses its old id and gets a new task.

`RESULT: LIVE OK` means no CRITICAL or MAJOR finding is open; MINOR findings can stay for the monthly work. There are no Launch Toggles or AM Items sections.

- `qa/<slug>/<slug>-launch-bugherd-tasks.json`: the same keys as the staging task file (`references/report-format.md`), every object `department` `Development` with the routing's Development column, `description` ending `(Launch check <date>, <finding_id>)`. It is a separate file, so the staging task file and what week-5-handoff-check reads from it never change.

`qa.py launch-check <report>` prints what later skills read from a launch check: `Live:`, `## Findings`, `## Re-run Status`, `RESULT:` and the task file's `tasks`. `qa.py redirects <index>` prints the index's redirect rows (`Old URL`, `New URL`, `Note`); contract `dev-handoff-index-to-staging-site-qa-launch`.
