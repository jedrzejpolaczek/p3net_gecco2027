# v005 — pytania implementującego do autora testów (runda 3)

Status: **OTWARTE** (2026-10-18). Testy poziomu 1 zmienia tylko autor testów (protokół §1); poniżej przypadki, w których
test i karta / kod referencyjny / decyzja projektu dają różne wyniki. Implementacja trzyma się karty i źródła.

| Q | Test | Co się dzieje | Propozycja |
|---|---|---|---|
| Q-37 (WYCOFANE 2026-10-18: po ustaleniu kolejności wartości w FIHC testy przechodzą) | `test_p3net.py::test_W2_*[P3Net]`, `test_W3_*[P3Net]` (budżet 300) | Przy b = 300 na pułapce 3×3×3 także **kanoniczne P3** zwykle nie buduje drugiego poziomu (2/3 seedów: jeden poziom; pomiar 2026-10-18); przy b = 600 obie metody mają 2–3 poziomy. Własności W2/W3 nie zależą od surogatu — test sprawdza budżet, nie mechanizm | Budżet P3Net w W2/W3 = 600 (lub ten sam co dla kanonicznego); albo `pytest.skip`, gdy run nie zbudował drugiego poziomu |
| Q-38 | `test_reinforce.py::test_WR2_*` | Implementacja referencyjna (PyTorch Adam w `reinforce.py` NAS-Bench-201) wywołuje `optimizer.step()` także w pierwszym kroku z przewagą 0 → licznik kroków Adama t = 1, a pierwszy niezerowy krok (t = 2) przesuwa logit o 0.372·lr, nie o lr (korekcja obciążenia). Test zakłada 0.5 | Oczekiwać |Δ| = lr · (0.1/0.19)/√(0.001/0.001999) ≈ 0.372 (zgodnie z referencją), albo równych |Δ| dla wszystkich logitów bez konkretnej wartości |
| Q-40 | `test_library_adapters.py::test_WA5_motpe_adapter_matches_native_optuna_loop` | Test buduje natywną pętlę z `n_startup_trials=10` przy b = 30, a karta (`library-adapters.md` §3) i test W-A1 tej samej karty wymagają min(10, ⌊0.25·b⌋) = 7. Przy tych samych ustawieniach adapter = pętla natywna (sprawdzone: b = 30 → 7, b = 40 → 10, sekwencje identyczne) | W natywnej pętli `n_startup_trials=m.config()["n_startup_trials"]` (jak `seed`) |
| Q-41 | `test_bartnik.py::test_WB5_dsa_real_evaluation_iff_gate_passes` | Karta Bartnik zmieniona 2026-10-18 (decyzja autora): **Z-B1 → Z-B1′** (bramka MO-DSA = Alg. 8 osobno dla każdego celu: predykcja lepsza na obu celach niż (1 − α)-kwantyl predykcji rozwiązań ocenionych naprawdę). Pod Z-B1 MO-DSA kończył się po rozgrzewce (W-B13: 10/50) | Przepisać W-B5 na Z-B1′ (zdarzenie `cluster_step` może nieść `alpha` i progi, jeśli potrzebne — do uzgodnienia w §7) |
| Q-39 | `test_reinforce.py::test_WR7_duplicates_free_and_budget`, `test_WR8_*[50-mnasnet]`, `[50-monas]` | Przy lr = 0.5 (Z-R1) polityka zbiega w kilkudziesięciu krokach do jednej architektury; dalej losuje wyłącznie duplikaty. Implementacja przerywa po 10 000 kolejnych duplikatów — przebieg kończy się przed budżetem (24/50; 6/8 na przestrzeni 9-elementowej). Decyzja projektu #36 (ExplorationCollapse) przewiduje takie zatrzymanie | Dla REINFORCE `exact=False` + asercja, że zatrzymanie ma powód „exploration collapse” (atrybut `stop_reason`), albo test na przestrzeni / ziarnach bez zbieżności |

## Rozstrzygnięcia rundy 3 (2026-10-18, autor testów)

Q-38, Q-39, Q-40 — testy poprawione zgodnie z propozycjami; Q-41 — W-B5 przepisany na Z-B1′; Q-37 wycofane.
Q-42 (nowe, od autora testów): `Reinforce.stop_reason` i pola bramki MO-DSA w `cluster_step` — dopisane do
`v005-interfaces.md` §7 i do kodu. Uwaga autora testów: reguła zatrzymania REINFORCE w implementacji (10 000 kolejnych
duplikatów) to zabezpieczenie metody; reguła #36 (ExplorationCollapse: < 20 % unikalnych w oknie 20) działa na poziomie
harnessu (asercja poziomu 4) — do sprawdzenia przy integracji (poziom 3).

