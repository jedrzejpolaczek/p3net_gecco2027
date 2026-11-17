# 05 — analizy drugorzędne z prerejestracji §5 i brakujące tabele opisowe (2026-11-17)

Źródło: `results/runs/c674c91e/analysis/` (CSV z `scripts/analyze_v005.py`, bez przeliczania rekordów). Tabele i wykres:
`scripts/render_v005_supplement.py` → `chapters/supplement/_generated_secondary.tex`, `figures/anytime__primary__budget350.pdf`;
sekcja suplementu `chapters/supplement/secondary.tex`; akapit „Secondary analyses (supplement)” i odwołania w
`chapters/results/main.tex`. Wszystko opisowe (bez testów), mediany po 30 seedach, b = 350 o ile nie podano inaczej.

## Po raz pierwszy omawiane

- **§5.2 koszt dojścia do celu** (`tab:v005-s-ctt`). Na JAHS progi 90 i 95 % są prawie bezużyteczne (HV ściśnięte przy
  1 — każde ramię dochodzi po kilku ewaluacjach); informacyjny jest próg 99 %: P3Net dochodzi w 67 / 87 / 90 % runów
  (C10 / CRC / FMN) po medianie 124 / 135 / 127 ewaluacji; większość ramion we wszystkich runach i szybciej (FMN ok. 20).
  Rodzina P3 (z eLyMPuS) jest tu najwolniejsza obok REINFORCE. NHB: 95 % najlepszej mediany IGD+ osiąga najwyżej połowa
  runów jakiegokolwiek ramienia (NSGANetV2 50 %), P3Net 3 %. Ramiona MF: koszt w ekwiwalentach pełnej ewaluacji;
  SH-EMOA (MF) ok. 231, bo pierwsze pełne treningi przychodzą późno.
- **§5.6a wrażliwość HV** (`tab:v005-s-hvsens`): Spearman kolejności ramion ref (1.05, 1.05) i (1.2, 1.2) vs (1.1, 1.1)
  ≥ 0.992 we wszystkich 12 komórkach JAHS; ranga P3Net bez zmian w każdej. Wybór punktu odniesienia nie wpływa na wnioski.
- **§5.9 luka generalizacji** (`tab:v005-s-gap`; średnia (test − walidacja) f1 członków frontu końcowego): różnice między
  przestrzeniami większe niż między ramionami — CRC +1.0…+1.9 pp, FMN +1.25…+2.1 pp, C10 −0.03…+0.35 pp, NHB −0.20…−0.50 pp,
  NB201 −2.4…−2.9 pp (podział `cifar10-valid`: test łatwiejszy), FCNet ≈ 0. Rodzina P3 na FMN w górnej części (+1.9–2.0).

## Wcześniej w raportach, teraz w tekście

- **§5.1 anytime** (`fig:v005-s-anytime`, wykres 4 paneli, b = 350): P3Net i kanoniczne P3 rosną późno i skokowo; do
  czołówki dochodzą po ok. 110–160 ewaluacjach na CRC i FMN, na C10 kończą poniżej najlepszego (NSGA-Net). NHB: w stawce.
  Ramiona MF są na osi kosztu — tylko w CSV.
- **§5.7 budżet** (`tab:v005-s-budget`): `duplication_rate` = 0 w każdym runie (duplikaty odfiltrowane przed ewaluacją,
  #35) — wskaźnik nieinformacyjny, napisane wprost w podpisie. Budżetu nie wyczerpują: REINFORCE (15.8 % runów),
  MO-DSA (80.9 %), MO-PSA (88.0 %), MOTPE (99.6 %), SH-EMOA MF (harmonogram kończy się przy 97–98 % kosztu).
- **§5.10 regret** (`tab:v005-s-regret`): CRC i FMN — P3Net 0.29 i 0.15 pp, w granicy 0.01 od najniższego; C10 0.52
  (najlepszy NSGA-Net 0.27), NHB 1.22 (najlepszy MO-BANANAS 0.69).

## Brakujące tabele

- **NB201** (`tab:v005-s-nb201`): mediana IGD+ i ranga per budżet; P3Net 15 / 13 / 12 / 12.
- **Q7** (`tab:v005-s-q7`): δ P3-eLyMPuS vs kanoniczne P3, 33 z 36 komórek ujemne.
- **GP** (`tab:v005-s-gp`, decyzja #30): OSS Vizier najlepszy z 22 ramion w 11 z 18 komórek (9 przestrzeni × b = 50, 100).

## Czego nie ma i dlaczego

- §5.4 jakość decyzji surogatu — niewykonane (prerejestracja §8.3, Limitations).
- Czas symulowanego treningu do celu (§5.2) — tylko w CSV (tabela byłaby dwa razy szersza).
