# v005 — lista zadań

Stan na 2026-10-31. **To jedyna lista zadań projektu.** Podstawa: „Zakończenie etapu A” w `v005-plan.md`.
Zasady:
- każda pozycja: co, po co, kto, czas, czy wymaga liczenia;
- nowe pozycje tylko jako PROPOZYCJA (sekcja na końcu), wpisywane do listy po akceptacji autora;
- każda decyzja zapisana raz (sekcja „Decyzje”); Claude nie pyta o nią ponownie.

## Etap A — co zostało

| # | Co | Po co | Kto | Czas | Liczenie? | Stan |
|---|---|---|---|---|---|---|
| 1 | Commit i push bieżącej pracy | zabezpieczenie; serwer bierze kod z repo | autor | minuty | nie | otwarte |
| 2 | Serwer Hetzner: snapshot albo usunięcie | koszt przestoju (rozliczenie godzinowe) | autor | minuty | nie | 2026-10-31 zrobione; serwer postawiony ponownie na przebieg v005 — po skopiowaniu wyników (2026-11-16) znów do snapshotu/usunięcia; **otwarte** |
| 3 | f2 dla NB201 = HW-NAS-Bench, edge GPU (P1 a): tablica f2 + zmiana karty `benchmarks.md` BM-2 | bez tablicy f2 NB201 nie wchodzi do v005 | Claude | 2–3 h | nie | **zrobione 2026-10-31** (tablica, karta, C-41/C-42; testy W-BM2/W-BM3 → poz. 4) |
| 3b | Poprawki P3: (2a) pamięć per przebieg + pamięć serwera JAHS; (2b) kontrola `surrogate_share` przy b=100 | kolumna pamięci w tabeli kosztów; start przebiegu | Claude | ~3–4 h | nie | **zrobione 2026-10-31**; ścieżkę linuksową (`clear_refs`, PSS) sprawdzi test z rundy 8 w bramce `checks` na serwerze |
| 3c | Nanieść P6 (plan B4 → „inny profil”) i P7 (sprostowanie raportu 02 §2.1) | zgodność z A9 | Claude | minuty | nie | **zrobione 2026-10-31** |
| 3d | Bramka `checks` ustawia `P3NET_BENCHMARK_DATA` (bez tego testy na danych benchmarków są w bramce pomijane) — zaakceptowane 2026-10-31 | testy W-BM1–W-BM7 naprawdę działają przed przebiegiem | Claude | minuty | nie | **zrobione 2026-10-31** (`run_pipeline.py::run_checks`); bramka zielona dopiero po rundzie 8 (W-BM2, W-BM3) |
| 3e | Plan siatki pod P2 b (P9): GP tylko b = 50, 100; Vizier w `v005-vizier.yaml`; seedy 62–91 (R3 b) | prognoza ~10 dni; Vizier sam na maszynie | Claude | minuty | nie | **zrobione 2026-10-31** (`--dry-run`: 19 440 + 1 080 + 1 080 + 4 800 i 540 punktów) |
| 4 | Testy dla zmian z 3 i 3b (runda 8) | protokół: testy pisze niezależny autor testów | autor testów (prompt: Claude) | sesja autora testów | nie | **zrobione 2026-10-31** (runda 8; z danymi 13 passed, test pamięci przebiegu tylko na Linuksie → serwer) |
| 5a | Skrypty analiz v005 (prerejestracja §7, K1–K7, K9) napisane i sprawdzone na rekordach A8 przed zamrożeniem (P8) | bez skryptów obietnice prerejestracji nie są wykonalne (błąd v004, Z9) | Claude | szacunek 1–2 dni | nie (serwer GPU, rekordy A8) | **zrobione 2026-10-31** (`analysis_v005/`, `scripts/analyze_v005.py`, 9 testów; rekordy runów mają `evaluation_metrics`) |
| 5 | Prerejestracja v005 | zamrożenie metod, metryk, analiz przed przebiegiem | Claude pisze, autor zatwierdza | ~1 dzień pisania | nie | **treść zatwierdzona 2026-10-31** (`v005-preregistration.md`); skrypty analiz → poz. 5a |
| 6 | Przebieg v005 z Vizierem, jedna maszyna (P2 b): najpierw `v005.yaml` (6 workerów), potem `v005-vizier.yaml` (1 worker) z tego samego commita (zaczyna się automatyczną bramką `checks`: testy, determinizm, karty — minuty) | **jedyne wyniki do artykułu** | autor uruchamia | ~10 dni (prognoza z A8, `v005-a8-analysis.md`) | **tak, serwer** | **zrobione 2026-11-16** (start 2026-11-01; run rooty `c674c91e`, `c674c91e-vizier`). 2026-11-03: wszystkie 2 160 punktów głównej części na JAHS CIFAR-10 nieudane — OOM zabijał most JAHS (13–15 GB) przy 6 workerach (`dmesg` 2026-11-02 12:24–12:28); dane JAHS na serwerze kompletne. Decyzja autora 2026-11-03 (a): przebieg bez zmian; po v005 i Vizierze `run_pipeline.sh --plan configs/pipeline/v005.yaml --workers 2 --retry-failed` (ten sam commit i run root; szacunek ~2 dni) |
| 7 | Kontrola po przebiegu i analizy z prerejestracji | wyniki do etapu B | Claude | dni pracy | nie (odczyt wyników) | **częściowo 2026-11-16**: przebieg zakończony (26 400 + 540 rekordów, 0 brakujących, 0 duplikatów), posthoc JAHS seedy 62–71, `analyze_v005.py` → `analysis/`; przegląd w `notes/archive/v005/analysis-v005/reports/01-v005-results-overview.md`; odchylenia w prerejestracji §8; tabele `chapters/results/_generated_*.tex` (`scripts/render_v005_tex.py`). K8 (§5.4) niewykonalne — decyzja a (odchylenie). **K10 zrobione 2026-11-17:** 40/40 treningów, raport `notes/archive/v005/analysis-v005/reports/06-retraining-k10.md`, akapit w Results (NB201 śr. −0.10 pp, NHB −0.88 pp; ρ 0.75 / 0.92) |

