# Tabela porównawcza algorytmów z bibliografii P3Net

Cel: jawnie rozpisać założenia (kodowanie, benchmark, predyktor, koszt ewaluacji) każdej pracy cytowanej w `P3Net_pl.md`, żeby odwołania w tekście typu "podobnie jak w X" albo "w przeciwieństwie do Y" dało się zweryfikować jednym spojrzeniem, zamiast opierać się na streszczeniu.

Metodologia: 10 prac przeczytanych w całości z lokalnych PDF-ów (`notes/articles`), 11 doszukanych w internecie (arXiv/ar5iv/Crossref) — dla 3 z nich (Özçelik 2026, Whitley i in. 2016, Tran i in. 2023) nie udało się dotrzeć do pełnego tekstu (paywall) — te pozycje są oznaczone niższą pewnością źródła, a poszczególne liczby z nich **wymagają ręcznej weryfikacji przed cytowaniem w artykule**.

Wiersze = algorytmy (nie prace) — jedna praca może dać >1 wariant, ale tu każda dała dokładnie jeden wpis oprócz "Bag of Baselines" (5 metod potraktowanych łącznie, bo to praca stricte porównawcza, nie propozycja jednego algorytmu).

Zobacz też `design_space_mechanisms.md` — ten sam materiał źródłowy, ułożony według osi decyzyjnych (kolejność konstrukcji algorytmu genetycznego) zamiast według algorytmów; przydatny, gdy pytanie brzmi "jakie warianty decyzji X już ktoś przetestował", a nie "czym jest algorytm Y".

---

## Tabela A — Kontekst i cele

| Algorytm | Rok / venue | Domena / dane | Cele optymalizacji | Wspólne arch+HP? | Gdzie w P3Net_pl.md |
|---|---|---|---|---|---|
| NSGA-Net (`lu2019nsganet`, poz. 11) | 2019, GECCO | Obrazy: CIFAR-10/100, CMU-Car | Accuracy vs. #params/FLOPs (multi-obj) | Nie | Wprowadzenie, Prace pokrewne, Proponowany Optymalizator, Diagnostyka |
| NSGANetV2 (`lu2020nsganetv2`, poz. 12) | 2020, ECCV | Obrazy: ImageNet, CIFAR-10/100 + 6 niestandardowych (STL-10, Flowers102, Pets, DTD, Aircraft, CINIC-10) | Accuracy vs #MAdds/#Params/latencja (2–5 celów) | Nie | Wprowadzenie, Prace pokrewne, Metody odniesienia |
| MoSegNAS (`lu2022mosegnas`, poz. 13) | 2022, arXiv | Obrazy: Cityscapes, COCO-Stuff-10K, PASCAL VOC (segmentacja semantyczna) | Accuracy (mIoU) vs latencja sprzętowa | Nie | Prace pokrewne |
| CS-GOMEA (`dushatskiy2019csgomea`, poz. 5) | 2019, GECCO | Syntetyczne kombinatoryczne: Onemax, Trap4, HIFF, NK-landscapes | Single-objective | Nie dotyczy (nie NAS) | Prace pokrewne |
| SA-P3-GOMEA (`dushatskiy2021...`, poz. 6) | 2021, GECCO | Rzeczywiste dane tabelaryczne: OpenML-CC18 (partycjonowanie ensemble SVM) | Single-objective | Nie dotyczy (nie NAS) | Prace pokrewne |
| P3 (`goldman2014parameterless`, poz. 7) | 2014, GECCO | Syntetyczne kombinatoryczne: Trap, HIFF, Rastrigin, NK, Ising, MAX-SAT | Single-objective | Nie dotyczy | Wprowadzenie, Prace pokrewne |
| GOMEA/ROMEA (`thierens2011optimal`, poz. 16) | 2011, GECCO | Syntetyczne kombinatoryczne: OneMax, Trap5, NK-landscape | Single-objective | Nie dotyczy | Wprowadzenie, Prace pokrewne |
| RV-GOMEA + clique linkage (`andreadis2024maxclique`, poz. 1) | 2024, GECCO | Syntetyczne ciągłe gray-box: Sphere, Rosenbrock, rodzina REB | Single-objective | Nie dotyczy | Prace pokrewne |
| LyMPuS / eLyMPuS / OLyMPuS (`przewozniczek2026lympus`, poz. 15) | 2026, GECCO | Syntetyczne kombinatoryczne: Bim10, Dec5, NK, Ising, Max3sat | Single-objective | Nie dotyczy | Wprowadzenie, Prace pokrewne, Proponowany Optymalizator |
| MO-SA-P3-GOMEA (`bartnik2026evolutionary`, poz. 3) | 2026, praca magisterska | Obrazy przez lookup: NAS-Bench-201 / CIFAR-10 | Accuracy vs zużycie energii GPU (2 cele) | Nie (tylko architektura) | Wprowadzenie, Prace pokrewne, Metody odniesienia |
| GOMEA-NAS + SynFlow (`tran2023gomeanas`, poz. 17) | 2023, GECCO Companion | Obrazy przez lookup: NATS-Bench / NAS-Bench-201 | Single-objective (zero-cost proxy) | Nie | Prace pokrewne |
| BOHB joint NAS+HPO (`zela2018towards`, poz. 21) | 2018, ICML AutoML WS | Obrazy: CIFAR-10 | Single-objective, budżet = czas treningu | Tak | Wprowadzenie, Prace pokrewne |
| Bag of Baselines — 5 metod (`guerreroviu2021bagofbaselines`, poz. 8) | 2021, arXiv | Obrazy: Oxford-Flowers (16×16), Fashion-MNIST | Accuracy vs #params (multi-obj) | Tak | Prace pokrewne |

