"""Markers and fixtures for v005 level-1 tests.

Markers
- benchmark_data: needs benchmark files on disk; skipped when absent.
- needs_clarification: written for the interpretation closest to the card,
  pending an answer in QUESTIONS.md (the marker carries the question id).
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from ._support import (
    CountingObjective,
    EventLog,
    additive_cost,
    random_weights,
    trap_f1,
    trap_space,
)

REPO = Path(__file__).resolve().parents[5]


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers", "benchmark_data: needs benchmark data on disk (skipped when absent)"
    )
    config.addinivalue_line(
        "markers", "needs_clarification(qid): test written for one interpretation; see QUESTIONS.md"
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Skip benchmark_data tests unless benchmark files are present: in
    P3NET_BENCHMARK_DATA if set, else in implementation/experiments/data
    (downloads live in data/cache, Q-51). Tests whose own file is missing skip
    themselves."""
    root = os.environ.get("P3NET_BENCHMARK_DATA")
    data_dir = Path(root) if root else REPO / "implementation" / "experiments" / "data"
    has_data = data_dir.is_dir() and any(p.is_file() for p in data_dir.rglob("*"))
    if has_data:
        return
    skip = pytest.mark.skip(reason=f"benchmark data not found in {data_dir}")
    for item in items:
        if "benchmark_data" in item.keywords:
            item.add_marker(skip)


@pytest.fixture
def small_trap():
    """3 blocks x 3 variables, alphabet 3 (n = 9): FIHC pass = 18 evaluations."""
    space = trap_space(n_blocks=3, block_size=3, alphabet=3)
    return space, trap_f1(block_size=3, n=9)


@pytest.fixture
def event_log() -> EventLog:
    return EventLog()


@pytest.fixture
def counting_trap_objective(small_trap):
    space, f1 = small_trap
    return CountingObjective(f1, additive_cost(random_weights([3] * 9, seed=1)))
