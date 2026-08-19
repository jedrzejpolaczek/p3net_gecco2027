# Plan: `experiments-bartnik` — Bartnik's winning algorithm class vs. the same P3Net baseline set

## Cel

Uruchomić najbliższy odpowiednik algorytmu, którym Bartnik dowiodła sukcesu na architecture-only
NAS-Bench-201 (`bartnik2026evolutionary`), wewnątrz tego samego harnessu, na tym samym search space
(`nas_bench_201`, już zaimplementowany), porównując go do **tych samych baseline'ów co P3Net**
(`random_search`, `sh_emoa`, `tpe`, `mo_bohb`, `nsga_net`, `nsganetv2`, `p3_alone`, `p3_absolute`) — nie do
jej własnych `MO-LS`/`MO-P3-GOMEA`. To jest bezpośredni test diagnostyczny hipotezy (i)-(ii) z
`conclusions.tex`: czy problem leży w silniku/surogacie P3Net, czy w samym benchmarku (iii).

## Zweryfikowany stan reużywalności (na podstawie przeglądu `implementation/`)

- **`implementation/lib`** (`p3net` package) jest już świadomie zaprojektowany jako niezależna biblioteka,
  współdzielona z `experiments/` przez lokalną zależność (`README.md` wprost mówi o docelowym rozdzieleniu na
  osobne repo). Nowy projekt korzysta z niej identycznie jak `experiments/`.
