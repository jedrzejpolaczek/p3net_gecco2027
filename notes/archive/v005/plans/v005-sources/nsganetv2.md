# NSGANetV2 (MSuNAS) — karta źródła

Status: **ZATWIERDZONA** (2026-10-16, autor projektu): O-V1, O-V2, V-1 a + Z-V1, V-2 a, V-3 (bez ramienia ciągłego),
W-V1–W-V6, test poziomu 2.
Decyzje wcześniejsze: #16 (wg publikacji i kodu autorów: AS, wewnętrzny NSGA-II, wybór podzbioru), #6 (nikt nie
dostaje darmowego f2), BB-4 (rozmiar startowy min(źródło, ⌊0.25·b⌋)). Zasada z karty NSGA-Net: przy rozbieżności
artykuł–kod **wierzymy kodowi autorów** i opisujemy różnicę.

## 1. Źródła

- Lu, Deb, Goodman, Banzhaf, Boddeti, *NSGANetV2: Evolutionary Multi-Objective Surrogate-Assisted Neural Architecture
  Search*, ECCV 2020 (`lu2020nsganetv2`). Plik: `notes/articles/NSGA/NSGANetV2 …pdf`. Alg. 1, §3.3, §4.1, §4.3.
- Kod autorów: `https://github.com/mikelzc1990/nsganetv2` (przeczytany 2026-10-16): `msunas.py` (pętla, wewnętrzny
  NSGA-II, wybór podzbioru), `acc_predictor/{adaptive_switching, rbf, gp, carts, mlp, factory}.py`; pymoo.

Dlaczego karta (R1 §6.2): w v004 był to NSGA-II z filtrem potomstwa OLS na one-hot, wybór po samym f̂1, bez AS, bez
wewnętrznego NSGA-II i bez wyboru podzbioru.

## 2. Algorytm — artykuł vs kod

| Element | Artykuł | Kod autorów |
|---|---|---|
| Start | N losowych architektur (100 w §4.3) | `n_doe = 100` (`search_space.initialize`) |
| Iteracja | dopasuj predyktor dokładności do archiwum → NSGA-II na (f̂1, f2) → wybierz podzbiór → oceń → dopisz | to samo; `iterations = 30`, `n_iter = 8` ocen na iterację |
| Predyktor | **Adaptive Switching**: MLP, CART, RBF, GP; wybór przez CV | AS z pulą **{RBF, GP, CART}** (bez MLP), 10-krotna CV, wybór max(średnia τ Kendalla − odch. std τ); **domyślny argument CLI = `rbf`**, AS przez `--predictor as` |
| Wewnętrzny NSGA-II | NSGA-II na (przewidywana dokładność, złożoność liczona wprost) | pop 40, 20 generacji, start = niezdominowane z archiwum, krzyżowanie dwupunktowe całkowite p = 0.9, mutacja wielomianowa całkowita η = 1, deduplikacja |
| Wybór podzbioru | najpierw najwyższa przewidywana dokładność, potem kandydaci z rzadkich obszarów osi złożoności | **GA (pop 100, 60 gen.)** wybiera dokładnie K kandydatów minimalizujących odch. std odstępów na osi f2 (archiwum niezdominowane + wybrani); **bez osobnego wyboru najlepszej dokładności** |
| Kandydaci już w archiwum | — | odrzucani przed wyborem podzbioru |
| Kodowanie | wektor całkowity | wektor całkowity (46 zmiennych OFA) |
| Dolny poziom | dostrajanie wag z supernetu | to samo |

## 3. Odstępstwa wymagane przez nasz problem

| # | Odstępstwo | Powód | Status |
|---|---|---|---|
| O-V1 | **f2 przewidywane drugim predyktorem** (ten sam mechanizm AS) w wewnętrznym NSGA-II i w wyborze podzbioru; oryginał liczy złożoność wprost | #6 (nikt nie dostaje darmowego f2) | do zatwierdzenia |
| O-V2 | Brak dolnego poziomu (supernet, dostrajanie) — ewaluacja = odczyt z benchmarku | benchmarki tablicowe/surogatowe | do zatwierdzenia (kategoria O) |
| O-V3 | Rozmiar startowy min(100, ⌊0.25·b⌋): 12 / 25 / 87 przy b = 50 / 100 / 350; K = 8 na iterację | BB-4 | zatwierdzone (reguła wspólna) |
| O-V4 | Genotyp kategoryczny kodowany liczbami 0…k−1 (jak kod autorów) | O-N3 | zatwierdzone (jak NSGA-Net) |