---

## Tabela B — Mechanizm przeszukiwania

| Algorytm | Silnik przeszukiwania | Kodowanie genotypu | Linkage-aware? | Black-box / gray-box | Model populacji |
|---|---|---|---|---|---|
| NSGA-Net | NSGA-II + Bayesian Optimization Algorithm (BOA) w fazie "eksploatacji" | Dyskretne, binarne (DAG komórki, styl Genetic CNN) + wektor całkowity ścieżki rozdzielczości (zwykle zafiksowany) | Nie (BOA modeluje zależności *między fazami*, nie linkage w sensie GOMEA) | Black-box | Pojedyncza, stały rozmiar (generacyjny NSGA-II) |
| NSGANetV2 | NSGA-II | Dyskretne, integer string stałej długości (głębokość/szerokość/kernel/expansion/rozdzielczość, zero-padded) | Nie | Black-box | Pojedyncza, stały rozmiar |
| MoSegNAS | NSGA-II | Dyskretne, integer string stałej długości 29 (zero-padded), przestrzeń ~10^14 | Nie | Black-box | Pojedyncza, stały rozmiar |
| CS-GOMEA | GOMEA (optimal mixing, Linkage Tree, Forced Improvements, IMS) | Dyskretne, binarne, do 400 zmiennych | Tak | Black-box | IMS (równoległe, rosnące populacje) |
| SA-P3-GOMEA | P3-GOMEA (optimal mixing w piramidzie, bez hill-climbera) | Dyskretne, kategorialne, do 500 zmiennych (kardynalność do 10) | Tak | Black-box | Piramida (P3) |
| P3 | FIHC + crossover na Linkage Tree, struktura piramidalna | Dyskretne (binarne w eksperymentach, ale metoda ogólna) | Tak | Black-box | Piramida (P3), bezparametrowa |
| GOMEA/ROMEA | Optimal mixing (GOM/ROM) na FOS: univariate / Marginal Product / Linkage Tree | Dyskretne, binarne, do 200 zmiennych | Tak (linkage uczone statystycznie z populacji) | Black-box (dokładna reewaluacja) | Pojedyncza, z IMS |
| RV-GOMEA + clique linkage | RV-GOMEA (Gene-pool Optimal Mixing, rzeczywistoliczbowe) | Ciągłe, ℝ^ℓ | Tak (clique-based conditional linkage z VIG) | **Gray-box** (jawny dostęp do podfunkcji, tania częściowa reewaluacja) | Pojedyncza, z IMS |
| LyMPuS / eLyMPuS / OLyMPuS | P3 (FIHC-eLyMPuS) i LT-GOMEA; nowy OLyMPuS = piramida + PXrLL | Dyskretne, binarne pseudo-Boolowskie | Tak (odkrywane rekurencyjnie, gwarancja poprawności przy pełnym VIG) | Black-box (surogat *symuluje* dostęp gray-box przez relatywne porównania par, bez jawnych podfunkcji) | Piramida (OLyMPuS) / pojedyncza (LT-GOMEA) |
| MO-SA-P3-GOMEA (Bartnik) | Multi-objective P3-GOMEA z bramką probabilistyczną dominacji Pareto | Dyskretne, kategorialne: 6 zmiennych × alfabet 5 (5⁶=15625) | Tak | Black-box | Piramida (P3) |
| GOMEA-NAS + SynFlow | GOMEA (optimal mixing) sterowany metryką Synaptic Flow | Dyskretne (NATS-Bench/NAS-Bench-201, DAG) — szczegóły niepotwierdzone z pełnego tekstu | Tak | Black-box | Nieznany z dostępnych źródeł (**niska pewność**) |
| BOHB joint (Zela) | Bayesian Optimization (multivariate KDE) + Hyperband (Successive Halving, η=3) | Mieszane: 10 kategorycznych (meta-parametry wielogałęziowego ResNet) + 7 ciągłych (LR, batch size, L2, momentum, MixUp, CutOut, ShakeDrop) | Nie | Black-box | Nie dotyczy (BO, nie populacja generacyjna) |
| Bag of Baselines — 5 metod | SH-EMOA / MO-BOHB / MS-EHVI / MO-BANANAS / BULK&CUT — mix EA+BO+Hyperband | Mieszane: kategoryczne/dyskretne (architektura CNN) + ciągłe (LR, batch size) | Nie (żadna z 5 nie modeluje jawnie zależności zmiennych) | Black-box | Zależnie od metody (SMS-EMOA w SH-EMOA; BO w MS-EHVI; itd.) |