- **Reużywalne 1:1, bez zmian:**
  - `search_spaces/nas_bench_201_genotype.py`, `substrates/nas_bench_201.py`, `configs/search_spaces/nas_bench_201.yaml`
    (architektura, FLOPs jako f2, pojedynczy poziom fideliów — te same, udokumentowane odstępstwa od Bartnik co
    w izolacyjnym eksperymencie P3Net).
  - Wszystkie `methods/*.yaml` + `methods/*.py` oprócz `p3net`/`p3_absolute` (te dwa zostają jako punkt
    odniesienia, nie kopiowane).
  - `stats/significance.py` (Wilcoxon + Holm + Cliff's delta), `reporting/_common.py`,
    `reporting/tables.py`, `p3net.metrics.hypervolume`/`igd_plus` z biblioteki.
  - `p3net.problem.genotype` (`SearchSpace`, `Genotype`, `CategoricalDomain`), `p3net.problem.objectives`
    (dominacja, `pareto_front`), `p3net.harness.runner.Runner`/`EvaluationCache`/`Method` protocol.
  - `p3net.search_engines.p3.linkage_tree` i `.optimal_mixing` — **potwierdzone jako już
    populacja-agnostyczne** (operują na przekazanej `population: list[Genotype]`, nie na `Pyramid`), więc
    nadają się do reużycia w nowym silniku bez modyfikacji.
- **Nowy kod, jeden moduł**: silnik klasy SA-P3-GOMEA (Dushatskiy 2021 + rozszerzenie MO Bartnik), jako nowa
  klasa metody implementująca wyłącznie `propose`/`update` (Protocol z `harness/runner.py`) — **żadnych zmian
  w `Runner`/`Substrate`/rejestrach** poza dopisaniem jednego if-branch w `run_experiment.py::build_method`
  i jednego pliku `configs/methods/*.yaml`.

## Kluczowa decyzja projektowa: który wariant Bartnik odtworzyć

Jej praca ma 4+ warianty (deterministyczny/probabilistyczny × joint/per-objective, ×z/bez online selection).
Replikacja wszystkich = nieproporcjonalny nakład. Rekomendacja: **jeden reprezentatywny, dobrze uzasadniony
wariant**, nie cała siatka:

- **Silnik populacji**: kanoniczny, pojedynczy-osobnik-wspina-piramidę P3 (Goldman 2014, Algorithm 3) + FIHC
  (Algorithm 4) + GOM (Algorithm 2) — **nie** batch-bootstrap `Pyramid` tego projektu. To jest właśnie różnica,
  którą chcemy izolować (hipoteza (i)). Wymaga nowej klasy `CanonicalPyramid`/`GoldmanPyramid` równoległej do
  istniejącej `Pyramid`, reużywającej `linkage_tree.py`/`optimal_mixing.py`.
- **Surogat**: absolutny regresor, nieliniowy — **Random Forest**, per-objective (dwa osobne modele, f1/f2),
  deterministyczny na start (probabilistyczny RF z inter-tree std jako rozszerzenie v2, nie v1 — jej Table 7.1
  pokazuje RF per-obj probabilistyczny jako najlepszy/blisko najlepszego, ale deterministyczny RF per-obj
  różni się od niego tylko brakiem $\sigma$-gated acceptance, więc jest naturalnym, prostszym pierwszym krokiem).
  Uzasadnienie wyboru RF nad SVR/MLP/GBoost: brak strojenia kernela (SVR), brak niestabilności między
  przebiegami (MLP, udokumentowana w jej pracy jako problem), prostszy niż GBoost + quantile-loss dla wariantu
  probabilistycznego, gdyby był dodany później.
- **Bramka akceptacji**: Pareto-dominance nad absolutnymi wartościami (nie relatywny $\hat\delta_F$) — zgodnie
  z Algorithm 8 Dushatskiego, uproszczona do reguły "nie gorszy" (`Compare`), tak jak już robi istniejący
  `P3Absolute` w tym projekcie (można podejrzeć jego strukturę `propose`/`update` jako wzorzec integracji z
  resztą harnessu — ale **nie** jego silnik populacji, bo `P3Absolute` używa batch `Pyramid`, dokładnie tego,
  co chcemy zastąpić).

**Explicit v1 scope**: MO-DSA-P3-GOMEA-class, deterministyczny, per-objective RF, bez online surrogate
selection, bez probabilistycznej bramki. Online selection / probabilistyczna wersja = jawnie poza zakresem v1
(Faza 5).

## Fazy

### Faza 0 — Weryfikacja i uzasadnienie wyboru wariantu
- Potwierdzić dokładnie Algorithm 3 (P3 iteration), Algorithm 4 (FIHC), Algorithm 2 (GOM) z jej pracy jako
  specyfikację do implementacji — już przeczytane w tej rozmowie, do przepisania w docstringu nowego modułu
  z cytatem `bartnik2026evolutionary` i `dushatskiy2021novelsurrogateassistedevolutionaryalgorithm`.
- Sprawdzić, czy `linkage_tree.py`/`optimal_mixing.py` faktycznie obsługują kategorialne domeny bez zmian
  (powinny — GOM/linkage tree z natury działa na dowolnym alfabecie, nie tylko binarnym) — jednorazowy test
  jednostkowy potwierdzający na `nas_bench_201_genotype`.

### Faza 1 — Nowy silnik: `CanonicalPyramid` / pojedynczy-osobnik-climbing (TDD)
Nowy plik w bibliotece lub w `experiments/methods/` (do ustalenia: jeśli ma być reużywalny poza NAS, do
`lib/src/p3net/search_engines/p3/canonical_pyramid.py`; jeśli ma zostać eksperymentalny, do
`experiments-bartnik/engines/`):
- `CanonicalPyramid` — poziomy jak `PyramidLevel`, ale dodawanie nowego osobnika = pojedyncza ścieżka
  `FIHC → dla każdego poziomu od dołu: GOM → jeśli poprawa, awansuj` (Algorithm 3), nie batch bootstrap całego
  poziomu naraz.
- `first_improvement_hill_climber(genotype, fitness_fn, rng)` — Algorithm 4, reużywalna, populacja-agnostyczna.
- Testy: replikacja małego syntetycznego przykładu z jej/Goldmana pracy (znany wynik), potwierdzenie że
  poziomy rosną $2^k$ jak oryginalny P3, potwierdzenie że GOM korzysta z `linkage_tree.py`/`optimal_mixing.py`
  bez zmian.

### Faza 2 — Absolutny surogat RF per-objective (TDD)
- `AbsoluteRandomForestSurrogate` — dwa `sklearn.RandomForestRegressor` (f1, f2), fit na jednorazowo
  zakodowanym (one-hot) genotypie, analogicznie do istniejącego `AbsoluteRegressorSurrogate`
  (`lib/src/p3net/surrogates/absolute_regressor.py`) ale z RF zamiast liniowego modelu — sprawdzić czy
  wystarczy podmienić `model_factory`, czy potrzebna nowa klasa (RF nie ma `.coef_`, więc jeśli istniejący kod
  zakłada liniowość gdziekolwiek, trzeba to obejść).
- Testy: fit na znanym nieliniowym wzorcu, potwierdzenie że RF go łapie tam gdzie liniowy `AbsoluteRegressorSurrogate` by nie złapał (mirror analogicznego testu z Fazy interaction-features P3Net).

### Faza 3 — `BartnikP3` method (`propose`/`update`, TDD)
- Nowa klasa `methods/bartnik_p3.py` w `experiments-bartnik/`, strukturalnie mirror `P3Absolute` (patrz jego
  `propose`/`update`) ale z `CanonicalPyramid` zamiast `Pyramid` i `AbsoluteRandomForestSurrogate`.
- Threshold/gate: $\lambda$-quantile jak w Algorithm 7/8 Dushatskiego (relaksacja $\eta=0.999$, reset na
  poprawę elitarnego frontu) — reużyć wzorca, jeśli już gdzieś w projekcie istnieje podobna logika progu
  (sprawdzić `p3net.py` — P3Net nie ma tego mechanizmu, będzie nowy kod).
- Warm-up: $\ell$ losowych realnych ewaluacji ($\ell$ = liczba zmiennych = 6), zgodnie z jej Algorithm 7.
- Testy: smoke test na realnych danych NAS-Bench-201 (budżet 10-20), potwierdzenie że warm-up + climbing +
  gate działają end-to-end.

### Faza 4 — Konfiguracja + wiring + eksperyment
- `configs/methods/bartnik_p3.yaml`: `method: bartnik_p3`, `params: {growth_factor: 2, eta: 0.999, warmup: 6, ...}`.
- Wpis w `run_experiment.py::build_method` (nowy `if kind == "bartnik_p3":`).
- **Baseline set = dokładnie ten sam co P3Net grid**: `random_search`, `sh_emoa`, `tpe`, `mo_bohb`,
  `nsga_net`, `nsganetv2`, `p3_alone`, `p3_absolute` — plus opcjonalnie `p3net` sam jako punkt odniesienia
  (żeby bezpośrednio zestawić "jej silnik" vs "nasz silnik" na tym samym search space i budżetach).
- Budżety/seedy: $R=30$, `budgets=[100, 350]` — spójne z izolacyjnym eksperymentem P3Net, dla bezpośredniej
  porównywalności wyników.
- Orkiestracja: nowy skrypt `scripts/run_bartnik_isolation.py`, mirror `run_nas_bench_201_isolation.py`
  (smoke test → pełny grid → analiza Wilcoxon+Holm+Cliff's delta), tym razem `bartnik_p3` vs cały baseline set
  P3Net zamiast tylko `random_search`.

### Faza 5 — Jawnie poza zakresem v1
- Probabilistyczny surogat (RF z inter-tree std, Gaussian Process) i probabilistyczna bramka Pareto-dominance
  (Equation 6.1 jej pracy) — realny kolejny krok, ale osobna iteracja.
- Online surrogate selection / hyperparameter tuning w trakcie biegu.
- PXrLL / dynamic surrogate selection.
- Zmierzona energia GPU zamiast FLOPs jako f2 (ta sama, już udokumentowana granica co w eksperymencie
  izolacyjnym P3Net — `nats_bench` jej nie eksponuje).
- Replikacja jej dokładnych baseline'ów (MO-LS, MO-P3-GOMEA) — celowo pominięte, bo cel to porównanie do
  baseline'ów P3Net, nie replikacja jej Table 7.1 один-do-jeden.

## Weryfikacja
- `uv run pytest` zielone po Fazach 1-4.
- Smoke test na realnych danych NAS-Bench-201 przed pełnym gridem.
- Wynik raportowany bez spinu w żadną stronę — zarówno "silnik Bartnik separuje się od baseline'ów" jak i
  "nadal się nie separuje" są poprawnymi, publikowalnymi wynikami (patrz `conclusions.tex`, dopisany akapit).
