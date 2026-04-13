"""TTAC Wireless: 5G drive-test troubleshooting evaluation."""

from inspect_ai import Task, task
from inspect_ai.agent import react
from inspect_ai.model import ChatMessageSystem
from inspect_ai.solver import Solver, TaskState, solver
from inspect_ai.util import store

from evals.ttac_wireless.config import (
    COMPOSE_FILE,
    MESSAGE_LIMIT,
    SYSTEM_PROMPT_MULTIPLE,
    SYSTEM_PROMPT_SINGLE,
)
from evals.ttac_wireless.samples import load_dataset
from evals.ttac_wireless.scorer import official_scorer
from evals.ttac_wireless.tools import filter_allowed


@solver
def prepare_scenario() -> Solver:
    """Set scenario_id + tag in store; inject tag-routed system prompt; set tools."""

    async def solve(state: TaskState, generate):
        tag = state.metadata.get("tag", "multiple-answer")
        allowed = state.metadata.get("allowed_tools", ["all"])

        store().set("scenario_id", state.metadata["scenario_id"])
        store().set("tag", tag)

        prompt = (
            SYSTEM_PROMPT_SINGLE if tag == "single-answer" else SYSTEM_PROMPT_MULTIPLE
        )
        state.messages = [ChatMessageSystem(content=prompt), *state.messages]

        state.tools = filter_allowed(allowed)
        return state

    return solve


@task
def ttac_wireless(full: bool = False) -> Task:
    """5G wireless network troubleshooting benchmark (TTAC Track A)."""
    dataset = load_dataset(full)

    return Task(
        dataset=dataset,
        solver=[prepare_scenario(), react()],
        scorer=official_scorer(),
        sandbox=("docker", COMPOSE_FILE),
        message_limit=MESSAGE_LIMIT,
    )
