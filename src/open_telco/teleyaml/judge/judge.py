from typing import Callable
from functools import lru_cache, partial
from pathlib import Path
from inspect_ai.scorer import scorer, accuracy, stderr, model_graded_qa, multi_scorer, Scorer
from inspect_ai.solver import TaskState
from inspect_ai.model import Model

from open_telco.teleyaml.judge.prompts import JUDGE_TEMPLATE, JUDGE_INSTRUCTIONS, SCORE_PATTERN


@lru_cache
def get_rubric(category: str) -> str:
    """Load rubric content based on category."""
    task_folder = category.lower().replace(' ', '_')
    path = Path(__file__).parent.parent / "tasks" / task_folder / "rubric.txt"
    return path.read_text()


def assign_rubrics(dataset_samples: list) -> list:
    """Attach rubrics to dataset samples based on category."""
    for sample in dataset_samples:
        category = sample.metadata.get("Category") or sample.metadata.get("category")
        sample.metadata["rubric"] = get_rubric(category)
    return dataset_samples


@scorer(metrics=[accuracy(), stderr()])
def judge(
    template: str | None = JUDGE_TEMPLATE,
    instructions: str | None = JUDGE_INSTRUCTIONS,
    grade_pattern: str | None = SCORE_PATTERN,
    include_history: bool | Callable[[TaskState], str] = False,
    model: list[str | Model] | str | Model | None = None,
) -> Scorer:
    """Score a question/answer task using a model"""
    get_scorer = partial(
        model_graded_qa,
        template=template,
        instructions=instructions,
        grade_pattern=grade_pattern,
        include_history=include_history,
    )

    # if only a single model is passed, return a single scorer
    if model is None or not isinstance(model, list):
        return get_scorer(model=model)

    # otherwise, use multi scorer
    assert isinstance(model, list)
    scorers = [get_scorer(model=m) for m in model]
    return multi_scorer(scorers, reducer="mean")
