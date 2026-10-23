"""Level-1 tests for MO-LS, local search with random scalarisation (card
`notes/plans/v005-sources/mo-ls.md`, W-L1-W-L5).

Source: den Ottelander et al., Local Search is a Remarkably Strong Baseline
for NAS, EMO 2021, §3; code github.com/tdenottelander/MacroNAS
(`src/SearchAlgorithms/MO/LS.cpp`). Card decisions: L-1 b (online min-max
normalisation), L-2 (lambda ~ U(0, 1) per round), O-L1, O-L2.

The proposal stream is parsed into rounds: a round starts from a random
solution, then for every variable (once, random order) proposes all its
other values at the current solution; MO-LS is a state machine proposing one
genotype per call (interfaces §0).
"""

from __future__ import annotations

import random

import pytest

from ._support import (
    CountingObjective,
    assert_budget_respected,
    diff_positions,
    drive,
    drive_batches,
    make,
    space_of,
)

DOM = [8, 8, 8, 8]  # 4096 genotypes: duplicates and accidental neighbours rare


def _mols():
    from p3net.v005.baselines.mo_ls import MOLS

    return MOLS


def _f_identical(seed=0):
    """f1 == f2 with distinct random values (a rugged landscape, so walks end
    in different places and rarely revisit H_t): a move is an improvement
    for every lambda and every normalisation, so the expected walk is known."""
    table: dict[tuple, float] = {}

    def f(g):
        g = tuple(g.values) if hasattr(g, "values") else tuple(g)
        if g not in table:
            table[g] = 1.0 + random.Random(hash((seed,) + g)).random()
        return table[g]

    return f


def _parse(stream, n):
    """Split the proposal stream into rounds. A round = start + blocks; a
    block = all proposals that change one variable v of the current solution.
    The solution after a block is inferred from the next block (it differs
    from the new current solution in one other variable), so moves are read
    from the stream, not assumed. Returns rounds as dicts."""
    rounds = []
    i = 0
    while i < len(stream):
        start = stream[i]
        cur = start
        i += 1
        blocks = []
        order: list[int] = []
        while i < len(stream) and len(order) < n:
            d = diff_positions(stream[i], cur)
            if len(d) != 1 or d[0] in order:
                break
            v = d[0]
            block = []
            while i < len(stream) and diff_positions(stream[i], cur) == [v]:
                block.append(stream[i])
                i += 1
            order.append(v)
            after = None
            if i < len(stream) and len(order) < n:
                nxt = stream[i]
                # the new current solution differs from cur at most at v, so its
                # v-value is nxt[v] (the move may go to a value already in H_t)
                c = cur[:v] + (nxt[v],) + cur[v + 1 :]
                d = diff_positions(nxt, c)
                if len(d) == 1 and d[0] not in order:
                    after = c
            blocks.append({"var": v, "cur": cur, "block": block, "after": after})
            if after is not None:
                cur = after
        rounds.append({"start": start, "order": order, "blocks": blocks, "final": cur})
    return rounds


def _stream(seed, budget, f1, f2):
    obj = CountingObjective(f1, f2)
    batches = drive_batches(make(_mols(), space_of(DOM), budget, seed), obj, budget)
    assert all(len(b) == 1 for b in batches), "MO-LS must propose one genotype per call"
    return [b[0] for b in batches]


def test_WL2_WL4_one_round_each_variable_once_all_values_then_restart():
    """W-L2 (L3): in a round every variable is visited once, in random order,
    and all its other values are evaluated; W-L4 (L4, loop = false): no
    second pass -- after one round a new random start follows (a start that
    neighbours the previous round's result would mean a second pass)."""
    f = _f_identical()
    stream = _stream(0, 300, f, f)
    rounds = _parse(stream, len(DOM))
    complete = rounds[:-1]
    assert len(complete) >= 5
    evaluated: set[tuple] = set()
    last_blk = (
        rounds[-1]["blocks"][-1] if rounds[-1]["blocks"] else None
    )  # may be cut by the budget
    for r in rounds:
        evaluated.add(r["start"])
        for blk in r["blocks"]:
            v, cur = blk["var"], blk["cur"]
            got = {g[v] for g in blk["block"]}
            assert len(got) == len(blk["block"])
            known = {x for x in range(DOM[v]) if cur[:v] + (x,) + cur[v + 1 :] in evaluated}
            if blk is not last_blk:
                assert got | known | {cur[v]} == set(range(DOM[v])), (
                    f"values of x{v} not all evaluated"
                )
            evaluated.update(blk["block"])
    # a round whose walk enters an already explored local optimum has its
    # remaining blocks fully in H_t (free, invisible) -- allowed, but rare
    full = [r for r in complete if sorted(r["order"]) == list(range(len(DOM)))]
    assert len(full) >= 0.7 * len(complete), [r["order"] for r in complete]
    assert all(len(set(r["order"])) == len(r["order"]) for r in rounds)
    assert len({tuple(r["order"]) for r in full}) > 1, "variable order is not random"
    # the last move of a round is not observable, so a second pass would start
    # within Hamming distance 2 of the inferred result -- every time; a random
    # start does so with probability ~8 %.
    near = [len(diff_positions(b["start"], a["final"])) <= 2 for a, b in zip(rounds, rounds[1:])]
    assert sum(near) <= max(1, 0.3 * len(near)), (
        "new rounds start next to the previous result: second pass?"
    )


