"""Extract a compact per-run record from every raw JSON of run root b4d25cac."""
import json, os, sys, pickle
from multiprocessing import Pool

RAW = sys.argv[1]
OUT = sys.argv[2]


def scalarize(d):
    out = {}
    for k, v in d.items():
        if isinstance(v, (int, float, str, bool)) or v is None:
            out[k] = v
        elif isinstance(v, dict) and k == "resources":
            out.update({"res_" + kk: vv for kk, vv in v.items()})
        elif isinstance(v, dict) and k == "surrogate_decisions":
            out["sd_offered"] = v.get("offered")
            out["sd_n_records"] = len(v.get("records") or [])
        elif k == "surrogate_quality_log":
            out["sq_log"] = [(r.get("history_size"), r.get("predicted_delta"), r.get("true_delta")) for r in v]
        elif k in ("chain_depth_log", "level_size_log"):
            out[k] = v
        elif isinstance(v, list):
            out["len_" + k] = len(v)
    return out


def one(name):
    path = os.path.join(RAW, name)
    try:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
    except Exception as e:  # noqa: BLE001
        return {"file": name, "error": repr(e)}
    return {
        "file": name,
        "method": d["method"],
        "space": d["search_space"],
        "budget": d["budget"],
        "seed": d["seed"],
        "evals": d.get("evaluations_used"),
        "obj": [tuple(h["objectives"]) for h in d["history"]],
        "diag": scalarize(d.get("diagnostics", {})),
        "extra_keys": sorted(set(d) - {"method", "search_space", "budget", "seed", "evaluations_used", "history", "diagnostics"}),
    }


if __name__ == "__main__":
    names = sorted(n for n in os.listdir(RAW) if n.endswith(".json"))
    with Pool(15) as pool:
        recs = pool.map(one, names, chunksize=64)
    with open(OUT, "wb") as f:
        pickle.dump(recs, f, protocol=pickle.HIGHEST_PROTOCOL)
    print(len(recs), "records;", sum("error" in r for r in recs), "errors")
