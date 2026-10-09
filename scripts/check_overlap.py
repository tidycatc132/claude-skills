#!/usr/bin/env python3
"""Offline trigger-collision check across the whole skill suite.

This is a cheap lexical proxy (TF-IDF cosine over names + descriptions). It cannot tell you
how Claude will actually route a prompt (run_trigger_evals.py does that), but it reliably
catches the structural problem that causes most mis-triggering: two skills whose
descriptions say nearly the same thing without naming each other.

Errors (exit 1):
  * two skills overlap >= HARNESS_OVERLAP_CROSSREF (default 0.30) and one description does
    not mention the other skill's name  -> add 'Do NOT use for X (use <other-skill>)'
  * two skills overlap >= HARNESS_OVERLAP_ERROR (default 0.60) -> merge or sharpen them
Warnings:
  * an eval prompt that lexically fits a different skill better than its own
  * a should_not_trigger prompt that lexically fits its own skill strongly
"""
from __future__ import annotations

import argparse
import math
import os
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

CROSSREF = float(os.environ.get("HARNESS_OVERLAP_CROSSREF", "0.30"))
HARD = float(os.environ.get("HARNESS_OVERLAP_ERROR", "0.60"))

STOP = set("""
a an and are as at be but by can do does for from has have how i if in into is it its of on or our so that the
their them then there these they this to up us use used using was we what when where which who will with you your
skill skills user users want wants need needs asks ask trigger triggers whenever any also even just like not
should must may make makes create creates built build builds generate generates help helps etc e g
""".split())


def tokens(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z][a-z0-9]{2,}", text.lower()) if t not in STOP]


def vec(tokens_: list[str], idf: dict[str, float]) -> dict[str, float]:
    tf = Counter(tokens_)
    return {t: c * idf.get(t, 1.0) for t, c in tf.items()}


def cos(a: dict[str, float], b: dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(v * b.get(k, 0.0) for k, v in a.items())
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    skills = [C.load_skill(d) for d in C.list_skill_dirs() if (d / "SKILL.md").exists()]
    if len(skills) < 2:
        print("fewer than two skills; nothing to compare")
        return 0

    all_names = [s["dirname"] for s in skills]

    def core_description(desc: str) -> str:
        """The part of a description that says what the skill DOES.

        Boundary sentences ('Do NOT use for X (use other-skill)') deliberately describe a sibling's job
        and name it, so they would inflate similarity for exactly the skills that did the right thing.
        """
        sentences = re.split(r"(?<=[.!?])\s+", desc)
        kept = [x for x in sentences if not re.search(r"do not use|don't use|not for|instead", x, re.I)]
        text = " ".join(kept) or desc
        for n in all_names:
            text = text.replace(n, " ")
        return text

    docs = {s["dirname"]: tokens(core_description(s["description"])) for s in skills}
    n = len(docs)
    df: Counter = Counter()
    for toks in docs.values():
        df.update(set(toks))
    idf = {t: math.log((n + 1) / (c + 1)) + 1.0 for t, c in df.items()}
    vecs = {k: vec(v, idf) for k, v in docs.items()}

    reports: dict[str, C.Report] = {s["dirname"]: C.Report(s["dirname"]) for s in skills}
    by_name = {s["dirname"]: s for s in skills}
    names = sorted(by_name)

    pair_scores = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            score = cos(vecs[a], vecs[b])
            pair_scores.append((score, a, b))
            if score >= HARD:
                reports[a].error(
                    f"description overlaps '{b}' at {score:.2f} (>= {HARD}). They will fight over the same prompts; merge them or sharpen the boundary."
                )
            if score >= CROSSREF:
                for x, y in ((a, b), (b, a)):
                    if y not in by_name[x]["description"]:
                        reports[x].error(
                            f"description overlaps '{y}' at {score:.2f} but never names it. Add a boundary like "
                            f"'Do NOT use for <the other job> (use {y})'."
                        )

    # eval prompts vs descriptions (lexical proxy => warnings only)
    for s in skills:
        name = s["dirname"]
        trig = C.EVALS_DIR / name / "trigger.json"
        if not trig.exists():
            continue
        try:
            data = C.load_json(trig)
        except Exception:
            continue

        def best(prompt: str):
            pv = vec(tokens(prompt), idf)
            scored = sorted(((cos(pv, vecs[k]), k) for k in names), reverse=True)
            return scored[0]

        for p in data.get("should_trigger", []):
            score, top = best(str(p))
            if top != name and score > 0:
                reports[name].warn(f"should_trigger prompt looks closer to '{top}' ({score:.2f}) lexically: \"{str(p)[:70]}\"")
        for p in data.get("should_not_trigger", []):
            score, top = best(str(p))
            if top == name and score >= 0.25:
                reports[name].warn(f"should_not_trigger prompt looks like this skill lexically ({score:.2f}): \"{str(p)[:70]}\"")

    out = list(reports.values())
    if not args.quiet:
        top3 = sorted(pair_scores, reverse=True)[:3]
        print("closest description pairs: " + ", ".join(f"{a}~{b} {s:.2f}" for s, a, b in top3))
    C.print_reports(out, show_warnings=not args.quiet)
    return 0 if all(r.ok for r in out) else 1


if __name__ == "__main__":
    sys.exit(main())
