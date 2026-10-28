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
scp -r data\cache\*  user@138.199.235.68:~/p3net_gecco2027/implementation/experiments/data/cache/
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

7. Postęp w dowolnej chwili, dla wszystkich trzech faz (A8, Vizier, posthoc): co jest gotowe, co liczy się teraz i jak długo,
   ETA wg czasów tych samych metod, błędy, RAM, dysk, ostatnie linie logów:

```bash
cd ~/p3net_gecco2027/implementation/experiments
bash scripts/a8_status.sh                  # raz
watch -n 300 bash scripts/a8_status.sh     # odświeżanie co 5 min (Ctrl+C kończy podgląd, nie obliczenia)
```

## 4. Wynik

8. Podsumowanie z obu run rootów: `ec1ba9cb` to główny przebieg, `e6734ccd` to powtórka qParEGO i Vizier (po commicie
   `e6734ccd9` pipeline założył nowy run root). Pierwszy run root ma pierwszeństwo, drugi tylko uzupełnia braki:

   Po OOM Viziera przy b=350 na JAHS dochodzi trzeci run root, z reszty Viziera
   (`configs/pipeline/v005-resources-vizier-rest.yaml`; nazwa = commit, z którym go uruchomisz):

```bash
uv run python scripts/summarize_resources_v005.py results/runs/ec1ba9cb results/runs/e6734ccd results/runs/<trzeci>
```

   Na serwerze w trakcie A8 nie rób `git pull` ani commitów: nowy commit oznacza nowy run root.

9. Skopiuj na laptopa oba run rooty (`resources_summary.md` jest w `ec1ba9cb`):

```powershell
scp -r root@138.199.235.68:~/p3net_gecco2027/implementation/experiments/results/runs/ec1ba9cb  implementation\experiments\results\runs\
scp -r root@138.199.235.68:~/p3net_gecco2027/implementation/experiments/results/runs/e6734ccd  implementation\experiments\results\runs\
```

10. Posthoc JAHS na danych v004 (A9). Uruchamiasz dopiero po kroku 6, bo posthoc ładuje własny most JAHS, około 12 GB
    na zbiór, i obok A8 by się nie zmieścił. Surowe pliki v004 są w repozytorium, więc nic nie trzeba kopiować.
    Skrypt można wznawiać po przerwaniu; gotowe pliki są pomijane. Spodziewaj się kilku godzin.

```bash
cd ~/p3net_gecco2027/implementation/experiments
nohup bash -c 'for r in b4d25cac gp-small; do
  uv run python scripts/posthoc_metrics.py --raw results/runs/$r/raw --pattern "*__jahs_bench_201*"; done' \
    > ~/posthoc_jahs.log 2>&1 &
grep "file(s) written" ~/posthoc_jahs.log   # na końcu dwie linie: 28080 (b4d25cac) i 1080 (gp-small)
```

    Kopia na laptopa:

```powershell
scp -r user@138.199.235.68:~/p3net_gecco2027/implementation/experiments/results/runs/b4d25cac/posthoc  results\runs\b4d25cac\
scp -r user@138.199.235.68:~/p3net_gecco2027/implementation/experiments/results/runs/gp-small/posthoc  results\runs\gp-small\
```

11. Usuń serwer (rozliczenie godzinowe).

## Czego się spodziewać

- Z poziomu 3 (laptop, 8 procesów naraz): ponad 30 min na przebieg przy b = 350 mają NSGANetV2, Vizier, MO-DSA, qNEHVI,
  qParEGO, ASHA; MO-PSA i Vizier miewają ponad 30 min już przy b = 50. Całość A8 może zająć 1–3 dni.
- Pipeline wznawia się po przerwaniu (gotowe punkty zostają) — można spokojnie restartować.
- NB201 liczy się tu z celami v004 (FLOPs zamiast energii), bo tablica energii powstaje na końcu; dla czasu i pamięci
  to bez znaczenia (oba to odczyt z tablicy).
