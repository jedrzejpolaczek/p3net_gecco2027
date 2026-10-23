# Surogat P3Net — karta źródła

Status: **ZATWIERDZONA** (2026-10-16, autor projektu; decyzje w §6).
Zależy od: `notes/plans/v005-sources/p3net.md` (zatwierdzona) — D-1 = b (reguła MO-GOMEA), D-2 = a (FIHC na prawdziwych
ewaluacjach), D-3 = b (mieszanie z poziomem na surogacie, prawdziwa ewaluacja wyniku po każdym poziomie; wariant a —
bramka w stylu SA-P3-GOMEA). Decyzje: `v005-decisions.md` #6 (nikt nie dostaje darmowego f2), #8 (nowy surogat).

## 1. Źródła

Surogat P3Net jest **projektem własnym**; nie ma jednego źródła do odtworzenia. Elementy z literatury:

| Element | Źródło | Plik w repo |
|---|---|---|
| Regresja na **parach** rozwiązań (model przewiduje różnicę fitness dwóch rozwiązań; trening na wszystkich uporządkowanych parach; predykcja wartości bezwzględnej przez uśrednienie po punktach odniesienia) | Dushatskiy, Mendrik, Alderliesten, Bosman, *CS-GOMEA*, GECCO'19 (`dushatskiy2019csgomea`), §2.1, Alg. 1 | `notes/articles/linkage learn/Convolutional neural network surrogate-assisted GOMEA.pdf` |
| Otwarty problem: surogat, który wykorzystuje drzewo powiązań | CS-GOMEA, §6 („future work”) | jw. |
| Porównanie względne zamiast wartości bezwzględnej, w kontekście powiązań | Przewoźniczek et al., *LyMPuS/eLyMPuS*, GECCO'26 (`przewozniczek2026lympus`) — inspiracja, nie mechanizm | `notes/articles/linkage learn/Limited Perfect Monotonical Surrogates constructed using.pdf` |
| Bramka akceptacji na kwantylu predykcji (tylko wariant D-3a) | Dushatskiy et al., GECCO'21 (SA-P3-GOMEA), §2.4.1; Bartnik 2026, Alg. 7–8 | `notes/articles/linkage learn/A Novel Surrogate-assisted…`, `notes/articles/NAS/MO-NAS/Evolutionary optimization…` |

Dane z v004, które uzasadniają zmiany (R2): krajobrazy silnie nieaddytywne (R² addytywny 0.36–0.48, z interakcjami 0.75–0.94);
f1 na FCNet skrajnie skośne (model liniowy na surowym f1: R² ≈ 0); RF przewidywał f1 ~10× dokładniej niż liniowy surogat
względny; błąd predykcji rośnie z długością łańcucha; LOO po parach dzielących punkty zawyżało jakość modelu.

## 2. Co surogat musi robić (wymagania z karty P3Net)

- **R1.** W trakcie mieszania z poziomem Pᵢ (P20–P25) ocenić każdy krok: czy nowe rozwiązanie x′ **dominuje** bieżące x,
  ma **te same** wartości celów, albo **nie jest zdominowane przez archiwum** (D-1 b). Potrzebne są więc przewidywane
  wartości **obu celów** (f1 i f2 — #6: kosztu nikt nie zna z góry), porównywalne z prawdziwymi wartościami w archiwum.
- **R2.** Działać od momentu, gdy jest wystarczająco danych; wcześniej mieszanie używa prawdziwych ewaluacji (czysty P3).
- **R3.** Nie zużywać budżetu (predykcje nie są ewaluacjami); budżet zużywają tylko FIHC (D-2 a) i ewaluacja wyniku po
  każdym poziomie (D-3 b).
- **R4.** Ten sam surogat w wariancie D-3a (bramka) — żeby porównanie wariantów izolowało sposób użycia surogatu, nie model.

## 3. Decyzje projektowe (opcje, za i przeciw)

### S-1. Forma predykcji

- **a) Model par + telescoping od ostatniego naprawdę ocenionego przodka** (pierwotny pomysł P3Net; tak opisuje to
  zatwierdzona karta P3Net, D-3 b): f̂(x_m) = f(x₀) − Σ δ̂(x_{i−1}, x_i).
  - Za: zgodne z zatwierdzoną kartą i pomysłem P3Net; wykorzystuje prawdziwą wartość przodka.
  - Przeciw: dla modelu nieliniowego błędy kroków się sumują; w v004 błąd rósł z długością łańcucha (2.8 → 5.0 p.p.).
- **b) Model par + predykcja przez uśrednienie po wielu punktach odniesienia** (CS-GOMEA, Alg. 1): f̂(x) = średnia po
  t ∈ H_t z f(t) + δ̂(t, x).
  - Za: oparcie w literaturze; brak łańcucha — błąd się nie sumuje; uśrednienie zmniejsza wariancję.
  - Przeciw: odejście od zatwierdzonego opisu D-3 b (telescoping); droższe obliczeniowo (|H_t| predykcji na krok).
