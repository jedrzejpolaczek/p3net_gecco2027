# MO-DSA-P3-GOMEA i MO-PSA-P3-GOMEA (Bartnik) — karta źródła

Status: **ZATWIERDZONA** (2026-10-16, autor projektu; decyzje w §9). Konsultacji z promotorem nie będzie
(decyzja autora 2026-10-16): niejasności (§6) przyjmujemy jako założenia i opisujemy w artykule.

> **Czekamy na odpowiedź autorki** — mail z pytaniami N-0–N-4 (bramka DSA, wspólne τ, „generacja”, drzewo powiązań,
> siatki grid searcha, kod i cache energii NB201) wysłany 2026-10-16. Jeśli odpowiedź przyjdzie przed prerejestracją
> v005, zastępuje odpowiednie założenia Z-B#; jeśli nie — założenia zostają i są opisane w artykule.

## 1. Źródła

- **Główne:** N. Bartnik, *Evolutionary optimization of deep neural networks…*, praca magisterska, 2026
  (`bartnik2026evolutionary`). Plik: `notes/articles/NAS/MO-NAS/Evolutionary optimization of deep neural.pdf`.
  Rozdziały: §4.5.4 (Alg. 7–8: SA-P3-GOMEA), §5.2–5.4, §6.3–6.4 (Alg. 9, Eq. 6.1–6.4), §7.1–7.2 (protokół, Tab. 7.1–7.2).
- **Pierwotne:** Dushatskiy, Alderliesten, Bosman, *A Novel Surrogate-assisted Evolutionary Algorithm Applied to
  Partition-based Ensemble Learning*, GECCO'21 (SA-P3-GOMEA). Plik: `notes/articles/linkage learn/A Novel Surrogate-assisted…pdf`.
- **Kod referencyjny:** SAGOMEA (Dushatskiy), `https://github.com/ArkadiyD/SAGOMEA` — jednokryterialny SA-P3-GOMEA; Bartnik
  podaje, że jej baseline'y (MO-GOMEA, MO-LS) pochodzą z tego repozytorium. **Kodu Bartnik nie mamy** (patrz §6, N-0).
- Reguła akceptacji MO-GOMEA (Alg. 6 u Bartnik; `luong2014mogomea`) — ta sama, którą przyjęliśmy w P3Net (D-1 b).

Dlaczego karta (R1 §4.2): `bartnik_p3` z v004 był niewierną rekonstrukcją (FIHC na lesie, bramka na oknie różnic f1
z λ = 0.5, przerywane wspinanie, warm-up n zamiast 100, FLOPs jako f2) i odtwarzał najsłabszy wariant pracy.

## 2. Algorytm wg źródła

Numeracja B# używana w testach i odstępstwach.

### Pętla (Alg. 7, SA-P3-GOMEA, przeniesiona do MO w §5)

- **B1.** Warm-up: losowe rozwiązania oceniane naprawdę → zbiór R. Dushatskiy: n rozwiązań; **Bartnik: 100**
  architektur, wspólny zestaw dla wszystkich wariantów (§7.1.1).
- **B2.** Surogat uczony na R; α = 1; próg = α-kwantyl (B14).
- **B3.** Pusta piramida. Pętla: nowe losowe rozwiązanie → poziom 0 (**bez hill climbera**; Dushatskiy §2.3.4).
- **B4.** Dla każdego poziomu L od 0 do najwyższego: naucz drzewo powiązań poziomu L; o ← GOM(p, poziom L) z oceną
  bramkowaną (B10); jeśli `Compare(o, p)` woli o → dodaj o do L+1, p ← o. **Wspinanie przez wszystkie poziomy**.
- **B5.** Po iteracji: jeśli archiwum się nie zmieniło → α ← α·γ, γ = 0.999 (MO: zmiana archiwum zastępuje
  „nowego najlepszego”, §6.4.2); jeśli się zmieniło → α ← 1.
- **B6.** Surogat przeuczany po każdej prawdziwej ewaluacji; próg przeliczany.
- **B7.** Stop: budżet 500 prawdziwych ewaluacji **albo** 1000 kolejnych iteracji zewnętrznych bez nowej prawdziwej
  ewaluacji („exploration collapse”, §6.3).

### GOM i akceptacja (Alg. 2, 6, 8, 9)

- **B8.** Dla każdego zbioru F z FOS (losowa kolejność): dawca losowy z bieżącego poziomu, **różniący się od o na F**
  (Alg. 9 l. 3); skopiuj d_F do o.
