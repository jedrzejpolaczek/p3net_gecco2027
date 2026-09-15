"""Tests for the multi-fidelity track (methods/multi_fidelity.py): the cost
model, Hyperband's bracket schedule, ASHA's promotion rule, multi-objective
promotion order, and the harness contract through run_single/persist_run."""

from __future__ import annotations

import json

import pytest
from p3net.problem.decoding import is_valid
from p3net.problem.genotype import Genotype

from methods.multi_fidelity import (
    AshaMO,
    HyperbandMO,
    MultiFidelityRunner,
    promotion_order,
    rung_epochs,
)
from scripts import run_experiment
from scripts import run_pipeline as rp
from search_spaces.nas_genotype import nas_search_space, nas_validity
from substrates.base import FidelityLevel, Substrate

FULL_EPOCHS = 9  # eta = 3 -> rungs 1, 3, 9


class FakeMultiFidelitySubstrate(Substrate):
    def __init__(self) -> None:
        self.calls: list[tuple[Genotype, int]] = []

    def fidelity_ladder(self):
        return (FidelityLevel(rank=0, config={"epochs": FULL_EPOCHS}),)

    def query_f1(self, genotype, fidelity):
        epochs = fidelity.config["epochs"]
        self.calls.append((genotype, epochs))
        base = float(sum(1 for v in genotype.values if v != "none"))
        return base + 0.01 * (hash(genotype.values[-1]) % 7) + 10.0 / epochs

    def analytic_f2(self, genotype):
        return float(sum(len(str(v)) for v in genotype.values))


@pytest.fixture
def space_config(monkeypatch):
    monkeypatch.setitem(
        run_experiment._SUBSTRATE_BUILDERS, "fake_mf", lambda cfg: FakeMultiFidelitySubstrate()
    )
    return {"search_space": "nas_genotype", "substrate": "fake_mf"}


ARMS = ("hyperband_mo", "asha_mo", "bohb_mo")


def test_rung_epochs_match_the_documented_ladders():
    assert rung_epochs(200) == [2, 7, 22, 67, 200]
    assert rung_epochs(12) == [1, 4, 12]
    assert rung_epochs(FULL_EPOCHS) == [1, 3, 9]


def test_promotion_order_puts_nondominated_first_and_boundaries_before_interior():
    g = [Genotype(values=(i,)) for i in range(5)]
    results = [
        (g[0], (3.0, 3.0)),  # dominated by g1
        (g[1], (2.0, 2.0)),  # front 0, interior
        (g[2], (1.0, 5.0)),  # front 0, boundary
        (g[3], (5.0, 1.0)),  # front 0, boundary
        (g[4], (6.0, 6.0)),  # dominated
    ]
    order = promotion_order(results)
    assert set(order[:3]) == {g[1], g[2], g[3]}
    assert order[2] == g[1]
    assert order[3:] == [g[0], g[4]]


def _runner_and_method(cls, budget, seed=1):
    substrate = FakeMultiFidelitySubstrate()
    import random

    method = cls(
        search_space=nas_search_space(),
        validity=nas_validity,
        rng=random.Random(seed),
        full_epochs=FULL_EPOCHS,
        seed=seed,
    )
    return MultiFidelityRunner(substrate=substrate, budget=budget), method


def test_hyperband_first_bracket_follows_li_et_al_schedule():
    # s_max = 2: bracket s=2 has n = ceil(3/3 * 9) = 9 configs at 1 epoch,
    # the best 3 continue to 3 epochs, the best 1 to 9 epochs.
    runner, method = _runner_and_method(HyperbandMO, budget=100)
    runner.run(method)
    first = [q.epochs for q in runner.queries[:13]]
    assert first == [1] * 9 + [3] * 3 + [9]
    rung0 = [(q.genotype, q.objectives) for q in runner.queries[:9]]
    promoted = {q.genotype for q in runner.queries[9:12]}
    assert promoted == set(promotion_order(rung0)[:3])
    # Next bracket s=1: n = ceil(3/2 * 3) = 5 new configs at 3 epochs.
    assert [q.epochs for q in runner.queries[13:18]] == [3] * 5
    assert not {q.genotype for q in runner.queries[13:18]} & {
        q.genotype for q in runner.queries[:13]
    }


def test_asha_promotes_as_soon_as_a_rung_has_eta_results():
    runner, method = _runner_and_method(AshaMO, budget=100)
    runner.run(method)
    epochs = [q.epochs for q in runner.queries[:5]]
    assert epochs == [1, 1, 1, 3, 1]
    rung0 = [(q.genotype, q.objectives) for q in runner.queries[:3]]
    assert runner.queries[3].genotype == promotion_order(rung0)[0]


def test_cost_counts_only_additional_epochs_and_never_exceeds_the_budget():
    runner, method = _runner_and_method(HyperbandMO, budget=20)
    runner.run(method)
    trained: dict[Genotype, int] = {}
    total = 0.0
    for q in runner.queries:
        assert q.cost == pytest.approx((q.epochs - trained.get(q.genotype, 0)) / FULL_EPOCHS)
        trained[q.genotype] = q.epochs
        total += q.cost
    assert total == pytest.approx(runner.cost_used)
    assert 20 - 1 < runner.cost_used <= 20 + 1e-9


@pytest.mark.parametrize("name", ARMS)
def test_multi_fidelity_arm_honours_the_harness_contract(name, space_config, tmp_path):
    config = run_experiment.load_method_config(name)
    result = run_experiment.run_single(config, space_config, 15, 1)
    history = result.state.history
    genotypes = [obs.genotype for obs in history]
    assert genotypes, "no configuration reached full training"
    assert len(genotypes) == len(set(genotypes)), "a genotype was fully evaluated twice"
    assert all(is_valid(g, nas_validity) for g in genotypes)
    queried = [(tuple(q.genotype.values), q.epochs) for q in result.method.fidelity_queries]
    assert len(queried) == len(set(queried)), "a (genotype, epochs) pair was queried twice"
    assert all(is_valid(q.genotype, nas_validity) for q in result.method.fidelity_queries)
    assert result.method.cost_used <= 15 + 1e-9

    path = run_experiment.persist_run(
        result, method_name=name, search_space_name="fake_mf", budget=15, seed=1, out_dir=tmp_path
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["diagnostics"]["cost_used"] == pytest.approx(result.method.cost_used)
    assert len(payload["diagnostics"]["fidelity_queries"]) == len(queried)
    point = rp.Point(stage="test", method=name, search_space="fake_mf", budget=15, seed=1)
    assert rp.validate_run_file(path, point) is None


@pytest.mark.parametrize("name", ARMS)
def test_multi_fidelity_arm_is_deterministic_for_a_fixed_seed(name, space_config):
    config = run_experiment.load_method_config(name)

    def trace(result):
        return [(list(q.genotype.values), q.epochs) for q in result.method.fidelity_queries]

    first = run_experiment.run_single(config, space_config, 10, 7)
    second = run_experiment.run_single(config, space_config, 10, 7)
    assert trace(first) == trace(second)


def test_objectives_at_full_epochs_equal_the_single_fidelity_objectives():
    substrate = FakeMultiFidelitySubstrate()
    g = nas_search_space().sample_uniform(__import__("random").Random(0))
    assert substrate.objectives_at_epochs(g, FULL_EPOCHS) == substrate.objectives(g)
