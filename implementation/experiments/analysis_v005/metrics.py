"""Primary metrics (pre-registration §3).

- oracle spaces: IGD+ against the exact oracle front, objectives normalised to the oracle front's
  [ideal, nadir] range (lower is better);
- JAHS: hypervolume with f1/100 and (f2 - min)/(max - min) from the parameter-count table, reference
  point (r, r), divided by r^2 so that it lies in [0, 1] (decision R5 b1; higher is better).
"""

from __future__ import annotations

import numpy as np

from analysis_v005.fronts import nondominated


class IGDPlus:
    """IGD+ against one oracle front; vectorised for many calls on the same front."""

    def __init__(self, oracle):
        o = np.asarray(oracle, float)
        self.lo, hi = o.min(0), o.max(0)
        self.span = np.where(hi > self.lo, hi - self.lo, 1.0)
        self.o = (o - self.lo) / self.span

    def __call__(self, points) -> float:
        a = (np.asarray(nondominated(points), float) - self.lo) / self.span
        d = np.maximum(a[None, :, :] - self.o[:, None, :], 0.0)
        return float(np.sqrt((d ** 2).sum(-1)).min(1).mean())


def normalise_jahs(points, bounds) -> np.ndarray:
    p = np.asarray(points, float)
    (a1, b1), (a2, b2) = bounds["f1"], bounds["f2"]
    return np.column_stack([(p[:, 0] - a1) / (b1 - a1), (p[:, 1] - a2) / (b2 - a2)])


def hv2(points, ref: float) -> float:
    """2-D hypervolume (minimisation) of already normalised points w.r.t. (ref, ref); points outside
    the reference box contribute nothing."""
    front = [p for p in nondominated(map(tuple, np.asarray(points, float))) if p[0] < ref and p[1] < ref]
    total, prev_f2 = 0.0, ref
    for f1, f2 in front:  # f1 ascending, f2 descending
        total += (ref - f1) * (prev_f2 - f2)
        prev_f2 = f2
    return total


def hv_jahs(points, bounds, ref: float) -> float:
    return hv2(normalise_jahs(points, bounds), ref) / (ref * ref)


def hv_between(points_norm, ref: float, lo: float, hi: float) -> float:
    """HV of normalised points restricted to f2 in [lo, hi) (HV decomposition, §5.6)."""
    stair = [(f2, f1) for f1, f2 in nondominated(map(tuple, np.asarray(points_norm, float)))
             if f1 < ref and f2 < ref]
    stair.sort()
    total = 0.0
    for i, (f2, f1) in enumerate(stair):
        nxt = stair[i + 1][0] if i + 1 < len(stair) else ref
        a, b = max(f2, lo), min(nxt, hi)
        if b > a:
            total += (ref - f1) * (b - a)
    return total
