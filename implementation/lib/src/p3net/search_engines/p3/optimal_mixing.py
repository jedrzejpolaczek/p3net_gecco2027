"""
Optimal mixing sweep (crossover on linkage subsets, no separate mutation
operator).

TODO:
- For a selected parent, visit every linkage subset in the current
  dependency model in random order.
- For each visited subset F, draw a donor from the population and propose a
  modification x' restricted to F (x'_i = x_i for all i not in F).
- This module produces *proposals* only; acceptance (surrogate- or
  real-fitness-gated) belongs to methods/p3net.py (step 3) or the P3-alone
  ablation's real-evaluation gate, not here -- keep this module
  acceptance-agnostic so both can reuse it.
- Confirm there is no separate mutation step: all variation must come from
  this sweep.
- Leave the donor-provenance question open per the paper's own unresolved
  TODO: whether a donor drawn here must come from H_t (like the parent and
  ancestor x0) or may be a transient, surrogate-only individual from earlier
  in the same sweep -- implement behind a config flag rather than hardcoding
  a silent choice, since the paper flags this as an open authorial decision.

Reference: chapters/v003/proposed_optimizer/main.tex ("Crossover", "No
mutation operator", "Search loop" step 1, "Parent, donor, and ancestor
provenance" TODO).
"""
