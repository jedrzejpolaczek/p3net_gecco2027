# Krajobraz algorytmów genetycznych i (MO-)NAS — stan na 2026-07

Notatka orientacyjna do pozycjonowania P3Net (P3 + surrogate predictor jako alternatywa dla NSGANetV2)
względem obecnego stanu dziedziny. Sporządzona na podstawie przeglądu literatury (WebSearch) w trakcie
pracy nad artykułem `nas_compare`.

> **PILNE (2026-07):** Promotor autora to Michal Witold Przewoźniczek (patrz sekcja 11) — jego własna,
> właśnie opublikowana praca (GECCO 2026, LyMPuS) łączy linkage discovery z surrogate'em w tej samej
> rodzinie algorytmów co P3. To bezpośrednio dotyka rdzenia pomysłu P3Net. Szczegóły w sekcji 11.
>
> **ROZSTRZYGNIĘTE:** autor porozmawiał z promotorem. Kierunek potwierdzony i zasugerowany przez samego
> Przewoźniczka: przenieść jego linię linkage-learning/surrogate (P3/GOMEA/LyMPuS) na domenę NAS —
> Przewoźniczek sam nie zajmuje się NAS, więc to naturalne rozszerzenie jego metod, nie konkurencja
> wobec czegoś, co on already robi.
>
> **Sekcja 12 zawiera pełną weryfikację źródłową** — 12 z 13 pobranych PDF-ów przeczytanych w całości
> (nie tylko streszczenia/wyniki WebSearch), ze skorygowanymi/dopracowanymi faktami.
>
> **⚠️ NAJWAŻNIEJSZE, PILNE (2026-07-22): sekcja 13.** Praca magisterska Niny Bartnik ("Evolutionary
> optimization of deep neural networks", WUST 2026, promotor: Przewoźniczek) adaptuje SA-P3-GOMEA do
> multi-objective NAS na NAS-Bench-201 (dokładność + zmierzona energia GPU). To ta sama rodzina algorytmów,
> ten sam promotor, ta sama domena (NAS), ten sam rok. **Zdanie o luce w `related_work.tex` ("P3 has not
> previously been combined with a surrogate in NAS") jest teraz nieprawdziwe w tej formie — wymaga
> natychmiastowej korekty i rozmowy z promotorem, zanim cokolwiek dalej się napisze.**

## Uwaga o metodologii i sile dowodów

Każda sekcja ma teraz blok **"Poziom dowodu"** rozróżniający trzy kategorie źródeł, od najmocniejszych do
najsłabszych:

- **Systematyczny przegląd / bibliometria** — dane liczbowe z wielu baz (Scopus/WoS/IEEE Xplore) albo
  systematyczna klasyfikacja dużej próby prac (np. 164 studiów ENAS). To najbliższe "dowodowi trendu"
  w ścisłym sensie.
- **Pojedyncza praca jako instancja trendu** — konkretna publikacja pokazująca, że coś się dzieje, ale
  sama w sobie nie dowodzi skali zjawiska. Traktuj jako ilustrację, nie potwierdzenie.
- **Dowód negatywny (brak w źródle)** — wnioskowanie z tego, czego dana systematyczna praca NIE wymienia.
  Słabszy typ dowodu (przegląd mógł czegoś nie objąć), ale wart odnotowania, gdy przegląd jest świeży
  i metodyczny.

Żadne z poniższych nie jest formalnym systematic literature review z protokołem PRISMA — to przegląd
orientacyjny robiony pod kątem jednego artykułu, nie osobna metaanaliza. Traktuj jako punkt wyjścia do
dalszej weryfikacji, nie jako gotowe cytaty bez sprawdzenia źródła pierwotnego.

## 1. Trendy w Genetic Algorithms / EC (ogólnie)

- Pole żywe i rosnące bibliometrycznie (GECCO 2025: ~1670 stron proceedings + 2615 stron companion).
- Trzy główne kierunki innowacji:
  - **(a)** hybrydyzacja z LLM (LLM jako operator genetyczny albo optymalizator) — patrz survey arXiv:2509.08269.
  - **(b)** automatyzacja projektowania metaheurystyk (hyper-heuristics, algorithm configuration).
  - **(c)** dalszy rozwój linkage-learning / gray-box optimization (patrz sekcja 5).
- Zastosowania praktyczne rosną (feature selection w ML, projektowanie inżynierskie, planowanie procesów),
  ale to nie jest miejsce nowości metodologicznej.

**Poziom dowodu:**
- *Systematyczny przegląd/bibliometria:* Özçelik, Efe — "Five Decades of Genetic Algorithms: A Systematic
  and Bibliometric Review (1975–2025)", Archives of Computational Methods in Engineering (Springer, 2026).
  Analiza >26 707 publikacji z Scopus, WoS i IEEE Xplore, sieci cytowań, mapy krajów/instytucji, 12 domen
  zastosowań. To najmocniejsze źródło całej notatki — realna bibliometria, nie pojedyncza opinia.
  DOI: 10.1007/s11831-025-10487-2.
- *Systematyczny przegląd (węższy zakres):* Zhang, Cheng, Yi, Tan — "A Systematic Survey on Large Language
  Models for Evolutionary Optimization: From Modeling to Solving" (arXiv:2509.08269, wrzesień 2025).
  Ustrukturyzowana taksonomia (modelowanie / rozwiązywanie, trzy paradygmaty roli LLM), obejmuje literaturę
  od stycznia 2023 — realny przegląd, nie pojedynczy artykuł.
- *Uwaga:* dane o "27 latach GECCO i ~1670 stronach proceedings 2025" to fakt organizacyjny (rozmiar
  konferencji), nie dowód treściowy trendu — traktuj jako kontekst, nie potwierdzenie konkretnej tezy.

## 2. Trendy w MO-NAS (Multi-Objective NAS)

- Ciężar innowacji przesunął się z "jaki EA użyć" na **"jak tanio i trafnie ocenić kandydata"**.
- Surrogate coraz częściej uczy się **rankingu / relacji dominacji Pareto** zamiast bezwzględnej dokładności:
  - Pareto-wise Ranking Classifier (IEEE TEVC 2024)
  - SiamNAS — Siamese Surrogate Model for Dominance Relation Prediction (GECCO 2025, arXiv:2506.02623)
  - Pairwise Comparison Relation-assisted MO-NAS z multi-populacją (arXiv:2407.15600)
- Drugi nurt: transfer/meta-wiedza między zadaniami NAS (transfer stacking + knowledge distillation,
  IEEE TEVC 2024; meta-knowledge assisted ENAS, arXiv:2504.21545).
- Trzeci: multi-fidelity / continuous encoding (arXiv:2509.01943), novelty search + dominacja Pareto
  (arXiv:2407.20656).
- **Nikt w tym nurcie nie zamienił backbone'u NSGA2 na strukturalnie inny mechanizm selekcji/generacji** —
  innowacja dzieje się wokół predyktora i reprezentacji, nie wokół silnika ewolucyjnego. To realna nisza.

**Poziom dowodu:**
- *Systematyczny przegląd — najważniejsze źródło tej sekcji:* Özçelik, Efe — "Evolutionary neural
  architecture search: a survey", Turkish Journal of Electrical Engineering and Computer Sciences,
  vol. 34, nr 4, s. 507–541 (2026). Systematyczna klasyfikacja **164 prac ENAS z lat 2020–2024** wg
  zastosowanego algorytmu ewolucyjnego. Konkretne, policzalne ustalenia:
  - Evolution Strategies (ES): 45,7% prac; Genetic Algorithms (GA) i pochodne: 29,9%.
  - Liczba publikacji rocznie wzrosła **6,6×** w latach 2020–2024.
  - Wzrost metod surrogate-assisted skoncentrowany w 2023–2024.
  - Podejścia multi-objective oparte o GA (NSGA-II, NSGA-III) **dominują** w wyszukiwaniu frontu Pareto.
  To jedyne w tej notatce twierdzenie poparte faktyczną, świeżą, ilościową klasyfikacją literatury —
  reszta sekcji 2 to pojedyncze prace ilustrujące te liczby, nie osobne dowody.
- *Pojedyncze prace jako instancje trendu* (ranking/dominance classifier, transfer knowledge,
  multi-fidelity) — SiamNAS, Pairwise Comparison MO-NAS, meta-knowledge ENAS, multi-fidelity encoding.
  Każda z osobna to jedna publikacja; siłę mają dopiero razem z wynikiem przeglądu Özçelik/Efe pokazującym
  ogólny wzrost kategorii "surrogate-assisted" w tym samym okresie.

## 3. Trendy w NAS (szerzej niż evolutionary/MO)

- Dominujący kierunek redukcji kosztu: **zero-cost proxies** (ocena po jednym mini-batchu) i
  **one-shot / weight-sharing supersieci** — próba niemal całkowitej eliminacji pełnego treningu.
- Krytyka zero-cost proxy udokumentowana: korelacje z trywialnymi statystykami (liczba parametrów, głębokość),
  utrata mocy rozróżniającej w czołówce architektur → stąd ensemble proxy (np. GreenFactory, >20 proxy + random forest).
- Nowy wyraźny nurt 2025: **LLM-driven NAS** (CoLLM-NAS, arXiv:2509.26037; LLM-NAS, arXiv:2510.01472).
- Ogólny obraz: konwergencja w stronę hybryd (EA + zero-cost + one-shot), rzadko czysto ewolucyjne metody
  z pełnym treningiem każdego kandydata.

**Poziom dowodu:**
- *Systematyczny przegląd:* White, Safari, Sukthanker, Ru, Elsken, Zela, Dey, Hutter — "Neural Architecture
  Search: Insights from 1000 Papers" (arXiv:2301.08727, 2023). Taksonomia przestrzeni przeszukiwań,
  algorytmów i technik przyspieszania (w tym zero-cost proxies) na podstawie >1000 prac NAS od 2020 r.
  Autorzy to czołowi badacze NAS (Hutter — współtwórca AutoML.org) — źródło wysokiej wiarygodności, choć
  z 2023 r., więc nie obejmuje najnowszych 2 lat.
- *Dedykowany benchmark/krytyczna ewaluacja:* "NAS-Bench-Suite-Zero: Accelerating Research on Zero Cost
  Proxies" (arXiv:2210.03230) oraz "An Evaluation of Zero-Cost Proxies" (IJCV, Springer 2024) —
  systematyczna, ilościowa ewaluacja wielu proxy na wielu przestrzeniach przeszukiwań, potwierdzająca
  zarówno popularność, jak i udokumentowane słabości (korelacja z trywialnymi statystykami).
- *Pojedyncze prace jako instancje trendu:* CoLLM-NAS (arXiv:2509.26037), LLM-NAS (arXiv:2510.01472) —
  **LLM-driven NAS to na razie 2 konkretne prace znalezione w wyszukiwaniu, nie potwierdzony masowy
  nurt.** Kontekstowo wspierane przez szerszy systematyczny przegląd LLM+EC (arXiv:2509.08269, sekcja 1),
  który wymienia NAS jako jedną z domen zastosowań, ale to nie to samo, co dedykowana bibliometria LLM-NAS.
  Traktuj to zdanie w sekcji 3 jako najsłabiej potwierdzone w całej notatce.

## 4. Czy NSGANetV2 jest dalej "trendy"?

- Jako konkretna implementacja z 2020 r. — nie jest tym, co dziś cytuje się jako SOTA.
- Jako wzorzec architektoniczny (NSGA2 + surrogate + selekcja elity do pełnego treningu) — **wciąż żywy**,
  rozwijany przez ulepszanie predyktora (sekcja 2), nie przez zmianę silnika ewolucyjnego.
- **NSGA-II pozostaje dominującym, standardowym baseline'em w MOEA również w 2025** — nic go nie zdetronizowało.
  Prace 2025 usprawniają NSGA-II (dynamiczny rozmiar populacji — arXiv:2509.01739, szybszy tie-breaking —
  AAAI 2025) zamiast go zastępować.
- **Wniosek:** nie ma dziś "modnego" GA, który zastąpił NSGA2 w MO-NAS. To wzmacnia pozycję P3Net —
  eksperyment podstawienia P3 w miejsce NSGA2 nie został jeszcze systematycznie zrobiony.

**Poziom dowodu:**
- *Dane bibliometryczne (cytowania):* NSGA-II (Deb i in., 2002, IEEE TEVC) ma ok. **45 530 cytowań**
  wg Semantic Scholar, **>35 240** wg Google Scholar, **>20 630** wg IEEE Xplore, gdzie jest **4. najczęściej
  cytowanym artykułem w całej bazie IEEE Xplore**. To bardzo mocny, łatwo weryfikowalny wskaźnik
  utrzymującej się centralności algorytmu w polu (cytowania kumulują się też historycznie, więc to nie
  dowodzi samo w sobie "trendu 2025", ale dowodzi statusu fundamentalnego punktu odniesienia).
- *Systematyczny przegląd, dowód specyficzny dla NAS:* ten sam przegląd Özçelik/Efe z sekcji 2 —
  "GA-based multiobjective approaches (NSGA-II, NSGA-III) dominate Pareto-optimal architecture search"
  w próbie 164 prac ENAS 2020–2024. To najmocniejszy, bo świeży i domenowo trafny dowód.
  - **Sprostowanie:** poprzednia wersja tej sekcji cytowała ogólne prace 2025 usprawniające NSGA-II
    (dynamic population sizes, tie-breaking) jako dowód "braku detronizacji" — to dobra ilustracja, ale
    to pojedyncze prace, nie przegląd; nie traktuj ich jako samodzielnego dowodu ilościowego.

## 5. Trendy w linkage-learning (poza NAS)

- Aktywny, ale niszowy podnurt EC, silnie związany z linią Peter Bosman / CWI / TU Delft.
- GECCO 2025: sesja o "empirical linkage learning" (dowody poprawności modelu linkage na problemach
  trap / H-IFF).
- Główny kierunek rozwoju: rozszerzenie na przestrzenie rzeczywiste — RV-GOMEA (arXiv i GECCO 2017,
  DOI 10.1145/3071178.3071272) oraz nowsze prace o "fitness-based linkage learning" i "maximum-clique
  conditional linkage modelling" dla gray-box optimization (arXiv:2402.10757, 2024).

**Poziom dowodu:**
- **Brak tu systematycznego przeglądu/bibliometrii — to najsłabiej udokumentowana sekcja notatki.**
  Nie znalazłem dedykowanego survey'u ilościowego dla samej rodziny GOMEA/P3/linkage-learning (w
  przeciwieństwie do sekcji 1–4, gdzie takie przeglądy istnieją). Poniższe to sygnały pośrednie, nie dowód
  ilościowy skali trendu:
  - *Sygnał realnego zastosowania (silniejszy niż sama publikacja):* RV-MO-GOMEA użyty do planowania
    brachyterapii — otrzymał **Silver Humies Award** (nagroda Human-Competitive Results przyznawana na
    GECCO za wyniki konkurencyjne wobec rozwiązań ludzkich w realnych zastosowaniach). To niezależne od
    autorów potwierdzenie praktycznej wartości, nie tylko akademickie cytowanie.
  - *Sygnał inwestycji infrastrukturalnej:* "A Joint Python/C++ Library for Efficient yet Accessible
    Black-Box and Gray-Box Optimization with GOMEA" (arXiv:2305.06246) — społeczność inwestuje w
    dostępność narzędziową, co zwykle towarzyszy rosnącej, nie zanikającej, aktywności badawczej.
  - *Pojedyncze prace GECCO 2024–2025* (runtime GOMEA na concatenated trap function, empirical linkage
    learning) — potwierdzają ciągłość aktywności teoretycznej, ale to małe, wyspecjalizowane grono (linia
    Bosman/CWI/TU Delft), nie masowy nurt porównywalny skalą do sekcji 1–3.
- **Rekomendacja:** jeśli w artykule chcesz twierdzić "linkage-learning to aktywny nurt", oprzyj to na
  konkretnych, policzalnych faktach z powyższych punktów (Humies Award, biblioteka, konkretne prace GECCO
  z datami), a nie na ogólnym stwierdzeniu "obszar jest aktywny" — bo tego nie potwierdza żaden przegląd.

## 6. Czy linkage-learning jest używany w NAS?

> **AKTUALIZACJA (po dedykowanym przeszukaniu "GOMEA NAS"):** poniższe pierwotne twierdzenie było za mocne
> i zostało obalone przez konkretną pracę — patrz "Ważna korekta" niżej. Zostawiam oryginalny tekst
> przekreślony/oznaczony, żeby było widać, jak zmieniła się ocena, zamiast czyścić historię notatki.

- ~~**Praktycznie wcale.**~~ **Nieprawda w tej formie — GOMEA (rodzic P3) był już użyty w NAS.**
  Wcześniej znalezione prace tej samej grupy badawczej (Dushatskiy/Alderliesten/Bosman, CWI/TU Delft)
  stosują linkage-learning + surrogate do ogólnej optymalizacji dyskretnej/kombinatorycznej, nie do NAS:
  - CS-GOMEA — Convolutional neural network surrogate-assisted GOMEA (GECCO 2019,
    DOI 10.1145/3321707.3321760, kod: github.com/ArkadiyD/CS-GOMEA)
  - SA-P3-GOMEA — surrogate-assisted P3-GOMEA, linia Dushatskiy/Alderliesten/Bosman (arXiv:2104.08048)

### Ważna korekta: GOMEA w NAS już istnieje (2023)

**Tran, Truong, Vo, Luong — "Accelerating Gene-pool Optimal Mixing Evolutionary Algorithm for Neural
Architecture Search with Synaptic Flow"**, GECCO 2023 Companion Proceedings (Lisbon), grupa Ngoc Hoang
Luong (VNU-HCM, Wietnam). To praca, która **wprost łączy GOMEA (rodzic P3, ta sama rodzina
linkage-learning) z NAS**, używając **Synaptic Flow** — zero-cost proxy (metryka liczona analitycznie z
sieci bez treningu, np. z gradientów wag) — jako taniego zastępnika pełnej ewaluacji podczas generowania
kandydatów przez GOMEA.

Ta sama grupa (Ngoc Hoang Luong i współpracownicy) ma całą aktywną linię badań nad MOENAS 2021–2024:
- Enhancing MOENAS with Surrogate Models and Potential Point-Guided Local Searches (2021) — surrogate
  (uczony predyktor dokładności) + lokalne przeszukiwanie, ale **generyczny MOEA, nie GOMEA/P3**.
- Enhancing MOENAS with training-free Pareto local search (Applied Intelligence, 2023).
- Efficient MO-NAS via Pareto Dominance-based Novelty Search (GECCO 2024).
- Lightweight MOENAS with low-cost proxy metrics.

**Co to zmienia dla P3Net:** luka nie jest już "linkage-learning EA w NAS praktycznie nie istnieje" — to
nieprawda, GOMEA w NAS istnieje od 2023 r. Luka zawęża się do dwóch, wciąż realnych różnic, które musicie
jawnie i precyzyjnie nazwać w Related Work:
1. **P3 vs GOMEA** — Tran et al. użyli GOMEA (stały rozmiar populacji, wymaga strojenia), nie P3
   (parameter-less population pyramid). To wciąż realna różnica architektoniczna.
2. **Zero-cost proxy vs uczony surrogate** — Synaptic Flow to metryka analityczna liczona bez treningu i
   bez danych z wcześniejszych ewaluacji; surrogate predictor (jak w NSGANetV2 i planowanym P3Net) to
   **model uczony na wynikach częściowych pełnych treningów**. To fundamentalnie inny mechanizm redukcji
   kosztu — nie jest to to samo, ale trzeba to jawnie odróżnić, a nie milczeć.

Precyzyjne sformułowanie luki po korekcie:
  - "linkage-learning EA + surrogate (uczony predyktor)" **już istnieje** (CS-GOMEA, SA-P3-GOMEA) — poza NAS,
  - "linkage-learning EA (GOMEA) w NAS" **już istnieje** (Tran et al. 2023) — ale z zero-cost proxy, nie surrogate'em,
  - "**P3 (nie GOMEA) + uczony surrogate w NAS**" — to jedyna kombinacja, dla której nie znalazłem żadnej
    pracy. To węższa, ale wciąż realna i broniąca się luka.

**Poziom dowodu:**
- *Dowód negatywny, obalony przez dedykowane wyszukiwanie — pouczający przykład na przyszłość:*
  systematyczny przegląd Özçelik/Efe (sekcja 2/4) klasyfikuje 164 prace ENAS 2020–2024 wg algorytmu i
  **nie wymienia GOMEA/P3/linkage-tree jako osobnej kategorii** — na tej podstawie pierwsza wersja tej
  notatki wywnioskowała "linkage-learning w NAS praktycznie nie istnieje". Jedno konkretne, dedykowane
  wyszukiwanie hasła "GOMEA neural architecture search" (zalecone tu wcześniej jako krok weryfikacyjny)
  od razu znalazło kontrprzykład (Tran et al. 2023). **Wniosek metodologiczny: nieobecność kategorii w
  przeglądzie o szerokim zakresie nie jest wiarygodnym dowodem nieistnienia wąskiej, specjalistycznej
  kombinacji — trzeba zawsze dodatkowo zrobić bezpośrednie wyszukiwanie danej kombinacji słów kluczowych.**
- *Pozytywny dowód istnienia:* Tran, Truong, Vo, Luong — GECCO 2023 Companion — konkretna, zweryfikowana
  publikacja łącząca GOMEA z NAS. To pojedyncza praca (nie systematyczny przegląd), ale wystarcza jako
  dowód *istnienia*, w przeciwieństwie do dowodu *nieistnienia*, gdzie potrzeba wyczerpującego przeszukania.
- *Nadal niepotwierdzone wyczerpująco:* czy ktoś użył **P3 konkretnie** (nie GOMEA) w NAS, i czy ktoś użył
  **uczonego surrogate'u** (nie zero-cost proxy) razem z linkage-learning EA w NAS. Żadne z wyszukiwań
  wykonanych w tej notatce (kilkanaście zapytań WebSearch) tego nie znalazło, ale — jak pokazuje powyższy
  przykład — to nie jest dowód rozstrzygający. Przed złożeniem artykułu zalecane bezpośrednie przeszukanie
  DBLP/Google Scholar fraz "P3 neural architecture search", "parameter-less population pyramid NAS".

## 7. Jak CS-GOMEA / SA-P3-GOMEA / RV-GOMEA odnoszą się do P3Net?

To pytanie osobne od "czy jest to trend" — chodzi o **bezpośrednie pokrewieństwo metodologiczne**, nie o
popularność. Te trzy prace nie są przypadkowymi cytatami z tej samej rodziny algorytmów — to konkretny
łańcuch dowodowy, który trzeba jawnie umieścić w Related Work, bo inaczej recenzent z community GOMEA/P3
zrobi to za Ciebie (i wypadnie to gorzej):

- **CS-GOMEA** (Dushatskiy, Mendrik i in., GECCO 2019) — pierwszy dowód, że **linkage-tree/FOS-based
  variation (rodzina GOMEA, ta sama co P3) da się sprzęgnąć z siecią neuronową jako surrogate'em**, zamiast
  kosztownej ewaluacji. Mechanicznie to dokładnie to, co robi P3Net (surrogate zastępuje część ewaluacji
  wewnątrz pętli linkage-learning EA) — różnica: CS-GOMEA testowano na syntetycznych funkcjach
  benchmarkowych ze zmiennymi kategorycznymi, nie na architekturach sieci i nie na GOMEA wariancie P3.
  **Znaczenie dla P3Net:** to dowód wykonalności na poziomie mechanizmu (surrogate + linkage-tree EA
  współpracują), ale nie dowód na to, że działa to w NAS ani że działa z P3 (a nie GOMEA).
- **SA-P3-GOMEA** / "Novel Surrogate-assisted EA Applied to Partition-based Ensemble Learning" (Dushatskiy,
  Alderliesten, Bosman, GECCO 2021, arXiv:2104.08048) — to **bliższy krewny P3Net niż CS-GOMEA**: (1) używa
  wariantu **P3-GOMEA**, nie samego GOMEA, więc jest bliżej Twojego P3, (2) stosuje surrogate do **realnego,
  kosztownego problemu związanego z ML** (dobór partycji do ensemble learning), a nie do syntetycznego
  benchmarku. To najbliższy istniejący precedens metodologiczny — właściwie brakuje mu tylko domeny NAS
  i architektura-specyficznej struktury zależności (np. sąsiedztwa warstw), żeby być tym, co proponujesz.
  **Praktyczna konsekwencja:** w Related Work musisz jasno powiedzieć, czym P3Net różni się od SA-P3-GOMEA
  — najprawdopodobniej: (a) domena (NAS vs. ensemble learning), (b) natura przestrzeni przeszukiwania
  (architektura sieci ma inną strukturę zależności niż dobór partycji danych), (c) rodzaj surrogate'u
  (predyktor dokładności/rankingu sieci vs. cokolwiek przewiduje SA-P3-GOMEA w swoim problemie). Pominięcie
  tej pracy w cytowaniach byłoby najsłabszym punktem artykułu dla recenzenta znającego linię Bosman/CWI.
- **RV-GOMEA** (Real-Valued GOMEA, Bouter i in., GECCO 2017, DOI 10.1145/3071178.3071272) — **słabiej
  bezpośrednio powiązany**. To rozszerzenie linkage-learning na zmienne ciągłe, podczas gdy typowe
  przestrzenie przeszukiwania NAS są dyskretne/kategoryczne (wybór operacji, liczba kanałów jako opcje).
  RV-GOMEA jest tu **dowodem dojrzałości i elastyczności rodziny GOMEA/P3** (pokazuje, że linkage-learning
  nie jest ograniczony do przestrzeni binarnych) — istotny tylko bezpośrednio, jeśli Twoja przestrzeń
  przeszukiwania P3Net zawiera komponenty ciągłe (np. współczynniki szerokości kanałów, learning rate jako
  część genotypu). Jeśli przestrzeń jest czysto dyskretna — wspomnij RV-GOMEA jednym zdaniem jako kontekst
  rodziny, nie jako metodologiczny precedens.

**Podsumowanie relacji:** CS-GOMEA dowodzi wykonalności mechanizmu (surrogate + linkage-tree EA), SA-P3-GOMEA
dowodzi wykonalności z konkretnie P3-GOMEA na realnym problemie ML-owym (najbliższy precedens), RV-GOMEA
dowodzi dojrzałości/elastyczności rodziny, ale nie jest bezpośrednim precedensem, chyba że przestrzeń
przeszukiwania jest częściowo ciągła. Żadna z tych prac nie testuje P3/GOMEA w NAS — to wciąż pozostaje
Twoją realną luką, ale musi być zaprezentowana jako "przeniesienie znanej, sprawdzonej kombinacji do nowej
domeny", a nie jako "wymyślenie kombinacji od zera" — bo to drugie sformułowanie byłoby nieścisłe i łatwe
do podważenia.

## 8. Dwie różne role "sieci neuronowej" — dlaczego przeniesienie do NAS nie jest trywialne

Ważne doprecyzowanie do sekcji 7 (CS-GOMEA), bo łatwo o nieporozumienie: "sieć neuronowa" pojawia się tam
w **innej roli** niż w NAS, więc "CS-GOMEA już sprzęgło linkage-tree z siecią neuronową" nie oznacza
automatycznie, że problem P3Net jest już rozwiązany.

| | CS-GOMEA | NAS / P3Net |
|---|---|---|
| Co koduje genotyp | bit-string do funkcji syntetycznej | architektura sieci neuronowej |
| Co jest "drogie" | nic naprawdę — OneMax/Trap/NK-landscapes/HIFF liczą się natychmiast, drogość jest symulowana | realny trening sieci (godziny–dni GPU) |
| Rola sieci neuronowej | CNN jako **surrogate** (predyktor fitness) | architektura jako **obiekt optymalizowany**; osobny, mały model może pełnić rolę surrogate'u |
| Struktura zależności w genotypie | abstrakcyjna, zdefiniowana przez funkcję benchmarkową (np. bloki 4-bitowe w Trap4) | konkretna, architektoniczna (sąsiedztwo warstw, typ operacji vs. szerokość kanału) |

Sprawdzone dokładnie (WebSearch): benchmarki CS-GOMEA to OneMax, Tight/Loose Trap4, NK-landscapes, HIFF,
MaxCut — klasyczne syntetyczne problemy kombinatoryczne używane w badaniach nad GA, **nie architektury
sieci neuronowych**. CNN w CS-GOMEA nigdy nie ocenia architektury — ocenia bit-string.

**Wniosek:** CS-GOMEA dowodzi tylko, że "linkage-tree EA + NN-surrogate" **w ogóle da się sprząc i to
działa na jakimś problemie**. Nie dowodzi, że hipoteza przenosi się na NAS, bo (a) genotyp architektury ma
inną naturę zależności niż bit-string funkcji Trap, (b) koszt/rodzaj ewaluacji jest fundamentalnie inny
(trening sieci vs. natychmiastowe obliczenie funkcji). To właśnie ta różnica domeny jest tym, co P3Net
musi wykazać empirycznie, a nie zakładać z góry — i to jest właściwe sformułowanie kontrybucji: nie
"wymyślenie nowej kombinacji technik", tylko "sprawdzenie, czy znana kombinacja przenosi się na jakościowo
inną domenę o innej strukturze zależności i innym reżimie kosztów ewaluacji".

## Synteza — ryzyko pracy odtwórczej

Nie na poziomie głównej idei (P3 + surrogate w NAS to pusta nisza, potwierdzona przeglądem). Realne ryzyka są
gdzie indziej:

1. **Typ predyktora.** Zwykły regresor dokładności to już nie nowość (tak działa NSGANetV2 z 2020 i cała
   fala prac po nim). Trend 2023–2025 to ranking/dominance classifier (sekcja 2). Warto rozważyć wariant
   rankingowy przynajmniej jako ablację.
2. **Related Work musi jawnie odciąć się od CS-GOMEA/SA-P3-GOMEA** (sekcja 7) — inaczej wygląda to, jakby
   autor "odkrywał" ideę surrogate + linkage-learning, która już istnieje; kontrybucją jest przeniesienie
   jej do NAS, nie sam pomysł kombinacji.
3. **NSGA-Net vs NSGANetV2** — trzeba jasno rozróżnić: oryginalny NSGA-Net (2019, arXiv:1810.03522) NIE ma
   surrogate'u (ma za to sieć bayesowską do eksploatacji struktury), surrogate pojawia się dopiero
   w NSGANetV2 (ECCV 2020). Baseline eksperymentalny powinien być NSGANetV2 (ten sam surrogate co P3Net,
   zmienna = tylko backbone NSGA2→P3), NSGA-Net v1 jako tło historyczne.
4. Nie trzeba konkurować z zero-cost proxies / one-shot NAS na czasie GPU (sekcja 3) — to inny cel badawczy;
   P3Net to pytanie ablacyjne o mechanizm generowania kandydatów, nie wyścig o rekord efektywności SOTA.
5. **Najsłabsze ogniwa dowodowe tej notatki** (patrz bloki "Poziom dowodu"): trend LLM-driven NAS (sekcja 3,
   tylko 2 prace) i ogólna "aktywność" linkage-learning (sekcja 5, brak bibliometrii). Nie cytuj ich w
   artykule z taką samą pewnością jak ustaleń z przeglądu Özçelik/Efe czy bibliometrii GA.

## Kluczowe źródła do zacytowania w Related Work

- NSGA-Net (Lu et al., GECCO 2019) — arXiv:1810.03522
- NSGANetV2 (Lu et al., ECCV 2020) — https://arxiv.org/abs/2007.10396
- **Parameter-less Population Pyramid** (Goldman & Punch, GECCO 2014) — NIE MA na arXiv. DOI
  10.1145/2576768.2598350 (paywall ACM: https://dl.acm.org/doi/abs/10.1145/2576768.2598350). Darmowy PDF
  (mirror proceedings): http://www.cmap.polytechnique.fr/~nikolaus.hansen/proceedings/2014/GECCO/proceedings/p785.pdf
- **CS-GOMEA** — pełny tytuł: "Convolutional neural network surrogate-assisted GOMEA" (Dushatskiy, Mendrik,
  Alderliesten, Bosman, GECCO 2019). NIE MA na arXiv. DOI 10.1145/3321707.3321760 (paywall ACM). Spróbować:
  https://research.tudelft.nl/en/publications/convolutional-neural-network-surrogate-assisted-gomea/ (może
  mieć open-access kopię). Kod (nie tekst): https://github.com/ArkadiyD/CS-GOMEA
- **"SA-P3-GOMEA" to moja nieformalna etykieta, NIE prawdziwy tytuł.** Prawdziwy tytuł: "A Novel
  Surrogate-assisted Evolutionary Algorithm Applied to Partition-based Ensemble Learning" (Dushatskiy,
  Alderliesten, Bosman, GECCO 2021). Link: https://arxiv.org/abs/2104.08048
