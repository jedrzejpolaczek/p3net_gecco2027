# v006 — zadania przeniesione z v005 (2026-11-17)

v005 zamknięte 2026-11-17: dokumenty v005 w `notes/archive/v005/` (plan, todo, prerejestracja, claimy, karty, audyt w
`plans/`; raporty 01–06 w `analysis-v005/`), zamrożona kopia artykułu w `chapters/archive/v005/` (z
`nas_compare_v0.0.5.tex`) i `figures/archive/v005/`. Artykuł roboczy: `nas_compare_v0.0.5.tex`, `chapters/`,
`figures/`, `refs.bib`. Autor decyduje, które zadania i w jakiej formie przechodzą do planu v006.

## A. Artykuł — szkice gotowe, do domknięcia przy składaniu

1. Podział tekst główny / suplement i limit 8 stron — po eksperymentach v006 (decyzja autora 2026-11-17).
2. Ostateczny tytuł (obecny w `chapters/title/main.tex` to propozycja).
3. Miejsce czterech rysunków (tekst główny czy suplement): `rank__p3net__by_budget`, `quality_vs_cost__colorectal`,
   `fronts__colorectal__budget350`, `anytime__primary__budget350`.
4. Ponowne sprawdzenie zgodności tekstu z claimami po zmianach v006 (tabela v005:
   `notes/archive/v005/plans/v005-claims.md`; v006 — własna).
5. Opcjonalnie: usunięcie komentarzy roboczych ze źródeł LaTeX-a, inny przedrostek niż `_generated_`.

## B. Bibliografia — wpisy cytowane w artykule do sprawdzenia (38)

Lista z `refs.bib` (73 cytowane klucze): brakujące pola wg stylu ACM-Reference-Format (ostrzeżenia BibTeX w Overleafie) oraz
wpisy z października opisane w `refs.bib` jako „metadata written from memory/arXiv; check before submission”. Źródło
danych: strona wydawcy (ACM DL, Springer, IEEE Xplore, PMLR, OpenReview, NeurIPS proceedings) albo „Cytuj” w Google
Scholar, sprawdzone na stronie wydawcy. Dla ICLR/PMLR/OpenReview brak miejsca wydania jest normalny — wystarczy
potwierdzić, że wpis jest poprawny. NAS-HPO-Bench-II-Plus: tom 14 i DOI dopisane 2026-11-17 (z PDF-u).

