# Default voice and style

Read this only when the client's `voice.md` or `style.md` is missing. A client's own file always wins, file by file: a client `voice.md` with a missing `style.md` uses the client voice and the default style.

## Pick the industry

Determine it from `brand.md` (industry, services), else from the client domain, the services in the keyword report and the topic. Record what you used under Research Log, Assumptions.

| Industry slug | Covers | Voice file | Style file |
|---|---|---|---|
| `home-services` | plumbing, HVAC, roofing, electrical, pest control, cleaning, landscaping, restoration, general contracting | `home-services-voice.md` | `home-services-style.md` |
| `financial-services` | banks, credit unions, lending, mortgages, insurance, financial advice, tax, accounting | `financial-services-voice.md` | `financial-services-style.md` |
| `legal` | law firms, legal services, mediation, notaries | `legal-voice.md` | `legal-style.md` |
| `b2b-saas` | software, SaaS, IT services, agencies, consulting, professional services sold to businesses | `b2b-saas-voice.md` | `b2b-saas-style.md` |

Set `voice_source` and/or `style_source` to `default/<industry-slug>`.

## No matching industry: generate

When the industry is none of the above, write the directives yourself and set the source to `default/generated`. A generated default has the same parts as the files here, in the same order:

- **Voice**: who is speaking (the business, first person plural, or a named expert), reading level, 4 to 6 tone directives as do/don't pairs, how to handle uncertainty and risk, how to make the call to action.
- **Style**: English variant and spelling, number and unit style, date style, capitalization of headings, terms to prefer and to avoid for this industry, claim rules (what may be claimed and how it must be supported).

Base it on how the top-ranking pages for the row's keyword and the industry's regulators write, not on invention. A generated default is always a concern.

## Using a default in a brief

Embed the default's directives in full under `## Voice and Style`, because the writer will not have this skill's files. Add 2 to 3 lines applying them to the page's topic.
