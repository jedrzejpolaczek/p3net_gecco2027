"""Runnable v005 methods of the P3 family (interfaces §1, §7).

All take (space, budget, rng, **params) (Q-03) and an optional `observer`
(Q-02). None of them accepts the benchmark or an f2 function (#6).
"""

from __future__ import annotations

from p3net.v005.p3.engine import P3Engine


class P3Canonical(P3Engine):
    """Card `p3-canonical.md`: P3 with every mixing step a real evaluation."""

    def __init__(self, space, budget, rng, *, observer=None):
        super().__init__(space, budget, rng, step_evaluator="real", observer=observer)


class P3Net(P3Engine):
    """Card `p3net.md` D-3 b: mixing on the pairwise surrogate, a real evaluation
    of the result after each level. `step_evaluator="oracle"` is W-K3's control."""

    def __init__(self, space, budget, rng, *, step_evaluator: str = "surrogate", observer=None):
        super().__init__(space, budget, rng, step_evaluator=step_evaluator, observer=observer)


class P3NetGate(P3Engine):
    """Card `p3net.md` D-3 a: the same surrogate as a gate (comparison variant)."""

    def __init__(self, space, budget, rng, *, observer=None):
        super().__init__(space, budget, rng, step_evaluator="gate", observer=observer)


class P3NetNoLink(P3Engine):
    """Card `p3net-surrogate.md` S-2 c: P3Net with a surrogate without linkage features."""

    def __init__(self, space, budget, rng, *, observer=None):
        super().__init__(space, budget, rng, step_evaluator="surrogate", use_linkage=False,
                         observer=observer)
