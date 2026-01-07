"""Calibration tasks for validating LLM-as-a-judge performance."""

import re

from inspect_ai import Task, task
from inspect_ai.dataset import MemoryDataset, Sample, hf_dataset, FieldSpec
from inspect_ai.scorer import Score, Target, mean, scorer
from inspect_ai.solver import TaskState, generate, system_message

from open_telco.teleyaml.constants import CATEGORY_AMF
from open_telco.teleyaml.judge.judge import assign_rubrics, get_rubric
from open_telco.teleyaml.judge.prompts import (
    JUDGE_INSTRUCTIONS,
    JUDGE_TEMPLATE,
    SCORE_PATTERN,
)
from open_telco.teleyaml.tasks.amf_configuration.calibration_samples import (
    get_calibration_samples,
)


def _build_system_prompt() -> str:
    """Build judge system prompt with rubric and instructions."""
    return JUDGE_TEMPLATE.format(
        question="{question}",
        rubric="{rubric}",
        answer="{solution}",
        instructions=JUDGE_INSTRUCTIONS,
    )


@scorer(metrics=[mean()])
def mae_scorer():
    """Score by computing absolute error between predicted and ground truth."""

    async def score(state: TaskState, target: Target) -> Score:
        response = state.output.completion
        ground_truth = float(target.text)

        match = re.search(SCORE_PATTERN, response)
        predicted = float(match.group(1)) if match else 0.0
        error = abs(predicted - ground_truth)

        return Score(
            value=error,
            answer=str(predicted),
            explanation=response,
            metadata={"predicted_score": predicted, "ground_truth": ground_truth},
        )

    return score


@task
def judge_eval() -> Task:
    """Evaluate LLM-as-a-judge performance on validation dataset."""
    dataset = hf_dataset(
        "otellm/teleyaml",
        split="test",
        sample_fields=FieldSpec(
            input="question",
            target="score",
            metadata=["solution", "question", "category"],
        ),
    )

    return Task(
        dataset=assign_rubrics(list(dataset)),
        solver=[system_message(_build_system_prompt()), generate()],
        scorer=mae_scorer(),
    )


@task
def judge_calibration() -> Task:
    """Evaluate LLM-as-a-judge on calibration samples with granular scores."""
    calibration_data = get_calibration_samples()
    rubric = get_rubric(CATEGORY_AMF)

    samples = [
        Sample(
            input=item["question"],
            target=str(item["score"]),
            metadata={
                "solution": item["solution"],
                "question": item["question"],
                "category": item["category"],
                "rubric": rubric,
                "expected_explanation": item["explanation"],
            },
        )
        for item in calibration_data
    ]

    dataset = MemoryDataset(samples=samples)

    return Task(
        dataset=dataset,
        solver=[system_message(_build_system_prompt()), generate()],
        scorer=mae_scorer(),
    )
