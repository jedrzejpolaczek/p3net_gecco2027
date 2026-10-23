"""Reference side of the NSGA-Net level-2 test: the authors' `search/nsganet.py`
(ianwhale/nsga-net) on pymoo 0.3.0. Runs in vendor/nsganet-env (Python 3.8, numpy < 1.24):

  vendor/nsganet-env/.venv/Scripts/python.exe -I nsganet_reference_runner.py \
      NSGA_NET_REPO PROBLEM BUDGET SEEDS OUT_JSON

Writes the HV of the first BUDGET *distinct* evaluated points per seed (pymoo
re-evaluates genotypes dropped from the population; with #35 they cost no budget).
"""

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _problems import PROBLEMS, hv, objective  # noqa: E402


def main():
    repo, name, budget, n_seeds, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
    sys.path.insert(0, repo)
    from pymop.problem import Problem
    from pymoo.optimize import minimize
    from search import nsganet as engine

    domains = PROBLEMS[name]["domains"]
    f = objective(name)
    res = []
    for seed in range(n_seeds):
        seen = {}

        class P(Problem):
            def __init__(self):
                super().__init__(n_var=len(domains), n_obj=2, n_constr=0, type_var=np.int,
                                 xl=np.zeros(len(domains)), xu=np.array(domains, float) - 1)

            def _evaluate(self, X, out_, *args, **kwargs):
                F = []
                for x in X:
                    key = tuple(int(round(v)) for v in x)
                    F.append(f(key))
                    seen.setdefault(key, F[-1])
                out_["F"] = np.array(F)

        np.random.seed(seed)
        method = engine.nsganet(pop_size=20, n_offsprings=20, eliminate_duplicates=True)
        minimize(P(), method, termination=("n_eval", 6 * budget), seed=seed, verbose=False)
        pts = list(seen.values())[:budget]
        res.append({"seed": seed, "hv": hv(pts, PROBLEMS[name]["ref"]), "distinct": len(seen)})
    Path(out).write_text(json.dumps(res))


if __name__ == "__main__":
    main()
