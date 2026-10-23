"""Level-1 tests for the P3Net surrogate (card
`notes/plans/v005-sources/p3net-surrogate.md`, W-S1-W-S10).

Own design with literature elements: pairwise regression (Dushatskiy et al.,
CS-GOMEA, GECCO'19, §2.1, Alg. 1), telescoping from the last really
evaluated ancestor (S-1 a), linkage-dependent interaction features (S-2 b),
log scale (S-3 a), RF (S-4 a), both objectives (S-5 a), grouped CV (S-8),
start after the first FIHC (S-9 a).
"""

from __future__ import annotations

import math
import random
import statistics

import numpy as np
import pytest

from p3net.harness.runner import Observation

from ._support import (
    CountingObjective,
    EventLog,
    G,
    additive_cost,
    assert_budget_respected,
    assert_no_benchmark_access,
    drive,
    make,
    random_weights,
    trap_f1,
    trap_space,
)

N_BLOCKS, BLOCK, K = 4, 2, 3
N = N_BLOCKS * BLOCK
BLOCKS = [tuple(range(b * BLOCK, (b + 1) * BLOCK)) for b in range(N_BLOCKS)]


def _f1():
    return trap_f1(BLOCK, N)


def _f2():
    return additive_cost(random_weights([K] * N, seed=3))


def _history(n: int, seed: int, f1=None, f2=None) -> list[Observation]:
    f1, f2 = f1 or _f1(), f2 or _f2()
    rng = random.Random(seed)
    seen, out = set(), []
    while len(out) < n:
        g = tuple(rng.randrange(K) for _ in range(N))
        if g in seen:
            continue
        seen.add(g)
        out.append(Observation(genotype=G(*g), objectives=(f1(g), f2(g))))
    return out


def _surrogate(use_linkage=True, seed=0):
    from p3net.v005.surrogates.pairwise import PairwiseSurrogate

    return PairwiseSurrogate([K] * N, use_linkage=use_linkage, rng=random.Random(seed))


def _all_clusters(link):
    singles = [(i,) for i in range(N)]
    return singles + [c for c in link if len(c) > 1]


def _p3net_run(cls_name="P3Net", budget=200, seed=0, log=None, **kw):
    from p3net.v005 import methods

    space = trap_space(3, 3, 3)
    obj = CountingObjective(trap_f1(3, 9), additive_cost(random_weights([3] * 9, seed=7)), log=log)
    if log is not None:
        kw["observer"] = log
    m = make(getattr(methods, cls_name), space, budget, seed, **kw)
    drive(m, obj, budget)
    return m, obj


def _spy_predictions(monkeypatch, log, repeat=1):
    from p3net.v005.surrogates import pairwise

    counter = {"n": 0}
    for name in ("predict_delta", "predict_chain"):
        orig = getattr(pairwise.PairwiseSurrogate, name)

        def spy(self, *a, _o=orig, **k):
            counter["n"] += 1
            if log is not None:
                log.append(("predict", {}))
            out = _o(self, *a, **k)
            for _ in range(repeat - 1):
                _o(self, *a, **k)
            return out

        monkeypatch.setattr(pairwise.PairwiseSurrogate, name, spy)
    return counter


# ---------------------------------------------------------------------------


def test_WS1_predictions_never_consume_budget(monkeypatch):
    """W-S1: the surrogate never calls the benchmark; the number of real
    evaluations does not depend on the number of predictions (doubling every
    prediction call leaves the evaluated sequence unchanged)."""
    counter = _spy_predictions(monkeypatch, None, repeat=1)
    _, obj1 = _p3net_run(budget=200, seed=2)
    n_pred = counter["n"]
    assert n_pred > 0, "P3Net made no surrogate prediction at all"
    assert_budget_respected(obj1, 200, exact=True)
    monkeypatch.undo()
    _spy_predictions(monkeypatch, None, repeat=2)
    _, obj2 = _p3net_run(budget=200, seed=2)
    assert obj1.calls == obj2.calls


def test_WS2_predicts_both_objectives_f2_from_model():
    """W-S2 (S-5 a, #6): the surrogate predicts both objectives; predicted f2
    of unevaluated candidates follows the true (additive) f2."""
    s = _surrogate()
    hist = _history(80, 0)
    s.fit(hist, _all_clusters(BLOCKS))
    f2 = _f2()
    anchor = hist[0]
    rng = random.Random(9)
    pred, true = [], []
    for _ in range(40):
        g = tuple(rng.randrange(K) for _ in range(N))
        out = s.predict_chain(anchor, [G(*g)])
        assert len(out) == 2 and all(math.isfinite(x) for x in out)
        pred.append(out[1])
        true.append(f2(g))
    rho = _spearman(pred, true)
    assert rho >= 0.8, f"predicted f2 does not track true f2 (Spearman {rho:.2f})"


def test_WS2_p3net_has_no_access_to_f2_of_unevaluated():
    """W-S2 (#6): neither P3Net nor its variants accept an f2/benchmark hook."""
    from p3net.v005 import methods

    for name in ("P3Net", "P3NetGate", "P3NetNoLink", "P3Canonical"):
        assert_no_benchmark_access(getattr(methods, name))


