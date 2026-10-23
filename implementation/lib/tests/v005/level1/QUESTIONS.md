# Pytania autora testów poziomu 1 (v005)

Runda 2 (2026-10-16): odpowiedzi w `notes/plans/v005-test-answers.md`, sygnatury w `v005-interfaces.md` §7. Przy
każdym pytaniu dopisano „Rozstrzygnięte”; nowe pytania: Q-35, Q-36 (na końcu).

Miejsca, w których karta (`notes/plans/v005-sources/*.md`) albo interfejs (`notes/plans/v005-interfaces.md`) nie
wystarczają do napisania jednoznacznego testu. Dla każdego pytania test jest napisany dla interpretacji najbliższej
karcie i (jeśli od odpowiedzi zależy wynik) oznaczony `@pytest.mark.needs_clarification("Q-xx")`. Odpowiedź autora
projektu zmienia albo interfejs, albo test — nigdy implementujący.

Legenda: **[I]** — wymaga zmiany/uzupełnienia interfejsu (propozycja sygnatury podana); **[K]** — niejasność karty;
**[S]** — sprzeczność karta–interfejs lub karta–karta; **[—]** — tylko informacja, test nie jest oznaczony.

## Wspólne

### Q-01 [—] Typ genotypu
§0 mówi „`Genotype` (krotka indeksów 0…k_i−1)”, a istniejący `p3net.problem.genotype.Genotype` to zamrożona dataclass z
polem `values`. Testy budują `Genotype(values=(…))` i porównują przez `.values` (pomocnik `vals()` akceptuje też
krotki). **Pytanie:** czy funkcje v005 przyjmują i zwracają `Genotype` (zalecane), czy gołe krotki?

**Rozstrzygnięte:** funkcje v005 przyjmują i zwracają `Genotype` (§7).
### Q-02 [I] Brak wglądu w stan wewnętrzny maszyn stanów (P3, P3Net, Bartnik)
Własności W1–W5, W14, W-K2, W-S8, W-B1–W-B6, W-B9, W-B11, W-B13 dotyczą przebiegu iteracji (wspinanie przez poziomy,
awans, bramka, przeuczanie), którego nie widać przez `propose`/`update`. Interfejs nie daje do tego żadnej sygnatury.
**Propozycja:** każda metoda-maszyna stanów przyjmuje `observer: Callable[[str, dict], None] | None = None` i wywołuje go
synchronicznie, a obiekty P3 mają atrybut `pyramid: Pyramid`. Zdarzenie dotyczące kroku jest emitowane **po**
rozstrzygnięciu kroku (czyli po jego prawdziwej ewaluacji, jeśli była). Schemat użyty w testach:

| zdarzenie | ładunek | metody |
|---|---|---|
| `iteration` | `{}` — początek iteracji P1–P6 / B3–B5 | P3*, Bartnik |
| `fihc_end` | `genotype` — wynik FIHC (P2) | P3*, P3-eLyMPuS |
| `insert` | `level`, `genotype` — udane dodanie do poziomu | P3*, Bartnik |
| `level_mix` | `level`, `before`, `after`, `before_objectives`, `after_objectives` (P3*: prawdziwe); Bartnik dodatkowo `compare: int`, `before_real`, `after_real` (albo `None`) | P3*, Bartnik |
| `cluster_step` | `level`, `cluster`, `candidate`, `current`, `changed: bool`, `accepted: bool`; Bartnik dodatkowo `gate_passed: bool`, `prediction: (f1, f2)` | P3*, Bartnik |
| `surrogate_fit` | `n_points`, `objective` (0/1) | Bartnik |
| `psa_decision` | `p_keep`, `p_revert`, `tau`, `reverted`, `appended`, `history_len` | MO-PSA |
| `stop` | `reason` | Bartnik (W-B12) |

Wywołania przekazuje się słowem kluczowym: `make(cls, space, budget, seed, observer=log)`.

**Rozstrzygnięte:** przyjęto `observer` ze schematem zdarzeń jak wyżej i atrybut `pyramid` (§7); oznaczenia zdjęte.
### Q-03 [S] Konwencja konstruktorów
§1: P3-rodzina `__init__(space, rng, *, step_evaluator=…)` (bez budżetu); §4: „Wszystkie metody:
`__init__(space, budget: int, rng, **params)`”. Testy używają §4 (budżet jest potrzebny do reguły K-2 i do rozmiarów
startowych). **Propozycja:** ujednolicić na `__init__(space, budget, rng, **params)` także w §1 (`step_evaluator` jako
parametr słownikowy).

