#!/usr/bin/env python3
"""Self-test for the new-build-kickoff scripts. Invented clients only. Prints `selftest: N/N passed`."""
from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from check_kickoff import check as check_folder, slugify  # noqa: E402

results: list[tuple[str, bool]] = []


def check(name: str, cond: bool) -> None:
    results.append((name, bool(cond)))
    if not cond:
        print(f"FAIL {name}")


def page(path: Path, title: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"<html><head><title>{title}</title></head><body></body></html>", encoding="utf-8")


def inventory_row(data: list[list[str]], folder: Path, html_dir: Path) -> tuple[bool, str]:
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / "fernhill-glass-and-glazing-url-inventory.csv").open("w", newline="", encoding="utf-8") as fh:
        csv.writer(fh).writerows([["url", "title", "page_type", "status", "source"], *data])
    sow = folder.parent / "sow.md"
    sow.write_text("Website build, 8 pages.\n", encoding="utf-8")
    row = [r for r in check_folder(folder, "Fernhill Glass & Glazing", sow, False, str(html_dir))
           if r[0] == "every saved page is in the inventory as saved"]
    return (row[0][1], row[0][2]) if row else (False, "row missing")


def main() -> int:
    check("ampersand becomes and", slugify("Fernhill Glass & Glazing") == "fernhill-glass-and-glazing")
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        site = tmp / "site"
        page(site / "index.html", "Fernhill Glass")
        page(site / "about" / "index.html", "About Fernhill")
        page(site / "services" / "window-repair" / "index.html", "Window Repair")
        page(site / "contact.html", "Contact Fernhill")
        out = tmp / "inv.csv"
        p = subprocess.run([sys.executable, HERE / "make_inventory.py", "--out", out, "--base", "fernhill.example",
                            "--html-dir", site], capture_output=True, text=True)
        rows = {r["url"]: r for r in csv.DictReader(out.open(encoding="utf-8"))} if p.returncode == 0 else {}
        want = {"https://fernhill.example/": "Fernhill Glass", "https://fernhill.example/about": "About Fernhill",
                "https://fernhill.example/services/window-repair": "Window Repair",
                "https://fernhill.example/contact": "Contact Fernhill"}
        check("subfolder pages read with titles", {u: r["title"] for u, r in rows.items()} == want)
        check("subfolder pages saved", all(r["status"] == "saved" for r in rows.values()))
        check("page types from subfolder paths", rows.get("https://fernhill.example/about", {}).get("page_type") == "about"
              and rows.get("https://fernhill.example/services/window-repair", {}).get("page_type") == "service")

        folder = tmp / "kickoff" / "fernhill-glass-and-glazing"
        full = [[u, t, "other", "saved", "saved"] for u, t in want.items()]
        ok, _ = inventory_row(full, folder, site)
        check("all saved pages listed passes", ok)
        partial = [full[0]] + [[u, "", "other", "listed", "sitemap"] for u, _, *_ in full[1:]]
        ok, detail = inventory_row(partial, folder, site)
        check("saved pages only listed from the sitemap fails", not ok and "3 missed" in detail and "/about" in detail)

    passed = sum(ok for _, ok in results)
    print(f"selftest: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
