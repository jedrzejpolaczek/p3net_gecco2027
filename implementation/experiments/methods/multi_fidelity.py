"""Multi-fidelity track: Hyperband, ASHA and BOHB, adapted to two objectives.

Why this track: the joint NAS+HPO baselines of Guerrero-Viu et al. (2021)
and Zela et al. (2018) are multi-fidelity -- they spend most of their budget
on short trainings and fully train only what survives. Every other arm of
this project is single-fidelity. Comparing the two needs a common currency,
so this track is run and reported separately, with cost measured in
full-evaluation equivalents.

Cost model (MultiFidelityRunner):
  * a query (genotype, e) returns (f1 after e training epochs, f2);
  * its cost is (e - e_prev) / E, where E is the full training length
    (JAHS-Bench-201: 200 epochs, NAS-HPO-Bench-II: 12) and e_prev is the
    largest epoch count this genotype was already queried at (0 if none).
    Both benchmarks' lower-fidelity values are intermediate records of the
    same full-length training run, so continuing a promoted configuration
    is charged only for the additional epochs (checkpoint resumption, as
    assumed by ASHA);
  * budget B means "cost equivalent to B full evaluations"; a query whose
    cost would exceed the remaining budget ends the run;
  * the run's result set -- what the Pareto-front metrics are computed on
    -- is the set of configurations queried at the full training length,
    so every arm is judged on full-fidelity objective values.

Fidelity ladder (Li et al., 2018, "Hyperband"): reduction factor eta = 3,
minimum resource 1 epoch, s_max = floor(log_eta(E)), rung i of bracket s at
round(E * eta^(i - s)) epochs. JAHS-Bench-201: 2, 7, 22, 67, 200 epochs;
NAS-HPO-Bench-II: 1, 4, 12. Lower rungs of NAS-HPO-Bench-II are its own
tabulated per-epoch records; JAHS-Bench-201's surrogate is queried at the
rung's epoch count.

Multi-objective promotion (all three arms, identical): a rung's results are
ordered by non-dominated sorting on (f1 at that rung, f2), ties within a
front broken by descending crowding distance -- the NSGA-II ordering that
MO-ASHA (Schmucker et al., 2021, "Multi-objective Asynchronous Successive
Halving") uses for promotion. The top floor(n / eta) are promoted.

Arms:
  * hyperband_mo: Hyperband's bracket schedule, new configurations drawn
    uniformly at random.
  * asha_mo: ASHA (Li et al., 2020, "A System for Massively Parallel
    Hyperparameter Tuning") run with one worker: whenever a configuration
    in the top 1/eta of some rung has not been promoted yet, the one on the
    highest such rung is promoted; otherwise a new random configuration
    starts at the lowest rung. Rungs are those of Hyperband's most
    aggressive bracket.
  * bohb_mo: Hyperband's bracket schedule with new configurations drawn by
    the real hpbandster BOHB config generator (Falkner et al., 2018),
    queried at the rung's epoch count and told every result at that epoch
    count. BOHB's KDE needs one scalar loss, so results are scalarised with
    the random-weight Tchebycheff function of methods/external/mo_bohb.py,
    normalised per epoch count. hyperband_mo and bohb_mo therefore differ
    only in how new configurations are sampled -- which is how Falkner et
    al. define BOHB relative to Hyperband.

Library note: hpbandster ships Hyperband and BOHB only as distributed
master/worker services, and optuna's pruners are single-objective; neither
exposes a sequential ask/tell interface with multi-objective promotion. The
bracket and rung logic is therefore implemented here, directly from the
papers' pseudocode; only BOHB's model-based sampler is the library's own.

Handling shared with the other arms: invalid genotypes are never queried;
a configuration is sampled at most once per run.
"""

from __future__ import annotations

import bisect
import math
import random
from dataclasses import dataclass, field
from typing import Any, Protocol

from p3net.harness.evaluation_cache import EvaluationCache
from p3net.harness.runner import Observation, RunState
from p3net.problem.decoding import Validity, is_valid
from p3net.problem.genotype import Genotype, SearchSpace
from p3net.problem.objectives import Objectives, crowding_distance, fast_nondominated_sort

