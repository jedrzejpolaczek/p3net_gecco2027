# Dokonczenie przebiegu v004 (bez rescale maszyny)

Glowna siatka gotowa 2026-10-05: 51 909 punktow w `results/runs/b4d25cac`, bez `oss_vizier`,
`botorch_qnehvi` i `botorch_qparego`. Maszyna zostaje 30 GB, wiec te trzy ramiona ida tylko do
budzetow 50 i 100; kolumny 200 i 350 opisuje Limitations wraz z pomiarami.

Kolejnosc jest wiazaca. Etap czasow musi byc PIERWSZY: dopisuje do `b4d25cac`, a ten katalog
przyjmuje wylacznie ten commit i czyste repozytorium. Dopiero po nim wolno zrobic `git pull`.

## 0. Kontrola

```bash
clear; /root/p3s.sh
```

## 1. Etap czasow, maszyna bezczynna

128 punktow (32 ramiona x 4 przestrzenie, budzet 350, jedno ziarno), kazdy w swiezym procesie,
pojedynczo. Okolo doby. Cztery punkty Viziera padna na pamieci i to jest oczekiwane.

```bash
pgrep -af "run_pipeline|query_server"
cd /root/p3net_gecco2027/implementation/experiments
PYTHONWARNINGS=ignore nohup bash scripts/run_pipeline.sh --stages s9_timing --workers 1 > /root/timing.log 2>&1 &
```

## 2. Sprawdzenie etapu czasow

```bash
ls /root/p3net_gecco2027/implementation/experiments/results/runs/b4d25cac/timing/raw | wc -l
grep -c "ALL REQUESTED STAGES COMPLETE" /root/timing.log
```

124 z 128 punktow to wynik poprawny (brakuje czterech Viziera).

## 3. Nowy kod (dopiero teraz)

```bash
cd /root/p3net_gecco2027 && git fetch origin && git reset --hard origin/main && git log --oneline -1
```

## 4. Trzy ramiona gaussowskie, budzety 50 i 100

Osobny plan (`v004-gp-small.yaml`) i osobny katalog przebiegu. Dwa workery, bo przy budzecie 100
jeden przebieg Viziera siega kilkunastu GB.

```bash
cd /root/p3net_gecco2027/implementation/experiments
PYTHONWARNINGS=ignore nohup bash scripts/run_pipeline.sh \
  --plan configs/pipeline/v004-gp-small.yaml \
  --run-root /root/p3net_gecco2027/implementation/experiments/results/runs/gp-small \
  --only-methods oss_vizier botorch_qnehvi botorch_qparego \
  --workers 2 --skip-checks \
  --stages s1_headline s6_heldout_seeds s8_fcnet > /root/gp.log 2>&1 &
```

## 5. Postep ramion gaussowskich

```bash
ls /root/p3net_gecco2027/implementation/experiments/results/runs/gp-small/raw 2>/dev/null | wc -l
free -g | head -2; df -h / | tail -1
```

Powyzej 25 GB zuzycia pamieci: ubij i wystartuj to samo z `--workers 1`.

## 6. Scalenie surowych plikow

```bash
cd /root/p3net_gecco2027/implementation/experiments
cp -n results/runs/gp-small/raw/*.json results/runs/b4d25cac/raw/
ls results/runs/b4d25cac/raw | wc -l
```

## 7. Metryki po przebiegu

```bash
cd /root/p3net_gecco2027/implementation/experiments
uv run python scripts/posthoc_metrics.py --raw results/runs/b4d25cac/raw
uv run python scripts/check_data.py
```

## 8. Wyniki na laptop (PowerShell lokalnie)

```powershell
scp -r root@SERWER:/root/p3net_gecco2027/implementation/experiments/results/runs/b4d25cac .\implementation\experiments\results\runs\
```

Potem mozna wylaczyc i usunac serwer.
