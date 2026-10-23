# v005 — publiczne interfejsy dla testów poziomu 1

Status: **ZATWIERDZONY, wersja 2** (2026-10-16). Wersja 2 = wersja 1 + zmiany z §7 (odpowiedzi na pytania autora
testów, `v005-test-answers.md`). **Przy sprzeczności obowiązuje §7.**
Po co: protokół (`v005-verification-protocol.md` §1) — autor testów (niezależny agent) widzi **kartę + publiczny
interfejs, bez implementacji**. Własności z kart dotyczą też elementów wewnętrznych (FOS, FIHC, bramka, nagroda), więc
każdy taki element musi mieć publiczną, testowalną funkcję/klasę o ustalonej sygnaturze. Implementujący **nie może
zmienić sygnatur** bez zmiany tego dokumentu i ponownego zatwierdzenia.

Konwencje: Python 3.13, pakiet `p3net` (`implementation/lib/src/p3net`), moduły v005 w `p3net.v005.*` (stary kod v004
zostaje do porównań, nie jest importowany przez v005). Każdy element losowy przyjmuje `rng: random.Random` (albo
`numpy.random.Generator` tam, gdzie biblioteka tego wymaga). Cele zawsze minimalizowane: `Objectives = tuple[float, float]`.

## 0. Wspólne (istnieją — bez zmian sygnatur)

- `p3net.harness.runner`: `Observation(genotype, objectives)`, `RunState(history, evaluations_used)`, protokół
  `Method.propose(state) -> list[Genotype]`, `Method.update(state, new_observations) -> None`, `Runner(objective, budget)`.
- `p3net.problem.genotype`: `Genotype` (krotka indeksów 0…k_i−1), `CategoricalDomain`, przestrzeń z `sample(rng)`.
- `p3net.problem.objectives`: `dominates(a, b)`, `pareto_front`, `fast_nondominated_sort`, `crowding_distance`.
- `p3net.problem.synthetic_kary`: pułapki k-arne, `true_dependency_graph(n_blocks, block_size)`.

Nowe wspólne (do dodania):

```python
# p3net.v005.common
def is_valid(space, g: Genotype) -> bool                       # Validity (#33)
class Budget:                                                    # reguła K-2
    def __init__(self, total: int): ...
    def charge(self, g: Genotype, cache: "EvalCache") -> bool    # False = budżet wyczerpany (nic nie oceniono)
class EvalCache:                                                 # H_t + deduplikacja (#35)
    def get(self, g) -> Objectives | None
    def put(self, g, objs) -> None
    def history(self) -> list[Observation]
def initial_design_size(source_value: int, budget: int) -> int   # BB-4: min(source, floor(0.25*b))
def online_minmax(history: list[Objectives]) -> Callable[[Objectives], tuple[float, float]]  # R-3 a, L-1 b
```

Metody wymagające ewaluacji krok po kroku (P3, eLyMPuS, MO-LS, Bartnik) są **maszynami stanów**: każdy `propose`
zwraca dokładnie jeden genotyp do prawdziwej ewaluacji; testy mogą też użyć `step_through(method, objective, budget)`
(`p3net.v005.testing`), który zwraca listę kolejno ocenionych genotypów.

## 1. P3 / P3Net / kanoniczne P3 (karty `p3net.md`, `p3-canonical.md`, `p3net-surrogate.md`)

