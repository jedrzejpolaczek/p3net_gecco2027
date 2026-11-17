# v005 — testy zgodności z kodem referencyjnym (poziom 2): kryteria

Status: **ZAPISANE PRZED TESTAMI** (2026-10-18). Protokół §3: kryterium zapisane przed testem; zatwierdza autor projektu.
Wspólna reguła (protokół, decyzja 2): mediana HV ±2 % + test równoważności (TOST, margines ±2 % mediany, α = 0.05),
100 przebiegów (decyzja 2026-10-19; było 20–30), chyba że niżej podano test deterministyczny (identyczna sekwencja / harmonogram — silniejszy).

| Metoda | Referencja | Test | Kryterium | Wykonalność |
|---|---|---|---|---|
| MOTPE | optuna `TPESampler` (natywna pętla) | deterministyczny (W-A5) | identyczna sekwencja propozycji | **zrobione** (poziom 1, W-A5) |
| SMAC3-ParEGO | smac 2.4.1 (natywna pętla) | deterministyczny (W-A5) | identyczna sekwencja | **zrobione** (W-A5) |
| Hyperband | hpbandster `HyperBand` (kopia w repozytorium BoB) | deterministyczny | identyczne nawiasy: liczby konfiguracji i budżety na każdym szczeblu, η = 3, R = 27 / 100 / 200 | wykonalne (czysty Python) |
| MO-BOHB (harmonogram) | hpbandster `MOBOHB` | deterministyczny | identyczne budżety i liczby konfiguracji nawiasów (η = 2) | wykonalne |
| SH-EMOA | `shemoa.py` (BoB) | deterministyczny: `get_budgets` | identyczne budżety i liczby ewaluacji | **zrobione** (W-BB2) |
| REINFORCE | `reinforce.py` NAS-Bench-201 | jednokryterialnie na NB201 (f1 walidacyjne), 100 przebiegów po 100 krokach | rozkład najlepszej dokładności walidacyjnej: mediana ±2 % + TOST | wykonalne (torch + nats_bench w `experiments/.venv`) |
| RegEvo | `R_EA.py` NAS-Bench-201 | jak wyżej, P = 10, S = 10 | jak wyżej | wykonalne |
| NSGA-Net | `ianwhale/nsga-net` (pymoo 0.3.0) | dwukryterialne pułapki k-arne + NAS-HPO-II, 100 przebiegów | mediana HV ±2 % + TOST | **trudne**: pymoo 0.3.0 używa `np.int`/`np.bool` (usunięte z numpy ≥ 1.24) — osobne środowisko ze starym numpy/Pythonem |
| NSGANetV2 | `mikelzc1990/nsganetv2` (`_next`, `_subset_selection`, AS) | deterministyczny na tym samym archiwum | identyczni kandydaci | **trudne**: pymoo 0.4 + pySOT + pydacefit (stare); nasze RBF/GP to odpowiedniki, nie kopie — test deterministyczny niemożliwy z definicji; zamiast niego: zgodność rankingu modeli (τ) na wspólnych danych |
| SH-EMOA / MO-BANANAS (pętla) | BoB `shemoa.py`, `mobananas.py` | `simple_problems.py` z repozytorium BoB, 100 przebiegów | mediana HV ±2 % + TOST | **trudne**: kod BoB zależy od Ax 0.1.x i torch; pętle trzeba uruchomić z podmienionym `Experiment` |
| P3 (kanoniczne) | kod Goldmana (C++, repozytorium do potwierdzenia) | jednokryterialnie: pułapki, NK; 100 przebiegów | mediana liczby ewaluacji do optimum ±2 % + TOST | **do ustalenia**: repozytorium nie zostało jeszcze odnalezione |
| P3-eLyMPuS | OLyMPuS `IslandGA.exe` (binarny) | binarnie: Dec5, mk-trapy (rozmiary z Tab. 5), 100 przebiegów | mediana FFE do optimum i odsetek odkrytych zależności ±2 % + TOST | wykonalne pod Windows; uruchomienie gotowego `.exe` z internetu — **wymaga zgody autora projektu** (alternatywa: kompilacja ze źródeł, MSVC) |
| Bartnik MO-PSA | brak kodu (Z-B0) | — | tylko poziom 1 + porównanie z SAGOMEA jednokryterialnie | SAGOMEA: C++ + Python — do sprawdzenia |
| qNEHVI / qParEGO / Vizier / NSGA-III / MOEA/D / RS | biblioteki | adapter = biblioteka (W-A1, W-A5 tam, gdzie możliwe) | — | MOEA/D: własna pętla wg pymoo 0.6.2 → test: z operatorami SBX/PM trajektoria = pymoo `MOEAD` na tych samych wagach i sąsiedztwie |

