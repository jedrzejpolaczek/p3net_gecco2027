# C3 — Search Spaces & Substrates Components

Defines *what* is being searched (the genotype, per benchmark) and *how*
a candidate gets a real objective value (the substrate adapter querying
each benchmark's real data). The two benchmarks deliberately do **not**
share a genotype — see below — even though both build on
`p3net.problem.genotype.SearchSpace`.

```mermaid
C4Component
  title Component diagram for search_spaces & substrates

  System_Ext(p3net_problem, "p3net.problem", "SearchSpace, Genotype, Validity")
  System_Ext(nashpobench, "nashpobench2api", "Real, in-process")
  System_Ext(jahsbench_bridge, "vendor/jahsbench-env/query_server.py", "Persistent subprocess")

  Container_Boundary(search_spaces, "search_spaces") {
    Component(cell_graph, "_cell_graph.py", "has_input_output_path", "Six-edge DAG topology + path-existence check, shared by both genotype modules")
    Component(nas_genotype, "nas_genotype.py", "nas_search_space, nas_validity, decode_nas_genotype, ContinuousThetaBounds", "JAHS-Bench-201's genotype: 6 architecture edges + discretised Theta")
    Component(nas_hpo_genotype, "nas_hpo_bench_ii_genotype.py", "nas_hpo_bench_ii_search_space, nas_hpo_bench_ii_validity, genotype_to_cellcode", "NAS-HPO-Bench-II's own, genuinely different genotype")
  }

  Container_Boundary(substrates, "substrates") {
    Component(base, "base.py", "Substrate (ABC), FidelityLevel", "objectives() = (query_f1 at r_K, analytic_f2) -- shared so it can't drift between benchmarks")
    Component(jahs_substrate, "jahs_bench_201.py", "JAHSBench201Substrate", "Bridges to the persistent subprocess")
    Component(nashpo_substrate, "nas_hpo_bench_ii.py", "NASHPOBenchIISubstrate", "In-process nashpobench2api queries")
  }

  Rel(nas_genotype, cell_graph, "path-existence validity check")
  Rel(nas_hpo_genotype, cell_graph, "path-existence validity check")
  Rel(nas_genotype, p3net_problem, "SearchSpace/Genotype/Validity")
  Rel(nas_hpo_genotype, p3net_problem, "SearchSpace/Genotype/Validity")
  Rel(jahs_substrate, base, "implements Substrate")
  Rel(nashpo_substrate, base, "implements Substrate")
  Rel(jahs_substrate, nas_genotype, "decodes genotypes it's queried with")
  Rel(nashpo_substrate, nas_hpo_genotype, "decodes genotypes it's queried with")
  Rel(jahs_substrate, jahsbench_bridge, "JSON-lines over stdin/stdout")
  Rel(nashpo_substrate, nashpobench, "In-process call")
```

## Components

| Component | Responsibility | Source |
|---|---|---|
| **_cell_graph.py** | `has_input_output_path`: the six-edge DAG topology and path-existence validity check genuinely shared by both genotype modules | `search_spaces/_cell_graph.py` |
| **nas_genotype.py** | `nas_search_space()`: 6 categorical architecture edges + discretised Θ (learning rate, weight decay, activation, augmentation). `ContinuousThetaBounds`: the separate real-valued Θ representation for the `nsganetv2_continuous` control | `search_spaces/nas_genotype.py` |
| **nas_hpo_bench_ii_genotype.py** | `nas_hpo_bench_ii_search_space()`: NAS-HPO-Bench-II's real, narrower genotype (4 cell ops, learning rate x batch size only) — verified against live data, not assumed | `search_spaces/nas_hpo_bench_ii_genotype.py` |
| **base.py** | `Substrate` (ABC): `fidelity_ladder`/`query_f1`/`analytic_f2` as the abstract contract; `objectives()` (shared, non-overridable) always queries `f1` at `r_K` and `f2` at the fixed highest-fidelity setting | `substrates/base.py` |
| **jahs_bench_201.py** | `JAHSBench201Substrate`: real queries via a persistent subprocess bridge | `substrates/jahs_bench_201.py` |
| **nas_hpo_bench_ii.py** | `NASHPOBenchIISubstrate`: real, in-process queries via `nashpobench2api` | `substrates/nas_hpo_bench_ii.py` |

## Why the two benchmarks don't share a genotype

An earlier version assumed one shared genotype module could serve both
benchmarks (they're both NAS-Bench-201-style cell graphs). Wiring real
NAS-HPO-Bench-II queries surfaced that its actual search space is
narrower (learning rate x batch size only, not JAHS-Bench-201's four
hyperparameter axes) — a real difference, not a configuration variant,
caught only by querying the live dataset rather than trusting the
structural assumption.
