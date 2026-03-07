from inspect_ai import Task, task
from inspect_ai.dataset import Sample, hf_dataset
from inspect_ai.scorer import choice
from inspect_ai.solver import multiple_choice

from evals._utils import resolve_dataset

DEFAULT_DATASET = "GSMA/ot-lite"
DEFAULT_DATASET_NAME = "sixg_bench"
DEFAULT_SPLIT = "test"


def record_to_sample(record: dict) -> Sample:
    """Convert a 6G-Bench record to an Inspect multiple-choice sample."""
    return Sample(
        input=record["question"],
        choices=record["choices"],
        target=chr(65 + record["answer"]),
        metadata={"task_id": record.get("task_id")},
    )


@task
def sixg_bench(
    task_id: str | None = None,
    dataset_path: str = DEFAULT_DATASET,
    split: str = DEFAULT_SPLIT,
    full: bool = False,
) -> Task:
    """6G-Bench: multiple-choice reasoning across AI-native 6G tasks."""
    ds_path, ds_split = resolve_dataset(full, dataset_path, DEFAULT_DATASET, split)
    dataset = hf_dataset(
        ds_path,
        name=DEFAULT_DATASET_NAME,
        sample_fields=record_to_sample,
        split=ds_split,
    )
    if task_id is not None:
        dataset = dataset.filter(
            lambda sample: sample.metadata is not None
            and sample.metadata.get("task_id") == task_id
        )
    return Task(
        dataset=dataset,
        solver=multiple_choice(cot=False),
        scorer=choice(),
    )
