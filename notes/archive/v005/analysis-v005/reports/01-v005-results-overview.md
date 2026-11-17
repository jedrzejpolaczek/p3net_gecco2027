# v005 — przegląd wyników po przebiegu

Stan na 2026-11-16. Źródło: `implementation/experiments/results/runs/c674c91e/analysis/` (wynik
`scripts/analyze_v005.py results/runs/c674c91e results/runs/c674c91e-vizier`), rekordy runów z run rootów
`c674c91e` i `c674c91e-vizier` (commit `c674c91e`). Pierwszy przegląd pod etap B — liczby opisowe, bez interpretacji
w tekście artykułu.

## 1. Kontrola po przebiegu

- Rekordy: 26 400 (`v005.yaml`: main 19 440, gp 1 080, elympus 1 080, mf 4 800) + 540 (`v005-vizier.yaml`);
  te same liczby na serwerze Hetzner i na serwerze GPU.
- `missing.csv` 0 wierszy, `duplicates.csv` 0 wierszy — każdy punkt siatki ma dokładnie jeden wynik, w tym 3 000
  punktów JAHS powtórzonych po awarii mostu (2026-11-06, OOM; `--retry-failed`, 2 workery) i punkty Viziera
  przerwane przez OOM workera (restart od zera, prerejestracja §4).
- `failures.jsonl` (`c674c91e`): 9 000 wpisów `failure` (3 000 punktów × 3 próby, wszystkie „shared jahs-bench bridge
  closed the connection”) + 3 000 wpisów `reset` z `--retry-failed`. `v005_status.sh` liczy wszystkie linie pliku.
- Kontrole level-4: 0 nieudanych runów.
- Posthoc JAHS (R8 b, seedy 62–71): 3 000 + 60 plików w `posthoc/`, bez błędów.

## 2. Wyniki testów (prerejestracja §4)

Komórka = (przestrzeń, budżet); przestrzenie główne: JAHS C10, CRC, FMN, NAS-HPO-Bench-II → 16 komórek. Rodzina Q1:
17 ramion przy b = 50, 100; 14 przy b = 200, 350 (GP tylko b = 50, 100). Kierunek = istotne po Holmie, α = 0.05.

| Rodzina | porównań | P3Net lepszy | P3Net gorszy | n.s. |
|---|---|---|---|---|
| Q1 | 248 | 30 | 100 | 118 |
| Q2 | 48 | 0 | 0 | 48 |
| Q4 (MF) | 80 | 12 | 33 | 35 |
| Q5 (FCNet) | 248 | 64 | 36 | 148 |

### Q1 według komórek (lepszy / gorszy / n.s.)

| Przestrzeń | b = 50 | 100 | 200 | 350 |
|---|---|---|---|---|
| JAHS C10 | 0 / 14 / 3 | 0 / 14 / 3 | 0 / 7 / 7 | 1 / 4 / 9 |
| JAHS CRC | 0 / 12 / 5 | 0 / 12 / 5 | 8 / 0 / 6 | 7 / 0 / 7 |
| JAHS FMN | 0 / 17 / 0 | 0 / 14 / 3 | 2 / 0 / 12 | 6 / 0 / 8 |
| NHB | 0 / 0 / 17 | 0 / 1 / 16 | 3 / 0 / 11 | 3 / 5 / 6 |

- Ramiona najczęściej lepsze od P3Net (komórki z 16): MO-BANANAS, NSGA-Net, NSGA-III, SH-EMOA po 9; NSGANetV2 8;
  MOTPE 7 (3 komórki odwrotnie).
- P3Net najczęściej lepszy od: REINFORCE 7, MO-PSA 5, random search 5, MO-DSA 4.

### Q2 / Q3 — wkład surogatu

| Para | TOST m = 0.33: równoważne / nierozstrzygnięte | m = 0.147 | δ: min / mediana / max |
|---|---|---|---|
| P3Net vs canonical P3 | 5 / 11 | 0 / 16 | −0.18 / −0.06 / 0.13 |
| P3Net vs P3Net-gate | 16 / 0 | 0 / 16 | −0.06 / 0.00 / 0.04 |
| P3Net vs P3Net-nolink | 16 / 0 | 0 / 16 | 0.00 / 0.00 / 0.01 |

Równoważność z gate i nolink jest w dużej części mechaniczna:

- wartość końcowa metryki identyczna jak w P3Net (ten sam seed, ta sama komórka), przestrzenie główne: gate 94.6 %
  runów, nolink 96.0 %, canonical 5.8 % (wszystkie przestrzenie, z FCNet i NB201: 86.9 / 92.7 / 4.4 %);
- mediana liczby kroków mieszania (`mixing_steps`) P3Net przy b = 50 / 100 / 200 / 350: przestrzenie główne
  0 / 0 / 1 / 8; FCNet 0 / 0 / 8 / 45.5; NB201 0 / 1 / 18 / 55.5. Udział surogatu w krokach mieszania (mediana,
  `surrogate_share`, przestrzenie główne): — / — / 0.60 / 0.63.

  (Poprawka 2026-11-16: pierwsza wersja raportu podawała 0 / 0 / 6 / 39 i 86.9 / 92.7 % — liczone po wszystkich
  przestrzeniach naraz, bez zaznaczenia tego.)