| # | Klucz | Pierwszy autor, rok | Tytuł (do wyszukania) | Miejsce publikacji | Co sprawdzić |
|---|---|---|---|---|---|
| 1 | `akiba2019optuna` | Akiba, 2019 | Optuna: A Next-generation Hyperparameter Optimization Framework | Proceedings of the 25th ACM SIGKDD International Conference on Knowledge Discovery \& Data Mining (KDD) | strony |
| 2 | `balandat2020botorch` | Balandat, 2020 | BoTorch: A Framework for Efficient Monte-Carlo Bayesian Optimization | Advances in Neural Information Processing Systems | strony |
| 3 | `bansal2022jahsbench` | Bansal, 2022 | JAHS-Bench-201: A Foundation For Research On Joint Architecture And Hyperparameter Search | Advances in Neural Information Processing Systems 35 (NeurIPS 2022), Datasets and Benchmarks Track | strony |
| 4 | `bergstra2012random` | Bergstra, 2012 | Random Search for Hyper-Parameter Optimization | Journal of Machine Learning Research | całość (autorzy, tytuł, miejsce, rok, strony) |
| 5 | `chebykin2022encas` | Chebykin, 2022 | Evolutionary Neural Cascade Search across Supernetworks | Proceedings of the Genetic and Evolutionary Computation Conference (GECCO) | strony |
| 6 | `daulton2020qehvi` | Daulton, 2020 | Differentiable Expected Hypervolume Improvement for Parallel Multi-Objective Bayesian Optimization | Advances in Neural Information Processing Systems (NeurIPS) | strony, całość (autorzy, tytuł, miejsce, rok, strony) |
| 7 | `daulton2021qnehvi` | Daulton, 2021 | Parallel Bayesian Optimization of Multiple Noisy Objectives with Expected Hypervolume Improvement | Advances in Neural Information Processing Systems (NeurIPS) | strony, całość (autorzy, tytuł, miejsce, rok, strony) |
| 8 | `deb2014nsga3` | Deb, 2014 | An Evolutionary Many-Objective Optimization Algorithm Using Reference-Point-Based Nondominated Sorting Approach, Part I: Solving Problems With Box Constraints | IEEE Transactions on Evolutionary Computation | całość (autorzy, tytuł, miejsce, rok, strony) |
| 9 | `dong2020nasbench201` | Dong, 2020 | NAS-Bench-201: Extending the Scope of Reproducible Neural Architecture Search | International Conference on Learning Representations (ICLR) | miejsce wydania, strony |
| 10 | `duan2021transnasbench101` | Duan, 2021 | TransNAS-Bench-101: Improving Transferability and Generalizability of Cross-Task Neural Architecture Search | Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR) | wydawca, miejsce wydania, strony |
| 11 | `dushatskiy2021novelsurrogateassistedevolutionaryalgorithm` | Dushatskiy, 2021 | A Novel Surrogate-assisted Evolutionary Algorithm Applied to Partition-based Ensemble Learning | Proceedings of the Genetic and Evolutionary Computation Conference (GECCO '21) | strony |
| 12 | `falkner2018bohb` | Falkner, 2018 | BOHB: Robust and Efficient Hyperparameter Optimization at Scale | Proceedings of the 35th International Conference on Machine Learning (ICML) | miejsce wydania |
| 13 | `hirose2021nashpobenchii` | Hirose, 2021 | NAS-HPO-Bench-II: A Benchmark Dataset on Joint Optimization of Convolutional Neural Network Architecture and Training Hyperparameters | Proceedings of the Asian Conference on Machine Learning (ACML) | miejsce wydania, strony |
| 14 | `hirose2026nashpobenchiiplus` | Hirose, 2026 | NAS-HPO-Bench-II-Plus: A Surrogate Benchmark Dataset toward Practical Scenarios in Joint Neural Architecture Search and Hyperparameter Optimization | IEEE Access | strony |
| 15 | `hsu2018monas` | Hsu, 2018 | MONAS: Multi-Objective Neural Architecture Search using Reinforcement Learning | arXiv preprint arXiv:1806.10332 | całość (autorzy, tytuł, miejsce, rok, strony) |
| 16 | `knowles2006parego` | Knowles, 2006 | ParEGO: A Hybrid Algorithm with On-Line Landscape Approximation for Expensive Multiobjective Optimization Problems | IEEE Transactions on Evolutionary Computation | całość (autorzy, tytuł, miejsce, rok, strony) |
| 17 | `kristiadi2024sober` | Kristiadi, 2024 | A Sober Look at LLMs for Material Discovery: Are They Actually Good for Bayesian Optimization Over Molecules? | Proceedings of the 41st International Conference on Machine Learning (ICML) | miejsce wydania |
| 18 | `li2018hyperband` | Li, 2018 | Hyperband: A Novel Bandit-Based Approach to Hyperparameter Optimization | Journal of Machine Learning Research | całość (autorzy, tytuł, miejsce, rok, strony) |
| 19 | `li2020asha` | Li, 2020 | A System for Massively Parallel Hyperparameter Tuning | Proceedings of Machine Learning and Systems (MLSys) | wydawca, miejsce wydania, całość (autorzy, tytuł, miejsce, rok, strony) |
| 20 | `li2021hwnasbench` | Li, 2021 | HW-NAS-Bench: Hardware-Aware Neural Architecture Search Benchmark | International Conference on Learning Representations (ICLR) | miejsce wydania, strony |
| 21 | `lindauer2022smac3` | Lindauer, 2022 | SMAC3: A Versatile Bayesian Optimization Package for Hyperparameter Optimization | Journal of Machine Learning Research | całość (autorzy, tytuł, miejsce, rok, strony) |
| 22 | `liu2024llambo` | Liu, 2024 | Large Language Models to Enhance Bayesian Optimization | International Conference on Learning Representations (ICLR) | miejsce wydania, strony |
| 23 | `luong2014mogomea` | Luong, 2014 | Multi-objective Gene-pool Optimal Mixing Evolutionary Algorithms | Proceedings of the Genetic and Evolutionary Computation Conference (GECCO) | całość (autorzy, tytuł, miejsce, rok, strony) |
| 24 | `mehta2022nasbenchsuite` | Mehta, 2022 | NAS-Bench-Suite: NAS Evaluation is (Now) Surprisingly Easy | International Conference on Learning Representations (ICLR) | miejsce wydania, strony |
| 25 | `ozaki2020motpe` | Ozaki, 2020 | Multiobjective Tree-Structured Parzen Estimator for Computationally Expensive Optimization Problems | Proceedings of the Genetic and Evolutionary Computation Conference (GECCO) | całość (autorzy, tytuł, miejsce, rok, strony) |
| 26 | `real2019regularized` | Real, 2019 | Regularized Evolution for Image Classifier Architecture Search | Proceedings of the AAAI Conference on Artificial Intelligence | całość (autorzy, tytuł, miejsce, rok, strony) |
| 27 | `romano2006appropriate` | Romano, 2006 | Appropriate Statistics for Ordinal Level Data: Should We Really Be Using t-test and Cohen's d for Evaluating Group Differences on the NSSE and Other Surveys? | Annual Meeting of the Florida Association of Institutional Research | wydawca, miejsce wydania, strony |
| 28 | `schmucker2021moasha` | Schmucker, 2021 | Multi-objective Asynchronous Successive Halving | arXiv preprint arXiv:2106.12639 | całość (autorzy, tytuł, miejsce, rok, strony) |
| 29 | `song2022ossvizier` | Song, 2022 | Open Source Vizier: Distributed Infrastructure and API for Reliable and Flexible Blackbox Optimization | International Conference on Automated Machine Learning (AutoML-Conf), Systems Track | wydawca, miejsce wydania, strony |
| 30 | `song2024vizier` | Song, 2024 | The Vizier Gaussian Process Bandit Algorithm | arXiv preprint arXiv:2408.11527 | całość (autorzy, tytuł, miejsce, rok, strony) |
| 31 | `tu2022nasbench360` | Tu, 2022 | NAS-Bench-360: Benchmarking Neural Architecture Search on Diverse Tasks | Advances in Neural Information Processing Systems 35 (NeurIPS 2022), Datasets and Benchmarks Track | miejsce wydania, strony |
| 32 | `white2021bananas` | White, 2021 | BANANAS: Bayesian Optimization with Neural Architectures for Neural Architecture Search | Proceedings of the AAAI Conference on Artificial Intelligence | całość (autorzy, tytuł, miejsce, rok, strony) |
| 33 | `williams1992reinforce` | Williams, 1992 | Simple Statistical Gradient-Following Algorithms for Connectionist Reinforcement Learning | Machine Learning | całość (autorzy, tytuł, miejsce, rok, strony) |
| 34 | `yang2020nasfrustratinglyhard` | Yang, 2020 | NAS evaluation is frustratingly hard | International Conference on Learning Representations (ICLR) | miejsce wydania, strony |
| 35 | `yu2020evaluatingnas` | Yu, 2020 | Evaluating the Search Phase of Neural Architecture Search | International Conference on Learning Representations (ICLR) | miejsce wydania, strony |
| 36 | `zela2018towards` | Zela, 2018 | Towards Automated Deep Learning: Efficient Joint Neural Architecture and Hyperparameter Search | ICML 2018 AutoML Workshop | wydawca, miejsce wydania, strony |
| 37 | `zhang2007moead` | Zhang, 2007 | MOEA/D: A Multiobjective Evolutionary Algorithm Based on Decomposition | IEEE Transactions on Evolutionary Computation | całość (autorzy, tytuł, miejsce, rok, strony) |
| 38 | `zoph2017nas` | Zoph, 2017 | Neural Architecture Search with Reinforcement Learning | International Conference on Learning Representations (ICLR) | miejsce wydania, strony, całość (autorzy, tytuł, miejsce, rok, strony) |

### B — wynik sprawdzenia z PDF-ów (2026-11-17, `notes/articles/` (HPO, NAS, MOEA, NSGA, linkage learn))

Poprawione w `refs.bib` (tylko pola wydrukowane w PDF-ach):
- MONAS (`hsu2018monas`): tytuł wg aktualnej wersji arXiv (v2) — „MONAS: Multi-Objective Neural Architecture Search”.
- NAS-HPO-Bench-II (`hirose2021nashpobenchii`): PMLR, tom 157.
- MO-GOMEA (`luong2014mogomea`): DOI 10.1145/2576768.2598261 (autorzy, GECCO'14 Vancouver — zgodne).
- ENCAS (`chebykin2022encas`): 13 stron (z „ACM Reference Format” w PDF).
- MOTPE: dostępny PDF to wersja czasopismowa — nowy wpis `ozaki2022motpe` (JAIR 73, 1209–1250, 2022, 5 autorów),
  cytowany w „Compared methods” zamiast `ozaki2020motpe` (GECCO 2020, z pamięci, niesprawdzony).

Zgodne z PDF (autorzy, tytuł, miejsce, rok; strony gdy wydrukowane): Bergstra 2012 (JMLR 13, 281–305), Daulton 2020
(NeurIPS 2020), Daulton 2021 (NeurIPS 2021), Knowles (TEVC 10(1), od s. 50), Hyperband (JMLR 18, 1–52), ASHA (MLSys
2020, autorzy), Real (AAAI 2019), MO-ASHA (arXiv, autorzy), Vizier GP (arXiv, 11 autorów), MOEA/D (TEVC 11(6), od s. 712),
Zoph (ICLR 2017), JAHS-Bench-201 i NAS-Bench-360 (NeurIPS 2022 D&B), NAS-Bench-201, HW-NAS-Bench, NAS-Bench-Suite,
LLAMBO, Yang 2020 (ICLR), BOHB i Kristiadi (ICML), OSS Vizier (AutoML Conf 2022), Zela (ICML 2018 AutoML Workshop).

Do rozstrzygnięcia przez autora:
1. **SMAC3:** PDF (arXiv v2) ma nagłówek „JMLR 22 (2021) 1–9”, wpis — tom 23, nr 54, 2022. Sprawdzić na jmlr.org.
2. **ParEGO:** nagłówek PDF „Vol. 10, No. 1, February 2005”, wpis — 2006 (wg IEEE Xplore tom 10 to 2006; nagłówek
   z błędem drukarskim?). Sprawdzić w IEEE Xplore.
3. **Plik 14** to kopia NAS-HPO-Bench-II (nie Plus) — dane Plus i tak wpisane z PDF w `notes/articles/` (HPO, NAS, MOEA, NSGA, linkage learn)
   (tom 14, DOI).
4. **Williams 1992 (plik 33):** skan bez warstwy tekstowej — nieczytelny maszynowo; wpis standardowy (Machine Learning
   8, 229–256), do potwierdzenia wzrokowo.
5. **Strony, których PDF-y nie podają** (wersje arXiv/preprint): Optuna (KDD), BoTorch, JAHS-Bench-201, Daulton ×2,
   Deb 2014 (wersja „early access”), NAS-Bench-201, TransNAS-Bench-101 (CVPR), Dushatskiy 2021, NAS-HPO-Bench-II,
   ASHA (tom 2 i strony z pamięci), HW-NAS-Bench, LLAMBO, NAS-Bench-Suite, Real 2019, OSS Vizier, NAS-Bench-360,
   BANANAS, Yang, Yu, Zela, Zoph — potrzebne strony z wersji wydawcy; dla ICLR/OpenReview i arXiv strony nie istnieją
   (ostrzeżenie zostaje, wpis poprawny).
6. **Romano 2006:** bez dostępu — zostaje wpis ze Scholara.

## C. Literatura do sprawdzenia — przeczytane 2026-11-17 (`notes/articles/` (HPO, NAS, MOEA, NSGA, linkage learn))

1. **HPNAS-RL** (Adde, Gottschalk, arXiv:2610.36882): łączne NAS+HPO dla RL algorytmem genetycznym na NSGA-II (EMNAS);
   bez P3/GOMEA/linkage learning — **luki nie zawęża**. Opcjonalnie jedno zdanie w Related Work (wielokryterialny EA w
   łącznym NAS+HPO poza benchmarkami). Notatka: `notes/ga_landscape_2026.md` §16e.
2. **NAS-HPO-Bench-II-Plus** (IEEE Access 14, 2026; opublikowany 13.07.2026, **przed zamrożeniem prerejestracji v005**):
   rozszerza NHB2 o 6 typów hiperparametrów (ciągłe, dyskretne, kategoryczne), przestrzeń warunkową i ocenę na wielu
   urządzeniach; surogaty MLP (τ Kendalla 0.940). **Zrobione 2026-11-17:** uzasadnienie w Setup („We use
   NAS-HPO-Bench-II rather than its successor … the tabular original gives the exact Pareto front against which IGD+ is
   computed”); zdanie „has since appeared” w pozycjonowaniu zastąpione odwołaniem do Setup. HPNAS-RL — bez cytowania
   (decyzja autora 2026-11-17).

## D. Etap D — wchodzi do planu v006 jako ostatni etap (jak w v005)

1. Anonimizacja: `authordraft`, autorzy i afiliacje, samocytowania (Bartnik; eLyMPuS — promotor) w trzeciej osobie.
2. Anonimowe repozytorium, link `\anonrepo`.
3. `printacmref`, daty konferencji, prawa — wg wytycznych GECCO'27 (sprawdzić wymagania dla zgłoszeń).
4. Ponowne wygenerowanie wszystkich tabel i rysunków z run rootów; zgodność liczb w tekście z tabelami.
5. Bibliografia — punkt B.

## E. Decyzje z v005 do planu v006

1. F1 (audyt v005): czy przeliczyć P3Net-gate z bramką kwantylową — decyzja w prerejestracji v006 (nie jako dopisek
   do v005; v005 obowiązuje §8.5).
2. P3-eLyMPuS z wiedzą dziedzinową (graf zależności NAS+HPO): ustalenia z 2026-11-16 (warianty: pewny / hipoteza /
   transfer, porównanie z pustym grafem; baseline'y z rekordów v005 — seedy 62–91, budżety 50–350, kod `c674c91e`;
   puste eLyMPuS przeliczane tylko przy zmianie kodu) — blok „Następna iteracja” w
   `notes/archive/v005/plans/v005-plan.md`.
3. Opcjonalnie: przyczyna systematycznie niższej dokładności po retreningu na NAS-HPO-Bench-II (−0.9 pp; podejrzenie —
   sieć z xautodl zamiast modułu autorów).
4. **Opcja do rozważenia: NAS-HPO-Bench-II-Plus jako przestrzeń v006** (decyzja przy planie v006). Za: hiperparametry
   ciągłe i warunkowe, cele sprzętowe na kilku urządzeniach, silne zależności architektura–trening — tam wiedza
   dziedzinowa dla eLyMPuS może mieć znaczenie. Przeciw / koszt: dyskretyzacja zmiennych ciągłych dla P3 (jak na JAHS),
   brak dokładnego frontu (HV z granicami przestrzeni zamiast IGD+), baseline'y v005 nie mają rekordów na tej przestrzeni
   (trzeba by je przeliczyć).
5. Proces (wnioski z audytu v005, `notes/archive/v005/plans/v005-audit-cards.md`): każdy wariant, analiza i parametr
   z karty ma własność W i test; prerejestracja pisana z kart **i** kodu; implementujący zapisuje pytanie zamiast
   rozstrzygać niejasność sam.

## F. Infrastruktura

1. Serwer Hetzner: snapshot albo usunięcie (decyzja autora; do v006 baseline'y bierzemy z rekordów v005).
2. ~~Przeniesienie `implementation/experiments-bartnik` i `-przewozniczek`~~ — zrobione 2026-11-17:
   `implementation/archive/`, ścieżka do biblioteki w ich `pyproject.toml` = `../../lib` (pierwsza próba zablokowana
   przez pliki otwarte w tym czasie przez inne procesy — przeszukiwanie katalogów, które sam uruchomiłem; druga próba
   przeszła).
3. `run_pipeline.py` (bramka `checks`) czyta karty i claimy z `notes/archive/v005/plans/`; v006 potrzebuje własnej
   lokalizacji (parametr zamiast stałej `NOTES_PLANS`).
