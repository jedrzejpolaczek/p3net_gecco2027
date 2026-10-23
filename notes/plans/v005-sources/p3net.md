# P3 / P3Net — karta źródła

Status: **ZATWIERDZONA** (2026-10-16) przez autora projektu.
Protokół: `notes/plans/v005-verification-protocol.md`. Decyzje: `notes/plans/v005-decisions.md` (#1–#9, #5 = silnik zgodny z P3).

Zasada (decyzja 2026-10-16): **P3Net = P3 zastosowane do joint NAS+HPO z surogatem.** Silnik jest P3 ze źródła;
odstępstwa tylko tam, gdzie wymaga ich surogat, wiele celów albo kategoryczny genotyp — każde opisane w §4 i
zatwierdzone. Dotychczasowa piramida P3Net (S1–S5) nie jest wzorcem.

## 1. Źródło

- Goldman, B. W., Punch, W. F. **Parameter-less Population Pyramid.** GECCO'14, s. 785–792.
  Plik: `notes/articles/linkage learn/P3/Parameter-less population pyramid.pdf`. Cytowany jako `goldman2014parameterless`.
- Uzupełniająco (nie w repo, do zdobycia): Goldman & Punch, *Fast and Efficient Black Box Optimization Using the
  Parameter-less Population Pyramid*, Evolutionary Computation 23(3), 2015 (`goldman2015fast`) — rozszerzona wersja.
- Kontekst prac pokrewnych z surogatem w P3 (do odróżnienia, nie wzorzec): Dushatskiy et al., GECCO'21 (SA-P3-GOMEA,
  `notes/articles/linkage learn/A Novel Surrogate-assisted Evolutionary Algorithm Applied to.pdf`); Bartnik 2026
  (`notes/articles/NAS/MO-NAS/Evolutionary optimization of deep neural.pdf`).

## 2. Algorytm wg źródła (P3)

Numeracja kroków P# używana dalej w testach i odstępstwach. Źródło jest sformułowane dla genotypów binarnych
(s. 785: „we will focus on the binary domain here for simplicity”) i jednego celu (maksymalizacja fitness).

### Pętla główna — Fig. 1 „Iterate-P3” (s. 786)

- **P1.** Utwórz nowe rozwiązanie losowe.
- **P2.** Zastosuj do niego hill climber (§2.1, P10–P12).
- **P3.** Jeśli rozwiązanie nie jest w zbiorze `hashset`: dodaj je do poziomu P₀ i do `hashset`.
- **P4.** Dla każdego poziomu Pᵢ piramidy, od dołu: zmieszaj rozwiązanie z Pᵢ (§2.3, P20–P25).
- **P5.** Jeśli fitness rozwiązania się **poprawił** (względem stanu przed mieszaniem z Pᵢ): jeśli nie ma go w
  `hashset`, dodaj je do Pᵢ₊₁ (tworząc ten poziom, jeśli nie istnieje) i do `hashset`.
- **P6.** Pętla po poziomach **nie jest przerywana**, gdy rozwiązanie się nie poprawi — mieszanie trwa z każdym
  poziomem (Fig. 1 nie ma `break`).
- **P7.** `hashset` = zbiór wszystkich rozwiązań w piramidzie; poziomy są rozłączne (s. 786, §2.2: „the levels
  represent disjoint sets of unique solutions”).
- **P8.** Brak parametrów: nie ma rozmiaru populacji ani rozmiarów poziomów; poziom rośnie o pojedyncze rozwiązania
  (§2.2, §2.5).

### Hill climber — FIHC (§2.1, s. 786)

- **P10.** Rozważ wszystkie pozycje genu xᵢ w losowej kolejności.
- **P11.** Dla xᵢ oceń rozwiązanie ze wszystkimi możliwymi wartościami xᵢ; jeśli któraś daje **ścisłą** poprawę,
  zastąp nią xᵢ.
- **P12.** Powtarzaj, aż żadna zmiana nie daje ścisłej poprawy (lokalne optimum). Pozycje już sprawdzone od ostatniej
  zmiany pomija się bez ewaluacji.

### Poziom i tablica częstości (§2.2, s. 786)

- **P13.** Każdy poziom przechowuje tablicę częstości par wartości genów; aktualizowana przy każdym dodaniu
  rozwiązania do poziomu.

### Tworzenie klastrów — Fig. 2 „Cluster-Creation” (s. 786)

