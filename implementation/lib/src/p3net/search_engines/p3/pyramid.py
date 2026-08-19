"""P3's population pyramid."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from p3net.metrics.hypervolume import hypervolume, nadir_point
from p3net.problem.genotype import Genotype
from p3net.problem.objectives import Objectives


def _padded_reference(points: Sequence[Objectives]) -> Objectives:
    """A hypervolume reference point strictly (not just weakly) worse than
    every one of `points`, padded 1% of each dimension's own observed span
    beyond the raw nadir. Without this, whichever point happens to define
    the nadir in some dimension has its own contribution to hypervolume
    collapse to exactly zero in that dimension (a `reference[j] - p[j] ==
    0` factor zeroes the whole rectangle) -- a well-known degenerate edge
    case for hypervolume reference points, not specific to this use, and
    especially likely here precisely because Pyramid.promote below is
    called on small, early populations where one new point often *is* the
    current worst in some dimension. A span of 0 (every point shares that
    dimension's value) falls back to padding by 1.0 rather than 0."""
    raw_nadir = nadir_point(points)
    ideal = tuple(min(p[j] for p in points) for j in range(len(raw_nadir)))
    return tuple(
        raw_nadir[j] + max(raw_nadir[j] - ideal[j], 1.0) * 0.01 for j in range(len(raw_nadir))
    )


@dataclass
class PyramidLevel:
    size: int
    population: list[Genotype] = field(default_factory=list)
    best_objectives: Objectives | None = None


@dataclass
class Pyramid:
    """An ordered list of levels of strictly growing size. A new level is
    added only once every existing level has stopped yielding improved
    solutions -- the "parameter-less" property: population size is never
    chosen in advance. Promoting a solution requires a REAL, fully
    evaluated objective value at every accepted step, per the canonical P3
    promotion rule.
    """

    growth_factor: int = 2
    levels: list[PyramidLevel] = field(default_factory=list)
    _stalled: list[bool] = field(default_factory=list)

    def add_level(self) -> PyramidLevel:
        size = self.growth_factor ** (len(self.levels) + 1)
        level = PyramidLevel(size=size)
        self.levels.append(level)
        self._stalled.append(False)
        return level

    @property
    def all_stalled(self) -> bool:
        return len(self.levels) > 0 and all(self._stalled)

    def maybe_grow(self) -> PyramidLevel | None:
        """Add a new level iff there are no levels yet, or every existing
        level is stalled. Returns the new level, or None if growth wasn't
        triggered."""
        if not self.levels or self.all_stalled:
            return self.add_level()
        return None

    def is_stalled(self, level_index: int) -> bool:
        return self._stalled[level_index]

    def promote(
        self,
        level_index: int,
        genotype: Genotype,
        objectives: Objectives,
        *,
        population_objectives: Sequence[Objectives],
    ) -> bool:
        """Register a genotype with a REAL objective value at the given
        level. Promotes (marks not-stalled) iff adding it to the level's
        current population increases that population's own hypervolume;
        otherwise marks the level stalled. Every call corresponds to one
        real evaluation.

        Softened from strict Pareto dominance against a single incumbent
        (2026-08-18, following the population-pyramid bootstrap-share
        investigation -- Conclusions): in two objectives, requiring a
        single sweep pass to beat one incumbent point on BOTH objectives
        simultaneously is rare by construction, so levels stalled almost
        immediately, forcing runaway geometric growth and making the
        uniform-random bootstrap share of the budget rise, not fall, with
        budget. Hypervolume contribution counts a genuinely useful
        trade-off (better on one objective, worse on another -- neither
        dominates nor is dominated) as improving, which strict dominance
        never could.

        `population_objectives` is every OTHER genotype already at this
        level, at the caller's own responsibility -- Pyramid tracks
        genotypes and each level's single best_objectives (kept for
        introspection) but not the full population's objectives, since
        those live in the caller's own H_t (p3net.methods.p3net.P3Net's
        `_history`), not here. Empty on a level's very first promote()
        call: any real point trivially has positive hypervolume against
        an empty population and counts as improving, mirroring the old
        rule's `best_objectives is None` special case.
        """
        level = self.levels[level_index]
        if not population_objectives:
            improved = True
        else:
            reference = _padded_reference(list(population_objectives) + [objectives])
            before = hypervolume(list(population_objectives), reference)
            after = hypervolume(list(population_objectives) + [objectives], reference)
            improved = after > before
        level.population.append(genotype)
        if improved:
            level.best_objectives = objectives
            self._stalled[level_index] = False
        else:
            self._stalled[level_index] = True
        return improved
