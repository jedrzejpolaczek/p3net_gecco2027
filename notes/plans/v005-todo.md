# v005 — lista rzeczy do zrobienia

Stan na 2026-10-23. Szczegóły: `v005-plan.md`, `v005-implementation-status.md`, `v005-level2-criteria.md`.

## Etap A — rzetelność

### Teraz (Claude)

- [x] Poziom 3 na JAHS z celami v005: 26 PASS, 1 TIMEOUT (MO-PSA), 0 FAIL.
- [x] Statusy w `v005-claims.md`: 43 ✅, 2 czekają na tablicę energii (C-41, C-42).
- [ ] Analizy na danych v004 (A9): poprawki raportowania A1–A6, S4′ vs S5, TOST dla par „bez różnicy”, dekompozycja HV,
      JAHS posthoc.
- [ ] Porządki: nieaktualne komentarze w `configs/methods/p3net_cascade_*.yaml`.

### Autor projektu

- [x] Runda 6 dla autora testów (Q-49).
- [ ] Runda 7 dla autora testów (W-BM7: 0.0 dla czasu ładowania, Q-50) — `v005-test-author-prompt.md`.
- [ ] Commit + push całej pracy (kod, testy, karty, configi `*_v005`, tablice `implementation/experiments/results/
      benchmark_tables/`) — po poziomie 3 na JAHS i statusach w `v005-claims.md`.
- [ ] Test zasobów A8 na Hetznerze wg `v005-a8-runbook.md`; odesłać run root.
- [ ] Pomiar energii NB201 na laptopie: pilotaż 1000 wejść, potem pełny pomiar (konsola administratora) — koniec etapu A.

### Potem

- [ ] Analiza A8 → skala siatki v005 (szkic `configs/pipeline/v005.yaml`: 28 560 przebiegów). — Claude
- [ ] Tablica energii (`build_energy_table`), testy NB201 (W-BM1–W-BM3), poziom 3 NB201 z energią. — Claude
- [ ] Prerejestracja v005: pilotaż JAHS (punkt odniesienia HV, A12), retrening punktu kolanowego (A10), lista
      „analiza → skrypt → plik”. — Claude pisze, autor zatwierdza.
- [ ] Bramka `checks` na finalnym kodzie (testy, determinizm, poziom 4, karty, `v005-claims.md`). — Claude
- [ ] Przebieg v005, kontrola po przebiegu, analizy z prerejestracji. — autor uruchamia, Claude przygotowuje.

### Czekamy

- [ ] Nina Bartnik: N-0–N-4 + dopytanie o bramkę MO-DSA (percentyl vs próg względem elitist). Po odpowiedzi: korekta
      MO-DSA/MO-PSA i powtórka porównania z SAGOMEA.

## Etap B — interpretacja

- [ ] B1–B6 (`v005-plan.md`), w tym: surogat P3Net obejmuje małą część budżetu przy b ≤ 350 (FIHC dominuje);
      REINFORCE zużywa 40–90 z 350 ewaluacji; JAHS `size_MB` w v004 (B6).

## Etap C — tekst artykułu

- [ ] Related Work (nowe metody, cytowania SH-EMOA / MO-BOHB).
- [ ] Zdania artykułu zgodne z `v005-claims.md`.
- [ ] Limitations z kart: energia na laptopie; brak kodu Bartnik (Z-B), MO-DSA vs SAGOMEA −7.5 %; P3-eLyMPuS vs OLyMPuS
      −13 % FFE (pętla FIHC); NSGA-Net bez BOA; błąd całki w MO-BOHB przeniesiony z kodu; REINFORCE zbieżność; SDK 19041
      przy kompilacji OLyMPuS; JAHS niższe wierności z surogatu; GP tylko b ≤ 100.
- [ ] Reprodukowalność, podział tekst główny / suplement.

## Etap D — przed wysyłką

- [ ] Anonimizacja, samocytowania w trzeciej osobie, anonimowe repozytorium, `printacmref`.
- [ ] Regeneracja tabel z run rootu v005; zgodność liczb w tekście.

## Po v005

- [ ] eLyMPuS z grafem zależności NAS+HPO (pomysł promotora).
