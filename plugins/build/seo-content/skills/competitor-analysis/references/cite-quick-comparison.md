# CITE Quick Comparison

A compact, peer-relative domain comparison used to fill the "CITE Score" row in the competitive landscape table. Based on the CITE Domain Rating v1.0 (40 items, 4 dimensions). In this skill it is **advisory**: a side-by-side signal of why one domain is more trusted and cited than another, not a formal audit.

## Dimensions and default weights

| Dim | Name | Default Weight | Core question |
|-----|------|:-:|---------------|
| C | Citation | 35% | How strongly is the domain referenced, through links AND AI citations? |
| I | Identity | 20% | How clearly is the domain recognized as a distinct entity? |
| T | Trust | 25% | Are there red flags suggesting manipulation? |
| E | Eminence | 20% | How visible and influential is the domain? |

Ownership rule: C = positive referencing signals; I = entity existence and brand coherence; T = suspicion and manipulation detection; E = visibility and influence outcomes. Do not count one observation twice (for example, links feed C; do not also credit them under E).

## Peer-relative rule

Declare the comparison cohort (the competitor set), market, and domain type before scoring. The thresholds below are diagnostic starting points, not universal pass/fail laws; where the cohort clearly differs (for example, a local niche where nobody has 500 referring domains), judge against the competitor set and say so. If evidence is missing, the item is **Unknown**. Unknown never becomes Partial or Fail.

## The 40 items

### C: Citation
| ID | Item | Diagnostic anchor |
|----|------|-------------------|
| C01 | Referring Domains Volume | >=500 unique referring domains |
| C02 | Referring Domains Quality | >=20% of referring domains have DA/DR 50+ |
| C03 | Link Equity Distribution | Top sources concentrate outbound links (<1,000 outbound domains) |
| C04 | Link Velocity | Steady natural growth; no month >3x average |
| C05 | AI Citation Frequency | Cited by >=2 AI engines on >=10 niche queries |
| C06 | AI Citation Prominence | Primary/sole source in >=50% of AI citations |
| C07 | Cross-Engine Citation | Cited by >=3 different AI engines |
| C08 | Citation Sentiment | >=80% of citations in positive/neutral context |
| C09 | Editorial Link Ratio | >=60% of backlinks from editorial decisions |
| C10 | Link Source Diversity | Referring domains span >=3 industries, >=5 regions |

### I: Identity
| ID | Item | Diagnostic anchor |
|----|------|-------------------|
| I01 | Knowledge Graph Presence | Entity in >=2 knowledge graphs (Google KG, Wikidata, DBpedia) |
| I02 | Brand Search Volume | Brand name >=1,000 monthly exact-match searches |
| I03 | Brand SERP Ownership | Brand search yields >=7 first-page results you control |
| I04 | Schema.org Coverage | >=50% of indexable pages with correct Schema.org markup |
| I05 | Author Entity Recognition | >=80% of content has authors with verifiable public identities |
| I06 | Domain Tenure | History coherent relative to entity stage; age alone cannot fail the domain |
| I07 | Cross-Platform Consistency | Brand name/description/contact identical across platforms |
| I08 | Niche Consistency | Same niche for >=3 consecutive years without major pivot |
| I09 | Unlinked Brand Mentions | >=50 third-party mentions without links |
| I10 | Query-Brand Association | Brand appears in industry query autocomplete |

### T: Trust
| ID | Item | Diagnostic anchor |
|----|------|-------------------|
| T01 | Link Profile Naturalness | No month >15% of total backlinks; growth correlates with publishing |
| T02 | Dofollow Ratio Normality | Dofollow 40-85% of total backlinks |
| T03 | Link-Traffic Coherence | Link/traffic relationship coherent within the peer set (**Veto**) |
| T04 | IP/Network Diversity | >=100 unique C-class IP ranges; no single C-class >5% |
| T05 | Backlink Profile Uniqueness | No verified manipulation network after common-source adjustment (**Veto**) |
| T06 | WHOIS & Registration Transparency | Ownership history coherent; privacy-protected WHOIS is neutral |
| T07 | Technical Security | Site-wide HTTPS + HSTS; no malware/phishing flags |
| T08 | Content Freshness Signal | New/updated content within last 90 days |
| T09 | Penalty & Deindex History | No verified active manual action or deindexing (**Veto**) |
| T10 | Review & Reputation Signals | >=3.5/5 average on >=2 third-party review platforms |

