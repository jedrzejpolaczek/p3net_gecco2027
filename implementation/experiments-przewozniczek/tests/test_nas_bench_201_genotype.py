"""Tests for search_spaces.nas_bench_201_genotype -- the architecture-only
NAS-Bench-201 SearchSpace/Decoder/Validity implementation (isolation
experiment plan, glimmering-swimming-book.md, Faza 1): mirrors
search_spaces/nas_genotype.py minus the Theta (hyperparameter) domains,
plus an arch-string encoder for nats_bench's own lookup format."""

import random

import pytest
from p3net.problem.genotype import Genotype

from search_spaces._cell_graph import N_EDGES
from search_spaces.nas_bench_201_genotype import (
    CELL_OPERATIONS,
    decode_nas_bench_201_genotype,
    genotype_to_arch_str,
    nas_bench_201_search_space,
    nas_bench_201_validity,
)


def test_search_space_has_exactly_six_edges_and_nothing_else():
    space = nas_bench_201_search_space()
    assert space.n == N_EDGES == 6


def test_search_space_sampling_respects_domain():
    space = nas_bench_201_search_space()
    rng = random.Random(0)
    for _ in range(50):
        genotype = space.sample_uniform(rng)
        assert space.contains(genotype)
        for value in genotype.values:
            assert value in CELL_OPERATIONS


def _all_none_genotype() -> Genotype:
    return Genotype(values=("none",) * N_EDGES)


def _fully_connected_genotype() -> Genotype:
    return Genotype(values=("nor_conv_3x3",) * N_EDGES)


def test_decoder_reshapes_flat_genotype_into_edges_only():
    config = decode_nas_bench_201_genotype(_fully_connected_genotype())
    assert config.edges == ("nor_conv_3x3",) * N_EDGES


def test_decoder_rejects_wrong_length_genotype():
    with pytest.raises(ValueError):
        decode_nas_bench_201_genotype(Genotype(values=("none",) * 3))


def test_validity_rejects_genotype_with_no_input_output_path():
    assert nas_bench_201_validity(_all_none_genotype()) > 0


def test_validity_accepts_genotype_with_a_direct_edge():
    values = ["none"] * N_EDGES
    values[3] = "nor_conv_3x3"  # edge 3 is (0 -> 3): direct connection
    assert nas_bench_201_validity(Genotype(values=tuple(values))) <= 0


def test_validity_accepts_genotype_needing_a_multi_hop_path():
    values = ["none"] * N_EDGES
    values[0] = "skip_connect"  # 0 -> 1
    values[4] = "skip_connect"  # 1 -> 3
    assert nas_bench_201_validity(Genotype(values=tuple(values))) <= 0


def test_validity_rejects_dead_end_path():
    values = ["none"] * N_EDGES
    values[0] = "skip_connect"  # 0 -> 1 only, never reaches 3
    assert nas_bench_201_validity(Genotype(values=tuple(values))) > 0


def test_arch_str_matches_the_published_nats_bench_format_for_all_none():
    # Verified directly against nats_bench's own TopologyStructure.tostr()
    # source (genotype_utils.py): node i's entries join with "|", each
    # entry is "op~from-node-index", the whole node wrapped in "|...|",
    # and the three nodes join with "+".
    edges = ("none",) * N_EDGES
    assert genotype_to_arch_str(edges) == "|none~0|+|none~0|none~1|+|none~0|none~1|none~2|"


def test_arch_str_matches_the_published_nats_bench_format_for_mixed_ops():
    # edge order from _cell_graph.CELL_EDGES: (0,1),(0,2),(1,2),(0,3),(1,3),(2,3)
    edges = ("skip_connect", "nor_conv_1x1", "nor_conv_3x3", "none", "avg_pool_3x3", "skip_connect")
    assert genotype_to_arch_str(edges) == (
        "|skip_connect~0|"
        "+|nor_conv_1x1~0|nor_conv_3x3~1|"
        "+|none~0|avg_pool_3x3~1|skip_connect~2|"
    )


def test_arch_str_rejects_wrong_edge_count():
    with pytest.raises(ValueError):
        genotype_to_arch_str(("none",) * 3)
