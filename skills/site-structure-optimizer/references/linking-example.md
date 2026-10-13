# Linking Example — worked before/after

One worked internal-linking example for a small blog, referenced from the Example section of [SKILL.md](../SKILL.md). All numbers are **Estimated** and illustrative.

## Setup

A small email-marketing blog. New post: **"Email marketing best practices"** (the pillar). Existing spokes: list-building, subject-lines, segmentation, automation, tools. One legacy page (old-promo) sits with no inbound links. The home page links to the pillar, list-building, and subject-lines from its body copy, so those three have inbound contextual links.

## Before — link graph

```mermaid
graph TD
  subgraph Site
    H[Home] --> B[Best practices pillar]
    H --> LB[List building]
    H --> SL[Subject lines]
  end
  subgraph Orphans
    SEG[Segmentation]
    AUT[Automation]
    TL[Tools]
    OP[Old promo]
  end
```

Diagnosis (Estimated):
- Pages analyzed: 8 · total internal links: 6 · avg links/page: 0.75 (below hub-spoke target 3–10) → −10
- Orphans: 4 (segmentation, automation, tools, old-promo) → −40 (each orphan is charged once, not again for having 0 contextual inbound links)
- Pillar has no spoke cross-links; segmentation/automation/tools unreachable
- **Structure score: 50/100** (100 − 40 − 10)

## Contextual Link Plan (Step 5 output)

| # | Source paragraph in pillar | Target | Suggested anchor | Priority |
|---|----------------------------|--------|------------------|----------|
| 1 | "Grow a permission-based list…" | /list-building | building an email list | High |
| 2 | "Write subject lines that earn opens…" | /subject-lines | writing subject lines | High |
| 3 | "Send the right message to the right group…" | /segmentation | audience segmentation | High |
| 4 | "Trigger sequences automatically…" | /automation | email automation | High |
| 5 | "Pick a platform that fits…" | /tools | email marketing tools | Medium |

Each spoke adds one link back to the pillar (spoke → hub). Old-promo has no traffic value → default disposition: 301 to the pillar (see SKILL.md Decision Gates).

## After — link graph

```mermaid
graph TD
  subgraph Pillars
    H[Home] --> B[Best practices pillar]
  end
  subgraph Cluster
    B --> LB[List building]
    B --> SL[Subject lines]
    B --> SEG[Segmentation]
    B --> AUT[Automation]
    B --> TL[Tools]
    LB --> B
    SL --> B
    SEG --> B
    AUT --> B
    TL --> B
  end
  OP[Old promo] -.301.-> B
```

After (Estimated):
- avg links/page: ~2.9 (still just below the hub-spoke target of 3) → −10 · orphans: 0 · every spoke ≤2 clicks from home
- Anchor mix: 100% descriptive on the 5 new links (no "click here")
- **Structure score: 90/100** (100 − 10). The remaining gap closes with one or two more spoke ↔ spoke cross-links, which lifts avg links/page above 3.

## Takeaway

Adding 5 descriptive contextual links plus 5 return links converted 4 orphans into a reachable cluster and lifted the pillar's inbound signal — no new content, structure only. Broken-target and migration risks (the old-promo 301) go into `open_loops` with a recommendation to run content-quality-auditor.
