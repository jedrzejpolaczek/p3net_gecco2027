"""
Generic search-space representation: a Cartesian product of variable domains.

Library-scope note: this module must stay domain-agnostic. The NAS-specific
instantiation (six architecture-edge dimensions + discretised training
hyperparameters, as used by the GECCO paper's JAHS-Bench-201 /
NAS-HPO-Bench-II experiments) is NOT implemented here -- it lives in
experiments/search_spaces/nas_genotype.py as a concrete user of the interface
defined in this file. Anyone using p3net on a different combinatorial +
continuous problem should be able to define their own search space here
without touching anything NAS-related.

TODO:
- Define a generic `SearchSpace` abstraction: an ordered collection of
  variable domains, each either a finite categorical set or a continuous
  range with a user-supplied discretisation policy (P3Net's own paper
  instantiates option (i): every continuous coordinate is discretised into a
  finite bin set fixed once before search, so the whole genotype is
  categorical -- but the library itself should not force that choice; the
  discretisation policy must be pluggable, not hardcoded).
- Define a `Genotype` value type over a `SearchSpace`: an assignment of one
  value per variable domain, with equality/hashing suitable for use as a
  deduplication-cache key (harness/evaluation_cache.py) and for keying
  observations in an H_t-style observation dataset.
- Genotype/SearchSpace must carry no notion of "architecture edge",
  "network", or "hyperparameter" -- those are domain vocabulary that belongs
  to a concrete SearchSpace instance a library user defines (see
  experiments/search_spaces/nas_genotype.py for the NAS example), not to the
  library's core type.

Reference (generic mechanism only -- see file header for what does NOT
belong here): chapters/v003/problem_formulation/main.tex (Formal
definition); chapters/v003/proposed_optimizer/main.tex ("Representation and
linkage tree" -- the linkage tree and optimal mixing sweep must apply
uniformly to any SearchSpace built this way, not just the NAS one).
"""
