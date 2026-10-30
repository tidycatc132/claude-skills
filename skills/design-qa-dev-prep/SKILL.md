---
name: design-qa-dev-prep
description: Checks the designers' inner-page templates against the page-type design briefs, the reference kit and the written pages before dev handoff, and writes dev's asset checklist. Reads the templates from Figma through the Figma connector, or from a design inventory the designer fills in; a script checks that every brief section has a container and none is empty, the template holds the longest page, CTAs sit where the brief puts them, colours and fonts match the brand kit and every asset has its details. Writes design/slug/slug-design-qa-devprep.md ending in RESULT PASS or FAIL. Use when Design asks for the design quality checklist, design QA or dev prep on the page templates, or whether the inner-page templates fit the pages and are ready for development. Do NOT use for template briefs (use page-type-design-briefs), the homepage brief (use homepage-design-brief), the dev handoff index (use dev-handoff-index), staging or live site checks (use technical-seo-checker), or the kit (use client-reference-kit).
---

# Design QA and dev prep

The designers build one template per page type from the page-type design briefs. Before dev starts, this skill checks that each template can hold what the briefs and the written pages need, and lists every asset dev will ask for. The comparison is done by a script; your job is to get an accurate inventory of the templates and to report what Design must fix.

## Input

All paths are relative to the client's working folder. `<slug>` is the client's folder name under `design/`.

| Path | Required | What it gives |
| --- | --- | --- |
| `design/<slug>/<slug>-page-type-design-briefs.md` | yes | From page-type-design-briefs: one section per page type (`## Service Pages`, `## Location Pages`, `## About Page`, `## Contact Page`, `## Resource Pages`), each with `### Pages`, `### Content Map` (the `Section` column), `### CTAs`, `### Content Length` (`H2 sections:`) and `### Responsive Priorities` |
| `content/<url-slug>/article.md` | yes | The written pages the briefs list, used to find the longest page of each type |
| `client-reference/<client-slug>/brand.md` (and `style.md`) | no | Colours and fonts the design may use. Pass `--kit` when there is more than one kit folder |
| `design/<slug>/<slug>-design-inventory.md` | yes, made in step 2 | What the templates hold, in the format in `references/inventory-format.md` |

If the page-type design briefs are missing, say they come first (page-type-design-briefs) and stop.

## Output

`design/<slug>/<slug>-design-qa-devprep.md`, written only by the script:

- Header line `Client: · Checked: · Inventory:`, then `# Design QA and Dev Prep: <client>`.
- `## Results`: `| Template | Check | Result | Detail |`, Result `PASS`, `FAIL` or `FLAG`. Checks per page type: `Template exists`, `Brief sections have containers`, `Containers have content`, `Section order`, `Holds the longest page`, `CTA placement`. Site-wide (`All`): `Inventory filled`, `Colours sourced`, `Fonts sourced`, `Asset details complete`.
- `## To Fix` (every FAIL, owner Design) and `## To Confirm` (every FLAG).
- `## Mobile-First Priorities`, copied from each brief's Responsive Priorities.
- `## Asset Checklist` with `### Images`, `### Icon set`, `### Fonts`, `### Colour palette`, `### Spacing`, `### Interactive elements`, copied from the inventory. It is the last section; dev-handoff-index copies it into the dev handoff index.
- Last line `RESULT:` then `PASS` or `FAIL` (`RESULT: PASS`, `RESULT: FAIL`). Any FAIL fails; a FLAG alone does not. dev-handoff-index treats `RESULT: FAIL` as blocking.

## Running the script

The script is `scripts/dqa.py` in this skill's folder. Run it from the client's working folder by its full path, as one plain command: `python3 <skill-folder>/scripts/dqa.py <mode> --slug <slug> ...`. Nothing chained before or after it (no `cd`, `&&`, pipes or loops). If a call is denied, send the same single `python3` command again, and use `python` if `python3` is missing. Never write the QA file or its results by hand because a call failed.

## Workflow

1. **Scan.** `python3 <skill-folder>/scripts/dqa.py scan --slug <slug>`. It lists each page type with its content-map sections, the sections the brief puts CTAs after, the longest page, the brand sources and whether an inventory exists.
2. **Get the inventory.** In this order:
   - An inventory already exists at `design/<slug>/<slug>-design-inventory.md` and the user did not say the designs changed: use it as it is.
   - The user gave a Figma link and Figma connector tools are available: read the file as `references/figma-read.md` says and write the inventory in `references/inventory-format.md`'s format with `Source: figma <link>`. Write only what you read; a value you could not read stays `<fill>`.
   - Otherwise: `python3 <skill-folder>/scripts/dqa.py template --slug <slug> --client "<client name>"`. It writes a blank inventory listing each template and its brief sections. Tell the user the designer fills it in (or sends the Figma link) and the check runs after. Stop there; do not run the check and do not make up design details.
3. **Run.** `python3 <skill-folder>/scripts/dqa.py run --slug <slug> --client "<client name>" --date <today>`. It writes the QA file and prints every FAIL and FLAG.
4. **Report** in a few lines: the result, each FAIL as a fix for Design in plain words, each FLAG as something Design confirms (for example a colour no brand source lists), and the QA file's path. On PASS, say dev-handoff-index will pick up the asset checklist. Do not soften a FAIL or call the templates ready when the result is FAIL.

When Design fixes something, they update the inventory (or you re-read Figma) and step 3 runs again.

## Rules

- The inventory records what the design has, never what it should have. Map each layer to the brief section it holds; use `global` for header, footer and navigation, and `none` for a layer that holds no brief section. Do not rename a layer to make it match.
- Do not judge looks. This is a fit check against the briefs and the brand sources, not a design critique.
- A colour or font no source names is a FLAG for Design to confirm, not a change you make.

## Scripts

| Script | Use |
| --- | --- |
| `scripts/dqa.py scan` | Briefs, longest pages, brand sources, inventory status |
| `scripts/dqa.py template` | Blank inventory for the designer (`--force` to replace one) |
| `scripts/dqa.py run` | The checks and the QA file |
| `scripts/dqa.py briefs` | The briefs as this skill reads them, as JSON under `## Page Types` (`--validate` for the contract) |
| `scripts/selftest_dqa.py` | Cases for the checks; run after changing `dqa.py` |

Standard-library Python 3 only.
