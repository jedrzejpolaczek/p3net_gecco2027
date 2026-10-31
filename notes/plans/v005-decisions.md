# v005 — rejestr skrótów i decyzji projektowych (A2)

Status: **PRZYJĘTY** (2026-10-16). Wszystkie pozycje rozstrzygnięte; obowiązujące szczegóły — w kartach `v005-sources/*.md` (karta ma pierwszeństwo przed opisem w tabelach poniżej, np. #21 → N z operatorami kategorycznymi, #28 → własny pomiar energii).

## Decyzja autora (2026-10-16)

- **Zostają (zaakceptowane, opisane w artykule):** #25, #30, #31, #32, #33, #34, #35, #36, #37.
- **Wszystkie pozostałe pozycje są do usunięcia (kategoria N)**, w tym wcześniej proponowane jako P/O: #21 (operatory
  kategoryczne w MOEA/D), #22 (kodowanie hybrydowe BANANAS + MAE i kandydaci wg autorów), #24 (wersje wielokryterialne z
  literatury), #26 (rozmiar liczony analitycznie), #28 (zmierzona energia zamiast FLOPs), #30 (GP przy b = 200/350).
- #5: przebudowa silnika P3Net zgodnie z P3 (decyzja 2026-10-16).
- Rozstrzygnięcia #13, #24, #28, #30 i reguła „poprawy” dla #5 — na końcu; otwarte tylko: RegEvo (#24).
Źródło listy: `notes/analysis-v004/reports/01-implementation-audit.md` (R1) §14 i sekcje szczegółowe.
Przyczyny Z1–Z11: `notes/plans/v005-plan.md`, „Skąd wzięły się błędy v004”.

Kategorie:
- **N — naprawiamy** (kod zmieniony, test z karty źródła),
- **P — decyzja projektu** (świadomy wybór, dotyczy wszystkich ramion jednakowo, opisany w artykule),
- **O — ograniczenie** (nie da się naprawić w tym projekcie; w Limitations).

Zasada na przyszłość: każde nowe udogodnienie lub odstępstwo dotyczące jednej metody wymaga wpisu tutaj przed
implementacją, z decyzją o symetrii.

## 1. P3Net (rdzeń)

| # | Skrót w v004 | Przyczyna | Kat. | Propozycja | Akcept. |
|---|---|---|---|---|---|
| 1 | Korzeń w zbiorach mieszania, brak singletonów, brak filtra D=0, kolejność losowa ⇒ surogat uczy się na wszystkich parach, predykcja nie zależy od F (R1 §3.1–3.2) | Z1, Z2 | N | FOS wg Goldmana & Puncha (bez korzenia, z singletonami, filtr D=0, od najmniejszych); test integracyjny „surogat dostaje < 100% par” | ☑ |
| 2 | Jeden losowy dawca ⇒ 13–24% no-opów, akceptowanych w ~50% przez szum numeryczny, liczonych do κ (R2 §4.3) | Z1 | N | Dawca różniący się w danym F (szukanie do skutku, jak w P3); no-opy nie liczą się do κ | ☑ |
| 3 | Akceptacja kroku względem przodka x₀, tekst mówi: względem bieżącego osobnika (R1 §3.2) | Z8 | N | Wzorcem tekst: akceptacja względem bieżącego | ☑ |
| 4 | Kryterium wzrostu poziomu liczone dla jednej „najlepszej” obserwacji partii (R1 §3.1) | Z8 | N | HV poziomu po dodaniu całej partii | ☑ |
| 5 | Rozmiary poziomów 2^(k+1), losowe zapełnianie poziomów, przemiatanie całej populacji poziomu; „cascade” = wszystkie poziomy przemiatane niezależnie — silnik to piramida populacji GOMEA/LTGA, nie P3 (R1 §3.1) | Z1, Z8, Z12 | N | **Decyzja 2026-10-16: przebudować silnik P3Net zgodnie z P3** (Goldman & Punch): jedno nowe rozwiązanie na iterację wspina się przez wszystkie poziomy, mieszanie z populacją każdego poziomu, poziomy bez rozmiarów docelowych, unikalność w piramidzie; odstępstwa tylko tam, gdzie wymaga ich surogat, każde w karcie źródła | ☑ |
| 6 | Darmowe f2 kandydatów tylko dla P3Net | Z7 | N | Usunąć hook dla wszystkich (decyzja A3) | ☑ |
| 7 | Progi akceptacji w s4 w jednostkach f1, bez normalizacji (R1 §3.5) | Z8, Z3 | N | Próg jako ułamek rozstępu f1 w H_t | ☑ |
| 8 | Surogat: liniowy Ridge na surowym f1 (na FCNet R² ≈ 0), siatka α {0.1, 1, 10}, LOO na parach dzielących punkty | Z3 | N | Nowy surogat S6 (decyzja A5c): log(f1) lub strata rankingowa, interakcje w obrębie F, walidacja niezależna od par | ☑ |
| 9 | Uzasadnienie κ błędem telescopingu (kolaps sumy dla modelu liniowego; R1 §3.2) | Z8 | N | Po zmianie surogatu sprawdzić, czy telescoping jest nietrywialny; uzasadnienie κ zgodne z tym, co model robi | ☑ |

