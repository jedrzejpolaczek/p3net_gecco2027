"""
Absolute regressor surrogate (NSGANetV2-style; also used by the P3+absolute
ablation).

TODO:
- Implement an absolute regressor predicting f1(x) directly from the full
  genotype encoding (not relative to a parent, not linkage-aware).
- Used by two arms: methods/nsganetv2.py (paired with NSGA-II) and
  methods/p3_absolute.py (paired with P3, isolating the linkage-aware-
  surrogate contribution from the search-engine contribution).
- Keep the model family swappable/consistent between both arms, since the
  ablation's validity depends on the *only* difference between them being
  the search engine.

Reference: chapters/v003/results/main.tex ("Baselines" -- "P3 with an
absolute regressor surrogate... isolating the contribution of the linkage
aware design from the contribution of the P3 engine itself").
"""
