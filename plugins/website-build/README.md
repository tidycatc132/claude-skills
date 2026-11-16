# Website build plugins

The website build skills in `skills/` are grouped into plugins by department, matching the Build Playbook's tabs. The skills stay where they are: each plugin entry in `.claude-plugin/marketplace.json` uses the repo root as its `source` and lists its skill folders under `skills`. Nothing is copied, so a merged change to a skill reaches every plugin that holds it.

| Plugin | Who installs it | Skills |
|---|---|---|
| `build-account-management` | AM / PM | new-build-kickoff, welcome-email, kickoff-call-brief, kickoff-call-processing, week-1-client-email, week-1-handoff-check, week-2-client-email, week-2-handoff-check, week-5-client-email, week-5-handoff-check, week-6-go-live-email, case-study, project-close-out |
| `build-seo-content` | SEO / Editor | client-reference-kit, keyword-research, site-structure-optimizer, content-brief, seo-content-writer, content-quality-auditor, competitor-analysis, growth-blueprint, blueprint-deck, retainer-roadmap, serp-analysis, content-gap-analysis, technical-seo-checker, seo-drift-monitor, offsite-signal-analyzer |
| `build-design` | Design | homepage-design-brief, page-type-design-briefs, design-qa-dev-prep |
| `build-development` | Dev | dev-handoff-index |
| `build-shared` | everyone (installed automatically) | client-context-update, client-feedback, staging-site-qa, ga4-event-tracking |
| `website-build` | someone who works across departments | none of its own; installs the five plugins above |
| `agency-tools` | as needed | prospect-digital-audit, google-ads-audit, google-ads-analysis, clickup-progress-sync, subagent-performance-review (outside the build process) |

The four department plugins each depend on `build-shared`, which holds the skills more than one department runs: client-context-update (AM, and Dev for platform access), client-feedback (AM, and SEO for Week 5 edits), staging-site-qa (PM staging QA, Dev launch check) and ga4-event-tracking (SEO and Dev). Each skill is in exactly one plugin, so installing several plugins never loads the same skill twice.

## Install

```
/plugin marketplace add tidycatc132/claude-skills
/plugin install build-account-management@wise-skills
```

Swap in the department's plugin name. `website-build@wise-skills` installs all five build plugins at once. Skills are then called by plugin and skill name, for example `/build-account-management:welcome-email`, or picked up from the request as usual.

No plugin sets a `version`, so each update follows the latest commit on `main`. Run `/plugin marketplace update wise-skills` to pull merged changes.

## Adding or moving a skill

A new skill in `skills/` is not in any plugin until its path is added to one entry's `skills` list in `.claude-plugin/marketplace.json`. Then run:

```
python3 plugins/check_marketplace.py
claude plugin validate .
```

The check fails when a skill is in no plugin or in two, when a listed path has no `SKILL.md`, or when a root-sourced entry lists no skills (Claude Code would then load all of `skills/` for it). This is why `website-build` has its own folder here instead of using the repo root.
