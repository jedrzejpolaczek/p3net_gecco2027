# v005 — etap B: interpretacja (B1–B6)

Stan na 2026-11-16. Źródło: `results/runs/c674c91e/analysis/` (v005, seedy 62–91) i raport 01. Wszystko poniżej jest
opisowe; testy potwierdzające to tylko Q1–Q5 z prerejestracji. Liczby „rank r/n” = pozycja mediany P3Net wśród ramion
toru głównego (z eLyMPuS) w komórce, 1 = najlepsza.

## B1 (a) — porównanie w wielu metrykach

**Jakość zależy od budżetu bardziej niż od przestrzeni.**

| Przestrzeń | rank b = 50 | 100 | 200 | 350 |
|---|---|---|---|---|
| JAHS C10 | 20/22 | 17/22 | 16/19 | 8/19 |
| JAHS CRC | 18/22 | 19/22 | **1/19** | 4/19 |
| JAHS FMN | 20/22 | 20/22 | 2/19 | 2/19 |
| NHB | 16/22 | 17/22 | 10/19 | 13/19 |
| NB201 (opisowo) | 15/22 | 13/22 | 12/19 | 12/19 |
| FCNet naval / park / prot / slice (b = 350) | | | | 7 / 7 / 11 / 9 z 19 |

- **P3Net jest gorszy od random search przy b = 50 i 100 na wszystkich trzech JAHS** (Q1, istotne po Holmie, δ od −0.43
  do −0.68). Przy b = 200 i 350 lepszy od random search na CRC, FMN i NHB (δ 0.56–0.82); na C10 n.s.
- Krzywe anytime (C10, b = 350): P3Net startuje najniżej wśród ramion z czołówki (HV 0.888 po 50 ewaluacjach vs 0.896–
  0.902) i dogania pod koniec (0.913 vs najlepsze 0.916). Na NHB podobnie (IGD+ 0.060 → 0.018; NSGANetV2 0.061 → 0.007).
- **Dekompozycja HV (JAHS, b = 350):** P3Net jest mocny na „dokładnym” końcu frontu (rank 7, 3, 3 z 24 na C10, CRC, FMN) i
  słabszy na „tanim” (15, 11, 4). Zgodnie z tym regret f1 P3Net jest niższy niż mediana ramion na JAHS (C10 0.52 vs 0.63,
  CRC 0.29 vs 0.40, FMN 0.15 vs 0.24); na NHB wyższy (1.22 vs 1.12).
- **Najlepsze ramię w komórce:** przy b = 50, 100 najczęściej GP (Vizier, qParEGO) albo NSGANetV2; przy b = 200, 350
  NSGANetV2, NSGA-Net, MO-BANANAS, SH-EMOA. Wyjątek: CRC b = 200 — P3Net.
- **Koszt do celu (§5.2) na JAHS słabo rozróżnia:** przy b = 350 każde ramię w każdym runie osiąga 95 % najlepszej
  mediany (HV ramion leży w wąskim pasie, np. C10 b = 350: 0.909–0.916); różnice widać tylko przy małych budżetach
  (najniżej C10 b = 50: kanoniczne P3 i eLyMPuS 63 % runów, warianty P3Net 70 %). Na NHB rozróżnia (b = 350: P3Net 3 %
  runów do 95 %, NSGANetV2 50 %). Do Limitations: cel względny przy nasyconym HV.
- **Wrażliwość HV na punkt odniesienia (§5.6a):** kolejność ramion praktycznie się nie zmienia (Spearman ≥ 0.99 dla
  (1.05, 1.05) i (1.2, 1.2) w każdej komórce JAHS) — wnioski Q1 nie zależą od wyboru punktu.

## B1 (b) — rozbiór drogi projektowej (co wnosi surogat)

