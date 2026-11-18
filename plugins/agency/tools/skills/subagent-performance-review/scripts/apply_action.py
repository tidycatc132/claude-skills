#!/usr/bin/env python3
"""Apply the review verdict to the sub-agent definition files.

Usage:
  python3 scripts/apply_action.py --review review_NAME.json --agents-dir DIR
          [--action VERDICT] [--body FILE] [--description TEXT] [--new-role NAME] [--into NAME]

Definition files are DIR/NAME.md with YAML frontmatter (name, description, tools,
model) and a system-prompt body. What each action does to the files:

  insufficient_data, retain  nothing
  improvement_plan  replaces the body with --body if given, then appends a
                    "## Performance improvement plan" section (findings, exit
                    criteria, re-review date); writes pip_NAME.md next to the review
  reassign          sets description to --description (required); --body optional
  replace           moves DIR/NAME.md to DIR/retired/NAME.AS_OF.md and writes a new
                    DIR/NAME.md with the same name, tools and model, --description
                    (or the old one) and --body (required)
  promote           writes DIR/NEW_ROLE.md (--new-role and --description required,
                    body from --body or the current definition); DIR/NAME.md stays in
                    place, so the old position remains filled
  merge             appends this agent's scope (or --description) to DIR/INTO.md's
                    description (--into required) and retires DIR/NAME.md

Every run appends one entry to review_actions.json next to the review file.
Standard library only. Exit codes: 0 ok, 1 bad input or missing file.
"""
import argparse
import datetime as dt
import json
import os
import shutil
import sys

ACTIONS = {"insufficient_data", "retain", "improvement_plan", "reassign", "replace", "promote", "merge"}


def read_definition(path):
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    if not text.startswith("---"):
        sys.exit(f"error: {path} has no YAML frontmatter")
    parts = text.split("\n---", 1)
    if len(parts) < 2:
        sys.exit(f"error: {path} frontmatter is not closed")
    fm_lines = parts[0].splitlines()[1:]
    body = parts[1].lstrip("\n")
    fm = []
    for line in fm_lines:
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            fm.append([k.strip(), v.strip()])
        elif fm:
            fm[-1][1] += "\n" + line
    return fm, body


def write_definition(path, fm, body):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    lines = ["---"] + [f"{k}: {v}" for k, v in fm] + ["---", ""]
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + body.rstrip("\n") + "\n")


def fm_get(fm, key, default=""):
    for k, v in fm:
        if k == key:
            return v
    return default


def fm_set(fm, key, value):
    for item in fm:
        if item[0] == key:
            item[1] = value
            return
    fm.append([key, value])


