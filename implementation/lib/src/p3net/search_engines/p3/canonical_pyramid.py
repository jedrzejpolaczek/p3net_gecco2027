"""Canonical, single-individual-climbing P3 population pyramid + First-
Improvement Hill Climber -- the population-management engine
notes/plans/experiments-bartnik-plan.md (Faza 1) asks for as a sibling to
this project's own batch-bootstrap `pyramid.Pyramid`, so the two engines can
be isolated against each other on the same search space and surrogate.

Reconstructed from the standard P3 family description repeated across
Goldman & Punch's "Fast and Efficient Black Box Optimization Using the
Parameter-less Population Pyramid" (2014/2015, Algorithms 2-4) and the two
works this module exists to approximate a variant of --
`bartnik2026evolutionary` and
`dushatskiy2021novelsurrogateassistedevolutionaryalgorithm` -- neither of
which has its algorithm listing transcribed anywhere in this repo. This is
a documented reconstruction, not a verified transcription:

- **First-Improvement Hill Climber** (`first_improvement_hill_climber`,
  Algorithm 4 shape): visit every genotype coordinate in random order;
  for each, try every other value in that coordinate's domain, in random
  order, and take the FIRST one that improves the running objective
  (first-improvement, not best-improvement) before moving to the next
  coordinate.
- **AddToPyramid** (`climb`, Algorithm 3 shape): FIHC the new individual
  first; then, starting at level 0, run one optimal-mixing sweep (GOM)
  against the level's current population; the individual is always added
  to that level; if the sweep's outcome improves over what entered the
  level, keep the improved individual and continue climbing to the next
  level, otherwise stop climbing (the individual's highest level is this
  one). A new level is added -- the only growth trigger, genuinely
  parameter-less like `pyramid.Pyramid`'s own stall-based growth -- only
  once an individual climbs successfully past every existing level.

Population-agnostic and NAS-agnostic by construction, exactly like
`linkage_tree.py`/`optimal_mixing.py`, both of which this module reuses
without modification (Faza 0's own verification step) rather than
reimplementing GOM.

Two documented differences from `pyramid.Pyramid`, the engine this project
already uses for P3Net/P3Absolute:

1. `Pyramid` bootstraps a whole level in one batch and only ever sweeps
   the newest level; this module climbs one individual through as many
   levels as it can in a single call, cascading upward exactly like
   canonical P3's "every level stays live" description
   (`p3net.methods.p3net.P3Net`'s own module docstring, "Known
   simplification 1" -- this module is the undiluted version of that).
2. `Pyramid.promote`'s growth trigger is a per-level stall flag (no
   improvement for one whole sweep pass over a bootstrapped population);
   `climb`'s growth trigger is "one individual reached the top and still
   improved", with no notion of population size or stall count at all.

Every step below -- FIHC and every GOM proposal -- costs one call to the
caller-supplied `fitness_fn`, i.e. one real evaluation. This module has no
concept of a surrogate or an acceptance gate: it is the canonical, real-
fitness-only engine. `experiments/methods/bartnik_p3.py` is the one that
wraps a surrogate and a gate around it, exactly the way
`p3net.methods.p3net.P3Net` wraps a surrogate around `pyramid.Pyramid`.
"""

from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass, field

from p3net.problem.decoding import Validity, is_valid
from p3net.problem.genotype import Genotype, SearchSpace
from p3net.problem.objectives import Objectives, dominates
from p3net.search_engines.p3.linkage_tree import build_linkage_tree
from p3net.search_engines.p3.optimal_mixing import SweepState


def _improves(candidate: Objectives, current: Objectives) -> bool:
    """Accept unless `current` strictly Pareto-dominates `candidate` --
    the same permissive "not worse" spirit as
    `methods.p3_absolute.P3Absolute`'s absolute acceptance rule, so a
    genuinely useful trade-off (better on one objective, worse on
    another) still counts as an improving step.

    Two consequences worth stating, because neither is what the rule was
    originally written for:

    1. Every production caller in this project drives `climb` with
       `fitness_fn=surrogate.predict`, NOT a real objective vector
       (`methods.bartnik_p3.BartnikP3._gated_climb_proposal` and its
       sibling in experiments-przewozniczek both do). Under a surrogate,
       permissiveness stops being "tolerate a real trade-off" and becomes
       "tolerate anything the surrogate's prediction error does not make
       look strictly dominated" -- a materially weaker filter than the
       same rule applied to measured objectives.
    2. The rule is multi-objective. A hill climber substituted via
       `climb`'s own `hill_climber` parameter need not be: notably
       `fihc_elympus`, which is driven through
       `make_elympus_fitness_adapter` and therefore optimises ONE scalar
       objective. Swapping the hill climber therefore changes two things
       at once -- the comparison mechanism AND the objective handling --
       so a comparison between a default climb and a substituted one does
       not isolate the comparison mechanism by itself. See
       `fihc_elympus`'s own module docstring."""
    return not dominates(current, candidate)


def first_improvement_hill_climber(
    genotype: Genotype,
    search_space: SearchSpace,
    fitness_fn: Callable[[Genotype], Objectives],
    rng: random.Random,
    *,
    validity: Validity | None = None,
) -> Genotype:
    """Algorithm 4 shape: local search over one individual, one
    coordinate at a time, taking the first improving alternative value
    found rather than searching for the best one."""
    current, _ = _first_improvement_hill_climb(
        genotype, search_space, fitness_fn, rng, validity=validity
    )
    return current


