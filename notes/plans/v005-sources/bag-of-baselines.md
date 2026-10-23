# Bag of Baselines: SH-EMOA, MO-BOHB, MS-EHVI, MO-BANANAS, BULK & CUT — karta źródła

Status: **ZATWIERDZONA** (2026-10-16, autor projektu): BB-1 a (BULK & CUT usunięty, opisany w artykule), BB-2 a,
BB-3 wg tabeli, BB-4 reguła min(źródło, ⌊0.25·b⌋), BB-5 z MO-SH-BANANAS w torze MF, nazwa „EHVI”, W-BB1–W-BB8, test
poziomu 2.
**Zmiana 2026-10-16 (`library-adapters.md`, A-1 a, A-2 a):** w torze głównym EHVI realizuje ramię **qNEHVI** (BoTorch),
a MOTPE — **optuna `TPESampler`** (implementacja autora MOTPE); port hpbandster zostaje tylko w MO-BOHB (tor MF).
Decyzje wcześniejsze: #17, #18 (pełne wersje MF w torze MF, części jednowiernościowe pod poprawną nazwą w torze głównym),
#24 (MO-BANANAS z tego źródła), „dodajemy MS-EHVI i BULK & CUT”, MS-EHVI bez darmowego f2 (#6), #37 (populacje 20,
hiperparametry z oryginałów).

## 1. Źródła

- Guerrero-Viu et al., *Bag of Baselines for Multi-objective Joint Neural Architecture Search and Hyperparameter
  Optimization*, AutoML Workshop @ ICML 2021, arXiv:2105.01015 (`guerreroviu2021bagofbaselines`). **PDF nie był w repo** —
  pobrany do scratchpada; dodać do `notes/articles/NAS/MO-NAS/`.
- Kod: `https://github.com/automl/multi-obj-baselines` (przeczytany 2026-10-16): `baselines/methods/{shemoa, mobohb,
  msehvi, mobananas, bulkandcut}`, parametry uruchomień w `examples/*.py`.
- Źródła metod bazowych (do cytowania przy każdej): SMS-EMOA (Beume 2007), BOHB (Falkner 2018), MOTPE (Ozaki 2020),
  EHVI (Emmerich 2005; implementacja Ax/BoTorch), BANANAS (White 2019).

Eksperymenty w źródle: Flowers i Fashion-MNIST, przestrzeń 9 hiperparametrów (Tab. 2), cele: dokładność walidacyjna i
liczba parametrów, 24 h na przebieg, 10 seedów, maks. 25 epok.

## 2. Metody wg źródła (paper + kod)

### SH-EMOA (Alg. 1; `shemoa.py`, `member.py`)

- **SH1.** Populacja losowa; ewolucja steady-state: jeden potomek na krok, mutacja albo krzyżowanie (po 50 %).
- **SH2.** Usunięcie: NDS, w ostatnim froncie usuwany punkt o najmniejszym wkładzie do HV (HSSP z k = |F|−1).
- **SH3.** Successive halving: budżety od b_max w dół co η = 2 (kod) do b_min; liczba ewaluacji na poziomie rośnie
  ×η w dół; po przejściu na wyższy budżet cała populacja jest oceniana ponownie (leniwie, `budget.setter`).
- **SH4. Szczegóły kodu, których nie ma w artykule:** turniej k = 3 po pozycji w populacji **posortowanej skalarem
  zależnym od problemu** `(15 − f0)·f1`; punkt odniesienia HV na sztywno `[log10(1e8), 0]`; mutacja = losowanie od nowa
  **5** losowo wybranych hiperparametrów; krzyżowanie jednorodne p = 0.5.
- Parametry (`examples/shemoa.py`): populacja 100, b_min 5, b_max 25 epok, 15 000 ewaluacji.

### MO-BOHB (§3.2; `mobohb/hpbandster`)

