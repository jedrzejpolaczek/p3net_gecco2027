"""Tests for methods.external.{mo_bohb,tpe} -- both real (Stage C):
mo_bohb_method wraps hpbandster's real BOHB config generator (Tchebycheff-
scalarised, see methods/external/mo_bohb.py's module docstring for why),
tpe_method wraps optuna's real TPESampler via its ask/tell API. (Gap in
the original task list -- adding it.)
"""

import random

import numpy as np
import pytest
from p3net.harness.evaluation_cache import EvaluationCache
from p3net.harness.runner import Runner
from p3net.problem.genotype import CategoricalDomain, Genotype, SearchSpace

import methods.external.mo_bohb as mo_bohb_module
import methods.external.tpe as tpe_module
from methods.external.mo_bohb import mo_bohb_method
from methods.external.tpe import tpe_method


def toy_space() -> SearchSpace:
    return SearchSpace(domains=(CategoricalDomain(values=(0, 1)),) * 6)


def always_valid(genotype: Genotype) -> float:
    return -1.0


def rejects_all_zero(genotype: Genotype) -> float:
    """A real, non-trivial constraint: invalid iff every coordinate is 0."""
    return -1.0 if any(genotype.values) else 1.0


def toy_objective(genotype: Genotype):
    total = sum(genotype.values)
    return (float(total), float(len(genotype.values) - total))


@pytest.mark.parametrize("factory_name", ["tpe", "mo_bohb"])
def test_each_wrapper_runs_a_full_budget_without_error(factory_name):
    space = toy_space()
    if factory_name == "tpe":
        method = tpe_method(space, always_valid, seed=0)
    else:
        method = mo_bohb_method(space, always_valid, random.Random(0))
    state = Runner(objective=toy_objective, budget=15).run(method)
    assert state.evaluations_used == 15


@pytest.mark.parametrize("factory_name", ["tpe", "mo_bohb"])
def test_each_wrapper_respects_the_dedup_cache(factory_name):
    space = toy_space()
    if factory_name == "tpe":
        method = tpe_method(space, always_valid, seed=1)
    else:
        method = mo_bohb_method(space, always_valid, random.Random(1))
    state = Runner(objective=toy_objective, budget=15).run(method)
    seen = [obs.genotype for obs in state.history]
    assert len(seen) == len(set(seen))


@pytest.mark.parametrize("factory_name", ["tpe", "mo_bohb"])
def test_each_wrapper_never_proposes_an_invalid_genotype(factory_name):
    space = toy_space()
    if factory_name == "tpe":
        method = tpe_method(space, rejects_all_zero, seed=2)
    else:
        method = mo_bohb_method(space, rejects_all_zero, random.Random(2))
    state = Runner(objective=toy_objective, budget=15).run(method)
    for obs in state.history:
        assert any(obs.genotype.values), "an all-zero (invalid) genotype was proposed"


def test_experiment_type_is_distinct_per_baseline_for_cache_isolation():
    space = toy_space()
    assert tpe_method(space, always_valid, seed=3).experiment_type == "tpe"
    assert mo_bohb_method(space, always_valid, random.Random(3)).experiment_type == "mo_bohb"


def test_tpe_supports_more_than_two_objectives():
    space = toy_space()

    def three_objective(genotype: Genotype):
        total = sum(genotype.values)
        return (float(total), float(len(genotype.values) - total), float(total**2))

    method = tpe_method(space, always_valid, n_objectives=3, seed=4)
    state = Runner(objective=three_objective, budget=10).run(method)
    assert state.evaluations_used == 10


def test_tpe_sample_records_internally_generated_duplicates_in_the_shared_cache(monkeypatch):
    """methods/external/tpe.py's sample() used to check cache.has(...) --
    a read-only lookup that never touches the shared duplication
    instrumentation -- whenever a freshly-sampled genotype turned out to
    already be in the cache, silently retrying without ever calling
    cache.record_proposal. Force a duplicate draw then a fresh one
    deterministically (optuna's real sampler draws aren't directly
    controllable) and assert the shared cache actually counted it."""
    space = SearchSpace(domains=(CategoricalDomain(values=(0, 1)),) * 2)
    cache = EvaluationCache()
    dup = Genotype(values=(0, 0))
    fresh = Genotype(values=(1, 1))
    cache.put(dup, (0.0, 0.0), experiment_type="tpe", protocol_version="v1")

    sequence = iter([dup, fresh])
    monkeypatch.setattr(
        tpe_module, "_suggest_genotype", lambda trial, search_space: next(sequence)
    )

    sample, _report = tpe_module.tpe_ask_tell(space, always_valid, cache, seed=0)
    result = sample()

    assert result == fresh
    assert cache._proposal_duplicates > 0


def test_mo_bohb_sample_records_internally_generated_duplicates_in_the_shared_cache(monkeypatch):
    """Same bug, same fix, for methods/external/mo_bohb.py's sample()."""
    space = SearchSpace(domains=(CategoricalDomain(values=(0, 1)),) * 2)
    cache = EvaluationCache()
    dup = Genotype(values=(0, 0))
    fresh = Genotype(values=(1, 1))
    cache.put(dup, (0.0, 0.0), experiment_type="mo_bohb", protocol_version="v1")

    sequence = iter([dup, fresh])
    monkeypatch.setattr(
        mo_bohb_module, "_config_to_genotype", lambda config, search_space: next(sequence)
    )

    sample, _report = mo_bohb_module.mo_bohb_ask_tell(
        space, always_valid, cache, rng=random.Random(0)
    )
    result = sample()

    assert result == fresh
    assert cache._proposal_duplicates > 0


