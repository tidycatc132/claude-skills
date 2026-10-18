# Processing rules

How to turn the Kickoff Call into `call-processing-plan.json`. The script rejects a plan that breaks the mechanical rules (marked *checked*); the judgment rules are yours.

## The plan file

```json
{
  "client": "Copperline Plumbing",
  "call_date": "2026-11-10",
  "agency_speakers": ["Dana Pruitt"],
  "updates": [
    {"section": "Services", "fact": "Water heater replacement is the service they most want to grow", "speaker": "Gus Moreno", "timestamp": "00:01:12", "quote": "Water heaters are where the margin is, push those."},
    {"section": "Platform Access", "fact": "Google Analytics: confirmed, the developer verified the invite during the call", "speaker": "Dana Pruitt", "timestamp": "00:09:40", "quote": "Zac just confirmed the Analytics invite came through."}
  ],
  "package": {
    "Services Priority": [{"text": "1. Water heater replacement, the service to grow first", "timestamps": ["00:01:12"]}],
    "Open Items": [{"text": "Hosting provider unknown; Gus will ask his nephew", "timestamps": ["00:09:58"]}]
  },
  "quotes": [
    {"quote": "Water heaters are where the margin is, push those.", "speaker": "Gus Moreno", "timestamp": "00:01:12", "use_for": ["services", "homepage"]}
  ],
  "page_mentions": [
    {"timestamp": "00:07:46", "kind": "promise", "low": 25, "high": 30, "said": "the initial build would be about twenty-five to thirty pages", "speaker": "Dana Pruitt", "quote": "we're looking at probably twenty-five to thirty pages"},
    {"timestamp": "00:07:00", "kind": "other", "note": "a competitor's page count"}
  ],
  "deliverables": [
    {"said": "a monthly email newsletter", "in_scope": false, "speaker": "Dana Pruitt", "timestamp": "00:04:26", "quote": "Sure, we can set that up for you."},
    {"said": "the Growth Blueprint by end of next week", "in_scope": true, "speaker": "Dana Pruitt", "timestamp": "00:11:00", "quote": "You'll have that by end of next week."}
  ]
}
```

- `client` equals the context's `Client:` line; `call_date` is `YYYY-MM-DD`; `agency_speakers` names the WISE people on the call exactly as the transcript spells them (*checked*).
- Every `quote` is copied word for word from one turn of that `speaker` at that `timestamp`: a contiguous piece of the turn, never cleaned up, shortened in the middle or joined across turns. Only whitespace and curly versus straight quotes are forgiven (*checked*).
- `timestamp` is `HH:MM:SS` as the `transcript` command prints it (*checked*).

## Update rows (`updates`)

These become `<slug>-call-updates.md`, which client-context-update merges into the context. Write one row per fact the call adds, changes or confirms that a later step needs.

- `section` is the context heading the fact belongs under, or `Platform Access` or `Intake Items` (*checked*). Never `Open Items` or `Sources`. Use the context's own sections: services in `Services`, areas and customer types in `Customers and Service Area`, voice, conversion and design references in `Goals and Conversion`, proof and differentiators in `Differentiators and Proof`, named competitors in `Competitors`, statements about the current site in `Website Today`.
- `fact` is one statement in plain words, in the speaker's terms, with no source tag and no `CONFLICT:` or `GAP:` prefix (*checked*). Say what was said, not that it was said ("Serves Hampstead twice a week", not "Ray mentioned Hampstead").
- Answer the gap questions the call answers: a row with the answer in the section of the matching `GAP:` bullet. A vague answer ("I'll have to check") is an open item, not a row.
- When the call contradicts a context fact, still write the row with the new version; client-context-update decides whether it wins or becomes a conflict.
- What WISE says on the call is evidence only for what WISE did or checked (access verified, a page count it looked up). The client's own words are the evidence for the business.
- `Platform Access` facts start `<Platform>: <status>` from the fixed lists (*checked*). Platforms: `Domain`, `Hosting`, `Website login`, `Google Analytics`, `Google Search Console`, `Google Business Profile`, `Google Tag Manager`, `Google Ads`, `Meta ads`, `Microsoft Ads`, `CRM, forms or call tracking`. Statuses: `confirmed` only when WISE says on the call that the access arrived and works; `invite sent` when the client says they already sent it; `someone else manages it` (say who); `not set up` when they say they never had it; `not sure`; `no answer` when the client holds the account and will add us or send it later (say who holds it); `needs help`; `n/a`. Never copy a username, password or code (*checked*); name only the platform.
- `Intake Items` facts start `<Item>: <status>` (*checked*), for items supplied or promised on the call, for example `Sites they like: received on the call, names only, no URLs`. Items: `Primary contact`, `Website approver`, `Business name, address, phone and hours`, `Logo files`, `Brand guidelines`, `Photos`, `Testimonials or reviews`, `Team members`, `Certifications, awards and memberships`, `Legal or compliance language`, `Sites they like`, `Things to avoid`, `Gap question answers`. Statuses: `received`, `partial`, `missing`, `none`, `n/a`.
- `python3 <skill-dir>/scripts/process_call.py updates kickoff/<slug>/<slug>-call-updates.md --json` prints the written file as client-context-update reads it, with the keys `Client`, `Source`, `Date`, `From` and `rows`.
- Do not write rows for scope promises: list them under `page_mentions` and `deliverables` and the script writes the `Scope Summary` `CONFLICT:` rows itself.

