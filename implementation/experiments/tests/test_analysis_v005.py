"""analysis_v005 (task 5a): metrics, orientation of effects, TOST verdicts, plan expansion, and that the
anytime curves end at the per-run value (on the A8 records when present)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from analysis_v005 import per_run, secondary, spec, tests
from analysis_v005.metrics import IGDPlus, hv2, hv_between, hv_jahs

EXP = Path(__file__).resolve().parent.parent
A8 = [EXP / "results" / "a8" / r for r in ("ec1ba9cb", "e6734ccd", "7b7abd84")]
BOUNDS = {"f1": [0.0, 100.0], "f2": [10.0, 110.0]}


def test_hv_jahs_normalised_to_unit_box():
    # ideal point -> whole (1.1 x 1.1) box -> 1.0 after dividing by 1.21
    assert hv_jahs([(0.0, 10.0)], BOUNDS, 1.1) == pytest.approx(1.0)
    # a point on the worst bounds still contributes (decision R5 b1): 0.1 * 0.1 / 1.21
    assert hv_jahs([(100.0, 110.0)], BOUNDS, 1.1) == pytest.approx(0.01 / 1.21)
    # with the reference on the bounds it would contribute nothing
    assert hv2([(1.0, 1.0)], 1.0) == 0.0


def test_hv_two_points_and_dominated_point_ignored():
    pts = [(0.2, 0.6), (0.5, 0.1), (0.6, 0.7)]  # third dominated
    expected = (1.0 - 0.2) * (1.0 - 0.6) + (1.0 - 0.5) * (0.6 - 0.1)
    assert hv2(pts, 1.0) == pytest.approx(expected)
    assert hv_between(pts, 1.0, -np.inf, np.inf) == pytest.approx(expected)
    t = 0.4
    assert hv_between(pts, 1.0, -np.inf, t) + hv_between(pts, 1.0, t, np.inf) == pytest.approx(expected)


def test_igd_plus_zero_on_oracle_and_positive_off_it():
    oracle = [(0.0, 1.0), (0.5, 0.5), (1.0, 0.0)]
    igd = IGDPlus(oracle)
    assert igd(oracle) == pytest.approx(0.0)
    assert igd(oracle + [(2.0, 2.0)]) == pytest.approx(0.0)  # dominated extra point changes nothing
    assert igd([(1.0, 1.0)]) > 0


def _frame(metric, ref_values, arm_values, arm="v005_random_search", group="primary"):
    rows = [dict(method=spec.REF, value=v) for v in ref_values] + [dict(method=arm, value=v) for v in arm_values]
    df = pd.DataFrame(rows)
    df["space"], df["budget"], df["metric"], df["group"] = "s", 100, metric, group
    return df


@pytest.mark.parametrize("metric,good,bad", [("hv", 0.9, 0.5), ("igd", 0.1, 0.5)])
def test_delta_positive_when_reference_is_better(metric, good, bad):
    rng = np.random.default_rng(0)
    df = _frame(metric, good + 0.01 * rng.standard_normal(30), bad + 0.01 * rng.standard_normal(30))
    res = tests.family_tests(df)
    row = res[(res.family == "Q1") & (res.arm == "v005_random_search")].iloc[0]
    assert row.delta == pytest.approx(1.0) and row.significant and row.direction == "REF better"


def test_holm_family_size_counts_only_arms_present():
    df = pd.concat([_frame("hv", np.linspace(0, 1, 30), np.linspace(0, 1, 30), arm=a) for a in spec.Q1[:3]])
    df = df.drop_duplicates()
    res = tests.family_tests(df)
    assert set(res[res.family == "Q1"].family_size) == {3}


def test_tost_verdicts():
    rng = np.random.default_rng(1)
    same = rng.standard_normal(400)
    df = _frame("hv", same, rng.permutation(same), arm="v005_p3net_gate")
    assert tests.tost(df).iloc[0]["verdict_0.33"] == "equivalent"
    df = _frame("hv", same + 3.0, same, arm="v005_p3net_gate")
    assert tests.tost(df).iloc[0]["verdict_0.33"] == "different"


def test_expected_points_match_the_plans():
    from scripts.analyze_v005 import PLANS

    exp = per_run.expected_points(PLANS)
    assert len(exp) == 19440 + 1080 + 1080 + 4800 + 540
    assert set(exp.seed) == set(spec.SEEDS)
    gp = exp[exp.method.isin(spec.GP)]
    assert set(gp.budget) == {50, 100}
    assert not exp.duplicated(["method", "space", "budget", "seed"]).any()


@pytest.mark.skipif(not all(r.exists() for r in A8), reason="A8 records not present")
def test_anytime_ends_at_the_per_run_value_on_a8_records():
    score = per_run.Scorer()
    checked = {"main": 0, "mf": 0}
    for rec in per_run.records(A8):
        if rec["search_space"] not in spec.SPACES or not rec["history"]:
            continue
        mf = "fidelity_queries" in rec["diagnostics"]
        kind = "mf" if mf else "main"
        if checked[kind] >= 25:
            continue
        values = secondary._anytime_mf(rec, score) if mf else secondary._anytime_main(rec, score)
        final = score(rec["search_space"], per_run.points(rec))
        assert values[-1] == pytest.approx(final), (rec["method"], rec["search_space"], rec["budget"])
        checked[kind] += 1
    assert checked["main"] > 0 and checked["mf"] > 0