- SiamNAS (GECCO 2025) — https://arxiv.org/abs/2506.02623
- Pairwise Comparison Relation-assisted MO-NAS — https://arxiv.org/abs/2407.15600
- Meta-knowledge assisted ENAS (2025) — https://arxiv.org/abs/2504.21545
- Multi-Fidelity Continuous Encoding MO-NAS (2025) — https://arxiv.org/abs/2509.01943
- RV-GOMEA linkage learning (gray-box optimization, 2024) — https://arxiv.org/abs/2402.10757
- A Systematic Survey on LLMs for Evolutionary Optimization (2025) — https://arxiv.org/abs/2509.08269
- Özçelik, Efe — Evolutionary neural architecture search: a survey (Turkish J. Electr. Eng. Comput. Sci.,
  vol. 34, nr 4, 2026, s. 507–541) — **kluczowe źródło ilościowe dla sekcji 2, 4 i 6**.
  https://journals.tubitak.gov.tr/elektrik/vol34/iss4/2/
- Five Decades of Genetic Algorithms: A Systematic and Bibliometric Review 1975–2025 (Archives of
  Computational Methods in Engineering, Springer, 2026) — DOI 10.1007/s11831-025-10487-2 (prawdopodobnie
  paywall — sprawdzić dostęp przez uczelnię)