## 4. Decyzje do podjęcia

### V-1. Predyktor

- **a) AS z kodu autorów** ({RBF, GP, CART}, 10-krotna CV, kryterium średnia τ − odch. std τ).
  - Za: AS to deklarowany komponent metody; kod pokazuje, jak dokładnie działa; brak MLP upraszcza.
  - Przeciw: artykuł wymienia też MLP — różnica do opisania.
- **b) RBF (domyślny argument kodu).** Przeciw: artykuł przedstawia AS jako część metody; RBF to tylko ustawienie domyślne CLI.
- **c) AS z MLP (jak w artykule).** Przeciw: odchodzi od kodu.

**Rekomendacja: a).** Uwaga: 10-krotna CV przy 12 punktach (b = 50) to folds po 1–2 punkty — τ Kendalla z jednego punktu
jest niezdefiniowane. Założenie Z-V1: liczba foldów = min(10, ⌊N/3⌋), żeby każdy fold miał ≥ 3 punkty (opisać).

### V-2. Wybór podzbioru

- **a) Jak kod** (GA na odstępach osi f2, bez osobnego wyboru najlepszej przewidywanej dokładności).
- **b) Jak artykuł** (najpierw najlepsza f̂1, potem rzadkie obszary).
- **c) Kod + najlepsza f̂1 wymuszona.**

**Rekomendacja: a)** — spójnie z decyzją dla NSGA-Net (kod autorów).

### V-3. Kontrola „NSGANetV2-continuous” (B5)

W v004 była zaplanowana, niezaimplementowana. **Rekomendacja: nie robić w v005** (wszystkie metody działają na tej samej
dyskretyzacji, #31); opisać w Limitations.

## 5. Własności do sprawdzenia testami (poziom 1)

| ID | Własność |
|---|---|
| W-V1 | Start: N = min(100, ⌊0.25·b⌋) losowych, ocenionych naprawdę; potem iteracje po K = 8 ocen (ostatnia może być krótsza — K-2) |
| W-V2 | AS: pula {RBF, GP, CART}; wybór = argmax(średnia τ − odch. std τ) w CV z Z-V1; osobny AS dla f1 i f2 (O-V1) |
| W-V3 | Wewnętrzny NSGA-II: pop 40, 20 generacji, start z niezdominowanych archiwum, krzyżowanie dwupunktowe p = 0.9, mutacja wielomianowa η = 1, deduplikacja; cele = (f̂1, f̂2) |
| W-V4 | Kandydaci obecni w archiwum odrzuceni przed wyborem podzbioru |
| W-V5 | Wybór podzbioru: dokładnie K kandydatów; GA (pop 100, 60 gen.) minimalizuje odch. std odstępów na osi f̂2 |
| W-V6 | Brak dostępu do f2 nieocenionych architektur; budżet nigdy nie przekroczony |

**Test zgodności (poziom 2):** nasze `_next` i `_subset_selection` vs kod autorów (pymoo z wersji repozytorium) na tym
samym archiwum, predyktorze i ziarnie — identyczni kandydaci (test deterministyczny); AS — ten sam zwycięzca na tych
samych foldach. Całość: median HV ±2 % + TOST na NAS-HPO-Bench-II, 20 przebiegów, z podmienionym dolnym poziomem.

## 6. Do zatwierdzenia

O-V1, O-V2; V-1 (rek. a + Z-V1), V-2 (rek. a), V-3 (rek. bez ramienia ciągłego); W-V1–W-V6; test poziomu 2.

**Z-V2 (2026-10-23, z bramki `checks`):** w Adaptive Switching model, którego nie da się dopasować w którymś foldzie
(RBF z ogonem liniowym i GP wymagają co najmniej d + 1 punktów), nie jest kandydatem na zwycięzcę (wcześniej: ocena 0
za ten fold); zwycięzca dopasowywany na wszystkich danych, w razie błędu — następny kwalifikujący się. Kod autorów
zamiast tego przerywa (`assert len(inputs) > len(inputs[0])`). W `scores` (`return_scores=True`) nieudany fold ma wartość 0.0. Dotyczy tylko małych N_doe (b ≤ 4·d), np. b = 20 w próbie
determinizmu; przy b ≥ 50 N_doe = 12 > d we wszystkich przestrzeniach, ale foldy (~0.9·N) mogą być mniejsze niż d + 1 (JAHS).