**Rozstrzygnięte:** wszystkie metody `__init__(space, budget, rng, **params)`, `step_evaluator` słownikowo (§7).
### Q-34 [—] Kto przycina partię przekraczającą budżet
Sterownik testów (`_support.drive`) ocenia **wszystko**, co metoda zaproponuje, i nie przycina partii — metoda sama musi
nie przekroczyć budżetu (K-2: „budżet nigdy nie jest przekroczony”; metoda zna `budget` z konstruktora). Jeśli
zamierzeniem jest przycinanie po stronie `Runner`, testy `*_budget_*` trzeba złagodzić.

**Rozstrzygnięte:** metoda sama nie przekracza budżetu, `Runner` tylko asertuje — sterownik testów bez zmian.
### Q-33 [—] `online_minmax` przy min = max
Karta R-3 a / L-1 b nie mówi, co zwraca normalizacja, gdy wszystkie dotąd ocenione wartości celu są równe. Testy tego
przypadku nie sprawdzają.

**Rozstrzygnięte:** przy min = max zwracane 0.0 dla tego celu; dopisany `test_WR3_online_minmax_degenerate_objective_maps_to_zero`.
## P3 / P3Net / kanoniczne P3

### Q-04 [I] Sygnatura `accept` w `mix_with_level`
Interfejs: `accept: Callable` bez argumentów. Testy przyjmują `accept(candidate: Genotype, current: Genotype) -> bool`
(oceniacz kroku: True = zostaw zmianę). **Propozycja:** wpisać tę sygnaturę do §1.

**Rozstrzygnięte:** `accept(candidate, current) -> bool` (§7).
### Q-05 [—] `domains` w `fihc` i `FrequencyTable`
Testy przekazują listę liczności `list[int]` (jak w `FrequencyTable(domains: list[int])`).

**Rozstrzygnięte:** `domains: list[int]` (§7).
### Q-09 [K] Tryb `step_evaluator="oracle"` (W-K3)
W ask–tell metoda nie ma dostępu do funkcji celu, więc „surogat-wyrocznia” musi zamieniać każde zapytanie do surogatu
na propozycję prawdziwej ewaluacji (wtedy W-K3 = identyczna sekwencja ocenionych genotypów). Tak jest napisany test.
**Pytanie:** czy tak ma działać `oracle`, czy dostaje osobną funkcję-wyrocznię w konstruktorze?

**Rozstrzygnięte:** `oracle` zamienia każde zapytanie do surogatu na liczoną propozycję prawdziwej ewaluacji — test W-K3 bez zmian.
### Q-10 [—] W-K5 to poziom 2
„Wersja jednokryterialna przechodzi test zgodności poziomu 2 z kodem autorów” — sam test zgodności należy do innej roli.
Napisany jest tylko warunek wstępny (tryb jednokryterialny dobrze zdefiniowany: f2 stałe ≡ f2 = f1).

**Rozstrzygnięte:** informacja, bez zmian.
## Surogat P3Net

### Q-06 [—] Skala wyniku `predict_chain`
`predict_delta` — skala log (S-3); dla `predict_chain` interfejs nie mówi, czy zwraca log, czy skalę oryginalną. Testy
używają tylko porządku (Spearman), więc są niezależne od odpowiedzi.

**Rozstrzygnięte:** `predict_chain` w skali log (§7); W-S2 nie zależy od skali, W-S7 — zob. nowe Q-36.
### Q-29 [—] Znak `predict_delta`
Test W-S4 przyjmuje δ(a, b) = log f(a) − log f(b) (S-1 a: f̂(x_m) = f(x₀) − Σ δ̂(x_{i−1}, x_i)). Przy odwrotnym znaku
W-S4 nie przejdzie dla żadnego modelu.

**Rozstrzygnięte:** δ(a, b) = log f(a) − log f(b) (§7), zgodnie z testem W-S4.
### Q-07 [K] `grouped_cv_folds` — czego są indeksy
Testy przyjmują: indeksy obserwacji w `history` (podział po rozwiązaniach); każdy punkt w walidacji dokładnie raz.

**Rozstrzygnięte:** indeksy obserwacji w `history`, każdy punkt w walidacji raz (§7).
### Q-08 [I] Diagnostyka W-S7
Brak sygnatury. **Propozycja:** `P3Net.diagnostics() -> dict` z kluczem `"chain_errors"`: lista
`{"chain_length": int, "predicted": (f1, f2), "true": (f1, f2)}` dla każdej prawdziwej ewaluacji kończącej łańcuch.

**Rozstrzygnięte:** `P3Net.diagnostics()["chain_errors"]` (§7); skala pola `true` — nowe Q-36.
## Bartnik MO-DSA / MO-PSA

### Q-11 [K] Konwencja `dominance_probability`
Eq. 6.1 jest dla (dokładność ↑, energia ↓); u nas oba cele minimalizowane. Testy przyjmują: `mu_*`, `sd_*` to pary
(f1, f2) w konwencji minimalizacji, P(new ≻ old) = Φ((μ1_old − μ1_new)/s1) · Φ((μ2_old − μ2_new)/s2).

