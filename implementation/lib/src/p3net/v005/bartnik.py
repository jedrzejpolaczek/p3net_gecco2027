"""MO-DSA-P3-GOMEA and MO-PSA-P3-GOMEA (Bartnik 2026; card
`bartnik-mo-sa-p3-gomea.md`, steps B1-B19, decisions B-1 a, B-2 a, B-3 a, B-4 b,
assumptions Z-B0-Z-B4).

Loop (Alg. 7): warm-up of real evaluations (B-2 a: 20 % of the budget), then per
iteration a random solution enters level 0 without a hill climber (B3) and climbs
every level by GOM (B4) with surrogate-gated real evaluations (B10, Alg. 8);
Compare uses real values when both solutions have them (B11). alpha starts at 1,
x gamma after an iteration with an unchanged archive, reset otherwise (B5). The
surrogate is refitted after every real evaluation (B6). The run stops after the
budget or 1000 consecutive iterations without a new real evaluation (B7).

- MO-DSA (deterministic RF per objective): a candidate is evaluated really iff, on
  every objective, its prediction beats the (1 - alpha)-quantile of the predictions
  for the really evaluated solutions -- Alg. 8 per objective (Z-B1', replacing Z-B1,
  under which the gate never relaxed and the run collapsed after the warm-up); a GOM
  change is kept by the
  MO-GOMEA rule on Compare values.
- MO-PSA (RF per objective, sigma = inter-tree standard deviation): GOM keeps a
  change unless p_revert >= tau and p_revert > p_keep (Alg. 9); the real-evaluation
  gate admits a candidate when the probability that an archive member dominates it
  (max over members) is below tau; one tau and one probability history serve both
  (Z-B2); tau = alpha-quantile of the history (Eq. 6.2).

Own choices recorded in the card (Z-B0, B-4 b): one-hot input; hyperparameter grid
`GRID`, chosen once per objective at the first fit by 3-fold CV R^2 (B18); linkage
trees by P3's entropy distance (Z-B4 pending the SAGOMEA code check); the FOS is
traversed in random order (Alg. 9 l. 1); a "generation" of B5 = one outer
iteration (Z-B3).
"""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np
from scipy.stats import norm
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold, cross_val_score

from p3net.problem.genotype import Genotype
from p3net.problem.objectives import dominates
from p3net.v005.common import is_valid, random_genotype
from p3net.v005.p3.mixing import mix_steps, mogomea_accept
from p3net.v005.p3.pyramid import Pyramid
from p3net.v005.stepper import StepMethod

#: B-4 b: own grid (the thesis gives none), fixed before any run.
GRID: tuple[dict, ...] = (
    {"max_features": 1.0, "min_samples_leaf": 1},
    {"max_features": 1.0, "min_samples_leaf": 3},
    {"max_features": "sqrt", "min_samples_leaf": 1},
    {"max_features": "sqrt", "min_samples_leaf": 3},
)
COLLAPSE_ITERATIONS = 1000


def dominance_probability(mu_new, sd_new, mu_old, sd_old) -> float:
    """Eq. 6.1 in the minimisation convention (Q-11):
    P(new > old) = prod_k Phi((mu_old_k - mu_new_k) / sqrt(sd_new_k^2 + sd_old_k^2));
    a factor with zero variance is the 0/1 step of a strict improvement."""
    p = 1.0
    for mn, sn, mo, so in zip(mu_new, sd_new, mu_old, sd_old):
        s = math.sqrt(sn * sn + so * so)
        if s == 0.0:
            p *= 1.0 if mn < mo else 0.0
        else:
            p *= float(norm.cdf((mo - mn) / s))
    return p


def quantile_threshold(history: Sequence[float], alpha: float) -> float:
    """B14 / Eq. 6.2: the alpha-quantile of the history (numpy 'linear', Q-12)."""
    return float(np.quantile(np.asarray(history, dtype=float), alpha, method="linear"))


