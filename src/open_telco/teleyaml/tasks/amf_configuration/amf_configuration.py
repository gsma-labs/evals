from textwrap import dedent
from pathlib import Path

from dotenv import load_dotenv
from inspect_ai import Task, task
from inspect_ai.dataset import FieldSpec, hf_dataset
from inspect_ai.scorer import accuracy, stderr
from inspect_ai.solver import system_message, generate

from open_telco.teleyaml.judge import judge

load_dotenv()


SYSTEM_PROMPT = dedent("""
You are an expert 5G Core Network Engineer and Configuration Specialist.
You are assisting a user with {Main Category} by converting requests into
server-side YAML configurations for {Category}.

<context>
{Context}
</context>

Your response must be valid YAML.
""")


def get_rubric() -> str:
    """Load AMF configuration rubric."""
    path = Path(__file__).parent / "rubric.txt"
    return path.read_text()


def assign_rubric(dataset_samples: list) -> list:
    """Attach rubric to dataset samples."""
    rubric = get_rubric()
    for sample in dataset_samples:
        sample.metadata["rubric"] = rubric
    return dataset_samples


@task
def amf_configuration() -> Task:
    dataset = hf_dataset(
        "otellm/gsma-sample-data",
        name="teleyaml",
        split="test",
        sample_fields=FieldSpec(
            input="Question",
            target="Answer",
            metadata=["Main Category", "Category", "Context"],
        ),
    )

    filtered_dataset = [
        sample for sample in dataset
        if sample.metadata.get("Category") == "AMF Configuration"
    ]

    judge_models = [
        "openrouter/openai/gpt-oss-120b",
    ]

    return Task(
        dataset=assign_rubric(filtered_dataset),
        solver=[system_message(SYSTEM_PROMPT), generate()],
        scorer=judge(model=judge_models),
        metrics=[accuracy(), stderr()],
    )
