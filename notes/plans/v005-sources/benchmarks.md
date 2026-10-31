# Benchmarki i cele (f1, f2) — karta źródła

Status: **ZATWIERDZONA** (2026-10-16, autor projektu): BM-1 a, BM-2 (energia inferencji, wszystkie 15 625, kontrola jakości), BM-3, BM-4, BM-5, W-BM1–W-BM7.
**Zmiana 2026-10-31 (P1 a, `v005-todo.md`):** BM-2 — źródło energii = HW-NAS-Bench, edge GPU (zamiast własnego pomiaru); W-BM2, W-BM3 przeformułowane (§3).
Decyzje wcześniejsze: #26 (JAHS: sprawdzić, czy `size_MB` zależy od HP), #27 (NB201: f1 = błąd walidacyjny), #28
(NB201: **własny pomiar energii GPU** wg metodyki Bartnik), #29 (logowanie zasobów), #31 (dyskretyzacja JAHS), #33
(Validity), #6 (f2 tylko z prawdziwej ewaluacji), MF-1 (f2 przy niższej wierności).

## 1. Stan obecny (kod `implementation/experiments/substrates/`)

| Przestrzeń | f1 | f2 | Uwagi |
|---|---|---|---|
| JAHS-Bench-201 (×3) | 100 − `valid_acc` (surogat JAHS, 200 epok) | `size_MB` (surogat JAHS) | #26 do sprawdzenia |
| NAS-HPO-Bench-II | 100 − dokładność walidacyjna po 12 epokach | `total_trainval_time` (12 epok) | MF: odczyt z tego samego biegu po e epokach |
| FCNet (×4) | walidacyjne MSE po 100 epokach, średnia z 4 seedów | czas treningu, średnia z 4 seedów | MF: czas·e/100 (zgodne z MF-1) |
| NAS-Bench-201 | **błąd testowy** | **FLOPs** | #27 i #28 — do zmiany (v005: f1 walidacyjne BM-1 a; f2 = energia z HW-NAS-Bench, BM-2) |

## 2. Decyzje

### BM-1. NB201: f1 (#27)

- **a) f1 = 100 − dokładność walidacyjna** z ustawienia `cifar10-valid` (trening na train, ocena na valid), 200 epok,
  **średnia po dostępnych seedach** (deterministycznie, jak FCNet); błąd testowy liczony tylko po przebiegu (raport).
  - Za: brak wyboru na zbiorze testowym; spójne z resztą przestrzeni. **Rekomendacja: a).**

### BM-2. NB201: f2 = zmierzona energia (#28)

Metodyka Bartnik (§6.2, Tab. 6.2–6.3): pyNVML, N_warmup = 3, N_samples = 3, mediana, cache po indeksie architektury. **U nas (ustawienia końcowe po pilotażu 4): N_samples = 5** (Q-47).

- **Który koszt:**
  - **a) energia inferencji** na zbiorze testowym CIFAR-10 (koszt wdrożenia; u Bartnik „figure of merit for
    deployment”). Energia inferencji zależy od architektury, nie od wartości wag → można mierzyć na sieci z losowymi
    wagami (bez treningu).
  - b) energia treningu 1 epoki. Przeciw: ~10–100× droższy pomiar.
  - **Rekomendacja: a).**
- **Zakres pomiaru:**
  - **a) wszystkie 15 625 architektur przed przebiegiem** → dokładny front referencyjny (IGD+ i punkt odniesienia HV
    z wyliczenia, jak u Bartnik). Koszt: rząd kilku dni GPU (do oszacowania pilotażem na 100 architekturach).
  - b) tylko zapytane w przebiegach (leniwie, cache). Za: taniej. Przeciw: front referencyjny tylko z sumy przebiegów;
    pomiar w trakcie przebiegu miesza się z czasem ścianowym metod.
  - **Rekomendacja: a)** — pomiar jako osobny, jednorazowy krok przygotowania benchmarku (tablica energii w repo),
    przebiegi tylko czytają tablicę.
