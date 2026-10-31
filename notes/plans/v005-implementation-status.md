# v005 — stan implementacji `p3net.v005`

Aktualizacja: 2026-10-18. Kod: `implementation/lib/src/p3net/v005/`. Testy poziomu 1:
`implementation/lib/tests/v005/level1/` (optuna/smac/botorch/vizier — w `experiments/.venv`).
Pytania do autora testów: `v005-implementer-questions.md` (runda 3).

| Moduł | Karta | Testy poziomu 1 |
|---|---|---|
| `common.py`, `stepper.py` | wspólne | (w testach kart) |
| `p3/` (linkage, fihc, mixing, pyramid, engine), `methods.py` | p3net, p3-canonical | 55/55 |
| `surrogates/pairwise.py` | p3net-surrogate | 14/14 |
| `bartnik.py` | bartnik | 35/35 |
| `elympus.py` | elympus | 27/27 |
| `baselines/regevo.py`, `baselines/mo_ls.py` | regevo, mo-ls | 18/18 |
| `baselines/reinforce.py` | reinforce | komplet (po rundzie 3) |
| `baselines/nsga_net.py` | nsga-net | 7/7 |
| `baselines/nsganetv2.py` | nsganetv2 | 11/11 |
| `baselines/bob.py` (SHEMOA, MOBANANAS), `mf.py` (Hyperband, ASHA) | bag-of-baselines, mf-track | 49/49 (+ W-BB4/5 w `experiments/.venv`) |
| `baselines/library.py` | library-adapters | 34/34 (`experiments/.venv`); W-A5 SMAC3 i MOTPE zgodne z natywnymi pętlami |
| `mf.py`: SHEMOAMF, MOBOHB, MOSHBANANAS | bag-of-baselines BB-5, mf-track | gotowe (2026-10-18); W-BB8 + przebiegi kontrolne (budżet zużyty, front tylko z e = E) |
| `benchmarks.py` + substraty (NB201 f1 walidacyjne i f2 = energia; JAHS f2 = liczba parametrów; `f1_split()`) | benchmarks | kod gotowy (2026-10-18; runner v004 zachowuje stare ustawienia jawnie, testy v004 27/27); brak tablicy energii |

**Pełny przebieg poziomu 1 (2026-10-18, `experiments/.venv`): 285 passed, 0 failed, 7 skipped** (testy `benchmark_data` — dane w `data/cache`, tablica energii jeszcze niezbudowana; do uruchomienia z `P3NET_BENCHMARK_DATA` po pomiarze energii).

## Uwagi implementacyjne (do kart / artykułu)

- FIHC: wartości zmiennej w rosnącej kolejności (źródło nie podaje; wymaga tego W-E12).
- Surogat P3Net: ≤ 3000 losowych uporządkowanych par do treningu; RF z domyślnymi hiperparametrami; cele uczenia
  zaokrąglone do 1e-9 (bez tego szum 1e-16 zmienia wybór równorzędnych podziałów i łamie niezmienniczość skali, W-S5);
  predykcja przez własne przejście po drzewach (wartości identyczne ze sklearn, ~60× szybciej).
- Bartnik: **Z-B1′** zamiast Z-B1 (decyzja 2026-10-18); siatka B-4 b w `bartnik.GRID`; drzewo powiązań = odległość
  entropijna P3 (Z-B4 — sprawdzić z kodem SAGOMEA); bramka PSA = max prawdopodobieństwa dominacji po archiwum.
- REINFORCE: Z-R3 C = 5; T (MnasNet) z konfiguracji eksperymentu, w braku — mediana f2 dotychczasowych ocen.
- NSGANetV2: GP = pydacefit (biblioteka autorów, 2026-10-21); RBF = odpowiednik scipy (rankingi identyczne z pySOT na poziomie 2).
- MOEA/D: własna implementacja pętli pymoo 0.6.2 (operatory kategoryczne nie dają się podpiąć bez obchodzenia pymoo).
- MO-BANANAS: predyktor (MLP n→10→2, Adam 0.1, 80 epok, zespół 5) przeniesiony do numpy (w środowisku biblioteki
  nie ma PyTorcha).