**Rozstrzygnięte:** konwencja minimalizacji jak wyżej (§7).
### Q-12 [—] Metoda kwantyla
`quantile_threshold` testowany tylko w punktach, w których wszystkie definicje kwantyla się zgadzają (statystyki
pozycyjne). Rozstrzygnąć definicję (np. `numpy.quantile`, `method="linear"`) przed poziomem 2.

**Rozstrzygnięte:** `numpy.quantile(..., method="linear")`; dopisany `test_WB10_quantile_threshold_is_numpy_linear`.
### Q-13 [I] Powód zatrzymania (W-B12)
Brak sygnatury. Test oczekuje zdarzenia `stop` z `reason` zawierającym „collapse” i `propose` zwracającego `[]` po
1000 iteracjach bez nowej ewaluacji. **Propozycja:** także atrybut `stop_reason: str | None`.

**Rozstrzygnięte:** zdarzenie `stop` + atrybut `stop_reason`; test W-B12 sprawdza oba.
## eLyMPuS

### Q-14 [K] `evaluate` i znak `partial_compare`
Testy przyjmują: w `partial_compare` i `recursive_ll` `evaluate(g) -> float` (cel danej instancji eLyMPuS); wynik
`partial_compare > 0` ⇔ x z `var := value` jest ściśle lepsze (mniejsze) od x; w `fihc_elympus` `evaluate(g) -> (f1, f2)`.
`schedule` może być dowolnym obiektem z `start_call`/`end_call` (testy podają atrapy „zawsze/nigdy weryfikuj”).

**Rozstrzygnięte:** konwencje jak wyżej (§7).
### Q-15 [K] Miara „podziałów” w W-E5
Liczby podziałów nie widać z interfejsu; test mierzy ewaluacje: ≤ 2·⌈log₂|D|⌉ + 2 (jedno porównanie = 2 ewaluacje na
podział + porównanie początkowe). **Propozycja:** `recursive_ll` zwraca też liczbę podziałów albo ją rejestruje.

**Rozstrzygnięte:** `recursive_ll` zwraca `(var, n_splits)`; test sprawdza `n_splits ≤ ⌈log₂|D|⌉` zamiast liczby ewaluacji.
### Q-19 [K] Reset licznika 1/x (W-E7, Z-E3 reguła 3)
Test przyjmuje, że po `end_call(..., repeated_optimum=True)` harmonogram zachowuje się jak świeży obiekt `OneOverX()`.
Jeśli reset zeruje tylko x, a nie licznik wywołań od ostatniej weryfikacji — doprecyzować.

**Rozstrzygnięte:** po `repeated_optimum=True` stan jak świeży `OneOverX()` (§7) — test bez zmian.
### Q-16 [K] W-E12: „ta sama trajektoria” a generator losowy
Test porównuje `fihc_elympus(..., AlwaysVerify, Random(s))` z `fihc(..., Random(s))`; zakłada, że obie funkcje zużywają
generator identycznie (ta sama permutacja zmiennych). Jeśli nie — W-E12 wymaga wstrzykniętej permutacji.

**Rozstrzygnięte:** parametr `order` w `fihc` i `fihc_elympus` (§7); W-E12 podaje ten sam `order` obu funkcjom i różne generatory.
### Q-17 [I] Dostęp do stanu P3-eLyMPuS
W-E11 i W-E13 wymagają `P3ELyMPuS.pyramid` i `P3ELyMPuS.elympus: tuple[ELyMPuS, ELyMPuS]` (brak w interfejsie).

**Rozstrzygnięte:** `P3ELyMPuS.pyramid` i `.elympus` (§7).
## Bag of Baselines

### Q-18 [K] `hv_contribution_remove` — wynik i punkt odniesienia
Test przyjmuje, że zwraca **indeks** usuwanego punktu w przekazanej liście; przykład dobrany tak, by wynik nie zależał od
punktu odniesienia (BB-3: wspólny punkt z protokołu metryk — nieznany w testach).

**Rozstrzygnięte:** zwraca indeks (§7).
### Q-20 [S] Start MOTPE: BB-4 vs library-adapters §3
Karta BoB, BB-4: MOTPE 12 / 25 / 50 (źródło 50); karta `library-adapters.md` §3: `n_startup_trials = min(10, ⌊0.25·b⌋)`
(źródło = domyślne optuny). Karta BoB odsyła do zmiany A-2 a, więc testy przyjmują wartość z `library-adapters.md`
(10 przy b ≥ 40). Potwierdzić i poprawić tabelę BB-4.