- **Sprzęt (decyzja autora 2026-10-16): laptop autora, NVIDIA GeForce RTX 3050 Ti Laptop GPU, 4 GB, sterownik 610.60**
  (serwery eksperymentów Hetzner CPX62 nie mają GPU; HW-NAS-Bench i wynajem GPU rozważone i odrzucone). Model GPU,
  sterownik, wersje CUDA/PyTorch, limit mocy i zegary zapisane w metadanych tablicy.
- **Warunki pomiaru (laptop):** tylko na zasilaczu, profil wydajności, zegary zablokowane (`nvidia-smi -lgc` i `-pl`,
  jeśli sterownik pozwala — inaczej zapisać, że nie), brak innych obciążeń; jeden rozmiar batcha dla wszystkich
  architektur (największy, który mieści się w 4 GB dla największej architektury); temperatura GPU logowana przy każdym
  pomiarze.
- **Przed pomiarem — sprawdzenia (bramka):** (1) czy NVML udostępnia licznik energii
  (`nvmlDeviceGetTotalEnergyConsumption`); jeśli nie — energia = całka z próbkowanej mocy (`nvmlDeviceGetPowerUsage`),
  zapisane w metadanych; (2) czy blokada zegarów działa; (3) **pilotaż**: 100 losowych architektur zmierzonych dwa razy
  (w odstępie ≥ 1 h) → Spearman ≥ 0.95 i mediana różnicy względnej ≤ 3 %. Niezaliczony pilotaż = powrót do decyzji
  (wynajem GPU albo HW-NAS-Bench).
- **Stan bramki (2026-10-16):** (1) **licznik energii NVML dostępny** (`nvmlDeviceGetTotalEnergyConsumption` działa przez
  pyNVML; `nvidia-smi` go nie pokazuje) → `energy_method = "counter"`; (2) blokada zegarów (`nvidia-smi -lgc`) **wymaga
  uprawnień administratora** — do wykonania z konsoli „jako administrator” przed pomiarem (`--clocks-locked`); zmiana
  limitu mocy **nieobsługiwana** na tym GPU (limit wymuszony 45 W, domyślny 40 W — zapisywany w metadanych);
  (3) pilotaż — do wykonania. Próba na 3 architekturach: ~12 s/architekturę (3 + 3 przejścia po 10 000 wejść, batch
  256) → pełna tablica ≈ 52 h; rozrzut 3 próbek w obrębie architektury do ±6 %, temperatura 68–75 °C.
  Narzędzia: `vendor/energy-env/` (osobne środowisko), `scripts/measure_nb201_energy.py`, `scripts/compare_energy_runs.py`.
- **Pilotaż 1 (2026-10-17, zegar 1500 MHz): NIEZALICZONY** — Spearman 0.975 (✓), mediana różnicy 11.5 % (✗). Przyczyna:
  **stałe przesunięcie poziomu** między sesjami (drugi przebieg ~11 % niżej prawie dla każdej architektury; porządek
  zachowany), rozrzut 3 próbek w architekturze mediana 12 %, spadki zegara poniżej blokady przy ~75 °C (16–20 / 100).
- **Poprawka (decyzja autora 2026-10-17, „opcja tania”), kryterium bez zmian:** (1) **korekta dryfu komórką odniesienia**
  `|nor_conv_3x3~0|+|nor_conv_1x1~0|skip_connect~1|+|avg_pool_3x3~0|nor_conv_3x3~1|nor_conv_1x1~2|` mierzoną na początku i
  co 10 architektur; wartość w tablicy = energia / energia odniesienia interpolowana liniowo w kolejności pomiaru
  (bezwymiarowa; dominacja i rangi niezmienione przez skalowanie); (2) **zegar zablokowany na 1200 MHz** (poniżej progu
  dławienia). Pilotaż 2 = dwa nowe przebiegi, kryterium na wartościach skorygowanych.