ETA = 3
MIN_EPOCHS = 1


class MultiFidelityMethod(Protocol):
    def propose_query(self) -> tuple[Genotype, int] | None: ...

    def observe(self, genotype: Genotype, epochs: int, objectives: Objectives) -> None: ...


@dataclass(frozen=True)
class FidelityQuery:
    genotype: Genotype
    epochs: int
    objectives: Objectives
    cost: float


@dataclass
class MultiFidelityRunner:
    """See the module docstring's "Cost model". `substrate` must provide
    max_epochs() and objectives_at_epochs() (substrates/base.py)."""

    substrate: Any
    budget: int
    queries: list[FidelityQuery] = field(default_factory=list, init=False)
    cost_used: float = field(default=0.0, init=False)

    def run(self, method: MultiFidelityMethod) -> RunState:
        state = RunState()
        full = self.substrate.max_epochs()
        trained: dict[Genotype, int] = {}
        while True:
            query = method.propose_query()
            if query is None:
                break
            genotype, epochs = query
            previous = trained.get(genotype, 0)
            if not previous < epochs <= full:
                raise ValueError(
                    f"query at {epochs} epochs after {previous} (full length {full}) "
                    "is not a forward step"
                )
            cost = (epochs - previous) / full
            if self.cost_used + cost > self.budget + 1e-9:
                break
            objectives = self.substrate.objectives_at_epochs(genotype, epochs)
            self.cost_used += cost
            trained[genotype] = epochs
            self.queries.append(FidelityQuery(genotype, epochs, objectives, cost))
            if epochs == full:
                state.history.append(Observation(genotype=genotype, objectives=objectives))
                state.evaluations_used += 1
            method.observe(genotype, epochs, objectives)
        return state


def rung_epochs(full_epochs: int, eta: int = ETA, min_epochs: int = MIN_EPOCHS) -> list[int]:
    """Distinct epoch counts of Hyperband's most aggressive bracket, lowest first."""
    s_max = int(math.floor(math.log(full_epochs / min_epochs) / math.log(eta) + 1e-9))
    epochs: list[int] = []
    for i in range(s_max + 1):
        e = max(min_epochs, round(full_epochs * eta ** (i - s_max)))
        if not epochs or e > epochs[-1]:
            epochs.append(e)
    return epochs


def _fronts_two_objectives(points: list[Objectives]) -> list[list[int]]:
    """Non-dominated fronts of 2-objective points in O(n log n) (same fronts
    as fast_nondominated_sort, which is O(n^2) and too slow for ASHA's
    lowest rung). Indices within each front are in ascending order."""
    order = sorted(range(len(points)), key=lambda i: (points[i][0], points[i][1]))
    last_f1: list[float] = []
    last_f2: list[float] = []
    fronts: list[list[int]] = []
    for i in order:
        f1, f2 = points[i][0], points[i][1]
        # Points arrive in lexicographic order, so front k's last point has
        # its lowest f2; p is dominated by front k iff that point dominates p.
        k = bisect.bisect_left(last_f2, f2)
        while k < len(fronts) and last_f2[k] == f2 and last_f1[k] < f1:
            k += 1
        if k == len(fronts):
            fronts.append([])
            last_f1.append(f1)
            last_f2.append(f2)
        fronts[k].append(i)
        last_f1[k], last_f2[k] = f1, f2
    return [sorted(front) for front in fronts]


def promotion_order(results: list[tuple[Genotype, Objectives]]) -> list[Genotype]:
    """Non-dominated rank first, then descending crowding distance (stable)."""
    if results and len(results[0][1]) == 2:
        points = [objectives for _, objectives in results]
        fronts = [[results[i] for i in front] for front in _fronts_two_objectives(points)]
    else:
        fronts = fast_nondominated_sort(results, lambda item: item[1])
    ordered: list[Genotype] = []
    for front in fronts:
        distances = crowding_distance(front, lambda item: item[1])
        ranked = sorted(range(len(front)), key=lambda i: -distances[i])
        ordered.extend(front[i][0] for i in ranked)
    return ordered


