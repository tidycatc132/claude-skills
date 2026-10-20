#!/usr/bin/env python3
"""Self-test for feedback.py's Week 2 reply, the nudge and the unchanged Week 1 path.

Usage:
  python3 selftest_week2.py [--week2 DIR] [--week1 DIR] [--plans DIR]

Copies each fixture folder to a temporary directory, renders the reference plan (must pass), then
changes the plan in one way the script must refuse (a strategy item not owned by SEO, a reply that
says the Blueprint already changed, a page with no content folder, a nudge before the reply-by date,
an invented date in the nudge, and so on). Defaults are the repo's invented Fernhollow (Week 2) and
Linden (Week 1) fixtures; run it after changing feedback.py. Prints one line per case and exits 1 on
any miss. Standard library only.
"""
from __future__ import annotations

import argparse
import copy
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "feedback.py"
REPO = HERE.parents[2]  # defaults resolve against the repo, from any working directory
W2_SLUG = "fernhollow-animal-hospital"
W1_SLUG = "linden-rowe-family-law"


TMP: list[Path] = []


def mkdtemp() -> Path:
    TMP.append(Path(tempfile.mkdtemp()))
    return TMP[-1]


def run(folder: Path, *args: str) -> tuple[int, str]:
    r = subprocess.run([sys.executable, str(SCRIPT), *args], cwd=folder, capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def render(src: Path, slug: str, plan: dict, dry: bool = False, prep=None) -> tuple[int, str, Path]:
    tmp = mkdtemp()
    shutil.copytree(src, tmp, dirs_exist_ok=True)
    if prep:
        prep(tmp)
    (tmp / "feedback-plan.json").write_text(json.dumps(plan), encoding="utf-8")
    args = ["render", f"kickoff/{slug}", "--feedback", "feedback-email.txt", "--plan", "feedback-plan.json"]
    rc, out = run(tmp, *args + (["--dry-run"] if dry else []))
    return rc, out, tmp


def nudge(src: Path, plan: dict, today: str, prep=None) -> tuple[int, str, Path]:
    tmp = mkdtemp()
    shutil.copytree(src, tmp, dirs_exist_ok=True)
    (tmp / "feedback-email.txt").unlink(missing_ok=True)
    if prep:
        prep(tmp)
    (tmp / "nudge-plan.json").write_text(json.dumps(plan), encoding="utf-8")
    rc, out = run(tmp, "nudge", f"kickoff/{W2_SLUG}", "--plan", "nudge-plan.json", "--today", today)
    return rc, out, tmp


def edit_body(plan: dict, old: str, new: str) -> dict:
    p = copy.deepcopy(plan)
    if old not in p["reply"]["body"]:
        raise SystemExit(f"selftest setup: {old!r} not in the reply body")
    p["reply"]["body"] = p["reply"]["body"].replace(old, new)
    return p


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--week2", default=str(REPO / "fixtures/client-feedback/fernhollow"))
    ap.add_argument("--week1", default=str(REPO / "fixtures/client-feedback/linden"))
    ap.add_argument("--plans", default=str(REPO / "fixtures/client-feedback/plans"))
    a = ap.parse_args()
    w2, w1, plans = Path(a.week2), Path(a.week1), Path(a.plans)
    p2 = json.loads((plans / "fernhollow-week-2-plan.json").read_text(encoding="utf-8"))
    p1 = json.loads((plans / "linden-week-1-plan.json").read_text(encoding="utf-8"))
    pn = json.loads((plans / "fernhollow-nudge-plan.json").read_text(encoding="utf-8"))
    results: list[tuple[str, bool, str]] = []

    def expect(name: str, rc_out, ok_when, want: str = "") -> None:
        rc, out = rc_out[0], rc_out[1]
        ok = ok_when(rc) and (want in out)
        results.append((name, ok, "" if ok else out.strip().splitlines()[-1] if out.strip() else "no output"))

    def item(plan: dict, n: int, **kw) -> dict:
        p = copy.deepcopy(plan)
        p["items"][n].update(kw)
        return p

    passes, fails = (lambda rc: rc == 0), (lambda rc: rc != 0)

    # Week 2 reply
    rc, out, tmp = render(w2, W2_SLUG, p2)
    rep = (tmp / "feedback" / W2_SLUG / "2026-12-03-feedback.md")
    text = rep.read_text(encoding="utf-8") if rep.exists() else ""
    expect("week 2 reference plan passes", (rc, out), passes, "RESULT: PASS")
    results.append(("week 2 report holds strategy rows for SEO",
                    "Status: hold the reply until SEO signs off" in text and "- #2 Keyword Opportunity:" in text, ""))
    results.append(("week 2 impact names Blueprint, deck and pages",
                    "high: Blueprint Executive Summary, Keyword Opportunity, Growth Strategy; deck slides 2, 9, 10, 14; "
                    "pages emergency-vet, home" in text, ""))
    results.append(("week 2 updates file in the old format",
                    (tmp / "feedback" / W2_SLUG / "2026-12-03-feedback-updates.md").exists(), ""))
    rc, out, tmp = render(w2, W2_SLUG, p2)
    (tmp / "feedback" / W2_SLUG / "2026-12-03-feedback.md").write_text(
        text.replace("Status: hold the reply until SEO signs off the items below\n", ""), encoding="utf-8")
    expect("check catches a missing SEO hold", run(tmp, "check", f"kickoff/{W2_SLUG}", "--feedback", "feedback-email.txt",
                                                  "--report", f"feedback/{W2_SLUG}/2026-12-03-feedback.md"),
           fails, "| SEO review | FAIL |")
    expect("strategy owned by Content refused", render(w2, W2_SLUG, item(p2, 1, owner="Content"), True)[:2],
           fails, "owned by SEO")
    expect("strategy affecting a page refused",
           render(w2, W2_SLUG, item(p2, 1, affects="page: home"), True)[:2], fails, "affects 'blueprint: <section>'")
    expect("strategy with low impact refused", render(w2, W2_SLUG, item(p2, 2, impact="low"), True)[:2],
           fails, "impact medium or high")
    expect("page with no content folder refused",
           render(w2, W2_SLUG, item(p2, 3, changes={"pages": ["dental-care", "sisters"]}), True)[:2],
           fails, "has no content/sisters/article.md")
    expect("unknown Blueprint section refused",
           render(w2, W2_SLUG, item(p2, 2, changes={"blueprint": ["Brand Voice"]}), True)[:2],
           fails, "is not a Blueprint section")
    expect("content change naming nothing refused", render(w2, W2_SLUG, item(p2, 3, changes={}), True)[:2],
           fails, "names the page(s)")
    expect("outside-scope request with changes refused",
           render(w2, W2_SLUG, item(p2, 5, changes={"pages": ["vet-redmond-or"]}), True)[:2],
           fails, "changes nothing until a signed change")
    expect("reply saying the Blueprint changed refused",
           render(w2, W2_SLUG, edit_body(p2, "Our SEO lead will review the keyword priorities with dental and wellness "
                                             "in mind, and I'll come back to you before we change the Blueprint.",
                                         "We've updated the Blueprint to lead with dental and wellness."), True)[:2],
           fails, "already changed")
    expect("reply committing before review refused",
           render(w2, W2_SLUG, edit_body(p2, "Our SEO lead will review the keyword priorities with dental and wellness "
                                             "in mind, and I'll come back to you before we change the Blueprint.",
                                         "We'll switch the keyword priorities to dental and wellness."), True)[:2],
           fails, "before SEO has reviewed it")
    no_bp = edit_body(edit_body(p2, "going through the deck", "going through everything"),
                      "before we change the Blueprint", "before we change anything")
    expect("reply naming neither Blueprint nor deck refused", render(w2, W2_SLUG, no_bp, True)[:2], fails,
           "names the Blueprint or the deck")
    expect("week 2 plan without the Blueprint refused",
           render(w2, W2_SLUG, p2, True, prep=lambda t: shutil.rmtree(t / "blueprint"))[:2], fails,
           "needs blueprint/")
    p_w1 = copy.deepcopy(p2)
    p_w1.pop("week")
    expect("strategy in a Week 1 plan refused", render(w2, W2_SLUG, p_w1, True)[:2], fails, "set \"week\": 2")

    # Nudge
    expect("nudge before the reply-by date refused", nudge(w2, pn, "2026-12-04")[:2], fails, "NOT DUE")
    rc, out, tmp = nudge(w2, pn, "2026-12-08")
    nf = tmp / "feedback" / W2_SLUG / "2026-12-08-week-2-nudge.md"
    expect("nudge after the reply-by date passes", (rc, out), passes, "RESULT: PASS")
    results.append(("nudge notes say Week 3 proceeds",
                    nf.exists() and "- Week 3 proceeds with the Blueprint as is." in nf.read_text(encoding="utf-8"), ""))
    bad_date = copy.deepcopy(pn)
    bad_date["reply"]["body"] = bad_date["reply"]["body"].replace("If a short call", "Could you reply by December 11? If a short call")
    expect("nudge with an invented date refused", nudge(w2, bad_date, "2026-12-08")[:2], fails, "the only date a nudge gives")
    no_go = copy.deepcopy(pn)
    no_go["reply"]["body"] = no_go["reply"]["body"].replace(
        "we will go ahead with the Blueprint as it stands and start on the next stage of the site",
        "we would love to hear from you")
    expect("nudge that does not say work goes ahead refused", nudge(w2, no_go, "2026-12-08")[:2], fails, "goes ahead")

    def logged(t: Path) -> None:
        d = t / "feedback" / W2_SLUG
        d.mkdir(parents=True, exist_ok=True)
        (d / "2026-12-03-feedback.md").write_text("Client: Fernhollow Animal Hospital\nWeek: 2\n", encoding="utf-8")
    expect("nudge after a logged Week 2 reply refused", nudge(w2, pn, "2026-12-08", prep=logged)[:2], fails,
           "REPLY LOGGED")

    # Week 1 unchanged
    rc, out, tmp = render(w1, W1_SLUG, p1)
    t1 = (tmp / "feedback" / W1_SLUG / "2026-11-25-feedback.md")
    t1 = t1.read_text(encoding="utf-8") if t1.exists() else ""
    expect("week 1 plan still passes", (rc, out), passes, "RESULT: PASS")
    results.append(("week 1 report has no Week 2 parts",
                    "Week:" not in t1 and "## SEO Review" not in t1 and
                    "- Items: 3 (0 content, 0 design, 0 scope, 1 question, 2 approval)" in t1, ""))
    expect("changes in a Week 1 plan refused", render(w1, W1_SLUG, item(p1, 0, changes={"pages": ["home"]}), True)[:2],
           fails, "Week 2 reply only")

    commit_cond = edit_body(p2, "Our SEO lead will review the keyword priorities with dental and wellness in mind, and I'll "
                                "come back to you before we change the Blueprint.",
                                "We'll switch the keyword priorities to dental once you confirm.")
    expect("commitment with only a client-side condition refused", render(w2, W2_SLUG, commit_cond, True)[:2], fails,
           "before SEO has reviewed it")
    p_unmarked = copy.deepcopy(p2)
    p_unmarked.pop("week")
    p_unmarked["items"] = [i for i in p_unmarked["items"] if i["type"] != "strategy"]
    for i in p_unmarked["items"]:
        i.pop("changes", None)
        if i["affects"].startswith(("blueprint", "page")):
            i["affects"] = "other"
    expect("Week 2 reply left unmarked refused", render(w2, W2_SLUG, p_unmarked, True)[:2], fails, "set \"week\": 2")
    friday = copy.deepcopy(pn)
    friday["reply"]["body"] = friday["reply"]["body"].replace("If a short call", "Could you reply by next week? If a short call")
    expect("nudge with a new deadline refused", nudge(w2, friday, "2026-12-08")[:2], fails, "new deadline")
    guide = REPO / "skills/blueprint-deck/references/slide-guide.md"
    if guide.exists():
        import re
        sys.path.insert(0, str(HERE))
        import feedback as FB
        deck = {int(n): t.strip() for n, t in re.findall(r"(?m)^\| (\d+) \| `[a-z-]+` \| (.+?) \|$",
                                                       guide.read_text(encoding="utf-8"))}
        wrong = [f"{n} {t}" for n, t in FB.DECK_SLIDES.items() if deck.get(n) != t]
        results.append(("deck slide numbers match blueprint-deck's slide guide", not wrong, "; ".join(wrong)))
    for t in TMP:
        shutil.rmtree(t, ignore_errors=True)
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'MISS'}  {name}" + (f"  ({detail})" if detail else ""))
    misses = sum(1 for _, ok, _ in results if not ok)
    print(f"{len(results) - misses}/{len(results)} cases")
    return 1 if misses else 0


if __name__ == "__main__":
    sys.exit(main())