Kolejność wykonania: deterministyczne (Hyperband, MO-BOHB, MOEA/D) → NB201 (REINFORCE, RegEvo) → P3-eLyMPuS (po zgodzie)
→ pozostałe „trudne” (osobne środowiska).

## Wyniki

### MOEA/D vs pymoo 0.6.2 (2026-10-18) — `implementation/lib/tests/v005/level2/test_moead_vs_pymoo.py`

- Ustawienie: te same operatory kategoryczne, N = 20, T = 4, Tchebycheff, 400 ewaluacji, 10 zmiennych × 8 wartości.
  pymoo ocenia duplikaty (~19 % ewaluacji), nasza wersja losuje je od nowa (#20, #35) → referencją jest pierwsze 400
  **różnych** punktów pymoo.
- 20 seedów: mediana 77.6 vs 77.3 (+0.4 %), TOST p = 0.094 (za mała moc). 30 seedów: mediana −2.3 % (przekroczony
  margines). **100 niezależnych seedów: średnia +1.2 % (Welch p = 0.009), mediana 78.0 vs 77.0; TOST z marginesem ±2 %
  przechodzi.**
- **Odstępstwo od kryterium:** liczba przebiegów 20–30 z protokołu jest za mała dla rozrzutu HV ~3 % — wynik zależy od
  wyboru seedów. Wniosek: implementacja równoważna pymoo w granicy ±2 %, z małą systematyczną przewagą (+1.2 %), najpewniej
  od losowania duplikatów zamiast ich oceniania. **Do decyzji autora:** przyjąć 100 przebiegów jako liczbę dla testów
  statystycznych poziomu 2 (zmiana protokołu, decyzja 2) albo zostawić 20–30 z zastrzeżeniem.

## Decyzje autora (2026-10-19)

1. **Liczba przebiegów w testach statystycznych poziomu 2: 100** (zamiana „20–30” z protokołu, decyzja 2; powód: przy
   rozrzucie HV ~3 % mediana z 20–30 przebiegów waha się o ±2 % — test bez mocy). Margines ±2 % i TOST bez zmian.
2. **P3-eLyMPuS: uruchomić gotowy `IslandGA.exe`** z repozytorium autorów (OLyMPuS).
3. **Osobne środowiska ze starymi wersjami dla wszystkich pięciu trudnych referencji**: NSGA-Net (pymoo 0.3.0), NSGANetV2
   (pymoo 0.4 + pySOT + pydacefit), pętle Bag of Baselines (Ax/torch), P3 Goldmana (C++, repozytorium do odnalezienia),
   SAGOMEA (C++ + Python). Gdy środowiska nie da się zbudować — odstępstwo uzasadnione z opisem przyczyny.

## Wyniki po decyzjach (2026-10-19)

- **MOEA/D, 100 przebiegów: PASS** (`test_moead_vs_pymoo.py`, SEEDS = range(100)).
- **P3-eLyMPuS — `IslandGA.exe` niewykonalne:** wszystkie trzy binarki w archiwach OLyMPuS (`zz_introduction`: 1.32 MB,
  1.36 MB, 2.03 MB; `zz_miscellaneous`: 2.90 MB) to starsze kompilacje — nie zawierają opcji `limitedSurrogate_*`
  ani `resultTransformation` z plików ustawień `exp_POLiNoMok`. eLyMPuS wymaga kompilacji ze źródeł (Visual Studio,
  Release x64; na tej maszynie brak kompilatora C++).
- **P3 kanoniczne — referencja odnaleziona:** OLyMPuS zawiera kod P3 Goldmana (`OptFrame/P3/`, „Brian Goldman”), a stara
  binarka uruchamia go (`optimizer_type p3` + `default.cfg` Goldmana). Próba: Dec5, n = 100 — optimum po 11 935 FFE.
  Konwersja ustawień `exp_POLiNoMok` do starego formatu: bez linii `func overlap`, `bit length`, `stop_condition_type ffe`.
- **P3-eLyMPuS — kompilacja ze źródeł (decyzja 2026-10-19, opcja a): OK.** VS 2022 Build Tools 17.14 + toolsety v141/v142
  (bez podnoszenia, jak w instrukcji autorów) + ATL; jedyna zmiana: Windows SDK 10.0.19041 zamiast 10.0.18362
  (niedostępny). Budowanie z krótkiej ścieżki (`subst X:`; inaczej `order-p3` przekracza MAX_PATH):
  `MSBuild X:\OptFrame\IslandGA.sln /t:IslandGA /p:Configuration=Release /p:Platform=x64 /p:WindowsTargetPlatformVersion=10.0.19041.0`.
  Binarka (3.45 MB) czyta oryginalne ustawienia `exp_POLiNoMok` bez zmian. Próba Dec5, n = 100: P3 standard — optimum
  po 19 951 FFE; P3-LSur1nth (eLyMPuS) — optimum po 42 155 FFE; plik `_VIGquality_` (odkryte zależności) zapisany.

### P3-eLyMPuS i P3 vs `IslandGA` — kryterium doprecyzowane przed testem (2026-10-19)

- Skrypt: `implementation/lib/tests/v005/level2/elympus_vs_islandga.py`. Problemy: Dec5 (n = 50, 100, 200) i bimodal-10
  (n = 100, 200) z `exp_POLiNoMok/deceptive` — dla mk-trapów autorzy nie mają ustawień P3-eLyMPuS (`settings_P3_LSur1nth`
  istnieją tylko dla funkcji zwodniczych), a format plików mk-landscape trzeba by przenosić osobno.
- Nasze metody są dwukryterialne: cel zdublowany (f2 = f1) → dominacja = poprawa f1. Przebieg do optimum.
- **Kryterium główne:** mediana FFE do optimum — nasze **unikalne ewaluacje** (#35) vs FFE referencji; ±2 % + TOST
  (100 przebiegów na stronę). Diagnostycznie: nasze wszystkie żądania ewaluacji (z powtórzeniami z pamięci podręcznej;
  referencja jej nie ma). Dla eLyMPuS dodatkowo: odsetek odkrytych prawdziwych zależności w chwili optimum ±2 % + TOST
  oraz liczba fałszywych (oczekiwane 0 po obu stronach).

### NSGA-Net vs kod autorów (2026-10-19) — `test_nsganet_vs_reference.py`

- Referencja: `search/nsganet.py` z `ianwhale/nsga-net` @ 0ee6225 na pymoo 0.3.0 w `implementation/experiments/vendor/nsganet-env`
  (Python 3.8, numpy 1.23.5; repozytorium autorów bez licencji → nie wkopiowane, ścieżka w `P3NET_NSGANET_REPO`).
  pop = potomstwo = 20, 400 **różnych** ewaluacji (jak MOEA/D), problemy wspólne `_problems.py`.
- **100 seedów: PASS.** additive: mediana HV 77.70 vs 77.83 (−0.2 %); trap k-arny: 220.95 vs 222.00 (−0.5 %); TOST ±2 % przechodzi.
- Niezrobione z kryterium: NAS-HPO-II w starym środowisku (ładowanie danych benchmarku na Pythonie 3.8) — do decyzji, czy
  potrzebne przy zgodności na dwóch problemach syntetycznych.

### P3 vs `IslandGA` — wyniki i ustalenia (2026-10-19/20)

- **Ziarno:** bez wiersza `random_seed` binarka sieje z zegara (sekundy) → pierwsza seria miała 4 różne przebiegi na 100;
  odrzucona. Skrypt wstawia `random_seed = i + 1`.
- **`P3standard` z `exp_POLiNoMok` to nie kanoniczne P3:** `opt_at_init 5` puszcza FIHC przez klasę ograniczonego
  surogatu (strategia `FIHCstandard`) — Dec5 n = 50: mediana 9 214 FFE. Kod Goldmana z FIHC Goldmana (`opt_at_init 1`,
  wariant `p3goldman` w skrypcie): 4 476. Referencją dla `P3Canonical` jest `opt_at_init 1`.
- **Licznik (decyzja a):** nasz `P3Canonical` nigdy nie pyta ponownie o rozwiązanie o znanej wartości (każde żądanie to
  nowy losowy punkt, ruch FIHC lub kandydat mieszania ≠ bieżący) → „wszystkie żądania” = licznik `evaluator.evaluate`
  Goldmana. Przegląd kodu: FIHC (losowa kolejność, `tried`), donate-until-different, akceptacja remisów (`d_slide = 1`),
  globalny `seen`, wstawianie wyżej tylko przy poprawie — zgodne.
- **Dec5 n = 50, 100 przebiegów:** mediana 5 120 vs 4 476 (+14 %), średnia 5 587 vs 5 192 (+7.6 %); Mann–Whitney p = 0.17;
  95 % CI ilorazu median [0.98, 1.28] — **różnica nieistotna**. TOST ±2 % nie przechodzi, bo **nie może** przy tym rozrzucie:
  CV FFE do optimum = 0.45 po obu stronach → TOST ±2 % wymaga ~6 800 przebiegów na stronę. Kryterium ±2 % (pisane z myślą
  o HV, CV ~3 %) jest dla FFE do optimum niewykonalne — **do decyzji autora**.
- **Decyzja autora (2026-10-20, opcja a):** kryterium ±2 % + TOST bez zmian, ale na Dec5 n = 50 z **7000 przebiegami na
  stronę** (P3: `P3Canonical` vs `p3goldman`; eLyMPuS: `P3ELyMPuS` vs `P3_LSur1nth`). Dec5 n = 100 i 200 — opisowo
  (100 przebiegów, Mann–Whitney + CI ilorazu median). Bimodal-10 pominięty (referencja ~10⁶ FFE — za drogie w Pythonie).
- **P3 kanoniczne — decyzja autora (2026-10-20): zgodne z kodem Goldmana (zaliczone).** Dec5 n = 50, 7000 przebiegów na
  stronę: mediana FFE 4974 vs 4978 (−0.07 %), średnia +0.84 % (90 % CI [−0.4 %, +2.1 %]), kwantyle 10–90 różnią się < 1.5 %,
  Mann–Whitney p = 0.27, KS p = 0.15. Kryterium mediany ±2 % spełnione; TOST p = 0.094 (górna granica CI 2.1 %) — w raporcie
  jako odnotowane. Opisowo (100 przebiegów): n = 100 +4.0 %, n = 200 +1.7 % (mediana).

### P3-eLyMPuS vs `IslandGA` — diagnoza (2026-10-20)

- Dec5 n = 50, mediany (200 przebiegów; referencja z własnym rozbiciem kosztu w `*_out.txt`, iteracje z kopii
  diagnostycznej referencji): P3 Goldmana — mieszanie 688, FIHC ~96 FFE/iterację; nasze P3 — 745, ~100, 42 iteracje;
  `P3standard` autorów (ścieżka `opt_at_init 5`, bez list) — 41.5 iteracji, FIHC 101/iterację, **mieszanie 4239**;
  P3-eLyMPuS autorów — 41.5, FIHC 144.5/iterację, mieszanie 2110; nasze P3-eLyMPuS (licznik jak w referencji: jeden cel,
  bez żądań o x w parze) — 42, ~114/iterację, mieszanie 747.
- FIHC-eLyMPuS w referencji zwraca prawdziwe optima lokalne w 99.8 % wywołań (3489/3495, 60 przebiegów), wartość zawsze
  zgodna z prawdziwą; fałszywych zależności 0 po obu stronach.
- Różnica FFE pochodzi głównie z **mieszania na ścieżce `opt_at_init 5`** (6× więcej niż u Goldmana przy tych samych
  iteracjach i koszcie FIHC; kod `Population::improve`/`donate`/`rebuild_tree` jak u Goldmana — przyczyna nieznaleziona).
- **Decyzja autora (2026-10-20, c): pytanie do M. Przewoźniczka; czekamy na odpowiedź** (jak w przypadku Bartnik).
  Do tego czasu eLyMPuS — poziom 2 otwarty.

### Hyperband i MO-BOHB — harmonogramy (2026-10-20) — `test_mf_schedules.py`: 6/6 PASS

- Hyperband `bracket_schedule(3, 1, 81)` = Li et al. 2018, Tabela 1 (identycznie).
- MO-BOHB: brackety (budżety, `ns`) = wzory z `hpbandster/optimizers/mobohb.py` dla E ∈ {12, 25, 50, 100, 200}; awans =
  `SuccessiveHalvingMOBOHB` (całe fronty NDS, **po pętli zawsze jeszcze jeden cały front** → awansuje więcej niż `ns`;
  nasz port robi to samo).
- **Znalezione przy okazji — brak w porcie MO-BOHB:** kod autorów przy `init=True` (domyślnie w `get_MOBOHB`) zaczyna od
  iteracji z `num_initial_samples` losowymi konfiguracjami ocenionymi od razu na max budget (`budgets=[25]*N`, 25 = max
  w ich ustawieniach; przykłady: N = 50 Flowers, 10 Fashion). Karta MB2 podaje `num_initial_samples` 50, ale BB-4 nie ma
  wiersza MO-BOHB, a port tej iteracji nie ma. **Do decyzji autora.**
- **Decyzja autora (2026-10-20, a):** initial design MO-BOHB dodany wg BB-4 (min(50, ⌊0.25·b⌋) konfiguracji na E;
  `mf.py`, `MOBOHB.n_init`); wiersz w BB-4; test w `test_mf_schedules.py` (9/9 PASS); prośba o test poziomu 1 — Q-43.

### REINFORCE i RegEvo vs kod NAS-Bench-201 (2026-10-20) — `test_reinforce_regevo_vs_nb201.py`: 2/2 PASS

- Referencja: pętle z `reinforce.py` i `R_EA.py` (D-X-Y) przeniesione dosłownie (bez CUDA, loggera i limitu czasu);
  reward po obu stronach = valid-accuracy cifar10-valid po 12 epokach (hp = "12", jak `train_and_eval`), deterministyczna,
  z tabeli `experiments/results/benchmark_tables/nb201_valid12_cifar10valid.json` (`scripts/build_nb201_valid12_table.py`).
- REINFORCE (100 kroków polityki; nasz reward zastąpiony surową accuracy — test maszynerii polityki/baseline/Adam):
  mediana najlepszej accuracy 82.67 vs 82.96, średnia 82.27 vs 82.27, MWU p = 0.69, TOST p < 1e-7.
- RegEvo (P = 10, S = 10, 100 różnych architektur): mediana 84.68 vs 84.68, średnia 84.57 vs 84.53, MWU p = 0.72, TOST p < 1e-70.
- Uwagi: margines ±2 % to ok. ±1.7 pkt accuracy — łagodny; średnie zgodne z dokładnością do 0.05 pkt.
- **Znalezione przy czytaniu `R_EA.py`:** (1) mutacja w referencji losuje węzeł, potem krawędź w węźle (krawędź do węzła 1:
  1/3, do węzła 3: po 1/9); nasza — każdą z 6 zmiennych po 1/6 (karta: „mutacja jednej zmiennej”). Wynik testu
  nierozróżnialny. **Do decyzji autora.** (2) `crowded_winner` rozstrzygał remisy globalnym `random` → poprawione
  (generator metody, `_TIE_RNG`; sygnatura bez zmian, testy poziomu 1 12/12).
- **Decyzja autora (2026-10-20, b):** mutacja RegEvo jak w `R_EA.py` (węzeł → krawędź; Z-RE1: zmienne spoza komórki jako
  osobne jednostki); karta O-RE3 zmieniona; test rozkładu w `test_reinforce_regevo_vs_nb201.py` (3/3 PASS, RegEvo nadal
  zgodne: mediana 84.71 vs 84.68); prośba o test poziomu 1 — Q-44.

### NSGANetV2 — kryterium doprecyzowane przed testem (2026-10-20)

Tabela: „test deterministyczny niemożliwy (nasze RBF/GP to odpowiedniki) → zgodność rankingu modeli (τ) na wspólnych
danych”. Doprecyzowanie: 100 zbiorów danych z problemu `additive` (`_problems.py`, 10 zmiennych × 8 wartości, cel f1),
50 punktów uczących (jak N_doe przy b = 200), 200 testowych; modele autorów (`acc_predictor/{rbf,gp,carts}.py`, pySOT
0.2.3, pydacefit 1.0.1, `vendor/nsganetv2-env`) vs nasze `_RBF`, `_GP`, `_CART`.
- **RBF, GP:** mediana τ Kendalla (nasze vs autorów, predykcje na zbiorze testowym) ≥ 0.95.
- **CART** (losowy zespół 5000 drzew): mediana τ(nasze, autorów) ≥ mediana τ(autorów seed 1, autorów seed 2) − 0.02.
- **Jakość:** dla każdego modelu |mediana τ(nasze, prawda) − mediana τ(autorów, prawda)| ≤ 0.02.
- **Adaptive Switching:** zgodność wyboru zwycięzcy (ten sam podział na foldy) w ≥ 80 % zbiorów.

### Pętle Bag of Baselines (SH-EMOA, MO-BANANAS) — sposób uruchomienia i kryterium (przed testem, 2026-10-21)

- Kod autorów (`shemoa.py`, `member.py`, `mobananas.py`) uruchamiany **bez zmian**; Ax zastąpiony zaślepką (tylko
  `Experiment.new_trial/eval_trial`, `GeneratorRun`, `Arm`, `Data.df`), pakiet `baselines` bez `__init__` (tylko
  `nDS`, `computeHV2D`) — `tests/v005/level2/bob_reference_runner.py`. Osobne środowisko z Ax 0.1.x niepotrzebne.
- Problem `flowers_like`: 13 zmiennych (11 × 8 + `batch_norm`, `global_avg_pooling` × 2 — klucze wymagane przez
  `Member.fitness`), cele addytywne; dla kodu autorów przeskalowane do konwencji Flowers (log10 #param w (0, 8),
  −accuracy w (−100, 0)), bo kod ma na sztywno klucz turnieju (15 − f0)·f1 i punkt HV [8, 0]; nasz port (T-2: NDS + wkład
  HV, normalizacja online) dostaje cele surowe — ranking dominacji ten sam.
- SH-EMOA jednowiernościowo (`budget_min = 24, budget_max = 25` → jeden budżet), populacja 20; 100 **różnych** punktów
  (#35). **Kryterium:** HV (surowe cele, punkt (13, 17)) — mediana ±2 % + TOST, 100 przebiegów.
- **MO-BANANAS** (kryterium jak SH-EMOA, przed testem): `get_MOBANANAS` — 20 początkowych, num_arch 8, select 4, 80 epok,
  5 sieci; 100 różnych punktów, HV ±2 % + TOST, 100 przebiegów. **Kod autorów nie uruchamia się w opublikowanej
  postaci** — trzy minimalne obejścia w runnerze (bez zmiany logiki): kolejność argumentów `Member(...)` w
  `BANANAS.__init__` (TypeError), tylko CPU (`neural_predictor.py` miesza tensory cuda/cpu), aliasy `np.float/int/bool`;
  dodatkowo nazwy 6 zmiennych jak we Flowers (`n_conv_*`, `n_fc_*`), bo sieć ma na sztywno 13 wejść.

### NSGANetV2 — wynik (2026-10-21), 100 zbiorów: 6/7 kryteriów PASS

- RBF: τ(nasze, autorów) = **1.000** (identyczne rankingi); jakość τ vs prawda 0.175 = 0.175.
- CART: τ(nasze, autorów) 0.977 vs τ(autorzy, autorzy-inny-seed) 0.977; jakość 0.308 = 0.308.
- Adaptive Switching: ten sam zwycięzca w 90 % zbiorów (rozkład RBF/GP/CART: 20/28/52 vs 19/29/52).
- **GP: τ(nasze, autorów) = 0.941 < 0.95 — FAIL**; jakość 0.223 vs 0.218 (nasza nieco lepsza; kryterium jakości spełnione).
  Przyczyna: sklearn GP zamiast `pydacefit.DACE` (inna optymalizacja θ). **Do decyzji autora.**
- **Decyzja autora (2026-10-21, a): GP = `pydacefit` 1.0.1 (biblioteka autorów, Apache-2.0)**, dodane do zależności
  `implementation/lib` (+ oba `uv.lock`). Jedyna zmiana: θ jako tablica jednoelementowa (`pydacefit` woła `np.where` na
  skalarze, czego numpy ≥ 2 nie przyjmuje) — ten sam model izotropowy. Na 100 zbiorach: τ(nasze, autorów) = **1.000**
  (min 1.000), maks. różnica predykcji 1.2e-14 → **NSGANetV2: 7/7 PASS** (po decyzji).

### SH-EMOA i MO-BANANAS vs Bag of Baselines — wyniki (2026-10-21) — `test_bob_loops_vs_reference.py`

- **MO-BANANAS: PASS.** Mediana HV 86.36 vs 85.59 (+0.9 %), średnia 85.81 vs 85.77, MWU p = 0.73, TOST p = 7.6e-4.
- **SH-EMOA: na granicy.** Mediana 83.86 vs 84.81 (−1.1 %; kryterium mediany ±2 % spełnione), średnia −1.0 %,
  MWU p = 0.10, **TOST p = 0.053** (próg 0.05). Najpewniejsze źródło: adaptacja T-2 (turniej po NDS + wkład HV zamiast
  skalaru (15 − f0)·f1). **Do decyzji autora.**
- **SH-EMOA — decyzja autora (2026-10-21, a): uznane za zgodne** (kryterium mediany spełnione, TOST p = 0.053 odnotowane;
  różnica najpewniej z adaptacji T-2).

### P3-eLyMPuS — odpowiedź M. Przewoźniczka i poprawka (2026-10-21)

- Odpowiedź: mixing na ścieżce `opt_at_init 5` celowo się nie zmienia; wyniki artykułu z `P3_LSur1nth` vs `P3standard`;
  porównać z obiema referencjami (Goldman i ścieżka LS).
- Przyczyna różnicy znaleziona w `Population::get_distance` (OLyMPuS P3): para, której VIG nie zna, dostaje **+1 do
  odległości linkage** → przy pustym VIG żadna odległość nie jest 0 i `keep_zeros 0` nie wycina klastrów (stąd 6× mixing
  w `P3standard`). **Decyzja autora (a): reguła dodana do naszego P3-eLyMPuS** (E-4, `Pyramid.pair_penalty`; Z-E7:
  zależność w VIG któregokolwiek celu się liczy); `P3Canonical` bez zmian (Goldman). Poziom 1 eLyMPuS/P3/P3Net 82/82.
- Dec5 n = 50, 200 przebiegów, po poprawce (licznik jak w referencji: jeden cel, bez żądań o x w parze): mixing 1859 vs
  2180 (było 747), weryfikacja 4069 vs 4463, razem ~6937 vs 8077 (−14 %).
- **Licznik referencji (z kodu `DecompUtilsGeneral.cpp`):** nowy kontekst pary = 2 FFE (`bCreateContextForIndividual`
  wymusza ocenę bieżącego rozwiązania + ocenę z odwróconym bitem), weryfikacja = 1 FFE, odkrywanie zależności osobno.
  Tą miarą (Dec5 n = 50, 200 przebiegów, mediany): nowe pary 399 vs 686, weryfikacja 4069 vs 4463, odkrywanie zależności
  678 vs 692, mixing 1859 vs 2180; razem ~7050 vs 8077 (−13 %).
- Pozostała różnica = struktura pętli FIHC: referencja robi pełne przejścia po wszystkich zmiennych do braku zmiany
  (`dComputeFitnessOptimize_LimitedSurr_FIHC_like`), nasz FIHC — jak Goldman — kończy po n kolejnych pozycjach bez zmiany.
- **Decyzja autora (2026-10-21, b): pętla FIHC Goldmana zostaje.** P3-eLyMPuS uznany za zgodny co do mechanizmu
  (prawdziwe optima lokalne, 0 fałszywych zależności, odkrywanie zależności 678 vs 692, linkage z VIG po E-4); różnica
  −13 % FFE vs `P3_LSur1nth` opisana jako różnica pętli FIHC (nasza tańsza). Do suplementu: porównanie z oboma P3
  (Goldman `opt_at_init 1` i ścieżka LS `P3standard`), jak radzi M. Przewoźniczek. **Poziom 2 eLyMPuS — zamknięty.**

### MO-DSA (Bartnik) vs SAGOMEA — sposób i kryterium (przed testem, 2026-10-21)

- SAGOMEA (Dushatskiy et al.; SA-P3-GOMEA jednokryterialnie) z repozytorium autorów, bez zmian w kodzie, zbudowany w
  Dockerze (Python 3.6, g++, `pyrfr` 0.8.0 — obraz `p3net-sagomea:1`, Dockerfile w `tests/v005/level2/sagomea/`);
  dopisana tylko klasa celu `ConcatenatedTrap` w `fitnessFunctions.py` (jak przewiduje README). Ustawienia jak
  `run_SAGOMEA_RF_0999`: `surrogateModelRF` (pyrfr, strojony), η = 0.999, `hillClimber=0`.
- Nasz MO-DSA na zdublowanym celu (f2 = f1) = wariant jednokryterialny; RF sklearn per cel (B-1 a), γ = 0.999.
- Problem: pułapka k = 5 (tabela dec_5 OLyMPuS), n = 50, maksimum 50; budżet 500 różnych ewaluacji.
- **Kryterium:** najlepsza wartość po 500 ewaluacjach — mediana ±2 % + TOST, 100 przebiegów. Różnice modelu (pyrfr
  strojony vs RF sklearn domyślny) są częścią porównania — test sprawdza rdzeń (GOM + bramka surogatu) na poziomie wyniku.
- Z-B4 rozstrzygnięte z kodu SAGOMEA (`FOS.cpp`): NMI = 1 − D P3 — zgodne z naszą implementacją.

### MO-DSA vs SAGOMEA — wynik (2026-10-22): **FAIL**

- 100 przebiegów na stronę, trap k = 5, n = 50, 500 ewaluacji: najlepsza wartość — nasz MO-DSA mediana **37** (średnia
  37.61, zakres 34–40), SAGOMEA mediana **40** (średnia 40.09, zakres 38–44); −7.5 %, MWU p = 3e-24, TOST p = 1.0.
- Czas: MO-DSA ~36 min na przebieg (b = 500; przeuczanie RF po każdej ewaluacji + kwantyle bramki) — do testu zasobów A8.
- Różnice do sprawdzenia: bramka (Z-B1′ kwantyl per cel vs reguła SAGOMEA), warm-up 20 % budżetu, RF sklearn domyślny
  vs pyrfr strojony. **Do decyzji autora.**
- **Przyczyna częściowa — bramka (2026-10-22):** kod SAGOMEA nadpisuje percentyl progiem `currentDelta · surrogate(elitist)`
  (`PopulationGeneral::setThreshold`), więc percentyl z artykułu jest martwy. Diagnostyka: MO-DSA z `gate="elitist"`
  (opcja diagnostyczna, domyślnie Z-B1′; poziom 1 Bartnik 35/35): mediana **38** (średnia 38.03) vs 40 — różnica średnich
  zmalała z 2.48 do 2.06 pkt, nadal istotna (MWU p = 2e-18). Bramka tłumaczy ~1/5 różnicy; reszta: struktura SAGOMEA
  (populacje GOMEA `gomeaP3` vs piramida P3), warm-up 20 % budżetu, RF sklearn vs strojony pyrfr. Czas: elitist 10 min,
  Z-B1′ 36 min na przebieg (b = 500). Pytanie o bramkę dopisane do Niny (2026-10-22).
- **Decyzja autora (2026-10-22, a):** MO-DSA zostaje wg tekstu Bartnik (Z-B1′, domyślnie); poziom 2 Bartnik zamknięty jako
  **odstępstwo uzasadnione** — brak kodu autorki, SAGOMEA różni się strukturą (populacje GOMEA), bramką (kod ≠ artykuł)
  i modelem. **Limitations:** wobec SAGOMEA (jednokryterialnie, trap5 n = 50, b = 500) mediana 37 vs 40 (−7.5 %).
  Po odpowiedzi Niny: korekta bramki / warm-upu / struktury i powtórka testu. Opcja `gate="elitist"` zostaje jako
  diagnostyczna.
