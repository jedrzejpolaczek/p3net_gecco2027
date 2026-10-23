# v005 — test zasobów (A8) na Hetznerze: runbook

Cel: każda metoda v005 × każda przestrzeń × b ∈ {100, 350}, 1 seed (61), w warunkach siatki (6 workerów, wspólny most
JAHS). Wynik: czas i szczytowa pamięć każdej metody + prognoza kosztu całej siatki `configs/pipeline/v005.yaml`
(dziś szkic: 28 560 przebiegów). Na tej podstawie ustalamy skalę siatki przed prerejestracją.

Plan: `implementation/experiments/configs/pipeline/v005-resources.yaml` (476 punktów: 378 główne, 80 MF, 18 Vizier).
Podsumowanie: `scripts/summarize_resources_v005.py`.

## 0. Przed serwerem (lokalnie)

1. Commit i push całej pracy v005. Pipeline nie startuje na niezacommitowanym kodzie, a run root zapisuje commit.
   Do commitu muszą wejść także tablice `implementation/experiments/results/benchmark_tables/` (nieśledzone, a JAHS
   v005 potrzebuje `jahs_param_counts.json`).

## 1. Serwer

2. Hetzner CPX62 (16 vCPU, 32 GB), Ubuntu 24.04, dysk ≥ 80 GB.
   Uwaga: CPX ma vCPU współdzielone — czasy mogą się wahać; jeśli dostępny, CCX43 (dedykowane) daje pewniejsze pomiary.
3. Na serwerze:

```bash
sudo apt-get update && sudo apt-get install -y git curl build-essential
git clone <adres repozytorium> p3net_gecco2027
cd p3net_gecco2027/implementation/experiments
bash scripts/bootstrap_env.sh
```

## 2. Dane (z laptopa, PowerShell, z `implementation\experiments`)

```powershell
scp -r data\cache\*  user@SERWER:~/p3net_gecco2027/implementation/experiments/data/cache/
```

4. Na serwerze sprawdzenie danych (JAHS ładuje się kilka minut):

```bash
uv run python scripts/check_data.py
```

## 3. Uruchomienie

5. Metody główne i MF (6 workerów):

```bash
cd ~/p3net_gecco2027/implementation/experiments
nohup bash scripts/run_pipeline.sh --plan configs/pipeline/v005-resources.yaml \
    --stages resources_main resources_mf --workers 6 > ~/a8_main.log 2>&1 &
tail -f ~/a8_main.log
```

6. Po zakończeniu kroku 5 — Vizier osobno, jeden worker (w v004 ~34 GB przy b = 350):

```bash
nohup bash scripts/run_pipeline.sh --plan configs/pipeline/v005-resources.yaml \
    --stages resources_vizier --workers 1 > ~/a8_vizier.log 2>&1 &
```

7. Postęp w dowolnej chwili:

```bash
uv run python scripts/run_pipeline.py --plan configs/pipeline/v005-resources.yaml --dry-run
```

## 4. Wynik

8. Podsumowanie (na serwerze; `<run root>` = katalog w `results/runs/` z nazwą commitu):

```bash
uv run python scripts/summarize_resources_v005.py results/runs/<run root>
```

9. Skopiuj na laptopa cały run root i plik `resources_summary.md`:

```powershell
scp -r user@SERWER:~/p3net_gecco2027/implementation/experiments/results/runs/<run root>  results\runs\
```

10. Usuń serwer (rozliczenie godzinowe).

## Czego się spodziewać

- Z poziomu 3 (laptop, 8 procesów naraz): ponad 30 min na przebieg przy b = 350 mają NSGANetV2, Vizier, MO-DSA, qNEHVI,
  qParEGO, ASHA; MO-PSA i Vizier miewają ponad 30 min już przy b = 50. Całość A8 może zająć 1–3 dni.
- Pipeline wznawia się po przerwaniu (gotowe punkty zostają) — można spokojnie restartować.
- NB201 liczy się tu z celami v004 (FLOPs zamiast energii), bo tablica energii powstaje na końcu; dla czasu i pamięci
  to bez znaczenia (oba to odczyt z tablicy).
