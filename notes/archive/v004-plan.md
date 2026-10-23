# P3Net v0.0.4 — plan prac

Stan na: 2026-09-14. Dokument roboczy: gdzie jesteśmy i co zostało.

## Cel

1. **Droga projektowa**: od pomysłu „NSGANetV2 z P3 zamiast NSGA-II” przez modyfikacje uzasadnione
   pomiarami do formy finalnej (P3Net z `cascade`, etap S5).
2. **Szerokie porównanie** z metodami joint HPO+NAS spoza niszy P3/GOMEA.
3. **Potwierdzenie** na nowych seedach (31–60) i na drugim benchmarku z innej dziedziny i rodziny
   architektur (FCNet).
4. **Wymiar praktyczny**: jakość w funkcji rzeczywistego kosztu (trening + narzut algorytmu).
5. **Miary jakości surogatów i sieci**: macierze pomyłek decyzji surogatów, zbiór testowy, ponowny
   trening frontu Pareto.

## Reguła zakresu porównania

Porównujemy wyłącznie metody, które optymalizują **cały joint genotyp** (architektura +
hiperparametry) sygnałem zdefiniowanym dla całego genotypu. Liczy się to, co metoda potrafi na zadanej
przestrzeni, a nie to, do czego ją pierwotnie zaprojektowano (NSGA-Net, BANANAS czy TPE traktują
genotyp jako ogólną przestrzeń kategorialną i spełniają regułę). Metody czysto HPO lub czysto NAS
wymagałyby osobnego wymiaru porównania i są poza zakresem. W tekście: ogólny akapit z uzasadnieniem;
zero-cost proxies jako przykład (nie widzą hiperparametrów, bo liczone są na nietrenowanej sieci).

## Ustalenia (decyzje podjęte)

| Temat | Decyzja |
|---|---|
| Rama artykułu | Design Evolution S1→S5 + porównanie + potwierdzenie; wyniki raportowane w całości |
| Kolejność S3 | RidgeCV przed naprawą piramidy |
| Ślepa uliczka S4′ | odtworzona i uruchamiana |
| Kryteria potwierdzenia | brak progów sukcesu; prerejestrowany tylko plan analizy |
| Potwierdzenie | wszystkie ramiona, seedy 31–60 |
| `bartnik_p3` | przeniesiony do `experiments/` |
| Obrona decyzji projektowych | pełna runda wariantów + sweep κ × próg na silniku S5 |
| Przebieg od zera | jeden skrypt, etapy, wznawianie po crashu, manifest z commitem |
| Nowe metody bazowe | B1–B5 (zrobione) + M1–M10 (niżej) |
| P3Net-eLyMPuS / P3Net-Bartnik | silnik S5, ten sam random forest; różnią się tylko mechanizmem porównania |
| `przewozniczek_p3elympus` | pełna siatka + ramię kontrolne B4 |
| Metody z dzieleniem wag (DARTS itd.) | tylko odniesienie literaturowe |
| Wymiar praktyczny | koszt symulowany treningu + narzut algorytmu + manifest sprzętu |
| Miary 1.1 | wszystkie cztery + ponowny trening frontu Pareto na GPU |
| Czas obliczeń | bez cięć; kilka tygodni akceptowalne; GPU używane bez wcześniejszego testu |
| D1 | tor wielowiernościowy: koszt odpowiadający 50/100/200/350 pełnym ewaluacjom |
| D2 | zero-cost proxies wykluczone (reguła zakresu) |
| D3 | drugi benchmark: **FCNet / NAS-HPO-Bench** (Klein & Hutter, 2019), wszystkie 4 zbiory, wszystkie ramiona, 4 budżety |
| D4 | ponowny trening: wszystkie metody × 4 główne przestrzenie, 1 konfiguracja (punkt kolanowy z przebiegu medianowego), 1 seed (~116 treningów) |
| D5 | obliczenia równolegle z zapisem czasu CPU i zegarowego + osobny sekwencyjny etap pomiaru czasu na końcu |
| M7/M8 | trzy ramiona: `p3net_bartnik`, `p3net_bartnik_fihc` (kontrola kroku doprecyzowania), `p3net_elympus` |
| D6 | NAS-Bench-201 (tylko architektura): **wyłącznie diagnostyka P3Net** i odtworzenie Bartnik, z adnotacją i uzasadnieniem w tekście; nie jest porównaniem metod |