Surogat ma mało okazji do działania przy b ≤ 350 — budżet zużywa głównie FIHC (pozycja B1 etapu B). Wynik Q3 nie
świadczy więc o tym, że surogat działa równie dobrze jak wariant bez niego.

### Q4 — tor multi-fidelity

P3Net gorszy od wszystkich pięciu ramion MF przy b = 50 i 100 na trzech JAHS (MO-BOHB także przy b = 200 na C10).
Przy b = 350 lepszy od ASHA, Hyperband, MOSH-BANANAS na CRC i FMN (na FMN także od SH-EMOA MF); na CRC przy b = 200
lepszy od Hyperband i MOSH-BANANAS. JAHS C10 przy b = 200, 350 — n.s. (poza MO-BOHB). NHB: przeważnie n.s.;
P3Net gorszy od ASHA przy b = 50, lepszy od Hyperband przy b = 200, przy b = 350 lepszy od ASHA i Hyperband, gorszy od
SH-EMOA MF.

Krzywe anytime ramion MF na osi kosztu nie mają wartości, dopóki żadna konfiguracja nie jest wytrenowana do końca.
SH-EMOA (MF) nie ma takiej konfiguracji przez ok. 60 % budżetu kosztu we wszystkich przestrzeniach (np. koszt 217–224
z 350); ASHA, Hyperband, MO-BOHB, MOSH-BANANAS — tylko na samym początku. Ostrzeżenie „All-NaN slice” w
`analyze_v005.py` pochodzi stąd. Trzeba to napisać przy wykresach anytime.

### Q5 — FCNet

| Zadanie | lepszy | gorszy | n.s. |
|---|---|---|---|
| naval propulsion | 15 | 4 | 43 |
| parkinsons telemonitoring | 16 | 2 | 44 |
| protein structure | 8 | 21 | 33 |
| slice localization | 25 | 9 | 28 |

Na FCNet bilans jest korzystniejszy dla P3Net niż na przestrzeniach głównych (wyjątek: protein structure).

## 3. Analizy opisowe (§5)

- **Q6, koszt optymalizatora** (`costs.csv`, `method_wall_seconds`, mediana, JAHS C10, b = 350): P3Net 5.7 s,
  P3Net-gate 5.8 s, MO-DSA 945 s, NSGANetV2 2 825 s, SMAC3-ParEGO 234 s, ASHA 799 s. Przy b = 100: Vizier 1 160 s,
  qNEHVI 160 s, qParEGO 68 s.
- **Q7, eLyMPuS vs canonical P3** (opisowo): eLyMPuS gorszy w 33 z 36 komórek (δ do −0.38; lepszy: NB201 b = 50, 350,
  FCNet slice b = 200).
- **Budżet niewykorzystany** (`budget_use.csv`, tor główny; stop przez „exploration collapse”):
  - REINFORCE 909 runów (10 000 kolejnych duplikatów; mediana 54 ewaluacji, maks. 143);
  - MO-DSA 206 runów, MO-PSA 130 runów (1 000 iteracji bez nowej ewaluacji; mediana MO-PSA przy b = 350: 72);
  - MOTPE 4 runy (27 ewaluacji).
  Głównie FCNet i NB201 (małe przestrzenie). Do opisania w artykule przy każdej tabeli tych ramion.

## 4. Jakość decyzji surogatu (§5.4, K8) — niewykonalna z rekordów v005

Rekordy v005 nie mają decyzji surogatu: `diagnostics.surrogate_decisions` nie występuje w żadnym rekordzie, a
`posthoc_metrics.py` zapisuje `decisions = None` we wszystkich plikach. `decision_log` ma tylko stara klasa
`p3net.methods.p3net` (`lib/src/p3net/methods/p3net.py`); metody `p3net/v005/` go nie mają, a
`diagnostics.v005.events` przechowuje tylko liczniki zdarzeń. Odchylenie od prerejestracji — decyzja autora w
`v005-todo.md` („Otwarte decyzje autora”).

## 5. Do etapu B

- B1: mała liczba kroków mieszania P3Net przy b ≤ 350 — wyjaśnia Q2/Q3; pokazać razem z identycznością wyników.
- Q1: zależność od budżetu (P3Net przegrywa przy b = 50, 100, dogania lub wygrywa przy b = 200, 350 na CRC i FMN).
- Krzywe anytime ramion MF — luka na początku osi kosztu (SH-EMOA MF do ok. 60 %).
- Ramiona z niewykorzystanym budżetem — opis przy tabelach.
- Poprawki raportowania z v004 (guard na `None`, liczba seedów w podpisie, rodzina Holma) — sprawdzić w skryptach
  tabel v005, zanim powstaną.
