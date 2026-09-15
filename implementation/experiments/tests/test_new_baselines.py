"""Tests for the seven v0.0.4 baselines: MO-LS, regularized evolution (MO),
NSGA-III, MOEA/D, BoTorch qNEHVI and qParEGO, SMAC3 ParEGO.

Each is driven through the real run_single/build_method path against a fake
substrate on the real JAHS-Bench-201 genotype (10 categorical coordinates
with the cell-validity constraint), so the harness contract every arm must
honour is checked end to end:
  * the full budget is spent;
  * no genotype is fully evaluated twice;
  * no invalid genotype is ever evaluated;
  * the same seed reproduces the same run exactly (required by the
    pipeline's determinism check)."""

from __future__ import annotations

import json

import pytest
from p3net.problem.decoding import is_valid

from scripts import run_experiment
from search_spaces.nas_genotype import nas_validity
from substrates.base import FidelityLevel, Substrate


class FakeSubstrate(Substrate):
    def fidelity_ladder(self):
        return (FidelityLevel(rank=0, config={"epochs": 1}),)

    def query_f1(self, genotype, fidelity):
        return float(sum(1 for v in genotype.values if v != "none")) + 0.01 * (
            hash(genotype.values[-1]) % 7
        )

    def analytic_f2(self, genotype):
        return float(sum(len(str(v)) for v in genotype.values))


@pytest.fixture
def space_config(monkeypatch):
    monkeypatch.setitem(run_experiment._SUBSTRATE_BUILDERS, "fake", lambda cfg: FakeSubstrate())
    return {"search_space": "nas_genotype", "substrate": "fake"}


# Budgets are the smallest that exercise each method past its initial design.
BUDGETS = {
    "mo_ls": 60,
    "regularized_evolution_mo": 60,
    "nsga3": 60,
    "moead": 60,
    "smac3_parego": 40,
    "botorch_qnehvi": 28,
    "botorch_qparego": 28,
    "reinforce_mo": 60,
    "bananas_mo": 30,
    "oss_vizier": 25,
    "p3net_bartnik": 40,
    "p3net_bartnik_fihc": 40,
    "p3net_elympus": 40,
    "p3_absolute_cascade": 40,
}


def _run(name, space_config, seed):
    config = run_experiment.load_method_config(name)
    return run_experiment.run_single(config, space_config, BUDGETS[name], seed)


@pytest.mark.parametrize("name", sorted(BUDGETS))
def test_new_baseline_honours_the_harness_contract(name, space_config):
    result = _run(name, space_config, seed=1)
    history = result.state.history
    assert result.state.evaluations_used == BUDGETS[name]
    genotypes = [obs.genotype for obs in history]
    assert len(genotypes) == len(set(genotypes)), "a genotype was fully evaluated twice"
    assert all(is_valid(g, nas_validity) for g in genotypes), "an invalid genotype was evaluated"


@pytest.mark.parametrize("name", sorted(BUDGETS))
def test_new_baseline_is_deterministic_for_a_fixed_seed(name, space_config):
    first = _run(name, space_config, seed=7)
    second = _run(name, space_config, seed=7)

    def as_json(result):
        return json.dumps([run_experiment._observation_to_dict(o) for o in result.state.history])

    assert as_json(first) == as_json(second)


@pytest.mark.parametrize(
    "name", ["mo_ls", "regularized_evolution_mo", "nsga3", "moead", "reinforce_mo"]
)
def test_different_seeds_give_different_runs(name, space_config):
    a = _run(name, space_config, seed=1)
    b = _run(name, space_config, seed=2)
    assert [o.genotype for o in a.state.history] != [o.genotype for o in b.state.history]


