#!/usr/bin/env python3
"""ADA cell: is the site running accessibility software, or does it pass a quick screen?

Usage:
    python3 -I check_ada.py PAGE.html [PAGE.html ...] [--out ada.json]

Each PAGE is the saved HTML of a key page (homepage and core service pages).
Prints JSON:
    {"result": "Pass" | "Fail",
     "ada_software": "<vendor>" | null,
     "software_pages": ["file", ...],
     "pages": [{"file", "images_without_alt", "unlabelled_fields", "lang_missing"}],
     "reason": "..."}

Pass when an accessibility overlay or widget is detected on any page, or when
every page has a lang attribute, no images without an alt attribute and no
unlabelled form fields. Otherwise Fail. This is a screen, not a WCAG audit.
"""
import json
import re
import sys
from html.parser import HTMLParser

# Vendor signatures: a substring of the script or widget markup -> display name.
ADA_SOFTWARE = [
    ("acsbapp.com", "accessiBe"), ("accessibe", "accessiBe"),
    ("userway.org", "UserWay"), ("_userway_", "UserWay"),
    ("audioeye.com", "AudioEye"), ("audioeye", "AudioEye"),
    ("equalweb.com", "EqualWeb"), ("equalweb", "EqualWeb"),
    ("accessiway", "AccessiWay"), ("allyable", "Allyable"), ("adally", "ADAlly"),
    ("maxaccess", "MaxAccess"), ("accessibilityspark", "Accessibility Spark"),
    ("accessibly", "Accessibly"), ("accessiblyapp", "Accessibly"),
    ("enable-ally", "Enable"), ("wp-accessibility", "WP Accessibility plugin"),
    ("one-click-accessibility", "One Click Accessibility plugin"),
    ("pojo-accessibility", "One Click Accessibility plugin"),
    ("recite.me", "Recite Me"), ("reciteme", "Recite Me"),
    ("essentialaccessibility", "eSSENTIAL Accessibility"), ("levelaccess", "Level Access"),
    ("monsido", "Monsido"), ("siteimprove", "Siteimprove"),
    ("usablenet", "UsableNet"), ("adaccessibility", "ADA Accessibility widget"),
    ("accessibility-widget", "accessibility widget"), ("accessibility_widget", "accessibility widget"),
]
SKIP_INPUT_TYPES = {"hidden", "submit", "button", "reset", "image"}


class Screen(HTMLParser):
    def __init__(self):
        super().__init__()
        self.lang = False
        self.images_without_alt = 0
        self.fields = []          # (id, has_own_label)
        self.label_for = set()
        self.in_label = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html" and (a.get("lang") or "").strip():
            self.lang = True
        elif tag == "img":
            if "alt" not in a and a.get("role") != "presentation" and a.get("aria-hidden") != "true":
                self.images_without_alt += 1
        elif tag == "label":
            self.in_label += 1
            if a.get("for"):
                self.label_for.add(a["for"])
        elif tag in ("input", "select", "textarea"):
            if tag == "input" and (a.get("type") or "text").lower() in SKIP_INPUT_TYPES:
                return
            own = bool(a.get("aria-label") or a.get("aria-labelledby") or a.get("title")) or self.in_label > 0
            self.fields.append((a.get("id"), own))

    def handle_endtag(self, tag):
        if tag == "label" and self.in_label:
            self.in_label -= 1

    @property
    def unlabelled_fields(self):
        return sum(1 for fid, own in self.fields if not own and not (fid and fid in self.label_for))


def software_in(html):
    low = html.lower()
    for needle, name in ADA_SOFTWARE:
        if needle in low:
            return name
    return None


def check(paths):
    pages, software, software_pages = [], None, []
    for path in paths:
        try:
            html = open(path, encoding="utf-8", errors="replace").read()
        except OSError as exc:
            print(f"skipped {path}: {exc}", file=sys.stderr)
            continue
        vendor = software_in(html)
        if vendor:
            software = software or vendor
            software_pages.append(path)
        s = Screen()
        s.feed(html)
        pages.append({"file": path, "images_without_alt": s.images_without_alt,
                      "unlabelled_fields": s.unlabelled_fields, "lang_missing": not s.lang})
    clean = bool(pages) and all(not p["lang_missing"] and p["images_without_alt"] == 0 and p["unlabelled_fields"] == 0 for p in pages)
    if software:
        result, reason = "Pass", f"{software} accessibility software detected on {len(software_pages)} of {len(pages)} pages"
    elif clean:
        result, reason = "Pass", f"no accessibility software, but all {len(pages)} key pages pass the quick screen"
    else:
        failing = [p for p in pages if p["lang_missing"] or p["images_without_alt"] or p["unlabelled_fields"]]
        detail = "; ".join(
            f"{p['file']}: " + ", ".join(x for x in (
                f"{p['images_without_alt']} images without alt" if p["images_without_alt"] else "",
                f"{p['unlabelled_fields']} unlabelled fields" if p["unlabelled_fields"] else "",
                "no lang attribute" if p["lang_missing"] else "") if x)
            for p in failing) or "no pages could be read"
        result, reason = "Fail", f"no accessibility software and the quick screen fails: {detail}"
    return {"result": result, "ada_software": software, "software_pages": software_pages, "pages": pages, "reason": reason}


def main():
    args = sys.argv[1:]
    out = None
    if "--out" in args:
        i = args.index("--out")
        out = args[i + 1] if i + 1 < len(args) else sys.exit("--out needs a file path")
        del args[i:i + 2]
    if not args:
        sys.exit(__doc__)
    report = check(args)
    text = json.dumps(report, indent=1)
    if out:
        with open(out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"{report['result']}: {report['reason']} (saved {out})")
    else:
        print(text)


if __name__ == "__main__":
    main()