def test_WL3_move_only_on_strict_improvement():
    """W-L3 (L3): after a variable's values are evaluated, the walk moves to
    the best one iff it strictly improves the scalarisation (f1 == f2: f
    strictly smaller), otherwise stays."""
    f = _f_identical(1)
    rounds = _parse(_stream(1, 300, f, f), len(DOM))
    checked = moved = 0
    for r in rounds:
        for blk in r["blocks"]:
            if blk["after"] is None:
                continue
            v, cur = blk["var"], blk["cur"]
            options = [cur] + [cur[:v] + (x,) + cur[v + 1 :] for x in range(DOM[v]) if x != cur[v]]
            best = min(options, key=f)
            expected = best if f(best) < f(cur) else cur
            assert blk["after"] == expected, "walk did not move to the strictly best value"
            checked += 1
            moved += expected != cur
    assert checked > 10 and moved > 0


def test_WL3_ties_do_not_move():
    """W-L3 (strict increase): on a flat landscape no move is made -- every
    block is proposed around the round's start."""
    obj = CountingObjective(lambda g: 1.0, lambda g: 1.0)
    batches = drive_batches(make(_mols(), space_of(DOM), 60, 2), obj, 60)
    stream = [b[0] for b in batches]
    start = stream[0]
    for g in stream[1 : 1 + sum(k - 1 for k in DOM)]:
        assert len(diff_positions(g, start)) == 1, "moved on a tie"


def test_WL1_new_random_start_and_new_lambda_each_round():
    """W-L1 (L1, L2): each round starts from a new random solution with a new
    lambda ~ U(0, 1). With f2 = C - f1 (equal ranges) a move lowers the
    values iff lambda > 0.5: within a round all moves go one way, across
    rounds both directions occur."""

    def f1(g):
        g = tuple(g.values) if hasattr(g, "values") else tuple(g)
        return 1.0 + sum(g)

    rounds = _parse(_stream(3, 700, f1, lambda g: 100.0 - f1(g)), len(DOM))
    dirs = []
    for r in rounds:
        d = {
            1 if b["after"][b["var"]] < b["cur"][b["var"]] else -1
            for b in r["blocks"]
            if b["after"] is not None and b["after"] != b["cur"]
        }
        assert len(d) <= 1, "moves in one round go both ways: lambda changed within a round"
        dirs.extend(d)
    assert set(dirs) == {1, -1}, "lambda is not redrawn per round"
    starts = [r["start"] for r in rounds]
    assert len(set(starts)) == len(starts), "a start repeated"


def test_WL5_online_normalisation():
    """W-L5 (L-1 b): normalisation by the current min/max of evaluated points."""
    from p3net.v005.common import online_minmax

    norm = online_minmax([(1.0, 5.0), (3.0, 9.0)])
    assert norm((1.0, 9.0)) == (0.0, 1.0)
    assert norm((2.0, 7.0)) == (0.5, 0.5)


@pytest.mark.parametrize("budget", [1, 23, 150])
def test_WL5_duplicates_free_budget_exact(budget):
    """W-L5 (O-L1, O-L2, L7): the current value of a variable (and any
    genotype already in H_t) is not re-evaluated; exactly b evaluations, also
    when the budget ends inside a round."""
    obj = CountingObjective(_f_identical(4), _f_identical(4))
    drive(make(_mols(), space_of([4] * 5), budget, 4), obj, budget)
    assert_budget_respected(obj, budget, exact=True)
