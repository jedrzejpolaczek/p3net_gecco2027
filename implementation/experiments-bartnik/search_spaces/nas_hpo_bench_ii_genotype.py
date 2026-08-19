"""
Concrete NAS-HPO-Bench-II search space: the SAME six-edge cell topology
as search_spaces/nas_genotype.py (search_spaces/_cell_graph.py), but with
NAS-HPO-Bench-II's own real operation vocabulary and hyperparameter grid
-- which differ from what nas_genotype.py assumes, because that module
targets JAHS-Bench-201 specifically (chapters/v003/related_work/main.tex
documents the two benchmarks as having different hyperparameter axes;
Stage B's implementation mistakenly reused one shared genotype for both,
caught while wiring real NAS-HPO-Bench-II queries).

Verified against the real downloaded benchmark data
(data/cache/nashpobench2/, loaded via substrates/nas_hpo_bench_ii.py),
not just the published description:

- 4 cell operations, not 5 -- NAS-HPO-Bench-II explicitly excludes the
  1x1 convolution NAS-Bench-201 has.
- The null/zero operation is cellcode digit "3", NOT digit "0" as in
  plain NAS-Bench-201's usual convention. Confirmed empirically, not
  assumed: querying cellcode '3|33|333' (every edge set to digit 3)
  against the real data scores ~9.7% accuracy -- chance level for this
  10-class task, i.e. a fully disconnected input-output graph -- while
  every other single-digit-repeated cellcode ('0|00|000', '1|11|111',
  '2|22|222') scores far above chance.
- The three non-null operations' exact digit<->name correspondence
  (skip_connect / nor_conv_3x3 / avg_pool_3x3) is INFERRED from each
  digit's average training cost in the real data (skip_connect having
  ~0 compute cost, then avg_pool_3x3, then nor_conv_3x3 as the most
  expensive, is a standard, well-established ordering for these
  operation types) -- not independently confirmed against the
  benchmark's own source, which treats cellcode digits as opaque
  integers and exposes no semantic label mapping. This labelling does
  NOT affect search correctness: P3Net and every other arm treat this
  as an opaque 4-valued categorical domain regardless of which name is
  attached to which digit.
- learning_rate / batch_size grids are copied verbatim from the loaded
  dataset (api.lrs / api.batch_sizes), not re-derived analytically.

Reference: chapters/v003/related_work/main.tex ("NAS-HPO-Bench-II...
varies only learning rate and batch size as hyperparameters").
"""

from __future__ import annotations

from dataclasses import dataclass

from p3net.problem.genotype import CategoricalDomain, Genotype, SearchSpace

from search_spaces._cell_graph import N_EDGES, has_input_output_path

CELL_OPERATIONS: tuple[str, ...] = ("nor_conv_3x3", "avg_pool_3x3", "skip_connect", "none")
"""Index order matches NAS-HPO-Bench-II's own cellcode digit order (0-3)
-- see module docstring for how this was determined."""
NONE_OPERATION = "none"

LEARNING_RATE_GRID: tuple[float, ...] = (0.003125, 0.00625, 0.0125, 0.025, 0.05, 0.1, 0.2, 0.4)
BATCH_SIZE_GRID: tuple[int, ...] = (16, 32, 64, 128, 256, 512)

HYPERPARAMETER_NAMES: tuple[str, ...] = ("learning_rate", "batch_size")


def nas_hpo_bench_ii_search_space() -> SearchSpace:
    """The real Lambda x Theta for NAS-HPO-Bench-II: six categorical
    architecture edges (4 ops each) x learning_rate x batch_size -- eight
    dimensions total, NOT the ten-dimensional genotype
    search_spaces/nas_genotype.py assumes for JAHS-Bench-201. Every arm
    run against this benchmark shares this exact search space (Fairness
    controls, scoped to this benchmark)."""
    edge_domains = tuple(CategoricalDomain(values=CELL_OPERATIONS) for _ in range(N_EDGES))
    theta_domains = (
        CategoricalDomain(values=LEARNING_RATE_GRID),
        CategoricalDomain(values=BATCH_SIZE_GRID),
    )
    return SearchSpace(domains=edge_domains + theta_domains)


@dataclass(frozen=True)
class NASHPOBenchIIConfiguration:
    """The Decoder's target type for this benchmark -- structured,
    NAS-HPO-Bench-II-specific (unlike the shared NASConfiguration in
    nas_genotype.py, this benchmark's real config shape genuinely has
    fewer fields, not just a different name)."""

    edges: tuple[str, ...]
    learning_rate: float
    batch_size: int


def decode_nas_hpo_bench_ii_genotype(genotype: Genotype) -> NASHPOBenchIIConfiguration:
    """D: genotype -> NASHPOBenchIIConfiguration. Pure reshaping; does not
    itself validate anything (see nas_hpo_bench_ii_validity)."""
    if len(genotype.values) != N_EDGES + len(HYPERPARAMETER_NAMES):
        raise ValueError(
            f"expected a {N_EDGES + len(HYPERPARAMETER_NAMES)}-coordinate NAS-HPO-Bench-II "
            f"genotype, got {len(genotype.values)}"
        )
    edges = tuple(genotype.values[:N_EDGES])
    learning_rate, batch_size = genotype.values[N_EDGES:]
    return NASHPOBenchIIConfiguration(
        edges=edges, learning_rate=learning_rate, batch_size=batch_size
    )


def nas_hpo_bench_ii_validity(genotype: Genotype) -> float:
    """g(x) <= 0 iff an input-output path exists through the cell graph,
    same rule as nas_genotype.nas_validity, scoped to this benchmark's
    own operation vocabulary and null-operation value."""
    config = decode_nas_hpo_bench_ii_genotype(genotype)
    return -1.0 if has_input_output_path(config.edges, NONE_OPERATION) else 1.0


def genotype_to_cellcode(edges: tuple[str, ...]) -> str:
    """Encodes edges into NAS-HPO-Bench-II's own cellcode string format
    'A|BC|DEF' (digit indices into CELL_OPERATIONS, in CELL_EDGES
    order) -- the exact key substrates/nas_hpo_bench_ii.py passes to
    NASHPOBench2API.query_by_key(cellcode=...)."""
    indices = [str(CELL_OPERATIONS.index(op)) for op in edges]
    return f"{indices[0]}|{indices[1]}{indices[2]}|{indices[3]}{indices[4]}{indices[5]}"
