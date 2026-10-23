"""Library adapters (card `library-adapters.md`): the method is the library with its
defaults; the ask-tell adapter does not change it (W-A5). Settings that differ from
the defaults are those of §3: SMAC3 n_trials = b (#19); MOEA/D with categorical
operators, T = ceil(0.2 N) = 4 and deduplication (#20, #21); population 20 (#37);
initial designs min(source, floor(0.25 b)) (BB-4).

Shared rules (§4): a genotype in H_t is told back with its known value and costs no
budget (#35); an invalid genotype is never evaluated (#33) -- the library is told a
failure / the worst values seen; f2 only from real evaluations (#6); the method
itself never exceeds the budget (K-2).

Libraries are imported lazily, so the module (and RandomSearch) works without them.
Genotype coordinate i <-> library parameter `x{i}` with choices 0..k_i-1 (Q-35).
"""

from __future__ import annotations

import logging
import math
import random
import tempfile
from pathlib import Path

import numpy as np

from p3net.harness.runner import Observation, RunState
from p3net.problem.genotype import Genotype
from p3net.problem.objectives import dominates, pareto_front
from p3net.v005.common import EvalCache, cardinalities, initial_design_size, is_valid, random_genotype, space_size

MAX_ASKS = 10_000


class _AskTell:
    """One proposal per call; `_ask()` returns (genotype, token); `_tell(token, f)`
    reports a value (`None` = invalid)."""

    def __init__(self, space, budget, rng):
        self.space, self.rng, self.budget = space, rng, int(budget)
        self.domains = cardinalities(space)
        self.cache = EvalCache()
        self.used = 0
        self._pending: tuple[Genotype, object] | None = None
        self.worst: list[float] | None = None
        self._deferred_invalid: list[object] = []
        self.stop_reason: str | None = None

    def _ask(self):
        raise NotImplementedError

    def _tell(self, token, f) -> None:
        raise NotImplementedError

    def _tell_invalid(self, token) -> None:
        if self.worst is None:
            self._deferred_invalid.append(token)
        else:
            self._tell(token, list(self.worst))

    def propose(self, state: RunState) -> list[Genotype]:
        if self.used >= self.budget or self._pending is not None:
            return []
        for _ in range(MAX_ASKS):
            g, token = self._ask()
            if not is_valid(self.space, g):
                self._tell_invalid(token)
                continue
            known = self.cache.get(g)
            if known is not None:
                self._tell(token, list(known))
                continue
            self._pending = (g, token)
            self.used += 1
            return [g]
        self.stop_reason = f"exploration collapse: {MAX_ASKS} asks without a new genotype"
        return []

    def update(self, state: RunState, new_observations: list[Observation]) -> None:
        for obs in new_observations:
            f = [float(x) for x in obs.objectives]
            self.cache.put(obs.genotype, f)
            self.worst = f if self.worst is None else [max(a, b) for a, b in zip(self.worst, f)]
            if self._pending is not None and obs.genotype == self._pending[0]:
                self._tell(self._pending[1], f)
                self._pending = None
        while self._deferred_invalid and self.worst is not None:
            self._tell(self._deferred_invalid.pop(0), list(self.worst))


# ---------------------------------------------------------------------------
# optuna: MOTPE, NSGA-III
# ---------------------------------------------------------------------------


class _Optuna(_AskTell):
    def __init__(self, space, budget, rng, sampler):
        super().__init__(space, budget, rng)
        import optuna

        optuna.logging.set_verbosity(optuna.logging.WARNING)
        self._optuna = optuna
        self.study = optuna.create_study(directions=["minimize", "minimize"], sampler=sampler)

    def _ask(self):
        t = self.study.ask()
        g = Genotype(values=tuple(t.suggest_categorical(f"x{i}", list(range(k))) for i, k in enumerate(self.domains)))
        return g, t

    def _tell_invalid(self, token) -> None:
        self.study.tell(token, state=self._optuna.trial.TrialState.FAIL)

    def _tell(self, token, f) -> None:
        self.study.tell(token, values=list(f))


