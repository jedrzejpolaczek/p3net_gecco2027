"""Tests for search_spaces.nas_hpo_bench_ii_genotype -- NAS-HPO-Bench-II's
own real search space (4 ops, learning_rate x batch_size), distinct from
search_spaces/nas_genotype.py's JAHS-Bench-201-oriented 10-dim genotype.
Cross-checked against the real downloaded benchmark data where possible.
(Gap in the original task list -- adding it.)
"""

import random

import pytest
from p3net.problem.genotype import Genotype

from search_spaces._cell_graph import CELL_EDGES, N_EDGES
from search_spaces.nas_hpo_bench_ii_genotype import (
    BATCH_SIZE_GRID,
    CELL_OPERATIONS,
    LEARNING_RATE_GRID,
    NONE_OPERATION,
    decode_nas_hpo_bench_ii_genotype,
    genotype_to_cellcode,
    nas_hpo_bench_ii_search_space,
    nas_hpo_bench_ii_validity,
)


def test_search_space_has_six_edges_plus_two_hyperparameters():
    space = nas_hpo_bench_ii_search_space()
    assert space.n == N_EDGES + 2 == 8


def test_only_four_operations_not_five():
    assert len(CELL_OPERATIONS) == 4
    assert "nor_conv_1x1" not in CELL_OPERATIONS


def test_search_space_sampling_respects_domains():
    space = nas_hpo_bench_ii_search_space()
    rng = random.Random(0)
    for _ in range(50):
        genotype = space.sample_uniform(rng)
        assert space.contains(genotype)
        for i in range(N_EDGES):
            assert genotype.values[i] in CELL_OPERATIONS
        assert genotype.values[N_EDGES] in LEARNING_RATE_GRID
        assert genotype.values[N_EDGES + 1] in BATCH_SIZE_GRID


def test_learning_rate_grid_matches_the_real_dataset_exactly():
    assert LEARNING_RATE_GRID == (0.003125, 0.00625, 0.0125, 0.025, 0.05, 0.1, 0.2, 0.4)


def test_batch_size_grid_matches_the_real_dataset_exactly():
    assert BATCH_SIZE_GRID == (16, 32, 64, 128, 256, 512)


def _all_none_genotype() -> Genotype:
    return Genotype(values=(NONE_OPERATION,) * N_EDGES + (0.1, 256))


def test_decoder_reshapes_flat_genotype_into_named_fields():
    values = ("nor_conv_3x3",) * N_EDGES + (0.1, 256)
    config = decode_nas_hpo_bench_ii_genotype(Genotype(values=values))
    assert config.edges == ("nor_conv_3x3",) * N_EDGES
    assert config.learning_rate == 0.1
    assert config.batch_size == 256


def test_decoder_rejects_wrong_length_genotype():
    with pytest.raises(ValueError):
        decode_nas_hpo_bench_ii_genotype(Genotype(values=(NONE_OPERATION,) * 3))


def test_validity_rejects_genotype_with_no_input_output_path():
    assert nas_hpo_bench_ii_validity(_all_none_genotype()) > 0


def test_validity_accepts_genotype_with_a_direct_edge():
    values = [NONE_OPERATION] * N_EDGES
    values[3] = "nor_conv_3x3"  # edge index 3 is (0 -> 3): direct connection
    genotype = Genotype(values=tuple(values) + (0.1, 256))
    assert nas_hpo_bench_ii_validity(genotype) <= 0


def test_cell_edges_are_shared_with_nas_genotype():
    # same topology as search_spaces.nas_genotype -- only the operation
    # vocabulary and hyperparameters differ between the two benchmarks.
    assert CELL_EDGES == ((0, 1), (0, 2), (1, 2), (0, 3), (1, 3), (2, 3))


# -- genotype_to_cellcode -------------------------------------------------


def test_genotype_to_cellcode_matches_the_real_apis_string_format():
    edges = ("nor_conv_3x3", "avg_pool_3x3", "skip_connect", "none", "nor_conv_3x3", "none")
    cellcode = genotype_to_cellcode(edges)
    assert cellcode.count("|") == 2
    a, bc, def_ = cellcode.split("|")
    assert len(a) == 1 and len(bc) == 2 and len(def_) == 3


def test_genotype_to_cellcode_all_none_is_the_real_all_zero_disconnected_code():
    # Empirically verified against the real API (see module docstring):
    # cellcode '3|33|333' is the fully-disconnected, chance-level-accuracy
    # network -- confirming digit 3 (not 0) is the null operation here.
    edges = (NONE_OPERATION,) * N_EDGES
    assert genotype_to_cellcode(edges) == "3|33|333"


def test_genotype_to_cellcode_round_trips_every_operation_to_a_valid_digit():
    for op in CELL_OPERATIONS:
        edges = (op,) * N_EDGES
        cellcode = genotype_to_cellcode(edges)
        digits = cellcode.replace("|", "")
        assert all(d in "0123" for d in digits)


@pytest.mark.skipif(
    not __import__("pathlib").Path("data/cache/nashpobench2/bench12.pkl").exists(),
    reason="real NAS-HPO-Bench-II data not downloaded in this environment",
)
def test_generated_cellcodes_are_all_real_queryable_keys():
    """Cross-check against the real downloaded dataset: every cellcode
    genotype_to_cellcode can produce must be one of the API's own
    enumerated cellcodes (not just syntactically shaped like one)."""
    from nashpobench2api import NASHPOBench2API as API

    api = API("data/cache/nashpobench2", verbose=False)
    space = nas_hpo_bench_ii_search_space()
    rng = random.Random(0)
    for _ in range(20):
        genotype = space.sample_uniform(rng)
        config = decode_nas_hpo_bench_ii_genotype(genotype)
        cellcode = genotype_to_cellcode(config.edges)
        assert cellcode in api.cellcodes
        assert config.learning_rate in api.lrs
        assert config.batch_size in api.batch_sizes
