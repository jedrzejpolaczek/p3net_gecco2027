# A9 — równoważność, S4′ vs S5, dekompozycja HV, duplikaty (dane v004, 2026-10-24)

**Wybory metody w tym raporcie są Claude'a, do akceptacji autora** (`v005-todo.md`): marginesy TOST 0.147 / 0.33,
bootstrap 90 % CI, podział HV w medianie f2 frontu. Wnioski dla planu (B4, raport 02 §2.1) = PROPOZYCJE P6, P7.

Skrypty: `notes/analysis-v004/equivalence.py`, `notes/analysis-v004/hvdecomp.py` (wejście: `analyze.py` → `per_run.csv`,
`runs.pkl`). Liczby eksploracyjne, jak w raporcie 02. 16 komórek głównych = 4 przestrzenie (JAHS C10, CRC, FMN, NHB) × 4 budżety.

## 1. TOST dla par „bez różnicy”

Metoda: Cliff's δ (dodatnie = lepiej dla pierwszego ramienia), 90% bootstrapowy CI (4000 próbek) = TOST na α=0.05 z każdej
strony. Werdykt: **równoważne**, gdy CI mieści się w (−m, m); **różne**, gdy CI wyklucza 0 (bez korekty Holma); inaczej
**nierozstrzygnięte**. Marginesy: m = 0.147 (pomijalny, Romano i in. 2006) i m = 0.33 (mały).

| Para | Seedy | m = 0.147: równ. / różne / nierozstrz. | m = 0.33: równ. / różne / nierozstrz. | mediana δ |
|---|---|---|---|---|
| S4′ vs S5 | 1–30 | 0 / 7 / 9 | 5 / 7 / 4 | +0.09 |
| S5 vs `inherited_cost` | 1–30 | 0 / 0 / 16 | 7 / 0 / 9 | +0.04 |
| M9 vs M10 | 1–30 | 0 / 4 / 12 | 2 / 4 / 10 | +0.04 |
| M9 vs M10 | 31–60 | 0 / 1 / 15 | 10 / 1 / 5 | −0.05 |
| S2 vs S1 | 1–30 | 0 / 1 / 15 | 6 / 1 / 9 | +0.12 |
| S3 vs S2 | 1–30 | 0 / 0 / 16 | 12 / 0 / 4 | −0.06 |
| S4 vs S3 | 1–30 | 0 / 6 / 10 | 2 / 6 / 8 | +0.20 |
| S5 vs `f1_truncation` | 1–30 | 0 / 0 / 16 | 9 / 0 / 7 | +0.07 |
| S5 vs `transient_donors` | 1–30 | 0 / 0 / 16 | 7 / 0 / 9 | −0.00 |
| S5 vs `threshold_permissive` | 1–30 | 0 / 2 / 14 | 8 / 2 / 6 | −0.02 |
| S5 vs bartnik_p3 | 31–60 | 0 / 6 / 10 | 3 / 6 / 7 | +0.11 |
| S5 vs M9 | 31–60 | 0 / 7 / 9 | 1 / 7 / 8 | +0.12 |
| S5 vs M10 | 31–60 | 0 / 7 / 9 | 2 / 7 / 7 | +0.01 |

Wnioski:

- Przy n = 30 na ramię **równoważności na marginesie pomijalnym nie da się wykazać w żadnej komórce** (szerokość CI δ ≈ ±0.25).
  „Brak różnicy” z v004 znaczy więc „brak dowodu różnicy”, nie „równoważne”.
- Na marginesie małym (0.33) najmocniej równoważne są S3 vs S2 (12/16), M9 vs M10 na seedach 31–60 (10/16),
  `f1_truncation` (9/16). `inherited_cost` vs S5: 7/16 równoważne, 0 różnych — zdanie „świeże f2 nie jest źródłem przewagi”
  można pisać tylko jako „brak różnicy, równoważność na marginesie małym w 7/16 komórek”.
- Przejścia S2→S1 i S4→S3 były w Q2 „0/0/16” po Holmie, a bez korekty mają 1 i 6 komórek z CI wykluczającym 0, wszystkie
  na korzyść późniejszego etapu.
