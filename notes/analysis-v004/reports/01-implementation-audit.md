# 01 — Audyt wierności implementacji metod mierzonych w v004

Przebieg 1 z `notes/analysis-v004/PROMPTS.md`. Tylko kod, konfiguracje, źródła i istniejące sprawdzenia —
**bez** analizy jakości wyników (to przebieg 2). Jedyne odczyty danych: liczba zużytych ewaluacji z nagłówków
plików przebiegów (sekcja 1.9) — fakt strukturalny o ramieniu, nie wynik jakościowy.

> **Korekta 2026-10-16 (A13):** pierwotnie raport zakładał (za `CONTEXT.md`), że praca magisterska Bartnik nie jest w repo, i
> oceniał wierność `bartnik_p3` jako „N” (brak źródła). Praca jest w `notes/articles/NAS/MO-NAS/`. Przepisane: §4.2; poprawione: §12
> (wiersz `bartnik_p3`), §14 pkt 4, §16. **Fakty przejęte bez sprawdzenia:** lista brakujących PDF-ów z `CONTEXT.md` (poza Bartnik
> potwierdzona: brak Vizier, BoTorch, Guerrero-Viu, BANANAS, SMAC3, TPE, MOEA/D, NSGA-III).

## Stan sekcji

| # | Sekcja | Stan |
|---|---|---|
| 0 | Zakres, oznaczenia, wersje | zrobione |
| 1 | Harness: ograniczenia wspólne dla wszystkich ramion | zrobione |
| 2 | Benchmarki (substraty) i dyskretyzacja | zrobione |
| 3 | Rodzina P3Net (S1–S5, s4, `final`) | zrobione |
| 4 | Kanoniczne P3: `bartnik_p3`, M9, M10, eLyMPuS | zrobione |
| 5 | `p3_alone*`, `p3_absolute` | zrobione |
| 6 | NSGA-Net, NSGANetV2 | zrobione |
| 7 | SH-EMOA, MO-BOHB | zrobione |
| 8 | Tor multi-fidelity | zrobione |
| 9 | BO: Vizier, qNEHVI, qParEGO, SMAC3, TPE | zrobione |
| 10 | Pozostałe: NSGA-III, MOEA/D, RegEvo, MO-LS, REINFORCE, BANANAS, RS | zrobione |
| 11 | `results/checks/` — co już sprawdzono | zrobione |
| 12 | Tabela zbiorcza | zrobione |
| 13 | Tabela hiperparametrów (suplement) | zrobione |
| 14 | Lista do Limitations | zrobione |
| 15 | Propozycje poprawek (opcje) | zrobione |
| 16 | Nieustalone | zrobione |
| 17 | Porównanie z `INITIAL_FINDINGS.md` | zrobione |

---

## 0. Zakres, oznaczenia, wersje

**Zakres.** Wszystkie ramiona `configs/pipeline/v004.yaml` i `v004-gp-small.yaml` (pliki identyczne poza
`primary_budgets`; sprawdzone porównaniem treści): grupa `comparison` (24), `final` (5), `multi_fidelity` (3),
s2 (4 etapy drogi projektowej), s4 (16 wariantów), s5 (9 ramion na NAS-Bench-201). Benchmarki: 3× JAHS-Bench-201,
NAS-HPO-Bench-II, 4× FCNet, NAS-Bench-201.

**Oznaczenia.**
- Pewność ustalenia: **W** (wysoka — przeczytany kod i/lub uruchomiony test), **Ś** (średnia — kod przeczytany,
  zachowanie wnioskowane), **N** (niska — brak źródła lub nie sprawdzone).
- Siła dowodu wniosku (wg CONTEXT.md): (1) interwencja/izolacja, (2) potwierdzające, (3) eksploracyjne,
  (4) hipoteza. W tym raporcie większość ustaleń to fakty o kodzie (pewność W/Ś); ich *skutek dla wyników* jest
  zwykle (4) — hipotezą do rozstrzygnięcia w przebiegu 2.
- Typ implementacji: **PI** pełna implementacja wg źródła · **AB** adapter do biblioteki · **RK** własna
  rekonstrukcja · **UW** uproszczony wariant · **NG** nowa generalizacja / projekt własny.

**Skrypty weryfikacyjne** (poza repo, katalog scratchpad sesji): `check_surrogate.py` (surogat względny),
`check_smac.py` (initial design SMAC3), `budget_use.py` (zużycie budżetu). Wyniki przytoczone w sekcjach.

**Wersje bibliotek** (`implementation/experiments/uv.lock`): optuna 4.9.0, smac 2.4.1, botorch 0.18.1,
gpytorch 1.15.2, pymoo 0.6.2, hpbandster 0.7.4, google-vizier 0.1.24, ConfigSpace 1.2.2, scikit-learn 1.9.0,
nats-bench 1.8, nashpobench2api 1.0.0, jax 0.4.38, torch 2.14.0, numpy 2.4.6. Most JAHS:
`vendor/jahsbench-env/.venv` — jahs_bench 1.1.0, scikit-learn 1.0.2, xgboost 1.5.2.
Nieustalone: czy `.venv` na maszynie obliczeniowej (Linux, chmura) miało dokładnie te wersje — manifest
`results/runs/b4d25cac/manifest.json` nie był tu sprawdzany pod kątem wersji pakietów.

---

## 1. Harness — ograniczenia wspólne dla wszystkich ramion

Pliki: `implementation/lib/src/p3net/harness/runner.py`, `harness/evaluation_cache.py`,
`implementation/experiments/scripts/run_experiment.py`, `stopping_rules.py`, `substrates/base.py`.

**H1. Ask–tell bez dostępu do benchmarku.** `Runner.run` (`runner.py:63-80`) woła `method.propose(state)` →
ewaluuje każdą propozycję przez `substrate.objectives` → `method.update(...)`. Metoda nie ma wywołania
benchmarku z wnętrza `propose`. Konsekwencja: każdy algorytm, który w oryginale ocenia kroki pośrednie
prawdziwą funkcją (P3: FIHC i GOM; eLyMPuS: porównania częściowe), musi je tu wykonywać na surogacie albo
jako osobne propozycje (`p3_alone`). Pewność W.

**H2. Budżet = liczba pełnych ewaluacji; brak deduplikacji w Runnerze.** Runner liczy każdą propozycję
(`runner.py:73-78`), także duplikat. Deduplikacja jest obowiązkiem metody (`cache.record_proposal`).
Wszystkie ramia ją robią (sprawdzone w każdym pliku), więc w praktyce duplikat nie zużywa budżetu, ale
gwarancja jest po stronie metody, nie harnessu. Pewność W.

**H3. Pusta propozycja kończy przebieg.** `runner.py:66-68`: `if not proposals: break`. Ramię, które w
danym kroku nie znajdzie nowego genotypu, kończy przebieg z niezużytym budżetem (patrz MOEA/D, sekcja 10, i
pomiar 1.9). Pewność W.

**H4. Dodatkowa reguła stopu `ExplorationCollapse`.** `stopping_rules.py`: stop, gdy w ostatnich 20
ewaluacjach jest < 4 różnych genotypów (próg 0.2). Przy deduplikacji po stronie metod praktycznie nie
wyzwala się (różne genotypy w historii są gwarantowane), ale formalnie jest częścią protokołu dla wszystkich
ramion jednowiernościowych. Ramion multi-fidelity nie dotyczy (osobny runner). Pewność Ś (nie sprawdzano,
czy kiedykolwiek się wyzwoliła).

**H5. Obcięcie partii do pozostałego budżetu.** `runner.py:69-71`: partia dłuższa niż pozostały budżet jest
obcinana do prefiksu. Dla metod partiowych (P3Net: |C*| na iterację; NSGA-Net/NSGANetV2: 20) ostatnia
partia jest niepełna, a jej skład zależy od kolejności zwróconej przez metodę (np. kolejność `pareto_front`).
Drobne. Pewność W.

**H6. f2 zawsze przy pełnej wierności i zawsze razem z f1.** `Substrate.objectives` (`base.py:265-269`)
zwraca `(f1 @ r_K, f2)`. Tor MF: f2 zawsze z r_K (`objectives_at_epochs`, `base.py:275-281`). Pewność W.

**H7. Hook `analytic_cost` — informacja uprzywilejowana tylko dla P3Net (checklista B3).**
`run_experiment.py:221`: dla każdej konfiguracji `method: p3net` z `use_analytic_cost` ≠ false metoda dostaje
`substrate.analytic_cost_objectives`, czyli f2 dowolnego genotypu **bez zużycia budżetu**. Używane przy
wyborze C* (`p3net.py:873-879`, `_absolute_estimate` `p3net.py:759-769`). Żadna inna klasa nie dostaje
substratu (`build_method` przekazuje `substrate` tylko do P3Net i ramion MF; ramiona MF używają go tylko do
`max_epochs()`). Co to f2 na każdej przestrzeni — sekcja 2: na NAS-HPO-Bench-II i FCNet to **zmierzony czas
treningu z tabeli**, na JAHS — wyjście surogatu benchmarku (`size_MB`), na NB201 — FLOPs z tabeli.
Ramiona, które to dostają: `p3net` (S4), `p3net_s2_analytic_cost`, `p3net_s3_ridge`, `p3net_s4_eager_mixing`,
cała grupa `final` (S5, `p3_absolute_cascade`, M7, kontrola M7, M8) i wszystkie warianty s4 poza
`p3net_cascade_inherited_cost`. Nie dostają: `p3net_s1_initial`, `p3net_cascade_inherited_cost`,
`p3_absolute`, wszystkie pozostałe ramiona. Pewność W.

**H8. Wspólna kontrola poprawności genotypu (Validity) i odrzucanie niepołączonych komórek.**
`search_spaces/_cell_graph.py:22-39`: genotyp bez ścieżki wejście→wyjście (same `none`) jest niepoprawny i
nie jest nigdy ewaluowany przez żadne ramię. Benchmarki same takie komórki mają (NB201/JAHS zwracają dla nich
wyniki), więc to decyzja projektu, stosowana jednakowo. Różnie obsługiwana w adapterach: TPE/NSGA-III —
`FAIL`, SMAC — najgorsze dotąd obserwowane wartości, Vizier — `infeasible`, MOEA/D — kara 1e12, BOHB — strata
`inf`, pozostałe — odrzucenie przed propozycją. Pewność W.

**H9. Zużycie budżetu (pomiar strukturalny).** Skrypt `budget_use.py` odczytał `evaluations_used` z nagłówka
każdego z 51 900 (b4d25cac) + 2 160 (gp-small) plików `raw/*.json` (bez parsowania historii). Wynik:
- **Wszystkie ramiona jednowiernościowe poza MOEA/D zużywają 100% budżetu w 100% przebiegów** (min = budżet).
- **MOEA/D: 265 z 1440 przebiegów (18.4%) kończy się przed budżetem**, średnio 91.7% budżetu. Prawie
  wyłącznie FCNet: przy b=200 23–28/30 przebiegów, przy b=350 29–30/30 przerwanych; mediana zużycia przy
  b=350 = 125.5–143.5 ewaluacji (min 46). JAHS: 2/720 przerwane (colorectal i fashion, b=350). NAS-HPO-II:
  7/240 (min 76). Mechanizm: `moead.py:370-403` — 10 000 kolejnych zapytań `ask()` zwraca wyłącznie
  duplikaty/niepoprawne genotypy → `return []` → H3 kończy przebieg. Przyczyna wnioskowana (Ś): SBX+PM z
  zaokrągleniem na indeksach kategorii o małych dziedzinach (FCNet: 2–6 wartości) i sąsiedztwo = cała
  populacja (n_neighbors=20 = liczba wag) → szybka zbieżność populacji do już ocenionych punktów.
  **Skutek:** na FCNet przy b≥200 MOEA/D jest porównywany przy faktycznie ~130 ewaluacjach, nie 200/350 —
  strukturalne upośledzenie, nie cecha metody per se (pymoo z `NoDuplicateElimination`).
- **Tor MF:** `evaluations_used` = liczba konfiguracji ocenionych przy pełnej wierności; z założenia < budżet.
  Hyperband/BOHB: deterministycznie 23 / 50 / 101–102 / 180 pełnych punktów przy b = 50/100/200/350 na JAHS i
  FCNet, 32/66/132/232 na NAS-HPO-II; ASHA: mediany 23–28 (b=50) … 150–198 (b=350). Metryki frontu liczone
  są więc na ~46–66% liczby punktów ramion jednowiernościowych przy tym samym koszcie. To konsekwencja D1, nie
  błąd (sekcja 8).

---

## 2. Benchmarki (substraty) i dyskretyzacja

Pliki: `implementation/experiments/substrates/*.py`, `search_spaces/*.py`, `configs/search_spaces/*.yaml`,
`vendor/jahsbench-env/query_server.py`.

