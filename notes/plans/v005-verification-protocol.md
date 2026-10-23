# v005 — protokół weryfikacji implementacji (A0)

Status: **PRZYJĘTY** (2026-10-16). Decyzje autora: protokół pełny; weryfikują autor + niezależny agent; szczegóły w „Decyzje”.
Cel: zapobiec przyczynom Z1–Z5 i Z8 (`notes/plans/v005-plan.md`): kod, testy i tekst nie mogą pochodzić z tej samej
niesprawdzonej intencji.

## 1. Role

| Rola | Kto | Widzi | Odpowiada za |
|---|---|---|---|
| Autor karty źródła | agent implementujący | źródło (PDF, kod referencyjny) | karta źródła (§2) |
| Zatwierdzający kartę | **autor projektu** | źródło + karta | zgodność karty ze źródłem; akceptacja odstępstw |
| Autor testów ze źródła | **niezależny agent** (osobna sesja) | karta + publiczny interfejs metody (`propose`/`update`, konfiguracja), **bez implementacji** | testy poziomu 1 (§3) |
| Implementujący | agent implementujący | karta + testy | kod przechodzący testy, bez zmiany testów |
| Przegląd końcowy | autor projektu | wszystko | akceptacja „definicji ukończenia” (§7) |

Zmiana testu poziomu 1 wymaga zmiany karty i ponownego zatwierdzenia — implementujący nie może dopasować testu do kodu.

## 2. Karta źródła (`notes/plans/v005-sources/<metoda>.md`)

```
# <metoda> — karta źródła
Źródło: <publikacja / kod referencyjny + wersja / commit>, plik w repo: <ścieżka>
## Algorytm wg źródła
<pseudokod lub cytaty z numerami stron/linii; każdy krok ponumerowany S1, S2, …>
## Parametry wg źródła
| parametr | wartość w źródle | wartość u nas | uzasadnienie różnicy |
## Odstępstwa (świadome)
| # | krok | odstępstwo | powód | wpis w v005-decisions.md |
## Własności do sprawdzenia testami
W1. <własność wynikająca z kroku Sx, sprawdzalna testem>
…
## Zdania artykułu opisujące tę metodę
<cytaty + ID w v005-claims.md>
```

Wymagane dla: P3Net S6, kanoniczne P3 (z prawdziwymi ewaluacjami i surogatowe), Bartnik MO-DSA i MO-PSA, eLyMPuS,
NSGA-Net, NSGANetV2, SH-EMOA, MO-BOHB, Hyperband, ASHA, BOHB, BANANAS, REINFORCE, RegEvo, MO-LS, SMAC3, TPE, NSGA-III,
MOEA/D, Vizier, qNEHVI, qParEGO, RS. Dla adapterów bibliotecznych karta opisuje konfigurację i ustawienia domyślne
biblioteki (z odnośnikiem do kodu biblioteki w danej wersji).

## 3. Poziomy testów

| Poziom | Co sprawdza | Przykłady (z błędów v004) | Kto pisze |
|---|---|---|---|
| 1. Testy ze źródła | Własności W1… z karty, na małych problemach o znanej odpowiedzi | FOS nie zawiera korzenia, zawiera singletony; dawca różni się w F; FIHC kończy w lokalnym optimum; bramka Bartnik startuje od α=1 | niezależny agent |
| 2. Zgodność z referencją | Nasz adapter vs kod referencyjny na wspólnym problemie; kryterium zapisane **przed** testem (np. mediana HV ±5%, 10 seedów) | NSGA-Net vs optuna (istnieje); SH-EMOA/MO-BOHB vs `automl/multi-obj-baselines`; Bartnik vs Tabela 7.1 | implementujący, kryterium zatwierdza autor |
| 3. Integracja na produkcji | Każda metoda × każda przestrzeń × {najmniejszy, największy budżet}, 1 seed | MOEA/D na FCNet b=350; SMAC3 na JAHS b=50 | automatycznie (`checks`) |
| 4. Asercje w trakcie przebiegu | Własności mechanizmów sprawdzane na żywych danych | surogat P3Net: odsetek par < 100%; SMAC3: projekt początkowy ≤ 25% budżetu; brak no-opów liczonych do κ; hook f2 nieobecny | w kodzie metod, raport w diagnostykach |
| 5. Kontrola po przebiegu | Każdy plik wyniku | `evaluations_used == budget` (tor główny); pola zasobów niepuste; komplet plików z listy prerejestracji | `checks` po etapie |