## Gdzie jesteśmy

| Faza | Zawartość | Stan |
|---|---|---|
| 0 | Poprawność kodu | ✅ zrobione |
| 1 | Etapy drogi projektowej S1–S4′ | ✅ zrobione |
| 2 | 7 metod bazowych (B1–B5) | ✅ zrobione |
| 2b | Dodatkowe metody M1–M10 | ✅ zrobione |
| 2c | Infrastruktura pomiarów + tor wielowiernościowy + GPU + równoległość | ✅ zrobione |
| 2d | FCNet | ✅ zrobione |
| 3 | Domknięcie konfiguracji, prerejestracja, commit | ✅ zrobione (commit: Ty) |
| 4 | Przebieg od zera (Ty) | ⏳ (próba 1 przerwana, poprawki wprowadzone) |
| 4b | Ponowny trening frontu Pareto na GPU (Ty) | ⏳ |
| 5 | Raporty | ⏳ |
| 6 | Tekst artykułu | ⏳ |

### Faza 0 — poprawność (zrobione)

- Błąd duplikatów w `cascade` naprawiony (NAS-HPO-Bench-II, budżet 350, 30 seedów: 11 → 0); test
  regresyjny nie przechodzi bez poprawki.
- Drzewo powiązań na genotypie k-arnym: znana odpowiedź odzyskana w 10/10 seedów.
- Kanoniczny P3 na pułapkach k-arnych: optimum w 10/10 (kryterium ≥ 8/10); random search i
  hill-climbing 0/10. P3Net przy budżecie 2000 gorszy od random search (surogat addytywny vs
  krajobraz nieaddytywny) — do Limitations.
- NSGA-Net vs optuna NSGA-II: w granicy 5% (+0.9% / −4.2%).
- Do Limitations: losowy wybór rodziców w NSGA-Net; odstępstwa kanonicznego P3 (korzeń w mieszaniu,
  brak kontroli dawcy); koszt `cascade`.
- Raporty: `implementation/experiments/results/checks/`.

### Faza 1 — droga projektowa (zrobione)

- Flagi w P3Net: `level_init`, `stall_criterion`, `bootstrap_threshold`; `surrogate_model` w
  `build_method`.
- S1 i S2 odtwarzają archiwa bit w bit (24/24 i 24/24); S4′ odtwarza udokumentowany objaw (2^96).
- Logi: `results/checks/stage_S1_reproduces_archive.log`, `stage_S2_reproduces_archive.log`.

### Faza 2 — metody bazowe (zrobione)

- MO-LS (Pareto Local Search), regularized evolution (MO, turniej po randze), NSGA-III (optuna),
  MOEA/D (pymoo), qNEHVI i qParEGO (BoTorch, GP kategorialny), SMAC3 z ParEGO.
- Testy: kontrakt harnessu, determinizm, zależność od seeda; regresja SMAC3 (NaN przy nieskończonym
  koszcie crash) naprawiona.
- Czas jednego przebiegu (NAS-HPO-Bench-II, budżet 350, CPU): RE 0.2 s, NSGA-III 0.3 s, MO-LS 2.9 s,
  MOEA/D 5.4 s, SMAC3 4 min, qParEGO 18 min, **qNEHVI 58 min**
  (`results/checks/new_baselines_timing_nashpo_b350.json`).

## Co zostało

### Faza 2b — dodatkowe metody (zrobione)

