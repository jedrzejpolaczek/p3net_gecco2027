"""Architecture-only NAS-Bench-201 search space: the six cell-graph edges
alone, no Theta (hyperparameter) dimension -- a mirror of
search_spaces/nas_genotype.py with the training-hyperparameter half
removed.

Built for the isolation experiment (glimmering-swimming-book.md): the
closest prior work, Bartnik (bartnik2026evolutionary), showed a
surrogate-assisted linkage-learning algorithm winning on exactly this
architecture-only NAS-Bench-201 setup, while this project's own joint
architecture+hyperparameter extension does not separate from
random_search anywhere. This module exists to test P3Net on the same,
unextended search space, holding everything else (engine, surrogate)
fixed at its current, already-fixed configuration.

CELL_OPERATIONS is the same five-operation vocabulary as
search_spaces/nas_genotype.py -- both modules describe the same
underlying NAS-Bench-201 cell family, so the operation names must match
exactly for genotype_to_arch_str's output to be valid nats_bench input.
"""

from __future__ import annotations

from dataclasses import dataclass

from p3net.problem.genotype import CategoricalDomain, Genotype, SearchSpace

from search_spaces._cell_graph import CELL_EDGES, N_EDGES, has_input_output_path

CELL_OPERATIONS: tuple[str, ...] = (
    "none",
    "skip_connect",
    "nor_conv_1x1",
    "nor_conv_3x3",
    "avg_pool_3x3",
)
NONE_OPERATION = "none"


def nas_bench_201_search_space() -> SearchSpace:
    """Lambda = Lambda_1 x ... x Lambda_6, architecture edges only -- no
    Theta domains appended, unlike nas_genotype.nas_search_space()."""
    edge_domains = tuple(CategoricalDomain(values=CELL_OPERATIONS) for _ in range(N_EDGES))
    return SearchSpace(domains=edge_domains)


@dataclass(frozen=True)
class NASBench201Configuration:
    """The Decoder's target type: just the six edges, no hyperparameter
    fields -- substrates/nas_bench_201.py translates this into nats_bench's
    own arch-string query format via genotype_to_arch_str below."""

    edges: tuple[str, ...]


def decode_nas_bench_201_genotype(genotype: Genotype) -> NASBench201Configuration:
    """D: genotype -> NASBench201Configuration. Pure reshaping; does not
    itself validate anything (see nas_bench_201_validity)."""
    if len(genotype.values) != N_EDGES:
        raise ValueError(f"expected a {N_EDGES}-coordinate architecture-only genotype, got {len(genotype.values)}")
    return NASBench201Configuration(edges=tuple(genotype.values))


def nas_bench_201_validity(genotype: Genotype) -> float:
    """g(x) <= 0 iff an input-output path exists through the cell graph,
    same rule as nas_genotype.nas_validity, expressed in the same
    {-1, +1} form p3net.problem.decoding.Validity expects."""
    config = decode_nas_bench_201_genotype(genotype)
    return -1.0 if has_input_output_path(config.edges, NONE_OPERATION) else 1.0


def genotype_to_arch_str(edges: tuple[str, ...]) -> str:
    """Translate this project's flat 6-edge tuple into the arch-string
    format nats_bench.api_topology.NATStopology.query_index_by_arch (and
    the wider NAS-Bench-201 ecosystem) expects: one '|op~from_node|'
    group per destination node, groups joined by '+'. Verified directly
    against nats_bench.genotype_utils.TopologyStructure.tostr()'s own
    source (glimmering-swimming-book.md, Faza 0): for destination node
    i (i=1,2,3), the group lists every edge (op, from_node) landing on
    it, in from_node order -- exactly the grouping _cell_graph.CELL_EDGES
    already encodes: node 1 <- edge 0; node 2 <- edges 1,2; node 3 <-
    edges 3,4,5."""
    if len(edges) != N_EDGES:
        raise ValueError(f"expected {N_EDGES} edges, got {len(edges)}")
    by_destination: dict[int, list[str]] = {}
    for (src, dst), op in zip(CELL_EDGES, edges):
        by_destination.setdefault(dst, []).append(f"{op}~{src}")
    groups = ["|" + "|".join(by_destination[dst]) + "|" for dst in sorted(by_destination)]
    return "+".join(groups)
