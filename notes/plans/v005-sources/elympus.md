# eLyMPuS na prawdziwych ewaluacjach — karta źródła

Status: **ZATWIERDZONA** (2026-10-16, autor projektu: O-E1, E-1 a, E-2 a, E-3 a, Z-E1–Z-E6, W-E1–W-E13 z W-E7b,
testy poziomu 2 i na NAS). Było: SZKIC (2026-10-16). Zatwierdza: autor projektu (bez konsultacji — protokół, decyzja 3;
niejasności jako założenia Z-E#, opisane w artykule).
Odpowiedź M. Przewoźniczka (2026-10-21) — przyczyna znaleziona (linkage z VIG, E-4); poziom 2 zamknięty (`v005-level2-criteria.md`). **Limitations:** pętla FIHC Goldmana zamiast pełnych przejść OLyMPuS (−13 % FFE na Dec5).
Rola (decyzja A7, #14): **osobny tor, wynik do suplementu.** Graf zależności zasiany wiedzą dziedzinową — **nie w v005**,
następna iteracja (`v005-plan.md`, „Następna iteracja”).

## 1. Źródła

- Przewoźniczek, Chicano, Tinós, Komarnicki, *Limited Perfect Monotonical Surrogates constructed using Variable
  Interaction Graphs*, GECCO'26 (`przewozniczek2026lympus`), s. 647–651. Plik:
  `notes/articles/linkage learn/Limited Perfect Monotonical Surrogates constructed using.pdf`. Suplement (PXrLL, OLyMPuS,
  Pseudocode S-3) — **nie w repo**.
- **Kod referencyjny:** `https://github.com/przewooz/OLyMPuS` (przypis 1 publikacji; C++, Windows, w archiwach zip;
  przeczytany 2026-10-16). eLyMPuS: `OptFrame/IslandGA/DecompUtilsGeneral.cpp` (`CBinary_DcmpUtil_LimitedSurrogate*`,
  FIHC-eLyMPuS: `dComputeFitnessOptimize_LimitedSurr_FIHC_like`, 1/x: `vRefreshStrategy_Reset`). Konfiguracje
  eksperymentów: `exp_POLiNoMok/…/settings_P3_LSur1nth_*.txt`. **Kod jest wyłącznie binarny** (`CBinaryOptimizer`,
  `vFlipGene`).
- Silnik bazowy: kanoniczne P3 (`p3-canonical.md`, zatwierdzona).

Dlaczego karta (R1 §4.3): w v004 eLyMPuS porównywał **predykcje lasu losowego** (więc nie oszczędzał żadnej prawdziwej
ewaluacji), miał stałe p = 0.2 zamiast 1/x, nie miał circuit check, FIHC robił jedno przejście, cache żył jedną wspinaczkę,
a pusty VIG oznaczał, że wynik porównania był używany dla każdego innego genotypu.

## 2. Mechanizm wg źródła

Numeracja E# używana w testach.

### Model (§3.1–3.2, Pseudocode 1–2)

- **E1.** VIG (graf zależności zmiennych) na starcie **pusty**; dla każdej zmiennej g lista par (hiperplaszczyzna
  kontekstu, wynik porównania). Kontekst = wartości zmiennych zależnych od g według bieżącego VIG.
- **E2.** `PartialComparison(x, g)`: porównanie x z x′ różniącym się tylko na g. Szukaj na liście g pary, której kontekst
  pasuje do x (`FindPair`). Jest → wynik z listy (**bez ewaluacji**). Brak → policz naprawdę (`Compute`: f(x), f(x′)),
  dopisz parę.
- **E3.** Jeśli bieżące wywołanie weryfikuje (E8): wynik z listy jest sprawdzany prawdziwą ewaluacją; różnica ⇒ brakuje
  zależności między g a którąś zmienną różniącą x od rozwiązania z pary ⇒ `RecursiveLL`.
- **E4.** Pary dopisane wcześniej **zostają ważne** po uzupełnieniu VIG (nic nie jest tracone).
- **E5.** Twierdzenie 1: przy pełnym VIG wynik z listy jest zawsze poprawny.

### RecursiveLL (Pseudocode 3)

- **E6.** Dla dwóch rozwiązań o równym kontekście g, a różnym wyniku porównania: dziel zbiór różniących się zmiennych na
  pół, aż zostanie jedna; dopisz krawędź g–v do VIG (oba kierunki). Gwarancja: jedna brakująca zależność w ≤ ⌈log₂|D|⌉
  krokach.
- **E7.** Odkrywane są zależności spełniające C1–C3 (nie C4–C6).

### FIHC-eLyMPuS (Pseudocode 4) i strategia 1/x

- **E8.** Na starcie wywołania decyzja „weryfikować czy nie” wg **1/x**: po wywołaniu z weryfikacją licz x kolejnych
  wywołań z weryfikacją bez znalezienia brakującej zależności; następna weryfikacja po x + 1 wywołaniach bez niej.
- **E9.** Losowa permutacja zmiennych; `repeat` przejście po wszystkich zmiennych z `PartialComparison`; przy poprawie
  zmiana i zapis kroku w ciągu T; `until` brak poprawy (**lokalne optimum**).
- **E10.** Po każdym kroku poprawiającym `CheckCircuits` (Pseudocode 5): jeśli T wraca do już odwiedzonego rozwiązania,
  któryś krok nie był poprawą ⇒ znajdź go (prawdziwe ewaluacje) i uruchom `RecursiveLL`; wyczyść T.

### Optymalizator

- **E11.** W publikacji FIHC-eLyMPuS **zastępuje FIHCwLL** w P3-FIHCwLL i LT-GOMEA-FIHCwLL; OLyMPuS dodaje PXrLL i krok ILS.

## 3. Parametry wg źródła

Brak (bezparametrowy). Budżet w publikacji: 2·10⁷ FFE i 12 h — rzędy wielkości więcej niż nasze 50–350.

## 4. Odstępstwa wymagane przez nasz problem

| # | Odstępstwo | Powód | Status |
|---|---|---|---|
| O-E1 | Genotyp k-arny: porównanie wartości b z bieżącą a na zmiennej g (k−1 porównań na zmienną) | nasze przestrzenie; publikacja: „not limited to the binary search space and apply to integer-based solution encoding” (§7) | do zatwierdzenia |
| O-E2 | Dwa cele (E-2) | problem wielokryterialny | wg E-2 |
| O-E3 | Silnik bazowy = kanoniczne P3 (E-1) | wg E-1 | wg E-1 |
| O-E4 | Ewaluacje z H_t (cache) są darmowe dla wszystkich metod | protokół (O-5, W15) | zatwierdzone (wspólne) |

## 5. Decyzje do podjęcia

### E-1. W jakim optymalizatorze

- **a) Kanoniczne P3 z FIHC zastąpionym przez FIHC-eLyMPuS.**
  - Za: ten sam silnik co kanoniczne P3 i P3Net — różnica „P3 vs P3+eLyMPuS” izoluje eLyMPuS; jest już zatwierdzony.
    **Kod referencyjny potwierdza, że to jest P3-eLyMPuS z publikacji:** konfiguracje `P3standard`, `P3_FIHCwLL` i
    `P3_LSur1nth` różnią się wyłącznie parametrem `limitedSurrogate_FIHCstrategy` (5 = FIHC, 4 = FIHCwLL, 2 = eLyMPuS
    z 1/x); optymalizator to w każdym przypadku to samo P3 (`optimizer_type = p3`). Można więc używać nazwy P3-eLyMPuS.
  - Przeciw: brak istotnych.
- **b) P3-FIHCwLL + FIHC-eLyMPuS jak w publikacji.**
  - Za: wierne publikacji.
  - Przeciw: P3-FIHCwLL to kolejne źródło do wiernej implementacji i kolejna karta; różnica wobec naszych metod miesza
    dwa mechanizmy.