| # | Ramię | Konfiguracja | Implementacja |
|---|---|---|---|
| M1 | REINFORCE (Zoph & Le) | `reinforce_mo` | `methods/reinforce_mo.py`: faktoryzowana polityka softmax na całym genotypie, nagroda = losowa skalaryzacja Chebysheva |
| M2 | BANANAS | `bananas_mo` | `methods/bananas_mo.py`: zespół 5 MLP na one-hot całego genotypu, niezależne próbkowanie Thompsona, skalaryzacja Chebysheva |
| M3 | OSS Vizier | `oss_vizier` | `methods/external/vizier_mo.py`: `VizierGPUCBPEBandit` (algorytm „DEFAULT”), natywne wiele celów, float64 jak w serwisie; JAX przypięty do 0.4.38 (equinox) |
| M4 | Hyperband | `hyperband_mo` | `methods/multi_fidelity.py` |
| M5 | ASHA | `asha_mo` | jw., jeden worker |
| M6 | BOHB z fidelity | `bohb_mo` | jw., próbnik = prawdziwy generator BOHB z hpbandster; promocja jak w M4 |
| M7 | P3Net-Bartnik | `p3net_bartnik` (+ kontrola `p3net_bartnik_fihc`) | S5 + absolutny random forest |
| M8 | P3Net-eLyMPuS | `p3net_elympus` | S5 + ten sam random forest + FIHC-eLyMPuS |
| M9 | `przewozniczek_p3elympus` | `przewozniczek_p3elympus` | przeniesiony; odtwarza surowe wyniki forka (2/2) |
| M10 | kontrola B4 | `canonical_p3_scalar_fihc` | kanoniczny P3 + FIHC po samym f1 |

- `bartnik_p3` przeniesiony, odtwarza surowe wyniki (2/2); domyślny P3Net bez zmian
  (`results/checks/phase2b_moved_arms_reproduce.log`).
- **Tor wielowiernościowy** (`MultiFidelityRunner`): koszt zapytania = dodatkowe epoki / pełna długość
  treningu (wznowienie z checkpointu — niższe wierności to zapisy pośrednie tego samego treningu);
  budżet w ekwiwalentach pełnej ewaluacji; wynik = konfiguracje ocenione przy pełnej długości.
  η = 3; szczeble JAHS-Bench-201: 2, 7, 22, 67, 200 epok; NAS-HPO-Bench-II: 1, 4, 12 (`iepoch` z tabeli).
  Promocja wielokryterialna: ranga niezdominowania + crowding distance (jak MO-ASHA). Zapis:
  `diagnostics.cost_used`, `diagnostics.fidelity_queries`.
- Substraty: `max_epochs()`, `objectives_at_epochs()`; ścieżka pełnej wierności bez zmian.
- Czasy (NAS-HPO-Bench-II, budżet 350, CPU): Hyperband 2.7 s, ASHA 4.5 s, BOHB 15.6 s, REINFORCE 2.7 s,
  BANANAS 170 s, **OSS Vizier 74 min** (`results/checks/phase2b_timing_nashpo_b350.json`).
- Do sprawdzenia w 2c: zapytania JAHS-Bench-201 przy niższych epokach na prawdziwym moście.

### Faza 2c — infrastruktura pomiarów (zrobione)

- **Tor wielowiernościowy**: gotowy w 2b. JAHS-Bench-201 przy niższych epokach sprawdzony na prawdziwym
  moście: wartość po 7 epokach = punkt 7 pełnej trajektorii (ten sam trening).
- **Wymiar praktyczny** (`measurement/resources.py`, `diagnostics.resources` każdego przebiegu):
  czas zegarowy i CPU, czas zapytań do benchmarku i narzut optymalizatora (różnica), czas liczenia f2
  kandydatów, CPU i szczytowa pamięć mostu JAHS (całe drzewo procesów), szczytowa RAM procesu, szczytowa
  pamięć GPU, urządzenie. **Koszt symulowany treningu** (`measurement/training_cost.py`): suma czasów
  treningu z benchmarku (JAHS `runtime`, NAS-HPO-Bench-II `total_trainval_time`, NB201 `train-all-time`);
  w torze wielowiernościowym tylko dodatkowe epoki.
  Krzywe jakość–koszt, koszt do 90/95/99% jakości, $ i energia — w raportach (faza 5), dane są zapisane.
