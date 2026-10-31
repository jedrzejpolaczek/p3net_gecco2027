# 02 — Analiza wyników v004

Przebieg 2 z `notes/analysis-v004/PROMPTS.md`. Opiera się na raporcie 1 (`01-implementation-audit.md`, dalej „R1 §x”).
Wszystkie obliczenia na kopii skryptów `notes/analysis-v004/*.py` poza repo (katalog scratchpad sesji, `V004_OUT` = `…/scratchpad/out`)
oraz na własnych skryptach w tym samym katalogu (`q1.py`, `augment.py`, `mech*.py` — nazwy podane przy liczbach).
Repo nie było zmieniane poza tym plikiem.

## Stan sekcji

| # | Sekcja | Stan |
|---|---|---|
| 0 | Uruchomienie i weryfikacja skryptów | zrobione |
| 1 | Odchylenia od prerejestracji | zrobione |
| 2 | Q1–Q7 | zrobione |
| 3 | Mechanizmy | zrobione |
| 4 | Analizy drugorzędne (prereg §5) | zrobione (bez posthoc JAHS) |
| 5 | Jakość × koszt | zrobione |
| 6 | Wyjaśnienia alternatywne, trafność | zrobione |
| 7 | Lista wniosków | zrobione |
| 8 | Rozbieżności z `INITIAL_FINDINGS.md` | zrobione |

Konwencje: komórka = (przestrzeń, budżet). Skróty przestrzeni: C10 = JAHS cifar10, CRC = JAHS colorectal_histology, FMN = JAHS
fashion_mnist, NHB = NAS-HPO-Bench-II, prot/nav/park/slice = FCNet, NB201 = NAS-Bench-201. Metryka: JAHS i NB201 — HV względne do
zamrożonego frontu (wyżej lepiej, „HV”), NHB i FCNet — IGD+ znormalizowane do zakresu frontu wyroczni (niżej lepiej). δ = Cliff's δ,
**dodatnie = lepiej dla S5** (`p3net_cascade`); „+” = S5 istotnie lepszy (Holm w komórce, α=0.05), „−” = istotnie gorszy, „·” = brak
odrzucenia. Liczności zawsze z kierunkiem: „a+/b−/c·”. Siła dowodu (1)–(4) wg CONTEXT.md.

---

## 0. Uruchomienie i weryfikacja skryptów

**Uruchomienie.** `run_all.sh` (kopia) przeczytał 51 900 + 2 160 plików, 0 błędów odczytu; `per_run.csv` 54 060 wierszy,
`comparisons.csv` 3 570 porównań, `timing.csv` 128 przebiegów s9.

**Weryfikacja metryk** (`verify_metrics.py`, 60 losowych przebiegów ze wszystkich przestrzeni): HV skryptu (`analyze.hv2` / front)
vs `p3net.metrics.hypervolume.hypervolume_relative_to_best_known_front` — maks. różnica 5.6·10⁻¹⁶; IGD+ skryptu vs
`p3net.metrics.igd_plus.igd_plus(normalise=True)` — maks. różnica 9.7·10⁻¹⁷. Skrypt liczy IGD+ na niezdominowanym podzbiorze, biblioteka na
wszystkich punktach — dla IGD+ to równoważne (punkt zdominowany nigdy nie daje mniejszej odległości d⁺). **Metryki poprawne.**

**Konwencja znaku δ** sprawdzona na wszystkich istotnych porównaniach Q1: δ > 0 ⇔ mediana S5 lepsza (HV większe / IGD+ mniejsze) w 100%
przypadków. W `vsRS` referencją jest RS (δ < 0 = ramię bije RS); w Q2 δ > 0 = późniejszy etap lepszy. Zgodne z README.

**Zamrożone fronty** (`fronts_info.json`): C10 85 punktów, CRC 25, FMN 29 — z ~590 tys. punktów etapów s1+s3+s7, seedy 1–30 (zgodnie z prereg
§3; zawiera punkty GP z gp-small — odchylenie 3 z CONTEXT.md). Punkt odniesienia = nadir puli + 10⁻⁶: C10 (95.45, 1.531), CRC
(93.97, 1.531), FMN (95.44, 1.073). NB201: front 15 punktów z etapu s5 (patrz §1).

**Uwagi do skryptów (bez wpływu na poprawność liczb, ale na interpretację):**
1. **Nadir puli jako punkt odniesienia** (zgodny z prereg) leży przy błędzie ~95% i rozmiarze ~1.5 MB — HV względne nawet przebiegu RS wynosi
   0.93–0.99; różnice między ramionami są w 3.–4. miejscu po przecinku. Dlatego obok HV podaję też „domknięcie luki” względem RS i
   najlepsze f1 (§2.0).
2. `summaries.py`, ranking: kolumna „n=32” to maksymalna liczba ramion w komórce, nie liczba komórek; rankingi mieszają ramiona z 4 i z 2
   budżetami (GP) — średnia ranga GP pochodzi tylko z b=50/100, gdzie wszyscy są gorsi.
3. `summaries.py`, koszt na FCNet: zegar z przebiegów równoległych s8 (orientacyjny, README to zaznacza); „x0.0” = ramię szybsze o rząd
   wielkości, nie zero.
4. Rodzina `vsRS` liczy Holma po **wszystkich ~50 ramionach** w komórce (łącznie z etapami s2/s4) — to nie jest rodzina prerejestrowana
   (checklista A4), moc znacznie mniejsza niż w Q1. Traktuję ją opisowo; S5 vs RS biorę z rodziny Q1.
5. `ladder.py`, część B: Spearman między predykowaną a prawdziwą *poprawą względem przodka*. Dla wariantów RF predykowana poprawa to
   f(x₀) − RF(x), prawdziwa f(x₀) − f(x): **oba zawierają ten sam składnik f(x₀)**, który zawyża korelację; dla S5 predykowana poprawa to
   g(x₀) − g(x) (bez f(x₀), R1 §3.2). Porównanie ρ S5 vs RF jest więc obciążone na korzyść RF. Poprawiona miara w §4.3.
6. `ladder.py` założenie „`surrogate_quality_log` = tylko zaakceptowane i ocenione kandydatury” — **potwierdzone w kodzie** (R1 §17:
   `p3net.py:376-387, 674-695` — tylko członkowie C* zaproponowani do ewaluacji, predykcja = końcowa ocena łańcucha).
7. Krzywe anytime z `augment.py` liczone po liczbie ewaluacji; dla ramion MF to nie jest oś kosztu (pominięte w §4.1).

---

## 1. Odchylenia od prerejestracji (`v004-preregistration.md`, §7 pusta)

| # | Odchylenie | Status | Dowód |
|---|---|---|---|
| 1 | GP (Vizier, qNEHVI, qParEGO) tylko b=50/100, osobny run root | **potwierdzone** | 720 przebiegów/ramię, wszystkie z gp-small (R1 §1.9); w Q1 przy b=200/350 rodzina Holma ma 21 ramion zamiast 24 |
| 2 | Kod raportujący używa sparowanego Wilcoxona | **potwierdzone** | `stats/significance.py:109` `wilcoxon(...)`; analiza tutaj używa MWU (zgodnie z prereg) |
| 3 | Front JAHS zawiera punkty GP z gp-small | **potwierdzone**, zgodne z literą §3 (to ramiona s1) | `analyze.py:FRONT_METHODS` |
| 4 | Retrening punktu kolanowego (§5, faza 4b) | **nie wykonano** | brak skryptu w `scripts/` i brak wyników w `results/`; brak względem prerejestracji |
| 5 | Front NB201 „z s1+s3+s7” | **niewykonalne literalnie** — NB201 jest tylko w s5; skrypt bierze wszystkie przebiegi s5, seedy 1–30 (15 punktów) | `analyze.py:153`; NB201 ma enumerowalny front wyroczni (15 625 architektur), nieużyty |
| 6 | Jakość decyzji surogatu z `posthoc_metrics.py` (§5) | **nie wykonano** — brak wyjść `posthoc` w `results/` | sprawdzone `find results -iname '*posthoc*'`; tu zastępczo: `surrogate_quality_log` (wyselekcjonowany) i własne etykietowanie dla przestrzeni tabelarycznych (§4.3) |
| 7 | Luki generalizacji (test, train–val, val–test) | **nie policzone w repo** (wymagają `posthoc_metrics.py`) | §4.6 — częściowo policzone tutaj dla przestrzeni tabelarycznych |
| 8 | Brakujące przebiegi | **brak** | wszystkie 101 wpisów `failures.jsonl` (69× „No space left on device” w s6 + zdarzenia bez etapu; 3 linie nieparsowalne) mają kompletny plik w `raw/`; liczności per ramię zgadzają się z planem (R1 §1.9) |
| 9 | Restarty OOM w gp-small poza `failures.jsonl` | potwierdzone z CONTEXT.md; zapis atomowy całego przebiegu ⇒ brak częściowych historii (R1 §9.1) | — |
| 10 | Rodzina „vs RS” | nie jest w prereg (A4) — opisowa | §0 uwaga 4 |
| 11 | Etap s9 (Vizier przy 350) | wbrew checkliście A5 **wszystkie 4 punkty Vizier są w s9** (128/128 kompletne, `stage_status.json`), szczytowe RSS do 30.6 GB | `timing.csv` |

---

## 2. Pytania Q1–Q7

### 2.0 Skala efektów — jak czytać liczby

Tabela per komórka (`cells.py`): mediana S5 [IQR], mediana RS, różnica bezwzględna, **domknięcie luki** = (S5 − RS)/(ideał − RS)
(ideał: HV = 1, IGD+ = 0; ułamek odległości RS→ideał pokonany przez S5), najlepsze ramię spośród ramion Q1 + MF (mediana) i jego
przewaga nad S5.

**Seedy 31–60 (potwierdzające), przestrzenie główne**

