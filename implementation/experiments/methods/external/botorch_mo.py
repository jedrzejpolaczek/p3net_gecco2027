"""Gaussian-process Bayesian optimisation baselines: qNEHVI and qParEGO (BoTorch).

Why these arms: GP-based BO is the main family of classic HPO missing from
the comparison -- TPE and MO-BOHB are density-estimator (KDE) based.
qNEHVI targets hypervolume improvement directly; qParEGO scalarises with
a random Chebyshev weight per step. Same GP, same candidate generation,
same budget -- only the acquisition differs.

Model: botorch.models.MixedSingleTaskGP with every genotype coordinate
declared categorical (cat_dims = all), i.e. BoTorch's categorical kernel on
an ordinal index encoding -- the library's own model for categorical
inputs, not a one-hot hack. Both objectives are modelled jointly (two
outputs, BoTorch's default Standardize outcome transform). BoTorch
maximises, so objectives are negated.

Initial design: 2 * (d + 1) uniformly random valid genotypes, the
initialisation used throughout BoTorch's multi-objective tutorials.

Acquisition:
  * qNEHVI -> qLogNoisyExpectedHypervolumeImprovement (BoTorch's
    recommended numerically stable form of qNEHVI), reference point set
    10% of the observed range beyond the worst observed value of each
    (negated) objective, the heuristic BoTorch's tutorials use.
  * qParEGO -> qLogNoisyExpectedImprovement on a Chebyshev scalarisation
    with weights drawn uniformly from the simplex at every step, BoTorch's
    qParEGO recipe.
Both use a 128-sample Sobol QMC sampler and prune_baseline=True.

Acquisition maximisation: the search space is categorical and has a
validity constraint (a cell must connect input to output), which
gradient-based optimisers cannot respect. The acquisition is therefore
maximised over a candidate pool rebuilt every step: `pool_size` uniformly
random valid unevaluated genotypes plus every valid unevaluated
one-coordinate neighbour of the current Pareto set. The best-scoring
candidate is proposed.

Device: CPU by default; `device: "cuda"` (or "auto") moves the model and the
candidate pool to the GPU. Tensors are float64 on either. On CUDA,
deterministic algorithms are enforced and the pool is scored in chunks of
`gpu_chunk_size` to bound memory.

CPU is the default because a 4 GB GPU is not enough for this arm at the
budgets this project uses: on the first full pipeline run, 509 of 578
failures were `CUDA error: out of memory` from qNEHVI and qParEGO at budgets
200 and 350, while the same runs cost about 14 minutes each on the CPU. Set
`device: "cuda"` only with a GPU whose memory has been checked at the
largest budget. CPU and GPU runs of the same seed are not expected to be
identical (different floating point kernels); every run records its device.

Efficiency choice (not a performance tweak): GP hyperparameters are refit
at every step, but the optimiser starts from the previous step's
hyperparameters (kernel, mean and likelihood parameters only -- never the
outcome transform's data-dependent buffers). Measured on this genotype:
~0.9 s per fit instead of ~4.7 s from scratch.
"""

from __future__ import annotations

import os
import random
import time
import warnings
from dataclasses import dataclass, field

import torch
from p3net.harness.evaluation_cache import EvaluationCache
from p3net.harness.runner import Observation, RunState
from p3net.problem.decoding import Validity, is_valid
from p3net.problem.genotype import Genotype, SearchSpace
from p3net.problem.objectives import pareto_front

from methods._shared import random_valid_batch

ACQUISITIONS = ("qnehvi", "qparego")


