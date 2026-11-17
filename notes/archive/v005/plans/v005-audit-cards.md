# v005 — przegląd kart źródeł vs kod vs testy (2026-11-17)

Powód: rozbieżność opisu P3Net-gate (prerejestracja „quantile acceptance gate”, kod: reguła akceptacji MO-GOMEA na
predykcji), wykryta przy pisaniu claimu C-48. Pytanie: czy to jedyne miejsce, gdzie karta była niejednoznaczna albo
decyzja nie dotarła do kodu, testów lub prerejestracji.

Metoda: dla każdej z 14 kart — decyzje i założenia (D-, S-, K-, B-, Z-, E-, BB-, A-, MF-, N-, V-, R-, RE-, L-, BM-),
czy mają własność W (test poziomu 1), a gdy nie — porównanie z kodem `implementation/lib/src/p3net/v005/`; do tego
stałe modułów w kodzie, których nie ma w kartach, oraz decyzje #25–#37 z `v005-decisions.md`. Bez liczenia.

## Wynik ogólny

Karty NSGA-Net, NSGANetV2, RegEvo, MO-LS, kanoniczne P3, MF, eLyMPuS (mechanizm), Bartnik (mechanizm): każda decyzja ma
własność W i test — zgodne. Rozbieżności skupiają się w miejscach **poza tabelami W**: warianty opisane prozą,
obietnice analiz w kartach, które nie weszły do prerejestracji, i stałe implementacji.

## Ustalenia

| # | Gdzie | Karta / decyzja | Kod / stan | Skutek | Waga |
|---|---|---|---|---|---|
| F1 | P3Net-gate | `p3net.md` D-3 a: „prawdziwa ewaluacja, gdy surogat przewiduje poprawę (z progiem)”; `p3net-surrogate.md` §5: „bramka kwantylowa”; prerejestracja Q2 b: „quantile acceptance gate” | `engine._mix_gate`: krok oceniany naprawdę, gdy **przewidywane** cele przechodzą regułę akceptacji MO-GOMEA (D-1 b); bez kwantyla; brak W, brak testu, brak pytania implementującego | opis w prerejestracji i karcie niezgodny z tym, co liczyło się we wszystkich przebiegach; wyniki spójne | wysoka (opis metody) |
| F2 | P3Net-gate | S-7 a: przeuczanie „po każdej prawdziwej ewaluacji i po każdej zmianie drzewa” | `_refit` tylko przed mieszaniem z poziomem; w gate prawdziwe ewaluacje w trakcie mieszania nie przeuczają modelu do następnego poziomu (w P3Net D-3 b równoważne, bo tam prawdziwa ewaluacja jest na końcu poziomu) | drugie odstępstwo gate od karty; nieopisane | średnia |
| F3 | surogat | S-8: „obowiązkowo walidacja krzyżowa grupowana” (do doboru hiperparametrów, „jeśli jakiekolwiek”); claim **C-15** „The surrogate is validated with grouped cross-validation” ✅ | `grouped_cv_folds` istnieje i ma test (W-S6), ale **nigdzie nie jest wywoływana**; RF z domyślnymi hiperparametrami (S-4 a), więc nic nie jest dobierane ani walidowane | zdanie C-15 jest nieprawdziwe w treści, choć ma zielony test | wysoka (claim) |
| F4 | surogat | „liczba par rośnie jak N² (potrzebne próbkowanie par)” — bez decyzji | `MAX_PAIRS = 3000` losowych uporządkowanych par (zużywa `rng`); zapisane tylko w `v005-implementation-status.md` | nieopisany parametr metody „bezparametrowej”; do opisu metody | średnia |
| F5 | wszystkie | #36: „`ExplorationCollapse` (stop przy < 20 % unikalnych w oknie 20)” | v005: progi per metoda — REINFORCE 10 000 kolejnych duplikatów, MOTPE/biblioteki 10 000 zapytań bez nowego genotypu, MO-DSA/MO-PSA 1 000 iteracji bez nowej ewaluacji, RegEvo 100 000 dzieci-duplikatów, P3 200 000 kolejnych trafień w cache | tekst decyzji z v004 nieaktualny; artykuł (Limitations) opisuje ogólnie — poprawny | niska |
| F6 | SH-EMOA, MO-BANANAS (BoB) | BB-3: punkt odniesienia HV „z protokołu metryk (wspólny, A12), w znormalizowanej przestrzeni celów” | `bob.py`: HV w celach znormalizowanych **min–max po ocenionych dotąd punktach** (`online_minmax`), ref (1.1, 1.1) — nie granice przestrzeni A12 | rozsądne (bez wiedzy spoza budżetu), ale inne niż karta; wiersz suplementu „common HV reference” wprowadza w błąd | średnia |
| F7 | MO-DSA, MO-PSA | B-3 (decyzja 2026-10-16): γ = 0.999, „γ = 0.9 w suplemencie jako analiza wrażliwości” | ramienia γ = 0.9 nie ma w żadnym planie; prerejestracja go nie wymienia | obietnica karty zgubiona przed prerejestracją | średnia |
| F8 | P3-eLyMPuS | „Test na NAS (suplement)”: oszczędzone ewaluacje, odsetek błędnych odpowiedzi z list, HV | rekordy nie logują statystyk eLyMPuS (tylko zdarzenia silnika); Q7 w prerejestracji = tylko δ jakości | dwie z trzech obiecanych miar niewykonalne z rekordów (jak K8) | średnia |
| F9 | adaptery bibliotek | §4: przebieg kończący się przed b to błąd (chyba że przestrzeń wyczerpana) | MOTPE: 4 przebiegi kończą się „10 000 asks without a new genotype” i są przyjęte z powodem zatrzymania | niezgodność reguły z praktyką; opisane w tabeli budżetu | niska |
| F10 | REINFORCE | decyzja (`v005-decisions.md`, „REINFORCE — nagroda”): **trzy warianty** (MnasNet, MONAS, Chen et al. ADC); R-5: MONAS α = 0.75 w torze głównym, α = 0.25 w suplemencie | uruchomiony jeden wariant: **MONAS α = 0.75** (domyślny w klasie); MnasNet, ADC i α = 0.25 nie liczone; brak zapisu decyzji o redukcji; prerejestracja: jedno ramię bez nagrody | artykuł musi podać nagrodę; redukcja do opisania | średnia |