- **"Multi-Objective P3" to skrót, NIE prawdziwy tytuł.** Prawdziwy tytuł: "Multi-Objective Parameter-less
  Population Pyramid for Solving Industrial Process Planning Problems" (Przewoźniczek i in., 2020).
  Link: https://arxiv.org/abs/2009.08929
- White et al. — Neural Architecture Search: Insights from 1000 Papers — https://arxiv.org/abs/2301.08727
- RV-GOMEA (Bouter et al., real-valued gene-pool optimal mixing EA, GECCO 2017) — DOI 10.1145/3071178.3071272
  (paywall ACM, brak arXiv)
- A Joint Python/C++ Library for Efficient yet Accessible Black-Box and Gray-Box Optimization with GOMEA
  (2023) — https://arxiv.org/abs/2305.06246
- **"Tran, Truong, Vo, Luong — Accelerating GOMEA for NAS with Synaptic Flow"** (GECCO 2023 Companion,
  Lisbon) — **kluczowe: GOMEA już użyty w NAS, must-cite dla Related Work, patrz sekcja 6**. Publikacja
  Companion GECCO — sprawdzić czy jest w ACM DL (prawdopodobnie DOI w zbiorze GECCO'23 Companion
  proceedings), nie potwierdzono obecności na arXiv — do zweryfikowania bezpośrednio.
