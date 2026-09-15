"""PrzewozniczekP3ELyMPuS: P3-eLyMPuS (source paper's Table 5: second-best
of six compared optimisers, after the authors' own OLyMPuS) reconstructed
inside this harness, run against the SAME baseline set `p3net` itself is
compared against (notes/plans/experiments-przewozniczek-plan.md is this
module's full specification; Faza 4 is this file specifically).

Combines pieces already built and independently validated:

- `p3net.search_engines.p3.canonical_pyramid` -- the canonical, single-
  individual-climbing P3 engine, reused unmodified (same engine
  `methods.bartnik_p3.BartnikP3` in the sibling `experiments-bartnik`
  package drives).
- `p3net.search_engines.p3.fihc_elympus.fihc_elympus` -- First-Improvement
  Hill Climber driven by `p3net.surrogates.elympus.ELyMPuS`, this
  project's own k-ary generalisation of the source paper's binary partial-
  comparison mechanism (Faza 0-2 of the plan; see
  notes/lympus-nas-adaptation-literature.md and
  notes/lympus-nas-adaptation-validation.md for the literature check and
  synthetic validation this rests on -- validated savings are modest,
  11-13%, smaller than the source paper's own binary results, an honest,
  documented gap, not glossed over. **That 11-13% figure does not
  transfer to this class's own production wiring as-is**: it was measured
  (Check 3) with ONE `ELyMPuS` instance's cache reused across 30
  independent climbs, and that same note states a single cold-cache run
  "shows no meaningful savings by itself" -- savings accumulate only with
  sustained reuse. `_gated_climb_proposal` below builds one `ELyMPuS` per
  call and reuses it across at most `max_climb_attempts` (default 5)
  climbs before discarding it on the next `propose()` -- a reuse depth
  roughly 6x shallower than what produced 11-13%, structurally closer to
  the validation's disclosed near-zero-savings cold-cache regime than to
  the headline figure. This is a second, separate honesty gap from the
  "surrogate-predicted, not real, evaluations" one below -- not fixed
  here, since resolving it (e.g. persisting `elympus` across
  `_gated_climb_proposal` calls) would need re-litigating the "cached
  against one surrogate fit is not sound against the next" constraint
  documented at that construction site.).
- `p3net.surrogates.absolute_random_forest.AbsoluteRandomForestSurrogate`
  -- reused unmodified, for the same structural reason as `BartnikP3`
  (below).

**Why this method still needs a fitted surrogate, even though eLyMPuS is
itself described as a kind of surrogate**: `canonical_pyramid.climb`'s
`fitness_fn` parameter is called synchronously and directly, many times
per call (the hill-climb step, every GOM sweep proposal, every promotion
check) -- but this class, like every method under this harness's
`p3net.harness.runner.Method` protocol, has no direct access to the real
substrate; it can only request real evaluations by returning genotypes
from `propose()` for the harness's own `Runner` to evaluate and budget-
count. `climb()` therefore cannot be driven by real fitness at all inside
this integration; both climb's outer GOM/promotion loop AND ELyMPuS's own
internal fitness_fn (via `make_elympus_fitness_adapter`) are driven by an
`AbsoluteRandomForestSurrogate` fit on `self._history` -- exactly
`BartnikP3`'s "surrogate screens, real evaluation confirms" split, applied
here for a structural reason (no substrate access), not a design choice
this method made independently.

**Consequence, stated plainly**: within this specific harness integration,
the FFE savings the synthetic validation (Faza 2) measured for eLyMPuS are
savings in `AbsoluteRandomForestSurrogate.predict` calls during a climb,
not savings in real NATS-Bench queries -- those only ever happen once per
`propose()` call, on the single gated final candidate, same as
`BartnikP3`. The scientific question this method exists to test is
unaffected by this (whether the eLyMPuS-class linkage-discovery mechanism,
plugged into the same canonical pyramid and gate as `BartnikP3`, separates
from `random_search` where P3Net does not) -- but the "cheap comparisons
instead of expensive evaluations" framing from the source paper does not
carry over to real evaluation counts here, and this docstring says so
rather than letting the source paper's framing imply something this
integration doesn't deliver.

Acceptance gate, warm-up, and performance-characteristic caveats: identical
in shape and reasoning to `methods.bartnik_p3.BartnikP3` in the sibling
`experiments-bartnik` package (lambda-quantile gate reconstructed from
Dushatskiy's Algorithm 7/8 shape; ell-random warm-up, ell = search space
dimensionality; level 0 of the pyramid never shrinks, so per-run cost can
grow faster than linearly in budget on landscapes with many mutually
Pareto-nondominated pairs). Not re-derived here -- see that module's
docstring for the full reasoning, identical in this class.
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
from p3net.search_engines.p3.fihc_elympus import fihc_elympus, make_elympus_fitness_adapter
from p3net.surrogates.absolute_random_forest import AbsoluteRandomForestSurrogate
from p3net.surrogates.elympus import ELyMPuS

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
class PrzewozniczekP3ELyMPuS:
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
    #: Passed straight through to ELyMPuS(verify_probability=...). Non-zero
    #: is required for `dependencies` to ever grow past empty here, since
    #: this class starts every ELyMPuS instance with no seeded dependency
    #: graph (see `_gated_climb_proposal` and ELyMPuS's own module
    #: docstring for why this is opt-in rather than always-on: it trades
    #: extra real-surrogate-prediction calls for runtime discovery).
    elympus_verify_probability: float = 0.2
    experiment_type: str = "przewozniczek_p3elympus"
    protocol_version: str = "v1"
    cache: EvaluationCache = field(default_factory=EvaluationCache)

    _pyramid: CanonicalPyramid = field(init=False, repr=False)
    _history: dict[Genotype, Observation] = field(default_factory=dict, init=False, repr=False)
    _warmup_proposed: int = field(default=0, init=False, repr=False)
    _delta_window: list[float] = field(default_factory=list, init=False, repr=False)
    _tau: float = field(default=0.0, init=False, repr=False)
    #: The Pareto front's actual MEMBERSHIP, not just its size -- see
    #: methods.bartnik_p3.BartnikP3's identical field for the full
    #: reasoning (same bug shape, same fix, reported alongside this one).
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
        # path -- see methods.bartnik_p3.BartnikP3's identical guard for
        # the full reasoning (same warmup=0 crash, same fix).
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

        # Recorded unconditionally, BEFORE the warmup gate below: skipping
        # this during warmup (an earlier version returned before ever
        # reaching it) meant `_delta_window` was still empty the moment
        # warmup ended, so the first post-warmup `_reset_gate()` computed
        # `_quantile([], ...) == 0.0` (accept-everything) instead of using
        # the `warmup` real deltas that were actually available -- exactly
        # the data this window exists to hold.
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
        # `>=`, not `==` -- see methods.bartnik_p3.BartnikP3's identical
        # condition for why (warmup=0 would otherwise never seed level 0).
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
        self._tau -= (1.0 - self.eta) * max(abs(self._tau), 1.0)

    def _fit_surrogate(self) -> AbsoluteRandomForestSurrogate:
        # `random_state` drawn from `self.rng` -- see
        # methods.bartnik_p3.BartnikP3's identical fix for the full
        # reasoning (unseeded sklearn RNG otherwise defeats
        # reproducibility from `self.rng` alone).
        surrogate = AbsoluteRandomForestSurrogate(
            n_estimators=self.n_estimators, random_state=self.rng.randrange(2**31)
        )
        surrogate.fit(list(self._history.values()))
        return surrogate

    def _gated_climb_proposal(self) -> list[Genotype]:
        surrogate = self._fit_surrogate()
        best_real_f1 = min(obs.objectives[self.objective_index] for obs in self._history.values())

        # One ELyMPuS instance per surrogate fit (i.e. per _gated_climb_proposal
        # call), NOT per climb attempt: all `max_climb_attempts` climbs below
        # share the same `surrogate.predict` fitness landscape, so reusing one
        # instance across them is sound and lets its comparison cache AND its
        # discovered `dependencies` (see ELyMPuS.discover_missing_dependency)
        # actually accumulate within one call, instead of being thrown away
        # after a single climb -- a previous version constructed a fresh
        # ELyMPuS per attempt, which defeated both the caching this class'
        # own docstring describes and the runtime dependency discovery
        # `verify_probability` below exists to enable (without it,
        # `dependencies` never grows past empty at all -- see
        # ELyMPuS's own module docstring and
        # notes/lympus-nas-adaptation-validation.md). A fresh instance is
        # still built once per _gated_climb_proposal call because the
        # underlying surrogate itself is refit every call -- a comparison
        # cached against one surrogate fit is not guaranteed sound against
        # the next one.
        elympus = ELyMPuS(
            search_space=self.search_space,
            fitness_fn=make_elympus_fitness_adapter(surrogate.predict, objective_index=self.objective_index),
            verify_probability=self.elympus_verify_probability,
            rng=self.rng,
        )

        def _hill_climber(genotype: Genotype) -> Genotype:
            return fihc_elympus(genotype, self.search_space, elympus, self.rng, validity=self.validity)

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
                hill_climber=_hill_climber,
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
