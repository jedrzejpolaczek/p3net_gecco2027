"""
TODO:
- Test the default StoppingRule (budget exhaustion) stops a run exactly at
  the configured budget, counting only full-evaluation calls (never
  surrogate calls) toward that budget.
- Test a custom StoppingRule (a simple synthetic one, not the paper's
  exploration-collapse criterion) can be supplied and is honoured, proving
  the protocol is genuinely pluggable rather than accidentally hardcoded.
- Test R independent repetitions run with a caller-supplied seed list and
  an identical initialization scheme across repetitions.
- Test the recorded observation dataset (H_t-style) contains exactly the
  full evaluations performed, in order, with no surrogate-only entries
  leaking in.

Reference: src/p3net/harness/runner.py; chapters/v003/results/main.tex
("Budgets, seeds, stopping", generic mechanism only).
"""
