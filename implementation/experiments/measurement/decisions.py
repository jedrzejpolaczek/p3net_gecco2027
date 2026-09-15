"""Quality of surrogate decisions (measures 1.1), from decision logs whose
records have been labelled with real f1 values by scripts/posthoc_metrics.py.

"improvement" records (p3net.harness.decision_log) form a binary
classification: predicted positive = the surrogate accepted the candidate;
actual positive = the candidate really improves f1 over the reference by at
least the decision's own threshold, f1(reference) - f1(candidate) >=
threshold, at full fidelity.

  * confusion counts TP, FP, TN, FN; precision, recall, F1, FPR, FNR,
    Matthews correlation coefficient, balanced accuracy (NaN where a
    denominator is zero);
  * rank agreement between predicted and real improvement: Spearman's rho
    and Kendall's tau-b;
  * calibration: records binned by predicted improvement (equal-count
    bins), mean predicted vs mean real improvement per bin.

"selection" records (a predictor ranking a pool) contribute rank agreement
between predicted f1 and real f1 only.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
from scipy import stats


def _ratio(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else math.nan


def confusion(records: list[dict[str, Any]]) -> dict[str, float]:
    tp = fp = tn = fn = 0
    for r in records:
        actual = r["true_improvement"] >= r["threshold"]
        if r["accepted"]:
            tp, fp = (tp + 1, fp) if actual else (tp, fp + 1)
        else:
            fn, tn = (fn + 1, tn) if actual else (fn, tn + 1)
    precision = _ratio(tp, tp + fp)
    recall = _ratio(tp, tp + fn)
    tnr = _ratio(tn, tn + fp)
    mcc_den = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    return {
        "n": tp + fp + tn + fn,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": _ratio(2 * precision * recall, precision + recall)
        if not (math.isnan(precision) or math.isnan(recall))
        else math.nan,
        "fpr": _ratio(fp, fp + tn),
        "fnr": _ratio(fn, fn + tp),
        "mcc": _ratio(tp * tn - fp * fn, mcc_den),
        "balanced_accuracy": (recall + tnr) / 2
        if not (math.isnan(recall) or math.isnan(tnr))
        else math.nan,
    }


def rank_agreement(predicted: list[float], actual: list[float]) -> dict[str, float]:
    if len(predicted) < 3 or len(set(predicted)) < 2 or len(set(actual)) < 2:
        return {"spearman": math.nan, "kendall": math.nan, "n": len(predicted)}
    return {
        "spearman": float(stats.spearmanr(predicted, actual).statistic),
        "kendall": float(stats.kendalltau(predicted, actual).statistic),
        "n": len(predicted),
    }


def calibration(records: list[dict[str, Any]], bins: int = 10) -> list[dict[str, float]]:
    if not records:
        return []
    ordered = sorted(records, key=lambda r: r["predicted"])
    out = []
    for chunk in np.array_split(np.arange(len(ordered)), min(bins, len(ordered))):
        members = [ordered[i] for i in chunk]
        out.append(
            {
                "n": len(members),
                "mean_predicted": float(np.mean([m["predicted"] for m in members])),
                "mean_true": float(np.mean([m["true_improvement"] for m in members])),
            }
        )
    return out


def decision_quality(records: list[dict[str, Any]]) -> dict[str, Any]:
    improvement = [r for r in records if r["kind"] == "improvement"]
    selection = [r for r in records if r["kind"] == "selection"]
    result: dict[str, Any] = {}
    for source in sorted({r["source"] for r in improvement}):
        group = [r for r in improvement if r["source"] == source]
        result[source] = {
            "confusion": confusion(group),
            "rank": rank_agreement(
                [r["predicted"] for r in group], [r["true_improvement"] for r in group]
            ),
            "calibration": calibration(group),
        }
    for source in sorted({r["source"] for r in selection}):
        group = [r for r in selection if r["source"] == source]
        result[source] = {
            "rank": rank_agreement([r["predicted"] for r in group], [r["true_f1"] for r in group])
        }
    return result


def simple_regret(history_f1: list[float], best_known_f1: float) -> list[float]:
    """Best f1 found after each evaluation minus the best known f1."""
    regret, best = [], math.inf
    for value in history_f1:
        best = min(best, value)
        regret.append(best - best_known_f1)
    return regret
