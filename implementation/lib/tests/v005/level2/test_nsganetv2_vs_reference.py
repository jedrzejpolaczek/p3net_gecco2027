"""Level 2: NSGANetV2 predictors vs the authors' -- checks the report written by
`nsganetv2_vs_reference.py` (about 40 min with the old env). Point
P3NET_NSGANETV2_REPORT to its `report.json`. Criterion: v005-level2-criteria.md,
"NSGANetV2 — kryterium doprecyzowane przed testem"."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

REPORT = os.environ.get("P3NET_NSGANETV2_REPORT")
pytestmark = pytest.mark.skipif(not (REPORT and Path(REPORT).exists()), reason="needs P3NET_NSGANETV2_REPORT")


@pytest.fixture(scope="module")
def rep():
    return json.loads(Path(REPORT).read_text())


@pytest.mark.parametrize("model", ["rbf", "gp"])
def test_deterministic_models_rank_like_the_authors(rep, model):
    assert rep[model]["median_tau_ours_ref"] >= 0.95, rep[model]


def test_cart_as_close_as_two_seeds_of_the_authors(rep):
    assert rep["carts"]["median_tau_ours_ref"] >= rep["carts"]["median_tau_ref_ref"] - 0.02, rep["carts"]


@pytest.mark.parametrize("model", ["rbf", "gp", "carts"])
def test_same_quality(rep, model):
    r = rep[model]
    assert abs(r["median_tau_ours_truth"] - r["median_tau_ref_truth"]) <= 0.02, r


def test_adaptive_switching_picks_the_same_winner(rep):
    assert rep["as_winner_agreement"] >= 0.8, rep
