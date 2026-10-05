# Dokonczenie przebiegu v004

## 0. Codzienna kontrola

```bash
/root/p3status.sh
```

## 1. Koniec glownej siatki

```bash
grep -c "All requested stages complete" /root/pipeline.log
```

## 2. Wylaczenie uslugi

```bash
systemctl disable --now p3net.service; sleep 10; pkill -9 -f query_server.py; pkill -9 -f run_pipeline; free -g | head -3
```

## 3. NAS-Bench-201, dwa workery

```bash
cd /root/p3net_gecco2027/implementation/experiments
PYTHONWARNINGS=ignore nohup bash scripts/run_pipeline.sh --workers 2 --skip-checks --stages s5_nas_bench_201 > /root/s5.log 2>&1 &
```

## 3b. Miejsce na dysku

```bash
df -h / | tail -1; du -sh /root/p3net_gecco2027/implementation/experiments/results/runs/*/logs
```

Ponizej 5 GB wolnego: przytnij logi workerow (`truncate -s 0 <plik>`) albo podepnij wolumen.

## 4. Rescale maszyny, potem sprawdzenie

```bash
cd /root/p3net_gecco2027/implementation/experiments && uv run python scripts/check_data.py && free -g | head -3
```

## 5. OSS Vizier, cztery shardy

```bash
cd /root/p3net_gecco2027/implementation/experiments
for i in 0 1 2 3; do
  PYTHONWARNINGS=ignore nohup bash scripts/run_pipeline.sh \
    --run-root /root/p3net_gecco2027/implementation/experiments/results/runs/vizier-$i \
    --shard $i/4 --only-methods oss_vizier --workers 1 --skip-checks \
    --stages s1_headline s6_heldout_seeds s8_fcnet > /root/vizier-$i.log 2>&1 &
done
```

## 6. Postep Viziera, koniec przy sumie 1444

```bash
for i in 0 1 2 3; do echo "shard $i: $(ls results/runs/vizier-$i/raw 2>/dev/null | wc -l)"; done; free -g | head -3
```

## 7. BoTorch, osiem shardow

```bash
cd /root/p3net_gecco2027/implementation/experiments
for i in 0 1 2 3 4 5 6 7; do
  PYTHONWARNINGS=ignore nohup bash scripts/run_pipeline.sh \
    --run-root /root/p3net_gecco2027/implementation/experiments/results/runs/botorch-$i \
    --shard $i/8 --only-methods botorch_qnehvi botorch_qparego --workers 1 --skip-checks \
    --stages s1_headline s6_heldout_seeds s8_fcnet > /root/botorch-$i.log 2>&1 &
done
```

## 8. Postep BoTorcha, koniec przy sumie 2888

```bash
for i in 0 1 2 3 4 5 6 7; do echo "shard $i: $(ls results/runs/botorch-$i/raw 2>/dev/null | wc -l)"; done; free -g | head -3
```

## 9. Scalenie surowych plikow

```bash
cd /root/p3net_gecco2027/implementation/experiments
cp -n results/runs/vizier-*/raw/*.json results/runs/b4d25cac/raw/
cp -n results/runs/botorch-*/raw/*.json results/runs/b4d25cac/raw/
ls results/runs/b4d25cac/raw | wc -l
```

## 10. Etap czasow, maszyna bezczynna

```bash
pgrep -af "run_pipeline|query_server"
cd /root/p3net_gecco2027/implementation/experiments
PYTHONWARNINGS=ignore nohup bash scripts/run_pipeline.sh --stages s9_timing --workers 1 > /root/timing.log 2>&1 &
```

## 11. Kompletnosc, kazdy etap N/N complete

```bash
cd /root/p3net_gecco2027/implementation/experiments
uv run python scripts/run_pipeline.py --dry-run --run-root /root/p3net_gecco2027/implementation/experiments/results/runs/b4d25cac
```

## 12. Metryki

```bash
cd /root/p3net_gecco2027/implementation/experiments
uv run python scripts/posthoc_metrics.py --raw results/runs/b4d25cac/raw
uv run python scripts/check_data.py
```

## 13. Wyniki na laptop, PowerShell lokalnie

```powershell
scp -r root@SERWER:/root/p3net_gecco2027/implementation/experiments/results/runs/b4d25cac .\implementation\experiments\results\runs\
```