- **B9.** Jeśli o się zmieniło: oceń surogatem.
- **B10.** Bramka prawdziwej ewaluacji (Alg. 8): jeśli predykcja przekracza próg T → prawdziwa ewaluacja, dopisanie do R.
- **B11.** `Compare(x, y)`: na prawdziwych wartościach, gdy oba je mają; inaczej na predykcjach (Alg. 8).
- **B12.** Akceptacja zmiany w GOM — **PSA** (Alg. 9): p_keep = P(o ≻ b), p_revert = P(b ≻ o) z Eq. 6.1; do historii
  dopisz max(p_keep, p_revert); cofnij, jeśli p_revert ≥ τ i p_revert > p_keep.
- **B13.** Eq. 6.1: P(new ≻ old) = Φ((μa_new − μa_old)/√(σa_new² + σa_old²)) · Φ((μe_old − μe_new)/√(σe_new² + σe_old²));
  dla członków archiwum σ = 0; przy σ = 0 czynnik jest skokiem 0/1.
- **B14.** Próg: **DSA** — α-kwantyl predykcji surogatu dla rozwiązań z prawdziwą wartością (Alg. 7–8); **PSA** —
  τ = α-kwantyl wszystkich zaobserwowanych prawdopodobieństw dominacji (Eq. 6.2).
- **B15.** Archiwum: ścisła dominacja (Eq. 4.7); dodanie usuwa zdominowanych.

### Surogaty (§5.3, §6.3–6.4)

- **B16.** Dwie konfiguracje: wspólny model (a, e) albo **osobny model na cel** (per-obj).
- **B17.** DSA: SVR, MLP, RF, GBoost. PSA: RF (σ = odchylenie między drzewami), GBoost (σ z kwantyli 16/84), MLP
  (MC dropout), GP (per-obj).
- **B18.** Hiperparametry: grid search przy pierwszym treningu danego typu, ocena R² w 3-krotnej CV; potem stałe.
- **B19.** (Wariant „online selection”) co 25/50/100 ewaluacji wybór typów z puli wg Spearmana na holdoucie
  (ostatnia 1/5 archiwum, ≥ 10 punktów), od 30 punktów archiwum.

## 3. Parametry wg źródła

| Parametr | Bartnik | Uwagi |
|---|---|---|
| Warm-up | 100 (wspólny zestaw) | Dushatskiy: n |
| γ (relaksacja) | 0.999 w tabeli głównej; badane też 0.99, 0.9 i per oś | §7: 0.9 lepsze dla DSA; per oś najlepsze |
| Budżet | 500 | NB201 = 15 625 architektur |
| Stop dodatkowy | 1000 iteracji bez nowej ewaluacji | |
| Seedy | 10 (42–51) | |
| Cele | dokładność CIFAR-10 (NB201) i zmierzona energia GPU (inferencja / trening 1 epoki) | FLOPs odrzucone (ρ = 0.749) |

## 4. Odstępstwa wymagane przez nasz problem

| # | Krok | Odstępstwo | Powód | Status |
|---|---|---|---|---|
| O-B1 | całość | Uruchomienie także na JAHS, NAS-HPO-II, FCNet (praca: tylko NB201) | protokół — wszystkie metody na wszystkich przestrzeniach | do zatwierdzenia |
| O-B2 | cele | f1 = nasz błąd, f2 = nasz koszt (na NB201: własny pomiar energii, #28 C); oba **przewidywane** | #6 (nikt nie dostaje f2) — zgodne z pracą (tam też oba przewidywane) | do zatwierdzenia |
| O-B3 | B1, B7 | Budżet 50–350 zamiast 500; warm-up wg B-2 | wspólny protokół | wg B-2 |
| O-B4 | B7 | Stop po budżecie wg reguły wspólnej (natychmiast, K-2) | protokół, decyzja 4 | zatwierdzone (wspólne) |

## 5. Decyzje do podjęcia

### B-1. Które warianty odtwarzamy

- **a) MO-DSA RF per-obj + MO-PSA RF per-obj.**
  - Za: ta sama klasa modelu co surogat P3Net (S-4 a) — porównanie z P3Net izoluje **mechanizm** (bramka vs zastąpienie,
    model bezwzględny vs względny), nie model; MO-PSA RF per-obj należy do najlepszych w pracy (142.53 / 353.72 HV).
  - Przeciw: MO-DSA RF per-obj jest u Bartnik słaby (nie bije MO-LS na inferencji) — recenzent może zarzucić wybór
    słabego wariantu; łagodzi to obecność MO-PSA.