- **Pilotaż 2 (1200 MHz + korekta):** Spearman 0.962, różnica 4.0 % — niezaliczony. **Pilotaż 3** (+ 5 próbek, ponowny
  pomiar przy rozrzucie > 8 % do 2 razy, odniesienie co 5): 0.980 / 3.43 % — niezaliczony. **Pilotaż 4** (+ rejestrowanie
  stanu sesji): **Spearman 0.975, różnica 3.00 % — ZALICZONY** (na granicy). We wszystkich pilotażach drugi przebieg był
  2–2.5× bardziej zaszumiony (rozrzut 10–13 % vs 5 %, ~80 % architektur z ponownym pomiarem); rejestrowany stan sesji
  (CPU, moc/temperatura GPU w spoczynku, zasilanie, bateria, P-state, przyczyny obniżenia zegara, plan zasilania)
  identyczny w obu — przyczyna nieustalona (do Limitations). Ustawienia końcowe: zegar 1200 MHz, 3 + 5 przejść, mediana,
  ponowny pomiar > 8 % (≤ 2), odniesienie co 5, korekta interpolacją. Szacowany czas pełnej tablicy: 4–10 dni.
- **Decyzja autora (2026-10-18): pełny pomiar odłożony na koniec etapu A** (przed przebiegami NB201 v005). Wtedy najpierw
  pilotaż z krótszym przejściem (1 000 wejść zamiast 10 000, ~10× szybciej, < 1 doba na całość); jeśli kryterium
  przejdzie — pełna tablica w tej wersji; jeśli nie — wersja 10 000 wejść albo HW-NAS-Bench.
- **Pilotaż 5 (2026-10-29, 1 000 wejść, 1200 MHz, te same 100 architektur): NIEZALICZONY** — Spearman 0.34, mediana
  różnicy 18.2 %. Przejście 0.20 s (vs 1.94 s przy 10 000) za krótkie dla licznika NVML: rozrzut próbek w architekturze
  52–55 % (pilotaż 4: 5–13 %), zmienność komórki odniesienia 13–17 % (0.6–2.7 %), 99 % architektur mierzonych ponownie;
  czas ~7 s/architekturę (zysk ~2.5×, nie 10×). Pełne przejście (pilotaż 4) zaliczone tylko na granicy, pełna tablica
  4–10 dni laptopa.
- **Autor (2026-10-29): pomiaru na laptopie nie jest w stanie wykonać.** Kierunek: HW-NAS-Bench („brzmi
  najrozsądniej”) — uwaga: 2026-10-16 autor odrzucił HW-NAS-Bench na rzecz laptopa; zmiana z powodu pilotaży 1–5.
- **DECYZJA AUTORA 2026-10-31 (P1 a) — obowiązuje w v005:** f2 = `edgegpu_energy` z HW-NAS-Bench v1.0 (Jetson TX2,
  TensorRT, batch 1, CIFAR-10, mJ/obraz; Li et al., ICLR 2021; MIT), zbiór `cifar10` tablicy HW-NAS-Bench (sieć
  `infer.tiny`, C = 16, N = 5 — ta sama co NATS `tss`). Sprawdzenie: `notes/plans/v005-hwnasbench-check.md` (indeksy
  zgodne z NATS 15 625/15 625; Spearman z FLOPs 0.55; szum w klasach izomorficznych CV 4.2 %). Wartości opublikowane,
  nie mierzone przez nas. Pozostałe punkty BM-2 powyżej (sprzęt, warunki, bramka, pilotaże) i kontrola jakości poniżej
  dotyczą zarzuconego pomiaru na laptopie — zostają jako zapis decyzji.
  - **Wykonanie:** `scripts/download_data.py --only hw_nas_bench` (pobranie, sha256
    `57f92c2d7b88814fa337d00f4597c8ca30d507c5a855c18d6fac57e5ad872700`) → `scripts/build_nb201_energy_table.py`
    (`p3net.v005.benchmarks.build_energy_table_hwnasbench`, wczytanie pickle z białą listą klas numpy) →
    `results/benchmark_tables/nb201_energy.json` (15 625 komórek po `arch_str`, metadane: źródło, sha256, urządzenie,
    batch, jednostka, liczba rozbieżności indeksów z NATS = 0). Zbudowane 2026-10-31.
  - **Limitations (zastępuje akapit poniżej):** brak własnego pomiaru energii (pilotaże 1–5); energia specyficzna dla
    urządzenia i batcha (nasz laptop, batch 256, vs TX2: Spearman 0.74); szum tablicy w klasach izomorficznych
    (mediana CV 4.2 %, 90. percentyl 10.3 %) — metoda może wybierać tańszy izomorf; wyniki NB201 v005 nieporównywalne
    z v004 (f2 = FLOPs, Spearman z energią 0.55); porównanie z Bartnik (Tab. 7.1) na FLOPs, bo jej f2 to energia
    innego GPU.
