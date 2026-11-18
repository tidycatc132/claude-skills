---
name: client-reference-kit
description: Use when the user wants the reference files a content team works from for one client, such as a client reference kit, brand and voice kit, style guide, source-of-truth pack or client onboarding docs, or asks to create or rebuild brand.md, voice.md, style.md, audience.md or compliance.md. Builds all five in one run from the project's own files first, then the client's website, then targeted web search for gaps, resolving conflicts in that order. The kit covers positioning, offers, approved claims, CTAs, voice, tone, do and don't phrasing, house style, lexicon, banned words, ICP, personas, objections, regulations, disclaimers and review triggers. Do NOT use for writing an article or page from the kit (use seo-content-writer), building personas alone (use audience-persona-builder), a scored brand audit or brand health report (use brand-research), or an E-E-A-T quality audit of one page or draft (use content-quality-auditor).
---

# Client reference kit

Writes five files that every writer and designer on a client account works from. Every line is a fact about this client, sourced, or a labelled gap. Write all five in one run; do not stop to ask the user anything before the files exist.

## Input

- The client: a name, domain or URL from the user's message. If none is given, take it from the workspace (a client folder name, a brief, an SOW).
- Output folder: the path the user names, otherwise `client-reference/<client-slug>/`, where the slug is the domain without `www.` and without the TLD (`kineticpathpt.com` gives `kineticpathpt`).

## Output

Five files in the output folder: `brand.md`, `voice.md`, `style.md`, `audience.md`, `compliance.md`. Their required `##` headings, counts and table columns are in `references/file-specs.md`. Read it before writing the first file.

## Discovery, in this order

1. **Project files.** Read briefs, kickoff or call notes, SOWs, existing guides, emails and any earlier kit in the working directory. These are tier `[internal]`.
2. **Client website.** Fetch the homepage, About, Products or Services, Pricing, Terms and Privacy Policy pages, plus any page those link to that states claims, credentials or disclaimers. Saved copies of the site in the project count as this tier, `[site]`.
3. **Targeted web search.** Search only for a named gap: the regulations that apply, third-party reviews or awards, competitor differentiators. Tier `[search]`. Skip this step when no search tool is available and say so in the answer.

When sources disagree, internal beats site, and site beats search. Record each conflict under `### Conflicts resolved` in that file's `## Sources`. A retired price, claim or name may appear only on a line that says it is retired.

For regulations, start from `references/regulatory-starters.md` and keep the rules the client's industry, locations, channels and offers actually trigger.

## Gaps

When no source has a required fact, write a line starting `GAP:` saying what is missing and who can supply it. A labelled `Recommended` default may follow when one is sensible (for example a serial-comma rule). Never fill a section with invented numbers, ratings, awards or certifications.

## Finish

1. Run the checker as its own plain command, giving the script by its path inside this skill's folder and the output folder as the argument:
   `python3 <skill-folder>/scripts/check_kit.py <output-folder>`
   Use whichever shell tool the session has (Bash or PowerShell). If a call is denied, retry the same plain `python3` command without `cd`, pipes or `&&`, and try the other shell tool if one exists. Do not conclude that the shell is unavailable. If `python3` is not found, use `python`.
2. If it lists problems, fix the files and run it again until every row passes.
3. Final answer: paste the checker's table exactly as printed (`| File | Status | Primary Sections Covered |`). Under it, list the open gaps grouped by who must answer them, and the conflicts you resolved.
