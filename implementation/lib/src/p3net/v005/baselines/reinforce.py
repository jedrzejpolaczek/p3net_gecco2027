"""REINFORCE with three multi-objective rewards (card `reinforce.md`).

Policy and update as the NAS-Bench-201 reference (`exps/NAS-Bench-201-algos/
reinforce.py`): a factorised policy (one softmax per variable, logits initialised
to 1e-3 * N(0, 1)), one architecture per step, a bias-corrected exponential moving
average baseline (momentum 0.9) updated *before* the advantage, loss
-log pi(a) * (r - baseline), Adam (lr 0.5, Ying et al. 2019; Z-R1).

Rewards (R-3 a: objectives normalised online to [0, 1], a = 1 - f1_n):
- "mnasnet": R = a * (c / T)^w, w = -0.07 on both sides of the target (soft
  constraint, MnasNet Eq. 2-3); c in the original units, T fixed per space (R-4 a).
- "monas":   R = alpha * a - (1 - alpha) * c_n (MONAS Eq. 3), alpha = 0.75 or 0.25.
- "adc":     Chen et al. 2020 Eq. 3 against the front before x (Alg. 2), Boltzmann
  exploration with cosine temperature 25 -> 1 and restarts every 0.2 b steps (R-6).
"""

from __future__ import annotations

import math
import statistics

import numpy as np

from p3net.harness.runner import Observation, RunState
from p3net.problem.genotype import Genotype
from p3net.problem.objectives import dominates
from p3net.v005.common import EvalCache, cardinalities, is_valid, online_minmax, space_size

MNASNET_W = -0.07
T_MAX, T_MIN = 25.0, 1.0
ADC_EPS = 0.1
#: Z-R3 (C is not given in the text): tanh saturates once front size + credit
#: reaches about 2 C; fixed before any run.
ADC_C = 5.0
MAX_DUPLICATES = 10_000


def reward_mnasnet(a: float, c: float, T: float, w: float = MNASNET_W) -> float:
    return a * (c / T) ** w


def reward_monas(a: float, c: float, alpha: float) -> float:
    return alpha * a - (1.0 - alpha) * c


def reward_adc(obj, front, eps: float = ADC_EPS, C: float = ADC_C) -> float:
    """Eq. 3 with minimised objectives, front taken before x is added (Q-27)."""
    obj = tuple(obj)
    dominating = sum(1 for p in front if dominates(tuple(p), obj))
    if dominating == 0:
        dominated = sum(1 for p in front if dominates(obj, tuple(p)))
        return math.tanh((len(front) + dominated) / C)
    rho = sum(1 for p in front if math.dist(tuple(p), obj) < eps)  # Euclidean (Q-27)
    return -math.tanh((dominating + rho) / C)


def temperature(step: int, period: int) -> float:
    """Chen et al. §4.3: cosine decay from T_max to T_min with warm restarts."""
    return T_MIN + 0.5 * (T_MAX - T_MIN) * (1.0 + math.cos(math.pi * (step % period) / period))


class _Adam:
    def __init__(self, shapes, lr, betas=(0.9, 0.999), eps=1e-8):
        self.lr, (self.b1, self.b2), self.eps = lr, betas, eps
        self.m = [np.zeros(s) for s in shapes]
        self.v = [np.zeros(s) for s in shapes]
        self.t = 0

    def step(self, params, grads):
        self.t += 1
        for p, g, m, v in zip(params, grads, self.m, self.v):
            m *= self.b1
            m += (1 - self.b1) * g
            v *= self.b2
            v += (1 - self.b2) * g * g
            mh = m / (1 - self.b1**self.t)
            vh = v / (1 - self.b2**self.t)
            p -= self.lr * mh / (np.sqrt(vh) + self.eps)


