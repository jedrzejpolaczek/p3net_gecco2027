"""Persistent query server for JAHS-Bench-201, run under this
directory's own Python 3.10 environment -- jahs-bench cannot install in
the project's main Python 3.13 environment: it hard-pins
scikit-learn<1.1.0, which has no wheel for Python >=3.11 and can't build
from source since Python 3.12 removed distutils.

Two modes, same protocol -- one JSON object per line in, one out:

  * default: request lines on stdin, responses on stdout, one caller;
  * `--serve PORT_FILE`: a TCP server on 127.0.0.1 (port written to
    PORT_FILE) that every pipeline worker on the machine shares.

The shared mode exists because the surrogate models are far larger in
memory than they look on Windows: one loaded dataset holds about 12 GB
resident (measured on Linux, anon-rss of the killed processes in the
first cloud run). One bridge per worker therefore exhausted a 30 GB
machine at three workers. With one shared bridge, the memory cost is
per DATASET, not per worker, and `--max-datasets` (default 2) bounds how
many stay resident: the least recently used one is dropped when a third
is requested.

Queries are answered by a pool of forked handler processes (`--parallel`).
Forking AFTER the models are loaded is what keeps this cheap: the children
share the parent's pages copy-on-write, so N handlers cost ~12 GB in total,
not N x 12 GB. Serving queries from a single process was measured to be the
throughput limit of the whole pipeline -- with six workers on cheap
JAHS-Bench-201 arms the machine ran at a load average of 1.9 out of 16
cores, because nearly all of those arms' time is benchmark queries.

Where fork is unavailable (Windows), queries are answered in-process under a
lock, which is what a single local run needs anyway.

Loading a Benchmark takes minutes, so a dataset is loaded once and kept
resident -- reloading per query would be impractical even at budget 50.

Request: {"edges": [op_name, ...] (6, search_spaces/_cell_graph.py's
CELL_EDGES order and nas_genotype.py's CELL_OPERATIONS naming),
"learning_rate": float, "weight_decay": float, "activation": str
(nas_genotype.py's lowercase naming), "trivial_augment": bool,
"dataset": str, "epochs": int}

Response: {"valid_acc": float, "size_mb": float, "train_acc": float,
"test_acc": float, "runtime": float} or {"error": str}. `runtime` is the
benchmark's cumulative training time up to `epochs`, in seconds.
"""

from __future__ import annotations

import argparse
import gc
import json
import multiprocessing
import os
import socket
import sys
import threading
import time
from collections import OrderedDict

import jahs_bench
from jahs_bench.lib.core.constants import EDGE_LIST, OP_NAMES, nb201_to_ops

# Our CELL_EDGES (search_spaces/_cell_graph.py), 0-indexed nodes:
#   index 0: (0,1)  index 1: (0,2)  index 2: (1,2)
#   index 3: (0,3)  index 4: (1,3)  index 5: (2,3)
# JAHS-Bench-201's own EDGE_LIST, 1-indexed nodes. Built by matching
# (src, dst) pairs after shifting to 0-indexed, not assumed -- the two
# conventions enumerate the same 6 edges in a different order.
_OUR_CELL_EDGES = ((0, 1), (0, 2), (1, 2), (0, 3), (1, 3), (2, 3))
_JAHS_EDGES_0INDEXED = tuple((s - 1, d - 1) for s, d in EDGE_LIST)
_OUR_EDGE_INDEX_TO_JAHS_OP_NUMBER = {
    our_index: _JAHS_EDGES_0INDEXED.index(pair) + 1
    for our_index, pair in enumerate(_OUR_CELL_EDGES)
}

_ACTIVATION_TO_JAHS = {"relu": "ReLU", "hardswish": "Hardswish", "mish": "Mish"}

#: Loaded datasets, least recently used first (see --max-datasets).
_benchmarks: "OrderedDict[str, jahs_bench.Benchmark]" = OrderedDict()
_max_datasets = 8


def _get_benchmark(dataset: str, data_dir: str) -> jahs_bench.Benchmark:
    if dataset in _benchmarks:
        _benchmarks.move_to_end(dataset)
        return _benchmarks[dataset]
    while len(_benchmarks) >= _max_datasets:
        evicted, benchmark = _benchmarks.popitem(last=False)
        del benchmark
        gc.collect()
        print(f"evicted {evicted} (max-datasets={_max_datasets})", file=sys.stderr, flush=True)
    _benchmarks[dataset] = jahs_bench.Benchmark(task=dataset, download=False, save_dir=data_dir)
    return _benchmarks[dataset]


def _build_config(request: dict) -> dict:
    config = {"Optimizer": "SGD", "N": 5, "W": 16, "Resolution": 1.0}
    for our_index, op_name in enumerate(request["edges"]):
        jahs_op_name = nb201_to_ops[op_name]
        op_number = _OUR_EDGE_INDEX_TO_JAHS_OP_NUMBER[our_index]
        config[f"Op{op_number}"] = OP_NAMES.index(jahs_op_name)
    config["LearningRate"] = request["learning_rate"]
    config["WeightDecay"] = request["weight_decay"]
    config["Activation"] = _ACTIVATION_TO_JAHS[request["activation"]]
    config["TrivialAugment"] = request["trivial_augment"]
    return config


