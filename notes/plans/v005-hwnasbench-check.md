# NB201 f2: HW-NAS-Bench zamiast własnego pomiaru energii — sprawdzenie (2026-10-30)

Kontekst: pomiar energii na laptopie (BM-2) nie dał powtarzalnego wyniku w akceptowalnym czasie. Pilotaże 1–4
(10 000 wejść/przejście) zaliczone dopiero za 4. razem, na granicy (3.00 % przy progu 3 %); pełna tablica 4–10 dni
laptopa. Pilotaż 5 (1 000 wejść, decyzja 2026-10-18): Spearman 0.34, różnica 18 % — przejście 0.2 s za krótkie dla
licznika NVML (rozrzut próbek 52–55 %, 99 % architektur mierzonych ponownie, przyspieszenie tylko ~2.5×).

## 1–4: sprawdzenia

| # | Co | Wynik |
|---|---|---|
| 4 | Licencja, dostępność | MIT (GaTech-EIC, 2022). `HW-NAS-Bench-v1_0.pickle`, 10.8 MB, z repo GATECH-EIC/HW-NAS-Bench, sha256 `57f92c2d…ad872700`. Pickle zawiera wyłącznie tablice numpy (sprawdzone opkodami, wczytany unpicklerem z białą listą klas). |
| 2 | Indeksy | Dla każdego indeksu jest `config.arch_str`; **0 rozbieżności** z `nats_bench.query_index_by_arch` na 15 625. Nasza tablica (`NB201Energy`) i tak jest kluczowana `arch_str`. |
| 3 | Sprzęt | `edgegpu_energy`: Jetson TX2, TensorRT, batch 1, obraz 32×32, 50 powtórzeń po 3 s rozgrzewki; energia/obraz = średnia moc × czas (mJ) — **zmierzona** (`dev/proj_edgegpu/EdgeGPU_Benchmark.py`). ASIC (Eyeriss) i FPGA — szacowane (do potwierdzenia cytatem z pracy). CIFAR-10: 2.06–48.8 mJ, mediana 24.0. |
| 1 | Korelacja z FLOPs | Spearman **0.55** (Pearson 0.46) → f2 istotnie inny niż w v004. Z opóźnieniem tego samego urządzenia 0.99 (energia ≈ moc × czas przy batch 1). |

Dodatkowo:

- **Szum HW-NAS-Bench:** 1350 klas architektur izomorficznych (te same obliczenia) ma >1 członka; rozrzut energii w klasie:
  mediana CV 4.2 %, 90. percentyl 10.3 % (rozrzut całej przestrzeni: 30.9 %). Rząd szumu jak w naszych pilotażach.
- **Energia zależy od sprzętu i batcha:** nasz laptop (batch 256, pilotaż 4) vs TX2: Spearman 0.74; laptop vs FLOPs:
  0.88; TX2 vs FLOPs: 0.55. Przy batch 256 GPU jest ograniczone obliczeniami (bliżej FLOPs), przy batch 1 — liczbą
  i opóźnieniem jąder.

## 5–6: dalsze prace (bez obliczeń na serwerze)

1. Karta BM-2: nowa decyzja (HW-NAS-Bench edge GPU, CIFAR-10) + uzasadnienie (pilotaże 1–5) — Claude pisze, autor zatwierdza.
2. Dane: pobieranie pliku w `scripts/download_data.py` (sha256), budowa `results/benchmark_tables/nb201_energy.json`
   z HW-NAS-Bench (ten sam format: `metadata` + `energy` po `arch_str`; `NB201Energy` bez zmian interfejsu). Wartości w mJ
   zamiast bezwymiarowych.
3. Testy (runda 8, autor testów): W-BM2 (kompletność 15 625, metadane: źródło, urządzenie, sha256); W-BM3 (protokół
   pomiaru laptopa) → nieaktualny, zastąpić testem zgodności źródła (0 rozbieżności indeksów, sha256).
4. Twierdzenia C-41, C-42 — przeformułować pod źródło HW-NAS-Bench.
5. Poziom 3 NB201 z energią, bramka `checks` — jak w planie.
6. Skrypty pomiarowe i log `results/energy/nb201_energy.jsonl` zostają jako dowód decyzji.

## Możliwe zmiany w artykule

- Benchmarks: NB201 f2 = energia inferencji na obraz na edge GPU (Jetson TX2, batch 1) z HW-NAS-Bench [Li et al., ICLR 2021],
  nie własny pomiar.
- Limitations: brak własnego pomiaru (dlaczego: pilotaże); energia specyficzna dla urządzenia (laptop vs TX2 ρ = 0.74);
  szum tablicy ~4 % (izomorfy) — metoda może wybierać tańszy izomorf.
- Wyniki NB201 v005 nie są porównywalne z v004 (f2 = FLOPs, ρ = 0.55 z energią).
- Porównanie z Bartnik (Tab. 7.1) bez zmian — na FLOPs; jej f2 to energia własnego GPU, my — TX2.
- Możliwa uwaga merytoryczna: wybór celu sprzętowego zmienia front (ρ 0.55 z FLOPs) — argument za raportowaniem f2 na
  sprzęcie docelowym, nie przez FLOPs.