- **b) Najlepsze warianty z Tab. 7.1:** MO-DSA MLP per-obj + MO-PSA MLP per-obj (inferencja) / GBoost per-obj (trening).
  - Za: „najlepsze, co autorka zgłosiła”.
  - Przeciw: najlepszy różni się między problemami; MLP wg samej pracy niestabilny (MC dropout nie śledzi błędu,
    142.40 vs 140.79 między kampaniami); miesza model z mechanizmem.
- **c) Wszystkie 16 + online selection.** Przeciw: koszt; to replikacja pracy, nie baseline.

**Rekomendacja: a)**; w artykule zdanie, że u Bartnik najlepsze były warianty probabilistyczne i MLP, i że MO-PSA RF
per-obj jest wśród nich.

### B-2. Warm-up przy budżecie 50–350

- **a) Proporcjonalnie: 20 % budżetu** (100/500 jak u Bartnik): 10 / 20 / 70 przy b = 50 / 100 / 350.
  - Za: zachowuje stosunek z pracy; wykonalne przy każdym budżecie.
  - Przeciw: liczba nie pochodzi wprost ze źródła.
- **b) n (jak Dushatskiy):** 6–10.
  - Za: wierne SA-P3-GOMEA. Przeciw: niewierne Bartnik; przy 6–10 punktach grid search z 3-krotną CV jest niestabilny.
- **c) 100 (jak Bartnik).** Przeciw: niewykonalne przy b = 50, przy b = 100 nie zostaje nic na wyszukiwanie.

**Rekomendacja: a).**

### B-3. γ (relaksacja bramki)

- **a) 0.999** — konfiguracja tabeli głównej. Za: wierne. Przeciw: przy ≤ 350 ewaluacjach α prawie nie spada; sama
  praca pokazuje, że 0.999 to najgorsze ustawienie dla DSA.
- **b) 0.9 dla obu.** Za: najlepsze wspólne γ dla DSA wg pracy. Przeciw: wybór pod wynik.
- **c) Per oś (najlepsze w pracy).** Przeciw: dodatkowy parametr do wyboru; ryzyko dopasowania.

**Rekomendacja: a)** jako wierne (wartość z głównej tabeli), z wynikami dla 0.9 w suplemencie jako analiza wrażliwości.

### B-4. Grid search hiperparametrów (B18)

Praca nie podaje siatek. **a)** wziąć siatki z kodu autorki (N-0); **b)** jeśli kod niedostępny — siatki własne,
zapisane w karcie przed uruchomieniem, jednakowe dla DSA i PSA. **Rekomendacja: a), awaryjnie b).**

## 6. Niejasności źródła i przyjęte założenia

