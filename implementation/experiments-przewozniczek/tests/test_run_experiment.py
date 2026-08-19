"""Tests for scripts.run_experiment -- the harness-driven single-run
entry point. Real substrates (jahs_bench_201, nas_hpo_bench_ii) raise
NotImplementedError until Stage C, so the harness wiring here is verified
against a fake substrate injected through the same registry the real
config files select from. (Gap in the original task list -- adding it.)
"""

import json
import random

import pytest
from p3net.harness.evaluation_cache import EvaluationCache
from sklearn.linear_model import RidgeCV

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
    result = run_experiment.run_single(method_config, fake_search_space_config, budget=15, seed=0)
    assert result.state.evaluations_used == 15
    assert len(result.state.history) == 15


def test_run_single_p3net_respects_budget(fake_search_space_config):
    method_config = {"method": "p3net", "params": {"growth_factor": 2}}
    result = run_experiment.run_single(method_config, fake_search_space_config, budget=20, seed=1)
    assert result.state.evaluations_used == 20


@pytest.mark.parametrize(
    "kind",
    [
        "p3_alone",
        "p3_absolute",
        "nsga_net",
        "nsganetv2",
        "sh_emoa",
        "mo_bohb",
        "tpe",
    ],
)
def test_run_single_every_wired_method_completes(fake_search_space_config, kind):
    method_config = {"method": kind, "params": {}}
    result = run_experiment.run_single(method_config, fake_search_space_config, budget=12, seed=2)
    assert result.state.evaluations_used == 12


def test_run_single_p3_alone_reports_sweeps_completed_diagnostic(fake_search_space_config):
    method_config = {"method": "p3_alone", "params": {}}
    result = run_experiment.run_single(method_config, fake_search_space_config, budget=30, seed=2)
    assert result.method.sweeps_completed >= 1


@pytest.mark.parametrize("kind", ["tpe", "mo_bohb"])
def test_run_single_seeds_external_wrappers_reproducibly(fake_search_space_config, kind):
    """Every other method deterministically replays given the shared
    `seed` -> random.Random(seed) run_single builds and threads through
    build_method. tpe_method/mo_bohb_method both accept their own `seed`
    kwarg, but build_method never passed run_single's real seed down to
    them -- so two runs with the identical seed could diverge (TPESampler
    seeded from OS entropy; hpbandster's BOHB config generator drawing
    from numpy's uncontrolled global RNG). Two full run_single calls with
    the same seed must produce byte-identical proposal sequences, exactly
    like every other wired method already does."""
    method_config = {"method": kind, "params": {}}
    result_a = run_experiment.run_single(method_config, fake_search_space_config, budget=15, seed=42)
    result_b = run_experiment.run_single(method_config, fake_search_space_config, budget=15, seed=42)
    genotypes_a = [obs.genotype for obs in result_a.state.history]
    genotypes_b = [obs.genotype for obs in result_b.state.history]
    assert genotypes_a == genotypes_b


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
    result = run_experiment.run_single(method_config, fake_search_space_config, budget=5, seed=3)
    out_path = run_experiment.persist_run(
        result, method_name="random_search", search_space_name="fake_space", budget=5, seed=3
    )
    assert out_path.exists()
    payload = json.loads(out_path.read_text())
    assert payload["evaluations_used"] == 5
    assert len(payload["history"]) == 5
    assert payload["seed"] == 3
    assert "duplication_rate" in payload["diagnostics"]


def test_persist_run_includes_sweeps_completed_for_p3_alone(
    tmp_path, monkeypatch, fake_search_space_config
):
    monkeypatch.setattr(run_experiment, "RESULTS_DIR", tmp_path)
    method_config = {"method": "p3_alone", "params": {}}
    result = run_experiment.run_single(method_config, fake_search_space_config, budget=30, seed=2)
    out_path = run_experiment.persist_run(
        result, method_name="p3_alone", search_space_name="fake_space", budget=30, seed=2
    )
    payload = json.loads(out_path.read_text())
    assert payload["diagnostics"]["sweeps_completed"] == result.method.sweeps_completed