- **c) Model bezwzględny** (predykcja f wprost z genotypu).
  - Za: najprostsze.
  - Przeciw: porzuca pomysł względnego surogatu; to już nie P3Net w sensie artykułu.

**Rekomendacja: a)** — zgodne z zatwierdzoną kartą; długość łańcucha i błąd rejestrowane (W-S7). b) wymagałoby zmiany
zatwierdzonej karty — podaję jako alternatywę, jeśli wolisz rozwiązanie z literatury.

### S-2. Jak surogat wykorzystuje powiązania (to, co w v004 nie działało — R1 §3.2)

Problem danych: para rozwiązań różniąca się **wyłącznie** w obrębie jednego małego klastra F jest wśród losowych ocen
prawie nieobecna (np. na JAHS dwa losowe genotypy zgadzają się na 8 pozycjach poza 2-elementowym F z prawdopodobieństwem
rzędu 10⁻⁵). Model uczony tylko na „parach z jednego F” nie miałby danych.

- **a) Osobny model dla każdego F**, uczony tylko na parach różniących się w F.
  - Za: dosłowna „świadomość powiązań”.
  - Przeciw: brak danych dla większości F (powyżej); wiele modeli.
- **b) Jeden model na wszystkich parach, z cechami zależnymi od F:** cechy = które zmienne się zmieniły (z jakiej na jaką
  wartość) + iloczyny cech **tylko dla par zmiennych w tym samym klastrze** bieżącego drzewa.
  - Za: dane z całego H_t; drzewo powiązań decyduje, jakie interakcje model może reprezentować — to odpowiada otwartemu
    problemowi z CS-GOMEA; obejmuje dane z FIHC (pary różniące się jedną zmienną) i z mieszania.
  - Przeciw: model zależy od drzewa, które zmienia się między poziomami i iteracjami — trzeba go przeuczać po zmianie drzewa.
- **c) Bez powiązań** (jak CS-GOMEA): model par bez informacji o F.
  - Za: najprostsze, oparte na literaturze.
  - Przeciw: porzuca główną deklarowaną nowość („linkage-aware”).

**Rekomendacja: b)** — jedyna opcja, w której powiązania realnie wpływają na model i są dane do uczenia. c) jako wariant
porównawczy (izoluje wkład powiązań — dokładnie to, czego v004 nie zmierzyło).

### S-3. Skala celów

Reguła D-1 (dominacja, archiwum) jest **niezmiennicza względem monotonicznych przekształceń każdego celu** osobno — można
więc uczyć i porównywać w przekształconej skali bez zmiany decyzji.

- **a) log dla obu celów** (f1: błąd w % lub MSE; f2: rozmiar / czas / energia — wszystkie dodatnie i skośne).
  - Za: usuwa problem FCNet (skośność 26–98, R² ≈ 0 na surowej skali); decyzje D-1 bez zmian.
  - Przeciw: log wymaga wartości > 0 (spełnione na wszystkich przestrzeniach, ale trzeba asercji).
- **b) Rangi / strata rankingowa** (model przewiduje, które z dwóch jest lepsze).
  - Za: najbardziej odporne na skalę.
  - Przeciw: D-1 wymaga porównania z archiwum (wartości), a nie tylko par — model rankingowy tego wprost nie daje.
- **c) Surowa skala.** Przeciw: v004 pokazał, że zawodzi na FCNet.

**Rekomendacja: a).**

### S-4. Klasa modelu

- **a) Las losowy (RF)** na cechach par z S-2.
  - Za: w v004 najlepsza dokładność (MAE ~10× mniejsze), dobre porządkowanie w najlepszym decylu; mało hiperparametrów;
    niepewność z rozrzutu drzew za darmo (przydatne dla wariantu z bramką).
  - Przeciw: słabo ekstrapoluje poza dane; liczba par rośnie jak N² (potrzebne próbkowanie par).
- **b) Gradient boosting.** Za: zwykle dokładniejszy. Przeciw: więcej hiperparametrów do strojenia (ryzyko dopasowania
  pod benchmark).
- **c) Ridge z interakcjami w obrębie F.** Za: szybki, przejrzysty. Przeciw: w v004 liniowe modele przegrywały; interakcje
  tylko parami.
- **d) Mała sieć neuronowa (jak CNN w CS-GOMEA).** Przeciw: dużo hiperparametrów, niestabilna przy ≤ 350 punktach.

**Rekomendacja: a)**, z hiperparametrami domyślnymi biblioteki (bez strojenia na benchmarkach); c) jako wariant tylko
jeśli chcesz zachować model liniowy dla porównania z v004.