| Komórka | S5 [IQR] | RS | S5−RS | domkn. luki | najlepsze ramię | najl.−S5 |
|---|---|---|---|---|---|---|
| C10/50 | 0.9519 [0.9399–0.9625] | 0.9554 | −0.0034 | −0.08 | asha_mo 0.9689 | +0.0170 |
| C10/100 | 0.9672 [0.9640–0.9708] | 0.9631 | +0.0042 | +0.11 | asha_mo 0.9743 | +0.0070 |
| C10/200 | 0.9747 [0.9707–0.9779] | 0.9691 | +0.0056 | +0.18 | tpe 0.9783 | +0.0036 |
| C10/350 | 0.9781 [0.9742–0.9810] | 0.9731 | +0.0051 | +0.19 | sh_emoa 0.9823 | +0.0041 |
| CRC/50 | 0.9858 [0.9832–0.9871] | 0.9802 | +0.0056 | +0.28 | asha_mo 0.9877 | +0.0019 |
| CRC/100 | 0.9898 [0.9876–0.9911] | 0.9853 | +0.0045 | +0.30 | oss_vizier 0.9928 | +0.0030 |
| CRC/200 | 0.9928 [0.9906–0.9938] | 0.9890 | +0.0037 | +0.34 | moead 0.9945 | +0.0017 |
| CRC/350 | 0.9942 [0.9929–0.9950] | 0.9902 | +0.0040 | +0.41 | bananas_mo 0.9957 | +0.0015 |
| FMN/50 | 0.9330 [0.9217–0.9577] | 0.9299 | +0.0031 | +0.04 | asha_mo 0.9765 | +0.0436 |
| FMN/100 | 0.9660 [0.9477–0.9793] | 0.9639 | +0.0021 | +0.06 | asha_mo 0.9817 | +0.0157 |
| FMN/200 | 0.9755 [0.9666–0.9873] | 0.9669 | +0.0086 | +0.26 | asha_mo 0.9877 | +0.0122 |
| FMN/350 | 0.9886 [0.9764–0.9915] | 0.9711 | +0.0175 | +0.61 | bananas_mo 0.9942 | +0.0055 |
| NHB/50 | 0.0457 [0.0408–0.0677] | 0.0531 | −0.0074 | +0.14 | oss_vizier 0.0345 | −0.0112 |
| NHB/100 | 0.0319 [0.0256–0.0413] | 0.0436 | −0.0117 | +0.27 | oss_vizier 0.0195 | −0.0124 |
| NHB/200 | 0.0215 [0.0185–0.0282] | 0.0350 | −0.0134 | +0.38 | sh_emoa 0.0146 | −0.0069 |
| NHB/350 | 0.0169 [0.0127–0.0193] | 0.0319 | −0.0150 | +0.47 | sh_emoa 0.0078 | −0.0091 |

**FCNet (seedy 1–30)**

| Komórka | S5 [IQR] | RS | S5−RS | domkn. luki | najlepsze ramię | najl.−S5 |
|---|---|---|---|---|---|---|
| prot/50 | 0.1730 [0.1121–0.2206] | 0.2116 | −0.0386 | +0.18 | oss_vizier 0.0383 | −0.1348 |
| prot/100 | 0.1049 [0.0857–0.1266] | 0.1373 | −0.0323 | +0.24 | oss_vizier 0.0119 | −0.0930 |
| prot/200 | 0.0717 [0.0418–0.0985] | 0.1072 | −0.0354 | +0.33 | przewozniczek_p3elympus 0.0119 | −0.0599 |
| prot/350 | 0.0538 [0.0355–0.0808] | 0.0763 | −0.0225 | +0.29 | przewozniczek_p3elympus 0.0045 | −0.0493 |
| nav/50 | 0.0276 [0.0166–0.0578] | 0.0833 | −0.0556 | +0.67 | oss_vizier 0.0073 | −0.0203 |
| nav/100 | 0.0126 [0.0109–0.0256] | 0.0562 | −0.0436 | +0.78 | oss_vizier 0.0028 | −0.0097 |
| nav/200 | 0.0080 [0.0057–0.0107] | 0.0347 | −0.0267 | +0.77 | sh_emoa 0.0019 | −0.0060 |
| nav/350 | 0.0055 [0.0035–0.0081] | 0.0196 | −0.0141 | +0.72 | sh_emoa 0.0009 | −0.0046 |
| park/50 | 0.3591 [0.1740–0.6565] | 0.4339 | −0.0748 | +0.17 | oss_vizier 0.0846 | −0.2745 |
| park/100 | 0.1961 [0.1226–0.2745] | 0.2904 | −0.0943 | +0.32 | oss_vizier 0.0453 | −0.1508 |
| park/200 | 0.1131 [0.0838–0.1467] | 0.2247 | −0.1116 | +0.50 | nsganetv2 0.0493 | −0.0638 |
| park/350 | 0.0742 [0.0530–0.1247] | 0.1618 | −0.0876 | +0.54 | sh_emoa 0.0198 | −0.0544 |
| slice/50 | 0.0454 [0.0303–0.0753] | 0.0675 | −0.0220 | +0.33 | oss_vizier 0.0086 | −0.0368 |
| slice/100 | 0.0233 [0.0182–0.0305] | 0.0505 | −0.0272 | +0.54 | oss_vizier 0.0030 | −0.0203 |
| slice/200 | 0.0154 [0.0108–0.0172] | 0.0345 | −0.0191 | +0.55 | sh_emoa 0.0035 | −0.0119 |
| slice/350 | 0.0113 [0.0087–0.0142] | 0.0232 | −0.0120 | +0.51 | sh_emoa 0.0011 | −0.0102 |

Jak oceniać znaczenie praktyczne:
- **JAHS:** różnice HV między ramionami to 0.001–0.02, ale przy punkcie odniesienia w nadirze (~95% błędu) nawet RS ma HV 0.93–0.99.
  Domknięcie luki daje lepszą skalę: S5 przy b ≥ 100 domyka 6–61% luki RS→front; najlepsze ramiona — zwykle 2–3× więcej.
  Rozrzut między seedami (IQR S5) jest tego samego rzędu co różnice między ramionami (np. FMN/350: IQR 0.015, S5−RS 0.018).
- **Zmienność bloku seedów:** mediana |przesunięcie mediany ramienia między seedami 1–30 a 31–60| = 0.0011 (C10), 0.0008 (CRC),
  0.0039 (FMN), 0.0027 (NHB); mediana |ramię − S5| w 31–60 = 0.0031 / 0.0017 / 0.0094 / 0.0066 (`seedshift.py`). Różnice rzędu
  przesunięcia bloku (~⅓ typowej różnicy) nie powinny być interpretowane jako przewagi.
- **NHB/FCNet (IGD+):** IGD+ = średnia znormalizowana odległość (w ułamkach zakresu frontu wyroczni) od frontu wyroczni do zbioru
  ramienia. Na FCNet różnice S5 vs najlepszy są duże w sensie praktycznym (prot/350: 0.054 vs 0.0045 — rząd wielkości).
- **Najlepsze f1** (minimalny błąd walidacyjny wśród ocenionych, `ranks.py`, seedy 31–60): S5 jest w rankingu ramion Q1 na miejscu
  5–23 (C10 6–16, CRC 10–13, **FMN 19–23**, NHB 5–11), a różnica do najlepszego ramienia to 0.3–0.5 p.p. błędu na JAHS i 0.4–0.8 p.p.
  na NHB. **HV S5 jest więc lepszy niż jego najlepsze f1** — przewaga S5 leży w pokryciu osi kosztu (mechanizm: §3.1).

### 2.1 Q1 — S5 vs ramiona porównawcze

Macierze (`q1.py`): „+” S5 istotnie lepszy, „−” istotnie gorszy, „·” brak odrzucenia; Holm w komórce (24 ramiona przy b ≤ 100,
21 przy b ≥ 200). Kolejność kolumn: C10, CRC, FMN, NHB × 50/100/200/350.

**Seedy 31–60 (potwierdzające)**

| Ramię | C10 | CRC | FMN | NHB | +/−/· | mediana δ |
|---|---|---|---|---|---|---|
| mo_ls | + + + + | + + + + | + + + + | + + · · | 14/0/2 | 0.73 |
| p3_alone | · + + + | + + + · | · + + + | · + + + | 12/0/4 | 0.56 |
| p3_alone_pop20 | · + + + | + + + + | · + + + | · · + + | 12/0/4 | 0.61 |
| p3_alone_pop40 | · + + + | + + + + | · · + + | · + + + | 12/0/4 | 0.58 |
| mo_bohb | · · + + | + + + + | · · + + | · + + + | 11/0/5 | 0.59 |
| random_search | · · + + | + + + + | · · · + | · + + + | 10/0/6 | 0.61 |
| reinforce_mo | · · + + | + + + + | · · · + | · + + + | 10/0/6 | 0.60 |
| p3_absolute | · · + + | · + + + | · · · + | · · + + | 8/0/8 | 0.40 |
| p3net (S4) | · · · + | · · · + | · · · + | · · + + | 5/0/11 | 0.38 |
| bartnik_p3 | · · + + | · · · · | · · · + | · · · · | 3/0/13 | 0.11 |
| nsganetv2 | · · · · | + · · · | · · + + | · · · · | 3/0/13 | 0.16 |
| canonical_p3_scalar_fihc | · · · · | · · · · | · · + + | · · · · | 2/0/14 | 0.01 |
| moead | · · · · | · · · · | · · · + | · · · + | 2/0/14 | 0.26 |
| smac3_parego | · · · · | + + · · | · · · · | · · · · | 2/0/14 | 0.11 |
| regularized_evolution_mo | · · · · | · · · · | · · · · | · · · + | 1/0/15 | 0.08 |
| botorch_qparego (b≤100) | · · | + · | · · | · · | 1/0/7 | 0.09 |
| botorch_qnehvi (b≤100) | · · | · · | · · | · · | 0/0/8 | 0.07 |
| przewozniczek_p3elympus | · · · · | · · · · | · · + + | − · · · | 2/1/13 | 0.12 |
| nsga_net | · · · · | + · · · | · · · · | · · · − | 1/1/14 | 0.03 |
| nsga3 | · · · · | · · · · | · · · · | · · · − | 0/1/15 | −0.07 |
| oss_vizier (b≤100) | · · | · − | · · | · − | 0/2/6 | −0.15 |
| bananas_mo | · · · · | · · · · | · · − − | · · · − | 0/3/13 | −0.30 |
| sh_emoa | · · · − | · · · · | · · · · | · · − − | 0/3/13 | −0.11 |
| tpe | · − − − | · · · · | · · · · | · · · · | 0/3/13 | −0.08 |

Suma (360 par ramię×komórka): 111+/14−/235·. Średnia ranga mediany komórki
wśród 25 ramion Q1 (`ranks.py`): BANANAS 4.0, SH-EMOA 5.2, TPE 6.2, Vizier 6.4 (tylko b ≤ 100), **S5 7.2**, NSGA-III 7.6, qNEHVI 8.5,
… RS 17.2, MO-LS 21.5. Ranga S5 zależy od budżetu: 11.5 (b=50), 5.8 (100), 5.2 (200), 6.5 (350).