- **c) OLyMPuS.** Przeciw: wymaga suplementu (brak w repo), PXrLL i ILS — największy koszt.

**Rekomendacja: a).**

### E-2. Dwa cele

Jedna prawdziwa ewaluacja daje oba cele naraz; zależności f1 i f2 są różne (f2 prawie addytywne — R² 0.70–1.00).

- **a) Osobny eLyMPuS (VIG + listy par) dla każdego celu;** krok FIHC przyjęty wg D-1 (dominacja) z wyników obu
  porównań; prawdziwa ewaluacja, gdy **którykolwiek** cel nie ma pary (albo weryfikacja).
  - Za: każdy VIG odzwierciedla zależności swojego celu; Twierdzenie 1 obowiązuje osobno dla każdego; VIG f2 będzie
    prawie pusty, więc porównania f2 tanio się uczą.
  - Przeciw: oszczędność tylko wtedy, gdy oba cele mają parę.
- **b) Jeden wspólny VIG (suma zależności).** Za: prostsze. Przeciw: kontekst większy niż trzeba dla f2 ⇒ mniej trafień.
- **c) eLyMPuS tylko dla f1.** Przeciw: f2 i tak wymaga ewaluacji, więc nic nie oszczędza (#6: f2 nie jest darmowe).

**Rekomendacja: a).**

