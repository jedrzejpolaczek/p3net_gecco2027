"""BartnikP3: reconstruction of the algorithm class Bartnik
(`bartnik2026evolutionary`) showed separating from baselines on
architecture-only NAS-Bench-201 -- run here against the SAME baseline set
`p3net` itself is compared against (notes/plans/experiments-bartnik-plan.md
is this module's full specification; Faza 3 is this file specifically).

Combines three pieces, each already built and tested independently:

- `p3net.search_engines.p3.canonical_pyramid` -- the canonical, single-
  individual-climbing P3 engine (Goldman 2014, Algorithm 3/4 shape),
  reused unmodified.
- `p3net.surrogates.absolute_random_forest.AbsoluteRandomForestSurrogate`
  -- deterministic, per-objective Random Forest absolute surrogate,
  reused unmodified.
- A lambda-quantile acceptance gate, reconstructed from
  `dushatskiy2021novelsurrogateassistedevolutionaryalgorithm`'s Algorithm
  7/8 shape (same reconstruction-not-transcription caveat as
  `canonical_pyramid.py`'s own module docstring): a candidate's predicted
  improvement in f1 over the current best REAL f1 must clear a threshold
  tau, tau starts at the lambda-quantile of the window of real observed
  deltas so far (0.0, i.e. accept-everything, while that window is still
  empty -- mirrors `p3net.methods.p3net.P3Net`'s own "not enough data yet"
  bootstrap-optimistic rule), relaxes by a factor eta<1 every time a
  climb attempt has to fall back to a plain random genotype (nothing
  surrogate-suggested cleared the gate), and resets to a fresh quantile
  the moment the real Pareto front changes.

**Key architectural decision, not incidental** (see this module's own
propose()/update() below): the CanonicalPyramid this class drives is
climbed entirely against the SURROGATE's predicted objectives, never real
ones -- climbing FIHC/GOM needs a fitness call at every single step
(module docstring of canonical_pyramid.py), and spending a real evaluation
at every one of those steps would defeat the entire point of a surrogate-
assisted algorithm. Real evaluations are reserved for whatever a full
climb's FINAL candidate turns out to be, gated by the lambda-quantile
rule above -- exactly Dushatskiy's "surrogate screens, real evaluation
confirms" split, and structurally the same shape
`p3net.methods.p3net.P3Net._sweep_proposals`/`_tentatively_accept` already
use for their own (different) surrogate.

ell-random warm-up (Dushatskiy's own Algorithm 7): `warmup` real
evaluations of uniform random valid genotypes precede any surrogate/
pyramid activity at all -- there is no real data yet to fit a surrogate
from, and Dushatskiy's own algorithm requires exactly this before its main
loop starts. Defaults to the search space's own dimensionality (ell = n),
matching the plan's "ell = 6 dla architecture-only NAS-Bench-201" -- 6 is
this default falling out of `search_space.n`, not a hardcoded constant.

**Documented performance characteristic**: level 0 of `_pyramid` never
shrinks -- every climb attempt appends its bootstrap/entering individual
to whatever level it reaches (`canonical_pyramid.climb`'s own docstring),
so `build_linkage_tree` and a full GOM sweep are repeated over a level 0
population that grows across the whole run. On a landscape where most
candidate pairs are mutually Pareto-nondominated (ties are common when f2
takes few distinct values, e.g. FLOPs on NAS-Bench-201's small
architecture space), the permissive not-worse acceptance rule
(`canonical_pyramid._improves`) lets almost every climb reach the top and
grow a new level, and per-run cost grows faster than linearly in budget.
Real, not yet mitigated in v1 -- surfaced here rather than hidden, per
this project's own convention for known limitations (compare
`p3net.methods.p3net.P3Net`'s own module docstring).
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from p3net.harness.evaluation_cache import EvaluationCache
from p3net.harness.runner import Observation, RunState
from p3net.problem.decoding import Validity, is_valid
from p3net.problem.genotype import Genotype, SearchSpace
from p3net.problem.objectives import pareto_front
from p3net.search_engines.p3.canonical_pyramid import CanonicalPyramid, climb
from p3net.surrogates.absolute_random_forest import AbsoluteRandomForestSurrogate

from methods._shared import random_valid_batch


def _quantile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    data = sorted(values)
    index = min(len(data) - 1, max(0, round(q * (len(data) - 1))))
    return data[index]


@dataclass
class BartnikP3:
    search_space: SearchSpace
    validity: Validity
    rng: random.Random
    warmup: int | None = None
    lambda_quantile: float = 0.5
    eta: float = 0.999
    n_estimators: int = 100
    objective_index: int = 0
    max_climb_attempts: int = 5
    delta_window_size: int = 50
    experiment_type: str = "bartnik_p3"
    protocol_version: str = "v1"
    cache: EvaluationCache = field(default_factory=EvaluationCache)

    _pyramid: CanonicalPyramid = field(init=False, repr=False)
    _history: dict[Genotype, Observation] = field(default_factory=dict, init=False, repr=False)
    _warmup_proposed: int = field(default=0, init=False, repr=False)
    _delta_window: list[float] = field(default_factory=list, init=False, repr=False)
    _tau: float = field(default=0.0, init=False, repr=False)
    #: The Pareto front's actual MEMBERSHIP, not just its size -- a front
    #: whose composition changes (one elite replaced by another) while its
    #: cardinality stays the same must still reset the gate, per this
    #: class's own documented contract ("resets to a fresh quantile the
    #: moment the real Pareto front changes"). Comparing only `len(elites)`
    #: (an earlier version of this field) misses exactly that case, since
    #: Genotype is frozen/hashable and safe to put in a frozenset.
    _elite_set: frozenset[Genotype] = field(default_factory=frozenset, init=False, repr=False)
    _last_was_fallback: bool = field(default=False, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.warmup is None:
            self.warmup = self.search_space.n
        self._pyramid = CanonicalPyramid()
        self._pyramid.add_level()

    # -- harness.Method protocol ------------------------------------------

    def propose(self, state: RunState) -> list[Genotype]:
        # `not self._history`, not just `self.warmup`, gates the surrogate
        # path: an explicit `warmup=0` would otherwise call
        # `_gated_climb_proposal` -> `_fit_surrogate` on zero observations
        # on the very first call, crashing instead of falling back to a
        # random proposal (AbsoluteRandomForestSurrogate.fit rejects an
        # empty observation list by design).
        if self._warmup_proposed < self.warmup or not self._history:
            self._warmup_proposed += 1
            return self._random_valid_batch(1)
        return self._gated_climb_proposal()

    def update(self, state: RunState, new_observations: list[Observation]) -> None:
        for obs in new_observations:
            self.cache.put(
                obs.genotype,
                obs.objectives,
                experiment_type=self.experiment_type,
                protocol_version=self.protocol_version,
            )
            self._history[obs.genotype] = obs

        # Recorded unconditionally, BEFORE the warmup gate below -- see
        # methods.przewozniczek_p3elympus.PrzewozniczekP3ELyMPuS's
        # identical fix for the full reasoning (skipping this during
        # warmup left `_delta_window` empty at the moment warmup ended,
        # discarding real warmup deltas the first post-warmup
        # `_reset_gate()` should have used).
        for obs in new_observations:
            best_before = min(
                (o.objectives[self.objective_index] for o in self._history.values() if o is not obs),
                default=obs.objectives[self.objective_index],
            )
            self._delta_window.append(best_before - obs.objectives[self.objective_index])
        if len(self._delta_window) > self.delta_window_size:
            self._delta_window = self._delta_window[-self.delta_window_size :]

        if self._warmup_proposed < self.warmup:
            return
        # `>=`, not `==`: with `warmup=0` the `not self._history` guard in
        # propose() forces `_warmup_proposed` to 1 before this ever runs,
        # so `== 0` would never fire again and level 0 would never get its
        # one-time bulk seed from `self._history` at all.
        if self._warmup_proposed >= self.warmup and not self._pyramid.levels[0].population:
            self._pyramid.levels[0].population = list(self._history.keys())

        elites = pareto_front(list(self._history.keys()), lambda g: self._history[g].objectives)

        elite_set = frozenset(elites)
        if elite_set != self._elite_set:
            self._elite_set = elite_set
            self._reset_gate()
        elif self._last_was_fallback:
            self._register_fallback()

    # -- internals ---------------------------------------------------------

    def _random_valid_batch(self, n: int) -> list[Genotype]:
        return random_valid_batch(
            n,
            self.search_space,
            self.validity,
            self.rng,
            self.cache,
            experiment_type=self.experiment_type,
            protocol_version=self.protocol_version,
        )

    def _quantile_threshold(self) -> float:
        return _quantile(self._delta_window, self.lambda_quantile)

    def _reset_gate(self) -> None:
        self._tau = self._quantile_threshold()

    def _register_fallback(self) -> None:
        # Multiplying tau by eta<1 only relaxes the gate (makes it easier
        # to clear) when tau is positive -- for a negative tau (the common
        # case: `best_real_f1 - predicted_f1` is usually negative for most
        # candidates), multiplying by eta<1 shrinks its magnitude, which
        # moves it TOWARD zero, i.e. makes the gate stricter, exactly
        # backwards. Subtracting a decaying, sign-agnostic margin instead
        # always moves tau down (always easier to clear), regardless of
        # its current sign.
        self._tau -= (1.0 - self.eta) * max(abs(self._tau), 1.0)

    def _fit_surrogate(self) -> AbsoluteRandomForestSurrogate:
        # `random_state` drawn from `self.rng`, not left at its `None`
        # default: without it, sklearn's RandomForestRegressor draws its
        # bootstrap/feature-selection randomness from unseeded global
        # state, so two runs sharing the same `rng` seed would still fit
        # different trees on every refit and diverge from there --
        # breaking reproducibility despite `self.rng` being seeded.
        surrogate = AbsoluteRandomForestSurrogate(
            n_estimators=self.n_estimators, random_state=self.rng.randrange(2**31)
        )
        surrogate.fit(list(self._history.values()))
        return surrogate

    def _gated_climb_proposal(self) -> list[Genotype]:
        surrogate = self._fit_surrogate()
        best_real_f1 = min(obs.objectives[self.objective_index] for obs in self._history.values())

        for _ in range(self.max_climb_attempts):
            start = self.search_space.sample_uniform(self.rng)
            if not is_valid(start, self.validity):
                continue
            candidate = climb(
                start,
                self._pyramid,
                search_space=self.search_space,
                fitness_fn=surrogate.predict,
                rng=self.rng,
                validity=self.validity,
            )
            predicted_f1 = surrogate.predict(candidate)[self.objective_index]
            predicted_delta = best_real_f1 - predicted_f1
            if predicted_delta < self._tau:
                continue
            if self.cache.record_proposal(
                candidate, experiment_type=self.experiment_type, protocol_version=self.protocol_version
            ):
                continue
            self._last_was_fallback = False
            return [candidate]

        self._last_was_fallback = True
        return self._random_valid_batch(1)
