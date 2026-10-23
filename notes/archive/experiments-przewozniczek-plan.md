# Plan: `experiments-przewozniczek` — eLyMPuS/OLyMPuS class adapted to NAS-Bench-201

## Cel

Przewoźniczek et al.'s `eLyMPuS`/`OLyMPuS` (`przewozniczek2026lympus`, GECCO 2026) nigdy nie był testowany na
NAS — tylko na syntetycznych problemach kombinatorycznych, **binarnych/pseudo-Boolowskich** (Bim10, Dec5, NK,
Ising, Max3Sat). To nie jest replikacja czyjegoś eksperymentu NAS-owego (jak `experiments-bartnik`) — to
**nowy, oryginalny test**, wymagający własnej adaptacji mechanizmu do 5-wartościowych zmiennych kategorialnych
(operacje na krawędziach komórki). Ten dokument traktuje tę adaptację jako główne ryzyko projektu i poświęca
jej osobną, wczesną fazę weryfikacji — zgodnie z wyraźnym życzeniem, żeby była dobrze udokumentowana i
sprawdzona, nie zaimplementowana naiwnie.

## Reużywalność (identyczna baza jak `experiments-bartnik`)

Search space (`nas_bench_201_genotype.py`), substrat (`nas_bench_201.py`), cały zestaw baseline'ów P3Net,
`stats/significance.py`, `reporting/`, `p3net.problem.*`, `p3net.harness.*`, `p3net.metrics.*` — patrz
`experiments-bartnik-plan.md` §"Zweryfikowany stan reużywalności", identycznie tutaj. Różnica leży wyłącznie w
nowym silniku optymalizacji, nie w harnessie wokół niego.

## Rdzeń problemu: eLyMPuS jest zdefiniowany dla zmiennych binarnych