- Phan, Luong — Enhancing Multi-objective Evolutionary NAS with Surrogate Models and Potential
  Point-Guided Local Searches (Springer, 2021), DOI 10.1007/978-3-030-79457-6_39 (paywall Springer,
  brak arXiv)
- Mouret, Clune — Illuminating search spaces by mapping elites (MAP-Elites) — https://arxiv.org/abs/1504.04909
- Pierrot, Richard, Beguir, Cully — Multi-Objective Quality Diversity Optimization (MOME, GECCO 2022) —
  https://arxiv.org/abs/2202.03057
- Nasir, Earle, Cleghorn, James, Togelius — LLMatic: NAS via LLMs and Quality Diversity Optimization
  (GECCO 2024) — https://arxiv.org/abs/2306.01102

## 9. Szkic (draft) do Introduction i Related Work

Uwaga: `refs.bib` w repo ma obecnie tylko 2 wpisy (benchmarking w optymalizacji, COCO) — żadna z prac
poniżej nie jest jeszcze dodana. Przed przepisaniem tego do `.tex` trzeba uzupełnić `refs.bib`.

### Introduction — szkic linii argumentacji

1. NAS przeszukuje dyskretne przestrzenie architektur, gdzie pełna ewaluacja kandydata = trening sieci od
   zera — to dominujący koszt obliczeniowy (już macie, zostaje bez zmian).
2. NSGA-Net (2019) był pierwszym systematycznym zastosowaniem NSGA2 do NAS — ale **bez surrogate'u**:
   eksploatuje historię przeszukiwania przez sieć bayesowską, każdy kandydat i tak trenowany od zera.
3. NSGANetV2 (2020) dodaje surrogate (predyktor dokładności) + supersieć, ograniczając pełny trening do
   elity — to wzorzec, który (wg systematycznego przeglądu Özçelik/Efe, 164 prac ENAS 2020–2024) **nadal
   dominuje** w multi-objective ENAS: podejścia GA-based (NSGA-II/III) rządzą wyszukiwaniem frontu Pareto,
   a kategoria surrogate-assisted rośnie najmocniej właśnie w 2023–2024. To nie jest przestarzały wybór.
4. We wszystkich tych podejściach silnik generowania/selekcji kandydatów pozostaje ten sam: NSGA2
   (crowding distance, sortowanie niezdominowane). Osobna linia badań — algorytmy linkage-learning
   (GOMEA, P3) — jawnie modeluje zależności strukturalne między zmiennymi genotypu przez linkage-tree
   crossover, zamiast zakładać ich niezależność.
5. Ta rodzina algorytmów była już z powodzeniem łączona z uczonym surrogate'em **poza NAS** (CS-GOMEA na
   syntetycznych benchmarkach kombinatorycznych; SA-P3-GOMEA na realnym, kosztownym problemie doboru
   partycji w ensemble learning) oraz osobno zastosowana **w NAS z zero-cost proxy**, nie z uczonym
   surrogate'em (Tran et al. 2023: GOMEA + Synaptic Flow). Żadna praca nie łączy P3 konkretnie z uczonym
   surrogate'em w domenie NAS.
6. Pytanie centralne (dopracowana wersja): przy identycznym, surrogate-assisted schemacie ewaluacji (jak
   w NSGANetV2) i ustalonym budżecie pełnych treningów, czy generowanie kandydatów sterowane strukturą
   zależności (P3, linkage-tree crossover) daje lepsze wyniki niż selekcja oparta o crowding distance
   (NSGA2)?