def handle(request: dict, data_dir: str) -> dict:
    benchmark = _get_benchmark(request["dataset"], data_dir)
    config = _build_config(request)
    epochs = request["epochs"]
    result = benchmark(config, nepochs=epochs)
    row = result[epochs]
    return {
        "valid_acc": row["valid-acc"],
        "size_mb": row["size_MB"],
        "train_acc": row["train-acc"],
        "test_acc": row["test-acc"],
        "runtime": row["runtime"],
    }


#: Handler pool (forked after the models are loaded) and what it was forked
#: for; rebuilt when the loaded dataset changes.
_pool = None
_pool_dataset = None
_pool_size = 1
_data_dir = ""
_state_lock = threading.Lock()
#: A pool child answers only from what it inherited: loading a dataset there
#: would cost another 12 GB, so it asks the parent to do it instead.
_NOT_LOADED = "__not_loaded__"


def _pool_handle(request: dict) -> dict:
    if request["dataset"] not in _benchmarks:
        return {"error": _NOT_LOADED}
    try:
        return handle(request, _data_dir)
    except Exception as e:  # noqa: BLE001 -- reported to the caller, not swallowed
        return {"error": f"{type(e).__name__}: {e}"}


def _ensure_pool(dataset: str):
    """A pool of handlers forked with `dataset` already loaded."""
    global _pool, _pool_dataset
    with _state_lock:
        if _pool is not None and _pool_dataset == dataset:
            return _pool
        _get_benchmark(dataset, _data_dir)  # load in the parent, then fork
        if _pool is not None:
            _pool.terminate()
            _pool.join()
        _pool = multiprocessing.get_context("fork").Pool(_pool_size)
        _pool_dataset = dataset
        print(f"forked {_pool_size} handlers for {dataset}", file=sys.stderr, flush=True)
        return _pool


def _shutdown_pool() -> None:
    if _pool is not None:
        _pool.terminate()
        _pool.join()


def _answer(line: str, data_dir: str) -> dict:
    try:
        request = json.loads(line)
        if request.get("command") == "shutdown":
            return {"shutdown": True}
        if _pool_size > 1 and hasattr(os, "fork"):
            response = _ensure_pool(request["dataset"]).apply(_pool_handle, (request,))
            if response.get("error") == _NOT_LOADED:
                # The pool was rebuilt for another dataset in between.
                response = _ensure_pool(request["dataset"]).apply(_pool_handle, (request,))
            return response
        with _state_lock:
            return handle(request, data_dir)
    except Exception as e:  # noqa: BLE001 -- reported to the caller, not swallowed
        return {"error": f"{type(e).__name__}: {e}"}


def serve(data_dir: str, port_file: str, idle_timeout: float) -> None:
    """One shared bridge for every worker on this machine."""
    clients = 0
    last_request = time.time()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 0))
    server.listen(128)
    port = server.getsockname()[1]
    # Written atomically: a worker that sees the file must be able to connect.
    temporary = port_file + ".tmp"
    with open(temporary, "w", encoding="utf-8") as handle_:
        handle_.write(f"{port}\n{os.getpid()}\n")
    os.replace(temporary, port_file)
    print(f"serving on 127.0.0.1:{port} (pid {os.getpid()})", file=sys.stderr, flush=True)

    def client(connection: socket.socket) -> None:
        nonlocal clients, last_request
        with connection, connection.makefile("rw", encoding="utf-8", newline="\n") as stream:
            for line in stream:
                line = line.strip()
                if not line:
                    continue
                response = _answer(line, data_dir)
                last_request = time.time()
                stream.write(json.dumps(response) + "\n")
                stream.flush()
                if response.get("shutdown"):
                    os.remove(port_file)
                    _shutdown_pool()
                    os._exit(0)
        clients -= 1

    def watchdog() -> None:
        while True:
            time.sleep(30.0)
            if clients == 0 and time.time() - last_request > idle_timeout:
                print("idle, exiting", file=sys.stderr, flush=True)
                try:
                    os.remove(port_file)
                except OSError:
                    pass
                _shutdown_pool()
                os._exit(0)

    threading.Thread(target=watchdog, daemon=True).start()
    while True:
        connection, _ = server.accept()
        clients += 1
        threading.Thread(target=client, args=(connection,), daemon=True).start()


def main() -> None:
    parser = argparse.ArgumentParser(description="JAHS-Bench-201 query bridge")
    parser.add_argument("data_dir")
    parser.add_argument("--serve", metavar="PORT_FILE", default=None)
    parser.add_argument("--max-datasets", type=int, default=8)
    parser.add_argument("--idle-timeout", type=float, default=3600.0)
    parser.add_argument(
        "--parallel",
        type=int,
        default=1,
        help="handler processes forked after loading (shared memory copy-on-write)",
    )
    args = parser.parse_args()

    global _max_datasets, _pool_size, _data_dir
    _max_datasets = args.max_datasets
    _pool_size = max(1, args.parallel)
    _data_dir = args.data_dir

    if args.serve:
        serve(args.data_dir, args.serve, args.idle_timeout)
        return

    # Only responses may reach the caller's stdout. jahs_bench and its
    # dependencies print to stdout themselves (observed on Linux: a line of
    # library output between the request and the response, which the caller
    # then tried to parse as JSON), so the library's stdout goes to stderr and
    # responses are written to the real stdout kept here.
    responses = sys.stdout
    sys.stdout = sys.stderr
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        response = _answer(line, args.data_dir)
        responses.write(json.dumps(response) + "\n")
        responses.flush()


if __name__ == "__main__":
    main()
