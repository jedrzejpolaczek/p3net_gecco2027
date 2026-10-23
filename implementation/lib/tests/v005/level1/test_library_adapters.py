"""Level-1 tests for the library adapters (card
`notes/plans/v005-sources/library-adapters.md`, W-A1-W-A6).

Sources: smac 2.4.1 (HPO facade + ParEGO), pymoo 0.6.2 MOEAD, optuna 4.9.0
(NSGAIIISampler, TPESampler = MOTPE), botorch 0.18.1 (qLogNEHVI, qLogNEI on
Chebyshev scalarisation), google-vizier 0.1.24 (GP-UCB-PE), own RS. Card
decisions: A-1 a, A-2 a, settings table §3, ask-tell rules §4.

Library-dependent tests are skipped when the library is not installed in
the test environment (`pytest.importorskip`); run them in the experiments
environment. `config()` keys follow interfaces §7 (Q-30).
"""

from __future__ import annotations

import math

import pytest

from ._support import (
    CountingObjective,
    G,
    additive_cost,
    assert_budget_respected,
    drive,
    drive_batches,
    make,
    random_weights,
    space_of,
    vals,
)

LIB = {
    "SMAC3ParEGO": "smac",
    "MOEAD": "pymoo",
    "NSGA3": "optuna",
    "MOTPE": "optuna",
    "QNEHVI": "botorch",
    "QParEGO": "botorch",
    "Vizier": "vizier",
    "RandomSearch": None,
}


def _cls(name):
    if LIB[name]:
        pytest.importorskip(LIB[name])
    from p3net.v005.baselines import library

    return getattr(library, name)


def _obj(domains, seed=0):
    w1 = random_weights(domains, seed)
    w2 = [[1.0 - x for x in row] for row in w1]
    return CountingObjective(additive_cost(w1), additive_cost(w2))


# ---------------------------------------------------------------------------
# W-A1: configuration = table §3
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("budget", [50, 100])
def test_WA1_smac3_parego_configuration(budget):
    """W-A1 (§3, #19): HPO facade, ParEGO, deterministic, n_trials = b."""
    cfg = make(_cls("SMAC3ParEGO"), space_of([3] * 9), budget, 0).config()
    assert cfg["facade"] == "HyperparameterOptimizationFacade"
    assert cfg["multi_objective_algorithm"] == "ParEGO"
    assert cfg["deterministic"] is True
    assert cfg["n_trials"] == budget


def test_WA1_moead_configuration():
    """W-A1 (§3, #20, #21): N = 20, Tchebycheff, prob_neighbor_mating 0.9,
    T = ceil(0.2 N) = 4, categorical operators, deduplication."""
    cfg = make(_cls("MOEAD"), space_of([3] * 9), 100, 0).config()
    assert cfg["n_partitions_or_pop"] == 20 or cfg.get("pop_size") == 20
    assert "tchebi" in str(cfg["decomposition"]).lower()
    assert cfg["prob_neighbor_mating"] == 0.9
    assert cfg["n_neighbors"] == 4
    assert "uniform" in str(cfg["crossover"]).lower()
    assert "reset" in str(cfg["mutation"]).lower()
    assert cfg["eliminate_duplicates"] is True


def test_WA1_nsga3_motpe_vizier_rs_configuration():
    """W-A1 (§3): NSGA-III population 20 (#37); MOTPE n_ei_candidates 24,
    multivariate False, n_startup_trials min(10, floor(0.25 b)); Vizier
    defaults (num_seed_trials 1); RS uniform on valid genotypes without
    duplicates."""
    assert make(_cls("NSGA3"), space_of([3] * 6), 100, 0).config()["population_size"] == 20
    motpe = make(_cls("MOTPE"), space_of([3] * 6), 100, 0).config()
    assert (motpe["n_ei_candidates"], motpe["multivariate"], motpe["n_startup_trials"]) == (
        24,
        False,
        10,
    )
    assert make(_cls("MOTPE"), space_of([3] * 6), 36, 0).config()["n_startup_trials"] == 9
    assert make(_cls("Vizier"), space_of([3] * 6), 50, 0).config()["num_seed_trials"] == 1
    assert make(_cls("RandomSearch"), space_of([3] * 6), 50, 0).config()["deduplicate"] is True