## Runda 4 (2026-10-20) — zmiana karty `bag-of-baselines.md` (BB-4), do testu poziomu 1

- **Q-43 (MO-BOHB, initial design).** Karta BB-4 dostała wiersz MO-BOHB: pierwsza iteracja to min(50, ⌊0.25·b⌋) losowych
  konfiguracji ocenionych na max budżecie E (kod autorów: `get_MOBOHB(init=True)`, `num_initial_samples`), potem
  brackety Hyperbanda. Proszę o test poziomu 1 (W-BB-nowy): pierwsza partia propozycji MO-BOHB = min(50, ⌊0.25·b⌋)
  różnych konfiguracji, wszystkie z fidelity E. Konstruktor ma nowy parametr `num_initial_samples` (domyślnie 50).
- **Przy okazji (benchmarki):** W-BM3 oczekuje N_samples = 3 (karta po pilotażach: 5); W-BM4 szuka `results/checks`
  w katalogu głównym repo (wynik BM-3 jest w `implementation/experiments/results/checks/`).
- **Q-44 (RegEvo, mutacja — zmiana karty O-RE3, 2026-10-20).** Wybór zmiennej jak w `R_EA.py`: w przestrzeni komórkowej
  węzeł jednostajnie, potem jego krawędź (krawędzie (0,1): 1/3; (0,2), (1,2): po 1/6; (0,3), (1,3), (2,3): po 1/9);
  zmienne spoza komórki — każda osobną jednostką (Z-RE1); bez komórki — jednostajnie. Proszę o test poziomu 1 rozkładu
  (np. chi-kwadrat na NB201 z rodzicem, którego każda zmiana jest poprawna).
- **Q-45 (P3-eLyMPuS, linkage — zmiana karty E-4, 2026-10-21).** Odległość linkage pary (a, b) w piramidzie P3-eLyMPuS =
  odległość entropijna + 1, gdy b ∉ VIG(a) w żadnym z dwóch eLyMPuS (Z-E7); kanoniczne P3 bez zmian. Proszę o test
  poziomu 1 (np. przy pustym VIG żaden klaster nie jest odrzucany przez regułę D = 0; dla pary z zależnością odległość
  bez kary).
- **Q-48 (NSGANetV2, Adaptive Switching — Z-V2, 2026-10-23).** Model, którego nie da się dopasować w którymś foldzie, nie
  może wygrać AS (wcześniej dostawał τ = 0 za ten fold). Proszę o test poziomu 1: przy N ≤ d (RBF/GP nie do dopasowania)
  zwycięzcą jest CART i `propose` nie rzuca wyjątku.

## Runda 6 (2026-10-23) — testy benchmarków uruchomione z danymi (`P3NET_BENCHMARK_DATA`)

- **Q-49a (W-BM4).** Test buduje genotyp przez `G(*g)` (indeksy) z wartości `space.sample_uniform(...)`, które dla JAHS są
  nazwami operacji i wartościami HP → `ValueError: invalid literal for int() ... 'nor_conv_3x3'`. Substrat przyjmuje
  genotyp z **wartościami** (jak `sample_uniform`); proszę przekazywać `Genotype(values=tuple(g))` zamiast `G(*g)`, a
  przy zmianie HP losować wartość z `space.domains[i].values`, nie indeks.
- **Q-49b (W-BM7).** Rekord przebiegu v005 ma teraz pola na najwyższym poziomie `resources.{peak_memory_server_mb,
  peak_memory_gpu_mb, surrogate_load_seconds, method_wall_seconds}` (+ `peak_memory_process_mb`). Nie wszystkie mają
  sens w każdym przebiegu: serwer JAHS jest tylko na JAHS, GPU nie ma na serwerze docelowym, a czasu ładowania surogatu
  nie mierzymy osobno (jest w czasie ściany). Propozycja: wymagać niepustych `method_wall_seconds` i
  `peak_memory_process_mb` zawsze, `peak_memory_server_mb` tylko dla przestrzeni JAHS, a `peak_memory_gpu_mb` i
  `surrogate_load_seconds` dopuścić jako `None`. Dodatkowo glob `v005*/**/*.json` nie znajdzie rekordów pipeline'u
  (`results/runs/<commit>/raw/v005_*.json`) — proponuję `results/runs/*/raw/v005_*.json`.
- Do wiadomości: W-BM1 (NB201) i W-BM2/W-BM3 padają, bo nie ma jeszcze tablicy energii (pomiar na końcu etapu A) —
  oczekiwane; W-BM5 (NAS-HPO-II, FCNet) przechodzi po wdrożeniu MF-1 a w substratach.
