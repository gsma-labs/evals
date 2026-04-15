"""Scorers for network diagnosis evaluation tasks."""

import json
from typing import Literal

from inspect_ai.scorer import Score, Scorer, Target, accuracy, mean, scorer, stderr
from inspect_ai.solver import TaskState

from evals.nika.core.tools import Submission

TaskLevel = Literal["detection", "localization", "rca", "full"]

DETECTION_WEIGHT = 0.2
LOCALIZATION_WEIGHT = 0.4
RCA_WEIGHT = 0.4


def compute_metrics(predicted: list[str], actual: list[str]) -> tuple[float, float, float, float]:
    """Compute accuracy, precision, recall, F1 for set comparison."""
    pred = {p.lower() for p in predicted}
    gold = {a.lower() for a in actual}

    if not gold and not pred:
        return (1.0, 1.0, 1.0, 1.0)
    if not pred or not gold:
        return (0.0, 0.0, 0.0, 0.0)

    tp = len(pred & gold)
    fp = len(pred - gold)
    fn = len(gold - pred)

    acc = tp / len(gold)
    prec = tp / (tp + fp)
    rec = tp / (tp + fn)
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0

    return (acc, prec, rec, f1)


@scorer(metrics=[accuracy(), stderr()])
def detection_scorer() -> Scorer:
    """Score whether the agent correctly detected an anomaly.

    Returns 1.0 if the agent's `is_anomaly` matches the expected value,
    0.0 otherwise.
    """

    async def score(state: TaskState, target: Target) -> Score:
        expected_anomaly, _, _ = json.loads(target.text)
        sub = state.store_as(Submission)

        if sub.is_anomaly is None:
            return Score(value=0.0, answer="No submission")

        correct = sub.is_anomaly == expected_anomaly
        return Score(
            value=1.0 if correct else 0.0,
            answer=str(sub.is_anomaly),
            explanation=f"Expected: {expected_anomaly}",
        )

    return score


@scorer(metrics={"*": [mean(), stderr()]})
def localization_scorer() -> Scorer:
    """Score device localization using F1 metrics.

    Compares the agent's `faulty_devices` against expected devices,
    returning accuracy, precision, recall, and F1 scores.
    """

    async def score(state: TaskState, target: Target) -> Score:
        _, expected_devices, _ = json.loads(target.text)
        sub = state.store_as(Submission)

        if sub.is_anomaly is None:
            return Score(
                value={"accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1": 0.0},
                answer="No submission",
            )

        acc, prec, rec, f1 = compute_metrics(sub.faulty_devices, expected_devices)
        return Score(
            value={"accuracy": acc, "precision": prec, "recall": rec, "f1": f1},
            answer=", ".join(sub.faulty_devices) or "(none)",
            explanation=f"Expected: {', '.join(expected_devices) or '(none)'}",
        )

    return score


@scorer(metrics={"*": [mean(), stderr()]})
def rca_scorer() -> Scorer:
    """Score root cause analysis using F1 metrics.

    Compares the agent's `root_cause_names` against expected causes,
    returning accuracy, precision, recall, and F1 scores.
    """

    async def score(state: TaskState, target: Target) -> Score:
        _, _, expected_rca = json.loads(target.text)
        if isinstance(expected_rca, str):
            expected_rca = [expected_rca]

        sub = state.store_as(Submission)

        if sub.is_anomaly is None:
            return Score(
                value={"accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1": 0.0},
                answer="No submission",
            )

        acc, prec, rec, f1 = compute_metrics(sub.root_cause_names, expected_rca)
        return Score(
            value={"accuracy": acc, "precision": prec, "recall": rec, "f1": f1},
            answer=", ".join(sub.root_cause_names) or "(none)",
            explanation=f"Expected: {', '.join(expected_rca) or '(none)'}",
        )

    return score


@scorer(metrics={"*": [mean(), stderr()]})
def full_scorer() -> Scorer:
    """Score full diagnosis with weighted composite.

    Combines detection (20%), localization F1 (40%), and RCA F1 (40%)
    into a single weighted score.
    """

    async def score(state: TaskState, target: Target) -> Score:
        expected_anomaly, expected_devices, expected_rca = json.loads(target.text)
        if isinstance(expected_rca, str):
            expected_rca = [expected_rca]

        sub = state.store_as(Submission)

        if sub.is_anomaly is None:
            return Score(
                value={"score": 0.0, "detection": 0.0, "localization_f1": 0.0, "rca_f1": 0.0},
                answer="No submission",
            )

        det = 1.0 if sub.is_anomaly == expected_anomaly else 0.0
        _, _, _, loc_f1 = compute_metrics(sub.faulty_devices, expected_devices)
        _, _, _, rca_f1 = compute_metrics(sub.root_cause_names, expected_rca)

        final = DETECTION_WEIGHT * det + LOCALIZATION_WEIGHT * loc_f1 + RCA_WEIGHT * rca_f1

        return Score(
            value={"score": final, "detection": det, "localization_f1": loc_f1, "rca_f1": rca_f1},
            answer=f"anomaly={sub.is_anomaly}, devices={sub.faulty_devices}, rca={sub.root_cause_names}",
        )

    return score