@pytest.mark.parametrize("name,acq", [("QNEHVI", "qLogNEHVI"), ("QParEGO", "qLogNEI")])
def test_WA1_gp_arms_configuration(name, acq):
    """W-A1 (§3): MixedSingleTaskGP (all dims categorical), Standardize, 128
    QMC samples, pool of 1024 random valid + 1-variable neighbours of the
    front."""
    cfg = make(_cls(name), space_of([3] * 6), 50, 0).config()
    assert cfg["acquisition"] == acq
    assert cfg["model"] == "MixedSingleTaskGP"
    assert cfg["outcome_transform"] == "Standardize"
    assert cfg["mc_samples"] == 128
    assert cfg["pool_size"] == 1024


# ---------------------------------------------------------------------------
# W-A2-W-A4
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "d,budget,expected", [(9, 50, 12), (9, 100, 25), (9, 350, 87), (3, 200, 30)]
)
def test_WA2_smac3_initial_design_size(d, budget, expected):
    """W-A2 (#19, BB-4): SMAC3 initial design = min(10 d, floor(0.25 b))."""
    cfg = make(_cls("SMAC3ParEGO"), space_of([3] * d), budget, 0).config()
    assert cfg["initial_design_size"] == expected == min(10 * d, budget // 4)


def test_WA3_moead_categorical_values_and_full_budget():
    """W-A3 (#20, #21): MOEA/D proposes only integer values in 0..k-1 and
    uses the full budget (no early stop on duplicates)."""
    domains = [6, 6, 2, 2, 3, 3, 6, 2, 4]
    obj = _obj(domains)
    batches = drive_batches(make(_cls("MOEAD"), space_of(domains), 200, 0), obj, 200)
    for b in batches:
        for g in b:
            assert all(isinstance(v, int) and 0 <= v < k for v, k in zip(g, domains)), g
    assert_budget_respected(obj, 200, exact=True)


@pytest.mark.parametrize("name", ["QNEHVI", "QParEGO"])
@pytest.mark.parametrize("d,budget,expected", [(9, 50, 12), (9, 100, 20), (6, 100, 14), (3, 16, 4)])
def test_WA4_gp_initial_design(name, d, budget, expected):
    """W-A4 (§3): GP initial design = min(2 (d + 1), floor(0.25 b))."""
    cfg = make(_cls(name), space_of([3] * d), budget, 0).config()
    assert cfg["n_initial"] == expected


@pytest.mark.parametrize("name", ["QNEHVI", "QParEGO"])
def test_WA4_gp_pool_valid_unevaluated(name):
    """W-A4 (§3, #33, #35): proposals come from a pool of valid, unevaluated
    genotypes -- no genotype is proposed twice, all are valid; one point
    per step after the initial design."""
    from p3net.v005.common import is_valid

    space = space_of([3, 3, 3])
    obj = _obj([3, 3, 3])
    batches = drive_batches(make(_cls(name), space, 16, 0), obj, 16)
    assert all(is_valid(space, G(*g)) for b in batches for g in b)
    assert len(set(obj.calls)) == len(obj.calls)
    assert all(len(b) == 1 for b in batches[1:])


# ---------------------------------------------------------------------------
# W-A5: the adapter does not change the library's method
# ---------------------------------------------------------------------------


def test_WA5_motpe_adapter_matches_native_optuna_loop():
    """W-A5 (§4, A-2 a): on the same seed the adapter proposes the same
    sequence as a native optuna loop with TPESampler(n_ei_candidates=24,
    multivariate=False, n_startup_trials = the adapter's own
    min(10, floor(0.25 b)), Q-40) and categorical parameters x0..x{n-1} with
    choices 0..k-1."""
    optuna = pytest.importorskip("optuna")
    domains = [3, 4, 2, 5, 3]
    m = make(_cls("MOTPE"), space_of(domains), 30, 0)
    seed = m.config()["seed"]
    obj_a = _obj(domains)
    adapted = [g for b in drive_batches(m, obj_a, 30) for g in b]

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    sampler = optuna.samplers.TPESampler(
        seed=seed,
        n_ei_candidates=24,
        multivariate=False,
        n_startup_trials=m.config()["n_startup_trials"],
    )
    assert m.config()["n_startup_trials"] == min(10, 30 // 4)
    study = optuna.create_study(directions=["minimize", "minimize"], sampler=sampler)
    obj_n = _obj(domains)
    native, seen = [], {}
    while len(native) < 30:
        t = study.ask()
        g = tuple(t.suggest_categorical(f"x{i}", list(range(k))) for i, k in enumerate(domains))
        if g in seen:
            study.tell(t, seen[g])
            continue
        seen[g] = obj_n(g)
        native.append(g)
        study.tell(t, seen[g])
    assert adapted == native


def test_WA5_smac3_adapter_matches_native_smac_loop(tmp_path):
    """W-A5 (§4; #19): on the same seed the SMAC3-ParEGO adapter proposes the
    same sequence as a native SMAC loop (HPO facade, ParEGO, deterministic,
    n_trials = b, default initial design) on the adapter's own ConfigSpace
    (`config()["configspace"]`, interfaces §7 Q-30). Genotype index i <->
    hyperparameter `x{i}` with choices 0..k-1 (Q-35)."""
    pytest.importorskip("smac")
    from smac import HyperparameterOptimizationFacade, Scenario
    from smac.multi_objective.parego import ParEGO
    from smac.runhistory.dataclasses import TrialValue

    domains = [3, 2, 4, 3]
    budget = 20
    m = make(_cls("SMAC3ParEGO"), space_of(domains), budget, 0)
    cfg = m.config()
    obj_a = _obj(domains)
    adapted = [g for b in drive_batches(m, obj_a, budget) for g in b]

    scen = Scenario(
        cfg["configspace"],
        deterministic=True,
        n_trials=budget,
        seed=cfg["seed"],
        objectives=["f1", "f2"],
        output_directory=tmp_path / "smac",
    )
    facade = HyperparameterOptimizationFacade(
        scen,
        lambda config, seed=0: [0.0, 0.0],
        multi_objective_algorithm=ParEGO(scen),
        overwrite=True,
        logging_level=40,
    )
    obj_n = _obj(domains)
    native, seen = [], {}
    for _ in range(10 * budget):
        if len(native) == budget:
            break
        info = facade.ask()
        g = tuple(int(info.config[f"x{i}"]) for i in range(len(domains)))
        if g not in seen:
            seen[g] = obj_n(g)
            native.append(g)
        facade.tell(info, TrialValue(cost=list(seen[g])))
    assert adapted == native


# ---------------------------------------------------------------------------
# W-A6: duplicates, invalid genotypes, budget
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "name", ["RandomSearch", "NSGA3", "MOTPE", "MOEAD", "SMAC3ParEGO", "Vizier"]
)
def test_WA6_duplicates_free_budget_never_exceeded(name):
    """W-A6 (§4, #35, K-2): on a 32-genotype space duplicates are frequent;
    none consumes budget; exactly b = 15 evaluations."""
    obj = _obj([2] * 5)
    drive(make(_cls(name), space_of([2] * 5), 15, 0), obj, 15)
    assert_budget_respected(obj, 15, exact=True)


def test_WA6_random_search_exhausts_space_without_repeats():
    """W-A6 / §3 RS: uniform on valid genotypes without duplicates -- with
    b = |space| every genotype is evaluated once; first proposals are
    spread over seeds (uniformity)."""
    obj = _obj([3, 3])
    drive(make(_cls("RandomSearch"), space_of([3, 3]), 9, 0), obj, 9)
    assert sorted(obj.calls) == sorted((a, b) for a in range(3) for b in range(3))
    from p3net.harness.runner import RunState

    firsts = {
        vals(make(_cls("RandomSearch"), space_of([3, 3]), 9, s).propose(RunState())[0])
        for s in range(60)
    }
    assert len(firsts) >= 7
    assert math.isfinite(len(firsts))