# ---------------------------------------------------------------------------
# Samplers of new configurations
# ---------------------------------------------------------------------------


@dataclass
class RandomSampler:
    search_space: SearchSpace
    validity: Validity
    rng: random.Random

    def sample(self, epochs: int, seen: set[Genotype]) -> Genotype | None:
        for _ in range(10_000):
            candidate = self.search_space.sample_uniform(self.rng)
            if candidate not in seen and is_valid(candidate, self.validity):
                return candidate
        return None

    def tell(self, genotype: Genotype, epochs: int, objectives: Objectives) -> None:
        pass


@dataclass
class BohbSampler:
    """hpbandster's BOHB config generator; see the module docstring."""

    search_space: SearchSpace
    validity: Validity
    rng: random.Random
    seed: int
    fallback: RandomSampler = field(init=False)

    def __post_init__(self) -> None:
        import numpy as np
        from hpbandster.optimizers.config_generators.bohb import BOHB as CG_BOHB

        from methods.external.mo_bohb import _build_configspace

        np.random.seed(self.seed)  # CG_BOHB draws from numpy's global RNG
        self._generator = CG_BOHB(_build_configspace(self.search_space, seed=self.seed))
        self._configs: dict[Genotype, dict] = {}
        self._ranges: dict[int, tuple[list[float], list[float]]] = {}
        self._next_job_id = 0
        self.fallback = RandomSampler(self.search_space, self.validity, self.rng)

    def _tell_loss(self, config: dict, epochs: int, loss: float) -> None:
        from hpbandster.core.dispatcher import Job

        job = Job(self._next_job_id, budget=float(epochs), config=config)
        self._next_job_id += 1
        job.result = {"loss": loss}
        self._generator.new_result(job)

    def sample(self, epochs: int, seen: set[Genotype]) -> Genotype | None:
        from methods.external.mo_bohb import _config_to_genotype

        for _ in range(1_000):
            config, _info = self._generator.get_config(float(epochs))
            genotype = _config_to_genotype(config, self.search_space)
            if not is_valid(genotype, self.validity):
                self._tell_loss(config, epochs, float("inf"))
                continue
            if genotype in seen:
                continue
            self._configs[genotype] = config
            return genotype
        return self.fallback.sample(epochs, seen)

    def tell(self, genotype: Genotype, epochs: int, objectives: Objectives) -> None:
        from methods.external.mo_bohb import _tchebycheff_scalarize

        config = self._configs.get(genotype)
        if config is None:  # a random-fallback genotype: build its config for the model
            config = {f"x{i}": v for i, v in enumerate(genotype.values)}
        mins, maxs = self._ranges.setdefault(epochs, ([], []))
        self._tell_loss(config, epochs, _tchebycheff_scalarize(objectives, self.rng, mins, maxs))


# ---------------------------------------------------------------------------
# Arms
# ---------------------------------------------------------------------------


@dataclass
class _MultiFidelityBase:
    search_space: SearchSpace
    validity: Validity
    rng: random.Random
    full_epochs: int
    seed: int = 0
    eta: int = ETA
    experiment_type: str = "multi_fidelity"
    protocol_version: str = "v1"
    cache: EvaluationCache = field(default_factory=EvaluationCache)
    multi_fidelity: bool = field(default=True, init=False)

    def _make_sampler(self):
        return RandomSampler(self.search_space, self.validity, self.rng)

    def __post_init__(self) -> None:
        self._rungs = rung_epochs(self.full_epochs, self.eta)
        self._seen: set[Genotype] = set()
        self._sampler = self._make_sampler()

    def _new_configuration(self, epochs: int) -> Genotype | None:
        genotype = self._sampler.sample(epochs, self._seen)
        if genotype is not None:
            self._seen.add(genotype)
            self.cache.record_proposal(
                genotype,
                experiment_type=self.experiment_type,
                protocol_version=self.protocol_version,
            )
        return genotype

    def _record(self, genotype: Genotype, epochs: int, objectives: Objectives) -> None:
        self._sampler.tell(genotype, epochs, objectives)
        if epochs == self.full_epochs:
            self.cache.put(
                genotype,
                objectives,
                experiment_type=self.experiment_type,
                protocol_version=self.protocol_version,
            )

    # The single-fidelity Method protocol is not supported: run_single
    # dispatches on `multi_fidelity` and drives these arms with
    # MultiFidelityRunner.
    def propose(self, state: RunState) -> list[Genotype]:
        raise TypeError("multi-fidelity arm: drive it with MultiFidelityRunner")

    def update(self, state: RunState, new_observations: list[Observation]) -> None:
        raise TypeError("multi-fidelity arm: drive it with MultiFidelityRunner")