- S5 wobec kanonicznych P3 (bartnik, M9, M10) **nie jest remisem**: na C10/FMN przy b ≥ 100 S5 lepszy (δ do +0.80),
  na NHB przy b ≤ 200 gorszy od M9/M10 (δ −0.33…−0.47) i od bartnik przy b = 50. Zdanie z raportu 02 „przeważnie remisuje”
  trzeba zastąpić „wynik zależy od przestrzeni”.
- Komórki „różne” są bez korekty na wiele porównań — to opis, nie test potwierdzający.

## 2. S4′ vs S5 bezpośrednio (seedy 1–30)

| Przestrzeń | b=50 | 100 | 200 | 350 |
|---|---|---|---|---|
| C10 | +0.24 · | +0.10 · | +0.08 ≈ | +0.04 ≈ |
| CRC | +0.24 · | −0.16 · | **−0.34** | **−0.50** (p=0.001) |
| FMN | +0.09 ≈ | +0.04 ≈ | −0.05 ≈ | **−0.29** |
| NHB | **+0.25** | **+0.30** (p=0.047) | **+0.31** (p=0.039) | **+0.44** (p=0.003) |

δ > 0 = S4′ lepszy; pogrubione = CI wyklucza 0; ≈ = równoważne przy m = 0.33; · = nierozstrzygnięte; p = MWU bez korekty.

Wniosek: S4′ i S5 **nie są równoważne** — S4′ lepszy na NHB we wszystkich budżetach, S5 lepszy na CRC (b ≥ 200) i FMN
(b = 350); na C10 bez różnicy. Do B4: opisywać S4′ jako alternatywę o innym profilu, nie jako „równoważną S5”.
(Dla v005 porównanie jest tylko historią v004 — `v005-plan.md` A5.)

## 3. Dekompozycja HV: tani vs dokładny koniec frontu (JAHS, front zamrożony A6)

Podział osi f2 w medianie f2 punktów zamrożonego frontu (połowa punktów frontu po każdej stronie). Część „tania” to tylko
1–6% HV frontu (C10 6.3%, CRC 2.0%, FMN 1.3%) — HV jest zdominowane przez prostokąt punktu o najlepszym f1, więc
`hv_rel` ≈ część „dokładna”. Podział „połowa HV” wypadał poza zakresem f2 frontu (CRC: t = 0.80 > max f2 0.37) i nie jest
użyty.

Mediana (po 12 komórkach JAHS) różnicy S5 − ramię, w ułamku danej części frontu, seedy 31–60:

| Ramię | tania część | dokładna część |
|---|---|---|
| RS | +0.017 | +0.004 |
| bartnik_p3 / M9 / M10 | +0.035 / +0.063 / +0.051 | +0.001 / −0.002 / −0.001 |
| Vizier | +0.022 | −0.005 |
| BANANAS | −0.027 | −0.001 |
| SH-EMOA / TPE / NSGA-III | −0.004 / 0.000 / −0.005 | 0.000 / 0.000 / +0.001 |

Wnioski: przewaga S5 nad kanonicznymi P3 i Vizierem leży w taniej części frontu (pokrycie osi kosztu, zgodnie z §3.1
raportu 02), ale ta część waży 1–6% HV. Na części dokładnej S5 lekko przegrywa z M9/M10 i Vizierem. BANANAS bije S5 w taniej
części. Wniosek dla v005: HV względny słabo widzi tani koniec frontu — warto raportować obie części osobno (do prerejestracji
v005, A12).

## 4. Duplikaty

`duplication_rate` = udział propozycji, które już były w historii, liczony w chwili propozycji (powtórki idą z cache i nie
zużywają budżetu). Mediany (wszystkie przestrzenie i budżety): S5 0.40, warianty S5 0.38–0.49, bartnik_p3 0.53, M9 0.50,
M10 0.48, S4′ 0.66, P3-alone 0.94, MOEA/D 0.95; TPE 0.08, SH-EMOA 0.26, NSGA-III 0.05; RS, BANANAS, BO z GP ≈ 0.

Wniosek: rodzina P3 marnuje 40–66% propozycji na powtórki (bez kosztu ewaluacji, ale z kosztem czasu optymalizatora);
MOEA/D w v004 to znany problem (naprawiony w v005, `v005-plan.md`). S4′ ma najwięcej duplikatów w rodzinie S.
