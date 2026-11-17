# v005 — retrening punktów kolanowych (§5.8, K10): instrukcja

Stan na 2026-11-16. Decyzje: P5 a, R9 a (2026-10-31); budżet punktu kolanowego = największy budżet ramienia; retrening
na serwerze GPU (Intel Core i7-11800H, 16 wątków, 32 GB RAM, NVIDIA GeForce RTX 3050 Ti 4 GB, Windows 11; zamiast serwera Hetzner; 2026-11-16, `v005-todo.md`).

## Co jest gotowe

- `scripts/retraining_knees_v005.py` → `results/retraining/knees_v005.json`: 22 punkty NB201 i 27 NAS-HPO-II
  (wszystkie ramiona mają 30 runów). Ramiona z tym samym genotypem dzielą jeden trening: **40 treningów**
  (NB201 16, NAS-HPO-II 24).
- `scripts/retrain_v005.py`: trening protokołem autorów benchmarku (źródła i różnice w docstringu), jeden plik na
  trening w `results/retraining/runs/`, wznawialny; `--report` → `results/retraining/retraining_v005.csv`.
- `scripts/retrain_v005_requirements.txt`: osobne środowisko (torch z CUDA, torchvision, xautodl bez zależności).

Próba 2026-11-16 (CPU, `--smoke 1`): oba protokoły działają, splity pobrane i sprawdzone (25 000 / 25 000), po
1 epoce valid acc NB201 41.5 %, NAS-HPO-II 33.7 %.

**Czas na serwerze GPU (RTX 3050 Ti, 4 GB)**, z pomiaru kroku treningowego każdej z 40 sieci (2026-11-16): same
obliczenia ≈ 12.6 h — NB201 16 × 22–70 min ≈ 10.9 h, NAS-HPO-II 24 × 2–5 min ≈ 1.7 h; z wczytywaniem danych i
zwolnieniem grzejącego się GPU szacunek **13–16 h**. Uwaga (2026-11-16): z 4 nietrwałymi workerami DataLoadera GPU
stało ~70 % czasu (27 s/epokę NB201, realnie ~28 h); od tej daty 8 trwałych workerów (`persistent_workers`), 9.5 s/epokę.

CIFAR-10 nie pobieramy przez torchvision: źródło (cs.toronto.edu) dawało 2026-11-16 kilka KB/s. Plik
`cifar-10-python.tar.gz` (MD5 `c58f30108f718f92721af3b95e74349a`) jest na serwerze Hetzner w `/root/cifar10/`;
torchvision sprawdza MD5 i wtedy niczego nie pobiera.

## Komendy (PowerShell, po kolei)

Środowisko i dane (raz, ~2.5 GB pobierania torch z CUDA):

```powershell
cd C:\Workspace\Uczelnia\p3net_gecco2027\implementation\experiments
uv venv $env:USERPROFILE\venvs\retrain-v005 --python 3.12
$py = "$env:USERPROFILE\venvs\retrain-v005\Scripts\python.exe"
uv pip install --python $py torch torchvision --index-url https://download.pytorch.org/whl/cu126
uv pip install --python $py numpy pyyaml
uv pip install --python $py --no-deps xautodl==1.0.0
& $py -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
New-Item -ItemType Directory -Force $env:USERPROFILE\cifar10 | Out-Null
scp root@37.27.242.136:/root/cifar10/cifar-10-python.tar.gz $env:USERPROFILE\cifar10\
```

Ostatnia komenda `python -c` powinna wypisać `True NVIDIA GeForce RTX 3050 Ti Laptop GPU`.

Próba na GPU (1 epoka na przestrzeń, ~2–3 min; wynik w `results/retraining/runs-smoke/`, nie wchodzi do wyników):

```powershell
& $py scripts/retrain_v005.py --data $env:USERPROFILE\cifar10 --smoke 1
```

Właściwy retrening, w tle (działa dalej po zamknięciu terminala; maszyna podłączona do zasilania — usypianie na
zasilaczu jest u autora wyłączone, `powercfg` 2026-11-16: 0):

```powershell
Start-Process -FilePath $py -ArgumentList "scripts/retrain_v005.py --data $env:USERPROFILE\cifar10" -WindowStyle Hidden -RedirectStandardOutput retrain.log -RedirectStandardError retrain.err
```

Postęp (koniec przy 40):

```powershell
(Get-ChildItem results\retraining\runs\*.json).Count; Get-Content retrain.log -Tail 2
```

Przerwanie (restart, wyłączenie maszyny): ta sama komenda `Start-Process ...` — gotowe treningi są pomijane, przerwany
liczy się od początku. Po zakończeniu:

```powershell
& $py scripts/retrain_v005.py --report
```