7. Kontrybucja: metoda P3Net + kontrolowane porównanie z NSGANetV2 (ten sam surrogate, zmienna = tylko
   backbone), z NSGA-Net v1 (tło historyczne, brak surrogate'u) oraz — jeśli czas pozwoli — z GOMEA+SynFlow
   (Tran et al., inny mechanizm redukcji kosztu: zero-cost proxy zamiast uczonego surrogate'u).

### Related Work — szkic struktury (podrozdziały)

1. **Evolutionary NAS bez surrogate'u** — NSGA-Net (2019): NSGA2 + sieć bayesowska do eksploatacji
   struktury, pełny trening każdego kandydata.
2. **Surrogate-assisted evolutionary NAS** — NSGANetV2 (2020) jako punkt odniesienia; szerszy kontekst z
   przeglądu Özçelik/Efe (dominacja GA-based MO, wzrost surrogate-assisted 2023–2024); nowsze kierunki:
   predyktor jako ranking/dominance classifier zamiast regresora (SiamNAS, Pairwise Comparison MO-NAS),
   transfer/meta-wiedza między zadaniami (meta-knowledge ENAS, transfer stacking+KD). Zaznaczyć: we
   wszystkich tych pracach backbone selekcji to wciąż NSGA2/NSGA3.
3. **Linkage-learning evolutionary algorithms** — krótko wytłumaczyć GOMEA/P3 (FOS, linkage-tree,
   optimal mixing vs. linkage-tree crossover), odrębna linia badań (Bosman/CWI/TU Delft), realne
   zastosowania poza ML (RV-MO-GOMEA w brachyterapii, Silver Humies Award — dowód dojrzałości metody).
4. **Surrogate-assisted linkage-learning EA (poza NAS)** — CS-GOMEA (CNN surrogate + GOMEA na OneMax/
   Trap/NK-landscapes/HIFF — **zaznaczyć wprost, że to syntetyczne problemy kombinatoryczne, nie
   architektury sieci**, żeby uniknąć wrażenia, że problem jest już rozwiązany, patrz sekcja 8 notatki);
   SA-P3-GOMEA (P3-GOMEA + surrogate na realnym problemie ensemble learning — najbliższy precedens
   metodologiczny, wymaga jawnego rozróżnienia od P3Net).
5. **Linkage-learning EA w NAS** — Tran et al. (2023): GOMEA + Synaptic Flow (zero-cost proxy) dla NAS.
   Jawnie nazwać różnicę: zero-cost proxy (bez uczenia, bez danych z wcześniejszych ewaluacji) vs. uczony
   surrogate (trenowany na wynikach częściowych pełnych treningów) — to różne mechanizmy redukcji kosztu.
6. **Luka i pozycjonowanie P3Net** — przecięcie "P3 (nie GOMEA) + uczony surrogate (nie zero-cost proxy) +
   domena NAS (nie syntetyczne benchmarki/ensemble learning)" nie zostało dotąd zbadane. Sformułować to
   jako przeniesienie sprawdzonej kombinacji technik do nowej, jakościowo innej domeny (inna struktura
   zależności w genotypie, inny reżim kosztu ewaluacji) — nie jako wynalezienie kombinacji od zera.

### Rzeczy do zrobienia przed napisaniem finalnej wersji

- Sprawdzić bezpośrednio (DBLP/Google Scholar), czy istnieje praca "P3 + NAS" lub "P3 + uczony surrogate"
  — dotychczasowe przeszukania (WebSearch) nie są wyczerpujące (patrz sekcja 6, akapit o obaleniu dowodu
  negatywnego).
- Przejrzeć całościowo dorobek grupy Ngoc Hoang Luong (VNU-HCM) pod kątem innych, bliżej niesprawdzonych
  prac na styku GOMEA/surrogate/NAS.
- Zdecydować, czy P3Net używa regresora dokładności czy rankingu/klasyfikatora dominacji (trend 2023–2025,
  sekcja 2) — i jeśli regresor, uzasadnić ten wybór na tle trendu.
- Zdecydować, czy przestrzeń przeszukiwania P3Net ma komponenty ciągłe (wpływa na to, czy RV-GOMEA jest
  bezpośrednim precedensem czy tylko kontekstem rodziny — sekcja 7).
- Dodać wszystkie wymienione prace do `refs.bib`.

## 10. Dodatek: Quality-Diversity jako alternatywny kierunek (dodane po dyskusji o pivocie)

Podczas rozmowy o ewentualnej zmianie kierunku (zamiana Pareto na QD/MAP-Elites, zachowanie osi
"mechanizm generowania/selekcji kandydatów") sprawdzone zostały dodatkowe źródła, nieobecne wcześniej
w tej notatce:

- **Mouret, Clune — "Illuminating search spaces by mapping elites"** (arXiv:1504.04909, 2015) —
  oryginalna praca definiująca MAP-Elites. Punkt wyjścia, jeśli P3Net miałby pójść w stronę QD.
- **Pierrot, Richard, Beguir, Cully — "Multi-Objective Quality Diversity Optimization" (MOME)**
  (GECCO 2022, arXiv:2202.03057) — wariant QD zachowujący lokalny front Pareto w obrębie każdej niszy;
  najbardziej pasujący do obecnej formalizacji P3Net z dwoma celami $(f_1, f_2)$, gdyby dodać osie
  niszowania oparte na strukturze genotypu.
- **Nasir, Earle, Cleghorn, James, Togelius — "LLMatic: NAS via LLMs and Quality Diversity
  Optimization"** (GECCO 2024, arXiv:2306.01102) — jedyna znaleziona praca łącząca QD z NAS wprost;
  używa LLM jako operatora wariacji, **nie** operatora świadomego zależności strukturalnych (jak
  linkage-tree) — to zostawia otwartą przestrzeń dla P3+QD.
- **Nasir i in. (novelty-driven ENAS, arXiv:2204.00188) oraz MTF-PDNS (arXiv:2407.20656)** — rodzina
  "dodaj różnorodność jako kryterium w ramach Pareto" — kontrastowa alternatywa dla czystego QD,
  omówiona w rozmowie: różnica mechaniczna to "wspólna, sporna pula" (Pareto+novelty) vs. "zarezerwowane
  nisze" (QD) — to rozróżnienie warto umieścić w Related Work, jeśli P3Net pójdzie w stronę QD.

**Status decyzji:** to wciąż faza eksploracji (brainstorming), nie podjęto ostatecznej decyzji, czy
P3Net zmienia kierunek na QD, zostaje przy Pareto, czy idzie w stronę hybrydy (SMS-EMOA/hypervolume,
opcja z rozmowy). Nic z tego nie zostało jeszcze spisane jako formalny design/spec.

## 11. KRYTYCZNE: przegląd dorobku promotora (Przewoźniczek) i sprawdzenie nazwy "P3Net"

### 11.1 Promotor

Autor potwierdził: **Michal Witold Przewoźniczek jest promotorem tej pracy** (patrz memory
`promoter_przewozniczek`). To wyjaśnia genezę tematu — promotor sam pracuje w linii linkage-learning/P3.

### 11.2 Pełny przegląd DBLP promotora (https://dblp.org/pid/17/2452.html)

Publikacje 2025–2026 (najnowsze), sprawdzone bezpośrednio przez WebFetch:

- **"Limited Perfect Monotonical Surrogates Constructed Using Low-Cost Recursive Linkage Discovery with
  Guaranteed Output"** — Przewoźniczek, Chicano, Komarnicki, Tinós, **GECCO 2026** (13 lipca 2026!),
  s. 645–653, DOI [10.1145/3795095.3805171](https://doi.org/10.1145/3795095.3805171),
  arXiv: [2604.11524](https://arxiv.org/abs/2604.11524).
  **⚠️ TO JEST NAJWAŻNIEJSZE ZNALEZISKO CAŁEGO PRZEGLĄDU.** Metoda "LyMPuS" (Limited Monotonical Perfect
  Surrogate) łączy **surrogate + linkage discovery** w tej samej rodzinie algorytmów co P3/GOMEA —
  dokładnie ten sam rdzeń pomysłu, na którym opiera się P3Net, tylko opublikowany przez samego promotora
  dosłownie kilka dni przed tą rozmową.

  **AKTUALIZACJA po przeczytaniu pełnego tekstu PDF (nie tylko abstraktu):**
  - eLyMPuS (empiryczna wersja LyMPuS dla black-box) porównuje dwa rozwiązania różniące się jedną zmienną
    bez pełnej ewaluacji, wspiera tanie wykrywanie brakującego linkage z gwarancją znalezienia zależności
    w ≤ $2\lceil\log_2(n)\rceil$ krokach; bezparametrowy, trenowany w locie.
  - **eLyMPuS został wprost zintegrowany z P3** (wariant "P3-FIHCwLL" → "P3-eLyMPuS") **i przetestowany
    eksperymentalnie** — w Tabeli 5 artykułu P3-eLyMPuS jest **drugim najskuteczniejszym** z sześciu
    porównywanych optymalizatorów (po autorskim OLyMPuS, przed P3-FIHCwLL). To znaczy: **kombinacja
    "P3 + surrogate" nie jest już tylko teoretycznie możliwa — jest zbudowana, zaimplementowana i
    zbenchmarkowana przez promotora, z publicznym kodem: https://github.com/przewooz/OLyMPuS**
  - Benchmarki testowe: bimodal-10 (i warianty z nakładaniem/szumem), funkcje deceptive (k=5), NK-fitness
    landscapes, Ising Spin Glasses, Max3Sat, mk-landscapes — **wyłącznie klasyczne, syntetyczne problemy
    kombinatoryczne/pseudo-boolowskie. Zero wzmianki o NAS, sieciach neuronowych czy uczeniu maszynowym
    jako domenie zastosowania.** Domena NAS pozostaje potwierdzone otwarta.
  - W bibliografii artykułu (pozycja [5]) jest jeszcze jedna praca Dushatskiy/Alderliesten/Bosman, którą
    warto dodać do listy źródeł: **"A Novel Approach to Designing Surrogate-assisted Genetic Algorithms
    by Combining Efficient Learning of Walsh Coefficients and Dependencies"**, ACM Trans. Evol. Learn.
    Optim. 1(2), art. 5, 2021, DOI 10.1145/3453141 — prawdopodobnie rozszerzona, czasopismowa wersja tej
    samej linii badań co SA-P3-GOMEA (ten sam zespół, ta sama tematyka: surrogate + linkage/Walsh
    coefficients), do zweryfikowania czy to inny artykuł czy inna wersja tego samego.
  - **Podziękowania w artykule: "We would like to thank Peter Bosman for his valuable remarks."** —
    potwierdza bezpośredni kontakt naukowy między linią Przewoźniczka a linią Bosmana (CWI/TU Delft,
    autorzy CS-GOMEA/SA-P3-GOMEA) — to nie są niezależne, nieświadome siebie grupy badawcze.

  **Rewizja wniosku:** luka "P3 + surrogate" (ogólnie, poza NAS) jest teraz **jednoznacznie zamknięta,
  nie tylko prawdopodobnie zamknięta** — P3-eLyMPuS istnieje, działa, jest opublikowany i ma kod na
  GitHubie. Jedyna wciąż otwarta (na ile ustalono) oś to zastosowanie tego (lub analogicznego) surrogate'u
  **w domenie NAS konkretnie** — architektura sieci jako genotyp, trening sieci jako kosztowna ewaluacja.
  To jeszcze mocniej uzasadnia rozmowę z promotorem: pytanie nie brzmi już "czy zrobić P3+surrogate", bo
  to już istnieje — brzmi "czy przenieść (i jak) istniejący, gotowy mechanizm promotora na NAS", co jest
  bardzo różnym punktem wyjścia niż budowanie surrogate'u od zera w stylu NSGANetV2.
- **"The hop-like problem nature — unveiling and modelling new features of real-world problems"**
  (Leading Blocks Problem) — Przewoźniczek, Frej, Komarnicki, **GECCO 2026**, s. 636–644,
  DOI [10.1145/3795095.3805173](https://doi.org/10.1145/3795095.3805173) — to ta sama praca omówiona
  wcześniej (wcześniej widziana jako arXiv:2406.01215 z 2024, teraz formalnie opublikowana GECCO 2026).
- "Pareto Front Improvements Phase using linkage learning and mating restrictions..." — Expert Systems
  with Applications, vol. 273 (2025) — multi-objective, linkage learning, ale przemysłowe process
  planning, nie ML/NAS.
- "From Direct to Directional Variable Dependencies — Nonsymmetrical Dependencies Discovery..." — IEEE
  TEVC, vol. 29(2) (2025) — teoria linkage discovery, nie NAS.
- "Obtaining Partition Crossover masks using Statistical Linkage Learning..." — GECCO 2026.
- Prace FOGA 2025 o linkage discovery i optymalizacji (kilka pozycji, nie zweryfikowano szczegółowo).

**Wniosek ogólny:** żadna ze sprawdzonych prac promotora nie dotyczy NAS ani sieci neuronowych jako
obiektu przeszukiwania — cały jego dorobek to teoria linkage discovery i zastosowania kombinatoryczne
(Max3Sat, planowanie przemysłowe). **Ale LyMPuS (GECCO 2026) to prawdopodobnie dokładnie ten typ
surrogate'u, którego P3Net potrzebuje** — zbudowany od zera przez samego promotora, kilka dni temu.

### 11.3 Rekomendacja — pilne

**Skontaktować się z promotorem przed dalszą pracą nad kierunkiem P3Net.** Możliwe scenariusze:
1. Promotor chce, żeby P3Net był właśnie rozszerzeniem LyMPuS na domenę NAS — w takim razie cały ten
   przegląd literaturowy powinien się przesunąć w stronę "LyMPuS + NAS", nie "P3 + własny, nowy surrogate
   w stylu NSGANetV2".
2. Promotor już planuje/realizuje takie rozszerzenie sam lub z kimś innym — trzeba to wiedzieć zanim
   zainwestuje się dalszy czas.
3. To zbieg okoliczności i promotor będzie zadowolony z niezależnego podejścia (NSGANetV2-style surrogate
   zamiast LyMPuS) — ale to też trzeba usłyszeć wprost, nie zakładać.

### 11.4 Sprawdzenie nazwy "P3Net"

Nazwa **nie jest unikalna w literaturze ML ogólnie**, ale nie ma kolizji w domenie NAS/EC:
- "P3Net (PointNet-based Path Planning Networks)" — planowanie ścieżki robota z chmur punktów,
  zupełnie inna dziedzina.
- "P3Net: Progressive and Periodic Perturbation for Semi-Supervised Medical Image Segmentation"
  (arXiv:2505.15861, 2025) — segmentacja obrazów medycznych, też niepowiązane.

Żadna z nich nie dotyczy NAS ani algorytmów ewolucyjnych — nazwa nie koliduje merytorycznie, ale nie
jest też w 100% unikalna przy wyszukiwaniu ("P3Net" wyciągnie też te dwie niepowiązane prace). Do
rozważenia: czy to problem (zależy od preferencji — część osób w ogóle by się tym nie przejmowała).

## 12. Weryfikacja pełnotekstowa (12 z 13 pobranych PDF-ów przeczytanych w całości)

Wszystko poniżej pochodzi z bezpośredniego przeczytania oryginalnych PDF-ów w `notes/articles/`, nie
z fragmentów wyszukiwarki — najsilniejszy dostępny poziom dowodu w tej notatce. Nieprzeczytany: *Five
Decades of Genetic Algorithms* (plik >20MB, przekracza limit narzędzia) — fakty z sekcji 1 o tej pracy
pozostają na poziomie streszczenia z WebSearch, niezweryfikowane pełnotekstowo.

### 12.1 NSGA-Net (2019) — potwierdzenia i nowe fakty

- Potwierdzone: brak surrogate'u, selekcja NSGA-II + sieć bayesowska (BOA-inspired) do eksploatacji
  historii przeszukiwania. Pełny trening każdego kandydata (25 epok, ~9 min/sieć na 1080Ti, populacja 40,
  łącznie ~1200 architektur, ~8 GPU-dni).
- **Nowy, mocny argument dla Introduction:** artykuł explicite dokumentuje silną redundancję mapowania
  genotyp→fenotyp — **60–80% duplikatów genomów** w miarę wzrostu liczby węzłów (ich Fig. 17, własny
  mechanizm detekcji duplikatów). To bezpośrednie, pierwotne źródło na poparcie argumentu o "utracie
  różnorodności strukturalnej" z naszej wcześniejszej dyskusji o QD — nie trzeba już tego wyprowadzać
  teoretycznie, autorzy NSGA-Net sami to zmierzyli i opisali jako problem.
- Ablacja crossover vs. mutation-only: crossover **jest korzystny** (kontrargument wobec części
  literatury NAS unikającej krzyżowania).
- **Ważne dla ewentualnego pivotu do QD/hypervolume:** Appendix C artykułu wprost testuje selekcję po
  crowding distance (CD) vs. wkład w hypervolume (HV-contribution) i **nie znajduje jednoznacznej
  przewagi HV-contribution** — cytując Ishibuchi i in. (2018), zaznaczają że selekcja HV-optymalna to
  problem NP-trudny i lokalna optymalizacja HV-contribution nie gwarantuje lepszego HV populacji.
  **To studzi entuzjazm dla "Opcji 1" (SMS-EMOA/hypervolume zamiast NSGA2) z wcześniejszej burzy mózgów
  — trzeba to zacytować jako zastrzeżenie, nie przedstawiać zamiany na selekcję wskaźnikową jako
  oczywisty zysk.**
- Nowe źródło do sprawdzenia: **PPP-Net** (Dong i in. 2018) — cytowany w NSGA-Net jako wcześniejsza praca
  z modelem predykcyjnym w multi-objective progressive NAS, potencjalnie wcześniejszy niż NSGANetV2
  precedens "predyktor + multi-objective NAS" (inny silnik niż NSGA2 — progressive search).

### 12.2 NSGANetV2 (2020) — istotne korekty

- **Korekta ważna dla Problem Formulation:** "pełna ewaluacja" w NSGANetV2 **nie jest treningiem od zera**
  — to fine-tuning wag odziedziczonych z supersieci (weight-sharing/OFA-style). Obecny
  `problem_formulation/main.tex` zakłada "$f_1(x)$ requires training $D(x)$ from scratch" — to dokładnie
  opisuje NSGA-Net v1, ale **nie** NSGANetV2. Jeśli NSGANetV2 ma być głównym baseline'em, trzeba albo
  doprecyzować tę różnicę explicite, albo świadomie zdecydować, że P3Net celowo trenuje od zera (co byłoby
  kolejną, dodatkową różnicą względem NSGANetV2, nie tylko backbone NSGA2→P3).
  Dwa poziomy surrogate'u: górny (architektura → dokładność, wybór spośród MLP/CART/RBF/GP przez
  "Adaptive Switching") + dolny (wagi, przez fine-tuning z supersieci).
- **Korekta:** V1→V2 to nie tylko "dodanie surrogate'u" — **zmieniła się też cała przestrzeń
  przeszukiwania** (v1: DAG/phase-encoding własnych komórek; v2: MobileNetV2/EfficientNet-style
  głębokość/szerokość/kernel/rozdzielczość, w stylu Once-For-All). Dwie zmienne zmieniły się naraz.
- Surrogate "online" (iteracyjnie dostrajany blisko aktualnego frontu) kontra "offline" (trenowany raz na
  szeroko próbkowanych architekturach, jak OnceForAll/ChamNet/PNAS) — NSGANetV2 idzie w stronę online,
  osiągając korelację rangową ~0.9 (vs. 0.476 dla PNAS). Wasz plan (inkrementalna aktualizacja
  $\mathcal{D}_t$) już jest zgodny z tym "online" podejściem — dobrze.
- Liczby do cytowania: ~350 w pełni ewaluowanych architektur (vs. 16 000 dla OnceForAll, ~1160 dla PNAS).

### 12.3 P3, oryginał (Goldman & Punch, 2014) — potwierdzenia i nowy cytat

- Potwierdzony mechanizm: FIHC (O(N) per ewaluację), linkage tree z entropii (styl LTGA), koszt
  budowy/dodania do piramidy O(N²) per dodanie (amortyzowane O(N) per ewaluację).
- Porównanie **P3 vs. LTGA** (nie vs. GOMEA — GOMEA to późniejszy, osobny wariant tej samej linii, nie
  omówiony w tej pracy z 2014): przyspieszenia 1.1×–942× w zależności od problemu (najmocniej: MAX-SAT
  942×, Ising Spin Glass 20.4×, NK-landscapes 4.4×), mimo że LTGA miało dostrojony rozmiar populacji
  (nieuczciwa przewaga), a P3 zero parametrów.
- **Znakomity, bezpośredni cytat do Introduction** — sekcja 2.5 artykułu ("Contrasted with the
  Generational Model"): autorzy explicite argumentują, że model generacyjny (jak NSGA2) cierpi na wyścig
  między malejącą różnorodnością a rosnącym fitness, prowadzący do przedwczesnej zbieżności, podczas gdy
  P3 "nie wyrzuca wcześniej zoptymalizowanych rozwiązań podczas dodawania różnorodności" — to pierwotne,
  autorskie uzasadnienie mechanizmu P3 dokładnie pokrywające się z naszą dyskusją o utracie różnorodności
  strukturalnej i QD. Warto zacytować wprost.
- Brak jakiejkolwiek wzmianki o NAS/surrogate'ach (2014, przed erą deep-learning NAS) — oczywiste, ale
  potwierdzone.

### 12.4 CS-GOMEA (2019) — potwierdzenia i nowy fakt

- Potwierdzone benchmarki: Onemax, Trap4 (Tight/Loose), HIFF, NK-landscapes (NK-S1) — wyłącznie
  syntetyczne, bez NAS.
- CNN trenowany na **różnicach fitness między parami** rozwiązań (nie wartościach bezwzględnych) — trik
  mnożący efektywny rozmiar danych treningowych (n rozwiązań → n² par).
- **Nowy fakt, dobry hak do Related Work:** autorzy sami piszą w dyskusji, że **nie wykorzystują
  informacji z linkage tree do budowy struktury surrogate'u** — traktują to jako "ważne pytanie badawcze
  na przyszłość" ("taking into account the subsets of dependent variables... instead of moving filters
  along input for all variables"). To wprost nazwana przez autorów luka, którą można zaadresować.
  Wspominają architekturę NAS explicite jako motywację we wstępie, ale nie testują na niej.

### 12.5 SA-P3-GOMEA / Partition-based Ensemble Learning (2021) — kluczowe korekty

- **Potwierdzony bezpośredni cytat autorów o nowości:** *"To the best of our knowledge, this is the
  first time a surrogate model is integrated into a P3 scheme."* — to najsilniejszy dostępny,
  pierwotny dowód na to, co dokładnie ta praca robi (i czego nie robi — nie NAS).
  **Nowa nazwa metody z artykułu: "eP3"** (nie ma w nim samej frazy "SA-P3-GOMEA" — to etykieta z
  wcześniejszych wyszukiwań; do poprawienia w cytowaniach na rzecz nazwy autorskiej, jeśli występuje
  w tekście, warto zweryfikować dokładne brzmienie przy pisaniu bibliografii).
- **Ważna korekta:** testowali 4 typy surrogate'u (MLP, Gradient Boosting, SVR, RF) — **SVR wypadł
  najlepiej, nie sieć neuronowa (MLP)**. To istotne dla P3Net: najbliższy precedens P3+surrogate **nie
  potwierdza**, że sieć neuronowa jest najlepszym wyborem surrogate'u w tej rodzinie algorytmów — trzeba
  to świadomie zaadresować/uzasadnić (np. że w NAS predyktory NN/GNN mają inne, lepiej udokumentowane
  wsparcie niż w generycznej optymalizacji kombinatorycznej).
- **Ważna korekta strukturalna:** wariant "P3-GOMEA" użyty w tej pracy **usuwa komponent hill-climbingu
  (FIHC)** z oryginalnego P3 — bo w reżimie ograniczonego budżetu ta faza zjadała budżet bez wyraźnej
  korzyści. To znaczy, że najbliższy precedens używa **P3 zmodyfikowanego**, nie P3 w pełnej, oryginalnej
  postaci — jeśli P3Net używa pełnego P3 z hill-climbingiem, to już jest różnica warta odnotowania.
  Nowy wniosek do rozważenia: warto sprawdzić empirycznie, czy FIHC ma sens w reżimie kosztowym NAS.
- Nowe źródło do sprawdzenia: cytują **"Den Ottelander, Dushatskiy, Virgolin, Bosman — Local Search is a
  Remarkably Strong Baseline for Neural Architecture Search"** (EMO 2021) — ten sam zespół CWI **ma
  osobną, wcześniejszą pracę bezpośrednio o NAS** (przez local search, nie P3/GOMEA+surrogate). To
  potwierdzone niezależnie także w White i in. "Insights from 1000 Papers" (sekcja 12.7) jako uznany,
  cytowany wynik o mocnym baseline'ie local-search dla NAS. Warto ją zdobyć i przeczytać — to najbliższy
  namacalny ślad tego zespołu w samym NAS.

### 12.6 Evolutionary NAS survey (Liu, Sun, Xue, Zhang, Yen, Tan — IEEE TNNLS 2022/2023, arXiv:2008.10937)

**Korekta nazewnictwa:** plik w folderze `NAS/MO-NAS` to **nie** jest przegląd Özçelik/Efe (2026) cytowany
wcześniej w tej notatce — to inny, wcześniejszy, również bardzo obszerny przegląd (>200 prac do 2020 r.).
Oba przeglądy są teraz potwierdzone i się uzupełniają (różne okresy: ten do 2020, Özçelik/Efe 2020–2024).

- Potwierdza dominację GA jako podtypu EA w ENAS (Table III) i NSGA-II/MOEA-D/NSGA-III jako **jedyne**
  metody w kategorii multi-objective w ich taksonomii.
- Katalog technik przyspieszania ewaluacji: dziedziczenie wag, early stopping, redukcja zbioru
  treningowego, redukcja populacji, pamięć populacji, one-shot/supersieci, sprzęt, **surrogate/predyktory
  wydajności** — surrogate to jedna z wielu kategorii, nie jedyny nurt.
- **Ważne, cytowalne ostrzeżenie metodologiczne (sekcja Challenges/Effectiveness):** wielokrotnie
  wykazano, że **random search dorównuje lub bije wiele metod EC-NAS** (Yu i in. "Evaluating the Search
  Phase of NAS", Wistuba i in., Liashchynskyi i in.). To wzmacnia zasadność Waszego już zaplanowanego
  baseline'u random search + TPE (macie to już w `results/main.tex`) — dobrze, że jest, warto to jawnie
  uzasadnić w Related Work jako odpowiedź na tę krytykę, a nie zostawiać czytelnikowi do domyślenia.
- **Trzecie, niezależne potwierdzenie nieobecności GOMEA/P3/linkage-tree** w katalogowanej literaturze
  ENAS (obok Özçelik/Efe 2026 i White i in. 1000 Papers) — trzy niezależne, obszerne przeglądy z różnych
  okresów (do 2020, 2020–2024, >1000 prac od 2020) **żadne nie wymienia linkage-learning EA jako
  kategorii**. To najsilniejszy dostępny w tej notatce dowód negatywny na lukę.

### 12.7 NAS: Insights from 1000 Papers (White i in., 2023, arXiv:2301.08727)

- Potwierdza wielokrotnie: NSGA-II/MOEA/D jako standardowy wybór multi-objective NAS; zero-cost proxies
  (SynFlow jako "best-performing" wśród 5 testowanych w Abdelfattah i in. 2021) i ich udokumentowaną
  zawodność ("may be unreliable, especially on larger search spaces", bias w stronę większych/szerszych
  modeli); proste metryki (liczba parametrów, FLOPs) konkurencyjne wobec wyrafinowanych proxy.
  Potwierdza local search jako uznany, mocny baseline NAS (cytuje wprost Ottelander/Dushatskiy/Bosman —
  patrz 12.5) na małych i dużych przestrzeniach przeszukiwania.
- Explicite best practice: porównanie z random search jest wymagane w dobrej metodologii NAS — kolejne
  potwierdzenie zasadności istniejącego planu baseline'ów.
- **Czwarte niezależne potwierdzenie nieobecności GOMEA/P3/linkage-tree** w całym, bardzo szerokim
  katalogu >1000 prac NAS.

### 12.8 Nowe znaleziska spoza pierwotnej listy

- **MoSegNAS** (Lu, Cheng, Huang i in., 2022, arXiv:2208.06820) — **ten sam Zhichao Lu co NSGA-Net/
  NSGANetV2**, rozszerza podejście NSGANetV2 (surrogate + supersieć) na segmentację semantyczną
  w czasie rzeczywistym. Wprowadza **RankNet** — surrogate MLP z funkcją straty opartą na rankingu, nie
  MSE — to kolejne, tym razem od samych autorów NSGANetV2, potwierdzenie trendu "predyktor jako ranker,
  nie regresor" z sekcji 2. Warto zacytować jako dowód, że nawet twórcy NSGANetV2 poszli w tym kierunku
  w kolejnej pracy.
- **CoLLM-NAS** (Li, Lin, Wang, 2026, arXiv:2509.26037) — potwierdza, że LLM-driven NAS to **szerszy
  klaster prac niż wcześniej sądzono** (cytuje m.in. GENIUS, EvoPrompting, LLMatic, RZ-NAS, LM-Searcher,
  NADER jako odrębne metody LLM+NAS) — **rewizja w górę** wcześniejszej oceny "tylko 2 prace, słaby
  dowód trendu" z sekcji 3. Explicite krytykuje klasyczne operatory EA (mutacja/crossover) jako
  "inherently local and undirected" — dobry kontrapunkt do podkreślenia w Introduction: P3 (świadomie
  modelujący zależności) to inna odpowiedź na tę samą krytykę niż LLM-guidance.
- **LLM-Guided NAS for Robust Co-Design of Physical Neural Networks** — niszowe zastosowanie
  (fizyczne/optyczne sieci, projektowanie pod niepewność produkcyjną), potwierdza rozprzestrzenianie się
  LLM-NAS na wyspecjalizowane dziedziny sprzętowe. Drugorzędne dla Related Work.
- **Systematic Survey on LLMs for Evolutionary Optimization** (Zhang i in., arXiv:2509.08269) —
  potwierdzona struktura (3 paradygmaty roli LLM), NAS jako jedna z omawianych domen zastosowań.

## 13. KRYTYCZNE: praca magisterska Niny Bartnik — bezpośredni, wewnątrz-zespołowy precedens

### 13.1 Co to jest

**Bartnik, Nina — "Evolutionary optimization of deep neural networks"**, praca magisterska, Politechnika
Wrocławska, Wydział Informatyki i Telekomunikacji, 2026. **Promotor: Michał Przewoźniczek** — ten sam
promotor co u autora tej notatki. Pełny tekst przeczytany (89 stron + appendix).

Streszczenie mechanizmu: adaptuje **SA-P3-GOMEA** (Dushatskiy, Alderliesten, Bosman, 2021 — dokładnie ta
sama praca, którą P3Net miał rozszerzyć na NAS) z problemu jednokryterialnego (partycjonowanie danych do
ensemble learning) na **multi-objective NAS**. Przestrzeń: NAS-Bench-201, genotyp = 6 zmiennych
dyskretnych × 5 operacji = 15625 architektur, dokładność brana z lookupu benchmarku (nie trenowana od
zera — benchmark już zawiera wyniki treningu). Dwa cele: dokładność CIFAR-10 oraz **zmierzona energia
GPU** (nie FLOPs — explicite odrzucone po pilotażu: FLOPs koreluje z dokładnością ρ=0.749, zmierzona
energia tylko ρ=0.492, więc FLOPs nie daje realnego kompromisu).

Cztery warianty: MO-DSA-P3-GOMEA (deterministyczny surrogate), to samo z dynamicznym doborem surrogate'u,
MO-PSA-P3-GOMEA (surrogate probabilistyczny, zwraca niepewność), to samo z dynamicznym doborem.
Surrogate: **regresor bezwzględny** przewidujący parę (dokładność, energia) z całego zakodowanego
genotypu — warianty: SVR/MLP/RF/GBoost (deterministyczne) lub RF/GBoost/MLP/Gaussian Process
(probabilistyczne, z estymacją niepewności $\sigma$). **To nie jest surrogate linkage-aware** — nie
wykorzystuje struktury drzewa linkage do samej konstrukcji predykcji, tylko standardowy regresor na
płaskim wektorze genotypu (mechanicznie bliżej NSGANetV2 niż eLyMPuS).

Porównanie: **MO-LS (local search) i MO-P3-GOMEA bez surrogate'u** — **NSGA2/NSGANetV2 nigdzie się nie
pojawia jako baseline**. Metryki: hypervolume, IGD+. Wynik główny: na "training energy" najlepsze warianty
(probabilistyczne, z dynamicznym doborem) osiągają ~354 HV wobec ~294 (MO-LS) i ~280 (MO-P3-GOMEA) —
istotna poprawa. Na "inference energy" różnice są małe — surrogate ledwie bije MO-LS (140.23), bo problem
jest "łatwy" (autorka to explicite nazywa).

Jej własne sformułowanie luki (Introduction): *"None of the surveyed works combines a surrogate, the
parameterless P3 variant, and measure inference and training energy as a second objective. The contribution
of this work is the combination of mentioned methods."* — strukturalnie niemal identyczne z Waszym zdaniem
o luce w `related_work.tex`.

### 13.2 Precyzyjne porównanie z P3Net

| | Bartnik (2026) | P3Net (ustalona wersja) |
|---|---|---|
| Silnik ewolucyjny | P3-GOMEA (GOMEA, nie P3 sensu stricto Goldman/Punch — choć nazwa "P3" pojawia się w akronimie, mechanizm to warianty rodziny GOMEA opisane w jej rozdziale 4.3.2) | P3 (Goldman & Punch) |
| Surrogate | bezwzględny regresor na płaskim genotypie | relatywny, linkage-aware, $\hat\delta_F$ (styl eLyMPuS) |
| Baseline porównawczy | MO-LS, MO-P3-GOMEA bez surrogate'u | NSGANetV2 (NSGA2 + surrogate) |
| Pytanie badawcze | czy surrogate (i jego rozszerzenia probabilistyczne/dynamiczne) przyspiesza P3-GOMEA-family | czy modelowanie zależności strukturalnych (P3) generuje lepszych kandydatów niż crowding distance (NSGA2) |
| Przestrzeń przeszukiwania | zamknięty benchmark NAS-Bench-201, dokładność z lookupu | otwarta, pełny trening od zera (jak założono w `problem_formulation.tex`) |
| Drugi cel | zmierzona energia GPU | analityczny koszt (FLOPs/params) |
| Rola drzewa linkage | tylko w operatorze wariacji (jak w standardowym P3-GOMEA), nie w surrogatcie | w operatorze wariacji **i** w surrogatcie |

### 13.3 Co z tego wynika

To bezpośrednio **unieważnia w obecnej formie** zdanie o luce: *"P3 has not previously been combined with
a surrogate in NAS"* — Bartnik to zrobiła, pod tym samym promotorem, w tym samym roku. Nie da się tego
dłużej sformułować tak ogólnie.

Realny, wciąż broniący się margines: (a) jej "P3" to praktycznie GOMEA-family z surrogate'em
bezwzględnym, nie P3 sensu stricto z surrogate'em linkage-aware; (b) nie porównuje się z NSGA2/NSGANetV2
w ogóle, więc pytanie "P3 vs NSGA2 jako silnik" pozostaje przez nią niezbadane; (c) jej przestrzeń to
zamknięty benchmark z lookupem, nie otwarte, kosztowne NAS z treningiem od zera. Ale to cienki margines —
tytuł, promotor, algorytm bazowy (SA-P3-GOMEA) i domena (NAS) są identyczne.

**To wymaga rozmowy z promotorem przed dalszym pisaniem — pilniej niż cokolwiek innego w tej notatce.**
Możliwe scenariusze: prace zaplanowane jako komplementarne (ona: czy surrogate w ogóle pomaga + jak go
ulepszyć; Wy: czy P3 bije NSGA2 jako silnik, z lepszym surrogatem); przypadkowe nakładanie się, które
trzeba rozdzielić; albo promotor uzna, że trzeba przeformułować kierunek P3Net jeszcze mocniej w stronę
tego, czego Bartnik nie zrobiła (linkage-aware surrogate, porównanie z NSGA2, otwarta przestrzeń z pełnym
treningiem).

### 13.4 Do zrobienia od razu

- Poprawić zdanie o luce w `related_work.tex` — nie może już brzmieć jak twierdzenie o nieistnieniu
  kombinacji P3+surrogate+NAS w ogóle.
- Dodać cytowanie pracy Bartnik (klucz `bartnik2026evolutionary`, już w `refs.bib`) i jawnie odróżnić
  P3Net w tekście.
- Sprawdzić, czy Bartnik cytuje LyMPuS (sekcja 11) lub Tran et al. 2023 (sekcja 6) — na pierwszy rzut oka
  jej bibliografia (103 pozycje, przejrzana) **nie zawiera żadnej z tych dwóch prac** — może umknęły jej
  literaturowo, albo LyMPuS wyszło zbyt późno, żeby zdążyła je uwzględnić (obie prace z 2026, zbliżone
  terminy). Warto to zauważyć, ale nie polegać na tym jako dowodzie — to obserwacja z jednej pracy, nie
  systematyczne przeszukanie.
- Zapytać promotora wprost, czy zna zakres pracy Bartnik i jak sugeruje odróżnić/pozycjonować P3Net.

## 14. Kategoria 1 (benchmark tabelaryczny) vs Kategoria 2 (trening na żywo) — decyzja metodologiczna

Wynikło z pytania "jak Bartnik dobiera architektury" — okazało się, że to fundamentalna, wcześniej
nieomówiona decyzja projektowa, którą trzeba podjąć świadomie, nie domyślnie.

### 14.1 Dwie kategorie praktycznego uprawiania NAS

**Kategoria 1 — benchmark tabelaryczny (lookup).** Ktoś wcześniej raz wytrenował wszystkie architektury
z małej, zamkniętej przestrzeni i opublikował wyniki jako gotową tabelę (NAS-Bench-101/201/301,
HW-NAS-Bench). Przykład: **Bartnik** — dokładność z lookupu NAS-Bench-201, żadnego treningu poza
jednoepokowym przebiegiem do pomiaru energii.

**Kategoria 2 — bezpośredni trening/fine-tuning w PyTorch/TensorFlow.** Architektura budowana "na żywo"
z genotypu i faktycznie trenowana. NSGA-Net: pełny trening od zera (25 epok, ~8 GPU-dni łącznie).
NSGANetV2: hybryda — supersieć trenowana raz, każdy kandydat dostaje tylko fine-tuning z wag
odziedziczonych (~1 GPU-dzień dzięki temu skrótowi).

Obecny `problem_formulation.tex` explicite zakłada Kategorię 2: *"A full evaluation $f_1(x)$ requires
training $D(x)$ from scratch."* — to jest model NSGA-Net, nie Bartnik.

### 14.2 Dlaczego Bartnik wybrała Kategorię 1 — i dlaczego to nie jest "łatwizna"

Trzy konkretne, metodologiczne powody, nie tylko wygoda:

1. **Izolacja zmiennej badanej.** Jej RQ dotyczy algorytmu/surrogate'u, nie znalezionej architektury.
   Trening na żywo wprowadziłby szum SGD, zanieczyszczający porównanie. Benchmark daje deterministyczną,
   powtarzalną wartość — jej własne słowa: *"Using a benchmark lookup makes this objective deterministic
   and reproducible."*
2. **Policzalny prawdziwy front Pareto (oracle) do IGD+.** W zamkniętej, w pełni znanej przestrzeni
   (15625 architektur) da się policzyć prawdziwy front brute-force'em — *"The reference Pareto front is
   computed by enumeration over the measurement cache."* W otwartej przestrzeni z pełnym treningiem
   **nigdy nie da się poznać prawdziwego frontu** — IGD+ jako rzetelna metryka jest praktycznie osiągalna
   tylko w Kategorii 1.
3. **Budżet obliczeniowy pracy magisterskiej.** Jej pełna kampania to setki przebiegów (4 warianty ×
   pule surrogate'ów × tempa relaksacji × harmonogramy dynamicznego doboru × 10 ziaren × 2 problemy).
   Przy Kategorii 2 to fizycznie niewykonalne w ramach pracy magisterskiej — dzięki lookupowi "drogi"
   element jest darmowy, więc cały budżet poszedł na szeroką siatkę eksperymentów algorytmicznych i na
   jedyny realny pomiar (energia GPU).

### 14.3 Bartnik sama przyznaje ograniczenie zakresu — cytat wprost

Sekcja Discussion (8.2) jej pracy: *"They rest on a single benchmark, NAS-Bench-201, and a single
dataset, with CIFAR-10 accuracy taken from the benchmark table and not from retraining, so the
conclusions describe this search space and not Neural Architecture Search in general."*

To bezpośrednio wspiera pozycjonowanie P3Net jako odpowiedzi na pytanie, którego jej praca **celowo nie
stawia**: czy ta klasa podejść (linkage-learning + surrogate) daje realną przewagę w drogim, otwartym
reżimie, nie tylko w zamkniętym, deterministycznym benchmarku.

### 14.4 Koszty przejścia na Kategorię 2 — czego świadomie się zrzekacie

1. **Deterministyczność** — wyniki zaszumione wariancją SGD, trzeba uśredniać po wielu ziarnach
   losowości (macie to już zapisane jako $s$ w `problem_formulation.tex`), co dodatkowo podnosi koszt.
2. **Prawdziwy front do IGD+** — nieosiągalny. Trzeba albo zrezygnować z IGD+ na rzecz metryk
   nie wymagających oracle (hypervolume względem best-known frontu, jak w NSGA-Net/NSGANetV2), albo
   zaakceptować, że IGD+ będzie tylko przybliżeniem.
3. **Skala eksperymentu** — drastycznie mniej wariantów/ziaren możliwych do przetestowania niż u Bartnik,
   bo każda ewaluacja kosztuje realny czas GPU.

### 14.5 Opcja pośrednia — nie trzeba wybierać skrajności

**Supersieć + fine-tuning (jak NSGANetV2)** zamiast czystego treningu od zera (jak NSGA-Net) — wciąż
"prawdziwy" trening (nie lookup), ale znacznie tańszy (~1 GPU-dzień zamiast ~8), bo kosztowna faza
(trening supersieci) jest jednorazowa, a każdy kandydat dostaje tylko kilka epok fine-tuningu.

### 14.6 Rekomendacja

Do rozstrzygnięcia świadomie, nie domyślnie, najlepiej razem z promotorem — biorąc pod uwagę realnie
dostępny budżet obliczeniowy:
- **Kategoria 1** (inny benchmark niż NAS-Bench-201, żeby uniknąć bezpośredniego nakładania z Bartnik) —
  jeśli priorytetem jest czystość porównania P3 vs NSGA2 jako silników i rzetelne IGD+.
- **Kategoria 2 pełna** (trening od zera, model NSGA-Net) — jeśli priorytetem jest realna użyteczność
  praktyczna, i jest dostęp do budżetu porównywalnego z ~8 GPU-dniami.
- **Kategoria 2 z supersiecią** (model NSGANetV2) — kompromis: realny trening, ale znacznie tańszy,
  praktyczna przewaga bez konieczności posiadania klastra GPU na wyłączność.

**Sprawdzone (2026-07-22):** żaden plik w aktywnym szkicu `chapters/v003/*` nie wspomina o kodowaniu
ciągłym ani o Kategorii 1/2 explicite — to wciąż otwarta decyzja, nieprzesądzona w żadnym dokumencie.
Wzmianki o zmiennych ciągłych istnieją tylko w starszej, niepodpiętej gałęzi `chapters/v002/` i dotyczą
hiperparametrów treningu (learning rate, dropout), nie kodowania architektury.

## 15. Decyzje z 2026-07-22 — kierunek NAS+HPO, wynik sprawdzenia niszy, aktualizacja v003

### 15.1 Decyzje potwierdzone przez użytkownika

1. Zostajemy przy P3 i surogacie w duchu Przewoźniczka (LyMPuS/$\hat{\delta}_F$, linkage-aware/relative) —
   bez zmian względem wcześniejszych ustaleń.
2. Kategoria 1 vs Kategoria 2 — **rozstrzygnięte (2026-07-22): oba równolegle, żaden jako jedyny.**
   Zamiast wybierać jeden benchmark, protokół raportuje wyniki na obu (JAHS-Bench-201 i
   NAS-HPO-Bench-II) i jawnie rozróżnia wyniki potwierdzone na obu (primary finding) od wyników
   specyficznych dla jednego benchmarku (nie uogólnianych). To świadoma decyzja projektowa, nie
   odroczenie — patrz 15.3 niżej za uzasadnieniem, dlaczego te dwa benchmarki nadają się akurat do takiego
   "bracketingu".
3. Konkretny benchmark: **JAHS-Bench-201** (primary, źródło HV) i **NAS-HPO-Bench-II** (Category-1
   counterpart, źródło IGD+ dzięki policzalnemu oracle frontowi), zamiast czystego NAS-Bench-201
   (co bezpośrednio nakładałoby się na pracę Bartnik).
4. Kierunek: **joint NAS+HPO** potwierdzony — genotyp obejmuje architekturę i hiperparametry treningu, nie
   tylko architekturę.
5. Wykonano dedykowane sprawdzenie niszy (zob. 15.2).

### 15.2 Wynik sprawdzenia niszy: GOMEA/P3 + joint NAS+HPO

Trzy zapytania web search (`GOMEA neural architecture search hyperparameter optimization joint`,
`"P3" OR "GOMEA" "JAHS-Bench" OR "NAS-HPO-Bench" linkage learning`,
`parameter-less population pyramid neural architecture search hyperparameter`) **nie zwróciły ani jednej
pracy łączącej GOMEA/P3/linkage-learning EA z joint NAS+HPO**. Podpole joint NAS+HPO istnieje i jest
ugruntowane (Zela et al. 2018 \citep{zela2018towards} jako praca założycielska; JAHS-Bench-201
\citep{bansal2022jahsbench} i NAS-HPO-Bench-II \citep{hirose2021nashpobenchii} jako standardowe
benchmarki; Guerrero-Viu et al. 2021 \citep{guerreroviu2021bagofbaselines} jako systematyczne porównanie
solverów), ale wszystkie porównywane tam algorytmy to standardowe MO-baseline'y (NSGA-II, MO-BOHB, random
search, differential evolution) — żaden nie jest z rodziny linkage-learning.

**Ocena rygoru:** to negatywny wynik wyszukiwania (nie znaleziono), nie systematyczny przegląd literatury
— traktować jako wsparcie dla claimu o luce, nie jako dowód rozstrzygający. Warto powtórzyć bardziej
dogłębne sprawdzenie (np. Google Scholar, DBLP po autorach z linii GOMEA/Bosman/Przewoźniczek) przed
złożeniem finalnej wersji artykułu.

### 15.3 JAHS-Bench-201 vs NAS-HPO-Bench-II — dlaczego "oba równolegle" ma sens jako rozstrzygnięcie

JAHS-Bench-201 to *surrogate benchmark* — nie tabela lookup, tylko wytrenowany regresor (XGBoost) nad
ciągłą przestrzenią hiperparametrów, pozwalający odpytywać prawie-ciągłe wartości tanio, bez realnego
treningu. To coś pomiędzy Kategorią 1 a 2: nie ma kosztu żywego treningu, ale wejście jest ciągłe, więc nie
ma też zamkniętej, skończonej siatki do enumeracji dla dokładnego oracle frontu (stąd HV względem
best-known frontu zamiast IGD+ na tym benchmarku). NAS-HPO-Bench-II to za to czysta Kategoria 1: 192K
stałych, zmierzonych naprawdę konfiguracji (architektura × learning rate × batch size), z policzalnym
oracle frontem (stąd IGD+ możliwe tu, ale nie na JAHS).

**Decyzja (2026-07-22):** zamiast wybierać jeden z nich, protokół w `results/main.tex` raportuje na obu i
jawnie oznacza, które wyniki trzymają się na obu benchmarkach (primary finding) a które są specyficzne dla
jednego (nie uogólniane poza niego). To rozwiązuje pierwotne pytanie 14. bez arbitralnego wyboru — mocna
strona jednego benchmarku (ciągłość, brak kosztu treningu) kompensuje słabość drugiego (brak IGD+), i na
odwrót (dokładny oracle front kompensuje sztywną siatkę). Koszt tej decyzji: podwójna liczba eksperymentów
do przeprowadzenia i zaraportowania.

### 15.4 Nowe pytanie techniczne: P3 na dyskretnym drzewie linkage vs ciągłe hiperparametry

P3/GOMEA w standardowej formie buduje linkage tree i wykonuje crossover nad dyskretnymi blokami zmiennych.
Joint NAS+HPO wprowadza wymiary ciągłe (learning rate, weight decay), których standardowy P3 nie obsługuje
wprost. Dwie opcje do rozstrzygnięcia przed implementacją:
- **Dyskretyzacja/binning** wymiarów ciągłych do skończonej siatki (prościej, zgodne z bazowym P3, ale
  traci rozdzielczość).
- **Rozszerzenie w duchu RV-GOMEA** (real-valued GOMEA, Bouter et al. 2017) — mixing nad zmiennymi
  ciągłymi, ale to inny mechanizm niż czysty P3 i wymaga jawnego uzasadnienia w Proposed Optimizer.

Zaflagowane w `results/main.tex` jako "Open decisions (ii)", nierozstrzygnięte w tej rundzie edycji.

### 15.5 Pliki zaktualizowane w tej rundzie

`refs.bib` (+4 wpisy: `zela2018towards`, `bansal2022jahsbench`, `hirose2021nashpobenchii`,
`guerreroviu2021bagofbaselines`), `chapters/v003/related_work/main.tex` (nowe akapity o joint NAS+HPO i o
pracy Bartnik, przepisane zdanie o luce), `chapters/v003/results/main.tex` (nowy akapit "Benchmark and
search space", zredukowane "Open decisions" z 3 do 2 punktów), `chapters/v003/problem_formulation/main.tex`
(jednozdaniowe zastrzeżenie o rozszerzeniu $\Lambda$ o wymiary ciągłe, odłożone do rozstrzygnięcia 15.4).
