# E1 — surogat przy b = 1 000 (eksploracyjnie)

Stan na 2026-11-16. Prerejestracja §7a (spisana przed gridem). Run root `results/runs/c674c91e-e1` (serwer Hetzner,
commit c674c91e + plik planu; kod metod identyczny z v005), 600/600 runów, 0 błędów, 0 duplikatów, każdy run zużył
pełne 1 000 ewaluacji. Analiza: `scripts/analyze_e1_v005.py` → `analysis/e1_q2.csv`, `e1_tost.csv`, `e1_descr.csv`.
**Wyłącznie eksploracyjnie; nic o P3Net względem innych metod.**

## Wynik w jednym zdaniu

Przy b = 1 000 surogat działa (100–230 kroków mieszania na run, 86–92 % decyzji mieszania przez surogat), a mimo to
P3Net nie różni się istotnie od kanonicznego P3 ani od swoich wariantów w żadnej z 12 porównań; koszt optymalizatora
rośnie z 0–2.5 s do 50–85 s na run.

## Q2 przy b = 1 000 (MWU, Holm w przestrzeni, δ > 0 = P3Net lepszy)

| Przestrzeń | vs kanoniczne P3 | vs gate | vs nolink |
|---|---|---|---|
| JAHS C10 (HV) | −0.26 (p_Holm 0.25) | −0.06 | +0.03 |
| JAHS CRC (HV) | +0.07 | +0.08 | +0.07 |
| JAHS FMN (HV) | −0.08 | −0.04 | −0.03 |
| NHB (IGD+) | +0.00 | +0.15 (p_Holm 0.94) | +0.04 |

Wszystkie n.s. Mediany w każdej przestrzeni w wąskim pasie (np. C10 HV 0.9169–0.9175, NHB IGD+ 0.0081–0.0091).

## Q3 / TOST

- m = 0.33: równoważne 9/12; nierozstrzygnięte 2 (FMN vs kanoniczne, NHB vs gate); **„different” 1: C10 vs kanoniczne
  P3** (δ −0.26, CI [−0.50, −0.02], na korzyść kanonicznego). MWU w tej samej komórce n.s. (p = 0.084) — dwa kryteria
  dają różny sygnał; efekt mały (różnica median HV 0.0006).
- m = 0.147: 0/12 równoważnych — przy 30 seedach szerokość CI (~0.5) nie pozwala wykazać tak wąskiej równoważności.
- W odróżnieniu od v005 (b ≤ 350) równoważność **nie jest mechaniczna**: runy nie są kopiami P3Net.

## Opisowo

| Przestrzeń | kroki mieszania P3Net (mediana) | udział surogatu | ten sam wynik co P3Net: kanon. / gate / nolink | czas optymalizatora P3Net / kanon. |
|---|---|---|---|---|
| JAHS C10 | 112 | 0.91 | 3 % / 33 % / 77 % | 68 s / 2.5 s |
| JAHS CRC | 91 | 0.90 | 13 % / 43 % / 80 % | 50 s / 1.1 s |
| JAHS FMN | 128.5 | 0.92 | 17 % / 67 % / 73 % | 75 s / 2.2 s |
| NHB | 227.5 | 0.86 | 7 % / 17 % / 20 % | 84 s / < 0.1 s |

- „Ten sam wynik” = ta sama końcowa wartość metryki przy tym samym seedzie; nie oznacza tej samej historii (na JAHS
  HV jest nasycone, różne drogi mogą kończyć tym samym frontem). Nie sprawdzałem historii.
- Gate: level 4 nie zapisuje `surrogate_share` (jak w v005); licznik kroków klastrów z rekordu silnika: 104–229,
  ten sam rząd co P3Net.
- Kanoniczne P3 robi tyle samo kroków mieszania (101–200) — surogat zmienia **decyzję** o akceptacji, nie ich liczbę.
- Random search (tylko punkt odniesienia): wszystkie cztery warianty P3 lepsze, δ 0.92–1.00 w każdej przestrzeni.

## Co z tego wynika (do etapu C)

1. Pytanie z B1 (b) ma odpowiedź: brak efektu surogatu w v005 nie wynikał tylko z braku okazji. Przy b = 1 000 surogat
   podejmuje ~90 % decyzji mieszania, a jakość końcowa się nie zmienia (12/12 n.s.; jedyny sygnał — C10 — przeciw
   P3Net).
2. Surogat parowy w obecnej postaci nie poprawia P3 na tych benchmarkach; kosztuje 27–45× więcej czasu optymalizatora
   na JAHS, na NHB 84 s wobec < 0.1 s (nolink tańszy: 6–20 s).
3. Wariant surogatu (gate, nolink) też nie ma znaczenia dla jakości.
4. Granice: eksploracyjne, jeden budżet, 4 przestrzenie, 30 seedów; równoważności przy m = 0.147 nie da się wykazać.
   Nie mówi nic o innej konstrukcji surogatu (pozycje B5: log(f1), akceptacja po obu celach) — te teraz mają sens,
   bo surogat faktycznie decyduje.