| Przestrzeń | n | Genotyp (siatki) | f1 | f2 | Wierność r_K | Determinizm | Pewność |
|---|---|---|---|---|---|---|---|
| JAHS-Bench-201 (cifar10, colorectal_histology, fashion_mnist) | 10 | 6 krawędzi × 5 op. (`none, skip_connect, nor_conv_1x1, nor_conv_3x3, avg_pool_3x3`); LR: 8 wartości log 1e-3…1; WD: 6 wartości log 1e-5…1e-2; aktywacja {relu, hardswish, mish}; TrivialAugment {F, T} | `100 − valid-acc` z surogatu XGBoost JAHS (`jahs_bench.Benchmark`, domyślny `kind` = surogat) | `size_MB` z surogatu JAHS przy 200 epokach | 200 epok; stałe `N=5, W=16, Resolution=1.0, Optimizer=SGD` (`query_server.py:131`) | deterministyczny (surogat) | W |
| NAS-HPO-Bench-II | 8 | 6 krawędzi × 4 op. (`nor_conv_3x3, avg_pool_3x3, skip_connect, none`); LR {0.003125…0.4} (8); batch {16…512} (6) — **pełna siatka benchmarku**, bez straty z dyskretyzacji | `100 − valid_acc` po 12 epokach, `mode='valid'`, ziarno `seeds[0]` API | `total_trainval_time` (s) z tabeli, 12 epok | 12 epok (tylko zakres tabelaryczny; 200-epokowy surogat nie jest używany) | deterministyczny (jedno ziarno tabeli) | W |
| FCNet (protein, naval, parkinsons, slice) | 9 | units1/2 {16…512}, aktywacje {tanh, relu}×2, dropout {0, 0.3, 0.6}×2, init_lr (6), schedule {cosine, const}, batch {8…64} — pełna siatka 62 208 | valid MSE po 100 epokach, **średnia z 4 ziaren** | czas treningu (s), średnia z 4 ziaren; czas do epoki e liniowo interpolowany | 100 epok | deterministyczny (uśrednienie) | W |
| NAS-Bench-201 (cifar10, s5) | 6 | 6 krawędzi × 5 op.; brak hiperparametrów | **`100 − test-accuracy`** (NATS `tss`, `hp="200"`, `is_random=False` = średnia z logowanych prób) | FLOPs (`get_cost_info`) | 200 epok | deterministyczny | W |

Uwagi:
- **JAHS: dyskretyzacja** LR (8) i WD (6) z ciągłych przedziałów benchmarku oraz zamrożenie wymiarów
  wierności N/W/Resolution na maksimum. Wszystkie ramiona przeszukują tę samą siatkę (fairness), ale front
  osiągalny na siatce może być gorszy niż w ciągłej przestrzeni; `nsganetv2_continuous` (kontrola) jest
  `not_yet_implemented` i nie ma go w v004. Pewność W.
- **JAHS f2 = `size_MB` z surogatu**, nie liczba parametrów policzona analitycznie. Rozmiar w rzeczywistości
  zależy tylko od architektury (przy stałych N, W), ale surogat może zwracać wartości zależne od
  hiperparametrów. Nieustalone: czy `size_MB` z JAHS jest stały przy zmianie LR/WD/aktywacji dla tej samej
  architektury (sprawdzenie: zapytać most o jedną architekturę z kilkoma wartościami LR).
- **NB201: f1 to błąd na zbiorze testowym** (wybór za Bartnik); selekcja na zbiorze testowym. Opisowe (D6).
- **NAS-HPO-Bench-II i FCNet: f2 jest wynikiem treningu**, nie wielkością liczalną bez treningu
  (`nas_hpo_bench_ii.py:117-121`, `fcnet.py` `analytic_f2`). Na tych przestrzeniach hook H7 jest
  zapytaniem do wyroczni. Pewność W.
- **Wierności pośrednie (tor MF):** NAS-HPO-II — rekord `iepoch` tej samej 12-epokowej sesji (spójny z f1 przy
  12); FCNet — krzywa walidacyjna z tabeli (spójna); JAHS — surogat pytany z `nepochs=e` (`query_server.py:146-148`):
  wartość przy e epokach pochodzi z modelu przewidującego krzywą, a nie z zapisu pośredniego tego samego
  treningu. Model kosztu „wznowienie z checkpointu” (`multi_fidelity.py:10-18`) jest więc na JAHS założeniem,
  nie własnością danych. Pewność Ś.
- Most JAHS: cache zapytań w substracie jest per proces (`_query_cache`), surogat deterministyczny; brak
  wpływu na wyniki. Pewność W.

---

## 3. Rodzina P3Net (S1–S5, warianty s4, grupa `final`)

Pliki: `implementation/lib/src/p3net/methods/p3net.py` (klasa `P3Net`), `search_engines/p3/pyramid.py`,
`optimal_mixing.py`, `linkage_tree.py`, `surrogates/relative_linkage_aware.py`, `surrogates/telescoping.py`,
`surrogates/absolute_random_forest.py`, `surrogates/absolute_regressor.py`; budowa w
`scripts/run_experiment.py:193-223`.