---

## Tabela C — Koszt ewaluacji i wyniki

| Algorytm | Predyktor zastępczy | Mechanizm pełnej ewaluacji | Budżet (zgłoszony) | Kluczowe metryki istotne dla P3Net | Pewność źródła |
|---|---|---|---|---|---|
| NSGA-Net | **Brak klasycznego predyktora regresyjnego** — BOA to generator nowych genotypów (sieć bayesowska nad fazami), nie estymator fitness | Pełny trening od zera | 1200 architektur / 8 dni GPU (populacja 40, 20+10 iteracji) | Redundancja duplikatów genotyp→fenotyp do **~81% przy 6 węzłach/fazę** (Fig. 17, s. 25); błąd 3.85% na CIFAR-10 | Pełny PDF |
| NSGANetV2 | MLP / CART / RBF / GP z Adaptive Switching; **online**, **bezwzględna** regresja accuracy | Fine-tuning wag odziedziczonych z supersieci (weight-sharing + SGD) | **350** pełnych ewaluacji (30 iteracji) | Rank-order corr. ~0.9 Kendall τ (RBF najlepszy na ImageNet); 2–5× szybszy niż NSGA-Net wg hypervolume | Pełny PDF |
| MoSegNAS | RankNet (MLP, ranking loss), **online**, **relatywny/ranking** + osobny lookup latencji per-warstwa | Pełny trening (dekoder BiSeNet stały) | Populacja 1000, 100 generacji, 8 ewaluacji/generację | RankNet Kendall τ=0.6873 (najlepszy z porównanych: SVR τ=0.44, Kriging τ=0.01); lookup latencji τ=0.858 vs FLOPs τ=0.59 | Pełny PDF |
| CS-GOMEA | CNN dylatacyjny, **online**, **relatywny** (regresja różnic fitness par rozwiązań, nie wartości bezwzględnej) | Dokładna ewaluacja funkcji syntetycznej | Zależny od l (do 400 zmiennych) | Zawsze trafia optimum na Onemax/Trap4/HIFF/NK-S1 do l=400, gdy SMAC/Hyperopt zawodzą już >l=16 | Pełny PDF |
| SA-P3-GOMEA | SVR/MLP/RF/GBoost (najlepszy SVR), **online**, bezwzględna regresja, brama akceptacji λ-kwantylowa | Trening SVM na partycji danych | 5000 realnych ewaluacji | Istotnie lepszy niż P3-GOMEA i TPE (Wilcoxon+Holm, α=0.1) na większości konfiguracji | Pełny PDF |
| P3 | Brak | Dokładna ewaluacja funkcji syntetycznej | >10^12 ewaluacji łącznie w kampanii eksperymentalnej | Speedup 1.1–3.1× nad LTGA (instancje 1:1); do 942× (MAX-SAT, klasy losowe) | Pełny PDF |
| GOMEA/ROMEA | Brak | Dokładna ewaluacja | Nie podano zbiorczo | LT-GOMEA rekomendowany jako najefektywniejszy wariant; oryginalny LTGA ~1.7–2.3× mniej efektywny niż ROMEA/GOMEA | Pełny PDF |
| RV-GOMEA + clique linkage | Brak modelu ML — częściowe ewaluacje wykorzystujące strukturę problemu (gray-box) | Częściowa reewaluacja (dokładna, nie aproksymowana) | 10^7 ewaluacji / 3h budżetu, l do 320 (ekstrapolowane) | Istotne różnice między modelami linkage (Mann-Whitney + Bonferroni, p<0.01) na większości problemów testowych | Pełny PDF (arXiv) |
| LyMPuS / eLyMPuS / OLyMPuS | eLyMPuS: **online**, "perfect" pod założeniem monotoniczności, **relatywne porównania parami** (nie regresja) | Dokładna ewaluacja gdy surogat niepewny/graf niekompletny | 2×10^7 FFE / 12h, 30 powtórzeń | Do **88% oszczędności** realnych ewaluacji (Tab. 4); OLyMPuS najlepszy w 10/16 problemów testowych | Pełny PDF |
| MO-SA-P3-GOMEA (Bartnik) | SVR/MLP/RF/GBoost (deterministyczne) + RF-dev/GBoost-quantile/MC-dropout-MLP/GP (probabilistyczne); **online**; bezwzględna regresja obu celów (joint i per-objective) | Lookup NAS-Bench-201 (accuracy) + bezpośredni pomiar zużycia GPU przez NVML (energia) | 500 realnych ewaluacji (3.2% z 15625, w tym 100 warm-up) | HV≈354 (najlepszy wariant probabilistyczny) vs 280 (P3-GOMEA bez surogatu) na training energy, Wilcoxon p<0.05; przewaga dużo mniejsza na inference energy | Pełny PDF (praca magisterska) |
| GOMEA-NAS + SynFlow | **Brak** — zero-cost proxy Synaptic Flow (metryka z gradientów, bez treningu) zamiast wyuczonego modelu | Zero-cost (jeden forward/backward pass) | Brak danych | Brak konkretnych liczb w dostępnych źródłach (ACM paywall) | **Tylko metadane + README GitHub — niska pewność** |
| BOHB joint (Zela) | KDE (multivariate Kernel Density Estimator) jako model BO | Trening SGD, budżet = czas (400s–3h, Hyperband η=3) | Nie podano wprost liczby konfiguracji | Błąd testowy 3.18%±0.16% (budżet 3h) < ResNet-18 3.34%; niska korelacja krótki↔długi budżet (rzędu ~0.05) | Pełny tekst (ar5iv) — **liczby do ręcznej weryfikacji** |
| Bag of Baselines — 5 metod | Zależnie od metody: ensemble NN (MO-BANANAS), MOTPE/KDE (MO-BOHB), GP tylko dla drogiego celu (MS-EHVI), brak (SH-EMOA, BULK&CUT poza HP) | Pełny trening (do 25 epok) | 24h na RTX 2080 Ti, 10 uruchomień | Hypervolume: BULK&CUT najlepszy na Flowers (329.5±1.4), MS-EHVI najlepszy na Fashion-MNIST (479.1±4.2) | Pełny PDF (arXiv) |