**Seedy 1–30 (eksploracyjne):** 81+/23−/256·. Ten sam układ, ale słabszy dla S5: RS 8/0/8, przegrane z SH-EMOA 0/5, BANANAS 0/6,
TPE 1/2, NSGA-III 0/3, NSGA-Net 0/2, Vizier 0/3, SMAC3 3/2.

**Zgodność 1–30 vs 31–60 (B10)** (`b10.py`, 360 par ramię×komórka): **zero zmian znaku wśród istotnych**; 76 par „+” w obu, 12 „−”
w obu, 219 „·” w obu; zmiany klasy: 35× „·”→„+”, 11× „−”→„·”, 5× „+”→„·”, 2× „·”→„−”. Znak δ zgodny w 80.8% par, ρ Spearmana δ =
0.83. Przesunięcie jest jednokierunkowe — **na seedach potwierdzających S5 wypada lepiej, nie gorzej**. Siła dowodu (2).

Wnioski Q1 (z siłą dowodu):
- S5 jest **istotnie lepszy od RS w 10/16 komórek, nigdy gorszy** (31–60); w 1–30: 8/16, nigdy gorszy. Różnice bezwzględne:
  JAHS +0.002…+0.018 HV (domknięcie luki 4–61%), NHB −0.007…−0.015 IGD+ (14–47%). Przy b=50 brak różnic z RS na JAHS (S5 wręcz
  nieco niżej na C10/50 i FMN/50). Siła (2).
- S5 bije wyraźnie ramiona słabe: MO-LS, P3-alone (×3), MO-BOHB, REINFORCE, P3-absolute, S4. Siła (2). Wierność tych ramion (R1 §5,
  §7, §10) — MO-BOHB i P3-alone są uproszczonymi wariantami, więc wygrana z nimi nie jest wygraną z „ustalonym baseline’em” (B5).
- S5 **nie jest najlepszy**: przegrywa istotnie z TPE (C10/100–350), SH-EMOA (C10/350, NHB/200–350), BANANAS (FMN/200–350,
  NHB/350), Vizier (CRC/100, NHB/100), NSGA-III i NSGA-Net (NHB/350). Siła (2) dla kierunku, (3) dla „kto jest najlepszy” (rangi
  opisowe).
- Z kanonicznymi P3 (bartnik, M9, M10) ~~S5 przeważnie remisuje na przestrzeniach głównych (3–2 wygrane, 0–1 porażka). Siła (2).~~
  **Sprostowanie 2026-10-31 (A9, raport 04 §1):** to nie remis — wynik zależy od przestrzeni: na C10/FMN przy b ≥ 100 S5 lepszy
  (δ do +0.80), na NHB przy b ≤ 200 gorszy od M9/M10 (δ −0.33…−0.47) i od bartnik przy b = 50. Bez korekty Holma — opis.

### 2.2 Q2 — droga projektowa S1 → S2 → S3 → S4 → S5 (+ S4′), seedy 1–30

| Przejście | +/−/· (16 komórek główn.) | mediana δ | mediana różnicy (JAHS HV / NHB IGD+) |
|---|---|---|---|
| S1 → S2 (świeże f2) | 0/0/16 | +0.12 | +0.0005 / −0.0015 |
| S2 → S3 (RidgeCV) | 0/0/16 | −0.06 | −0.0004 / +0.0003 |
| S3 → S4 (warm start + kryterium HV) | 0/0/16 | +0.20 | +0.0015 / −0.0058 |
| S4 → S4′ (mieszanie od 2 osobników) | **6/0/10** (C10/350, CRC/50, CRC/200, CRC/350, NHB/200, NHB/350) | +0.30 | +0.0018 / −0.0101 |
| S4 → S5 (`cascade`) | **5/0/11** (C10/350, CRC/200, CRC/350, NHB/200, NHB/350) | +0.21 | +0.0020 / −0.0061 |

(„+” = późniejszy etap istotnie lepszy.) Na FCNet S4 → S5 7/0/9, na NB201 1/0/1 (b=350).
Wnioski: (i) pierwsze trzy przejścia nie dają istotnej zmiany w żadnej komórce, choć mediany δ są dodatnie przy S1→S2 i S3→S4 —
efekty małe, kierunkowo spójne (siła (3)); (ii) **S4′ jest lepszy od S4 w 6/16 i nigdzie gorszy** — sprzeczne z opisem v0.0.3
(„regressed severely”), i tak samo dobry jak S5 (bezpośrednio S4′ vs S5 nie było w Q2; mediany zbliżone); (iii) S4 → S5 to jedyny
etap z poprawą w Q2 obok S4′, efekt rośnie z budżetem (wszystkie istotne komórki przy b ≥ 200). Siła (3) (seedy 1–30, interwencja
jednoosiowa ⇒ dla samego przejścia (1)).

### 2.3 Q3 — obrona decyzji (16 wariantów S5, seedy 1–30, 4 przestrzenie główne)

| Wariant | +/−/· | mediana δ | uwagi |
|---|---|---|---|
| `grow_on_stall` | **8/0/8** | +0.43 | S5 lepszy przy b ≥ 200 (C10/200–350, CRC/100–350, FMN/350, NHB/200–350) |
| `kappa1_thr0` | 0/**1**/15 | −0.16 | wariant lepszy w NHB/350 |
| `inherited_cost` | 0/0/16 | +0.04 | **B3: brak efektu świeżego f2 także na NHB** (różnica IGD+ +0.0005) |
| `f1_truncation`, `transient_donors`, `threshold_permissive` | 0/0/16 | −0.02…+0.07 | — |
| 11 komórek κ × próg | 0/0/16 każda (poza κ1_thr0) | −0.16…0.00 | na NHB wszystkie mediany IGD+ lepsze od S5 o 0.002–0.004 (nieistotne); κ2log ≈ κ∞ zgodnie z R1 §3.5 |

Wnioski: jedyna decyzja projektowa obroniona istotnie to **reinjekcja zamiast wzrostu przy pustym C*** (siła (1)/(3): interwencja
jednoosiowa, seedy eksploracyjne). Pozostałe wybory są obojętne w granicach mocy (siła (3)); na NHB kierunkowo lepsze byłyby mniejsze κ
lub próg > 0 (hipoteza (4)). Skala progów 0.01–0.02 p.p. jest pomijalna (R1 §3.5), więc „próg nie ma znaczenia” dotyczy tylko takich
progów. `inherited_cost` ≈ S5 na NHB (f2 = czas z tabeli): darmowe f2 nie jest źródłem przewagi S5 na NHB (siła (1) na tej przestrzeni);
na FCNet nieizolowane (R1 §3.3).

### 2.4 Q4 — warianty surogatu (S5 jako referencja)

| Ramię | 31–60 główne | 1–30 główne | FCNet | komentarz |
|---|---|---|---|---|
| `p3_absolute_cascade` | 3/0/13 | 1/0/15 | 0/0/16 | S5 lepszy w FMN/350, NHB/200–350 |
| `p3net_bartnik` (RF) | 1/0/15 | 2/0/14 | 3/1/12 | RF ≈ S5 |
| `p3net_bartnik_fihc` (RF+FIHC) | 3/0/13 | 1/0/15 | **0/8/8** | lepszy od S5 na FCNet (prot/200–350, park/50–200, slice/100–350) |
| `p3net_elympus` (RF+FIHC-eLyMPuS) | 5/1/10 | 1/0/15 | 0/4/12 | na głównych gorszy od S5 w FMN/100–350, NHB/200–350; lepszy w CRC/200 |

Zgodność 1–30 vs 31–60 (64 pary): bez zmian znaku istotnych; 9× „·”→„+”. Drabinka (S5 → RF → RF+FIHC → RF+FIHC-eLyMPuS) — §3.3.
Wnioski: (i) **względny Ridge vs absolutny Ridge** (S5 vs `p3_absolute_cascade`): S5 lepszy lub równy, nigdy gorszy (3/0/13
potwierdzające) — różnica dotyczy kotwiczenia/akceptacji/regularyzacji, nie linkage (R1 §3.2); siła (2) dla kierunku, (1) dla
interpretacji mechanicznej; (ii) **RF zamiast Ridge nie poprawia S5** na przestrzeniach głównych (siła (2)); (iii) FIHC na RF pomaga na
FCNet (8/16 lepiej od S5), szkodzi kierunkowo na JAHS/NHB (siła (3)).

### 2.5 Q5 — FCNet (seedy 1–30, opisowo)

| Ramię | +/−/· | | Ramię | +/−/· |
|---|---|---|---|---|
| mo_bohb | 11/0/5 | | mo_ls | 2/5/9 |
| random_search | 11/0/5 | | regularized_evolution_mo | 0/6/10 |
| reinforce_mo | 11/0/5 | | nsganetv2 | 1/6/9 |
| smac3_parego | 7/0/9 | | nsga3 | 1/8/7 |
| p3_absolute | 6/0/10 | | nsga_net | 1/8/7 |
| p3net (S4) | 5/0/11 | | oss_vizier (b≤100) | 0/8/0 |
| p3_alone_pop20 / pop40 | 4/0/12, 2/0/14 | | bartnik_p3 | 0/10/6 |
| p3_alone | 7/1/8 | | przewozniczek_p3elympus | 0/11/5 |
| moead, tpe, qNEHVI, qParEGO | bez istotnych | | bananas_mo | 0/12/4 |
| | | | sh_emoa | 0/12/4 |
| | | | canonical_p3_scalar_fihc | 0/13/3 |

Średnia ranga mediany komórki: Vizier 1.0 (b ≤ 100), M10 3.4, SH-EMOA 3.5, BANANAS 4.4, M9 5.2, Bartnik 6.4, …, **S5 13.0**, RS 21.2.
S5 bije RS 11/16 (różnice IGD+ 0.012–0.112, domknięcie luki 17–78%), ale **przegrywa z 10 ramionami**, w tym z całą rodziną
kanonicznego P3. **Q5 nie zgadza się z Q1 co do pozycji S5** (środek stawki na głównych vs dolna połowa na FCNet); zgadza się co do
„S5 > RS”. Siła (3) (opisowe, prereg §6).

### 2.6 Q6 — koszt praktyczny: §4.7 i §5.

### 2.7 Q7 — tor multi-fidelity (koszt w ekwiwalentach pełnych ewaluacji)

| Ramię | 31–60 główne | 1–30 główne | FCNet |
|---|---|---|---|
| hyperband_mo | 8/1/7 | 8/4/4 | 6/0/10 |
| bohb_mo | 10/1/5 | 9/4/3 | 3/3/10 |
| asha_mo | 2/**8**/6 | 1/**10**/5 | 0/**16**/0 |

