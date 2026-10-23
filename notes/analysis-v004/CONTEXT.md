# Wspólny kontekst analizy v004 (dla agentów: przebiegi 1–3)

Repozytorium: `c:\Workspace\Uczelnia\p3net_gecco2027` — artykuł P3Net na GECCO'27 (LaTeX) + kod eksperymentów (Python).
Cel całości: **wyczerpująca analiza** wyników v004 i wierności implementacji metod, jako podstawa późniejszej aktualizacji artykułu.
Na tym etapie nic nie przycinamy pod limit stron — ma być szeroko, ale uporządkowane, z jawnym rozróżnieniem faktu, wnioskowania i spekulacji.
Język raportów: polski (nazwy metod, metryk i terminy techniczne mogą zostać po angielsku).

## Zasady wspólne

- **Nie edytuj** artykułu, notatek, planów ani kodu. Jedyne pliki, które wolno tworzyć/zmieniać w repo, to raporty w
  `notes/analysis-v004/reports/` (nazwa podana w prompcie przebiegu). Skrypty i dane pośrednie trzymaj poza repo (katalog tymczasowy, `$V004_OUT`).
- **Nie uruchamiaj** nowych przebiegów eksperymentów. Analizujesz istniejące dane i kod.
- **Zapisuj raport przyrostowo** — po każdej ukończonej sekcji dopisz ją do pliku raportu. Jeśli kontekst się kończy, raport ma być użyteczny
  w stanie, w jakim jest; na górze utrzymuj listę sekcji: zrobione / częściowo / niezrobione.
- Każda liczba: skąd (etap, pytanie Q, plik) i jak policzona. Każde ustalenie o kodzie: plik i funkcja/linia.
  Czego nie da się ustalić z kodu lub danych — wypisz jako „nieustalone”, nie zgaduj.
- Każdy wniosek oznacz siłą dowodu: **(1)** interwencja/izolacja, **(2)** potwierdzające (seedy 31–60, primary, Q1/Q4/Q7),
  **(3)** eksploracyjne/korelacyjne, **(4)** hipoteza do sprawdzenia — oraz wskaż, czym można go rozstrzygnąć.
- Zmiany kodu i nowe eksperymenty — tylko jako propozycje do decyzji autora.
- Obok efektów statystycznych (Cliff's δ, p) zawsze podawaj **różnicę bezwzględną metryki** i oceniaj znaczenie praktyczne
  (np. różnice median HV w 3.–4. miejscu po przecinku). Liczności „k z 16 komórek” są opisowe i zawsze z kierunkiem.

## Materiały

| Co | Gdzie |
|---|---|
| Artykuł v0.0.3 | `chapters/v003/` (abstract, introduction, related_work, problem_formulation, proposed_optimizer, results/main.tex + `results/_generated_*.tex`, conclusions); odłożony `notes/archive/parked/przewozniczek_isolation.tex` (teza obalona, raport 03 §0); bibliografia `refs.bib` |
| Prerejestracja (WIĄŻĄCA) | `notes/plans/v004-preregistration.md` — Q1–Q7, seedy (§2), metryki i fronty (§3), protokół (§4), analizy drugorzędne (§5), co nie jest porównaniem (§6), odchylenia (§7) |
| Plan v004 | `notes/archive/v004-plan.md` (zarchiwizowany 2026-10-16; aktualny plan: `notes/plans/v005-plan.md`) — etapy S1–S5, ramiona B1–B5, M1–M10, decyzje D1–D6 |
| Checklista audytu | `notes/archive/v004-audit-checklist.md` (zarchiwizowana 2026-10-16; aktualne punkty przeniesione do `notes/plans/v005-plan.md`) — A (kod raportujący, niezrobione), B1–B10 (pytania do rozstrzygnięcia wynikami), C, D |
| Notatki o usprawnieniach | `notes/archive/p3net-improvements.md` — stan 2026-10-07, **sprzed** wyników v004; część faktów nieaktualna |
| Tło implementacyjne | `notes/archive/` (`lympus-nas-adaptation-literature.md`, `lympus-nas-adaptation-validation.md`, `experiments-przewozniczek-plan.md`, `experiments-bartnik-plan.md`, `algorithms_comparison.md`, `design_space_mechanisms.md`), `implementation/experiments/CHANGELOG.md` |
| Publikacje źródłowe (PDF) | `notes/articles/` — P3 (Goldman & Punch), LyMPuS/eLyMPuS (Przewoźniczek et al.), SA-P3 (Dushatskiy et al.), CS-GOMEA, NSGA-Net, NSGANetV2, Local Search (den Ottelander et al.) i in. **Brak** m.in.: Vizier, BoTorch/qNEHVI/qParEGO, Guerrero-Viu et al. (SH-EMOA, MO-BOHB), BANANAS, SMAC3, TPE, MOEA/D, NSGA-III — dla nich ocena opiera się na dokumentacji/kodzie biblioteki i musi być oznaczona jako mniej pewna. *Korekta 2026-10-16:* praca magisterska Niny Bartnik **jest** w repo: `notes/articles/NAS/MO-NAS/Evolutionary optimization of deep neural.pdf` (wcześniej błędnie podana jako brakująca). Zasada: przed oceną wierności zawsze wyszukać źródło w `notes/articles/` |
| Sprawdzenia poprawności | `implementation/experiments/results/checks/` (np. `p3_trap_correctness*.md`, `nsga_sanity_check.md`, `phase2c_jahs_bridge_memory.log`, logi reprodukcji etapów) |
| Wyniki v0.0.3 (do porównania przed/po) | `implementation/experiments/results/tables/*.md`, `results/nas_bench_201_isolation_result.md` |

## Kod

- Metody P3Net i rodzina P3: `implementation/lib/src/p3net/` (`methods/p3net.py`, `search_engines/p3/` — `canonical_pyramid.py`, `fihc_elympus.py`;
  `surrogates/` — m.in. `elympus.py`).
- Baseline'y i rekonstrukcje: `implementation/experiments/methods/` (`bartnik_p3.py`, `przewozniczek_p3elympus.py`, `nsganetv2.py`, `sh_emoa.py`,
  `multi_fidelity.py`, `bananas_mo.py`, …; `external/` — adaptery: `vizier_mo.py`, `botorch_mo.py`, `smac_parego.py`, `tpe.py`, `mo_bohb.py`,
  `moead.py`, `nsga3.py`).
