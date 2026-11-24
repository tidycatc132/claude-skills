#!/usr/bin/env python3
"""GA4 event tracking for a launched WISE website build, set up through Google Tag Manager.

  plan      read the dev handoff index (and the newest launch check for the live address), write
            tracking/<slug>/<slug>-tracking-plan.md and tracking/<slug>/<slug>-gtm-container.json
  check     test the plan and the container file against each other and the GTM import format
  site      after Dev imports and publishes the container: test every Build page (live, or saved
            HTML) for the container snippet, a doubled GA4 tag, the conversion links and the form;
            writes tracking/<slug>/<slug>-tracking-check-<date>.md
  contract  print what this skill reads from the dev handoff index, or validate a contract fixture

Standard library only. Paths are relative to the client's working folder (the current folder).
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

MEASUREMENT_RE = re.compile(r"^G-[A-Z0-9]{4,12}$")
GTM_RE = re.compile(r"^GTM-[A-Z0-9]{4,10}$")
EVENT_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,39}$")
RESERVED_PREFIXES = ("google_", "ga_", "firebase_", "_")
INIT_ALL_PAGES = "2147479573"  # GTM built-in trigger "Initialization - All Pages"
MAP_LINK_REGEX = r"(google\.[a-z.]+/maps|maps\.google\.|maps\.app\.goo\.gl|goo\.gl/maps|maps\.apple\.com)"

BUILT_INS = [
    ("PAGE_URL", "Page URL"),
    ("PAGE_HOSTNAME", "Page Hostname"),
    ("PAGE_PATH", "Page Path"),
    ("CLICK_URL", "Click URL"),
    ("CLICK_TEXT", "Click Text"),
    ("FORM_ID", "Form ID"),
]
MEASUREMENT_VAR = "GA4 Measurement ID"


def die(msg: str, code: int = 2) -> None:
    print(f"STOP: {msg}")
    sys.exit(code)


def read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def write(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


# --------------------------------------------------------------------------- #
# Reading the dev handoff index
# --------------------------------------------------------------------------- #
def parse_index(text: str) -> dict:
    client = ""
    m = re.search(r"(?m)^Client:\s*(.+?)\s*$", text)
    if m:
        client = m.group(1)
    pages: list[dict] = []
    section = ""
    cur: dict | None = None
    in_links = False
    in_global = False
    analytics = False
    points: list[dict] = []
    in_points = False
    for line in text.splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
            in_global = section == "Global"
            in_links = False
            in_points = False
            cur = None
            continue
        if in_global:
            if line.startswith("### "):
                analytics = line[4:].strip() == "Analytics and tracking"
                in_points = False
                continue
            if analytics and line.startswith("Conversion points"):
                in_points = True
                continue
            if analytics and in_points:
                pm = re.match(r"^- (.+?): (tel:\S+|mailto:\S+|contact form)\s*(?:\((anchor|section): (.*)\))?\s*$", line)
                if pm:
                    kind = "form" if pm.group(2) == "contact form" else pm.group(2).split(":", 1)[0]
                    points.append({"Page": pm.group(1), "kind": kind, "link": pm.group(2),
                                   "label": (pm.group(4) or "").strip()})
            continue
        if line.startswith("### "):
            cur = {"Page": line[4:].strip(), "URL": "", "Priority": "", "Section": section, "Internal links": []}
            pages.append(cur)
            in_links = False
            continue
        if cur is None:
            continue
        fm = re.match(r"^- (Page|URL|Priority|Status|Internal links):\s*(.*)$", line)
        if fm:
            key, val = fm.group(1), fm.group(2).strip()
            in_links = key == "Internal links"
            if key in ("Page", "URL", "Priority"):
                cur[key] = val
            continue
        if in_links:
            lm = re.match(r"^\s+- (\S+) \(anchor: (.*?)\)", line)
            if lm:
                cur["Internal links"].append({"url": lm.group(1), "anchor": lm.group(2)})
            elif not line.startswith("  "):
                in_links = False
    has_analytics = "### Analytics and tracking" in text
    contact = next((p for p in pages if p["Section"] == "Contact Page" and p["URL"]), None)
    return {"Client": client, "pages": pages, "points": points, "has_analytics": has_analytics,
            "contact_url": contact["URL"] if contact else ""}


def build_pages(idx: dict) -> list[dict]:
    return [p for p in idx["pages"] if p["Priority"] == "Build" and p["URL"]]


def newest_launch_check(slug: str) -> str:
    files = sorted(glob.glob(f"qa/{slug}/{slug}-launch-check-*.md"))
    return files[-1] if files else ""


def live_from_launch_check(path: str) -> str:
    m = re.search(r"(?m)^Live:\s*(\S+)", read(path))
    return m.group(1).rstrip("/") if m else ""


def host_of(url: str) -> str:
    return urllib.parse.urlparse(url).hostname or ""


# --------------------------------------------------------------------------- #
# The event set (fixed, generic: the same for every site)
# --------------------------------------------------------------------------- #
def event_set(lead_mode: str, thank_you: str, contact_url: str) -> list[dict]:
    ev = []
    if lead_mode == "thank-you":
        ev.append({"name": "generate_lead", "key": True, "trigger": "thankyou",
                   "fires": f"the thank-you page {thank_you} loads after a form is sent",
                   "params": [("lead_type", "form")]})
    else:
        ev.append({"name": "generate_lead", "key": True, "trigger": "form",
                   "fires": "a form on the site is submitted and passes the browser's validation",
                   "params": [("lead_type", "form"), ("form_id", "{{Form ID}}")]})
    ev.append({"name": "click_to_call", "key": True, "trigger": "tel",
               "fires": "a visitor clicks a phone link (tel:)",
               "params": [("lead_type", "phone"), ("link_url", "{{Click URL}}"), ("link_text", "{{Click Text}}")]})
    ev.append({"name": "click_to_email", "key": False, "trigger": "mailto",
               "fires": "a visitor clicks an email link (mailto:)",
               "params": [("lead_type", "email"), ("link_url", "{{Click URL}}"), ("link_text", "{{Click Text}}")]})
    ev.append({"name": "get_directions", "key": False, "trigger": "maps",
               "fires": "a visitor clicks a Google Maps or Apple Maps link",
               "params": [("link_url", "{{Click URL}}"), ("link_text", "{{Click Text}}")]})
    if contact_url:
        ev.append({"name": "cta_click", "key": False, "trigger": "cta",
                   "fires": f"a visitor clicks a link to the contact page {contact_url} from another page",
                   "params": [("link_url", "{{Click URL}}"), ("link_text", "{{Click Text}}")]})
    return ev


# --------------------------------------------------------------------------- #
# GTM container export (exportFormatVersion 2)
# --------------------------------------------------------------------------- #
def _p(key: str, value: str, typ: str = "TEMPLATE") -> dict:
    return {"type": typ, "key": key, "value": value}


def _cond(kind: str, arg0: str, arg1: str, ignore_case: bool = False, negate: bool = False) -> dict:
    params = [_p("arg0", arg0), _p("arg1", arg1)]
    if ignore_case:
        params.append(_p("ignore_case", "true", "BOOLEAN"))
    if negate:
        params.append(_p("negate", "true", "BOOLEAN"))
    return {"type": kind, "parameter": params}


def host_regex(host: str) -> str:
    bare = host[4:] if host.startswith("www.") else host
    return r"^(www\.)?" + re.escape(bare) + "$"


def build_container(client: str, measurement: str, gtm_id: str, google_tag: bool, events: list[dict],
                    host: str, thank_you: str, contact_url: str, today: str, form_paths: list[str] | None = None) -> dict:
    acc, con = "0", "0"
    guard = [_cond("MATCH_REGEX", "{{Page Hostname}}", host_regex(host), ignore_case=True)] if host else []
    variables = [{"accountId": acc, "containerId": con, "variableId": "1", "name": MEASUREMENT_VAR,
                  "type": "c", "parameter": [_p("value", measurement)]}]
    builtins = [{"accountId": acc, "containerId": con, "type": t, "name": n} for t, n in BUILT_INS]
    triggers, tags = [], []
    tid = 10

    def link_trigger(name: str, filters: list[dict]) -> str:
        nonlocal tid
        tid += 1
        triggers.append({"accountId": acc, "containerId": con, "triggerId": str(tid), "name": name,
                         "type": "LINK_CLICK",
                         "waitForTags": {"type": "BOOLEAN", "value": "false"},
                         "checkValidation": {"type": "BOOLEAN", "value": "false"},
                         "waitForTagsTimeout": {"type": "TEMPLATE", "value": "2000"},
                         "uniqueTriggerId": {"type": "TEMPLATE"},
                         "filter": filters + guard})
        return str(tid)

    trig_for: dict[str, str] = {}
    for e in events:
        t = e["trigger"]
        if t == "form":
            tid += 1
            fpaths = sorted({fp.rstrip("/") for fp in (form_paths or [])})
            fcond = ([_cond("MATCH_REGEX", "{{Page Path}}",
                            "^(" + "|".join(re.escape(fp) for fp in fpaths) + ")/?$", ignore_case=True)]
                     if fpaths else [])
            triggers.append({"accountId": acc, "containerId": con, "triggerId": str(tid),
                             "name": "WISE - Form submit (lead form pages)" if fpaths else "WISE - Form submit (all forms)",
                             "type": "FORM_SUBMISSION",
                             "waitForTags": {"type": "BOOLEAN", "value": "true"},
                             "checkValidation": {"type": "BOOLEAN", "value": "true"},
                             "waitForTagsTimeout": {"type": "TEMPLATE", "value": "2000"},
                             "uniqueTriggerId": {"type": "TEMPLATE"},
                             "autoEventFilter": [_cond("MATCH_REGEX", "{{Page URL}}", ".*")],
                             **({"filter": fcond + guard} if (fcond or guard) else {})})
            trig_for[e["name"]] = str(tid)
        elif t == "thankyou":
            tid += 1
            path = thank_you.rstrip("/")
            triggers.append({"accountId": acc, "containerId": con, "triggerId": str(tid),
                             "name": f"WISE - Thank-you page {thank_you}", "type": "PAGEVIEW",
                             "filter": [_cond("MATCH_REGEX", "{{Page Path}}", "^" + re.escape(path) + "/?$",
                                              ignore_case=True)] + guard})
            trig_for[e["name"]] = str(tid)
        elif t == "tel":
            trig_for[e["name"]] = link_trigger("WISE - Click phone link", [_cond("STARTS_WITH", "{{Click URL}}", "tel:", True)])
        elif t == "mailto":
            trig_for[e["name"]] = link_trigger("WISE - Click email link", [_cond("STARTS_WITH", "{{Click URL}}", "mailto:", True)])
        elif t == "maps":
            trig_for[e["name"]] = link_trigger("WISE - Click map link", [_cond("MATCH_REGEX", "{{Click URL}}", MAP_LINK_REGEX, True)])
        elif t == "cta":
            path = re.escape(contact_url.rstrip("/"))
            dom = re.escape(host[4:] if host.startswith("www.") else host) if host else r"[^/]+"
            url_re = r"^https?://(www\.)?" + dom + path + r"/?([?#].*)?$" if host else r"^https?://[^/]+" + path + r"/?([?#].*)?$"
            trig_for[e["name"]] = link_trigger(
                "WISE - Click link to contact page",
                [_cond("MATCH_REGEX", "{{Click URL}}", url_re, True),
                 _cond("MATCH_REGEX", "{{Page Path}}", "^" + path + "/?$", True, negate=True)])
    tagid = 100
    if google_tag:
        tagid += 1
        gt_trigger = INIT_ALL_PAGES
        if guard:
            tid += 1
            triggers.append({"accountId": acc, "containerId": con, "triggerId": str(tid),
                             "name": "WISE - Initialization (live site only)", "type": "INIT", "filter": list(guard)})
            gt_trigger = str(tid)
        tags.append({"accountId": acc, "containerId": con, "tagId": str(tagid), "name": "WISE - Google tag (GA4)",
                     "type": "googtag", "parameter": [_p("tagId", "{{" + MEASUREMENT_VAR + "}}")],
                     "firingTriggerId": [gt_trigger], "tagFiringOption": "ONCE_PER_EVENT"})
    for e in events:
        tagid += 1
        table = [{"type": "MAP", "map": [_p("parameter", k), _p("parameterValue", v)]} for k, v in e["params"]]
        tags.append({"accountId": acc, "containerId": con, "tagId": str(tagid), "name": f"WISE - GA4 event - {e['name']}",
                     "type": "gaawe",
                     "parameter": [_p("sendEcommerceData", "false", "BOOLEAN"),
                                   _p("eventName", e["name"]),
                                   _p("measurementIdOverride", "{{" + MEASUREMENT_VAR + "}}"),
                                   {"type": "LIST", "key": "eventSettingsTable", "list": table}],
                     "firingTriggerId": [trig_for[e["name"]]], "tagFiringOption": "ONCE_PER_EVENT"})
    return {
        "exportFormatVersion": 2,
        "exportTime": f"{today} 00:00:00",
        "containerVersion": {
            "path": "accounts/0/containers/0/versions/0", "accountId": acc, "containerId": con,
            "containerVersionId": "0", "name": f"WISE event tracking - {client}",
            "container": {"path": "accounts/0/containers/0", "accountId": acc, "containerId": con,
                          "name": client, "publicId": gtm_id or "GTM-XXXXXXX", "usageContext": ["WEB"]},
            "tag": tags, "trigger": triggers, "variable": variables, "builtInVariable": builtins,
        },
    }


# --------------------------------------------------------------------------- #
# Plan
# --------------------------------------------------------------------------- #
def where_on_site(e: dict, idx: dict, thank_you: str) -> str:
    pts = idx["points"]
    if e["trigger"] in ("tel", "mailto", "form"):
        kind = {"tel": "tel", "mailto": "mailto", "form": "form"}[e["trigger"]]
        hits = [p for p in pts if p["kind"] == kind]
        if not hits:
            what = {"tel": "phone links", "mailto": "email links", "form": "contact forms"}[kind]
            return f"no {what} listed in the index; the tag stays ready for any added later"
        pages = []
        for p in hits:
            if p["Page"] not in pages:
                pages.append(p["Page"])
        if kind == "form":
            return "; ".join(f"{p['Page']} ({p['label'] or 'contact form'})" for p in hits)
        links = sorted({p["link"] for p in hits})
        return ", ".join(pages) + " (" + ", ".join(links) + ")"
    if e["trigger"] == "thankyou":
        forms = [p for p in pts if p["kind"] == "form"]
        src = "; ".join(f"{p['Page']} ({p['label'] or 'contact form'})" for p in forms) or "no contact forms listed in the index"
        return f"{thank_you}, after: {src}"
    if e["trigger"] == "maps":
        return "the index does not list map links; fires on any Google Maps or Apple Maps link"
    if e["trigger"] == "cta":
        hits = []
        for p in build_pages(idx):
            if p["URL"] == idx["contact_url"]:
                continue
            for l in p["Internal links"]:
                if l["url"].rstrip("/") == idx["contact_url"].rstrip("/"):
                    hits.append(f"{p['Page']} ({l['anchor']})")
        return "; ".join(hits) if hits else "no links to the contact page listed in the index"
    return ""


def render_plan(a: dict) -> str:
    idx, events = a["idx"], a["events"]
    key_events = [e["name"] for e in events if e["key"]]
    dims = []
    for e in events:
        for k, _ in e["params"]:
            if k in ("lead_type", "form_id") and k not in dims:
                dims.append(k)
    L = [
        f"Client: {idx['Client']}",
        f"Index: {a['index_path']}",
        f"Live: {a['live'] or 'unknown'}" + (f" (from {a['live_src']})" if a["live"] else ""),
        f"Measurement ID: {a['measurement']}",
        f"GTM container: {a['gtm_id'] or 'not given'}",
        f"Google tag: {'in container' if a['google_tag'] else 'already on the site (not in container)'}",
        f"Lead event: {'thank-you page ' + a['thank_you'] if a['lead_mode'] == 'thank-you' else 'form submission'}",
        f"Container file: {a['container_path']}",
        f"Written: {a['today']}",
        "",
        f"# Event Tracking Plan: {idx['Client']}",
        "",
    ]
    if a["warnings"]:
        L += [f"WARNING: {w}" for w in a["warnings"]] + [""]
    L += [
        "## Events",
        "",
        "| Event | Fires when | Parameters | Key event | On this site |",
        "|---|---|---|---|---|",
    ]
    for e in events:
        params = ", ".join(f"`{k}`" for k, _ in e["params"])
        L.append(f"| `{e['name']}` | {e['fires']} | {params} | {'yes' if e['key'] else 'no'} | {where_on_site(e, idx, a['thank_you'])} |")
    L += [
        "",
        "GA4 enhanced measurement already records page views, scrolls, outbound clicks, site search, video plays, "
        "file downloads and form interactions; this container adds only the events above, so nothing is counted twice.",
        "",
        "## GTM Container",
        "",
        f"`{a['container_path']}` holds, all named with the prefix `WISE - `:",
        "",
        f"- Variable `{MEASUREMENT_VAR}` (constant): `{a['measurement']}`.",
    ]
    if a["google_tag"]:
        L.append("- Tag `WISE - Google tag (GA4)` on Initialization - All Pages: loads GA4 and sends page views.")
    for e in events:
        L.append(f"- Tag `WISE - GA4 event - {e['name']}`: fires when {e['fires']}.")
    if a["host"]:
        L.append(f"- Every trigger, including the one that loads the Google tag, fires only on the live hostname `{a['host']}` (with or without www), so staging visits are never counted.")
    if a["lead_mode"] == "form" and a["form_paths"]:
        L.append("- `generate_lead` listens only on the pages the index lists with a contact form: " + ", ".join(f"`{x}`" for x in a["form_paths"]) + ". Search, newsletter and comment forms elsewhere are not counted as leads.")
    L.append("- Built-in variables switched on: " + ", ".join(n for _, n in BUILT_INS) + ".")
    L += [
        "",
        "## Install (Dev)",
        "",
        "1. In Google Tag Manager open the client's web container"
        + (f" `{a['gtm_id']}`" if a["gtm_id"] else "") + ". Admin > Import Container.",
        f"2. Choose `{a['container_path']}`. Workspace: Existing, the default workspace. Import option: Merge, then Rename conflicting tags, triggers and variables. Confirm.",
    ]
    if a["google_tag"]:
        L.append("3. If GA4 is already loaded another way (a Google tag or GA4 configuration tag already inside this GTM container, a hard-coded gtag.js snippet, or a CMS plugin sending the same Measurement ID), remove or pause it now, or the site counts every page view twice. The site check can only see the page code, not other tags inside GTM.")
    else:
        L.append("3. The site already loads GA4 itself, so the container has no Google tag. Leave that GA4 code in place; the event tags send to the same Measurement ID.")
    L += [
        "4. Make sure the container snippet is on every page: the script in the head and the noscript iframe right after the opening body tag.",
        "5. Click Preview, open the live site, and do each test in the Test section below. Every event tag must show under Tags Fired.",
        f"6. Submit, version name `WISE event tracking {a['today']}`, and Publish.",
        f"7. Run the site check: `python3 <skill-folder>/scripts/tracking.py site --plan {a['plan_path']}`. It must end `RESULT: TRACKING OK`.",
        "",
        "## GA4 Settings (SEO)",
        "",
        "1. Admin > Data display > Key events > New key event: add " + ", ".join(f"`{k}`" for k in key_events)
        + ". Adding them by name now means the first conversion already counts.",
        "2. Admin > Data display > Custom definitions > Create custom dimension, scope Event, for each parameter: "
        + ", ".join(f"`{d}`" for d in dims) + ". Use the parameter name as the dimension name.",
        "3. Admin > Data collection and modification > Data streams > the web stream > Enhanced measurement: leave it on with every option on.",
        "4. Admin > Data collection and modification > Data retention: set event data retention to 14 months.",
        "5. Admin > Product links: link Google Search Console to the property if it is not linked yet.",
        "",
        "## Test",
        "",
        "Dev runs these in GTM Preview; SEO then watches each event arrive in GA4 Admin > DebugView.",
        "",
        "| Event | How to test | Pass when |",
        "|---|---|---|",
    ]
    for e in events:
        how = {
            "form": "fill in and send a contact form with test details (say TEST in the message). If the tag does not fire, the form is probably sent by AJAX: re-run plan with --thank-you <path>",
            "thankyou": f"send a contact form; the browser lands on {a['thank_you']}",
            "tel": "click a phone number link (on a phone, or cancel the call prompt on a computer)",
            "mailto": "click an email address link",
            "maps": "click a directions or map link, if the site has one",
            "cta": "on any page except the contact page, click a button or link that goes to the contact page",
        }[e["trigger"]]
        L.append(f"| `{e['name']}` | {how} | the tag shows under Tags Fired, and `{e['name']}` appears in DebugView with its parameters |")
    L += [
        "",
        "## Sign-off",
        "",
        "- [ ] Container imported, previewed and published (Dev)",
        "- [ ] Site check ends `RESULT: TRACKING OK` (Dev)",
        "- [ ] Every event seen in DebugView (SEO)",
        "- [ ] Key events and custom dimensions added in GA4 (SEO)",
        "",
        "## Not Covered",
        "",
        "- Live chat, Juvo, call-tracking numbers, booking widgets inside an iframe, ecommerce and Google Ads or Meta conversions are not part of this generic set. Add them on their own only when the client has them.",
        "",
    ]
    return "\n".join(L)


def cmd_plan(args: argparse.Namespace) -> int:
    slug = args.slug
    index_path = f"handoff/{slug}/{slug}-dev-handoff-index.md"
    if not os.path.isfile(index_path):
        die(f"{index_path} is missing. Run dev-handoff-index first.")
    if not args.measurement_id:
        die("no GA4 Measurement ID. Ask the SEO for it (GA4 Admin > Data collection and modification > Data streams > the web stream, starts G-) and pass --measurement-id.")
    mid = args.measurement_id.strip().upper()
    if not MEASUREMENT_RE.match(mid):
        die(f"'{args.measurement_id}' is not a GA4 Measurement ID (it looks like G-XXXXXXXXXX). A UA- or GTM- ID will not work here.")
    gtm_id = (args.gtm_id or "").strip().upper()
    if gtm_id and not GTM_RE.match(gtm_id):
        die(f"'{args.gtm_id}' is not a GTM container ID (it looks like GTM-XXXXXXX).")
    thank_you = ""
    if args.thank_you:
        thank_you = args.thank_you.strip()
        if thank_you.startswith("http"):
            thank_you = urllib.parse.urlparse(thank_you).path or "/"
        if not thank_you.startswith("/"):
            thank_you = "/" + thank_you
        if thank_you.strip("/") == "":
            die("--thank-you cannot be the homepage; every homepage visit would count as a lead. Give the thank-you page's own path.")
    idx = parse_index(read(index_path))
    if not build_pages(idx):
        die(f"{index_path} lists no Build pages.")
    warnings = []
    live, live_src = "", ""
    if args.site:
        live, live_src = args.site.rstrip("/"), "--site"
    else:
        lc = newest_launch_check(slug)
        if lc:
            live, live_src = live_from_launch_check(lc), lc
    if live and not live.startswith("http"):
        live = "https://" + live
    host = host_of(live) if live else ""
    if not host:
        live = ""
        warnings.append("live address unknown (no launch check and no --site), so the triggers have no hostname guard "
                        "and staging visits will be counted. Re-run with --site https://<live domain>.")
    if not idx["has_analytics"]:
        warnings.append("the dev handoff index has no `### Analytics and tracking` section, so no conversion points "
                        "are listed. Re-run dev-handoff-index; the generic events are still set up.")
    if not idx["contact_url"]:
        warnings.append("the dev handoff index has no Contact Page, so the contact-page click event (cta_click) is left out.")
    lead_mode = "thank-you" if thank_you else "form"
    by_name = {p["Page"]: p["URL"] for p in idx["pages"]}
    form_paths = []
    for pt in idx["points"]:
        u = by_name.get(pt["Page"])
        if pt["kind"] == "form" and u and u not in form_paths:
            form_paths.append(u)
    if lead_mode == "form" and not form_paths:
        warnings.append("the dev handoff index lists no contact form, so `generate_lead` counts every form submitted on the site, "
                        "including search or newsletter forms. Re-run dev-handoff-index, or use --thank-you <path>.")
    events = event_set(lead_mode, thank_you, idx["contact_url"])
    today = args.date or dt.date.today().isoformat()
    plan_path = f"tracking/{slug}/{slug}-tracking-plan.md"
    container_path = f"tracking/{slug}/{slug}-gtm-container.json"
    container = build_container(idx["Client"] or slug, mid, gtm_id, not args.no_google_tag, events, host,
                                thank_you, idx["contact_url"], today, form_paths)
    write(container_path, json.dumps(container, indent=2) + "\n")
    a = {"idx": idx, "events": events, "index_path": index_path, "live": live, "live_src": live_src, "host": host,
         "measurement": mid, "gtm_id": gtm_id, "google_tag": not args.no_google_tag, "lead_mode": lead_mode,
         "thank_you": thank_you, "container_path": container_path, "plan_path": plan_path, "today": today,
         "warnings": warnings, "form_paths": form_paths}
    write(plan_path, render_plan(a))
    print(f"Wrote {plan_path}")
    print(f"Wrote {container_path}")
    print("Events: " + ", ".join(e["name"] + (" (key event)" if e["key"] else "") for e in events))
    for w in warnings:
        print(f"WARNING: {w}")
    return 0


# --------------------------------------------------------------------------- #
# Check (plan against container)
# --------------------------------------------------------------------------- #
def header(text: str, key: str) -> str:
    m = re.search(rf"(?m)^{re.escape(key)}:\s*(.*?)\s*$", text)
    return m.group(1) if m else ""


def check_files(plan_path: str) -> list[tuple[bool, str]]:
    res: list[tuple[bool, str]] = []
    ok = lambda c, m: res.append((bool(c), m))  # noqa: E731
    if not os.path.isfile(plan_path):
        return [(False, f"{plan_path} is missing; run plan first")]
    plan = read(plan_path)
    cpath = header(plan, "Container file")
    ok(cpath and os.path.isfile(cpath), f"container file named in the plan exists ({cpath or 'none named'})")
    if not (cpath and os.path.isfile(cpath)):
        return res
    try:
        data = json.loads(read(cpath))
    except json.JSONDecodeError as e:
        return res + [(False, f"container file is valid JSON ({e})")]
    ok(data.get("exportFormatVersion") == 2, "container uses GTM export format version 2")
    cv = data.get("containerVersion", {})
    tags, triggers = cv.get("tag", []), cv.get("trigger", [])
    variables, builtins = cv.get("variable", []), cv.get("builtInVariable", [])
    trig_ids = {t.get("triggerId") for t in triggers} | {INIT_ALL_PAGES}
    names = {v.get("name") for v in variables} | {b.get("name") for b in builtins}
    dangling = [t["name"] for t in tags for f in t.get("firingTriggerId", []) if f not in trig_ids]
    ok(not dangling, "every tag fires on a trigger that is in the file" + (f" (not: {', '.join(dangling)})" if dangling else ""))
    refs = set(re.findall(r"\{\{([^}]+)\}\}", json.dumps(cv)))
    missing = sorted(refs - names)
    ok(not missing, "every {{variable}} used is defined or switched on" + (f" (missing: {', '.join(missing)})" if missing else ""))
    ids = [x.get("tagId") for x in tags] + [x.get("triggerId") for x in triggers] + [x.get("variableId") for x in variables]
    ok(len(ids) == len(set(ids)), "tag, trigger and variable ids are unique")
    mid = header(plan, "Measurement ID")
    mvar = next((v for v in variables if v.get("name") == MEASUREMENT_VAR), None)
    mval = next((p.get("value") for p in (mvar or {}).get("parameter", []) if p.get("key") == "value"), "")
    ok(MEASUREMENT_RE.match(mid or ""), f"plan Measurement ID looks like G-XXXXXXXXXX ({mid or 'none'})")
    ok(mval == mid, f"container's {MEASUREMENT_VAR} matches the plan ({mval or 'none'})")
    ev_tags = {}
    for t in tags:
        if t.get("type") == "gaawe":
            en = next((p.get("value") for p in t.get("parameter", []) if p.get("key") == "eventName"), "")
            ev_tags[en] = t
            plist = next((p.get("list", []) for p in t.get("parameter", []) if p.get("key") == "eventSettingsTable"), [])
            ok(len(plist) <= 25, f"`{en}` sends at most 25 parameters")
    bad = [e for e in ev_tags if not EVENT_NAME_RE.match(e) or e.lower().startswith(RESERVED_PREFIXES)]
    ok(not bad, "event names are valid GA4 names (letters, digits, underscores, max 40, no reserved prefix)"
       + (f" (bad: {', '.join(bad)})" if bad else ""))
    rows = re.findall(r"(?m)^\| `([^`]+)` \| .*? \| (yes|no) \| .*\|$", plan.split("## Events", 1)[-1].split("\n## ", 1)[0])
    plan_events = {n: k for n, k in rows}
    ok(set(plan_events) == set(ev_tags), "the plan's Events table and the container's event tags list the same events"
       + (f" (plan: {', '.join(sorted(plan_events))}; container: {', '.join(sorted(ev_tags))})" if set(plan_events) != set(ev_tags) else ""))
    ok(plan_events.get("generate_lead") == "yes", "`generate_lead` is a key event")
    gt = header(plan, "Google tag")
    has_gt = any(t.get("type") == "googtag" for t in tags)
    ok(has_gt == gt.startswith("in container"), f"Google tag in the container matches the plan ({gt or 'not stated'})")
    live = header(plan, "Live")
    if live and live != "unknown":
        host = host_of(live.split()[0])
        rx = host_regex(host)
        unguarded = [t["name"] for t in triggers
                     if not any(c.get("type") == "MATCH_REGEX"
                                and any(p.get("value") == "{{Page Hostname}}" for p in c.get("parameter", []))
                                and any(p.get("value") == rx for p in c.get("parameter", []))
                                for c in t.get("filter", []))]
        gt_unguarded = [t["name"] for t in tags if t.get("type") == "googtag" and INIT_ALL_PAGES in t.get("firingTriggerId", [])]
        ok(not gt_unguarded, "the Google tag fires on the live-only Initialization trigger, not on all hosts")
        ok(not unguarded, f"every trigger is limited to the live hostname {host}" + (f" (not: {', '.join(unguarded)})" if unguarded else ""))
    return res


def cmd_check(args: argparse.Namespace) -> int:
    plan_path = args.plan or f"tracking/{args.slug}/{args.slug}-tracking-plan.md"
    res = check_files(plan_path)
    for good, msg in res:
        print(("PASS " if good else "FAIL ") + msg)
    failed = [m for g, m in res if not g]
    print("RESULT: PASS" if not failed else f"RESULT: FAIL ({len(failed)})")
    return 0 if not failed else 1


# --------------------------------------------------------------------------- #
# Site check (after the container is published)
# --------------------------------------------------------------------------- #
def fetch(url: str, timeout: int = 20) -> tuple[int, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; tracking-check)"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except (urllib.error.URLError, OSError) as e:
        return 0, str(e)


def saved_file(root: str, path: str) -> str:
    rel = path.strip("/")
    return os.path.join(root, rel, "index.html") if rel else os.path.join(root, "index.html")


def norm_tel(s: str) -> str:
    digits = re.sub(r"[^0-9]", "", urllib.parse.unquote(s))
    return digits[-10:] if len(digits) >= 10 else digits


def page_findings(html: str, page: dict, points: list[dict], gtm_id: str, mid: str, google_tag: bool,
                  lead_mode: str) -> tuple[str, str, list[str], list[str], str]:
    issues, notes = [], []
    gtm_ids = sorted(set(re.findall(r"GTM-[A-Z0-9]{4,10}", html)))
    loader = re.search(r"googletagmanager\.com/gtm\.js", html) is not None
    if gtm_id in gtm_ids and loader:
        gtm_cell = "yes"
    elif gtm_id in gtm_ids:
        gtm_cell = "ID only"
        issues.append(f"{page['Page']} ({page['URL']}): `{gtm_id}` appears but the gtm.js loader script is missing, so the container never loads.")
    else:
        gtm_cell = "no"
        other = f" (found {', '.join(gtm_ids)} instead)" if gtm_ids else ""
        issues.append(f"{page['Page']} ({page['URL']}): the GTM container `{gtm_id}` is not on the page{other}, so no event fires here.")
    if loader and gtm_id in gtm_ids and not re.search(r"googletagmanager\.com/ns\.html\?id=" + re.escape(gtm_id), html):
        notes.append(f"{page['Page']}: the noscript iframe after the opening body tag is missing (only affects visitors without JavaScript).")
    direct = set(re.findall(r"gtag/js\?id=(G-[A-Z0-9]+)", html)) | set(
        re.findall(r"gtag\(\s*['\"]config['\"]\s*,\s*['\"](G-[A-Z0-9]+)", html))
    if google_tag:
        dup = "yes" if mid in direct else "no"
        if mid in direct:
            issues.append(f"{page['Page']} ({page['URL']}): GA4 `{mid}` is also loaded directly on the page and by the container, so page views are counted twice. Remove the hard-coded gtag.js or plugin tag.")
    else:
        dup = "n/a"
        if mid not in direct:
            issues.append(f"{page['Page']} ({page['URL']}): the plan says the site loads GA4 itself, but `{mid}` is not on the page, so no page views are sent. Re-run plan without --no-google-tag, or add GA4 to the site.")
    for other in sorted(direct - {mid}):
        notes.append(f"{page['Page']}: another GA4 property `{other}` is loaded on the page; check with the SEO whether it should stay.")
    hrefs = re.findall(r"""href\s*=\s*["']([^"']+)["']""", html, re.I)
    tels = {norm_tel(h[4:]) for h in hrefs if h.lower().startswith("tel:")}
    mails = {h[7:].split("?")[0].lower() for h in hrefs if h.lower().startswith("mailto:")}
    expected = [p for p in points if p["Page"] == page["Page"]]
    seen, missing = [], []
    for p in expected:
        if p["kind"] == "tel":
            (seen if norm_tel(p["link"][4:]) in tels else missing).append(p["link"])
        elif p["kind"] == "mailto":
            (seen if p["link"][7:].split("?")[0].lower() in mails else missing).append(p["link"])
        elif p["kind"] == "form":
            has_form = re.search(r"<form\b", html, re.I) is not None
            (seen if has_form else missing).append("contact form")
            if not has_form and lead_mode == "form":
                issues.append(f"{page['Page']} ({page['URL']}): the index lists a contact form but the page HTML has no <form> element (it may sit in an iframe or be built by a script), so the form submission trigger cannot see it. Re-run plan with --thank-you <path> if the form sends visitors to a thank-you page.")
    for m in missing:
        if m != "contact form":
            notes.append(f"{page['Page']}: the index lists `{m}` but the page has no such link; `click_to_call` or `click_to_email` cannot fire for it here.")
    links_cell = f"{len(seen)} of {len(expected)}" if expected else "none listed"
    return gtm_cell, dup, issues, notes, links_cell


def cmd_site(args: argparse.Namespace) -> int:
    plan_path = args.plan
    if not os.path.isfile(plan_path):
        die(f"{plan_path} is missing; run plan first.")
    plan = read(plan_path)
    m = re.match(r"tracking/([^/]+)/", plan_path.replace(os.sep, "/"))
    slug = m.group(1) if m else ""
    index_path = header(plan, "Index")
    if not os.path.isfile(index_path):
        die(f"{index_path} (named in the plan) is missing.")
    idx = parse_index(read(index_path))
    mid = header(plan, "Measurement ID")
    gtm_id = (args.gtm_id or header(plan, "GTM container")).upper()
    if not GTM_RE.match(gtm_id):
        die("no GTM container ID. Ask Dev for it (GTM, top bar, starts GTM-) and pass --gtm-id.")
    google_tag = header(plan, "Google tag").startswith("in container")
    lead_mode = "thank-you" if header(plan, "Lead event").startswith("thank-you") else "form"
    live = header(plan, "Live").split(" ")[0]
    if args.saved:
        source = f"saved pages: {args.saved}"
    else:
        if not live or live == "unknown":
            die("the plan has no live address. Pass --saved <folder> or re-run plan with --site.")
        source = live
    rows, issues, notes = [], [], []
    for p in build_pages(idx):
        if args.saved:
            f = saved_file(args.saved, p["URL"])
            if not os.path.isfile(f):
                rows.append(f"| {p['Page']} | {p['URL']} | not saved | - | - | ISSUE |")
                issues.append(f"{p['Page']} ({p['URL']}): no saved page at {f}.")
                continue
            html = read(f)
        else:
            status, html = fetch(live + p["URL"])
            if status != 200:
                rows.append(f"| {p['Page']} | {p['URL']} | could not load ({status or 'no answer'}) | - | - | ISSUE |")
                issues.append(f"{p['Page']} ({p['URL']}): the live page did not answer 200 ({status or html[:80]}).")
                continue
        gtm_cell, dup, pi, pn, links_cell = page_findings(html, p, idx["points"], gtm_id, mid, google_tag, lead_mode)
        issues += pi
        notes += pn
        rows.append(f"| {p['Page']} | {p['URL']} | {gtm_cell} | {dup} | {links_cell} | {'ISSUE' if pi else 'OK'} |")
    today = args.date or dt.date.today().isoformat()
    events = re.findall(r"(?m)^\| `([^`]+)` \| ", plan.split("## Test", 1)[-1])
    out = [
        f"Client: {idx['Client']}",
        f"Checked: {today}",
        f"Plan: {plan_path}",
        f"Source: {source}",
        f"GTM container: {gtm_id}",
        f"Measurement ID: {mid}",
        "",
        f"# Tracking Check: {idx['Client']}",
        "",
        "## Pages",
        "",
        "| Page | URL | GTM container | GA4 loaded twice | Conversion links | Result |",
        "|---|---|---|---|---|---|",
        *rows,
        "",
        "## Issues",
        "",
        *([f"- {i}" for i in issues] or ["- none"]),
        "",
        "## Notes",
        "",
        *([f"- {n}" for n in notes] or ["- none"]),
        "",
        "## Still to Test by Hand",
        "",
        "This check reads the page code; only GTM Preview and GA4 DebugView prove each event arrives. Follow the plan's Test section for:",
        "",
        *[f"- [ ] `{e}`" for e in events],
        "",
        "RESULT: TRACKING OK" if not issues else "RESULT: TRACKING ISSUES",
        "",
    ]
    path = f"tracking/{slug}/{slug}-tracking-check-{today}.md"
    write(path, "\n".join(out))
    print(f"Wrote {path}")
    print(f"Issues: {len(issues)}, notes: {len(notes)}")
    print("RESULT: TRACKING OK" if not issues else "RESULT: TRACKING ISSUES")
    return 0


# --------------------------------------------------------------------------- #
# Contracts
# --------------------------------------------------------------------------- #
def cmd_contract(args: argparse.Namespace) -> int:
    if args.validate:
        data = json.loads(read(args.validate))
        if isinstance(data, list):
            for item in data:
                for k in ("Page", "URL", "Priority", "Internal links"):
                    if k not in item:
                        print(f"FAIL: item without {k}")
                        return 1
            if not any(i["Priority"] == "Build" for i in data):
                print("FAIL: no Build page")
                return 1
        elif isinstance(data, dict):
            live = data.get("Live:", "")
            if not str(live).startswith("http") or not host_of(str(live).split()[0]):
                print("FAIL: Live: is not an address")
                return 1
        print("OK")
        return 0
    if args.kind == "index":
        idx = parse_index(read(args.file))
        items = []
        for p in idx["pages"]:
            items.append({"Page": p["Page"], "URL": p["URL"], "Priority": p["Priority"], "Section": p["Section"],
                          "Internal links": [l["url"] for l in p["Internal links"]],
                          "Conversion points": [c["link"] for c in idx["points"] if c["Page"] == p["Page"]]})
        print(json.dumps(items, indent=2))
        return 0
    die("contract needs 'index <file>' or --validate <fixture>")
    return 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan")
    p.add_argument("--slug", required=True)
    p.add_argument("--measurement-id")
    p.add_argument("--gtm-id")
    p.add_argument("--site", help="live base URL, when there is no launch check yet")
    p.add_argument("--thank-you", help="path of the page a sent form lands on, e.g. /thank-you/")
    p.add_argument("--no-google-tag", action="store_true", help="the site already loads GA4 itself")
    p.add_argument("--date")
    p.set_defaults(func=cmd_plan)
    c = sub.add_parser("check")
    c.add_argument("--slug")
    c.add_argument("--plan")
    c.set_defaults(func=cmd_check)
    s = sub.add_parser("site")
    s.add_argument("--plan", required=True)
    s.add_argument("--gtm-id")
    s.add_argument("--saved", help="folder of saved live pages: index.html, <path>/index.html")
    s.add_argument("--date")
    s.set_defaults(func=cmd_site)
    k = sub.add_parser("contract")
    k.add_argument("kind", nargs="?", choices=["index"])
    k.add_argument("file", nargs="?")
    k.add_argument("--validate")
    k.set_defaults(func=cmd_contract)
    args = ap.parse_args()
    if args.cmd == "check" and not (args.slug or args.plan):
        ap.error("check needs --slug or --plan")
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
