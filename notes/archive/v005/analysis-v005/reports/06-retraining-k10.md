# 06 — retrening punktów kolanowych (K10, prerejestracja §3 poz. 8, §8.4) — 2026-11-17

Źródło: `implementation/experiments/results/retraining/` — 40 treningów (`runs/*.json`, zakończone 2026-11-17 12:04),
`scripts/analyze_retraining_v005.py` → `retraining_v005_arms.csv`, `retraining_v005_summary.csv`. Opisowo, bez testów.
Maszyna i ustawienia: prerejestracja §8.4 (m.in. przerwa 08:13 — brak pamięci wirtualnej; restart, przerwany trening
NB201 policzony od nowa).

| | NB201 | NAS-HPO-II |
|---|---|---|
| ramiona / treningi | 22 / 16 | 27 / 24 |
| średnia różnica (retrening − benchmark), pp dokładności walidacyjnej | −0.10 | −0.88 |
| mediana / maks. \|różnicy\| | 0.24 / 0.56 | 0.96 / 3.38 (OSS Vizier) |
| Spearman benchmark vs retrening (treningi) | 0.75 | 0.92 |
| P3Net: benchmark → retrening | 88.92 → 88.56 | 82.36 → 81.00 |
| ranga P3Net: benchmark → retrening | 9 → 15 (z 22) | 9 → 16 (z 27) |

Wnioski:
- NB201: wartości benchmarku potwierdzone w granicach ±0.6 pp.
- NAS-HPO-II: retrening systematycznie niższy (−0.9 pp średnio). Możliwa przyczyna (niesprawdzona): sieć budowana z
  xautodl TinyNetwork, nie z modułu autorów (§8.4); jeden seed na trening.
- Kolana wielu ramion leżą blisko (NB201: 16 z 22 w 0.6 pp; NHB: 13 z 27 w 1 pp od P3Net), więc pojedynczy trening
  przestawia rangi — retrening nie rozróżnia ramion. Spadek rangi P3Net to efekt tej bliskości, nie wynik o metodzie.
- Akapit „Retraining the knee points” w `chapters/results/main.tex` (zastąpił `\TODO`).
