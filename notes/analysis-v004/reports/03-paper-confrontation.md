# 03 — Konfrontacja wyników v004 z artykułem v0.0.3, checklistą, notatkami i literaturą

Przebieg 3 z `notes/analysis-v004/PROMPTS.md`. Materiał do dyskusji o aktualizacji artykułu; artykułu nie edytowano.
Odnośniki: **R1 §x** = `01-implementation-audit.md`, **R2 §x / W#** = `02-results-analysis.md` (sekcja / wniosek z listy R2 §7).
Siła dowodu (1)–(4) jak w CONTEXT.md.

> **Korekta 2026-10-16 (A13):** pierwotnie raport zakładał (za `CONTEXT.md`), że praca Bartnik nie jest w repo. Jest
> (`notes/articles/NAS/MO-NAS/Evolutionary optimization of deep neural.pdf`). Poprawione: §1 B6, §4 (wiersz Bartnik), §7 Q9; ocena
> wierności rekonstrukcji — R1 §4.2.

## Stan sekcji

| # | Sekcja | Stan |
|---|---|---|
| 0 | Dodatkowe obliczenia w tym przebiegu | zrobione |
| 1 | Checklista B1–B10 | zrobione |
| 2 | Twierdzenia artykułu v0.0.3 | zrobione |
| 3 | `notes/p3net-improvements.md` | zrobione |
| 4 | Literatura | zrobione |
| 5 | Możliwe narracje | zrobione |
| 6 | Brakujące analizy i eksperymenty | zrobione |
| 7 | Pytania do autora | zrobione |

---

## 0. Dodatkowe obliczenia w tym przebiegu

Jedno nowe porównanie (poza raportami 1–2), na danych `per_run.csv` z R2, MWU dwustronny **bez korekty** (para porównań wybrana
pod konkretną tezę odłożonego tekstu `_parked/przewozniczek_isolation.tex`), δ dodatnie = pierwsze ramię lepsze:

| Para | NB201 b=100 | NB201 b=350 | główne 1–30 | główne 31–60 | FCNet |
|---|---|---|---|---|---|
| M9 (`przewozniczek_p3elympus`) vs `bartnik_p3` | δ −0.13, p=0.38 | **δ +0.51, p=0.0007** | 2+/0−/14· | 1+/1−/14· | 3+/0−/13· |
| **M10 (`canonical_p3_scalar_fihc`) vs `bartnik_p3`** | δ −0.03, p=0.87 | **δ +0.56, p=0.0002** | 1+/1−/14· | 1+/1−/14· | 6+/0−/10· |
| **M9 vs M10** (izolacja eLyMPuS) | δ −0.12, p=0.41 | δ −0.05, p=0.75 | 1+/0−/15· | 0+/0−/16· | 0+/0−/16· |
| M8 (`p3net_elympus`) vs kontrola M7 | — | — | 0+/1−/15· | 0+/2−/14· | 0+/0−/16· |

Wniosek (siła (1) dla NB201 b=350 — interwencja jednoosiowa, choć eksploracyjne seedy): **przewagę M9 nad `bartnik_p3` na NB201 przy 350
w całości odtwarza M10, czyli zwykły FIHC po skalarnym f1 bez eLyMPuS**; eLyMPuS nie dokłada nic (M9 ≈ M10 we wszystkich 50 komórkach).

---

## 1. Checklista `v004-audit-checklist.md`, B1–B10

### B1. Czy null to cecha P3, czy naszego wariantu piramidy?

- **Gałąź, która się zrealizowała: żadna z dwóch przewidzianych w czystej postaci — null S4 zniknął.** S5 (`cascade`) separuje się od RS
  w 10/16 komórek (31–60), 8/16 (1–30), 11/16 (FCNet), nigdy gorszy (R2 §2.1, W1). Kanoniczne P3 też się separują: `bartnik_p3` 7/16,
  M9 7/16, M10 7/16 (31–60, rodzina vsRS; R2 summaries). Na NB201 przy 350 separują się S5, M9, M10, nie S4 i nie `bartnik_p3` (R2 §2.8).
- Diagnoza „bootstrap”: udział bootstrapu S5 przy 350 = 18–45% (główne), 55–60% (FCNet), vs S4 ~91% — `cascade` go zmienił (R2 §3.1). Ale:
  S4′ (0.6% bootstrapu) jest równie dobry, a wewnątrz S5 więcej bootstrapu koreluje z lepszą jakością (W6) — prosta teza „losowy
  bootstrap zjada budżet ⇒ null” jest **częściowo** wsparta (interwencje między ramionami) i **osłabiona** wewnątrz ramienia.
- Ważne zastrzeżenie (R1 §3.1, §4.1): S5 „cascade” to nie kaskada P3, a kanoniczne ramiona to rekonstrukcje z FIHC jednoprzebiegowym i
  wnętrzem na surogacie — kontrast „nasza piramida vs piramida P3” nie jest czysty.
- **Co zmienić w tekście:** usunąć „P3's pyramid” jako przyczynę nulla; pisać „our level-growth schedule (S4)”; null dotyczył S4, nie
  P3Net w ogóle. Sekcja 4 „Following P3, … 2^k” → „Unlike canonical P3, our levels have target sizes 2^(k+1)…” (R1 §3.1, R1 §14 pkt 3).
  Ujednolicić opis reguły wzrostu (HV poziomu przy jednej „najlepszej” obserwacji partii, R1 §3.1). Udział bootstrapu S5 podawać obok S4.

### B2. Surogat względny vs absolutny

- **Zrealizowało się: S5 ≥ `p3_absolute_cascade`** (3+/0−/13· na 31–60; 1/0/15 na 1–30; 0/0/16 FCNet; R2 §2.4, W12) — S5 lepszy lub równy,
  nigdy gorszy. **RF (M7) ≈ S5** na głównych (1/0/15), mimo ~10× dokładniejszego f1 (R2 §3.3, W13). **M8 vs kontrola**: 0+/1−/15 i
  0+/2−/14 (kontrola lepsza w 3 komórkach), FCNet 0/0/16 (§0).
- Dlaczego to nie jest „null z konstrukcji”: S5 i wariant absolutny różnią się kotwiczeniem predykcji, regułą akceptacji (pierwszy krok
  real-vs-pred w wariancie absolutnym) i efektywną regularyzacją (R1 §3.2). Przewaga S5 to przewaga tych trzech rzeczy, nie linkage.
- Punkt „sprawdzić w kodzie, czy w₁ = −w₂”: **sprawdzone — model wychodzi antysymetryczny**, formuła artykułu jest zgodna z zachowaniem
  (R1 §3.2 pkt 3).
- Nazwa „linkage-aware”: **ograniczenie par jest puste** — korzeń drzewa w FOS ⇒ wszystkie pary H_t w treningu, predykcja niezależna od F
  (R1 §3.2 pkt 1–2). Przemianowanie jest konieczne, nie opcjonalne.
- **Co zmienić:** opisać δ̂ jako „globalny addytywny Ridge trenowany na parach z H_t, zakotwiczony w prawdziwym f1 przodka”; S5 vs
  absolutny — „kotwiczenie i reguła akceptacji pomagają”, a nie „relatywność/linkage pomaga”. RF ≈ S5 ⇒ osłabić „The surrogate is additive …”
  jako wyjaśnienie na przestrzeniach głównych; na FCNet addytywność na surowym MSE jest wyjaśnieniem dobrze wspartym (R2 §3.0a, W16).

### B3. Darmowe f2 z wyroczni

- **Zrealizowało się: różnica pomijalna na 4 przestrzeniach głównych** — `inherited_cost` ≈ S5 w 16/16, także na NHB (różnica IGD+
  +0.0005; R2 §2.3, W10). Siła (1) na tych przestrzeniach.
