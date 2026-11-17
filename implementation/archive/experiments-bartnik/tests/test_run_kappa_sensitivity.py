"""Tests for scripts.run_kappa_sensitivity -- the kappa / acceptance-
threshold joint sensitivity sweep (chapters/v003/proposed_optimizer/
main.tex, "Chain depth (kappa)"; chapters/v003/results/main.tex,
"Surrogate error accumulation (kappa and acceptance threshold)").

Exercised against a fake substrate and small, in-test sweep_config
dicts, never a real benchmark or the real, much larger configs/
experiment/kappa_threshold_sweep.yaml grid -- same pattern as
tests/test_run_grid.py and tests/test_run_experiment.py.
"""

import math

import pytest

from reporting.plots import SensitivityPoint
from scripts import run_experiment, run_kappa_sensitivity
from substrates.base import FidelityLevel, Substrate


class FakeSubstrate(Substrate):
    def fidelity_ladder(self):
        return (FidelityLevel(rank=0, config={"epochs": 1}),)

    def query_f1(self, genotype, fidelity):
        return float(sum(1 for v in genotype.values if v != "none"))

    def analytic_f2(self, genotype):
        return float(len(genotype.values))


class CountingClosableFakeSubstrate(FakeSubstrate):
    """Tracks how many instances get built and whether each was closed --
    catches a regression back to "one Substrate per grid cell/seed",
    which would pay JAHS-Bench-201's several-minute subprocess-startup
    cost once per grid cell instead of once for the whole sweep (same
    concern scripts/run_grid.py's own analogous test guards)."""

    instances: list["CountingClosableFakeSubstrate"] = []

    def __init__(self):
        self.closed = False
        CountingClosableFakeSubstrate.instances.append(self)

    def close(self):
        self.closed = True


TINY_SWEEP_CONFIG = {
    "kappa_grid": [1, "auto_1x"],
    "epsilon": 0.01,
    "acceptance_threshold_grid": [0.0, "epsilon"],
    "swept_jointly": True,
}


@pytest.fixture
def fake_search_space_config(monkeypatch):
    monkeypatch.setitem(run_experiment._SUBSTRATE_BUILDERS, "fake", lambda cfg: FakeSubstrate())
    monkeypatch.setattr(
        run_kappa_sensitivity,
        "load_search_space_config",
        lambda name: {"search_space": "nas_genotype", "substrate": "fake"},
    )
    monkeypatch.setattr(
        run_kappa_sensitivity,
        "load_method_config",
        lambda name: {"method": "p3net", "params": {"growth_factor": 2}},
    )


# -- pure grid-resolution helpers -------------------------------------------


def test_resolve_kappa_grid_resolves_symbolic_entries_against_n():
    resolved = run_kappa_sensitivity.resolve_kappa_grid([1, "auto_1x", "auto_2x", None], n=10)
    assert resolved == [1, 4, 8, run_kappa_sensitivity.KAPPA_UNBOUNDED_SENTINEL]


def test_resolve_kappa_grid_floors_n_at_2_like_p3net_itself():
    # P3Net.__post_init__ floors n at 2 before computing its own default
    # (ceil(log2(1)) would be 0, an unusable chain-depth bound) -- mirrored
    # here so a degenerate 1-dimensional search space resolves the same
    # "auto" kappa P3Net itself would pick.
    resolved = run_kappa_sensitivity.resolve_kappa_grid(["auto_1x"], n=1)
    assert resolved == [1]


def test_resolve_kappa_grid_rejects_an_unknown_symbolic_entry():
    with pytest.raises(ValueError):
        run_kappa_sensitivity.resolve_kappa_grid(["not_a_real_symbol"], n=10)


def test_resolve_threshold_grid_resolves_symbolic_entries_against_epsilon():
    resolved = run_kappa_sensitivity.resolve_threshold_grid(
        [0.0, "epsilon", "2*epsilon"], epsilon=0.01
    )
    assert resolved == [0.0, 0.01, 0.02]


def test_resolve_threshold_grid_rejects_an_unknown_symbolic_entry():
    with pytest.raises(ValueError):
        run_kappa_sensitivity.resolve_threshold_grid(["not_a_real_symbol"], epsilon=0.01)


def test_sweep_cells_is_the_full_cross_product_when_swept_jointly():
    cells = run_kappa_sensitivity.sweep_cells(TINY_SWEEP_CONFIG, n=10)
    assert set(cells) == {(1, 0.0), (1, 0.01), (4, 0.0), (4, 0.01)}


def test_sweep_cells_rejects_a_non_joint_sweep_shape_as_not_yet_supported():
    sweep_config = {**TINY_SWEEP_CONFIG, "swept_jointly": False}
    with pytest.raises(NotImplementedError):
        run_kappa_sensitivity.sweep_cells(sweep_config, n=10)


