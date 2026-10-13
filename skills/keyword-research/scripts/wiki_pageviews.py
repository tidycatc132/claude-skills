#!/usr/bin/env python3
"""Monthly Wikipedia pageviews for an article, as a keyless attention proxy. Standard library only.

What this is for: ranking topics against each other and spotting seasonality (which month peaks,
whether interest is rising or falling). What it is NOT: a search-volume number. Wikipedia readers
are not Google searchers, and the article title is not a keyword. Never report these figures as
volume; label them Measured (Wikipedia pageviews) and use them only for relative demand and timing.

Usage:
  python3 wiki_pageviews.py "Search_engine_optimization" --months 12
  python3 wiki_pageviews.py "Water_heating" --months 24 --lang en --json

Output: one line per month (YYYY-MM  views), then total, average, peak month, and a trend
direction (rising / falling / flat) from the last three months against the first three.
Exit code 1 on a network failure, with a plain message on stderr.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

API = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/{lang}.wikipedia/all-access/user/{title}/monthly/{start}/{end}"
USER_AGENT = "keyword-research-skill/1.0 (topic demand proxy; contact via the skill repository)"
TREND_THRESHOLD = 0.15  # +/-15% between first and last three months counts as a direction


def month_range(months: int, today: dt.date | None = None) -> tuple[str, str]:
    today = today or dt.date.today()
    first_this_month = today.replace(day=1)
    end = first_this_month - dt.timedelta(days=1)  # last day of the previous full month
    start = first_this_month
    for _ in range(months):
        start = (start - dt.timedelta(days=1)).replace(day=1)
    return start.strftime("%Y%m%d"), end.strftime("%Y%m%d")


def fetch(title: str, months: int, lang: str, timeout: float = 15.0) -> list[tuple[str, int]]:
    start, end = month_range(months)
    url = API.format(lang=lang, title=urllib.parse.quote(title.replace(" ", "_"), safe=""), start=start, end=end)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    items = data.get("items", [])
    return [(f"{it['timestamp'][:4]}-{it['timestamp'][4:6]}", int(it.get("views", 0))) for it in items]


def trend_direction(series: list[tuple[str, int]]) -> str:
    if len(series) < 4:
        return "insufficient data"
    n = min(3, len(series) // 2)
    first = sum(v for _, v in series[:n]) / n
    last = sum(v for _, v in series[-n:]) / n
    if first == 0:
        return "rising" if last > 0 else "flat"
    change = (last - first) / first
    if change > TREND_THRESHOLD:
        return "rising"
    if change < -TREND_THRESHOLD:
        return "falling"
    return "flat"


def summarize(title: str, series: list[tuple[str, int]]) -> dict:
    total = sum(v for _, v in series)
    peak = max(series, key=lambda x: x[1]) if series else ("", 0)
    return {
        "article": title,
        "months": len(series),
        "series": [{"month": m, "views": v} for m, v in series],
        "total_views": total,
        "average_views": round(total / len(series)) if series else 0,
        "peak_month": peak[0],
        "peak_views": peak[1],
        "trend": trend_direction(series),
        "note": "Wikipedia pageviews: an attention proxy for relative demand and seasonality, not search volume.",
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("title", help="Wikipedia article title, e.g. Search_engine_optimization")
    ap.add_argument("--months", type=int, default=12, help="number of full months to fetch (default 12)")
    ap.add_argument("--lang", default="en", help="Wikipedia language edition (default en)")
    ap.add_argument("--json", action="store_true", help="print the summary as JSON")
    args = ap.parse_args(argv)
    if args.months < 1:
        print("error: --months must be at least 1", file=sys.stderr)
        return 2
    try:
        series = fetch(args.title, args.months, args.lang)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"error: no pageview data for article {args.title!r} on {args.lang}.wikipedia "
                  "(check the exact title, underscores for spaces)", file=sys.stderr)
        else:
            print(f"error: Wikimedia API returned HTTP {e.code}", file=sys.stderr)
        return 1
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        print(f"error: could not reach the Wikimedia API ({e}). Network may be blocked; "
              "report topic demand as N/A rather than guessing.", file=sys.stderr)
        return 1
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        print(f"error: unexpected response from the Wikimedia API: {e}", file=sys.stderr)
        return 1
    summary = summarize(args.title, series)
    if args.json:
        print(json.dumps(summary, indent=2))
        return 0
    for row in summary["series"]:
        print(f"{row['month']}  {row['views']:>10,}")
    print(f"total {summary['total_views']:,} over {summary['months']} months, average {summary['average_views']:,}/month")
    print(f"peak month {summary['peak_month']} ({summary['peak_views']:,}), trend {summary['trend']}")
    print(summary["note"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