- **Na FCNet nierozstrzygnięte** — wariant nie był uruchomiony (R1 §3.3).
- Inne ramiona nie dostają f2 kandydatów (R1 H7): asymetria istnieje, ale na głównych nie tłumaczy wyników.
- **Co zmienić:** Fairness controls — jedno zdanie o hooku, wynik `inherited_cost`, rozróżnienie JAHS (rozmiar liczalny) vs NHB/FCNet
  (czas z tabeli), adnotacja „na FCNet nieizolowane”.

### B4. „Nie odróżnia się od RS” ≠ „zachowuje się jak RS”

- Sprawa nieaktualna dla S5 (S5 > RS w 10/16). **Dotyczy S4** (0/16 w 1–30, 4/16 w 31–60) i innych ramion (MO-BOHB 0/16, REINFORCE 0/16,
  SMAC3 przy b ≤ 100 na JAHS, R2 §6).
- **Co zmienić:** usunąć „behaves as random search does” i argument Spearman ρ=0.980 (n=144). Dla ramion bez separacji: „not distinguishable
  at n=30”; jeśli potrzebne „≈ RS” — TOST z jawnym marginesem (R2 §6, moc).

### B5. Baseline'y i ich nazwy

- **SH-EMOA i MO-BOHB** jednowiernościowe (R1 §7). S5 bije MO-BOHB w 11/16 (31–60), a MO-BOHB nie bije RS w żadnej komórce (R2 §2.1, §3.4)
  ⇒ wygrane z MO-BOHB **nie** są wygranymi z ustalonym baselinem. SH-EMOA jest wśród najlepszych ramion (bije S5 w 3/16).
- **NSGANetV2**: `model_factory` = `LinearRegression` (OLS), selekcja po samym f̂1, bez f2 (R1 §6.2). S5 vs NSGANetV2: 3+/0−/13 (31–60).
- `nsganetv2_continuous` poza v004 — zdanie w Limitations zostaje.
- **Cytowania**: SH-EMOA → Guerrero-Viu et al. (nie `beume2007smsemoa`); MO-BOHB → Guerrero-Viu et al. (nie `falkner2018bohb`) (R1 §7).
- Dochodzą nowe: NSGA-Net = NSGA-II bez turnieju i BOA; P3-alone = płaska FIFO, jednokryterialna; SMAC3 przy b ≤ 100 = Sobol (potwierdzone
  wynikami, W21); MOEA/D nie zużywa budżetu na FCNet; BANANAS bez path encoding (R1 §10, §14).

### B6. Eksperymenty izolujące i rodzina benchmarków

- **NB201**: mediany 0.985–0.996, przy b=100 nikt ≠ RS (poza gorszym MO-LS) — sufit (R2 §2.8, W24). „showing the null survives” — w v004
  nieprawdziwe dla S5 (S5 > RS przy 350).
- **FCNet (Q5) niezgodny z Q1 co do pozycji S5**: na głównych S5 jest 5., na FCNet 13. z 25, przegrywa z 10 ramionami, w tym z całą rodziną
  kanonicznego P3 (R2 §2.5, W3). Gałąź „niezgodny → wiadomość o zależności od benchmarku” zrealizowała się, z konkretnym mechanizmem:
  surogat liniowy na surowym MSE jest na FCNet ślepy (R² ≈ 0, MCC decyzji 0.17; W16).
- Plateau we wczesnym budżecie: na FCNet krzywe anytime nie wykazują wczesnego plateau (slice: S5 0.062 → 0.011; R2 §4.1) — argument za
  „sufitem” nie przenosi się na FCNet.
- „documented to win” o Bartnik — doprecyzować (*korekta 2026-10-16:* praca jest w repo, R1 §4.2). W pracy wygrywają warianty
  probabilistyczne (MO-PSA) i MLP; odtworzony przez nas wariant deterministyczny RF **nie** bije MO-LS na energii inferencji
  (Tabela 7.1: HV 139.89 vs 140.23). W v004 `bartnik_p3` na NB201 nie separuje się od RS.
- Limitations: FCNet z konwersji Syne Tune, interpolowany czas, MLP 2-warstwowe — dopisać.

### B7. Diagnostyka surogatu

- **Precyzja vs base rate** (R2 §4.3): S5 na NHB 0.78 vs base 0.59, MCC 0.44, bal. acc 0.72; na FCNet 0.64 vs 0.57, MCC 0.17. Liczba „0.498”
  z v0.0.3 była precyzją S4 bez base rate; w v004 trzeba podawać MCC/balanced accuracy. JAHS — brak etykiet (posthoc nieuruchomiony).
- **Jednostki MSE**: f1 w punktach procentowych błędu (JAHS, NHB, NB201), MSE (FCNet). MAE S5 na wybranych kandydatach 5.1 p.p. (JAHS), 11.0
  (NHB) — R2 §3.3.
- **Proxy interakcji**: R2 §3.0a mierzy addytywność na bezstronnej próbce RS dla 9 przestrzeni (R² addytywny vs z interakcjami). Kolejność
  z v0.0.3 (FMN < C10 < CRC < NHB przyrost R²) **nie** odtwarza się: przyrosty R² z interakcjami parami 0.39 (FMN), 0.50 (C10), 0.39 (CRC), 0.40 (NHB) (inna definicja niż v0.0.3: wszystkie pary, nie tylko pary z krawędzią)
  na surowym f1 — wszystkie duże i podobne; akapit „This is exactly the order…” usunąć.
- `p3net_surrogate_interactions` nie jest w v004 — usunąć zdanie albo oznaczyć jako v0.0.3.

### B8. Ścieżka projektowa i twierdzenia przyczynowe

- s2: S1→S2→S3→S4 0/16 w każdym przejściu (R2 §2.2, W8) — „warm start lowers it only modestly” i wpływ świeżego f2/Ridge: brak
  istotnych zmian; mediany δ dodatnie przy S1→S2 (+0.12) i S3→S4 (+0.20), ujemne przy S2→S3 (−0.06).
- **„fixed constant regressed severely” (S4′) upada**: S4′ lepszy od S4 w 6/16, nigdzie gorszy (W7).
- `p3_absolute` (stary) vs `p3_absolute_cascade`: różnią się OLS vs Ridge, f2 dziedziczony vs świeży i `cascade` (R1 §5.2) — to nie jest
  czysta interwencja na piramidzie; tekst „intervention … moved onto the same pyramid” trzeba przeformułować lub usunąć.
- s4: 16 wariantów — tylko `grow_on_stall` istotnie gorszy (8/16) i `kappa1_thr0` lepszy w 1 komórce (W9, W11) ⇒ ograniczenie „defaults … not
  re-validated after the redesign” usunąć, zastąpić wynikiem Q3 (z zastrzeżeniem o skali progów, R1 §3.5).

### B9. Znaczenie praktyczne

- Bezwzględne różnice: S5 − RS = +0.002…+0.018 HV (JAHS), −0.007…−0.015 IGD+ (NHB); domknięcie luki RS→front 4–61% (R2 §2.0). Różnice
  S5 vs najlepsze ramię: +0.0015…+0.044 HV, 0.007–0.012 IGD+ (NHB), na FCNet rząd wielkości (R2 §2.0).
- Cost-to-target w postaci z prereg jest zdegenerowany (R2 §4.2) — do suplementu. Retrening punktu kolanowego **nie wykonany** (R2 §1).
- Koszt optymalizatora (s9): S5 27–186 s/przebieg; GP 0.7–3.4 h, Vizier do 31 GB; S5 nie jest na froncie jakość × koszt (R2 §4.7, §5, W22).
  Argument „koszt optymalizatora BO dwarfs the evaluation” (pamięć projektu) — dane są: Vizier 7 267–12 037 s vs RS 2–10 s przy b=350 na
  benchmarkach tabelarycznych/surogatowych; w realnym treningu (10⁴ h symulowanego treningu na przebieg JAHS) narzut BO jest pomijalny —
  argument działa tylko w reżimie benchmarków.

### B10. Rozbieżności eksploracja vs potwierdzenie

