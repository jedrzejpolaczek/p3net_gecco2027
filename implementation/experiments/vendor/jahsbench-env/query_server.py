"""Persistent query server for JAHS-Bench-201, run under this
directory's own Python 3.10 environment -- jahs-bench cannot install in
the project's main Python 3.13 environment: it hard-pins
scikit-learn<1.1.0, which has no wheel for Python >=3.11 and can't build
from source since Python 3.12 removed distutils.

Protocol: reads one JSON object per line from stdin, writes one JSON
object per line to stdout, flushing after each. Loads the Benchmark
(and its surrogate models) ONCE per dataset and keeps it resident --
reloading several GB of XGBoost surrogates on every single query would
be impractically slow for even a 50-evaluation budget.

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

import json
import sys

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

_benchmarks: dict[str, jahs_bench.Benchmark] = {}


def _get_benchmark(dataset: str, data_dir: str) -> jahs_bench.Benchmark:
    if dataset not in _benchmarks:
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


def main() -> None:
    data_dir = sys.argv[1]
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
        try:
            request = json.loads(line)
            response = handle(request, data_dir)
        except Exception as e:  # noqa: BLE001 -- reported to the caller, not swallowed
            response = {"error": f"{type(e).__name__}: {e}"}
        responses.write(json.dumps(response) + "\n")
        responses.flush()


if __name__ == "__main__":
    main()