ASHA bije S5 na JAHS przy wszystkich budżetach (31–60: C10 4/4, CRC/50, FMN/50–200), z dużą przewagą przy małym budżecie (FMN/50:
0.9765 vs 0.9330, C10/50: 0.9689 vs 0.9519); przegrywa z S5 na NHB/200–350. Na FCNet ASHA lepsza w 16/16. Hyperband i BOHB
przegrywają z S5 głównie na CRC i NHB, są lepsze na FMN/50. Zgodność 1–30 vs 31–60: 93.8% zgodnych znaków, bez zmian znaku istotnych.
Wnioski: przy równym koszcie w epokach **ASHA jest najsilniejszą metodą na JAHS i FCNet** (siła (2) na JAHS, (3) FCNet); mechanizm i
zastrzeżenie (front z ~połowy punktów, JAHS niższe wierności z surogatu, R1 §8) — §3.4.

### 2.8 NAS-Bench-201 (s5, opisowo, seedy 1–30)

| b | S5 | S4 | RF | RF+eLy | bartnik_p3 | M9 | M10 | MO-LS | RS |
|---|---|---|---|---|---|---|---|---|---|
| 100 | 0.9871 | 0.9860 | 0.9871 | 0.9848 | 0.9856 | 0.9854 | 0.9853 | 0.9750 | 0.9857 |
| 350 | 0.9952 | 0.9921 | 0.9949 | 0.9960 | 0.9935 | 0.9962 | 0.9958 | 0.9961 | 0.9918 |

Przy b=100 żadne ramię nie różni się od RS (poza MO-LS — gorszy); przy b=350 od RS odróżniają się (na korzyść) S5, RF, RF+eLy, M9,
M10, MO-LS; nie: S4, `bartnik_p3`. Różnice bezwzględne 0.003–0.004 HV przy medianach ~0.99 — sufit benchmarku (B6). Siła (3)/opis.

---

## 3. Mechanizmy

Pomocnicze pomiary w tej sekcji (wszystkie poza repo):
- `additivity.py` — addytywność krajobrazu per przestrzeń na **bezstronnej próbce**: unikalne punkty z historii wszystkich przebiegów RS
  (7.6–20.9 tys. unikalnych na przestrzeń, losowo 6000), 5-krotna CV;
- `coverage.py` — pokrycie osi kosztu przez fronty przebiegów;
- `surq.py` — jakość surogatu z `surrogate_quality_log` (miara bez obciążenia z §0 uw. 5);
- `mf.py` — korelacja wierności niskich z pełną i liczba przejrzanych konfiguracji w torze MF;
- `altref.py` — odporność rankingu JAHS na wybór punktu odniesienia HV.

### 3.0 Dwa fakty o krajobrazach, które tłumaczą większość wyników

**(a) Addytywność f1** (`additivity.py`, R² w CV; „pair” = Ridge z interakcjami parami; top10 = ρ Spearmana predykcji z prawdą w
najlepszym decylu):

| Przestrzeń | skośność f1 | R² addytywny (surowe f1) | R² z interakcjami | R² RF | ρ top10 addyt. | ρ top10 RF | R² addyt. (log f1) | R² addyt. f2 |
|---|---|---|---|---|---|---|---|---|
| C10 | 2.6 | 0.44 | 0.94 | 0.94 | 0.17 | 0.46 | 0.51 | 0.995 |
| CRC | 3.4 | 0.43 | 0.81 | 0.84 | 0.30 | 0.41 | 0.57 | 1.000 |
| FMN | 3.7 | 0.36 | 0.75 | 0.92 | −0.04 | 0.32 | 0.43 | 0.894 |
| NHB | 0.8 | 0.44 | 0.83 | 0.83 | 0.30 | 0.54 | 0.44 | 0.827 |
| NB201 | 2.9 | 0.48 | 0.77 | 0.87 | 0.10 | 0.56 | 0.63 | 1.000 |
| FCNet prot | 26 | 0.09 | 0.20 | 0.39 | 0.11 | 0.81 | 0.58 | 0.961 |
| FCNet nav | 98 | −0.00 | −0.01 | −0.36 | 0.19 | 0.42 | 0.71 | 0.766 |
| FCNet park | 87 | 0.00 | 0.00 | −0.49 | 0.07 | 0.62 | 0.70 | 0.698 |
| FCNet slice | 69 | 0.00 | 0.01 | 0.09 | −0.03 | 0.38 | 0.69 | 0.824 |

Wnioski (siła (1) dla własności krajobrazu na próbce RS; skutek dla metod — (3)):
- Na JAHS/NHB/NB201 model addytywny (klasa modelu S5) wyjaśnia ~40% wariancji f1, a interakcje parami podnoszą to do 75–94% —
  krajobrazy są **silnie nieaddytywne**. W najlepszym decylu (tam, gdzie leży front) addytywna predykcja ma ρ ≈ 0–0.3.
- Na FCNet f1 (MSE) jest ekstremalnie prawostronnie skośne (skośność 26–98): **addytywny Ridge na surowym f1 ma R² ≈ 0**; po
  logarytmie R² 0.58–0.71. S5 trenuje na surowym f1 (R1 §3.2), więc na FCNet jego surogat jest praktycznie ślepy. RF ma ujemne R² na
  surowej skali (wartości odstające), ale w najlepszym decylu porządkuje dobrze (ρ 0.38–0.81) — drzewa są niezmiennicze na monotoniczne
  przekształcenia celu.
- f2 jest prawie addytywne wszędzie (R² 0.70–1.00) — przewidywanie kosztu jest łatwe; trudne jest f1.

**(b) Gdzie leży wartość metryki.** Na JAHS najsilniejsze ramiona oceniają dużo tanich modeli: mediana f2 ocenionych punktów
(31–60, wszystkie budżety): ASHA 0.10 MB, BANANAS 0.13, Vizier 0.14, SH-EMOA 0.17 vs RS 0.36, S5 0.34, P3-alone 0.44. Analogicznie na
NHB (ASHA 99 s, Vizier 105, SH-EMOA 116 vs RS 160) i FCNet. HV z punktem odniesienia w nadirze nagradza oba końce frontu; ranking jest
jednak **odporny na wybór punktu odniesienia** (`altref.py`: przy punkcie 10% za nadirem zamrożonego frontu S5 ma średnią rangę 6.0 vs
7.0 przy nadirze puli; kolejność czołówki BANANAS, SH-EMOA, TPE, NSGA-III bez zmian). Siła (3).

### 3.1 Dlaczego S5 naprawił S4

Udział bootstrapu (losowego zapełniania poziomów) w propozycjach, seedy 1–30, przestrzenie główne, mediany:

| Ramię | b=50 | 100 | 200 | 350 | Q2/Q3 vs sąsiad |
|---|---|---|---|---|---|
| S1 | 0.89 | 0.91 | 0.94 | 0.96 | — |
| S3 | 0.87 | 0.90 | 0.93 | 0.96 | — |
| S4 | 0.67 | 0.77 | 0.85 | 0.91 | S3→S4 0/0/16 |
| S4′ (mieszanie od 2) | 0.04 | 0.02 | 0.01 | 0.006 | S4→S4′ 6/0/10 |
| **S5** | 0.16 | 0.18 | 0.22 | 0.27 | S4→S5 5/0/11 |
| S5 + `grow_on_stall` | 0.80 | 0.84 | 0.88 | 0.91 | S5 lepszy 8/0/8 |

Wyjaśnienie: w S4 (tylko najnowszy poziom aktywny) każde utknięcie poziomu tworzy nowy, dwa razy większy poziom, który trzeba
zapełnić losowo — przy b=350 ~91% propozycji to próbki jednostajne, więc S4 jest w praktyce RS z domieszką mieszania (S4 vs RS: 0/16
istotnych w 1–30 w rodzinie vsRS, 4/16 w 31–60). `cascade` utrzymuje wszystkie poziomy w mieszaniu, więc większość budżetu idzie na mieszanie elit
(warm start) zamiast na losowe wypełnianie. **Dowód konwergentny:** trzy niezależne interwencje, które obniżają udział bootstrapu (S4′,
S5) lub go podnoszą (`grow_on_stall`), przesuwają jakość w przewidywanym kierunku (siła (1)/(3): interwencje jednoosiowe na seedach
eksploracyjnych).
**Czy to wystarcza?** Nie w pełni: (i) wewnątrz S5 korelacja Spearmana udziału bootstrapu z jakością jest **dodatnia** w 13/16 komórek
(ρ −0.21…+0.35; więcej losowości = lepiej) — więc „próbki losowe są złe” nie jest mechanizmem; lepsza hipoteza (4): liczy się, czy
mieszanie działa na elitarnych, ciepło startowanych populacjach (S5, S4′), a nie ile jest losowych próbek; (ii) S4′ ma udział 0.6% i
jakość podobną do S5 — więc to nie „właściwa proporcja” bootstrapu, tylko jego brak w dużych, świeżych poziomach. Rozstrzygnięcie:
wariant S4 z ciepłym startem całego nowego poziomu (bez losowego dopełniania) albo S5 z ograniczeniem liczby poziomów.

### 3.2 Dlaczego S5 dobrze na JAHS, słabo na FCNet; dlaczego kanoniczne P3 odwrotnie

**Pokrycie osi kosztu** (`coverage.py`, b=350; `f2lo_rel` = najtańszy punkt frontu przebiegu względem zakresu f2 frontu odniesienia,
0 = osiąga najtańszy; `f1gap_rel` = (najlepsze f1 − najlepsze f1 frontu)/|najlepsze f1 frontu|):

| Grupa | S5 | RS | SH-EMOA | BANANAS | ASHA | M10 (kanon.) | RF+FIHC | NSGANetV2 |
|---|---|---|---|---|---|---|---|---|
| JAHS f2lo_rel / f1gap_rel | **0.013** / 0.090 | 0.017 / 0.108 | 0.015 / 0.061 | 0.004 / 0.099 | 0.007 / 0.096 | 0.022 / **0.058** | 0.022 / 0.061 | 0.026 / 0.046 |
| NHB | 0.008 / 0.070 | 0.009 / 0.089 | 0.002 / 0.076 | 0.009 / 0.054 | 0.007 / 0.070 | 0.012 / 0.026 | 0.009 / 0.019 | 0.023 / 0.015 |
| FCNet | 0.001 / **0.529** | 0.004 / 0.536 | 0.001 / 0.218 | 0.001 / 0.507 | 0.001 / 0.245 | 0.002 / 0.324 | 0.003 / 0.393 | 0.003 / 0.224 |

