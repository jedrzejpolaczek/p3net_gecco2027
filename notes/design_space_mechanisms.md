# Przestrzeń projektowa: mechanizmy jako klocki

Cel inny niż `algorithms_comparison.md`: tamten plik odpowiada "czym jest algorytm X" (wiersz = algorytm). Ten plik odpowiada "jakie znam warianty decyzji projektowej Y i kto już ich użył" (wiersz = decyzja) — po to, żebyś mógł zapytać "czy mogę zrobić wariant P3Net z X zamiast Y" i od razu zobaczyć: (a) czy ktoś już tak robił i jak to wyszło, (b) czego to wymaga od reszty algorytmu, żeby w ogóle działało.

**Układ:** osie ułożone w kolejności, w jakiej konstruuje się kanoniczny algorytm genetyczny (Holland 1975; Goldberg 1989): Reprezentacja → Populacja początkowa → Funkcja przystosowania → Selekcja rodzicielska → Krzyżowanie → Mutacja → Selekcja środowiskowa → Kryterium stopu. Nie każda oś odpowiada dokładnie jednemu krokowi — część to *doprecyzowania* jednego kroku, część to *rozszerzenia* nieobecne w kanonicznym GA (bo ten zakładał tanią ewaluację), a trzy kanoniczne kroki nie miały pierwotnie dedykowanej osi.

**Zweryfikowane ćwiczeniem kontrolnym:** przeszliśmy przez rekonstrukcję P3Net krok po kroku, sprawdzając, czy każda jego decyzja projektowa mieści się w istniejących osiach. Znaleziono 7 realnych luk/nieścisłości — opisanych niżej, każda oznaczona jako: **nowa oś** (≥2 niezależne, udokumentowane warianty od różnych algorytmów), **poprawka opisu** (oś istniała, ale była błędnie sformułowana), albo **konsekwencja sprzężenia** (nie wolny klocek — wynika automatycznie z połączenia dwóch innych osi, więc nie dostaje własnego wiersza z wieloma opcjami, tylko wpis w "Znanych ograniczeniach łączenia").

**Jak z tego korzystać:** wybierz po jednej opcji z każdej osi — to szkic nowego algorytmu. Sekcja "Poza konstrukcją" (typ danych) nie jest wolnym klockiem — to informacja, jak daleko od sprawdzonego gruntu odchodzisz. Potem sprawdź "Znane ograniczenia łączenia" na dole. Reszta wymaga Twojej własnej oceny sensowności.

**Zakres źródłowy:** to, co zweryfikowaliśmy w tej sesji (`algorithms_comparison.md` + pełny tekst sekcji Proponowany Optymalizator w `P3Net_pl.md`) plus ogólna wiedza o taksonomii GA tam, gdzie wyraźnie to zaznaczam.

**Druga runda weryfikacji (krzyżowa kontrola z `algorithms_comparison.md`):** po zbudowaniu wersji krok-po-kroku sprawdzono systematycznie, czy każdy algorytm z Tabel A/B/C tamtego pliku pojawia się we wszystkich pasujących mu osiach tutaj. Znaleziono i poprawiono 12 niespójności (brakujące wpisy, jeden błąd faktyczny w klasyfikacji domeny RV-GOMEA, jedną niespójność strukturalną z pominięciem LyMPuS w głównej tabeli predyktora) — poprawki wprowadzone bezpośrednio poniżej, bez osobnego dziennika zmian.

---

## Krok 1 — Reprezentacja (kodowanie genotypu)

### Oś: Kodowanie genotypu — struktura