### E-3. Wynik FIHC-eLyMPuS a zbiór wynikowy

Ścieżka FIHC może dojść do rozwiązania, którego nikt nie ocenił naprawdę (wszystkie kroki z list par).

- **a) Rozwiązanie końcowe FIHC oceniane naprawdę** (1 ewaluacja, chyba że jest w H_t) przed wejściem do piramidy.
  - Za: piramida i H_t zawierają tylko prawdziwe wartości (O-5); reguła D-1 i archiwum działają na prawdziwych danych.
  - Przeciw: koszt 1 ewaluacji na wywołanie.
- **b) Bez oceny.** Przeciw: rozwiązanie bez wartości celów nie może wejść do archiwum ani H_t; łamie O-5.

**Rekomendacja: a)** — kod referencyjny robi dokładnie to (Z-E2).

## 6. Niejasności — rozstrzygnięte w kodzie referencyjnym (2026-10-16)

| # | Pytanie | Co robi kod | Przyjmujemy |
|---|---|---|---|
| Z-E1 | Co jest zapamiętywane przy k > 2 | binarnie: dla (zmienna g, wartości kontekstu) zbiór **najlepszych wartości** g (`GeneContext_Values::v_best_values`; 1 wartość = jest lepsza, 2 = remis); kodu k-arnego brak | **generalizacja własna** (publikacja §7 zapowiada ją jako możliwą): dla (g, kontekst) zapamiętujemy **uporządkowanie wszystkich k wartości** g — tyle i tak ocenia krok FIHC (P11: wszystkie wartości g), więc koszt wpisu = koszt kroku FIHC; porównanie dowolnych dwóch wartości g w tym kontekście jest potem darmowe. Opisane w artykule jako nasze rozszerzenie |
| Z-E2 | Czy rozwiązanie końcowe FIHC-eLyMPuS jest oceniane naprawdę | tak: `dComputeFitness()` po pętli, liczone jako koszt FIHC | tak (E-3 a) |
| Z-E3 | Strategia 1/x | licznik globalny na przebieg (pola obiektu surogatu); weryfikacja **zawsze**, gdy VIG pusty; zawsze w wywołaniu następującym po wywołaniu, które odkryło zależność; licznik **zerowany**, gdy FIHC dojdzie do lokalnego optimum już wcześniej znalezionego (`v_update_optimized_individuals`) | dokładnie jak kod (te trzy reguły nie są opisane w publikacji — wymienić w artykule) |
| Z-E4 | eLyMPuS w mieszaniu P3 | nie: `limitedSurrogate_mixing = 0 (standardNoSurr)` w konfiguracji P3-eLyMPuS | nie |
| Z-E5 | Remis w FIHC | ruch tylko przy wyniku 1 (ścisła poprawa); remis = brak ruchu | brak ruchu; przy dwóch celach: ruch tylko przy dominacji (D-1) |
| Z-E6 | Typ zależności i kierunkowość | `dependencyType = nonMonotonical`, `directionalDependencies = 0` (symetryczne) | jak kod |

