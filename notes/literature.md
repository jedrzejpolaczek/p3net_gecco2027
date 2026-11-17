# Literatura — stan po v005 (2026-11-17), punkt wyjścia dla v006

Notatka robocza. Pełna historia przeszukań (lipiec–listopad 2026, w tym nieaktualne wnioski z v003) jest w
`notes/archive/ga_landscape_2026-07_v003-v005.md`; odnośniki „§n” poniżej wskazują tamten plik. PDF-y przeczytanych prac:
`notes/articles/` (HPO, NAS, MOEA, NSGA, linkage learn).

## Luka, której bronimy (stan na 2026-11-17)

Nie jesteśmy pierwsi z linkage learning ani z P3 w wyszukiwaniu architektur. Do obrony:
1. P3 (piramida populacji) w **wielokryterialnym łącznym NAS+HPO** na benchmarkach tabelarycznych i surogatowych;
2. **szerokie, prerejestrowane porównanie** z metodami NAS, ewolucyjnymi, BO, GP i multi-fidelity, z kosztem
   optymalizatora;
3. wynik dla **surogatu par** (P3Net) — brak wykrywalnej poprawy, także przy budżecie 1000.

Tak sformułowane w artykule: `chapters/related_work/positioning.tex` („Position of this study”).

## Prace, które definiują tło (wszystkie w `refs.bib`)

**P3 i jego warianty**
- Goldman i Punch — P3 (GECCO 2014, `goldman2014parameterless`), złożoność ewaluacji (ECJ 2015, `goldman2015fast`).
- MO-P3 — Przewoźniczek, Dziurzanski, Zhao, Indrusiak (SWEVO 2021, `przewozniczek2021mop3`); rozwinięcie — Niemczyk,
  Przewoźniczek, Dziurzanski (ESWA 2025, `niemczyk2025pareto`). Planowanie procesów, bez surogatu, nie NAS.
- **P3 w NAS:** Dahi, Luque, Chicano (PPSN 2026, `dahi2026tightening`; znany tylko z suplementu) — P3 dobiera głębokość
  i szerokość małego MLP w potoku kwantowym, NAS jednokryterialny; wcześniej linkage-learning EA w NAS dla transpilacji
  kwantowej (EvoApps 2024, `dahi2024evolutionary`).
- P3 w potoku ML bez NAS/HPO: P3DE (NCA 2026; binarna selekcja cech) — niecytowane.

**Rodzina GOMEA w NAS**
- den Ottelander i in. (EMO 2021, `denottelander2021localsearch`) — MO-GOMEA ≈ NSGA-II ≈ LS ≈ RS na NAS-Bench-101,
  przewaga MO-GOMEA tylko na większych przestrzeniach MacroNAS.
- ENCAS — Chebykin i in. (GECCO 2022, `chebykin2022encas`) — MO-GOMEA dla kaskad sieci; doktorat Chebykina (2026)
  zostawia łączne NAS+HPO jako przyszłą pracę.
- Tran i in. (GECCO 2023 Companion, `tran2023gomeanas`) — GOMEA + Synaptic Flow (proxy bez treningu).
- Bartnik (praca magisterska 2026, `bartnik2026evolutionary`; promotor Przewoźniczek) — SA-P3-GOMEA w MO-NAS na
  NAS-Bench-201; jej MO-DSA i MO-PSA są ramionami porównawczymi v005 (założenia Z-B; autorka nie odpowiedziała).

**Surogat a linkage**
- CS-GOMEA — Dushatskiy i in. (GECCO 2019, `dushatskiy2019csgomea`): surogat nie wykorzystuje linkage w swojej
  konstrukcji (problem otwarty nazwany przez autorów).
- SA-P3-GOMEA — Dushatskiy i in. (GECCO 2021, `dushatskiy2021novelsurrogateassistedevolutionaryalgorithm`).
- **LyMPuS / eLyMPuS** — Przewoźniczek, Chicano, Komarnicki, Tinós (GECCO 2026, `przewozniczek2026lympus`; jedna praca:
  „Limited Perfect Monotonical Surrogates…”). P3-eLyMPuS przetestowany na NK, Ising, Max3Sat; kod
  https://github.com/przewooz/OLyMPuS. Podstawa v006 (eLyMPuS z grafem wiedzy dziedzinowej).

**Łączne NAS+HPO — benchmarki i baseline'y**
- JAHS-Bench-201 (`bansal2022jahsbench`), NAS-HPO-Bench-II (`hirose2021nashpobenchii`), **NAS-HPO-Bench-II-Plus**
  (IEEE Access 14, 2026, `hirose2026nashpobenchiiplus`; surogatowy, zmienne ciągłe i warunkowe, cele sprzętowe;
  uzasadnienie, czemu v005 go nie używa — Setup; opcja dla v006 — `notes/plans/v006-carryover.md` E.4).
- Bag of Baselines (`guerreroviu2021bagofbaselines`), Zela i in. 2018 (`zela2018towards`).
- Bez cytowania (przeczytane): HPNAS-RL (arXiv 2026; NSGA-II w łącznym NAS+HPO dla RL), MO-DEHB, ELLG (zgłoszenie
  ICLR 2026, niepublikowane).

**Benchmarki NAS — krytyka** (używane w Related Work): Yang i in. 2020, Mehta i in. 2022, Lopes i in. 2023 (przestrzeń
NAS-Bench-201 mała, redundantna, przesunięta ku dobrym architekturom), Tu i in. 2022, Duan i in. 2021.

## Przeszukania wykonane (podsumowanie)

- 2026-07: przegląd ogólny trendów GA/MO-NAS i dorobku promotora (§1–§15 archiwum).
- 2026-11-16: WebSearch po v005 i E1 (§16).
- 2026-11-17: Google Scholar przez autora — „P3 NAS HPO”, pełne nazwy („population pyramid”, „gene-pool optimal mixing”,
  „linkage learning”/„linkage tree” + NAS, „model-based evolutionary”), „Cytowane przez” Goldman i Punch 2014/2015,
  profil promotora; filtr „Od 2026” (2021–2025 pokryte wcześniej) — §16a–§16e. DBLP nie powtarzane.

## Wnioski metodologiczne (zachować)

- Brak kategorii w szerokim przeglądzie nie dowodzi nieistnienia wąskiej kombinacji — zawsze bezpośrednie zapytanie
  o kombinację (lekcja z §6: GOMEA w NAS znaleziony dopiero dedykowanym zapytaniem).
- Skrót „P3” w Scholarze to szum (warstwy FPN, uczestnicy) — szukać pełną nazwą; „GOMEA” od 3. strony dopasowuje
  nazwiska Gomez/Gomes.

## Dla v006

- Przed Related Work v006: powtórzyć przeszukanie (Scholar, DBLP) dla nowej tezy — eLyMPuS / surogat z wiedzą
  dziedzinową w NAS+HPO, „domain knowledge” + linkage learning, „prior dependency graph”.
