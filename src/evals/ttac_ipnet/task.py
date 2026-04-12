"""TTAC IP Network: multi-vendor CLI troubleshooting evaluation."""

from inspect_ai import Task, task
from inspect_ai.agent import react
from inspect_ai.solver import TaskState, solver
from inspect_ai.util import store

from evals.ttac_ipnet.config import COMPOSE_FILE, MESSAGE_LIMIT, SYSTEM_PROMPT
from evals.ttac_ipnet.samples import load_dataset
from evals.ttac_ipnet.scorer import ttac_ipnet_scorer
from evals.ttac_ipnet.tools import execute_cli_command


@solver
def set_question():
    async def solve(state: TaskState, generate):
        store().set("question_number", state.metadata["question_number"])
        return state

    return solve


@task
def ttac_ipnet(grader_model: str | None = None) -> Task:
    """IP network fault diagnosis benchmark (TTAC Track B)."""
    dataset = load_dataset()

    return Task(
        dataset=dataset,
        solver=[
            set_question(),
            react(prompt=SYSTEM_PROMPT, tools=[execute_cli_command()]),
        ],
        scorer=ttac_ipnet_scorer(grader_model),
        sandbox=("docker", COMPOSE_FILE),
        message_limit=MESSAGE_LIMIT,
    )