def test_persist_run_includes_pyramid_diagnostics_for_p3net(
    tmp_path, monkeypatch, fake_search_space_config
):
    """New Phase 0 diagnostics (bootstrap_proposals, mixing_proposals,
    surrogate_fit_seconds, linkage_tree_seconds, population_snapshots) must
    be captured the same way sweeps_completed/surrogate_quality_log
    already are -- additive, read via getattr, no schema break."""
    monkeypatch.setattr(run_experiment, "RESULTS_DIR", tmp_path)
    method_config = {"method": "p3net", "params": {"growth_factor": 2}}
    result = run_experiment.run_single(method_config, fake_search_space_config, budget=20, seed=1)
    out_path = run_experiment.persist_run(
        result, method_name="p3net", search_space_name="fake_space", budget=20, seed=1
    )
    payload = json.loads(out_path.read_text())
    diagnostics = payload["diagnostics"]
    assert diagnostics["bootstrap_proposals"] == result.method.bootstrap_proposals
    assert diagnostics["mixing_proposals"] == result.method.mixing_proposals
    assert diagnostics["surrogate_fit_seconds"] == result.method.surrogate_fit_seconds
    assert diagnostics["linkage_tree_seconds"] == result.method.linkage_tree_seconds
    assert diagnostics["bootstrap_proposals"] + diagnostics["mixing_proposals"] > 0
    assert len(diagnostics["population_snapshots"]) == len(result.method.population_snapshots)
    assert diagnostics["population_snapshots"][0][0] == list(
        result.method.population_snapshots[0][0].values
    )


def test_population_snapshots_feed_archive_turnover_end_to_end(
    tmp_path, monkeypatch, fake_search_space_config
):
    """The point of persisting population_snapshots: closing the "Known
    gaps" item that metrics.diagnostics.archive_turnover had no real data
    to run against. Reconstructed genotypes from the persisted JSON must
    round-trip cleanly into that function."""
    from p3net.problem.genotype import Genotype

    from metrics.diagnostics import archive_turnover

    monkeypatch.setattr(run_experiment, "RESULTS_DIR", tmp_path)
    method_config = {"method": "p3net", "params": {"growth_factor": 2}}
    result = run_experiment.run_single(method_config, fake_search_space_config, budget=20, seed=1)
    out_path = run_experiment.persist_run(
        result, method_name="p3net", search_space_name="fake_space", budget=20, seed=1
    )
    payload = json.loads(out_path.read_text())
    reconstructed = [
        [Genotype(values=tuple(values)) for values in snapshot]
        for snapshot in payload["diagnostics"]["population_snapshots"]
    ]
    points = archive_turnover(reconstructed)
    assert len(points) == len(reconstructed) - 1


def test_persist_run_includes_pyramid_diagnostics_for_p3_absolute(
    tmp_path, monkeypatch, fake_search_space_config
):
    """p3_absolute shares p3net.methods.p3net.P3Net's own Pyramid engine
    since 2026-08-18 (Phase 3, Conclusions) -- _diagnostics' getattr-based
    capture picks these up for it too, with no p3_absolute-specific code
    in run_experiment.py, since the attribute names are identical."""
    monkeypatch.setattr(run_experiment, "RESULTS_DIR", tmp_path)
    method_config = {"method": "p3_absolute", "params": {"growth_factor": 2}}
    result = run_experiment.run_single(method_config, fake_search_space_config, budget=20, seed=1)
    out_path = run_experiment.persist_run(
        result, method_name="p3_absolute", search_space_name="fake_space", budget=20, seed=1
    )
    payload = json.loads(out_path.read_text())
    diagnostics = payload["diagnostics"]
    assert diagnostics["bootstrap_proposals"] == result.method.bootstrap_proposals
    assert diagnostics["mixing_proposals"] == result.method.mixing_proposals
    assert diagnostics["bootstrap_proposals"] + diagnostics["mixing_proposals"] > 0
    assert len(diagnostics["population_snapshots"]) == len(result.method.population_snapshots)
    # p3_absolute has no telescoping construction -- these must be absent.
    assert "chain_depth_log" not in diagnostics
    assert "surrogate_fit_seconds" not in diagnostics


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
    assert (
        run_experiment.load_search_space_config("jahs_bench_201")["search_space"] == "nas_genotype"
    )
    assert (
        run_experiment.load_search_space_config("nas_hpo_bench_ii")["search_space"]
        == "nas_hpo_bench_ii_genotype"
    )
    assert (
        run_experiment.load_search_space_config("nas_bench_201")["search_space"]
        == "nas_bench_201_genotype"
    )
    budgets = run_experiment.load_budgets_config()
    assert budgets["budget_tiers"] == [50, 100, 200, 350]
    assert len(budgets["seeds"]) == 30


