"""
delta_hat_F: relative, linkage-aware surrogate (P3Net's own contribution).

TODO:
- Implement delta_hat_F: Lambda* x Lambda* -> R, predicting f1(x) - f1(x')
  for a parent x and a candidate x' differing from x only on the
  coordinates of linkage subset F.
- Train on pairwise fitness differences derived from H_t (the observation
  dataset of full evaluations so far), retrained after every round of full
  evaluations.
- Mechanistically: regression on continuous fitness differences (closer to
  CS-GOMEA's relative surrogate), not eLyMPuS's discrete
  better/worse/ambiguous comparison -- do not implement a
  discrete-comparison output by mistake.
- No formal recovery guarantee applies here (eLyMPuS's
  monotonicity-conditional guarantee does not transfer to NN fitness) --
  treat as a learned heuristic estimator only; do not implement or advertise
  a correctness bound.
- This is what P3's optimal mixing sweep queries at every proposed
  modification (search_engines/p3/optimal_mixing.py output).

Reference: chapters/v003/problem_formulation/main.tex ("Surrogate model");
chapters/v003/proposed_optimizer/main.tex ("Surrogate", "Design rationale
(adapted from eLyMPuS)"); chapters/v003/related_work/main.tex
(eLyMPuS/CS-GOMEA lineage paragraph).
"""
