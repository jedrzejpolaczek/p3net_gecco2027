"""Tests for the FCNet search space and substrate (phase 2d).

Substrate tests need the downloaded table (scripts/download_fcnet.py) and
are skipped without it."""

from __future__ import annotations

import itertools
import math
import random

import pytest
from p3net.problem.decoding import is_valid
from p3net.problem.genotype import Genotype

from methods.multi_fidelity import rung_epochs
from search_spaces.fcnet_genotype import (
    decode_fcnet_genotype,
    fcnet_search_space,
    fcnet_validity,
)
from substrates.fcnet import DEFAULT_DATA_DIR, FCNET_TASKS, FCNetSubstrate

HAS_DATA = (DEFAULT_DATA_DIR / "objectives_evaluations.npy").exists()
needs_data = pytest.mark.skipif(not HAS_DATA, reason="FCNet data not downloaded")

#: input dimension of each task's regression dataset, recovered from n_params
INPUT_DIMENSIONS = {
    "protein_structure": 9,
    "naval_propulsion": 15,
    "parkinsons_telemonitoring": 20,
    "slice_localization": 380,
}


def test_search_space_has_the_published_size_and_no_infeasible_configurations():
    space = fcnet_search_space()
    assert space.n == 9
    assert math.prod(len(d.values) for d in space.domains) == 62_208
    rng = random.Random(0)
    for _ in range(50):
        assert is_valid(space.sample_uniform(rng), fcnet_validity)


def test_decoder_rejects_values_outside_the_grid():
    with pytest.raises(ValueError):
        decode_fcnet_genotype(Genotype(values=(100, 16, "tanh", "tanh", 0.0, 0.0, 0.1, "const", 8)))


def test_multi_fidelity_rungs_for_100_epochs():
    assert rung_epochs(100) == [1, 4, 11, 33, 100]


@needs_data
@pytest.mark.parametrize("task", FCNET_TASKS)
def test_every_configuration_is_found_and_rows_are_aligned(task):
    substrate = FCNetSubstrate(task=task)
    space = fcnet_search_space()
    d = INPUT_DIMENSIONS[task]
    rng = random.Random(1)
    combos = list(itertools.product(*(dom.values for dom in space.domains)))
    for values in rng.sample(combos, 300):
        g = Genotype(values=values)
        u1, u2 = values[0], values[1]
        metrics = substrate.full_fidelity_metrics(g)
        assert metrics["n_params"] == (d + 1) * u1 + (u1 + 1) * u2 + (u2 + 1)
        f1, f2 = substrate.objectives(g)
        assert f1 == metrics["valid_mse"] and f2 == metrics["training_seconds"] > 0


@needs_data
def test_fidelity_and_training_time_accounting():
    substrate = FCNetSubstrate(task="protein_structure")
    g = fcnet_search_space().sample_uniform(random.Random(3))
    assert substrate.objectives_at_epochs(g, 100) == substrate.objectives(g)
    assert substrate.objectives_at_epochs(g, 4)[1] == substrate.objectives(g)[1]
    assert substrate.training_seconds(g, 25) == pytest.approx(substrate.analytic_f2(g) / 4)
    with pytest.raises(ValueError):
        substrate.objectives_at_epochs(g, 101)


@needs_data
def test_all_objectives_enumerates_the_table():
    genotypes, objectives = FCNetSubstrate(task="naval_propulsion").all_objectives()
    assert len(genotypes) == len(set(genotypes)) == 62_208
    substrate = FCNetSubstrate(task="naval_propulsion")
    for i in (0, 12_345, 62_207):
        assert tuple(objectives[i]) == substrate.objectives(genotypes[i])
