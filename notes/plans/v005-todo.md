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
| 5a | Skrypty analiz v005 (prerejestracja §7, K1–K7, K9) napisane i sprawdzone na rekordach A8 przed zamrożeniem (P8) | bez skryptów obietnice prerejestracji nie są wykonalne (błąd v004, Z9) | Claude | szacunek 1–2 dni | nie (laptop, rekordy A8) | **zrobione 2026-10-31** (`analysis_v005/`, `scripts/analyze_v005.py`, 9 testów; rekordy runów mają `evaluation_metrics`) |
| 5 | Prerejestracja v005 | zamrożenie metod, metryk, analiz przed przebiegiem | Claude pisze, autor zatwierdza | ~1 dzień pisania | nie | **treść zatwierdzona 2026-10-31** (`v005-preregistration.md`); skrypty analiz → poz. 5a |
| 6 | Przebieg v005 z Vizierem, jedna maszyna (P2 b): najpierw `v005.yaml` (6 workerów), potem `v005-vizier.yaml` (1 worker) z tego samego commita (zaczyna się automatyczną bramką `checks`: testy, determinizm, karty — minuty) | **jedyne wyniki do artykułu** | autor uruchamia | ~10 dni (prognoza z A8, `v005-a8-analysis.md`) | **tak, serwer** | **zrobione 2026-11-16** (start 2026-11-01; run rooty `c674c91e`, `c674c91e-vizier`). 2026-11-03: wszystkie 2 160 punktów głównej części na JAHS CIFAR-10 nieudane — OOM zabijał most JAHS (13–15 GB) przy 6 workerach (`dmesg` 2026-11-02 12:24–12:28); dane JAHS na serwerze kompletne. Decyzja autora 2026-11-03 (a): przebieg bez zmian; po v005 i Vizierze `run_pipeline.sh --plan configs/pipeline/v005.yaml --workers 2 --retry-failed` (ten sam commit i run root; szacunek ~2 dni) |
| 7 | Kontrola po przebiegu i analizy z prerejestracji | wyniki do etapu B | Claude | dni pracy | nie (odczyt wyników) | **częściowo 2026-11-16**: przebieg zakończony (26 400 + 540 rekordów, 0 brakujących, 0 duplikatów), posthoc JAHS seedy 62–71, `analyze_v005.py` → `analysis/`; przegląd w `notes/analysis-v005/reports/01-v005-results-overview.md`; odchylenia w prerejestracji §8; tabele `chapters/v005/results/_generated_*.tex` (`scripts/render_v005_tex.py`). K8 (§5.4) niewykonalne — decyzja a (odchylenie). **Otwarte: K10 retrening** — skrypty gotowe i sprawdzone (`notes/plans/v005-retraining-runbook.md`), 40 treningów na GPU laptopa, ≈ 13–16 h; uruchamia autor |

Czekamy (nie blokuje 1–5): **Nina Bartnik** — N-0–N-4 i bramka MO-DSA. Brak odpowiedzi przed prerejestracją →
założenia Z-B zostają i idą do artykułu. **2026-10-31: autor nie spodziewa się odpowiedzi** → obowiązują założenia Z-B; Limitations (etap C) je opisuje.

## Zrobione (etap A)

- Protokół weryfikacji, karty źródeł, rejestr decyzji (`v005-decisions.md`), tabela „zdanie ↔ test” (`v005-claims.md`, 43/45).
- Poziomy 1–4 (testy, zgodność z kodem autorów, integracja, kontrole w trakcie przebiegu).
- A9: poprawki kodu raportującego A1–A6; równoważność, S4′ vs S5, dekompozycja HV, duplikaty (`notes/analysis-v004/reports/04-a9-equivalence-hv.md`).
- A8: pomiar czasu i pamięci metod na serwerze (2026-10-24…29, ~5.5 dnia serwera; **wyniki nie wchodzą do artykułu**),
  analiza w `v005-a8-analysis.md`.
- Odpowiedź M. Przewoźniczka (2026-10-21).

## Decyzje autora zapisane w tej rundzie

