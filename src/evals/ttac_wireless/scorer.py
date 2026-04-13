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

from evals.ttac_wireless.config import ANSWER_PATTERN, ANSWER_SEPARATOR


def extract_codes(text: str) -> list[str] | None:
    r"""Return the codes inside the last \boxed{...} in `text`, or None.

    Mirrors official utils.extract_answer: the last match wins, whitespace is
    stripped, and pipe-separated tokens are returned in source order.
    """
    matches = re.findall(ANSWER_PATTERN, text)
    if not matches:
        return None
    raw = matches[-1].strip()
    codes = [c.strip() for c in raw.split(ANSWER_SEPARATOR) if c.strip()]
    return codes or None


def official_score(predicted: list[str], gt: str) -> bool:
    """Lenient port of the official compute_score (hard-match only).

    NOT bit-identical to the competition's compute_score. Semantics:
      - Empty `predicted` returns False.
      - Whole-string equality is checked first (case-insensitive, after
        joining `predicted` with '|'). This is the lenient extension:
        the competition scorer would return False for a multi-code
        prediction against a `gt` of the same shape, because its
        recursion compares each split alternative against the joined
        prediction as a raw string.
      - Otherwise, if `gt` contains '|', it is split and each alternative
        is compared (order-sensitive) to the joined `pred_str`.
      - Case-insensitive throughout.
    """
    if not predicted:
        return False
    pred_str = ANSWER_SEPARATOR.join(predicted).strip().lower()
    gt_clean = gt.strip().lower()
    if pred_str == gt_clean:
        return True
    if ANSWER_SEPARATOR in gt_clean:
        return any(pred_str == g.strip() for g in gt_clean.split(ANSWER_SEPARATOR))
    return False


def build_score_metadata(
    predicted: list[str] | None,
    gt: str,
    tag: str,
    tool_calls: int,
) -> dict:
    """Per-sample telemetry dict consumed by the custom @metric functions.

    `strict_match` is set-equality on codes (does `predicted` contain exactly
    the alternatives listed in `gt`, order-independent, no extras). This is a
    deliberately stricter, order-agnostic signal than `official_score`: a
    sample can have `value=INCORRECT` and `strict_match=True` (e.g. agent
    emitted all alternatives in the "wrong" order under the official raw-
    string compare). It can also have `value=CORRECT` and `strict_match=False`
    (agent matched one alternative but did not list them all).
    """
    pred = predicted or []
    expected = sorted({c.strip() for c in gt.split(ANSWER_SEPARATOR) if c.strip()})
    return {
        "predicted": sorted(pred),
        "expected": expected,
        "tag": tag,
        # Order-agnostic set equality; see docstring for semantics vs value.
        "strict_match": sorted(pred) == expected,
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
            return 0.0
        to_float = value_to_float()
        return sum(to_float(s.score.value) for s in subset) / len(subset)

    return compute


@metric
def accuracy_multiple() -> Metric:
    def compute(scores: list[SampleScore]) -> float:
        subset = [s for s in scores if s.score.metadata.get("tag") == "multiple-answer"]
        if not subset:
            return 0.0
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
        metadata = build_score_metadata(predicted, target.text, tag, tool_calls)

        if predicted is None:
            return Score(
                value=INCORRECT,
                answer=r"no \boxed{} found",
                metadata=metadata,
            )

        value = CORRECT if official_score(predicted, target.text) else INCORRECT
        return Score(
            value=value,
            answer=ANSWER_SEPARATOR.join(predicted),
            metadata=metadata,
        )

    return score