- **Brak zmian znaku wśród istotnych** w Q1, Q4, Q7 (R2 §2.1, §2.4, §2.7). Przesunięcie jednokierunkowe: na 31–60 S5 wypada lepiej
  (35× „·”→„+” w Q1). Raportować obie kolumny obok siebie.

---

## 2. Twierdzenia artykułu v0.0.3

Klasyfikacja: **U** = utrzymane, **Z** = do zmiany (prawdziwe w zawężonej postaci albo z innymi liczbami), **X** = upada. „v0.0.3 L” =
numer linii w pliku źródłowym.

### 2.1 Tytuł, abstrakt, wstęp, kontrybucje

| # | Twierdzenie (skrót) | Gdzie | Status | Uzasadnienie |
|---|---|---|---|---|
| A1 | „P3Net pairs P3 with a relative, linkage-aware surrogate that predicts the change in accuracy from a modification restricted to one linkage subset” | abstract L5–6; intro L80–83 | **X** (opis) | Restrykcja do podzbioru jest pusta (korzeń w FOS), predykcja nie zależy od F, model = globalny addytywny Ridge na parach (R1 §3.2) |
| A2 | „We compare it against NSGANetV2, … SH-EMOA, MO-BOHB, TPE, random search …, 4 budgets, 30 seeds” | abstract L6–8 | **Z** | v004: 24 ramiona Q1 + 5 final + 3 MF, seedy 1–60, FCNet; nazwy baseline'ów wymagają doprecyzowania (B5) |
| A3 | „The result is negative. P3Net does not separate from random search in any of the sixteen cells” | abstract L10–11; intro L89–90 | **X** dla S5 | S5 > RS w 10/16 (31–60), nigdy gorszy (W1). Prawdziwe tylko dla S4 na seedach 1–30 |
| A4 | „neither does the same engine with an absolute surrogate” | abstract L11 | **Z** | `p3_absolute` 3/16 vs RS (31–60), `p3_absolute_cascade` 4/16 (R2 summaries); zależy od wersji |
| A5 | „geometric level growth forces the bootstrap share to rise …, 89.7–92.4% at 350” | abstract L12–14 | **Z** | Prawdziwe dla S4 (~91%); S5 18–45% (R2 §3.1). Mechanizm częściowo wsparty (W6) |
| A6 | „Removing the hyperparameter dimension does not change the outcome” | abstract L14 | **X** | Na NB201 przy 350 S5 > RS (δ +0.61); przy 100 nikt ≠ RS — sufit, nie „ten sam null” (R2 §2.8) |
| A7 | „a reconstruction of the closest prior design reproduces the same null” | abstract L15–16 | **Z** | `bartnik_p3` na NB201 nadal ≈ RS przy 350 (p=0.14 w rodzinie vsRS NB201), ale M10/M9 (ten sam silnik, skalarny FIHC) > RS — „null” jest cechą FIHC wielokryterialnego w tej rekonstrukcji (§0) |
| A8 | Tytuł „Combining P3 with a Surrogate Predictor for NAS” | title | **Z** | Wynik nie jest już negatywny względem RS; rozważyć tytuł oddający „middle of the pack / what helps” |
| C1 | Kontrybucja 1 (kontrolowane porównanie, Holm, IGD+ na wyroczni) | intro L94–97 | **Z** | Utrzymana i rozszerzona (FCNet, 24 ramiona, prerejestracja, seedy potwierdzające); test MWU zamiast Wilcoxona (A1 checklisty) |
| C2 | Kontrybucja 2 („P3's geometric pyramid growth forces … bootstrap; travels with the engine rather than the surrogate”) | intro L98–100 | **Z** | „P3's” → „our level-growth schedule”; „travels with the engine” — wsparte przez S4 vs S5, S4′, `grow_on_stall` (W5, W6), ale nie przez „P3” |
| C3 | Kontrybucja 3 (izolacja NB201, null przeżywa, Bartnik reprodukuje) | intro L101–103 | **X** w obecnej postaci | jw. A6, A7; zastąpić: „NB201 is at ceiling; the Bartnik-class reconstruction differs from its scalar-FIHC control” |
| C4 | Kontrybucja 4 (harness, liczby regenerowane z surowych przebiegów) | intro L104–105 | **U** | Uzupełnić deklarację dostępności kodu i prerejestrację; skrypty raportujące wymagają A1–A6 |
| I1 | „NSGA-Net/NSGANetV2 … use NSGA-II, whose variation operators treat coordinates independently” | intro L68–69 | **U** | Zgodne z naszą implementacją; doprecyzować, że nasze NSGANetV2 to uproszczony filtr (R1 §6.2) |
| I2 | „On combinatorial benchmarks their advantage grows with problem size” | intro L74–75 | **U** | Cytowanie literatury; nasz test pułapek przy b=2000 tego nie podważa (R1 §11) |

### 2.2 Problem Formulation

| # | Twierdzenie | Status | Uzasadnienie |
|---|---|---|---|
| P1 | Genotyp kategoryczny, HP dyskretyzowane | **U** | R1 §2 (JAHS: LR 8, WD 6; NHB pełna siatka benchmarku) |
| P2 | f1 = validation error | **Z** | Na NB201 f1 = błąd **testowy** (R1 §2); dopisać |
| P3 | f2: model size (JAHS), tabelaryczny czas (NHB) „not cheaper to obtain” | **Z** | Dopisać FCNet (czas, średnia 4 ziaren) i NB201 (FLOPs); JAHS `size_MB` pochodzi z surogatu JAHS, nie z liczenia parametrów (R1 §2) |
| P4 | „Both objectives are always queried at r_K” | **Z** | Nieprawda dla toru MF (f1 przy niższych epokach); dodać tor MF |
| P5 | „Budget = number of full evaluations; deterministic” | **Z** | Tor MF: ekwiwalenty epok (R1 §8); FCNet deterministyczny przez uśrednienie |
| P6 | Definicja δ̂_F „for x′ differing from x only on F … trained on pairwise differences” | **X** (w sensie „restricted to F”) | R1 §3.2 pkt 1–2 |

### 2.3 Proposed Optimizer

| # | Twierdzenie | Status | Uzasadnienie |
|---|---|---|---|
| O1 | „Following standard P3, a linkage tree is built by UPGMA over normalised MI” | **Z** | Miara = 1 − średnie NMI (sklearn), nie D Goldmana; podobna, nie identyczna (R1 §3.1) |
| O2 | „no mutation; all variation from optimal mixing” | **U** | R1 §3.1 |
| O3 | „ridge regression (regularisation chosen by built-in CV)” | **Z** | RidgeCV z siatką α ∈ {0.1, 1, 10}; LOO na parach dzielących punkty ⇒ zwykle α = 0.1 (R1 §3.2 pkt 5) |
| O4 | „A linear model … can only represent w·onehot(x) − w·onehot(x′)” | **U** (w praktyce) | Model wychodzi antysymetryczny (R1 §3.2 pkt 3); formalnie dwa wektory wag |
| O5 | Telescoping f̂(x_m) = f(x₀) − Σ δ̂ | **Z** | Dla tego modelu suma kolapsuje do f(x₀) − δ̂(x₀, x_m) (R1 §3.2 pkt 4) — wzór poprawny, ale „chain” nie wnosi informacji |
| O6 | Krok 1 „every linkage subset of the current tree … donor proposes a modification restricted to F” | **Z** | Z korzeniem (kopia dawcy), bez singletonów, jeden dawca (no-opy 13% decyzji, R2 §4.3) |
| O7 | Krok 2–3 „scored by δ̂_F relative to the individual they modify … accepted if δ̂_F ≥ 0” | **X** | Kod: łańcuch vs przodek x₀, nie vs bieżący (R1 §3.2); no-opy akceptowane ~50% przez szum numeryczny (R2 §4.3) |
| O8 | Krok 4 „nondominated in (f̂₁, f₂)” | **Z** | Dopisać: f2 świeże z hooka (H7) — tylko P3Net ma tę informację; `inherited_cost` pokazuje, że na głównych to bez znaczenia |
| O9 | Krok 5 „duplicates … served from a cache shared identically by every method and do not consume budget” | **Z** | Cache jest per metoda i deduplikacja leży po stronie metod (R1 H2); w praktyce żaden duplikat nie zużywa budżetu |
| O10 | „κ … heuristic bound on accumulated telescoping error” | **X** (uzasadnienie) | Telescoping nie kumuluje błędu dla tego modelu; błąd rośnie z odległością od przodka (R2 §3.3, W25). κ bywa wiążące w ≥25% łańcuchów |
| O11 | „Following P3, levels of geometrically growing target size, 2^k” | **X** | P3 nie ma rozmiarów docelowych; w kodzie 2^(k+1) (R1 §3.1) |
| O12 | „First, only the newest level is swept” | **Z** | Prawda dla S4; S5 przemiata wszystkie poziomy niezależnie (≠ kaskada P3) |
| O13 | „a new level is grown as soon as a sweep fails to increase the level's HV” | **Z** | HV liczone dla jednej „najlepszej” obserwacji partii (R1 §3.1) |
| O14 | „warm-started from the nondominated front of H_t, truncated … over (f̂₁, f₂)” | **Z** | Obcinanie po prawdziwych celach z H_t |

### 2.4 Setup

| # | Twierdzenie | Status | Uzasadnienie |
|---|---|---|---|
| S1 | Benchmarki: JAHS ×3, NHB; „test robustness within one family, not generalisation” | **Z** | Dochodzi FCNet (inna rodzina) i NB201 |
| S2 | Siatka ablacji 2×3 (NSGA-II/P3 × none/abs/rel) | **Z** | `p3_absolute` vs P3Net różni się w 3 osiach (R1 §5.2); czystszy kontrast `p3_absolute_cascade` vs S5 |
| S3 | „P3+abs. and NSGANetV2 use unregularised linear regression” | **U** | R1 §5.2, §6.2 |
| S4 | SH-EMOA cyt. `beume2007smsemoa`, MO-BOHB cyt. `falkner2018bohb` | **X** | Źródło: Guerrero-Viu et al.; oba jednowiernościowe (R1 §7) |
| S5 | Fairness controls: wspólny genotyp, walidacja, budżet, cache | **Z** | Dopisać: hook f2 tylko dla P3Net; deduplikacja per metoda; SMAC3 `n_trials`; MOEA/D przerywa (R1 §1.9, §9.2) |
| S6 | „NSGANetV2 on continuous Θ was not completed” | **U** | Nadal poza v004 |
| S7 | Budżety 50/100/200/350, R=30 | **Z** | R=30 + 30 potwierdzających; GP tylko 50/100 |
| S8 | Metryki: IGD+ na NHB (oracle 25 pkt), HV na JAHS względem frontu ze „wszystkich ramion, budżetów, seedów” | **Z** | v004: front z s1+s3+s7, seedy 1–30 (prereg §3), punkt odniesienia = nadir puli (R2 §0); FCNet IGD+ |
| S9 | „paired Wilcoxon signed-rank” | **X** | Prereg: MWU (A1); analiza v004 w R2 na MWU |

### 2.5 Headline, Diagnosis, Isolation (Results)

| # | Twierdzenie | Status | Uzasadnienie |
|---|---|---|---|
| H1 | „59 of 160 comparisons reject …; all seven wins against differently-engineered baselines are against MO-BOHB” | **X** | v004 (31–60, S5): 111+/14−/235· z 360; wygrane z MO-LS, P3-alone ×3, MO-BOHB, RS, REINFORCE, P3-abs., S4, Bartnik, NSGANetV2, M10, MOEA/D, SMAC3, RegEvo, qParEGO (R2 §2.1) |
| H2 | „No separation from random search … largest |δ| = 0.336” | **X** | jw. A3 |
| H3 | „P3+abs. also separates in none, MO-BOHB in one, every other arm in at least six” | **X** | v004: MO-BOHB 0, REINFORCE 0, P3-alone 1, qNEHVI 0, MO-LS 1 (31–60) — wiele ramion nie separuje się |
| H4 | „The two arms that never separate are exactly the two that run P3Net's pyramid” | **X** | S5 i `p3_absolute_cascade` na piramidzie separują się (10/16, 4/16) |
| H5 | „P3Net's margin tracks baseline's margin vs RS (Spearman 0.980): P3Net behaves as random search does” | **X** | B4 |
| H6 | Rys. konwergencji: „All arms reach a shared plateau within the first tenth” | **Z** | Na FMN/NHB/FCNet krzywe rosną do końca (R2 §4.1); nie ma wspólnego plateau |
| D1 | „bootstrap share rises with budget … 89.7–92.4% at 350 … accounts directly for the random-search-like behaviour” | **Z** | Prawdziwe dla S4; „accounts directly” — wsparte przez interwencje S4→S5, S4′, `grow_on_stall`, osłabione wewnątrz S5 (W6) |
| D2 | „P3+abs. on a flat population separated; on the pyramid separates in none; indistinguishable from P3Net in 16/16 — the intervention” | **Z** | Interwencja zmieniała też OLS/Ridge i f2 (B8); v004: S5 > `p3_absolute_cascade` w 3/16 |
| D3 | „P3-alone … stagnate; sweep counts 1508–2388” | **U** (mechanizm) | P3-alone jednokryterialny, FIFO, dedup z cache (R1 §5.1); przegrywa z S5 12/16 |
| D4 | „gate precision 0.498 … indistinguishable from chance” | **Z** | Dotyczyło S4; S5 na NHB precyzja 0.78 vs base 0.59, MCC 0.44; na FCNet MCC 0.17 (R2 §4.3) |
| D5 | „R² predicted vs true δ: −1.46 … −3.28” | **Z** | Do przeliczenia na S5; R2 §3.3: MAE 5.1 (JAHS), 11.0 (NHB), systematyczny optymizm −4.6 / −9.3 p.p. |
| D6 | „error concentrates at the level of size 16” | **Z/niezweryfikowane** | Nie sprawdzane w v004; R1 lista „R1” (ryzykowne) |
| D7 | „Telescoping accumulates error over the first steps (MSE 26.5 → 106.2)” | **Z** | Błąd rośnie z głębokością (2.75 → 5.04 p.p.), ale przez odległość od przodka, nie przez sumowanie (R2 §3.3, R1 §3.2) |
| D8 | „δ̂ linear … cannot represent joint effects … in tension with OM” | **U** | Krajobrazy silnie nieaddytywne: R² 0.36–0.48 vs 0.75–0.94 z interakcjami (W17) |
| D9 | Proxy interakcji i „exactly the order in which wins weaken” | **X** | Nie odtwarza się (B7) |
| D10 | `p3net_surrogate_interactions` 1/16 | **Z** | Wynik z v0.0.3, nie z v004 — oznaczyć albo usunąć |
| D11 | „Duplicate proposals are not what distinguishes P3Net” | **U/niezweryfikowane** | `duplication_rate` nie analizowany w R2; liczby do przeliczenia |
| N1 | „NB201: P3Net does not separate from RS at either budget” | **X** dla S5 | S5 > RS przy 350 (δ +0.61); S4 nadal ≈ RS (R2 §2.8) |
| N2 | „Bartnik's design avoids both defects … does not separate from RS nor P3Net … null not specific to P3Net” | **X** | `bartnik_p3` ≈ RS, ale M10 (różni się tylko skalarnym FIHC) > RS i > `bartnik_p3` (δ +0.56, §0) — „null” jest specyficzny dla wielokryterialnego FIHC w rekonstrukcji, nie dla rodziny |
| N3 | „f2 = FLOPs … deviations affect absolute values but not the comparison” | **Z** | f1 = test error to selekcja na teście — dotyczy wszystkich ramion jednakowo, ale nie „nie zmienia porównania” z literaturą |

### 2.6 Wnioski, Limitations, Future work

| # | Twierdzenie | Status | Uzasadnienie |
|---|---|---|---|
| K1 | „P3Net never separates from RS, and loses to SH-EMOA, TPE, NSGA-Net, NSGANetV2 increasingly as budget grows” | **X/Z** | S5 > RS; przegrywa z TPE, SH-EMOA, BANANAS, Vizier, NSGA-III/Net (1–3 komórki każdy), ale **nie** z NSGANetV2 (3+/0−) i nie „increasingly” (ranga S5 poprawia się z budżetem, R2 §3.6) |
| K2 | „The strongest account is structural and sits in the search engine … the one account supported by an intervention” | **Z** | Dla S4 → S5: tak (W5); ale S5 wciąż nie jest najlepszy, a na FCNet ograniczeniem jest surogat (W16) |
| K3 | „The relative surrogate … acceptance gate performs at chance” | **Z** | NHB MCC 0.44, FCNet 0.17 (R2 §4.3) |
| K4 | „Adding interaction features did not change search outcomes” | **Z** | v0.0.3; w v004 RF (nieliniowy) też nie zmienia na głównych (W13) — wniosek „pojemność surogatu nie jest wąskim gardłem na głównych” jest **wzmocniony** |
| K5 | „Removing Θ does not change the result, so the null is not an artefact of the joint genotype” | **X** | jw. N1 |
| K6 | „Bartnik reconstruction … reproduces the null” | **X** | jw. N2 |
| K7 | „consistent with a benchmark ceiling” (Lopes, den Ottelander) | **Z** | Dla NB201 (mediany ~0.99) — tak; dla JAHS/NHB/FCNet — nie: metody wyraźnie się różnią (domknięcie luki 4–99%) |
| L1 | „one cell-based family, small image classification” | **Z** | FCNet (MLP, regresja) rozszerza |
| L2 | „JAHS answers through a learned surrogate …” | **U** + dopisać | wpływ na tor MF (niższe wierności z surogatu, R1 §8) |
| L3 | „The surrogate ablation changes regularisation as well as formulation” | **U/Z** | dla `p3_absolute`; dla `p3_absolute_cascade` — oba Ridge, ale różnią się efektywną α (R1 §3.2) |
| L4 | „design defaults … not re-validated after the redesign” | **X** | s4 je zwalidował (W9, W11) |
| L5 | „pairwise MI may miss higher-order dependencies” | **U** | — |
| F1 | „pyramid driven by donor pool … our attempt with a fixed constant regressed severely” | **X** (druga część) | S4′ > S4 w 6/16 (W7) |
| F2 | „surrogate that exploits the linkage tree (CS-GOMEA open problem)” | **U** | wzmocnione: obecny surogat w ogóle nie korzysta z drzewa (R1 §3.2) |
| F3 | „larger or less redundant search space” | **Z** | FCNet nie jest większa; pozostaje otwarte |

### 2.7 Related Work — tam, gdzie dotyka wyników

| # | Twierdzenie | Status | Uzasadnienie |
|---|---|---|---|
| RW1 | „P3 … adding a level only once existing levels stop improving … central to the diagnosis” | **Z** | Opis P3 poprawny; ale nasz mechanizm (rozmiary 2^(k+1), bootstrap) nie jest P3 (R1 §3.1) |
| RW2 | „P3Net's surrogate follows eLyMPuS in being relative and linkage-aware over an incompletely discovered structure” | **X** | Brak powiązania z linkage (R1 §3.2) |
| RW3 | „Bartnik … absolute regressor; P3Net differs: relative, linkage-aware surrogate” | **Z** | Różnica „relative” prawdziwa tylko jako kotwiczenie; „linkage-aware” — nie |
| RW4 | Akapit LLM: „warm-starting the sparse early phase … targets the bootstrap that our diagnosis implicates” | **Z** | Bootstrap S5 jest niski (18–45%); argument słabnie |
| RW5 | „Any result on this family should be read against [benchmark-design literature]” | **U** | wzmocnione: wyniki zależą od rodziny (FCNet vs JAHS) |

### 2.8 Zdania opisujące metody, które R1 wykazał jako nieścisłe (zestawienie)

1. Surogat „relative, linkage-aware … restricted to the one linkage subset” — abstract, intro, Problem Formulation, Proposed Optimizer,
   Related Work (A1, P6, RW2): **pusta restrykcja**, globalny addytywny Ridge na wszystkich parach (R1 §3.2).
2. Telescoping jako źródło kumulowanego błędu i κ jako jego ograniczenie (O5, O10, D7): kolaps sumy (R1 §3.2 pkt 4).
3. Akceptacja „relative to the individual they modify” (O7): w kodzie względem przodka.
4. „Every linkage subset … donor” (O6): korzeń, brak singletonów, jeden dawca (R1 §3.1).
5. „Following P3, … 2^k” (O11): P3 nie ma rozmiarów docelowych; kod 2^(k+1).
6. „cascading one individual's improvement through every level” jako to, czego nie robimy (O12) — a S5 `cascade` robi coś innego niż P3.
7. Kanoniczny P3 w `bartnik_p3`: „canonical single-individual-climbing P3” (N2) — FIHC jednoprzebiegowy, przerywana wspinaczka, piramida z
   osobników nieocenionych, f2 przewidywane (R1 §4.1); bramka ≠ SA-P3-GOMEA (R1 §4.2).
8. SH-EMOA, MO-BOHB (S4): jednowiernościowe, źle cytowane (R1 §7).
9. NSGANetV2 (I1, S2): OLS, selekcja po f̂1, bez AS, bez złożoności (R1 §6.2).
10. NSGA-Net: NSGA-II bez turnieju i BOA (R1 §6.1).
11. P3-alone jako „P3 bez surogatu”: płaska FIFO, jednokryterialna (R1 §5.1).
12. „cache shared identically by every compared method” (O9): per metoda.
13. Problem Formulation: f1 = walidacja (NB201: test), f2 na JAHS „model size” (z surogatu JAHS).

---

## 3. `notes/p3net-improvements.md` (stan 2026-10-07, sprzed v004)

### 3.1 „Gdzie jesteśmy”

| Fakt | Aktualny? | Stan v004 |
|---|---|---|
| 0/16 komórek bez separacji od RS | **nie** | S5: 10/16 (31–60), 8/16 (1–30), 11/16 FCNet, nigdy gorszy (W1). S4 nadal 0/16 (1–30), 4/16 (31–60) |
| przegrane z SH-EMOA/TPE/NSGA-Net/NSGANetV2 rosną z budżetem (0→5→10→12) | **częściowo** | S5, 31–60, wszystkie ramiona Q1: 1 / 3 / 3 / 7 przegranych przy b = 50/100/200/350 (z 14); z NSGANetV2 S5 już nie przegrywa (3+/0−) |
| P3+abs. na tej samej piramidzie → 0/16 → winny silnik | **nie** | `p3_absolute_cascade` 4/16 vs RS; S5 ≥ absolutny (3+/0−/13·) |
| NB201: P3Net null, `bartnik_p3` null, `przewozniczek_p3elympus` wygrywa przy 350 (δ=+0.69) | **częściowo** | S5 też wygrywa z RS przy 350 (δ +0.61); M9 wygrywa, **ale M10 też** — przyczyną nie jest eLyMPuS (§0) |
| sweep wariantów → zero istotnych różnic | **tak** (z wyjątkiem) | s4: 15/16 wariantów bez różnic, `grow_on_stall` gorszy 8/16 (W9, W11) |
| `cascade` → 1 wygrana, reszta neutralna/ujemna, droższy | **nie** | S4→S5: 5/16 (główne), 7/16 (FCNet), nigdzie gorszy; droższy (27–186 s vs 5–150 s) |
| k-arne pułapki, b=2000: P3Net gorszy od RS | **tak** (nieprzeliczane) | `p3_trap_correctness_equal_budget_2000.md`: S4 15.72, S5 16.09, RS 16.38 |

### 3.2 Problemy P1–P7 (P4 przeniesiony do R1 w notatce)

| Problem | Status | Uzasadnienie |
|---|---|---|
| P1 Piramida zjada budżet na bootstrap | **częściowo rozwiązany** | `cascade` obniża udział do 18–45% (główne), 55–60% (FCNet); S4′ do <1%; obie wersje poprawiają jakość (W5–W7). Wewnątrz S5 więcej bootstrapu ≈ lepiej — przestał być głównym ograniczeniem |
| P2 Bramka = rzut monetą | **częściowo** | S5 na NHB MCC 0.44 (precyzja 0.78 vs base 0.59); na FCNet MCC 0.17 — wciąż prawie losowa (W16) |
| P3 Surogat addytywny, źle skalibrowany | **otwarty, z nową diagnozą** | Krajobrazy silnie nieaddytywne (W17); S5 optymistyczny o 4.6–9.3 p.p. (R2 §3.3); na FCNet główny problem to **skala celu** (surowe MSE, R² ≈ 0); RF (nieliniowy, dokładny) nie poprawia HV na głównych (W13) — pojemność nie jest wąskim gardłem tam |
| P5 Teleskopowanie kumuluje błąd | **przeformułowany** | Suma kolapsuje (R1 §3.2); błąd rośnie z odległością od przodka, nie z sumowaniem (W25); κ wiąże w ≥25% łańcuchów, ale κ ∈ {1…∞} bez wpływu (W11) |
| P6 Luka B4 przed wnioskiem o eLyMPuS | **rozwiązany** | M10 uruchomiony: M9 ≈ M10 wszędzie; przewaga M9 nad `bartnik_p3` na NB201 w całości od skalarnego FIHC (§0). eLyMPuS w tej integracji nic nie wnosi (W15) |
| P7 Przestrzeń za mała / redundantna | **częściowo** | FCNet sprawdzony (inna rodzina, nie większa) — S5 słabszy, kanoniczne P3 silniejsze. Większa przestrzeń nadal nietestowana |

### 3.3 Pomysły I1–I9 i R1–R7

| Pomysł | Ocena | Dlaczego |
|---|---|---|
| I1 Kalman / regresja bayesowska | **osłabiony** | Dokładność surogatu nie jest wąskim gardłem na głównych (RF ~10× dokładniejszy bez poprawy HV, W13); bramka trójdzielna mogłaby pomóc na FCNet, ale prostszy krok to zmiana skali celu |
| I2 Warunkowy eLyMPuS | **zbędny w obecnym harnessie / otwarty z prawdziwymi ocenami** | Na darmowej funkcji nie może pomóc (R1 §4.3, W15); sens ma tylko test na prawdziwych ewaluacjach (§6) |
| I3 Piramida sterowana dawcami | **osłabiony** | Bootstrap przestał dominować po `cascade`; S4′ pokazuje, że wcześniejsze mieszanie działa bez nowej reguły |
| I5 Ranking zamiast regresji | **wsparty** | Na FCNet regresja na surowym MSE zawodzi (R² ≈ 0), a model rankingowy (RF w top-decylu ρ 0.38–0.81) działa; strata rankingowa lub log(f1) usuwa problem skali (W16) |
| I6 Aktywne uczenie / niepewność | **otwarty** | Brak danych; optymizm S5 (klątwa zwycięzcy) sugeruje, że niepewność przy wyborze C* byłaby sensowna (4) |
| I8 Multi-fidelity | **silnie wsparty** | ASHA najlepsza na JAHS i FCNet przy równym koszcie epok (W19) |
| I9 `cascade` | **wsparty i przyjęty** (S5) | W5 |
| R1 Poprawki pod poziom 16 | **nadal ryzykowny, niezbadany** | Brak analizy w v004 |
| R2 Cechy interakcji | **osłabiony** | RF (pełna nieliniowość) bez poprawy na głównych (W13) |
| R3 Strojenie κ i progu | **zbędny** | s4: bez efektu (W11); progi w złych jednostkach (R1 §3.5) |
| R4 Stałe dobrane na danych | **bez zmian** (zasada) | — |
| R5 Adaptacyjna siatka HP | **otwarty** | Brak ramienia ciągłego |
| R6 Warm-start z LLM | **osłabiony** | Bootstrap S5 niski; argument z Related Work słabnie |
| R7 Porzucenie piramidy | **otwarty, mocniej uzasadniony** | S4′ (mieszanie od 2 osobników, prawie bez bootstrapu) ≈ S5; kanoniczne P3 bez rozmiarów docelowych dobre na NHB/FCNet — rozmiary 2^k nie wydają się potrzebne |

### 3.4 Priorytety z końca notatki — co zmienia kolejność

Stara kolejność: 1 M10 → 2 I3 → 3 I2+I1 → 4 I5/I6 → 5 P7 → 6 R-lista.
- **1 (M10) — zrobione**, wynik: eLyMPuS nic nie wnosi w tej integracji ⇒ **3 (I2+I1) spada** na koniec, warunkowo na test z prawdziwymi ocenami.
- **2 (I3) spada** — bootstrap przestał być głównym ograniczeniem.
- **Awansują:** (a) skala/ranking celu w surogacie (I5, log(f1)) — tani test, rozstrzyga W3/W16; (b) akceptacja wielokryterialna w wariantach
  RF (W14) — rozstrzyga N-D (§5); (c) MF jako składnik silnika (I8) — najsilniejszy sygnał w danych; (d) P7 większa przestrzeń — bez zmian,
  wciąż najbardziej decydujący test dla rodziny LL.
Proponowana nowa kolejność: I5 / log(f1) → akceptacja MO w RF → I8 → P7 → I6 → I2/I1 (z prawdziwymi ocenami) → R-lista.

---

## 4. Literatura z Related Work

| Praca | Co twierdzi | Nasze wyniki | Zgoda / spór i wniosek |
|---|---|---|---|
| **den Ottelander et al. 2021** (EMO; `notes/articles/NAS/Local Search…`) | LS mocnym baseline'em; na NB101 trudno pobić RS, MO-GOMEA = RS; na MacroNAS MO-GOMEA > RS | NB201: sufit, przy b=100 nikt ≠ RS ✓. **Ale** na JAHS/NHB/FCNet rodzina LL (S5, kanoniczne P3) bije RS w 7–11/16. Nasz MO-LS słaby przy b ≤ 100 (gorszy od RS w 6–9/16), dobry na FCNet przy 350 | Zgoda na NB201. Spór pozorny dla LS: nasz PLS bada **pełne** sąsiedztwo (39 sąsiadów), przy b ≤ 100 to 1–2 centra (R1 §10) — wariant i budżet, nie sprzeczność. Wniosek: przestrzenie joint (JAHS 4.5 mln konfiguracji) nie są „NB101-like” — LL może się separować |
| **Goldman & Punch 2014/2015** | P3 bez parametrów, FIHC + kaskada; przewaga rośnie z rozmiarem | Nasz silnik odbiega od P3 (R1 §3.1, §4.1); kanoniczny `climb` rozwiązuje pułapki przy 50 000 ocen, nie przy 2 000 | Brak sporu — nie testujemy P3 w jego reżimie (budżety ≤ 350 vs 10³–10⁵). Nie wolno przypisywać naszych wyników „P3” |
| **Qiao & Gallagher 2024** | Ograniczenie czasu GOMEA na pułapkach, przewaga rośnie z liczbą i długością podfunkcji | Budżety ≪ granic z analizy; brak testu skalowania | Neutralne; cytować tylko jako motywację P7 |
| **Guerrero-Viu et al. 2021** | SH-EMOA i MO-BOHB jako baseline'y joint NAS+HPO (wielowiernościowe) | Nasz SH-EMOA (bez SH) w czołówce; nasz MO-BOHB (jednowiernościowy, losowa skalaryzacja) ≈ RS; prawdziwe MF (ASHA) najsilniejsze | Zgoda co do siły SH-EMOA i MF; słabość MO-BOHB to cecha **naszej adaptacji**, nie metody (R1 §7) |
| **Bartnik 2026** (praca mag., `notes/articles/NAS/MO-NAS/…`; *korekta 2026-10-16*) | Warianty probabilistyczne MO-PSA-P3-GOMEA i MLP wygrywają z MO-LS na NB201 (energia GPU, budżet 500); wariant deterministyczny RF — nie na energii inferencji (Tab. 7.1) | `bartnik_p3` vs MO-LS na NB201: b=100 0.9856 vs 0.9750 (lepszy), b=350 0.9935 vs 0.9961 (**gorszy**); vs RS bez separacji | Częściowy spór przy 350; nasza rekonstrukcja (FLOPs, bramka ≠ SA-P3-GOMEA, FIHC MO) nie odtwarza jej wyniku w pełni. Po lekturze pracy (R1 §4.2): rekonstrukcja niewierna (FIHC, ewaluacje tylko na końcu wspinaczki, warm-up 6 vs 100, inna bramka), a odtworzony wariant był słaby także u autorki — brak sporu z jej wynikami, jest spór z naszą rekonstrukcją. Bartnik odrzuca FLOPs jako f2 (ρ z dokładnością 0.749), co współtłumaczy sufit NB201 |
| **Przewoźniczek et al. 2026 (LyMPuS/eLyMPuS)** | Oszczędność FFE w lokalnym przeszukiwaniu, gwarantowane odkrywanie linkage (binarne) | Integracja porównuje darmowe predykcje; M8 ≈ kontrola, M9 ≈ M10 | **Brak testu** tezy publikacji (R1 §4.3) — ani zgoda, ani spór. W tekście nie łączyć wyników M8/M9 z wartością eLyMPuS |
| **Dushatskiy et al. 2021 (SA-P3-GOMEA)** | Surogat w P3-GOMEA, bramka kwantylowa na predykcjach; SVR najlepszy w ich problemie | RF przewiduje f1 najdokładniej, ale nie poprawia HV na głównych; bramka w `bartnik_p3` ≠ ich bramka (R1 §4.2) | Zgoda, że wybór surogatu nie jest najważniejszy; nasza obserwacja dokłada: **o wyniku decyduje obsługa celów (akceptacja po f1), nie dokładność** (W13–W14, siła (3)) |
| **Dushatskiy et al. 2019 (CS-GOMEA)** | Surogat nie wykorzystuje linkage — problem otwarty | Nasz surogat też nie (nawet mniej, niż deklarowano — R1 §3.2) | Zgoda; F2 (future work) wzmocniony |
| **Lopes et al. 2023** | Przestrzeń komórkowa NB201 redundantna, skośna ku dobrym architekturom | NB201 sufit ~0.99 ✓; JAHS (ta sama komórka + HP) daje rozróżnienie metod | Zgoda dla NB201; dodanie HP zmienia trudność — argument „benchmark ceiling” nie dotyczy JAHS |
| **Yang et al. 2020** | RS konkurencyjne; projekt przestrzeni decyduje | Kolejność metod zmienia się między JAHS a FCNet (S5 5. vs 13.); RS przegrywa z większością | Częściowa zgoda: zależność od przestrzeni ✓; „RS konkurencyjne” — na naszych przestrzeniach nie (RS ranga 17/25) |
| **Mehta et al. 2022 (NAS-Bench-Suite)** | Rankingi słabo przenoszą się między benchmarkami; LS, BANANAS mocne | BANANAS w czołówce wszędzie ✓; rankingi zmieniają się JAHS ↔ FCNet ✓ | Zgoda; wspiera narrację N-C (§5) |
| **Lu et al. 2020 (NSGANetV2)** | AS + wewnętrzny NSGA-II z dokładną złożonością + wybór podzbioru | Nasza wersja uproszczona (R1 §6.2); S5 > nasz NSGANetV2 w 3/16 | Brak wniosku o oryginale; jedyna uczciwa forma: „NSGA-II + liniowy filtr po f1 w duchu NSGANetV2” |
| **Lu et al. 2019 (NSGA-Net)** | NSGA-II + BOA | Nasza wersja bez BOA i turnieju | jw. |

---

## 5. Możliwe narracje zaktualizowanego artykułu

| Narracja | Główna teza | Co ją niesie (siła) | Co ją osłabia | Czego brakuje | Największe ryzyko recenzenckie |
|---|---|---|---|---|---|
| **N-A „Umiarkowany wynik pozytywny”** | Linkage-learning EA z surogatem i wszystkimi poziomami w mieszaniu (S5) wyraźnie bije RS i wiele baseline'ów w joint NAS+HPO | W1 (2), W5 (1/3), B10 bez zmian znaku (2) | W2 (S5 dopiero 5.), W3 (FCNet 13.), W22 (nie na froncie jakość × koszt), opis surogatu nieścisły | jasne „po co używać S5” | „Dlaczego nie SH-EMOA/BANANAS, które są lepsze i 10× tańsze?” |
| **N-B „Anatomia: co działa, a co nie w surogatowym EA z linkage”** | Rozbiór drogi projektowej: co poprawia (cascade/wczesne mieszanie, kotwiczenie), co nie (linkage w surogacie, Ridge vs RF, κ, próg, eLyMPuS w tej integracji) | W5–W9, W12 (1/2/3), W13, W15 | wiele interwencji na seedach eksploracyjnych; brak większej przestrzeni | MO-akceptacja w RF; log(f1); FOS bez korzenia | „Wkład metodyczny mały; to raport z debugowania” |
| **N-C „Zależność od benchmarku i skali celu”** | Pozycja metod (w tym S5) zależy od rodziny benchmarków; na FCNet surowe MSE niszczy surogaty liniowe | W3, W16, W17 (1 dla krajobrazu), Q5 vs Q1 | tylko 2 rodziny; Mehta/Yang już to mówią | log(f1)-S5 jako interwencja; 3. rodzina | „Znane z literatury” |
| **N-D „Obsługa celów, nie dokładność surogatu”** | W MO surogatowym przeszukiwaniu o jakości frontu decyduje to, które cele wchodzą do akceptacji i selekcji (świeże f2 w C*, akceptacja po f1), a nie dokładność predykcji f1 | W13–W14 (2/3), W4 (3), coverage (R2 §3.2), RF 10× dokładniejszy bez zysku | korelacyjne; `inherited_cost` ≈ S5 osłabia rolę świeżego f2 | **interwencja**: akceptacja MO w RF; dekompozycja HV | „Wniosek z jednej rodziny metod; brak interwencji” |
| **N-E „Koszt praktyczny metod”** | Przy równej jakości narzut optymalizatora różni się o 3–4 rzędy; GP nie skaluje się | W20, W22, s9 (3) | narzut pomijalny wobec realnego treningu; GP tylko ≤ 100 | GP przy 200/350; pieniądze/energia z założeniami | „Benchmarki tabelaryczne zawyżają znaczenie narzutu” |
| **N-F „Wynik negatywny dla LL (dawna narracja)”** | P3Net nie bije RS | — | W1 ją obala | — | Nie do obrony |

Rekomendacja do dyskusji: **N-B jako rdzeń + N-D jako główna hipoteza mechanistyczna** (z interwencją MO-akceptacji, jeśli czas pozwoli),
N-C jako sekcja „dlaczego FCNet inaczej”. N-A tylko jako jedno zdanie wyniku (S5 > RS), nie teza.

---

## 6. Brakujące analizy i eksperymenty

Priorytet: P0 (przed jakąkolwiek liczbą w tekście), P1 (zmienia wnioski), P2 (wzmacnia), P3 (opcjonalne). Koszt: na podstawie czasów s9 (R2 §4.7)
i liczby przebiegów; „runy” = (ramię × przestrzeń × budżet × seed).

| # | Co | Prio | Koszt | Co rozstrzyga |
|---|---|---|---|---|
| E1 | A1: MWU zamiast Wilcoxona w `stats/significance.py` + test | P0 | < 1 dzień kodu | zgodność z prereg |
| E2 | A2–A4: guard `None`, n z danych, adnotacja o rodzinie Holma, generator podsumowania, tabela vs RS z dwiema kolumnami | P0 | 1–2 dni | poprawność tekstu |
| E3 | A5–A6: brak pamięci mostu/GPU w s9 opisać; zamrożony front + punkt odniesienia zapisać | P0 | < 1 dzień | prereg §3, §5 |
| E4 | Prereg §7: wpisać odchylenia (GP ≤ 100, front NB201 z s5, brak 4b, brak posthoc, pamięć mostu) | P0 | godziny | uczciwość |
| E5 | `posthoc_metrics.py` na JAHS (etykiety decyzji, front testowy) | P1 | ~3 × ładowanie mostu (12 GB) + kilka h CPU | B7 na JAHS, luki generalizacji |
| E6 | S5 z log(f1) (lub stratą rankingową) na FCNet i 4 przestrzeniach głównych | P1 | kod: godziny; 960 runów S5 (FCNet ~1–2 min, JAHS ~3 min) ≈ 1–2 dni na 6 workerach | W3/W16, narracja N-C |
| E7 | `inherited_cost` na FCNet | P1 | 480 runów S5, < 1 dzień | B3 na FCNet |
| E8 | Akceptacja wielokryterialna (lub z świeżym f2) w wariantach RF (M7, M7+FIHC) | P1 | kod: 1 dzień; 2 × 1440 runów × 5–15 min ≈ 4–8 dni | N-D (interwencja) |
| E9 | SMAC3 z `n_trials` = budżet | P2 | 1440 runów × ~4 min ≈ 1 dzień | W21 — uczciwy SMAC3 |
| E10 | MOEA/D z eliminacją duplikatów (lub raport z faktycznym budżetem) | P2 | kod godziny; 480 runów FCNet | Info− MOEA/D |
| E11 | eLyMPuS na prawdziwych ewaluacjach (wspinaczka jako maszyna stanów, 1/x, circuit check, FIHC do optimum); pułapki k-arne + binarne + NHB/NB201 | P2 | kod: 3–5 dni; runy tanie (tabele) | czy wolno cokolwiek powiedzieć o eLyMPuS (R1 §4.3) |
| E12 | Kanoniczne P3 (M10) ze świeżym f2 przy selekcji/bramce | P2 | kod mały; 1440 runów × ~20 min ≈ 20 dni CPU / 6 workerów ≈ 3–4 dni | W18: czy kanoniczne P3 + f2 łączy oba atuty |
| E13 | FOS bez korzenia, z singletonami, dawca różniący się (P-K1, P-K3) jako wariant S5 | P2 | kod 1 dzień; 960 runów ≈ 2 dni | czy „linkage-aware” może zacząć coś znaczyć |
| E14 | Dekompozycja HV (tani vs dokładny koniec frontu) i duplikaty | P2 | godziny analizy | W4, D11 |
| E15 | TOST/równoważność dla par bez różnic (np. S5 vs `inherited_cost`, M9 vs M10) | P2 | godziny | B4 |
| E16 | Retrening punktu kolanowego (prereg 4b) | P3 | ~116 treningów GPU | prereg §5; inaczej zgłosić jako brak |
| E17 | Większe przestrzenie (MacroNAS, NB101, NAS-Bench-Suite) | P3 (P1 dla narracji LL) | nowe substraty: 1–2 tyg.; runy zależne | P7, den Ottelander |
| E18 | GP przy 200/350 | P3 | qNEHVI ~2.3 h/run, Vizier ~2–3.4 h i do 34 GB; 720 runów/ramię ⇒ tygodnie | W20 |
| E19 | NSGANetV2-continuous / wierny NSGANetV2 (AS + wewnętrzny NSGA-II + złożoność) | P3 | kod 2–4 dni; 1440 runów | B5, dyskretyzacja |
| E20 | Weryfikacja hipotezy poziomu 16 (R1) z logów `level_size_log` | P3 | godziny | D6 |

---

## 7. Pytania do autora

| # | Decyzja | Rekomendacja | Konsekwencje |
|---|---|---|---|
| Q1 | Którą narrację wybrać (§5)? | N-B + N-D (+ N-C dla FCNet) | Przepisanie abstraktu, kontrybucji 2–3, Diagnosis i Isolation; tytuł bez „negative result” |
| Q2 | Surogat „relative, linkage-aware”: przemianować czy naprawić kod (FOS bez korzenia) i przeliczyć? | Przemianować teraz („pairwise-trained, ancestor-anchored additive surrogate”); naprawę jako wariant E13, jeśli czas | Bez naprawy — tekst zgodny z kodem, ale traci deklarowaną nowość; z naprawą — nowy etap S6, nowe przebiegi, ryzyko nowych odchyleń od prereg |
| Q3 | Co z eLyMPuS (M8, M9) w artykule? | Zostawić jako kontrolę negatywną z jawnym zastrzeżeniem (R1 §4.3), bez wniosku o metodzie; tekst z `_parked/` porzucić (teza obalona, §0) | Uczciwość wobec autorów eLyMPuS (samocytowania!); alternatywa — przenieść do suplementu |
| Q4 | Czy uruchomić dodatkowe eksperymenty przed wysyłką? | Tak, tanie: E6 (log f1), E7 (`inherited_cost` FCNet), E9 (SMAC3); jeśli możliwe E8 (MO-akceptacja) | ~1 tydzień obliczeń; nowe przebiegi poza prerejestracją — oznaczyć jako eksploracyjne |
| Q5 | Jak raportować baseline'y o obniżonej wierności (SMAC3 b ≤ 100, MOEA/D FCNet, MO-BOHB, SH-EMOA bez SH)? | Adnotacja w tabelach + przemianowanie; SMAC3 przeliczyć (E9) | Bez tego recenzent może zarzucić „słabe baseline'y” |
| Q6 | GP tylko b ≤ 100 — osobna tabela czy w głównych heatmapach? | Osobna tabela b=50/100 z GP + główne heatmapy bez GP przy 200/350 z adnotacją | Rodzina Holma zmienna — opisać w podpisie |
| Q7 | Wypełnić prereg §7 teraz (z datą)? | Tak | Wymagane przez samą prerejestrację |
| Q8 | Retrening punktu kolanowego (4b) — zrobić czy zgłosić brak? | Zgłosić jako brak, chyba że GPU jest dostępne bez opóźnienia | Brak względem prereg; słabsza sekcja praktyczna |
| Q9 | Jak traktować porównanie z Bartnik (praca magisterska w repo, rekonstrukcja niewierna — R1 §4.2, korekta 2026-10-16)? | Nazwać „Bartnik-inspired reconstruction”, nie twierdzić odtworzenia; podać wynik vs MO-LS na NB201 obu budżetów | Recenzent nie zweryfikuje pracy magisterskiej; samocytowanie promotora w trzeciej osobie (D checklisty) |
| Q10 | Czy w głównym tekście zostaje NB201? | Tak, krótko jako „ceiling check” | Usunąć „null survives” |
| Q11 | Czy zmienić metrykę JAHS (punkt odniesienia) na mniej zdegenerowaną? | Nie (prereg); dodać „domknięcie luki” i odporność rankingu (R2 §3.0b) jako opis | Zachowana zgodność z prereg |
| Q12 | Czy S4′ („dead end”) zostaje ślepą uliczką w narracji? | Nie — opisać jako równoważną alternatywę dla S5 (W7) | Zmiana opisu drogi projektowej i Future work |
