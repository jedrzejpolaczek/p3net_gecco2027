"""Usage (from implementation/experiments, P3NET_BENCHMARK_DATA set):
    uv run python scripts/check_p3net_rng_offset_v005.py nas_hpo_bench_ii_v005 fcnet_naval_propulsion_v005

Hypothesis: P3Net differs from canonical P3 at b where no mixing step happens only because P3Net's
constructor draws rng.getrandbits(64) for the surrogate. Check: canonical P3 with that one draw consumed
first must reproduce the recorded P3Net history exactly; plain canonical P3 must reproduce its own record."""
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, ".")
from methods import v005_adapter  # noqa: E402
from scripts import run_experiment as rx  # noqa: E402

ROOT = Path("results/runs/c674c91e/raw")
REAL_RANDOM = random.Random


class Advanced(REAL_RANDOM):
    def __init__(self, seed):
        super().__init__(seed)
        self.getrandbits(64)


def history(method, space, budget, seed, advance):
    v005_adapter.random.Random = Advanced if advance else REAL_RANDOM
    try:
        res = rx.run_single(rx.load_method_config(method), rx.load_search_space_config(space), budget, seed)
    finally:
        v005_adapter.random.Random = REAL_RANDOM
    return [list(o.genotype.values) for o in res.state.history]


def recorded(method, space, budget, seed):
    d = json.loads((ROOT / f"{method}__{space}__budget{budget}__seed{seed}.json").read_text(encoding="utf-8"))
    return [h["genotype"] for h in d["history"]]


for space in sys.argv[1:]:
    for seed in (62, 63, 64):
        b = 50
        canon_plain = history("v005_p3_canonical", space, b, seed, advance=False)
        canon_adv = history("v005_p3_canonical", space, b, seed, advance=True)
        p3net = recorded("v005_p3net", space, b, seed)
        own = recorded("v005_p3_canonical", space, b, seed)
        norm = lambda h: [[float(x) if isinstance(x, (int, float)) else x for x in g] for g in h]  # noqa: E731
        print(f"{space} seed {seed}: canonical reproduces its record: {norm(canon_plain) == norm(own)}; "
              f"canonical with one draw consumed == P3Net record: {norm(canon_adv) == norm(p3net)}; "
              f"plain canonical == P3Net: {norm(canon_plain) == norm(p3net)}")