- **Kontrola jakości pomiaru (laptop, nieaktualne od 2026-10-31):** powtórzenie pomiaru 50 losowych architektur na końcu → zgodność rang (Spearman ≥ 0.95)
  i mediana różnicy względnej ≤ 3 % (Tab. 6.3 u Bartnik: 2.4 % dla (3, 3)); inaczej pomiar powtarzany.
- **Limitations (laptop — nieaktualne od 2026-10-31, zastąpione akapitem przy decyzji P1 a):** energia zmierzona na jednym laptopowym GPU klasy konsumenckiej; wartości
  bezwzględne specyficzne dla urządzenia i nieprzenoszalne; laptop podlega zmiennym limitom mocy i dławieniu termicznemu
  (ograniczone przez blokadę zegarów i kontrolę powtarzalności, nie wyeliminowane); NVML mierzy tylko pobór GPU (bez CPU,
  DRAM, strat zasilacza — jak u Bartnik); pomiar na sieciach z losowymi wagami (energia inferencji nie zależy od wartości
  wag, ale nie mierzymy wytrenowanych modeli); jeśli licznik energii niedostępny — energia z próbkowanej mocy (mniejsza
  dokładność przy krótkiej inferencji); rozmiar batcha ograniczony pamięcią 4 GB. Wnioski o koszcie na NB201 dotyczą tego
  urządzenia; NB201 pozostaje krótką uwagą (B2).

### BM-3. JAHS: f2 (#26)

Test (przed prerejestracją): dla 200 losowych komórek × 10 losowych kombinacji HP (LR, WD, aktywacja, TrivialAugment)
odczytać `size_MB` z surogatu.

- Jeśli `size_MB` jest **stałe przy stałej komórce** (różnice < 10⁻⁶) → zostaje (zgodne z definicją: rozmiar zależy tylko
  od architektury).