**Źródło.** Projekt własny repo (NG). Odniesienia: P3 — Goldman & Punch, GECCO'14
(`notes/articles/linkage learn/P3/Parameter-less population pyramid.pdf`); κ = 2⌈log₂ n⌉ zapożyczone z
eLyMPuS (Przewoźniczek et al., GECCO'26) jako heurystyka. Nie ma publikacji, z którą można by porównać
„wierność” — porównuję (a) z kanonicznym P3 i (b) z opisem w `chapters/v003/proposed_optimizer/main.tex`.

### 3.1 Silnik populacji vs kanoniczny P3

| Element | Kanoniczny P3 (Goldman & Punch 2014, Fig. 1–3, §2.1–2.3) | P3Net (kod) | Pewność |
|---|---|---|---|
| Iteracja | 1 nowe losowe rozwiązanie → FIHC → wspinanie przez kolejne poziomy (mix z P_i, przy poprawie dodanie do P_{i+1}) | Cały poziom bootstrapowany losowo do rozmiaru docelowego, potem w każdym wywołaniu **każdy** rodzic poziomu jest przemiatany (generacyjnie, styl LTGA/GOMEA) — `p3net.py:590-655` | W |
| Rozmiar poziomu | brak rozmiaru docelowego; poziom rośnie o kolejne rozwiązania | `2^(k+1)` dla poziomu k (`pyramid.py:54`: poziom 0 = 2, poziom 1 = 4, …); tekst artykułu mówi „2^k” (przesunięcie o 1) | W |
| Hill climber | FIHC do lokalnego optimum (powtarzany, aż brak ścisłej poprawy) | **brak** w S1–S5 (tylko kontrola M7 i M8: jedno przejście FIHC po predykcji RF) | W |
| Nowy poziom | gdy rozwiązanie poprawi się na najwyższym poziomie | gdy wszystkie poziomy „stalled”: przejście nie zwiększyło HV poziomu (S4+) lub nie zdominowało incumbenta (S1–S3) — `pyramid.py:80-138` | W |
| Które poziomy aktywne | wszystkie (rozwiązanie przechodzi przez każdy) | S4: tylko najnowszy (`p3net.py:342-346`); S5 `cascade=True`: **każdy poziom niezależnie przemiata własną populację w każdym wywołaniu** (`p3net.py:354-365`) — to nie jest kaskada P3 (jedno rozwiązanie w górę piramidy), tylko równoległe generacje na wszystkich poziomach | W |
| FOS (zbiory mieszania) | wszystkie węzły drzewa poza korzeniem, **z** singletonami; usuwane klastry z D=0; kolejność od najmniejszych | wszystkie węzły **wewnętrzne, z korzeniem, bez singletonów** (`linkage_tree.py:342-356`); brak filtra D=0; kolejność losowa (`optimal_mixing.py:207`) | W |
| Miara linkage | D(Ci,Cj) = średnia z 2 − (H(i)+H(j))/H(i,j) | 1 − średnie NMI (sklearn `normalized_mutual_info_score`, normalizacja arytmetyczna), UPGMA — podobne, nie identyczne | Ś |
| Dawca | losowy dawca **różniący się** w danym klastrze (szukanie do skutku) | jeden losowy dawca (`optimal_mixing.py:218`); gdy równy bieżącemu na F → propozycja = bieżący (no-op) | W |
| Akceptacja kroku | prawdziwa ewaluacja; zachowaj, jeśli fitness nie spadł | predykcja surogatu tylko dla f1; S5: skumulowana poprawa względem przodka x₀ ≥ próg (`p3net.py:868-869`) — 3.2 | W |
| Unikalność w piramidzie | hashset wszystkich rozwiązań; poziomy rozłączne | deduplikacja propozycji przez cache; poziomy mogą dzielić genotypy (warm start kopiuje front H_t do nowego poziomu) | W |
| Mutacja | brak | brak | W |

Konsekwencje (pewność W dla mechaniki, skutek dla wyników = (4)):
- **Korzeń w FOS** daje propozycję „kopia dawcy” (cały genotyp dawcy): po akceptacji przemiatanie
  kontynuuje się od kopii już ocenionego osobnika. **Brak singletonów**: zmiana jednej współrzędnej jest możliwa
  tylko, gdy dawca różni się od bieżącego dokładnie na jednej pozycji klastra. Dla n=10 FOS ma 9 zbiorów
  (`check_surrogate.py`: „num subsets 9, root included: True, singletons: 0”).
- **No-op** (dawca równy bieżącemu na F) jest „akceptowany” (predykcja 0 ≥ próg 0) i **liczy się do długości
  łańcucha κ** (`p3net.py:636-641`) — zużywa limit κ bez zmiany genotypu. Częstość no-opów nieustalona
  (zależy od różnorodności poziomu; przy poziomach 2–4 osobników prawdopodobnie wysoka). Sprawdzenie: w powtórce
  przebiegu zliczyć `proposal.candidate == proposal.parent`.
- **Wybór „najlepszej” obserwacji do kryterium wzrostu** (`p3net.py:427-430`): pierwsza obserwacja partii,
  podmieniana tylko na taką, która ją dominuje; HV liczone dla tej jednej. Partia, w której inna, niezdominowana
  obserwacja zwiększyłaby HV, może zostać uznana za „stalled”. Wpływa na tempo wzrostu piramidy (a więc na
  udział bootstrapu). Pewność W (kod); wielkość efektu nieustalona.
- Nazewnictwo: S5 „cascade” to **„all-levels-active”**, nie kaskada w sensie P3. Wniosek „cascade pomaga /
  nie pomaga” dotyczy tego wariantu; kanoniczne wspinanie testują dopiero `bartnik_p3`/M9/M10 (sekcja 4).

### 3.2 Surogat względny δ̂_F — sprawdzone własności

Weryfikacja na kodzie biblioteki (`check_surrogate.py`: losowa populacja 30 genotypów JAHS, drzewo z 16, OLS i
RidgeCV) oraz na 3 prawdziwych historiach `p3net_cascade` b=100 seed 1 (`check_alpha.py`):

1. **Ograniczenie par do podzbiorów linkage jest puste.** Korzeń (wszystkie zmienne) należy do FOS, więc
   `_matching_subset` (`relative_linkage_aware.py:52-61`) dopasowuje **każdą** parę różnych genotypów:
   870/870 par użytych. Trening = wszystkie N(N−1) uporządkowane pary z H_t. Pewność W.
2. **Predykcja nie zależy od F** (`predict` używa F tylko do sprawdzenia przynależności): identyczna dla
   pierwszego i ostatniego podzbioru. Pewność W.
3. **Model wychodzi antysymetryczny:** obie kolejności par w danych ⇒ δ̂(x,x) ≈ 0 (−3.6·10⁻¹⁴ OLS,
   −5.5·10⁻¹² Ridge), δ̂(x,y)+δ̂(y,x) ≈ 0. W praktyce δ̂(x,x′) = g(x) − g(x′), g liniowe na one-hot — zdanie
   artykułu „w·onehot(x) − w·onehot(x′)” zgadza się z zachowaniem modelu (rozstrzyga punkt checklisty B2:
   formalnie dwa wektory wag, w praktyce w₂ = −w₁). Pewność W.
4. **Telescoping kolapsuje dokładnie:** f̂(x₂) przez łańcuch x₀→x₁→x₂ = f(x₀) − δ̂(x₀,x₂) (OLS: 36.000000 vs
   36.000000; Ridge: 36.000336 vs 36.000336). Błąd **nie kumuluje się** z długością łańcucha; uzasadnienie κ w
   artykule („bound on accumulated telescoping error”) nie dotyczy używanego modelu — κ ogranicza tylko liczbę
   zaakceptowanych kroków przed ewaluacją. Pewność W.
5. **δ̂ ≈ różnica absolutnego RidgeCV, ale słabiej regularyzowana.** Na prawdziwych historiach korelacja δ̂ z
   h(x)−h(x′) (h = RidgeCV na punktach): 0.81–0.91 (JAHS cifar10), 0.94–0.996 (NAS-HPO-II), 0.97–0.999 (FCNet
   protein); nachylenie 1.4–2.1 na JAHS przy N ≤ 100. RidgeCV wybiera α=0.1 na parach vs α=10 na punktach
   (JAHS, N=30/60). Siatka α domyślna (0.1, 1, 10); GCV/LOO po parach dzielących punkty nie jest walidacją
   niezależną, więc ciąży ku małemu α. Siła dowodu (3), 3 przebiegi.
6. Model addytywny (brak interakcji; `use_surrogate_interactions` nie jest w v004). Nieznana wartość kategorii
   → zerowy fragment one-hot. Fit na wszystkich parach H_t w każdym wywołaniu: O(N²) wierszy (N=350 →
   122 150) — koszt widoczny w s9.

**Co więc faktycznie różni S5 od `p3_absolute_cascade` (Q4, checklista B2).** Ta sama klasa, ten sam
RidgeCV i one-hot, ta sama piramida, `cascade`, świeże f2. Różnice:
- (a) efektywna regularyzacja (pary vs punkty, pkt 5);
- (b) **zakotwiczenie**: S5 szacuje f̂(x_m) = f(x₀) + h(x_m) − h(x₀) (korekta o resztę rodzica); wariant
  absolutny używa h(x_m) bez kotwicy (`_absolute_estimate`, `p3net.py:759-769`) — dotyczy też wyboru C*;
- (c) **reguła akceptacji**: S5 — łańcuch względem przodka, obie strony z modelu (h(x_m) ≤ h(x₀) przy progu 0);
  absolutny — krok względem bieżącego, a **pierwszy krok porównuje prawdziwe f(x₀) z predykcją h(x₁)**
  (`_accept_absolute`, `p3net.py:771-783`). Dla rodziców-elit (zwykle z ujemną resztą — lepszych, niż model
  przewiduje) wariant absolutny jest bardziej zachowawczy.
- **Nie** różni ich „linkage-awareness” (pkt 1–2).
Wniosek z Q4 „względny vs absolutny” mówi więc o kotwiczeniu, regule akceptacji i regularyzacji liniowego
modelu, nie o idei surogatu świadomego linkage. Checklista B2 („null oczekiwany z konstrukcji”) jest za mocna:
różnice (a)–(c) są realne, więc brak efektu nie byłby tautologią — ale niczego nie mówi o linkage.

**Rozbieżności kod ↔ tekst artykułu** (v0.0.3, `proposed_optimizer/main.tex:56-95`):
- „every linkage subset of the current tree” — w kodzie z korzeniem, bez liści; w P3 odwrotnie.
- krok 3: „scored by δ̂_F relative to the individual they modify … accepted if δ̂_F ≥ 0” — kod porównuje łańcuch
  z przodkiem x₀, nie z bieżącym osobnikiem (krok gorszy od bieżącego, ale nie gorszy od x₀, jest akceptowany).
- „truncated … over (f̂₁, f₂)” — warm start i obcinanie poziomu używają prawdziwych celów z H_t.
- „2^k for level k” — w kodzie 2^(k+1).
- κ jako ograniczenie błędu telescopingu — pkt 4.

### 3.3 Informacja uprzywilejowana: świeże f2 (H7, checklista B3)

C* = kandydaci niezdominowani w (f̂₁, f2), gdzie f2 kandydata **nieewaluowanego** pochodzi z `analytic_cost`
(`p3net.py:873-879`). Na NAS-HPO-II i FCNet to zmierzony czas treningu z tabeli — wynik treningu, którego żadna
inna metoda nie zna przed ewaluacją. Na JAHS to `size_MB` z surogatu JAHS (wielkość w zasadzie liczalna
analitycznie z architektury). Inne ramiona surogatowe nie mają tej informacji: NSGANetV2 i `p3_absolute` nie
używają f2 kandydata przy selekcji (NSGANetV2 sortuje po samym f̂₁, `p3_absolute` dziedziczy f2 rodzica),
Bartnik/M9/M10 przewidują f2 lasem losowym, BO modeluje f2 GP. Izolacja: `p3net_cascade_inherited_cost` (s4,
**tylko 4 przestrzenie główne — nie ma jej na FCNet**). Wpływ: każde porównanie S5 (oraz M7, kontroli M7, M8,
`p3_absolute_cascade`, S4) z ramionami zewnętrznymi na NAS-HPO-II i FCNet zawiera asymetrię na korzyść P3Net.
Pewność W (mechanizm); skutek (4) → rozstrzyga Q3 dla `inherited_cost` na NAS-HPO-II; na FCNet nierozstrzygalne
bez nowego przebiegu.

Wycieku f1 do metody nie ma: `analytic_cost_objectives` (`base.py:297-305`) zwraca 0.0 w slocie f1. Na JAHS hook
wykonuje jednak pełne zapytanie do mostu (odpowiedź z `valid_acc` jest buforowana w substracie, metoda jej nie
widzi) — koszt zegarowy, nie informacyjny.

### 3.4 Droga projektowa s2 (S1 → S4′) — co zmienia każdy etap

| Etap | Konfiguracja | Zmiana względem poprzedniego | Uwagi |
|---|---|---|---|
| S1 `p3net_s1_initial` | OLS, f2 dziedziczony, poziom pusty (losowy), stall = ścisła dominacja | — | odtwarza archiwum bit w bit (`stage_S1_reproduces_archive.log`) |
| S2 `p3net_s2_analytic_cost` | + świeże f2 | 1 oś | wprowadza H7 |
| S3 `p3net_s3_ridge` | + RidgeCV | 1 oś | |
| S4 `p3net` | + warm start **i** stall po HV (domyślne `level_init`, `stall_criterion`) | **2 osie naraz** (sparowane celowo, docstring `p3net.py:486-503`) | wkładów warm startu i kryterium HV nie da się rozdzielić z s2 (checklista B8) |
| S4′ `p3net_s4_eager_mixing` | S4 + `bootstrap_threshold: growth_factor` (mieszanie od 2 osobników) | 1 oś | ślepa uliczka, odtwarza objaw „2^96” |
| S5 `p3net_cascade` | S4 + `cascade: true` | 1 oś | finalny |

Pewność W.

### 3.5 Warianty s4 (obrona decyzji, 16 ramion na S5; tylko 4 przestrzenie główne)

- `inherited_cost` (f2 z przodka), `f1_truncation` (obcinanie po f1), `grow_on_stall` (pusty C* → nowy
  poziom zamiast wstrzyknięcia losowego), `transient_donors` (dawcy także spośród wyników przemiatania z tej
  samej iteracji), `threshold_permissive` (próg −0.01), siatka κ ∈ {1, ⌈log₂n⌉, 2⌈log₂n⌉, ∞=10⁶} × próg ∈
  {0, 0.01, 0.02} bez komórki S5 (2⌈log₂n⌉, 0). Rozwiązanie κ: `run_experiment.py:113-126`. Pewność W.
- **Progi są w jednostkach f1, bez normalizacji.** Na przestrzeniach głównych f1 to błąd w punktach
  procentowych (zakres w próbce RS b=350 seed 1: JAHS 4.1–90, NAS-HPO-II od 14.6). Próg 0.01–0.02 p.p. jest
  pomijalny wobec rozrzutu predykcji, więc warianty progowe różnią się od S5 głównie tym, że **odrzucają
  predykcje dokładnie równe 0** — no-opy (3.1) i kroki neutralne; `permissive` (−0.01) akceptuje minimalne
  pogorszenia. Wniosek „próg nie ma znaczenia” dotyczy progów rzędu 10⁻⁴ zakresu f1, nie progów merytorycznych.
  (Na FCNet, gdzie najlepsze MSE ~10⁻⁴ na naval/slice, ten sam próg 0.01 odrzucałby prawie wszystko — siatki tam
  nie ma, ale tym bardziej nie wolno uogólniać.) Pewność W (jednostki), skutek (4).
- **κ = 2⌈log₂n⌉ i κ = ∞ prawie nie mogą się różnić:** FOS ma n−1 zbiorów (9 na JAHS, 7 na NAS-HPO-II), a
  κ = 8 (JAHS) / 6 (NAS-HPO-II) zatrzymuje przemiatanie dopiero po 8 / 6 zaakceptowanych krokach (wliczając
  no-opy). Komórki różnią się tylko w przemiataniach z ≥ 8 z 9 (≥ 6 z 7) akceptacji. Przewidywanie (4):
  `kappa2log_*` ≈ `kappainf_*`. Pewność W (arytmetyka); skutek do sprawdzenia w Q3.

### 3.6 Grupa `final`: `p3_absolute_cascade`, M7, kontrola M7, M8

Wszystkie to klasa `P3Net` z `cascade: true`, świeżym f2 i piramidą S5 (`configs/methods/*.yaml`).
- `p3_absolute_cascade`: `surrogate_kind: absolute_linear`, RidgeCV — 3.2 (a)–(c). Pewność W.
- **M7 `p3net_bartnik`**: `absolute_rf` — dwa `RandomForestRegressor(100)` (f1, f2) na one-hot, refit co wywołanie
  (`p3net.py:739-748`); f2 z lasu i tak nadpisywany świeżym f2 z hooka. Akceptacja jak w wariancie absolutnym
  (krok vs bieżący; pierwszy krok: prawdziwe f(x₀) vs predykcja). Z pracą Bartnik łączy go **tylko rodzaj
  surogatu** — silnik to piramida P3Net, bez bramki λ-kwantylowej i bez kanonicznego wspinania. Nazwa
  „P3Net-Bartnik” nie może sugerować odtworzenia metody Bartnik. Pewność W.
- **Kontrola M7 `p3net_bartnik_fihc`**: M7 + jedno przejście FIHC po predykcji f1 lasu dla **każdego** wyniku
  przemiatania przed C* (`p3net.py:645-649`, `_make_refiner`): współrzędne w losowej kolejności, pierwsza
  wartość „nie gorsza” (remisy akceptowane — `_improves` = `not dominates` na 1-krotce), **bez powtarzania do
  lokalnego optimum**. Pewność W.
- **M8 `p3net_elympus`**: kontrola M7 z FIHC-eLyMPuS zamiast FIHC (sekcja 4.3). M8 vs kontrola to jedyna izolacja
  mechanizmu porównania przy identycznym silniku i surogacie (różnią się też strumieniem RNG — eLyMPuS losuje
  weryfikacje). Prerejestracja Q4 porównuje każdy wariant z S5, **nie** M8 z kontrolą — bezpośrednie M8 vs
  kontrola to analiza dodatkowa (siła (3) na seedach 1–30).

---

## 4. Kanoniczne P3: `bartnik_p3`, M9 `przewozniczek_p3elympus`, M10 `canonical_p3_scalar_fihc`; eLyMPuS

Pliki: `implementation/lib/src/p3net/search_engines/p3/canonical_pyramid.py` (`climb`,
`_first_improvement_hill_climb`), `search_engines/p3/fihc_elympus.py`, `surrogates/elympus.py`,
`implementation/experiments/methods/bartnik_p3.py`, `methods/przewozniczek_p3elympus.py`. Konfiguracje:
`bartnik_p3.yaml`, `przewozniczek_p3elympus.yaml`, `canonical_p3_scalar_fihc.yaml` (ta ostatnia to
`method: przewozniczek_p3elympus` z `hill_climber: fihc_scalar`).

### 4.1 Wspólny silnik `canonical_pyramid.climb` vs P3 (Goldman & Punch 2014)

| Element | P3 (Fig. 1, §2.1, §2.3) | `climb` (kod) | Pewność |
|---|---|---|---|
| FIHC | ścisła poprawa; powtarzany aż do braku poprawy (lokalne optimum) | **jedno przejście** po współrzędnych; pierwsza wartość „nie gorsza” (`_improves` = nie zdominowana; remisy akceptowane) — `canonical_pyramid.py:119-160` | W |
| Przejście przez poziomy | „for all P_i: mix; if improved, add to P_{i+1}” — mieszanie z **każdym** poziomem | przerwanie przy pierwszym poziomie bez poprawy (`canonical_pyramid.py:257-261`) | W |
| Kryterium poprawy | wzrost (skalarnego) fitness | `current != entering_x` i wejście nie dominuje wyniku — **permisywne wielokryterialne** na predykcjach (f1, f2) | W |
| Unikalność | hashset; poziomy rozłączne | brak; poziom 0 rośnie bez ograniczeń (udokumentowane w `bartnik_p3.py:49-61`) | W |
| FOS, dawca | jak w 3.1 (bez korzenia, z singletonami, dawca różniący się) | jak P3Net: z korzeniem, bez singletonów, jeden losowy dawca | W |
| Ewaluacje | każdy krok FIHC i GOM = prawdziwa ewaluacja | **każdy krok na lesie losowym** (`fitness_fn=surrogate.predict`); prawdziwa ewaluacja tylko końcowego kandydata wspinaczki po bramce (1 na `propose`) | W |

Dodatkowe własności integracji (wszystkie trzy ramiona):
- **Piramida zawiera osobniki nigdy nieocenione** — wyniki wspinaczek po surogacie; prawdziwe obserwacje nie
  trafiają do piramidy (poza jednorazowym zasiewem poziomu 0 z warm-upu, `bartnik_p3.py:180-181`). Drzewo
  linkage uczy się więc ze statystyk osobników zoptymalizowanych pod kolejne, nieaktualne już lasy (las jest
  przeuczany przy każdym `propose`, piramida trwa). Pewność W; skutek (4).
- **f2 przewidywany lasem**, mimo że na wszystkich przestrzeniach f2 jest dostępne bez treningu co najmniej tak
  jak dla P3Net (H7) — te ramiona nie dostają hooka. Asymetria na niekorzyść względem P3Net. Pewność W.
- Do 5 wspinaczek na `propose` (`max_climb_attempts`); jeśli żaden kandydat nie przejdzie bramki albo jest
  duplikatem — losowy genotyp i relaksacja progu (`_register_fallback`). Warm-up = n losowych ewaluacji
  (10 na JAHS, 8 na NAS-HPO-II, 9 na FCNet, 6 na NB201). Pewność W.
- Test poprawności silnika (`results/checks/p3_trap_correctness.md`): `climb` z **prawdziwą** funkcją celu
  (jednokryterialną) rozwiązuje pułapki k-arne 10/10 przy 50 000 ewaluacjach — waliduje silnik mimo
  odstępstw powyżej, ale nie waliduje użycia z surogatem i bramką.

### 4.2 `bartnik_p3`: bramka vs SA-P3-GOMEA (Dushatskiy et al., GECCO'21) i praca Bartnik

> **Korekta 2026-10-16 (A13).** Pierwotna wersja tej sekcji podawała, że praca Bartnik „nie jest w repo” (za `CONTEXT.md`).
> To nieprawda: praca jest w `notes/articles/NAS/MO-NAS/Evolutionary optimization of deep neural.pdf` (w repo od 2026-07-31,
> omówiona też w `notes/ga_landscape_2026.md` §13). Sekcja przepisana na podstawie pracy (§4.5 Algorytm 7–8, §5.2–5.4, §7.1–7.2,
> Tabela 7.1). Zmienia to ocenę: wierność wobec Bartnik z „N” na „W — rekonstrukcja niewierna”.

Źródło: praca magisterska Bartnik (`bartnik2026evolutionary`, `notes/articles/NAS/MO-NAS/Evolutionary optimization of deep neural.pdf`),
która przenosi SA-P3-GOMEA (Dushatskiy et al., GECCO'21) na dwa cele (MO-DSA-P3-GOMEA — surogat deterministyczny; MO-PSA-P3-GOMEA —
probabilistyczny); plan odtworzenia `notes/archive/experiments-bartnik-plan.md`. „Algorithm 7/8” z docstringu to numeracja z pracy
Bartnik (reprodukcja Algorytmów 2/3 Dushatskiego). Typ: RK, **wierność wobec Bartnik niska (W — porównane ze źródłem)**, wobec
Dushatskiego niska.

| Element | Bartnik (MO-DSA-P3-GOMEA, za SA-P3-GOMEA) | `bartnik_p3` (kod) |
|---|---|---|
| Hill climber | **brak** — nowy losowy osobnik trafia od razu na poziom 0 (Alg. 7 l. 11); Dushatskiy §2.3.4 usunął LS jako marnujący budżet | FIHC (permisywnie wielokryterialny, jednoprzebiegowy, na lesie) na starcie każdej wspinaczki |
| Gdzie prawdziwe ewaluacje | **wewnątrz GOM**: każdy kandydat z predykcją powyżej progu T jest oceniany od razu (Alg. 8 `Evaluate`); porównanie na prawdziwych wartościach, gdy oba je mają (`Compare`) | tylko końcowy kandydat całej wspinaczki; wnętrze wyłącznie na lesie |
| Wielkość progowana | α-kwantyl predykcji surogatu dla rozwiązań z prawdziwą wartością (wersja PSA: kwantyl prawdopodobieństw dominacji) | `best_real_f1 − pred_f1` vs λ-kwantyl okna 50 ostatnich **prawdziwych** różnic (`bartnik_p3.py:161-172, 205-209`) |
| Kwantyl i relaksacja | α = 1 na starcie, ×0.999 po każdej generacji bez zmiany archiwum, reset do 1 przy zmianie archiwum | λ = 0.5 stałe; τ −= (1−η)·max(|τ|,1); reset do kwantyla przy zmianie składu frontu |
| Wspinanie przez piramidę | przez **wszystkie** poziomy (Alg. 7 l. 14–22) | przerywane na pierwszym poziomie bez poprawy |
| Archiwum | elitarne archiwum niezdominowanych, ścisła dominacja | front z H_t |
| Warm-up | **100** losowych architektur (wspólny zestaw dla wszystkich wariantów) | n = 6 (NB201), 8–10 (pozostałe) |
| Surogat | SVR / MLP / RF / GBoost, wspólny lub per cel; hiperparametry strojone; warianty z niepewnością i z wyborem surogatu w trakcie | RF(100) per cel, deterministyczny, bez strojenia |
| Cele | dokładność (NB201, CIFAR-10) i **zmierzona energia GPU** (inferencja / trening 1 epoki) | f1 = błąd testowy, f2 = FLOPs |
| Protokół | budżet 500, 10 seedów, stop po 1000 iteracjach bez nowej ewaluacji | budżet 100/350, 30 seedów |

**Co mówi sama praca o odtworzonym wariancie** (Tabela 7.1, średnie z 10 seedów): MO-DSA RF per-obj ma HV 139.89 (inferencja) vs
MO-LS 140.23 i 305.80 (trening) vs MO-LS 294.23 — **na energii inferencji nie bije MO-LS**. Wygrywają warianty probabilistyczne
(MO-PSA, HV 142–143 / 346–354) i MLP. Odtworzyliśmy więc wariant, który i u autorki był słaby, w dodatku niewiernie.

**FLOPs jako f2:** Bartnik odrzuca FLOPs, bo w pilotażu na NB201 korelują z dokładnością (ρ = +0.749, wobec +0.492 dla energii) —
„optimizing the two jointly reduces almost to the accuracy-only ranking” (§5.2.2). Nasz NB201 z FLOPs jest więc problemem prawie
jednokryterialnym, co współtłumaczy sufit benchmarku (R2 §2.8).

Konsekwencje: (i) λ=0.5 z okna, w którym większość różnic jest ujemna (nowa obserwacja gorsza od najlepszej),
daje zwykle τ < 0 — bramka przepuszcza kandydatów przewidywanych jako gorsi od najlepszego o |mediana|;
(ii) bramka nie korzysta z f2, choć ramię jest oceniane HV. Pewność W (kod), skutek (4).
NB201 (s5): f1 = błąd testowy, f2 = FLOPs zamiast zmierzonej energii GPU (`nas_bench_201.py`, docstring) —
odstępstwo od Bartnik udokumentowane. W grupie `comparison` ramię biegnie też na przestrzeniach joint
(architektura + HP), czyli poza zakresem pracy Bartnik.
**Co wolno wnioskować:** o „kanonicznym P3 + RF + bramka kwantylowa w naszej rekonstrukcji, z wnętrzem
wspinaczki na surogacie”. Nie o metodzie Bartnik ani o SA-P3-GOMEA. Checklista B1 („kanoniczne P3 separuje się
/ nie separuje od RS”) testuje więc silnik z jednym nowym osobnikiem na iterację, **ale** z FIHC jednoprzebiegowym,
przerywaniem wspinaczki i piramidą z osobników surogatowych — to nie jest czysty kontrast „nasz wzrost poziomów
vs piramida P3”.

### 4.3 eLyMPuS (M8 `p3net_elympus`, M9 `przewozniczek_p3elympus`) i kontrola M10

**Co to jest wg źródła** (Przewoźniczek, Chicano, Tinós, Komarnicki, GECCO'26,
`notes/articles/linkage learn/Limited Perfect Monotonical Surrogates constructed using.pdf`): LyMPuS porównuje
dwa rozwiązania różniące się jedną zmienną binarną w kontekście jej zależności (empiryczny VIG); eLyMPuS buduje go
w locie, oszczędzając **prawdziwe ewaluacje** (FFE) w lokalnym przeszukiwaniu; FIHC-eLyMPuS z adaptacyjną
strategią weryfikacji „1/x” i darmowym wykrywaniem brakującego linkage przez cykl (circuit check); RecursiveLL z
gwarancją ≤ 2⌈log₂ n⌉ kroków; OLyMPuS = piramida + PXrLL + krok ILS. P3-eLyMPuS = P3-FIHCwLL z FIHC-eLyMPuS.

| Element | Publikacja | Repo (`elympus.py`, `fihc_elympus.py`) | Pewność |
|---|---|---|---|
| Alfabet | binarny (flip) | k-arny: porównanie wartości alternatywnej z bieżącą (k−1 porównań na zmienną) — **generalizacja własna repo**, w publikacji zapowiedziana jako future work | W |
| Kierunkowość zależności | klauzule C1–C6 (symetryczne i kierunkowe) | tylko „symetryczne” (bez C4–C6); odkryta zależność dopisywana tylko do `dependencies[g]` | W |
| Weryfikacja | strategia 1/x na poziomie całego wywołania FIHC (coraz rzadziej, gdy nic nie znaleziono) | stałe p=0.2 na każde trafienie cache z innego genotypu (`elympus.py:273-299`) | W |
| Circuit check | tak (darmowe wykrycie brakującego linkage) | brak | W |
| FIHC | „repeat … until” do lokalnego optimum, ścisła poprawa | jedno przejście, BETTER lub TIE akceptowane (`fihc_elympus.py:360-382`) | W |
| Ranking k wartości | — | `rank_values` istnieje, nieużywany | W |
| PXrLL, ILS, OLyMPuS | tak | brak (P3-eLyMPuS, nie OLyMPuS) | W |
| Funkcja porównywana | prawdziwy fitness (kosztowny) | **predykcja f1 lasu losowego** (M8: `p3net.py:808-813`; M9: `przewozniczek_p3elympus.py:309-316`) | W |
| Cele | 1 | 1 (f1); reszta silnika: P3Net (M8) lub `climb` na (f̂1, f̂2) (M9) | W |
| Czas życia cache | cały przebieg | jedna instancja na dopasowanie lasu: M8 — jedno wywołanie przemiatania (wszyscy rodzice wszystkich poziomów), M9 — ≤ 5 wspinaczek | W |
| Start VIG | pusty | pusty: dopóki nic nie odkryto, kontekst każdej zmiennej jest pusty, więc **porównanie (g, a, b) policzone raz jest używane dla każdego innego genotypu** (założenie pełnej separowalności) | W |

**Pomiar mechanizmu** (`check_elympus.py`): las RF(100) dopasowany do historii przebiegu M9 (b=100, seed 1) na
3 przestrzeniach; FIHC-eLyMPuS w konfiguracji produkcyjnej (pusty VIG, p=0.2) i dla każdego porównania
równoległe porównanie bezpośrednie na tym samym lesie:

| Przestrzeń | Wspinaczki na instancję | Porównania | Błędne decyzje akcept./odrzuć | Odkryte zależności |
|---|---|---|---|---|
| JAHS cifar10 | 5 (jak M9) | 114 | 8 (7.0%) | 0 |
| JAHS cifar10 | 30 | 612 | 67 (10.9%) | 9 |
| NAS-HPO-II | 5 | 74 | 6 (8.1%) | 4 |
| NAS-HPO-II | 30 | 460 | 38 (8.3%) | 10 |
| FCNet protein | 5 | 63 | 4 (6.3%) | 0 |
| FCNet protein | 30 | 422 | 51 (12.1%) | 7 |

Siła dowodu: (1) dla mechanizmu (bezpośrednie porównanie decyzji na tej samej funkcji), 1 seed × 3 przestrzenie.
Zatem w v004 **eLyMPuS = FIHC na predykcji lasu z ~6–12% decyzji zastąpionych przybliżonymi**, a jedyną
„oszczędnością” są wywołania `RandomForest.predict`, które nie są liczone do budżetu ani nie mają znaczenia
kosztowego. Pewność W.

**Izolacja (checklista B4 z `_parked/przewozniczek_isolation.tex`).** M9 i M10 różnią się wyłącznie hill
climberem: `fihc_elympus` vs `_first_improvement_hill_climb` na **tym samym skalarnym** f̂1 lasu, z tym samym
silnikiem, bramką i lasem (`przewozniczek_p3elympus.py:295-326`). **M10 izoluje mechanizm porównania od
skalaryzacji — luka B4 jest domknięta** dla pary M9–M10. Pozostałe kontrasty: `bartnik_p3` vs M10 = FIHC
wielokryterialny permisywny vs skalarny (sam efekt skalaryzacji FIHC); `bartnik_p3` vs M9 = oba naraz
(skonfundowane, jak opisuje docstring `fihc_elympus.py`). GOM/promocja we wszystkich trzech: na (f̂1, f̂2)
lasu, permisywnie. Różnica RNG: eLyMPuS konsumuje `rng.random()` przy weryfikacji, więc trajektorie M9 i M10
rozchodzą się także losowo (nie tylko przez decyzje). Pewność W.

**Odpowiedź wprost: czy na tej implementacji wolno pisać „eLyMPuS nie pomaga”?** **Nie.** Uzasadnienie:
1. Mechanizm z założenia oszczędza kosztowne ewaluacje; tu porównuje darmowe predykcje lasu. Nie ma czego
   oszczędzać, więc najlepszy możliwy wynik eLyMPuS w tym układzie to „tyle samo co FIHC”, a każde odstępstwo
   to szum aproksymacji (zmierzone 6–12% błędnych decyzji). Wynik M8 ≈ kontrola lub M9 ≈ M10 (albo gorzej) jest
   przewidywalny z konstrukcji i nie jest dowodem przeciw eLyMPuS.
2. Implementacja nie jest wierna: k-arna generalizacja bez publikacji i bez walidacji w konfiguracji produkcyjnej
   (walidacja Faza 2 w `lympus-nas-adaptation-validation.md` sprawdzała poprawność przy *znanym* VIG i
   oszczędności przy cache współdzielonym przez 30 wspinaczek; jakości decyzji przy pustym VIG nie mierzono),
   brak strategii 1/x, circuit check, FIHC do optimum, C4–C6, PXrLL, ILS.
3. Wolno napisać najwyżej: „w naszym układzie, gdzie porównania eLyMPuS dotyczą predykcji surogatu, a nie
   prawdziwych ewaluacji, zastąpienie bezpośrednich porównań naszą k-arną generalizacją eLyMPuS nie poprawiło
   [wyniku z Q4/M9–M10]” — i to jako stwierdzenie o tej integracji, nie o metodzie.

**Jaki test byłby rzetelny** (propozycje, do decyzji autora):
- Prawdziwe ewaluacje wewnątrz FIHC, liczone do budżetu. Harness to umożliwia: `p3_alone` już prowadzi GOM krok
  po kroku na prawdziwym f1 przez `propose` pojedynczych kandydatów. Ograniczenie z docstringu M9 („climb nie może
  być sterowany prawdziwym fitness”) wynika z synchronicznego API `climb`, nie z harnessu — wspinaczkę można
  przepisać jako generator/maszynę stanów oddającą każdą ewaluację jako propozycję.
- Porównać P3-FIHC (real) vs P3-FIHC-eLyMPuS (real) przy tym samym budżecie FFE: (a) na syntetycznych pułapkach
  k-arnych ze znanym VIG (`synthetic_kary.py`) i na ich binarnym kodowaniu — oddziela mechanizm od generalizacji
  k-arnej; (b) na NAS-HPO-II / NB201 (tabelaryczne, tanie). Miary: FFE do celu, końcowe f1, liczba odkrytych
  zależności, odsetek błędnych porównań.
- Wierne elementy: strategia 1/x zamiast stałego p, circuit check, FIHC do lokalnego optimum, cache przez cały
  przebieg (przy prawdziwej funkcji celu jest poprawny między wywołaniami — problem „nieaktualnego lasu” znika).
- Jednokryterialnie (jak w publikacji), a dopiero potem wariant wielokryterialny.

---

## 5. `p3_alone`, `p3_alone_pop20`, `p3_alone_pop40`, `p3_absolute`

### 5.1 `p3_alone*` (`methods/p3_alone.py`)

- **Co robi:** płaska populacja o stałym rozmiarze (10 / 20 / 40), losowy bootstrap; potem w kółko: losowy rodzic,
  drzewo linkage z populacji, przemiatanie GOM z **prawdziwą** ewaluacją każdej propozycji (po jednej na
  `propose`), akceptacja gdy f1 kandydata ≤ f1 bieżącego (`p3_alone.py:375-380`). Po zakończeniu przemiatania wynik
  dopisywany do populacji, **usuwany najstarszy** osobnik (`pop(0)`, FIFO). Duplikaty rozstrzygane z cache bez
  zużycia budżetu. Pewność W.
- **Typ:** UW. To nie jest P3: brak piramidy, brak FIHC, brak nowych losowych osobników (poza awaryjnym
  wstrzyknięciem po 20 przemiataniach samych duplikatów), zastępowanie FIFO zamiast jakościowego. Bliżej
  „LTGA/GOM z jednym rodzicem na raz”. **Jednokryterialne**: akceptacja tylko po f1, f2 ignorowany przez cały
  przebieg — ocenianie HV mierzy, ile front f2 „przypadkiem” pokrywa archiwum.
- FOS jak w 3.1 (korzeń: propozycja = kopia dawcy, czyli duplikat już ocenionego — rozstrzygana z cache, darmowa).
- **Wnioski:** „P3 bez surogatu” w sensie v0.0.3 — tylko dla tego wariantu; nazwa „P3 alone” zawyża podobieństwo
  do P3. `budget_starvation_expected: true` w `p3_alone.yaml` — autor wiedział, że to ramię z założenia
  głodzone budżetem. Pewność W.

### 5.2 `p3_absolute` (`methods/p3_absolute.py`; grupa `comparison`)

- Ta sama piramida co P3Net (S4-podobna: tylko najnowszy poziom, warm start, stall po HV, obcinanie NDS), surogat
  absolutny `AbsoluteRegressorSurrogate` z **`LinearRegression` (OLS)** (`run_experiment.py:226-234`), akceptacja
  krokowa `predicted ≤ current_value` z pierwszym krokiem „prawdziwe f(x₀) vs predykcja” (`p3_absolute.py:201-230`),
  **f2 dziedziczony** z rodzica (brak hooka H7 — `current_estimate` zachowuje f2 rodzica). Pewność W.
- **Względem S4 (`p3net`) różni się w trzech osiach naraz:** surogat (absolutny vs względny), model (OLS vs
  RidgeCV), f2 (dziedziczony vs świeży). Porównanie `p3_absolute` vs `p3net` nie jest „interwencją na surogacie”
  (checklista B8). Czystszy kontrast to `p3_absolute_cascade` vs S5 (3.2). Pewność W.
- Brak `cascade`; brak decyzji `kappa` z łańcuchem względnym (κ ogranicza liczbę akceptacji, jak w P3Net).

---

## 6. NSGA-Net i NSGANetV2

### 6.1 `nsga_net` (`methods/nsga_net.py`)

- **Źródło:** Lu et al., GECCO'19 (`notes/articles/NSGA/NSGA-NET …pdf`): NSGA-II z eksploracją (krzyżowanie
  + mutacja) i **etapem eksploatacji BOA** (sieć bayesowska z historii), własne kodowanie makro/mikro i operator
  krzyżowania zachowujący wspólne bloki.