- Konfiguracje: `implementation/experiments/configs/methods/*.yaml`, `configs/search_spaces/*.yaml`, plany `configs/pipeline/v004.yaml`,
  `configs/pipeline/v004-gp-small.yaml`.
- Benchmarki (substraty): `implementation/experiments/substrates/`; most JAHS: `implementation/experiments/vendor/jahsbench-env/`.
- Harness: `implementation/experiments/scripts/run_experiment.py`, `scripts/run_pipeline.py`.
- Raportowanie z repo: `scripts/generate_report.py`, `scripts/posthoc_metrics.py`, `reporting/`, `stats/significance.py`.
- Prace nad rekonstrukcjami (kod, walidacja, plany): `implementation/experiments-bartnik/`, `implementation/experiments-przewozniczek/`.
- Wersje bibliotek: `implementation/experiments/pyproject.toml` + `uv.lock`, `implementation/lib/pyproject.toml` + `uv.lock`, `implementation/experiments/.venv`.

## Dane v004 (`implementation/experiments/results/runs/`)

- `b4d25cac/` — plan `v004.yaml`, commit b4d25cac, wszystkie etapy kompletne:
  s1 headline (24 ramiona porównawcze, seedy 1–30) · s2 droga projektowa S1, S2, S3, S4′ · s3 S5 + warianty surogatu ·
  s4 obrona decyzji (16 wariantów na S5) · s5 NAS-Bench-201 (tylko architektura; opisowo, prereg §6) · s6 seedy 31–60 (potwierdzające) ·
  s7 multi-fidelity · s8 FCNet (4 zadania) · s9 pomiar czasu sekwencyjny (`timing/raw/`, budżet 350, seed 1).
  ~51.9 tys. plików JSON w `raw/` (~19 GB). `failures.jsonl` — 101 wpisów (zapełniony dysk w s6, punkty powtórzone).
- `gp-small/` — Vizier, BoTorch qNEHVI, qParEGO, tylko budżety 50 i 100, etapy s1/s6/s8 (plan `v004-gp-small.yaml`, commit 1bba34af;
  względem b4d25cac różni się tylko plik planu, kod metod identyczny). 2160 przebiegów. Worker przeciekał pamięć: OOM i restart usługi systemd
  co ~1.5–2 h (22+ razy), restarty **nie** są zapisane w `failures.jsonl` (którego tu brak).
- `archiwum/` — przerwane przebiegi, pomijać.
- Plik przebiegu: `method, search_space, budget, seed, evaluations_used, history[{genotype, objectives}], diagnostics{...}`.
  Etap nie jest zapisany — wynika z metody i zakresu seedów.
- Fronty oracle (NAS-HPO-II, FCNet): `implementation/experiments/results/reference_fronts/oracle__*.json`.
  Fronty JAHS/NB201 trzeba zamrozić wg prereg §3 (pliki `reference_fronts/jahs_bench_201*.json` i `nas_hpo_bench_ii.json` w repo są z v0.0.3 —
  nie używać do v004).

## Skrypty eksploracyjne

`notes/analysis-v004/` — przeczytaj `README.md`. Uruchomienie: `V004_OUT=<katalog poza repo> sh notes/analysis-v004/run_all.sh`
(ekstrakcja ~1–2 min; wyjścia: `per_run.csv`, `comparisons.csv`, `summary.csv`, `timing.csv`, `diag.pkl`, `summaries.txt`).
To kod z jednej sesji, **nieprzejrzany**: zanim użyjesz liczb, sprawdź go (np. HV 2D i IGD+ względem `implementation/lib/src/p3net/metrics/`
na próbce przebiegów; konwencje znaku δ; definicje rodzin testów).

## Znane odchylenia od prerejestracji (do potwierdzenia i uzupełnienia; prereg §7 jest pusta)

1. Metody GP (Vizier, qNEHVI, qParEGO) tylko przy budżetach 50 i 100, w osobnym run roocie (`v004-gp-small.yaml` opisuje powód: pamięć i czas).
   Skutek: rodzina Holma w Q1 przy b=200/350 jest mniejsza; rankingi z GP tylko dla b=50/100.
2. Kod raportujący w repo (`stats/significance.py`) używa paired Wilcoxon; prereg §4 wymaga dwustronnego Mann–Whitney U (checklista A1).
3. Zamrożony front JAHS/NB201 w skryptach eksploracyjnych zawiera punkty metod GP z gp-small (zgodnie z §3, bo to ramiona s1 — ale do odnotowania).
4. Retrening punktu kolanowego (prereg §5, faza 4b) — sprawdzić, czy wykonano; jeśli nie, to brak względem prerejestracji.

## Wstępne ustalenia z wcześniejszej sesji

Plik `notes/archive/analysis-v004/INITIAL_FINDINGS.md`. **Otwórz go dopiero po własnych obliczeniach** danej sekcji i porównaj; rozbieżności wypisz.
