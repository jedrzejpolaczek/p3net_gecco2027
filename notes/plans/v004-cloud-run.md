# Uruchomienie fazy 4 w chmurze (albo lokalnie)

Instrukcja krok po kroku dla przebiegu `configs/pipeline/v004.yaml` (56 348 punktów).
Wszystko działa tak samo lokalnie na Windows i na maszynie linuksowej; różni się tylko
skrypt startowy (`run_pipeline.ps1` kontra `run_pipeline.sh`).

## 1. Ile to jest pracy

Z pomiarów pierwszego przebiegu: **ok. 2900 godzin pracy jednego workera**.
Jeden worker zajmuje 2 wątki, więc maszyna z N vCPU liczy około N/2 punktów naraz.

| Maszyna | Workerów | Czas całości |
|---|---|---|
| 8 vCPU / 32 GB | 4 | ok. 30 dni |
| 16 vCPU / 64 GB | 8 | ok. 15 dni |
| 2 × 16 vCPU / 64 GB | 2 × 8 | ok. 8 dni |
| 4 × 16 vCPU / 64 GB | 4 × 8 | ok. 4 dni |

**Koszt liczy się jako: 2900 / (liczba workerów na maszynę) × stawka godzinowa maszyny.**
Przy 16 vCPU praca zajmie ok. 360 godzin maszynowych niezależnie od tego, na ile maszyn to
podzielisz, więc koszt zależy tylko od ceny za godzinę i od tego, czy vCPU są dedykowane.

Pamięć: **minimum 4 GB na workera**, bo jedno ramię (OSS Vizier) potrafi zająć 13 GB, a most
JAHS-Bench-201 przy starcie 17,5 GB (ładuje się tylko jeden naraz, pilnuje tego blokada).
Przy 8 workerach planuj 64 GB RAM. Dysk: 20 GB na dane benchmarków plus ok. 10 GB na wyniki.

## 2. Jaką maszynę

**Rekomendacja: Hetzner Cloud, linia CCX (dedykowane vCPU), lokalizacja w UE.**

- **CCX33** — 8 vCPU, 32 GB RAM, 240 GB dysku;
- **CCX43** — 16 vCPU, 64 GB RAM, 360 GB dysku (najlepszy stosunek do naszego profilu).

Dlaczego ta linia, a nie tańsza:
- **vCPU są dedykowane.** Nasze obliczenia to tygodnie 100% CPU. Na współdzielonych vCPU
  (Hetzner CPX, Contabo, większość tanich VPS-ów) dostawca wprost pisze, że to profil „low to
  medium CPU usage”: wydajność spada w sposób nieprzewidywalny, a **pomiary czasu z etapu
  `s9_timing` przestają być wiarygodne** — a to jest osobny wynik w artykule (wymiar praktyczny).
- **Rozliczenie godzinowe z miesięcznym limitem.** Maszynę kasujesz po kilku dniach i płacisz
  tylko za godziny.
- Transfer w cenie (dziesiątki TB), a my wyślemy ok. 20 GB danych.

Alternatywy, jeśli liczy się wyłącznie cena:
- **Contabo** (np. 16 vCPU / 64 GB) bywa kilkukrotnie tańszy w skali miesiąca, ale vCPU są
  współdzielone i **nie ma rozliczenia godzinowego** — cennik jest na umowę 24-miesięczną.
  Rozsądne tylko jako maszyna liczące etapy siatki, nigdy dla `s9_timing`.
- **Instancje spot** (GCP Spot, AWS Spot) bywają najtańsze i nasz pipeline przeżywa ubicie
  procesu (wznawia się z ostatniego ukończonego punktu), ale wymagają skryptu, który po
  odtworzeniu maszyny ponownie wgra dane.
- **Klaster uczelniany (SLURM)**, jeśli masz dostęp: dla tego profilu zwykle darmowy i mocniejszy
  niż każda z powyższych opcji. Jedno zadanie na etap, `--workers` równe przydzielonym rdzeniom.

Cen nie podaję z pamięci, bo zmieniają się co kwartał: sprawdź je w panelu Hetznera przy
zakładaniu serwera i pomnóż przez liczbę godzin z tabeli w punkcie 1.

## 3. Przygotowanie maszyny

Zakładam Ubuntu 24.04, użytkownik z sudo, dysk co najmniej 60 GB.

```bash
sudo apt-get update && sudo apt-get install -y git curl build-essential
git clone <adres repozytorium> p3net_gecco2027
cd p3net_gecco2027/implementation/experiments
bash scripts/bootstrap_env.sh
```