- **Miary 1.1**:
  - log decyzji surogatów (`p3net.harness.decision_log`): próbka rezerwuarowa ≤ 500 decyzji na przebieg,
    osobny RNG — przebiegi bit w bit bez zmian (`results/checks/phase2c_instrumentation_unchanged.log`).
    Źródła: P3Net (mieszanie; krok doprecyzowania FIHC/eLyMPuS), P3+abs. (mieszanie), `bartnik_p3`
    i `przewozniczek_p3elympus` (bramka; hill-climber), NSGANetV2 (wybór przez predyktor);
  - `scripts/posthoc_metrics.py`: po przebiegu, poza budżetem — dokładności train/valid/test i czas
    treningu każdej ocenionej konfiguracji, prawdziwe f1 dla decyzji; wznawialny;
  - `measurement/decisions.py`: TP/FP/TN/FN, precision, recall, F1, FPR, FNR, MCC, balanced accuracy,
    Spearman, Kendall τ, kalibracja, regret. Front testowy i luki — w raportach.
  - NAS-Bench-201 (`cifar10`) nie ma walidacji; f1 = błąd testowy (odtworzenie Bartnik).
- **GPU**: PyTorch 2.14.0+cu126. BoTorch na CUDA (`device: auto`), float64, deterministyczne algorytmy,
  ocena puli w porcjach; ten sam seed daje identyczną historię. Wyniki CPU i GPU nie muszą być równe —
  urządzenie zapisane w przebiegu. OSS Vizier (JAX) na Windows tylko CPU.
- **Równoległość (D5)** (`scripts/run_pipeline.py`, `file_locks.py`): workery z blokadą per przebieg
  (O_EXCL, blokady martwych procesów łamane), sloty zasobów (`gpu`: 1 — BoTorch; `heavy_gp`: 2 — Vizier),
  stała liczba wątków na przebieg (2) niezależnie od liczby workerów, restart padniętego workera,
  `logs/worker-<i>.log`. Test end-to-end: 2 workery dają historie identyczne z przebiegiem sekwencyjnym.
- **Pamięć JAHS**: most ładuje modele z **17,5 GB** szczytu, potem 1,9 GB → jedna inicjalizacja naraz
  (blokada), domyślnie **3 workery** (`results/checks/phase2c_jahs_bridge_memory.log`).
  Stderr mostu do pliku tymczasowego (pełny potok mógłby zawiesić wielotygodniowy przebieg).
- **Etap pomiaru czasu** (`kind: timing`, `s9_timing`): po wszystkich siatkach, sekwencyjnie, każdy punkt
  w świeżym procesie → `timing/raw/`. Uwaga: w JAHS pierwsze zapytanie zawiera ~224 s ładowania mostu
  (liczone w `benchmark_seconds`, nie w narzucie optymalizatora).
- **Manifest** (`measurement/hardware.py` → `sessions.jsonl` przy każdym uruchomieniu): CPU, rdzenie, RAM,
  GPU (sterownik, pamięć, temperatura, moc), PyTorch/CUDA, plan zasilania, bateria/zasilacz, obciążenie
  CPU na starcie, wersje bibliotek. Temperatura CPU niedostępna bez uprawnień administratora.
  Maszyna: Dell XPS 15 9510, i7-11800H (8C/16T), 31.7 GB RAM, RTX 3050 Ti Laptop 4 GB (596.08), Windows 11 Pro.
- Wrapper: `run_pipeline.ps1 -Workers N`.

### Faza 2d — FCNet / NAS-HPO-Bench (zrobione)

