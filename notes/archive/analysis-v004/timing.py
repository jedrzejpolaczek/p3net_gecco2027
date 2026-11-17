"""Tabulate the sequential timing stage s9 (b4d25cac/timing/raw: budget 350, seed 1) into timing.csv."""
import json
import os
from pathlib import Path

import pandas as pd

RAW = Path(__file__).resolve().parents[2] / "implementation/experiments/results/runs/b4d25cac/timing/raw"
OUT = Path(os.environ["V004_OUT"])
FIELDS = ["wall_seconds", "cpu_seconds", "benchmark_seconds", "optimizer_seconds", "process_peak_rss_mb",
          "bridge_peak_rss_mb", "gpu_peak_memory_mb", "simulated_training_seconds"]

rows = []
for path in sorted(RAW.glob("*.json")):
    d = json.loads(path.read_text(encoding="utf-8"))
    r = d["diagnostics"].get("resources", {})
    rows.append(dict(method=d["method"], space=d["search_space"], **{k: r.get(k) for k in FIELDS}))
t = pd.DataFrame(rows)
t.to_csv(OUT / "timing.csv", index=False)
print(len(t), "timing runs")
p = t.pivot_table(index="method", columns="space", values="wall_seconds").round(0)
p["rss_max_MB"] = t.groupby("method").process_peak_rss_mb.max().round(0)
print(p.sort_values("nas_hpo_bench_ii").to_string())