- **Surogat prawie nie działa przy b ≤ 350.** Mediana kroków mieszania P3Net na run: JAHS 0 / 0 / 0–1 / 6–8, NHB
  0 / 0 / 7.5 / 50, NB201 0 / 1 / 18 / 55.5, FCNet 0 / 0–0.5 / 6.5–9.5 / 41–54 (b = 50 / 100 / 200 / 350). Budżet zużywa
  FIHC. Na JAHS do mieszania dochodzi najpóźniej; liczba współrzędnych tego nie wyjaśnia (JAHS 10, FCNet 9, NHB 8, NB201
  6, a FCNet ma 41–54 kroki przy b = 350) — przyczyna (np. liczność domen, liczba ewaluacji FIHC na rozwiązanie) do
  sprawdzenia w rekordach.
- Stąd Q2/Q3: P3Net-gate i P3Net-nolink kończą identycznie jak P3Net w 94.6 % i 96.0 % runów na przestrzeniach głównych;
  „równoważność” TOST (m = 0.33, 16/16) jest w dużej części mechaniczna i **nie jest dowodem, że wariant surogatu nie ma
  znaczenia** — tylko tego, że przy tych budżetach nie ma okazji zadziałać.
- **P3Net vs kanoniczne P3:** identyczny wynik tylko w 5.8 % runów, choć przy b = 50 P3Net nie wykonuje żadnego kroku
  mieszania. **Wyjaśnione (raport 03):** warianty z surogatem pobierają jedną liczbę z generatora na ziarno surogatu, więc
  idą innym strumieniem losowym; bez kroków mieszania P3Net jest kanonicznym P3 (sprawdzone: identyczne historie, 6/6).
- Kierunek na NHB przeciw P3Net: mediany IGD+ kanonicznego P3 lepsze przy b = 100, 200, 350 (0.035 / 0.020 / 0.016 vs
  0.042 / 0.024 / 0.018), TOST nierozstrzygnięty (δ −0.12 … −0.18).
- K8 (jakość decyzji surogatu) niewykonalne (prerejestracja §8 poz. 3) — zastępuje je liczba kroków i `surrogate_share`
  (0.60 / 0.63 przy b = 200 / 350 na przestrzeniach głównych).

## B1 (c) — zależność od benchmarku

- JAHS C10 zachowuje się inaczej niż CRC i FMN: przy b = 200, 350 P3Net na CRC i FMN w czołówce (rank 1–4), na C10 nie
  (16 i 8 z 19; nadal gorszy od 7 i 4 ramion).
- NHB: przewaga ramion ewolucyjnych z populacją (NSGANetV2, NSGA-III, SH-EMOA); P3Net w środku stawki.
- FCNet (Q5) korzystniejszy dla P3Net niż przestrzenie główne (64 lepszy / 36 gorszy / 148 n.s.), z wyjątkiem protein.
  Wynik z przestrzeni głównych nie przenosi się wprost — sformułować wyniki per przestrzeń (etap C).

## B1 (d) — koszt praktyczny

Czas optymalizatora (bez zapytań do benchmarku) i szczytowa pamięć procesu, mediany na run, `costs.csv`:

| Ramię | JAHS C10 b = 100 | NHB b = 100 | pamięć (C10 / NHB) | JAHS C10 b = 350 |
|---|---|---|---|---|
| OSS Vizier | 1 160 s | 921 s | 14.0 / 18.4 GB | — (nie uruchamiany) |
| NSGANetV2 | 624 s | 554 s | 1.5 / 2.9 GB | 2 825 s |
| MO-DSA | 348 s | 262 s | 1.5 / 2.8 GB | 946 s |
| qNEHVI | 160 s | 112 s | 2.7 / 3.8 GB | — |
| P3Net | 0.3 s | — | | 5.7 s |

- Ramiona najlepsze przy małych budżetach (Vizier, NSGANetV2) kosztują 2–3 rzędy wielkości więcej czasu optymalizatora
  niż P3Net; Vizier dodatkowo do 25 GB (118 restartów po OOM, prerejestracja §8 poz. 2). To argument o brakującej osi
  porównania (koszt samego optymalizatora), nie o wadzie BO.
- Uwaga: czasy JAHS C10 zmierzone przy 2 workerach (§8 poz. 1).

## B2 — NAS-Bench-201 (do decyzji autora)