Źródło nie rozstrzyga poniższych punktów, a kodu autorki nie mamy. Przyjmujemy założenia (Z-B#) i **opisujemy je w
artykule** (suplement, sekcja „Reimplementation of MO-SA-P3-GOMEA”: „the thesis does not specify X; we assume Y”).

| # | Niejasność | Założenie | Uzasadnienie |
|---|---|---|---|
| N-0 | Brak kodu MO-DSA/MO-PSA i cache energii NB201 | **Z-B0:** implementacja własna wg opisu; siatki grid searcha własne (B-4 b), zapisane przed uruchomieniem; test poziomu 2 tylko vs SAGOMEA (jednokryterialnie) | jedyne dostępne źródło kodu |
| N-1 | Co progowane w bramce **MO-DSA** przy dwóch celach: Alg. 8 progował skalarną predykcję, §5.4 — prawdopodobieństwo dominacji przez archiwum, które przy σ = 0 jest 0/1 (kwantyl zdegenerowany) | **Z-B1:** reguła z §5.4 z σ = 0: prawdziwa ewaluacja, gdy **żaden członek archiwum nie dominuje predykcji** kandydata; α w DSA steruje wyłącznie akceptacją w GOM | §5.4 to jedyna reguła MO podana wprost; przy σ = 0 redukuje się do niezdominowania (B13) |
| N-1 (zmiana 2026-10-18) | Z-B1 w praktyce: predykcje lasu leżą blisko średniej i prawie zawsze są zdominowane przez front, a bramka nie ma relaksacji — MO-DSA kończył się po rozgrzewce (10/50 ewaluacji, test W-B13) | **Z-B1′ (zastępuje Z-B1, decyzja autora):** bramka z Alg. 8 osobno dla każdego celu — prawdziwa ewaluacja, gdy na **obu** celach predykcja jest lepsza niż (1 − α)-kwantyl predykcji dla rozwiązań ocenionych naprawdę (minimalizacja; α = 1 → lepsza od wszystkich); α luzuje się jak w B5 | bezpośrednie przeniesienie Alg. 8 na dwa cele; Bartnik bada bramki „per oś” (§7, rozdz. 8.2); zachowuje relaksację progu |
| N-2 | Czy bramka (B10) i akceptacja w GOM (B12) w PSA dzielą τ i historię | **Z-B2:** tak — jedno τ, jedna historia prawdopodobieństw | §6.4.1: „this probability acceptance rule is used in two points” |
| N-3 | „Generacja” w B5 | **Z-B3:** jedna iteracja zewnętrzna (jedno nowe rozwiązanie wspina się po piramidzie) | w P3 nie ma generacji; Alg. 7 l. 23 relaksuje „during this iteration” |
| N-4 | Miara i metoda budowy drzewa powiązań | **Z-B4 (rozstrzygnięte z kodu SAGOMEA, 2026-10-21):** `FOS.cpp` LTFOS, domyślnie `similarityMeasure = 1` = znormalizowane MI = (H(X)+H(Y))/H(X,Y) − 1 = **1 − D** odległości entropijnej P3; UPGMA przez łańcuch najbliższych sąsiadów; filtr: przy podobieństwie ≥ 1 − 1e-6 (D ≈ 0) dzieci odrzucane (= P16); `orderFOS = 1` rosnąco po rozmiarze (= P17). Nasza implementacja (odległość entropijna P3) jest więc zgodna. | Bartnik: „uses same mechanisms as original SA-P3-GOMEA” (§5.5) |

Ryzyko: Z-B1 może nie odpowiadać temu, co autorka zaimplementowała; jeśli nasz MO-DSA wyjdzie wyraźnie inaczej niż w
Tab. 7.1, nie wolno tego przypisać metodzie — tylko naszej interpretacji.

## 7. Własności do sprawdzenia testami (poziom 1)

| ID | Krok | Własność |
|---|---|---|
| W-B1 | B3 | Brak hill climbera; nowe rozwiązanie trafia od razu na poziom 0 |
| W-B2 | B1 | Warm-up wg B-2, wszystkie oceniane naprawdę, przed pierwszym treningiem |
| W-B3 | B4 | Wspinanie przez wszystkie poziomy; awans tylko gdy `Compare` woli o |
| W-B4 | B8 | Dawca różni się od o na F, jeśli taki istnieje na poziomie |
| W-B5 | B10 | Prawdziwa ewaluacja wtedy i tylko wtedy, gdy predykcja przechodzi próg |
| W-B6 | B11 | `Compare` używa prawdziwych wartości, gdy oba je mają |
| W-B7 | B5 | α = 1 na starcie; ×γ po iteracji bez zmiany archiwum; reset do 1 przy zmianie |
| W-B8 | B13 | Eq. 6.1 zgodne z wartościami ręcznymi; przy σ = 0 redukuje się do skoku 0/1 |
| W-B9 | B12 | Cofnięcie wtedy i tylko wtedy, gdy p_revert ≥ τ i p_revert > p_keep; historia rośnie o max(p_keep, p_revert) |
| W-B10 | B14 | Próg = α-kwantyl właściwej historii (DSA: predykcje ocenionych; PSA: prawdopodobieństwa) |
| W-B11 | B6 | Surogat przeuczany po każdej prawdziwej ewaluacji |
| W-B12 | B7 | Stop po 1000 iteracjach bez nowej ewaluacji (zapisany powód zatrzymania) |
| W-B13 | B16 | Per-obj: dwa niezależne modele; f2 nie jest odczytywane z benchmarku dla nieocenionych |

**Test zgodności (poziom 2):** jeśli dostaniemy cache energii (N-0) — MO-PSA RF per-obj na NB201 z jej danymi, budżet
500, 10 seedów; kryterium: średnie HV w ±2 % wartości z Tab. 7.1 (142.53 / 353.72) i TOST. Bez cache — tylko poziom 1 +
porównanie z SAGOMEA w wersji jednokryterialnej (bez PSA). Kryterium zapisane przed testem.

## 8. Do zatwierdzenia

O-B1, O-B2; B-1 (rek. a), B-2 (rek. a), B-3 (rek. a + 0.9 w suplemencie), B-4 (b — kodu brak); założenia
Z-B0–Z-B4; W-B1–W-B13; kryterium poziomu 2.

## 9. Decyzje (2026-10-16)

O-B1, O-B2 zatwierdzone; B-1 a (MO-DSA i MO-PSA, RF per-obj); B-2 a (warm-up 20 % budżetu); B-3 a (γ = 0.999, γ = 0.9
w suplemencie); B-4 b (siatki własne, zapisane przed uruchomieniem); założenia Z-B0–Z-B4 przyjęte do czasu ewentualnej
odpowiedzi autorki; W-B1–W-B13 i kryterium poziomu 2 przyjęte.
