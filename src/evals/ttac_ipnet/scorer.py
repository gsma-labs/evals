"""TTAC IP Network scorer.

The public dataset has no ground truth answers.
Uses model_graded_qa as an approximate scorer.
Replace with a custom scorer when answer keys become available.
"""

from inspect_ai.scorer import model_graded_qa


def ttac_ipnet_scorer(grader_model: str | None = None):
    """Return a model-graded QA scorer for IP network troubleshooting."""
    kwargs = {}
    if grader_model:
        kwargs["model"] = grader_model
    return model_graded_qa(**kwargs)
