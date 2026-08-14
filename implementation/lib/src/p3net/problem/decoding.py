"""
Generic decoding/validity protocols: user-pluggable D and g.

Library-scope note: the library does not know what a genotype "means" --
only that a user-supplied decoder turns it into whatever the black-box
objective consumes, and a user-supplied validity check filters out
structurally infeasible genotypes. The NAS-specific decoder (genotype -> a
network description consumable by a benchmark adapter) and validity check
(does an input-output path exist through the cell graph) live in
../experiments/search_spaces/nas_genotype.py, not here.

TODO:
- Define a `Decoder` protocol: a callable `Genotype -> T` for whatever
  target type T a concrete problem needs (a network description, a
  configuration dict, anything). The library's search engines and
  surrogates must never depend on T's shape.
- Define a `Validity` protocol: a callable `Genotype -> float` returning a
  structural feasibility score, valid iff the score is <= 0 (boolean
  feasibility is the common case: g(x) in {-1, +1}; expressed in real-valued
  form so a graded infeasibility measure can be used if a concrete problem
  defines one).
- Define the generic valid-genotype filter given a SearchSpace and a
  Validity callable (analogous to Lambda* = {x in Lambda : g(x) <= 0} in
  the paper, but generic over any SearchSpace).
- Ensure the search loop contract (methods/p3net.py) rejects invalid
  candidates prior to surrogate scoring, regardless of what the concrete
  Validity implementation checks.

Reference (generic mechanism only): chapters/v003/problem_formulation/
main.tex ("Decoding and validity"); chapters/v003/proposed_optimizer/
main.tex ("Constraint handling"). Concrete NAS instantiation:
../experiments/search_spaces/nas_genotype.py.
"""
