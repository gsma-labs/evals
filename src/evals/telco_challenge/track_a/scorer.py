r"""TTAC Wireless scorer. Port of official compute_score with Inspect metrics."""

import re

from inspect_ai.scorer import (
    CORRECT,
    INCORRECT,
    Metric,
    SampleScore,
    Score,
    Target,
    accuracy,
    metric,
    scorer,
    stderr,
    value_to_float,
)
from inspect_ai.solver import TaskState

from evals.telco_challenge.track_a.config import ANSWER_PATTERN, ANSWER_SEPARATOR


def extract_codes(text: str) -> list[str] | None:
    r"""Return the codes inside the last \boxed{...} in `text`, or None.

    Mirrors official utils.extract_answer: the last match wins, whitespace is
    stripped, and pipe-separated tokens are returned in source order.
    """
    matches = re.findall(ANSWER_PATTERN, text)
    if not matches:
        return None
    raw = matches[-1].strip()
    raw = re.sub(r"[{}]", "", raw)
    codes = [c.strip() for c in raw.split(ANSWER_SEPARATOR) if c.strip()]
    return codes or None


def official_score(predicted: list[str], gt: str) -> float:
    """IoU-based scorer (order-insensitive, case-insensitive).

    Returns:
      - 0.0 when `predicted` is empty or there is no overlap with `gt`.
      - 1.0 for exact set match (single-answer: one code equals gt).
      - |intersection| / |union| for partial multi-answer overlap.
    """
    if not predicted:
        return 0.0
    pred_set = {c.strip().lower() for c in predicted}
    gt_set = {c.strip().lower() for c in gt.split(ANSWER_SEPARATOR) if c.strip()}
    intersection = pred_set & gt_set
    union = pred_set | gt_set
    if not union:
        return 0.0
    return len(intersection) / len(union)


def build_score_metadata(
    predicted: list[str] | None,
    gt: str,
    tag: str,
    tool_calls: int,
    iou: float,
) -> dict:
    """Per-sample telemetry dict consumed by the custom @metric functions.

    `strict_match` is True when IoU equals 1.0 (exact set match between
    predicted codes and ground-truth alternatives, order-independent).
    """
    pred = predicted or []
    expected = sorted({c.strip() for c in gt.split(ANSWER_SEPARATOR) if c.strip()})
    return {
        "predicted": sorted(pred),
        "expected": expected,
        "tag": tag,
        "iou": iou,
        "strict_match": iou == 1.0,
        "no_answer": predicted is None,
        "num_predicted": len(pred),
        "tool_calls": tool_calls,
    }


def _count_tool_calls(state: TaskState) -> int:
    count = 0
    for m in state.messages:
        if getattr(m, "role", None) != "assistant":
            continue
        tool_calls = getattr(m, "tool_calls", None) or []
        count += len(tool_calls)
    return count


@metric
def strict_accuracy() -> Metric:
    def compute(scores: list[SampleScore]) -> float:
        flags = [bool(s.score.metadata.get("strict_match")) for s in scores]
        return sum(flags) / len(flags) if flags else 0.0

    return compute


@metric
def no_answer_rate() -> Metric:
    def compute(scores: list[SampleScore]) -> float:
        flags = [bool(s.score.metadata.get("no_answer")) for s in scores]
        return sum(flags) / len(flags) if flags else 0.0

    return compute


@metric
def mean_tool_calls() -> Metric:
    def compute(scores: list[SampleScore]) -> float:
        values = [int(s.score.metadata.get("tool_calls", 0)) for s in scores]
        return sum(values) / len(values) if values else 0.0

    return compute


@metric
def mean_options_selected() -> Metric:
    def compute(scores: list[SampleScore]) -> float:
        values = [
            int(s.score.metadata.get("num_predicted", 0))
            for s in scores
            if not s.score.metadata.get("no_answer")
        ]
        return sum(values) / len(values) if values else 0.0

    return compute


@metric
def accuracy_single() -> Metric:
    def compute(scores: list[SampleScore]) -> float:
        subset = [s for s in scores if s.score.metadata.get("tag") == "single-answer"]
        if not subset:
            return float("nan")
        to_float = value_to_float()
        return sum(to_float(s.score.value) for s in subset) / len(subset)

    return compute


@metric
def accuracy_multiple() -> Metric:
    def compute(scores: list[SampleScore]) -> float:
        subset = [s for s in scores if s.score.metadata.get("tag") == "multiple-answer"]
        if not subset:
            return float("nan")
        to_float = value_to_float()
        return sum(to_float(s.score.value) for s in subset) / len(subset)

    return compute


@scorer(
    metrics=[
        accuracy(),
        stderr(),
        strict_accuracy(),
        no_answer_rate(),
        mean_tool_calls(),
        mean_options_selected(),
        accuracy_single(),
        accuracy_multiple(),
    ]
)
def official_scorer():
    async def score(state: TaskState, target: Target) -> Score:
        predicted = extract_codes(state.output.completion)
        tag = state.metadata.get("tag", "multiple-answer")
        tool_calls = _count_tool_calls(state)
        iou = official_score(predicted, target.text) if predicted else 0.0
        metadata = build_score_metadata(predicted, target.text, tag, tool_calls, iou)

        if predicted is None:
            return Score(
                value=INCORRECT,
                answer=r"no \boxed{} found",
                metadata=metadata,
            )

        value = CORRECT if iou > 0 else INCORRECT
        return Score(
            value=value,
            answer=ANSWER_SEPARATOR.join(predicted),
            metadata=metadata,
        )

    return score
