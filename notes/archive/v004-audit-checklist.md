# Audyt v0.0.3 → lista kontrolna dla v0.0.4

Stan na 2026-10-07. Źródło: audyt tekstu `chapters/v003/` (v0.0.3) zestawiony z planem v004
(`configs/pipeline/v004.yaml`, `notes/plans/v004-preregistration.md`, `notes/plans/v004-plan.md`).
Wszystkie liczby v0.0.3 w tekście zgadzały się z wygenerowanymi tabelami — problemy dotyczą
interpretacji, uczciwości porównania i spójności opisu, nie arytmetyki.

Jak używać: przejść sekcje A → D w kolejności. A blokuje generowanie liczb. B to rozgałęzienia
zależne od wyników — każdy punkt mówi, co sprawdzić i jak zmienia się tekst. C to poprawki tekstu
niezależne od wyników. D to formalności przed wysyłką. Odhaczać `[x]` i dopisywać wynik w linii.

---

## A. Przed renderowaniem jakichkolwiek liczb v004 (kod analizy i raportowania)

Nic z tej sekcji nie wymaga ponownego liczenia przebiegów: wszystko działa na gotowych plikach JSON.
Wprowadzać dopiero po zakończeniu runbooka (`v004-finish-runbook.md`, krok 7), bo zmiana kodu
blokuje dopisywanie do run root `b4d25cac`.

- [ ] **A1. Test statystyczny.** `implementation/experiments/stats/significance.py:109` nadal liczy
  sparowany `wilcoxon`. Prerejestracja (§4) wymaga dwustronnego Mann–Whitney U (przebiegi różnych
  ramion z tym samym seedem nie dzielą wspólnych liczb losowych). Zmienić + test jednostkowy.
  Sprawdzić też docstringi i podpisy tabel ("paired Wilcoxon") w `scripts/render_results_tex.py`.
- [ ] **A2. Trzy luki raportowania** (pamięć projektu, 2026-10-05):
  - guard `None` dla `adj_p`/`effect` w tabelach fixed-budget (jak w `_heatmap_cell`);
  - `n=30` w podpisie liczone z danych, nie wpisane na sztywno;
  - zdanie w tekście/podpisie, że rodzina Holma kurczy się przy budżetach 200/350, bo
    `oss_vizier`, `botorch_qnehvi`, `botorch_qparego` biegły tylko na 50/100 (`v004-gp-small.yaml`).
- [ ] **A3. Generator podsumowania** (`render_results_tex.py` → `_generated_summary.tex`):
  - lista w nawiasie ma wymieniać **wszystkie** wygrane z zewnętrznymi baseline'ami (w v0.0.3:
    „seven … MO-BOHB” z 4 pozycjami w nawiasie);
  - usunąć „exactly the family the central question is staked on” przy porównaniach wewnątrz P3 —
    centralne pytanie (Q1) to S5 vs ramiona zewnętrzne, nie ablacje;
  - „loses at every budget on X (from budget 100)” → „at every budget from 100”;
  - liczba pojedyncza/mnoga dla 1 przypadku („one is a loss … cases where … beats”);
  - liczności zawsze z kierunkiem (prerejestracja §4): „k lepszych / m gorszych z 16”.
  - referencja = `p3net_cascade` (S5), nie `p3net` (S4); nazwy ramion, liczba ramion i rozmiar
    rodziny brane z danych, nie wpisane („eleven arms”, „ten other arms” w v0.0.3).
- [ ] **A4. Tabela „separacja od random search”** (`tab:vs-random`): dwie kolumny — lepsze / gorsze
  od RS. W v0.0.3 P3-alone (10) i MO-BOHB (1) liczyły się tak samo jak ramiona lepsze od RS.
- [ ] **A5. Etap s9 (timing)** — w przebiegu nic do zmiany: s9 liczy się z `v004.yaml` w `b4d25cac`,
  `gp-small` go nie uruchamia (runbook, krok 4). W tekście opisać brak 4 punktów `oss_vizier`
  (OOM przy budżecie 350) w tabeli kosztów.
- [ ] **A6. Front referencyjny i punkt referencyjny HV** — zamrożone przed odczytem seedów 31–60
  (prerejestracja §3). Zapisać commit/plik i podać punkt referencyjny w tekście.

---

## B. Po wynikach — co sprawdzić i jak to zmienia tekst

Każdy punkt: **pytanie → gdzie patrzeć → gałęzie**. Wynik z seedów 1–30 to eksploracja; tylko
31–60 (s6) jest potwierdzające dla Q1, Q4, Q7. Gdy się różnią — oba obok siebie (prerejestracja §2).