- **MB1.** Hyperband (η = 2 domyślnie w klasie) z wyborem awansu przez NDS + HSSP.
- **MB2.** Generator konfiguracji: MOTPE (`config_generators/mobohb.py`), parametry: `num_initial_samples` 50,
  `num_candidates` 24, γ = 0.10; przestrzeń przez `search_space.as_uniform_space()`.
- Część jednowiernościowa = **MOTPE** (MO-BOHB bez Hyperbandu) — tak nazywana w torze głównym (#18).

### MS-EHVI (§3.3, Alg. 2; `msehvi.py`)

- **ME1.** Początek: 50 punktów Sobola. Potem BO z EHVI (Ax `Models.MOO`, BoTorch), jeden punkt na krok.
- **ME2.** Element „mixed surrogate”: tani cel (liczba parametrów) liczony wprost funkcją deterministyczną zamiast GP.
- **Nasz przypadek (#6, nikt nie dostaje darmowego f2):** bez ME2 metoda jest **zwykłym EHVI** z niezależnym GP na
  każdy cel — to „vanilla EHVI”, który artykuł podaje jako bazę (Tab. 1, Fig. 4). Nazwa w artykule: **EHVI**, nie MS-EHVI.

### MO-BANANAS (§3.4, Alg. 3; `mobananas.py`, `neural_predictor.py`)

- **MBa1.** Populacja startowa losowa; w pętli: trening zespołu 5 sieci (80 epok, Adam lr 0.1, MSE), sortowanie
  populacji NDS + crowding distance, mutacja `num_arch` najlepszych, wybór `select_models` kandydatów przez niezależne
  próbkowanie Thompsona, ewaluacja.
- **MBa2.** Kodowanie: wektor wartości (bez path encoding — autorzy: „not meaningful for our search space”). Mutacja:
  3 losowe hiperparametry; liczbowe — obcięty rozkład normalny, σ = (max − min)/3; **kategoryczne — losowanie od nowa**
  (gałąź `except` w `mutate`).
- **MBa3.** Szczegół kodu: cel 0 skalowany `−y/10` przed treningiem predyktora (zależne od problemu).
- Parametry: `get_MOBANANAS` — initial 20, num_arch 8, select 4; w eksperymentach artykułu wersja z SH (MO-SH-BANANAS:
  initial 10, num_arch 20, select 10, η = 3).

### BULK & CUT (§3.5, Alg. 4–5; `bulkandcut/`)

- **BC1.** Trzy fazy czasowe: inicjalizacja losowa → bulk-up (**morfizmy sieci**: wstawienie warstwy z dziedziczeniem
  wag) → cut-down (**przycinanie strukturalne + destylacja wiedzy** od rodzica). Rodzic wybierany „Paretsilon greedy”.
  Hiperparametry niearchitektoniczne: constrained BO.
- **BC2.** Metoda wymaga **trenowania sieci i operowania na ich wagach**.

## 3. Problemy przeniesienia na nasze benchmarki

| # | Problem | Dotyczy |
|---|---|---|
| T-1 | **BULK & CUT nie da się uruchomić na benchmarkach tablicowych / surogatowych** (JAHS, NAS-HPO-II, FCNet, NB201): nie ma wag do dziedziczenia, morfizmów ani przycinania; wynik sieci po destylacji nie istnieje w żadnej tabeli | BC |
| T-2 | Elementy kodu zależne od problemu Flowers: skalar `(15 − f0)·f1` w turnieju, punkt odniesienia `[log10(1e8), 0]`, liczba mutowanych hiperparametrów (5 z ~13), skalowanie `−y/10` | SH-EMOA, MO-BANANAS |
| T-3 | Rozmiary startowe (50–100) przy budżecie 50–350 | SH-EMOA, MOTPE, EHVI, MO-BANANAS |
| T-4 | Kod z 2021 r. (Ax/BoTorch, hpbandster, ConfigSpace w starych wersjach) | wszystkie |
| T-5 | Nasze zmienne są kategoryczne (#31: siatki LR/WD też jako kategorie) — gaussowska mutacja MO-BANANAS i tak losuje je od nowa | MO-BANANAS |

## 4. Decyzje do podjęcia

### BB-1. BULK & CUT (T-1)

- **a) Usunąć z v005; opisać w artykule** („requires network morphisms, pruning and distillation, which tabular and
  surrogate benchmarks cannot provide”). Kategoria O.
  - Za: uczciwe; każda wersja na benchmarku byłaby naszą adaptacją bez związku z metodą.
  - Przeciw: cofa wcześniejszą decyzję „dodajemy obie”; jeden baseline mniej.
- **b) Wersja „genotypowa”:** bulk = mutacja zwiększająca rozmiar, cut = mutacja zmniejszająca, Paretsilon greedy,
  constrained BO dla HP.
  - Przeciw: odrzuca istotę metody (dziedziczenie wag, destylacja) — własna adaptacja, której chcieliśmy unikać.
- **c) Uruchomić prawdziwy BULK & CUT na prawdziwym trenowaniu** (np. Flowers jak w źródle). Przeciw: poza naszymi
  benchmarkami i budżetem obliczeniowym; nieporównywalne z resztą tabeli.