- **JAHS:** S5 dobrze pokrywa tani koniec frontu (3. najtańszy punkt), a jego najlepsze f1 jest przeciętne (f1gap 0.090 vs 0.046–0.061
  dla ramion z FIHC/NSGANetV2/SH-EMOA). Mechanizm (R1 §3.3, §3.6): wybór C* jest niezdominowany w (f̂1, **świeże f2**), a akceptacja
  kroków jest po f1 z surogatem o niskiej jakości rankingu (ρ ≈ 0.3–0.4, §4.3) — wyniki przemiatania są rozrzucone po osi f2, a f2 jest
  znane dokładnie; front jest szeroki i tani. HV to nagradza. Siła (3).
- **FCNet:** surogat S5 nie widzi f1 (R² ≈ 0, §3.0a), więc S5 ≈ „RS z mieszaniem i świeżym f2”: f1gap 0.529 ≈ RS 0.536. Ramiona z RF
  (kanoniczne P3, RF+FIHC), z modelami odpornymi na skalę (BANANAS na znormalizowanych celach) albo bez modelu, ale z selekcją
  (SH-EMOA, NSGA-II) zbliżają się do najlepszego f1 (f1gap 0.22–0.39), a IGD+ normalizowane do frontu wyroczni nagradza cały front.
  Siła (3); hipoteza rozstrzygalna (4): S5 z log(f1) w surogacie.
- **Kanoniczne P3 (M9, M10, bartnik_p3):** las losowy + FIHC po jednej współrzędnej optymalizują f1 skutecznie (najlepsze f1 w grupie
  na NHB/FCNet), ale f2 jest **przewidywane** (bez świeżego f2, R1 §4.1), a bramka jest po samym f1 — tani koniec frontu jest słabiej
  pokryty (JAHS f2lo_rel 0.020–0.023). Na NHB/FCNet (IGD+, front wyroczni) wygrywa jakość f1, na JAHS (HV) — pokrycie kosztu.
  Typ przestrzeni: FCNet (tylko HPO, małe dziedziny 2–6) i NHB (małe dziedziny 4–8) sprzyjają lokalnemu przeszukiwaniu po jednej
  współrzędnej (MO-LS na FCNet: ranga 24 → 4.8 od b=50 do b=350).

### 3.3 Drabinka S5 → RF → RF+FIHC → RF+FIHC-eLyMPuS

Kroki (`ladder.py`, kopia; seedy 31–60 na głównych, 1–30 na FCNet/NB201; MWU, Holm w komórce po 4 krokach; „lepiej” = późniejszy
etap istotnie lepszy):

| Krok | JAHS (12 komórek) | NHB (4) | FCNet (16) | NB201 (2) | mediana δ (FCNet/JAHS/NHB) |
|---|---|---|---|---|---|
| S5 → RF | 0 lepiej / 1 gorzej / 11 = | 0/0/4 | 1/3/12 | 0/0/2 | −0.06 / −0.24 / −0.29 |
| RF → RF+FIHC | 3/1/8 | 0/0/4 | **10**/0/6 | — | +0.43 / +0.16 / +0.08 |
| RF+FIHC → RF+FIHC-eLyMPuS | 0/0/12 | 0/0/4 | 0/0/16 | — | −0.06 / −0.02 / −0.19 |
| S5 → RF+FIHC-eLyMPuS | 1/3/8 | 0/2/2 | 4/0/12 | 0/0/2 | +0.28 / −0.15 / −0.35 |

**Jakość surogatu na ocenionych kandydatach** (`surq.py`, b=350, seedy 1–30, mediana po przebiegach; MAE = |f̂1 − f1| w jednostkach f1,
obciążenie = mediana f̂1 − f1, base = odsetek kandydatów rzeczywiście lepszych od przodka):

| Grupa | MAE S5 | MAE RF | MAE RF+FIHC | MAE AbsRidge | obciąż. S5 | obciąż. RF | base S5 | base RF | base RF+FIHC |
|---|---|---|---|---|---|---|---|---|---|
| JAHS | 5.08 | 0.49 | 0.26 | 2.25 | −4.60 | +0.10 | 0.49 | 0.90 | 0.81 |
| NHB | 10.98 | 3.24 | 1.53 | 7.19 | −9.27 | +0.59 | 0.51 | 0.87 | 0.83 |
| FCNet | 0.475 | 0.006 | 0.003 | 0.245 | −0.467 | +0.002 | 0.54 | 0.96 | 0.82 |
| NB201 | 3.29 | 0.54 | — | — | −2.95 | +0.06 | 0.61 | 0.87 | — |

- Las losowy przewiduje f1 wybranych kandydatów **~10× dokładniej** niż S5, a S5 jest **systematycznie optymistyczny** (f̂1 niższe od
  prawdy o 4.6 p.p. na JAHS, 9.3 na NHB) — klątwa zwycięzcy przy wyborze C* po predykcji i słabo regularyzowany model par (R1 §3.2).
  Połowa kandydatów S5 nie jest lepsza od przodka (base ≈ 0.5), przy RF — 87–96%.
- **Mimo to RF nie poprawia S5** na JAHS/NHB (0 lepiej) — dokładniejszy surogat f1 przesuwa kandydatów ku niższemu f1 i wyższemu f2
  (mediana f2 ocenionych punktów przy b=350: RF +2…+42%, RF+FIHC +9…+42%, RF+eLy +9…+65% względem S5; najlepsze f1 −2…−24%; `ladder.py` C).
  **Hipoteza „akceptacja po samym f1 psuje front po osi f2” jest wsparta**: na JAHS warianty RF mają gorszy tani koniec
  (f2lo_rel 0.019–0.022 vs 0.013 S5) i lepsze najlepsze f1 (f1gap 0.051–0.085 vs 0.090). Siła (3).
- Na FCNet ten sam przesuw pomaga, bo S5 nie ma tam żadnej informacji o f1 (3.0a) — RF+FIHC 10/16 lepiej od RF.
- **Krok eLyMPuS: 0/32 istotnych** (0/0/12, 0/0/4, 0/0/16), mediany δ lekko ujemne. Zgodne z R1 §4.3: zastąpienie bezpośredniego porównania
  przybliżonym (6–12% błędnych decyzji) na darmowej funkcji nie może pomóc. **Nie jest to dowód przeciw eLyMPuS** (R1 §4.3).
- Zastrzeżenie do porównań jakości: `surrogate_quality_log` zawiera tylko członków C* (wybór po predykcji) — optymizm S5 jest częściowo
  artefaktem selekcji; RF jest jej poddany tak samo, a obciążenie ma ~0, więc różnica jest realna.
- **Błąd S5 rośnie z głębokością łańcucha**, mimo że telescoping kolapsuje (R1 §3.2): mediana |f̂1 − f1| na JAHS 2.75 (głębokość 1),
  3.50 (2), 3.84 (3–4), 5.04 (5–8); NHB 7.8 → 10.9. Mechanizm: dłuższy łańcuch = kandydat dalej od przodka = ekstrapolacja modelu
  addytywnego dalej od danych, nie sumowanie błędów. Uwaga do R1 §3.5: mediana głębokości łańcucha logowanych kandydatów S5 to 7 na JAHS
  (κ=8; 75. percentyl = 8) i 5 na NHB (κ=6) — **κ bywa wiążące** w ≥25% łańcuchów, częściej niż wynikałoby z założenia R1; mimo to
  κ2log ≈ κ∞ w Q3 (0/0/16 obie).

### 3.4 Vizier, ASHA, SH-EMOA, BANANAS, TPE (mocne) oraz P3-alone, MO-BOHB, MO-LS, MOEA/D (słabe)

- **ASHA** (`mf.py`, b=350): przegląda **~5 300–5 900 konfiguracji** na JAHS i FCNet (vs 350 w torze jednowiernościowym), ~70% kosztu
  na niskich szczeblach; ρ(f1 przy 2 epokach, f1 przy 200) = 0.87 (C10), 0.68 (CRC), 0.48 (FMN); FCNet 0.73–0.90 przy 1 epoce. Promocja
  MO (NDS + crowding) z dokładnym f2 premiuje tanie konfiguracje (mediana f2 0.10 MB na JAHS). Na NHB tylko 1 211 konfiguracji (najniższy
  szczebel = 1 z 12 epok = 8% kosztu), więc przewaga znika (S5 lepszy na NHB/200–350). Zastrzeżenie R1 §8: na JAHS niższe wierności to
  predykcje surogatu JAHS przy `nepochs=e`, a koszt „wznowienia” jest modelowy — przewaga ASHA na JAHS może być częściowo artefaktem
  benchmarku-surogatu. Siła (3).
- **Vizier** (tylko b ≤ 100): najlepszy na NHB i FCNet (ranga 1.0), na JAHS średni (6.4). Na JAHS jego front nie sięga taniego końca
  (b=100: f2lo_rel 0.028, najgorszy w grupie po MO-LS) przy dobrym f1 (f1gap 0.110). Hipoteza (4): GP z jądrem kategorycznym dobrze
  modeluje małe tabelaryczne przestrzenie (NHB 8 wymiarów, FCNet 9 z dziedzinami 2–8), a na JAHS HV premiuje pokrycie kosztu, którego
  skalaryzacja HV w akwizycji przy 50–100 punktach nie zapewnia. Brak danych przy b ≥ 200.
- **SH-EMOA**: selekcja przeżycia po wkładzie HV (R1 §7.1) optymalizuje dokładnie metrykę JAHS; ocenia tanie modele (mediana f2 0.17 MB).
  Najlepszy lub drugi przy b=350 na NHB i FCNet. **BANANAS**: skalaryzacja Chebysheva z losową wagą na znormalizowanych celach +
  mutacje frontu → najtańszy front (f2lo_rel 0.004 na JAHS). **TPE**: MOTPE, dobry przy b ≤ 200 na C10; słabnie przy 350 na FCNet.
- **P3-alone**: jednokryterialny (f1) z FIFO i prawdziwą ewaluacją każdego kroku GOM (R1 §5.1) — ocenia najdroższe modele (mediana f2
  0.44 MB) i nie dba o front. **MO-BOHB**: KDE na losowo ważonych skalaryzacjach (R1 §7.2) ≈ RS (0/16 lepszy od RS, główne).
  **REINFORCE** ≈ RS (0/16). **MO-LS**: pełne sąsiedztwo (39 sąsiadów na JAHS) — przy b ≤ 100 bada 1–2 centra, więc jest skrajnie lokalny;
  gorszy od RS w 6/16 (1–30) i 9/16 (31–60) komórek głównych, na FCNet przy 350 w czołówce. **MOEA/D**: kończy przed budżetem na FCNet przy b ≥ 200 (R1 §1.9), na
  głównych przeciętny (kodowanie porządkowe).

