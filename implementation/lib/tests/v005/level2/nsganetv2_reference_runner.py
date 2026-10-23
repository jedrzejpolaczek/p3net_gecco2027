"""Reference side of the NSGANetV2 level-2 test: the authors' predictors
(`acc_predictor/{rbf,gp,carts}.py`, mikelzc1990/nsganetv2, Apache-2.0) on the datasets
written by `test_nsganetv2_vs_reference.py`. Runs in vendor/nsganetv2-env:

  vendor/nsganetv2-env/.venv/Scripts/python.exe -I nsganetv2_reference_runner.py REPO DATA_JSON OUT_JSON

For every dataset: test-set predictions of RBF, GP and CART (CART twice, two seeds), and
the Adaptive Switching fold scores (Kendall tau per fold and model) on the given folds.
"""

import json
import sys

import numpy as np
from scipy import stats


def main():
    repo, data_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
    sys.path.insert(0, repo)
    from acc_predictor.factory import get_acc_predictor

    data = json.load(open(data_path))
    out = []
    for d in data:
        Xtr, ytr, Xte = np.array(d["Xtr"], float), np.array(d["ytr"], float), np.array(d["Xte"], float)
        res = {}
        for model in ("rbf", "gp"):
            res[model] = np.ravel(get_acc_predictor(model, Xtr, ytr).predict(Xte)).tolist()
        for k, seed in (("carts", d["seed"]), ("carts2", d["seed"] + 100000)):
            np.random.seed(seed)
            res[k] = np.ravel(get_acc_predictor("carts", Xtr, ytr).predict(Xte)).tolist()
        # AdaptiveSwitching._n_fold_validation on the given permutation
        np.random.seed(d["seed"])
        perm = np.array(d["perm"])
        tau = np.full((10, 3), np.nan)
        for i, tst in enumerate(np.array_split(perm, 10)):
            trn = np.setdiff1d(perm, tst, assume_unique=True)
            for j, model in enumerate(("rbf", "gp", "carts")):
                p = get_acc_predictor(model, Xtr[trn], ytr[trn]).predict(Xtr[tst])
                tau[i, j] = stats.kendalltau(np.ravel(p), ytr[tst])[0]
        res["as_tau"] = tau.tolist()
        out.append(res)
    json.dump(out, open(out_path, "w"))


if __name__ == "__main__":
    main()
