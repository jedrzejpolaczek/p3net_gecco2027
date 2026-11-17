"""Shared cell-graph connectivity check: both search_spaces/nas_genotype.py
(JAHS-Bench-201) and search_spaces/nas_hpo_bench_ii_genotype.py
(NAS-HPO-Bench-II) use the identical six-edge, four-node DAG topology and
"does an input-output path exist" validity rule -- only the operation
vocabulary and hyperparameters differ between the two benchmarks. Kept
here once rather than duplicated across the two modules."""

from __future__ import annotations

CELL_EDGES: tuple[tuple[int, int], ...] = ((0, 1), (0, 2), (1, 2), (0, 3), (1, 3), (2, 3))
"""Standard NAS-Bench-201-style cell: 4 nodes (0 = input, 3 = output), 6
directed edges forming a DAG. Fixed edge-index convention (documented
since NAS-Bench-201 itself doesn't mandate one):

  edge 0: (0 -> 1)   edge 1: (0 -> 2)   edge 2: (1 -> 2)
  edge 3: (0 -> 3)   edge 4: (1 -> 3)   edge 5: (2 -> 3)
"""
N_NODES = 4
N_EDGES = len(CELL_EDGES)


def has_input_output_path(edges: tuple, none_value) -> bool:
    """True iff a path from node 0 to node N_NODES-1 exists using only
    edges whose operation is not `none_value` (a "none"/zero edge removes
    that connection from the graph)."""
    adjacency: dict[int, list[int]] = {n: [] for n in range(N_NODES)}
    for (src, dst), op in zip(CELL_EDGES, edges):
        if op != none_value:
            adjacency[src].append(dst)

    visited = {0}
    frontier = [0]
    while frontier:
        node = frontier.pop()
        for neighbour in adjacency[node]:
            if neighbour not in visited:
                visited.add(neighbour)
                frontier.append(neighbour)
    return (N_NODES - 1) in visited