**Rekomendacja: a).**

### BB-2. Sposób implementacji (T-4)

- **a) Wierny port kodu autorów** (SH-EMOA, MO-BANANAS: ~400 linii czystego Pythona; MOTPE/MO-BOHB: kod hpbandster z
  repozytorium autorów, dołączony do projektu); **EHVI: aktualne Ax/BoTorch** (standardowy qEHVI).
  - Za: logika 1:1 z kodem autorów; brak zależności od wersji z 2021 r.; test zgodności: nasz port vs ich kod na tym
    samym ziarnie i prostym problemie (`problems/simple_problems.py`).
  - Przeciw: port trzeba zweryfikować (poziom 2).
- **b) Uruchamianie ich kodu bez zmian** (stare wersje bibliotek w osobnym środowisku).
  - Za: zero portowania. Przeciw: konflikty zależności; hard-code'y z T-2 i tak trzeba zmienić.

**Rekomendacja: a).**

### BB-3. Elementy zależne od problemu (T-2)

Musimy je czymś zastąpić — każda zamiana to odstępstwo, opisane w artykule.

| Element | Propozycja | Uzasadnienie |
|---|---|---|
| Skalar `(15 − f0)·f1` do sortowania przed turniejem (SH-EMOA) | sortowanie populacji **NDS + wkład HV** (to samo kryterium, którego metoda używa przy usuwaniu) | zgodne z logiką metody; bez stałych problemu |
| Punkt odniesienia HV `[log10(1e8), 0]` | punkt odniesienia z protokołu metryk (wspólny, A12), w znormalizowanej przestrzeni celów | wspólne dla wszystkich metod |
| Mutacja 5 z ~13 hiperparametrów (SH-EMOA), 3 z ~13 (MO-BANANAS) | **ten sam ułamek** zaokrąglony w górę: SH-EMOA ⌈0.38·n⌉ (JAHS 4, NAS-HPO-II 4, FCNet 4, NB201 3); MO-BANANAS ⌈0.23·n⌉ (3, 2, 3, 2) | zachowuje intensywność mutacji ze źródła |
| Skalowanie `−y/10` (MO-BANANAS) | standaryzacja każdego celu (średnia 0, odchylenie 1) w zbiorze treningowym | odpowiednik bez stałej problemu |

**Rekomendacja:** jak w tabeli.

### BB-4. Rozmiary startowe (T-3)