def read_file(path):
    if not os.path.exists(path):
        sys.exit(f"error: file not found: {path}")
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def pip_section(review):
    lines = [f"## Performance improvement plan (opened {review['as_of']}, re-review {review['re_review_date']})", "",
             "Findings from the last review:"]
    lines += [f"- {f}" for f in review.get("findings", [])] or ["- composite below 70 with no single dominant weakness"]
    lines += ["", "Exit criteria at re-review:",
              "- composite score 70 or higher over the next window",
              "- no fabrication and no scope violations in any dispatch",
              "- first-pass acceptance 70% or higher",
              "", "If the exit criteria are not met the definition is replaced."]
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--review", required=True)
    ap.add_argument("--agents-dir", required=True)
    ap.add_argument("--action", choices=sorted(ACTIONS), help="override the review verdict (recorded as an override)")
    ap.add_argument("--body", help="file holding the new system-prompt body")
    ap.add_argument("--description", help="new description text for the definition that changes")
    ap.add_argument("--new-role", help="promote: name of the new role file")
    ap.add_argument("--into", help="merge: name of the agent that absorbs this one")
    args = ap.parse_args()

    review = json.loads(read_file(args.review))
    agent = review["agent"]
    as_of = review.get("as_of") or dt.date.today().isoformat()
    action = args.action or review["verdict"]
    override = bool(args.action) and args.action != review["verdict"]
    adir = args.agents_dir
    path = os.path.join(adir, f"{agent}.md")
    entry = {"as_of": as_of, "agent": agent, "action": action, "verdict": review["verdict"], "override": override,
             "changed": [], "created": [], "retired": [], "re_review_date": review.get("re_review_date")}

    if action in ("insufficient_data", "retain"):
        pass
    elif action == "improvement_plan":
        fm, body = read_definition(path)
        if args.body:
            body = read_file(args.body)
        body = body.rstrip("\n") + "\n\n" + pip_section(review)
        write_definition(path, fm, body)
        pip_path = os.path.join(os.path.dirname(os.path.abspath(args.review)), f"pip_{agent}.md")
        with open(pip_path, "w", encoding="utf-8") as fh:
            fh.write(f"# Performance improvement plan: {agent}\n\nVerdict: improvement_plan (composite {review['composite']})\n"
                     f"Reason: {review.get('verdict_reason','')}\n\n" + pip_section(review)
                     + f"\nInstructions {'rewritten from ' + args.body if args.body else 'kept; plan section appended'} in {path}.\n")
        entry["changed"].append(path)
        entry["created"].append(pip_path)
    elif action == "reassign":
        if not args.description:
            sys.exit("error: reassign needs --description with the narrowed scope")
        fm, body = read_definition(path)
        fm_set(fm, "description", args.description.strip())
        if args.body:
            body = read_file(args.body)
        write_definition(path, fm, body)
        entry["changed"].append(path)
    elif action == "replace":
        if not args.body:
            sys.exit("error: replace needs --body with the new system prompt")
        fm, _old = read_definition(path)
        retired = os.path.join(adir, "retired", f"{agent}.{as_of}.md")
        os.makedirs(os.path.dirname(retired), exist_ok=True)
        shutil.move(path, retired)
        if args.description:
            fm_set(fm, "description", args.description.strip())
        write_definition(path, fm, read_file(args.body))
        entry["retired"].append(retired)
        entry["created"].append(path)
    elif action == "promote":
        if not (args.new_role and args.description):
            sys.exit("error: promote needs --new-role and --description for the new role")
        fm, body = read_definition(path)
        new_fm = [[k, v] for k, v in fm]
        fm_set(new_fm, "name", args.new_role)
        fm_set(new_fm, "description", args.description.strip())
        new_path = os.path.join(adir, f"{args.new_role}.md")
        if os.path.exists(new_path):
            sys.exit(f"error: {new_path} already exists")
        write_definition(new_path, new_fm, read_file(args.body) if args.body else body)
        entry["created"].append(new_path)
        entry["backfill"] = f"{path} left in place; the position stays filled by the same definition"
    elif action == "merge":
        if not args.into:
            sys.exit("error: merge needs --into NAME")
        fm, _body = read_definition(path)
        tpath = os.path.join(adir, f"{args.into}.md")
        tfm, tbody = read_definition(tpath)
        extra = (args.description or fm_get(fm, "description")).strip()
        fm_set(tfm, "description", (fm_get(tfm, "description") + " Also covers, merged from " + agent + ": " + extra).strip())
        write_definition(tpath, tfm, tbody)
        retired = os.path.join(adir, "retired", f"{agent}.{as_of}.md")
        os.makedirs(os.path.dirname(retired), exist_ok=True)
        shutil.move(path, retired)
        entry["changed"].append(tpath)
        entry["retired"].append(retired)

    log_path = os.path.join(os.path.dirname(os.path.abspath(args.review)), "review_actions.json")
    log = json.loads(read_file(log_path)) if os.path.exists(log_path) else []
    log.append(entry)
    with open(log_path, "w", encoding="utf-8") as fh:
        json.dump(log, fh, indent=2)
    print(f"ACTION: {action}" + (" (override of verdict %s)" % review["verdict"] if override else ""))
    for k in ("changed", "created", "retired"):
        for p in entry[k]:
            print(f"{k}: {p}")
    if entry.get("backfill"):
        print(entry["backfill"])
    print(f"logged in {log_path}")


if __name__ == "__main__":
    main()
