"""Shared deduplication / reproducibility cache."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from p3net.problem.genotype import Genotype


@dataclass(frozen=True)
class CacheKey:
    genotype: Genotype
    experiment_type: str
    protocol_version: str


@dataclass
class EvaluationCache:
    """Deduplication cache: skip re-evaluating a genotype already fully
    evaluated under the same (experiment type, protocol version). A
    protocol-version bump therefore invalidates stale entries automatically
    -- they simply become unreachable under the new version, without
    needing to be deleted. Also tracks genotype duplication rate at
    PROPOSAL time, independent of whether a given proposal turns out to be
    a cache hit or miss (Diagnostics: counted at proposal time, not
    evaluation time)."""

    _store: dict[CacheKey, Any] = field(default_factory=dict)
    _proposals_seen: int = field(default=0)
    _proposal_duplicates: int = field(default=0)

    def has(self, genotype: Genotype, *, experiment_type: str, protocol_version: str) -> bool:
        return CacheKey(genotype, experiment_type, protocol_version) in self._store

    def get(self, genotype: Genotype, *, experiment_type: str, protocol_version: str) -> Any:
        return self._store.get(CacheKey(genotype, experiment_type, protocol_version))

    def put(
        self, genotype: Genotype, value: Any, *, experiment_type: str, protocol_version: str
    ) -> None:
        self._store[CacheKey(genotype, experiment_type, protocol_version)] = value

    def record_proposal(
        self, genotype: Genotype, *, experiment_type: str, protocol_version: str
    ) -> bool:
        """Call once per candidate a search operator generates, regardless
        of whether it is later intercepted by the cache. Returns True iff
        this proposal duplicates a genotype already in the cache."""
        self._proposals_seen += 1
        is_duplicate = self.has(
            genotype, experiment_type=experiment_type, protocol_version=protocol_version
        )
        if is_duplicate:
            self._proposal_duplicates += 1
        return is_duplicate

    @property
    def duplication_rate(self) -> float:
        if self._proposals_seen == 0:
            return 0.0
        return self._proposal_duplicates / self._proposals_seen

    def size(self) -> int:
        return len(self._store)