## 7. Własności do sprawdzenia testami (poziom 1)

| ID | Krok | Własność |
|---|---|---|
| W-E1 | E1 | VIG pusty na starcie (v005: bez wiedzy dziedzinowej) |
| W-E2 | E2 | Trafienie w listę par nie wywołuje benchmarku; brak trafienia = prawdziwe ewaluacje + dopisanie pary |
| W-E3 | E5 | Z **pełnym prawdziwym** VIG (problem syntetyczny) każdy wynik z listy jest poprawny (Tw. 1) |
| W-E4 | E6, E7 | Każda odkryta krawędź jest prawdziwą zależnością problemu (zero fałszywych krawędzi na pułapkach / NK o znanym VIG) |
| W-E5 | E6 | `RecursiveLL` znajduje zależność w ≤ ⌈log₂|D|⌉ podziałach |
| W-E6 | E4 | Pary dopisane przed uzupełnieniem VIG pozostają używane |
| W-E7 | E8, Z-E3 | Harmonogram weryfikacji zgodny z 1/x i trzema regułami kodu (pusty VIG, po odkryciu, reset przy powtórzonym optimum) — test na sekwencji zdarzeń |
| W-E7b | Z-E1 | Wpis dla (g, kontekst) powstaje z jednego kroku FIHC na g i zawiera uporządkowanie wszystkich k wartości; dla k = 2 zachowanie identyczne z kodem binarnym |
| W-E8 | E9 | FIHC kończy w lokalnym optimum (żaden ruch jednej zmiennej nie daje dominującej poprawy na prawdziwej funkcji, gdy VIG pełny) |
| W-E9 | E10 | `CheckCircuits` wykrywa powrót w T i uruchamia `RecursiveLL` |
| W-E10 | E-2 | Osobne VIG dla f1 i f2; prawdziwa ewaluacja, gdy któryś cel nie ma pary |
| W-E11 | E-3 | Każde rozwiązanie w piramidzie i H_t ma prawdziwe wartości |
| W-E12 | całość | Z weryfikacją zawsze włączoną: ta sama trajektoria i to samo optimum co zwykły FIHC (różni się tylko licznik ewaluacji) |
| W-E13 | całość | Pamięć (VIG, listy par) żyje przez cały przebieg |

**Test zgodności (poziom 2):** P3-eLyMPuS z kodu referencyjnego (gotowy `IslandGA.exe` w `zz_introduction`, konfiguracje
`settings_P3_LSur1nth_*`) vs nasz z k = 2, na Dec5 i mk-trapach (rozmiary z Tab. 5): liczba FFE do optimum i odsetek
odkrytych zależności, ±2 % median + TOST, 30 przebiegów. Kryterium zapisane przed testem.

**Test na NAS (suplement):** NAS-HPO-II i NB201 (dwa cele), budżet 50–350: P3 + FIHC-eLyMPuS vs kanoniczne P3 —
liczba prawdziwych ewaluacji oszczędzonych przez eLyMPuS, odsetek błędnych odpowiedzi z list (mierzony przez
weryfikację), HV. Oczekiwanie do prerejestracji: przy budżecie ≤ 350 oszczędności małe, bo odkrywanie VIG kosztuje.

**E-4 (2026-10-21, decyzja autora a, po teście poziomu 2):** linkage piramidy P3-eLyMPuS jak w OLyMPuS (`Population::get_distance`): odległość pary zmiennych, której VIG nie zna, +1. **Z-E7:** przy dwóch celach para jest „znana”, gdy zależność jest w VIG któregokolwiek celu. Test poziomu 1: Q-45.

## 8. Do zatwierdzenia

O-E1; E-1 (rek. a — potwierdzone kodem), E-2 (rek. a), E-3 (rek. a — potwierdzone kodem); Z-E1 (generalizacja k-arna,
własna), Z-E2–Z-E6 (wg kodu); W-E1–W-E13 z W-E7b; testy poziomu 2 i na NAS.