## Koszty (do testu zasobów A8)

- NSGANetV2: b = 100 ≈ 17 min na przebieg (CART 5000 drzew × 10 foldów × 2 cele na iterację, jak w kodzie autorów);
  przy b = 350 — kilka godzin.
- MO-DSA: b = 100 ≈ 2.5 min (przeuczanie po każdej ewaluacji + kwantyle bramki).
- P3Net: b = 300 ≈ 15–30 s.

## Do zgłoszenia autorowi testów przy etapie benchmarków

W-BM3 oczekuje N_samples = 3 (karta po pilotażach: 5); W-BM4 szuka `results/checks` w katalogu głównym repo (wynik BM-3
jest w `implementation/experiments/results/checks/`).

## Port MF metod BoB (2026-10-18) — co jest wierne kodowi, a co trzeba opisać

- SH-EMOA MF: `get_budgets(ceil(0.2 E), E, 2, fe, pop)`; liczba ewaluacji `fe` = największa, której planowany koszt
  (z wznawianiem treningu populacji przy przejściu na wyższy budżet) mieści się w budżecie — zużycie 84–90 % budżetu.
- MO-SH-BANANAS: SH po `select` kandydatach na drabinie `get_budgets(ceil(0.2 E), E, 3)` rosnąco, zostaje len // 3;
  ocalali trafiają do listy architektur (jak w kodzie: tylko ocalali, z wartością przy E).
- MO-BOHB: initial design min(50, ⌊0.25 b⌋) konfiguracji na E (`init=True`, dodane 2026-10-20); harmonogram hpbandster (η = 2), promocja SH jak w kodzie (całe fronty NDS, ostatni włączany w całości —
  bez HSSP z artykułu), generator MOTPE z `mobohb_utils` (zmienne całkowite jak `as_uniform_space()`; pygmo → 2-D HV).
  **Wierne przeniesienie błędu kodu:** dolna granica całki w jądrze dyskretnym to `x + 0.5 q` (zamiast `x − 0.5 q`), więc
  stosunek wiarygodności TPE jest prawie stały — próbkowanie modelowe niewiele różni się od losowego. Do Limitations /
  suplementu (zgodnie z zasadą „jak w kodzie autorów”); alternatywnie decyzja o poprawce.

## Poziom 3 — integracja (2026-10-22/23)

Harness: `experiments/methods/v005_adapter.py` (indeksy ↔ wartości genotypu; protokół MF partie ↔ pojedyncze zapytania),
`run_experiment.build_method(..., budget=)` + diagnostyka `v005` w wynikach, 27 configów `configs/methods/v005_*.yaml`
(metody i configi v004 bez zmian). Skrypt: `experiments/scripts/run_level3_v005.py` → `results/level3_v005/summary.json`.

27 metod × 9 przestrzeni × b ∈ {50, 350}, 1 seed, limit 30 min/przebieg (laptop, 8 procesów naraz): **476 przebiegów —
407 PASS, 11 PASS-COLLAPSE, 55 TIMEOUT, 3 ERROR, 0 FAIL** (żadnego złego zużycia budżetu).
- ERROR: 2 × JAHS b = 350 (`XGBoostError: bad allocation` — dwa mosty JAHS naraz przekroczyły RAM) — powtórzone pojedynczo;
  qNEHVI NAS-HPO-II b = 350 (proces padł bez wyniku) — powtórzone z widocznym błędem.
- TIMEOUT (do testu zasobów A8): NSGANetV2 10 (w tym JAHS b = 50), Vizier 10 (w tym NB201 b = 50), MO-DSA 9 (w tym JAHS
  b = 50), qNEHVI 8, qParEGO 8, ASHA 8 (wszystkie b = 350), MO-PSA 2 (FCNet-naval b = 50, JAHS b = 50).
