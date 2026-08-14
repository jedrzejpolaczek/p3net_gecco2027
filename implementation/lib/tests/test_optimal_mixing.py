"""
TODO:
- Test a full sweep visits every linkage subset in the current tree, in
  random order, for a given parent.
- Test proposals modify only the coordinates in the visited subset F,
  leaving all other coordinates equal to the parent's.
- Test there is no mutation path -- all variation traces back to
  donor-based crossover.

Reference: src/p3net/search_engines/p3/optimal_mixing.py;
chapters/v003/proposed_optimizer/main.tex ("Search loop" step 1, "No
mutation operator").
"""