- **Kod:** NSGA-II µ+λ: populacja 20, potomstwo 20 na generację, **rodzice losowani jednostajnie** (brak turnieju
  binarnego), krzyżowanie jednorodne na całym genotypie, mutacja per współrzędna z p=0.1, selekcja NDS + crowding
  (`_shared.py:374-393`). Brak BOA, brak operatorów NSGA-Net.
- **Typ:** UW — „ogólny NSGA-II na kategorycznym genotypie”, nie NSGA-Net. Sanity check (`nsga_sanity_check.md`):
  w granicy 5% od optuna NSGA-II na dwóch problemach syntetycznych (+0.91%, −4.23%) — potwierdza, że to rozsądny
  NSGA-II, nie że to NSGA-Net. Losowy wybór rodziców jest już na liście do Limitations (plan v004, Faza 0).
- **Wnioski:** wyniki dotyczą NSGA-II z domyślnymi operatorami; nie należy pisać o NSGA-Net jako metodzie.
  Pewność W.

### 6.2 `nsganetv2` (`methods/nsganetv2.py`)

- **Źródło:** Lu et al., ECCV'20 (MSuNAS/NSGANetV2): archiwum startowe, w każdej iteracji **Adaptive Switching**
  (MLP, CART, RBF, GP — wybór przez CV), **NSGA-II na surogacie** po (predykowana dokładność, złożoność liczona
  wprost, np. #MAdds), wybór podzbioru do treningu (najlepszy predykowany + rozproszenie po osi złożoności), dolny
  poziom: supernet/fine-tuning.
- **Kod:** jak `nsga_net`, ale w każdej generacji pula 60 potomków (multiplier 3) jest sortowana po **predykcji
  samego f1** i do ewaluacji idzie 20 najlepszych (`nsganetv2.py:149-172`). Regresor: **`LinearRegression` (OLS) na
  one-hot** (`run_experiment.py:237-245`), dopasowany do całej historii. Brak AS, brak wewnętrznego NSGA-II na
  surogacie, brak wyboru podzbioru po złożoności, **f2 kandydata w ogóle nieużywany przy selekcji**, brak supernetu
  (bez znaczenia na benchmarkach tabelarycznych). Mutacja zaszyta na 0.1.
- **Typ:** UW — „NSGA-II + filtr potomstwa liniowym surogatem f1, w duchu NSGANetV2” (checklista B5). Pewność W.
- **Informacja / upośledzenie:** oryginał korzysta z darmowej złożoności przy wyborze kandydatów — tutaj tego nie ma,
  podczas gdy S5 ma świeże f2 (H7). Wybór po samym f̂1 spycha propozycje w region niskiego błędu (zwykle wysokiego
  kosztu), co szkodzi HV. Asymetria na niekorzyść NSGANetV2 względem S5 i względem oryginału. Pewność W (mechanizm),
  skutek (4).
- **Wnioski:** „S5 vs NSGANetV2” = S5 vs uproszczony filtr OLS; nie wolno uogólniać na NSGANetV2.
  `nsganetv2_continuous` (ciągłe Θ) — `not_yet_implemented`, poza v004.

---

## 7. SH-EMOA i MO-BOHB (tor główny, jedna wierność; checklista B5)

Źródło obu: Guerrero-Viu et al. 2021, „Bag of Baselines for Multi-objective Joint NAS and HPO”
(`guerreroviu2021bagofbaselines` w `refs.bib`; PDF brak w `notes/articles/`). **Cytowanie w v0.0.3 jest
niepoprawne**: `chapters/v003/results/main.tex:15` cytuje SH-EMOA przez `beume2007smsemoa` (SMS-EMOA) i MO-BOHB
przez `falkner2018bohb` (jednokryterialny BOHB); źródłem obu nazw jest Guerrero-Viu et al. Pewność W (tekst), N
(zgodność kodu z kodem referencyjnym — opis referencji w docstringach nie był weryfikowany tutaj).

### 7.1 `sh_emoa` (`methods/sh_emoa.py`)

- **Kod:** steady-state (µ+1) EMOA: populacja 20 (`sh_emoa.yaml`; domyślna klasy 10), turniej rozmiaru 3 **po samej
  randze frontu** (`sh_emoa.py:394-397`; docstring klasy obiecuje rozstrzyganie remisów po wkładzie HV — w kodzie
  remisy rozstrzyga kolejność losowania), potomek z krzyżowania jednorodnego (p=0.5) **albo** mutacji (losowanie
  wartości per współrzędna z p=0.2, może wylosować tę samą), selekcja: NDS + usuwanie najmniejszego wkładu HV z
  ostatniego frontu (zasada SMS-EMOA), punkt odniesienia = nadir populacji + 1%.
- **Brak części „SH”** (successive halving — ponowne oceny populacji przy rosnącej liczbie epok): harness głównego
  toru jest jednowiernościowy. Typ: UW. Nazwa „SH-EMOA” bez SH jest myląca; propozycja checklisty B5 („SMS-EMOA-style
  EMOA (single-fidelity part of SH-EMOA)”) jest właściwa. Pewność W.

### 7.2 `mo_bohb` (`methods/external/mo_bohb.py`)

- **Kod:** generator konfiguracji `hpbandster.optimizers.config_generators.bohb.BOHB` (hpbandster 0.7.4) wołany
  zawsze z jednym budżetem `FIXED_BUDGET = 1.0` — **bez Hyperbandu**, czyli sam próbnik KDE (TPE-podobny) BOHB.
  Wiele celów: każdy zgłaszany wynik skalaryzowany ważonym Tchebycheffem z **nową losową wagą przy każdym zgłoszeniu**,
  po normalizacji min–max bieżącym zakresem (`mo_bohb.py:165-200`). Duplikat zgłaszany ponownie (znana wartość, nowa
  waga) — ten sam punkt trafia do KDE kilka razy z różnymi stratami. Niepoprawne genotypy: strata `inf`.
- **Odstępstwa od MO-BOHB Guerrero-Viu:** tamten używa zmodyfikowanego hpbandster z wielokryterialnym
  generatorem i jest wielowiernościowy. Tutaj: jedna wierność, skalaryzacja losowa per obserwacja (KDE uczy się
  mieszaniny losowo ważonych krajobrazów — dla danej konfiguracji strata zależy od wylosowanej wagi, więc sygnał
  dobry/zły jest silnie zaszumiony), domyślne `top_n_percent=15`, `min_points_in_model=None` (= d+1),
  `random_fraction` domyślne. Typ: AB + UW. Właściwa nazwa: „BOHB-KDE sampler, single-fidelity, random
  Tchebycheff scalarisation”. Pewność W (kod), Ś (zachowanie KDE).
- Prawdziwy wielowiernościowy BOHB jest w torze MF (`bohb_mo`, sekcja 8).
- **Wnioski:** wygrane S5 z „MO-BOHB” (v0.0.3) nie są wygranymi z ustalonym baseline’em wielowiernościowym;
  dotyczą słabego, jednowiernościowego próbnika z zaszumioną skalaryzacją.

---

## 8. Tor multi-fidelity: `hyperband_mo`, `asha_mo`, `bohb_mo` (`methods/multi_fidelity.py`)

- **Model kosztu (D1)** `MultiFidelityRunner` (`multi_fidelity.py:98-134`): zapytanie (genotyp, e epok) kosztuje
  (e − e_prev)/E (wznowienie od ostatniej oceny tego genotypu); budżet B = koszt B pełnych ewaluacji; zapytanie
  przekraczające pozostały budżet **kończy przebieg** (reszta niewykorzystana, < koszt jednego zapytania). E: JAHS 200,
  NAS-HPO-II 12, FCNet 100. Pewność W.
- **Co trafia do metryk:** tylko konfiguracje ocenione przy e = E (`state.history`); oceny przy niższych epokach są w
  `diagnostics.fidelity_queries`, ale nie w froncie. Zmierzone (1.9): Hyperband/BOHB 23/50/101–102/180 pełnych punktów
  (JAHS, FCNet) i 32/66/132/232 (NAS-HPO-II) przy b = 50/100/200/350; ASHA 23–28 … 150–198. Pewność W.
- **Drabina:** η=3, min 1 epoka, s_max = ⌊log₃E⌋: JAHS 2, 7, 22, 67, 200; NAS-HPO-II 1, 4, 12; FCNet 1, 4, 11, 33, 100
  (wyliczone z `rung_epochs`). Pewność W.
- **Promocja MO:** NDS na (f1 przy danej wierności, f2) + crowding malejąco, top ⌊n/η⌋ (NSGA-II-owa kolejność, jak jeden z
  wariantów MO-ASHA). f2 przy każdej wierności = wartość z r_K (dla NAS-HPO-II/FCNet to czas *pełnego* treningu, czyli
  znany z góry dla wszystkich ramion MF jednakowo). Pewność W.
- **Hyperband:** harmonogram nawiasów od s_max w dół, potem cyklicznie; nowe konfiguracje losowe. Implementacja własna
  (nie hpbandster/optuna — brak sekwencyjnego API z MO-promocją, docstring). Typ: RK według pseudokodu Li et al.
  Pewność Ś (zgodność z pseudokodem przeczytana, nie testowana tutaj).
- **ASHA:** jeden worker, czyli de facto synchroniczna wersja z promocją z najwyższego możliwego szczebla; bez
  równoległości ASHA traci swoją raison d'être, ale przy jednym workerze to poprawne zachowanie. Typ: RK.
- **BOHB (`bohb_mo`):** harmonogram Hyperbandu + prawdziwy generator BOHB z hpbandster, pytany z budżetem = liczba
  epok szczebla, informowany o każdym wyniku na tym szczeblu; skalaryzacja jak w 7.2 (losowa waga per wynik,
  normalizacja **osobno per liczba epok**). Typ: AB + RK.
- **JAHS przy niższych epokach:** wartości z surogatu `nepochs=e`, nie zapis pośredni tego samego treningu (sekcja 2).
- **Ograniczenia/wnioski:** porównanie Q7 jest „przy równym koszcie w ekwiwalentach epok”, a nie „przy równej liczbie
  pełnych ewaluacji”; front MF ma ~połowę punktów. Koszt narzutu algorytmu (zegar) — osobno w s9. Na JAHS założenie
  wznowienia z checkpointu jest modelowe. Pewność W.

---

## 9. BO i modele zastępcze: Vizier, qNEHVI, qParEGO, SMAC3-ParEGO, TPE

Wspólne: adapter ask–tell (`methods/external/_ask_tell_shared.py`); duplikat zgłaszany bibliotece ze znaną wartością
(bez ewaluacji), niepoprawny genotyp obsługiwany wg H8; brak źródeł PDF w repo (CONTEXT.md) — ocena wg kodu
biblioteki, pewność co najwyżej Ś dla zgodności z publikacjami.

### 9.1 GP: `oss_vizier`, `botorch_qnehvi`, `botorch_qparego` — tylko b = 50 i 100 (`v004-gp-small.yaml`)

- **Zakres:** run root `gp-small`, budżety 50/100, seedy 1–60 na 4 przestrzeniach głównych + seedy 1–30 na FCNet;
  brak kolumn 200/350 (pamięć/czas: Vizier ~34 GB przy 350, qNEHVI 8419 s na przebieg — nagłówek pliku planu).
  b4d25cac nie zawiera żadnego przebiegu GP (sprawdzone w 1.9: 720 przebiegów na ramię, wszystkie z gp-small).
  Restarty usługi przy OOM nie są w `failures.jsonl` (CONTEXT.md). Determinizm: przebiegi GP po restarcie są
  liczone od nowa (zapis atomowy całego przebiegu), więc restart nie zostawia częściowych historii. Pewność W.
- **Vizier** (`vizier_mo.py`, google-vizier 0.1.24): `VizierGPUCBPEBandit` z domyślnymi argumentami (algorytm
  „DEFAULT”), float64, każda współrzędna jako CATEGORICAL po indeksach; wielokryterialność natywna (skalaryzacja
  hiperobjętościowa 1000 losowych wag w akwizycji, `gp_ucb_pe.py:309-319`); `num_seed_trials=1` (pierwszy punkt =
  środek przestrzeni), trust region włączony. Niepoprawne → `infeasible`. Typ: AB, domyślne. Pewność W/Ś.
- **BoTorch** (`botorch_mo.py`, botorch 0.18.1): `MixedSingleTaskGP` ze wszystkimi wymiarami kategorycznymi
  (kodowanie porządkowe indeksów, jądro kategoryczne), Standardize, oba cele razem; projekt początkowy 2(d+1)
  losowych (22 JAHS, 18 NAS-HPO-II, 20 FCNet); akwizycja qLogNEHVI (punkt odniesienia 10% zakresu za najgorszym)
  lub qLogNEI na losowej Chebyshevowej skalaryzacji (qParEGO), 128 próbek Sobol QMC; **maksymalizacja akwizycji po
  puli** 1024 losowych + wszyscy sąsiedzi 1-współrzędnościowi frontu (nie `optimize_acqf_mixed`); refit GP co krok z
  ciepłym startem hiperparametrów; CPU (`device` domyślne). Typ: AB z własną optymalizacją akwizycji (uzasadnioną
  ograniczeniem Validity). Przy b=50 to ~28–32 kroków BO. Pewność W.
- **Wnioski:** rankingi z GP tylko dla b ≤ 100 (znane odchylenie 1 w CONTEXT.md); rodzina Holma Q1 mniejsza przy
  200/350. Przewaga/strata GP przy małym budżecie nie mówi nic o b ≥ 200.

### 9.2 `smac3_parego` (`smac_parego.py`, smac 2.4.1)

- `HyperparameterOptimizationFacade` + `ParEGO`, wszystkie ustawienia domyślne, `deterministic=True`,
  **`n_trials=10**7`** („budżet kończy harness, nie SMAC”). Niepoprawne → najgorsze dotąd wartości (nie CRASHED).
- **Ustalenie (W, `check_smac.py`):** domyślny projekt początkowy HPO facade to Sobol z
  `n_configs_per_hyperparameter=10` i `max_ratio=0.25` względem `n_trials`; przy `n_trials=10⁷` limit nie działa, więc
  **projekt początkowy ma 10·d konfiguracji: 100 (JAHS), 80 (NAS-HPO-II), 90 (FCNet)**. Skutek:
  - b = 50: SMAC3 = **czysty Sobol** na wszystkich przestrzeniach;
  - b = 100: czysty Sobol na JAHS; 20 kroków modelu na NAS-HPO-II, 10 na FCNet;
  - b = 200/350: model działa przez 100–270 kroków.
  Niepoprawne konfiguracje Sobola są zgłaszane bez ewaluacji, więc liczba ocenionych punktów Sobola może być
  nieco < 10·d. Przy b ≤ 100 na JAHS ramię SMAC3 jest więc quasi-losowym przeszukiwaniem — wyniki SMAC3 przy
  małym budżecie nie mówią nic o SMAC3/ParEGO jako metodzie. Gdyby ustawić `n_trials` = budżet, projekt początkowy
  miałby ⌊0.25·b⌋ = 12/25/50/87 punktów. Typ: AB, ale z konfiguracją, która zmienia charakter metody. Wpływ (4):
  przewidywanie SMAC3 ≈ RS przy b ≤ 100 na JAHS — do sprawdzenia w przebiegu 2.

### 9.3 `tpe` (`tpe.py`, optuna 4.9.0)

- `TPESampler(seed)` z domyślnymi: `n_startup_trials=10`, `multivariate=False` (**niezależne rozkłady per wymiar** —
  brak modelowania interakcji, istotne dla przestrzeni joint), `n_ei_candidates=24`; wielokryterialnie optuna
  używa MOTPE (podział na dobre/złe przez niedominację). Duplikaty zgłaszane jako ukończone triale ze znaną wartością
  (liczą się do historii TPE, nie do budżetu), niepoprawne jako FAIL. Typ: AB, domyślne. Pewność W.

---

## 10. Pozostałe ramiona

| Ramię | Plik | Źródło | Co robi kod | Typ | Główne odstępstwa / uwagi | Pewność |
|---|---|---|---|---|---|---|
| `nsga3` | `external/nsga3.py` | Deb & Jain 2014; optuna `NSGAIIISampler` | domyślne optuna (crossover jednorodny, `swapping_prob` 0.5, `crossover_prob` 0.9, mutacja 1/n, punkty odniesienia dla 2 celów, `dividing_parameter` 3) poza `population_size=20` (domyślnie 50) | AB | przy 2 celach NSGA-III ≈ NSGA-II z innym mechanizmem niszowania; duplikaty zgłaszane ze znaną wartością liczą się do generacji optuna (generacja może być „pełna” duplikatów) | W |
| `moead` | `external/moead.py` | Zhang & Li 2007; pymoo 0.6.2 | 20 wektorów wag (uniform, 19 podziałów), `n_neighbors=20` (= cała populacja), Tchebycheff (domyślne dla 2 celów), SBX(η=20)+PM(η=20) na indeksach z zaokrągleniem, `NoDuplicateElimination`; niepoprawne → kara 1e12 | AB | **kodowanie porządkowe kategorii** (narzuca nieistniejący porządek); **przerywa przed budżetem**: 18.4% przebiegów, prawie cały FCNet przy b ≥ 200 (mediana ~126–144 ewaluacji przy b=350) — 10 000 kolejnych `ask()` bez nowego genotypu → `[]` → koniec (H3, 1.9) | W |
| `regularized_evolution_mo` | `regularized_evolution_mo.py` | Real et al. 2019 | P=20, S=5, mutacja jednej współrzędnej na inną wartość, usuwanie najstarszego; „najlepszy” w turnieju = ranga NDS w próbce + crowding + losowo | NG (adaptacja MO własna) | S/P = 0.25 jak w oryginale; oryginał P=100, S=25 i jednokryterialny | W |
| `mo_ls` | `mo_ls.py` | Pareto Local Search (Paquete et al. 2004); White et al. 2021 | archiwum niezdominowanych; losowy niezbadany członek archiwum → ocena **całego** sąsiedztwa 1-współrzędnościowego w losowej kolejności (JAHS: 6·4+7+5+2+1 = 39 sąsiadów); restart losowy, gdy wszystko zbadane | PI (wariant PLS z pełnym sąsiedztwem) | brak parametrów; sąsiedztwo raz wygenerowane jest dokańczane nawet, gdy archiwum się zmieni | W |
| `reinforce_mo` | `reinforce_mo.py` | Zoph & Le 2017 (polityka faktoryzowana jak w benchmarkach) | niezależny softmax per współrzędna, aktualizacja po każdej ewaluacji (batch 1), lr 0.1, baseline EMA 0.9; nagroda = −Chebyshev z **nową losową wagą przy każdej ewaluacji**, normalizacja bieżącym min/max | NG (adaptacja MO) | sygnał nagrody silnie zaszumiony przez losową wagę (ten sam punkt dostaje różne nagrody); brak kontrolera RNN; nie strojone | W |
| `bananas_mo` | `bananas_mo.py` | White, Neiswanger & Savani 2021 | 10 losowych startowych; zespół 5 × MLP (10 warstw × 20, Adam, lr 0.01, 200 iteracji, sklearn); niezależne próbkowanie Thompsona; kandydaci: 100 mutacji (1–2 współrzędne) frontu + 100 losowych; skalaryzacja Chebysheva z losową wagą co krok | AB/RK + NG (MO) | **kodowanie one-hot całego genotypu zamiast path encoding** (path encoding nie obejmuje HP); strata MSE (oryginał MAE); kandydaci także losowi (oryginał: mutacje najlepszych); sklearn `MLPRegressor` bez early stopping | W/Ś |
| `random_search` | `random_search.py` | — | próbkowanie jednostajne z odrzucaniem niepoprawnych i duplikatów | PI | rozkład = jednostajny na **poprawnych** genotypach | W |

Uwagi wspólne: populacje 20 we wszystkich metodach populacyjnych to wybór projektu („to match every other
population-based arm”), nie strojenie; hiperparametry wszystkich baseline’ów domyślne / z oryginałów, bez strojenia
na tych benchmarkach (asymetria względem S5 projektowanego na seedach 1–30 tych samych przestrzeni — checklista C).

---

## 11. `results/checks/` i `runs/b4d25cac/checks.json` — co już sprawdzono

| Sprawdzenie | Co pokazuje | Czego NIE pokazuje |
|---|---|---|
| `runs/b4d25cac/checks.json` | commit b4d25cac, `dirty: false`; testy lib 203 passed, experiments 367 passed / 2 skipped; determinizm: każde ramię planu uruchomione dwa razy (NAS-HPO-II, b=20, seed 1) daje identyczną historię — `true` dla wszystkich | poprawności algorytmów; determinizmu na JAHS/FCNet i przy większych budżetach; `gp-small` nie ma własnego `checks.json` (kod metod identyczny, CONTEXT.md) |
| `p3_trap_correctness.md` | kanoniczny `climb` z prawdziwym fitness: 10/10 optimów na pułapkach k-arnych (m=5, k=4, alfabet 3, zmienne przeplecione) przy 50 000 ewaluacji, RS i restartowany FIHC 0/10 — kryteria ustalone przed przebiegiem | zachowania `climb` z surogatem i bramką (bartnik/M9/M10); P3Net przy 2000 ewaluacji 0/10, mediana 15.72 (default) i 16.09 (cascade) — poniżej RS 16.38 przy równym budżecie (`…_equal_budget_2000.md`); kanoniczny P3 przy 2000 też 0/10 (17.75) — przy małym budżecie pułapki nie rozróżniają silników |
| `nsga_sanity_check.md` | `nsga_net` w granicy 5% od optuna NSGA-II (linear +0.91%, LOTZ −4.23%), oba > RS | że `nsga_net` = NSGA-Net (6.1) |
| `phase2b_moved_arms_reproduce.log`, `phase2c_instrumentation_unchanged.log`, `phase3_engine_unchanged.log` | przeniesione/oprzyrządowane ramiona odtwarzają wcześniejsze surowe wyniki bit w bit (2–4 przebiegi na ramię) | poprawności tych wcześniejszych wyników; mała próbka |
| `stage_S1_reproduces_archive.log`, `stage_S2_reproduces_archive.log` | konfiguracje S1 i S2 odtwarzają archiwa sprzed refaktoryzacji 24/24 | że archiwa były poprawne; S3/S4′ nie mają takiego logu (S4′ — „odtwarza udokumentowany objaw”, plan v004) |
| `phase2d_fcnet_smoke.log` | front FCNet z `all_objectives` zgodny z brute force (protein 21 pkt, slice 28); smoke każdego ramienia na FCNet bez duplikatów | jakości na FCNet |
| `phase2c_jahs_bridge_memory.log` | pamięć mostu JAHS (Windows 17.5 GB szczytowo; Linux ~11.7 GB anon-rss na zbiór) | — (infrastruktura) |
| `phase2b_timing.log`, `new_baselines_timing_nashpo_b350.json`, `phase2b_timing_nashpo_b350.json` | czasy jednego przebiegu NAS-HPO-II b=350 (np. Vizier 4414 s, qNEHVI ~58 min, BANANAS 170 s); MF: Hyperband 232 pełnych / 1031 zapytań, koszt 349.5 | czasów z s9 (sekwencyjne, właściwe źródło Q6) |

Wniosek dla wiarygodności: sprawdzenia dotyczą **determinizmu, regresji i poprawności silników bazowych z
prawdziwym fitness**. Nie ma sprawdzeń, które walidowałyby: (a) surogatowe użycie kanonicznego silnika,
(b) poprawność decyzji eLyMPuS w konfiguracji produkcyjnej (zrobione tu, 4.3), (c) zgodność adapterów
bibliotecznych z zamierzonym zachowaniem (np. projekt początkowy SMAC3, 9.2), (d) zużycia budżetu (zrobione tu,
1.9), (e) własności surogatu względnego (zrobione tu, 3.2).

---

## 12. Tabela zbiorcza

Legenda typu: PI / AB / RK / UW / NG (sekcja 0). „Info+” = informacja uprzywilejowana, „Info−” = upośledzenie
strukturalne. Pewność: W/Ś/N.

| Ramię (etapy) | Źródło | Typ | Główne odstępstwa | Info+ / Info− | Wpływ na wnioski | Pewność |
|---|---|---|---|---|---|---|
| `p3net_cascade` S5 (s1 via s3, s3, s5, s6, s8) | własne (P3Net) | NG | piramida 2^(k+1) z bootstrapem całych poziomów; wszystkie poziomy przemiatane niezależnie (≠ kaskada P3); FOS z korzeniem, bez singletonów; jeden dawca (no-opy liczone do κ); akceptacja łańcucha vs przodek; surogat = addytywny Ridge na wszystkich parach (linkage nieużywany); telescoping kolapsuje | **Info+**: świeże f2 kandydatów (H7) — na NAS-HPO-II/FCNet to czas treningu z tabeli | wnioski o „P3Net” dotyczą tego wariantu; „linkage-aware” i „bound on telescoping error” nie mają pokrycia w kodzie; porównania z ramionami zewnętrznymi na NAS-HPO-II/FCNet z asymetrią B3 | W |
| `p3net` S4 (s1, s5) | własne | NG | jak S5, tylko najnowszy poziom aktywny | Info+ (H7) | jak S5 | W |
| `p3net_s1_initial` … `p3net_s4_eager_mixing` (s2) | własne | NG | etapy drogi: S1 OLS/f2 dziedziczony/pusty poziom/dominacja; S2 +f2; S3 +Ridge; S4 = 2 osie naraz (warm + HV); S4′ mieszanie od 2 | S1: brak Info+; S2+: Info+ | krok S3→S4 nie rozdziela warm startu i kryterium HV | W |
| 16 wariantów s4 (`p3net_cascade_*`) | własne | NG | progi 0.01/0.02/−0.01 w punktach procentowych błędu (pomijalne; różnią się głównie traktowaniem predykcji = 0); κ=2log ≈ κ=∞ z arytmetyki FOS; tylko 4 przestrzenie główne | `inherited_cost`: bez Info+ | „próg/κ nie mają znaczenia” — tylko dla tych skal; B3 nieizolowalne na FCNet | W |
| `p3_absolute_cascade` (final) | własne | NG | jak S5, surogat absolutny Ridge; różni się kotwiczeniem, regułą akceptacji (pierwszy krok real vs pred) i regularyzacją — nie linkage | Info+ | Q4 „względny vs absolutny” = test kotwiczenia/akceptacji, nie linkage | W |
| `p3net_bartnik` M7 (final, s5) | własne + RF jak w rekonstr. Bartnik | NG | silnik S5 + RF(100) absolutny; z Bartnik wspólny tylko surogat | Info+ (f2 z hooka nadpisuje RF) | nie odtwarza metody Bartnik | W |
| `p3net_bartnik_fihc` (final) | własne | NG | M7 + jednoprzebiegowy FIHC po f̂1 lasu | Info+ | kontrola M8 | W |
| `p3net_elympus` M8 (final, s5) | własne + eLyMPuS (k-arna generalizacja własna) | NG | kontrola + FIHC-eLyMPuS na predykcji lasu; pusty VIG, p=0.2, bez 1/x, circuit check, C4–C6; 6–12% decyzji błędnych vs bezpośrednie porównanie | Info+; mechanizm bez funkcji (nic do zaoszczędzenia) | nie wolno pisać „eLyMPuS nie pomaga” (4.3) | W |
| `bartnik_p3` (s1, s5) | praca Bartnik (w repo; korekta 2026-10-16) + SA-P3-GOMEA | RK | kanoniczny `climb` (FIHC jednoprzebiegowy, przerwanie wspinaczki, permisywna MO-poprawa, brak hashsetu), całe wnętrze na RF; bramka λ-kwantyl z okna prawdziwych różnic (≠ α-kwantyl predykcji z resetem do 1); NB201: f2 = FLOPs, f1 = test | Info−: f2 przewidywane RF, mimo że dostępne | wnioski o „kanonicznym P3 w naszej rekonstrukcji”, nie o Bartnik/SA-P3-GOMEA; B1 nie jest czystym kontrastem piramid | W (kod), N (wierność Bartnik) |
| `przewozniczek_p3elympus` M9 (s1, s5) | LyMPuS GECCO'26 + własna generalizacja | NG | `bartnik_p3` z FIHC-eLyMPuS (skalarny f̂1); GOM/promocja na RF; cache ≤ 5 wspinaczek | Info− (jak bartnik) | jak M8; M9 vs `bartnik_p3` skonfundowane (skalaryzacja + mechanizm) | W |
| `canonical_p3_scalar_fihc` M10 (s1, s5) | własne (kontrola B4) | NG | M9 z plain FIHC na tym samym skalarnym f̂1 | Info− | **izoluje mechanizm porównania** (M9 vs M10) | W |
| `p3_alone`, `_pop20`, `_pop40` (s1) | P3 (nominalnie) | UW | płaska populacja FIFO, GOM z prawdziwą ewaluacją, jednokryterialny, bez FIHC/piramidy | Info−: ignoruje f2; głodzony budżetem z założenia | „P3 bez surogatu” tylko w tym sensie | W |
| `p3_absolute` (s1) | własne | UW | piramida S4-podobna + OLS absolutny, f2 dziedziczony | brak Info+ | vs `p3net` — 3 osie naraz | W |
| `nsga_net` (s1) | Lu et al. 2019 | UW | NSGA-II bez turnieju, bez BOA, operatory ogólne | — | to ogólny NSGA-II | W |
| `nsganetv2` (s1) | Lu et al. 2020 | UW | filtr potomstwa OLS po samym f̂1; bez AS, bez wewn. NSGA-II, bez wyboru po złożoności | **Info−**: nie używa f2 kandydata (oryginał używa) | nie uogólniać na NSGANetV2 | W |
| `sh_emoa` (s1) | Guerrero-Viu et al. 2021 (cyt. w v0.0.3 błędnie: SMS-EMOA) | UW | tylko część EMOA (SMS-EMOA-podobna), bez SH; turniej bez rozstrzygania remisów po HV | — | nazwa/cytowanie do poprawy (B5) | W |
| `mo_bohb` (s1) | Guerrero-Viu et al. 2021 (cyt. w v0.0.3: BOHB) | AB+UW | sam próbnik KDE BOHB przy jednej wierności, losowa waga Tchebycheffa per wynik | Info−: zaszumiony sygnał | nie jest MO-BOHB; wygrane z nim słabe (B5) | W |
| `hyperband_mo`, `asha_mo`, `bohb_mo` (s6, s7, s8) | Li et al. 2018/2020, Falkner et al. 2018 | RK (+AB próbnik BOHB) | koszt w ekwiwalentach epok; front tylko z pełnych ocen (~46–66% punktów); ASHA 1 worker; JAHS niższe epoki z surogatu | — | Q7 = równy koszt epok, nie równa liczba ocen | W |
| `oss_vizier` (s1/s6/s8, gp-small) | Song et al. 2022; google-vizier 0.1.24 | AB | domyślny GP-UCB-PE, kategorie po indeksach | Info−: tylko b ≤ 100 | brak wniosków dla b ≥ 200 | W |
| `botorch_qnehvi`, `botorch_qparego` (gp-small) | BoTorch 0.18.1 | AB | MixedSingleTaskGP, akwizycja maksymalizowana po puli (losowa + sąsiedzi frontu) | Info−: tylko b ≤ 100 | jw. | W |
| `smac3_parego` (s1) | SMAC3 2.4.1 | AB | `n_trials=10⁷` ⇒ Sobol 10·d punktów (100/80/90) | **Info−**: przy b ≤ 100 (JAHS) czysty Sobol | wyniki SMAC3 przy b ≤ 100 ≈ quasi-RS | W |
| `tpe` (s1) | optuna 4.9.0 | AB | domyślne, `multivariate=False` | — | — | W |
| `nsga3` (s1) | optuna 4.9.0 | AB | domyślne, pop 20 | — | — | W |
| `moead` (s1) | pymoo 0.6.2 | AB | kodowanie porządkowe, SBX/PM + zaokrąglenie | **Info−**: przerywa przed budżetem (FCNet b ≥ 200: ~130 ocen) | wyniki MOEA/D na FCNet b ≥ 200 nie są „przy budżecie” | W |
| `regularized_evolution_mo` (s1) | Real et al. 2019 | NG (MO) | turniej po randze NDS | — | adaptacja MO własna | W |
| `mo_ls` (s1, s5) | PLS / White et al. 2021 | PI | pełne sąsiedztwo 1-współrzędnościowe | — | — | W |
| `reinforce_mo` (s1) | Zoph & Le 2017 | NG (MO) | polityka faktoryzowana; losowa waga nagrody per krok | — | adaptacja MO własna, nie strojona | W |
| `bananas_mo` (s1) | White et al. 2021 | AB/RK + NG | one-hot zamiast path encoding, MSE, kandydaci + losowi | — | adaptacja MO własna | Ś |
| `random_search` (s1, s5) | — | PI | jednostajnie na poprawnych genotypach | — | — | W |

---

## 13. Tabela hiperparametrów (do suplementu)

„YAML” = `implementation/experiments/configs/methods/<ramię>.yaml`; „kod” = wartość domyślna klasy/adaptera;
„bibl.” = domyślne biblioteki. n = długość genotypu (JAHS 10, NAS-HPO-II 8, FCNet 9, NB201 6).

| Ramię | Parametry (źródło) |
|---|---|
| P3Net (wszystkie `method: p3net`) | `growth_factor` 2 (YAML); rozmiar poziomu k = 2^(k+1) (kod); κ = 2⌈log₂n⌉ = 8 / 6 / 8 / 6 (kod, `kappa: null`); `acceptance_threshold` 0.0 (YAML); `objective_index` 0; surogat RidgeCV, α ∈ {0.1, 1, 10} (sklearn 1.9.0, `run_experiment.py:204`); `use_analytic_cost` true; `level_init` warm; `stall_criterion` hypervolume; `bootstrap_threshold` level_size; `truncation` pareto; `stall_recovery` reinject (1 genotyp); `donor_pool` h_t_only; `cascade` false (S4) / true (S5 i `final`, s4) |
| S1 / S2 / S3 / S4′ | S1: OLS, `use_analytic_cost` false, `level_init` empty, `stall_criterion` dominance; S2: jw. + `use_analytic_cost` true; S3: jw. + RidgeCV; S4′: S4 + `bootstrap_threshold` growth_factor |
| s4 | jak S5 z jedną zmianą: `use_analytic_cost` false · `truncation` f1_sort · `stall_recovery` grow · `donor_pool` transient · próg −0.01 · κ ∈ {1, ⌈log₂n⌉ (4 / 3), 2⌈log₂n⌉, 10⁶} × próg ∈ {0, 0.01, 0.02} |
| `p3_absolute_cascade` | S5 + `surrogate_kind` absolute_linear, RidgeCV |
| `p3net_bartnik` / `_fihc` / `p3net_elympus` | S5 + `surrogate_kind` absolute_rf, `rf_n_estimators` 100 (kod), `random_state` z rng; `hill_climber` none / fihc / fihc_elympus; `elympus_verify_probability` 0.2 (kod) |
| `bartnik_p3` | `warmup` n (null → n), `lambda_quantile` 0.5, `eta` 0.999, `n_estimators` 100, `max_climb_attempts` 5 (YAML); `delta_window_size` 50 (kod) |
| `przewozniczek_p3elympus` | jak `bartnik_p3` + `elympus_verify_probability` 0.2, `hill_climber` fihc_elympus (kod) |
| `canonical_p3_scalar_fihc` | jak wyżej, `hill_climber` fihc_scalar (YAML) |
| `p3_alone` / `_pop20` / `_pop40` | `population_size` 10 / 20 / 40 (YAML); limit 20 przemiatań bez nowej propozycji (kod) |
| `p3_absolute` | `growth_factor` 2, κ 2⌈log₂n⌉ (YAML/kod); OLS (`run_experiment.py:230`) |
| `nsga_net` | `population_size` 20, `mutation_rate` 0.1 (YAML); krzyżowanie jednorodne, rodzice losowi (kod) |
| `nsganetv2` | `population_size` 20, `offspring_pool_multiplier` 3 (YAML); mutacja 0.1, OLS (kod) |
| `sh_emoa` | `population_size` 20, `mutation_rate` 0.2, `crossover_probability` 0.5, `tournament_size` 3 (YAML) |
| `mo_bohb` | `top_n_percent` 15, `min_points_in_model` None (= d+1), budżet stały 1.0, Tchebycheff ρ=0.05 (kod); reszta hpbandster 0.7.4 |
| `hyperband_mo` / `asha_mo` / `bohb_mo` | η = 3, min 1 epoka (kod); E = 200 / 12 / 100; BOHB: hpbandster domyślne, Tchebycheff per liczba epok |
| `oss_vizier` | wszystkie domyślne `VizierGPUCBPEBandit` (google-vizier 0.1.24): `num_seed_trials` 1, trust region, `ard_random_restarts` 4, 1000 skalaryzacji HV; float64 |
| `botorch_qnehvi` / `qparego` | `n_initial` 2(n+1), `pool_size` 1024, `mc_samples` 128, `chunk_size` 256, `device` cpu (kod); ref. punkt 10% zakresu; reszta botorch 0.18.1 |
| `smac3_parego` | HPO facade domyślne (smac 2.4.1): Sobol 10·d (bo `n_trials` 10⁷), random design 0.2, RF; ParEGO domyślne |
| `tpe` | optuna 4.9.0: `n_startup_trials` 10, `n_ei_candidates` 24, `multivariate` False, gamma domyślna |
| `nsga3` | `population_size` 20 (YAML); optuna: `crossover_prob` 0.9, `swapping_prob` 0.5, `mutation_prob` 1/n, `dividing_parameter` 3 |
| `moead` | `n_weights` 20 (kod); pymoo 0.6.2: `n_neighbors` 20, `prob_neighbor_mating` 0.9, SBX(prob 1.0, η 20), PM(η 20), Tchebycheff |
| `regularized_evolution_mo` | `population_size` 20, `sample_size` 5 (YAML) |
| `mo_ls` | brak |
| `reinforce_mo` | `learning_rate` 0.1, `baseline_momentum` 0.9 (YAML); logity startowe 0 |
| `bananas_mo` | `n_initial` 10, `ensemble_size` 5 (YAML); 10 × 20 neuronów, Adam lr 0.01, 200 iteracji, 100 + 100 kandydatów (kod) |
| `random_search` | brak |
| Harness | `ExplorationCollapse`: okno 20, min. 20% unikalnych; `threads_per_run` 2; deduplikacja per metoda |

---

## 14. Lista ograniczeń do sekcji Limitations

Kolejność: od najsilniej wpływających na interpretację.

1. **Świeże f2 tylko dla P3Net** (H7, 3.3). Na NAS-HPO-Bench-II i FCNet f2 to zmierzony czas treningu — S5 i warianty
   `final` znają go dla kandydatów przed ewaluacją. Izolacja tylko na 4 przestrzeniach głównych (`inherited_cost`).
2. **Surogat „linkage-aware” nie korzysta z linkage** (3.2): korzeń w FOS ⇒ wszystkie pary użyte, predykcja niezależna
   od F; liniowy model antysymetryczny = różnica addytywnej funkcji; telescoping kolapsuje (κ nie ogranicza błędu).
3. **Silnik P3Net odbiega od P3** (3.1): poziomy 2^(k+1) bootstrapowane w całości, generacyjne przemiatanie wszystkich
   rodziców, brak FIHC, FOS z korzeniem i bez singletonów, jeden dawca (no-opy), „cascade” ≠ kaskada P3.
4. **Kanoniczne P3 (bartnik/M9/M10) są rekonstrukcjami z wnętrzem na surogacie** (4.1–4.2): FIHC jednoprzebiegowy,
   przerywana wspinaczka, piramida z osobników nieocenionych, bramka różna od SA-P3-GOMEA; f2 przewidywane, nie
   liczone; porównanie z pracą Bartnik (korekta 2026-10-16, §4.2): brak FIHC i ewaluacje wewnątrz GOM u autorki, warm-up 100, inna bramka — rekonstrukcja niewierna.
5. **eLyMPuS w roli bez funkcji** (4.3): porównuje darmowe predykcje lasu, nie prawdziwe ewaluacje; k-arna generalizacja
   własna, niepublikowana; 6–12% decyzji przybliżonych błędnie; brak 1/x, circuit check, C4–C6, PXrLL, ILS.
6. **Baseline'y uproszczone względem nazw**: NSGA-Net (bez BOA/turnieju), NSGANetV2 (OLS, bez AS, bez wyboru po
   złożoności, f2 ignorowany), SH-EMOA (bez SH), MO-BOHB (jedna wierność, KDE na losowej skalaryzacji), P3-alone (płaska
   populacja FIFO, jednokryterialna), BANANAS (one-hot, nie path encoding). Cytowania SH-EMOA/MO-BOHB do poprawy.
