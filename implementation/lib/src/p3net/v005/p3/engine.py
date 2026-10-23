"""The P3 engine shared by canonical P3 and P3Net (card `p3-canonical.md`, K-1 a:
one engine, an exchangeable evaluator of mixing steps).

Fig. 1 'Iterate-P3' (Goldman & Punch 2014, p. 786), with the approved deviations:
O-1 categorical genotype, O-2/D-1 b two objectives (dominance in FIHC and at
promotion, MO-GOMEA acceptance in mixing), O-3/D-3 surrogate in mixing (P3Net),
O-4 valid random solutions, O-5 result = H_t.

Mixing-step evaluators (`step_evaluator`):
- "real":      every changing step is one real evaluation (canonical P3, P22/P25);
- "oracle":    the surrogate is replaced by the true function, every query is a real
               evaluation (W-K3) -- identical to "real";
- "surrogate": steps on the pairwise surrogate, telescoped from the last real
               ancestor; the result is evaluated really after each level (D-3 b);
- "gate":      every step predicted; a real evaluation only when the prediction is
               accepted, the decision then on real values (D-3 a, SA-P3-GOMEA style).
"""

from __future__ import annotations

import math
import random
from collections.abc import Generator

from p3net.harness.runner import Observation
from p3net.problem.genotype import Genotype
from p3net.problem.objectives import Objectives, dominates
from p3net.v005.common import is_valid, random_genotype
from p3net.v005.p3.fihc import fihc_steps
from p3net.v005.p3.mixing import mix_steps, mogomea_accept
from p3net.v005.p3.pyramid import Pyramid
from p3net.v005.stepper import StepMethod

STEP_EVALUATORS = ("real", "oracle", "surrogate", "gate")


def _log(o) -> tuple[float, ...]:
    return tuple(math.log(x) for x in o)


