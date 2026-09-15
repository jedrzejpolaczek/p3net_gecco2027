"""MOEA/D baseline (general-purpose MOEA, decomposition based) via pymoo.

Why this arm: MOEA/D (Zhang & Li, 2007) is the standard decomposition
counterpart to NSGA-III's reference points -- together they cover the two
main ways MOEAs handle multiple objectives.

Real: pymoo.algorithms.moo.moead.MOEAD driven through pymoo's ask/tell
interface. 20 weight vectors ("uniform" reference directions, 19
partitions for two objectives) to match the population of 20 used by every
other population-based arm; every other MOEA/D setting is pymoo's default.

Encoding: pymoo has no categorical variable type for MOEA/D, so each
coordinate is the integer index of its value, with pymoo's documented
mixed-integer recipe -- integer random sampling, SBX crossover and
polynomial mutation followed by rounding repair. This imposes an ordering on
categorical values that the problem does not have (paper, Limitations).

Handling shared with the other external arms:
  * pymoo's MOEA/D is steady-state: ask() may return a single individual
    or a population; both are buffered and handed out one genotype at a
    time, and told back together once all have objective values;
  * an invalid genotype is never evaluated -- it is told a penalty
    objective vector worse than any real value, so decomposition steers
    away from it;
  * a genotype already evaluated is told its real cached value.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

import numpy as np
from p3net.harness.evaluation_cache import EvaluationCache
from p3net.harness.runner import Observation, RunState
from p3net.problem.decoding import Validity, is_valid
from p3net.problem.genotype import Genotype, SearchSpace

#: Objective vector told for an invalid genotype. Both objectives in this
#: project are non-negative error / cost quantities far below this.
INVALID_PENALTY = 1e12


@dataclass
class MOEAD:
    search_space: SearchSpace
    validity: Validity
    rng: random.Random
    seed: int = 0
    n_weights: int = 20
    n_objectives: int = 2
    experiment_type: str = "moead"
    protocol_version: str = "v1"
    cache: EvaluationCache = field(default_factory=EvaluationCache)

    _algorithm: object = field(default=None, init=False, repr=False)
    _batch: object = field(default=None, init=False, repr=False)
    _batch_genotypes: list[Genotype] = field(default_factory=list, init=False, repr=False)
    _batch_values: dict[int, list[float]] = field(default_factory=dict, init=False, repr=False)
    _awaiting: dict[Genotype, list[int]] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        from pymoo.algorithms.moo.moead import MOEAD as PymooMOEAD
        from pymoo.core.problem import Problem
        from pymoo.operators.crossover.sbx import SBX
        from pymoo.operators.mutation.pm import PM
        from pymoo.operators.repair.rounding import RoundingRepair
        from pymoo.operators.sampling.rnd import IntegerRandomSampling
        from pymoo.util.ref_dirs import get_reference_directions

        upper = [len(d.values) - 1 for d in self.search_space.domains]
        problem = Problem(
            n_var=self.search_space.n, n_obj=self.n_objectives, xl=0, xu=np.array(upper), vtype=int
        )
        self._algorithm = PymooMOEAD(
            get_reference_directions("uniform", self.n_objectives, n_partitions=self.n_weights - 1),
            sampling=IntegerRandomSampling(),
            crossover=SBX(vtype=float, repair=RoundingRepair()),
            mutation=PM(vtype=float, repair=RoundingRepair()),
        )
        self._algorithm.setup(
            problem, termination=("n_eval", 10**12), seed=self.seed, verbose=False
        )

    # -- harness.Method ---------------------------------------------------

    def propose(self, state: RunState) -> list[Genotype]:
        for _ in range(10_000):
            if self._batch is None:
                self._next_batch()
            for position, genotype in enumerate(self._batch_genotypes):
                if position in self._batch_values or any(
                    position in v for v in self._awaiting.values()
                ):
                    continue
                if not is_valid(genotype, self.validity):
                    self._batch_values[position] = [INVALID_PENALTY] * self.n_objectives
                    continue
                if genotype in self._awaiting:
                    self._awaiting[genotype].append(position)  # same child twice in one batch
                    continue
                if self.cache.record_proposal(
                    genotype,
                    experiment_type=self.experiment_type,
                    protocol_version=self.protocol_version,
                ):
                    known = self.cache.get(
                        genotype,
                        experiment_type=self.experiment_type,
                        protocol_version=self.protocol_version,
                    )
                    self._batch_values[position] = list(known)
                    continue
                self._awaiting[genotype] = [position]
                return [genotype]
            if not self._awaiting:
                self._tell_batch()
            else:
                return []  # unreachable in practice: harness evaluates before asking again
        return []

    def update(self, state: RunState, new_observations: list[Observation]) -> None:
        for obs in new_observations:
            self.cache.put(
                obs.genotype,
                obs.objectives,
                experiment_type=self.experiment_type,
                protocol_version=self.protocol_version,
            )
            for position in self._awaiting.pop(obs.genotype, []):
                self._batch_values[position] = list(obs.objectives)
        if self._batch is not None and len(self._batch_values) == len(self._batch_genotypes):
            self._tell_batch()

    # -- internals --------------------------------------------------------

    def _next_batch(self) -> None:
        from pymoo.core.population import Population

        asked = self._algorithm.ask()
        # Steady-state MOEA/D yields a single Individual and expects that
        # same object back with F set; generational algorithms yield a
        # Population. Keep whatever was asked, read X from a view of it.
        self._batch = asked
        rows = asked.get("X") if isinstance(asked, Population) else [asked.X]
        values = self.search_space.domains
        self._batch_genotypes = [
            Genotype(values=tuple(values[i].values[int(round(x))] for i, x in enumerate(row)))
            for row in rows
        ]
        self._batch_values = {}
        self._awaiting = {}

    def _tell_batch(self) -> None:
        from pymoo.core.population import Population

        F = np.array(
            [self._batch_values[i] for i in range(len(self._batch_genotypes))], dtype=float
        )
        if isinstance(self._batch, Population):
            self._batch.set("F", F)
        else:
            self._batch.set("F", F[0])
        self._algorithm.tell(infills=self._batch)
        self._batch = None
        self._batch_genotypes = []
        self._batch_values = {}
        self._awaiting = {}