To dwa niezależne pytania, wcześniej błędnie zlane w jedno (znalezisko #1, **poprawka opisu**): struktura kodowania i kardynalność alfabetu to nie ta sama decyzja — Bartnik/NAS-Bench-201 jest dowodem: jego genotyp jest grafowy *i* niebinarny jednocześnie.

| Opcja | Kto już tego używa | Uwaga |
|---|---|---|
| Graf-krawędź-operacja (DAG komórki) | NSGA-Net; MO-SA-P3-GOMEA (Bartnik, komórka NAS-Bench-201); P3Net; GOMEA-NAS + SynFlow (niska pewność źródła) | Podatne na duplikację przez izomorfizm grafu i na niewykonalność (patrz Krok 1↔3) |
| String pozycyjny stałej długości (sekwencyjny, nie graf) | NSGANetV2, MoSegNAS | Unika izomorfizmu grafu i (w praktyce) niewykonalności — każdy string jest z definicji poprawny |
| Płaski wektor bez struktury grafowej/pozycyjnej | SA-P3-GOMEA (przypisanie partycji danych); P3, GOMEA/ROMEA, CS-GOMEA, LyMPuS/eLyMPuS (pseudo-Boolowskie funkcje testowe, nie NAS); RV-GOMEA + clique linkage (odpowiednik ciągły, ℝ^ℓ); BOHB joint (Zela), Bag of Baselines (wektor hiperparametrów, nie graf/pozycyjny NAS-string) | |

### Oś: Kodowanie genotypu — kardynalność alfabetu

| Opcja | Kto już tego używa |
|---|---|
| Binarne | NSGA-Net, P3, GOMEA/ROMEA, CS-GOMEA, LyMPuS/eLyMPuS |
| Kategorialne, alfabet > 2 | MO-SA-P3-GOMEA (Bartnik, alfabet 5); SA-P3-GOMEA (kardynalność do 10); NSGANetV2, MoSegNAS (wiele opcji na pozycję stringa); P3Net (operacje + $\Theta$ zdyskretyzowane do binów); GOMEA-NAS + SynFlow (niska pewność źródła) |
| Ciągłe, ℝ^ℓ | RV-GOMEA + clique linkage |
| Mieszane (kategoryczne + ciągłe) | BOHB joint (Zela); Bag of Baselines |

**Widelec: obsługa ciągłych współrzędnych, gdy silnik jest z natury dyskretny (drzewo powiązań/optimal mixing)** — znalezisko #2, **za słabe na pełną oś, notatka**. Jawnie nazwany w P3Net_pl.md (Sformułowanie Problemu): (i) dyskretyzacja każdej ciągłej współrzędnej do skończonego zbioru binów, tak że cały genotyp jest kategoryczny — **P3Net wybiera to**; (ii) rozszerzenie drzewa powiązań o osobny operator mieszania rzeczywistoliczbowego w duchu RV-GOMEA. Sprawdziłem: nikt w tym zestawieniu faktycznie nie przetestował (ii) na genotypie *mieszanym* — RV-GOMEA+clique reprezentuje tę filozofię wyłącznie na domenie *czysto ciągłej*. To nie jest oś z dwoma zweryfikowanymi wariantami, tylko widelec, gdzie tylko jedna strona ma precedens, a druga jest nazwaną wprost, ale nieprzetestowaną hipotezą.

### Sub-decyzja: co dokładnie jest kodowane (zakres reprezentacji)

| Opcja | Kto już tego używa |
|---|---|
| Tylko architektura, HP zafiksowane lub poza genotypem | NSGA-Net, NSGANetV2, MoSegNAS, MO-SA-P3-GOMEA (Bartnik), GOMEA-NAS + SynFlow |
| Wspólnie architektura + hiperparametry treningowe | BOHB joint (Zela), Bag of Baselines, P3Net |
| Nie dotyczy (nie NAS) | CS-GOMEA, SA-P3-GOMEA, P3, GOMEA/ROMEA, RV-GOMEA + clique linkage, LyMPuS/eLyMPuS |

---

## Krok 2 — Populacja początkowa (i jej struktura przez cały przebieg)

### Oś: Model populacji

| Opcja | Kto już tego używa |
|---|---|
| Pojedyncza, stały rozmiar (generacyjna NSGA-II) | NSGA-Net, NSGANetV2, MoSegNAS |
| Piramida (P3), rosnący rozmiar, bezparametrowa | P3, SA-P3-GOMEA, MO-SA-P3-GOMEA (Bartnik), LyMPuS/OLyMPuS, P3Net |
| IMS — Interleaved Multistart Scheme (równoległe, rosnące populacje) | CS-GOMEA, GOMEA/ROMEA, RV-GOMEA + clique linkage, LyMPuS/LT-GOMEA (wariant alternatywny do piramidy OLyMPuS) |
| Nie dotyczy (Bayesian Optimization, nie populacja) | BOHB joint (Zela) |
| Zależnie od metody (mix: SMS-EMOA-populacyjny w części wariantów, BO w innych) | Bag of Baselines |

*Uwaga:* ta oś opisuje strukturę populacji przez cały przebieg (nie tylko inicjalizację) — dla P3/IMS "inicjalizacja" i "struktura" to jedno i to samo.

---

## Krok 3 — Funkcja przystosowania (fitness)

Tu skupia się większość osi — bo to właśnie ten krok kanoniczny GA traktuje jako "czarną skrzynkę o zerowym koszcie", a cała literatura o NAS/surrogate-assisted EA istnieje po to, żeby tę skrzynkę rozpakować i uczynić tanią.

### Oś: Cele optymalizacji (co fitness *jest*: skalar czy wektor)

| Opcja | Kto już tego używa |
|---|---|
| Single-objective | CS-GOMEA, SA-P3-GOMEA, P3, GOMEA/ROMEA, RV-GOMEA + clique linkage, LyMPuS/eLyMPuS, GOMEA-NAS + SynFlow, BOHB joint (Zela) |
| Multi-objective (2 cele) | NSGA-Net, MoSegNAS, MO-SA-P3-GOMEA (Bartnik), P3Net |
| Multi-objective (2–5 celów) | NSGANetV2, Bag of Baselines |

### Założenie o wyroczni: Black-box vs gray-box

| Opcja | Kto już tego używa | Uwaga |
|---|---|---|
| Black-box | Wszystkie oprócz poniższego | Dokładność walidacyjna sieci neuronowej nie jest rozkładalna na podfunkcje → z konieczności black-box dla całej linii NAS |
| Gray-box (jawny dostęp do podfunkcji celu) | RV-GOMEA + clique linkage | Testowany wyłącznie na syntetycznych funkcjach z jawnie rozkładalną strukturą |
| Black-box, ale surogat *symuluje* korzyść gray-box przez relatywne porównania | LyMPuS/eLyMPuS, P3Net | Przybliżenie korzyści gray-box bez jawnego dostępu do podfunkcji |

### Konkretny substrat: Mechanizm pełnej ewaluacji

| Opcja | Kto już tego używa | Uwaga |
|---|---|---|
| Pełny trening od zera | NSGA-Net, MoSegNAS (dekoder stały), Bag of Baselines | |
| Fine-tuning wag z supersieci (weight-sharing) | NSGANetV2 | Udokumentowane ryzyko (Yu i in. 2020) |
| Dokładna ewaluacja funkcji syntetycznej | P3, GOMEA/ROMEA, CS-GOMEA, LyMPuS/eLyMPuS | |
| Częściowa reewaluacja (gray-box) | RV-GOMEA + clique linkage | |
| Trening rzeczywistego modelu na danych tabelarycznych | SA-P3-GOMEA | |
| Lookup table + bezpośredni pomiar sprzętowy | MO-SA-P3-GOMEA (Bartnik) | |
| Zero-cost (jeden forward/backward pass) | GOMEA-NAS + SynFlow | |
| Trening SGD, budżet = czas (Hyperband) | BOHB joint (Zela) | |
| Predyktor zastępczy benchmarku (JAHS-Bench-201) / tablica przeglądowa (NAS-HPO-Bench-II) | P3Net | Substrat spoza tego zestawienia — patrz Prace poboczne w `algorithms_comparison.md` |

### Rozszerzenie 1: Predyktor zastępczy — tania aproksymacja fitness

| Opcja | Kto już tego używa | Uwaga |
|---|---|---|
| Brak (dokładna ewaluacja / częściowa reewaluacja gray-box) | P3, GOMEA/ROMEA, RV-GOMEA + clique linkage | |
| Brak (generator, nie estymator fitness) | NSGA-Net (BOA) | Nie mylić z "brak predyktora" w innym sensie |
| Bezwzględna regresja, online | NSGANetV2, SA-P3-GOMEA, MO-SA-P3-GOMEA (Bartnik) | |
| Relatywny, świadomy struktury powiązań (mechanizm dokładny różni się między poniższymi — patrz podpunkt niżej: dwa niezależne wymiary) | CS-GOMEA, P3Net, LyMPuS/eLyMPuS | Wymaga zdefiniowanego drzewa powiązań — patrz "Znane ograniczenia łączenia" |
| Ranking (RankNet, ranking loss) | MoSegNAS | |
| Zero-cost proxy (bez uczenia) | GOMEA-NAS + SynFlow | |
| Zależnie od metody | Bag of Baselines | |

**Podpunkt — predyktor relatywny: dwa niezależne wymiary** (znalezisko #3, **poprawka opisu**: oś już istniała jako CS-GOMEA vs eLyMPuS, ale te dwa wiersze mylnie różniły tylko "czy jest gwarancja", podczas gdy realnie różnią się na dwóch osiach naraz):

| Wymiar | Wariant A | Wariant B |
|---|---|---|
| Mechanizm | Regresja wartości różnicy fitness (liczba ciągła) — **CS-GOMEA, P3Net** | Dyskretne porównanie kierunku {lepszy/gorszy/niejednoznaczny}, bez regresji — **eLyMPuS** |
| Gwarancja formalna | Brak — tylko walidacja empiryczna — **CS-GOMEA, P3Net** | "Perfect" pod założeniem monotoniczności krajobrazu — **eLyMPuS** |

*Uwaga redakcyjna do P3Net_pl.md:* tekst nazywa mechanizm P3Net "analogicznym do eLyMPuS", ale technicznie (regresja na różnicach, bez gwarancji) siedzi w tej samej komórce co CS-GOMEA. Podobieństwo do eLyMPuS dotyczy filozofii (relatywny, świadomy struktury powiązań, odkrywanej przyrostowo), nie konkretnego mechanizmu obliczeniowego — warto to doprecyzować w tekście, żeby czytelnik nie mylił tych dwóch wymiarów.

**Podpunkt — strategia próbkowania danych treningowych predyktora** (dotyczy tylko wariantów *online*):

| Wariant | Kto go używa |
|---|---|
| Online, ograniczone do okolic aktualnego frontu Pareto | NSGANetV2 (explicite kontrastowane z podejściem offline-jednostajnym), MoSegNAS |
| Online, przyrostowo z całego archiwum ewaluacji | CS-GOMEA, SA-P3-GOMEA, LyMPuS/eLyMPuS, MO-SA-P3-GOMEA (Bartnik), P3Net |
| Offline, jednostajne przed startem przeszukiwania | Brak wśród algorytmów; tak buduje surogat sam benchmark JAHS-Bench-201 |

**Podpunkt — zakres predyktora względem celów** (dotyczy tylko algorytmów wielokryterialnych):

| Wariant | Kto go używa |
|---|---|
| Predyktor uczony obejmuje wszystkie cele | NSGANetV2 (bezwzględna regresja wszystkich celów), MO-SA-P3-GOMEA (Bartnik, warianty joint i per-objective) |
| Predyktor uczony tylko dla głównego celu (accuracy); drugi cel liczony analitycznie/przez lookup, bez udziału predyktora | MoSegNAS (RankNet dla accuracy + osobny lookup latencji per-warstwa), P3Net ($f_2$ liczony analitycznie, bez predyktora) |

### Rozszerzenie 2: Ograniczanie akumulacji błędu predyktora wzdłuż łańcucha tymczasowych akceptacji

Znalezisko #5, **nowa oś**. Konieczne tam, gdzie predyktor relatywny akceptuje wiele kolejnych modyfikacji bez pełnej ewaluacji pomiędzy nimi — bez tego mechanizmu błąd predyktora kumuluje się bez korekty.

| Opcja | Kto już tego używa | Uwaga |
|---|---|---|
| Limit głębokości łańcucha: licz kolejne kroki zaakceptowane wyłącznie przez predyktor, wymuś pełną ewaluację po $\kappa$ krokach, niezależnie od pewności każdego pojedynczego kroku | P3Net | $\kappa$ inicjalizowane granicą eLyMPuS $2\lceil\log_2 n\rceil$, ale bez formalnej gwarancji monotoniczności, którą ta granica pierwotnie zakładała |
| Brama progowa per-decyzja: ufaj tylko predykcjom powyżej pewnego kwantyla pewności, niezależnie od pozycji w łańcuchu | SA-P3-GOMEA | Odpowiada na inne pytanie niż κ: "czy ufam TEJ predykcji" zamiast "jak długo ufam SOBIE z rzędu" |

### Rozszerzenie 3: Selekcja kandydatów do pełnej ewaluacji (spośród predyktorem-zaakceptowanych)

Znalezisko #6, **nowa oś**. Osobna decyzja od progu akceptacji wewnątrz sweepu (Krok 7) i od klasycznej selekcji środowiskowej — dotyczy tego, kto z puli kandydatów zaaprobowanych przez predyktor faktycznie dostaje drogie zapytanie do prawdziwej wyroczni.

| Opcja | Kto już tego używa |
|---|---|
| Niezdominowanie w przestrzeni przewidywanych celów (front Pareto na estymatach) | P3Net |
| Najwyższa przewidywana wartość głównego celu, reszta dobierana dla rozproszenia po osi kosztu | NSGANetV2 |

### Rozszerzenie 4: Ewaluacja wielopoziomowa (multi-fidelity)

| Opcja | Kto już tego używa |
|---|---|
| Wykorzystuje drabinę wierności (Hyperband/successive halving) | BOHB joint (Zela); SH-EMOA (jedna z 5 metod Bag of Baselines) |
| Formalnie zdefiniowana, świadomie niewykorzystywana — działa wyłącznie na $r_K$ | P3Net i wszystkie metody odniesienia w Wynikach |
| Benchmark udostępnia oś wierności niezależnie od użycia | JAHS-Bench-201 (N/W/R/epoch), NAS-HPO-Bench-II (epoch przez wbudowany surogat) |

### Rozszerzenie 5: Obsługa duplikatów genotypu

| Opcja | Kto już tego używa | Uwaga |
|---|---|---|
| Nie dotyczy — kodowanie bez izomorfizmu grafowego, albo brak kroku dekodowania w ogóle (genotyp = fenotyp) | NSGANetV2, MoSegNAS, RV-GOMEA + clique linkage, BOHB joint, Bag of Baselines, CS-GOMEA, P3, GOMEA/ROMEA, LyMPuS/eLyMPuS, SA-P3-GOMEA | |
| Cache/detekcja duplikatów **po** wygenerowaniu (search-time) | NSGA-Net (Appendix E.3); P3Net (cache deduplikacji) | Standardowa praktyka od 2019 — **łapie**, nie **zapobiega** |
| Kanonizacja izomorfizmów **przy budowie** benchmarku | NAS-Bench-101 (→423K unikalnych), NAS-HPO-Bench-II (4096→~1K) | |
| Świadomie **brak** deduplikacji | NAS-Bench-201 (15625 raw, 6466 unikalnych, ~59%) → dziedziczone przez JAHS-Bench-201; SA-P3-GOMEA/Bartnik (ta sama komórka, bez wzmianki) | |
| **Nietestowane w żadnym źródle z tej sesji:** czy silnik świadomy zależności generuje mniej duplikatów w momencie proponowania | — | Diagnostyka testowana przez P3Net |

### Na granicy Kroku 1 i Kroku 3: Obsługa niewykonalności genotypu

Klasyczny GA Hollanda zakładał, że każdy bitstring jest poprawny — problem pojawia się dopiero, gdy dekodowanie (Krok 1→fenotyp) może zawieść. **Inne zjawisko niż duplikacja**: niewykonalność = genotyp w ogóle się nie dekoduje; duplikacja = wiele genotypów dekoduje się do tego samego, poprawnego fenotypu. Znalezisko #7, **nowa oś** (dodano "Odrzucenie" jako brakującą kategorię z klasycznej triady GA: odrzucenie/naprawa/kara).

| Opcja | Kto już tego używa | Uwaga |
|---|---|---|
| Zjawisko nie występuje — domena bezograniczeniowa | GOMEA/ROMEA, P3, CS-GOMEA, LyMPuS/eLyMPuS (pseudo-Boolowskie); SA-P3-GOMEA; RV-GOMEA + clique linkage (Sphere/Rosenbrock/REB, pełna domena ℝ^ℓ) | |
| Naprawa (repair): niepodłączone fragmenty struktury usuwane, nie cały genotyp odrzucany | NSGA-Net — "hanging nodes... are expelled from the final architecture" (Appendix E.1) | |
| Odrzucenie (rejection): kandydat naruszający ograniczenie jest wyrzucany przed dalszym przetwarzaniem | P3Net — kandydaci naruszający $g(x)\leq 0$ są odrzucani przed odpytaniem predyktora zastępczego | |
| Kara (penalty): genotyp dekoduje się, ale dostaje pogorszoną wartość fitness zamiast być odrzuconym | — | Klasyczna trzecia kategoria z ogólnej teorii GA; **nieobserwowana w źródłach z tej sesji** |
| Zjawisko nie występuje z definicji benchmarku — każda surowa kombinacja ma wpis w tabeli | NAS-Bench-201, JAHS-Bench-201, NAS-HPO-Bench-II | |

---

## Krok 4 — Selekcja rodzicielska

**Częściowo wypełnione dzięki rekonstrukcji P3Net.** Wcześniej flagowane jako luka bez danych źródłowych — teraz mamy jeden konkretny, potwierdzony wariant:

| Opcja | Kto już tego używa |
|---|---|
| Losowanie wyłącznie spośród osobników w pełni ocenionych (nigdy spośród tymczasowych, akceptowanych tylko przez predyktor) | P3Net — rodzice i przodek $x_0$ konstrukcji teleskopowej zawsze pochodzą z $\mathcal{H}_t$ |

Nadal brak drugiego, kontrastowego wariantu z innego źródła — mechanizm wyboru rodziców jest w praktyce zbundlowany wewnątrz "Silnika przeszukiwania" (Krok 5) dla pozostałych algorytmów (np. NSGA-II definiuje wybór rodziców razem z całą logiką rankingu, GOMEA/optimal mixing nie ma osobnej fazy "wybierz rodziców" w ogóle). Gdyby pojawiło się źródło różnicujące to wprost dla innego algorytmu, warto dodać.

---

## Krok 5 — Krzyżowanie

### Oś: Silnik przeszukiwania

*Zastrzeżenie:* ta oś w praktyce nie jest czystym Krokiem 5 — nazwy takie jak "GOMEA" czy "NSGA-II" oznaczają całe pakiety łączące Krok 4, Krok 5 i czasem Krok 7 w jedną, nierozdzielną całość.

| Opcja | Kto już tego używa | Uwaga |
|---|---|---|
| NSGA-II (sortowanie niezdominowane + crowding distance) | NSGANetV2, MoSegNAS | Nie modeluje zależności między zmiennymi genotypu |
| NSGA-II + generator historii (Bayesian Network) w fazie eksploatacji | NSGA-Net | BOA to *generator* nowych genotypów, nie predyktor fitness |
| GOMEA / optimal mixing na FOS | GOMEA/ROMEA (Thierens & Bosman), CS-GOMEA, LyMPuS/LT-GOMEA (wariant alternatywny do P3-FIHC-eLyMPuS) | Linkage uczony statystycznie z populacji |
| P3-GOMEA (optimal mixing w piramidzie, bez hill-climbera) | SA-P3-GOMEA, MO-SA-P3-GOMEA (Bartnik) | |
| P3 (FIHC + crossover na Linkage Tree, struktura piramidalna) | P3 (Goldman & Punch), LyMPuS/eLyMPuS (FIHC-eLyMPuS), P3Net | P3Net zastępuje FIHC pętlą: tymczasowa akceptacja przez predyktor → pełna ewaluacja wybranych kandydatów (patrz Krok 3) |
| RV-GOMEA + clique-based conditional linkage | RV-GOMEA + clique linkage | Jedyny silnik **gray-box** |
| GOMEA sterowany metryką zero-cost | GOMEA-NAS + SynFlow | Niska pewność źródła |
| Bayesian Optimization (KDE) + Hyperband | BOHB joint (Zela) | Nie populacja generacyjna |
| Mix EA + BO + Hyperband (5 wariantów) | Bag of Baselines | Żaden z 5 nie modeluje jawnie zależności zmiennych |

**Podpunkt — typ modelu zależności (FOS), doprecyzowanie *jak dokładnie* wygląda krzyżowanie wewnątrz rodziny GOMEA/P3:**

| Wariant FOS | Kto go używa |
|---|---|
| Univariate / Marginal Product | GOMEA/ROMEA (Thierens & Bosman — porównane obok Linkage Tree we własnej pracy źródłowej); wymienione też jako opcje w bibliotece GOMEA (Bouter i in.) |
| Linkage Tree (aglomeracyjne grupowanie hierarchiczne, np. UPGMA nad informacją wzajemną) | GOMEA/ROMEA, CS-GOMEA, P3, P3Net |
| Warunkowy, oparty na maximum-clique (VIG) | RV-GOMEA + clique linkage |
| Rekurencyjne odkrywanie z gwarancją przy pełnym VIG | LyMPuS/eLyMPuS |

---

## Krok 6 — Mutacja

**Luka potwierdzona jako realna cecha rodziny, nie tylko brak danych.** Rekonstrukcja P3Net to potwierdza wprost: cała wariacja P3Net to optimal mixing (Krok 5), żaden osobny operator mutacji nie występuje w opisanej pętli przeszukiwania. Dla całej linii GOMEA/P3 w tym zestawieniu krzyżowanie/optimal mixing robi całą pracę, którą w klasycznym GA dzieli się między krzyżowanie i mutację — to nie przeoczenie źródeł, tylko realna właściwość tej rodziny algorytmów. NSGA-Net ma mutację (bit-flip, maks. 1 bit), ale to pojedynczy, odosobniony fakt bez żadnego kontrastowego wariantu do porównania.

---

## Krok 7 — Selekcja środowiskowa (zastępowanie)

### Oś: Reguła akceptacji / selekcji

| Opcja | Kto już tego używa |
|---|---|
| Elityzm jawny (najlepsze rozwiązanie zawsze przechodzi dalej) | NSGA-Net ("Elitist-preserving", nazwane wprost) |
| Sortowanie niezdominowane + crowding distance | NSGA-Net, NSGANetV2, MoSegNAS |
| Optimal mixing: akceptacja przy braku pogorszenia (próg zero) | P3/GOMEA domyślnie; P3Net ($\hat\delta_F \geq 0$, testowane łącznie z $\kappa$) |
| Forced Improvements (wymuszona poprawa, gdy optimal mixing utknie) | GOMEA/ROMEA, CS-GOMEA |
| Bramka progowa relaksowana (adaptacyjny próg λ-kwantylowy) | SA-P3-GOMEA |
| Bramka probabilistyczna dominacji Pareto | MO-SA-P3-GOMEA (Bartnik) |
| Piramida: nigdy nie odrzuca wcześniej znalezionych dobrych rozwiązań | P3, LyMPuS/OLyMPuS, P3Net |
| Nie dotyczy — model bayesowski/mieszany, brak klasycznej selekcji środowiskowej w sensie GA | BOHB joint (Zela); Bag of Baselines (zależnie od podmetody) |

---

## Krok 8 — Kryterium stopu

**Brak dedykowanej osi — luka źródłowa.** Mamy dane surowe (kolumna "Budżet" w Tabeli C `algorithms_comparison.md`), ale nieujednolicone do porównywalnej postaci "typu kryterium" — każde źródło raportuje inną jednostkę (liczba ewaluacji, GPU-dni, sekundy). Sekcja Proponowany Optymalizator P3Net_pl.md też nie precyzuje tego wprost (prawdopodobnie w Wynikach, poza zakresem tego przeglądu).

---

## Poza konstrukcją (nie krok algorytmu)

### Oś: Domena / typ danych

| Domena | Kto już w niej działa |
|---|---|
| Obrazy — klasyfikacja, pełny trening w pętli | NSGA-Net, NSGANetV2, Bag of Baselines |
| Obrazy — segmentacja semantyczna | MoSegNAS |
| Obrazy — poprzez lookup/benchmark, bez treningu w pętli | MO-SA-P3-GOMEA (Bartnik), GOMEA-NAS + SynFlow, P3Net |
| Obrazy — rzeczywisty trening na każdym kroku (nie lookup) | BOHB joint (Zela) |
| Syntetyczne kombinatoryczne (dyskretne), bez związku z NAS | CS-GOMEA, P3, GOMEA/ROMEA, LyMPuS/eLyMPuS |
| Syntetyczne ciągłe, bez związku z NAS | RV-GOMEA + clique linkage |
| Rzeczywiste dane tabelaryczne, bez związku z NAS | SA-P3-GOMEA |

**Konsekwencja:** mechanizm sprawdzony wyłącznie w domenie "syntetyczne kombinatoryczne" (np. eLyMPuS, model FOS oparty na maximum-clique) nie ma jeszcze potwierdzenia empirycznego w domenie obrazów/NAS. P3Net jest pierwszym testem takiego transferu dla kilku z tych mechanizmów naraz.

---

## Znane ograniczenia łączenia osi

1. **Predyktor relatywny świadomy struktury powiązań (Krok 3) wymaga silnika linkage-aware (Krok 5: GOMEA/P3-rodzina).** Wprost w P3Net_pl.md: "nie może zostać połączony z NSGA-II".
2. **Gray-box (założenie w Kroku 3) wymaga jawnie rozkładalnej funkcji celu.** Dokładność sieci neuronowej tego nie spełnia — stąd cała linia NAS działa black-box z konieczności.
3. **Model piramidalny P3 (Krok 2) wymaga realnej ewaluacji fitness przy każdej zaakceptowanej lokalnej poprawie**, nie tylko na końcu — konsekwencje budżetowe przy małych budżetach.
4. **Kodowanie graf-krawędź-operacja (Krok 1) niesie ryzyko duplikacji i niewykonalności (granica Krok 1/3);** kodowanie pozycyjne oba te ryzyka obniża, ale bez formalnego porównania w źródłach.
5. **Weight-sharing (Krok 3, substrat) ma udokumentowany koszt wiarygodności**, nie tylko oszczędność czasu (Yu i in. 2020).
6. **Zero-cost proxy (Krok 3, rozszerzenie) eliminuje fazę uczenia, ale nie adaptuje się do zadania/danych** jak predyktor uczony na obserwacjach — brak bezpośredniego porównania jakości w źródłach.
7. **Ewaluacja wielopoziomowa (Krok 3, rozszerzenie) ma sens tylko, gdy substrat oferuje tanią, informatywną wersję niskiej wierności** — nie da się jej zastosować do substratu dającego z góry jeden, punktowy wynik.
8. **Naprawa niewykonalności przez "wycinanie" (granica Krok 1/3) jest specyficzna dla kodowań grafowych** — nie ma naturalnego odpowiednika przy kodowaniu pozycyjnym/płaskim, gdzie każdy string jest z definicji poprawny.
9. **Domena walidacji ogranicza wiarygodność transferu mechanizmu** — patrz konsekwencja w sekcji "Poza konstrukcją".
10. **Predyktor relatywny (Krok 3) połączony z selekcją wymagającą porównywalności między różnymi liniami rodowymi (multi-objective, Krok 3: Cele optymalizacji) wymaga mechanizmu składania delt w estymatę porównywalną globalnie** — znalezisko #4. Sam predyktor relatywny mówi tylko "lepszy/gorszy niż mój rodzic", co nie wystarcza do porównania kandydatów z różnych linii w kroku selekcji do pełnej ewaluacji. P3Net rozwiązuje to konstrukcją teleskopową: sumuje delty wzdłuż łańcucha do najbliższego w pełni ocenionego przodka. Algorytmy single-objective z predyktorem relatywnym (CS-GOMEA, eLyMPuS) tego nie potrzebują, bo porównania są zawsze lokalne (rodzic vs dziecko), nigdy między różnymi liniami.