@dataclass
class HyperbandMO(_MultiFidelityBase):
    experiment_type: str = "hyperband_mo"

    def __post_init__(self) -> None:
        super().__post_init__()
        self._s_max = len(self._rungs) - 1
        self._s = self._s_max
        self._start_bracket()

    def _start_bracket(self) -> None:
        s = self._s
        self._i = 0
        self._n = int(math.ceil((self._s_max + 1) / (s + 1) * self.eta**s))
        self._to_sample = self._n
        self._queue: list[Genotype] = []
        self._results: list[tuple[Genotype, Objectives]] = []
        self._outstanding = 0

    def _epochs(self) -> int:
        return self._rungs[self._s_max - self._s + self._i]

    def propose_query(self) -> tuple[Genotype, int] | None:
        if self._to_sample > 0:
            genotype = self._new_configuration(self._epochs())
            if genotype is None:
                return None
            self._to_sample -= 1
        else:
            genotype = self._queue.pop(0)
        self._outstanding += 1
        return genotype, self._epochs()

    def observe(self, genotype: Genotype, epochs: int, objectives: Objectives) -> None:
        self._record(genotype, epochs, objectives)
        self._outstanding -= 1
        self._results.append((genotype, objectives))
        if self._to_sample or self._queue or self._outstanding:
            return
        if self._i < self._s:
            n_i = len(self._results)
            keep = max(1, n_i // self.eta)
            self._queue = promotion_order(self._results)[:keep]
            self._results = []
            self._i += 1
        else:
            self._s = self._s - 1 if self._s > 0 else self._s_max
            self._start_bracket()


@dataclass
class BohbMO(HyperbandMO):
    experiment_type: str = "bohb_mo"

    def _make_sampler(self):
        return BohbSampler(self.search_space, self.validity, self.rng, self.seed)


@dataclass
class AshaMO(_MultiFidelityBase):
    experiment_type: str = "asha_mo"

    def __post_init__(self) -> None:
        super().__post_init__()
        self._rung_results: list[list[tuple[Genotype, Objectives]]] = [[] for _ in self._rungs]
        self._promoted: list[set[Genotype]] = [set() for _ in self._rungs]
        self._top_cache: dict[int, tuple[int, list[Genotype]]] = {}

    def propose_query(self) -> tuple[Genotype, int] | None:
        for k in range(len(self._rungs) - 2, -1, -1):
            for genotype in self._top(k):
                if genotype not in self._promoted[k]:
                    self._promoted[k].add(genotype)
                    return genotype, self._rungs[k + 1]
        genotype = self._new_configuration(self._rungs[0])
        return None if genotype is None else (genotype, self._rungs[0])

    def _top(self, k: int) -> list[Genotype]:
        """Top floor(n / eta) of rung k, recomputed only when the rung changed."""
        results = self._rung_results[k]
        cached = self._top_cache.get(k)
        if cached is None or cached[0] != len(results):
            cached = (len(results), promotion_order(results)[: len(results) // self.eta])
            self._top_cache[k] = cached
        return cached[1]

    def observe(self, genotype: Genotype, epochs: int, objectives: Objectives) -> None:
        self._record(genotype, epochs, objectives)
        self._rung_results[self._rungs.index(epochs)].append((genotype, objectives))