- **Dane**: oryginalne archiwum (ml4aad.org) zwraca 404. Źródło: publiczne repozytorium Syne Tune na
  Hugging Face (`synetune/blackbox-repository/fcnet`), tabela skonwertowana z oryginalnych HDF5
  opublikowanym skryptem; pobieranie z weryfikacją SHA-256: `scripts/download_fcnet.py`.
  Sprawdzone na pobranych plikach: hashe, kształt (4 zadania × 62 208 × 4 seedy × 100 epok × 5 metryk),
  brak NaN, zgodność wierszy — n_params każdej konfiguracji pasuje do wzoru sieci dwuwarstwowej z jedną
  liczbą cech na zadanie (protein 9, naval 15, parkinsons 20, slice 380).
- **Przestrzeń** (`search_spaces/fcnet_genotype.py`): 9 wymiarów kategorialnych — architektura (liczba
  neuronów, aktywacja, dropout w 2 warstwach) i hiperparametry (init_lr, lr_schedule, batch_size);
  62 208 konfiguracji, wszystkie poprawne.
- **Cele** (`substrates/fcnet.py`): f1 = MSE walidacyjne po 100 epokach, f2 = czas treningu (s) — jak f2
  w NAS-HPO-Bench-II; oba jako średnia z 4 seedów (benchmark deterministyczny).
  Wierności 1–100 epok (szczeble η=3: 1, 4, 11, 33, 100); czas do epoki e = runtime·e/100 (interpolacja
  liniowa jak w kodzie FCNet i w Syne Tune). Metryki post-hoc: train/valid/test MSE, n_params.
- **Konfiguracje**: `fcnet_protein_structure`, `fcnet_naval_propulsion`,
  `fcnet_parkinsons_telemonitoring`, `fcnet_slice_localization`.
- **Fronty oracle** (dokładne, IGD+): 21 / 24 / 15 / 28 punktów; zgodne z niezależnym brute force.
- Test dymny wszystkich ramion na FCNet: `results/checks/phase2d_fcnet_smoke.log`.
- Do fazy 3: etap FCNet w `configs/pipeline/v004.yaml`. Do fazy 5: osobna tabela FCNet (nie w
  `PRIMARY_SEARCH_SPACES`). Do Limitations: małe MLP, regresja tabelaryczna, stała topologia 2 warstw,
  dane z konwersji zewnętrznej (oryginał niedostępny), czas treningu interpolowany liniowo.

### Faza 3 — domknięcie konfiguracji (zrobione, commit po Twojej stronie)

- **P3+abs. na silniku S5** (`p3_absolute_cascade`): nowy `surrogate_kind: absolute_linear` w P3Net —
  absolutny regresor RidgeCV na one-hot genotypu (ten sam model co surogat względny S5), więc ablacja
  różni się od S5 tylko „względny i linkage-aware” vs „absolutny”. Zastępuje uruchamianie starego
  `p3_absolute` (stały silnik, OLS) — nie ma on trybu `cascade`, a OLS odpadł w S3.
- **5 wariantów na S5**: `p3net_cascade_{inherited_cost, f1_truncation, grow_on_stall, transient_donors,
  threshold_permissive}`.
- **Sweep κ × próg (11 komórek)** wg `configs/experiment/kappa_threshold_sweep.yaml`: κ ∈ {1, ⌈log₂n⌉,
  2⌈log₂n⌉, bez limitu}, próg ∈ {0, ε, 2ε}, ε = 0,01. Symboliczne κ (`log2n`, `2log2n`, `unbounded`)
  rozwiązywane per przestrzeń w `run_experiment.resolve_kappa` (JAHS 4, NAS-HPO-II 3, FCNet 4);
  „bez limitu” = 1 000 000 jak we wcześniejszym sweepie.
