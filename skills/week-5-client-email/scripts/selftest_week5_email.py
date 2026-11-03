#!/usr/bin/env python3
"""Self-test for week5_email.py. Run from the repo root: python3 skills/week-5-client-email/scripts/selftest_week5_email.py"""
from __future__ import annotations

import contextlib
import datetime as dt
import io
import json
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import week5_email as W  # noqa: E402

REPO = HERE.parents[2]
FIX = REPO / "fixtures" / "week-5-client-email"
QF = REPO / "fixtures" / "staging-site-qa" / "quillfeather" / "after-fixes" / "qa" / "quillfeather-plumbing" / "quillfeather-plumbing-staging-qa-2026-10-27.md"
results = []


def ok(name, cond):
    results.append((name, bool(cond)))


def run(argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
        code = W.main(argv)
    return code, buf.getvalue()


def workdir(src: str) -> Path:
    t = Path(tempfile.mkdtemp())
    shutil.copytree(FIX / src, t / "w")
    return t / "w"


def put_email(root: Path, slug: str, text: str) -> Path:
    p = root / "emails" / slug / f"{slug}-week-5-email.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


def failed_rows(out: str) -> set:
    return {ln.split("|")[1].strip() for ln in out.splitlines() if "| FAIL |" in ln}


d = dt.date
ok("tue + 3 business days = fri", W.add_business_days(d(2026, 11, 10), 3) == d(2026, 11, 13))
ok("fri + 3 business days = wed", W.add_business_days(d(2026, 11, 6), 3) == d(2026, 11, 11))
ok("sat + 3 business days = wed", W.add_business_days(d(2026, 11, 7), 3) == d(2026, 11, 11))
ok("written date", W.written(d(2026, 11, 13)) == "Friday, November 13")
ok("greeting first name", W.greeting_for("Priya Raman") == "Hi Priya,")
ok("greeting with title", W.greeting_for("Dr. Lena Ortiz") == "Hi Dr. Ortiz,")

# facts
mb = workdir("marrowbrook")
code, out = run(["facts", "--slug", "marrowbrook-electric", "--root", str(mb), "--send-date", "2026-11-10", "--contact", "Priya Raman"])
ok("facts ok", code == 0)
ok("facts picks newest report", "staging-qa-2026-11-09.md (RESULT: READY)" in out)
ok("facts no warning when ready", W.WARN_PREFIX not in out)
ok("facts staging url from report", "Staging: https://marrowbrook.staging-wise.site" in out)
ok("facts voice email row", "no exclamation marks" in out)
ok("facts default go-ahead", "No-reply line: yes" in out)
code, out = run(["facts", "--slug", "marrowbrook-electric", "--root", str(mb), "--send-date", "2026-11-10", "--reply-by", "2026-11-14"])
ok("facts AM reply-by on a Saturday stops", code == 2 and "STOP" in out)
code, out = run(["facts", "--slug", "marrowbrook-electric", "--root", str(mb), "--send-date", "2026-11-10", "--reply-by", "2026-11-17"])
ok("facts AM reply-by kept", code == 0 and "Reply by: 2026-11-17" in out and "Reply-by rule: AM's date" in out)
code, out = run(["facts", "--slug", "nobody", "--root", str(mb)])
ok("facts stops without context", code == 2 and "new-build-kickoff" in out)
shutil.rmtree(mb / "qa")
code, out = run(["facts", "--slug", "marrowbrook-electric", "--root", str(mb)])
ok("facts stops without any staging URL", code == 2 and "staging URL" in out)
code, out = run(["facts", "--slug", "marrowbrook-electric", "--root", str(mb), "--staging-url", "https://mb.example.site", "--contact", "Priya Raman"])
ok("facts warns with no QA report", code == 0 and "no staging QA report found" in out)

fh = workdir("fernhollow")
code, out = run(["facts", "--slug", "fernhollow-bakery", "--root", str(fh), "--send-date", "2026-11-06", "--no-go-ahead"])
ok("facts contact from context", "Contact: Lena Ortiz" in out)
ok("facts warns NOT READY", "ends RESULT: NOT READY" in out)
ok("facts lists 2 AM items", "2 open AM items" in out and "catering menu prices" in out and "online ordering cart" in out)
ok("facts reply-by wed", "Reply by: 2026-11-11" in out)

# check: the good draft passes
mb = workdir("marrowbrook")
good = (FIX / "drafts" / "marrowbrook-electric-week-5-email.md").read_text(encoding="utf-8")
p = put_email(mb, "marrowbrook-electric", good)
code, out = run(["check", str(p)])
ok("good draft passes", code == 0 and out.rstrip().endswith("RESULT: PASS"))

# check: the hand-edited draft fails on exactly the planted problems
p = put_email(mb, "marrowbrook-electric", (FIX / "drafts" / "marrowbrook-electric-week-5-email-edited.md").read_text(encoding="utf-8"))
code, out = run(["check", str(p)])
bad = failed_rows(out)
ok("edited draft fails", code == 1)
for row in ("header lines", "QA report line", "no other links", "reply-by written out", "one date only", "no internal words"):
    ok(f"edited draft: {row}", row in bad)
ok("edited draft: link check ignores trailing period", "bugherd.com/projects/marrowbrook." not in out)

# check: mutations of the good draft
def mutate(old, new, row, slug="marrowbrook-electric", root=mb, base=good):
    q = put_email(root, slug, base.replace(old, new))
    c, o = run(["check", str(q)])
    ok(f"mutation caught: {row}", c == 1 and row in failed_rows(o))

mutate("Password: [AM: paste the staging password here]", "Password: Volt-Ridge-88", "password placeholder")
mutate("Edits by: reply or BugHerd", "Edits by: reply", "BugHerd mention")
mutate("No-reply line: yes", "No-reply line: dropped", "no-reply line")
mutate("Reply by: 2026-11-13", "Reply by: 2026-11-12", "reply-by date")
mutate("Hi Priya,", "Hello there,", "greeting")
mutate("Account Manager, WISE Digital Partners", "WISE", "sign-off")
mutate("This is the last check before launch. ", "", "last check before launch")
mutate("services and contact details", "and services", "what to look at")
mutate("Your new Marrowbrook", "Our PM says your new Marrowbrook", "no internal words")
mutate("for a final look", "after our punch list", "no internal words")
mutate("Thanks,\n", ("word " * 60) + "\nThanks,\n", "body under 150 words")
mutate("Client: Marrowbrook Electric\n", "WARNING (not part of the email): something\n\nClient: Marrowbrook Electric\n", "warnings above the email")

# a NOT READY report requires the warnings
fh = workdir("fernhollow")
fgood = good.replace("Marrowbrook Electric", "Fernhollow Bakery").replace("marrowbrook-electric", "fernhollow-bakery") \
    .replace("marrowbrook.staging-wise.site", "fernhollow.staging-wise.site").replace("Priya Raman", "Lena Ortiz").replace("Hi Priya,", "Hi Lena,") \
    .replace("staging-qa-2026-11-09.md (RESULT: READY)", "staging-qa-2026-11-05.md (RESULT: NOT READY)")
q = put_email(fh, "fernhollow-bakery", fgood)
c, o = run(["check", str(q)])
ok("NOT READY without warnings fails", c == 1 and "warnings above the email" in failed_rows(o))
_, facts_out = run(["facts", "--slug", "fernhollow-bakery", "--root", str(fh), "--send-date", "2026-11-10", "--contact", "Lena Ortiz", "--protected", "--bugherd"])
block = facts_out.split("-----\n")[1]
warn_part = block.split("\nClient:")[0].rstrip("\n") + "\n\n"
q = put_email(fh, "fernhollow-bakery", warn_part + fgood)
c, o = run(["check", str(q)])
ok("NOT READY with copied warnings passes", c == 0)

# contracts
code, out = run(["contract", "qa", str(QF)])
data = json.loads(out)
ok("contract qa reads staging-site-qa report", code == 0 and data["RESULT:"] == "NOT READY" and data["Staging:"] == "https://quillfeather.staging-wise.site" and data["## AM Items"] == [])
code, out = run(["contract", "email", str(FIX / "drafts" / "marrowbrook-electric-week-5-email.md")])
ok("contract email header", json.loads(out) == {"Client:": "Marrowbrook Electric", "Send date:": "2026-11-10", "Reply by:": "2026-11-13"})
tmp = Path(tempfile.mkdtemp()) / "x.json"
tmp.write_text(json.dumps({"Client:": "X", "Send date:": "2026-11-10"}))
code, _ = run(["contract", "--validate", str(tmp)])
ok("contract validate rejects missing key", code == 1)

bad = [n for n, r in results if not r]
for n, r in results:
    if not r:
        print(f"FAIL {n}")
print(f"selftest: {len(results) - len(bad)}/{len(results)} passed")
sys.exit(1 if bad else 0)