def test_nas_bench_201_search_space_and_substrate_build_and_wire():
    """glimmering-swimming-book.md, Faza 3: the new isolation-experiment
    search space registers in the same builders as the two existing
    benchmarks, with no other change to run_experiment.py's shape."""
    config = run_experiment.load_search_space_config("nas_bench_201")
    search_space, validity = run_experiment.build_search_space(config)
    assert search_space.n == 6  # architecture edges only, no Theta
    substrate = run_experiment.build_substrate(config)
    assert substrate.dataset == "cifar10"
    assert substrate.fidelity_ladder()[-1].config["epochs"] == 200


def test_p3net_config_always_wires_the_substrates_analytic_cost(fake_search_space_config):
    """Adopted 2026-08-17 (Results, Findings; p3net.methods.p3net.P3Net's
    module docstring): a design-decision ablation found a consistent,
    partly-significant improvement from computing f2 fresh via the
    substrate during C* selection, versus inheriting it from the
    ancestor. build_method now wires substrate.analytic_cost_objectives
    into P3Net.analytic_cost unconditionally for every p3net config, not
    behind an opt-in marker."""
    config = run_experiment.load_method_config("p3net")
    search_space, validity = run_experiment.build_search_space(fake_search_space_config)
    substrate = run_experiment.build_substrate(fake_search_space_config)
    method = run_experiment.build_method(
        config,
        search_space=search_space,
        validity=validity,
        rng=random.Random(0),
        cache=EvaluationCache(),
        substrate=substrate,
    )
    genotype = search_space.sample_uniform(random.Random(1))
    assert method.analytic_cost(genotype) == substrate.analytic_cost_objectives(genotype)


def test_p3net_config_wires_a_regularised_model_factory(fake_search_space_config):
    """Adopted 2026-08-18 (Results, "Surrogate quality: magnitude
    calibration"; Conclusions): plain sklearn.linear_model.LinearRegression
    produced wild, unstable predictions for a newly-matured pyramid
    level's first sweep pass (median squared error 6-19x every other
    level size, real data). RidgeCV -- regularisation strength picked by
    its own built-in cross-validation, not hand-tuned -- replaces it as
    RelativeLinkageAwareSurrogate's model_factory for every p3net config."""
    config = run_experiment.load_method_config("p3net")
    search_space, validity = run_experiment.build_search_space(fake_search_space_config)
    substrate = run_experiment.build_substrate(fake_search_space_config)
    method = run_experiment.build_method(
        config,
        search_space=search_space,
        validity=validity,
        rng=random.Random(0),
        cache=EvaluationCache(),
        substrate=substrate,
    )
    assert method.model_factory is RidgeCV


def test_p3net_surrogate_interactions_config_loads_and_runs(fake_search_space_config):
    """Phase 4's single-axis ablation config (configs/methods/
    p3net_surrogate_interactions.yaml) is a plain params: override on
    "method: p3net", the same pattern p3_alone_pop20.yaml etc. already
    use -- build_method needs no p3net_surrogate_interactions-specific
    branch, and use_surrogate_interactions reaches the constructed
    P3Net unchanged via **params."""
    config = run_experiment.load_method_config("p3net_surrogate_interactions")
    assert config["method"] == "p3net"
    assert config["default_grid"] is False
    assert config["params"]["use_surrogate_interactions"] is True

    result = run_experiment.run_single(config, fake_search_space_config, budget=20, seed=1)
    assert result.method.use_surrogate_interactions is True
    assert result.state.evaluations_used == 20


def test_build_method_p3net_requires_a_substrate():
    with pytest.raises(ValueError):
        run_experiment.build_method(
            {"method": "p3net", "params": {}},
            search_space=None,
            validity=None,
            rng=None,
            cache=None,
        )
