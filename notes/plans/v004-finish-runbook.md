# Dokończenie przebiegu v004 — instrukcja do kopiowania

Stan wyjściowy (2026-09-28): na maszynie działa usługa `p3net.service` liczącą główną siatkę
bez `oss_vizier`, `botorch_qnehvi`, `botorch_qparego` i bez etapów `s5_nas_bench_201` oraz
`s9_timing`. Katalog przebiegu: `results/runs/b4d25cac`. Wszystkie polecenia jako `root`.

Kolejność jest wiążąca — każdy krok dopiero po zakończeniu poprzedniego, bo każdy potrzebuje
całej pamięci maszyny.

## 0. Kontrola codzienna

```bash
/root/p3status.sh
```

Zdrowo: `active`, licznik punktów rośnie, `swap` bliski zeru, `load` ~6, zero błędów.
Alarm: `STALL`, swap powyżej 2 GB, ten sam błąd dziesiątki razy, dysk powyżej 90%.

## 1. Główna siatka (trwa, ~5 dni)

Sprawdzenie, czy skończyła:

```bash
grep -c "All requested stages complete" /root/pipeline.log
```

`1` lub więcej = koniec. Wtedy wyłącz usługę na dobre:

```bash
systemctl disable --now p3net.service; sleep 10; pkill -9 -f query_server.py; pkill -9 -f run_pipeline; free -g | head -3
```

## 2. NAS-Bench-201 — etap s5 (540 punktów, kilka godzin)

Osobno i na dwóch workerach, bo `nats_bench` doczytuje dane architektura po architekturze
i przy ramionach z pełnym FIHC narasta do kilku GB na worker (28 GB przy sześciu workerach
zatrzymało przebieg 2026-09-28).

```bash
cd /root/p3net_gecco2027/implementation/experiments
nohup bash scripts/run_pipeline.sh --workers 2 --skip-checks --stages s5_nas_bench_201 > /root/s5.log 2>&1 &
```

Kontrola: `free -g` — powyżej 25 GB zejdź na jeden worker (`--workers 1`).

## 3. Rescale maszyny

Wyłącz serwer w panelu Hetznera, zmień typ, włącz. Bez powiększania dysku rescale jest
odwracalny. Do kompletu budżetów potrzeba 192 GB; przy 64 GB BoTorch idzie tylko do budżetu 200.

Po ponownym uruchomieniu:

```bash
cd /root/p3net_gecco2027/implementation/experiments && uv run python scripts/check_data.py && free -g | head -3
```

## 4. OSS Vizier

Zrównoleglenie przez osobne katalogi przebiegu: slot `heavy_gp` o przepustowości 1 obowiązuje
tylko wewnątrz jednego katalogu. Każdy shard potrzebuje ~34 GB na ramię plus ~10 GB na własny
mostek JAHS, czyli 44 GB. Na 192 GB mieszczą się cztery.

```bash
cd /root/p3net_gecco2027/implementation/experiments
for i in 0 1 2 3; do
  nohup bash scripts/run_pipeline.sh \
    --run-root /root/p3net_gecco2027/implementation/experiments/results/runs/vizier-$i \
    --shard $i/4 --only-methods oss_vizier --workers 1 --skip-checks \
    --stages s1_headline s6_heldout_seeds s8_fcnet > /root/vizier-$i.log 2>&1 &
done
```

Postęp:

```bash
for i in 0 1 2 3; do echo "shard $i: $(ls results/runs/vizier-$i/raw 2>/dev/null | wc -l) / 361"; done; free -g | head -3
```

Koniec, gdy suma wynosi 1444.

## 5. BoTorch (qNEHVI i qParEGO)

Dopiero po Vizierze. 12 GB na ramię plus 10 GB na mostek, czyli 22 GB na shard — na 192 GB
mieszczą się osiem.

```bash
cd /root/p3net_gecco2027/implementation/experiments
for i in 0 1 2 3 4 5 6 7; do
  nohup bash scripts/run_pipeline.sh \
    --run-root /root/p3net_gecco2027/implementation/experiments/results/runs/botorch-$i \
    --shard $i/8 --only-methods botorch_qnehvi botorch_qparego --workers 1 --skip-checks \
    --stages s1_headline s6_heldout_seeds s8_fcnet > /root/botorch-$i.log 2>&1 &
done
```

Postęp:

```bash
for i in 0 1 2 3 4 5 6 7; do echo "shard $i: $(ls results/runs/botorch-$i/raw 2>/dev/null | wc -l) / 361"; done; free -g | head -3
```

Koniec, gdy suma wynosi 2888.

## 6. Scalenie surowych plików

```bash
cd /root/p3net_gecco2027/implementation/experiments
cp -n results/runs/vizier-*/raw/*.json results/runs/b4d25cac/raw/
cp -n results/runs/botorch-*/raw/*.json results/runs/b4d25cac/raw/
ls results/runs/b4d25cac/raw | wc -l
```

## 7. Etap czasów — na samym końcu, przy bezczynnej maszynie

Wszystkie 53 ramiona, jeden przebieg naraz, we świeżym procesie. To z tego powstaje tabela
kosztów w artykule, więc musi opisywać jedną maszynę i jeden stan bezczynności.

```bash
pgrep -af "run_pipeline|query_server"   # musi nie wypisać nic
cd /root/p3net_gecco2027/implementation/experiments
nohup bash scripts/run_pipeline.sh --stages s9_timing --workers 1 > /root/timing.log 2>&1 &
```

## 8. Sprawdzenie kompletności

```bash
cd /root/p3net_gecco2027/implementation/experiments
uv run python scripts/run_pipeline.py --dry-run --run-root /root/p3net_gecco2027/implementation/experiments/results/runs/b4d25cac
```

Każdy etap musi pokazać `N/N complete`. Dopiero wtedy:

```bash
uv run python scripts/posthoc_metrics.py --raw results/runs/b4d25cac/raw
uv run python scripts/check_data.py
```

## 9. Zabranie wyników na laptop

Z PowerShella na laptopie:

```powershell
scp -r root@SERWER:/root/p3net_gecco2027/implementation/experiments/results/runs/b4d25cac .\implementation\experiments\results\runs\
```

Potem można wyłączyć i usunąć serwer.
