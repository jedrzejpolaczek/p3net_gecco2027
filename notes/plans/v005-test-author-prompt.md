# Prompt dla niezależnej sesji: autor testów poziomu 1 (v005)

Użycie: otwórz **nową** sesję Claude Code w katalogu repozytorium i wklej wszystko poniżej linii.
Po zakończeniu sesji przejrzyj `implementation/lib/tests/v005/level1/QUESTIONS.md` i `COVERAGE.md`.

---

Jesteś **niezależnym autorem testów** w projekcie badawczym (artykuł GECCO'27: P3 z surogatem do łącznego NAS + HPO).
Twoja rola wynika z protokołu `notes/plans/v005-verification-protocol.md` (przeczytaj §1, §3, §7): piszesz **testy
poziomu 1** — testy własności wynikających ze źródeł metod — **zanim powstanie implementacja**. Implementujący nie może
potem zmieniać Twoich testów. Celem jest, żeby kod, testy i tekst artykułu nie wynikały z tej samej niesprawdzonej
intencji.

## Co wolno czytać

1. `notes/plans/v005-verification-protocol.md`
2. `notes/plans/v005-interfaces.md` — **jedyne źródło sygnatur**; importuj dokładnie te nazwy i moduły.
3. Karty źródeł `notes/plans/v005-sources/*.md` (wszystkie 14): p3net, p3net-surrogate, p3-canonical,
   bartnik-mo-sa-p3-gomea, elympus, bag-of-baselines, nsga-net, nsganetv2, reinforce, regevo, mo-ls, library-adapters,
   mf-track, benchmarks.
4. `notes/plans/v005-decisions.md` (rejestr decyzji; przy sprzeczności obowiązuje karta).
5. Publikacje i kod referencyjny wskazane w kartach (PDF-y w `notes/articles/`, repozytoria z linków) — **tylko
   po to, żeby sprawdzić, co mówi źródło**, gdy karta odsyła do konkretnego miejsca.
6. Istniejące moduły wymienione w `v005-interfaces.md` §0 — **tylko ich sygnatury i docstringi**, nie logikę.

## Czego NIE wolno czytać ani uruchamiać

- Kodu w `implementation/lib/src/p3net/` poza sygnaturami z §0, w szczególności `p3net/v005/` (jeśli powstanie),
  `methods/`, `search_engines/`, `surrogates/`.
- Kodu w `implementation/experiments/methods/`, `implementation/experiments-*/`, istniejących testów
  `implementation/lib/tests/*.py` i `implementation/experiments/tests/` (to testy v004 — nie wzoruj się na nich).
- Raportów `notes/analysis-v004/` i archiwum `notes/archive/` (opisują błędy v004; nie są specyfikacją).
- Nie modyfikuj **niczego** poza katalogiem `implementation/lib/tests/v005/level1/`. Nie commituj.

## Co masz napisać

Katalog `implementation/lib/tests/v005/level1/`:

- Jeden plik na kartę: `test_<karta>.py` (np. `test_p3net.py`, `test_p3net_surrogate.py`, `test_bartnik.py`, …).
- **Każda własność z tabel „Własności do sprawdzenia testami”** w każdej karcie (W1–W16, W-S1–W-S10, W-K1–W-K5,
  W-B1–W-B13, W-E1–W-E13 + W-E7b, W-BB1–W-BB8, W-N1–W-N6, W-V1–W-V6, W-R1–W-R8, W-RE1–W-RE6, W-L1–W-L5, W-A1–W-A6,
  W-MF1–W-MF7, W-BM1–W-BM7) ma **co najmniej jeden test**. Nazwa testu zaczyna się od ID, np.
  `test_W11_donor_differs_on_cluster`, docstring cytuje własność i krok źródła (np. „P21–P23, Goldman & Punch 2014 s. 787”).
- Test musi **nie przejść, gdyby własność była fałszywa** (protokół §4). Unikaj testów, które przechodzą dla każdej
  implementacji (np. tylko „zwraca listę”).
- Małe problemy o znanej odpowiedzi: pułapki k-arne (`p3net.problem.synthetic_kary`), ręcznie policzone przykłady
  (np. Eq. 1 P3, Eq. 6.1 Bartnik, Eq. 3 ADC, wzór MnasNet), sztuczne funkcje celu z licznikiem wywołań, by sprawdzać
  liczbę ewaluacji i to, czy surogat nie woła benchmarku.
- Testy deterministyczne (stałe ziarna), bez sieci, bez GPU, bez benchmarków na dysku; każdy plik < ~30 s.
  Testy wymagające danych benchmarków (W-BM*) oznacz `@pytest.mark.benchmark_data` i pomijaj, gdy danych brak.
- Testy statystyczne (np. W16: „≥ 8/10 przebiegów”) — tak jak w karcie, z ustalonymi ziarnami.
- `COVERAGE.md`: tabela `ID własności | karta | test(y)` — każda własność z każdej karty, bez wyjątków.
- `QUESTIONS.md`: każde miejsce, gdzie karta lub interfejs nie wystarcza do napisania jednoznacznego testu (brak
  sygnatury, niejasna własność, sprzeczność karta–interfejs). **Nie zgaduj** — zapisz pytanie, napisz test dla
  interpretacji najbliższej karcie i oznacz go `@pytest.mark.needs_clarification` z odnośnikiem do pytania.
- `conftest.py` z markerami (`benchmark_data`, `needs_clarification`) i ewentualnymi fikstrami (sztuczne przestrzenie,
  liczniki ewaluacji).

Na tym etapie **wszystkie testy będą padać** (brak modułów `p3net.v005`) — to oczekiwane. Sprawdź tylko, że pliki się
parsują: `python -m pytest implementation/lib/tests/v005/level1 --collect-only -q` (błędy importu modułów v005 są
w porządku; błędy składni — nie).

## Nie pisz

Testów poziomu 2 (zgodność z kodem referencyjnym), 3 (integracja) ani 5 (kontrola po przebiegu) — to inne role.

## Na koniec

Krótkie podsumowanie po polsku: liczba testów na kartę, liczba pytań w `QUESTIONS.md`, własności, których nie dało się
przetestować bez zmiany interfejsu (z propozycją zmiany sygnatury).

---

# Runda 2 — po odpowiedziach (wklej do **tej samej** sesji autora testów)

Odpowiedzi na Twoje pytania są w `notes/plans/v005-test-answers.md`, a zmiany sygnatur w `notes/plans/v005-interfaces.md`
§7 (wersja 2; przy sprzeczności obowiązuje §7). Zasady jak w rundzie 1 (te same zakazy czytania i zapisu).

1. Dla każdego testu oznaczonego `needs_clarification("Q-xx")`: dostosuj test do odpowiedzi i **zdejmij oznaczenie**.
   Szczególnie: Q-16 (W-E12 z parametrem `order`), Q-23 (W-N2: krzyżowanie zawsze, p = 1.0), Q-27 (front przed
   dodaniem x, odległość euklidesowa), Q-12 (`numpy.quantile`, `method="linear"`), Q-33 (min = max → 0.0), Q-20 (MOTPE
   start = min(10, ⌊0.25·b⌋)), Q-15 (`recursive_ll` zwraca `(var, n_splits)` — sprawdzaj `n_splits ≤ ⌈log₂|D|⌉`).
2. Dopisz test W-A5 dla SMAC3 (przestrzeń z `config()["configspace"]`).
3. Q-33 — dopisz test przypadku min = max.
4. Uzupełnij W-BM2 o nowe klucze metadanych `NB201Energy` (§7, Benchmarki).
5. W `QUESTIONS.md` przy każdym pytaniu dopisz „Rozstrzygnięte: …” (jednym zdaniem) albo nowe pytanie, jeśli odpowiedź
   rodzi kolejną niejasność. Zaktualizuj `COVERAGE.md`.
6. Sprawdź: `--collect-only` bez błędów składni; `ruff` czysty; liczba testów z `needs_clarification` = 0 (albo lista
   nowych pytań).

Na koniec krótkie podsumowanie po polsku: co zmieniłeś, ile nowych pytań.

---

# Runda 3 — pytania implementującego (wklej do **tej samej** sesji autora testów)

Implementacja `p3net.v005` jest gotowa (poza MF-wersjami metod BoB i benchmarkami). Kilka testów nie zgadza się z kartą,
kodem referencyjnym albo decyzją projektu — lista z uzasadnieniem i propozycjami: `notes/plans/v005-implementer-questions.md`
(Q-38, Q-39, Q-40, Q-41; Q-37 wycofane). Zmieniła się też karta Bartnik (Z-B1 → Z-B1′, `v005-sources/bartnik-mo-sa-p3-gomea.md` N-1).

Zasady jak wcześniej (nie czytasz `p3net/v005`). Dla każdego Q: popraw test zgodnie z kartą/źródłem albo uzasadnij w
`QUESTIONS.md`, dlaczego test ma rację. Zaktualizuj `COVERAGE.md`. Na koniec krótko po polsku: co zmieniłeś.

---

# Runda 4 — zmiany kart po testach zgodności z kodem autorów (wklej do **tej samej** sesji autora testów)

Testy poziomu 2 (porównanie z kodem autorów) zmieniły trzy karty i wykryły dwie rozbieżności w Twoich testach
benchmarków. Szczegóły: `notes/plans/v005-implementer-questions.md`, sekcja „Runda 4” (Q-43, Q-44, Q-45, W-BM3, W-BM4).

Zmienione karty (przeczytaj zmienione punkty):
- `v005-sources/bag-of-baselines.md`, BB-4 — nowy wiersz MO-BOHB: initial design min(50, ⌊0.25·b⌋) konfiguracji na max
  fidelity E, potem brackety Hyperbanda; konstruktor `MOBOHB(..., num_initial_samples=50)` (Q-43).
- `v005-sources/regevo.md`, O-RE3 + Z-RE1 — mutacja „węzeł → krawędź” jak w `R_EA.py` (Q-44).
- `v005-sources/elympus.md`, E-4 + Z-E7 — w P3-eLyMPuS odległość linkage pary +1, gdy żaden z dwóch VIG nie zna
  zależności; kanoniczne P3 bez zmian (Q-45).

Zasady jak wcześniej (nie czytasz `p3net/v005`). Zadania:
1. Dopisz testy poziomu 1 dla Q-43, Q-44, Q-45 (propozycje w `v005-implementer-questions.md`).
2. W-BM3: karta `benchmarks.md` po pilotażach mówi N_samples = 5 — dostosuj test albo uzasadnij w `QUESTIONS.md`.
3. W-BM4: wynik BM-3 jest w `implementation/experiments/results/checks/` — popraw ścieżkę.
4. Zaktualizuj `COVERAGE.md` i `QUESTIONS.md`; `--collect-only` bez błędów, `ruff` czysty.

Na koniec krótko po polsku: co zmieniłeś, czy są nowe pytania.

---

# Runda 5 — odpowiedzi na Q-46, Q-47 i nowe Q-48 (wklej do **tej samej** sesji autora testów)

Odpowiedzi: `notes/plans/v005-test-answers.md`, sekcja „Runda 4”; sygnatury: `v005-interfaces.md`, uzupełnienie 2026-10-21.

1. **Q-46** — Twoja sygnatura przyjęta bez zmian: `cluster_distance(table, ci, cj, known=None)`,
   `build_clusters(table, rng, known=None)`, `p3net.v005.elympus.vig_known(elympus_pair)`. Zdejmij
   `needs_clarification("Q-46")` z testów `test_E4_*`.
2. **Q-47** — karta `benchmarks.md` poprawiona (N_samples = 5). Klucze metadanych dla ustawień po pilotażach:
   `clocks_locked` (True), `clock_lock_mhz` (1200), `reference_arch` (`arch_str` komórki (3, 2, 1, 4, 3, 2)),
   `ref_every` (5), `max_spread` (0.08), `max_retries` (2). Dopisz je do testu W-BM3.
3. **Q-48** (nowe, karta `nsganetv2.md`, Z-V2) — w Adaptive Switching model, którego nie da się dopasować w którymś
   foldzie (RBF/GP przy mniej niż d + 1 punktach), nie może zostać zwycięzcą. Dopisz test poziomu 1: przy N ≤ d
   zwycięzcą jest CART, a `propose` nie rzuca wyjątku.

Zasady jak wcześniej (nie czytasz `p3net/v005`). Zaktualizuj `QUESTIONS.md` i `COVERAGE.md`; `--collect-only` bez
błędów, `ruff` czysty. Na koniec krótko po polsku: co zmieniłeś, czy są nowe pytania.

---

# Runda 6 — testy benchmarków uruchomione z danymi (wklej do **tej samej** sesji autora testów)

Implementujący uruchomił `test_benchmarks.py` z `P3NET_BENCHMARK_DATA`. Dwa testy mają problem po stronie testu —
szczegóły i propozycje: `notes/plans/v005-implementer-questions.md`, sekcja „Runda 6” (Q-49a, Q-49b).

1. **Q-49a (W-BM4):** test buduje genotyp przez `G(*g)` (indeksy) z wartości `space.sample_uniform(...)`, które dla JAHS
   są nazwami operacji i wartościami HP — `ValueError`. Substrat przyjmuje genotyp z **wartościami**: przekazuj
   `Genotype(values=tuple(g))`, a przy zmianie HP losuj wartość z `space.domains[i].values`.
2. **Q-49b (W-BM7):** rekord przebiegu v005 ma pola na najwyższym poziomie `resources.{peak_memory_server_mb,
   peak_memory_gpu_mb, surrogate_load_seconds, method_wall_seconds, peak_memory_process_mb}`. Wymagaj niepustych
   `method_wall_seconds` i `peak_memory_process_mb` zawsze, `peak_memory_server_mb` tylko dla przestrzeni JAHS;
   `peak_memory_gpu_mb` i `surrogate_load_seconds` mogą być `None`. Rekordy pipeline'u leżą w
   `implementation/experiments/results/runs/*/raw/v005_*.json` — popraw glob.

Do wiadomości (nie zmieniaj): W-BM1 (NB201), W-BM2, W-BM3 padają, bo tablica energii NB201 jeszcze nie istnieje
(pomiar na końcu etapu A); W-BM5 przechodzi po wdrożeniu MF-1 a w substratach.

Zasady jak wcześniej (nie czytasz `p3net/v005`). Zaktualizuj `QUESTIONS.md` i `COVERAGE.md`; `--collect-only` bez
błędów, `ruff` czysty. Na koniec krótko po polsku: co zmieniłeś, czy są nowe pytania.

---

# Runda 7 — odpowiedzi na W-BM7 / Q-50 (wklej do **tej samej** sesji autora testów)

Odpowiedzi: `notes/plans/v005-test-answers.md`, sekcja „Runda 6”.
1. `surrogate_load_seconds` na JAHS jest teraz mierzone — wymaganie niepustego pola zostaje; **0.0 jest poprawne**
   (most załadowany wcześniej przez inny przebieg). Upewnij się, że test nie odrzuca 0.0.
2. **Q-50:** przestrzeń bierz z `rec["search_space"]` (np. `jahs_bench_201_v005`); JAHS = nazwa zaczyna się od `jahs`.
3. `NB201Energy.energy(g)` przyjmuje wartości albo indeksy (`v005-interfaces.md`) — W-BM2 z wartościami jest poprawny.

Zasady jak wcześniej. Na koniec krótko po polsku: co zmieniłeś.
