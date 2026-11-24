# Drift rules (what `scripts/diff_snapshots.py` flags, and how hard)

Load this when the user asks why something was rated the way it was, or wants to tune a threshold. Thresholds live as constants at the top of `scripts/diff_snapshots.py`; this file describes them and must change with them.

## Severities

| severity | meaning | typical action |
|---|---|---|
| `critical` | visibility is being lost right now | fix today |
| `high` | will cost rankings or rich results if left | fix this week |
| `medium` | worth a look; often intentional | confirm with whoever changed it |
| `low` | cosmetic or small movement | note it |
| `info` | a change that is neutral or positive | none |

## Per-page rules (category, field)

Field comparison is skipped for a page whose current status is not 200 or that could not be fetched: the error page's title, H1 and missing schema would otherwise drown the real finding.

| category | field | condition | severity |
|---|---|---|---|
| `status` | `status` | 200 became 4xx/5xx or unreachable | critical |
| `status` | `status` | 200 became 3xx | high |
| `status` | `status` | non-200 became 200 | info |
| `status` | `redirect_to` | URL now redirects (live fetch only) | medium |
| `page` | `fetch_error` | current fetch failed | high |
| `page` | `page` | URL in baseline but not in current snapshot | high |
| `page` | `page` | URL new in current snapshot | info |
| `robots` | `noindex` | false became true (meta robots or `X-Robots-Tag`) | critical |
| `robots` | `noindex` | true became false | info |
| `robots` | `nofollow` | false became true | medium |
| `canonical` | `canonical` | changed to a URL on another host | high |
| `canonical` | `canonical` | changed to another URL on the same host | high |
| `canonical` | `canonical` | removed | medium |
| `canonical` | `canonical` | added, not self-referencing | medium |
| `canonical` | `canonical` | added, self-referencing | low |
| `title` | `title` | removed or empty | high |
| `title` | `title` | changed | medium |
| `title` | `title` on subject `*` | titles changed on at least 3 pages AND at least 25% of compared pages in one diff (`MASS_TITLE_MIN`, `MASS_TITLE_SHARE`); the note names the shared trailing segment when 3+ share one | critical |
| `meta_description` | `meta_description` | removed | medium |
| `meta_description` | `meta_description` | changed | low |
| `meta_description` | `meta_description` | added | info |
| `h1` | `h1` | removed | medium |
| `h1` | `h1` | changed, or one H1 became several | low |
| `schema` | `schema_types` | any top-level `@type` (or `@graph` member type, or microdata `itemtype`) disappeared | high |
| `schema` | `schema_types` | type added | info |
| `content` | `word_count` | visible words fell 50%+ (baseline had 100+ words) | medium |
| `content` | `word_count` | visible words fell 25% to 49% | low |
| `content` | `lang` | `html lang` changed | low |
| `content` | `hreflang_count` | hreflang alternates went to zero | medium |

`schema_types` is compared as a set of type names, so reordering or editing property values does not fire. `INVALID_JSON_LD` appears as a type when a JSON-LD block does not parse; it disappearing is reported like any removed type, so read the note.

## Ranking rules (category `ranking`, subject = keyword)

Positions over 100 (`NOT_RANKING`), blank or 0 count as "not ranking". Keywords are matched case-insensitively.

| field | condition | severity |
|---|---|---|
| `position` | ranked in baseline, not ranking now | high |
| `position` | dropped 10+ places | high |
| `position` | dropped 3 to 9 places, or left the top 10 | medium |
| `position` | dropped 1 or 2 places | low |
| `position` | improved, or started ranking | info |
| `position` | keyword present in baseline but absent from the current rankings file | medium (export problem, not a ranking) |
| `position` | keyword new to tracking | info |
| `url` | a different URL ranks for the keyword | medium |

Rankings move for reasons that have nothing to do with the site (algorithm updates, competitors, SERP features). Pair a ranking drop with an on-page finding on the same URL before blaming the deploy; the report's "Likely causes" section does this ordering for you.

## Index rules (category `index`, subject `*`)

Only when both snapshots carry `indexed_count`.

| condition | severity |
|---|---|
| fell 25%+ | critical |
| fell 10% to 24% | high |
| fell under 10% | low |
| rose | info |

## Verdict

`REGRESSION DETECTED` when any critical or high row exists; `MINOR DRIFT` when only medium or low; `NO REGRESSION` when nothing or info only. `--fail-on <severity>` makes the script exit 3 when that severity or worse occurred, for use in CI.
