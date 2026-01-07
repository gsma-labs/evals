"""AMF Configuration evaluation task."""

from inspect_ai import Task, task

from open_telco.teleyaml.constants import (
    CATEGORY_AMF,
    DEFAULT_DATASET,
    DEFAULT_DATASET_NAME,
    DEFAULT_JUDGE_MODEL,
    DEFAULT_SPLIT,
)
from open_telco.teleyaml.tasks.task_factory import create_teleyaml_task


@task
def amf_configuration(
    dataset_path: str = DEFAULT_DATASET,
    dataset_name: str = DEFAULT_DATASET_NAME,
    split: str = DEFAULT_SPLIT,
    judge_model: str | list[str] | None = DEFAULT_JUDGE_MODEL,
) -> Task:
    """Evaluate model on AMF Configuration YAML generation."""
    return create_teleyaml_task(
        category=CATEGORY_AMF,
        dataset_path=dataset_path,
        dataset_name=dataset_name,
        split=split,
        judge_model=judge_model,
    )
