# MO-LS (lokalne przeszukiwanie z losową skalaryzacją) — karta źródła

Status: **ZATWIERDZONA** (2026-10-16, autor projektu): L-1 b, L-2 (losowe λ), W-L1–W-L5, test poziomu 2.

## 1. Źródła

- Den Ottelander, Dushatskiy, Virgolin, Bosman, *Local Search is a Remarkably Strong Baseline for Neural Architecture
  Search*, EMO 2021, LNCS 12654, s. 465–479 (arXiv 2004.08996v3) (`denottelander2021localsearch` — klucz w `refs.bib`
  potwierdzony 2026-10-16). Plik w repo:
  `notes/articles/NAS/Local Search is a Remarkably Strong Baseline.pdf`, §3 (algorytm LS).
- Kod autorów: `https://github.com/tdenottelander/MacroNAS` (przeczytany 2026-10-16): `src/SearchAlgorithms/MO/LS.cpp`,
  normalizacja celów w `src/FitnessFunction/CIFAR/Bench_CIFAR10.cpp`.
- Ten sam baseline (MO-LS z grupy Bosmana) jest punktem odniesienia u Bartnik (Tab. 7.1) — spójne porównanie.

Dlaczego karta (R1 §10): w v004 `mo_ls` był Pareto Local Search (Paquete 2004) z pełnym sąsiedztwem i archiwum
niezdominowanych — **inną metodą** niż „LS” z cytowanej pracy.

## 2. Algorytm wg artykułu i kodu (zgodne)

- **L1.** Losowa architektura (jak RS), ocena.
- **L2.** Losowy współczynnik skalaryzacji λ ~ U(0, 1); funkcja: λ·g1 + (1 − λ)·g2 (maksymalizacja).
- **L3.** Jedna runda: zmienne w losowej kolejności; dla każdej zmiennej ocena **wszystkich** wartości (best-improvement
  po wartościach, first-improvement po zmiennych); ruch, gdy skalaryzacja **ściśle** rośnie.
- **L4.** Po jednej rundzie (`loop = false`, domyślnie i w artykule) — restart od L1, aż do wyczerpania budżetu.
- **L5.** Zbiór wynikowy: wszystkie ocenione (archiwum niezdominowanych liczone po fakcie).
- **L6.** Kod: g1 = dokładność·0.01, g2 = 1 − (MMACs − min)/(max − min), **min/max — stałe całego benchmarku**.
- **L7.** Kod ocenia też bieżącą wartość zmiennej (pętla po całym alfabecie) — u nas to duplikat z H_t, bez kosztu.

## 3. Odstępstwa i decyzje

| # | Odstępstwo | Powód | Status |
|---|---|---|---|
| O-L1 | Duplikaty (w tym bieżąca wartość, L7) nie zużywają budżetu | #35 | zatwierdzone (wspólne) |
| O-L2 | Stop dokładnie po b ewaluacjach, także w środku rundy | K-2 | zatwierdzone (wspólne) |

### L-1. Normalizacja celów do skalaryzacji

- **a) Jak kod: stałe min/max całego benchmarku.** Za: wierne. Przeciw: wiedza o zakresie f2 spoza budżetu (REINFORCE
  R-3 tego nie dostał).
- **b) Bieżące min/max ocenionych dotąd punktów** (jak REINFORCE R-3 a). Za: spójne z resztą; żadnej wiedzy z
  zewnątrz. Przeciw: odstępstwo od kodu; skalaryzacja tego samego punktu zmienia się w trakcie.

**Rekomendacja: b)** — zasada „żadnej wiedzy o celach spoza ewaluacji” ważniejsza niż szczegół kodu; odstępstwo opisane.
g1 = 1 − f1_norm (dla wszystkich przestrzeni, także FCNet z MSE).

### L-2. Wybór λ

Kod ma też warianty deterministyczne (`OBJECTIVESPACE`, `SCALARIZATIONSPACE` — wypełnianie największej luki); artykuł
używa losowego. **Rekomendacja: losowe λ ~ U(0, 1)** (artykuł + domyślne w kodzie).

## 4. Własności do sprawdzenia testami (poziom 1)

| ID | Własność |
|---|---|
| W-L1 | Każda runda zaczyna się od nowej losowej, poprawnej architektury i nowego λ ~ U(0, 1) |
| W-L2 | Jedna runda: każda zmienna raz, w losowej kolejności; wszystkie wartości zmiennej ocenione |
| W-L3 | Ruch tylko przy ścisłym wzroście skalaryzacji (λ·g1 + (1−λ)·g2) |
| W-L4 | Brak drugiej rundy (restart po jednej) |
| W-L5 | Normalizacja wg L-1; duplikaty bez kosztu; budżet nigdy nie przekroczony |

**Test zgodności (poziom 2):** nasz MO-LS vs `MacroNAS` LS (`-o LS noloop 1`) na problemie z kodu autorów (MacroNAS
benchmark, CIFAR-10, z ich normalizacją — dla testu tryb L-1 a): median HV ±2 % + TOST, 30 przebiegów, ten sam budżet.

## 5. Do zatwierdzenia

L-1 (rek. b), L-2 (losowe λ), W-L1–W-L5, test poziomu 2 (z trybem L-1 a tylko na potrzeby testu).
