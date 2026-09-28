# Dokonczenie przebiegu v004

Kolejnosc wiazaca - kazdy krok po zakonczeniu poprzedniego, bo kazdy potrzebuje calej pamieci
maszyny. Wszystko jako `root`. Katalog glownego przebiegu: `results/runs/b4d25cac`.

## 0. Codzienna kontrola

```bash
/root/p3status.sh
```

Zdrowo: `active`, licznik punktow rosnie, swap bliski zeru, load ~6, zero bledow.
Alarm: `STALL`, swap powyzej 2 GB, ten sam blad dziesiatki razy, dysk powyzej 90%.

## 1. Koniec glownej siatki

```bash
grep -c "All requested stages complete" /root/pipeline.log
```

## 2. Wylaczenie uslugi po zakonczeniu

```bash
systemctl disable --now p3net.service; sleep 10; pkill -9 -f query_server.py; pkill -9 -f run_pipeline; free -g | head -3
```

## 3. NAS-Bench-201, dwa workery

`nats_bench` doczytuje dane architektura po architekturze, wiec przy ramionach z pelnym FIHC
narasta do kilku GB na worker; przy szesciu zatrzymalo przebieg 2026-09-28. Powyzej 25 GB
zuzycia zejdz na `--workers 1`.

```bash
cd /root/p3net_gecco2027/implementation/experiments
nohup bash scripts/run_pipeline.sh --workers 2 --skip-checks --stages s5_nas_bench_201 > /root/s5.log 2>&1 &
```

## 4. Rescale maszyny (panel Hetznera), potem sprawdzenie

Bez powiekszania dysku rescale jest odwracalny. Komplet budzetow wymaga 192 GB; przy 64 GB
BoTorch idzie tylko do budzetu 200.

```bash
cd /root/p3net_gecco2027/implementation/experiments && uv run python scripts/check_data.py && free -g | head -3
```

## 5. OSS Vizier, cztery shardy

Slot `heavy_gp` o przepustowosci 1 obowiazuje tylko wewnatrz jednego katalogu przebiegu, wiec
zrownoleglenie robimy osobnymi katalogami. Shard potrzebuje ~34 GB na ramie plus ~10 GB na
wlasny mostek JAHS.

```bash
cd /root/p3net_gecco2027/implementation/experiments
for i in 0 1 2 3; do
  nohup bash scripts/run_pipeline.sh \
    --run-root /root/p3net_gecco2027/implementation/experiments/results/runs/vizier-$i \
    --shard $i/4 --only-methods oss_vizier --workers 1 --skip-checks \
    --stages s1_headline s6_heldout_seeds s8_fcnet > /root/vizier-$i.log 2>&1 &
done
```

## 6. Postep Viziera (koniec przy sumie 1444)

```bash
for i in 0 1 2 3; do echo "shard $i: $(ls results/runs/vizier-$i/raw 2>/dev/null | wc -l)"; done; free -g | head -3
```

## 7. BoTorch, osiem shardow

Dopiero po Vizierze. 12 GB na ramie plus 10 GB na mostek, czyli 22 GB na shard.

```bash
cd /root/p3net_gecco2027/implementation/experiments
for i in 0 1 2 3 4 5 6 7; do
  nohup bash scripts/run_pipeline.sh \
    --run-root /root/p3net_gecco2027/implementation/experiments/results/runs/botorch-$i \
    --shard $i/8 --only-methods botorch_qnehvi botorch_qparego --workers 1 --skip-checks \
    --stages s1_headline s6_heldout_seeds s8_fcnet > /root/botorch-$i.log 2>&1 &
done
```

## 8. Postep BoTorcha (koniec przy sumie 2888)

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

## 10. Etap czasow - maszyna musi byc bezczynna

Pierwsza komenda musi nie wypisac nic. Z tego etapu powstaje tabela kosztow w artykule, wiec
musi opisywac jedna maszyne i jeden stan bezczynnosci.

```bash
pgrep -af "run_pipeline|query_server"
cd /root/p3net_gecco2027/implementation/experiments
nohup bash scripts/run_pipeline.sh --stages s9_timing --workers 1 > /root/timing.log 2>&1 &
```

## 11. Kompletnosc (kazdy etap musi pokazac N/N complete)

```bash
cd /root/p3net_gecco2027/implementation/experiments
uv run python scripts/run_pipeline.py --dry-run --run-root /root/p3net_gecco2027/implementation/experiments/results/runs/b4d25cac
```

## 12. Metryki po przebiegu

```bash
cd /root/p3net_gecco2027/implementation/experiments
uv run python scripts/posthoc_metrics.py --raw results/runs/b4d25cac/raw
uv run python scripts/check_data.py
```

## 13. Zabranie wynikow na laptop (PowerShell lokalnie)

```powershell
scp -r root@SERWER:/root/p3net_gecco2027/implementation/experiments/results/runs/b4d25cac .\implementation\experiments\results\runs\
```
