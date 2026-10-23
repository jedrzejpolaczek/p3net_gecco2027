# v005 — odpowiedzi na pytania autora testów poziomu 1

Status: **ZATWIERDZONE** (2026-10-16): autor projektu przyjął propozycje autora testów; decyzje techniczne (Q-06, Q-12, Q-16, Q-20, Q-23, Q-27, Q-33, Q-34) podjęte przez agenta implementującego na podstawie kart i kodu referencyjnego.
Pytania: `implementation/lib/tests/v005/level1/QUESTIONS.md` (34 pozycje). Po zatwierdzeniu: (1) zmiany sygnatur trafiają do
`v005-interfaces.md` (wersja 2), (2) sesja autora testów zdejmuje `needs_clarification` / poprawia testy wg tej listy.
Implementujący niczego tu nie zmienia.

Skrót: **P** = przyjąć propozycję autora testów bez zmian.

| Q | Odpowiedź |
|---|---|
| Q-01 | Funkcje v005 przyjmują i zwracają `Genotype` (dataclass z `values`) |
| Q-02 | **P** — `observer: Callable[[str, dict], None] \| None = None`, schemat zdarzeń z Q-02; atrybut `pyramid` |
| Q-03 | **P** — wszystkie metody `__init__(space, budget, rng, **params)`; `step_evaluator` jako parametr słownikowy |
| Q-04 | **P** — `accept(candidate, current) -> bool` |
| Q-05 | **P** — `domains: list[int]` (liczności) |
| Q-06 | `predict_chain` zwraca skalę log (jak `predict_delta`); reguła D-1 porównuje w skali log z log(prawdziwe) archiwum |
| Q-07 | **P** — indeksy obserwacji w `history`; każdy punkt w walidacji dokładnie raz |
| Q-08 | **P** — `P3Net.diagnostics()["chain_errors"]` |
| Q-09 | **P** — `oracle`: każde zapytanie do surogatu staje się propozycją prawdziwej ewaluacji (liczonej do budżetu) |
| Q-10 | Informacja — bez zmian |
| Q-11 | **P** — konwencja minimalizacji: P = Φ((μ1_old − μ1_new)/s1)·Φ((μ2_old − μ2_new)/s2) |
| Q-12 | Kwantyl: `numpy.quantile(..., method="linear")` (domyślny numpy) |
| Q-13 | **P** — zdarzenie `stop` + atrybut `stop_reason: str \| None` |
| Q-14 | **P** — znaki i `evaluate` jak w Q-14 |
| Q-15 | **P** — `recursive_ll` zwraca `(var_found \| None, n_splits)` |
| Q-16 | Dodać parametr `order: list[int] \| None = None` do `fihc` i `fihc_elympus` (wstrzyknięta permutacja); W-E12 porównuje przy tym samym `order` |
| Q-17 | **P** — `P3ELyMPuS.pyramid`, `P3ELyMPuS.elympus` |
| Q-18 | **P** — zwraca indeks |
| Q-19 | **P** — po `repeated_optimum=True` harmonogram jak świeży `OneOverX()` (kod: oba liczniki zerowane) |
| Q-20 | Obowiązuje `library-adapters.md` (MOTPE `n_startup_trials = min(10, ⌊0.25·b⌋)`); poprawić tabelę BB-4 w karcie BoB (wiersz MOTPE → odsyłacz, wiersz EHVI → qNEHVI wg `library-adapters.md`) |
| Q-21 | **P** — `.config()` dla wszystkich metod |
| Q-22 | **P** — `SHEMOA.population` + funkcje modułowe |
| Q-23 | **P** dla sygnatur. Prawdopodobieństwa **odczytane z pymoo 0.3.0**: krzyżowanie dwupunktowe **zawsze (p = 1.0)** — `PointCrossover` nie ma parametru p; mutacja 1/n na zmienną, `np.rint`, naprawa do zakresu. Karta NSGA-Net poprawiona. Test W-N2: p = 1.0 |
| Q-24 | **P** — `NSGANet.population` |
| Q-25 | **P** — `adaptive_switching(..., return_scores=False)`, sygnatura `inner_nsga2` z Q-25; `subset_selection` zwraca maskę bool (jak kod autorów) |
| Q-26 | **P** — parametry i atrybuty z Q-26; bazowa EMA **z korekcją obciążenia** dokładnie jak `ExponentialMovingAverage` w kodzie NAS-Bench-201 |
| Q-27 | Front **przed** dodaniem x (Alg. 2: nagroda w l. 6, aktualizacja frontu w l. 7–17); ρ — odległość **euklidesowa** w znormalizowanej przestrzeni celów (artykuł dopuszcza L1 lub L2) |
| Q-28 | **P** — typy `Observation`; wołanie przez moduł; populacja w kolejności wieku |
| Q-29 | **P** — δ(a, b) = log f(a) − log f(b) |
| Q-30 | **P** — klucze `config()` z Q-30; SMAC3 W-A5 dopisać po ustaleniu przestrzeni ConfigSpace (`config()["configspace"]`) |
| Q-31 | **P** — protokół MF: `propose -> list[tuple[Genotype, int]]`, `final_observations()`, `bracket_schedule`, `promote_nsga2`, `extrapolate_f2`; konstruktor MF z `max_epochs` |
| Q-32 | **P** + metadane `NB201Energy` uzupełnić o pola z BM-2 (laptop): `power_limit_w`, `clocks_locked`, `energy_method` (`"counter"` / `"power_integral"`), `batch_size`, `temperature_log` |
| Q-33 | `online_minmax` przy min = max zwraca 0.0 dla tego celu |
| Q-34 | Metoda sama nie przekracza budżetu (zna `budget`); `Runner` dodatkowo **asertuje** (nie przycina) |