## 2. Kanoniczne P3 i rekonstrukcja Bartnik

| # | Skrót w v004 | Przyczyna | Kat. | Propozycja | Akcept. |
|---|---|---|---|---|---|
| 10 | FIHC jednoprzebiegowy, akceptuje remisy; wspinaczka przerywana na pierwszym poziomie bez poprawy; brak hashsetu (R1 §4.1) | Z1 | N | `climb` wg Goldmana & Puncha (FIHC do lokalnego optimum, ścisła poprawa; mieszanie z każdym poziomem; unikalność) | ☑ |
| 11 | Wnętrze wspinaczki na lesie losowym; piramida z osobników nigdy nieocenionych (R1 §4.1) | Z6 | N | Ramiona z prawdziwymi ewaluacjami krok po kroku (decyzja A7); obecne surogatowe zostają jako osobne, opisane | ☑ |
| 12 | Rekonstrukcja Bartnik niewierna: FIHC, ewaluacje tylko na końcu, warm-up 6, bramka λ=0.5 z prawdziwych różnic (R1 §4.2) | Z1, Z10 | N | Wierny MO-DSA-P3-GOMEA + MO-PSA (decyzja A6); test odtworzenia Tabeli 7.1 na NB201, budżet 500 | ☑ |
| 13 | f2 przewidywane lasem (przy darmowym f2 dla P3Net) | Z7 | P | Po #6 symetryczne: wszyscy przewidują lub znają f2 tylko z ewaluacji; opisać | ☑ |
| 14 | eLyMPuS: k-arna generalizacja własna, porównania na lesie, p=0.2 zamiast 1/x, bez circuit check (R1 §4.3) | Z1, Z6 | N | Osobny tor (decyzja A7): prawdziwe ewaluacje, elementy z publikacji; wynik do suplementu | ☑ |

## 3. Baseline'y

