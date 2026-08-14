"""Tests for scripts.run_grid -- grid enumeration and skip-cached
dispatch. (Gap in the original task list -- adding it.)"""

import json

from scripts import run_experiment, run_grid
from substrates.base import FidelityLevel, Substrate


class FakeSubstrate(Substrate):
    def fidelity_ladder(self):
        return (FidelityLevel(rank=0, config={"epochs": 1}),)

    def query_f1(self, genotype, fidelity):
        return float(sum(1 for v in genotype.values if v != "none"))

    def analytic_f2(self, genotype):
        return float(len(genotype.values))


def test_enumerate_grid_is_the_full_cross_product(monkeypatch):
    monkeypatch.setattr(
        run_grid, "load_budgets_config", lambda: {"budget_tiers": [10, 20], "seeds": [1, 2, 3]}
    )
    points = run_grid.enumerate_grid(
        methods=["p3net", "random_search"], search_spaces=["jahs_bench_201"]
    )
    assert len(points) == 2 * 1 * 2 * 3
    assert all(p.search_space == "jahs_bench_201" for p in points)


def test_enumerate_grid_defaults_to_every_config_file_on_disk():
    points = run_grid.enumerate_grid()
    method_names = {p.method for p in points}
    space_names = {p.search_space for p in points}
    assert "p3net" in method_names
    assert "random_search" in method_names
    assert space_names == {"jahs_bench_201", "nas_hpo_bench_ii"}


def test_run_grid_writes_one_file_per_point_and_skips_on_rerun(tmp_path, monkeypatch):
    monkeypatch.setitem(run_experiment._SUBSTRATE_BUILDERS, "fake", lambda cfg: FakeSubstrate())
    monkeypatch.setattr(run_experiment, "RESULTS_DIR", tmp_path)
    monkeypatch.setattr(
        run_grid,
        "load_search_space_config",
        lambda name: {"search_space": "nas_genotype", "substrate": "fake"},
    )
    monkeypatch.setattr(
        run_grid, "load_method_config", lambda name: {"method": "random_search", "params": {}}
    )

    points = [
        run_grid.GridPoint(method="random_search", search_space="fake_space", budget=5, seed=seed)
        for seed in (1, 2)
    ]
    written, skipped = run_grid.run_grid(points)
    assert len(written) == 2
    assert len(skipped) == 0
    for path in written:
        payload = json.loads(path.read_text())
        assert payload["evaluations_used"] == 5

    written_again, skipped_again = run_grid.run_grid(points)
    assert len(written_again) == 0
    assert len(skipped_again) == 2


def test_run_grid_does_not_skip_when_told_not_to(tmp_path, monkeypatch):
    monkeypatch.setitem(run_experiment._SUBSTRATE_BUILDERS, "fake", lambda cfg: FakeSubstrate())
    monkeypatch.setattr(run_experiment, "RESULTS_DIR", tmp_path)
    monkeypatch.setattr(
        run_grid,
        "load_search_space_config",
        lambda name: {"search_space": "nas_genotype", "substrate": "fake"},
    )
    monkeypatch.setattr(
        run_grid, "load_method_config", lambda name: {"method": "random_search", "params": {}}
    )

    points = [
        run_grid.GridPoint(method="random_search", search_space="fake_space", budget=5, seed=1)
    ]
    run_grid.run_grid(points)
    written_again, skipped_again = run_grid.run_grid(points, skip_cached=False)
    assert len(written_again) == 1
    assert len(skipped_again) == 0