---

## Prace poboczne (benchmarki, survey'e, teoria, biblioteki, studia empiryczne)

Nie dostały wiersza w tabelach powyżej (nie są algorytmami przeszukiwania), ale definiują pojęcia/dane, do których inne wiersze się odwołują.

**JAHS-Bench-201** (`bansal2022jahsbench`, poz. 2) — Benchmark. Kodowanie mieszane: dyskretna komórka NAS-Bench-201 (5⁶=15625 architektur) + hiperparametry kategoryczne (aktywacja, augmentacja) i ciągłe (LR, weight decay) + 4-wymiarowa oś wierności (N/W/R/epoch). Surogat pod spodem: XGBoost per metryka, Kendall τ do 0.994 na CIFAR-10. 3 zadania: CIFAR-10, Colorectal-Histology, Fashion-MNIST, ~161M punktów danych. Wspólne arch+HP jest tu celem centralnym — eksperyment kontrolny pokazuje, że pełne JAHS jest 29–33× szybsze niż HPO-only/NAS-only osobno. *Pełny PDF przeczytany.*

**NAS-HPO-Bench-II** (`hirose2021nashpobenchii`, poz. 9) — Benchmark. Dyskretna siatka: komórka DAG 4 węzły/6 krawędzi/4 operacje (4⁶=4096, redukcja do 1K przez izomorfizm) × 48 kombinacji LR/batch size. Hybrydowy surogat: dokładny lookup dla treningu 12-epokowego, model GIN+MLP (bagging ×10, R²=0.876) dla treningu 200-epokowego. CIFAR-10. Metody wspólne (joint) wyraźnie przewyższają sekwencyjne (BOHB najlepszy: 87.86%±0.89 po 200 epokach). *Pełny PDF przeczytany.*

