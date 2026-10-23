# Adaptery bibliotek: SMAC3-ParEGO, MOEA/D, NSGA-III, MOTPE (optuna), qNEHVI, qParEGO, Vizier, RS — karta źródła

Status: **ZATWIERDZONA** (2026-10-16, autor projektu): A-1 a (qNEHVI zamiast EHVI z Ax), A-2 a (MOTPE z optuny), §3, §4, W-A1–W-A6, poziom 2.
Decyzje wcześniejsze: #19 (SMAC3 `n_trials` = budżet), #20 i #21 (MOEA/D: deduplikacja, operatory kategoryczne — N),
#30 (GP tylko b = 50/100, osobna tabela), #6, #35, #37, BB-4 (rozmiar startowy min(źródło, ⌊0.25·b⌋)), K-2.
Zasada: metoda = biblioteka z ustawieniami domyślnymi; adapter ask–tell nie zmienia logiki biblioteki. Każde
ustawienie inne niż domyślne — w tabeli §3 z powodem.

## 1. Źródła (metoda → publikacja → implementacja)

| Ramię | Publikacja | Implementacja (wersja z v004) |
|---|---|---|
| SMAC3-ParEGO | Lindauer et al. 2022 (SMAC3); Knowles 2006 (ParEGO) | smac 2.4.1, `HyperparameterOptimizationFacade` + `ParEGO` |
| MOEA/D | Zhang & Li 2007 | pymoo 0.6.2 `MOEAD` |
| NSGA-III | Deb & Jain 2014 | optuna 4.9.0 `NSGAIIISampler` |
| MOTPE | Ozaki et al. 2020/2022 | optuna 4.9.0 `TPESampler` (dla > 1 celu = MOTPE, implementacja autorów MOTPE) |
| qNEHVI | Daulton et al. 2021 | botorch 0.18.1, `qLogNEHVI` |
| qParEGO | Daulton et al. 2020 | botorch 0.18.1, `qLogNEI` na losowej skalaryzacji Czebyszewa |
| Vizier | Song et al. 2024 (OSS Vizier, GP-UCB-PE) | google-vizier 0.1.24, `VizierGPUCBPEBandit` |
| RS | Bergstra & Bengio 2012 | własna (jednostajnie na poprawnych genotypach) |

PDF-ów publikacji brak w repo — do dodania przed etapem C (cytowania).

## 2. Dublowania z Bag of Baselines (do rozstrzygnięcia)

### A-1. EHVI (karta BoB) vs qNEHVI (v004)

Oba to akwizycja hiperobjętościowa na GP; przy deterministycznym benchmarku qNEHVI ≈ qEHVI (różnią się obsługą szumu).

- **a) Jedno ramię: qNEHVI (BoTorch `qLogNEHVI`)**, w artykule jako „EHVI-based BO (qNEHVI)”; BoB cytowane jako źródło
  wyboru EHVI dla joint NAS+HPO.
  - Za: jedna aktualna, utrzymywana implementacja; nie dublujemy prawie identycznej metody; Ax `Models.MOO` z BoB i tak
    wywołuje BoTorch.
  - Przeciw: zmienia zatwierdzoną kartę BoB (EHVI przez Ax).
- **b) Dwa ramiona.** Przeciw: dwa prawie identyczne wyniki; dwa razy koszt GP (#30).

**Rekomendacja: a)** (karta BoB: EHVI → qNEHVI, BB-2 dla EHVI bez zmian w duchu — aktualne BoTorch).

### A-2. MOTPE (BoB, hpbandster) vs TPE (optuna)

Optuna `TPESampler` przy dwóch celach to MOTPE (implementacja Ozakiego, autora MOTPE). BoB w torze jednowiernościowym
dałby MOTPE z hpbandster (port autorów BoB).

- **a) Jedno ramię: MOTPE z optuny**; MO-BOHB (tor MF) zostaje na kodzie BoB.
  - Za: implementacja autora metody; brak dubla. Przeciw: zmienia zatwierdzoną kartę BoB (MOTPE z hpbandster).
- **b) Dwa ramiona.** Przeciw: dubel.

**Rekomendacja: a).**

## 3. Ustawienia (domyślne, chyba że podano powód)