**Rozstrzygnięte:** obowiązuje `library-adapters.md`: MOTPE start = min(10, ⌊0.25·b⌋) — test bez zmian.
### Q-21 [I] Parametry MO-BANANAS
Brak sygnatury do odczytu ustawień (zespół 5, 80 epok, num_arch 8, select 4, standaryzacja). **Propozycja:**
`.config() -> dict` także dla metod spoza `library` (klucze: `ensemble_size`, `epochs`, `num_arch`, `select_models`,
`target_scaling`).

**Rozstrzygnięte:** `.config()` dla wszystkich metod, klucze jak w propozycji (§7).
### Q-22 [I] Populacja SH-EMOA i operatory
W-BB1 (stała populacja, usuwany z ostatniego frontu) wymaga atrybutu `population`; turnieju k = 3 i krzyżowania
jednorodnego p = 0.5 nie da się sprawdzić z zewnątrz (W-BB3 sprawdza tylko, że potomek jest mutacją ≤ ⌈0.38·n⌉ zmiennych
albo krzyżowaniem dwóch członków). **Propozycja:** `SHEMOA.population` oraz funkcje modułowe
`shemoa_tournament(population, k, rng)`, `uniform_crossover(p1, p2, rng)`, `shemoa_mutation(g, domains, n_mut, rng)`.

**Rozstrzygnięte:** `SHEMOA.population` + `shemoa_tournament`, `uniform_crossover`, `shemoa_mutation` (§7); dopisane testy `test_WBB3_tournament_k3`, `test_WBB3_uniform_crossover_half_from_each_parent`, `test_WBB3_mutation_redraws_n_mut_variables`.
## NSGA-Net / NSGANetV2

### Q-23 [I] Sygnatury operatorów NSGA-Net i domyślne p z pymoo 0.3.0
Interfejs podaje tylko nazwy. Testy przyjmują:
`binary_tournament(a, b, rng) -> 0 | 1` (a, b = (objectives, crowding)), `two_point_crossover(p1, p2, rng) -> (c1, c2)`,
`int_polynomial_mutation(g, domains, rng) -> g'`. Prawdopodobieństwa przyjęte jak „oczekiwane” w karcie (krzyżowanie
0.9, mutacja 1/n na zmienną) — karta każe je odczytać z pymoo 0.3.0; potwierdzić.

**Rozstrzygnięte:** sygnatury jak w propozycji; krzyżowanie dwupunktowe zawsze (p = 1.0), mutacja 1/n — W-N2 sprawdza krzyżowanie w każdej próbie.
### Q-24 [I] Populacja NSGA-Net (W-N4)
Wymaga atrybutu `NSGANet.population` (lista obserwacji po przetrwaniu).

**Rozstrzygnięte:** `NSGANet.population` (§7).
### Q-25 [I] NSGANetV2: AS i wewnętrzny NSGA-II
- `adaptive_switching` zwraca tylko (nazwa, model) — kryterium wyboru i liczby foldów (Z-V1) nie da się sprawdzić.
  **Propozycja:** `adaptive_switching(X, y, rng, return_scores=False)`; przy `True` zwraca też
  `scores: dict[str, list[float]]` (τ Kendalla na foldach).
- `inner_nsga2(...)` — brak sygnatury. Testy przyjmują
  `inner_nsga2(archive: list[Observation], predictor: Callable[[list[Genotype]], np.ndarray (N×2)], domains, rng)
  -> list[Genotype]`.
- `subset_selection` — testy akceptują maskę bool (jak kod autorów) albo listę indeksów.

**Rozstrzygnięte:** `return_scores`, sygnatura `inner_nsga2` jak w propozycji, `subset_selection` zwraca maskę bool (test akceptuje maskę).
## REINFORCE

### Q-26 [I] Wariant nagrody, logity, cel T
Testy przyjmują: `Reinforce(space, budget, rng, reward="mnasnet"|"monas"|"adc", target=…)`, atrybuty `logits` (lista
wektorów, po jednym na zmienną), `target`, `n_policy_updates`. Karta R3 i kod referencyjny (`reinforce.py`,
`ExponentialMovingAverage`) — bazowa EMA jest **z korekcją obciążenia** (licznik/mianownik), więc pierwszy krok ma
przewagę 0; test W-R2 na tym się opiera — potwierdzić, że implementujemy EMA dokładnie jak kod referencyjny.

**Rozstrzygnięte:** parametry i atrybuty jak w propozycji; EMA z korekcją obciążenia jak w NAS-Bench-201 (§7).
### Q-27 [K] ADC: front przed czy po dodaniu x; metryka ρ
Test przyjmuje front **przed** dodaniem x i odległość, przy której przykłady są jednoznaczne (punkt w odległości
0.03/0.03 — wewnątrz ε = 0.1 dla metryki euklidesowej, Czebyszewa i miejskiej). N(P_f) = liczność frontu.

