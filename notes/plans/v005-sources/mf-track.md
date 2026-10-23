# Tor multi-fidelity (MF) — karta źródła

Status: **ZATWIERDZONA** (2026-10-16, autor projektu): usunięcie `bohb_mo`, MF-1 a, MF-2 a, MF-3 a, MF-4, W-MF1–W-MF7, poziom 2.
Decyzje wcześniejsze: #17, #18 (SH-EMOA i MO-BOHB w pełnej wersji MF), #25 (JAHS: niższe wierności z surogatu —
ograniczenie), #32 (tor MF osobno, koszt w ekwiwalentach pełnych ewaluacji), BB-5 (MO-SH-BANANAS w torze MF), #6, K-2.

## 1. Ramiona i źródła

| Ramię | Publikacja | Implementacja |
|---|---|---|
| Hyperband-MO | Li et al., JMLR 2018 (Hyperband) + promocja NSGA-II z MO-ASHA (Schmucker et al. 2021) | własna wg pseudokodu Li et al. (jak v004) |
| ASHA-MO | Li et al., MLSys 2020 (ASHA) + Schmucker et al. 2021 (MO-ASHA, wariant NSGA-II) | własna (jak v004) |
| MO-BOHB | Guerrero-Viu et al. 2021 (BoB) | kod BoB (`mobohb/hpbandster`) — karta `bag-of-baselines.md` |
| SH-EMOA | j.w. | port kodu BoB — karta BoB |
| MO-SH-BANANAS | j.w. | port kodu BoB (`moshbananas.py`) — karta BoB |

**Zmiana względem v004:** `bohb_mo` z v004 (BOHB z losową skalaryzacją przy każdym wyniku — nasza adaptacja) **usunięty**;
jego miejsce zajmuje MO-BOHB z BoB (opublikowana wersja wielokryterialna). W `refs.bib` brak Li et al. 2018, Li et al.
2020 i Schmucker et al. 2021 — dodać (PDF-y do `notes/articles/`).

## 2. Model kosztu i co liczy się do wyników (z v004, zostaje)

- Zapytanie (genotyp, e epok) kosztuje (e − e_prev)/E — wznowienie od ostatniej oceny tego genotypu; budżet = B pełnych
  ewaluacji; stop wg K-2 (zapytanie przekraczające budżet kończy przebieg).
- Do frontu i metryk trafiają **tylko oceny przy e = E**; niższe wierności — w diagnostyce.
- E: JAHS 200, NAS-HPO-II 12, FCNet 100. NB201 poza torem MF (jak w v004).

## 3. Decyzje

### MF-1. f2 przy niższej wierności (#6)

W v004 f2 przy każdej wierności = wartość z pełnego treningu (dla NAS-HPO-II/FCNet: czas **całego** treningu) — to
informacja „z przyszłości”.

- **a) f2 obserwowane przy e epokach = to, co benchmark daje dla e epok;** jeśli benchmark ma tylko czas pełnego
  treningu, obserwacja = czas·e/E (czas na epokę × e). Do promocji metoda może ekstrapolować do E (czas na epokę × E) —
  to rachunek, który zrobiłby użytkownik po e epokach.
  - Za: zgodne z #6 (żadnej wiedzy, której nie da się zaobserwować po e epokach). Przeciw: przy liniowym czasie wynik
    jest liczbowo taki sam jak w v004 — zmiana porządkuje uzasadnienie, nie liczby.
- **b) Promocja tylko po f1.** Przeciw: promocja przestaje być wielokryterialna.

JAHS: f2 = rozmiar modelu nie zależy od liczby epok (obserwowany przy każdej wierności) — wg karty benchmarków (#26).

**Rekomendacja: a).**

### MF-2. Promocja wielokryterialna w Hyperband/ASHA

- **a) NDS + crowding (wariant NSGA-II z MO-ASHA, Schmucker et al. 2021)** — jak v004, teraz z cytowaniem źródła.
- **b) NDS + HSSP (jak MO-BOHB/SH-EMOA w BoB).** Za: jednolite w torze. Przeciw: to reguła innego źródła.

**Rekomendacja: a)** — każda metoda z regułą swojego źródła (Hyperband/ASHA: MO-ASHA; BoB: NDS + HSSP).

### MF-3. Drabiny wierności

- **Hyperband/ASHA:** η = 3, r_min = 1 epoka (jak v004): JAHS 2, 7, 22, 67, 200; NAS-HPO-II 1, 4, 12; FCNet 1, 4, 11,
  33, 100.
- **Metody BoB** (źródło: b_min = 5, b_max = 25 epok, czyli b_min/b_max = 0.2; η: SH-EMOA 2, MO-BOHB 2, MO-SH-BANANAS 3):
  - **a) Zachować stosunek 0.2 i η ze źródła:** b_max = E, b_min = ⌈0.2·E⌉ (JAHS 40, NAS-HPO-II 3, FCNet 20).
    Za: wierne proporcjom źródła. Przeciw: inne drabiny niż Hyperband/ASHA w tym samym torze.
  - **b) Wspólna drabina z Hyperband/ASHA.** Za: jednolite. Przeciw: odchodzi od źródła.

**Rekomendacja: a)** — każda metoda ze swoimi parametrami; porównanie i tak jest „przy równym koszcie”.

### MF-4. Populacja i rozmiary startowe metod BoB w torze MF

Jak w torze głównym (BB-4, #37): populacja SH-EMOA 20, starty min(źródło, ⌊0.25·b⌋) liczone w **pełnych** ewaluacjach
ekwiwalentnych. **Rekomendacja: przyjąć.**

## 4. Własności do sprawdzenia testami (poziom 1)

| ID | Własność |
|---|---|
| W-MF1 | Koszt zapytania (e − e_prev)/E; suma kosztów ≤ B; przebieg kończy się wg K-2 |
| W-MF2 | Front i metryki wyłącznie z ocen przy e = E |
| W-MF3 | f2 przy e < E wg MF-1 (nigdy wartość z pełnego treningu odczytana wprost) |
| W-MF4 | Hyperband: harmonogram nawiasów i liczby konfiguracji zgodne z pseudokodem Li et al. (s_max, n_i, r_i) |
| W-MF5 | ASHA: promocja z najwyższego możliwego szczebla, gdy ⌊n/η⌋ kandydatów w szczeblu |
| W-MF6 | Promocja Hyperband/ASHA: NDS + crowding (MF-2 a) |
| W-MF7 | Drabiny wg MF-3 |

**Poziom 2:** Hyperband — harmonogram (nawiasy, liczby konfiguracji i epok) identyczny z hpbandster `HyperBand` na tych
samych η, r_min, R (test deterministyczny, bez wyników); jednokryterialnie — jakość ±2 % + TOST vs hpbandster na NAS-HPO-II.
ASHA — vs implementacja referencyjna (np. syne-tune) jednokryterialnie, jeden worker. Metody BoB — wg karty BoB.

## 5. Do zatwierdzenia

Usunięcie `bohb_mo` (zastąpiony MO-BOHB z BoB); MF-1 a, MF-2 a, MF-3 a, MF-4; W-MF1–W-MF7; poziom 2; dopisanie źródeł do
`refs.bib`.