class AlphaSchedule:
    """B5: alpha = 1 at start; x gamma after an iteration that left the archive
    unchanged; back to 1 when it changed (B-3 a: gamma = 0.999)."""

    def __init__(self, gamma: float = 0.999):
        self.gamma = gamma
        self.alpha = 1.0

    def end_iteration(self, archive_changed: bool) -> float:
        self.alpha = 1.0 if archive_changed else self.alpha * self.gamma
        return self.alpha


def psa_gom_keep(p_keep: float, p_revert: float, tau: float) -> bool:
    """B12 / Alg. 9: revert iff p_revert >= tau and p_revert > p_keep."""
    return not (p_revert >= tau and p_revert > p_keep)


def _flatten(tree):
    t = tree.tree_
    return (t.children_left.tolist(), t.children_right.tolist(), t.feature.tolist(), t.threshold.tolist(),
            t.value[:, 0, 0].tolist())


def _tree_value(flat, x) -> float:
    left, right, feat, thr, val = flat
    node = 0
    while left[node] != -1:
        node = left[node] if x[feat[node]] <= thr[node] else right[node]
    return val[node]


class _ForestPerObjective:
    """B16-B18: one random forest per objective on one-hot genotypes; the grid is
    searched once per objective at the first fit (3-fold CV, R^2)."""

    def __init__(self, domains: list[int], rng, probabilistic: bool):
        self.domains = domains
        self.offsets = np.cumsum([0] + domains)
        self.rng = rng
        self.probabilistic = probabilistic
        self.params: list[dict | None] = [None, None]
        self.models: list[RandomForestRegressor] = []

    def _x(self, gs: Sequence[Genotype]) -> np.ndarray:
        X = np.zeros((len(gs), int(self.offsets[-1])))
        for r, g in enumerate(gs):
            for i, v in enumerate(g.values):
                X[r, self.offsets[i] + v] = 1.0
        return X

    def fit(self, genotypes: Sequence[Genotype], objectives: Sequence[Sequence[float]], emit) -> None:
        X = self._x(genotypes)
        Y = np.asarray(objectives, dtype=float)
        self.models = []
        for k in range(Y.shape[1]):
            if self.params[k] is None:
                self.params[k] = self._grid_search(X, Y[:, k])
            m = RandomForestRegressor(random_state=self.rng.randrange(2**31), **self.params[k])
            m.fit(X, Y[:, k])
            self.models.append(m)
            emit("surrogate_fit", n_points=len(genotypes), objective=k)
        self._flat = [[_flatten(t) for t in m.estimators_] for m in self.models]
        self._cache = {}

    def _grid_search(self, X, y) -> dict:
        if len(y) < 6:
            return dict(GRID[0])
        cv = KFold(n_splits=3, shuffle=True, random_state=self.rng.randrange(2**31))
        best, best_score = GRID[0], -math.inf
        for params in GRID:
            m = RandomForestRegressor(random_state=0, n_estimators=50, **params)
            score = float(np.mean(cross_val_score(m, X, y, cv=cv, scoring="r2")))
            if score > best_score:
                best, best_score = params, score
        return dict(best)

    def predict(self, g: Genotype) -> tuple[tuple[float, ...], tuple[float, ...]]:
        """Mean over the trees (= RandomForestRegressor.predict) and, for PSA, the
        inter-tree standard deviation. Single-point traversal of the fitted trees
        (identical values to sklearn, without its per-call overhead), cached until the
        next fit."""
        hit = self._cache.get(g)
        if hit is not None:
            return hit
        x = self._x([g])[0]
        mus, sds = [], []
        for trees in self._flat:
            per_tree = np.array([_tree_value(t, x) for t in trees])
            mus.append(float(per_tree.mean()))
            sds.append(float(per_tree.std()) if self.probabilistic else 0.0)
        out = (tuple(mus), tuple(sds))
        self._cache[g] = out
        return out


