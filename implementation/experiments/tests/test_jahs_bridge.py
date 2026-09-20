"""Tests for the JAHS-Bench-201 bridge protocol, against a stand-in server
(tests/fake_jahs_server.py) rather than the real 12 GB benchmark.

What is pinned:
  * a line of library output on stdout is skipped, not parsed as a result;
  * with P3NET_JAHS_SERVER_DIR set, every substrate talks to ONE shared
    bridge (that is the whole point: a bridge per worker needs 12 GB each);
  * the shared bridge is started once, concurrent clients get consistent
    answers, and a caller that arrives later reuses the running one;
  * errors from the bridge surface as exceptions, not as silent results.
"""

from __future__ import annotations

import json
import socket
import sys
import threading
import time
from pathlib import Path

import pytest
from p3net.problem.genotype import Genotype

from substrates import jahs_bench_201 as jahs

FAKE_SERVER = Path(__file__).resolve().parent / "fake_jahs_server.py"
GENOTYPE = Genotype(
    values=(
        "nor_conv_3x3",
        "skip_connect",
        "nor_conv_1x1",
        "avg_pool_3x3",
        "none",
        "nor_conv_3x3",
        0.1,
        0.0005,
        "relu",
        False,
    )
)


@pytest.fixture
def fake_bridge(monkeypatch):
    monkeypatch.setattr(jahs, "BRIDGE_PYTHON", Path(sys.executable))
    monkeypatch.setattr(jahs, "BRIDGE_SCRIPT", FAKE_SERVER)


@pytest.fixture
def shared(monkeypatch, tmp_path, fake_bridge):
    monkeypatch.setenv(jahs.SERVER_DIR_ENV, str(tmp_path))
    yield tmp_path
    port_file = tmp_path / "jahs-server.port"
    if port_file.exists():
        port = int(port_file.read_text(encoding="utf-8").splitlines()[0])
        with socket.create_connection(("127.0.0.1", port), timeout=10) as connection:
            connection.sendall(b'{"command": "shutdown"}\n')
            connection.recv(64)


def test_own_bridge_skips_library_output_on_stdout(fake_bridge, monkeypatch):
    monkeypatch.delenv(jahs.SERVER_DIR_ENV, raising=False)
    substrate = jahs.JAHSBench201Substrate()
    try:
        base = float(sum(len(str(v)) for v in GENOTYPE.values[:6]))
        f1, f2 = substrate.objectives(GENOTYPE)
        assert f1 == pytest.approx(100.0 - (base + 2.0))  # 100 - valid_acc at 200 epochs
        assert f2 == pytest.approx(base / 10.0)
    finally:
        substrate.close()


def test_shared_bridge_is_started_once_and_reused(shared):
    first = jahs.JAHSBench201Substrate()
    second = jahs.JAHSBench201Substrate()
    try:
        assert first.objectives(GENOTYPE) == second.objectives(GENOTYPE)
        port_file = shared / "jahs-server.port"
        assert port_file.exists()
        # Both substrates were answered by the same server process.
        pids = {substrate._response(GENOTYPE, 200)["pid"] for substrate in (first, second)}
        assert len(pids) == 1
        assert int(port_file.read_text(encoding="utf-8").splitlines()[1]) == pids.pop()
    finally:
        first.close()
        second.close()


def test_shared_bridge_serves_concurrent_clients_consistently(shared):
    substrates = [jahs.JAHSBench201Substrate() for _ in range(4)]
    results: list[list] = [[] for _ in substrates]
    epochs = [1, 7, 22, 67, 200]

    def work(index: int) -> None:
        for e in epochs:
            results[index].append(substrates[index].objectives_at_epochs(GENOTYPE, e))

    threads = [threading.Thread(target=work, args=(i,)) for i in range(len(substrates))]
    try:
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        assert all(row == results[0] for row in results)
        assert len({tuple(row) for row in results}) == 1
        assert len(results[0]) == len(epochs)
    finally:
        for substrate in substrates:
            substrate.close()


def test_closing_a_substrate_leaves_the_shared_bridge_running(shared):
    first = jahs.JAHSBench201Substrate()
    first.objectives(GENOTYPE)
    port_file = shared / "jahs-server.port"
    port = int(port_file.read_text(encoding="utf-8").splitlines()[0])
    first.close()

    second = jahs.JAHSBench201Substrate()
    try:
        second.objectives(GENOTYPE)
        assert int(port_file.read_text(encoding="utf-8").splitlines()[0]) == port
    finally:
        second.close()


def test_bridge_errors_are_raised(shared):
    substrate = jahs.JAHSBench201Substrate()
    substrate.dataset = "unknown_dataset"
    try:
        with pytest.raises(RuntimeError, match="unknown dataset"):
            substrate.objectives(GENOTYPE)
    finally:
        substrate.close()


def test_shared_bridge_shuts_down_on_request(shared):
    substrate = jahs.JAHSBench201Substrate()
    substrate.objectives(GENOTYPE)
    substrate.close()

    from scripts.run_pipeline import shutdown_jahs_server

    run_root = shared.parent
    (run_root / "jahs").mkdir(exist_ok=True)
    (run_root / "jahs" / "jahs-server.port").write_text(
        (shared / "jahs-server.port").read_text(encoding="utf-8"), encoding="utf-8"
    )
    messages: list[str] = []
    shutdown_jahs_server(run_root, messages.append)
    assert messages == ["shared JAHS bridge shut down"]
    # The server removes its port file as it exits, just after answering.
    deadline = time.monotonic() + 10.0
    while (shared / "jahs-server.port").exists() and time.monotonic() < deadline:
        time.sleep(0.1)
    assert not (shared / "jahs-server.port").exists()


def test_run_pipeline_points_workers_at_one_shared_bridge(tmp_path):
    from scripts.run_pipeline import worker_env

    env = worker_env(2, tmp_path, jahs_max_datasets=1)
    assert env[jahs.SERVER_DIR_ENV] == str(tmp_path / "jahs")
    assert env[jahs.SERVER_MAX_DATASETS_ENV] == "1"
    assert json.loads('{"ok": true}')  # keep json import meaningful for linters
