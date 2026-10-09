# About the golden outputs

`evals/<skill>/golden/<case-id>/` holds approved outputs for each output-eval case. They serve two jobs:

1. `python3 scripts/run_output_evals.py --golden` re-evaluates every assertion against them with no model call. That is a free, fast CI check that the assertions still agree with output a human approved.
2. They are the reference you diff a new real run against.

How a golden comes to exist:

1. Run `python3 scripts/run_output_evals.py --skill <id> --record --judge` and read what the model actually produced.
2. If it is good, keep the recorded golden (commit it). If it is not, fix the skill, not the assertions.
3. Never write a golden by hand to match the assertions; it must be a recording of a real run.

Goldens are frozen once committed, like every other eval file.