### S-5. Drugi cel (koszt)

- **a) Ten sam model par, osobno dla f2.** Za: symetria; f2 jest prawie addytywne (R² 0.70–1.00), więc łatwe.
- **b) Prostszy model dla f2 (bezwzględny).** Za: tańsze. Przeciw: dwa różne mechanizmy w jednym surogacie.

**Rekomendacja: a).**

### S-6. Długość łańcucha (κ)

P3 nie ma κ. W mieszaniu z poziomem łańcuch ma długość co najwyżej liczby klastrów (~2n).

- **a) Bez limitu** (wierne P3). Za: brak parametru. Przeciw: długie łańcuchy = większy błąd telescopingu (S-1 a).
- **b) Stałe κ.** Przeciw: parametr, w v004 bez wpływu na wyniki.
- **c) Limit z niepewności** (RF: rozrzut drzew przekracza próg ⇒ prawdziwa ewaluacja). Za: adaptacyjne. Przeciw: to jest
  hybryda D-3 c, którą odrzucono.

**Rekomendacja: a)**, z rejestrowaniem błędu względem długości łańcucha (W-S7); decyzja może wrócić po wynikach.

### S-7. Kiedy przeuczać

- **a) Po każdej prawdziwej ewaluacji i po każdej zmianie drzewa** (przy b ≤ 350 ocen — tanie).
- **b) Raz na iterację P1–P6.**

**Rekomendacja: a).**

### S-8. Walidacja (dobór hiperparametrów, jeśli jakiekolwiek)

- **Obowiązkowo:** walidacja krzyżowa **grupowana po rozwiązaniach** (para nie może dzielić punktu między treningiem a
  walidacją) — w v004 LOO po parach zawyżało jakość i wybierało za słabą regularyzację (R1 §3.2).

### S-9. Zimny start

- **a) Surogat włącza się po pierwszym FIHC** (D-2 a). FIHC pierwszego rozwiązania daje 24–39 prawdziwych ewaluacji
  sąsiadów różniących się jedną zmienną — naturalny zbiór uczący dla par; do tego momentu mieszanie na prawdziwych
  ewaluacjach.
  - Za: bez dodatkowego parametru (P3 jest bezparametrowy); dane idealne dla modelu par.
  - Przeciw: przy b = 50 FIHC zużywa większość budżetu (karta P3Net §9).
- **b) Stały próg danych (np. n+1 ocen).** Przeciw: parametr dobrany ręcznie.

**Rekomendacja: a).**

## 4. Własności do sprawdzenia testami (poziom 1)

| ID | Własność |
|---|---|
| W-S1 | Surogat nigdy nie wywołuje benchmarku; liczba ewaluacji nie zależy od liczby predykcji |
| W-S2 | Przewiduje oba cele; f2 nie jest odczytywane z benchmarku dla nieocenionych kandydatów |
| W-S3 | Cechy interakcji powstają tylko dla par zmiennych w tym samym klastrze bieżącego drzewa (S-2 b); zmiana drzewa zmienia zbiór cech |
| W-S4 | Na problemie o znanej strukturze (pułapki k-arne) model z cechami S-2 b przewiduje istotnie lepiej niż bez nich (S-2 c) |
| W-S5 | Trening i predykcja w skali log; decyzje D-1 identyczne jak przy porównaniu w skali oryginalnej dla prawdziwych wartości |
| W-S6 | Walidacja grupowana: żaden punkt nie występuje jednocześnie w parach treningowych i walidacyjnych |
| W-S7 | Rejestrowany błąd predykcji vs długość łańcucha (diagnostyka) |
| W-S8 | Przed pierwszym zakończonym FIHC mieszanie używa prawdziwych ewaluacji (S-9 a) |
| W-S9 | Model antysymetryczny: δ̂(x, x′) ≈ −δ̂(x′, x) i δ̂(x, x) ≈ 0 (z konstrukcji danych lub cech) |
| W-S10 | Ten sam obiekt surogatu używany w P3Net (D-3 b) i wariancie D-3 a |

## 5. Warianty porównawcze (wynikają z decyzji)

- **P3Net-gate** (D-3 a): ten sam surogat, bramka kwantylowa w stylu SA-P3-GOMEA / Bartnik — izoluje „zastąpienie vs bramka”.
- **P3Net-nolink** (S-2 c): model par bez cech z drzewa powiązań — izoluje wkład powiązań.

## 6. Decyzje (2026-10-16)

S-1 a (telescoping), S-2 b + wariant c, S-3 a (log), S-4 a (RF, domyślne hiperparametry), S-5 a, S-6 a (bez limitu,
diagnostyka W-S7), S-7 a, S-8 obowiązkowe, S-9 a (start po pierwszym FIHC); lista W-S1–W-S10 przyjęta.