| # | Skrót w v004 | Przyczyna | Kat. | Propozycja | Akcept. |
|---|---|---|---|---|---|
| 15 | NSGA-Net: rodzice losowi (bez turnieju), bez BOA, operatory ogólne (R1 §6.1) | Z1 | N | Turniej binarny; BOA wg publikacji albo jawne odstępstwo w karcie źródła | ☑ |
| 16 | NSGANetV2: OLS, wybór po samym f̂1, bez adaptacyjnego wyboru surogatu, bez NSGA-II na surogacie i bez złożoności (R1 §6.2) | Z1 | N | Wg publikacji i kodu autorów (AS, wewnętrzny NSGA-II na (f̂1, f2), wybór podzbioru) | ☑ |
| 17 | SH-EMOA bez części SH; turniej bez rozstrzygania remisów po HV (R1 §7.1) | Z1 | N | Pełna wersja w torze MF; w torze głównym część jednowiernościowa pod poprawną nazwą; wg `automl/multi-obj-baselines` | ☑ |
| 18 | MO-BOHB jednowiernościowy, losowa waga Tchebycheffa przy każdej obserwacji (R1 §7.2) | Z1 | N | Pełna wersja w torze MF wg `automl/multi-obj-baselines`; część jednowiernościowa pod poprawną nazwą | ☑ |
| 19 | SMAC3: `n_trials=10⁷` ⇒ projekt początkowy 10·d (przy b ≤ 100 na JAHS czysty Sobol) | Z3, Z4 | N | `n_trials` = budżet; asercja: projekt początkowy ≤ 25% budżetu | ☑ |
| 20 | MOEA/D przerywa przed budżetem (FCNet b ≥ 200) | Z4, Z5 | N | Eliminacja duplikatów / ponowne próbkowanie; asercja pełnego zużycia budżetu | ☑ |
| 21 | MOEA/D: kodowanie porządkowe kategorii (SBX/PM + zaokrąglenie) | Z3 | O | pymoo nie ma kategorycznego MOEA/D; opisać jako ograniczenie (alternatywa N: własne operatory kategoryczne) | ☑ |
| 22 | BANANAS: one-hot zamiast path encoding; MSE zamiast MAE; kandydaci także losowi (R1 §10) | Z1 | P + N | Path encoding nie obejmuje HP → one-hot zostaje (P, opisane); MAE i kandydaci wg kodu autorów (`naszilla`) (N) | ☑ |
| 23 | P3-alone: płaska populacja FIFO, jednokryterialna, bez piramidy i FIHC — nie jest P3 (R1 §5.1) | Z1 | N | Ablację „P3 bez surogatu” przejmuje kanoniczne P3 na prawdziwych ewaluacjach (#11); P3-alone usunąć z v005 albo przemianować | ☑ |
| 24 | Adaptacje wielokryterialne własne z losową wagą przy każdym kroku (REINFORCE, RegEvo, BANANAS, BOHB) | — | P | Zostają, opisane jako adaptacje projektu; dla REINFORCE rozważyć stałą wagę na epizod | ☑ |

## 4. Benchmarki i pomiary

| # | Skrót w v004 | Przyczyna | Kat. | Propozycja | Akcept. |
|---|---|---|---|---|---|
| 25 | JAHS: niższe wierności w torze MF z surogatu (`nepochs=e`), nie z zapisu tego samego treningu | — | O | Ograniczenie benchmarku; opisać przy wynikach MF | ☑ |
| 26 | JAHS: f2 = `size_MB` z surogatu JAHS | — | O + test | Sprawdzić, czy zależy od HP przy stałej architekturze; jeśli tak — liczyć parametry analitycznie (N). **Wynik 2026-10-16: zależy (200/200 komórek) → f2 = analityczna liczba parametrów** (`benchmarks.md` BM-3) | ☑ |
| 27 | NB201: f1 = błąd testowy (selekcja na teście) | Z1 | N | f1 = błąd walidacyjny (`cifar10-valid`), test jako metryka po przebiegu | ☑ |
| 28 | NB201: f2 = FLOPs, prawie jednokryterialne (ρ z dokładnością 0.749 wg Bartnik) | — | O | Energii nie mamy; opisać (NB201 tylko jako krótka uwaga, decyzja B2) | ☑ |
| 29 | s9 bez pamięci mostu JAHS i GPU; brak czasu ładowania mostu | Z5 | N | Rejestracja + asercja niepustych pól (decyzja A8) | ☑ |
| 30 | GP tylko przy b ≤ 100 | Z11 | O | Osobna tabela (decyzja A8) | ☑ |

## 5. Decyzje protokołu (wspólne dla wszystkich ramion, do potwierdzenia)

| # | Decyzja | Kat. | Uwagi | Akcept. |
|---|---|---|---|---|
| 31 | Dyskretyzacja HP na JAHS (LR 8, WD 6 wartości); N/W/Resolution zamrożone na maksimum | P | Wspólna; brak ramienia ciągłego (kontrola NSGANetV2-continuous — B5) | ☑ |
| 32 | Tor główny jednowiernościowy, budżet = liczba pełnych ewaluacji; tor MF osobno, koszt w ekwiwalentach epok | P | — | ☑ |
| 33 | Odrzucanie komórek bez ścieżki wejście–wyjście (Validity) | P | Benchmarki takie komórki mają; decyzja wspólna | ☑ |
| 34 | Harness ask–tell; metoda nie ma dostępu do benchmarku poza propozycjami | P | Nie zabrania ewaluacji krok po kroku (#11) | ☑ |
| 35 | Deduplikacja po stronie metody; duplikat nie zużywa budżetu | P | Do asercji w `checks` | ☑ |
| 36 | `ExplorationCollapse` (stop przy < 20% unikalnych w oknie 20) | P | Opisać; asercja, czy kiedykolwiek się wyzwala | ☑ |
| 37 | Populacje 20 w metodach populacyjnych; hiperparametry baseline'ów domyślne / z oryginałów, bez strojenia | P | Asymetria strojenia opisana (etap C) | ☑ |

## Punkty otwarte — rozstrzygnięcia (2026-10-16)

| # | Rozstrzygnięcie |
|---|---|
| 5 | Silnik P3Net przebudowany zgodnie z P3 (opcja b); obecna piramida nie jest utrzymywana. **„Poprawa” przy ≥ 2 celach = relacja Pareto** (dokładna reguła — nie zdominowany / dominujący / wejście na front — do zapisania w karcie źródła P3Net) |
| 13 | Zamknięte: nikt nie dostaje darmowego f2 (#6), więc warunki są równe |
| 24 | Wynik wyszukiwania literatury: **BANANAS** — istnieje MO-BANANAS (Guerrero-Viu et al. 2021, kod `automl/multi-obj-baselines`) → użyć go. **REINFORCE** — opublikowane nagrody wielokryterialne: MnasNet (iloczyn ważony dokładność × (koszt/cel)^w), MONAS (nagroda łącząca dokładność i energię), Chen et al. 2020 (niestacjonarny gradient polityki, cały front) → wybrać jedną z publikacji zamiast naszej losowej wagi. **RegEvo** — nie znaleziono opublikowanej wielokryterialnej wersji regularized/aging evolution (najbliższe: LEMONADE — inna metoda; Age-Fitness Pareto Optimization — poza NAS) → **do decyzji autora: nasza adaptacja jawnie opisana albo usunięcie ramienia** |
| 28 | **[Nieaktualne 2026-10-31: zastąpione decyzją P1 a — energia NB201 z HW-NAS-Bench, edge GPU; `v005-todo.md`, `v005-sources/benchmarks.md` BM-2]** ~~Własny pomiar energii GPU dla NB201~~ (dostępne są tylko publikacje, bez pomiarów Bartnik). Metodyka wg pracy Bartnik (pyNVML, rozgrzewanie i powtórzenia, cache po indeksie architektury); energia jest specyficzna dla sprzętu — opisać |
| 30 | **Zaakceptowane jako ograniczenie** (brak maszyny): GP tylko przy b = 50/100, osobna tabela (zgodne z A8) |

## Rozstrzygnięcia #24 i zestawu metod (2026-10-16, cd.)

| Kwestia | Decyzja |
|---|---|
| RegEvo (brak opublikowanej wersji wielokryterialnej) | **Zostaje nasza adaptacja** (turniej po randze Pareto, usuwanie najstarszego); **jawnie odnotowana w artykule** jako jedyna własna adaptacja wielokryterialna; karta źródła z opisanym odstępstwem |
| REINFORCE — nagroda wielokryterialna | Otwarte: przegląd literatury (bez bezpośredniego porównania nagród w HV) — decyzja autora po przeglądzie |
| MO-BANANAS | Używamy wersji z Guerrero-Viu et al. 2021 (`automl/multi-obj-baselines`) |
| MS-EHVI, BULK & CUT (Bag of Baselines) | **Dodajemy obie.** Otwarte: MS-EHVI z założenia liczy tani cel wprost — kolizja z #6 (darmowe f2 dla nikogo) do rozstrzygnięcia |

## REINFORCE i MS-EHVI — decyzje (2026-10-16, cd.)

| Kwestia | Decyzja |
|---|---|
| REINFORCE — nagroda | **Trzy warianty**: nagroda MnasNet (`tan2019mnasnet`, iloczyn ważony dokładność × (koszt/cel)^w), MONAS (`hsu2018monas`, nagroda łącząca dokładność i koszt), Chen et al. (`chen2020mononstationary`, nagroda zmienna w czasie śledząca cały front). Źródła dopisane do `refs.bib`. W artykule wyjaśnić pochodzenie: literatura nie porównuje tych nagród bezpośrednio w HV/IGD+; MnasNet i MONAS szukają punktu kompromisu, Chen et al. — frontu |
| MS-EHVI | **Bez darmowego f2** — modeluje także koszt (zgodne z #6). Odstępstwo od źródła opisane w karcie źródła i w artykule |
| MS-EHVI → EHVI (2026-10-16) | Bez taniego celu liczonego wprost MS-EHVI = zwykły EHVI (baza z Tab. 1 źródła) → w artykule nazwa **EHVI** (`v005-sources/bag-of-baselines.md`) |
| BULK & CUT (2026-10-16) | **Usunięty** (zmiana decyzji „dodajemy obie”): wymaga morfizmów sieci, przycinania i destylacji na wytrenowanych wagach, czego benchmarki tablicowe/surogatowe nie dają. Kategoria O, opis w artykule |
| MO-SH-BANANAS (2026-10-16) | Dodany do toru MF (wersja użyta w eksperymentach źródła) |
| Bramka MO-DSA (2026-10-18) | **Z-B1 → Z-B1′**: Alg. 8 osobno dla każdego celu z relaksacją α (pod Z-B1 bramka nie luzowała się i MO-DSA kończył się po rozgrzewce) — `v005-sources/bartnik-mo-sa-p3-gomea.md` N-1 |
| Dublowania (2026-10-16) | EHVI (BoB) = ramię **qNEHVI** (BoTorch); MOTPE (BoB) = **optuna `TPESampler`** — po jednym ramieniu (`v005-sources/library-adapters.md` A-1, A-2) |