- PASS-COLLAPSE: **wyłącznie REINFORCE** (#36, 10 000 kolejnych duplikatów): zużywa 38 (NB201), 49 (NAS-HPO-II),
  71–88 (FCNet, JAHS) z 350 ewaluacji — polityka (Adam lr 0.5) zbiega, a duplikaty nie kosztują budżetu (#35). Do decyzji.
- Powtórki ERROR (2026-10-23): P3 kanoniczne i MOTPE na JAHS b = 350 — PASS pojedynczo (517 s, 536 s; przyczyna: RAM przy
  dwóch mostach); qNEHVI NAS-HPO-II b = 350 — przebieg kompletny (350 ewaluacji) w 74 min, bez limitu czasu → TIMEOUT
  według limitu 30 min (A8); pierwotny „brak pliku wyniku” = najpewniej zasoby przy 8 procesach naraz.
  **Wynik końcowy poziomu 3: 0 błędów metod, 0 FAIL.**
- REINFORCE: decyzja autora (2026-10-23, a) — bez zmian; opis w `v005-sources/reinforce.md` („Poziom 3”) i Limitations.

## Poziom 4 — kontrole w trakcie przebiegu (2026-10-23)

`experiments/measurement/v005_checks.py`, liczone w `run_single` dla każdej metody v005, zapisywane w diagnostyce
(`level4`): budżet (K-2), powód wcześniejszego zatrzymania (#36), initial design ≤ ⌊0.25·b⌋ (BB-4), f2 tylko z prawdziwych
ewaluacji (#6: `analytic_cost_queries == 0`), udział kroków mixingu P3Net ocenianych surogatem w (0, 1) (S-6; n/d bez
mixingu), pola zasobów (A8). Adapter liczy zdarzenia metod przyjmujących `observer`; `config()`/`diagnostics()`
zapisywane jako JSON (obiekty bibliotek → repr — wcześniej MOTPE/SMAC3 by się nie zapisały). Testy harnessu 34/34.

**Obserwacja do interpretacji (B):** P3Net, NAS-HPO-II, b = 350: 7 iteracji, 6 FIHC zużywa ~340 ewaluacji, mixing to
42 kroki (36 przez surogat, 6 prawdziwych). NB201 b = 350: 24 kroki mixingu, udział surogatu 0.58. Przy budżetach ≤ 350
surogat P3Net dotyka małej części przebiegu — FIHC dominuje budżet.

## Bramka `checks` (2026-10-23)

`scripts/run_pipeline.py`, etap `checks`: testy (lib + experiments), determinizm (każda metoda 2× ten sam seed,
NAS-HPO-II b = 20), **poziom 4 na tych przebiegach**, **karty zatwierdzone i każde zdanie w `v005-claims.md` z testem**
(`cards: true`); błąd czegokolwiek blokuje siatkę. Plan `configs/pipeline/v005.yaml` (SZKIC do prerejestracji: siatki
główna / eLyMPuS / MF, seedy 61–90 — 28 560 przebiegów; skala do ustalenia po A8).
Próba determinizmu + poziomu 4 dla 27 metod: **27/27 identyczne, 27/27 poziom 4 OK** (po poprawce Z-V2 w NSGANetV2 —
wcześniej wyjątek przy b = 20). Bramka blokuje dziś tylko brak `v005-claims.md` (zgodnie z zamierzeniem).

## Cele v005 w przestrzeniach + A8 (2026-10-23)

- **Znalezione:** runner domyślnie daje NB201 i JAHS cele v004 (NB201: test + FLOPs, JAHS: `size_MB`), a configi przestrzeni
  nie ustawiały źródeł → poziom 3 na NB201/JAHS szedł na celach v004. Poprawka bez ruszania v004: configi
  `nas_bench_201_v005.yaml` (f1 valid, f2 energia) i `jahs_bench_201*_v005.yaml` (f2 = liczba parametrów); plany v005
  i `run_level3_v005.py` używają tylko ich. Powtórka poziomu 3 na `jahs_bench_201_v005` (27 metod, b = 50) — w toku;
  NB201 z energią — po zbudowaniu tablicy energii (bramka `checks`).
- **A8:** plan `configs/pipeline/v005-resources.yaml` (476 punktów, b ∈ {100, 350}, seed 61; NB201 z FLOPs tylko do
  pomiaru czasu), podsumowanie `scripts/summarize_resources_v005.py` (czas, RSS, wykładnik t ∝ b^k, prognoza
  roboczogodzin siatki), runbook `notes/plans/v005-a8-runbook.md`.

## Poprawki po testach benchmarków z danymi (2026-10-23)

- **MF-1 a wdrożone w substratach:** NAS-HPO-II i FCNet przy e < E epok dają f2 = czas zaobserwowany do epoki e
  (`training_seconds`); wcześniej czas całego treningu (v004). Domyślnie v005; runner przypina v004 (`f2_at_fidelity:
  full`), configi `nas_hpo_bench_ii_v005.yaml`, `fcnet_*_v005.yaml` ustawiają `observed`; testy v004 przypięte jawnie.
  Wszystkie configi v005 (przestrzenie i metody) mają `default_grid: false` (poza domyślną siatką v004). Testy
  experiments 367/367 (+ 2 pominięte), W-BM5 PASS; MF na configach v005: 26/28 PASS przy 30 min limicie.
- **Rekord przebiegu v005:** pola `resources.{peak_memory_server_mb, peak_memory_gpu_mb, surrogate_load_seconds,
  method_wall_seconds, peak_memory_process_mb}` na najwyższym poziomie (interfejs §7); pytanie o W-BM4/W-BM7 — Q-49.
- **ASHA — wydajność:** promocja przeliczała ogólny niezdominowany sort O(n²) przy każdym zapytaniu (dolny szczebel
  FCNet: tysiące konfiguracji) → sort dwukryterialny przez przemiatanie (`mf._fronts_2d`, te same fronty — sprawdzone na
  3000 losowych zbiorach z remisami; kolejność w obrębie frontu wg indeksu). ASHA b = 350: FCNet > 30 min → 285 s,
  NAS-HPO-II → 13 s. Poziom 1 MF 24/24.

## A9 — poprawki kodu raportującego A1–A6 (2026-10-24)

- **A1:** `stats/significance.py` — dwustronny Mann–Whitney U (próby niezależne, różne liczności dozwolone) zamiast
  sparowanego Wilcoxona; `reporting/tables.py` porównuje wszystkie przebiegi każdego ramienia (nie tylko wspólne seedy);
  docstringi, podpis tabel i skrypt izolacji NB201 poprawione; testy (`test_significance.py`, regresja zakresu Holma)
  przepisane na MWU.
- **A2:** `render_results_tex.py` — „--” przy braku porównania (`adj_p`/`effect` = None), n z danych, rozmiar rodziny
  Holma per budżet w podpisie, gdy się różni.
- **A3:** `render_results_narrative.py` — referencja z danych (`reference_method`), liczności zawsze z kierunkiem,
  wszystkie istotne wyniki (bez top-4), rodziny metod i zbiory ramion jako argumenty, budżety z danych.
- **A4:** tabela „vs random search” — kolumny „istotnie lepsze” / „istotnie gorsze” (`rejection_counts`).
- **A5:** `scripts/cost_table_v004.py` → `results/tables/cost_s9.md` (s9: 128 punktów, komplet); adnotacja: ramiona GP
  mają koszt w s9, ale brak wyników jakości przy b = 200/350; pamięć mostu JAHS w v004 nie zapisana (n/r).
- **A6:** `scripts/freeze_fronts_v004.py` — fronty best-known JAHS (s1, s3, s7 + GP z gp-small) i NB201 (s5) wyłącznie
  z seedów 1–30, punkt odniesienia = nadir tych punktów; zapis w `results/reference_fronts/` i
  `results/tables/reference_front_provenance.md`. Wynik: JAHS 3660 przebiegów (fronty 85 / 25 / 29 punktów; CRC, FMN),
  NB201 540 przebiegów (front 15); punkty odniesienia w tabeli.
Testy raportowania 72/72.

## A8 — przebieg na Hetznerze (2026-10-24/25, run root `ec1ba9cb`)

- `resources_main` + `resources_mf` (6 workerów): 457/458 po ~20 h. Jedyny brak: `v005_qparego` JAHS C10 b=350.
- **OOM:** 5 zabitych procesów (14:49–18:58, 9–16 GB RSS każdy). Przy 6 workerach qNEHVI/qParEGO b=350 na JAHS + most
  JAHS (~12 GB) nie mieszczą się w 30 GB (swap 8 GB); zabity most zrywa połączenie obu ramion GP. qNEHVI przeszedł za 3.
  próbą (5745 s), qParEGO wyczerpał 3 próby. Zabite próby liczone od zera, w wynikach tylko udana. Zgodne z decyzją A8
  „bez GP przy b ≥ 200”.
- Powtórka qParEGO osobno (1 worker), potem Vizier (1 worker, `--max-retries 1`); OOM Viziera przy b=350 też jest wynikiem.
- Most JAHS przeładowywał zbiory (np. fashion_mnist 2×) — workery rozłożone na różne zbiory; koszt przeładowań wliczony w czas
  przebiegów, do uwzględnienia w prognozie siatki.
- Po commicie `e6734ccd9` (tylko skrypt statusu, `bootstrap_env.sh`, runbook — kod metod bez zmian) powtórka qParEGO
  trafiła do nowego run rootu `e6734ccd`. Z niego bierzemy tylko brakujący punkt (qParEGO JAHS C10 b=350, 1 worker) i
  Viziera; `summarize_resources_v005.py` przyjmuje kilka run rootów (pierwszy ma pierwszeństwo).
- **Vizier:** w `e6734ccd` gotowe NB201 i NHB (b=100 i 350; ~30 GB RSS już przy b=100 na NB201). JAHS C10 b=350 zabijany
  przez OOM przez ~24 h (worker restartowany od zera, bez wpisu w `failures.jsonl`, więc `--max-retries` nie działa)
  aż do wyczerpania restartów → wynik A8: Vizier b=350 na JAHS nie mieści się w 30 GB. Reszta (JAHS ×3 b=100, FCNet ×4
  b=100/350, 11 punktów) w osobnym planie `configs/pipeline/v005-resources-vizier-rest.yaml`; CRC/FMN b=350 pominięte.
- **2026-10-29/30:** analiza A8 → `v005-a8-analysis.md`. Posthoc JAHS na danych v004 (serwer) przerwany decyzją autora
  2026-10-30 na 2 776 / 28 080 plikach (tempo 3 pliki/min ≈ 5.5 dnia); kopia częściowa w `results/runs/b4d25cac/posthoc/`;
  brak posthocu JAHS = odchylenie v004.
- **2026-10-29:** pilotaż energii 5 niezaliczony, pomiar na laptopie zarzucony (`benchmarks.md` BM-2); sprawdzenie
  HW-NAS-Bench → `v005-hwnasbench-check.md`; decyzja = P1 w `v005-todo.md`.
- **2026-10-31:** P1 = a. `benchmarks.py::build_energy_table_hwnasbench`, `scripts/build_nb201_energy_table.py`,
  pobieranie w `scripts/download_data.py --only hw_nas_bench` (sha256) → `results/benchmark_tables/nb201_energy.json`
  (15 625, mJ/obraz, Jetson TX2, 0 rozbieżności indeksów z NATS). Testy z `P3NET_BENCHMARK_DATA`: 10 passed, 3 failed
  (W-BM2, W-BM3 — stary protokół laptopa, runda 8; W-BM7 — poprawka P3 (2a)).
- **2026-10-31:** runda 8 autora testów: `test_benchmarks.py` z danymi 13 passed, 1 skipped (test pamięci przebiegu — tylko
  Linux); W-BM7 padał na rekordach A8 sprzed poprawki → rekordy A8 przeniesione do `results/a8/` (decyzja autora).