```python
# p3net.v005.p3.linkage
class FrequencyTable:                     # P13
    def __init__(self, domains: list[int]): ...
    def add(self, g: Genotype) -> None
    def entropy(self, vars: tuple[int, ...]) -> float           # H (Eq. 2)
def cluster_distance(table, ci: tuple[int,...], cj: tuple[int,...]) -> float   # D (Eq. 1)
def build_clusters(table, rng) -> list[tuple[int, ...]]         # P14–P18: kolejność użycia (od najmniejszych)

# p3net.v005.p3.fihc
def fihc(g: Genotype, compare: Callable[[Genotype, Genotype], int], domains, rng) -> Genotype   # P10–P12
#   compare(a, b) > 0 ⇔ a ściśle lepsze (D-1: dominacja); wołane przez oceniacza, który liczy ewaluacje

# p3net.v005.p3.mixing
def mix_with_level(g, level: list[Genotype], clusters, accept: Callable, rng) -> Genotype   # P20–P25
def mogomea_accept(new: Objectives, old: Objectives, archive: list[Objectives]) -> bool      # D-1 b

# p3net.v005.p3.pyramid
class Pyramid:
    levels: list[list[Genotype]]; hashset: set[Genotype]
    def add(self, level: int, g: Genotype) -> bool               # False, gdy g już w hashset

# p3net.v005.methods
class P3Canonical(Method): ...       # wszystkie kroki prawdziwe (K-1: ten sam silnik, oceniacz = prawdziwy)
class P3Net(Method): ...             # mieszanie na surogacie, prawdziwa ewaluacja po poziomie (D-3 b)
class P3NetGate(Method): ...         # wariant D-3 a
class P3NetNoLink(Method): ...       # wariant S-2 c
#   wszystkie: __init__(space, rng, *, step_evaluator: Literal["real","surrogate","oracle"]=...)  # W-K3

# p3net.v005.surrogates.pairwise
class PairwiseSurrogate:             # S-1 a … S-9
    def __init__(self, domains, *, use_linkage: bool, rng): ...
    def fit(self, history: list[Observation], clusters: list[tuple[int,...]]) -> None
    def features(self, a: Genotype, b: Genotype) -> "np.ndarray"     # W-S3: interakcje tylko w klastrach
    def predict_delta(self, a, b) -> tuple[float, float]             # log-skala (S-3), oba cele (S-5)
    def predict_chain(self, anchor: Observation, chain: list[Genotype]) -> tuple[float, float]   # telescoping
def grouped_cv_folds(history, n_folds, rng) -> list[tuple[set[int], set[int]]]                  # S-8
```

## 2. Bartnik MO-DSA / MO-PSA (karta `bartnik-mo-sa-p3-gomea.md`)

```python
# p3net.v005.bartnik
def dominance_probability(mu_new, sd_new, mu_old, sd_old) -> float      # Eq. 6.1 (B13)
def quantile_threshold(history: list[float], alpha: float) -> float      # B14
class AlphaSchedule:                                                      # B5: start 1, ×γ, reset
    def __init__(self, gamma: float = 0.999): ...
    def end_iteration(self, archive_changed: bool) -> float
def psa_gom_keep(p_keep: float, p_revert: float, tau: float) -> bool     # B12
class MODSA(Method): ...; class MOPSA(Method): ...                        # __init__(space, budget, rng)
```

## 3. eLyMPuS (karta `elympus.md`)

```python
# p3net.v005.elympus
class ELyMPuS:
    def __init__(self, domains, rng): ...
    vig: dict[int, set[int]]
    def partial_compare(self, x: Genotype, var: int, value: int, evaluate, verify: bool) -> int   # E2–E3, Z-E1
    def recursive_ll(self, x1, x2, var, evaluate) -> int | None            # E6
class OneOverX:                                                            # E8, Z-E3
    def start_call(self, vig_empty: bool) -> bool                          # True = weryfikuj w tym wywołaniu
    def end_call(self, found_dependency: bool, repeated_optimum: bool) -> None
def fihc_elympus(x, elympus_per_objective: tuple[ELyMPuS, ELyMPuS], evaluate, schedule, rng) -> Genotype   # E9–E10, E-2
class P3ELyMPuS(Method): ...
```

## 4. Baseline'y

```python
# p3net.v005.baselines.nsga_net       NSGANet(Method)        + binary_tournament, two_point_crossover, int_polynomial_mutation
# p3net.v005.baselines.nsganetv2      NSGANetV2(Method)      + adaptive_switching(X, y, rng) -> (model_name, model),
#                                                             inner_nsga2(...), subset_selection(cand_f2, nd_f2, K, rng)
# p3net.v005.baselines.reinforce      Reinforce(Method)      + reward_mnasnet(a, c, T), reward_monas(a, c, alpha),
#                                                             reward_adc(obj, front, eps, C), temperature(step, period)
# p3net.v005.baselines.regevo         RegEvo(Method)         + crowded_winner(sample, population)
# p3net.v005.baselines.mo_ls          MOLS(Method)
# p3net.v005.baselines.bob            SHEMOA(Method), MOBANANAS(Method), MOSHBANANAS(Method), MOBOHB(Method)
#                                       + hv_contribution_remove(front), get_budgets(bmin, bmax, eta, max_evals, pop)
# p3net.v005.baselines.library        SMAC3ParEGO, MOEAD, NSGA3, MOTPE, QNEHVI, QParEGO, Vizier, RandomSearch
#                                       wszystkie: .config() -> dict  (W-A1: rzeczywista konfiguracja biblioteki)
# p3net.v005.mf                       HyperbandMO, ASHAMO + bracket_schedule(eta, r_min, R), mf_cost(e, e_prev, E)
```

Wszystkie metody: `__init__(space, budget: int, rng, **params)`; parametry domyślne = wartości z kart.