**A Survey on Evolutionary NAS** (`liu2023survey`, poz. 10) — Survey, >200 prac ENAS. Klasyfikuje kodowania (layer/block/cell/topology-based; fixed vs variable-length) i predyktory (learning-curve-based vs end-to-end, głównie offline/bezwzględne w cytowanych pracach). **Nie podaje liczbowego wskaźnika "duplication ratio"** — najbliższe temu są mechanizmy hashowania/pamięci populacji unikające re-ewaluacji identycznych architektur (Fujino, Miahi, Sun, Johner — bez procentowej statystyki). *Pełny PDF przeczytany.*

**Neural Architecture Search: Insights from 1000 Papers** (`white2023insights`, poz. 18) — Survey, >1000 prac. **Ważna uwaga redakcyjna:** nie stwierdza wprost "NSGA-II+surogat to dominujący paradygmat" — mówi ogólnie o popularności rodziny multi-objective EA (w tym NSGA-II) + surogat, bez wskazania jednego dominującego algorytmu. NAS-Bench-101 = dokładnie 423 624 unikalne architektury. Obserwuje niską wariancję wydajności w przestrzeni DARTS (~10^18 architektur) — to redundancja *funkcjonalna* (podobna wydajność różnych architektur), nie tożsamość zakodowanych stringów, czyli **inne zjawisko niż duplication rate NSGA-Net**. Brak liczbowego wskaźnika duplikacji genotypów. *Pełny PDF przeczytany.*

**Evolutionary neural architecture search: a survey** (`ozcelik2026survey`, poz. 14) — Survey, 164 prac ENAS (2020–2024). ES dominuje (45.7%), GA (29.9%); surogaty "znacząco rosną od 2023–2024". **Niska pewność** — tylko abstrakt zweryfikowany przez Crossref, pełny tekst niedostępny (bardzo świeża publikacja, t. 34 nr 4 2026).

**Gray Box Optimization for Mk Landscapes** (`whitley2016graybox`, poz. 19) — Teoria. Dowodzi, że Gray Box Optimization efektywnie oblicza hyperplane averages w O(n), rozwiązując niektóre problemy w O(1) ewaluacji. To fundament ścisłego sensu "gray-box" (jawny dostęp do podfunkcji celu) używanego w tekście P3Net do kontrastu z reżimem black-box P3Net. **Niska/średnia pewność** — tylko abstrakt zweryfikowany przez Crossref, pełny tekst zablokowany (MIT Press paywall).

