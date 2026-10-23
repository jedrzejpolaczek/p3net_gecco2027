"""The P3 pyramid (Goldman & Punch 2014, §2.2, p. 786; card `p3net.md` P7-P8, P13):
disjoint levels of unique solutions, no target sizes, one frequency table per level."""

from __future__ import annotations

from p3net.problem.genotype import Genotype
from p3net.v005.p3.linkage import FrequencyTable, build_clusters


class Pyramid:
    def __init__(self, domains: list[int] | None = None):
        self.domains = domains
        self.levels: list[list[Genotype]] = []
        self.hashset: set[Genotype] = set()
        self.tables: list[FrequencyTable] = []
        self._clusters: dict[int, tuple[int, list[tuple[int, ...]]]] = {}
        #: optional `known(a, b)` for the E-4 linkage of P3-eLyMPuS; clusters are rebuilt when a level
        #: changes, with the VIG as it is then (OLyMPuS `rebuild_tree` on `add`)
        self.known = None

    def add(self, level: int, g: Genotype) -> bool:
        """P3/P5/P7: add g to `level` (creating it if it is the next one) unless g is
        already anywhere in the pyramid."""
        if g in self.hashset:
            return False
        if level > len(self.levels):
            raise ValueError(f"level {level} skipped: pyramid has {len(self.levels)} levels")
        if level == len(self.levels):
            self.levels.append([])
            self.tables.append(FrequencyTable(self.domains or [0] * len(g.values)))
        self.levels[level].append(g)
        self.tables[level].add(g)
        self.hashset.add(g)
        return True

    def clusters(self, level: int, rng) -> list[tuple[int, ...]]:
        """Linkage clusters of a level (Fig. 2), rebuilt when the level has changed
        since the last call."""
        size = len(self.levels[level])
        cached = self._clusters.get(level)
        if cached is None or cached[0] != size:
            self._clusters[level] = (size, build_clusters(self.tables[level], rng, self.known))
        return self._clusters[level][1]