- **P14.** Odległość między klastrami (Eq. 1): D(Cᵢ, Cⱼ) = (1 / |Cᵢ|·|Cⱼ|) · Σ_{cᵢ∈Cᵢ, cⱼ∈Cⱼ} [2 − (H(cᵢ) + H(cⱼ)) / H(cᵢ ∪ cⱼ)],
  H — entropia z tablicy częstości (Eq. 2).
- **P15.** Aglomeracyjnie: zacznij od singletonów {0}, …, {N−1}; łącz parę o najmniejszym D; `useful` zbiera wszystkie
  utworzone klastry, **w tym singletony**.
- **P16.** Jeśli D(Cᵢ, Cⱼ) = 0, usuń Cᵢ i Cⱼ z `useful` (podklastry, które idealnie się przewidują).
- **P17.** Uporządkuj `useful` **od najmniejszego**, klastry równej wielkości w losowej kolejności.
- **P18.** Usuń z `useful` największy klaster (cały genotyp).

### Użycie klastrów — Fig. 3 „Cluster-Usage” i §2.3 (s. 786–787)

- **P20.** Dla każdego Cᵢ z `useful` (w kolejności P17):
- **P21.** dla dawców d z poziomu w losowej kolejności: skopiuj wartości d na pozycjach Cᵢ do rozwiązania;
- **P22.** jeśli rozwiązanie się **zmieniło**: oceń je; jeśli fitness **spadł** — cofnij zmianę; przerwij szukanie dawcy
  (`break`) — jeden dawca na klaster;
- **P23.** jeśli się nie zmieniło — próbuj kolejnego dawcy (P3 szuka dawcy różniącego się w Cᵢ, s. 787).
- **P24.** Zmiana przy **równym** fitness jest zachowywana (drift przez plateau, s. 786).
- **P25.** Każdy klaster kosztuje co najwyżej jedną ewaluację (s. 787).

## 2a. Kodowanie przestrzeni (genotyp)

Wszystkie zmienne kategoryczne (wartości bez porządku), w ustalonej kolejności współrzędnych
(`implementation/experiments/search_spaces/*.py`).

| Przestrzeń | n | Zmienne (liczba wartości) | Rozmiar przestrzeni |
|---|---|---|---|
| JAHS-Bench-201 (×3 zbiory) | 10 | 6 krawędzi komórki: {none, skip_connect, nor_conv_1x1, nor_conv_3x3, avg_pool_3x3} (5 każda); learning rate: 8 wartości log 10⁻³…1; weight decay: 6 wartości log 10⁻⁵…10⁻²; aktywacja {relu, hardswish, mish} (3); TrivialAugment {F, T} (2) | 5⁶·8·6·3·2 ≈ 4.5·10⁶ |
| NAS-HPO-Bench-II | 8 | 6 krawędzi: {nor_conv_3x3, avg_pool_3x3, skip_connect, none} (4 każda); learning rate {0.003125 … 0.4} (8); batch {16 … 512} (6) | 4⁶·8·6 = 196 608 |
| FCNet (×4 zadania) | 9 | units warstwy 1 i 2 {16 … 512} (6, 6); aktywacja 1 i 2 {tanh, relu} (2, 2); dropout 1 i 2 {0, 0.3, 0.6} (3, 3); init LR (6); harmonogram LR {cosine, const} (2); batch {8 … 64} (4) | 62 208 |
| NAS-Bench-201 | 6 | 6 krawędzi × 5 operacji | 15 625 |

