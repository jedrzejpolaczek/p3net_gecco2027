"""Tests for search_spaces.nas_genotype -- the concrete NAS
SearchSpace/Decoder/Validity implementation."""

import random

import pytest
from p3net.problem.genotype import Genotype

from search_spaces.nas_genotype import (
    ACTIVATIONS,
    CELL_EDGES,
    CELL_OPERATIONS,
    N_EDGES,
    ContinuousThetaBounds,
    decode_nas_genotype,
    nas_search_space,
    nas_validity,
)


def test_search_space_has_six_edges_plus_four_hyperparameters():
    space = nas_search_space()
    assert space.n == N_EDGES + 4 == 10


def test_search_space_sampling_respects_domains():
    space = nas_search_space()
    rng = random.Random(0)
    for _ in range(50):
        genotype = space.sample_uniform(rng)
        assert space.contains(genotype)
        for i in range(N_EDGES):
            assert genotype.values[i] in CELL_OPERATIONS
        assert genotype.values[N_EDGES + 2] in ACTIVATIONS  # activation coordinate


def test_discretisation_grid_is_fixed_and_stable():
    space_1 = nas_search_space()
    space_2 = nas_search_space()
    lr_grid_1 = space_1.domains[N_EDGES].values
    lr_grid_2 = space_2.domains[N_EDGES].values
    assert lr_grid_1 == lr_grid_2
    assert len(lr_grid_1) == 8


def _all_none_genotype() -> Genotype:
    return Genotype(values=("none",) * N_EDGES + (1e-3, 1e-5, "relu", False))


def _fully_connected_genotype() -> Genotype:
    return Genotype(values=("nor_conv_3x3",) * N_EDGES + (1e-3, 1e-5, "relu", False))


def test_decoder_reshapes_flat_genotype_into_named_fields():
    genotype = _fully_connected_genotype()
    config = decode_nas_genotype(genotype)
    assert config.edges == ("nor_conv_3x3",) * N_EDGES
    assert config.learning_rate == 1e-3
    assert config.weight_decay == 1e-5
    assert config.activation == "relu"
    assert config.trivial_augment is False


def test_decoder_rejects_wrong_length_genotype():
    with pytest.raises(ValueError):
        decode_nas_genotype(Genotype(values=("none",) * 3))


def test_validity_rejects_genotype_with_no_input_output_path():
    # all edges "none" -> no path from node 0 to node 3
    assert nas_validity(_all_none_genotype()) > 0


def test_validity_accepts_genotype_with_a_direct_edge():
    # edge index 3 is (0 -> 3): a direct connection, valid on its own
    values = ["none"] * N_EDGES
    values[3] = "nor_conv_3x3"
    genotype = Genotype(values=tuple(values) + (1e-3, 1e-5, "relu", False))
    assert nas_validity(genotype) <= 0


def test_validity_accepts_genotype_needing_a_multi_hop_path():
    # 0->1 (edge 0) and 1->3 (edge 4), no direct 0->3 edge
    values = ["none"] * N_EDGES
    values[0] = "skip_connect"  # 0 -> 1
    values[4] = "skip_connect"  # 1 -> 3
    genotype = Genotype(values=tuple(values) + (1e-3, 1e-5, "relu", False))
    assert nas_validity(genotype) <= 0


def test_validity_rejects_dead_end_path():
    # 0->1 only (edge 0); node 1 never reaches node 3
    values = ["none"] * N_EDGES
    values[0] = "skip_connect"  # 0 -> 1
    genotype = Genotype(values=tuple(values) + (1e-3, 1e-5, "relu", False))
    assert nas_validity(genotype) > 0


def test_cell_edges_form_a_dag_from_node_0_to_node_3():
    for src, dst in CELL_EDGES:
        assert src < dst  # DAG: every edge points "forward"


def test_continuous_theta_variant_is_genuinely_separate_not_a_search_space():
    bounds = ContinuousThetaBounds()
    # It is its own minimal dataclass, not a p3net.problem.SearchSpace --
    # proves the continuous control baseline isn't silently reusing (or
    # silently discretising within) the shared categorical SearchSpace.
    assert not hasattr(bounds, "domains")
    assert not hasattr(bounds, "sample_uniform")
    assert bounds.learning_rate_low < bounds.learning_rate_high
    assert bounds.weight_decay_low < bounds.weight_decay_high
