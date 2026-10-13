# Topic clusters

A cluster is one pillar page plus the cluster pages that support it, linked both ways. Propose a pillar only after the viability check passes.

## Pillar viability worksheet

Fill this before naming a pillar. One row per candidate.

| Field | Value | Notes |
|---|---|---|
| Head keyword | | the broad term the pillar targets |
| Volume | | Measured or N/A |
| KD | | Measured or N/A |
| Business relevance (1 to 5) | | Estimated unless the user gave it |
| Current rank | | from GSC or SE Ranking, N/A if unknown |
| Who owns the topic now | | the 2 to 3 domains that dominate the head term and its subtopics |
| Estimated subtopics | | count of distinct cluster keywords found in Discover and Variations |
| Existing assets | | client pages that already cover part of it |

Proceed when all of these hold:

- 8 to 12 viable subtopics exist (each with its own target keyword and a reason to be a separate page)
- combined cluster volume is above 5,000/mo, or the topic is strategically important for a stated reason (revenue line, launch, regulatory need)
- the topic is tied to the client's actual expertise, so the pillar can be more than a summary
- the client can add original data, examples, photos or process detail that competitors lack
- no single competitor owns an unbeatable cluster (a site with DR 40+ above the client's that already has pillar plus 10+ interlinked pages on it)

If fewer than 8 subtopics survive, fold the idea into an existing pillar or ship the strongest 2 to 3 pages as standalone and revisit.

## Subtopic map

| Subtopic | Target keyword | Volume | KD | Intent (I/N/C/T) | Format | Status |
|---|---|---|---|---|---|---|
| | | | | | | new / refresh / exists |

Status `exists` means a URL already covers it; link it, do not rebuild. `refresh` means a URL exists but misses the intent or the subtopic depth.

## Architecture patterns

Pick one per cluster and say which in the report.

- **Hub and spoke** (educational topics): the pillar is a broad guide; spokes are the deep dives. Linking is pillar to each spoke and back.
- **Layered** (technical topics): beginner, intermediate, advanced tiers. Each tier links up one level and down one level, the pillar sits at the top.
- **Use case** (products and services): the pillar is the offering; spokes are "for [segment]" or "for [industry]" or "in [city]" pages. Spokes link to each other only where segments overlap.
- **Process** (how-to topics): research, plan, execute, measure. Spokes link in sequence, plus every spoke links to the pillar.

## Linking rules

1. Every cluster page links to the pillar, in the body, early.
2. The pillar links to every core cluster page.
3. Each cluster page links to 2 or 3 sibling cluster pages where the topics touch.
4. Anchors are descriptive ("tankless water heater installation cost"), never "click here" or the bare URL.
5. Body links count; footer and sidebar links do not substitute for them.

## Build sequence

1. Pillar first, even if it starts shorter than its final form.
2. The 3 or 4 lowest-KD cluster pages (fast ranking signals and early links to the pillar).
3. The highest-volume cluster pages.
4. Niche and long-tail cluster pages.
5. Refresh the pillar with links to everything published, updated data and a summary of the cluster.

## Measurement checkpoints

| When | Check | Action if missing |
|---|---|---|
| 2 weeks | all pages indexed (GSC URL inspection or SEOGets indexing status) | fix internal links, submit sitemap, check noindex |
| 1 month | impressions appearing for cluster keywords, positions 20 to 50 | tighten titles and H1s to the target keyword |
| 3 months | several cluster pages in the top 20, pillar impressions rising | add internal links from older high-authority pages, pursue 2 to 3 links |
| 6 months | pillar in the top 10 for the head term or a close variant, cluster pages in the top 10 for their targets | refresh thin pages, merge any that still get nothing |

## Anti-patterns

- **Orphans**: a cluster page with no link from the pillar or siblings. Fix the links before writing more pages.
- **Footer-only linking**: links exist but only in navigation. Search engines discount them; move links into the body.
- **Over-linking**: every paragraph links to five pages. Keep 3 to 8 contextual internal links per page.
- **Thin subtopics**: a page that cannot exceed 300 useful words. Merge it into the pillar as a section with an anchor.
- **Pillar as a link list**: a pillar that only summarizes the spokes. It should answer the head keyword on its own.

## Cluster output template

```
### Cluster: <name>  (pattern: hub and spoke | layered | use case | process)
Pillar: "<head keyword>"  vol <n or N/A>  KD <n or N/A>  <intent>  <format>  <status>
Cluster pages:
  1. "<keyword>"  vol  KD  intent  format  status
  2. ...
Viability: <passes / fails which condition>
Build order: pillar, then pages <ids> (lowest KD), then <ids> (volume), then <ids> (niche)
```
