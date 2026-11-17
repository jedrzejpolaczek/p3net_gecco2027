# Regularized (aging) evolution — adaptacja wielokryterialna — karta źródła

Status: **ZATWIERDZONA** (2026-10-16, autor projektu): O-RE2, O-RE3, O-RE4, RE-1 b, W-RE1–W-RE6, test poziomu 2.
Decyzja wcześniejsza (`v005-decisions.md`, #24): opublikowanej wersji wielokryterialnej nie ma → **zostaje nasza
adaptacja**, jawnie odnotowana w artykule jako **jedyna własna adaptacja wielokryterialna** wśród baseline'ów.

## 1. Źródła

- Real, Aggarwal, Huang, Le, *Regularized Evolution for Image Classifier Architecture Search*, AAAI 2019
  (`real2019regularized`), Alg. 1 („Aging Evolution”), §Methods. arXiv 1802.01548 (scratchpad → `notes/articles/NAS/`).
- Implementacja dla benchmarków: NAS-Bench-201 `exps/NAS-Bench-201-algos/R_EA.py` (Dong & Yang 2020, App.).

## 2. Algorytm wg źródeł (jednokryterialny)

| Element | Real et al. 2019 | NAS-Bench-201 `R_EA.py` |
|---|---|---|
| Populacja P, próbka S | P = 100, S = 25 (główne; S/P = 0.25) | P = 10, S = 10 (wybrane z {3, 5, 10}) |
| Start | P losowych architektur | to samo |
| Turniej | S losowych z populacji (**ze zwracaniem**), rodzic = najlepszy w próbce | to samo (`random.choice` S razy) |
| Mutacja | jedna z: zmiana operacji / zmiana wejścia (hidden state) / **identyczność (p = 0.05)** | zmiana jednej operacji na **inną** |
| Usuwanie | **najstarszy** (kolejka) | to samo (`popleft`) |

## 3. Odstępstwa

| # | Odstępstwo | Powód | Status |
|---|---|---|---|
| O-RE1 | **Wybór „najlepszego” w próbce przy dwóch celach** (RE-1) | brak wersji wielokryterialnej w literaturze | do decyzji (RE-1) |
| O-RE2 | P = 20 (#37), S = 5 (zachowany stosunek S/P = 0.25 z Real et al.) | #37 | do zatwierdzenia |
| O-RE3 | Mutacja: jedna losowa zmienna → inna wartość (jak NAS-Bench-201); **zmiana 2026-10-20 (decyzja b, test poziomu 2):** wybór zmiennej jak w `R_EA.py` — w przestrzeni komórkowej najpierw węzeł (jednostajnie), potem krawędź wchodząca do niego (krawędź do węzła 1: 1/3, do węzła 2: po 1/6, do węzła 3: po 1/9); **Z-RE1:** każda zmienna spoza komórki (HP w JAHS) to osobna jednostka losowana na równi z węzłami; w przestrzeniach bez komórki — jednostajnie po zmiennych; **bez mutacji identycznościowej** — na deterministycznym benchmarku z deduplikacją kopia rodzica nic nie wnosi (#35) | benchmark deterministyczny | do zatwierdzenia |
| O-RE4 | Dziecko-duplikat (już w H_t): nie zużywa budżetu; **wchodzi do populacji** ze znaną wartością i starzeje się normalnie | #35; zachowuje dynamikę starzenia | do zatwierdzenia |

## 4. Decyzja RE-1: kto wygrywa turniej przy dwóch celach

- **a) Ranga NDS w próbce, remis — crowding w próbce, dalej losowo** (v004).
  - Za: lokalne, proste. Przeciw: crowding liczony na 5 punktach jest prawie bez znaczenia (skrajne punkty mają ∞).
- **b) Porównanie „crowded comparison” NSGA-II liczone na całej populacji:** wygrywa członek próbki z najniższą rangą
  NDS w populacji, remis — większy crowding w jego froncie populacji.
  - Za: znany operator z literatury (Deb et al. 2002) — adaptacja składa się z dwóch opublikowanych elementów
    (aging evolution + crowded comparison); stabilniejsze rangi.
  - Przeciw: koszt NDS populacji na każdy turniej (P = 20 — pomijalny).
- **c) Losowy spośród niezdominowanych w próbce.**
  - Za: najmniej założeń. Przeciw: słabsza presja selekcyjna.

**Rekomendacja: b).** Zdanie do artykułu: „We adapt aging evolution to two objectives by replacing the single-objective
tournament winner with NSGA-II's crowded-comparison operator over the current population.”

## 5. Własności do sprawdzenia testami (poziom 1)

| ID | Własność |
|---|---|
| W-RE1 | Start: P = 20 losowych, poprawnych, ocenionych |
| W-RE2 | Próbka: S = 5 losowań ze zwracaniem z populacji |
| W-RE3 | Zwycięzca wg RE-1 (rangi i crowding liczone na całej populacji) |
| W-RE4 | Mutacja zmienia dokładnie jedną zmienną na inną wartość |
| W-RE5 | Po dodaniu dziecka usuwany jest najstarszy (FIFO); rozmiar populacji stały |
| W-RE6 | Duplikat: bez zużycia budżetu, wchodzi do populacji (O-RE4); budżet nigdy nie przekroczony |

**Test zgodności (poziom 2):** wersja jednokryterialna (turniej po f1) vs `R_EA.py` NAS-Bench-201 na NB201, P = 10,
S = 10, te same ziarna: rozkład najlepszej dokładności walidacyjnej, ±2 % + TOST, 100 przebiegów. Adaptacja MO — tylko
poziom 1.

## 6. Do zatwierdzenia

O-RE2, O-RE3, O-RE4; RE-1 (rek. b); W-RE1–W-RE6; test poziomu 2.