Ograniczenie: komórka musi mieć ścieżkę wejście–wyjście bez `none` (Validity, O-4). Siatki LR/WD na JAHS to dyskretyzacja
(decyzja protokołu #31); na NAS-HPO-Bench-II i FCNet siatki są pełnymi siatkami benchmarków.

## 3. Parametry wg źródła

| Parametr | Źródło | P3Net v005 | Uwagi |
|---|---|---|---|
| Rozmiar populacji / poziomów | brak (P8) | brak | dotychczasowe `growth_factor`, rozmiary 2^(k+1) — usunięte |
| Miara linkage | D z Eq. 1 na entropii (P14) | D z Eq. 1 | dotychczas 1 − średnie NMI (sklearn) — zmiana |
| Kolejność klastrów | od najmniejszych (P17) | od najmniejszych | dotychczas losowa |
| Hill climber | FIHC do lokalnego optimum (P10–P12) | do decyzji (§5, D-2) | |
| Wszystkie pozostałe | brak | brak | P3 jest bezparametrowy |

## 4. Odstępstwa wymagane przez nasz problem

Każde musi zostać zatwierdzone; po zatwierdzeniu trafia do `v005-decisions.md`.

| # | Krok | Odstępstwo | Powód | Status |
|---|---|---|---|---|
| O-1 | cały algorytm | Genotyp **kategoryczny k-arny** zamiast binarnego | Zmienne to wybory bez porządku (operacje, aktywacje, siatki HP); kodowanie binarne rozbiłoby jeden wybór na kilka bitów, które muszą zmieniać się razem, i tworzyło kody bez znaczenia (5 operacji → 3 bity → 3 nieważne kody). Precedens: Dushatskiy et al. (P3-GOMEA na problemie nie-binarnym), Bartnik (NB201, 6 × 5). Skutki dla P3: (a) P11 sprawdza k−1 alternatyw na pozycję — FIHC droższy; (b) entropia par z tablicy k×k potrzebuje więcej próbek, przy małych poziomach MI zawyżone → fałszywe powiązania; (c) filtr D=0 (P16) częściej się uruchamia przy małych poziomach. P14 i P20–P25 działają bez zmian dla k > 2 | do zatwierdzenia |
| O-2 | P5, P11, P22 | **Dwa cele** (błąd f1, koszt f2) zamiast jednego fitness — „poprawa” wg relacji Pareto (decyzja autora); dokładna reguła: §5, D-1 | problem wielokryterialny | do decyzji D-1 |
| O-3 | P2, P4, P11, P22 | **Część ewaluacji zastąpiona surogatem** — to jest pomysł P3Net; gdzie i jak: §5, D-3 | budżet ≤ 350 pełnych ewaluacji wobec 10³–10⁵ w źródle | do decyzji D-3 |
| O-4 | P1 | Nowe losowe rozwiązanie musi być **poprawne** (Validity: ścieżka wejście–wyjście) | reguła protokołu #33, wspólna dla wszystkich | do zatwierdzenia |
| O-5 | wynik | Zbiór wynikowy = wszystkie rozwiązania ocenione naprawdę (H_t), nie zawartość piramidy | protokół metryk wspólny dla wszystkich metod | do zatwierdzenia |

## 5. Decyzje projektowe do podjęcia (opcje, za i przeciw)

### D-1. Co znaczy „poprawa” przy dwóch celach (P5, P11, P22, P24)

W źródle trzy miejsca używają porównania fitness: FIHC (P11, *ścisła poprawa*), mieszanie (P22–P24, *nie spadł* —
równy zostaje), awans na poziom wyżej (P5, *poprawił się*). Decyzja autora: relacja Pareto. Możliwe definicje:

- **a) Dominacja:** x′ lepsze od x, jeśli x′ dominuje x (nie gorsze w obu celach, lepsze w co najmniej jednym).
  „Nie gorsze” (P22) = x nie dominuje x′.
  - Za: najprostsza, wprost przenosi relacje „lepszy” / „nie gorszy” ze źródła.
  - Przeciw: przy dwóch celach większość par jest wzajemnie niezdominowana. „Ścisła poprawa” (FIHC, awans) zdarza się
    rzadko, a „nie gorsze” przepuszcza prawie wszystko — w v004 dokładnie to (permisywne `not dominates`) rozregulowało
    kanoniczne P3 (R1 §4.1).
- **b) Dominacja przy FIHC i awansie, „niezdominowany przez archiwum” przy mieszaniu:** krok mieszania przyjęty, jeśli
  nowe rozwiązanie nie jest zdominowane przez globalne archiwum niezdominowanych rozwiązań.
  - Za: kroki prowadzące do frontu przechodzą, kroki w obszar zdominowany są cofane; zbliżone do archiwum elitarnego
    u Bartnik (§5.4, Eq. 4.7).
  - Przeciw: mieszanie przestaje być lokalnym porównaniem z rodzicem (odejście od P22); rozwiązania z dala od frontu
    trudniej poprawiać.
- **c) Wkład do hiperobjętości (HV):** x′ lepsze od x, jeśli zastąpienie x przez x′ zwiększa HV zbioru (np. poziomu
  albo archiwum).
  - Za: skalar, więc „ścisła poprawa” / „nie spadł” mają naturalny sens; spójne z metryką oceny (HV).
  - Przeciw: wymaga punktu odniesienia; zależy od kontekstu (zbioru), więc nie jest relacją dwóch rozwiązań; w v004
    kryterium HV dla wzrostu poziomów było źródłem błędu (R1 §3.1).

