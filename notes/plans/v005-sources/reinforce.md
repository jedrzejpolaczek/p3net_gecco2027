# REINFORCE z trzema nagrodami wielokryterialnymi — karta źródła

Status: **ZATWIERDZONA** (2026-10-16, autor projektu): R-1 a, R-2 a (Z-R1), R-3 a (Z-R2), R-4 a, R-5 a, R-6 (ADC,
skalowanie, Z-R3), W-R1–W-R8, test poziomu 2.
Decyzje wcześniejsze (`v005-decisions.md`, #24): trzy warianty nagrody — MnasNet, MONAS, Chen et al. 2020; w artykule
wyjaśnić pochodzenie (literatura nie porównuje tych nagród w HV/IGD+).

## 1. Źródła

| Element | Źródło | Plik (scratchpad → do `notes/articles/NAS/`) |
|---|---|---|
| Algorytm REINFORCE | Williams 1992 | — |
| Implementacja referencyjna dla benchmarków | Dong & Yang, NAS-Bench-201, ICLR 2020, App. (`dong2020nasbench201`); kod `D-X-Y/AutoDL-Projects/exps/NAS-Bench-201-algos/reinforce.py` | arXiv 2001.00326 |
| Współczynnik uczenia | Ying et al., NAS-Bench-101, ICML 2019, App. S2/S4 (`ying2019nasbench101`) | arXiv 1902.09635 |
| Nagroda 1 | Tan et al., MnasNet, CVPR 2019, Eq. 2–3 (`tan2019mnasnet`) | arXiv 1807.11626 |
| Nagroda 2 | Hsu et al., MONAS, 2018, Eq. 3 (`hsu2018monas`) | arXiv 1806.10332 |
| Nagroda 3 | Chen, Zhou, Trimponias, Li, *Multi-objective NAS via Non-stationary Policy Gradient*, 2020, §4.2 ADC, §4.3 temperatura (`chen2020mononstationary`) | arXiv 2001.08437 |

Dlaczego karta (R1 §10): w v004 nagroda = −Czebyszew z **nową losową wagą przy każdej ewaluacji** (ten sam punkt
dostawał różne nagrody), lr 0.1 bez źródła.

## 2. REINFORCE wg implementacji NAS-Bench-201

- **R1.** Polityka faktoryzowana: niezależny softmax na każdą zmienną (logity startowe 10⁻³·N(0,1)); bez kontrolera RNN.
- **R2.** Jedna architektura na krok: losowanie z polityki → ewaluacja → nagroda r → aktualizacja.
- **R3.** Bazowa: wykładnicza średnia krocząca nagród, momentum 0.9, **aktualizowana przed** liczeniem przewagi
  (`baseline.update(r)`, potem `loss = −log π · (r − baseline)`).
- **R4.** Optymalizator Adam na logitach. LR: NAS-Bench-201 testuje {0.01, 0.02, 0.05, 0.1, 0.2, 0.5} „following Ying
  et al.”, ale **wartości wybranej nie ma w tekście** („the learning date is set as .” — puste w PDF). Ying et al.:
  **0.5** (App. S2).

## 3. Nagrody wg źródeł

Oznaczenia: a = dokładność (większa lepsza), c = koszt (f2, mniejszy lepszy).

- **MnasNet (Eq. 2–3):** R = a · (c / T)^w, w = α jeśli c ≤ T, w = β w p.p.; wersja „soft”: **α = β = −0.07**; T =
  docelowy koszt (stała aplikacji).
- **MONAS (Eq. 3, „mixed reward”):** R = α · a − (1 − α) · c, a i c **znormalizowane do [0, 1]**; w artykule
  **α = 0.25 i α = 0.75** (dwa przebiegi).
- **Chen et al. — ADC (Eq. 3, Alg. 2):** nagroda zależna od bieżącego frontu P_f: dla x niezdominowanego
  R = tanh((N(P_f) + N_≻(x; P_f)) / C), dla zdominowanego R = −tanh((N_≺(x; P_f) + ρ(x; P_f, ε)) / C) (N_≻ — ile
  punktów frontu x dominuje, N_≺ — ile dominuje x, ρ — liczba punktów frontu w promieniu ε). Front aktualizowany po
  każdej ewaluacji. Eksploracja: temperatura Boltzmanna z kosinusowym spadkiem i restartami, T_max = 25 → T_min = 1,
  okres 1200 kroków (przy 6000 krokach). Drugi wariant Chen et al. (ADF — wyżarzanie docelowego f2) wymaga 1500 kroków
  rozgrzewki.

## 4. Odstępstwa i decyzje

### R-1. Kontroler

- **a) Polityka faktoryzowana jak NAS-Bench-201** dla wszystkich trzech nagród (źródła nagród używają RNN/LSTM i PPO
  (MnasNet) — wspólne odstępstwo, opisane).
  - Za: standardowy baseline REINFORCE na benchmarkach tablicowych; nagroda jest jedyną różnicą między wariantami.
  - Przeciw: nie odtwarza kontrolerów źródeł nagród.

**Rekomendacja: a).**

### R-2. Współczynnik uczenia

- **a) 0.5** (Ying et al.; NAS-Bench-201 deklaruje, że idzie za nimi). Założenie Z-R1, opisane.
- **b) 0.1** (v004, bez źródła). Przeciw: brak źródła.

**Rekomendacja: a).**

### R-3. Skale celów (wspólne dla trzech nagród)

