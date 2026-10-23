# Prompty dla agentów — analiza v004 w trzech przebiegach

Każdy przebieg w osobnej sesji, po kolei. Każdy czyta `notes/analysis-v004/CONTEXT.md` i raporty poprzednich przebiegów.
Raporty: `notes/analysis-v004/reports/`. Poprawę samego artykułu robi osobny, późniejszy przebieg — po decyzjach autora z raportu 3.

---

## Przebieg 1 — audyt wierności implementacji

```
Przeczytaj najpierw notes/analysis-v004/CONTEXT.md (repo: c:\Workspace\Uczelnia\p3net_gecco2027) i stosuj jego zasady wspólne.

Zadanie: audyt wierności implementacji KAŻDEJ mierzonej metody w v004. Raport zapisuj przyrostowo do
notes/analysis-v004/reports/01-implementation-audit.md. Nie analizuj jeszcze wyników jakościowych — to przebieg 2.

Zakres: każde ramię z configs/pipeline/v004.yaml i v004-gp-small.yaml (grupy comparison, final, multi_fidelity, etapy S1–S4′ z s2,
16 wariantów z s4, ramiona s5 NAS-Bench-201). Dla każdego ustal i opisz:
1. Czym metoda jest według źródła (publikacja w notes/articles/ lub dokumentacja/kod biblioteki; jeśli źródła brak — zaznacz niższą pewność).
2. Co faktycznie robi kod: plik, klasa/funkcja, kluczowe parametry z YAML, wersja biblioteki (uv.lock / .venv / vendor/).
3. Typ: pełna implementacja / adapter do biblioteki / własna rekonstrukcja / uproszczony wariant / nowa generalizacja.
4. Odstępstwa od oryginału, limity, „pójście na skróty”, wyłączone mechanizmy, wartości domyślne zamiast strojonych, ograniczenia harnessu
   (ask–tell, budżet liczony tylko w pełnych ewaluacjach, brak dostępu do benchmarku z wnętrza metody, dyskretyzacja HP, jedna wierność,
   obsługa zmiennych kategorycznych, wielokryterialność vs skalaryzacja).
5. Czy ramię dostaje informację niedostępną innym (np. hook analytic_cost / darmowe f2 przy wyborze kandydatów — checklista B3),
   albo jest strukturalnie upośledzone (np. nie zużywa budżetu).
6. Jakie wnioski z wyników to odstępstwo podważa lub zawęża: co mówi o metodzie ogólnie, a co tylko o naszej wersji.
7. Pewność ustalenia (wysoka/średnia/niska) i co trzeba by sprawdzić, żeby ją podnieść.

Punkty startowe (zweryfikuj każdy w kodzie; lista NIE jest kompletna):
- eLyMPuS (lib/src/p3net/surrogates/elympus.py, search_engines/p3/fihc_elympus.py): k-arna generalizacja to własny projekt repo, nie publikacji;
  tylko zależności symetryczne (brak C4–C6); brak pełnego rankingu k wartości; P3-eLyMPuS, nie OLyMPuS (brak PXrLL, perturbacji ILS,
  wykrywania brakującego linkage); jednokryterialny; w p3net_elympus i przewozniczek_p3elympus fitness_fn = predykcja random forest, nie prawdziwa
  ewaluacja; w przewozniczek_p3elympus GOM/promocja w climb też po surogacie. Porównaj z publikacją LyMPuS w notes/articles/linkage learn/
  i z notes/archive/lympus-nas-adaptation-*.md. Odpowiedz wprost: czy na tej implementacji wolno pisać „eLyMPuS nie pomaga” i jaki test byłby rzetelny.
- bartnik_p3: rekonstrukcja z pracy magisterskiej (implementation/experiments-bartnik/, notes/archive/experiments-bartnik-plan.md); NB201: f2 = FLOPs
  zamiast energii GPU, f1 = test error.
- canonical_p3_scalar_fihc (M10): czy faktycznie izoluje mechanizm porównania od skalaryzacji (luka B4 z _parked/przewozniczek_isolation.tex).
- P3Net S1–S5 i warianty: odstępstwa od kanonicznego P3 (publikacja P3 w notes/articles/linkage learn/P3/) — rozmiary poziomów 2^k,
  sweep tylko najnowszego poziomu (S4) vs cascade (S5), kryterium wzrostu po HV, warm start, brak mutacji, telescoping, κ, analytic_cost.
- NSGANetV2 i NSGA-Net vs publikacje (notes/articles/NSGA/): supernet/weight sharing, adaptacyjny wybór surogatu, jaki regresor (model_factory).
- SH-EMOA, MO-BOHB: jedna wierność w torze głównym (checklista B5); poprawność nazwy i cytowania.
- Hyperband/ASHA/BOHB (multi_fidelity.py): budżet w ekwiwalentach pełnych ewaluacji (decyzja D1), które punkty trafiają do metryki.
- Vizier, BoTorch qNEHVI/qParEGO, SMAC3-ParEGO, TPE, MOEA/D, NSGA-III, BANANAS, REINFORCE, RegEvo, MO-LS, random search: adaptery,
  parametry domyślne vs dobrane, ograniczenia (GP tylko b=50/100), dlaczego MOEA/D często nie zużywa budżetu.
- Benchmarki (implementation/experiments/substrates/, vendor/jahsbench-env/): co jest f1/f2 na każdej przestrzeni, z jakiego splitu,
  przy jakiej wierności, czy deterministyczne; dyskretyzacja HP (siatki per przestrzeń).
- results/checks/: co już sprawdzono (np. p3_trap_correctness, nsga_sanity_check) i co z tego wynika dla wiarygodności implementacji.

Wynik:
- tabela zbiorcza: ramię × (źródło, typ implementacji, główne odstępstwa, informacja uprzywilejowana/upośledzenie, wpływ na wnioski, pewność);
- tabela hiperparametrów wszystkich metod (do suplementu: wartości z YAML i domyślne biblioteki);
- omówienie najważniejszych przypadków (co najmniej: eLyMPuS, kanoniczne P3, P3Net S4/S5, NSGANetV2, SH-EMOA/MO-BOHB, GP, multi-fidelity);
- lista ograniczeń do sekcji Limitations i lista propozycji poprawek implementacji (tylko jako opcje).
W czacie na koniec: krótkie podsumowanie najpoważniejszych ograniczeń i lista rzeczy nieustalonych.
```