- **`configs/pipeline/v004.yaml`**: grupy metod (kotwice YAML, spłaszczane w `stage_methods`):
  `comparison` (24 ramiona: v0.0.3, B1–B5, M1–M3, `bartnik_p3`, M9, M10), `final` (S5, P3+abs.,
  M7, kontrola, M8), `multi_fidelity` (Hyperband, ASHA, BOHB). Etapy:

  | Etap | Zawartość | Punkty |
  |---|---|---|
  | s1_headline | `comparison` × 4 przestrzenie × 4 budżety × 30 seedów | 11 520 |
  | s2_design_evolution | S1, S2, S3, S4′ | 1 920 |
  | s3_final | `final` | 2 400 |
  | s4_design_defense | 5 wariantów + 11 komórek sweepu | 7 680 |
  | s5_nas_bench_201 | D6: S4, S5, M7, M8, `bartnik_p3`, M9, M10, MO-LS, RS; budżety 100, 350 | 540 |
  | s6_heldout_seeds | `comparison` + `final` + `multi_fidelity`, seedy 31–60 | 15 360 |
  | s7_multi_fidelity | `multi_fidelity` | 1 440 |
  | s8_fcnet | `comparison` + `final` + `multi_fidelity` × 4 zadania FCNet | 15 360 |
  | s9_timing | wszystkie ramiona porównania, budżet 350, seed 1, sekwencyjnie | 128 |
  | **razem** | | **56 348** |

  Preflight bez braków; test planu sprawdza m.in., że żaden punkt nie należy do dwóch etapów.
- **Prerejestracja**: `notes/plans/v004-preregistration.md` (pytania Q1–Q7, seedy 1–30 eksploracyjne,
  31–60 potwierdzające, metryki, zamrożone fronty, protokół statystyczny, analizy opisowe).
  Zmiana protokołu względem v0.0.3: **test Manna–Whitneya zamiast sparowanego Wilcoxona** — przebiegi
  różnych ramion z tym samym seedem nie są parami; kod `stats/significance.py` do zmiany w fazie 5.
- Silnik bez zmian bit w bit: `results/checks/phase3_engine_unchanged.log`.
- Testy: biblioteka 203, eksperymenty 339 (+2 pominięte).
- **Commit (Ty)**: pipeline odmawia startu na niezacommitowanym kodzie.

### Faza 4 — przebieg od zera (Ty)

**Próba 1 (2026-09-15/16, lokalnie, Windows) przerwana i skasowana.** 2421 z 56 348 punktów w
30 godzin, 578 awarii, 158 punktów porzuconych. Przyczyny i poprawki:

| Problem | Poprawka |
|---|---|
| BoTorch na GPU 4 GB: 509 × `CUDA out of memory` przy budżetach 200 i 350 | `device: cpu` domyślnie (GPU tylko jawnie); na CPU ok. 14 min na przebieg |
| OSS Vizier trzyma 13 GB na przebieg, dwa naraz + mosty JAHS wyczerpały 31,7 GB RAM (padające workery, `bad allocation` w moście, `WinError 1455`) | slot `heavy_gp` z pojemnością 1; domyślnie 2 workery zamiast 3 |
| Worker porzucany po 5 restartach (w2 przepadł na 5 godzin przed końcem) | limit restartów 20 |
| Brak jakiegokolwiek sygnału postępu w terminalu przez wiele godzin | linia `STATUS` co 10 minut (`--status-every`) |

Dodatkowo, pod kątem uruchomienia w chmurze (`notes/plans/v004-cloud-run.md`):

- `--shard i/N` — rozłączny podział planu na maszyny, bez koordynacji; `--unlock-after H` łamie
  blokady po awarii na innym hoście;
- `scripts/run_pipeline.sh` i `scripts/bootstrap_env.sh` (Linux), ścieżka interpretera mostu JAHS
  zależna od systemu, nazwa CPU i governor na Linuksie, model maszyny wirtualnej w manifeście;
- PyTorch: wariant CUDA na Windows, CPU na Linuksie (oszczędza ok. 3 GB na maszynę);
- `scripts/download_data.py` (FCNet + surogaty JAHS) i `scripts/check_data.py` (po jednym
  prawdziwym zapytaniu do każdego benchmarku).

Szacunek z pomiarów: **ok. 2900 godzin pracy jednego workera**, czyli ok. 15 dni na maszynie
16 vCPU / 64 GB (8 workerów) albo ok. 4 dni na czterech takich maszynach.