Z przeczytanej w całości pracy (`Limited Perfect Monotonical Surrogates...`, GECCO'26):

- Podstawowa operacja to **flip** ($x_g \to \bar{x_g}$) — dla zmiennej binarnej to jedyna możliwa zmiana.
  Dla NAS-Bench-201 każda krawędź ma **5** możliwych operacji (`none`, `skip_connect`, `nor_conv_1x1`,
  `nor_conv_3x3`, `avg_pool_3x3`), więc "flip" nie ma jednoznacznego odpowiednika — zmiana $x_g$ może iść do
  jednej z **4** innych wartości, nie jednej.
- Funkcja $b(x_g, \phi, \mathbf{x}) \in \{\{0\},\{1\},\{0,1\}\}$ (Eq. 2) porównuje **dokładnie dwie** wartości
  $x_g$ (0 vs 1) w danym kontekście $\phi$. Dla $k=5$ potrzeba porównania $\binom{5}{2}=10$ par wartości, albo
  pełnego uporządkowania 5 wartości — obie opcje są nowym projektem, nie mają gotowego odpowiednika w pracy.
- Non-monotonicity check (klauzule C1-C6, §2) jest zdefiniowany przez pojedyncze flipy $x^g$, $x^h$, $x^{g,h}$.
  Dla zmiennych $k$-arnych trzeba zdefiniować, **względem której pary wartości** (nie tylko której pary
  zmiennych) sprawdzana jest zależność — sam artykuł explicite tego nie robi.
- Autorzy sami stwierdzają (Conclusions, s.652): *"the proposed mechanisms are not limited to the binary
  search space and apply to integer-based solution encoding... which is a future work step"* — czyli **nie
  jest to rozwiązany problem w literaturze źródłowej**, tylko zadeklarowany kierunek.

To NIE dotyczy całego silnika — `linkage_tree.py`/optimal mixing (GOM, używane też w tym projekcie dla P3Net)
z natury działa na dowolnym skończonym alfabecie przez wzajemną informację (entropijną), nie zakłada
binarności; oryginalna praca LTGA (Thierens 2010, cytowana przez Przewoźniczka) jest zdefiniowana ogólnie.
Problem dotyczy **specyficznie** mechanizmu eLyMPuS (partial comparisons + non-monotonicity check +
gwarantowane odkrywanie linkage) — to jest jądro tej pracy i jądro adaptacji.

## Faza 0 — Weryfikacja literaturowa PRZED jakąkolwiek implementacją

To musi być zrobione i udokumentowane zanim powstanie jakikolwiek kod adaptujący, żeby nie "wymyślać koła na
nowo" niepoprawnie ani nie przeoczyć istniejącego, poprawnego rozwiązania:

1. **WebSearch/przeszukanie literatury** za frazami typu: "non-monotonicity check multi-valued variables",
   "gray-box optimization non-binary alphabet", "GOMEA categorical linkage discovery guaranteed",
   "generalized non-linearity check k-ary", cytowania cytujące `munetomo1999linkage` (oryginalna
   non-linearity/non-monotonicity check) w kontekście nie-binarnym. Cel: sprawdzić, czy istnieje już
   opublikowana, poprawna generalizacja non-monotonicity check na zmienne $k$-arne, zanim zaprojektujemy
   własną.
2. Sprawdzić `notes/design_space_mechanisms.md` i `notes/ga_landscape_2026.md` (już w repo) pod kątem
   wcześniej znalezionych wskazówek o generalizacji — te notatki już dotykały tematu eLyMPuS vs P3Net.
3. Przeczytać uważnie referencje [10],[13],[21] z pracy LyMPuS (Komarnicki 2023, Ma 2022, Sun 2019 —
   "recursive/differential grouping", "overlapping decomposition") — to są prace o wykrywaniu zależności w
   przestrzeniach **ciągłych**, gdzie "flip" też nie ma naturalnego odpowiednika i community już musiało
   rozwiązać analogiczny problem (tam: perturbacja o krok $\delta$ zamiast flip) — potencjalnie najbliższy
   precedens metodologiczny do zacytowania i zaadaptować analogię.
4. Wyjście fazy: krótki, spisany research note (`notes/lympus-nas-adaptation-literature.md`) z jednoznaczną
   odpowiedzią: "generalizacja X istnieje w literaturze Y, adaptujemy ją" **albo** "nie istnieje, projektujemy
   własną, tu jest uzasadnienie" — obie odpowiedzi są akceptowalne, ale musi być udokumentowane które.

## Faza 1 — Projekt generalizacji (zależny od wyniku Fazy 0)

Dwa kandydackie projekty do rozstrzygnięcia w Fazie 0/1 (nie wybierane z góry w tym dokumencie):

**Kandydat A — per-przejście (directed value-transition), granularniejszy**
Każda para (zmienna, wartość docelowa) traktowana jak osobny "ruch" — dla $x_g$ z 5 wartościami, 4 możliwe
ruchy z bieżącej wartości. Non-monotonicity check sprawdzany per konkretna para przejść (np. "$x_g: a\to a'$"
vs "$x_h: b\to b'$"), analogicznie do oryginalnych klauzul C1-C6, ale sparametryzowanych wartościami docelowymi,
nie tylko zmiennymi. Wada: kombinatorycznie więcej par do sprawdzenia ($O(k^2)$ zamiast $O(1)$ per para
zmiennych) — kwestia czy to nadal jest "low-cost" w duchu oryginalnej pracy.

**Kandydat B — ranking/porządek wartości w kontekście**
$b(x_g, \phi, \mathbf{x})$ generalizuje się do zwracania częściowego porządku (lub pełnego rankingu) $k$
wartości domeny $x_g$ w danym kontekście $\phi$, zbudowanego z $k-1$ porównań względem obecnej wartości
(mirror FIHC's Algorithm 4, który **już** iteruje "for all values v in domain" — to jest naturalne
rozszerzenie istniejącego mechanizmu FIHC, nie nowy wymysł). Non-monotonicity check wykrywa zależność, gdy
porządek zmienia się między dwoma kontekstami $\phi$ różniącymi się wartością innej zmiennej.
Zaleta: FIHC (Algorithm 4) w oryginalnej pracy **już jest zdefiniowany $k$-arnie** ("for all values $v$ in
the domain of $x_i$") — to sugeruje, że autorzy mieli w głowie generalizację bliższą kandydatowi B.

**Rekomendacja robocza (do potwierdzenia po Fazie 0)**: Kandydat B, bo mniej ingeruje w strukturę FFE-cost
rachunku artykułu (Section 3.3 podaje dokładne koszty FFE dla RecursiveLL zakładając $O(\log_2 |C|)$ — trzeba
sprawdzić, czy ten rachunek przeżywa generalizację, czy trzeba go przeliczyć na nowo dla $k$-arnych domen).

## Faza 2 — Implementacja + walidacja na SYNTETYCZNYCH problemach $k$-arnych (nie na NAS jeszcze)

Krytyczne zgodnie z instrukcją "dobrze udokumentowane i sprawdzone": **nie wolno** wdrażać wprost na NAS bez
wcześniejszej walidacji na znanych, kontrolowanych problemach — dokładnie tak jak sama praca LyMPuS najpierw
waliduje na Bim10/Dec5/NK/ISG/Max3Sat, zanim cokolwiek twierdzi.

- Zaprojektować/dobrać **$k$-arny odpowiednik** jednego z jej testowych problemów o znanej strukturze
  zależności — np. $k$-arny bimodalny deceptive function (uogólnienie Eq. 1, $bim_k$, na alfabet $\{0,...,K-1\}$
  zamiast $\{0,1\}$) lub $k$-arny NK-landscape (NK z natury już jest zdefiniowany dla dowolnego alfabetu w
  oryginalnej literaturze Kauffmana — sprawdzić czy `nkLand` w kodzie Przewoźniczka (github.com/przewooz/OLyMPuS,
  wspomniany w pracy) już to obsługuje, zanim pisać od zera).
- Zaimplementować generalizowany eLyMPuS (`p3net`-independent moduł, bo to nie jest NAS-specific — kandydat na
  `lib/src/p3net/surrogates/` **lub** osobny pakiet, do ustalenia) z testami potwierdzającymi:
  1. Gwarancja poprawności: jeśli $eG = G$ (pełen graf zależności), `PartialComparison` zawsze zwraca poprawny
     wynik (mirror Theorem 1 z pracy, przetestowane empirycznie na znanym $G$).
  2. Gwarancja odkrywania linkage: brakująca zależność zostaje znaleziona w ograniczonej liczbie kroków (mirror
     Theorem 2) — zmierzyć rzeczywistą złożoność dla wybranego kandydata A/B i porównać z teoretycznym
     $O(\log_2 n)$ z oryginału (może się zmienić przy generalizacji — udokumentować rzeczywisty wynik, nie
     zakładać że się nie zmienia).
  3. FFE-savings: powtórzyć analog Table 4 z jej pracy (% ewaluacji oszczędzonych przez eLyMPuS) na wybranym
     syntetycznym $k$-arnym problemie, jako dowód że mechanizm faktycznie coś oszczędza po generalizacji, nie
     tylko że się nie wywala.
- Wyjście fazy: `notes/lympus-nas-adaptation-validation.md` — wyniki walidacji syntetycznej, decyzja
  go/no-go przed przejściem do NAS.

## Faza 3 — FIHC-eLyMPuS + populacja pyramidowa (P3-eLyMPuS, nie od razu pełny OLyMPuS)

Jej Table 5 pokazuje **P3-eLyMPuS jako drugi najskuteczniejszy** wariant (po autorskim OLyMPuS, przed
P3-FIHCwLL) — i jest strukturalnie prostszy niż OLyMPuS (brak PXrLL, brak ILS-like perturbation step, brak
circuit-based dodatkowej detekcji). **Rekomendacja: zacząć od P3-eLyMPuS, nie OLyMPuS**, żeby ograniczyć
liczbę nowych, niesprawdzonych mechanizmów naraz (generalizacja $k$-arna + OLyMPuS-specific PXrLL/ILS naraz to
zbyt duże ryzyko błędu w jednym kroku).

- `FIHC-eLyMPuS` (Algorithm 4/Pseudocode 4) z generalizowanym $k$-arnym `PartialComparison` z Fazy 2.
- Silnik populacji: **ta sama kanoniczna, pojedynczy-osobnik-climbing piramida co w `experiments-bartnik`**
  (P3 Algorithm 3 Goldmana) — FIHC-eLyMPuS **zastępuje** zwykły FIHC jako krok lokalnego przeszukiwania
  wewnątrz piramidy. To realne, bezpośrednie źródło reużycia między `experiments-bartnik` i
  `experiments-przewozniczek`: **jeśli `CanonicalPyramid` z planu Bartnik powstanie jako reużywalny moduł
  (nie eksperyment-specific), oba projekty go współdzielą**, różniąc się tylko krokiem lokalnego
  przeszukiwania (zwykły FIHC + surogat absolutny RF vs FIHC-eLyMPuS).
- Testy: smoke test na syntetycznym problemie z Fazy 2, potem na realnych danych NAS-Bench-201 (mały budżet).

## Faza 4 — Konfiguracja + wiring + eksperyment (identyczne z `experiments-bartnik`)

- `configs/methods/przewozniczek_p3elympus.yaml`, wpis w `build_method`.
- Ten sam baseline set co P3Net (nie jej MO-LS/MO-P3-GOMEA), te same budżety/seedy ($R=30$, $\{100,350\}$),
  ten sam orkiestracyjny skrypt (mirror `run_nas_bench_201_isolation.py`).

## Faza 5 — Jawnie poza zakresem v1

- Pełny OLyMPuS (PXrLL, ILS-like perturbation, circuit-based missing-linkage detection) — realny kolejny krok
  po potwierdzeniu, że P3-eLyMPuS w ogóle działa poprawnie po generalizacji.
- Odkrywanie zależności niesymetrycznych (directional dependencies, C4-C6) — praca explicite je obsługuje, ale
  to dodatkowa złożoność nieplanowana w v1.
- Kandydat B vs A pozostawiony otwarty do rozstrzygnięcia w Fazie 0/1, nie przesądzony w tym dokumencie.

## Ryzyko i uczciwość naukowa

To jest **oryginalny wkład metodologiczny** (generalizacja eLyMPuS na $k$-arne domeny), nie odtworzenie
istniejącego wyniku — inaczej niż `experiments-bartnik`. Wymaga to:
- Jawnego opisania generalizacji jako własnej decyzji projektowej z uzasadnieniem (nie "tak zrobił
  Przewoźniczek", bo on tego nie zrobił dla NAS/$k$-arnych domen).
- Cytowania oryginalnej pracy (`przewozniczek2026lympus`) precyzyjnie jako punktu wyjścia, nie jako źródła
  gotowej metody dla tego przypadku.
- Jeśli wynik na NAS wypadnie negatywnie (brak separacji od `random_search`, jak w pozostałych eksperymentach
  tego projektu), to jest to poprawny, publikowalny wynik — ale z zastrzeżeniem, że nie można jednoznacznie
  odróżnić "mechanizm eLyMPuS nie pomaga na NAS" od "nasza generalizacja na $k$-arne domeny jest niepoprawna/
  nieoptymalna" bez walidacji z Fazy 2 — stąd jej krytyczne znaczenie w tym planie.

## Weryfikacja
- `uv run pytest` zielone po każdej fazie.
- Faza 0 i Faza 2 mają własne, spisane wyjścia (`notes/lympus-nas-adaptation-*.md`) — to są bramki go/no-go,
  nie tylko wewnętrzne notatki robocze.
- Smoke test na realnych danych NAS-Bench-201 przed pełnym gridem (Faza 4).