## Przyczyna wspólna

Testy poziomu 1 pilnują tylko tego, co jest w tabelach W. F1, F2 (wariant gate), F7, F8, F10 (warianty i analizy
opisane prozą), F3 (warunek „jeśli jakiekolwiek”), F4 i F6 (rozstrzygnięte w kodzie bez pytania) leżą poza nimi.
Prerejestrację pisano z kart, nie z kodu, więc niejednoznaczności przeszły dalej. Implementujący (Claude) rozstrzygał
niejasności sam zamiast zapisać pytanie — F1, F4, F6.

## Do decyzji autora (krok 2)

- F1, F2: wpis do prerejestracji §8 (opis wariantu gate niezgodny z kodem; przeuczanie co poziom), poprawka karty
  surogatu §5, wiersz w tabeli odstępstw; test W17 (runda 10, już przygotowana).
- F3: usunąć/przepisać C-15 (np. „the surrogate uses library-default hyperparameters; nothing is tuned”), bez zdania o
  walidacji w artykule.
- F4: opisać w metodzie (≤ 3 000 losowych par) i dodać do tabeli odstępstw/założeń.
- F5: poprawić tekst #36 w `v005-decisions.md` (progi per metoda).
- F6: poprawić wiersz BoB w tabeli odstępstw i kartę BB-3.
- F7, F8, F10: dopisać jako odstępstwa §8 (obietnice karty niewykonane / zredukowane) — albo dołożyć przebiegi
  (F7: 2 ramiona × 1 080 przebiegów; F10: do 3 ramion × 1 080) — koszt do podania przed decyzją.
- F9: zdanie w karcie adapterów.

## Krok 2 — wykonane 2026-11-17 (decyzje autora: poprawki opisów; F7, F8, F10 bez dokładania przebiegów)

| # | Co zrobiono |
|---|---|
| F1, F2 | prerejestracja §8.5; karta surogatu §5 i S-7 (sprostowania); tabela odstępstw (wiersz P3Net-gate); Limitations (zdanie); Setup i C-48 opisują bramkę z kodu; test W17 — runda 10 |
| F3 | C-15 wycofany (`v005-claims.md`); karta S-8 (stan); nowy claim C-49 (pary, domyślne hiperparametry) |
| F4 | karta S-4 (uzupełnienie) i W-S11; tabela odstępstw (wiersz P3Net surrogate); C-49; test — runda 10 |
| F5 | `v005-decisions.md` #36 — progi v005 per metoda |
| F6 | tabela odstępstw (wiersz BoB: normalizacja min–max online, ref (1.1, 1.1)); karta BoB (audyt) |
| F7 | karta Bartnik (audyt): γ = 0.9 nie liczone |
| F8 | karta eLyMPuS (audyt): test na NAS nie wykonany, v005 = Q7 |
| F9 | karta adapterów (audyt) |
| F10 | karta REINFORCE (audyt) i W-R9; `v005-decisions.md`; Compared methods: „MONAS reward (α = 0.75)”; C-50; test — runda 10 |

Do zrobienia przez autora: wkleić rundę 10 (`v005-test-author-prompt.md`) do sesji autora testów. Przy przepisywaniu
sekcji metody (punkt 1): opisać ≤ 3 000 par i domyślne hiperparametry RF; usunąć zdanie v003 o walidacji krzyżowej
(`chapters/archive/v003/proposed_optimizer/main.tex` l. 57).

