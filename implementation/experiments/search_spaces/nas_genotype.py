"""
Concrete NAS search space: cell-graph architecture edges + discretised
training hyperparameters, implementing p3net.problem's generic
SearchSpace/Decoder/Validity interfaces.

Unverified-against-live-data note: the concrete dimensions/ranges below
(cell operations, hyperparameter ranges) are based on the *published*
description of the JAHS-Bench-201 / NAS-Bench-201 search space, not a live
query against the jahs-bench package (Stage C in ../TASKS.md hasn't run
yet). The cell topology (4 nodes, 6 edges, DAG from node 0 to node 3) is
the standard NAS-Bench-201 convention and is unlikely to be wrong; the
exact hyperparameter bounds should be double-checked once the real
benchmark package is installed.

This is the NAS-specific content that used to live directly in the
library's problem/genotype.py and problem/decoding.py before the
library/experiments split -- it depends ON p3net.problem rather than
being part of it, exactly the way any other p3net user's problem
definition would.
"""

from __future__ import annotations

from dataclasses import dataclass

from p3net.problem.genotype import CategoricalDomain, Genotype, SearchSpace, discretize_log_uniform

from search_spaces._cell_graph import N_EDGES, has_input_output_path

CELL_OPERATIONS: tuple[str, ...] = (
    "none",
    "skip_connect",
    "nor_conv_1x1",
    "nor_conv_3x3",
    "avg_pool_3x3",
)
NONE_OPERATION = "none"

# -- Training hyperparameters (Theta) ----------------------------------------

LEARNING_RATE_GRID: tuple[float, ...] = discretize_log_uniform(1e-3, 1.0, n=8)
WEIGHT_DECAY_GRID: tuple[float, ...] = discretize_log_uniform(1e-5, 1e-2, n=6)
ACTIVATIONS: tuple[str, ...] = ("relu", "hardswish", "mish")
TRIVIAL_AUGMENT: tuple[bool, ...] = (False, True)

# Genotype coordinate order: 6 architecture edges, then the 4
# hyperparameters below, in this fixed order.
HYPERPARAMETER_NAMES: tuple[str, ...] = (
    "learning_rate",
    "weight_decay",
    "activation",
    "trivial_augment",
)


def nas_search_space() -> SearchSpace:
    """The shared, discretised search space Lambda = Lambda_1 x ... x
    Lambda_6 x Theta used identically by P3Net and every other baseline
    arm except NSGANetV2's continuous-Theta control (Fairness controls) --
    entirely categorical, so it can be handed unmodified to
    p3net.search_engines.p3.linkage_tree / optimal_mixing.
    """
    edge_domains = tuple(CategoricalDomain(values=CELL_OPERATIONS) for _ in range(N_EDGES))
    theta_domains = (
        CategoricalDomain(values=LEARNING_RATE_GRID),
        CategoricalDomain(values=WEIGHT_DECAY_GRID),
        CategoricalDomain(values=ACTIVATIONS),
        CategoricalDomain(values=TRIVIAL_AUGMENT),
    )
    return SearchSpace(domains=edge_domains + theta_domains)


@dataclass(frozen=True)
class ContinuousThetaBounds:
    """The unconstrained, real-valued encoding of Theta that NSGANetV2
    would natively use (methods/nsganetv2.py's continuous control
    variant). NOT a p3net.problem.SearchSpace: P3's linkage tree requires
    a categorical genotype, and the continuous control baseline doesn't
    use the P3 engine at all (plain NSGA-II with real-valued crossover on
    these two coordinates alongside the same 6 categorical edges) -- so
    this is a deliberately separate, minimal representation, not a variant
    of the shared SearchSpace above.
    """

    learning_rate_low: float = 1e-3
    learning_rate_high: float = 1.0
    weight_decay_low: float = 1e-5
    weight_decay_high: float = 1e-2


@dataclass(frozen=True)
class NASConfiguration:
    """The Decoder's target type: a structured, benchmark-agnostic
    description of one candidate. experiments/substrates/*.py translate
    this into each benchmark's own query format -- this class itself
    knows nothing about JAHS-Bench-201's or NAS-HPO-Bench-II's APIs."""

    edges: tuple[str, ...]
    learning_rate: float
    weight_decay: float
    activation: str
    trivial_augment: bool


def decode_nas_genotype(genotype: Genotype) -> NASConfiguration:
    """D: genotype -> NASConfiguration. Pure reshaping of the flat
    categorical genotype into named fields; does not itself validate
    anything (see nas_validity)."""
    if len(genotype.values) != N_EDGES + len(HYPERPARAMETER_NAMES):
        raise ValueError(
            f"expected a {N_EDGES + len(HYPERPARAMETER_NAMES)}-coordinate NAS genotype, "
            f"got {len(genotype.values)}"
        )
    edges = tuple(genotype.values[:N_EDGES])
    learning_rate, weight_decay, activation, trivial_augment = genotype.values[N_EDGES:]
    return NASConfiguration(
        edges=edges,
        learning_rate=learning_rate,
        weight_decay=weight_decay,
        activation=activation,
        trivial_augment=trivial_augment,
    )


def nas_validity(genotype: Genotype) -> float:
    """g(x) <= 0 iff an input-output path exists through the cell graph
    (Problem Formulation: "does an input-output path exist between input
    and output of the cell"). Boolean validity expressed in the real-valued
    {-1, +1} form p3net.problem.decoding.Validity expects."""
    config = decode_nas_genotype(genotype)
    return -1.0 if has_input_output_path(config.edges, NONE_OPERATION) else 1.0