**Rozstrzygnięte:** front przed dodaniem x, ρ euklidesowe w znormalizowanej przestrzeni; przykłady W-R5 przeniesione do [0, 1] i dopisany przypadek rozróżniający L2 od L1.
## RegEvo

### Q-28 [K] Typy `crowded_winner` i obserwacja populacji
Testy przyjmują: `sample`, `population` — listy `Observation`; wynik — wybrany element (`Observation`). W-RE2, W-RE5,
W-RE6 podsłuchują wywołania `crowded_winner` przez `monkeypatch` atrybutu modułu (`regevo.crowded_winner`), więc
`RegEvo` musi wołać tę funkcję przez moduł (nie przez lokalną referencję) i przekazywać aktualną populację w kolejności
wieku. **Propozycja:** zapisać to w §4.

**Rozstrzygnięte:** typy `Observation`, wołanie przez moduł, populacja w kolejności wieku (§7).
## Adaptery bibliotek

### Q-30 [I] Klucze `config()` i ziarno biblioteki
W-A1 mówi „test odczytuje obiekt biblioteki i porównuje parametry”, ale `.config()` nie ma ustalonych kluczy. Testy
przyjmują nazwy parametrów bibliotek: SMAC — `facade`, `multi_objective_algorithm`, `deterministic`, `n_trials`,
`initial_design_size`; MOEA/D — `pop_size`, `decomposition`, `prob_neighbor_mating`, `n_neighbors`, `crossover`,
`mutation`, `eliminate_duplicates`; NSGA-III — `population_size`; MOTPE — `n_ei_candidates`, `multivariate`,
`n_startup_trials`, `gamma`, `seed`; qNEHVI/qParEGO — `acquisition`, `model`, `outcome_transform`, `mc_samples`,
`pool_size`, `n_initial`, `n_models`; Vizier — `num_seed_trials`; RS — `deduplicate`. W-A5: ziarno biblioteki z
`config()["seed"]`, nazwy parametrów optuny `x0…x{n−1}`, wybory `0…k−1`. Test W-A5 dla SMAC3 nie został napisany —
wymaga znajomości przestrzeni ConfigSpace adaptera (do dopisania po ustaleniu).

**Rozstrzygnięte:** klucze `config()` jak w propozycji, SMAC3 ma `configspace`; dopisany `test_WA5_smac3_adapter_matches_native_smac_loop` — mapowanie konfiguracji na genotyp: nowe Q-35.
## Tor MF

### Q-31 [I] Brak protokołu ask–tell dla wierności
`Method.propose` zwraca tylko genotypy; tor MF potrzebuje (genotyp, epoki). Brak też: skąd metoda zna E, formatu
`bracket_schedule`, funkcji promocji i ekstrapolacji f2. Testy przyjmują:
`propose(state) -> list[tuple[Genotype, int]]`, odpowiedź `Observation` w tej samej kolejności,
`final_observations() -> list[Observation]` (tylko e = E), `bracket_schedule(eta, r_min, R) -> list[list[tuple[n, r]]]`
(nawiasy od s_max w dół, szczeble rosnąco; r zaokrąglane do najbliższej liczby całkowitej — zgodnie z drabinami MF-3),
`promote_nsga2(points, k) -> list[int]`, `extrapolate_f2(f2_at_e, e, E) -> float`. Konstruktory MF: `(space, budget, rng)`
— brakuje E (do dodania, np. `max_epochs`).

**Rozstrzygnięte:** protokół MF jak w propozycji, konstruktor z `max_epochs` (§7); testy podają `max_epochs=27`.
## Benchmarki

### Q-32 [I] Konstruktory substratów i tablica energii
Testy W-BM1–W-BM5, W-BM7 wymagają danych (`benchmark_data`) i nieustalonego API: konstruktory
`NASBench201Substrate()` itd. bez argumentów, `Substrate.f1_split()`, `p3net.v005.benchmarks.NB201Energy` z
`__len__`, `metadata()` (klucze `gpu_model`, `driver`, `cuda`, `torch`, `n_warmup`, `n_samples`, `aggregate`,
`quality_control`) i `energy(g)`; plik wyniku BM-3 w `results/checks/*jahs*size*`; pola zasobów w rekordach przebiegów
`resources.{peak_memory_server_mb, peak_memory_gpu_mb, surrogate_load_seconds, method_wall_seconds}`. Interfejs §5
podaje tylko nazwy `NB201Energy` i `f1_split()`. Uwaga: przestrzeń JAHS w testach W-BM6 to
`search_spaces.nas_genotype.nas_search_space()` (10 zmiennych, zgodnie z kartą P3Net §2a).

**Rozstrzygnięte:** API jak w propozycji + metadane `power_limit_w`, `clocks_locked`, `energy_method`, `batch_size`, `temperature_log`; W-BM2 sprawdza nowe klucze.