class P3Engine(StepMethod):
    def __init__(self, space, budget, rng, *, step_evaluator: str = "real", use_linkage: bool = True,
                 observer=None):
        super().__init__(space, budget, rng, observer=observer)
        if step_evaluator not in STEP_EVALUATORS:
            raise ValueError(f"step_evaluator must be one of {STEP_EVALUATORS}")
        self.step_evaluator = step_evaluator
        self.pyramid = Pyramid(self.domains)
        self.surrogate = None
        self._chain_errors: list[dict] = []
        self._fit_key = None
        if step_evaluator in ("surrogate", "gate"):
            from p3net.v005.surrogates.pairwise import PairwiseSurrogate

            self.surrogate = PairwiseSurrogate(
                self.domains, use_linkage=use_linkage, rng=random.Random(rng.getrandbits(64))
            )

    def diagnostics(self) -> dict:
        return {"chain_errors": list(self._chain_errors)}

    # -- iteration (Fig. 1) ----------------------------------------------------------
    def _run(self) -> Generator[Genotype, Objectives, None]:
        pyr = self.pyramid
        while True:
            self._emit("iteration")
            x = random_genotype(self.space, self.rng)  # P1, O-4
            fx = yield x
            x, fx = yield from self._fihc(x, fx)  # P2
            self._emit("fihc_end", genotype=x)
            if pyr.add(0, x):  # P3
                self._emit("insert", level=0, genotype=x)
            i = 0
            while i < len(pyr.levels):  # P4, P6: every level, no break
                before, f_before = x, fx
                x, fx = yield from self._mix(i, x, fx)
                self._emit("level_mix", level=i, before=before, after=x,
                           before_objectives=f_before, after_objectives=fx)
                if dominates(fx, f_before) and pyr.add(i + 1, x):  # P5, D-1 b
                    self._emit("insert", level=i + 1, genotype=x)
                i += 1

    def _fihc(self, x: Genotype, fx: Objectives):
        """P10-P12 on real evaluations (D-2 a); strict improvement = dominance."""
        steps = fihc_steps(x, self.domains, self.rng)
        try:
            cand, cur = next(steps)
            while True:
                better = 0
                if is_valid(self.space, cand):
                    fc = yield cand
                    if dominates(fc, fx):
                        better, fx = 1, fc
                cand, cur = steps.send(better)
        except StopIteration as stop:
            return stop.value, fx

    # -- mixing with one level (P20-P25) ---------------------------------------------
    def _mix(self, level: int, x: Genotype, fx: Objectives):
        clusters = self.pyramid.clusters(level, self.rng)
        donors = self.pyramid.levels[level]
        if self.step_evaluator in ("real", "oracle"):
            return (yield from self._mix_real(level, x, fx, donors, clusters))
        self._refit(clusters)
        if self.step_evaluator == "gate":
            return (yield from self._mix_gate(level, x, fx, donors, clusters))
        return (yield from self._mix_surrogate(level, x, fx, donors, clusters))

    def _mix_real(self, level, x, fx, donors, clusters):
        steps = mix_steps(x, donors, clusters, self.rng)
        try:
            cluster, cand, cur = next(steps)
            while True:
                accepted = False
                if cand != cur and is_valid(self.space, cand):
                    fc = yield cand
                    accepted = mogomea_accept(fc, fx, self.archive.points)
                    if accepted:
                        fx = fc
                self._emit("cluster_step", level=level, cluster=cluster, candidate=cand, current=cur,
                           changed=cand != cur, accepted=accepted)
                cluster, cand, cur = steps.send(accepted)
        except StopIteration as stop:
            return stop.value, fx

    def _mix_surrogate(self, level, x, fx, donors, clusters):
        anchor = Observation(genotype=x, objectives=fx)
        chain: list[Genotype] = []
        f_cur = _log(fx)
        log_archive = [_log(p) for p in self.archive.points]
        steps = mix_steps(x, donors, clusters, self.rng)
        try:
            cluster, cand, cur = next(steps)
            while True:
                accepted = False
                if cand != cur and is_valid(self.space, cand):
                    pred = self.surrogate.predict_chain(anchor, chain + [cand])
                    accepted = mogomea_accept(pred, f_cur, log_archive)
                    if accepted:
                        chain.append(cand)
                        f_cur = pred
                self._emit("cluster_step", level=level, cluster=cluster, candidate=cand, current=cur,
                           changed=cand != cur, accepted=accepted)
                cluster, cand, cur = steps.send(accepted)
        except StopIteration as stop:
            result = stop.value
        if not chain:
            return result, fx
        f_real = yield result  # D-3 b: one real evaluation after the level
        self._chain_errors.append({"chain_length": len(chain), "predicted": f_cur, "true": _log(f_real)})
        return result, f_real

    def _mix_gate(self, level, x, fx, donors, clusters):
        log_archive = [_log(p) for p in self.archive.points]
        steps = mix_steps(x, donors, clusters, self.rng)
        try:
            cluster, cand, cur = next(steps)
            while True:
                accepted = False
                if cand != cur and is_valid(self.space, cand):
                    anchor = Observation(genotype=cur, objectives=fx)
                    pred = self.surrogate.predict_chain(anchor, [cand])
                    if mogomea_accept(pred, _log(fx), log_archive):  # gate on the prediction
                        fc = yield cand
                        accepted = mogomea_accept(fc, fx, self.archive.points)
                        if accepted:
                            fx = fc
                        log_archive = [_log(p) for p in self.archive.points]
                self._emit("cluster_step", level=level, cluster=cluster, candidate=cand, current=cur,
                           changed=cand != cur, accepted=accepted)
                cluster, cand, cur = steps.send(accepted)
        except StopIteration as stop:
            return stop.value, fx

    def _refit(self, clusters) -> None:
        """S-7 a: the surrogate is current with every real evaluation and the
        level's tree (refit lazily, right before it is used)."""
        key = (len(self.cache), tuple(clusters))
        if key != self._fit_key:
            self.surrogate.fit(self.cache.history(), clusters)
            self._fit_key = key
