# P3Net — notatki: jak usprawnić

Stan: 2026-10-07. Źródła: `chapters/v003`, `_parked/przewozniczek_isolation.tex`,
`implementation/experiments/CHANGELOG.md`, `notes/plans/v004-plan.md`,
`notes/lympus-nas-adaptation-validation.md`, `results/tables/p3net_variants_comparable.md`.

## Gdzie jesteśmy (1 linijka na fakt)

- 0/16 komórek: brak separacji od random search
- przegrane z SH-EMOA / TPE / NSGA-Net / NSGANetV2 rosną z budżetem (0 → 5 → 10 → 12)
- P3+abs. regressor na tej samej piramidzie → też 0/16 → winny silnik, nie surogat
- NB201 arch-only: P3Net null, `bartnik_p3` null, `przewozniczek_p3elympus` **wygrywa** przy b=350 (δ=+0.69)
- sweep wariantów (κ ½/2×, próg strict/permissive, donors, truncation, interactions) → zero istotnych różnic
- `cascade` → 1 wygrana (Colorectal b200), reszta neutralna/ujemna, droższy
- k-arne pułapki, b=2000: P3Net gorszy od random search → porażka niezależna od NAS

---

## Problem → rozwiązanie (ogólne, wynikają z konstrukcji algorytmu)

### P1. Piramida zjada budżet na losowy bootstrap
- objaw: 89.7–92.4% budżetu przy b=350 to losowe wypełnianie poziomów
- przyczyna: rozmiar poziomu 2^k → nowy poziom > suma poprzednich (matematyka, nie cecha NAS)
- warm-start z frontu H_t pomógł mało — reguła wzrostu bez zmian
- próba: stała zamiast 2^k → duża regresja (OM bez prawdziwej populacji degeneruje)
- rozwiązania:
  - wzrost poziomu sterowany pulą dawców (rośnie, gdy dawcom brak różnorodności), nie harmonogramem
  - wypełnianie nowego poziomu przez mutację / OM z frontu zamiast uniform random
  - kanoniczny P3: kaskada jednego osobnika przez wszystkie poziomy zamiast sweepu tylko najnowszego

### P2. Bramka akceptacji = rzut monetą
- precyzja 0.498 (14562 predykcji); lepiej tylko przy |H_t| ≤ 30 (0.551)
- rozwiązania:
  - porównanie dyskretne lepszy / gorszy / niejednoznaczny (eLyMPuS) zamiast regresji δ
  - niejednoznaczny → realna ewaluacja (zamiast zgadywania)
  - bramka kwantylowa (Dushatskiy / bartnik): ufaj tylko predykcjom z górnego kwantyla pewności
  - bramka probabilistyczna P(δ>0) > τ — patrz Kalman (I1)

### P3. Surogat addytywny, źle skalibrowany
- ridge na one-hot → brak interakcji, sprzeczne z ideą OM
- R² < 0 wszędzie (−1.46 … −3.28); na pułapkach k-arnych też przegrywa → problem ogólny
- RF (bartnik_p3) też nie wystarczył sam w sobie
- rozwiązania:
  - ranking zamiast regresji (RankNet / pairwise loss) — liczy się kolejność, nie wartość
  - surogat zbudowany na drzewie linkage — otwarty problem CS-GOMEA

### P5. Teleskopowanie kumuluje błąd
- MSE 26.5 (głębokość 1) → 106.2 (głębokość 5)
- κ = 2⌈log₂n⌉ to heurystyka bez gwarancji (brak monotoniczności)
- rozwiązanie: cięcie łańcucha po skumulowanej wariancji zamiast stałego κ (I1)

### P6. Otwarta luka B4 (przed wnioskiem o eLyMPuS)
- przewozniczek vs bartnik różnią się też celem: skalarny f1 vs akceptacja "nie zdominowany"
- potrzebne ramię kontrolne: kanoniczny P3 + bramka + RF + FIHC po samym f1 → `canonical_p3_scalar_fihc` (M10, v004)
- dopiero wynik M10 rozstrzygnie: mechanizm porównania czy skalaryzacja

### P7. Przestrzeń za mała / redundantna
- NB201 / JAHS: mała, skośna ku dobrym architekturom (Lopes 2023)
- den Ottelander: MO-GOMEA = random na NB101, wygrywa na MacroNAS
- rozwiązania:
  - test na większej przestrzeni (MacroNAS, NB101, FCNet w v004 — sprawdzić wynik)
  - skalowanie n i patrzenie, czy przewaga rośnie (zgodnie z literaturą LL)

---

## Improvements: pomysł → co ma poprawić (ogólne)

### I1. Filtr Kalmana jako surogat (rekurencyjna regresja bayesowska)
- stan = wagi surogatu, pomiar = każda pełna ewaluacja
- Q=0 ≡ ridge + kowariancja; Q>0 ≡ dryf / zapominanie
- daje:
  - P(δ>0) → bramka trójdzielna (lepszy / gorszy / niejednoznaczny → realna ewaluacja) → P2, most do eLyMPuS
  - wariancja wzdłuż łańcucha → cięcie zamiast κ → P5
  - tanie aktualizacje online (bez refitu od zera)
- nie daje:
  - nic na piramidę (P1) — 90% budżetu dalej losowe
  - nic na addytywność (P3) — model wciąż liniowy
  - nic na szum — benchmarki deterministyczne
