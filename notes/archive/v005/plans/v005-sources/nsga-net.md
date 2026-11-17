# NSGA-Net — karta źródła

Status: **ZATWIERDZONA** (2026-10-16, autor projektu): N-1 a (wersja zgodna z kodem autorów, bez BOA — opisane w
artykule), N-2 a, O-N3, W-N1–W-N6, test poziomu 2.
Decyzje wcześniejsze: #15 (turniej binarny; BOA wg publikacji albo jawne odstępstwo), #35 (deduplikacja), #37
(populacja 20, hiperparametry z oryginału).

## 1. Źródła

- **Cytowana wersja:** Lu et al., *NSGA-Net: Neural Architecture Search using Multi-Objective Genetic Algorithm*,
  GECCO'19, s. 419–427 (`lu2019nsganet`). Plik: `notes/articles/NSGA/NSGA-Net Neural Architecture Search using
  Multi-Objective Genetic Algorithm (GECCO 2019, arXiv v2).pdf` (arXiv:1810.03522v2, 18.04.2019 — wersja zbieżna z
  GECCO; dodana 2026-10-16).
- Wcześniejsza wersja (ICLR 2019 „under review”, arXiv v1): `notes/articles/NSGA/NSGA-NET …pdf` — **nie cytować**.
- **Porównanie GECCO vs ICLR:** te same operatory (krzyżowanie „homogeneous”, mutacja ≤ 1 bit, BOA) i ta sama
  przestrzeń makro (bity, 3 fazy × 6 węzłów, operacje węzłów ustalone). GECCO dodaje: **p_krzyżowania = 0.9,
  p_mutacji = 0.02**, 20 generacji eksploracji + **10 generacji eksploatacji (BOA)**, populacja 40, start losowy
  (opcjonalnie zasiew architekturami ręcznymi); wybór rodziców nadal nieopisany. Przestrzeń mikro z kodu autorów
  pojawia się dopiero w późniejszych wersjach.
- Kod autorów: `https://github.com/ianwhale/nsga-net` (przeczytany 2026-10-16): `search/nsganet.py` (algorytm),
  `search/evolution_search.py` (parametry), `pymoo == 0.3.0`.

## 2. Algorytm — artykuł vs kod

| Element | Artykuł GECCO'19 (§3.2, §4.2) | Kod autorów |
|---|---|---|
| Szkielet | NSGA-II: µ + λ, przetrwanie po randze NDS i crowding distance | to samo (`RankAndCrowdingSurvival`) |
| Wybór rodziców | nie opisany („parents selected from the population”) | **turniej binarny**: dominacja, przy braku dominacji crowding, remis losowo |
| Krzyżowanie | **„homogeneous”**, p = 0.9: wspólne bity rodziców zachowane, pozostałe losowo od jednego z rodziców, liczba jedynek potomka między liczbami rodziców | **dwupunktowe** (`PointCrossover(n_points=2)`) |
| Mutacja | **odwrócenie co najwyżej 1 bitu**, p = 0.02 | **wielomianowa** na liczbach całkowitych, η = 3 (`PolynomialMutation(eta=3, var_type=int)`) |
| Eksploatacja | **BOA**: sieć bayesowska p(x₁), p(x₂ | x₁), p(x₃ | x₂) po fazach, z całej historii; 10 ostatnich generacji | **brak** |
| Duplikaty | przybliżone wykrywanie duplikatów fenotypu (App. 6.1) | `eliminate_duplicates = True` (genotyp) |
| Kodowanie | bitowe (makro: graf faz, Xie & Yuille) | makro: bity; **mikro: liczby całkowite (operacje 0…n_ops−1)** — operatory z kodu działają na nich wprost |
| Populacja / potomstwo / generacje | 40 / 40 / 20 eksploracji + 10 eksploatacji | 40 / 40 / 50 (domyślne argumenty) |

Prawdopodobieństwa krzyżowania i mutacji — **odczytane z kodu pymoo 0.3.0 (2026-10-16, sdist PyPI)**: `PointCrossover`
nie ma parametru prawdopodobieństwa — **krzyżowanie zawsze (p = 1.0)**; `PolynomialMutation(prob=None)` → **p = 1/n na
zmienną**; dla `var_type=int` wynik `np.rint`, potem naprawa do zakresu (`OutOfBoundsRepair`). (Wcześniejsze
„oczekiwane 0.9” było błędne.)

## 3. Odstępstwa wymagane przez nasz problem

| # | Odstępstwo | Powód | Status |
|---|---|---|---|
| O-N1 | Populacja 20, potomstwo 20 (zamiast 40/40) | #37 | zatwierdzone (wspólne) |
| O-N2 | Liczba generacji wynika z budżetu; stop wg K-2 | protokół | zatwierdzone (wspólne) |
| O-N3 | Genotyp kategoryczny kodowany liczbami całkowitymi 0…k−1 | nasze przestrzenie; kod autorów robi to samo w przestrzeni mikro | do zatwierdzenia |

