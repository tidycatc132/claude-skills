# Mermaid Templates — site hierarchy & link graph

Copy-paste `mermaid` diagrams for architecture Step 7 (Draw the Site Map) and linking-mode site maps in [SKILL.md](../SKILL.md). Paste any block into a Mermaid renderer. Swap the bracketed labels for real pages. Convention: one subgraph per nav zone; orphans in their own subgraph with no inbound edges; islands are clusters that link among themselves but never back to a pillar.

## 1. Hierarchy tree (L0 → L1 → L2/L3)

```mermaid
graph TD
  H[Home /] --> S1[Section /features]
  H --> S2[Section /use-cases]
  H --> S3[Blog /blog]
  S1 --> F1[Reporting /features/reporting]
  S1 --> F2[Automation /features/automation]
  S3 --> P1[Post /blog/subject-lines]
  S3 --> P2[Post /blog/segmentation]
```

## 2. Nav zones (header / footer / sidebar)

```mermaid
graph TD
  subgraph Header
    H[Home] --> Feat[Features]
    H --> Price[Pricing]
    H --> CTA[Start free]
  end
  subgraph Footer
    H --> About[About]
    H --> Docs[Docs]
    H --> Legal[Privacy]
  end
```

## 3. Hub/spoke topic cluster

```mermaid
graph TD
  P[Pillar: Email marketing] --> A[List building]
  P --> B[Subject lines]
  P --> C[Segmentation]
  A --> P
  B --> P
  C --> P
  A --- B
  style P fill:#9C27B0,color:#fff
```

Solid = hub↔spoke links; `---` = cross-links between spokes. Purple = the hub/pillar.

## 4. Orphan & island highlighting

Orphans have no inbound edge; islands cross-link internally but never to a pillar.

```mermaid
graph TD
  subgraph Pillars
    H[Home] --> P[Pillar: Email]
  end
  subgraph Cluster
    P --> A[List building]
    P --> B[Subject lines]
  end
  subgraph Island
    X[Glossary A] --- Y[Glossary B]
  end
  subgraph Orphans
    O[Old promo page]
  end
  style X fill:#f44336,color:#fff
  style Y fill:#f44336,color:#fff
  style O fill:#FFC107
```

Color key: **red** (#f44336) = island (reconnect to a pillar or retire); **yellow** (#FFC107) = orphan (add inbound links, noindex, or 301).

## 5. Before / after (linking mode)

```mermaid
graph TD
  subgraph Before
    Hb[Home] --> Bb[Pillar]
    SEGb[Segmentation]
    AUTb[Automation]
  end
  subgraph After
    Ha[Home] --> Ba[Pillar]
    Ba --> SEGa[Segmentation]
    Ba --> AUTa[Automation]
    SEGa --> Ba
    AUTa --> Ba
  end
```

Use `-.301.->` for a planned redirect edge (dotted): `OP[Old promo] -.301.-> B[Pillar]`.

## 6. Color-coding conventions

Apply `style` fills to make the diagnostic view readable at a glance.

```mermaid
graph TD
  H[Home] --> F[Features]
  H --> N[New section]
  H --> R[Deprecated page]
  H --> O[Orphan page]
  style H fill:#4CAF50,color:#fff
  style F fill:#4CAF50,color:#fff
  style N fill:#2196F3,color:#fff
  style R fill:#f44336,color:#fff
  style O fill:#FFC107
```

Key: **green** (#4CAF50) = existing, no change; **blue** (#2196F3) = new page to create; **red** (#f44336) = remove/redirect or island; **yellow** (#FFC107) = orphan/restructure; **purple** (#9C27B0) = hub or CTA.

## 7. Architecture boards (Step 7: site map, main navigation, footer)

Architecture mode outputs these three diagrams as three separate fenced blocks, each a board of its own. All three use `graph TD` so every level sits on one horizontal row and the tree reads top to bottom.

### 7a. Site Map board

Shapes and sizes by level: home is a double circle, Level 1 pages are stadiums (pill shape) in a larger font, Level 2 pages are rectangles, Level 3 and deeper are rounded rectangles in a smaller font. Pages outside the SOW scope keep their level shape and carry the `(not in SOW scope)` suffix; orphans go in their own subgraph with no inbound edges; islands are red.

```mermaid
graph TD
  H(((Home /)))
  H --> S1([Services /services])
  H --> S2([About /about])
  H --> S3([Blog /blog #40;not in SOW scope#41;])
  H --> S4([Contact /contact #40;not in SOW scope#41;])
  S1 --> P1[Roof repair /services/roof-repair]
  S1 --> P2[Gutters /services/gutters]
  P1 --> D1(Emergency repair /services/roof-repair/emergency)
  S3 --> B1(Posts /blog/post-slug #40;not in SOW scope#41;)
  subgraph Orphans
    O[Old promo /promo-2024]
  end
  classDef home fill:#9C27B0,color:#fff,font-size:20px,font-weight:bold
  classDef level1 fill:#4CAF50,color:#fff,font-size:16px,font-weight:bold
  classDef level2 fill:#E8F5E9,color:#111,font-size:13px
  classDef level3 fill:#F5F5F5,color:#111,font-size:11px
  class H home
  class S1,S2,S3,S4 level1
  class P1,P2 level2
  class D1,B1 level3
  style O fill:#FFC107
```

Mermaid cannot set a node's width directly; the `font-size` in each `classDef` is what makes higher levels render larger. Write parentheses inside labels as `#40;` and `#41;` so they do not change the shape.

### 7b. Main Navigation board

Only the pages in the header navigation, in menu order, with dropdown children under their parent. The CTA is the rightmost node.

```mermaid
graph TD
  NAV[Main navigation]
  NAV --> N1([Services])
  NAV --> N2([About])
  NAV --> N3([Blog])
  NAV --> N4([Contact])
  NAV --> CTA{{Get a quote}}
  N1 --> N1a[Roof repair]
  N1 --> N1b[Gutters]
  classDef cta fill:#9C27B0,color:#fff,font-weight:bold
  class CTA cta
```

### 7c. Footer board

Only the pages recommended for the footer, one subgraph per footer column. Legal and utility pages that are not in the SOW scope belong here.

```mermaid
graph TD
  subgraph C1["Column 1: Services"]
    F1[Roof repair]
    F2[Gutters]
  end
  subgraph C2["Column 2: Company"]
    F3[About]
    F4[Contact]
  end
  subgraph C3["Column 3: Legal"]
    F5[Privacy policy #40;not in SOW scope#41;]
    F6[Terms and conditions #40;not in SOW scope#41;]
  end
```

## Rendering notes

- Architecture boards (section 7) always use `graph TD`; the older templates above may use `graph LR` for wide, shallow sites.
- Keep node labels short (`page name /url`) so the diagram stays readable.
- One subgraph per nav zone keeps orphans and islands visually separate — the point of the map.