class MOTPE(_Optuna):
    """optuna TPESampler with two objectives = MOTPE (A-2 a), library defaults;
    n_startup_trials = min(10, floor(0.25 b))."""

    def __init__(self, space, budget, rng):
        import optuna

        self.seed = rng.randrange(2**31)
        self.n_startup = initial_design_size(10, budget)
        sampler = optuna.samplers.TPESampler(seed=self.seed, n_ei_candidates=24, multivariate=False,
                                             n_startup_trials=self.n_startup)
        super().__init__(space, budget, rng, sampler)

    def config(self) -> dict:
        s = self.study.sampler
        return {"n_ei_candidates": s._n_ei_candidates, "multivariate": s._multivariate,
                "n_startup_trials": s._n_startup_trials, "gamma": s._gamma, "seed": self.seed}


class NSGA3(_Optuna):
    """optuna NSGAIIISampler, defaults, population 20 (#37)."""

    def __init__(self, space, budget, rng, *, population_size: int = 20):
        import optuna

        self.seed = rng.randrange(2**31)
        self.population_size = int(population_size)
        super().__init__(space, budget, rng,
                         optuna.samplers.NSGAIIISampler(population_size=self.population_size, seed=self.seed))

    def config(self) -> dict:
        return {"population_size": self.population_size, "seed": self.seed}


# ---------------------------------------------------------------------------
# SMAC3 ParEGO
# ---------------------------------------------------------------------------