### B1. Czy null to cecha P3, czy naszego wariantu piramidy? (audyt #1 — krytyczny)

Kontekst: v0.0.3 przypisuje bootstrap „population pyramid” / „P3's geometric level growth”.
Kanoniczny P3 (Goldman & Punch 2014) dodaje jedno rozwiązanie z hill-climbingu na iterację i nie ma
docelowych rozmiarów 2^k. S5 (`p3net_cascade`) nadal ma `growth_factor: 2`; `cascade` naprawia
tylko „sweep tylko najnowszego poziomu”.

- Gdzie: Q1, ramiona `bartnik_p3`, `przewozniczek_p3elympus`, `canonical_p3_scalar_fihc` vs
  `random_search` i vs S5; udział bootstrapu S5 vs S4 (diagnostyka).
- [ ] Kanoniczne P3 **separują się od RS na korzyść**, S5 nie → diagnoza „nasz geometryczny wzrost
  poziomów” jest wspierana. Tekst: zawsze „our level-growth schedule”, nigdy „P3's pyramid”.
- [ ] Kanoniczne P3 **też nie separują się** → null nie jest specyficzny dla piramidy. Diagnoza
  bootstrapu spada do roli obserwacji o S5; główna teza przesuwa się na benchmark/sufit (B6) lub
  na cechę wspólną rodziny P3. Przepisać abstrakt, „What the diagnosis supports” i kontrybucję 2.
- [ ] Udział bootstrapu S5 wciąż ~90% przy 350 → podać obok S4; jeśli cascade go nie zmienił,
  powiedzieć to wprost.
- [ ] Sekcja 4 „Following P3, … $2^k$” → „Unlike canonical P3, …”. Ujednolicić trzy opisy reguły
  wzrostu poziomu (Rys. 1 „stop yielding improved solutions”, Sek. 4 „fails to increase level's
  hypervolume”, Diagnoza „hypervolume-contribution criterion rather than strict dominance”).

### B2. Surogat względny vs absolutny (audyt #2 — krytyczny)

Kontekst: `p3_absolute_cascade` = RidgeCV na one-hot, ten sam model co S5. Dla modelu addytywnego
predykcja względna to różnica dwóch predykcji absolutnych — różnica S5 vs `p3_absolute_cascade`
sprowadza się do doboru próbek uczących (pary vs punkty). Null jest **oczekiwany z konstrukcji**.

- Gdzie: Q4 (rodzina 4 wariantów), `p3_absolute_cascade`, M7 `p3net_bartnik` (RF), kontrola
  `p3net_bartnik_fihc`, M8 `p3net_elympus`.
- [ ] S5 ≈ `p3_absolute_cascade` → napisać, że to przewidywalne dla liniowego modelu, a nie
  dowód przeciw idei względnego surogatu. Nie sprzedawać jako odkrycia.
- [ ] RF (M7) > S5 → wspiera diagnozę addytywności; przesuwa wniosek na „liniowy surogat”.
- [ ] RF ≈ S5 → addytywność nie jest wąskim gardłem; osłabić akapit „The surrogate is additive…”.
- [ ] M8 vs kontrola `p3net_bartnik_fihc` → jedyna czysta izolacja wkładu eLyMPuS; raportować
  wprost niezależnie od kierunku.
- [ ] Poprawić zdanie w `proposed_optimizer`: ridge na konkatenacji (x, x′) ma **dwa niezależne**
  wektory wag (w₁·x + w₂·x′), nie „w·onehot(x) − w·onehot(x′)” — chyba że model jest tak
  ograniczony; sprawdzić w kodzie i opisać zgodnie z kodem.
- [ ] Nazwa „linkage-aware”: surogat to jeden globalny model, linkage wyznacza tylko, które pary
  się porównuje. Albo przemianować („linkage-restricted”), albo zdefiniować dokładnie, co znaczy.
  Future work sam przyznaje, że surogat nie korzysta z drzewa linkage.

### B3. Darmowe f2 z wyroczni (audyt #4 — krytyczny, NIEROZWIĄZANE w v004)

Kontekst: S5 domyślnie `use_analytic_cost=true` — przy wyborze C* czyta f2 nieewaluowanych
kandydatów. Na NAS-HPO-Bench-II (`substrates/nas_hpo_bench_ii.py:117`) i FCNet (`fcnet.py:134`)
f2 = czas treningu z tabeli, czyli informacja dostępna dopiero po treningu. Tylko P3Net ma ten hook.
Problem Formulation sama pisze, że ten f2 „is not cheaper to obtain”.

