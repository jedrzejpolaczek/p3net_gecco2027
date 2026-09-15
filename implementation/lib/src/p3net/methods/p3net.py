"""P3Net: P3 engine + relative, linkage-aware surrogate delta_hat_F.

Known simplifications in this implementation, documented rather than
silently shipped:

1. **Single active level at a time, not full simultaneous cross-level
   cascading.** `search_engines/p3/pyramid.py`'s `Pyramid` IS wired in
   here (2026-08-15): population size is no longer a constructor
   argument -- level 0 starts at `growth_factor` individuals and a new,
   larger level is grown automatically once the current level's sweep
   passes stop improving (`Pyramid.all_stalled`), genuinely
   "parameter-less". What's still simplified relative to the canonical
   P3/GOMEA pyramid: only the newest level is actively swept at a time.
   Canonical P3 keeps every level live, cascading a single new solution's
   improvement attempt upward through all of them; here, once a level
   stalls and a new one is grown, the old level's population is frozen
   (its observations remain in H_t, but it is never swept again). An
   every-level-simultaneous-cascade variant was implemented and measured
   (R=30, 4 datasets x 4 budgets): mixed, dataset-dependent results (one
   significant win on Colorectal-Histology, neutral-to-negative on
   CIFAR-10, non-significantly worse on Fashion-MNIST at the smallest
   budget), plus a real per-iteration compute cost (the surrogate is
   refit and the linkage tree rebuilt once per active level rather than
   once total). Not adopted; left as a candidate for a dedicated,
   better-powered follow-up rather than a default (Results, Findings;
   Conclusions, Future directions).
2. **Stall recovery within one sweep pass is random reinjection, not
   forced pyramid growth.** If a single sweep pass's C* ends up empty
   after dedup (every candidate that pass produced was already fully
   evaluated), this class falls back to proposing a small batch of fresh
   random valid genotypes for *that pass*, so the search keeps spending
   its budget rather than halting outright. This is a different, narrower
   situation than simplification 1's pyramid growth (which triggers on a
   pass completing without any real improvement, not on a pass producing
   zero *proposals*). A forced-growth alternative was implemented and
   measured alongside the cascade variant above: no significant
   difference anywhere in the same grid, so reinjection stays the default
   (Results, Findings).

Also empirically tested and confirmed as the retained default in that
same measurement round: population truncation via nondominated sort
(rather than a single-objective sort on f1 alone) once a pyramid level
exceeds its target size, and h_t-only donor provenance during the
optimal-mixing sweep (rather than also allowing transient, not-yet-fully-
evaluated donors from earlier in the same iteration) -- both showed no
significant difference in fixed-budget hypervolume, so both stay exactly
as originally designed. f2 (analytic cost) is always freshly computed
during C* selection now (see `analytic_cost` below); an earlier variant
that instead inherited it from the ancestor showed a consistent,
partly-significant improvement in favour of the fresh computation and was
adopted as the only behaviour, closing what had been "Known
simplification 2" here.
"""

from __future__ import annotations

import logging
import math
import random
import time
from collections.abc import Callable, Collection
from dataclasses import dataclass, field
from typing import Any

from p3net.harness.decision_log import DecisionLog
from p3net.harness.evaluation_cache import EvaluationCache
from p3net.harness.runner import Observation, RunState
from p3net.problem.decoding import Validity, is_valid
from p3net.problem.genotype import Genotype, SearchSpace
from p3net.problem.objectives import Objectives, dominates, pareto_front, select_survivors
from p3net.search_engines.p3.canonical_pyramid import _first_improvement_hill_climb
from p3net.search_engines.p3.fihc_elympus import fihc_elympus
from p3net.search_engines.p3.linkage_tree import build_linkage_tree, linkage_subsets
from p3net.search_engines.p3.optimal_mixing import SweepState
from p3net.search_engines.p3.pyramid import Pyramid, PyramidLevel
from p3net.surrogates.absolute_random_forest import AbsoluteRandomForestSurrogate
from p3net.surrogates.absolute_regressor import AbsoluteRegressorSurrogate
from p3net.surrogates.elympus import ELyMPuS
from p3net.surrogates.relative_linkage_aware import (
    NoLinkageTreeError,
    RelativeLinkageAwareSurrogate,
)
from p3net.surrogates.telescoping import AncestorNotEvaluatedError, ChainStep, telescoped_estimate

logger = logging.getLogger(__name__)


class _LinearAsObjectives:
    """AbsoluteRegressorSurrogate predicts f1 only; expose it with the
    forest's Objectives-shaped predict (only index `objective_index` is ever
    read from an absolute prediction)."""

    def __init__(self, regressor: AbsoluteRegressorSurrogate, objective_index: int) -> None:
        self._regressor = regressor
        self._width = objective_index + 1

    def predict(self, genotype: Genotype) -> Objectives:
        return (self._regressor.predict(genotype),) * self._width