class Reinforce:
    def __init__(self, space, budget, rng, *, reward: str = "monas", alpha: float = 0.75,
                 target: float | None = None, learning_rate: float = 0.5, baseline_momentum: float = 0.9):
        if reward not in ("mnasnet", "monas", "adc"):
            raise ValueError("reward must be 'mnasnet', 'monas' or 'adc'")
        self.space, self.rng, self.budget = space, rng, int(budget)
        self.reward, self.alpha, self.target = reward, float(alpha), target
        self.domains = cardinalities(space)
        np_rng = np.random.default_rng(rng.getrandbits(64))
        self.logits = [1e-3 * np_rng.standard_normal(k) for k in self.domains]
        self.lr, self.momentum = float(learning_rate), float(baseline_momentum)
        self._adam = _Adam([k for k in self.domains], self.lr)
        self._num = self._den = 0.0
        self.cache = EvalCache()
        self.front: list[tuple[float, ...]] = []  # ADC front of real objectives
        self.used = self.step_count = self.n_policy_updates = 0
        self.period = max(1, round(0.2 * self.budget))
        self._pending: Genotype | None = None
        self._size = space_size(space)
        self.stop_reason: str | None = None

    def config(self) -> dict:
        return {"reward": self.reward, "alpha": self.alpha, "target": self.target, "learning_rate": self.lr,
                "baseline_momentum": self.momentum, "period": self.period, "adc_c": ADC_C, "adc_eps": ADC_EPS}

    # -- policy --------------------------------------------------------------------
    def _temp(self) -> float:
        return temperature(self.step_count, self.period) if self.reward == "adc" else 1.0

    def _probs(self) -> list[np.ndarray]:
        T = self._temp()
        out = []
        for z in self.logits:
            e = np.exp((z - z.max()) / T)
            out.append(e / e.sum())
        return out

    def _sample(self) -> Genotype:
        while True:
            g = Genotype(values=tuple(int(self.rng.choices(range(len(p)), weights=p)[0]) for p in self._probs()))
            if is_valid(self.space, g):
                return g

    def _reward(self, g: Genotype, f: tuple[float, ...]) -> float:
        hist = [o.objectives for o in self.cache.history()]
        norm = online_minmax(hist)
        f1n, f2n = norm(f)
        a = 1.0 - f1n
        if self.reward == "monas":
            return reward_monas(a, f2n, self.alpha)
        if self.reward == "mnasnet":
            if self.target is None:  # R-4 a expects T from the experiment config
                self.target = statistics.median(h[1] for h in hist)
            return reward_mnasnet(a, f[1], self.target)
        front_n = [norm(p) for p in self.front if tuple(p) != tuple(f)]
        return reward_adc(norm(f), front_n)

    def _learn(self, g: Genotype, r: float) -> None:
        self._num = self.momentum * self._num + (1 - self.momentum) * r
        self._den = self.momentum * self._den + (1 - self.momentum)
        adv = r - self._num / self._den  # baseline updated before the advantage
        T = self._temp()
        grads = []
        for z, p, a in zip(self.logits, self._probs(), g.values):
            onehot = np.zeros_like(z)
            onehot[a] = 1.0
            grads.append(-adv * (onehot - p) / T)  # d(-log pi(a) * adv) / d logits
        self._adam.step(self.logits, grads)
        self.n_policy_updates += 1
        self.step_count += 1

    def _update_front(self, f) -> None:
        f = tuple(f)
        if any(dominates(p, f) or p == f for p in self.front):
            return
        self.front = [p for p in self.front if not dominates(f, p)] + [f]

    # -- ask-tell ----------------------------------------------------------------------
    def propose(self, state: RunState) -> list[Genotype]:
        if self.used >= self.budget or self.stop_reason is not None:
            return []
        for _ in range(MAX_DUPLICATES):
            g = self._sample()
            known = self.cache.get(g)
            if known is None:
                self._pending = g
                self.used += 1
                return [g]
            self._learn(g, self._reward(g, known))  # W-R7: duplicates still update the policy
            if len(self.cache) >= self._size:
                self.stop_reason = "search space exhausted"
                return []
        self.stop_reason = f"exploration collapse: {MAX_DUPLICATES} consecutive duplicate samples (#36)"
        return []

    def update(self, state: RunState, new_observations: list[Observation]) -> None:
        for obs in new_observations:
            f = tuple(float(x) for x in obs.objectives)
            self.cache.put(obs.genotype, f)
            r = self._reward(obs.genotype, f)
            self._update_front(f)
            self._learn(obs.genotype, r)
        self._pending = None