- Gdzie: s4, `p3net_cascade_inherited_cost` vs S5, osobno per przestrzeń.
- [ ] Różnica pomijalna → ujawnić w Fairness controls jedno zdanie + wynik wariantu.
- [ ] Różnica istotna na NAS-HPO/FCNet → S5 jest uprzywilejowany; raportować wariant
  `inherited_cost` jako właściwy na tych przestrzeniach albo doliczać zapytania f2 do budżetu.
- [ ] Na JAHS rozmiar modelu jest faktycznie liczalny bez treningu — rozróżnić przestrzenie.
- [ ] Sprawdzić, czy którekolwiek inne ramię (NSGANetV2, P3+abs.) dostaje f2 kandydatów
  nieewaluowanych; jeśli nie — napisać, że to asymetria na korzyść P3Net.

### B4. „Nie odróżnia się od RS” ≠ „zachowuje się jak RS” (audyt #3)

Kontekst v0.0.3: δ(P3Net vs RS) dodatni w **16/16** komórek (+0.03…+0.34), żadna istotna.

- [ ] Policzyć znaki δ S5 vs RS we wszystkich komórkach (primary + FCNet). Jeśli znowu
  jednokierunkowe — podać jako obserwację eksploracyjną (prerejestracja zakazuje agregacji p).
- [ ] Zmienić sformułowania „behaves as random search does” na „not distinguishable from RS at
  this sample size”; ewentualnie dodać (jako eksploracyjny) test równoważności TOST z jawnie
  podanym marginesem δ albo raport mocy.