### 3.5 Rola typu przestrzeni

| Typ | Przestrzeń | Obserwacja |
|---|---|---|
| tylko architektura, tabela | NB201 | sufit: mediany 0.985–0.996; przy b=100 nikt nie odróżnia się od RS; addytywność 0.48 (pair 0.77) |
| architektura + HPO, surogat | JAHS ×3 | S5 w czołówce przez pokrycie kosztu; ASHA bardzo silna (niższe wierności z surogatu); f2 = rozmiar (R² addyt. ≈ 1) |
| architektura + HPO, tabela | NHB | kanoniczne P3 i SH-EMOA lepsze w najlepszym f1; S5 środek; ASHA słaba (12 epok) |
| tylko HPO, tabela | FCNet | f1 skrajnie skośne → surogat liniowy S5 ślepy; RF/selekcja/GP wygrywają; S5 w dolnej połowie |

Dyskretyzacja HP (R1 §2) dotyczy tylko JAHS (LR 8, WD 6 wartości) i jest wspólna dla wszystkich ramion; jej wpływu nie da się ocenić z
danych (brak ramienia ciągłego).

### 3.6 Rola budżetu

- **S5:** ranga 11.5 (b=50) → 5.8 / 5.2 / 6.5 (b=100–350) na głównych 31–60; przy b=50 brak różnic z RS, na C10/50 i FMN/50 mediana
  niższa od RS. Przy b=50 piramida ma kilka małych poziomów, a surogat jest uczony na < 50 punktach (odpowiednio ~1 200 par) — mało
  informacji, duży optymizm (§3.3). Przewaga nad RS rośnie z budżetem (domknięcie luki FMN 0.04 → 0.61, NHB 0.14 → 0.47).
- **ASHA:** największa przewaga przy b=50 (FMN/50 +0.044 HV), maleje z budżetem — screening wielu konfiguracji daje najwięcej, gdy
  pełnych ocen jest mało.
- **MO-LS, NSGA-Net, NSGA-III:** silnie zyskują z budżetem (średnie rangi, główne 31–60: MO-LS 25.0 → 16.5, NSGA-Net 19.5 → 4.5, NSGA-III 12.2 → 3.8; FCNet: MO-LS 24.2 → 4.8) — metody
  populacyjne/lokalne potrzebują kilku generacji.
- **GP:** tylko b ≤ 100 — ich pozycja przy większych budżetach nieznana.

---

## 4. Analizy drugorzędne (prereg §5, opisowo)

### 4.1 Krzywe anytime (`augment.py`, `anytime.py`)

Metryka zbioru pierwszych k ocen, k = 10%…100% budżetu (oś = liczba pełnych ocen; ramiona MF pominięte, bo ich oś to koszt). b=350,
mediana po seedach (31–60 główne, 1–30 FCNet). Wybrane przestrzenie:

| FMN (HV) | 10% | 30% | 50% | 70% | 100% |
|---|---|---|---|---|---|
| BANANAS | 0.930 | 0.975 | 0.982 | 0.991 | 0.994 |
| NSGA-III | 0.924 | 0.967 | 0.977 | 0.984 | 0.988 |
| **S5** | 0.923 | 0.966 | 0.974 | 0.978 | 0.989 |
| SH-EMOA | 0.933 | 0.966 | 0.973 | 0.978 | 0.981 |
| TPE | 0.933 | 0.970 | 0.974 | 0.975 | 0.978 |
| S4 | 0.929 | 0.958 | 0.965 | 0.968 | 0.976 |
| RS | 0.921 | 0.964 | 0.966 | 0.968 | 0.971 |
| M10 | 0.922 | 0.954 | 0.957 | 0.961 | 0.963 |

| NHB (IGD+) | 10% | 30% | 50% | 70% | 100% |
|---|---|---|---|---|---|
| SH-EMOA | 0.062 | 0.026 | 0.016 | 0.012 | 0.008 |
| BANANAS | 0.046 | 0.024 | 0.019 | 0.016 | 0.010 |
| NSGA-III | 0.077 | 0.036 | 0.024 | 0.018 | 0.011 |
| M10 | 0.042 | 0.025 | 0.020 | 0.017 | 0.014 |
| TPE | 0.056 | 0.029 | 0.023 | 0.020 | 0.015 |
| **S5** | 0.053 | 0.030 | 0.023 | 0.019 | 0.017 |
| S4 | 0.062 | 0.038 | 0.031 | 0.029 | 0.027 |
| RS | 0.078 | 0.043 | 0.036 | 0.034 | 0.032 |

| FCNet slice (IGD+) | 10% | 30% | 50% | 70% | 100% |
|---|---|---|---|---|---|
| SH-EMOA | 0.054 | 0.009 | 0.004 | 0.002 | 0.001 |
| NSGA-III | 0.117 | 0.022 | 0.008 | 0.004 | 0.002 |
| MO-LS | 0.105 | 0.022 | 0.010 | 0.006 | 0.002 |
| M10 | 0.057 | 0.010 | 0.006 | 0.004 | 0.003 |
| BANANAS | 0.050 | 0.013 | 0.009 | 0.006 | 0.005 |
| RF+FIHC | 0.048 | 0.015 | 0.010 | 0.007 | 0.007 |
| **S5** | 0.062 | 0.022 | 0.017 | 0.014 | 0.011 |
| RS | 0.080 | 0.051 | 0.035 | 0.032 | 0.023 |

Obserwacje (3): S5 rośnie wolno, ale stale (na FMN dogania czołówkę dopiero w ostatnich 30% budżetu — zgodne z rosnącą rangą z
budżetem, §3.6); S4 wypłaszcza się po ~50% (bootstrap dużych poziomów, §3.1); NSGA-III/MO-LS startują najgorzej i kończą wysoko.

### 4.2 Cost to target (90/95/99%)

Prereg: liczba ocen do pierwszego osiągnięcia 90/95/99% „najlepszej mediany końcowej w komórce”. Dla HV względnego ~0.99 cel
literalny jest zdegenerowany (90% = 0.89 osiąga każde ramię po 10% budżetu; 99% osiągają S5, BANANAS, NSGA-III, TPE, SH-EMOA po 20–80%
budżetu na C10/CRC/FMN, a na przestrzeniach IGD+ prawie nikt poza ramieniem najlepszym). Wariant „lukowy” (cel = RS_końc. +
p·(najlepszy − RS_końc.)) przy p=0.9 osiągają tylko 1–3 ramiona na przestrzeń (SH-EMOA, BANANAS, NSGA-III, MO-LS), S5 w żadnej.
Rozdzielczość: siatka 10% budżetu. **Wniosek:** ta miara w tej postaci nie różnicuje ramion poza czołówką — do suplementu, nie do tekstu.
Symulowany czas treningu do celu — pominięty (na JAHS brak kosztu per ocena w historii; tylko suma przebiegu).

### 4.3 Jakość decyzji surogatu

Brak wyników `posthoc_metrics.py` (§1, odch. 6). Zastępczo:

**(a) Etykietowanie zalogowanych decyzji na przestrzeniach tabelarycznych** (`decisions.py`, `dq.py`): dla NHB i 4 × FCNet, b=350, seedy 1–30,
wszystkie zalogowane rekordy (jednostajna próbka ≤ 500 decyzji na przebieg, `decision_log.py`), etykieta = prawdziwe f1 z tabeli; 825 tys.
decyzji. „noop” = propozycja identyczna z punktem odniesienia.

| Ramię / źródło | Grupa | akcept. | base | precyzja | MCC | bal. acc | ρ (bez no-op) | no-op | akcept. no-op |
|---|---|---|---|---|---|---|---|---|---|
| S5 mixing | NHB | 0.59 | 0.59 | 0.78 | 0.44 | 0.72 | 0.73 | 0.13 | 0.52 |
| S5 mixing | FCNet | 0.59 | 0.57 | 0.64 | **0.17** | 0.58 | **0.28** | 0.13 | 0.51 |
| S4 mixing | NHB / FCNet | 0.60 / 0.57 | 0.56 / 0.54 | 0.73 / 0.69 | 0.41 / 0.35 | 0.70 / 0.67 | 0.61 / 0.44 | 0.04 | — |
| AbsRidge (`p3_absolute_cascade`) mixing | NHB / FCNet | 0.26 / 0.37 | 0.47 / 0.56 | 0.78 / 0.75 | 0.37 / 0.30 | 0.66 / 0.64 | 0.62 / 0.23 | 0.15 / 0.21 | — |
| RF mixing (M7) | NHB / FCNet | 0.28 / 0.26 | 0.44 / 0.44 | 0.86 / 0.89 | 0.52 / 0.54 | 0.74 / 0.74 | 0.77 / 0.74 | 0.14 / 0.16 | — |
| RF+FIHC refinement | NHB / FCNet | 0.09 / 0.12 | 0.25 / 0.26 | 0.73 / 0.73 | 0.34 / 0.40 | 0.61 / 0.65 | — | 0 | — |
| RF+eLy refinement | NHB / FCNet | 0.10 / 0.14 | 0.24 / 0.25 | 0.64 / 0.68 | 0.32 / 0.39 | 0.61 / 0.65 | — | 0 | — |
| M10 refinement / gate | NHB | 0.37 / 0.47 | 0.51 / 0.54 | 0.69 / 0.93 | 0.27 / 0.73 | 0.63 / 0.87 | — | — | — |
| M9 refinement / gate | NHB | 0.39 / 0.52 | 0.52 / 0.57 | 0.67 / 0.93 | 0.24 / 0.74 | 0.62 / 0.87 | — | — | — |
| NSGANetV2 selekcja (ρ pred–true f1) | NHB / FCNet | — | — | — | — | — | 0.63 / 0.48 | — | — |

Wnioski: (i) na NHB decyzje S5 są umiarkowanie dobre (MCC 0.44, precyzja 0.78 przy base 0.59); **na FCNet bliskie losowym** (MCC 0.17,
ρ 0.28) — zgodne z R² ≈ 0 (§3.0a). Kalibracja S5 na FCNet: predykowane „poprawy” od −95 do +559 (jednostki MSE, gdy prawdziwe są
rzędu ±0.03), a w najwyższym decylu predykcji P(poprawa) = 0.50 — rzut monetą. Na NHB kalibracja monotoniczna (P(poprawa) 0.06 → 0.96
po decylach). (ii) RF lepiej rozróżnia (MCC 0.52–0.54 w obu grupach). (iii) **eLyMPuS vs FIHC (refinement): MCC 0.32 vs 0.34 (NHB),
0.39 vs 0.40 (FCNet)** — praktycznie to samo, zgodne z R1 §4.3. (iv) Precyzja zawsze porównana z base rate, nie z 0.5 (B7): S5 na FCNet
+0.07 ponad base. (v) **No-opy:** 13% decyzji mieszania S5 i 14–24% w wariantach absolutnych/RF to propozycje identyczne z punktem
odniesienia (rozstrzyga „nieustalone” z R1 §16); w S5 ich akceptacja wynosi ~50% — decyduje znak szumu numerycznego (predykcja
±10⁻¹¹ wobec progu 0), a zaakceptowane zużywają κ.