@dataclass
class BoTorchMO:
    search_space: SearchSpace
    validity: Validity
    rng: random.Random
    acquisition: str = "qnehvi"
    seed: int = 0
    n_initial: int | None = None
    pool_size: int = 1024
    mc_samples: int = 128
    #: "cpu" (default), "cuda", or "auto" = CUDA when available.
    device: str = "cpu"
    #: Candidates scored per acquisition call on CUDA (bounds GPU memory).
    gpu_chunk_size: int = 256
    experiment_type: str = "botorch_mo"
    protocol_version: str = "v1"
    cache: EvaluationCache = field(default_factory=EvaluationCache)

    fit_seconds: float = field(default=0.0, init=False)
    _history: dict[Genotype, Observation] = field(default_factory=dict, init=False, repr=False)
    _order: list[Genotype] = field(default_factory=list, init=False, repr=False)
    _hyperparameters: dict | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.acquisition not in ACQUISITIONS:
            raise ValueError(f"acquisition must be one of {ACQUISITIONS}")
        if self.n_initial is None:
            self.n_initial = 2 * (self.search_space.n + 1)
        self._index = [
            {value: i for i, value in enumerate(domain.values)}
            for domain in self.search_space.domains
        ]
        if self.device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        if self.device == "cuda":
            # Deterministic cuBLAS and kernels, so a seeded run repeats on
            # the same GPU (pipeline determinism check). Must be set before
            # cuBLAS is first used in this process.
            os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
            torch.use_deterministic_algorithms(True, warn_only=True)
        self._device = torch.device(self.device)
        torch.manual_seed(self.seed)

    # -- encoding ---------------------------------------------------------

    def _encode(self, genotypes: list[Genotype]) -> torch.Tensor:
        return torch.tensor(
            [[self._index[i][v] for i, v in enumerate(g.values)] for g in genotypes],
            dtype=torch.double,
            device=self._device,
        )

    # -- harness.Method ---------------------------------------------------

    def propose(self, state: RunState) -> list[Genotype]:
        if len(self._history) < self.n_initial:
            return random_valid_batch(
                1,
                self.search_space,
                self.validity,
                self.rng,
                self.cache,
                experiment_type=self.experiment_type,
                protocol_version=self.protocol_version,
            )
        pool = self._candidate_pool()
        if not pool:
            return []
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            acq = self._acquisition_function()
            with torch.no_grad():
                X_pool = self._encode(pool).unsqueeze(1)
                if self._device.type == "cuda":
                    scores = torch.cat(
                        [
                            acq(X_pool[i : i + self.gpu_chunk_size])
                            for i in range(0, len(pool), self.gpu_chunk_size)
                        ]
                    )
                else:
                    scores = acq(X_pool)
        best = pool[int(torch.argmax(scores))]
        self.cache.record_proposal(
            best, experiment_type=self.experiment_type, protocol_version=self.protocol_version
        )
        return [best]

    def update(self, state: RunState, new_observations: list[Observation]) -> None:
        for obs in new_observations:
            self.cache.put(
                obs.genotype,
                obs.objectives,
                experiment_type=self.experiment_type,
                protocol_version=self.protocol_version,
            )
            self._history[obs.genotype] = obs
            self._order.append(obs.genotype)

    # -- internals --------------------------------------------------------

    def _candidate_pool(self) -> list[Genotype]:
        pool: dict[Genotype, None] = {}
        front = pareto_front(list(self._order), lambda g: self._history[g].objectives)
        for g in front:
            for i, domain in enumerate(self.search_space.domains):
                for value in domain.values:
                    if value != g.values[i]:
                        pool[g.with_values(indices=[i], new_values=[value])] = None
        added = attempts = 0
        while added < self.pool_size and attempts < self.pool_size * 20:
            attempts += 1
            g = self.search_space.sample_uniform(self.rng)
            if g not in pool:
                pool[g] = None
                added += 1
        return [
            g
            for g in pool
            if g not in self._history
            and is_valid(g, self.validity)
            and not self.cache.has(
                g, experiment_type=self.experiment_type, protocol_version=self.protocol_version
            )
        ]

    def _fit_model(self):
        from botorch.fit import fit_gpytorch_mll
        from botorch.models import MixedSingleTaskGP
        from gpytorch.mlls import ExactMarginalLogLikelihood

        X = self._encode(self._order)
        Y = -torch.tensor(
            [self._history[g].objectives for g in self._order],
            dtype=torch.double,
            device=self._device,
        )
        model = MixedSingleTaskGP(X, Y, cat_dims=list(range(self.search_space.n)))
        if self._hyperparameters is not None:
            model.load_state_dict(self._hyperparameters, strict=False)
        started = time.perf_counter()
        fit_gpytorch_mll(ExactMarginalLogLikelihood(model.likelihood, model))
        self.fit_seconds += time.perf_counter() - started
        self._hyperparameters = {
            k: v.detach().clone()
            for k, v in model.state_dict().items()
            if not k.startswith("outcome_transform")
        }
        return model, X, Y

    def _acquisition_function(self):
        from botorch.sampling import SobolQMCNormalSampler

        model, X, Y = self._fit_model()
        sampler = SobolQMCNormalSampler(
            sample_shape=torch.Size([self.mc_samples]), seed=self.rng.randrange(2**31)
        )
        if self.acquisition == "qnehvi":
            from botorch.acquisition.multi_objective.logei import (
                qLogNoisyExpectedHypervolumeImprovement,
            )

            worst, best = Y.min(dim=0).values, Y.max(dim=0).values
            ref_point = worst - 0.1 * (best - worst).clamp_min(1e-9)
            return qLogNoisyExpectedHypervolumeImprovement(
                model=model, ref_point=ref_point, X_baseline=X, sampler=sampler, prune_baseline=True
            )

        from botorch.acquisition.logei import qLogNoisyExpectedImprovement
        from botorch.acquisition.objective import GenericMCObjective
        from botorch.utils.multi_objective.scalarization import get_chebyshev_scalarization
        from botorch.utils.sampling import sample_simplex

        weights = (
            sample_simplex(Y.shape[-1], dtype=torch.double, seed=self.rng.randrange(2**31))
            .squeeze(0)
            .to(self._device)
        )
        scalarization = get_chebyshev_scalarization(weights=weights, Y=Y)
        objective = GenericMCObjective(lambda samples, X=None: scalarization(samples))
        return qLogNoisyExpectedImprovement(
            model=model, X_baseline=X, sampler=sampler, objective=objective, prune_baseline=True
        )


def botorch_method(
    search_space: SearchSpace,
    validity: Validity,
    rng: random.Random,
    *,
    acquisition: str,
    seed: int | None = None,
    cache: EvaluationCache | None = None,
    **params,
) -> BoTorchMO:
    return BoTorchMO(
        search_space=search_space,
        validity=validity,
        rng=rng,
        acquisition=acquisition,
        seed=seed if seed is not None else 0,
        experiment_type=f"botorch_{acquisition}",
        cache=cache if cache is not None else EvaluationCache(),
        **params,
    )