Skrypt instaluje `uv`, buduje główne środowisko z `uv.lock` (na Linuksie wariant PyTorcha bez
CUDA, czyli bez 3 GB zbędnych bibliotek) oraz osobne środowisko Python 3.10 dla mostu
JAHS-Bench-201.

## 4. Dane benchmarków (ok. 5 GB)

Dwa zbiory pobiorą się same, dwa trzeba skopiować z tej maszyny, bo są publikowane wyłącznie
przez Google Drive:

```bash
uv run python scripts/download_data.py      # FCNet + surogaty JAHS-Bench-201
```

Z lokalnego Windowsa (PowerShell, z katalogu `implementation\experiments`):

```powershell
scp -r data\cache\nashpobench2  user@SERWER:~/p3net_gecco2027/implementation/experiments/data/cache/
scp -r data\cache\nats_bench    user@SERWER:~/p3net_gecco2027/implementation/experiments/data/cache/
```

Możesz też przesłać wszystkie cztery katalogi (`data\cache\*`, ok. 5 GB) — wtedy masz pewność,
że na obu maszynach są dokładnie te same bajty. Potem, na serwerze:

```bash
uv run python scripts/check_data.py
```

Robi po jednym prawdziwym zapytaniu do każdego benchmarku. JAHS ładuje się ok. 4 minut.
Dopiero gdy wszystkie cztery wypiszą `OK`, ma sens startowanie przebiegu.

## 5. Uruchomienie

Jedna maszyna, 16 vCPU:

```bash
cd ~/p3net_gecco2027/implementation/experiments
nohup bash scripts/run_pipeline.sh --workers 8 > ~/pipeline.log 2>&1 &
tail -f ~/pipeline.log
```

Kilka maszyn — każda dostaje rozłączny kawałek planu, bez żadnej koordynacji między nimi:

```bash
# maszyna 1 z 3
nohup bash scripts/run_pipeline.sh --workers 8 --shard 0/3 > ~/pipeline.log 2>&1 &
# maszyna 2: --shard 1/3, maszyna 3: --shard 2/3
```

Pierwszy etap (`checks`) trwa ok. 25 minut: testy biblioteki, testy eksperymentów i sprawdzenie
determinizmu wszystkich 64 ramion. Uruchom go tylko na jednej maszynie; na pozostałych dodaj
`--skip-checks`.

## 6. Podgląd postępu

- W terminalu co 10 minut pojawia się linia `STATUS ...` z postępem etapów, listą liczonych
  właśnie ramion i wolną pamięcią (`--status-every 0` wyłącza).
- Linia na każdy ukończony przebieg: `results/runs/<commit>/logs/progress.log`.
- Pełne wyjście workerów: `logs/worker-<i>.log`; nieudane przebiegi: `failures.jsonl`.

```bash
tail -f results/runs/*/logs/progress.log
ls results/runs/*/raw | wc -l          # ile punktów gotowych
python - <<'EOF'
import json, collections
c = collections.Counter()
for line in open('results/runs/' + __import__('os').listdir('results/runs')[0] + '/failures.jsonl'):
    r = json.loads(line)
    if r.get('event') == 'failure':
        c[r['error'][:60]] += 1
print(c.most_common(10))
EOF
```

## 7. Zebranie wyników

Z każdej maszyny ściągnij katalog przebiegu i scal surowe pliki w jeden katalog (nazwy punktów
są unikalne, shardy są rozłączne):

```powershell
scp -r user@SERWER:~/p3net_gecco2027/implementation/experiments/results/runs/<commit> .\results\runs\
```

Po scaleniu:

```powershell
uv run python scripts/posthoc_metrics.py --raw results\runs\<commit>\raw
```

## 8. Zastrzeżenia, o których trzeba pamiętać przy pisaniu artykułu

1. **Nie mieszamy platform w jednej tabeli.** Każdy przebieg jest deterministyczny na swojej
   maszynie, ale Windows i Linux mają inne biblioteki BLAS, więc historie mogą się różnić na
   ostatnich bitach. Cała faza 4 musi powstać w jednym środowisku. Wyniki sprzed przenosin są
   skasowane, więc nie ma czym zanieczyścić.
2. **Wszystkie shardy muszą być tej samej klasy maszyny.** Inaczej wymiar praktyczny (czasy,
   pamięć) miesza dwie populacje sprzętu.
3. **Etap `s9_timing` uruchom na jednej maszynie, bez niczego innego w tle** — dlatego jest
   sekwencyjny i startuje po wszystkich etapach siatki.
4. Manifest sprzętu trafia do `sessions.jsonl` przy każdym uruchomieniu (procesor, RAM, GPU,
   wersje bibliotek, a na maszynie wirtualnej także producent i model według DMI). To z niego
   powstaje tabela sprzętu w artykule.