## 5. Benchmarki (karta `benchmarks.md`)

Istniejący `Substrate` (`experiments/substrates/base.py`) bez zmian sygnatur; nowe: `NB201Energy` (tablica energii,
metadane sprzętu), metoda `Substrate.f1_split() -> Literal["valid"]` do testu W-BM1/W-BM5.

## 6. Do zatwierdzenia

Moduł `p3net.v005` obok kodu v004; sygnatury §0–§5; zasada „sygnatury zamrożone po zatwierdzeniu”. Potem: zlecenie
testów poziomu 1 niezależnemu agentowi (osobna sesja lub sub-agent bez dostępu do `p3net.v005` — tylko karty i ten
dokument).

## 7. Wersja 2 — zmiany (2026-10-16, z `v005-test-answers.md`)

Numery Q odnoszą się do `implementation/lib/tests/v005/level1/QUESTIONS.md`; szczegóły schematów — tam.

**Wspólne**
- Q-01: wszystkie funkcje v005 przyjmują i zwracają `Genotype` (dataclass z `values`).
- Q-03: **wszystkie** metody (także rodzina P3 z §1): `__init__(space, budget: int, rng, **params)`; `step_evaluator`
  jako parametr słownikowy.
- Q-02, Q-13: metody-maszyny stanów (P3Canonical, P3Net, P3NetGate, P3NetNoLink, P3ELyMPuS, MODSA, MOPSA) przyjmują
  `observer: Callable[[str, dict], None] | None = None`; zdarzenia `iteration`, `fihc_end`, `insert`, `level_mix`,
  `cluster_step`, `surrogate_fit`, `psa_decision`, `stop` (ładunki wg Q-02), emitowane synchronicznie **po**
  rozstrzygnięciu kroku. Atrybuty: `pyramid: Pyramid` (P3*), `stop_reason: str | None` (Bartnik).
- Q-21, Q-30: każda metoda ma `.config() -> dict` (klucze wg Q-21 / Q-30, w tym `seed`; SMAC3 dodatkowo `configspace`).
- Q-33: `online_minmax` — przy min = max dla danego celu zwraca 0.0.
- Q-34: metoda sama nie przekracza budżetu; `Runner` asertuje (nie przycina).

**P3 / surogat**
- Q-04: `mix_with_level(..., accept: Callable[[Genotype, Genotype], bool], ...)` — `accept(candidate, current)`.
- Q-05: `domains: list[int]` (liczności) w `fihc` i `FrequencyTable`.
- Q-16: `fihc(..., order: list[int] | None = None)` i `fihc_elympus(..., order: list[int] | None = None)`.
- Q-06, Q-29: `predict_delta(a, b)` = log f(a) − log f(b); `predict_chain` zwraca skalę log.
- Q-07: `grouped_cv_folds` zwraca indeksy obserwacji w `history`.
- Q-08: `P3Net.diagnostics() -> dict` z kluczem `"chain_errors"` (lista `{"chain_length", "predicted", "true"}`).
- Q-09: `step_evaluator="oracle"` — każde zapytanie do surogatu staje się propozycją prawdziwej ewaluacji (liczonej).

**Bartnik**
- Q-11: `dominance_probability` w konwencji minimalizacji: Φ((μ1_old − μ1_new)/s1)·Φ((μ2_old − μ2_new)/s2).
- Q-12: `quantile_threshold` = `numpy.quantile(history, alpha, method="linear")`.

**eLyMPuS**
- Q-14: `partial_compare(...) > 0` ⇔ wariant ściśle lepszy (mniejszy); `evaluate(g) -> float` w `partial_compare` /
  `recursive_ll`, `-> (f1, f2)` w `fihc_elympus`.
- Q-15: `recursive_ll(...) -> tuple[int | None, int]` (znaleziona zmienna, liczba podziałów).
- Q-17: `P3ELyMPuS.pyramid`, `P3ELyMPuS.elympus: tuple[ELyMPuS, ELyMPuS]`.
- Q-19: `end_call(..., repeated_optimum=True)` przywraca stan świeżego `OneOverX()`.

**Baseline'y**
- Q-18: `hv_contribution_remove(front) -> int` (indeks).
- Q-22: `SHEMOA.population`; `shemoa_tournament(population, k, rng)`, `uniform_crossover(p1, p2, rng)`,
  `shemoa_mutation(g, domains, n_mut, rng)`.
- Q-23: `binary_tournament(a, b, rng) -> 0 | 1`, `two_point_crossover(p1, p2, rng) -> (c1, c2)` (zawsze, p = 1.0),
  `int_polynomial_mutation(g, domains, rng) -> Genotype` (p = 1/n, `rint`, naprawa do zakresu).