Plan mówi: „benchmark słabo rozróżnia metody; FLOPs prawie jednokryterialne”. To dotyczyło v004 (f2 = FLOPs). W v005
f2 = energia z HW-NAS-Bench i obraz jest inny: front oracle ma 30 punktów (z 15 284 komórek), mediany IGD+ przy b = 350
rozciągają się od 0.0096 (NSGANetV2) do 0.0375 (MO-DSA), kolejność ramion jest stabilna między b = 200 i 350 (Spearman
0.95). NB201 rozróżnia więc metody. **Zdanie B2 trzeba zmienić** — propozycja: NB201 opisowo, P3Net w środku stawki
(rank 12/19 przy b = 200, 350), między kanonicznym P3 a random search.

REINFORCE na NB201 ma tę samą medianę 0.1393 przy każdym budżecie — kolaps na duplikatach (#36, mediana 54 ewaluacji,
min. 19); opisać przy tabelach razem z MO-DSA / MO-PSA (raport 01 §3).

## B3 — eLyMPuS

Q7: gorszy od kanonicznego P3 w 33 z 36 komórek (δ do −0.38). Zgodnie z B3 — w tekście tylko jako kierunek; następny krok
to eLyMPuS z grafem zależności NAS+HPO (pomysł promotora, „Po v005” w `v005-todo.md`), nie strojenie obecnego wariantu.

## B4 — S4′ vs S5

Bez nowych danych w v005 (S4′/S5 to warianty z v004, raport `notes/analysis-v004/reports/04-a9-equivalence-hv.md` §2).
Tekst zgodnie z P6: alternatywa o innym profilu (S4′ lepszy na NHB, S5 na CRC przy b ≥ 200 i FMN przy b = 350).

## B5 — testy hipotez interpretacyjnych (wymagają liczenia; do decyzji autora)

Plan wymienia: log(f1), akceptacja po obu celach w wariantach RF, kanoniczne P3 ze świeżym f2, większe przestrzenie.
Wyniki v005 zmieniają priorytety: dopóki surogat wykonuje 0–8 kroków mieszania na run (JAHS), żadna zmiana **sposobu**
decyzji surogatu (log(f1), akceptacja po obu celach) nie może się ujawnić. Jedyny test, który odpowiada na pytanie
z B1 (b), to **większy budżet**. Propozycja (eksploracyjna, poza prerejestracją, na nowych seedach):

- P3Net, P3Net-gate, P3Net-nolink, kanoniczne P3 × 4 przestrzenie główne × b = 1 000 × 30 seedów = 480 runów;
- koszt: przy b = 350 run trwa ~20–25 s; przy b = 1 000 nieznany (więcej kroków mieszania = więcej uczenia surogatu) —
  szacunek 2–4 min na run, tj. ~15–30 CPU-h; most JAHS potrzebuje 13–15 GB RAM na zbiór. **Przed decyzją: pilotaż
  10 runów** (minuty), żeby zmierzyć czas.
- pozostałe pozycje B5 — odłożyć (bez większego budżetu nic nie pokażą).

## B6 — JAHS `size_MB` w v004

Bez obliczeń: w v005 f2 = liczba parametrów (BM-3), więc problem dotyczy tylko interpretacji v004. Do tekstu: część
„poprawy f2” na JAHS w v004 mogła wynikać ze zmiany HP (szum surogatu do 34 % przy stałej komórce), nie z architektury.

## Do etapu C — zebrane

1. Wyniki per przestrzeń i per budżet; główny wzór: P3Net słaby przy b ≤ 100 (gorszy od random search na JAHS), w
   czołówce przy b ≥ 200 na CRC i FMN.
2. Profil frontu: mocny koniec dokładny, słabszy tani.
3. Surogat przy b ≤ 350 prawie nieaktywny → Q2/Q3 opisać razem z liczbą kroków i odsetkiem identycznych runów.
4. Koszt optymalizatora jako osobna oś porównania.
5. Limitations: koszt do celu na JAHS nasycony; czasy C10 przy 2 workerach; K8 niewykonane; kolapsy REINFORCE / MO-DSA /
   MO-PSA; GP tylko b ≤ 100.
6. Przy budżetach bez kroków mieszania P3Net i kanoniczne P3 to ten sam algorytm (raport 03) — napisać wprost.