### E: Eminence
| ID | Item | Diagnostic anchor |
|----|------|-------------------|
| E01 | Organic Search Visibility | Ranks for >=1,000 keywords in top 100 |
| E02 | Organic Traffic Estimate | >=10,000 estimated monthly organic visits |
| E03 | SERP Feature Ownership | Appears in >=3 SERP feature types |
| E04 | Technical Crawlability | AI-crawler-friendly robots.txt; clean rendering; <3s load |
| E05 | Multi-Platform Footprint | Official presence on >=3 major platforms with recent activity |
| E06 | Authoritative Media Coverage | Featured in >=3 authoritative publications |
| E07 | Topical Authority Depth | Ranks for long-tail (4+ word) keywords deep in niche |
| E08 | Topical Authority Breadth | Covers >=70% of sub-topics in primary niche |
| E09 | Geographic Reach | Organic traffic from >=10 countries/regions |
| E10 | Industry Share of Voice | >=5% visibility share across top 50 industry keywords |

## Scoring (the rules `scripts/cite_score.py` implements; it shows the arithmetic)

- Per item: Pass = 10, Partial = 5, Fail = 0, Unknown = not scored.
- Dimension score = mean of the scored items × 10 (0-100). State the coverage (for example, "C: 6/10 items observed").
- Default diagnostic = C × 0.35 + I × 0.20 + T × 0.25 + E × 0.20.
- Domain-type weights (use when the domain type is clear):

| Dim | Default | Content Publisher | Product & Service | E-commerce | Community & UGC | Tool & Utility | Authority & Institutional |
|-----|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| C | 35% | 40% | 25% | 20% | 35% | 25% | 45% |
| I | 20% | 15% | 30% | 20% | 10% | 30% | 20% |
| T | 25% | 20% | 25% | 35% | 25% | 25% | 20% |
| E | 20% | 25% | 20% | 25% | 30% | 20% | 15% |

Domain type: publishes articles/news/guides/research → Content Publisher; sells/markets a product or service → Product & Service; online store or marketplace → E-commerce; hosts user-generated content/forums/Q&A → Community & UGC; provides web tools/utilities/apps → Tool & Utility; academic/government/non-profit/standards → Authority & Institutional.

Rating scale: 90-100 Excellent; 75-89 Good; 60-74 Medium; 40-59 Low; 0-39 Poor.

**Vetoes**: check T03, T05, T09 first. One *verified* veto fail caps that domain's score at 59 and adds a "Manipulation Alert" to `open_loops`. Two or more verified veto fails: report no score for that domain. Missing evidence for a veto item stays Unknown and does not trigger the veto.

**Labeling**: the CITE score is Calculated from the item results; mark it **partial-coverage** when any dimension has Unknown items, and N/A when fewer than half the items in any dimension are observed. A comparable score requires full evidence coverage; with partial coverage, compare dimensions rather than headline numbers.

## Where the evidence comes from

| Signal | Source |
|--------|--------|
| C01-C04, C09-C10, T01-T05 | SEO data connector backlink reports (referring domains, authority, new/lost history, link attributes, referring IPs) or user exports |
| C05-C08 | Manual AI-answer spot checks across engines (ChatGPT, Perplexity, Google AI Overviews, Gemini, Claude) or an AI-visibility tool |
| I01-I03, I10 | Knowledge-graph lookups (Wikidata, Google KG), brand search volume, brand SERP check, autocomplete |
| I04-I09 | Site fetch (schema, author pages), WHOIS/Wayback, cross-platform profile check, brand mention search |
| T06-T10 | WHOIS, HTTPS/security headers, last-modified dates, Search Console manual actions (own site only), review platforms (Trustpilot, G2, BBB) |
| E01-E10 | SEO data connector visibility/traffic/SERP features/geography; robots.txt; media mention search |

## Common mistakes

- Counting total backlinks instead of unique referring domains (C01).
- Equating many low-authority links with quality (C02).
- Ignoring AI citations and checking only backlinks (C05).
- Skipping the veto items (T03, T05, T09) before scoring the rest.
- Treating a high follower count or a single DA/DR number as a proxy for overall authority.