def _interaction(s, i, j):
    a = [0] * N
    bi, bj, bij = list(a), list(a), list(a)
    bi[i] = 1
    bj[j] = 1
    bij[i] = bij[j] = 1
    F = lambda x, y: np.asarray(s.features(G(*x), G(*y)), dtype=float)  # noqa: E731
    return F(a, bij) - F(a, bi) - F(a, bj) + F(a, a)


def test_WS3_interaction_features_only_within_clusters():
    """W-S3 (S-2 b): interaction features exist only for variable pairs in
    the same cluster of the current tree; changing the tree changes them."""
    hist = _history(60, 1)
    s = _surrogate(use_linkage=True)
    s.fit(hist, _all_clusters([(0, 1), (2, 3), (4, 5), (6, 7)]))
    assert np.any(_interaction(s, 0, 1) != 0), "no interaction feature for a same-cluster pair"
    assert np.all(_interaction(s, 0, 2) == 0), "interaction feature for a cross-cluster pair"
    s.fit(hist, _all_clusters([(0, 2), (1, 3), (4, 5), (6, 7)]))
    assert np.any(_interaction(s, 0, 2) != 0), "tree change did not add the new interaction"
    assert np.all(_interaction(s, 0, 1) == 0), "tree change did not remove the old interaction"


def test_WS3_nolink_variant_has_no_interactions():
    """W-S3 / S-2 c (P3Net-nolink): without linkage the features are additive
    in the changed variables."""
    hist = _history(60, 1)
    s = _surrogate(use_linkage=False)
    s.fit(hist, _all_clusters([(0, 1), (2, 3), (4, 5), (6, 7)]))
    assert np.all(_interaction(s, 0, 1) == 0)


def _block_pairs(seed, n):
    rng = random.Random(seed)
    pairs = []
    while len(pairs) < n:
        a = [rng.randrange(K) for _ in range(N)]
        b = list(a)
        blk = rng.choice(BLOCKS)
        for i in blk:
            b[i] = rng.choice([v for v in range(K) if v != a[i]])
        pairs.append((tuple(a), tuple(b)))
    return pairs


def test_WS4_linkage_features_predict_better_on_traps():
    """W-S4 (S-2 b vs S-2 c): on k-ary traps (blocks of 2, alphabet 3) the
    model with in-cluster interaction features predicts held-out
    within-block changes better than the model without them: mean MAE ratio
    < 0.9 and better in >= 4/5 seeds."""
    f1 = _f1()
    wins, ratios = 0, []
    for seed in range(5):
        hist = _history(120, 100 + seed)
        errs = {}
        for link in (True, False):
            s = _surrogate(use_linkage=link, seed=seed)
            s.fit(hist, _all_clusters(BLOCKS))
            e = []
            for a, b in _block_pairs(200 + seed, 60):
                true = math.log(f1(a)) - math.log(
                    f1(b)
                )  # S-1 a: delta(x_{i-1}, x_i) = f(x_{i-1}) - f(x_i), log scale
                e.append(abs(s.predict_delta(G(*a), G(*b))[0] - true))
            errs[link] = statistics.fmean(e)
        ratios.append(errs[True] / errs[False])
        wins += errs[True] < errs[False]
    assert wins >= 4 and statistics.fmean(ratios) < 0.9, f"ratios {ratios}"


def test_WS5_log_scale_predictions_are_scale_invariant():
    """W-S5 (S-3 a): training and prediction in log scale -- multiplying f1
    and f2 by constants leaves predicted log-deltas unchanged."""
    hist = _history(70, 4)
    scaled = [
        Observation(genotype=o.genotype, objectives=(10.0 * o.objectives[0], 7.0 * o.objectives[1]))
        for o in hist
    ]
    s1, s2 = _surrogate(seed=5), _surrogate(seed=5)
    s1.fit(hist, _all_clusters(BLOCKS))
    s2.fit(scaled, _all_clusters(BLOCKS))
    rng = random.Random(1)
    for _ in range(30):
        a = G(*(rng.randrange(K) for _ in range(N)))
        b = G(*(rng.randrange(K) for _ in range(N)))
        d1, d2 = s1.predict_delta(a, b), s2.predict_delta(a, b)
        assert np.allclose(d1, d2, rtol=1e-6, atol=1e-9), f"{d1} vs {d2}: not on a log scale"


def test_WS5_nonpositive_objective_rejected():
    """W-S5 (S-3 a: 'log requires values > 0 -- needs an assertion')."""
    hist = _history(20, 4)
    bad = hist[:-1] + [
        Observation(genotype=hist[-1].genotype, objectives=(0.0, hist[-1].objectives[1]))
    ]
    with pytest.raises((ValueError, AssertionError)):
        _surrogate().fit(bad, _all_clusters(BLOCKS))