7. **Konfiguracje biblioteczne zmieniające charakter metody**: SMAC3 z `n_trials=10⁷` ⇒ 10·d punktów Sobola (b ≤ 100 na
   JAHS = czysty Sobol); MOEA/D przerywa przed budżetem (FCNet b ≥ 200).
8. **GP tylko b ≤ 100** (gp-small), rodziny Holma przy 200/350 mniejsze.
9. **Tor MF**: równy koszt w epokach, front z ~połowy punktów; JAHS niższe wierności z surogatu, nie z zapisu tego
   samego treningu.
10. **Dyskretyzacja** LR/WD na JAHS (8 × 6), stałe N/W/Resolution; kontrola ciągła (`nsganetv2_continuous`) nie istnieje.
11. **Jedna miara f2 per benchmark różna co do natury**: rozmiar modelu (JAHS, surogat), czas treningu (NAS-HPO-II, FCNet),
    FLOPs (NB201) — wnioski o „koszcie” nie są jednorodne między przestrzeniami.
12. **NB201 f1 = błąd testowy** (selekcja na teście), f2 = FLOPs zamiast energii (odstępstwo od Bartnik); s5 opisowe (D6).
13. **Progi s4 w jednostkach f1 bez normalizacji** (0.01–0.02 p.p.); κ = 2log ≈ ∞ z konstrukcji FOS.
14. **Asymetria strojenia**: S5 projektowany na seedach 1–30 tych samych przestrzeni; baseline'y na ustawieniach
    domyślnych; populacje 20 to wybór, nie strojenie.
