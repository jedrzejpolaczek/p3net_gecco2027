# Eksploracyjna analiza wyników v004

Skrypty z pierwszego przeglądu wyników v004 (2026-10). **Nie są** kodem raportującym artykułu
(`implementation/experiments/scripts/generate_report.py`) i nie mają wprowadzonych poprawek A1–A6
z `notes/archive/v004-audit-checklist.md` (przeniesione do `notes/plans/v005-plan.md`, A9). Liczby z nich są eksploracyjne.

## Pliki dla agentów analizy

- `CONTEXT.md` — wspólny kontekst i zasady dla przebiegów 1–3 (materiały, kod, dane, znane odchylenia od prerejestracji).
- `PROMPTS.md` — trzy prompty: 1) audyt wierności implementacji, 2) analiza wyników, 3) konfrontacja z artykułem, notatkami i literaturą.
- `INITIAL_FINDINGS.md` — przeniesione do `notes/archive/analysis-v004/` (zastąpione raportem 02, §8).
- `reports/` — raporty przebiegów (`01-implementation-audit.md`, `02-results-analysis.md`, `03-paper-confrontation.md`).

## Uruchomienie

```sh
V004_OUT=<katalog poza repo> sh notes/analysis-v004/run_all.sh
```

Pliki pośrednie (pickle, CSV, `summaries.txt`) trafiają do `$V004_OUT`, nie do repo.
Python: `implementation/experiments/.venv` (można nadpisać zmienną `PY`).

## Dane wejściowe

- `implementation/experiments/results/runs/b4d25cac/` — plan `v004.yaml`, etapy s1–s9.
- `implementation/experiments/results/runs/gp-small/` — Vizier, BoTorch qNEHVI/qParEGO, budżety 50 i 100
  (plan `v004-gp-small.yaml`, commit 1bba34af; kod metod identyczny jak w b4d25cac).
- Fronty oracle: `implementation/experiments/results/reference_fronts/oracle__*.json`.

## Skrypty

| Plik | Co robi | Wyjście |
|---|---|---|
| `extract.py <raw> <out.pkl>` | równolegle czyta wszystkie JSON-y przebiegów, zostawia historię celów i skalarne diagnostyki | `runs.pkl`, `runs_gp.pkl` |
| `analyze.py` | zamraża fronty JAHS/NB201 (prereg §3: s1+s3+s7, seedy 1–30), liczy metrykę per przebieg (HV 2D względem frontu albo IGD+ znormalizowany do frontu oracle), testy Q1–Q4, Q7, vs RS, NB201 (dwustronny MWU, Holm w komórce, Cliff's δ) | `per_run.csv`, `comparisons.csv`, `summary.csv`, `fronts_info.json`, `diag.pkl` |
| `timing.py` | tabela z etapu s9 (sekwencyjnie, budżet 350, seed 1) | `timing.csv` |
| `ladder.py` | rozkład S5 → RF → RF+FIHC → RF+FIHC-eLyMPuS na kroki; jakość surogatu z `surrogate_quality_log`; profil f1/f2 ocenionych punktów | wydruk |
| `equivalence.py` | A9: TOST (bootstrapowy 90% CI Cliff's δ, marginesy 0.147 / 0.33) dla par „bez różnicy” i S4′ vs S5 | `equivalence.csv`, wydruk |
| `hvdecomp.py` | A9: HV JAHS rozbity na tanią / dokładną część frontu (front zamrożony A6); `duplication_rate` per metoda | `hvdecomp.csv`, wydruk |
| `summaries.py` | zestawienia: wygrane/porażki per grupa przestrzeni, vs RS, Q2/Q3, rankingi wg typu problemu (wszystkie budżety i tylko 50/100), udział bootstrapu, kompromis jakość–czas względem S5 | `summaries.txt` |

## Konwencje

- `comparisons.csv`: kolumna `delta` — dodatnia = lepiej dla ramienia referencyjnego (`ref`); `sig` = Holm-adjusted p < 0.05.
  Dla rodziny `vsRS` referencją jest random search, więc `delta < 0` znaczy, że ramię bije RS. Dla `Q2` `delta > 0` znaczy, że późniejszy etap jest lepszy.
- Rodziny `Q1`/`Q4`/`Q7`/`vsRS` są liczone na wszystkich przestrzeniach obecnych w danych; NB201 ma osobne rodziny `NB201`, `NB201_vsRS`
  (w `Q1`/`vsRS` komórki NB201 należy pomijać).
- Szczątkowe przebiegi GP z b4d25cac są wykluczone (przeniesione do `runs/archiwum/`); metody GP pochodzą wyłącznie z gp-small.
- `ladder.py` zakłada, że `surrogate_quality_log` zawiera tylko kandydatów zaakceptowanych i ocenionych naprawdę — niesprawdzone w kodzie.
- Czasy dla FCNet w `summaries.py` to mediany z przebiegów równoległych (etap s8), nie z sekwencyjnego s9 — orientacyjne.
- RSS procesów w `per_run.csv` dla gp-small jest zawyżone przez wyciek pamięci w procesie workera; pamięć per przebieg brać z s9.