**Rekomendacja: b)** — najbliżej idei „poprawa = przybliżenie frontu Pareto”, bez punktu odniesienia; dominacja
zostaje tam, gdzie źródło wymaga ścisłej poprawy (FIHC, awans).

### D-2. Hill climber (P2, P10–P12)

- **a) FIHC wg źródła, wszystkie kroki prawdziwymi ewaluacjami.**
  - Za: wierne.
  - Przeciw: jedno FIHC do lokalnego optimum na JAHS (10 zmiennych, 4–7 alternatyw) to dziesiątki–setki ewaluacji —
    przy budżecie 50–350 kilka rozwiązań na cały przebieg. Dushatskiy (§2.3.4) usunął FIHC właśnie z tego powodu.
- **b) FIHC na surogacie, prawdziwa ewaluacja tylko wyniku** (w ramach D-3).
  - Za: zachowuje krok P2 i jego rolę (lokalne optimum przed mieszaniem); koszt 1 ewaluacji.
  - Przeciw: lokalne optimum surogatu, nie problemu — to był błąd ramion kanonicznych v004 (R1 §4.1) — tu świadomy i
    opisany.
- **c) Bez FIHC** (jak SA-P3-GOMEA i Bartnik).
  - Za: najprostsze, jest precedens w literaturze.
  - Przeciw: odstępstwo od P3 w kroku P2; P3 bez FIHC to P3-GOMEA (inna metoda).

**Rekomendacja: b)** — zostawia strukturę P3, a koszt FIHC przenosi na surogat, co jest właśnie pomysłem P3Net.
Alternatywa c) jako wariant porównawczy.

### D-3. Gdzie surogat zastępuje ewaluację (O-3) — rdzeń pomysłu P3Net

- **a) Bramka na każdym kroku (styl SA-P3-GOMEA):** każdy krok mieszania (P22) oceniany przez surogat; prawdziwa
  ewaluacja tylko, gdy surogat przewiduje poprawę (z progiem); porównania na prawdziwych wartościach, gdy oba je mają.
  - Za: sprawdzona w literaturze; prawdziwe dane napływają w trakcie wspinaczki.
  - Przeciw: to jest SA-P3-GOMEA / Bartnik — nowość P3Net zawęża się do surogatu i wielu celów; trudniej się odróżnić od
    pracy z tej samej grupy.
- **b) Łańcuch surogatowy z ewaluacją na poziomie (styl dotychczasowego P3Net):** mieszanie z poziomem Pᵢ (P20–P25)
  przebiega na surogacie (relatywnym, z telescopingiem od ostatniego naprawdę ocenionego przodka); po zakończeniu
  mieszania z poziomem wynik jest oceniany naprawdę i dopiero ta wartość decyduje o awansie (P5).
  - Za: zachowuje oryginalny pomysł P3Net (relatywny surogat + telescoping) w silniku P3; jedna ewaluacja na poziom —
    budżet idzie na przejście przez piramidę; wyraźnie inne niż SA-P3-GOMEA.
  - Przeciw: decyzje w obrębie poziomu w całości zależą od jakości surogatu (w v004 słabej na FCNet).
- **c) Hybryda:** łańcuch surogatowy jak b), ale z bramką „sprawdź naprawdę” przy niepewnych predykcjach.
  - Za: łączy zalety, ogranicza błędy surogatu.
  - Przeciw: wymaga miary niepewności (np. zespół modeli) — więcej elementów do zweryfikowania.

**Rekomendacja: b)** jako P3Net (spójne z pierwotnym pomysłem i wyraźnie różne od prac pokrewnych), a) jako wariant
porównawczy — wtedy artykuł odpowiada wprost, który sposób łączenia P3 z surogatem lepiej działa.

### D-4. Surogat (decyzja A5c: nowy) — do osobnej karty

Model, cel (log f1 / ranking), interakcje w obrębie F, walidacja — osobna karta `v005-sources/p3net-surrogate.md`
(po zatwierdzeniu D-3, bo D-3 decyduje, co surogat ma przewidywać).

## 6. Własności do sprawdzenia testami (poziom 1, pisze niezależny agent)