| Data | Decyzja |
|---|---|
| 2026-10-26 | A8: Viziera dokończyć (pomiar); po OOM reszta planem `v005-resources-vizier-rest.yaml` |
| 2026-10-29 | Pomiarów energii na laptopie autor nie jest w stanie zrobić. Pilotaż 5 (1 000 wejść) niezaliczony (`benchmarks.md` BM-2). |
| 2026-10-29 | HW-NAS-Bench jako f2 NB201 „brzmi najrozsądniej” — kierunek; formalna zmiana karty = P1 |
| 2026-10-30 | Posthoc JAHS na danych v004 przerwany (2 776 z 28 080 plików); brak = odchylenie v004 |
| 2026-11-16 | Retrening (§5.8, K10) na laptopie autora (RTX 3050 Ti Laptop, 4 GB), nie na serwerze GPU Hetzner — zastępuje decyzję z 2026-10-31 „GPU do retreningu (R9)” |
| 2026-11-16 | Retrening (§5.8, K10): punkt kolanowy z największego budżetu ramienia — b = 350, ramiona GP (Vizier, qNEHVI, qParEGO) b = 100; NB201 22 i NAS-HPO-II 27 punktów, ≈ 23 GPU-h (16–34) wg czasów z tablic. Doprecyzowanie prerejestracji (budżet nie był podany) |
| 2026-11-16 | K8 (§5.4) = a: odchylenie od prerejestracji — jakość decyzji surogatu niewykonana, bo metody `p3net/v005/` nie logują decyzji (`decision_log`), a `posthoc/` ma `decisions = None`; zastępczo opisać `surrogate_share` i `mixing_steps` (`budget_use.csv`). Posthoc tabelaryczny dokończony mimo to (laptop) |
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
| 2026-10-31 | GPU do retreningu (R9): Hetzner, serwer GPU dedykowany; ofertę i cenę sprawdza i decyduje autor przed uruchomieniem retreningu — **zastąpione 2026-11-16: laptop autora** |
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
| 2026-11-16 | B5: testy hipotez — przy 0–8 krokach mieszania na run (JAHS) zmiany sposobu decyzji surogatu nie mogą się ujawnić | **a** — tylko test większego budżetu (P3Net, gate, nolink, kanoniczne P3 × 4 przestrzenie główne × b = 1 000 × 30 nowych seedów, eksploracyjnie), najpierw pilotaż 10 runów do pomiaru czasu (szacunek całości 15–30 CPU-h); **b** — B5 pominąć, opisać jako ograniczenie | a (pilotaż: minuty) |
| 2026-11-16 | P3Net i kanoniczne P3 kończą identycznie tylko w 5.8 % runów, choć przy b = 50 P3Net nie wykonuje kroku mieszania — różnica spoza decyzji surogatu | zdecydowane (a) — wyjaśnione: warianty z surogatem pobierają `rng.getrandbits(64)` w konstruktorze, więc idą innym strumieniem losowym; bez kroków mieszania P3Net = kanoniczne P3 (sprawdzone 6/6 runów); `notes/analysis-v005/reports/03-p3net-vs-canonical-rng.md` | a |

Wybory Claude'a w analizach: brak oczekujących.

## Etap B — interpretacja

- [x] B1–B6 opisane 2026-11-16: `notes/analysis-v005/reports/02-stage-b-interpretation.md` (bez nowego liczenia).
      Otwarte: B2 (zmiana zdania), B5 (pilotaż), różnica P3Net vs kanoniczne P3 — PROPOZYCJE wyżej.

## Etap C — tekst artykułu

- [ ] Related Work (nowe metody, cytowania SH-EMOA / MO-BOHB; HW-NAS-Bench, jeśli P1 = a).
- [ ] Zdania artykułu zgodne z `v005-claims.md`.
- [ ] Limitations z kart (lista w `v005-plan.md`, etap C).
- [ ] Reprodukowalność, podział tekst główny / suplement.

## Etap D — przed wysyłką

- [ ] Anonimizacja, samocytowania w trzeciej osobie, anonimowe repozytorium, `printacmref`.
- [ ] Regeneracja tabel z run rootu v005; zgodność liczb w tekście.

## Po v005

- [ ] eLyMPuS z grafem zależności NAS+HPO (pomysł promotora).
