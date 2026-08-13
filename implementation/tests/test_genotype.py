"""
TODO:
- Test generic SearchSpace construction from arbitrary categorical (and,
  where a discretisation policy is supplied, continuous) variable domains --
  must not assume NAS semantics; use a small synthetic search space, not the
  NAS one.
- Test a caller-supplied discretisation policy is applied once and stays
  stable.
- Test Genotype equality/hashing used by the deduplication cache.
- The NAS-specific instantiation (experiments/search_spaces/nas_genotype.py)
  gets its own test at experiments/tests/test_nas_search_space.py -- do not
  duplicate NAS-specific assertions here.

Reference: src/p3net/problem/genotype.py;
chapters/v003/problem_formulation/main.tex (generic mechanism only).
"""
