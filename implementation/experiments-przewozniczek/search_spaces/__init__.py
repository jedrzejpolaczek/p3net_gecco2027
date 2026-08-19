"""experiments.search_spaces -- concrete SearchSpace/Decoder/Validity
instances for this paper's NAS domain, implementing p3net.problem's
generic interfaces. Two separate genotypes, one per benchmark
(nas_genotype.py for JAHS-Bench-201, nas_hpo_bench_ii_genotype.py for
NAS-HPO-Bench-II) -- they do not share a search space; see
nas_hpo_bench_ii_genotype.py's module docstring for why."""

from search_spaces._cell_graph import CELL_EDGES, N_EDGES, N_NODES
from search_spaces.nas_genotype import (
    ACTIVATIONS,
    CELL_OPERATIONS,
    HYPERPARAMETER_NAMES,
    LEARNING_RATE_GRID,
    NONE_OPERATION,
    TRIVIAL_AUGMENT,
    WEIGHT_DECAY_GRID,
    ContinuousThetaBounds,
    NASConfiguration,
    decode_nas_genotype,
    nas_search_space,
    nas_validity,
)
from search_spaces.nas_hpo_bench_ii_genotype import (
    BATCH_SIZE_GRID,
    NASHPOBenchIIConfiguration,
    decode_nas_hpo_bench_ii_genotype,
    genotype_to_cellcode,
    nas_hpo_bench_ii_search_space,
    nas_hpo_bench_ii_validity,
)
from search_spaces.nas_hpo_bench_ii_genotype import (
    CELL_OPERATIONS as NAS_HPO_BENCH_II_CELL_OPERATIONS,
)
from search_spaces.nas_hpo_bench_ii_genotype import (
    LEARNING_RATE_GRID as NAS_HPO_BENCH_II_LEARNING_RATE_GRID,
)

__all__ = [
    "ACTIVATIONS",
    "CELL_EDGES",
    "CELL_OPERATIONS",
    "HYPERPARAMETER_NAMES",
    "LEARNING_RATE_GRID",
    "N_EDGES",
    "N_NODES",
    "NONE_OPERATION",
    "TRIVIAL_AUGMENT",
    "WEIGHT_DECAY_GRID",
    "ContinuousThetaBounds",
    "NASConfiguration",
    "decode_nas_genotype",
    "nas_search_space",
    "nas_validity",
    "BATCH_SIZE_GRID",
    "NASHPOBenchIIConfiguration",
    "NAS_HPO_BENCH_II_CELL_OPERATIONS",
    "NAS_HPO_BENCH_II_LEARNING_RATE_GRID",
    "decode_nas_hpo_bench_ii_genotype",
    "genotype_to_cellcode",
    "nas_hpo_bench_ii_search_space",
    "nas_hpo_bench_ii_validity",
]
