PY ?= python3

.PHONY: init check selftest triggers outputs golden package

init:        ## session-start ritual
	bash init.sh

check:       ## cheap gates (what the Stop hook runs)
	$(PY) scripts/validate_skill.py --all --strict --quiet
	$(PY) scripts/check_contracts.py --all
	$(PY) scripts/check_overlap.py --quiet
	$(PY) scripts/check_backlog.py --against-git

selftest:    ## do the sensors fire on known-bad input?
	$(PY) scripts/selftest.py

triggers:    ## real routing evals (needs the claude CLI, costs tokens)
	$(PY) scripts/run_trigger_evals.py --runs 2

outputs:     ## real output evals with the LLM judge (needs the claude CLI, costs tokens)
	$(PY) scripts/run_output_evals.py --judge

golden:      ## offline: assertions against recorded golden outputs (free, CI-friendly)
	$(PY) scripts/run_output_evals.py --golden

package:     ## build dist/*.zip and dist/*.skill for every skill that passes the gates
	$(PY) scripts/package_skill.py --all