15. Adaptacje wielokryterialne własne (RegEvo, REINFORCE, BANANAS, MO-BOHB, bohb_mo): losowa skalaryzacja per krok w
    czterech z nich.
16. Odrzucanie komórek bez ścieżki wejście–wyjście (Validity) we wszystkich ramionach — decyzja projektu, nie benchmarku.

---

## 15. Propozycje poprawek implementacji (tylko opcje, do decyzji autora; bez uruchamiania)

Bez nowych przebiegów (tekst/analiza):
- P-T1. Opisać surogat zgodnie z kodem: „globalny addytywny Ridge trenowany na wszystkich parach H_t”; usunąć „linkage-aware”
  albo zdefiniować; usunąć uzasadnienie κ przez błąd telescopingu.
- P-T2. Opisać S5 jako „all-levels-active pyramid”, nie „cascade” w sensie P3; poprawić „2^k” na 2^(k+1) lub zmienić opis.
- P-T3. Przemianować baseline'y (B5) i poprawić cytowania SH-EMOA/MO-BOHB → Guerrero-Viu et al.
- P-T4. Raportować SMAC3 przy b ≤ 100 z adnotacją „initial design only”; MOEA/D na FCNet z faktycznym zużyciem budżetu.
- P-T5. W Q4 dodać eksploracyjnie M8 vs `p3net_bartnik_fihc` i M9 vs M10 jako jedyne izolacje mechanizmu porównania,
  z zastrzeżeniem z 4.3.

