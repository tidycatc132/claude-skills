# About the golden outputs

`evals/<skill>/golden/<case-id>/` holds approved outputs for each output-eval case. They serve two jobs:

1. `python3 scripts/run_output_evals.py --golden` re-evaluates every assertion against them with no model call. That is a free, fast CI check that the assertions still agree with output a human approved.
2. They are the reference you diff a new real run against.

**The goldens that ship with this kit are synthetic.** The CSV and brief files were produced by running the example skills' own scripts, and the `stdout.txt` replies were written by hand to match the assertions. They bootstrap the offline check; they are not recordings of a model run.

When you adopt a skill for real:

1. Run `python3 scripts/run_output_evals.py --skill <id> --record --judge` and read what the model actually produced.
2. If it is good, keep the recorded golden (commit it). If it is not, fix the skill, not the assertions.
3. Replace the synthetic goldens for skills you keep.

Goldens are frozen once committed, like every other eval file.