**(b) `surrogate_quality_log`** (ocenieni członkowie C*): §3.3 — MAE S5 ~10× większe niż RF, systematyczny optymizm S5.

**(c) Błąd vs głębokość łańcucha:** §3.3 — rośnie z głębokością (JAHS 2.75 → 5.04).

### 4.4 Regret (najlepsze f1) — b=350

`f1gap_rel` z §3.2 (względna luka najlepszego f1 do najlepszego f1 frontu odniesienia: wyroczni na NHB/FCNet, zamrożonego na JAHS):
S5 0.090 (JAHS), 0.070 (NHB), 0.529 (FCNet); najlepsze ramiona: NSGANetV2 0.046 / 0.015 / 0.224, M10 0.058 / 0.026 / 0.324, RF+FIHC
0.061 / 0.019 / 0.393, SH-EMOA 0.061 / 0.076 / 0.218; RS 0.108 / 0.089 / 0.536. S5 jest blisko RS w najlepszym f1 na FCNet, a lepszy od
RS o ~1/5 luki na JAHS/NHB. Siła (3).

### 4.5 Luki generalizacji (tylko NHB i FCNet; `gen.py`)

Dla członków frontu przebiegów b=350 (seedy 1–30) policzone błędy testowe z tabel (NHB: `test_acc`; FCNet: `final_test_error`).
- Względna luka test−walidacja (mediana): NHB −0.005…−0.015, FCNet naval −0.05…−0.09, slice −0.10…−0.15, protein −0.013…−0.017, parkinsons
  +0.003…+0.024 — **ten sam rząd dla wszystkich ramion**; żadne ramię nie „przeucza” walidacji bardziej niż inne.
- ρ(val, test) na froncie: 0.96–1.00 dla wszystkich ramion.
- Błąd testowy konfiguracji najlepszej walidacyjnie (NHB): S5 14.60, RS 14.77, M10 14.06, NSGANetV2 14.01, SH-EMOA 14.72 — kolejność jak
  na walidacji.
Wniosek (3): na tabelach front testowy dałby te same wnioski. JAHS nie policzony (wymaga mostu 12 GB na zbiór; `posthoc_metrics.py`
nieuruchomiony). NB201: f1 już jest błędem testowym (R1 §2).

### 4.6 Wykorzystanie budżetu i duplikaty

Z R1 §1.9: wszystkie ramiona jednowiernościowe poza MOEA/D zużywają 100% budżetu; MOEA/D przerywa w 18.4% przebiegów (prawie cały FCNet
b ≥ 200). MF: pełnych ocen 46–66% budżetu. Odsetek duplikatów propozycji (`duplication_rate`) — w `per_run.csv`, nie analizowany tutaj
(duplikaty nie zużywają budżetu w żadnym ramieniu, R1 H2).

### 4.7 Koszty z s9 (Q6) — b=350, seed 1, sekwencyjnie

Zegar [s] (C10 / CRC / FMN / NHB) i szczytowe RSS procesu [MB] (most JAHS **nie** wliczony; `bridge_peak_rss_mb` i `gpu_peak_memory_mb`
w s9 są puste — brak względem prereg §5):

| Grupa | Ramiona | zegar | RSS |
|---|---|---|---|
| bardzo tanie | RS, MO-LS, NSGANetV2, RegEvo, NSGA-Net, REINFORCE, SH-EMOA, NSGA-III, P3-abs. | 9–11 / 2–3 | 425 / 1 551 |
| tanie | MOEA/D, MO-BOHB, TPE, P3-alone ×3 | 13–132 / 4–79 | 425 / 1 552–1 557 |
| średnie | **S5 173 / 135 / 186 / 27**, S4 133–150 / 5, AbsRidge 95–128 / 7, BANANAS 109–127 / 126, Hyperband 161–174 / 3, BOHB 227–241 / 13, ASHA 406–472 / 4, SMAC3 243–248 | | S5 734–840 / 1 801 (najwyższe poza GP) |
| drogie | RF 322–392 / 148, RF+eLy 450–540 / 274, RF+FIHC 415–856 / 582, kanoniczne P3 ×3 1 075–1 311 / 773–857 | | ~425 / 1 560 |
| bardzo drogie | qParEGO 3 384–5 676 / 2 585, qNEHVI 3 354–7 612 / 4 996, **Vizier 8 347–12 037 / 7 267** | | 8–16 GB (BoTorch), **27–31 GB (Vizier)** |

Narzut optymalizatora (zegar − czas zapytań benchmarku) to > 95% zegara dla wszystkich ramion z modelem (benchmarki są tabelaryczne / surogatowe).
Symulowany czas treningu na przebieg (b=350): S5 zużywa mniej niż RS (tańsze modele), ale więcej niż SH-EMOA/BANANAS/MO-LS: np. NHB
20.7 h (S5) vs 25.2 (RS), 13.6 (SH-EMOA), 17.1 (BANANAS); FCNet slice 39.8 vs 51.6, 24.4, 22.6. Na JAHS wartości benchmarku są rzędu
1.4–2.2·10⁴ h na przebieg (jednostki `runtime` JAHS; nieweryfikowane) i porządkują ramiona tak samo. Pieniądze/energia nie liczone (brak
przyjętych założeń cenowych).

---

## 5. Kompromis jakość × koszt

Front Pareto (jakość = mediana 31–60 przy b=350; koszt = s9 b=350 seed 1; GP wykluczone — brak jakości przy 350; `cost.py`):

| Przestrzeń | jakość × zegar | jakość × RSS |
|---|---|---|
| C10 | RS (0.9731, 9 s) → NSGA-Net (0.9800, 9) → NSGA-III (0.9804, 10) → **SH-EMOA (0.9823, 10)** | SH-EMOA |
| CRC | REINFORCE (0.9907, 9) → RegEvo (0.9940, 9) → NSGANetV2 (0.9949, 9) → MOEA/D (0.9957, 16) → BANANAS (0.9957, 110) | BANANAS |
| FMN | RegEvo (0.9865, 9) → NSGA-III (0.9882, 9) → **BANANAS (0.9942, 109)** | BANANAS |
| NHB | RS (0.0319, 2) → MO-LS (0.0166, 2) → NSGA-Net (0.0123, 3) → **SH-EMOA (0.0078, 3)** | RS → SH-EMOA |

**S5 nie jest na żadnym froncie jakość × koszt** przy b=350 (siła (3)): na każdej przestrzeni istnieje ramię lepsze i 10–20× tańsze
(SH-EMOA, NSGA-III, BANANAS). Przy b ≤ 100 dochodzi Vizier (najlepszy na NHB/FCNet, ale 1–3.4 h i do 31 GB na przebieg — R1, `timing.csv`).
Uwaga: koszt zegarowy optymalizatora jest pomijalny wobec realnego treningu (sekundy–godziny vs 10⁴ h symulowanego treningu na przebieg
JAHS) — w praktyce liczyłby się czas treningu ocenionych konfiguracji (§4.7), a tam wygrywają ramiona oceniające tanie modele.

---

## 6. Wyjaśnienia alternatywne i zagrożenia trafności

