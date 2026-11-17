# v005 — analiza A8 (pomiar czasu i pamięci metod; 2026-10-29)

Dane: run rooty `ec1ba9cb` (metody główne + MF, 6 workerów), `e6734ccd` (qParEGO osobno, Vizier NB201/NHB),
`7b7abd84` (reszta Viziera) — 490 przebiegów, seed 61, b ∈ {100, 350}. Wyniki A8 nie wchodzą do artykułu.
**Lokalizacja (od 2026-10-31):** `implementation/experiments/results/a8/<root>` (przeniesione z `results/runs/` — rekordy sprzed
poprawki pamięci blokowały W-BM7 w bramce `checks`; decyzja autora 2026-10-31).
**Model prognozy czasu i warianty S0/S1 to wybór Claude'a, do akceptacji autora**; wnioski → PROPOZYCJE P2, P3 w
`v005-todo.md`.
Skrypt: `implementation/experiments/scripts/analyze_a8_v005.py` (model czasu: t(b) = t(b0)·(b/b0)^k, b0 = 100 dla
b ≤ 100, inaczej 350; NB201 v005 liczony z czasów NB201 z A8). Siatka: `configs/pipeline/v005.yaml`, 28 560 punktów,
seedy 61–90.

## Czas siatki

| Wariant | 6 workerów | Vizier (osobno, 1 worker) | 1 maszyna | 2 maszyny |
|---|---|---|---|---|
| S0: szkic, wszystkie budżety | 1525 h → 10.6 dnia | 689 h → 28.7 dnia (+ JAHS b ≥ 200 nie mieści się w RAM) | 39 dni | 29 dni |
| S1: GP (Vizier, qNEHVI, qParEGO) tylko b = 50, 100 | 741 h → 5.1 dnia | 114 h → 4.8 dnia | 9.9 dnia | 5.1 dnia |

Największe pozycje w S1: NSGANetV2 374 h, MO-DSA 157 h, Vizier 114 h, ASHA 67 h, MO-PSA 58 h.

## Pamięć

- Vizier: ~28 GB ponad random search (FCNet b=350), 30 GB RSS już przy b=100 na NB201 → tylko sam na maszynie 30 GB;
  b=350 na JAHS (z mostem ~12 GB) nie mieści się wcale (OOM, `v005-implementation-status.md`).
- qNEHVI/qParEGO b=350 na JAHS przy 6 workerach → OOM (zabity most). W S1 nie występuje.
- **Pomiar pamięci w warunkach siatki jest niewiarygodny:** `process_peak_rss_mb` to szczyt procesu workera od jego startu,
  nie przebiegu (worker liczy wiele punktów po kolei) — stąd identyczne wartości (7918 / 10373 MB ponad RS) u ~20 metod.
  Pamięć mostu JAHS (`bridge_peak_rss_mb`) nie zapisana w żadnym przebiegu (wspólny most). Do poprawy przed v005
  (zerowanie szczytu na początku przebiegu, np. `/proc/self/clear_refs` = 5 na Linuksie; pomiar mostu wspólnego).

## Kontrole level 4

- `surrogate_share` FAIL w 6 przebiegach P3Net / P3Net-nolink przy b=100: 1 krok mieszania, a jest to obowiązkowa
  prawdziwa ewaluacja na poziom (D-3 b) → udział 0 z definicji. Kontrola powinna dawać „n/a”, gdy kroków mieszania
  nie ma więcej niż obowiązkowych prawdziwych. Przy b=350 udział 50–86 %, ale na JAHS tylko 6–8 kroków mieszania na
  przebieg (wątek B: surogat P3Net działa na małej części budżetu).
- Pozostałe kontrole: OK.
