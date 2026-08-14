"""p3net -- a linkage-learning search engine (P3) paired with a relative,
linkage-aware surrogate, for black-box combinatorial (+ optionally
discretised-continuous) optimisation problems.

This is the public API surface. Anything not re-exported here is an
implementation detail that downstream consumers (e.g. the sibling
experiments package) should not depend on directly.
"""

from p3net.harness import (
    EvaluationCache,
    Method,
    Observation,
    Runner,
    RunState,
    SeedPolicy,
    StoppingRule,
)
from p3net.methods import P3Net
from p3net.metrics import hypervolume, hypervolume_relative_to_best_known_front, igd_plus
from p3net.problem import (
    CategoricalDomain,
    Decoder,
    FidelityLadder,
    FidelityLevel,
    Genotype,
    Objectives,
    SearchSpace,
    Validity,
    discretize_linear,
    discretize_log_uniform,
    dominates,
    evaluate_with_noise,
    is_valid,
    pareto_front,
    valid_subset,
)
from p3net.search_engines.p3 import (
    LinkageNode,
    Proposal,
    Pyramid,
    PyramidLevel,
    SweepState,
    build_linkage_tree,
    linkage_subsets,
    propose_modification,
)
from p3net.surrogates import (
    AbsoluteRegressorSurrogate,
    AncestorNotEvaluatedError,
    ChainStep,
    NoLinkageTreeError,
    RelativeLinkageAwareSurrogate,
    telescoped_estimate,
)

__all__ = [
    "P3Net",
    # problem
    "CategoricalDomain",
    "Decoder",
    "FidelityLadder",
    "FidelityLevel",
    "Genotype",
    "Objectives",
    "SearchSpace",
    "Validity",
    "discretize_linear",
    "discretize_log_uniform",
    "dominates",
    "evaluate_with_noise",
    "is_valid",
    "pareto_front",
    "valid_subset",
    # search_engines.p3
    "LinkageNode",
    "Proposal",
    "Pyramid",
    "PyramidLevel",
    "SweepState",
    "build_linkage_tree",
    "linkage_subsets",
    "propose_modification",
    # surrogates
    "AbsoluteRegressorSurrogate",
    "AncestorNotEvaluatedError",
    "ChainStep",
    "NoLinkageTreeError",
    "RelativeLinkageAwareSurrogate",
    "telescoped_estimate",
    # harness
    "EvaluationCache",
    "Method",
    "Observation",
    "Runner",
    "RunState",
    "SeedPolicy",
    "StoppingRule",
    # metrics
    "hypervolume",
    "hypervolume_relative_to_best_known_front",
    "igd_plus",
]
