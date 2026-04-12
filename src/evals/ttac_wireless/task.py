"""TTAC Wireless: 5G drive-test troubleshooting evaluation."""

from inspect_ai import Task, task
from inspect_ai.agent import react
from inspect_ai.solver import TaskState, solver
from inspect_ai.util import store

from evals.ttac_wireless.config import COMPOSE_FILE, MESSAGE_LIMIT, SYSTEM_PROMPT
from evals.ttac_wireless.samples import load_dataset
from evals.ttac_wireless.scorer import iou_scorer
from evals.ttac_wireless.tools import all_tools


@solver
def set_scenario():
    async def solve(state: TaskState, generate):
        store().set("scenario_id", state.metadata["scenario_id"])
        return state

    return solve


@task
def ttac_wireless(full: bool = False) -> Task:
    """5G wireless network troubleshooting benchmark (TTAC Track A)."""
    dataset = load_dataset(full)

    return Task(
        dataset=dataset,
        solver=[
            set_scenario(),
            react(prompt=SYSTEM_PROMPT, tools=all_tools()),
        ],
        scorer=iou_scorer(),
        sandbox=("docker", COMPOSE_FILE),
        message_limit=MESSAGE_LIMIT,
    )