**A Joint Python/C++ Library for GOMEA** (`bouter2023library`, poz. 4) — Biblioteka-implementacja, nie algorytm. Pakiet `gomea` z osobnymi modułami discrete/real-valued, kilkoma modelami linkage (Univariate, Linkage Tree, Conditional). Testowana na trap function, MaxCut, Rosenbrock — brak jakiegokolwiek związku z NAS. GBO redukuje liczbę ewaluacji nawet o rząd wielkości względem BBO na tych samych problemach. *Pełny PDF przeczytany.*

**Evaluating the Search Phase of NAS** (`yu2020evaluatingnas`, poz. 20) — Studium empiryczne (nie proponuje algorytmu), ocenia ENAS/DARTS/NAO/random search na NAS-Bench-101. Kluczowy wniosek: korelacja rankingu (Kendall τ) między dokładnością z weight-sharing a niezależnym treningiem **spada wraz ze wzrostem złożoności przestrzeni** (rzędu 0.44→0.20 przy 3→7 węzłach); dla przestrzeni RNN korelacja bliska zeru. Bezpośrednio uzasadnia, dlaczego P3Net (i NSGANetV2) sięgają po osobny wyuczony predyktor zamiast (zawodnego) weight-sharing jako "taniego surogatu". *Pełny tekst przeczytany (ar5iv), liczby do ręcznej weryfikacji.*

---

## Uwagi redakcyjne wynikające z tego researchu

1. **Zdanie o "trzech przeglądach potwierdzających dominujący paradygmat NSGA-II+surogat"** (Prace pokrewne, linia 36) — White i in. 2023 tego wprost nie potwierdza; mówi o popularności rodziny MOEA+surogat, nie o dominacji konkretnie NSGA-II. Warto rozważyć złagodzenie sformułowania.
2. **NSGA-Net nie ma klasycznego predyktora regresyjnego** — używa Bayesian Optimization Algorithm (sieć bayesowska) jako *generatora* nowych genotypów w fazie eksploatacji, nie jako estymatora fitness. Jeśli tekst gdziekolwiek sugeruje, że NSGA-Net ma "predyktor" w tym samym sensie co NSGANetV2, to nieścisłość.
3. **[ZAKTUALIZOWANE — już wpisane do P3Net_pl.md] Redundancja duplikatów u NSGA-Net (60–80%, dochodzące do ~81%) dotyczy kodowania grafu komórki (DAG)** — pierwotnie sądziłem, że żadna inna praca w zestawieniu nie używa tego typu kodowania. To nieprawda: **NAS-Bench-201** (Dong & Yang, ICLR 2020, Appendix A) używa dokładnie tego typu kodowania (4 węzły, 6 krawędzi, 5 operacji, 5⁶=15625) i jawnie **nie deduplikuje** — tylko 6466/15625 (~41%) jest topologicznie unikalnych, czyli ~59% duplikacji, w tym samym paśmie co NSGA-Net. **JAHS-Bench-201** (jeden z dwóch głównych benchmarków P3Net) jest zbudowany bezpośrednio na tej przestrzeni (Tabela 1/7 w Bansal i in. 2022 podaje identyczne 15625, nie zredukowaną liczbę) i dziedziczy ten brak deduplikacji (Sekcja 6: "we inherit its scope for included architectures"). NAS-HPO-Bench-II natomiast DEDUPLIKUJE (4096→~1K). White i in. 2023 opisują *inne* zjawisko (redundancja funkcjonalna w przestrzeni DARTS), które nie powinno być mylone z duplication rate.
4. **Zela i in. 2018 przeszukuje meta-parametry wielogałęziowego ResNet, nie komórki w stylu DARTS/NAS-Bench-201** — jeśli tekst P3Net opisuje tę pracę jako operującą na "operacjach komórki", to wymaga korekty.
5. **Trzy pozycje o niskiej pewności źródła** (Özçelik 2026, Whitley i in. 2016, Tran i in. 2023) — żadnych konkretnych liczb z nich nie należy cytować bez dodatkowej weryfikacji (dostęp instytucjonalny do MIT Press/ACM DL albo kontakt z autorami).
