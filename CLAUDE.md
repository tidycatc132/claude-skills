# Skill Library

## Purpose
This repo is where we build, test, and package Claude skills for WISE Digital Partners
(SEO, GEO/AEO, content, reporting). Skills run for 65+ client accounts, so they must be
client-agnostic and config-driven.

## Repo layout
skills/<skill-name>/SKILL.md      # frontmatter (name, description) + instructions
skills/<skill-name>/references/   # long reference docs loaded on demand
skills/<skill-name>/scripts/      # deterministic helpers (Python/Node)
skills/<skill-name>/evals/        # test prompts + expected behaviors
dist/                             # packaged .skill files (gitignored)

## Skill standards
- Description is the trigger: say what it does AND when to use it, with real user phrasings.
- SKILL.md under ~500 lines; push detail into references/ and link from SKILL.md.
- Never hardcode client names, URLs, or keys. Inputs come from config files or the user.
- State inputs, outputs, and file format explicitly. Specify "done" criteria.
- Prefer scripts for anything deterministic (parsing, scoring, CSV/XLSX). Prose for judgment.
- Every skill gets at least 3 eval prompts, including one edge case and one should-NOT-trigger.

## Workflow
1. Plan before building: confirm the skill's trigger, inputs, outputs.
2. Draft SKILL.md, then run the evals and show results.
3. Iterate on failures, then package to dist/.
4. Small commits, one skill per branch, descriptive messages.

## Don't
- Don't ask clarifying questions when a reasonable default exists. Pick one, state the assumption, build it.
- Don't touch skills outside the one being worked on.