def test_WS5_acceptance_decisions_invariant_under_log():
    """W-S5 (S-3: D-1 is invariant to monotone transforms of each
    objective): mogomea_accept gives the same decision on log values."""
    from p3net.v005.p3.mixing import mogomea_accept

    rng = random.Random(0)
    lg = lambda o: (math.log(o[0]), math.log(o[1]))  # noqa: E731
    for _ in range(2000):
        pt = lambda: (rng.choice([1, 2, 3, 4, 5]) * 1.0, rng.choice([1, 2, 3, 4, 5]) * 1.0)  # noqa: E731
        new, old = pt(), pt()
        arch = [pt() for _ in range(rng.randrange(0, 5))]
        assert mogomea_accept(new, old, arch) == mogomea_accept(
            lg(new), lg(old), [lg(a) for a in arch]
        )


def test_WS6_grouped_cv_no_solution_in_train_and_validation():
    """W-S6 (S-8): folds are grouped by solutions -- no history point is in
    both the training and the validation part of a fold; every point is
    validated exactly once."""
    from p3net.v005.surrogates.pairwise import grouped_cv_folds

    hist = _history(37, 6)
    folds = grouped_cv_folds(hist, 5, random.Random(0))
    assert len(folds) == 5
    val_count = [0] * len(hist)
    for train, val in folds:
        assert not (set(train) & set(val)), "a solution is in both train and validation"
        assert set(train) | set(val) <= set(range(len(hist)))
        for i in val:
            val_count[i] += 1
    assert val_count == [1] * len(hist)


def test_WS7_chain_error_is_recorded():
    """W-S7 (S-6 a diagnostics): P3Net records prediction error vs chain
    length for each real evaluation that ends a surrogate chain; `true` is
    the log of the really evaluated objectives (Q-36)."""
    m, obj = _p3net_run(budget=250, seed=3)
    rows = m.diagnostics()["chain_errors"]
    assert rows, "no chain-error records"
    raw = [obj.value(g) for g in obj.calls]
    # both "predicted" and "true" on the log scale (Q-06, Q-36)
    evaluated = [(math.log(a), math.log(b)) for a, b in raw]
    for r in rows:
        assert int(r["chain_length"]) >= 1
        assert len(r["predicted"]) == 2
        t = tuple(r["true"])
        assert any(np.allclose(t, e, rtol=1e-12, atol=1e-12) for e in evaluated)


def test_WS8_no_surrogate_before_first_completed_fihc(monkeypatch):
    """W-S8 (S-9 a): before the first FIHC completes, no surrogate prediction
    is made (mixing up to then uses real evaluations)."""
    log = EventLog()
    _spy_predictions(monkeypatch, log)
    _p3net_run(budget=250, seed=1, log=log)
    kinds = [k for k, _ in log]
    assert "fihc_end" in kinds and "predict" in kinds
    assert kinds.index("predict") > kinds.index("fihc_end")


def test_WS9_model_is_antisymmetric():
    """W-S9: delta(x, x') ~ -delta(x', x) and delta(x, x) ~ 0."""
    s = _surrogate()
    s.fit(_history(80, 8), _all_clusters(BLOCKS))
    rng = random.Random(2)
    sym, mag, self_ = [], [], []
    for _ in range(50):
        a = G(*(rng.randrange(K) for _ in range(N)))
        b = G(*(rng.randrange(K) for _ in range(N)))
        dab, dba = np.asarray(s.predict_delta(a, b)), np.asarray(s.predict_delta(b, a))
        sym.append(np.abs(dab + dba))
        mag.append(np.abs(dab))
        self_.append(np.abs(np.asarray(s.predict_delta(a, a))))
    scale = np.mean(mag, axis=0)
    assert np.all(np.mean(sym, axis=0) <= 0.1 * scale + 1e-9), "not antisymmetric"
    assert np.all(np.mean(self_, axis=0) <= 0.1 * scale + 1e-9), "delta(x, x) is not ~0"


def test_WS10_same_surrogate_in_p3net_and_gate_variant(monkeypatch):
    """W-S10 (R4): P3Net (D-3 b) and P3Net-gate (D-3 a) build the same
    surrogate (class and settings); P3Net-nolink differs only by
    use_linkage=False."""
    from p3net.v005.surrogates import pairwise

    made = []
    orig = pairwise.PairwiseSurrogate.__init__

    def spy(self, domains, *a, **k):
        made.append((list(domains), {kk: v for kk, v in k.items() if kk != "rng"}))
        return orig(self, domains, *a, **k)

    monkeypatch.setattr(pairwise.PairwiseSurrogate, "__init__", spy)
    configs = {}
    for name in ("P3Net", "P3NetGate", "P3NetNoLink"):
        made.clear()
        _p3net_run(name, budget=150, seed=0)
        assert made, f"{name} never built a PairwiseSurrogate"
        configs[name] = made[0]
    assert configs["P3Net"] == configs["P3NetGate"]
    assert configs["P3Net"][1].get("use_linkage") is True
    nolink = dict(configs["P3NetNoLink"][1])
    assert nolink.pop("use_linkage") is False
    ref = dict(configs["P3Net"][1])
    ref.pop("use_linkage")
    assert nolink == ref


def _spearman(a, b):
    ra = np.argsort(np.argsort(a))
    rb = np.argsort(np.argsort(b))
    return float(np.corrcoef(ra, rb)[0, 1])
