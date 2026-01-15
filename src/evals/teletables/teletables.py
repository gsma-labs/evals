from inspect_ai import Task, task
from inspect_ai.dataset import Sample, hf_dataset
from inspect_ai.scorer import choice
from inspect_ai.solver import multiple_choice

DEFAULT_DATASET = "GSMA/open_telco"
DEFAULT_DATASET_NAME = "teletables"
DEFAULT_SPLIT = "test"


def record_to_sample(record: dict) -> Sample:
    """Convert dataset record to Sample with subject metadata."""
    return Sample(
        input=record["question"],
        choices=record["choices"],
        target=chr(65 + record["answer"]),
    )


@task
def teletables(
    dataset_path: str = DEFAULT_DATASET,
    split: str = DEFAULT_SPLIT,
) -> Task:
    dataset = hf_dataset(
        dataset_path,
        name=DEFAULT_DATASET_NAME,
        sample_fields=record_to_sample,
        split=split,
    )
    return Task(
        dataset=dataset,
        solver=multiple_choice(cot=False),
        scorer=choice(),
    )