Nagrody wymagają a ∈ [0, 1] (MnasNet: iloczyn; MONAS: [0, 1] wprost). FCNet ma f1 = MSE (nie dokładność), koszty mają
różne jednostki.

- **a) Normalizacja min–max bieżąca** (po ocenionych dotąd punktach) obu celów do [0, 1]; a = 1 − f1_norm,
  c = c_norm (MONAS); MnasNet: a = 1 − f1 dla przestrzeni klasyfikacyjnych (błąd w [0, 1]), 1 − f1_norm dla FCNet;
  c w oryginalnych jednostkach względem T.
  - Za: MONAS normalizuje wprost; brak wiedzy spoza przebiegu. Przeciw: nagroda tego samego punktu zmienia się, gdy
    rosną min/max (mniej niż losowa waga w v004, ale nadal).
- **b) Normalizacja stałymi zakresami benchmarku** (min/max z całej tabeli). Przeciw: wiedza spoza budżetu.

**Rekomendacja: a)** (założenie Z-R2, opisane).

### R-4. Cel T w MnasNet

- **a) T = mediana f2 w benchmarku** (jedna liczba na przestrzeń, jak „target latency” podawany przez użytkownika).
  - Za: odpowiada roli T w źródle (stała aplikacji). Przeciw: wiedza o benchmarku (jedna liczba).
- **b) T = bieżąca mediana f2 ocenionych.** Za: bez wiedzy zewnętrznej. Przeciw: T się zmienia — tego nie ma w źródle.

**Rekomendacja: a)** — T jest w źródle parametrem użytkownika, nie wiedzą o kandydacie.

### R-5. MONAS: α

- **a) Dwa ramiona: α = 0.25 i α = 0.75** (jak w źródle). Za: wierne; benchmark tani. Przeciw: dodatkowe ramię.
- **b) Jedno ramię, α = 0.5.** Przeciw: wartości nie ma w źródle.

**Rekomendacja: a)** (tor główny: α = 0.75, suplement: α = 0.25 — albo oba w suplemencie; do decyzji przy tabelach).

### R-6. Chen et al.: ADC czy ADF; skalowanie do budżetu

- **ADC** (rekomendacja): wprost nagradza powiększanie frontu („śledzi cały front”, jak ustaliliśmy w #24); ADF
  wymaga 1500 kroków rozgrzewki — niewykonalne przy b ≤ 350.
- Skalowanie: okres temperatury **0.2·b** (1200/6000 jak w źródle), T_max = 25, T_min = 1; ε = 0.1 w znormalizowanej
  przestrzeni celów (źródło: 0.1M parametrów — jednostka problemu); **C nieodczytane z tekstu** — założenie Z-R3: C
  dobrane tak, by tanh nasycał się przy połowie oczekiwanej liczności frontu, wartość zapisana przed uruchomieniem.

## 5. Własności do sprawdzenia testami (poziom 1)

| ID | Własność |
|---|---|
| W-R1 | Polityka faktoryzowana; logity startowe ~10⁻³·N(0,1); jedna próbka na krok |
| W-R2 | Bazowa EMA 0.9 aktualizowana przed przewagą; strata = −log π · (r − b); Adam, lr 0.5 |
| W-R3 | MnasNet: R = a·(c/T)^−0.07 dla obu gałęzi; T stałe w przebiegu |
| W-R4 | MONAS: R = α·a − (1−α)·c na wartościach w [0, 1] |
| W-R5 | ADC: wartości R zgodne z Eq. 3 na ręcznie policzonych przykładach; front aktualizowany jak w Alg. 2 |
| W-R6 | ADC: temperatura wg wzoru kosinusowego z restartem co 0.2·b kroków |
| W-R7 | Duplikat (architektura już oceniona) dostaje nagrodę z H_t i nie zużywa budżetu; polityka i tak jest aktualizowana |
| W-R8 | Budżet nigdy nie przekroczony |

**Test zgodności (poziom 2):** REINFORCE z nagrodą = dokładność (jednokryterialnie) vs `reinforce.py` NAS-Bench-201 na
NB201, te same ziarna: rozkład najlepszej dokładności walidacyjnej po 100 i 500 krokach, ±2 % + TOST, 100 przebiegów.
Nagrody — tylko poziom 1 (brak kodu referencyjnego).

## 6. Do zatwierdzenia

R-1 a, R-2 a (Z-R1), R-3 a (Z-R2), R-4 a, R-5 a, R-6 (ADC + skalowanie + Z-R3), W-R1–W-R8, test poziomu 2. PDF-y źródeł
dodać do `notes/articles/NAS/`.

## Poziom 3 — zbieżność polityki (2026-10-23, decyzja autora a)

Na wszystkich przestrzeniach REINFORCE kończy się regułą #36 (10 000 kolejnych duplikatów) po 38 (NB201), 49 (NAS-HPO-II),
71–88 (FCNet, JAHS) z 350 ewaluacji: polityka z Adamem lr 0.5 zbiega do jednej architektury, a duplikaty nie kosztują
budżetu (#35; w kodzie NAS-Bench-201 kolejne próbki tej samej architektury zużywają budżet). **Zostaje bez zmian**
(wierność kodowi + wspólne reguły). **Limitations / tekst:** REINFORCE wykorzystuje ~40–90 z 350 ewaluacji — wynik jest
skutkiem zbieżności polityki, nie budżetu.
