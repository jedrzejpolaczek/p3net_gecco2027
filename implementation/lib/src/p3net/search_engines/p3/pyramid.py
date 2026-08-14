"""P3's population pyramid."""

from __future__ import annotations

from dataclasses import dataclass, field

from p3net.problem.genotype import Genotype
from p3net.problem.objectives import Objectives, dominates


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

    def promote(self, level_index: int, genotype: Genotype, objectives: Objectives) -> bool:
        """Register a genotype with a REAL objective value at the given
        level. Promotes (marks not-stalled) iff it improves on the level's
        current best; otherwise marks the level stalled. Every call
        corresponds to one real evaluation."""
        level = self.levels[level_index]
        improved = level.best_objectives is None or dominates(objectives, level.best_objectives)
        level.population.append(genotype)
        if improved:
            level.best_objectives = objectives
            self._stalled[level_index] = False
        else:
            self._stalled[level_index] = True
        return improved