def _first_improvement_hill_climb(
    genotype: Genotype,
    search_space: SearchSpace,
    fitness_fn: Callable[[Genotype], Objectives],
    rng: random.Random,
    *,
    validity: Validity | None = None,
    on_decision: Callable[[Genotype, Genotype, float, bool], None] | None = None,
) -> tuple[Genotype, Objectives]:
    """Same climb as `first_improvement_hill_climber`, but also returns the
    final individual's objective vector -- `climb()` needs it immediately
    afterwards, and this loop already computed it as `current_obj`;
    recomputing via a second `fitness_fn(x)` call (as `climb()` used to,
    unconditionally) wastes one real evaluation on every plain-FIHC climb
    for a value already known. `first_improvement_hill_climber`'s own
    public, genotype-only return type is preserved above so existing
    callers/tests are unaffected.

    `on_decision(current, candidate, predicted_f1_improvement, accepted)`,
    if given, is told about every alternative the climb scores (for
    surrogate-decision logging, p3net.harness.decision_log); it has no
    effect on the climb."""
    current = genotype
    current_obj = fitness_fn(current)
    order = list(range(search_space.n))
    rng.shuffle(order)
    for i in order:
        domain = search_space.domains[i]
        alternatives = [v for v in domain.values if v != current.values[i]]
        rng.shuffle(alternatives)
        for value in alternatives:
            candidate = current.with_values(indices=[i], new_values=[value])
            if validity is not None and not is_valid(candidate, validity):
                continue
            candidate_obj = fitness_fn(candidate)
            improves = _improves(candidate_obj, current_obj)
            if on_decision is not None:
                on_decision(current, candidate, current_obj[0] - candidate_obj[0], improves)
            if improves:
                current, current_obj = candidate, candidate_obj
                break
    return current, current_obj


@dataclass
class CanonicalPyramidLevel:
    """One rung of the canonical pyramid: just the accumulated
    population, no target size -- climbing individuals accumulate here
    one at a time, never in a batch."""

    population: list[Genotype] = field(default_factory=list)


@dataclass
class CanonicalPyramid:
    """An ordered list of canonical pyramid levels. Unlike `pyramid.
    Pyramid`, there is no `growth_factor`/target size and no explicit
    stall bookkeeping -- `climb` below is the only thing that ever adds a
    level, and it does so exactly once per individual that climbs past
    every level that already exists."""

    levels: list[CanonicalPyramidLevel] = field(default_factory=list)

    def add_level(self) -> CanonicalPyramidLevel:
        level = CanonicalPyramidLevel()
        self.levels.append(level)
        return level


def climb(
    individual: Genotype,
    pyramid: CanonicalPyramid,
    *,
    search_space: SearchSpace,
    fitness_fn: Callable[[Genotype], Objectives],
    rng: random.Random,
    validity: Validity | None = None,
    hill_climber: Callable[[Genotype], Genotype] | None = None,
) -> Genotype:
    """Algorithm 3 shape: FIHC the individual, then sweep it up through
    the pyramid's existing levels via GOM, one level at a time, promoting
    to the next level only on improvement. `pyramid` must already have at
    least one level (mirroring `pyramid.Pyramid`'s own
    construction/`add_level` convention -- callers add the first level
    themselves).

    `hill_climber`, if given, REPLACES the plain-FIHC local-search step
    with any single-argument (genotype -> genotype) callable -- notably
    `p3net.search_engines.p3.fihc_elympus.fihc_elympus`, pre-bound by the
    caller via a closure (it needs an `ELyMPuS` instance and its own
    `rng`/`validity`, neither of which `climb` should need to know about).
    Every step AFTER the hill-climb (GOM sweeps, promotion) always uses
    real, multi-objective `fitness_fn` -- unchanged regardless of which
    hill-climber ran first (notes/plans/experiments-przewozniczek-plan.md,
    Faza 3: "FIHC-eLyMPuS replaces the plain FIHC step", nothing else)."""
    if not pyramid.levels:
        raise ValueError("climb requires at least one existing level (call add_level first)")

    if hill_climber is None:
        x, x_obj = _first_improvement_hill_climb(
            individual, search_space, fitness_fn, rng, validity=validity
        )
    else:
        x = hill_climber(individual)
        x_obj = fitness_fn(x)

    level_index = 0
    while level_index < len(pyramid.levels):
        level = pyramid.levels[level_index]
        entering_x, entering_obj = x, x_obj

        if len(level.population) < 2:
            # Not enough population yet to build a linkage tree (GOM needs
            # at least a pair to compute pairwise mutual information) --
            # bootstrap this level by simple insertion and stop climbing
            # for this individual, mirroring `pyramid.Pyramid`'s own
            # "no established population to compare against yet" bootstrap
            # phase rather than promoting past an untested level.
            level.population.append(x)
            return x

        root = build_linkage_tree(level.population)
        sweep = SweepState.start(x, root, level.population, rng)
        current, current_obj = x, x_obj
        while not sweep.done:
            proposal = sweep.propose()
            if validity is not None and not is_valid(proposal.candidate, validity):
                sweep.reject(proposal)
                continue
            candidate_obj = fitness_fn(proposal.candidate)
            if _improves(candidate_obj, current_obj):
                sweep.accept(proposal)
                current, current_obj = proposal.candidate, candidate_obj
            else:
                sweep.reject(proposal)

        level.population.append(entering_x)

        if current != entering_x and _improves(current_obj, entering_obj):
            x, x_obj = current, current_obj
            level_index += 1
        else:
            return entering_x

    new_level = pyramid.add_level()
    new_level.population.append(x)
    return x