## Nowe pytania (runda 2)

### Q-35 [I] Mapowanie konfiguracji SMAC3 na genotyp (W-A5)
`config()["configspace"]` daje przestrzeń, ale nie mówi, jak hiperparametr odpowiada współrzędnej genotypu. Test
`test_WA5_smac3_adapter_matches_native_smac_loop` (oznaczony `needs_clarification("Q-35")`) przyjmuje to samo co dla
optuny: współrzędna i ↔ hiperparametr kategoryczny `x{i}` z wyborami `0…k_i−1` (liczby całkowite). **Propozycja:**
zapisać to w §7; ewentualnie dodać `config()["genotype_of"]: Callable[[Configuration], Genotype]`.

**Rozstrzygnięte** (akceptacja autora projektu, „kontynuuj”): przyjęto propozycję — `x{i}`, wybory `0…k_i−1`;
oznaczenie zdjęte. Do dopisania w `v005-interfaces.md` §7 (poza uprawnieniami autora testów).

### Q-36 [K] Skala pola `true` w `diagnostics()["chain_errors"]`
`predicted` jest w skali log (Q-06), a dla `true` skala nie jest ustalona. Test W-S7 akceptował obie skale; warto ustalić, żeby diagnostyka W-S7 liczyła błąd w jednej skali
(zalecane: log, jak `predicted`).

**Rozstrzygnięte** (akceptacja autora projektu, „kontynuuj”): `true` w skali log; W-S7 sprawdza tylko skalę log. Do
dopisania w `v005-interfaces.md` §7 (poza uprawnieniami autora testów).

## Runda 3 — pytania implementującego (`notes/plans/v005-implementer-questions.md`, 2026-10-18)

### Q-37 — W2/W3 dla P3Net przy b = 300
Wycofane przez implementującego (po ustaleniu kolejności wartości w FIHC testy przechodzą). **Rozstrzygnięte:** bez
zmian w testach.

### Q-38 — W-R2: wartość pierwszego kroku Adama
Implementujący ma rację: kod referencyjny (`reinforce.py`, NAS-Bench-201) woła `optimizer.step()` w każdym kroku, także
przy przewadze 0, więc licznik kroków Adama rośnie, a pierwszy niezerowy krok ma korekcję obciążenia dla t > 1 (0.372
przy t = 2, nie lr). **Rozstrzygnięte:** test oczekuje teraz |Δ| = lr·(0.1/(1 − 0.9ᵗ))/√(0.001/(1 − 0.999ᵗ)) dla każdego
logitu, gdzie t = numer kroku z pierwszą zmianą polityki (kroki z przewagą 0 też liczą się do t).

### Q-39 — REINFORCE kończy się przed budżetem
Implementujący ma rację co do karty: W-R8 mówi tylko „budżet nigdy nie przekroczony”, a K-2 dopuszcza zakończenie
wcześniej; zatrzymanie przy zbieżności polityki przewiduje #36. Test miał wymóg mocniejszy niż karta. **Rozstrzygnięte:**
W-R7 i W-R8 sprawdzają ≤ b bez duplikatów, a gdy przebieg kończy się przed b — że `stop_reason` zawiera „collapse” i
`propose` zwraca `[]`. Wymaga dopisania `Reinforce.stop_reason: str | None` do §7 (nowe Q-42). Uwaga do #36: reguła
implementacji („10 000 kolejnych duplikatów”) nie jest regułą #36 („< 20 % unikalnych w oknie 20”) — to sprawa
asercji poziomu 4, nie tego testu.

### Q-40 — W-A5 MOTPE: `n_startup_trials` w pętli natywnej
Błąd testu: pętla natywna miała na sztywno 10, a karta (§3) daje min(10, ⌊0.25·b⌋) = 7 przy b = 30. **Rozstrzygnięte:**
pętla natywna bierze `m.config()["n_startup_trials"]`; dodatkowo test sprawdza, że to 7.

### Q-41 — W-B5 po zmianie karty (Z-B1 → Z-B1′)
Test pisany pod Z-B1, które karta zastąpiła. **Rozstrzygnięte:** W-B5 przepisany na Z-B1′ — prawdziwa ewaluacja ⇔ na obu
celach predykcja < (1 − α)-kwantyl (numpy linear) predykcji bieżącego modelu dla wszystkich rozwiązań ocenionych
naprawdę; test sprawdza też wartości progów i że bramka choć raz przepuszcza. Wymaga ładunku `cluster_step`
`alpha`, `thresholds: (t1, t2)`, `reference_predictions: list[(p1, p2)]` w §7 (nowe Q-42).