def test_tpe_is_unchanged_by_the_optuna_wrapper_refactor(space_config):
    """tpe_ask_tell now delegates to the shared optuna_ask_tell. TPE's stored
    runs must stay reproducible, so its behaviour must not change: same seed,
    same sampler construction order, same history."""
    import optuna
    from p3net.harness.evaluation_cache import EvaluationCache

    from methods.external._ask_tell_shared import AskTellMethod
    from methods.external.tpe import tpe_method

    config = run_experiment.load_method_config("tpe")
    via_harness = run_experiment.run_single(config, space_config, 40, 3)

    # Reference: the pre-refactor construction, inlined.
    from p3net.harness.runner import Runner

    from search_spaces.nas_genotype import nas_search_space

    space = nas_search_space()
    cache = EvaluationCache()
    study = optuna.create_study(
        directions=["minimize", "minimize"], sampler=optuna.samplers.TPESampler(seed=3)
    )
    pending = {}

    def sample():
        from methods.external.tpe import _suggest_genotype

        while True:
            trial = study.ask()
            g = _suggest_genotype(trial, space)
            if not is_valid(g, nas_validity):
                study.tell(trial, state=optuna.trial.TrialState.FAIL)
                continue
            if cache.record_proposal(g, experiment_type="tpe", protocol_version="v1"):
                study.tell(
                    trial, values=list(cache.get(g, experiment_type="tpe", protocol_version="v1"))
                )
                continue
            pending[g] = trial
            return g

    def report(g, objectives):
        study.tell(pending.pop(g), values=list(objectives))

    substrate = FakeSubstrate()
    reference = Runner(objective=substrate.objectives, budget=40).run(
        AskTellMethod(sampler=sample, report=report, experiment_type="tpe", cache=cache)
    )
    assert [o.genotype for o in via_harness.state.history] == [
        o.genotype for o in reference.history
    ]
    assert tpe_method  # imported symbol still exported


def test_smac_survives_a_space_where_most_asked_genotypes_are_invalid(monkeypatch):
    """Regression: invalid genotypes were told to SMAC as CRASHED with an
    infinite cost; ParEGO's normalisation turned that into NaN and SMAC's
    random forest crashed on NAS-HPO-Bench-II. A validity rule rejecting
    most of the space reproduces the condition deterministically."""
    monkeypatch.setitem(run_experiment._SUBSTRATE_BUILDERS, "fake", lambda cfg: FakeSubstrate())
    import search_spaces.nas_genotype as ng

    def strict_validity(genotype):
        return -1.0 if genotype.values[0] == genotype.values[1] else 1.0

    monkeypatch.setitem(
        run_experiment._SEARCH_SPACE_BUILDERS,
        "strict_space",
        lambda: (ng.nas_search_space(), strict_validity),
    )
    config = run_experiment.load_method_config("smac3_parego")
    result = run_experiment.run_single(
        config, {"search_space": "strict_space", "substrate": "fake"}, 40, 1
    )
    assert result.state.evaluations_used == 40
    assert all(strict_validity(o.genotype) <= 0 for o in result.state.history)


def test_symbolic_kappa_is_resolved_per_search_space():
    assert run_experiment.resolve_kappa("log2n", n=10) == 4
    assert run_experiment.resolve_kappa("log2n", n=8) == 3
    assert run_experiment.resolve_kappa("2log2n", n=10) is None
    assert run_experiment.resolve_kappa("unbounded", n=10) == run_experiment.KAPPA_UNBOUNDED
    assert run_experiment.resolve_kappa(4, n=10) == 4
    assert run_experiment.resolve_kappa(None, n=10) is None
    with pytest.raises(ValueError):
        run_experiment.resolve_kappa("sqrt", n=10)


def test_sweep_cells_build_p3net_with_the_intended_kappa_and_threshold(space_config):
    from search_spaces.nas_genotype import nas_search_space

    n = nas_search_space().n
    expected = {
        "p3net_cascade_kappa1_thr2eps": (1, 0.02),
        "p3net_cascade_kappalog_thr1eps": (4, 0.01),
        "p3net_cascade_kappa2log_thr2eps": (2 * 4, 0.02),
        "p3net_cascade_kappainf_thr0": (run_experiment.KAPPA_UNBOUNDED, 0.0),
    }
    assert n == 10
    for name, (kappa, threshold) in expected.items():
        result = run_experiment.run_single(
            run_experiment.load_method_config(name), space_config, 12, 1
        )
        assert result.method.cascade
        assert (result.method.kappa, result.method.acceptance_threshold) == (kappa, threshold)


def test_absolute_linear_ablation_differs_from_final_engine_only_in_surrogate(space_config):
    final = run_experiment.load_method_config("p3net_cascade")["params"]
    ablation = run_experiment.load_method_config("p3_absolute_cascade")["params"]
    differing = {k for k in set(final) | set(ablation) if final.get(k) != ablation.get(k)}
    assert differing == {"surrogate_kind", "surrogate_model"}
    assert ablation["surrogate_model"] == "ridge_cv"  # final engine's default model