- Q-24: `NSGANet.population`.
- Q-25: `adaptive_switching(X, y, rng, return_scores=False)`; `inner_nsga2(archive, predictor, domains, rng) ->
  list[Genotype]`; `subset_selection(...)` zwraca maskę bool.
- Q-26: `Reinforce(space, budget, rng, reward="mnasnet"|"monas"|"adc", target=..., alpha=...)`; atrybuty `logits`,
  `target`, `n_policy_updates`; bazowa EMA z korekcją obciążenia (jak NAS-Bench-201).
- Q-27: `reward_adc` liczy względem frontu **przed** dodaniem x; ρ — odległość euklidesowa w znormalizowanej
  przestrzeni celów.
- Q-28: `crowded_winner(sample: list[Observation], population: list[Observation]) -> Observation`; `RegEvo` woła ją przez
  moduł, populacja w kolejności wieku.

**Tor MF** (Q-31)
- Metody MF: `__init__(space, budget, rng, *, max_epochs: int, **params)`; `propose(state) -> list[tuple[Genotype, int]]`
  (genotyp, epoki); odpowiedź — `Observation` w tej samej kolejności; `final_observations() -> list[Observation]`
  (tylko e = E).
- `bracket_schedule(eta, r_min, R) -> list[list[tuple[int, int]]]`, `promote_nsga2(points, k) -> list[int]`,
  `extrapolate_f2(f2_at_e, e, E) -> float`, `mf_cost(e, e_prev, E) -> float`.

**Benchmarki** (Q-32)
- Konstruktory substratów bez argumentów; `Substrate.f1_split() -> Literal["valid"]`.
- `p3net.v005.benchmarks.NB201Energy`: `__len__`, `energy(g) -> float`, `metadata() -> dict` z kluczami `gpu_model`,
  `driver`, `cuda`, `torch`, `n_warmup`, `n_samples`, `aggregate`, `quality_control`, `power_limit_w`, `clocks_locked`,
  `energy_method` (`"counter"` | `"power_integral"`), `batch_size`, `temperature_log`.
- Wynik BM-3: `results/checks/*jahs*size*`; pola zasobów w rekordach przebiegów: `resources.{peak_memory_server_mb,
  peak_memory_gpu_mb, surrogate_load_seconds, method_wall_seconds}`.

**Uzupełnienie (2026-10-17, runda 2 autora testów; przyjęte przez autora projektu):**
- Q-35: adapter SMAC3 — współrzędna genotypu i ↔ hiperparametr ConfigSpace `x{i}` z wyborami `0…k_i−1`.
- Q-36: `P3Net.diagnostics()["chain_errors"][*]["true"]` w skali log (jak `"predicted"`).

**Uzupełnienie (2026-10-18, runda 3; Q-42, przyjęte):**
- `Reinforce.stop_reason: str | None` — powód zatrzymania przed budżetem („exploration collapse …”, „search space exhausted”).
- MO-DSA: zdarzenie `cluster_step` niesie dodatkowo wartości z chwili decyzji bramki (Z-B1′): `alpha`, `thresholds`
  (po jednym na cel) i `reference_predictions` (predykcje modelu dla wszystkich rozwiązań ocenionych naprawdę przed
  kandydatem).

**Uzupełnienie (2026-10-21, runda 4; Q-43–Q-47, przyjęte):**
- `MOBOHB(space, budget, rng, *, max_epochs, ..., num_initial_samples=50)` — pierwsza partia: min(num_initial_samples,
  ⌊0.25·b⌋) różnych konfiguracji na E (Q-43).
- Linkage z VIG (E-4, Q-46): `p3net.v005.p3.linkage.cluster_distance(table, ci, cj, known=None)` i
  `build_clusters(table, rng, known=None)`; `known(a, b) -> bool`, para nieznana → odległość + 1, `known=None` = kanoniczne
  P3. `p3net.v005.elympus.vig_known(elympus_pair) -> Callable[[int, int], bool]` (Z-E7). `Pyramid.known` — to samo dla
  piramidy (P3-eLyMPuS ustawia `vig_known(self.elympus)`).
- `NB201Energy.energy(g)`: genotyp z wartościami (nazwy operacji) albo indeksami do `OPS`.
- `NB201Energy.metadata()` (Q-47) dodatkowo: `n_samples` = 5, `clock_lock_mhz` (1200), `reference_arch`, `ref_every` (5),
  `max_spread` (0.08), `max_retries` (2).
