# v005 — dlaczego P3Net i kanoniczne P3 różnią się, gdy surogat nie działa

Stan na 2026-11-16. Pytanie z raportu 02 (B1 b): przy b = 50 P3Net nie wykonuje żadnego kroku mieszania, a mimo to kończy
identycznie jak kanoniczne P3 tylko w 5.8 % runów (przestrzenie główne).

## Przyczyna: przesunięty strumień liczb losowych, nie inny algorytm

Oba ramiona to ta sama klasa `P3Engine` (`lib/src/p3net/v005/p3/engine.py`), różniąca się tylko oceniaczem kroków
mieszania (`step_evaluator`). Każde dostaje generator `random.Random(seed)` (`methods/v005_adapter.py`, l. 187). Warianty
z surogatem (P3Net, P3Net-gate, P3Net-nolink) w konstruktorze pobierają z niego jedną liczbę na ziarno surogatu:

```python
self.surrogate = PairwiseSurrogate(self.domains, use_linkage=use_linkage, rng=random.Random(rng.getrandbits(64)))
```

Kanoniczne P3 tego nie robi. Od pierwszego `random_genotype` oba ramiona z tym samym seedem idą więc innymi losowymi
ścieżkami. Dopóki surogat nie wykona kroku, P3Net **jest** kanonicznym P3 — z innym, równie dobrym strumieniem losowym.

## Sprawdzenie (2026-11-16, serwer GPU, minuty)

Kanoniczne P3 uruchomione ponownie (`run_experiment.run_single`, ten sam kod i konfiguracja co w v005) z generatorem,
z którego przed startem pobrano jedno `getrandbits(64)`:

| Przestrzeń, b = 50 | seed 62 | 63 | 64 |
|---|---|---|---|
| NAS-HPO-Bench-II | identyczna historia | identyczna | identyczna |
| FCNet naval | identyczna | identyczna | identyczna |

W każdym przypadku historia ewaluacji (genotyp po genotypie) jest identyczna z rekordem P3Net z run rootu `c674c91e`;
kanoniczne P3 bez przesunięcia odtwarza własny rekord. (NHB seed 62: zwykłe kanoniczne P3 też jest identyczne z P3Net —
przypadek, oba strumienie dały ten sam przebieg.) Skrypt: `implementation/experiments/scripts/check_p3net_rng_offset_v005.py`.

## Co to znaczy dla wyników

1. **Przy b = 50 i 100 (na JAHS także 200) wynik P3Net to wynik kanonicznego P3** — surogat nie wykonuje kroku. Q1 przy
   tych budżetach mówi o silniku P3 (FIHC + piramida), nie o P3Net jako metodzie z surogatem. Słabość przy małych budżetach
   (gorszy od random search na JAHS) to słabość P3 z FIHC: pierwsze ewaluacje idą na lokalne wspinanie jednego
   rozwiązania.
2. **Q2/Q3 „P3Net vs kanoniczne P3” przy tych budżetach porównuje algorytm z nim samym** na dwóch niezależnych próbkach
   seedów. Brak istotnych różnic i TOST „równoważne / nierozstrzygnięte” są tam oczekiwane z konstrukcji. Test nadal jest
   poprawny (Mann–Whitney bez parowania, §4), ale nie mówi nic o surogacie.
3. **Gate i nolink** pobierają tę samą liczbę, więc idą tą samą ścieżką co P3Net aż do pierwszego kroku mieszania — stąd
   94.6 / 96.0 % identycznych wyników (raport 02).
4. **Wpływ surogatu można ocenić tylko tam, gdzie kroków jest więcej:** NHB, NB201 i FCNet przy b = 350 (41–56 kroków).
   Na NHB przy b = 200 i 350 kierunek jest przeciw P3Net (kanoniczne P3 lepsze w medianie, δ −0.14 i −0.18, TOST
   nierozstrzygnięty).
5. Nie jest to błąd w wynikach ani odchylenie od prerejestracji — seedy są niezależne, testy niesparowane. Jest to
   informacja do tekstu (etap C): napisać wprost, że przy budżetach bez kroków mieszania P3Net i kanoniczne P3 to ten sam
   algorytm.

## Możliwa zmiana na przyszłość (nie dla v005)

Ziarno surogatu brać z osobnego generatora (np. `random.Random(seed + stała)`), nie z `rng`. Wtedy P3Net i kanoniczne P3
z tym samym seedem szłyby tą samą ścieżką aż do pierwszej decyzji surogatu, a różnica w wyniku byłaby wprost efektem
surogatu (porównanie sparowane). Zmiana kodu metod — tylko w następnej iteracji, z nowym commitem i przebiegiem.