### Q-42 [I] Uzupełnienia §7 wynikające z rundy 3
1. `Reinforce.stop_reason: str | None` (zawiera „collapse”, gdy przebieg zatrzymała reguła #36); po zatrzymaniu
   `propose` zwraca `[]`.
2. MO-DSA, zdarzenie `cluster_step`: dodatkowo `alpha: float`, `thresholds: (float, float)`,
   `reference_predictions: list[(float, float)]` (predykcje bieżącego modelu dla rozwiązań ocenionych naprawdę, w
   kolejności ewaluacji).
Testy W-R7, W-R8 i W-B5 już tego wymagają; do zatwierdzenia przez autora projektu i dopisania do
`v005-interfaces.md` §7.

## Runda 4 — zmiany kart po testach poziomu 2 (`v005-implementer-questions.md`, „Runda 4”, 2026-10-20/21)

### Q-43 — MO-BOHB: initial design (BB-4, wiersz MO-BOHB)
**Rozstrzygnięte:** dopisane `test_WBB7_mobohb_initial_design_at_max_fidelity` (pierwsza partia = min(num_initial_samples,
⌊0.25·b⌋) różnych konfiguracji, wszystkie przy e = E; b = 50/100/350/1000 oraz num_initial_samples = 20) i
`test_WBB7_mobohb_num_initial_samples_default` (domyślnie 50). Protokół MF wg §7 (Q-31), `max_epochs` = 27.

### Q-44 — RegEvo: wybór zmiennej do mutacji (O-RE3 z 2026-10-20, Z-RE1)
**Rozstrzygnięte:** dopisane trzy testy rozkładu (chi-kwadrat, p > 0.001, ≥ 900 mutacji): NB201 — krawędź do węzła j z
prawdopodobieństwem 1/(3j) (mapowanie współrzędna → węzeł odczytane z `genotype_to_arch_str`), a rozkład jednostajny
musi zostać odrzucony; JAHS — każda z 4 zmiennych HP 1/7, krawędzie komórki łącznie 3/7; przestrzeń bez komórki —
jednostajnie. Pary (rodzic, potomek) odczytane z podsłuchu `crowded_winner` (Q-28); liczone tylko mutacje rodziców bez
krawędzi `none`, żeby odrzucanie niepoprawnych komórek nie zniekształcało rozkładu. Sprawdzone na makietach: reguła
„węzeł → krawędź” przechodzi, jednostajny wybór zmiennej pada na NB201 i JAHS.

### Q-45 — P3-eLyMPuS: linkage z karą za nieznaną parę (E-4, Z-E7)
**Rozstrzygnięte częściowo:** dopisane testy `test_E4_*` (ręczne wartości D z karą +1; przy pustym VIG reguła D = 0 nic
nie usuwa, po dodaniu zależności znów działa; para znana, gdy jest w VIG któregokolwiek celu; kanoniczne P3 bez zmian),
ale interfejs nie ma sygnatury — nowe Q-46.

### Q-46 [I] Sygnatura linkage z VIG (E-4)
Karta E-4 nie mówi, przez jaką funkcję przechodzi kara, a §1 ma tylko `cluster_distance(table, ci, cj)` i
`build_clusters(table, rng)`. Testy `test_E4_*` (oznaczone `needs_clarification("Q-46")`) przyjmują:
`cluster_distance(table, ci, cj, known: Callable[[int, int], bool] | None = None)`,
`build_clusters(table, rng, known=None)` (odległość pary = entropijna + 1, gdy `not known(a, b)`; `known=None` =
kanoniczne P3) oraz `p3net.v005.elympus.vig_known(elympus_pair) -> Callable[[int, int], bool]` (Z-E7). **Propozycja:**
dopisać do §7; jeśli implementacja ma inną sygnaturę — podać ją, testy dostosuję.

**Rozstrzygnięte** (`v005-test-answers.md`, runda 4; interfejs, uzupełnienie 2026-10-21): sygnatura przyjęta bez zmian;
oznaczenia zdjęte. Dopisany `test_E4_p3_elympus_pyramid_uses_vig_known` (`Pyramid.known` P3-eLyMPuS = `vig_known` obu
VIG, czytane na bieżąco; kanoniczne P3 bez `known`).

### Q-47 [K] W-BM3: N_samples po pilotażach
Karta `benchmarks.md` (pilotaż 4, „Ustawienia końcowe”) daje 3 przejścia rozgrzewające + 5 mierzonych, mediana — test
oczekuje teraz `n_samples == 5`. **Rozstrzygnięte** w teście; do poprawy w karcie: tabela własności (W-BM3) i §BM-2
(„N_samples = 3”) nadal mówią 3. Ustawienia dodane po pilotażach (zegar 1200 MHz, korekta dryfu komórką odniesienia co
5 architektur, ponowny pomiar przy rozrzucie > 8 %, ≤ 2 razy) nie mają kluczy metadanych w §7, więc test ich nie sprawdza
— jeśli mają być sprawdzane, potrzebne klucze (np. `clock_mhz`, `reference_cell`, `reference_every`,
`remeasure_threshold`, `max_remeasures`).

**Rozstrzygnięte** (runda 4): karta poprawiona (N_samples = 5); W-BM3 sprawdza też `clocks_locked` = True,
`clock_lock_mhz` = 1200, `reference_arch` = `arch_str` komórki (3, 2, 1, 4, 3, 2) (z `genotype_to_arch_str`),
`ref_every` = 5, `max_spread` = 0.08, `max_retries` = 2.

### W-BM4 / W-BM7 — ścieżka wyników
**Rozstrzygnięte:** wynik BM-3 szukany w `implementation/experiments/results/checks/`; rekordy przebiegów (W-BM7) w
`implementation/experiments/results/` (ta sama pomyłka w ścieżce).

## Runda 5 (2026-10-23)

### Q-48 — NSGANetV2: Adaptive Switching przy małym N (karta `nsganetv2.md`, Z-V2)
**Rozstrzygnięte:** dopisane `test_WV2_too_few_points_cart_wins` (N = 3, 6, 10 przy d = 10: zwycięzcą jest CART, bez
wyjątku) i `test_WV2_small_initial_design_propose_does_not_raise` (b = 20, N_doe = 5 ≤ d: przebieg zużywa dokładnie b).
W `test_WV2_selection_criterion_and_fold_count` przypadek N = 9 (foldy uczące po 6 < d + 1 = 7 punktów — pod Z-V2 RBF i
GP się nie kwalifikują) zastąpiony N = 15, żeby test kryterium mean(τ) − std(τ) dotyczył sytuacji, w której wszystkie
trzy modele są kandydatami. Uwaga (bez oznaczenia, nie blokuje): Z-V2 nie mówi, jak model niekwalifikujący się występuje
w `scores` przy `return_scores=True` (pominięty / NaN) — testy tego nie sprawdzają.

## Runda 6 (2026-10-23) — testy benchmarków uruchomione z danymi

### Q-49a — W-BM4: genotyp z indeksami zamiast wartości
Błąd testu: substraty przyjmują genotyp z **wartościami** domen (jak `sample_uniform`), a test budował `G(*g)` z
indeksów i losował indeksy HP. **Rozstrzygnięte:** test przekazuje `Genotype(values=tuple(g))` i losuje HP z
`space.domains[i].values`. Pozostałe testy substratów (W-BM1, W-BM2, W-BM5) już przekazują genotyp z `sample_uniform`;
W-BM6 woła `is_valid` z v005, które przyjmuje genotyp z indeksami (Q-01).

### Q-49b — W-BM7: schemat rekordu przebiegu
**Rozstrzygnięte częściowo:** glob → `implementation/experiments/results/runs/*/raw/v005_*.json`; pola w
`rec["resources"]`; zawsze niepuste `method_wall_seconds` i `peak_memory_process_mb`; `peak_memory_gpu_mb` musi być
zapisane, może być `None` (brak GPU na serwerze docelowym). Na JAHS niepuste `peak_memory_server_mb` **oraz
`surrogate_load_seconds`** — tu test zostaje przy karcie, nie przy propozycji (Q-50).

### Q-50 [K] Czas ładowania surogatu JAHS (#29, BM-5)
Propozycja implementującego dopuszcza `surrogate_load_seconds = None`, bo „czasu ładowania surogatu nie mierzymy
osobno”. Karta tego nie dopuszcza: #29 wymienia „brak czasu ładowania mostu” jako błąd v004 kategorii N (naprawiamy), a
BM-5 każe rejestrować czas ładowania surogatu z asercją niepustych pól. Chodzi o most/surogat JAHS (`jahsbench`), więc
test wymaga tego pola na JAHS (na innych przestrzeniach może być `None`). Jeśli decyzja projektu ma być inna — zmienić
#29 / BM-5, wtedy test dostosuję. Założenie do potwierdzenia: przestrzeń przebiegu rozpoznawana po polu `rec["space"]`
(jeśli go brak — po nazwie pliku), JAHS ⇔ nazwa zawiera „jahs”.

**Rozstrzygnięte** (`v005-test-answers.md`, runda 6/7): `surrogate_load_seconds` na JAHS jest mierzone i wymagane —
0.0 jest poprawne (most załadowany wcześniej przez inny przebieg); test traktuje jako puste tylko brak, `None`, `""`
i `[]` (guard `test_WBM7_zero_is_not_an_empty_resource_field`). Przestrzeń z `rec["search_space"]`, JAHS ⇔ nazwa
zaczyna się od `jahs` (fallback na nazwę pliku usunięty). `NB201Energy.energy(g)` przyjmuje wartości albo indeksy —
W-BM2 bez zmian.

