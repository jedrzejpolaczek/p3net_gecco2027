# P3Net v0.0.5 — plan poprawek i nowego przebiegu

Stan: 2026-10-16. Zastępuje `notes/archive/v004-plan.md` i `notes/archive/v004-audit-checklist.md`
(punkty, które pozostały aktualne, są przeniesione tutaj).

Podstawa: raporty analizy v004 — `notes/analysis-v004/reports/01-implementation-audit.md` (R1),
`02-results-analysis.md` (R2), `03-paper-confrontation.md` (R3) — oraz decyzje autora z 2026-10-16.
Prerejestracja v004 (`notes/plans/v004-preregistration.md`) jest zamknięta: §7 opisuje odchylenia
i status v004 (wyniki eksploracyjne, motywacja poprawek, nie główny wynik artykułu).

## Cel

Artykuł proponuje nowy algorytm (P3Net) i ocenia go na tle innych metod joint NAS+HPO.
v0.0.5 ma dać tę ocenę na **zweryfikowanych** implementacjach: bez skrótów, które w v004 zaburzały
wyniki (R1 §14), w wielu metrykach (jakość frontu, dokładność, pokrycie kosztu, zasoby).

## Etapy

| Etap | Co | Warunek przejścia dalej |
|---|---|---|
| **A** | Rzetelność: weryfikacja i poprawki implementacji, brakujące analizy, nowa prerejestracja, przebieg v005 | Wszystkie kryteria z „Zakończenie etapu A” spełnione |
| **B** | Interpretacja wyników v005 | Narracja i lista wniosków z siłą dowodu |
| **C** | Poprawki tekstu i pisanie v0.0.4 / v0.0.5 artykułu | Tekst zgodny z tabelą „zdanie ↔ test” |
| **D** | Formalności przed wysyłką (GECCO'27, double-blind) | Lista D odhaczona |

---

## Skąd wzięły się błędy v004 (żeby ich nie powtórzyć)

| # | Przyczyna | Przykłady w v004 | Zabezpieczenie w v005 |
|---|---|---|---|
| Z1 | Specyfikacja z pamięci lub intencji, nie ze źródła | Bartnik (praca w repo od 2026-07-31, nieużyta), FOS w P3, FIHC, NSGA-Net, NSGANetV2, SH-EMOA | Karta źródła dla każdej metody (A0) |
| Z2 | Testy zapisują błędną specyfikację albo sprawdzają elementy osobno | test drzewa wymaga korzenia w FOS; testy surogatu na ręcznych podzbiorach | Testy pisane ze źródła; testy integracyjne (A0) |
| Z3 | Niezweryfikowane ustawienia domyślne bibliotek | SMAC3 `n_trials`, MOEA/D, siatka α RidgeCV | Asercje konfiguracji (A0) |
| Z4 | Testy w warunkach innych niż produkcyjne | sztuczny substrat, budżety 25–60 | Testy na prawdziwych przestrzeniach przy min. i maks. budżecie (A0) |
| Z5 | Brak kontroli wyników po przebiegu | MOEA/D < budżet, puste pola pomiarów, brak posthoc | Kontrola po przebiegu + lista „zobowiązanie → skrypt → plik” (A0, A9) |
| Z6 | Ograniczenie harnessu obchodzone surogatem | eLyMPuS i kanoniczne P3 liczone na lesie losowym | Rejestr decyzji; ewaluacje krok po kroku (A2, A7) |
| Z7 | Udogodnienie dla jednej metody | darmowe f2 tylko dla P3Net | Rejestr decyzji + test symetrii (A2, A3) |
| Z8 | Tekst z intencji, nie z kodu | opis surogatu, akceptacji, κ, poziomów, baseline'ów | Tabela „zdanie ↔ test” (A0) |
| Z9 | Brak procesu dla zobowiązań i odchyleń | pusta §7, brak retreningu | Odchylenia wpisywane w dniu wykrycia; zobowiązania z właścicielem, terminem i skryptem (A11, A10) |
| Z10 | Kontekst analiz bez weryfikacji | „brak pracy Bartnik” w `CONTEXT.md` | Każdy fakt z dowodem; sekcja „fakty przejęte bez sprawdzenia” w raportach (A13) |
| Z11 | Planowanie zasobów niezgodne z metodami | GP poza pamięcią przy b ≥ 200 | Test zasobów przy maks. budżecie przed zamrożeniem planu (A8) |
| Z12 | Dryf przez kolejne poprawki: każda zmiana uzasadniona lokalnie objawem, żadna nie porównana z algorytmem wzorcowym; tekst dopasowywany do kodu | silnik P3Net odszedł od P3 w krokach 2026-08-14 … 09-15 bez decyzji autora | Karta źródła jako stały wzorzec; każda zmiana logiki silnika w rejestrze decyzji z porównaniem do karty i akceptacją autora; przegląd zgodności z kartą przy każdym kamieniu milowym |

---

## Etap A — rzetelność

Kolejność: A0 → A2 → (A3–A8 równolegle) → prerejestracja v005 (A1, A10, A12) → `checks` → przebieg.
A9 równolegle od teraz. A11 i A13 — zrobione 2026-10-16.

### A0. Protokół weryfikacji implementacji — decyzja: pełny; weryfikują autor + niezależny agent

Dla każdej metody i każdego zdania artykułu opisującego metodę:
1. **Karta źródła** (`notes/plans/v005-sources/<metoda>.md`): cytat lub pseudokod ze źródła, numer strony, lista świadomych
   odstępstw z uzasadnieniem.
2. **Testy ze źródła** — pisane z karty, nie z kodu. Pisze je agent, który widzi kartę i interfejs, ale nie implementację;
   autor zatwierdza karty.
3. **Testy integracyjne** na każdej przestrzeni przy najmniejszym i największym budżecie.
4. **Asercje mechanizmów w trakcie przebiegu** (np. surogat P3Net używa < 100% par; projekt początkowy SMAC3 ≤ 25% budżetu).
5. **Kontrola po przebiegu**: `evaluations_used == budget` (tor główny), pola zasobów niepuste, komplet plików wymaganych
   przez prerejestrację.
6. **Tabela „zdanie ↔ test”** (`notes/plans/v005-claims.md`): każde zdanie opisu metody ma test, który by nie przeszedł,
   gdyby zdanie było fałszywe.

Punkty 3–5 jako etap `checks` w `run_pipeline.py`, który blokuje start siatki.
**Wynik:** dokument protokołu + szablon karty źródła, do akceptacji autora przed zmianami kodu.

### A1. Nowy przebieg — decyzja: pełny v005 z nową prerejestracją

- Nowy run root i nowa prerejestracja (`notes/plans/v005-preregistration.md`), zamrożona przed startem.
- Seedy: 1–30 eksploracyjne, 31–60 również eksploracyjne (użyte w analizie v004), **61–90 potwierdzające**.
- Kod zamrażany dopiero po przejściu A0.

### A2. Rejestr skrótów i decyzji — decyzja: tabela do zatwierdzenia

Tabela wszystkich 24 punktów z R1 §14: kategoria (naprawiamy / decyzja projektu, opisana / ograniczenie w Limitations),
przyczyna Z1–Z11, proponowana poprawka. Po zatwierdzeniu staje się rejestrem decyzji projektowych
(`notes/plans/v005-decisions.md`); każde nowe udogodnienie dla jednej metody wymaga wpisu.

### A3. Darmowe f2 — decyzja: dla nikogo

Usunąć hook `analytic_cost` z P3Net (świeże f2 kandydatów). Dane v004 (`inherited_cost` ≈ S5 w 16/16, R2 §2.3) wskazują,
że strata jakości będzie niewielka; v005 to zmierzy.

### A4. Baseline'y — decyzja: przeliczyć wszystkie poprawione wersje

- SMAC3: `n_trials` = budżet (projekt początkowy 25%).
- MOEA/D: eliminacja duplikatów albo operator kategoryczny; pełne zużycie budżetu.
- NSGA-Net: turniej binarny; BOA wg publikacji (albo jawne odstępstwo w karcie).
- NSGANetV2: adaptacyjny wybór surogatu, wewnętrzny NSGA-II na (f̂1, złożoność), wybór podzbioru wg publikacji.
- **SH-EMOA i MO-BOHB: pełne wersje wielowiernościowe w torze MF**; w torze głównym ich części jednowiernościowe pod
  poprawnymi nazwami.
- BANANAS, P3-alone, pozostałe — wg kart źródła.
- Kody referencyjne: `automl/multi-obj-baselines` (SH-EMOA, MO-BOHB), oficjalny kod NSGANetV2, `naszilla` (BANANAS),
  optuna (NSGA-II/III). Gdzie kodu nie ma — wystarcza publikacja (karta źródła).
- Kryterium zgodności z referencją ustalone przed testem (np. mediana HV w granicy ±5% na problemie syntetycznym).

### A5. P3Net S6 — decyzja: silnik zgodny z P3 + nowy surogat, jako nowa wersja z testami

Zasada (decyzja 2026-10-16): pomysł P3Net to **P3 zastosowane do joint NAS+HPO z surogatem** — tego się trzymamy.
Wzorcem silnika jest P3 (Goldman & Punch, GECCO'14, Fig. 1–3, §2.1–2.3), nie dotychczasowa piramida P3Net.

- **Silnik (wzorcem P3):** w każdej iteracji jedno nowe losowe rozwiązanie; (FIHC wg P3 albo jawne odstępstwo, jeśli
  wymaga go budżet — uzasadnione w karcie, por. Dushatskiy §2.3.4); wspinanie przez **wszystkie** poziomy z mieszaniem
  względem populacji każdego poziomu; awans na poziom wyżej przy poprawie; poziomy bez rozmiarów docelowych; unikalność
  rozwiązań w piramidzie; zbiory mieszania bez korzenia, z singletonami, filtr D=0, od najmniejszych; dawca różniący się
  w danym zbiorze; akceptacja kroku względem bieżącego rozwiązania.
- **Surogat w silniku:** odstępstwa od P3 tylko tam, gdzie wymaga ich surogat (np. które kroki są oceniane naprawdę, a które
  przez surogat) — każde w karcie źródła i w rejestrze decyzji.
- **Nowy surogat:** log(f1) lub strata rankingowa; interakcje w obrębie F. Nowy opis w artykule, pisany razem z kodem i
  testami (A0).
- **Wielokryterialność:** kryterium „poprawy” i awansu w P3 jest jednokryterialne — sposób uogólnienia na (f1, f2) do ustalenia
  w karcie źródła (decyzja projektu, wpis w rejestrze).
- Dotychczasowa piramida (S1–S5) nie jest utrzymywana jako wariant; jej wyniki zostają jako zapis v004. Porównanie S4′ vs S5
  (A9) traci znaczenie dla v005 i jest tylko opisem historii v004.

### A6. Bartnik — decyzja: wierny wariant deterministyczny + wariant probabilistyczny (PSA)

Według pracy (R1 §4.2): bez FIHC, ewaluacje bramkowane wewnątrz GOM, α-kwantyl od 1 z relaksacją ×0.999, wspinanie przez
wszystkie poziomy, warm-up 100, archiwum elitarne. Test odtworzenia: NB201, budżet 500, warm-up 100, 10 seedów —
porównanie z Tabelą 7.1 (na FLOPs, bo energii nie mamy; różnica opisana).

### A7. Ewaluacje wewnątrz wspinaczki — decyzja: cała rodzina kanoniczna; eLyMPuS jako osobny tor (suplement)

- Wspinaczka jako maszyna stanów oddająca każdą ewaluację harnessowi (jak `p3_alone`).
- Kanoniczne P3 (M10 i warianty) z prawdziwymi ewaluacjami jako osobne ramiona obok obecnych.
- eLyMPuS: wierne elementy (strategia 1/x, circuit check, FIHC do optimum, pamięć przez cały przebieg; opcjonalnie graf
  zależności zasiany wiedzą dziedzinową — do omówienia z promotorem). Test: pułapki k-arne i binarne, potem NAS-HPO-II /
  NB201. Wynik do suplementu.

### A8. Zasoby — decyzja: bez GP przy b ≥ 200, naprawić pomiary

- Osobna tabela GP dla b = 50/100, z adnotacją: „najlepszy w jakości przy b ≤ 100; koszt X h i Y GB na przebieg”.
- s9: rejestrować pamięć mostu JAHS, pamięć GPU, czas ładowania mostu; asercja niepustych pól.
- Test zasobów każdej metody przy największym budżecie na docelowej maszynie przed zamrożeniem planu.

### A9. Analizy na danych v004 — decyzja: teraz

- S4′ vs S5 bezpośrednio.
- Test równoważności (TOST) dla par „bez różnicy” (np. S5 vs `inherited_cost`, M9 vs M10).
- Dekompozycja HV (tani vs dokładny koniec frontu); duplikaty.
- `posthoc_metrics.py` na JAHS (most, ~12 GB na zbiór).
- **Kod raportujący (dawna checklista A1–A6):**
  - A1: Mann–Whitney U zamiast sparowanego Wilcoxona w `stats/significance.py` + test; docstringi i podpisy tabel.
  - A2: guard `None` dla `adj_p`/`effect`; `n` z danych; adnotacja o kurczącej się rodzinie Holma (GP tylko 50/100).
  - A3: generator podsumowania — wszystkie wygrane, liczności z kierunkiem, referencja z danych, bez wpisanych nazw i liczb.
  - A4: tabela „vs RS” z dwiema kolumnami (lepsze / gorsze).
  - A5: opis braków w tabeli kosztów (A8).
  - A6: zamrożone fronty + punkt odniesienia zapisane i podane w tekście (`generate_report.py --refreeze`).

### A10. Retrening punktu kolanowego — decyzja: częściowy, zaplanowany z góry w prerejestracji v005

NB201 i NAS-HPO-II (publiczne skrypty treningowe). Właściciel, termin i skrypt wpisane przed zamrożeniem prerejestracji.

### A11. Odchylenia v004 — zrobione 2026-10-16 (`v004-preregistration.md` §7, z uzasadnieniem)

### A12. Metryka JAHS — decyzja: zmienić w prerejestracji v005

Punkt odniesienia HV wybrany na pilotażu (np. RS vs jedna silna metoda) przed zamrożeniem; „domknięcie luki” jako miara
opisowa. Wybór uzasadniony w prerejestracji.

### A13. Kontekst i raporty — zrobione 2026-10-16

Poprawione R1 §4.2, R3 i `CONTEXT.md` (praca Bartnik jest w repo).

### Do zebrania w etapie A (dla sekcji „Reproducibility”, opis w etapie C)

n i siatki dyskretyzacji per przestrzeń, κ per przestrzeń, hiperparametry wszystkich metod (R1 §13), punkt odniesienia HV.

### Zakończenie etapu A

- [ ] Protokół A0 przyjęty; karty źródeł i tabela „zdanie ↔ test” kompletne.
- [ ] Rejestr decyzji (A2) zatwierdzony.
- [ ] Wszystkie testy (źródło, integracja, asercje) przechodzą; etap `checks` zielony.
- [ ] Odtworzenie wyników Bartnik (A6) i zgodność baseline'ów z referencjami (A4) udokumentowane.
- [x] **Odpowiedź M. Przewoźniczka otrzymana (2026-10-21)** (mail 2026-10-20: mieszanie na ścieżce `opt_at_init 5` w OLyMPuS, `v005-level2-criteria.md`).
- [ ] **Czekamy na odpowiedź Niny Bartnik** (mail 2026-10-16, niejasności N-0–N-4 z `v005-sources/bartnik-mo-sa-p3-gomea.md`). **Dopytanie 2026-10-22:** bramka — percentyl (Alg. 8) czy próg względem elitist jak w kodzie SAGOMEA (poziom 2: −7.5 % vs SAGOMEA).
      Przed prerejestracją: odpowiedź zastępuje założenia Z-B#, brak odpowiedzi — założenia zostają i idą do artykułu.
- [ ] Tablica energii NB201 (`v005-sources/benchmarks.md` BM-2): pilotaż 1 000 wejść → pełny pomiar na laptopie
      (odłożone na koniec etapu A, decyzja 2026-10-18; blokada zegarów wymaga konsoli administratora).
- [ ] Prerejestracja v005 zamrożona (seedy 61–90, metryka JAHS, retrening, lista analiz → skrypty → pliki).
- [ ] Przebieg v005 zakończony; kontrola po przebiegu bez alarmów.
- [ ] Analizy z prerejestracji v005 policzone.

---

## Etap B — interpretacja (po etapie A)

| # | Decyzja |
|---|---|
| B1 | Narracja łączy: (a) prezentację algorytmu z porównaniem wielometrycznym, (b) rozbiór drogi projektowej, (c) zależność od benchmarku, (d) koszt praktyczny |
| B2 | NAS-Bench-201: krótka uwaga (benchmark słabo rozróżnia metody; FLOPs prawie jednokryterialne — R1 §4.2); jako materiał na dalsze kroki we wnioskach |
| B3 | eLyMPuS: po poprawkach zapisać jako kierunek potencjalnych ulepszeń; po ewaluacji v005 rozważyć testy na bogatszych danych |
| B4 | S4′: opisać jako alternatywę równoważną S5, na podstawie bezpośredniego porównania (A9) |
| B5 | Testy hipotez interpretacyjnych (log(f1), akceptacja po obu celach w wariantach RF, kanoniczne P3 ze świeżym f2, większe przestrzenie) — uruchamiane po v005, zależnie od wyników |
| B6 | JAHS f2 w v004 (`size_MB`) zawierało szum surogatu zależny od HP (BM-3: rozrzut przy stałej komórce do 34 %) — przy interpretacji v004 zaznaczyć, że część „poprawy f2” na JAHS mogła wynikać ze zmiany HP, nie architektury; v005 używa liczby parametrów |

---

## Etap C — tekst artykułu (po etapie B)

Z dawnej checklisty (sekcja C), nadal aktualne:
- Zawęzić twierdzenia do testowanego wariantu; formułować wyniki per przestrzeń, nie zbiorczo.
- Kontrybucja „harness”: deklaracja dostępności kodu i danych (link anonimowy).
- Reprodukowalność: dane zebrane w etapie A.
- Napisać jawnie: Holm tylko w komórce, liczności między komórkami opisowe.
- Asymetria strojenia: P3Net projektowany na seedach 1–60 tych samych przestrzeni, baseline'y domyślne; potwierdzenie = seedy
  61–90 + FCNet.
- Etykieta `tab:heatmap-jahs` → `tab:heatmap-cifar` (jeśli tabele zostają).
- Akapit o LLM w Related Work skrócić do 3–4 zdań.
- Zdecydować, co w tekście głównym, a co w suplemencie (dopiero przy pisaniu).

Nowe:
- Related Work: dodać pozycje dla metod z v004/v005 (Hyperband, ASHA, BOHB, Vizier, BoTorch/qNEHVI, SMAC3, BANANAS, REINFORCE,
  RegEvo, MOEA/D, NSGA-III, FCNet); poprawić cytowania SH-EMOA i MO-BOHB (Guerrero-Viu et al.); przejrzeć
  `notes/ga_landscape_2026.md` (ENCAS, kategoria 1 vs 2) i potem ją zarchiwizować.
- Poprawić wszystkie zdania z R3 §2.8 zgodnie z tabelą „zdanie ↔ test”.
- **Limitations — zebrać z kart** (`v005-sources/*.md`): każde odstępstwo kategorii O i każde założenie Z-# z
  „opisać w artykule”. Obowiązkowo m.in.: pomiar energii NB201 na laptopowym GPU (`benchmarks.md` BM-2, akapit
  „Limitations”), BULK & CUT nieuruchamialny na benchmarkach, założenia Z-B0–Z-B4 (brak kodu Bartnik), NSGA-Net bez BOA
  (kod autorów), RegEvo jako jedyna własna adaptacja MO, JAHS niższe wierności z surogatu (#25), GP tylko b ≤ 100 (#30).

Nieaktualne punkty dawnej sekcji C (nie przenoszone): „showing → finding no evidence” w kontrybucji 3 (kontrybucja upada),
sygnał negatywnego wyniku w tytule (wynik nie jest negatywny).

## Etap D — przed wysyłką (GECCO'27, double-blind)

- [ ] Usunąć `authordraft`, zanonimizować autorów; placeholdery afiliacji.
- [ ] Samocytowania (Bartnik; eLyMPuS — promotor) w trzeciej osobie.
- [ ] Link do kodu przez anonimowe repozytorium.
- [ ] `printacmref`, daty konferencji, prawa wg wymagań GECCO'27.
- [ ] Zregenerować wszystkie `_generated_*.tex` z run rootu v005; sprawdzić zgodność liczb w tekście z tabelami.

---

## Następna iteracja (po v005) — WAŻNE, nie zgubić

**eLyMPuS z wiedzą dziedzinową (sugestia promotora, potwierdzona 2026-10-16).** eLyMPuS startuje z grafem zależności
zasianym wiedzą o NAS+HPO zamiast z pustym:
- zależności w architekturze komórki (krawędzie wchodzące do / wychodzące z tego samego węzła; `none` a ścieżki
  wejście–wyjście);
- zależności między hiperparametrami (szybkość uczenia ↔ weight decay ↔ rozmiar batcha; szybkość uczenia ↔ aktywacja);
- zależności architektura ↔ hiperparametry;
- struktura kosztu (rozmiar / FLOPs jako suma wkładów krawędzi).

Do zbadania: zależności zasiane jako **pewne** vs jako **podejrzenie do weryfikacji** przez eLyMPuS (autor: „raczej
pewne”). Test uczciwości: porównać z eLyMPuS startującym z pustego grafu, żeby oddzielić zysk z wiedzy od zysku z mechanizmu.
Warunek: najpierw tor eLyMPuS na prawdziwych ewaluacjach z v005 (A7). Szczegóły uzgodnić z promotorem.

## Archiwizacja (harmonogram)

| Co | Kiedy |
|---|---|
| `notes/plans/v004-plan.md`, `notes/plans/v004-audit-checklist.md` | zrobione razem z utworzeniem tego planu |
| `notes/analysis-v004/PROMPTS.md` | po zakończeniu etapu A |
| `implementation/experiments-bartnik/`, `implementation/experiments-przewozniczek/` | po napisaniu artykułu na v005 (używa ich `scripts/check_paper_numbers.py` dla liczb v0.0.3); wtedy poprawić ten skrypt, `implementation/README.md` i ścieżki w docstringach |
| `implementation/experiments/results/tables/` (v0.0.3) | po napisaniu artykułu na v005 |
| `notes/ga_landscape_2026.md` | po aktualizacji Related Work (etap C) |
