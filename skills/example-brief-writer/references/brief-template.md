# Brief template

`scripts/make_briefs.py` chooses the outline and word-count target from `page_type`.

| `page_type` | Outline (H2s) | Words |
|---|---|---|
| `service` | What it is; Who it is for; How it works; What affects the price; FAQs; Next step | 900 |
| `location` | Service area; Local proof; Services offered here; FAQs; Contact | 700 |
| `blog` | Quick answer; Key points; Common mistakes; FAQs; Related reading | 1200 |

Every brief ends with the same checklist: the target keyword appears in the title and the first paragraph, each H2 is answerable on its own, and every claim has a source or is marked for the client to confirm.

To change an outline or word count, edit the `OUTLINES` table at the top of `scripts/make_briefs.py` and update this file to match.