class _BartnikEngine(StepMethod):
    probabilistic = False

    def __init__(self, space, budget, rng, *, gamma: float = 0.999, gate: str = "quantile", observer=None):
        super().__init__(space, budget, rng, observer=observer)
        if gate not in ("quantile", "elitist"):
            raise ValueError("gate must be 'quantile' (Z-B1', default) or 'elitist' (SAGOMEA code, diagnostic)")
        self.gate = gate
        self.warmup = int(budget) // 5  # B-2 a
        self.alpha = AlphaSchedule(gamma)
        self.history_p: list[float] = []  # PSA dominance-probability history (Z-B2)
        self.pyramid = Pyramid(self.domains)
        self.model = _ForestPerObjective(self.domains, rng, self.probabilistic)
        self._preds: list = []
        self._preds_fit = None
        self._last_gate: dict = {}
        self._stale = False

    def config(self) -> dict:
        return {"warmup": self.warmup, "gamma": self.alpha.gamma, "probabilistic": self.probabilistic,
                "grid": list(GRID), "gate": self.gate}

    # -- values used by Compare (B11) ------------------------------------------------
    def _value(self, g: Genotype):
        real = self.cache.get(g)
        if real is not None:
            return real, (0.0,) * len(real), True
        mu, sd = self.model.predict(g)
        return mu, sd, False

    def _real_eval(self, g: Genotype):
        """Yield one real evaluation; the refit (B6) follows right after the step's
        event is emitted (`_refit_if_stale`), before any further real evaluation."""
        f = yield g
        self._stale = True
        return f

    def _refit_if_stale(self) -> None:
        if self._stale:
            self.model.fit([o.genotype for o in self.cache.history()],
                           [o.objectives for o in self.cache.history()], self._emit)
            self._stale = False

    def _gate(self, g: Genotype, mu, sd) -> bool:
        if not self.probabilistic and self.gate == "elitist":
            # Level-2 diagnostic (2026-10-22): the gate SAGOMEA's code actually uses
            # (PopulationGeneral::setThreshold overwrites the percentile with
            # currentDelta * surrogate(elitist); real evaluation iff the prediction is
            # strictly better). Minimisation of positive values: mu_k < pred_k(elitist_k) / alpha,
            # elitist_k = best real solution on objective k, on every objective.
            hist = self.cache.history()
            thresholds = []
            for k in range(len(mu)):
                elite = min(hist, key=lambda o: o.objectives[k])
                thresholds.append(self.model.predict(elite.genotype)[0][k] / self.alpha.alpha)
            self._last_gate = {"alpha": self.alpha.alpha, "thresholds": thresholds, "reference_predictions": []}
            return all(mu[k] < thresholds[k] for k in range(len(mu)))
        if not self.probabilistic:
            # Z-B1' (2026-10-18): Alg. 8 per objective -- the prediction must beat, on every
            # objective, the (1 - alpha)-quantile of the predictions for the really evaluated
            # solutions (minimisation; alpha = 1 -> better than all of them), alpha relaxing as in B5.
            if self._preds_fit is not self.model._flat:  # predictions of H_t change only at a refit
                self._preds = [self.model.predict(o.genotype)[0] for o in self.cache.history()]
                self._preds_fit = self.model._flat
            q = 1.0 - self.alpha.alpha
            thresholds = [quantile_threshold([e[k] for e in self._preds], q) for k in range(len(mu))]
            self._last_gate = {"alpha": self.alpha.alpha, "thresholds": thresholds,
                               "reference_predictions": list(self._preds)}  # gate-time values (Q-42)
            return all(mu[k] < thresholds[k] for k in range(len(mu)))
        tau = quantile_threshold(self.history_p, self.alpha.alpha) if self.history_p else 1.0
        zero = (0.0,) * len(mu)
        p_dom = max((dominance_probability(a, zero, mu, sd) for a in self.archive.points), default=0.0)
        return p_dom < tau or not self.history_p

    def _evaluate(self, g: Genotype):
        """Alg. 8 Evaluate: prediction, and a real evaluation when the gate passes."""
        if g in self.cache:
            return True, None
        if not is_valid(self.space, g):
            return False, None
        mu, sd = self.model.predict(g)
        passed = self._gate(g, mu, sd)
        if passed:
            yield from self._real_eval(g)
        return passed, mu

    def _run(self):
        # B1: warm-up, all real, distinct, before the first training
        while len(self.cache) < self.warmup:
            g = random_genotype(self.space, self.rng)
            if g not in self.cache:
                yield g
        self.model.fit([o.genotype for o in self.cache.history()],
                       [o.objectives for o in self.cache.history()], self._emit)
        quiet = 0
        while True:
            self._emit("iteration")
            n_before, front_before = len(self.cache), list(self.archive.points)
            p = random_genotype(self.space, self.rng)  # B3: no hill climber
            yield from self._evaluate(p)
            self._refit_if_stale()
            if self.pyramid.add(0, p):
                self._emit("insert", level=0, genotype=p)
            L = 0
            while L < len(self.pyramid.levels):  # B4: every level
                o = yield from self._gom(L, p)
                vo, _, ro = self._value(o)
                vp, _, rp = self._value(p)
                compare = 1 if dominates(vo, vp) else (-1 if dominates(vp, vo) else 0)
                self._emit("level_mix", level=L, before=p, after=o, compare=compare,
                           before_real=vp if rp else None, after_real=vo if ro else None)
                if compare > 0:
                    if self.pyramid.add(L + 1, o):
                        self._emit("insert", level=L + 1, genotype=o)
                    p = o
                L += 1
            self.alpha.end_iteration(self.archive.points != front_before)
            quiet = 0 if len(self.cache) > n_before else quiet + 1
            if quiet >= COLLAPSE_ITERATIONS:  # B7
                self._stop("exploration collapse: 1000 iterations without a new real evaluation")
                return

    def _gom(self, level: int, p: Genotype):
        clusters = list(self.pyramid.clusters(level, self.rng))
        self.rng.shuffle(clusters)  # Alg. 9 l. 1: FOS in random order
        steps = mix_steps(p, self.pyramid.levels[level], clusters, self.rng)
        try:
            cluster, cand, cur = next(steps)
            while True:
                keep, passed, pred = False, False, None
                self._last_gate = {}
                if cand != cur and is_valid(self.space, cand):
                    passed, pred = yield from self._evaluate(cand)
                    keep = self._accept(cand, cur)
                self._emit("cluster_step", level=level, cluster=cluster, candidate=cand, current=cur,
                           changed=cand != cur, accepted=keep, gate_passed=passed, prediction=pred,
                           **self._last_gate)
                self._refit_if_stale()
                cluster, cand, cur = steps.send(keep)
        except StopIteration as stop:
            return stop.value

    def _accept(self, cand: Genotype, cur: Genotype) -> bool:
        vc, _, _ = self._value(cand)
        vb, _, _ = self._value(cur)
        return mogomea_accept(vc, vb, self.archive.points)


class MODSA(_BartnikEngine):
    """MO-DSA-P3-GOMEA, RF per objective (B-1 a)."""

    probabilistic = False


class MOPSA(_BartnikEngine):
    """MO-PSA-P3-GOMEA, RF per objective with inter-tree sigma (B-1 a)."""

    probabilistic = True

    def _accept(self, cand: Genotype, cur: Genotype) -> bool:
        mc, sc, _ = self._value(cand)
        mb, sb, _ = self._value(cur)
        p_keep = dominance_probability(mc, sc, mb, sb)
        p_revert = dominance_probability(mb, sb, mc, sc)
        appended = max(p_keep, p_revert)
        self.history_p.append(appended)
        tau = quantile_threshold(self.history_p, self.alpha.alpha)
        keep = psa_gom_keep(p_keep, p_revert, tau)
        self._emit("psa_decision", p_keep=p_keep, p_revert=p_revert, tau=tau, reverted=not keep,
                   appended=appended, history_len=len(self.history_p))
        return keep