| ID | Krok | Własność |
|---|---|---|
| W1 | P1, P3 | Każda iteracja tworzy dokładnie jedno nowe rozwiązanie; trafia do P₀ wtedy i tylko wtedy, gdy nie ma go w `hashset` |
| W2 | P6 | Rozwiązanie jest mieszane z każdym istniejącym poziomem, także gdy na niższym się nie poprawiło |
| W3 | P5 | Awans na Pᵢ₊₁ tylko przy poprawie (wg D-1) i tylko, gdy rozwiązania nie ma w `hashset`; Pᵢ₊₁ tworzony, gdy nie istnieje |
| W4 | P7 | Poziomy są rozłączne; żadne rozwiązanie nie występuje dwa razy w piramidzie |
| W5 | P8 | Brak rozmiarów docelowych; liczność poziomu = liczba dodanych rozwiązań |
| W6 | P12 | FIHC kończy w punkcie, w którym żadna zmiana jednej pozycji nie daje ścisłej poprawy (wg D-1 i D-2) |
| W7 | P14 | D obliczane wg Eq. 1 na entropii; test na problemie o znanej strukturze (np. pułapki k-arne) odzyskuje bloki |
| W8 | P15, P18 | `useful` zawiera wszystkie singletony i nie zawiera klastra = cały genotyp |
| W9 | P16 | Klastry z D = 0 usunięte |
| W10 | P17 | Kolejność od najmniejszych; remisy losowo |
| W11 | P21–P23 | Dawca różni się od rozwiązania w danym klastrze, jeśli taki istnieje na poziomie; brak propozycji „bez zmiany” |
| W12 | P22, P24 | Zmiana cofana przy pogorszeniu, zachowywana przy remisie (wg D-1) |
| W13 | P25 | Co najwyżej jedna ocena (prawdziwa lub surogatowa, wg D-3) na klaster |
| W14 | O-3 | Liczba prawdziwych ewaluacji na iterację zgodna z D-3 (np. dla b: ≤ 1 + liczba poziomów) |
| W15 | O-5 | Każda prawdziwa ewaluacja trafia do H_t; duplikaty nie zużywają budżetu |
| W16 | całość | Na pułapkach k-arnych (z prawdziwą funkcją celu, bez surogatu) P3 odnajduje optimum w ≥ 8/10 przebiegów (kryterium jak w `results/checks/p3_trap_correctness.md`) |

Test zgodności (poziom 2): implementacja P3 bez surogatu i z jednym celem vs referencja — kod autorów P3 (Goldman,
publiczne repozytorium, do odnalezienia) na pułapkach i NK; kryterium wg protokołu (±2%, TOST) — do zapisania przed testem.

## 7. Zdania artykułu opisujące P3 / P3Net (do `v005-claims.md`)

Do uzupełnienia po zatwierdzeniu D-1–D-3; każde zdanie z testem z §6. Przykłady:
- „P3Net follows P3: each iteration adds one random solution that climbs through every pyramid level” → W1, W2, W3.
- „Linkage clusters are built with P3's entropy-based distance and applied smallest-first” → W7–W10.
- „A donor that differs on the cluster is always chosen” → W11.

## 8. Do zatwierdzenia przez autora

1. Odstępstwa O-1, O-4, O-5 (wynikają z problemu i protokołu).
2. D-1: reguła „poprawy” przy dwóch celach (rekomendacja b).
3. D-2: hill climber (rekomendacja b; c jako wariant).
4. D-3: gdzie surogat zastępuje ewaluację (rekomendacja b jako P3Net, a jako wariant).
5. Lista własności W1–W16.

## 9. Decyzje autora (2026-10-16)

- **D-2 = a)** FIHC wg źródła, wszystkie kroki prawdziwymi ewaluacjami. Konsekwencja do odnotowania: jedno FIHC do
  lokalnego optimum kosztuje co najmniej Σ(k−1) ewaluacji (JAHS: 39, NAS-HPO-II: 30, FCNet: 25, NB201: 24) na każde
  przejście po pozycjach; przy budżecie 50–100 P3Net wykona tylko kilka iteracji P1–P6.
- **D-3 = b) jako P3Net + a) jako wariant porównawczy.**
- **O-4** zatwierdzone.
- **D-1 = b)** dominacja przy FIHC i awansie; przy mieszaniu przyjęcie, gdy nowe rozwiązanie dominuje poprzednie, ma te same wartości celów albo nie jest zdominowane przez archiwum elitarne (reguła MO-GOMEA, `luong2014mogomea`).
- **O-1, O-5** zatwierdzone; karta zatwierdzona w całości.
