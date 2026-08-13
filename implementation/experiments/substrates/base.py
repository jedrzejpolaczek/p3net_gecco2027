"""
Common substrate interface: the thing that answers full evaluations of f1
for this paper's two benchmarks.

TODO:
- Define an abstract query interface: query(genotype, fidelity_level) -> f1
  value, covering both live-training-style and lookup/surrogate-style
  substrates. Genotypes come from experiments/search_spaces/nas_genotype.py;
  fidelity levels use p3net.problem's generic FidelityLadder abstraction.
- Expose the fidelity ladder r_1 < ... < r_K for the concrete benchmark,
  including any extra resource axes (e.g. input resolution) each level
  fixes.
- Expose whether the substrate answers deterministically or stochastically,
  so callers know whether p3net.problem's generic s-seed/median averaging
  path applies.
- Expose the analytic f2 (cost proxy) computation, independent of fidelity
  level -- this concrete f2 wiring is what problem/objectives.py in the
  library deliberately leaves to substrates/ (the library has no opinion on
  "parameter count" or "FLOPs" as a concept).
- Define what counts as "the full evaluation budget" cost unit for
  p3net.harness.runner: calls to f1 only, never calls to a surrogate.

Reference: chapters/v003/problem_formulation/main.tex ("Surrogate model"
preamble, "Multi fidelity evaluation"); chapters/v003/results/main.tex
("Benchmark and search space"). Generic interfaces this plugs into:
src/p3net/problem/objectives.py, harness/runner.py.
"""