---

## Przebieg 2 — analiza wyników

```
Przeczytaj najpierw notes/analysis-v004/CONTEXT.md (repo: c:\Workspace\Uczelnia\p3net_gecco2027) i stosuj jego zasady wspólne.
Potem przeczytaj raport z przebiegu 1: notes/analysis-v004/reports/01-implementation-audit.md — uwzględniaj go w każdym wyjaśnieniu.

Zadanie: wyczerpująca analiza wyników v004. Raport zapisuj przyrostowo do notes/analysis-v004/reports/02-results-analysis.md.

Kolejność pracy:
0. Uruchom notes/analysis-v004/run_all.sh (V004_OUT poza repo) i przejrzyj kod skryptów. Zweryfikuj metryki na próbce przebiegów względem
   implementation/lib/src/p3net/metrics/ (HV, IGD+) i konwencje znaku δ. Błędy w skryptach opisz i popraw we własnej kopii poza repo.
   Dopiero po własnych obliczeniach danej sekcji otwórz notes/analysis-v004/INITIAL_FINDINGS.md i wypisz rozbieżności.
1. Odchylenia od prerejestracji: potwierdź i uzupełnij listę z CONTEXT.md (w tym, czy wykonano retrening punktu kolanowego, prereg §5).
2. Pytania Q1–Q7, każde osobno: per przestrzeń × budżet mediany, IQR, MWU + Holm w komórce, Cliff's δ, różnice bezwzględne metryki i ich znaczenie
   praktyczne; liczności z kierunkiem; zgodność seedy 1–30 vs 31–60 (checklista B10). Q5 (FCNet) i NB201 (s5) opisowo, zgodnie z prereg §6.
3. Wyjaśnienia mechanizmów — dla każdej istotnej obserwacji: dlaczego tak wyszło, na podstawie kodu, diagnostyk i raportu 1. Minimum:
   - dlaczego S5 naprawił S4 (bootstrap, cascade) i czy to wystarcza jako wyjaśnienie;
   - dlaczego S5 dobrze na JAHS, słabo na FCNet; dlaczego kanoniczne P3 odwrotnie;
   - drabinka S5 → RF → RF+FIHC → RF+FIHC-eLyMPuS: co daje każdy krok; zweryfikuj hipotezę „akceptacja po samym f1 psuje front po osi f2”
     (rozkład f2 ocenionych punktów, zasięg frontu po osi kosztu, metryka tylko po f1); sprawdź w kodzie, co zawiera surrogate_quality_log;
   - dlaczego Vizier wygrywa na benchmarkach tabelarycznych, a nie na JAHS; dlaczego ASHA tak dobrze na JAHS;
   - dlaczego SH-EMOA/BANANAS/TPE są mocne; dlaczego P3-alone, MO-BOHB, MO-LS, MOEA/D słabe;
   - rola typu przestrzeni: tylko architektura (NB201) vs architektura+HPO (JAHS, NAS-HPO-II) vs tylko HPO (FCNet); model-surogat (JAHS)
     vs tabela; dyskretyzacja HP;
   - rola budżetu: gdzie przewagi rosną/maleją z budżetem i dlaczego (w tym S5 przy b=50/100 vs 200/350).
4. Analizy drugorzędne z prereg §5 (opisowo): krzywe anytime, cost-to-target (90/95/99%), jakość decyzji surogatu (scripts/posthoc_metrics.py:
   precyzja vs base rate, MCC, balanced accuracy, ρ, kalibracja), regret, luki generalizacji (val–test, gdzie benchmark je ma), koszty z s9
   (wall, CPU, narzut optymalizatora, RAM, simulated training time; pieniądze/energia tylko przy jawnych założeniach), duplikaty, wykorzystanie
   budżetu, błąd telescopingu vs głębokość łańcucha, proxy interakcji (addytywność) per przestrzeń — także na FCNet.
   Jeśli czegoś nie da się policzyć z zapisanych danych — napisz dlaczego.
5. Kompromis jakość–koszt: dla każdej przestrzeni, które metody są na froncie Pareto (jakość × czas, jakość × RAM).
6. Wyjaśnienia alternatywne i zagrożenia trafności: dopasowanie do benchmarku vs ograniczenie modelu; asymetria strojenia (S5 projektowany na seedach
   1–30 tych samych przestrzeni, baseline'y domyślne); darmowe f2; dyskretyzacja HP; wierność baseline'ów (raport 1); moc testów; wpływ zamrożonego
   frontu; brak GP przy b=200/350; poprawność skryptów.
7. Lista wszystkich wniosków: siła dowodu (1–4), zależność od ograniczeń implementacji, czym rozstrzygnąć.
W czacie na koniec: krótkie podsumowanie najważniejszych wniosków i rozbieżności z INITIAL_FINDINGS.md.
```

