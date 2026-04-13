r"""TTAC Wireless scorer. Port of official compute_score with Inspect metrics."""

import re

from inspect_ai.scorer import (
    CORRECT,
    INCORRECT,
    Score,
    Target,
    accuracy,
    scorer,
    stderr,
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
    """Faithful port of the official compute_score (hard-match only).

    Multi-code predictions are joined with '|' into a raw string and compared
    case-insensitively. If the raw strings match, return True. Otherwise, when
    the ground truth contains '|' it denotes alternatives; return any() over
    the split pieces. Matches the official asymmetry between prediction-join
    and gt-split.
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
    pred = predicted or []
    expected = sorted({c.strip() for c in gt.split(ANSWER_SEPARATOR) if c.strip()})
    return {
        "predicted": sorted(pred),
        "expected": expected,
        "tag": tag,
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


@scorer(metrics=[accuracy(), stderr()])
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