- Jeśli **zmienia się z HP** (surogat uczony z szumem) → **f2 = liczba parametrów liczona analitycznie** z komórki
  (sieć NB201/JAHS przy N, W, Resolution zamrożonych na maksimum, #31), budowana raz kodem sieci JAHS/NATS; tablica w repo.

**Rekomendacja:** wykonać test; decyzja wynika z wyniku (reguła powyżej, ustalona przed testem).

**Wynik (2026-10-16, `results/checks/bm3_jahs_size_vs_hp_cifar10.md`):** `size_MB` zmienia się z HP w **200/200**
komórkach (rozrzut przy stałej komórce: mediana 0.025 MB, maks. 0.28 MB, maks. względny 34 %) → **f2 na JAHS = analityczna
liczba parametrów** (`scripts/build_jahs_param_counts.py` → `results/benchmark_tables/jahs_param_counts.json`, 15 625
komórek × 3 zadania; sieć xautodl `infer.tiny`, C = 16, N = 5; głowa klasyfikatora wg liczby klas). Walidacja: korelacja z
medianą `size_MB` po HP — Pearson 0.999, Spearman 0.989; `size_MB` ≈ liczba parametrów / 10⁶ (współczynnik 0.247 względem
parametrów × 4 B) — czyli `size_MB` to liczba parametrów w milionach z szumem surogatu.
**Skutek dla interpretacji v004 (etap B):** f2 na JAHS w v004 zawierało szum surogatu zależny od HP — metoda mogła
„poprawiać” f2, zmieniając LR/WD przy stałej architekturze. Odnotować przy interpretacji wyników JAHS z v004.

### BM-4. NAS-HPO-Bench-II i FCNet — bez zmian

Sprawdzić testem, że f1 pochodzi ze zbioru walidacyjnego (nie testowego) i że f2 przy niższej wierności spełnia MF-1.

### BM-5. Logowanie zasobów (#29)

Pamięć serwera JAHS i GPU, czas ładowania surogatu, czas ścianowy metody (bez czasu odczytu benchmarku) — rejestrowane;
asercja niepustych pól.

**Uzupełnienie 2026-10-31 (decyzja P3 (2a), `v005-todo.md`; przyczyna: A8, `v005-a8-analysis.md` „Pamięć”):**
- `peak_memory_process_mb` = szczyt pamięci procesu **w tym przebiegu**, nie od startu procesu workera. Na Linuksie szczyt
  jądra (VmHWM) zerowany na starcie przebiegu (`/proc/self/clear_refs` = 5) → `peak_memory_process_scope = "run"`;
  gdzie się nie da (Windows) → `"process"` (szczyt od startu procesu; dokładny tylko przy świeżym procesie na przebieg).
- `peak_memory_server_mb` (JAHS) = szczyt pamięci mostu JAHS (proces + procesy potomne) próbkowany na starcie i końcu
  przebiegu i po zapytaniach do benchmarku; także przy **wspólnym** moście (PID z pliku portu). Na Linuksie suma PSS
  (strony współdzielone copy-on-write liczone raz), inaczej suma RSS → `peak_memory_server_method` = `"pss_sum"` /
  `"rss_sum"`. Wspólny most obsługuje wszystkie workery naraz — wartość to koszt maszyny, nie jednego przebiegu (opisać
  w podpisie tabeli kosztów).

## 3. Własności do sprawdzenia testami (poziom 1)

| ID | Własność |
|---|---|
| W-BM1 | NB201: f1 z `cifar10-valid` (walidacja), średnia po seedach; żaden kod metody nie widzi błędu testowego |
| W-BM2 | NB201: f2 = wartość z tablicy energii; tablica kompletna (15 625), metadane źródła obecne (zmiana 2026-10-31, P1 a: źródło HW-NAS-Bench, `metric = edgegpu_energy`, urządzenie Jetson TX2, batch 1, jednostka mJ/obraz, zbiór `cifar10`) |
| W-BM3 | (zmiana 2026-10-31, P1 a; dawniej: protokół pomiaru na laptopie — nieaktualny) Zgodność ze źródłem: sha256 pliku HW-NAS-Bench = `57f92c2d…ad872700`; 0 rozbieżności indeksów HW-NAS-Bench z `nats_bench.query_index_by_arch`; wartości w tablicy = `edgegpu_energy[i]` z pliku dla `arch_str` z `config[i]`; plik o innym sha256 odrzucony przed wczytaniem |
| W-BM4 | JAHS: f2 wg wyniku BM-3 (test zapisany w `results/checks/`) |
| W-BM5 | NAS-HPO-II, FCNet: f1 walidacyjne; f2 przy e < E wg MF-1 |
| W-BM6 | Validity (#33) jednakowa na JAHS, NAS-HPO-II, NB201 |
| W-BM7 | Pola zasobów (BM-5) niepuste w każdym przebiegu; (2026-10-31, P3 (2a)) na Linuksie `peak_memory_process_scope = "run"` i szczyt przebiegu nie zawiera szczytu wcześniejszego przebiegu w tym samym procesie; na JAHS `peak_memory_server_method` ∈ {`pss_sum`, `rss_sum`} |

## 4. Do zatwierdzenia

BM-1 a; BM-2 (energia inferencji, pomiar wszystkich 15 625 przed przebiegiem, kontrola jakości) + **wskazanie GPU**;
BM-3 (test i reguła); BM-4; BM-5; W-BM1–W-BM7. — Zatwierdzone 2026-10-16; BM-2 zmienione 2026-10-31 (P1 a).