class _MemoisedForest:
    """Memoises AbsoluteRandomForestSurrogate.predict for one fit. Hill
    climbing and eLyMPuS query the same genotypes many times within one sweep
    call; a forest prediction is deterministic for a fixed fit, so caching is
    exact."""

    def __init__(self, forest: AbsoluteRandomForestSurrogate) -> None:
        self._forest = forest
        self._cache: dict[Genotype, Objectives] = {}

    def predict(self, genotype: Genotype) -> Objectives:
        cached = self._cache.get(genotype)
        if cached is None:
            cached = self._forest.predict(genotype)
            self._cache[genotype] = cached
        return cached


@dataclass
class P3Net:
    """P3Net: P3's optimal-mixing sweep scored by the relative,
    linkage-aware surrogate delta_hat_F, wired into the harness.Method
    protocol (propose/update) so it can be driven by harness.Runner.
    Operates exclusively at whatever single fidelity level the objective
    function passed to Runner represents -- the fidelity ladder is not
    consumed here.
    """

    search_space: SearchSpace
    validity: Validity
    model_factory: Callable[[], Any]
    rng: random.Random
    growth_factor: int = 2
    kappa: int | None = None
    acceptance_threshold: float = 0.0
    objective_index: int = 0
    #: Single-axis ablation (2026-08-18, Phase 4 of the pyramid/surrogate
    #: fix plan; configs/methods/p3net_surrogate_interactions.yaml):
    #: threaded into RelativeLinkageAwareSurrogate.include_interactions
    #: below. Default False keeps p3net.yaml's own behaviour unchanged.
    use_surrogate_interactions: bool = False
    #: Design-decision ablation axes (restored 2026-09-13 to re-validate the
    #: 2026-08-16 ablation round on the post-pyramid-fix engine; review
    #: finding P4). Every default reproduces this class's single retained
    #: behaviour exactly, so p3net.yaml is unaffected -- the regression test
    #: tests/test_p3net_design_variants.py pins that. Each non-default value
    #: is the variant the 2026-08-16 round measured, ported onto the current
    #: engine (warm-started levels, hypervolume-contribution stall rule).
    #:
    #: truncation: "pareto" = nondominated sort + crowding distance when a
    #: level exceeds its target size; "f1_sort" = single-objective sort on f1.
    truncation: str = "pareto"
    #: stall_recovery: when one sweep pass's C* is empty after dedup,
    #: "reinject" random diversity into the current level, or "grow" = mark
    #: the level stalled and grow (and warm-start) a new level immediately.
    stall_recovery: str = "reinject"
    #: donor_pool: "h_t_only" = donors drawn from real H_t members only;
    #: "transient" = later parents in the same iteration may also use an
    #: earlier parent's not-yet-evaluated sweep outcome as a donor.
    donor_pool: str = "h_t_only"
    #: cascade: False = only the newest level is swept; True = every level
    #: bootstraps/sweeps on every propose() call, observations routed back
    #: to the level that proposed them.
    cascade: bool = False
    #: Design-evolution stages (restored 2026-09-14 so every stage of the
    #: paper's Design Evolution section is a configuration of one codebase,
    #: re-runnable with full diagnostics). Defaults are the current engine.
    #:
    #: level_init: how a newly grown pyramid level starts. "warm" = seeded
    #: from H_t's current nondominated front (adopted 2026-08-18); "empty" =
    #: filled purely by uniform random sampling (the original engine).
    level_init: str = "warm"
    #: stall_criterion: when a sweep pass counts as improving its level.
    #: "hypervolume" = the pass's best result increases the level
    #: population's hypervolume (adopted 2026-08-18); "dominance" = it must
    #: strictly Pareto-dominate the level's single best incumbent (the
    #: original engine).
    stall_criterion: str = "hypervolume"
    #: bootstrap_threshold: population size at which a level stops random
    #: bootstrap and starts optimal mixing. "level_size" = the level's full
    #: geometric target (the current engine); "growth_factor" = level 0's own
    #: size for every level -- the "start mixing much sooner, like canonical
    #: P3" attempt of 2026-08-18, reverted after a unit test showed runaway
    #: level growth. Restored as a documented dead end, never as a default.
    bootstrap_threshold: str = "level_size"
    #: Surrogate variants (P3Net-Bartnik / P3Net-eLyMPuS, v0.0.4 plan M7/M8).
    #:
    #: surrogate_kind: "relative" = delta_hat_F (default, P3Net itself);
    #: "absolute_rf" = an absolute random forest per objective
    #: (p3net.surrogates.absolute_random_forest, the nonlinear surrogate of
    #: this project's Bartnik reconstruction), refit once per sweep call.
    #: A proposed modification is tentatively accepted iff the forest's
    #: predicted f1 improves on the current individual's value by at least
    #: acceptance_threshold (the current value starts as the parent's real f1
    #: and becomes the prediction once a step is accepted) -- the same rule
    #: as experiments' P3Absolute.
    #: "absolute_linear" = the same rule with an absolute regressor built from
    #: `model_factory` over the one-hot genotype
    #: (p3net.surrogates.absolute_regressor, P3Absolute's surrogate) -- the
    #: surrogate-only ablation of the final engine: same model class as the
    #: relative surrogate, only relative + linkage-aware vs absolute differs.
    surrogate_kind: str = "relative"
    #: hill_climber (requires surrogate_kind="absolute_rf"): optional local
    #: refinement of every sweep outcome before C* selection, driven by the
    #: forest's predicted f1 (one scalar objective for every option, so the
    #: options differ only in the comparison mechanism). "none" = no
    #: refinement; "fihc" = plain first-improvement hill climbing;
    #: "fihc_elympus" = the same climb with acceptance decided by eLyMPuS
    #: partial comparisons (p3net.search_engines.p3.fihc_elympus) -- how
    #: P3-eLyMPuS uses eLyMPuS, since eLyMPuS compares single-variable
    #: changes, not whole linkage-subset changes.
    hill_climber: str = "none"
    rf_n_estimators: int = 100
    #: Passed to ELyMPuS(verify_probability=...); must be > 0 for eLyMPuS to
    #: discover any dependency (it starts from an empty graph here), same
    #: value as experiments' PrzewozniczekP3ELyMPuS.
    elympus_verify_probability: float = 0.2
    #: Every objective other than f1 (index `objective_index`) is computed
    #: fresh for each candidate during C* selection via this callable
    #: (`Callable[[Genotype], Objectives]`), matching the search loop's own
    #: description (Section "Deduplication": C* selection uses
    #: nondomination in (f_hat_1, f2), with f2 computed analytically per
    #: candidate without a full evaluation). `None` inherits every non-f1
    #: objective from the ancestor's value instead -- correct and complete
    #: for single-objective use, where no such callable is needed.
    analytic_cost: Callable[[Genotype], Objectives] | None = None
    experiment_type: str = "p3net"
    protocol_version: str = "v1"
    cache: EvaluationCache = field(default_factory=EvaluationCache)

    #: Uniform sample of surrogate accept/reject decisions, checked against
    #: the benchmark after the run (p3net.harness.decision_log). Never
    #: influences the search.
    decision_log: DecisionLog = field(default_factory=DecisionLog, init=False, repr=False)

    _pyramid: Pyramid = field(init=False, repr=False)
    _history: dict[Genotype, Observation] = field(default_factory=dict, init=False, repr=False)

    #: (|H_t| at proposal time, predicted delta, true delta) for every
    #: proposal that was actually scored by a fitted surrogate and later
    #: really evaluated -- the live-search surrogate-quality signal
    #: chapters/v003/results/main.tex's "Surrogate quality" paragraph asks
    #: for, since a post-hoc refit on the persisted final H_t alone cannot
    #: reproduce what delta_hat_F predicted *at the time* (Results,
    #: Findings). Bootstrap-phase and stall/diversity-injection proposals
    #: (no surrogate involved) never appear here. Public so
    #: scripts/run_experiment.py's diagnostics capture can read it the same
    #: way it already reads sweeps_completed/duplication_rate.
    surrogate_quality_log: list[tuple[int, float, float]] = field(
        default_factory=list, init=False, repr=False
    )
    #: Telescoping chain length for each surrogate_quality_log entry, same
    #: order, same length -- a parallel list rather than widening that
    #: tuple's shape, so nothing that already unpacks it as a 3-tuple
    #: breaks (2026-08-17, following up on Results' magnitude-calibration
    #: finding: wild predicted-delta outliers cluster tightly around one
    #: |H_t| window in every search space, and telescoped_estimate sums one
    #: delta_hat_F call per chain step, so a longer chain sums more
    #: independent prediction errors into one final estimate).
    chain_depth_log: list[int] = field(default_factory=list, init=False, repr=False)
    #: The sweeping level's target size at scoring time, same order/length
    #: as surrogate_quality_log -- follow-up to chain_depth_log: does the
    #: |H_t| ~ 30-58 magnitude-outlier window line up with a specific
    #: pyramid level (e.g. a level's first sweep pass right after its own
    #: bootstrap completes) rather than being explained by chain depth or
    #: raw |H_t| alone.
    level_size_log: list[int] = field(default_factory=list, init=False, repr=False)
    _pending_predictions: dict[Genotype, tuple[float, float, int, int, int]] = field(
        default_factory=dict, init=False, repr=False
    )
    #: cascade=True only: which pyramid level each proposed, not-yet-observed
    #: genotype came from, so update() routes each observation back to it.
    _pending_level: dict[Genotype, int] = field(default_factory=dict, init=False, repr=False)

    #: Diagnostics (2026-08-17): counts and component-level timings this
    #: session's own investigation had to reconstruct via ad-hoc
    #: instrumented replay, promoted to first-class fields so a pyramid
    #: fix's effect is verifiable directly from persisted results/raw/
    #: without repeating that exercise (Results, "Diagnostics: population-
    #: pyramid bootstrap share"). bootstrap_proposals/mixing_proposals
    #: count genotypes returned by _bootstrap_proposals/_sweep_proposals
    #: respectively -- the same "uniform-random-bootstrap" vs "mixing-
    #: driven" split already used in that Results paragraph.
    #: surrogate_fit_seconds/linkage_tree_seconds are component overhead,
    #: not end-to-end wall-clock (the project's "cost accounted in calls
    #: to f1" premise stays the headline metric) -- they exist to answer
    #: whether that overhead is large enough to matter when choosing a
    #: heavier surrogate model class. population_snapshots records the
    #: current level's population (a copy, so later mutation doesn't alter
    #: already-recorded snapshots) once per _update_level_population call --
    #: exactly the `list[list[Genotype]]` shape the experiments package's
    #: `metrics.diagnostics.archive_turnover` already accepts and is
    #: already tested against (that function existed with no caller able
    #: to supply real data -- "Known gaps", CHANGELOG.md -- this closes
    #: that gap by capturing the data here, not by re-deriving the
    #: turnover logic, which stays in the experiments package this
    #: library intentionally has no dependency on).
    bootstrap_proposals: int = field(default=0, init=False, repr=False)
    mixing_proposals: int = field(default=0, init=False, repr=False)
    surrogate_fit_seconds: float = field(default=0.0, init=False, repr=False)
    linkage_tree_seconds: float = field(default=0.0, init=False, repr=False)
    population_snapshots: list[list[Genotype]] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.truncation not in ("pareto", "f1_sort"):
            raise ValueError(f"unknown truncation strategy {self.truncation!r}")
        if self.stall_recovery not in ("reinject", "grow"):
            raise ValueError(f"unknown stall_recovery strategy {self.stall_recovery!r}")
        if self.donor_pool not in ("h_t_only", "transient"):
            raise ValueError(f"unknown donor_pool strategy {self.donor_pool!r}")
        if self.level_init not in ("warm", "empty"):
            raise ValueError(f"unknown level_init {self.level_init!r}")
        if self.stall_criterion not in ("hypervolume", "dominance"):
            raise ValueError(f"unknown stall_criterion {self.stall_criterion!r}")
        if self.bootstrap_threshold not in ("level_size", "growth_factor"):
            raise ValueError(f"unknown bootstrap_threshold {self.bootstrap_threshold!r}")
        if self.surrogate_kind not in ("relative", "absolute_rf", "absolute_linear"):
            raise ValueError(f"unknown surrogate_kind {self.surrogate_kind!r}")
        if self.hill_climber not in ("none", "fihc", "fihc_elympus"):
            raise ValueError(f"unknown hill_climber {self.hill_climber!r}")
        if self.hill_climber != "none" and self.surrogate_kind != "absolute_rf":
            raise ValueError("hill_climber requires surrogate_kind='absolute_rf'")
        if self.kappa is None:
            n = max(self.search_space.n, 2)
            self.kappa = 2 * math.ceil(math.log2(n))
        self._pyramid = Pyramid(growth_factor=self.growth_factor)
        self._pyramid.add_level()

    @property
    def _level(self) -> PyramidLevel:
        return self._pyramid.levels[-1]

    @property
    def _level_index(self) -> int:
        return len(self._pyramid.levels) - 1

    # -- harness.Method protocol ------------------------------------------

    def propose(self, state: RunState) -> list[Genotype]:
        if self._pyramid.all_stalled:
            self._grow_level()
        if not self.cascade:
            level = self._level
            if len(level.population) < self._bootstrap_target(level):
                return self._bootstrap_proposals(level)
            return self._sweep_proposals(level)

        # cascade=True: every level, old and new, proposes on every call.
        # Levels propose independently, so two of them can produce the same
        # not-yet-evaluated genotype in one batch; `batch` is passed down as
        # the cache's `pending` set so a later level never re-proposes what
        # an earlier level already has (otherwise the Runner evaluates it
        # twice -- observed in 61 of 480 runs before this fix).
        proposals: list[Genotype] = []
        batch: set[Genotype] = set()
        for level_index, level in enumerate(self._pyramid.levels):
            if len(level.population) < self._bootstrap_target(level):
                level_proposals = self._bootstrap_proposals(level, exclude=batch)
            else:
                level_proposals = self._sweep_proposals(level, exclude=batch)
            for g in level_proposals:
                self._pending_level[g] = level_index
                batch.add(g)
            proposals.extend(level_proposals)
        return proposals

    def update(self, state: RunState, new_observations: list[Observation]) -> None:
        for obs in new_observations:
            self.cache.put(
                obs.genotype,
                obs.objectives,
                experiment_type=self.experiment_type,
                protocol_version=self.protocol_version,
            )
            self._history[obs.genotype] = obs
            pending = self._pending_predictions.pop(obs.genotype, None)
            if pending is not None:
                predicted_f1, ancestor_f1, history_size, chain_depth, level_size = pending
                self.surrogate_quality_log.append(
                    (
                        history_size,
                        ancestor_f1 - predicted_f1,  # predicted delta
                        ancestor_f1 - obs.objectives[self.objective_index],  # true delta
                    )
                )
                self.chain_depth_log.append(chain_depth)
                self.level_size_log.append(level_size)

        if not self.cascade:
            self._update_level_population(self._level, self._level_index, new_observations)
            return

        # cascade=True: route each observation back to the level that
        # proposed it, then apply the per-level logic once per level.
        by_level: dict[int, list[Observation]] = {}
        for obs in new_observations:
            level_index = self._pending_level.pop(obs.genotype, self._level_index)
            by_level.setdefault(level_index, []).append(obs)
        for level_index, group in by_level.items():
            self._update_level_population(self._pyramid.levels[level_index], level_index, group)

    def _update_level_population(
        self, level: PyramidLevel, level_index: int, new_observations: list[Observation]
    ) -> None:
        """The bootstrap/promote/truncate logic for one pyramid level's
        share of one update() call."""
        bootstrapping = len(level.population) < self._bootstrap_target(level)

        if bootstrapping:
            # No established population to compare against yet -- fill
            # the level directly, no promote()/stall judgement (see
            # _seed_best_objectives below for how the baseline gets set
            # once bootstrap completes).
            for obs in new_observations:
                if obs.genotype not in level.population:
                    level.population.append(obs.genotype)
            if len(level.population) >= self._bootstrap_target(level):
                self._seed_best_objectives(level)
        else:
            # One promote() call per sweep pass (not per observation):
            # a pass's real outcome is its single best result, by Pareto
            # dominance -- calling promote() once per observation in a
            # mixed improve/non-improve batch would let a later
            # non-improving call overwrite an earlier improving one's
            # "not stalled" signal, incorrectly marking a genuinely
            # improving pass as stalled.
            best_obs = new_observations[0]
            for obs in new_observations[1:]:
                if dominates(obs.objectives, best_obs.objectives):
                    best_obs = obs
            # Every OTHER genotype already at this level, before this
            # update's new_observations are appended below -- Pyramid
            # doesn't track objectives itself (module docstring change,
            # 2026-08-18), only P3Net's own _history does.
            population_objectives = [self._history[g].objectives for g in level.population]
            self._pyramid.promote(
                level_index,
                best_obs.genotype,
                best_obs.objectives,
                population_objectives=population_objectives,
                criterion=self.stall_criterion,
            )
            for obs in new_observations:
                if obs.genotype not in level.population:
                    level.population.append(obs.genotype)

        if len(level.population) > level.size:
            # Multi-objective survivor selection (nondominated sort +
            # crowding distance), not a single-objective sort on f1 alone
            # -- the latter would silently discard genotypes that are
            # Pareto-optimal overall just because another genotype happens
            # to beat them on objective_index, narrowing the population's
            # diversity along every other objective over time. Measured
            # against an f1-only sort (truncation="f1_sort", the ablation
            # variant) on the pre-pyramid-fix engine: no significant
            # difference; re-validation on the current engine pending.
            if self.truncation == "f1_sort":
                level.population.sort(
                    key=lambda g: self._history[g].objectives[self.objective_index]
                )
                level.population = level.population[: level.size]
            else:
                level.population = select_survivors(
                    level.population, lambda g: self._history[g].objectives, level.size
                )

        self.population_snapshots.append(list(level.population))

    # -- internals ---------------------------------------------------------

    def _bootstrap_target(self, level: PyramidLevel) -> int:
        """Population size at which `level` leaves random bootstrap and
        starts optimal mixing (see `bootstrap_threshold`)."""
        if self.bootstrap_threshold == "growth_factor":
            return min(level.size, self.growth_factor)
        return level.size

    def _grow_level(self) -> PyramidLevel:
        """Add the next pyramid level, warm-started or empty per
        `level_init`."""
        level = self._pyramid.add_level()
        if self.level_init == "warm":
            self._warm_start_level(level)
        return level

    def _warm_start_level(self, level: PyramidLevel) -> None:
        """Seed a newly-grown level with the current nondominated front
        from H_t, rather than starting purely random (2026-08-18,
        Conclusions: adopted alongside the hypervolume-contribution
        stall criterion below -- warm-starting alone would make strict
        dominance even harder to clear, so the two are paired). These
        genotypes are already evaluated, so this costs zero fresh
        evaluation budget, and moves the implementation closer to
        canonical P3's cascading (module docstring, "Known simplification
        1"). Deliberately parameter-free: no elite count to choose --
        it's "the whole current front, capped to the new level's own
        size" via the same nondominated-sort-plus-crowding-distance rule
        population truncation already uses (_update_level_population,
        below) if the front is larger than the level. A no-op on the
        very first level (H_t is still empty at construction time),
        leaving _bootstrap_proposals's plain random fill as the only
        source for a level that has nothing yet to warm-start from.
        """
        if not self._history:
            return
        elites = pareto_front(list(self._history.keys()), lambda g: self._history[g].objectives)
        if len(elites) > level.size:
            elites = select_survivors(elites, lambda g: self._history[g].objectives, level.size)
        level.population = list(elites)
        self._seed_best_objectives(level)

    def _seed_best_objectives(self, level: PyramidLevel) -> None:
        """Fold the just-completed bootstrap population down to its
        single best (by Pareto dominance) to give promote() a real
        baseline for the level's first post-bootstrap sweep pass --
        without this, that first pass would always count as "improving"
        simply because best_objectives was still None."""
        best: Genotype | None = None
        for g in level.population:
            obj = self._history[g].objectives
            if best is None or dominates(obj, self._history[best].objectives):
                best = g
        if best is not None:
            level.best_objectives = self._history[best].objectives

    def _bootstrap_proposals(
        self, level: PyramidLevel, exclude: Collection[Genotype] = ()
    ) -> list[Genotype]:
        """No linkage tree or surrogate can exist yet -- propose uniform
        random valid genotypes until this level reaches its target
        size. `exclude`: genotypes already proposed earlier in the same
        batch (cascade only; empty otherwise)."""
        needed = self._bootstrap_target(level) - len(level.population)
        proposals = self._diversity_injection(n=needed, exclude=exclude)
        self.bootstrap_proposals += len(proposals)
        return proposals

    def _sweep_proposals(
        self, level: PyramidLevel, exclude: Collection[Genotype] = ()
    ) -> list[Genotype]:
        # Step 6 (of the *previous* iteration): the tree and surrogate are
        # rebuilt once here, at the start of this iteration, and reused for
        # every parent's sweep below (steps 1-3) -- never rebuilt mid-sweep.
        tree_start = time.perf_counter()
        linkage_root = build_linkage_tree(level.population)
        self.linkage_tree_seconds += time.perf_counter() - tree_start
        subsets = linkage_subsets(linkage_root)
        surrogate: RelativeLinkageAwareSurrogate | None = None
        absolute: _MemoisedForest | None = None
        refine: Callable[[Genotype], Genotype] | None = None
        if self.surrogate_kind == "absolute_rf":
            absolute = self._fit_absolute_surrogate()
            refine = self._make_refiner(absolute)
        elif self.surrogate_kind == "absolute_linear":
            absolute = self._fit_absolute_linear_surrogate()
        else:
            surrogate = RelativeLinkageAwareSurrogate(
                model_factory=self.model_factory,
                include_interactions=self.use_surrogate_interactions,
            )
            try:
                fit_start = time.perf_counter()
                surrogate.fit(
                    list(self._history.values()), subsets, objective_index=self.objective_index
                )
                self.surrogate_fit_seconds += time.perf_counter() - fit_start
            except NoLinkageTreeError:
                logger.debug(
                    "not enough pairwise data to fit delta_hat_F this iteration "
                    "(population=%d); proceeding without a surrogate",
                    len(level.population),
                )
                surrogate = None

        # Steps 1-3: sweep every parent; candidate_estimates collects each
        # sweep's final individual and its (surrogate- or exactly-known)
        # estimated objectives, scoped to this iteration only.
        # candidate_ancestors parallels it (surrogate-quality logging below
        # needs each candidate's ancestor's REAL f1, already known from H_t).
        candidate_estimates: dict[Genotype, Objectives] = {}
        candidate_ancestors: dict[Genotype, Genotype] = {}
        candidate_chain_depths: dict[Genotype, int] = {}
        # Donor provenance (module docstring): by default every parent's
        # sweep draws donors only from level.population (real H_t members),
        # matching the parent/ancestor-x0 restriction the paper states.
        # donor_pool="transient" additionally exposes each earlier parent's
        # just-produced, not-yet-evaluated sweep outcome as a donor to every
        # LATER parent in this same iteration (the ablation variant).
        transient_pool: list[Genotype] = []
        for parent in level.population:
            ancestor = self._history[parent]
            donor_population = (
                level.population
                if self.donor_pool == "h_t_only"
                else list(level.population) + transient_pool
            )
            sweep = SweepState.start(parent, linkage_root, donor_population, self.rng)
            chain: list[ChainStep] = []
            current_estimate: Objectives = ancestor.objectives
            while not sweep.done:
                proposal = sweep.propose()
                if not is_valid(proposal.candidate, self.validity):
                    sweep.reject(proposal)
                    continue
                trial_chain = chain + [
                    ChainStep(
                        x_prev=proposal.parent, x_next=proposal.candidate, subset=proposal.subset
                    )
                ]
                oi = self.objective_index
                if absolute is not None:
                    accept, trial_estimate = self._accept_absolute(
                        absolute, ancestor, current_estimate, proposal.candidate
                    )
                    self.decision_log.improvement(
                        source="mixing",
                        reference=proposal.parent,
                        candidate=proposal.candidate,
                        predicted_improvement=current_estimate[oi] - trial_estimate[oi],
                        threshold=self.acceptance_threshold,
                        accepted=accept,
                    )
                else:
                    accept, trial_estimate = self._tentatively_accept(
                        surrogate, ancestor, trial_chain, proposal.candidate
                    )
                    if surrogate is not None:
                        self.decision_log.improvement(
                            source="mixing",
                            reference=ancestor.genotype,
                            candidate=proposal.candidate,
                            predicted_improvement=ancestor.objectives[oi] - trial_estimate[oi],
                            threshold=self.acceptance_threshold,
                            accepted=accept,
                        )
                if accept:
                    chain = trial_chain
                    sweep.accept(proposal)
                    current_estimate = trial_estimate
                    if len(chain) >= self.kappa:
                        break
                else:
                    sweep.reject(proposal)
            outcome = sweep.current
            if refine is not None and absolute is not None:
                refined = refine(outcome)
                if refined != outcome:
                    outcome = refined
                    current_estimate = self._absolute_estimate(absolute, ancestor, refined)
            candidate_estimates[outcome] = current_estimate
            candidate_ancestors[outcome] = parent
            candidate_chain_depths[outcome] = len(chain)
            if self.donor_pool == "transient":
                transient_pool.append(outcome)

        # Step 4: C* = candidates nondominated in this iteration's estimated
        # objective space only (not pooled across iterations).
        candidates = [g for g in candidate_estimates if is_valid(g, self.validity)]
        if not candidates:
            return []
        selected = pareto_front(candidates, lambda g: candidate_estimates[g])

        # Dedup: skip anything already in H_t / already proposed this run.
        proposals = [
            g
            for g in selected
            if not self.cache.record_proposal(
                g,
                experiment_type=self.experiment_type,
                protocol_version=self.protocol_version,
                pending=exclude,
            )
        ]
        if proposals:
            self.mixing_proposals += len(proposals)
            if surrogate is not None or absolute is not None:
                # A real surrogate scored this iteration's sweeps -- record
                # each proposal's telescoped prediction now, against its
                # ancestor's already-known real f1, so update() can compare
                # it to the real f1 once this proposal is actually
                # evaluated. Skipped when surrogate is None (bootstrap-
                # adjacent "not enough data yet" iterations, _tentatively_
                # accept's optimistic accept-everything path): there is no
                # genuine prediction to score there.
                for g in proposals:
                    ancestor_f1 = self._history[candidate_ancestors[g]].objectives[
                        self.objective_index
                    ]
                    self._pending_predictions[g] = (
                        candidate_estimates[g][self.objective_index],
                        ancestor_f1,
                        len(self._history),
                        candidate_chain_depths[g],
                        level.size,
                    )
            return proposals
        # Stall (module docstring, simplification 2): every candidate this
        # one sweep pass produced was already fully evaluated -- inject
        # fresh random diversity into the current level rather than
        # halting the whole run (Runner.run treats an empty propose() as
        # "stop the whole run", not "try again next call"). Counted as
        # mixing, not bootstrap: this is a within-sweep fallback, not the
        # level-growth-triggered fill _bootstrap_proposals performs.
        if self.stall_recovery == "grow":
            # Ablation variant: treat a zero-proposal pass as the level
            # having nothing left to try -- force it stalled and grow (and
            # warm-start, as every new level now is) a new level at once.
            self._pyramid.mark_stalled(self._level_index)
            self._grow_level()
            return self._bootstrap_proposals(self._level, exclude=exclude)
        fallback = self._diversity_injection(exclude=exclude)
        self.mixing_proposals += len(fallback)
        return fallback

    def _diversity_injection(
        self, *, n: int = 1, exclude: Collection[Genotype] = ()
    ) -> list[Genotype]:
        proposals: list[Genotype] = []
        attempts = 0
        while len(proposals) < n and attempts < n * 50 + 50:
            attempts += 1
            candidate = self.search_space.sample_uniform(self.rng)
            if not is_valid(candidate, self.validity):
                continue
            if candidate in proposals:
                continue
            if self.cache.record_proposal(
                candidate,
                experiment_type=self.experiment_type,
                protocol_version=self.protocol_version,
                pending=exclude,
            ):
                continue
            proposals.append(candidate)
        return proposals

    # -- absolute random-forest surrogate (surrogate_kind="absolute_rf") ----

    def _fit_absolute_surrogate(self) -> _MemoisedForest | None:
        if len(self._history) < 2:
            return None
        forest = AbsoluteRandomForestSurrogate(
            n_estimators=self.rf_n_estimators, random_state=self.rng.randrange(2**31)
        )
        fit_start = time.perf_counter()
        forest.fit(list(self._history.values()))
        self.surrogate_fit_seconds += time.perf_counter() - fit_start
        return _MemoisedForest(forest)

    def _fit_absolute_linear_surrogate(self) -> _MemoisedForest | None:
        if len(self._history) < 2:
            return None
        regressor = AbsoluteRegressorSurrogate(model_factory=self.model_factory)
        fit_start = time.perf_counter()
        regressor.fit(list(self._history.values()), objective_index=self.objective_index)
        self.surrogate_fit_seconds += time.perf_counter() - fit_start
        return _MemoisedForest(_LinearAsObjectives(regressor, self.objective_index))

    def _absolute_estimate(
        self, absolute: _MemoisedForest, ancestor: Observation, candidate: Genotype
    ) -> Objectives:
        predicted = absolute.predict(candidate)
        non_f1 = (
            self.analytic_cost(candidate) if self.analytic_cost is not None else ancestor.objectives
        )
        return tuple(
            predicted[i] if i == self.objective_index else non_f1[i]
            for i in range(len(ancestor.objectives))
        )

    def _accept_absolute(
        self,
        absolute: _MemoisedForest | None,
        ancestor: Observation,
        current_estimate: Objectives,
        candidate: Genotype,
    ) -> tuple[bool, Objectives]:
        """Accept iff the forest predicts an f1 improvement of at least
        acceptance_threshold over the current individual (its real f1 until
        a step is accepted, its predicted f1 afterwards)."""
        estimate = self._absolute_estimate(absolute, ancestor, candidate)
        improvement = current_estimate[self.objective_index] - estimate[self.objective_index]
        return improvement >= self.acceptance_threshold, estimate

    def _make_refiner(
        self, absolute: _MemoisedForest | None
    ) -> Callable[[Genotype], Genotype] | None:
        if absolute is None or self.hill_climber == "none":
            return None
        if self.hill_climber == "fihc":

            def plain(genotype: Genotype) -> Genotype:
                refined, _ = _first_improvement_hill_climb(
                    genotype,
                    self.search_space,
                    lambda g: (absolute.predict(g)[self.objective_index],),
                    self.rng,
                    validity=self.validity,
                    on_decision=self._log_refinement,
                )
                return refined

            return plain

        # One ELyMPuS per forest fit: its comparison cache is only valid for
        # the forest it was computed against (same reasoning as
        # experiments' PrzewozniczekP3ELyMPuS).
        elympus = ELyMPuS(
            search_space=self.search_space,
            fitness_fn=lambda g: absolute.predict(g)[self.objective_index],
            verify_probability=self.elympus_verify_probability,
            rng=self.rng,
        )

        def with_elympus(genotype: Genotype) -> Genotype:
            return fihc_elympus(
                genotype,
                self.search_space,
                elympus,
                self.rng,
                validity=self.validity,
                on_decision=self._log_refinement,
            )

        return with_elympus

    def _log_refinement(
        self, current: Genotype, candidate: Genotype, predicted: float, accepted: bool
    ) -> None:
        self.decision_log.improvement(
            source="refinement",
            reference=current,
            candidate=candidate,
            predicted_improvement=predicted,
            threshold=0.0,
            accepted=accepted,
        )

    def _tentatively_accept(
        self,
        surrogate: RelativeLinkageAwareSurrogate | None,
        ancestor: Observation,
        chain: list[ChainStep],
        candidate: Genotype,
    ) -> tuple[bool, Objectives]:
        """Step 2-3: score a proposed chain via delta_hat_F, and tentatively
        accept iff it predicts nonnegative improvement (the configurable
        acceptance_threshold). ancestor is always drawn from H_t (the
        parent's own Observation), and the telescoping construction below
        enforces the x_0-in-H_t invariant itself.
        """
        if surrogate is None:
            # not enough data to score yet -- accept optimistically; the
            # real evaluation in step 5 corrects the record either way
            return True, ancestor.objectives
        try:
            estimate_f1 = telescoped_estimate(
                ancestor, chain, surrogate, set(self._history), objective_index=self.objective_index
            )
        except AncestorNotEvaluatedError:
            logger.warning(
                "telescoping ancestor %r was not in H_t -- this should never happen "
                "given the parent/x0-from-H_t invariant; accepting optimistically "
                "and continuing, but this indicates a real bug if it recurs",
                ancestor.genotype,
            )
            return True, ancestor.objectives
        predicted_improvement = ancestor.objectives[self.objective_index] - estimate_f1
        accept = predicted_improvement >= self.acceptance_threshold
        # f2 (analytic cost) is always freshly computed for `candidate`
        # when analytic_cost is supplied, otherwise inherited from the
        # ancestor's value (module docstring).
        non_f1_source = (
            self.analytic_cost(candidate) if self.analytic_cost is not None else ancestor.objectives
        )
        estimated_objectives = tuple(
            estimate_f1 if i == self.objective_index else non_f1_source[i]
            for i in range(len(ancestor.objectives))
        )
        return accept, estimated_objectives