| Ramię | Ustawienia v005 | Odstępstwo od domyślnych i powód |
|---|---|---|
| SMAC3-ParEGO | HPO facade domyślna, `deterministic=True`, **`n_trials = b`** | #19: przy 10⁷ projekt początkowy = 10·d (b ≤ 100 = czysty Sobol); przy `n_trials = b` limit 0.25·b działa (= BB-4) |
| MOEA/D | N = 20 (#37), Tchebycheff, `prob_neighbor_mating` 0.9; **operatory kategoryczne**: krzyżowanie jednorodne + mutacja „random reset” p = 1/n; **T = ⌈0.2·N⌉ = 4** sąsiadów; **deduplikacja z ponownym losowaniem** | #21: SBX/PM na indeksach narzuca porządek kategoriom; #20: przerywanie przed budżetem; T = 20 przy N = 20 to brak sąsiedztwa — zachowany stosunek T/N = 0.2 z Zhang & Li (N = 100, T = 20) |
| NSGA-III | optuna domyślne, `population_size` 20 | #37 |
| MOTPE | optuna domyślne (`n_ei_candidates` 24, `multivariate=False`), `n_startup_trials` = min(10, ⌊0.25·b⌋) = 10 | BB-4 (bez zmiany dla b ≥ 40) |
| qNEHVI, qParEGO | `MixedSingleTaskGP` (wszystkie wymiary kategoryczne), Standardize, 128 próbek QMC; **projekt początkowy min(2(d+1), ⌊0.25·b⌋)**: 12 / 14–22 przy b = 50 / 100 (2(d+1): JAHS 22, FCNet 20, NAS-HPO-II 18, NB201 14); akwizycja maksymalizowana po puli (1024 losowych poprawnych + sąsiedzi 1-zmiennej frontu) | BB-4; pula zamiast `optimize_acqf_mixed`, bo optymalizator BoTorch nie zna ograniczenia Validity (#33) — opisane |
| Vizier | domyślne (`num_seed_trials=1`, trust region) | — |
| RS | jednostajnie na poprawnych genotypach, bez duplikatów | #33, #35 |

GP (qNEHVI, qParEGO, Vizier): tylko b = 50 i 100, osobna tabela (#30).

## 4. Wspólne zasady adaptera ask–tell

- Duplikat: zgłaszany bibliotece z wartością z H_t (nie zużywa budżetu, #35); niepoprawny genotyp: wg #33 (zgłaszany
  jako błąd / najgorsza wartość — jak biblioteka to obsługuje); f2 tylko z prawdziwej ewaluacji (#6).
- **Asercja zużycia budżetu:** przebieg, który kończy się przed b ewaluacjami, jest błędem (chyba że przestrzeń
  wyczerpana) — dotyczy szczególnie MOEA/D (#20) i NSGA-III (generacje pełne duplikatów).

## 5. Własności do sprawdzenia testami (poziom 1)

| ID | Własność |
|---|---|
| W-A1 | Konfiguracja każdej biblioteki = tabela §3 (test odczytuje obiekt biblioteki i porównuje parametry) |
| W-A2 | SMAC3: rozmiar projektu początkowego = min(10·d, ⌊0.25·b⌋) |
| W-A3 | MOEA/D: operatory kategoryczne (żadna wartość spoza 0…k−1, brak zaokrągleń), T = 4, pełne zużycie budżetu |
| W-A4 | GP: projekt początkowy wg §3; pula akwizycji zawiera tylko poprawne, nieocenione genotypy |
| W-A5 | Adapter: ta sama sekwencja propozycji co natywna pętla biblioteki na tym samym ziarnie (optuna, SMAC3 — deterministycznie) |
| W-A6 | Duplikaty i niepoprawne nie zużywają budżetu; budżet nigdy nie przekroczony |

**Poziom 2:** dla bibliotek = W-A5 (adapter nie zmienia metody). MOEA/D z własnymi operatorami — porównanie z pymoo
MOEA/D na problemie ciągłym z tymi samymi wagami i sąsiedztwem (operatory podmienione na SBX/PM): identyczna trajektoria.

## 6. Do zatwierdzenia

A-1 (rek. a — qNEHVI zamiast EHVI z Ax; zmiana karty BoB), A-2 (rek. a — MOTPE z optuny; zmiana karty BoB), tabela §3
(w tym MOEA/D: operatory kategoryczne i T = 4), §4, W-A1–W-A6, poziom 2.