## Package bullets (`package`)

The Blueprint Input Package must let SEO start the Growth Blueprint without opening the transcript. Each bullet is one point with the timestamp(s) of the turns it comes from; the script adds `[call]`. A section the call never touched gets "Not discussed on the call." from the script; leave it out of the plan.

| Section | What goes in it |
|---|---|
| `Services Priority` | Services in the order the client wants them sold, numbered `1.`, `2.`; services to play down or drop, and why. |
| `Audiences` | Who the site is for: customer types, referral sources (realtors, other firms), what each needs. |
| `Service Area Tiers` | Core, secondary and excluded areas as tiers ("Core: ...", "Secondary: ...", "Not targeted: ..."), with any share of clients they gave. |
| `Voice and Design Direction` | How the site should sound, in the client's words; sites they like and why; what to avoid (looks, features, words). |
| `Competitors` | Each named competitor and how the client sees them; anything WISE shared about them. |
| `Topics to Own` | Subjects the client wants to be the go-to source on, with the customer question behind each when they gave one. |
| `Goals and Success Measures` | What a win looks like: leads, bookings, the conversion action, numbers they gave. |
| `Scope Decisions` | Scope points settled on the call that are not conflicts (a page type agreed, a deliverable date). The script puts the scope source lines and the conflicts first. |
| `Open Items` | Everything discussed but not settled, with who owes it: missing access, decisions to make, files to send. |

Only what was said on the call goes in, and every bullet must be true of the turns it cites. Do not add what WISE will do next, how the SOW or the context covers it, or any other conclusion of yours: "Search Console: never set up, per Ray" is right, "WISE will set it up under the SOW" is not, unless someone said so on the call. The context already holds the Sales call; do not copy it in unless the client restated it on this call.

## Quotes (`quotes`)

8 to 12 quotes (fewer only when the client spoke fewer turns), each at least 5 words, from client-side speakers only, never from `agency_speakers` (*checked*). Prefer the lines a writer or strategist would reuse: their top priority, what they want the site to feel like, what they dislike, how they beat competitors, what success means, what they explicitly do not want. One idea per quote; no two quotes the same.

`use_for` is one or more of `services`, `audience`, `service-area`, `voice`, `design`, `competitors`, `proof`, `topics`, `goals`, `pain-point`, `homepage` (*checked*).

## Page counts and deliverables (the scope rule)

The scope source (the SOW, or the signed deal terms when there is no SOW) owns the page count and the deliverables. Nothing said on a call changes it.

- **Every page-count mention the `transcript` command lists gets a `page_mentions` entry** (*checked*). `kind` is `promise` when WISE states how many pages the build will have, `request` when the client asks for a number, `other` for anything else (a competitor's site, the current site, the client repeating a number just said), with a `note`. A `promise` or `request` gives `low` and `high` as numbers (one number: both the same), `said` in a few words, and the verbatim quote.
- The script flags a `promise` or `request` as a `CONFLICT:` unless both numbers equal the scope source's `SOW pages:` count. When `SOW pages:` is `unknown`, every stated count is a conflict: a call cannot set the count the signed scope left open.
- **List every deliverable WISE promised or agreed to on the call** under `deliverables`, with `in_scope` `true` when the context's `Included services:` (or the quoted scope lines) covers it and `false` otherwise (an email newsletter, blog writing, paid media, extra page types). A `false` becomes a `CONFLICT:`. A date for a deliverable that is in scope (the Growth Blueprint, a summary email) is `in_scope: true`, not a conflict.
- Never write the conflict yourself, never present the call's number as the new scope, and never drop a conflict because the client was happy with it.