Czekamy (nie blokuje 1–5): **Nina Bartnik** — N-0–N-4 i bramka MO-DSA. Brak odpowiedzi przed prerejestracją →
założenia Z-B zostają i idą do artykułu. **2026-10-31: autor nie spodziewa się odpowiedzi** → obowiązują założenia Z-B; Limitations (etap C) je opisuje.

## Zrobione (etap A)

- Protokół weryfikacji, karty źródeł, rejestr decyzji (`v005-decisions.md`), tabela „zdanie ↔ test” (`v005-claims.md`, 43/45).
- Poziomy 1–4 (testy, zgodność z kodem autorów, integracja, kontrole w trakcie przebiegu).
- A9: poprawki kodu raportującego A1–A6; równoważność, S4′ vs S5, dekompozycja HV, duplikaty (`notes/archive/analysis-v004/reports/04-a9-equivalence-hv.md`).
- A8: pomiar czasu i pamięci metod na serwerze (2026-10-24…29, ~5.5 dnia serwera; **wyniki nie wchodzą do artykułu**),
  analiza w `v005-a8-analysis.md`.
- Odpowiedź M. Przewoźniczka (2026-10-21).

## Decyzje autora zapisane w tej rundzie

| Data | Decyzja |
|---|---|
| 2026-10-26 | A8: Viziera dokończyć (pomiar); po OOM reszta planem `v005-resources-vizier-rest.yaml` |
| 2026-10-29 | Pomiarów energii na serwerze GPU autor nie jest w stanie zrobić. Pilotaż 5 (1 000 wejść) niezaliczony (`benchmarks.md` BM-2). |
| 2026-10-29 | HW-NAS-Bench jako f2 NB201 „brzmi najrozsądniej” — kierunek; formalna zmiana karty = P1 |
| 2026-10-30 | Posthoc JAHS na danych v004 przerwany (2 776 z 28 080 plików); brak = odchylenie v004 |
| 2026-11-16 | Retrening (§5.8, K10) na serwerze GPU (Intel Core i7-11800H, 16 wątków, 32 GB RAM, NVIDIA GeForce RTX 3050 Ti 4 GB, Windows 11), nie na serwerze GPU Hetzner — zastępuje decyzję z 2026-10-31 „GPU do retreningu (R9)” |
| 2026-11-16 | Retrening (§5.8, K10): punkt kolanowy z największego budżetu ramienia — b = 350, ramiona GP (Vizier, qNEHVI, qParEGO) b = 100; NB201 22 i NAS-HPO-II 27 punktów, ≈ 23 GPU-h (16–34) wg czasów z tablic. Doprecyzowanie prerejestracji (budżet nie był podany) |
| 2026-11-16 | K8 (§5.4) = a: odchylenie od prerejestracji — jakość decyzji surogatu niewykonana, bo metody `p3net/v005/` nie logują decyzji (`decision_log`), a `posthoc/` ma `decisions = None`; zastępczo opisać `surrogate_share` i `mixing_steps` (`budget_use.csv`). Posthoc tabelaryczny dokończony mimo to (serwer GPU) |
| 2026-11-03 | JAHS CIFAR-10 po OOM mostu: a — przebieg bez zmian, nieudane punkty ponownie po Vizierze z 2 workerami (`--retry-failed`), ten sam commit i run root |
| 2026-10-31 | P1 = a: f2 NB201 z HW-NAS-Bench, edge GPU |
| 2026-10-31 | P2 = b: Vizier w v005, jedna maszyna (~10 dni) |
| 2026-10-31 | P3: zrobić (2a) i (2b) |
| 2026-10-31 | P4 = granice: punkt odniesienia HV na JAHS z granic przestrzeni (błąd ≤ 100 %, maks. liczba parametrów z tablicy), bez pilotażu — zastępuje plan A12 |
| 2026-10-31 | P6: plan B4 zmienić na „inny profil” |
| 2026-10-31 | P7: raport 02 §2.1 sprostować |
| 2026-10-31 | Marginesy TOST (Cliff's δ, 90 % CI z bootstrapu): oba — m = 0.33 główny w zdaniach artykułu, m = 0.147 raportowany obok; tak samo w prerejestracji v005 |
| 2026-10-31 | Zaakceptowane: podział HV w medianie f2 frontu (raport 04); model prognozy czasu t(b) = t(b0)·(b/b0)^k (`v005-a8-analysis.md`) |
| 2026-10-31 | Prerejestracja: R1 a (Q2 = P3Net vs kanoniczne P3, P3Net-gate, P3Net-nolink; Q1 = 17 innych metod); R2 a (testy na JAHS ×3 + NAS-HPO-II; FCNet osobny blok; NB201 opisowo); R3 b (seed 61 zastąpiony 91 → seedy 62–91); R4 a (NB201: IGD+ vs front oracle); R6 (TOST: P3Net vs gate, nolink, kanoniczne P3); R7 a (koszty z rekordów siatki); R8 b (posthoc JAHS na kilku seedach); R9 a (retrening wszystkich ramion na NB201 i NAS-HPO-II). R5 — do dyskusji |
| 2026-10-31 | R5 = b1: HV na JAHS — cele znormalizowane granicami przestrzeni (f1 / 100; f2 = (p − min) / (max − min) liczby parametrów z tablicy), punkt odniesienia (1.1, 1.1), HV dzielone przez 1.21 (∈ [0, 1]); za praktyką „granice + margines” (Bartnik s. 53) |
| 2026-10-31 | R5′: dodać analizę wrażliwości HV na JAHS — punkty (1.05, 1.05) i (1.2, 1.2), opisowo |
| 2026-10-31 | R8 b: posthoc JAHS na 10 seedach (62–71), jak liczba runów u Bartnik, NSGANetV2, SA-P3-GOMEA; szacunek ≈ 4 h serwera po przebiegu |
| 2026-10-31 | Prerejestracja v005 — treść zatwierdzona przez autora. Zamrożona wersja = stan pliku w commicie, z którego startuje przebieg; zmiany wynikłe z 5a (skrypty) wpisywane przed startem z datą |
| 2026-10-31 | GPU do retreningu (R9): Hetzner, serwer GPU dedykowany; ofertę i cenę sprawdza i decyduje autor przed uruchomieniem retreningu — **zastąpione 2026-11-16: serwer GPU (RTX 3050 Ti)** |
| 2026-10-31 | P8: dodać pozycję „skrypty analiz napisać i sprawdzić na rekordach A8 przed zamrożeniem” (poz. 5a) |
| 2026-10-31 | P9: plan siatki — GP tylko b = 50, 100; Vizier osobno (`v005-vizier.yaml`, 1 worker, run root `<commit>-vizier`) |
| 2026-10-31 | Rekordy A8 (`ec1ba9cb`, `e6734ccd`, `7b7abd84`) przeniesione z `results/runs/` do `results/a8/` (wariant a) — inaczej W-BM7 blokuje bramkę `checks`; na serwerze ze snapshotu powtórzyć |
| 2026-10-31 | P5 = a: retrening punktu kolanowego na GPU wynajętym w chmurze (koszt i zakres ramion do oszacowania przed prerejestracją) |

## Otwarte decyzje autora (PROPOZYCJE Claude'a)

| # | Sprawa | Warianty | Rekomendacja Claude'a |
|---|---|---|---|
| 2026-10-31 | Koszt do celu (prerejestracja §5.2) dla IGD+: **a** — IGD+ ≤ najlepsza / q (q = 0.9, 0.95, 0.99) | zdecydowane | a |
| 2026-10-31 | Luki generalizacji (§5.9): **a** — średni błąd testowy członków frontu końcowego i średnia różnica test − walidacja | zdecydowane | a |
| 2026-11-16 | K8, jakość decyzji surogatu (§5.4): rekordy v005 nie mają decyzji surogatu | zdecydowane | a |
| 2026-11-16 | B2: zdanie planu „NB201 słabo rozróżnia metody; FLOPs prawie jednokryterialne” dotyczy v004 (f2 = FLOPs); w v005 (f2 = energia) mediany IGD+ przy b = 350 od 0.0096 do 0.0375, kolejność stabilna (Spearman 0.95 między b = 200 i 350) | zdecydowane (a, zmienione w `v005-plan.md` B2) | a |
| 2026-11-16 | B5: testy hipotez — przy 0–8 krokach mieszania na run (JAHS) zmiany sposobu decyzji surogatu nie mogą się ujawnić | zdecydowane (a) — wykonane jako E1 (prerejestracja §7a, + random search jako odniesienie, 600 runów na serwerze); wynik: `notes/archive/v005/analysis-v005/reports/04-e1-surrogate-budget-1000.md` | a |
| 2026-11-16 | P3Net i kanoniczne P3 kończą identycznie tylko w 5.8 % runów, choć przy b = 50 P3Net nie wykonuje kroku mieszania — różnica spoza decyzji surogatu | zdecydowane (a) — wyjaśnione: warianty z surogatem pobierają `rng.getrandbits(64)` w konstruktorze, więc idą innym strumieniem losowym; bez kroków mieszania P3Net = kanoniczne P3 (sprawdzone 6/6 runów); `notes/archive/v005/analysis-v005/reports/03-p3net-vs-canonical-rng.md` | a |

Wybory Claude'a w analizach: brak oczekujących.

## Etap B — interpretacja

- [x] B1–B6 opisane 2026-11-16: `notes/archive/v005/analysis-v005/reports/02-stage-b-interpretation.md` (bez nowego liczenia).
      B2, B5 (E1, raport 04) i różnica P3Net vs kanoniczne P3 (raport 03) zamknięte — decyzje wyżej.

## Etap C — tekst artykułu

- [x] Related Work (nowe metody, cytowania SH-EMOA / MO-BOHB; HW-NAS-Bench, jeśli P1 = a). **Najpierw:** autor
      powtarza przeszukanie literatury w Google Scholar / DBLP (P3 / GOMEA / linkage learning w NAS i NAS+HPO);
      wstępne wyniki z 2026-11-16 w `notes/ga_landscape_2026.md` §16 (do cytowania: ENCAS 2022, dodany do `refs.bib`;
      HPNAS-RL 2026 do sprawdzenia w pełnym tekście).
      Szkic 2026-11-17 (Claude): akapit „Compared methods” (`chapters/related_work/compared_methods.tex`,
      33 cytowania, 7 nowych wpisów w `refs.bib` sprawdzonych na arXiv/JMLR) i skrócony akapit o LLM (`llm.tex`,
      4 zdania). **Pozycjonowanie P3/GOMEA — szkic 2026-11-17, zaakceptowany przez autora 2026-11-17:**
      `chapters/related_work/positioning.tex` (zastępuje v003 „Linkage learning and P3”, „Surrogate-assisted
      linkage learning”, „Closest prior work”; 19 cytowań, wszystkie w `refs.bib`). Źródła: przeszukanie autora
      2026-11-17, `notes/ga_landscape_2026.md` §16a–§16d (Dahi 2026 opisany tylko z suplementu). Dahi i in. 2024 dodany
      (`dahi2024evolutionary`, BibTeX ze Scholara).
      Zdania v003 do zmiany przy przeróbce sekcji (plików v003 nie ruszano): Related Work „Closest prior work” —
      „NSGA-II and NSGANetV2 as baselines” i „to which, to our knowledge, no linkage-learning EA has previously been
      applied” (fałszywe: P3 w NAS u Dahi 2026, GOMEA w NAS od 2021); Introduction l. 20–21 „Whether the combination
      transfers to NAS … is open” (GOMEA w NAS już badane — zawęzić do wielokryterialnego łącznego NAS+HPO);
      Abstract i Introduction „This work”/„The answer is negative”/Contributions opisują wyniki v003 (null vs random
      search, 89.7–92.4 % bootstrap) — do napisania od nowa pod v005.
- [x] Zdania artykułu zgodne z `v005-claims.md` (zatwierdzone przez autora 2026-11-17). Szkic 2026-11-17: zdania o metodach w szkicach etapu C sprawdzone;
      dwa nowe wiersze C-46 (przesunięcie RNG — test poziomu 1 do napisania), C-47 jako PROPOZYCJE w `v005-claims.md`.
- [ ] Limitations z kart (lista w `v005-plan.md`, etap C). Szkic 2026-11-17: `chapters/limitations/main.tex`
      (tekst główny) i `supplement_deviations.tex` (tabela wszystkich odstępstw i założeń z kart, decyzji i §8).
- [x] Experimental setup — zatwierdzony przez autora 2026-11-17; szkic 2026-11-17: `chapters/setup/main.tex` (przestrzenie i cele, tabela
      `tab:v005-spaces`, metryki, ramiona i tory, budżety i seedy, statystyka); nowe wpisy bib `ishibuchi2015igdplus`,
      `romano2006appropriate` (BibTeX ze Scholara); claim C-48 (gate) bez testu — decyzja autora.
- [ ] Analizy §5 i brakujące tabele — szkic 2026-11-17: `scripts/render_v005_supplement.py` →
      `chapters/supplement/_generated_secondary.tex` (§5.2, §5.6a, §5.7, §5.9, §5.10, NB201, Q7, GP) i
      `figures/anytime__primary__budget350.pdf` (§5.1); sekcja `chapters/supplement/secondary.tex`; akapit „Secondary
      analyses” i odwołania w Results; raport `notes/archive/v005/analysis-v005/reports/05-secondary-analyses.md`.
- [ ] Reprodukowalność, podział tekst główny / suplement. Szkic 2026-11-17: `chapters/reproducibility/main.tex`
      (`\anonrepo` = link anonimowy, etap D); podział — przy składaniu.
- [ ] Plik główny v005 — złożony 2026-11-17: `nas_compare_v0.0.5.tex` (preambuła jak v0.0.3 + tabularx, makra
      `\anonrepo`, `\TODO`); Related Work v005 złożony w `chapters/related_work/main.tex`; suplement na razie
      jako dodatek (appendix), osobny plik w etapie D. Odwołania i cytowania sprawdzone skryptem (0 niezdefiniowanych,
      0 brakujących kluczy). **Kompilacja: autor w Overleafie** — czeka na wynik.
- [ ] Results (narracja „badanie empiryczne”, decyzja autora 2026-11-16). Szkic 2026-11-17:
      `chapters/results/main.tex` (Q1–Q7, E1, NB201; `\TODO` = retraining K10) + `_generated_e1.tex`
      (`scripts/analyze_e1_v005.py`).

- [x] Przegląd kart vs kod vs testy (audyt po rozbieżności P3Net-gate) — 2026-11-17, `v005-audit-cards.md` (F1–F10);
      krok 2 (poprawki opisów) wykonany; rundy testów 10, 10b i 11 zakończone 2026-11-17 (C-48–C-52 ✅).
      F1 (przeliczenie gate z kwantylem): decyzja przy planowaniu P3-eLyMPuS z grafem (`v005-plan.md`).

- [ ] Sekcje dotąd z v003 (punkt 1) — szkice v005 2026-11-17: `chapters/{title,abstract,introduction,
      problem_formulation,proposed_optimizer,conclusions}/main.tex`; tytuł = propozycja (decyzja autora); plik główny
      wczytuje już tylko v005. Claimy: nowe C-51 (✅), C-52 (telescoping — test zlecony, runda 11). Czeka na przegląd
      autora i kompilację.

## Etap D — przed wysyłką

- [ ] Podział tekst główny / suplement i limit 8 stron — po eksperymentach z P3-eLyMPuS z wiedzą dziedzinową (decyzja autora 2026-11-17).
- [ ] Anonimizacja, samocytowania w trzeciej osobie, anonimowe repozytorium, `printacmref`.
- [ ] Regeneracja tabel z run rootu v005; zgodność liczb w tekście.

## Po v005

- [ ] eLyMPuS z grafem zależności NAS+HPO (pomysł promotora). Ustalenia 2026-11-16 (warianty, transfer, porównania z
      rekordów v005 bez przeliczania baseline'ów, zasady wiedzy): `v005-plan.md`, „Następna iteracja”.
