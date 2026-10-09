#!/usr/bin/env bash
# Session start ritual: prove the base is green before building on it.
#   bash init.sh          full check
#   bash init.sh --quick  skip the harness self-test
cd "$(dirname "$0")" || exit 1
PY="${PYTHON:-python3}"
quick=0; [ "${1:-}" = "--quick" ] && quick=1
red=0

step() { printf '\n== %s\n' "$1"; }
run()  { "$@" || red=1; }

if ! command -v "$PY" >/dev/null 2>&1; then echo "python3 not found (set PYTHON=...)"; exit 1; fi

if command -v git >/dev/null 2>&1 && [ ! -d .git ]; then
  git init -q && echo "initialized a git repository"
fi
if command -v git >/dev/null 2>&1 && ! git rev-parse --verify HEAD >/dev/null 2>&1; then
  echo "NOTE: no commits yet. Evals, fixtures and contracts are only frozen once committed:"
  echo "      git add -A && git commit -m 'Harness baseline'"
fi

if [ "$quick" -eq 0 ]; then
  step "harness self-test (do the sensors actually fire?)"
  run "$PY" scripts/selftest.py --quiet
fi

step "validate skills (strict)"
run "$PY" scripts/validate_skill.py --all --strict --quiet

step "pipeline contracts"
run "$PY" scripts/check_contracts.py --all

step "trigger overlap"
run "$PY" scripts/check_overlap.py --quiet

step "backlog"
run "$PY" scripts/check_backlog.py --against-git
"$PY" scripts/check_backlog.py --status

step "next up"
"$PY" scripts/check_backlog.py --next

echo
if [ "$red" -eq 0 ]; then echo "GREEN: safe to build."; else echo "RED: fix the above before building anything new."; fi
exit "$red"
