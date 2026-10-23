# Kanoniczne P3 (bez surogatu) — karta źródła

Status: **ZATWIERDZONA** (2026-10-16, autor projektu; decyzje w §7).
Zależy od: `notes/plans/v005-sources/p3net.md` (zatwierdzona). Ta karta opisuje **tylko różnice** względem niej.

## 1. Źródło i rola

- Źródło: jak P3Net — Goldman & Punch, GECCO'14 (`goldman2014parameterless`), kroki P1–P25 z karty P3Net §2.
- Referencyjny kod autorów: repozytorium Goldmana na GitHubie (prawdopodobnie `brianwgoldman/FastEfficientP3`, C++) —
  **do potwierdzenia**; potrzebny do testu zgodności poziomu 2 (karta P3Net §6).
- Rola w artykule: **ablacja „P3Net bez surogatu”**. Ten sam silnik, te same decyzje D-1, D-2, O-1, O-4, O-5; każdy krok
  mieszania oceniany naprawdę. Porównanie P3Net vs kanoniczne P3 odpowiada wprost: *czy surogat pomaga P3 przy
  budżecie 50–350 ewaluacji?*

Dlaczego karta jest potrzebna (v004, R1 §4.1): v004 **nie miało** P3 na prawdziwych ewaluacjach. Ramiona „kanoniczne”
(`bartnik_p3`, `przewozniczek_p3elympus`, `canonical_p3_scalar_fihc`) liczyły każdy krok FIHC i mieszania na lesie
losowym, FIHC robiło jedno przejście z akceptacją „nie gorsze”, przejście przez poziomy było przerywane, nie było
`hashset`. Jedyny test na prawdziwej funkcji (`results/checks/p3_trap_correctness.md`) dotyczył jednokryterialnych
pułapek, nie użycia w eksperymencie.

## 2. Różnice względem P3Net

| Krok | P3Net (zatwierdzone) | Kanoniczne P3 |
|---|---|---|
| P2, P10–P12 (FIHC) | prawdziwe ewaluacje (D-2 a) | bez zmian |
| P20–P25 (mieszanie) | na surogacie, prawdziwa ewaluacja wyniku po każdym poziomie (D-3 b) | **każdy krok, który zmienia rozwiązanie, = jedna prawdziwa ewaluacja** (P22, P25 dosłownie) |
| P5 (awans) | na prawdziwej wartości po poziomie | na prawdziwej wartości (jest zawsze) |
| Reguła poprawy | D-1 b | D-1 b (bez zmian) |
| Surogat | tak | **brak** |

Odstępstw od źródła jest tyle co w P3Net bez O-3: O-1 (kategoryczny genotyp), O-2/D-1 (dwa cele), O-4 (Validity),
O-5 (wynik = H_t). Wszystkie już zatwierdzone.

## 3. Konsekwencja budżetowa (do odnotowania w artykule)

Jedno przejście FIHC kosztuje ≥ Σ(k−1) ewaluacji (JAHS 39, NAS-HPO-II 30, FCNet 25, NB201 24), a każdy klaster w
mieszaniu — do jednej ewaluacji (P25; ~2n−2 klastrów na poziom). Przy b = 50 kanoniczne P3 wykona na JAHS **około
jednej** iteracji P1–P6; przy b = 350 — kilka. To nie jest błąd implementacji, tylko właściwość P3 przy małym
budżecie, i właśnie dlatego jest to dobra ablacja. Oczekiwanie (do prerejestracji, nie do dopasowania): przewaga
P3Net rośnie, gdy budżet maleje.

## 4. Decyzje do podjęcia

### K-1. Implementacja

- **a) Ten sam silnik co P3Net z wymiennym „oceniaczem kroku mieszania”** (prawdziwa ewaluacja albo surogat).
  - Za: różnica między metodami = dokładnie jeden element; błąd w silniku wpływa na obie jednakowo i jest wykrywany
    jednym zestawem testów (W1–W16).
  - Przeciw: P3Net i P3 nie są niezależnymi implementacjami — błąd wspólny nie zostanie wykryty porównaniem; chroni
    przed tym test zgodności z kodem autorów (poziom 2).
- **b) Osobna implementacja.**
  - Za: niezależność.
  - Przeciw: dwa silniki do weryfikacji; różnice w wynikach mogą wynikać z drobnych różnic implementacji, nie z surogatu.

**Rekomendacja: a).**

### K-2. Wyczerpanie budżetu w środku iteracji

- **a) Zatrzymanie natychmiast**; wszystko ocenione do tej chwili jest w H_t (O-5).
  - Za: budżet nigdy nie jest przekroczony; jednakowo dla wszystkich metod.
- **b) Dokończenie iteracji.** Przeciw: przekracza budżet.

**Rekomendacja: a)** (ta sama reguła dla P3Net — do dopisania do protokołu jako wspólna).

### K-3. Miejsce w artykule

- **a) Główna tabela** obok P3Net. Za: to jest bezpośredni dowód, że surogat coś wnosi.
- **b) Suplement.** Przeciw: bez tej ablacji główne twierdzenie („surogat pomaga P3”) nie ma testu.

**Rekomendacja: a).**

## 5. Własności do sprawdzenia testami (poziom 1)

Wszystkie W1–W16 z karty P3Net (z D-3 = „każdy krok prawdziwy”), plus:

| ID | Własność |
|---|---|
| W-K1 | Zero wywołań surogatu; obiekt surogatu nie jest tworzony |
| W-K2 | Każdy krok mieszania, który zmienia rozwiązanie, zużywa dokładnie jedną prawdziwą ewaluację, chyba że genotyp jest już w H_t (wtedy zero — W15) |
| W-K3 | Na tym samym ziarnie P3Net z „surogatem-wyrocznią” (predykcja = prawdziwa wartość, każde wywołanie liczone jako ewaluacja) daje **identyczną trajektorię** jak kanoniczne P3 — dowód, że jedyną różnicą jest surogat |
| W-K4 | Budżet nigdy nie jest przekroczony; przebieg kończy się dokładnie na b ewaluacjach albo wcześniej (K-2 a) |
| W-K5 | Wersja jednokryterialna przechodzi test zgodności poziomu 2 z kodem autorów (pułapki, NK; ±2 %, TOST) |

## 6. Do zatwierdzenia

K-1 (rek. a), K-2 (rek. a, wspólne dla wszystkich metod), K-3 (rek. a), własności W-K1–W-K5.

## 7. Decyzje (2026-10-16)

K-1 a, K-2 a (reguła wspólna dla wszystkich metod — dopisać do `v005-verification-protocol.md`), K-3 a; W-K1–W-K5
przyjęte. Do wykonania: potwierdzić repozytorium kodu autorów P3.