- [ ] Usunąć lub osłabić argument Spearman ρ=0.980 (n=144): punkty zależne, korelacja w dużej
  części mechaniczna, jeśli P3Net ≈ RS (audyt #11).

### B5. Baseline'y i ich nazwy (audyt #5)

- [ ] SH-EMOA i MO-BOHB w głównym torze biegną przy jednej wierności (brak SH; BOHB-KDE na
  skalaryzacji Tchebycheffa). Napisać to w Setup albo przemianować („SMS-EMOA-style”,
  „BOHB-KDE (single-fidelity)”). Prawdziwe multi-fidelity = tor Q7 (Hyperband/ASHA/BOHB).
- [ ] Jeśli zewnętrzne wygrane S5 są znowu tylko z MO-BOHB, a MO-BOHB sam jest gorszy od RS →
  nie prezentować ich jako wygranych z „established baseline”.
- [ ] NSGANetV2: bez supernetu, bez adaptacyjnego wyboru surogatu; sprawdzić, jaki regresor podaje
  `run_experiment.py` (`model_factory`) i opisać jako „NSGA-II + absolute regressor in the spirit
  of NSGANetV2”.
- [ ] `nsganetv2_continuous` **nie jest w planie v004** — ograniczenie z Fairness controls zostaje;
  zostawić zdanie w Limitations.
- [ ] Cytowanie SH-EMOA przez `beume2007smsemoa` → cytować Guerrero-Viu et al. jako źródło
  SH-EMOA, SMS-EMOA najwyżej jako bazę.

### B6. Eksperymenty izolujące i rodzina benchmarków (audyt #7)

- [ ] NB201 (s5) jest opisowe (D6) — w tekście nie używać sformułowań „showing the null survives”;
  mediany ~0.985–0.994 → podać jako sufit/niską moc.
- [ ] FCNet (Q5) zgodny z Q1 → „null replicates on a second family”; niezgodny → to staje się
  główną wiadomością o zależności od benchmarku. W obu wypadkach Limitations: dane z zewnętrznej
  konwersji, interpolowany czas treningu, małe MLP 2-warstwowe.
- [ ] Sprawdzić, czy na FCNet też jest plateau we wczesnym budżecie — jeśli tak, to argument za
  „benchmark ceiling”, nie za wadą metody.
- [ ] „documented to win” o Bartnik (praca magisterska): doprecyzować — wygrywa z MO-LS, nie z RS.

### B7. Diagnostyka surogatu (audyt #9, #10)

- [ ] Precyzja bramki: porównać z **odsetkiem ulepszeń wśród propozycji** (base rate), nie z 0.5.
  Raportować MCC i balanced accuracy (prerejestracja §5).
- [ ] Podać jednostki MSE (punkty procentowe błędu? ułamek?).
- [ ] Proxy interakcji: z FCNet 8 punktów zamiast 4 — jeśli kolejność się utrzymuje, podać
  korelację rang z n; jeśli nie — usunąć akapit „This is exactly the order…”.
- [ ] Ramię `p3net_surrogate_interactions` (v0.0.3, 1/16) nie jest w v004 — albo usunąć zdanie,
  albo zaznaczyć, że pochodzi z v0.0.3.

### B8. Ścieżka projektowa i twierdzenia przyczynowe (audyt #8)

- [ ] s2 (S1→S2→S3→S4→S4′) daje liczby dla: „warm start lowers it only modestly”, „fixed constant
  regressed severely” (S4′), wpływu świeżego f2 (S2) i Ridge (S3). Każde z tych zdań ma dostać
  liczbę albo zniknąć.
- [ ] „Intervention” z P3+abs. przeniesionym na piramidę: jeśli `p3_absolute` (stary) vs
  `p3_absolute_cascade` to porównanie tego, sprawdzić, czy różnią się też OLS vs Ridge — wtedy
  to nie jest czysta interwencja i trzeba to napisać.
- [ ] s4 (warianty single-axis + κ×próg na S5) zastępuje ograniczenie „defaults … not
  re-validated after the redesign” — usunąć je z Limitations albo zaktualizować.

### B9. Znaczenie praktyczne (audyt #14)

- [ ] Obok δ podać bezwzględne różnice HV/IGD+ (w v0.0.3 ~0.005–0.01 HV).
- [ ] Cost-to-target (90/95/99%), regret, retrening punktu kolanowego, koszty z s9 — wybrać 1
  rysunek/tabelę do głównego tekstu, reszta do suplementu.
- [ ] Argument o koszcie optymalizatora BO (pamięć projektu) — wymaga danych z s9.

### B10. Rozbieżności eksploracja vs potwierdzenie

- [ ] Dla każdej komórki Q1/Q4/Q7: zgodność kierunku i istotności seedy 1–30 vs 31–60.
  Rozbieżności raportować obok siebie, nie wybierać korzystniejszego.

---

## C. Poprawki tekstu niezależne od wyników

- [ ] **Abstrakt/wnioski:** zawęzić twierdzenia do tego, co testowano (nasz wariant piramidy,
  liniowy surogat), chyba że B1 pokaże inaczej.
- [ ] **Wnioski:** „loses to SH-EMOA, TPE, NSGA-Net, and NSGANetV2 increasingly” — w v0.0.3 nie
  dotyczyło Fashion-MNIST. Formułować per przestrzeń albo z wyjątkiem.
- [ ] **Kontrybucja 4 (harness):** dodać deklarację dostępności kodu/danych (link anonimowy).
- [ ] **Kontrybucja 3:** „showing” → „finding no evidence that…”.
- [ ] **Reprodukowalność:** n i rozdzielczość siatki per przestrzeń, κ per przestrzeń,
  hiperparametry wszystkich baseline'ów (tabela w suplemencie), punkt referencyjny HV.
- [ ] **Holm tylko w komórce** — napisać jawnie, że liczności między komórkami są opisowe.
- [ ] **Asymetria strojenia:** napisać, że S5 projektowano na seedach 1–30 tych samych przestrzeni,
  a baseline'y mają domyślne ustawienia; potwierdzenie = seedy 31–60 + FCNet.
- [ ] Etykieta `tab:heatmap-jahs` dotyczy tylko CIFAR-10 → `tab:heatmap-cifar`.
- [ ] Akapit o LLM w Related Work skrócić do 3–4 zdań (limit stron).
- [ ] Tytuł i sekcja „Proposed Optimizer”: rozważyć sygnał negatywnego wyniku w tytule.
- [ ] Liczba ramion/rozmiar: przy ~24 ramionach głównych + 5 finalnych + 3 MF + 4 etapach + 16
  wariantach nie zmieści się to w 8 stronach. Zdecydować, co jest w głównym tekście (proponuję:
  Q1 heatmapy, Q4, B1, B3, jedna figura kosztów), reszta do suplementu.

---

## D. Przed wysyłką (GECCO, double-blind)

- [ ] Usunąć `authordraft`, zanonimizować autorów; placeholdery afiliacji.
- [ ] Samocytowania (Bartnik — promotor M. Przewoźniczek; eLyMPuS) w trzeciej osobie.
- [ ] Link do kodu przez anonimowe repozytorium.
- [ ] `printacmref`, daty konferencji, prawa — wg wymagań GECCO'27.
- [ ] Zregenerować wszystkie `_generated_*.tex` z ostatniego run root i sprawdzić zgodność liczb
  w tekście z tabelami (jak w audycie v0.0.3).