---

## Przebieg 3 — konfrontacja z artykułem, notatkami i literaturą

```
Przeczytaj najpierw notes/analysis-v004/CONTEXT.md (repo: c:\Workspace\Uczelnia\p3net_gecco2027) i stosuj jego zasady wspólne.
Potem przeczytaj raporty: notes/analysis-v004/reports/01-implementation-audit.md i 02-results-analysis.md. Opieraj się na nich;
jeśli coś liczysz lub sprawdzasz dodatkowo, napisz to.

Zadanie: skonfrontować wyniki z artykułem v0.0.3, checklistą audytu, notatką o usprawnieniach i literaturą — jako materiał do dyskusji
o aktualizacji artykułu. Raport zapisuj przyrostowo do notes/analysis-v004/reports/03-paper-confrontation.md. Nie edytuj artykułu.

1. Checklista notes/plans/v004-audit-checklist.md, punkty B1–B10: dla każdego — która gałąź się zrealizowała, z jakim dowodem, co to zmienia w tekście.
2. Każde twierdzenie artykułu chapters/v003/ (abstrakt, kontrybucje, Problem Formulation, Proposed Optimizer, Setup, Headline, Diagnosis, Isolation,
   Wnioski, Limitations, Future work, także Related Work tam, gdzie dotyka wyników): utrzymane / do zmiany / upada — z uzasadnieniem i odnośnikiem
   do raportu 1 lub 2. Osobno: zdania opisujące metody, które raport 1 wykazał jako nieścisłe (np. opis surogatu, piramidy, baseline'ów).
3. notes/p3net-improvements.md: każdy fakt z „Gdzie jesteśmy” — aktualny czy nie; każdy problem P1–P7 — rozwiązany / częściowo / otwarty;
   każdy pomysł I1–I9 i R1–R7 — wsparty / osłabiony / zbędny / nadal otwarty; które priorytety z końca notatki zmieniają kolejność.
4. Literatura z Related Work (refs.bib, notes/articles/): gdzie wyniki zgadzają się, a gdzie kłócą z cytowanymi pracami (den Ottelander, Goldman & Punch,
   Qiao & Gallagher, Guerrero-Viu, Bartnik, Przewoźniczek/eLyMPuS, Dushatskiy, CS-GOMEA, Lopes, Yang, Mehta, NSGANetV2) i co z tego wynika.
5. Możliwe narracje zaktualizowanego artykułu (bez cięcia pod limit stron): dla każdej — główna teza, które wyniki ją niosą (z siłą dowodu),
   co ją osłabia, czego brakuje, największe ryzyko recenzenckie.
6. Lista brakujących analiz i eksperymentów (z priorytetem i szacunkiem kosztu), w tym: poprawki A1–A6, test eLyMPuS na prawdziwych ewaluacjach,
   akceptacja wielokryterialna w wariantach RF, większe przestrzenie, ewentualna kontrola NSGANetV2-continuous.
7. Pytania do autora — decyzje, których nie podejmiesz sam, każde z rekomendacją i konsekwencjami.
W czacie na koniec: krótkie podsumowanie i pytania z punktu 7.
```