Wymagające zmiany kodu i nowych przebiegów (opcje):
- P-K1. Usunąć korzeń z FOS i dodać singletony (P3-zgodnie) — wtedy ograniczenie par w surogacie zaczyna działać. Wariant
  s4-podobny na S5.
- P-K2. `inherited_cost` (lub doliczanie zapytań f2 do budżetu) na FCNet; alternatywnie hook f2 dla wszystkich ramion
  surogatowych (NSGANetV2, Bartnik/M9/M10) na JAHS, gdzie rozmiar jest liczalny.
- P-K3. Dawca różniący się na F (P3) i niewliczanie no-opów do κ.
- P-K4. Kryterium wzrostu na wszystkich nowych obserwacjach (HV po dodaniu całej partii), nie na jednej „najlepszej”.
- P-K5. SMAC3: `n_trials` = budżet (initial design 25% budżetu) albo jawne `n_configs`.
- P-K6. MOEA/D: eliminacja duplikatów / mutacja kategoryczna, albo raport z faktycznym budżetem.
- P-K7. NSGANetV2: wewnętrzny NSGA-II na (f̂1, f2) i wybór podzbioru po f2; AS między kilkoma regresorami.
- P-K8. eLyMPuS z prawdziwymi ewaluacjami liczonymi do budżetu (wspinaczka jako maszyna stanów, jak `p3_alone`), strategia
  1/x, circuit check, FIHC do optimum; test na pułapkach k-arnych + binarnym kodowaniu + NAS-HPO-II (4.3).