def test_load_sweep_config_reads_the_real_settled_grid_file():
    # configs/experiment/kappa_threshold_sweep.yaml is real, checked-in
    # project data (not a fixture) -- this is a regression guard against
    # that file's shape drifting out from under sweep_cells' expectations.
    sweep_config = run_kappa_sensitivity.load_sweep_config()
    assert sweep_config["kappa_grid"] == [1, "auto_1x", "auto_2x", None]
    assert sweep_config["acceptance_threshold_grid"] == [0.0, "epsilon", "2*epsilon"]
    assert sweep_config["swept_jointly"] is True
    cells = run_kappa_sensitivity.sweep_cells(sweep_config, n=10)
    assert len(cells) == 4 * 3


# -- run_sensitivity_grid, against a fake substrate --------------------------


def test_run_sensitivity_grid_returns_one_sensitivity_point_per_grid_cell(
    fake_search_space_config,
):
    points = run_kappa_sensitivity.run_sensitivity_grid(
        search_space_name="fake_space",
        budget=12,
        seeds=[1, 2],
        sweep_config=TINY_SWEEP_CONFIG,
    )
    assert len(points) == 4
    assert all(isinstance(p, SensitivityPoint) for p in points)
    seen = {(p.kappa, p.acceptance_threshold) for p in points}
    assert seen == {(1, 0.0), (1, 0.01), (4, 0.0), (4, 0.01)}


def test_run_sensitivity_grid_points_carry_finite_hypervolume(fake_search_space_config):
    sweep_config = {**TINY_SWEEP_CONFIG, "acceptance_threshold_grid": [0.0]}
    points = run_kappa_sensitivity.run_sensitivity_grid(
        search_space_name="fake_space",
        budget=20,
        seeds=[1, 2, 3],
        sweep_config=sweep_config,
    )
    assert len(points) == 2
    assert all(math.isfinite(p.hypervolume) for p in points)


def test_run_sensitivity_grid_persists_one_raw_file_per_cell_per_seed(
    tmp_path, monkeypatch, fake_search_space_config
):
    monkeypatch.setattr(run_experiment, "RESULTS_DIR", tmp_path)
    run_kappa_sensitivity.run_sensitivity_grid(
        search_space_name="fake_space",
        budget=12,
        seeds=[1, 2],
        sweep_config=TINY_SWEEP_CONFIG,
    )
    written = list(tmp_path.glob("*.json"))
    assert len(written) == 4 * 2  # 4 cells x 2 seeds


def test_run_sensitivity_grid_no_persist_writes_nothing(
    tmp_path, monkeypatch, fake_search_space_config
):
    monkeypatch.setattr(run_experiment, "RESULTS_DIR", tmp_path)
    sweep_config = {**TINY_SWEEP_CONFIG, "kappa_grid": [1], "acceptance_threshold_grid": [0.0]}
    run_kappa_sensitivity.run_sensitivity_grid(
        search_space_name="fake_space",
        budget=12,
        seeds=[1],
        sweep_config=sweep_config,
        persist=False,
    )
    assert list(tmp_path.glob("*.json")) == []


def test_run_sensitivity_grid_reuses_one_substrate_across_the_whole_grid(monkeypatch):
    CountingClosableFakeSubstrate.instances = []
    monkeypatch.setitem(
        run_experiment._SUBSTRATE_BUILDERS, "fake", lambda cfg: CountingClosableFakeSubstrate()
    )
    monkeypatch.setattr(
        run_kappa_sensitivity,
        "load_search_space_config",
        lambda name: {"search_space": "nas_genotype", "substrate": "fake"},
    )
    monkeypatch.setattr(
        run_kappa_sensitivity,
        "load_method_config",
        lambda name: {"method": "p3net", "params": {"growth_factor": 2}},
    )
    run_kappa_sensitivity.run_sensitivity_grid(
        search_space_name="fake_space",
        budget=12,
        seeds=[1, 2],
        sweep_config=TINY_SWEEP_CONFIG,
    )
    assert len(CountingClosableFakeSubstrate.instances) == 1
    assert CountingClosableFakeSubstrate.instances[0].closed is True


def test_run_sensitivity_grid_does_not_close_a_caller_supplied_substrate(monkeypatch):
    monkeypatch.setattr(
        run_kappa_sensitivity,
        "load_search_space_config",
        lambda name: {"search_space": "nas_genotype", "substrate": "fake"},
    )
    monkeypatch.setattr(
        run_kappa_sensitivity,
        "load_method_config",
        lambda name: {"method": "p3net", "params": {"growth_factor": 2}},
    )
    substrate = CountingClosableFakeSubstrate()
    sweep_config = {**TINY_SWEEP_CONFIG, "kappa_grid": [1], "acceptance_threshold_grid": [0.0]}
    run_kappa_sensitivity.run_sensitivity_grid(
        search_space_name="fake_space",
        budget=10,
        seeds=[1],
        sweep_config=sweep_config,
        substrate=substrate,
    )
    assert substrate.closed is False