## 4. Decyzje do podjęcia

### N-1. Którą wersję odtwarzamy

- **a) Kod autorów** (turniej binarny, krzyżowanie dwupunktowe, mutacja wielomianowa η = 3, deduplikacja, bez BOA).
  - Za: to jest opublikowany, uruchamialny artefakt; operatory działają na kodowaniu całkowitym bez żadnej adaptacji;
    weryfikowalne testem zgodności z kodem autorów (pymoo 0.3.0).
  - Przeciw: brak BOA, czyli jednego z pięciu deklarowanych komponentów artykułu. W artykule: „we use the authors'
    public implementation, which does not include the BOA exploitation stage”.
- **b) Artykuł GECCO'19** (krzyżowanie „homogeneous” p = 0.9, mutacja ≤ 1 zmiany p = 0.02, BOA w ostatniej 1/3
  generacji).
  - Za: pełna metoda z cytowanej publikacji; parametry podane wprost.
  - Przeciw: operatory i BOA są zdefiniowane dla **bitowego** kodowania faz. Na kategorycznym genotypie:
    krzyżowanie „homogeneous” bez warunku liczby jedynek = krzyżowanie jednorodne (blisko); mutacja ≤ 1 zmiany = zmiana
    jednej zmiennej na inną wartość (blisko); BOA „po fazach” trzeba zastąpić łańcuchem p(x₁), p(x₂ | x₁), … po
    zmiennych albo grupach (architektura | HP) — **nasza adaptacja**. Wyboru rodziców artykuł nie podaje (trzeba
    przyjąć turniej binarny z kodu). Nie ma kodu do testu zgodności dla BOA.
- **c) a) jako NSGA-Net + BOA dołożone jako wariant w suplemencie.**
  - Za: pokazuje wpływ BOA. Przeciw: wariant to nasza adaptacja; koszt dodatkowego ramienia.

**Rekomendacja: a)** — jedyna wersja bez własnych adaptacji. c) tylko jeśli chcesz mieć BOA w ogóle.

### N-2. Mutacja wielomianowa na zmiennych bez porządku

W kodzie autorów mutacja wielomianowa traktuje numer operacji jak liczbę (operacja 3 jest „bliżej” 2 niż 0). Na naszych
zmiennych bez porządku (operacje, aktywacja) to arbitralne; na siatkach LR/WD/batch porządek jest sensowny.

- **a) Tak jak kod** (na wszystkich zmiennych, kodowanie całkowite). Za: wierne. Przeciw: arbitralny porządek kategorii.
- **b) Wielomianowa na zmiennych porządkowych, losowanie od nowa na nieuporządkowanych.** Za: sensowniejsze.
  Przeciw: nasza modyfikacja.

**Rekomendacja: a)** + kolejność kategorii ustalona raz (jak w `search_spaces/*.py`) i opisana; b) byłoby odstępstwem.

## 5. Własności do sprawdzenia testami (poziom 1)

| ID | Własność |
|---|---|
| W-N1 | Wybór rodziców: turniej binarny — dominujący wygrywa; bez dominacji większy crowding; remis losowo |
| W-N2 | Krzyżowanie dwupunktowe z prawdopodobieństwem z pymoo 0.3.0; geny potomka pochodzą z rodziców |
| W-N3 | Mutacja wielomianowa η = 3, wynik zaokrąglony i w zakresie 0…k−1; prawdopodobieństwo per zmienna z pymoo 0.3.0 |
| W-N4 | Przetrwanie: µ + λ, NDS + crowding (identyczne z pymoo NSGA-II) |
| W-N5 | Duplikaty (w populacji, potomstwie i H_t) eliminowane przed ewaluacją; nie zużywają budżetu |
| W-N6 | Populacja 20, potomstwo 20, start losowy; budżet nigdy nie przekroczony |

**Test zgodności (poziom 2):** nasz NSGA-Net vs `ianwhale/nsga-net` (`nsganet.py` na pymoo 0.3.0) na problemie
syntetycznym z kodowaniem całkowitym (np. dwukryterialne pułapki k-arne) i na NAS-HPO-Bench-II, te same ziarna i
budżet: median HV ±2 % + TOST, 20 przebiegów. Kryterium zapisane przed testem.

## 6. Do zatwierdzenia

O-N3; N-1 (rek. a), N-2 (rek. a); W-N1–W-N6; test poziomu 2. (Wersja GECCO'19 sprawdzona 2026-10-16 — §1.)
