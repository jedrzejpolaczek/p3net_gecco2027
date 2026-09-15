"""Record of surrogate-driven decisions, for confusion-matrix analysis after a run.

A surrogate decision is a point where a method accepts or rejects a
candidate on predicted, not real, objective values: P3Net's tentative
acceptance of a mixing step, a surrogate gate that decides whether a
candidate is evaluated at all, a predictor that picks which offspring to
evaluate. Rejected candidates are never evaluated during the run, so
whether a decision was right is only known after the run, by querying the
benchmark for the logged genotypes outside the evaluation budget
(scripts/posthoc_metrics.py).

Every decision is offered to the log; at most `limit` are kept, chosen by
reservoir sampling (Vitter's Algorithm R), so the kept records are a uniform
random sample of all decisions made in the run. The reservoir uses its own
random generator with a fixed seed, never the method's -- logging cannot
change what a method does.

Record kinds:
  * "improvement": accepted iff the predicted improvement of `candidate`
    over `reference` in f1 was at least `threshold`. The real label is
    f1(reference) - f1(candidate) >= threshold, both at full fidelity.
  * "selection": `candidate` was (accepted) or was not selected from a pool
    ranked by predicted f1 (`predicted` is that prediction, `reference` is
    absent). Used for rank correlation, not a confusion matrix.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any

from p3net.problem.genotype import Genotype

DEFAULT_LIMIT = 500


@dataclass
class DecisionLog:
    limit: int = DEFAULT_LIMIT
    seed: int = 0
    offered: int = 0
    records: list[dict[str, Any]] = field(default_factory=list)
    _rng: random.Random = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._rng = random.Random(self.seed)

    def _offer(self, record: dict[str, Any]) -> None:
        self.offered += 1
        if len(self.records) < self.limit:
            self.records.append(record)
            return
        slot = self._rng.randrange(self.offered)
        if slot < self.limit:
            self.records[slot] = record

    def improvement(
        self,
        *,
        source: str,
        reference: Genotype,
        candidate: Genotype,
        predicted_improvement: float,
        threshold: float,
        accepted: bool,
    ) -> None:
        self._offer(
            {
                "kind": "improvement",
                "source": source,
                "reference": list(reference.values),
                "candidate": list(candidate.values),
                "predicted": float(predicted_improvement),
                "threshold": float(threshold),
                "accepted": bool(accepted),
            }
        )

    def selection(
        self, *, source: str, candidate: Genotype, predicted_f1: float, accepted: bool
    ) -> None:
        self._offer(
            {
                "kind": "selection",
                "source": source,
                "candidate": list(candidate.values),
                "predicted": float(predicted_f1),
                "accepted": bool(accepted),
            }
        )

    def as_dict(self) -> dict[str, Any]:
        return {"offered": self.offered, "limit": self.limit, "records": self.records}
