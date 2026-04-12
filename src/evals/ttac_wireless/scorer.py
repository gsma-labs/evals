r"""TTAC Wireless scorer. IoU over answer code sets extracted from \\boxed{}."""

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


def extract_codes(text: str) -> set[str] | None:
    r"""Pull answer codes from \\boxed{C3|C5} notation. Returns None if no match."""
    match = re.search(ANSWER_PATTERN, text)
    if not match:
        return None

    raw = match.group(1).strip()
    codes = {c.strip() for c in raw.split(ANSWER_SEPARATOR) if c.strip()}
    return codes


def compute_iou(predicted: set[str], expected: set[str]) -> float:
    """Intersection over union of two code sets."""
    overlap = predicted & expected
    combined = predicted | expected

    if not combined:
        return 0.0
    return len(overlap) / len(combined)


@scorer(metrics=[accuracy(), stderr()])
def iou_scorer():
    async def score(state: TaskState, target: Target) -> Score:
        raw_answer = state.output.completion

        predicted_codes = extract_codes(raw_answer)
        if predicted_codes is None:
            return Score(value=INCORRECT, answer="no \\boxed{} found")

        expected_codes = {c.strip() for c in target.text.split(ANSWER_SEPARATOR)}

        iou = compute_iou(predicted_codes, expected_codes)
        is_correct = iou == 1.0

        return Score(
            value=CORRECT if is_correct else INCORRECT,
            answer=ANSWER_SEPARATOR.join(sorted(predicted_codes)),
            metadata={
                "iou": iou,
                "predicted": sorted(predicted_codes),
                "expected": sorted(expected_codes),
            },
        )

    return score