| Zagrożenie | Co mówią dane | Ocena |
|---|---|---|
| **Dopasowanie S5 do seedów 1–30** | Na seedach 31–60 S5 wypada *lepiej* (Q1: 35× „·”→„+”, 0 zmian znaku istotnych; B10) | wykluczone dla seedów (2) |
| **Dopasowanie do rodziny benchmarków** (S5 projektowany na tych samych 4 przestrzeniach) | Na FCNet (nowa rodzina) S5 spada do dolnej połowy; ale istnieje mechanizm niezależny od dopasowania: liniowy surogat na surowym, skrajnie skośnym MSE ma R² ≈ 0 (§3.0a), decyzje S5 na FCNet MCC 0.17 (§4.3) | „ograniczenie modelu” lepiej wsparte niż „dopasowanie” (3); rozstrzygnięcie: S5 z log(f1) na FCNet (4) |
| **Asymetria strojenia** (S5 projektowany, baseline'y domyślne) | Działa na korzyść S5; mimo to S5 jest 5. na głównych | nie zmienia wniosku „S5 nie jest najlepszy”; osłabia „S5 > X” dla X bliskich S5 |
| **Darmowe f2 (B3)** | `inherited_cost` ≈ S5 w 16/16 na głównych, także na NHB (różnica IGD+ +0.0005) | na głównych przewaga S5 nie pochodzi z hooka (1); na FCNet nieznane |
| **Dyskretyzacja HP** (JAHS) | wspólna dla wszystkich; brak ramienia ciągłego | nieoceniane |
| **Wierność baseline'ów** (R1) | SMAC3 przy b ≤ 100 = Sobol: na JAHS SMAC3 vs RS bez różnicy w 12/12 komórek b ≤ 100 (oba bloki seedów, δ −0.15…+0.38), a przy 200/350 bije RS w 6/6 komórek JAHS (31–60; rodzina vsRS) (δ do −0.87) — **potwierdzenie przewidywania R1 §9.2**; MOEA/D na FCNet przy ~130 ocenach; NSGANetV2 bez f2; MO-BOHB/P3-alone uproszczone | wygrane S5 z MO-BOHB, P3-alone, SMAC3 (b ≤ 100) nie są wygranymi z tymi metodami w ich właściwej postaci |
| **Moc testów** | n = 30 na ramię; po Holmie z 21–24 porównań istotne są zwykle dopiero |δ| ≳ 0.35–0.4; wiele komórek „·” ma |δ| 0.2–0.3 | „brak różnicy” ≠ równoważność (B4); brak testu TOST |
| **Zamrożony front / punkt odniesienia HV** | ranking odporny na punkt odniesienia (`altref.py`, §3.0b) | niski wpływ (3) |
| **Brak GP przy 200/350** | rodzina Q1 mniejsza; Vizier najlepszy na NHB/FCNet przy ≤ 100 | ranking „S5 5. z 25” dotyczy mieszaniny budżetów |
| **Benchmark-surogat JAHS** | niższe wierności ASHA z surogatu (R1 §8); f2 = `size_MB` z surogatu | przewaga ASHA na JAHS może być zawyżona (4) |
| **Poprawność skryptów** | metryki zgodne z biblioteką do 10⁻¹⁶; znaki δ sprawdzone; drobne uwagi §0 | niskie ryzyko |
| **Selekcja w `surrogate_quality_log`** | tylko członkowie C* | optymizm S5 częściowo artefaktem; porównanie MAE S5 vs RF zachowane, bo oba podlegają selekcji |

---

## 7. Lista wniosków

Siła: (1) interwencja/izolacja, (2) potwierdzające (seedy 31–60, główne, Q1/Q4/Q7), (3) eksploracyjne/korelacyjne, (4) hipoteza.

| # | Wniosek | Siła | Zależność od ograniczeń implementacji (R1) | Czym rozstrzygnąć |
|---|---|---|---|---|
| W1 | S5 istotnie lepszy od RS w 10/16 komórek głównych, nigdy gorszy; różnice +0.002…+0.018 HV / −0.007…−0.015 IGD+, domknięcie luki do frontu 4–61% | (2) | „S5” = wariant z R1 §3 | — |
| W2 | S5 nie jest najlepszy: średnia ranga 7.2 wśród 25 ramion Q1 (5. miejsce); istotnie gorszy od TPE, SH-EMOA, BANANAS, Vizier, NSGA-III, NSGA-Net w 1–3 komórkach każdy | (2) kierunek, (3) ranking | rangi mieszają budżety (GP tylko ≤ 100) | — |
| W3 | Na FCNet S5 bije RS 11/16, ale przegrywa z 10 ramionami (ranga 13.0) | (3) | — | log(f1) w surogacie (4) |
| W4 | Przewaga S5 na JAHS pochodzi z pokrycia taniego końca frontu, nie z najlepszego f1 (ranga najlepszego f1 5–23) | (3) | świeże f2 (H7) — ale `inherited_cost` ≈ S5 | dekompozycja HV na końce frontu |
| W5 | S4 → S5 (`cascade`) poprawia jakość w 5/16 (główne) i 7/16 (FCNet) komórek, wszystkie istotne przy b ≥ 200 | (1)/(3) | „cascade” ≠ kaskada P3 (R1 §3.1) | — |
| W6 | Spadek udziału bootstrapu (S4 91% → S5 27% przy 350) towarzyszy poprawie; S4′ (0.6%) równie dobry, `grow_on_stall` (91%) gorszy (8/16) — ale wewnątrz S5 więcej bootstrapu ≈ lepiej | (1)/(3) | — | S4 z ciepłym startem całego poziomu (4) |
| W7 | S4′ (mieszanie od 2 osobników) lepszy od S4 w 6/16, nigdzie gorszy — sprzeczne z „regressed severely” w v0.0.3 | (3) | — | S4′ vs S5 bezpośrednio |
| W8 | S1→S2→S3→S4: 0/16 istotnych zmian w każdym przejściu | (3) | S3→S4 to 2 osie naraz | — |
| W9 | Jedyna obroniona decyzja projektowa: reinjekcja zamiast wzrostu przy pustym C* (8/16) | (1)/(3) | — | — |
| W10 | Darmowe f2 nie jest źródłem przewagi S5 na głównych (w tym NHB, gdzie f2 = czas z tabeli) | (1) na 4 przestrzeniach | FCNet bez izolacji | `inherited_cost` na FCNet |
| W11 | κ i próg (w badanych skalach) bez wpływu; na NHB mniejsze κ kierunkowo lepsze | (3) | progi pomijalne w jednostkach f1 (R1 §3.5) | progi znormalizowane |
| W12 | Względny Ridge ≥ absolutny Ridge (3/0/13 potwierdzające) | (2) | różnica = kotwica/akceptacja/regularyzacja, nie linkage (R1 §3.2) | — |
| W13 | RF w miejsce Ridge: f1 przewidywane ~10× dokładniej, ale bez poprawy HV na głównych; FIHC na RF pomaga na FCNet (10/16 vs RF) | (2)/(3) | akceptacja po samym f1 (R1 §3.6) | akceptacja wielokryterialna w wariantach RF |
| W14 | Akceptacja po f1 w wariantach RF przesuwa oceny ku droższym modelom (+9…+65% f2) i lepszemu f1 (−2…−24%) | (3) | — | jw. |
| W15 | Krok eLyMPuS: 0/32 istotnych; MCC decyzji jak FIHC | (1) dla tej integracji | **eLyMPuS na darmowej funkcji** (R1 §4.3) — nie wolno uogólniać | eLyMPuS na prawdziwych ocenach |
| W16 | Surogat S5 na FCNet ≈ losowy (MCC 0.17, ρ 0.28; R² addytywny ≈ 0); na NHB umiarkowany (MCC 0.44) | (1) dla decyzji (etykiety z tabel) | trenowanie na surowym f1 | log(f1) |
| W17 | Krajobrazy JAHS/NHB/NB201 silnie nieaddytywne (R² 0.36–0.48 vs 0.75–0.94 z interakcjami) | (1) dla krajobrazu | — | — |
| W18 | Kanoniczne P3 (M9, M10, bartnik) w czołówce na NHB/FCNet dzięki lepszemu f1, przeciętne na JAHS | (3) | f2 przewidywane, wnętrze na RF (R1 §4.1) | kanoniczne P3 ze świeżym f2 |
| W19 | ASHA najlepsza na JAHS (8/16 lepsza od S5, 31–60) i FCNet (16/16) przy równym koszcie epok; słaba na NHB | (2) JAHS, (3) FCNet | JAHS niższe wierności z surogatu; front z ~połowy punktów | — |
| W20 | Vizier najlepszy na NHB i FCNet przy b ≤ 100, ale 1–3.4 h i do 31 GB na przebieg | (2)/(3) | tylko b ≤ 100 | GP przy 200/350 |
| W21 | SMAC3 ≈ RS przy b ≤ 100 na JAHS, wyraźnie lepszy przy 200/350 — artefakt konfiguracji | (1) | `n_trials=10⁷` (R1 §9.2) | `n_trials` = budżet |
| W22 | S5 nie leży na froncie jakość × koszt przy b=350 na żadnej przestrzeni głównej; SH-EMOA/BANANAS/NSGA-III lepsze i szybsze | (3) | koszt z 1 seeda s9 | — |
| W23 | Luki val–test podobne dla wszystkich ramion (NHB, FCNet); ρ(val, test) ≥ 0.96 | (3) | JAHS nie policzony | posthoc na JAHS |
| W24 | NB201: sufit (mediany 0.985–0.996); przy b=100 nikt ≠ RS | opis | f1 = test | — |
| W25 | Błąd predykcji S5 rośnie z głębokością łańcucha (2.8 → 5.0 p.p. na JAHS) mimo kolapsu telescopingu | (3) | — | — |
| W26 | 13–24% propozycji mieszania to no-opy; w S5 akceptowane w ~50% przez szum numeryczny | (1) dla częstości (próbka logu) | R1 §3.1 | P-K3 z R1 |

---

## 8. Rozbieżności z `INITIAL_FINDINGS.md` (otwarty po §0–§7)

| Punkt INITIAL_FINDINGS | Ten raport | Status |
|---|---|---|
| S5 > RS 10/16 (31–60), 8/16 (1–30), 11/16 (FCNet), nigdy gorszy; S4 0/16 | to samo (Q1); S4 vs RS 0/16 w 1–30, ale **4/16 w 31–60** (rodzina vsRS) | zgodne, uzupełnione |
| Bootstrap S4 ~90–93%, S5 18–45% (główne), 55–60% (FCNet) przy 350 | zgodne; dodatkowo S4′ 0.6% i odwrotna korelacja wewnątrz S5 (§3.1) | zgodne; osłabia prostą narrację |
| S5 ~5. z 23, ranga 7.8 | 5. z 25 ramion Q1, ranga 7.2 (inny zbiór ramion: z S4 i GP) | drobna różnica definicji |
| Porażki S5 głównie z SH-EMOA, TPE, BANANAS (po 3) | zgodne; plus Vizier 2, NSGA-III 1, NSGA-Net 1, M9 1 | zgodne |
| FCNet: S5 ~16. | ranga 13.0 wśród 25 ramion Q1 (bez MF/final) | różnica zbioru ramion |
| BoTorch ≈ S5 we wszystkich komórkach, 3–40× droższy | jakość: qParEGO gorszy od S5 w CRC/50 (31–60), poza tym remisy; **koszt s9: 18–185× droższy** (3 354–7 612 s vs 27–186 s) | koszt zaniżony w INITIAL |
| „Wszystkie metody poza GP ~1.5–1.8 GB RAM” | to RSS na NHB (API w procesie); na JAHS 425–840 MB **bez mostu** (most nie jest mierzony w s9) | doprecyzowanie |
| Q2: S4→S5 poprawa 6/16 (primary), 7/16 (FCNet); S4′ lepsze w 6/16 | S4→S5 **5/16** primary, 7/16 FCNet; S4′ 6/16 | rozbieżność 6 vs 5 (możliwe pomylenie z S4′) |
| Q3 | zgodne | — |
| Q4: RF Spearman ~0.8–0.95 vs S5 ~0.3–0.4 | ta miara jest obciążona na korzyść RF (wspólny składnik f(x₀), §0 uw. 5); miara nieobciążona (MAE) potwierdza przewagę RF (~10×) | wniosek utrzymany, miara do zmiany |
| Założenie: `surrogate_quality_log` = tylko zaakceptowane i ocenione | potwierdzone w kodzie (R1 §17) | potwierdzone |
| Hipoteza: przewaga S5 na JAHS z pokrycia osi kosztu | wsparta przez `coverage.py` (§3.2) i ranking najlepszego f1 (§2.0) | wsparta (3) |
| MOEA/D nie zużywa budżetu na FCNet/NAS-HPO (46–81 zamiast 350) | FCNet tak; NHB tylko 7/240 przebiegów (R1 §1.9) | częściowo |
| Ryzyko dopasowania nierozstrzygnięte | analiza addytywności (§3.0a) i decyzji (§4.3) wskazuje konkretny mechanizm na FCNet (surowe MSE) | przesunięcie ku „ograniczeniu modelu” |
| Q7: ASHA bije S5 w 8/16 (31–60) | zgodne | — |
| NB201: odróżniają się S5, RF, RF+eLy, M9, M10, MO-LS; nie S4, bartnik | zgodne | — |

