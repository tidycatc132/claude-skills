# CITE Items Fed by This Skill

CITE is a domain-level rating framework (Citation, Identity, Trust, Eminence). This skill **does not score CITE and does not trigger vetoes**. It supplies off-site inputs and maps them to the items below so a formal domain authority / CITE review can score them. Missing evidence is **Unknown**, never Partial or Fail.

## Item definitions

### C: Citation

**C01: Referring Domains Volume** (measure: unique referring domains count, not total links)
- **Pass**: >=500 unique referring domains.
- **Partial**: 50-499 referring domains.
- **Fail**: <50 referring domains.

**C02: Referring Domains Quality** (measure: authority of referring domains, DA = Moz Domain Authority / DR = Ahrefs Domain Rating)
- **Pass**: >=20% of referring domains have DA/DR 50+.
- **Partial**: 5-19% have strong authority.
- **Fail**: <5% have notable authority.

**C04: Link Velocity** (measure: month-over-month new referring domains)
- **Pass**: Steady growth; no month >3x average monthly acquisition.
- **Partial**: Mostly steady with 1-2 explainable spikes.
- **Fail**: Sudden spikes suggesting bulk acquisition.

**C05: AI Citation Frequency** (measure: query 20+ niche questions across 4+ AI engines)
- **Pass**: Cited on >=10 distinct niche queries across >=2 AI engines.
- **Partial**: Cited on 3-9 queries.
- **Fail**: Cited on 0-2 queries or not cited.

**C06: AI Citation Prominence** (measure: classify citations as primary / supplementary / footnote)
- **Pass**: Primary/sole source in >=50% of citations.
- **Partial**: One of several sources in most citations.
- **Fail**: Only supplementary mentions or footnotes.

**C07: Cross-Engine Citation** (measure: count distinct AI engines that cite the domain)
- **Pass**: Cited by >=3 different AI engines.
- **Partial**: Cited by 2 AI engines.
- **Fail**: Cited by 0-1 AI engines.

**C10: Link Source Diversity** (measure: cluster referring domains by industry and geography)
- **Pass**: >=3 industries and >=5 geographic regions.
- **Partial**: 2 industries or 3-4 regions.
- **Fail**: 1 industry or <3 regions.

### T: Trust

**T01: Link Profile Naturalness** (measure: distribution of the link growth curve over time)
- **Pass**: Natural distribution; no month >15% of total backlinks; growth correlates with publishing.
- **Partial**: Mostly natural with 1-2 explainable anomalies.
- **Fail**: Obvious unnatural patterns or bulk acquisition.

**T02: Dofollow Ratio Normality** (measure: dofollow % of total backlinks)
- **Pass**: 40-85% dofollow.
- **Partial**: 85-90% (slightly elevated).
- **Fail**: >90% (manipulation signal) or <20%.

**T03: Link-Traffic Coherence** | **VETO ITEM** (measure: organic visits per referring domain against a declared peer cohort)
- **Pass**: The link/traffic relationship falls within the declared peer distribution or has a documented, credible explanation.
- **Partial**: The relationship is anomalous but evidence does not establish manipulation.
- **Fail**: A material anomaly plus corroborating manipulation evidence is verified against the declared cohort → veto triggered.
- **Unknown**: No suitable peer distribution or reliable traffic/link evidence is available.

**T05: Backlink Profile Uniqueness** | **VETO ITEM** (measure: link-intersect overlap with other domains, after removing ubiquitous sources)
- **Pass**: Overlap is ordinary for the declared ecosystem after ubiquitous/common sources are removed.
- **Partial**: Unusual overlap exists but shared ownership, syndication, or niche structure remains a plausible explanation.
- **Fail**: A declared comparison universe and corroborating network evidence establish coordinated manipulation → veto triggered.
- **Unknown**: No defensible comparison universe or cross-domain backlink evidence is available.

## Veto handling for this skill

T03 and T05 are veto items in a formal CITE review: a verified fail caps the domain score, and two or more verified veto fails block the score. This skill never declares a veto. When its evidence suggests T03/T05 risk (including a toxic ratio above 15%), it writes a **Manipulation risk** line in `open_loops` and recommends a formal domain authority / CITE review.

## Mapping from this skill's outputs

| Skill output | CITE item | Evidence strength |
|---|---|---|
| Referring domains count | C01 | Direct input |
| Authority distribution (DA/DR breakdown) | C02 | Direct input |
| Link velocity | C04 | Direct input |
| Geographic distribution | C10 | Direct input |
| Dofollow/nofollow ratio | T02 | Direct input |
| Toxic-link / naturalness analysis | T01, T03 | Direct input (T03 needs a declared peer cohort) |
| Competitive link intersection | T05 | Direct input (needs a declared comparison universe) |
| AI-referral volume | C05 | Informs, does not evidence |
| Primary-vs-supplementary landing-page mix | C06 | Informs, does not evidence |
| Cross-engine spread of AI referral sources | C07 | Informs, does not evidence |
| WebSearch / connector AI-citation spot-check | C05, C06, C07 | Proxy (WebSearch) or Measured per engine (connector or pasted answers) |

Common mistakes: counting total links instead of unique referring domains (C01); conflating quantity with quality (C02: 200 high-authority editorial links beat 10,000 directory links); checking only backlinks and ignoring AI citations (C05).
