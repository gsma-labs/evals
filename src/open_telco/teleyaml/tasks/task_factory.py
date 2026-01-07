"""Generic task factory for teleyaml evaluation tasks.

This module eliminates code duplication by providing a single factory function
that creates tasks for any teleyaml category (AMF, Slice, UE Provisioning).
"""

from inspect_ai import Task
from inspect_ai.dataset import FieldSpec, hf_dataset
from inspect_ai.solver import generate, system_message

from open_telco.teleyaml.constants import (
    DEFAULT_DATASET,
    DEFAULT_DATASET_NAME,
    DEFAULT_JUDGE_MODEL,
    DEFAULT_SPLIT,
    SYSTEM_PROMPT,
)
from open_telco.teleyaml.judge import assign_rubrics, judge


def create_teleyaml_task(
    category: str,
    dataset_path: str = DEFAULT_DATASET,
    dataset_name: str = DEFAULT_DATASET_NAME,
    split: str = DEFAULT_SPLIT,
    judge_model: str | list[str] | None = None,
) -> Task:
    """Create a teleyaml evaluation task for the specified category.

    Args:
        category: The task category to filter on (e.g., "AMF Configuration").
        dataset_path: HuggingFace dataset path.
        dataset_name: Dataset configuration name.
        split: Dataset split to use.
        judge_model: Model(s) to use for judging. Defaults to DEFAULT_JUDGE_MODEL.

    Returns:
        A configured Task for the specified category.
    """
    if judge_model is None:
        judge_model = DEFAULT_JUDGE_MODEL

    dataset = hf_dataset(
        dataset_path,
        name=dataset_name,
        split=split,
        sample_fields=FieldSpec(
            input="Question",
            target="Answer",
            metadata=["Main Category", "Category", "Context"],
        ),
    )

    filtered_dataset = [
        sample for sample in dataset if sample.metadata.get("Category") == category
    ]

    return Task(
        dataset=assign_rubrics(filtered_dataset),
        solver=[system_message(SYSTEM_PROMPT), generate()],
        scorer=judge(model=judge_model),
    )