def test_tchebycheff_scalarize_is_invariant_to_objective_rescaling():
    """2026-08-18 fix (Conclusions, CHANGELOG.md): without normalising
    objectives to a comparable scale before weighting, max(weighted) was
    dominated by whichever objective happened to have the larger raw
    scale almost regardless of the randomly drawn weight -- on
    NAS-HPO-Bench-II specifically, f2 is roughly 19x f1's scale, so
    max(weighted) was cost-dominated in the vast majority of calls,
    undermining the whole point of the random weight (a distribution of
    differently-emphasised scalarised landscapes, per the module
    docstring). After min-max normalising by the running per-objective
    range, the result must be exactly invariant to an objective's raw
    scale: min-max normalisation cancels out any positive linear
    rescaling exactly, so scaling f2 by 1000x with the same weight draws
    (same rng seed) must produce identical scalarised values."""
    history = [(0.1, 5.0), (0.9, 95.0), (0.5, 50.0), (0.3, 30.0), (0.7, 70.0)]
    scale = 1000.0

    mins_a: list[float] = []
    maxs_a: list[float] = []
    rng_a = random.Random(0)
    results_a = [
        mo_bohb_module._tchebycheff_scalarize((f1, f2), rng_a, mins_a, maxs_a)
        for f1, f2 in history
    ]

    mins_b: list[float] = []
    maxs_b: list[float] = []
    rng_b = random.Random(0)  # same seed -> identical weight draws
    results_b = [
        mo_bohb_module._tchebycheff_scalarize((f1, f2 * scale), rng_b, mins_b, maxs_b)
        for f1, f2 in history
    ]

    for a, b in zip(results_a, results_b):
        assert a == pytest.approx(b)


class _FixedSequenceRandom:
    """Minimal random.Random-like stub returning a fixed sequence of
    values from .random() -- deterministic control over
    _tchebycheff_scalarize's weight draws, for a direct behavioural
    check rather than only the scale-invariance property above."""

    def __init__(self, values: list[float]) -> None:
        self._values = iter(values)

    def random(self) -> float:
        return next(self._values)


def test_tchebycheff_scalarize_lets_a_dominant_weight_on_the_narrow_objective_win():
    """Direct behavioural check, not just the invariance property above:
    before normalising, a ~1000x raw scale gap (f2 up to 5000 here, f1 at
    most 0.9) meant max(weighted) was cost-dominated almost regardless of
    the drawn weight. With a controlled weight draw giving f1 nearly all
    the weight (0.99 vs 0.01), the *normalised* f1 term must now win --
    the property normalisation exists to restore."""
    mins: list[float] = []
    maxs: list[float] = []
    history = [(0.1, 5.0), (0.9, 5000.0), (0.5, 2500.0)]
    rng = random.Random(0)
    for f1, f2 in history:
        mo_bohb_module._tchebycheff_scalarize((f1, f2), rng, mins, maxs)
    # Range now established: f1 in [0.1, 0.9], f2 in [5.0, 5000.0].

    # raw_weights = [rng.random() + 1e-6, ...], then normalised to sum 1
    # -- feeding [0.99, 0.01] makes weights approximately [0.99, 0.01].
    controlled_rng = _FixedSequenceRandom([0.99, 0.01])
    result = mo_bohb_module._tchebycheff_scalarize((0.9, 2500.0), controlled_rng, mins, maxs)
    # f1=0.9 is the top of its own observed range -> normalised f1 = 1.0,
    # weighted ~= 0.99 (plus the rho*sum(weighted) augmentation term,
    # itself dominated by that same ~0.99). f2=2500.0 is the midpoint of
    # [5, 5000] -> normalised f2 ~= 0.5, weighted ~= 0.005. Loose bounds
    # deliberately, rather than a hand-computed exact float: the point is
    # that this lands nowhere near f2's raw ~2500 scale (or even the
    # unnormalised weighted value of ~25 the old, buggy version would
    # have produced here), not an exact augmented-Tchebycheff value.
    assert 0.9 < result < 1.2


def test_mo_bohb_method_reseeds_numpy_even_when_preceded_by_unrelated_draws():
    """hpbandster's real BOHB config generator has no seed/random_state
    parameter and draws from the GLOBAL numpy RNG (np.random.rand/
    randint/choice), uncontrolled by this project's own seed. Two
    mo_bohb_method instances built with the same seed, run back to back in
    the same process with unrelated np.random draws interleaved between
    them (as scripts/run_grid.py's single-process grid sweep would do),
    must still produce identical proposal sequences -- proving the fix
    actually reseeds at construction time rather than relying on
    incidental global state left over from process start."""
    space = toy_space()

    def run_once():
        method = mo_bohb_method(space, always_valid, random.Random(0), seed=123)
        state = Runner(objective=toy_objective, budget=10).run(method)
        return [obs.genotype for obs in state.history]

    genotypes_a = run_once()
    for _ in range(50):
        np.random.rand()
    genotypes_b = run_once()

    assert genotypes_a == genotypes_b