- P-K9. Kanoniczny `climb`: FIHC do lokalnego optimum, przejście przez wszystkie poziomy, hashset, prawdziwe f2 z hooka.
- P-K10. Progi s4 znormalizowane (np. ułamek rozstępu f1 w H_t).

---

## 16. Nieustalone

- Wersje pakietów na maszynie obliczeniowej (manifest nie sprawdzony pod tym kątem).
- Czy `size_MB` z JAHS zależy od hiperparametrów dla stałej architektury.
- Częstość no-opów i propozycji „kopia dawcy” (korzeń) w przemiataniach P3Net; jak często κ faktycznie przerywa przemiatanie.
- Wielkość efektu reguły „jedna najlepsza obserwacja” na tempo wzrostu piramidy (3.1).
- Czy `ExplorationCollapse` zatrzymała którykolwiek przebieg (z 1.9: wszystkie poza MOEA/D zużyły budżet, więc praktycznie
  nie — ale dla MOEA/D nie rozróżniono H3 od H4; mechanizm z kodu wskazuje H3).
- Zgodność `sh_emoa`, `mo_bohb` z kodem referencyjnym Guerrero-Viu (`automl/multi-obj-baselines`) — tylko deklaracje w
  docstringach.
- ~~Wierność `bartnik_p3` wobec pracy Bartnik (brak źródła)~~ — rozstrzygnięte 2026-10-16 (§4.2): niewierna; „Algorithm 7/8” = numeracja pracy Bartnik.
- Jakość decyzji eLyMPuS na NB201 i na pozostałych przestrzeniach / seedach (zmierzone: 1 seed × 3 przestrzenie).
- Wpływ niezależnej (`multivariate=False`) TPE i porządkowego kodowania MOEA/D na wyniki — tylko mechanizm.
- Czy różnice (a)–(c) z 3.2 przekładają się na różnicę S5 vs `p3_absolute_cascade` — przebieg 2 (Q4).

---

## 17. Porównanie z `INITIAL_FINDINGS.md` (otwarte po zakończeniu sekcji 0–16)

Tylko punkty dotyczące implementacji; wyniki jakościowe zostają dla przebiegu 2.

| Punkt w INITIAL_FINDINGS | Ten audyt | Zgodność |
|---|---|---|
| eLyMPuS w P3Net i M9 pyta las losowy, mechanizm oszczędzania nie jest testowany; M8 vs kontrola czyste co do celu | zgodne (4.3); dodatkowo zmierzone 6–12% błędnych decyzji vs bezpośrednie porównanie i brak elementów publikacji (1/x, circuit check, FIHC do optimum) | zgodne, uzupełnione |
| „MOEA/D często nie zużywa budżetu na FCNet/NAS-HPO (np. 46–81 ewaluacji zamiast 350)” | FCNet: tak (b=350: 119/120 przebiegów przerwanych, min 46–81); **NAS-HPO-II: rzadko** (7/240, min 76); JAHS 2/720 | częściowo — „NAS-HPO” zawyżone |
| „`surrogate_quality_log` zawiera tylko zaakceptowane i ocenione kandydatury” — założenie niesprawdzone | **potwierdzone w kodzie**: wpis powstaje w `update()` tylko dla genotypów z `_pending_predictions`, czyli członków C* zaproponowanych do ewaluacji (`p3net.py:376-387, 674-695`); predykcja = końcowa ocena łańcucha (S5: zakotwiczona; RF: po ewentualnym FIHC). Próba jest więc wyselekcjonowana (niezdominowane estymaty), a predykcje S5 i RF nie są tego samego rodzaju (kotwica vs absolutna) — porównanie korelacji pred/true między nimi jest obciążone | potwierdzone, z zastrzeżeniem |
| Q4: akceptacja i FIHC po samym f1 przesuwają wyszukiwanie ku dokładnym, drogim modelom | zgodne z mechaniką: w całej rodzinie P3Net akceptacja kroków i FIHC używają wyłącznie f1; f2 wchodzi tylko przy C* (3.1, 3.6) | mechanizm zgodny |
| `inherited_cost` ≈ S5 w 16/16 | wariant istnieje tylko na 4 przestrzeniach głównych; na FCNet (f2 = czas z tabeli) asymetria B3 nieizolowana (3.3) | uzupełnienie: wniosek nie obejmuje FCNet |
| Kanoniczne P3 w czołówce na FCNet / NAS-HPO-II | to ramiona z f2 przewidywanym RF i całym wnętrzem na surogacie (4.1) — jeśli wygrywają, to mimo braku Info+, nie dzięki niej | kontekst do przebiegu 2 |
| GP tylko b=50/100 | zgodne (9.1) | zgodne |
| — | Nowe względem INITIAL_FINDINGS: pusta restrykcja par w surogacie (korzeń w FOS), kolaps telescopingu, SMAC3 = czysty Sobol przy b ≤ 100 na JAHS, progi s4 w p.p. błędu, κ=2log ≈ κ=∞, różnice S5 vs `p3_absolute_cascade` (kotwica/akceptacja/regularyzacja), cytowania SH-EMOA/MO-BOHB | — |