## Do zatwierdzenia

Cała tabela; w szczególności decyzje własne (nie „P”): Q-06, Q-12, Q-16, Q-20, Q-23 (p = 1.0), Q-27, Q-33, Q-34.

## Runda 2 (2026-10-17)

| Q | Odpowiedź |
|---|---|
| Q-35 | Adapter SMAC3: współrzędna i ↔ `x{i}`, wybory `0…k_i−1` (przyjęte) |
| Q-36 | `chain_errors[*]["true"]` w skali log (przyjęte) |

Stan testów poziomu 1 po rundzie 2: 292 zebrane, ruff czysty, `needs_clarification` = 0 — **gotowe dla implementującego**.

## Runda 4 (2026-10-21)

- **Q-46:** przyjęta Twoja sygnatura — `cluster_distance(table, ci, cj, known=None)`, `build_clusters(table, rng, known=None)`,
  `p3net.v005.elympus.vig_known(elympus_pair)`; dopisane do `v005-interfaces.md` (uzupełnienie 2026-10-21). Zdejmij
  `needs_clarification("Q-46")`.
- **Q-47:** karta `benchmarks.md` poprawiona (W-BM3 i §BM-2: N_samples = 5 u nas; 3 to wartość ze źródła Bartnik). Klucze
  metadanych dla ustawień po pilotażach są (§7): `clocks_locked`, `clock_lock_mhz`, `reference_arch`, `ref_every`,
  `max_spread`, `max_retries` — proszę o test W-BM3 sprawdzający ich wartości (True, 1200, `arch_str` komórki (3, 2, 1, 4, 3, 2), 5, 0.08, 2).

## Runda 5 (2026-10-23)

- **Z-V2, `return_scores=True`:** model niekwalifikujący się zostaje w `scores` z wartością **0.0** za każdy fold, którego
  nie dało się dopasować (lista ma zawsze tyle pozycji, ile foldów); o wykluczeniu decyduje osobno kryterium wyboru
  (−∞ dla modelu z nieudanym foldem). Dopisane do karty `nsganetv2.md` (Z-V2). Test nie jest wymagany.

## Runda 6 (2026-10-23)

- **W-BM7, `surrogate_load_seconds` na JAHS:** przyjęte (#29, BM-5). Pole jest teraz mierzone: czas zapytań, które
  uruchomiły most JAHS albo były pierwszym zapytaniem instancji substratu (start mostu, ładowanie zbioru, czekanie na
  blokadę), liczony w obrębie przebiegu — **0.0, gdy most był już załadowany** (wspólny most w pipeline), `None` na
  przestrzeniach bez mostu. Test może wymagać wartości ≠ None na JAHS (0.0 jest poprawne).
- **Q-50:** rekord ma klucz `search_space` (nazwa configu przestrzeni, np. `jahs_bench_201_v005`), nie `space`; JAHS =
  nazwa zaczyna się od `jahs`. Nazwa pliku: `<method>__<search_space>__budget<b>__seed<s>.json`.
- **`NB201Energy.energy(g)`:** przyjmuje genotyp z **wartościami albo indeksami** (`arch_str` rozpoznaje nazwy operacji
  i indeksy do `OPS`); dopisane do `v005-interfaces.md`.