| Etap | Zawartość | Przebiegi (szac.) |
|---|---|---|
| 0 | środowisko, testy, determinizm, pomiar pamięci procesów | — |
| 1 | tabela główna: ~25 ramion × 4 przestrzenie × 4 budżety × 30 seedów | ~12 000 |
| 2 | droga projektowa S1, S2, S3, S4′ | 1 920 |
| 3 | S5 + P3+abs. z `cascade` | 960 |
| 4 | obrona decyzji na S5 (5 wariantów + sweep) | 7 680 |
| 5 | tor wielowiernościowy (Hyperband, ASHA, BOHB) | 1 440 |
| 6 | FCNet: wszystkie ramiona × 4 zbiory × 4 budżety × 30 seedów | ~12 000 |
| 7 | NAS-Bench-201, diagnostyka P3Net (S4, S5, P3Net-Bartnik, P3Net-eLyMPuS, `bartnik_p3`, `przewozniczek_p3elympus`, B4, MO-LS, random search; 2 budżety) | ~540 |
| 8 | potwierdzenie na seedach 31–60 (~27 ramion, 4 główne przestrzenie) | ~13 000 |
| 9 | sekwencyjny etap pomiaru czasu (D5) | mały |
| 10 | raporty, zamrożone fronty, strażnik liczb | — |

**Razem ok. 50 tys. przebiegów.** Najdroższe: qNEHVI (~17 dni na CPU dla obu siatek głównych, plus
FCNet), qParEGO (~5 dni), ramiona z `cascade` i eLyMPuS, SMAC3. Równoległość (D5) i GPU skracają czas.

### Faza 4b — ponowny trening frontu Pareto (GPU)

- ~116 treningów (D4); dla każdej przestrzeni trzeba znaleźć kod treningowy zgodny z benchmarkiem
  (JAHS-Bench-201 najbardziej niepewny — sprawdzić na początku fazy).
- Wynik: macierz pomyłek, precision, recall, F1 per klasa; zgodność z jakością z benchmarku.

### Fazy 5–6 — raporty i tekst

- Tabele: droga projektowa, tabela główna + heatmapy, potwierdzenie, obrona decyzji, tor
  wielowiernościowy, FCNet, wymiar praktyczny, macierze pomyłek surogatów, ponowny trening,
  diagnostyka NAS-Bench-201.
- Tekst:
  - tabela sprzętu i oprogramowania z manifestu;
  - akapit o regule zakresu (tylko metody joint; dlaczego nie czysto HPO ani czysto NAS; zero-cost
    proxies jako przykład);
  - adnotacja, że NAS-Bench-201 to diagnostyka P3Net i odtworzenie Bartnik, a nie porównanie metod;
  - „Scope of comparison”:
    - porównane (z wersjami bibliotek);
    - odniesienie literaturowe: DARTS, P-DARTS, PC-DARTS, Fair DARTS, ENAS, Once-for-All, SPOS, FBNet,
      Auto-DeepLab, AutoHAS (tylko architektura, dzielenie wag; opublikowane wyniki, „inny protokół”);
    - wykluczone z powodem: zero-cost proxies (reguła zakresu), hypergradient descent i PBT
      (wymagają treningu), SageMaker HPO (chmura, zamknięty, płatny), Vertex AI AutoML / Auto-PyTorch /
      Auto-sklearn / AutoKeras (pełne AutoML na własnych przestrzeniach i danych), W&B Sweeps
      (duplikat GP-BO), SigOpt (niedostępny — do potwierdzenia), NNI (algorytmy pokryte; zgodność
      z Pythonem 3.13 — do potwierdzenia), TransNAS-Bench-101 (tylko architektura).

## Otwarte decyzje

Brak.

## Kolejność

2b → 2c → 2d → 3 → commit → 4 → 4b → 5 → 6.

4b wymaga frontów z etapu 1 i dzieli GPU z ramionami BoTorch, więc najprościej uruchomić go po fazie 4.