class SMAC3ParEGO(_AskTell):
    """HPO facade + ParEGO, all defaults, deterministic, n_trials = b (#19)."""

    def __init__(self, space, budget, rng):
        super().__init__(space, budget, rng)
        from smac import HyperparameterOptimizationFacade, Scenario
        from smac.multi_objective.parego import ParEGO

        logging.getLogger("smac").setLevel(logging.ERROR)
        self.seed = rng.randrange(2**31)
        self._workdir = tempfile.TemporaryDirectory(prefix="smac3_v005_")
        scen = Scenario(self._configspace(), deterministic=True, n_trials=self.budget, seed=self.seed,
                        objectives=["f1", "f2"], output_directory=Path(self._workdir.name) / "smac")
        self.smac = HyperparameterOptimizationFacade(scen, lambda config, seed=0: [0.0, 0.0],
                                                     multi_objective_algorithm=ParEGO(scen), overwrite=True,
                                                     logging_level=40)

    def _configspace(self):
        from ConfigSpace import Categorical, ConfigurationSpace

        cs = ConfigurationSpace(seed=self.seed)
        cs.add([Categorical(f"x{i}", list(range(k))) for i, k in enumerate(self.domains)])
        return cs

    def config(self) -> dict:
        return {"facade": "HyperparameterOptimizationFacade", "multi_objective_algorithm": "ParEGO",
                "deterministic": True, "n_trials": self.budget,
                "initial_design_size": min(10 * len(self.domains), self.budget // 4),
                "seed": self.seed, "configspace": self._configspace()}

    def _ask(self):
        info = self.smac.ask()
        return Genotype(values=tuple(int(info.config[f"x{i}"]) for i in range(len(self.domains)))), info

    def _tell(self, token, f) -> None:
        from smac.runhistory.dataclasses import TrialValue

        self.smac.tell(token, TrialValue(cost=list(f)))


# ---------------------------------------------------------------------------
# Vizier
# ---------------------------------------------------------------------------


class Vizier(_AskTell):
    """OSS Vizier `VizierGPUCBPEBandit`, defaults (num_seed_trials = 1)."""

    def __init__(self, space, budget, rng):
        super().__init__(space, budget, rng)
        import jax
        from vizier._src.algorithms.designers.gp_ucb_pe import VizierGPUCBPEBandit
        from vizier.service import pyvizier as vz

        self._vz = vz
        problem = vz.ProblemStatement()
        for i, k in enumerate(self.domains):
            problem.search_space.root.add_categorical_param(f"x{i}", [str(v) for v in range(k)])
        for j in range(2):
            problem.metric_information.append(vz.MetricInformation(name=f"f{j + 1}",
                                                                   goal=vz.ObjectiveMetricGoal.MINIMIZE))
        jax.config.update("jax_enable_x64", True)
        self.seed = rng.randrange(2**31)
        self.designer = VizierGPUCBPEBandit(problem, rng=jax.random.PRNGKey(self.seed))
        self._next_id = 1

    def config(self) -> dict:
        return {"num_seed_trials": getattr(self.designer, "num_seed_trials", 1), "seed": self.seed}

    def _ask(self):
        trial = self.designer.suggest(count=1)[0].to_trial(self._next_id)
        self._next_id += 1
        return Genotype(values=tuple(int(trial.parameters[f"x{i}"].value) for i in range(len(self.domains)))), trial

    def _complete(self, trial, metrics, reason):
        from vizier import algorithms as vza

        trial.complete(self._vz.Measurement(metrics=metrics or {}), infeasibility_reason=reason)
        self.designer.update(vza.CompletedTrials([trial]), vza.ActiveTrials())

    def _tell_invalid(self, token) -> None:
        self._complete(token, None, "invalid genotype")

    def _tell(self, token, f) -> None:
        self._complete(token, {f"f{j + 1}": float(v) for j, v in enumerate(f)}, None)


# ---------------------------------------------------------------------------
# BoTorch: qNEHVI, qParEGO
# ---------------------------------------------------------------------------


class _BoTorch:
    acquisition = ""

    def __init__(self, space, budget, rng, *, pool_size: int = 1024, mc_samples: int = 128):
        self.space, self.rng, self.budget = space, rng, int(budget)
        self.domains = cardinalities(space)
        self.n_initial = initial_design_size(2 * (len(self.domains) + 1), self.budget)
        self.pool_size, self.mc_samples = int(pool_size), int(mc_samples)
        self.cache = EvalCache()
        self.order: list[Genotype] = []
        self.used = 0
        self._pending = False
        self._hyper = None
        self.seed = rng.randrange(2**31)

    def config(self) -> dict:
        return {"acquisition": self.acquisition, "model": "MixedSingleTaskGP", "outcome_transform": "Standardize",
                "mc_samples": self.mc_samples, "pool_size": self.pool_size, "n_initial": self.n_initial,
                "n_models": 2, "seed": self.seed}

    def _encode(self, gs):
        import torch

        return torch.tensor([list(g.values) for g in gs], dtype=torch.double)

    def _pool(self) -> list[Genotype]:
        pool: dict[Genotype, None] = {}
        front = pareto_front(list(self.order), lambda g: self.cache.get(g))
        for g in front:
            for i, k in enumerate(self.domains):
                for v in range(k):
                    if v != g.values[i]:
                        pool[g.with_values(indices=[i], new_values=[v])] = None
        added = tries = 0
        while added < self.pool_size and tries < 20 * self.pool_size:
            tries += 1
            g = random_genotype(self.space, self.rng, valid_only=False)
            if g not in pool:
                pool[g] = None
                added += 1
        return [g for g in pool if g not in self.cache and is_valid(self.space, g)]

    def _acq(self, X, Y):
        raise NotImplementedError

    def propose(self, state: RunState) -> list[Genotype]:
        if self.used >= self.budget or self._pending:
            return []
        if len(self.cache) < self.n_initial:
            for _ in range(MAX_ASKS):
                g = random_genotype(self.space, self.rng)
                if g not in self.cache:
                    break
            else:
                return []
            choice = g
        else:
            import warnings

            import torch
            from botorch.fit import fit_gpytorch_mll
            from botorch.models import MixedSingleTaskGP
            from gpytorch.mlls import ExactMarginalLogLikelihood

            pool = self._pool()
            if not pool:
                return []
            torch.manual_seed(self.seed + len(self.cache))
            X = self._encode(self.order)
            Y = -torch.tensor([self.cache.get(g) for g in self.order], dtype=torch.double)  # botorch maximises
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                model = MixedSingleTaskGP(X, Y, cat_dims=list(range(len(self.domains))))
                if self._hyper is not None:
                    model.load_state_dict(self._hyper, strict=False)
                fit_gpytorch_mll(ExactMarginalLogLikelihood(model.likelihood, model))
                self._hyper = {k: v.detach().clone() for k, v in model.state_dict().items()
                               if not k.startswith("outcome_transform")}
                acq = self._acq(model, X, Y)
                with torch.no_grad():
                    Xp = self._encode(pool).unsqueeze(1)
                    scores = torch.cat([acq(Xp[i:i + 256]) for i in range(0, len(pool), 256)])
            choice = pool[int(torch.argmax(scores))]
        self._pending = True
        self.used += 1
        return [choice]

    def update(self, state: RunState, new_observations: list[Observation]) -> None:
        for obs in new_observations:
            self.cache.put(obs.genotype, obs.objectives)
            self.order.append(obs.genotype)
        self._pending = False


class QNEHVI(_BoTorch):
    """qLogNEHVI on independent GPs per objective (A-1 a: the EHVI arm)."""

    acquisition = "qLogNEHVI"

    def _acq(self, model, X, Y):
        import torch
        from botorch.acquisition.multi_objective.logei import qLogNoisyExpectedHypervolumeImprovement
        from botorch.sampling import SobolQMCNormalSampler

        worst, best = Y.min(dim=0).values, Y.max(dim=0).values
        ref = worst - 0.1 * (best - worst).clamp_min(1e-9)
        sampler = SobolQMCNormalSampler(sample_shape=torch.Size([self.mc_samples]), seed=self.rng.randrange(2**31))
        return qLogNoisyExpectedHypervolumeImprovement(model=model, ref_point=ref, X_baseline=X, sampler=sampler,
                                                       prune_baseline=True)


class QParEGO(_BoTorch):
    """qLogNEI on a random Chebyshev scalarisation per step."""

    acquisition = "qLogNEI"

    def _acq(self, model, X, Y):
        import torch
        from botorch.acquisition.logei import qLogNoisyExpectedImprovement
        from botorch.acquisition.objective import GenericMCObjective
        from botorch.sampling import SobolQMCNormalSampler
        from botorch.utils.multi_objective.scalarization import get_chebyshev_scalarization
        from botorch.utils.sampling import sample_simplex

        w = sample_simplex(Y.shape[-1], dtype=torch.double, seed=self.rng.randrange(2**31)).squeeze(0)
        scal = get_chebyshev_scalarization(weights=w, Y=Y)
        sampler = SobolQMCNormalSampler(sample_shape=torch.Size([self.mc_samples]), seed=self.rng.randrange(2**31))
        return qLogNoisyExpectedImprovement(model=model, X_baseline=X, sampler=sampler,
                                            objective=GenericMCObjective(lambda s, X=None: scal(s)),
                                            prune_baseline=True)


# ---------------------------------------------------------------------------
# MOEA/D (pymoo 0.6.2 logic, categorical operators)
# ---------------------------------------------------------------------------


class MOEAD:
    """MOEA/D (Zhang & Li 2007) with pymoo 0.6.2's loop: N = 20 uniform weight vectors,
    Tchebycheff decomposition, neighbourhood of T = ceil(0.2 N) = 4, mating from the
    neighbourhood with probability 0.9 (else from the whole population); offspring by
    uniform crossover + random-reset mutation (p = 1/n) (#21); duplicates re-drawn
    (#20); every neighbour whose decomposed value improves is replaced."""

    def __init__(self, space, budget, rng, *, pop_size: int = 20, prob_neighbor_mating: float = 0.9):
        self.space, self.rng, self.budget = space, rng, int(budget)
        self.domains = cardinalities(space)
        self.N = min(int(pop_size), self.budget)
        self.T = math.ceil(0.2 * self.N)
        self.p_nb = float(prob_neighbor_mating)
        w = np.linspace(0, 1, self.N)
        self.W = np.column_stack([w, 1 - w]) if self.N > 1 else np.array([[0.5, 0.5]])
        d = ((self.W[:, None, :] - self.W[None, :, :]) ** 2).sum(-1)
        self.B = np.argsort(d, axis=1)[:, : self.T]
        self.cache = EvalCache()
        self.pop: list[Observation] = []
        self.ideal: np.ndarray | None = None
        self.used = 0
        self._pending: list[Genotype] = []
        self._order: list[int] = []
        self._current: int | None = None
        self._size = space_size(space)
        self.stop_reason: str | None = None

    def config(self) -> dict:
        return {"pop_size": self.N, "n_partitions_or_pop": self.N, "decomposition": "Tchebicheff",
                "prob_neighbor_mating": self.p_nb, "n_neighbors": self.T, "crossover": "uniform (p = 0.5 per gene)",
                "mutation": "random reset (p = 1/n)", "eliminate_duplicates": True}

    def _tcheby(self, f, i) -> float:
        return float(np.max(self.W[i] * np.abs(np.asarray(f) - self.ideal)))

    def _offspring(self, i: int) -> Genotype | None:
        for _ in range(MAX_ASKS):
            pool = list(self.B[i]) if self.rng.random() < self.p_nb else list(range(self.N))
            a, b = self.rng.sample(pool, 2) if len(pool) >= 2 else (pool[0], pool[0])
            pa, pb = self.pop[a].genotype.values, self.pop[b].genotype.values
            child = [x if self.rng.random() < 0.5 else y for x, y in zip(pa, pb)]
            n = len(child)
            for j, k in enumerate(self.domains):
                if self.rng.random() < 1.0 / n:
                    child[j] = self.rng.randrange(k)
            g = Genotype(values=tuple(child))
            if g not in self.cache and is_valid(self.space, g):
                return g
            if len(self.cache) >= self._size:
                return None
        return None

    def propose(self, state: RunState) -> list[Genotype]:
        if self.used >= self.budget or self._pending:
            return []
        if not self.pop:
            init: list[Genotype] = []
            while len(init) < self.N:
                g = random_genotype(self.space, self.rng)
                if g not in init:
                    init.append(g)
            self._pending = init
        else:
            if not self._order:
                self._order = list(range(self.N))
                self.rng.shuffle(self._order)
            self._current = self._order.pop()
            g = self._offspring(self._current)
            if g is None:
                self.stop_reason = "search space exhausted"
                return []
            self._pending = [g]
        self.used += len(self._pending)
        return list(self._pending)

    def update(self, state: RunState, new_observations: list[Observation]) -> None:
        for obs in new_observations:
            self.cache.put(obs.genotype, obs.objectives)
        if not self.pop:
            self.pop = [Observation(genotype=o.genotype, objectives=tuple(o.objectives)) for o in new_observations]
            self.ideal = np.min([o.objectives for o in self.pop], axis=0)
        else:
            obs = new_observations[0]
            f = np.asarray(obs.objectives, float)
            self.ideal = np.minimum(self.ideal, f)
            for j in self.B[self._current]:
                if self._tcheby(f, j) < self._tcheby(self.pop[j].objectives, j):
                    self.pop[j] = Observation(genotype=obs.genotype, objectives=tuple(f))
        self._pending = []


# ---------------------------------------------------------------------------
# Random search
# ---------------------------------------------------------------------------


class RandomSearch:
    """Uniform over valid genotypes, without duplicates (#33, #35)."""

    def __init__(self, space, budget, rng):
        self.space, self.rng, self.budget = space, rng, int(budget)
        self.cache = EvalCache()
        self.used = 0
        self._size = space_size(space)

    def config(self) -> dict:
        return {"deduplicate": True, "valid_only": True}

    def propose(self, state: RunState) -> list[Genotype]:
        if self.used >= self.budget or len(self.cache) + self.used - len(self.cache) >= self._size:
            return []
        for _ in range(MAX_ASKS * 10):
            g = random_genotype(self.space, self.rng)
            if g not in self.cache:
                self.used += 1
                return [g]
        return []

    def update(self, state: RunState, new_observations: list[Observation]) -> None:
        for obs in new_observations:
            self.cache.put(obs.genotype, obs.objectives)
