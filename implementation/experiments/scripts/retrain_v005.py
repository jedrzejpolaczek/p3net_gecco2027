"""K10 step 2 (pre-registration §5.8): retrain the knee points of results/retraining/knees_v005.json once,
with each benchmark's public training protocol, on a GPU. Imports nothing from this project, so it runs in
its own small environment (scripts/retrain_v005_requirements.txt) on the rented GPU server.

Protocols (sources read 2026-11-16):
  NAS-Bench-201, `cifar10-valid` (D-X-Y/AutoDL-Projects: configs/nas-benchmark/hyper-opts/200E.config,
    exps/NAS-Bench-201/main.py): network xautodl TinyNetwork, C = 16, N = 5; SGD lr 0.1, momentum 0.9,
    Nesterov, weight decay 5e-4; cosine schedule to 0 over 200 epochs, updated every iteration, no warmup;
    batch 256; cross-entropy; train = the 25 000 "train" indices of cifar-split.txt with random crop 32
    (padding 4) and horizontal flip; validation = the 25 000 "valid" indices without augmentation; test =
    the official 10 000 images. Benchmark seeds 777, 888, 999 -- here one run, seed 777.
  NAS-HPO-Bench-II (yoichii/nashpobench2: config/hydra/acml12.yaml and the files it includes): skeleton
    nasbench201like (3 stages x 5 cells, channels 16/32/64, residual reduction blocks) -- built here with
    the same xautodl TinyNetwork, its ops conv3x3/avgpool/identity/zero = xautodl's nor_conv_3x3,
    avg_pool_3x3, skip_connect, none; SGD with the knee's learning rate and batch size, momentum 0.9,
    Nesterov, weight decay 5e-4; CosineAnnealingLR(T_max = 12) stepped once per epoch; 12 epochs;
    cross-entropy; split config/idx/split.yaml (25 000 / 25 000); train AND validation images augmented
    (random crop 32, padding 4, horizontal flip) as in the authors' datasets/acml.yaml; test not
    augmented. Benchmark seeds 222, 555, 888 -- here one run, seed 222.
  Known differences: one seed instead of the benchmark's three (§5.8 "retrained once"); the NAS-HPO-II
  network comes from xautodl, not the authors' module (same skeleton and op set; layer details such as
  pooling padding counts not checked); different GPU and library versions (recorded in every output).

    python scripts/retrain_v005.py --knees results/retraining/knees_v005.json --data ~/cifar10 \
        --out results/retraining/runs                    # every training job not finished yet
    python scripts/retrain_v005.py ... --smoke 1          # 1 epoch of each space, to a separate folder
    python scripts/retrain_v005.py ... --report          # results/retraining/retraining_v005.csv

One output file per training job (`train_key`; arms with the same genotype share a job), written
atomically; finished jobs are skipped, so the command can simply be run again after an interruption.
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import math
import os
import platform
import time
import urllib.request
from pathlib import Path

SPLITS = {
    "nas_bench_201_v005": "https://raw.githubusercontent.com/D-X-Y/AutoDL-Projects/main/configs/nas-benchmark/"
                          "cifar-split.txt",
    "nas_hpo_bench_ii_v005": "https://raw.githubusercontent.com/yoichii/nashpobench2/main/config/idx/split.yaml",
}
MEAN = [x / 255 for x in (125.3, 123.0, 113.9)]
STD = [x / 255 for x in (63.0, 62.1, 66.7)]


def protocol(space: str, knee: dict) -> dict:
    if space == "nas_bench_201_v005":
        return dict(epochs=200, lr=0.1, batch_size=256, schedule="cosine_per_iteration", seed=777,
                    augment_valid=False)
    return dict(epochs=12, lr=knee["learning_rate"], batch_size=knee["batch_size"], schedule="cosine_per_epoch",
                seed=222, augment_valid=True)


# ------------------------------------------------------------------------------------------------ data

def load_split(space: str, cache: Path) -> tuple[list[int], list[int], str]:
    path = cache / Path(SPLITS[space]).name
    if not path.exists():
        cache.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(SPLITS[space], path)
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if space == "nas_bench_201_v005":
        d = ast.literal_eval(raw.decode())  # {"train": ["int", [...]], "valid": ["int", [...]]}
        train, valid = (list(map(int, d[k][1])) for k in ("train", "valid"))
    else:
        import yaml

        d = yaml.safe_load(raw)
        train, valid = list(map(int, d["train"])), list(map(int, d["valid"]))
    if len(train) != 25000 or len(valid) != 25000 or set(train) & set(valid):
        raise ValueError(f"{path}: unexpected split ({len(train)} / {len(valid)})")
    return train, valid, digest


def loaders(space: str, data: Path, cache: Path, p: dict, workers: int):
    import torch
    import torchvision
    import torchvision.transforms as T

    aug = T.Compose([T.RandomCrop(32, padding=4), T.RandomHorizontalFlip(), T.ToTensor(), T.Normalize(MEAN, STD)])
    plain = T.Compose([T.ToTensor(), T.Normalize(MEAN, STD)])
    train_idx, valid_idx, digest = load_split(space, cache)
    train_set = torchvision.datasets.CIFAR10(str(data), train=True, download=True, transform=aug)
    valid_set = torchvision.datasets.CIFAR10(str(data), train=True, download=True,
                                             transform=aug if p["augment_valid"] else plain)
    test_set = torchvision.datasets.CIFAR10(str(data), train=False, download=True, transform=plain)
    g = torch.Generator().manual_seed(p["seed"])
    kw = dict(num_workers=workers, pin_memory=True)
    bs = p["batch_size"]
    return (torch.utils.data.DataLoader(torch.utils.data.Subset(train_set, train_idx), batch_size=bs,
                                        shuffle=True, generator=g, drop_last=False, **kw),
            torch.utils.data.DataLoader(torch.utils.data.Subset(valid_set, valid_idx), batch_size=bs, **kw),
            torch.utils.data.DataLoader(test_set, batch_size=bs, **kw), digest)


# ------------------------------------------------------------------------------------------------ training

def evaluate(model, loader, device) -> float:
    import torch

    model.eval()
    correct = total = 0
    with torch.no_grad():
        for x, y in loader:
            x, y = x.to(device, non_blocking=True), y.to(device, non_blocking=True)
            out = model(x)
            logits = out[1] if isinstance(out, tuple) else out
            correct += int((logits.argmax(1) == y).sum())
            total += len(y)
    return 100.0 * correct / total


def train_one(space: str, knee: dict, data: Path, cache: Path, epochs: int | None, workers: int) -> dict:
    import numpy as np
    import torch
    from xautodl.models import get_cell_based_tiny_net

    p = protocol(space, knee)
    if epochs is not None:
        p["epochs"] = epochs
    torch.manual_seed(p["seed"])
    np.random.seed(p["seed"])
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    train, valid, test, digest = loaders(space, data, cache, p, workers)
    model = get_cell_based_tiny_net(dict(name="infer.tiny", C=16, N=5, arch_str=knee["arch_str"],
                                         num_classes=10)).to(device)
    params = sum(t.numel() for t in model.parameters())
    opt = torch.optim.SGD(model.parameters(), lr=p["lr"], momentum=0.9, nesterov=True, weight_decay=5e-4)
    loss_fn = torch.nn.CrossEntropyLoss()
    steps = len(train)
    log, started = [], time.time()
    for epoch in range(p["epochs"]):
        model.train()
        for i, (x, y) in enumerate(train):
            if p["schedule"] == "cosine_per_iteration":
                t = (epoch + i / steps) / p["epochs"]
                for group in opt.param_groups:
                    group["lr"] = 0.5 * p["lr"] * (1 + math.cos(math.pi * t))
            x, y = x.to(device, non_blocking=True), y.to(device, non_blocking=True)
            out = model(x)
            loss = loss_fn(out[1] if isinstance(out, tuple) else out, y)
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
        if p["schedule"] == "cosine_per_epoch":
            for group in opt.param_groups:
                group["lr"] = 0.5 * p["lr"] * (1 + math.cos(math.pi * (epoch + 1) / p["epochs"]))
        last = epoch == p["epochs"] - 1
        row = dict(epoch=epoch + 1, train_loss=float(loss.detach()), seconds=round(time.time() - started, 1))
        if last or space == "nas_hpo_bench_ii_v005" or (epoch + 1) % 25 == 0:
            row["valid_acc"] = evaluate(model, valid, device)
        if last:
            row["test_acc"] = evaluate(model, test, device)
        log.append(row)
        print(f"  {knee['train_key']} epoch {epoch + 1}/{p['epochs']} {row}", flush=True)
    import torchvision
    import xautodl

    return dict(train_key=knee["train_key"], search_space=space, arch_str=knee["arch_str"], protocol=p,
                valid_acc=log[-1]["valid_acc"], test_acc=log[-1]["test_acc"], params=params,
                wall_seconds=round(time.time() - started, 1), epochs_log=log, split_sha256=digest,
                device=torch.cuda.get_device_name(0) if device.type == "cuda" else platform.processor(),
                versions=dict(torch=torch.__version__, torchvision=torchvision.__version__,
                              xautodl=getattr(xautodl, "__version__", "?"), python=platform.python_version()))


def write_atomic(path: Path, payload: dict) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    os.replace(tmp, path)


# ------------------------------------------------------------------------------------------------ report

def report(knees: list[dict], out_dir: Path, csv_path: Path) -> None:
    rows = []
    for k in knees:
        path = out_dir / f"{k['train_key']}.json"
        r = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
        bench_valid = 100.0 - k["benchmark_f1"]
        rows.append(dict(method=k["method"], search_space=k["search_space"], budget=k["budget"], seed=k["seed"],
                         train_key=k["train_key"], benchmark_valid_acc=bench_valid,
                         retrained_valid_acc=r and r["valid_acc"], retrained_test_acc=r and r["test_acc"],
                         difference=r and r["valid_acc"] - bench_valid, wall_seconds=r and r["wall_seconds"],
                         device=r and r["device"]))
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    done = sum(r["retrained_valid_acc"] is not None for r in rows)
    print(f"{done}/{len(rows)} arms with a retrained value -> {csv_path}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--knees", type=Path, default=Path("results/retraining/knees_v005.json"))
    ap.add_argument("--data", type=Path, default=Path("~/cifar10").expanduser(), help="CIFAR-10 (downloaded if absent)")
    ap.add_argument("--out", type=Path, default=Path("results/retraining/runs"))
    ap.add_argument("--space", choices=list(SPLITS), default=None, help="only this space")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--smoke", type=int, default=None, metavar="EPOCHS",
                    help="train the first job of each space for EPOCHS epochs into <out>-smoke/ (not results)")
    ap.add_argument("--report", action="store_true", help="only write results/retraining/retraining_v005.csv")
    args = ap.parse_args(argv)

    knees = json.loads(args.knees.read_text(encoding="utf-8"))["knees"]
    if args.report:
        report(knees, args.out, args.out.parent / "retraining_v005.csv")
        return 0
    jobs: dict[str, dict] = {}
    for k in knees:
        if args.space is None or k["search_space"] == args.space:
            jobs.setdefault(k["train_key"], k)
    if args.smoke is not None:
        seen, smoke = set(), {}
        for key, k in jobs.items():
            if k["search_space"] not in seen:
                seen.add(k["search_space"])
                smoke[key] = k
        jobs, out_dir = smoke, args.out.with_name(args.out.name + "-smoke")
    else:
        out_dir = args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    cache = args.out.parent / "splits"
    todo = [k for key, k in jobs.items() if not (out_dir / f"{key}.json").exists()]
    print(f"{len(jobs)} training job(s), {len(jobs) - len(todo)} done, {len(todo)} to run -> {out_dir}")
    for n, k in enumerate(todo, 1):
        print(f"[{n}/{len(todo)}] {k['train_key']} ({k['search_space']})", flush=True)
        result = train_one(k["search_space"], k, args.data, cache, args.smoke, args.workers)
        write_atomic(out_dir / f"{k['train_key']}.json", result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
