# Faza 0 — weryfikacja literaturowa: generalizacja eLyMPuS non-monotonicity check na zmienne k-arne

Data: 2026-08-19. Zakres: WebSearch (kilka zapytań, patrz niżej), przegląd `notes/design_space_mechanisms.md`
i `notes/ga_landscape_2026.md` (już w repo), próba wglądu w kod źródłowy `github.com/przewooz/OLyMPuS`.

## Odpowiedź jednoznaczna

**Nie istnieje opublikowana generalizacja non-monotonicity check / eLyMPuS-style partial comparisons na
zmienne k-arne (kategorialne, k>2).** Projektujemy własną (Faza 1), z uzasadnieniem poniżej.

## Co sprawdzono i co znaleziono

1. **WebSearch bezpośrednio na temat**: "non-monotonicity check multi-valued categorical variables
   linkage discovery gray-box optimization", "GOMEA categorical linkage discovery guaranteed non-binary
   alphabet k-ary" — żadne trafienie nie dotyczy non-monotonicity checku na alfabetach >2. Jedyne istotne
   trafienia (RV-GOMEA conditional linkage, fitness-based linkage learning + maximum-clique, arXiv:2402.10757)
   dotyczą zmiennych **ciągłych** (RV-GOMEA), nie kategorialnych k-arnych — inny problem (patrz niżej dlaczego
   to nie jest to samo). Jeden wynik wprost stwierdza: *"the cardinality of variables is a problematic issue,
   and problems with non-uniform cardinality of variables are not usually addressed in gray-box optimization
   methods"* — potwierdzenie z drugiej ręki, że jest to otwarty problem w polu, nie tylko w tej pracy.

2. **Munetomo (oryginalny non-linearity/non-monotonicity check, cytowany przez Przewoźniczka)**: LIMD
   (Linkage Identification by Non-monotonicity Detection) i jego rozszerzenie **LINC-R** (Linkage
   Identification by Nonlinearity Check for **Real-Coded** GAs, Munetomo) — LINC-R jest właśnie precedensem,
   którego szukaliśmy: generalizacja flip-based non-linearity checku na domenę, gdzie "flip" nie ma
   naturalnego odpowiednika (tam: ciągła), robiona przez **losową perturbację o krok** zamiast pojedynczego
   bitowego flipu. To dokładnie analogiczny problem strukturalny do naszego (k-arne: "flip" niejednoznaczny
   bo jest k-1 możliwych przejść), ale rozwiązany dla **innej** przyczyny niejednoznaczności (continuum, nie
   wielowartościowość dyskretna) — więc jest to precedens *metodologiczny* ("jak feed forward non-monotonicity
   check gdy pojedynczy determinowany ruch nie istnieje"), nie gotowa formuła do przeniesienia wprost.

3. **Recursive/differential grouping (referencje [10],[13],[21] z pracy LyMPuS — Komarnicki 2023, Ma 2022,
   Sun 2019)**: potwierdzone WebSearch, że cała rodzina Differential Grouping / Recursive Differential
   Grouping (DG, RDG, ERDG) jest zdefiniowana wyłącznie dla **dużej skali, zmiennych ciągłych**
   (cooperative co-evolution, large-scale continuous optimization) — brak wariantu kategorialnego/k-arnego
   w żadnym ze znalezionych źródeł (2019–2023). Ten sam wzorzec co punkt 2: precedens rozwiązuje "flip nie ma
   naturalnego odpowiednika" dla continuum, nie dla wielowartościowości dyskretnej.

4. **Kod źródłowy `github.com/przewooz/OLyMPuS`**: repozytorium dostępne, ale zawartość spakowana w
   archiwa (`OptFrame.zip`, `exp_POLiNoMok.zip`, `zz_introduction.zip`, `zz_miscellaneous.zip`) —
   niedostępna do wglądu przez WebFetch bez pobrania i rozpakowania (poza zakresem tej sesji, nie ma
   uzasadnienia inwestować w to więcej czasu skoro odpowiedź na pytanie kluczowe — czy istnieje publikowana
   generalizacja — jest już jednoznaczna z punktów 1-3 i z jawnego stwierdzenia autorów w Conclusions, patrz
   niżej). Nie znaleziono żadnej niezależnej wzmianki (recenzji, cytowania, forka) sugerującej k-ary wsparcie.

5. **Jawne stwierdzenie autorów pracy źródłowej** (już wyekstrahowane w planie): *"the proposed mechanisms
   are not limited to the binary search space and apply to integer-based solution encoding... which is a
   future work step"* (Conclusions, s.652) — autorzy sami deklarują to jako **niezrobiony** krok, nie
   odsyłają do żadnej istniejącej pracy, która by to rozwiązywała.

6. **`notes/design_space_mechanisms.md`**: potwierdza (Krok 3, "predyktor relatywny: dwa niezależne
   wymiary") że eLyMPuS jest sklasyfikowany jako "dyskretne porównanie kierunku {lepszy/gorszy/niejednoznaczny},
   bez regresji" z "gwarancją formalną pod założeniem monotoniczności krajobrazu" — wyłącznie w kontekście
   pseudo-Boolowskim; żadna wzmianka o k-arnej generalizacji w istniejących notatkach repo.

7. **`notes/ga_landscape_2026.md`**: potwierdza RV-GOMEA jako jedyny człon rodziny GOMEA/P3 obsługujący
   zmienne poza binarnymi, i to wyłącznie **ciągłe** (ℝ^ℓ), nie kategorialne. Żadna wzmianka o k-arnym
   non-monotonicity checku.

## Wniosek dla Fazy 1

Nie ma gotowej, poprawnej generalizacji do zaadaptowania. Projektujemy własną. Najbliższy metodologiczny
precedens co do *wzorca* rozwiązania (nie formuły) to LINC-R/RDG: gdy pojedynczy zdeterminowany "flip" nie
ma odpowiednika, zastępuje się go **systematycznym przejściem przez wszystkie możliwe alternatywy** danej
zmiennej w danym kontekście, zamiast jednego z góry ustalonego ruchu. To bezpośrednio wspiera Kandydat B
(ranking/porządek k wartości w kontekście) z planu — nie jest to arbitralny wybór, tylko przeniesienie tego
samego wzorca rozwiązania, którym community rozwiązało analogiczny problem strukturalny w innej domenie
(continuum zamiast k-arności), połączone z obserwacją, że FIHC Algorithm 4 w oryginalnej pracy już iteruje
"for all values v in the domain" k-arnie.

## Cytowanie do CHANGELOG / docstringów

- Przewoźniczek, Chicano, Komarnicki, Tinós — "Limited Perfect Monotonical Surrogates Constructed Using
  Low-Cost Recursive Linkage Discovery with Guaranteed Output", GECCO 2026 (`przewozniczek2026lympus`) —
  punkt wyjścia, NIE źródło gotowej k-arnej metody.
- Munetomo — LINC-R (Linkage Identification by Nonlinearity Check for Real-Coded GAs) — metodologiczny
  precedens dla "flip → systematyczna perturbacja/iteracja po alternatywach", cytowany jako uzasadnienie
  wzorca, nie jako źródło formuły.