- ryzyko: źle dobrany model → wariancja zaniżona → sprawdzić kalibrację (pokrycie przedziałów)
- warianty: EKF / UKF na małym nieliniowym modelu; Ensemble KF (zespół = niepewność bez linearyzacji)
- kolejność: dopiero po naprawie P1

### I2. Warunkowy eLyMPuS jako mechanizm porównania
- zastępuje δ̂_F porównaniem dyskretnym z odkrywaniem linkage
- co poprawia: P2, P3; jedyny kierunek z pozytywnym wynikiem (NB201 b=350)
- uwaga: oszczędność FFE w k-arnej wersji tylko 11–13% (vs 30–60% binarnie)
- warunek: M10 (P6)

### I3. Piramida sterowana dawcami
- co poprawia: P1 — budżet idzie w mixing, nie w losowanie
- metryka sukcesu: udział bootstrapu ↓, separacja od random search ↑

### I5. Ranking zamiast regresji
- pairwise / listwise loss na parach (x, x')
- co poprawia: P2 (bramce potrzebny znak, nie wartość), P3 (mniej wrażliwe na skalę błędu)

### I6. Aktywne uczenie / dobór do ewaluacji wg niepewności
- C* = niezdominowane w (f̂₁, f₂) + kandydaci o największej niepewności (UCB / EI na δ)
- co poprawia: P2, dane tam, gdzie surogat ślepy
- wymaga niepewności → I1 albo zespół

### I8. Multi-fidelity
- tani filtr przy niskich epokach przed pełną ewaluacją (drabina już zaimplementowana)
- co poprawia: więcej "pomiarów" na budżet → lepszy surogat wcześniej (P2)
- uwaga: trzeci, nieablowany mechanizm — osobne ramię

### I9. `cascade` (kaskada przez wszystkie poziomy)
- mechanizm kanonicznego P3, nie wymyślony pod dane
- co poprawia: P1 (wykorzystanie niższych poziomów)
- odroczone: 1 wygrana, niedostatecznie zbadane, droższe → dedykowany eksperyment z większą mocą
- nie uzasadniać wygraną na Colorectal b200 (cherry-pick)

---

## ⚠ Ryzykowne — dopasowanie pod benchmark (osobna lista)

Wspólne: motywacja pochodzi z obserwacji na tych samych 4 przestrzeniach i seedach 1–30,
więc ocena na nich będzie zawyżona.

### R1. Poprawki pod skok błędu na poziomie 16 (dawne P4)
- obserwacja: R² = −4.71 (MSE 767) vs +0.55 (MSE 85) na poziomie 2
- hipoteza (nowa populacja + F bez par treningowych) **niepotwierdzona**
- pomysły: fallback na realną ewaluację dla F z < N par; dryf wag (Kalman Q>0); prior z rodzica w LT (dawne I4)
- dlaczego ryzykowne: leczy objaw jednego poziomu przy jednym budżecie
- warunek: najpierw potwierdzić mechanizm (log par na F vs błąd), dopiero potem poprawka

### R2. Cechy interakcji / surogat per-F dobrany wg proxy interakcji
- motywacja: przyrost R² z interakcji zmierzony na tych benchmarkach (+0.016 … +0.259)
- już przetestowane (`p3net_surrogate_interactions`) → bez efektu
- dlaczego ryzykowne: dobór pojemności modelu pod konkretną strukturę JAHS / NAS-HPO-II

### R3. Strojenie κ i progu akceptacji
- κ ½ / 2×, strict / permissive → zero istotnych różnic
- dlaczego ryzykowne: klasyczne strojenie parametrów na danych testowych

### R4. Stałe dobrane na tych danych
- np. limit udziału bootstrapu ≤ 30%, próg N par, τ bramki
- dlaczego ryzykowne: magiczne liczby z tych samych przebiegów
- jeśli potrzebne: ustalić a priori albo z problemu syntetycznego

### R5. Adaptacyjna siatka HP / mieszane kodowanie (dawne P8)
- siatka zamiast ciągłych HP; kontrola NSGANetV2-continuous nie uruchomiona
- pomysły: zagęszczanie siatki wokół frontu; RV-GOMEA-style dla HP
- dlaczego ryzykowne: strojenie pod 4 HP konkretnie z JAHS

### R6. Warm-start z LLM / transfer (dawne I7)
- celuje w losowy bootstrap (P1)
- dlaczego ryzykowne: informacja spoza budżetu, możliwa kontaminacja NB201 (publiczny)
- → future work, nie w artykule

### R7. Porzucenie piramidy (jedna populacja + LT)
- może działać, ale to już nie P3 → zmienia się pytanie badawcze, nie tylko algorytm
- jeśli tak: nazwać jako inny algorytm, nie "poprawiony P3Net"

---

## Zabezpieczenia przed dopasowaniem
- seedy 31–60 (prerejestracja v004) — nieużyte do projektowania
- FCNet — niezależny benchmark, inna rodzina
- k-arne pułapki / NK — poprawka ogólna, jeśli pomaga też tam
- mechanizm i hipoteza zapisane przed uruchomieniem, nie po wyniku

---

## Priorytety (moja kolejność)
1. M10 / B4 → czy eLyMPuS to faktycznie mechanizm porównania
2. I3 (piramida) — bez tego reszta ginie w 90% losowania
3. I2 + I1 razem: eLyMPuS-like bramka trójdzielna z P(δ>0) z Kalmana
4. I5 / I6 jeśli surogat dalej słaby
5. P7: większa przestrzeń jako test sufitu benchmarku
6. R-lista tylko po potwierdzeniu mechanizmu i z walidacją na seedach 31–60 + FCNet
