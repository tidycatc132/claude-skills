#!/usr/bin/env python3
"""Check a welcome email against the kickoff files and the links the AM gave.

  check_email.py <slug>-welcome-email.md --gap <slug>-gap-questions.md \
      --context <slug>-context.md --am "Jordan Ellis" --form-url URL [--booking-url URL]

Prints one line per problem, then `RESULT: PASS` or `RESULT: FAIL` (exit 1).
Standard library only.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from open_questions import parse  # noqa: E402

SIGN_OFF = "Account Manager, WISE Digital Partners"
MAX_WORDS = 250  # body words, not counting the numbered questions
URL_RE = re.compile(r"https?://[^\s)>\]]+")
ITEM_RE = re.compile(r"^(\d+)\.\s+(.*\S)\s*$")
# Phrases WISE does not use with clients (references/voice.md).
BANNED = [
    "thrilled", "excited to partner", "excited to work", "delighted", "world-class",
    "cutting-edge", "best-in-class", "don't hesitate", "do not hesitate", "synergy",
    "game-changer", "game changer",
]
# Numbers the email may use without a source: Week 1, 2 to 3 design options, a 15-minute form.
ALLOWED_NUMBERS = {"1", "2", "3", "15"}


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.replace("’", "'")).strip()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("email")
    ap.add_argument("--gap", required=True)
    ap.add_argument("--context", required=True)
    ap.add_argument("--am", required=True, help="the Account Manager's name as it should be signed")
    ap.add_argument("--form-url", required=True)
    ap.add_argument("--booking-url")
    a = ap.parse_args()

    problems: list[str] = []
    text = Path(a.email).read_text(encoding="utf-8").replace("\r\n", "\n")
    gap_text = Path(a.gap).read_text(encoding="utf-8")
    ctx_text = Path(a.context).read_text(encoding="utf-8")
    client = re.search(r"^Client:\s*(.+?)\s*$", gap_text, re.M)
    client = client.group(1) if client else ""

    lines = text.split("\n")
    if len(lines) < 4 or lines[0] != f"Client: {client}":
        problems.append(f"line 1 must be 'Client: {client}'")
    if len(lines) < 4 or not re.match(r"^Subject: \S.{5,}$", lines[1]):
        problems.append("line 2 must be 'Subject: <subject line>'")
    elif len(lines[1]) - len("Subject: ") > 70:
        problems.append("subject line is over 70 characters")
    if len(lines) < 4 or lines[2] != "":
        problems.append("line 3 must be blank; the email body starts on line 4")
    body_lines = lines[3:]
    body = "\n".join(body_lines)

    # Questions: every open one, verbatim, numbered 1..n in file order; no answered ones.
    qs = parse(gap_text)
    open_q = [q for q in qs if not q["answer"]]
    done_q = [q for q in qs if q["answer"]]
    items = [(int(m.group(1)), m.group(2)) for m in (ITEM_RE.match(l) for l in body_lines) if m]
    want = [(i + 1, norm(q["question"])) for i, q in enumerate(open_q)]
    got = [(n, norm(t)) for n, t in items]
    if got != want:
        if not open_q and got:
            problems.append("no gap questions are open, but the email has a numbered list")
        else:
            for n, q in want:
                if (n, q) not in got:
                    problems.append(f"open question missing or changed, expected as item {n}: {q[:70]}")
            for n, q in got:
                if (n, q) not in want:
                    problems.append(f"numbered item {n} is not an open gap question: {q[:70]}")
    nbody = norm(body)
    for q in done_q:
        if norm(q["question"]) in nbody:
            problems.append(f"answered question {q['number']} is in the email; leave it out")

    # Links: the form link always; the booking link when given; no other links.
    urls = [u.rstrip(".,;:") for u in URL_RE.findall(body)]
    if a.form_url not in urls:
        problems.append("the intake form link is missing or altered")
    allowed = {a.form_url}
    if a.booking_url:
        allowed.add(a.booking_url)
        if a.booking_url not in urls:
            problems.append("the Kickoff Call booking link is missing or altered")
    for u in urls:
        if u not in allowed:
            problems.append(f"link not given by the AM: {u}")

    # Signed by the AM.
    filled = [l.strip() for l in body_lines if l.strip()]
    if filled[-2:] != [a.am, SIGN_OFF]:
        problems.append(f"the email must end with '{a.am}' then '{SIGN_OFF}' on the last two lines")

    # Placeholders and banned phrases.
    for m in re.finditer(r"\[[^\]\n]*\]|<[^>\n]*>|\b(TODO|TBD|FIXME)\b", body):
        problems.append(f"placeholder left in the email: {m.group(0)[:40]}")
    low = body.lower().replace("’", "'")
    for p in BANNED:
        if p in low:
            problems.append(f"banned phrase: '{p}'")
    if body.count("!") > 1:
        problems.append(f"{body.count('!')} exclamation marks; use at most 1")

    # Numbers must come from the kickoff files or the fixed list.
    question_lines = {i for i, l in enumerate(body_lines) if ITEM_RE.match(l)}
    prose = "\n".join(l for i, l in enumerate(body_lines) if i not in question_lines)
    prose = URL_RE.sub(" ", prose)
    known = set(re.findall(r"\d+", ctx_text + "\n" + gap_text)) | ALLOWED_NUMBERS
    for n in sorted(set(re.findall(r"\d+", prose))):
        if n not in known:
            problems.append(f"number '{n}' is not in the kickoff files")

    words = len(prose.split())
    if words > MAX_WORDS:
        problems.append(f"body has {words} words outside the questions (max {MAX_WORDS})")

    for p in problems:
        print(f"FAIL: {p}")
    print(f"open questions: {len(open_q)}, answered and left out: {len(done_q)}, body words: {words}")
    print("RESULT: PASS" if not problems else "RESULT: FAIL")
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
