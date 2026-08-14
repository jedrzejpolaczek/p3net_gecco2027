"""Tests for scripts.run_experiment -- the harness-driven single-run
entry point. Real substrates (jahs_bench_201, nas_hpo_bench_ii) raise
NotImplementedError until Stage C, so the harness wiring here is verified
against a fake substrate injected through the same registry the real
config files select from. (Gap in the original task list -- adding it.)
"""

import json

import pytest

from scripts import run_experiment
from substrates.base import FidelityLevel, Substrate


class FakeSubstrate(Substrate):
    def fidelity_ladder(self):
        return (FidelityLevel(rank=0, config={"epochs": 1}),)

    def query_f1(self, genotype, fidelity):
        return float(sum(1 for v in genotype.values if v != "none"))

    def analytic_f2(self, genotype):
        return float(len(genotype.values))


@pytest.fixture
def fake_search_space_config(monkeypatch):
    monkeypatch.setitem(run_experiment._SUBSTRATE_BUILDERS, "fake", lambda cfg: FakeSubstrate())
    return {"search_space": "nas_genotype", "substrate": "fake"}


def test_run_single_random_search_respects_budget(fake_search_space_config):
    method_config = {"method": "random_search", "params": {}}
    state = run_experiment.run_single(method_config, fake_search_space_config, budget=15, seed=0)
    assert state.evaluations_used == 15
    assert len(state.history) == 15


def test_run_single_p3net_respects_budget(fake_search_space_config):
    method_config = {"method": "p3net", "params": {"population_size": 8}}
    state = run_experiment.run_single(method_config, fake_search_space_config, budget=20, seed=1)
    assert state.evaluations_used == 20


@pytest.mark.parametrize(
    "kind", ["p3_alone", "p3_absolute", "nsga_net", "nsganetv2", "sh_emoa", "mo_bohb", "tpe"]
)
def test_run_single_every_wired_method_completes(fake_search_space_config, kind):
    method_config = {"method": kind, "params": {}}
    state = run_experiment.run_single(method_config, fake_search_space_config, budget=12, seed=2)
    assert state.evaluations_used == 12


def test_build_method_rejects_a_not_yet_implemented_kind():
    with pytest.raises(NotImplementedError):
        run_experiment.build_method(
            {"method": "nsganetv2_continuous", "params": {}},
            search_space=None,
            validity=None,
            rng=None,
            cache=None,
        )


def test_persist_run_writes_readable_json(tmp_path, monkeypatch, fake_search_space_config):
    monkeypatch.setattr(run_experiment, "RESULTS_DIR", tmp_path)
    method_config = {"method": "random_search", "params": {}}
    state = run_experiment.run_single(method_config, fake_search_space_config, budget=5, seed=3)
    out_path = run_experiment.persist_run(
        state, method_name="random_search", search_space_name="fake_space", budget=5, seed=3
    )
    assert out_path.exists()
    payload = json.loads(out_path.read_text())
    assert payload["evaluations_used"] == 5
    assert len(payload["history"]) == 5
    assert payload["seed"] == 3


def test_result_path_is_deterministic_given_the_same_inputs():
    a = run_experiment.result_path(
        method_name="p3net", search_space_name="jahs_bench_201", budget=50, seed=1
    )
    b = run_experiment.result_path(
        method_name="p3net", search_space_name="jahs_bench_201", budget=50, seed=1
    )
    assert a == b


def test_real_configs_load_and_parse():
    for name in [
        "p3net",
        "random_search",
        "p3_alone",
        "p3_absolute",
        "nsga_net",
        "nsganetv2",
        "sh_emoa",
    ]:
        config = run_experiment.load_method_config(name)
        assert config["method"]
    for name in ["jahs_bench_201", "nas_hpo_bench_ii"]:
        config = run_experiment.load_search_space_config(name)
        assert config["search_space"] == "nas_genotype"
    budgets = run_experiment.load_budgets_config()
    assert budgets["budget_tiers"] == [50, 100, 200]
    assert len(budgets["seeds"]) == 10