## 4. Tabela „zdanie ↔ test” (`notes/plans/v005-claims.md`)

| ID | Zdanie (artykuł, sekcja) | Metoda | Test(y) | Status |
|---|---|---|---|---|
| C-xx | „…” | … | `tests/...::test_...` | ✅ / ❌ |

Każde zdanie opisujące działanie metody musi mieć test, który nie przeszedłby, gdyby zdanie było fałszywe. Zdanie bez
testu nie trafia do artykułu (albo dostaje sformułowanie ostrożne i wpis „niesprawdzalne testem” z uzasadnieniem).

## 5. Bramka w pipeline

Etap `checks` w `scripts/run_pipeline.py` przed pierwszym etapem siatki:
1. testy poziomów 1–2 (pytest) — zielone;
2. poziom 3 (integracja) — zielony;
3. determinizm (istniejący mechanizm) — zielony;
4. test zasobów przy największym budżecie na docelowej maszynie (A8) — mieści się w limicie;
5. wszystkie karty źródeł zatwierdzone, wszystkie wpisy `v005-claims.md` mają test.

Niepowodzenie dowolnego punktu blokuje start siatki. Po każdym etapie siatki — kontrola poziomu 5; alarm zatrzymuje kolejny etap.

## 6. Lista „zobowiązanie → skrypt → plik”

Każdy punkt prerejestracji v005 (analizy główne i drugorzędne, retrening, pomiary) ma: właściciela, termin, skrypt,
oczekiwany plik wyniku. Brak pliku po terminie = alarm i wpis do §7 prerejestracji w dniu wykrycia.

## 7. Definicja ukończenia metody

- [ ] karta źródła zatwierdzona;
- [ ] odstępstwa wpisane w `v005-decisions.md`;
- [ ] testy poziomu 1 (niezależne) zielone;
- [ ] zgodność z referencją (poziom 2) spełniona albo odstępstwo uzasadnione;
- [ ] integracja (poziom 3) zielona na wszystkich przestrzeniach;
- [ ] asercje (poziom 4) obecne;
- [ ] zdania artykułu o metodzie mają testy.

## 8. Kolejność prac

1. Akceptacja tego protokołu i `v005-decisions.md`.
2. Karty źródeł: najpierw P3Net S6, kanoniczne P3, Bartnik (największe zmiany), potem baseline'y.
3. Testy poziomu 1 (niezależny agent) → implementacja → poziomy 2–4.
4. `checks` + test zasobów → prerejestracja v005 → przebieg.

## Decyzje (2026-10-16)

1. **Testy poziomu 1 pisze niezależny agent dla wszystkich metod** (także adapterów bibliotecznych).
2. **Kryterium zgodności z referencją (poziom 2):** domyślnie ±2% mediany HV + test równoważności (TOST) na **100 seedach** (zmiana 2026-10-19; było 20–30 — za mała moc),
   na problemie syntetycznym i na NAS-HPO-Bench-II; tam, gdzie źródło podaje własne liczby (Bartnik, eLyMPuS), kryterium
   ustalone w karcie źródła. Każde kryterium zapisane przed testem.
3. **Karty źródeł eLyMPuS i Bartnik zatwierdza autor projektu.** Zmiana 2026-10-16: konsultacji z promotorem nie będzie —
   niejasności źródeł przyjmujemy jako założenia (Z-#) w karcie i opisujemy w artykule jako wynikające z braku źródeł.
4. **Budżet wspólny dla wszystkich metod** (karta `p3-canonical.md`, K-2 a): metoda zatrzymuje się natychmiast po b-tej
   prawdziwej ewaluacji, także w środku iteracji; wszystko ocenione do tej chwili jest w H_t; budżet nigdy nie jest
   przekroczony. Test poziomu 1 dla każdej metody.
