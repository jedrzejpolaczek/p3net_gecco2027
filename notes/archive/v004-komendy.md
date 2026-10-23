# Dokonczenie v004: punkt i komenda

## 0. Kontrola

```bash
clear; /root/p3s.sh
```

## 1. Etap czasow, maszyna bezczynna

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

## 3. Nowy kod (dopiero teraz)

```bash
cd /root/p3net_gecco2027 && git fetch origin && git reset --hard origin/main && git log --oneline -1
```

## 4. Trzy ramiona gaussowskie, budzety 50 i 100

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

```bash
scp -r root@SERWER:/root/p3net_gecco2027/implementation/experiments/results/runs/b4d25cac .\implementation\experiments\results\runs\
```