Reguła wspólna (precedens: SMAC #19, Bartnik B-2): **min(wartość ze źródła, ⌊0.25·b⌋)**; populacja SH-EMOA = 20 (#37).

| Metoda | Źródło | b = 50 | b = 100 | b = 350 |
|---|---|---|---|---|
| EHVI → qNEHVI | wg `library-adapters.md` §3: min(2(d+1), ⌊0.25·b⌋) | — | — | — |
| MOTPE (optuna) | wg `library-adapters.md` §3: min(10, ⌊0.25·b⌋) | 10 | 10 | 10 |
| MO-BANANAS | 20 | 12 | 20 | 20 |
| SH-EMOA | 100 → 20 (#37) | 12 | 20 | 20 |
| MO-BOHB (tor MF) | `num_initial_samples` 50 (`get_MOBOHB(init=True)`: pierwsza iteracja — losowe konfiguracje na max budżecie); dodane 2026-10-20 (test poziomu 2 wykrył brak w porcie; decyzja autora a) | 12 | 25 | 50 |

- Za: jedna reguła dla wszystkich; zawsze ≥ 75 % budżetu na wyszukiwanie. Przeciw: przy b = 50 odchodzi od źródła.

**Rekomendacja: przyjąć.**

### BB-5. Tor główny vs MF

Zgodnie z #17/#18: tor główny — **SH-EMOA bez SH** (nazwa: „SMS-EMOA-style steady-state EA, SH-EMOA without successive
halving”), **MOTPE**, **EHVI**, **MO-BANANAS** (bez SH); tor MF — **SH-EMOA**, **MO-BOHB**, **MO-SH-BANANAS** z pełnym
SH/HB (b_min/b_max/η ze źródła przeskalowane do epok benchmarku; szczegóły w karcie toru MF). Do potwierdzenia, że
MO-SH-BANANAS wchodzi do toru MF (dotąd go nie było).

## 5. Własności do sprawdzenia testami (poziom 1)

| ID | Metoda | Własność |
|---|---|---|
| W-BB1 | SH-EMOA | Steady-state: populacja stała; usuwany punkt należy do ostatniego frontu NDS i ma najmniejszy wkład HV |
| W-BB2 | SH-EMOA (MF) | Liczby ewaluacji na budżet zgodne z `get_budgets`; po zmianie budżetu cała populacja oceniona ponownie |
| W-BB3 | SH-EMOA | Mutacja zmienia dokładnie ⌈0.38·n⌉ losowych zmiennych (losowanie od nowa); krzyżowanie jednorodne p = 0.5; turniej k = 3 |
| W-BB4 | MOTPE | γ = 0.10, 24 kandydatów, rozdział dobrych/złych wg reguły MOTPE (NDS + HV); po starcie losowym |
| W-BB5 | EHVI | Niezależny GP na każdy cel (f2 też modelowane — #6); akwizycja qEHVI; 1 punkt na krok |
| W-BB6 | MO-BANANAS | Zespół 5 sieci, 80 epok; sortowanie NDS + crowding; Thompson niezależny; `select` ewaluacji na iterację |
| W-BB7 | wszystkie | Rozmiar startowy wg BB-4; budżet nigdy nie przekroczony (reguła K-2) |
| W-BB8 | wszystkie | Brak dostępu do f2 poza prawdziwą ewaluacją |

**Test zgodności (poziom 2):** nasz port vs kod autorów na `simple_problems.py` (te same ziarna, ten sam budżet):
SH-EMOA, MO-BANANAS, MOTPE — median HV ±2 % + TOST, 20 przebiegów; EHVI — porównanie z Ax `Models.MOO` (ten sam
interfejs). Kryterium zapisane przed testem.

## 6. Do zatwierdzenia

BB-1 (rek. a — usunięcie BULK & CUT, zmiana wcześniejszej decyzji), BB-2 (rek. a), BB-3 (tabela), BB-4 (reguła),
BB-5 (w tym MO-SH-BANANAS w torze MF), nazwa „EHVI” zamiast „MS-EHVI”, W-BB1–W-BB8, test poziomu 2.
