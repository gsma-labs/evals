"""TTAC Wireless: 5G drive-test troubleshooting evaluation."""

from inspect_ai import Task, task
from inspect_ai.agent import AgentPrompt, AgentState, react
from inspect_ai.model import ChatMessageAssistant, ChatMessageSystem, ChatMessageUser
from inspect_ai.solver import Solver, TaskState, solver
from inspect_ai.tool import Tool, ToolSource
from inspect_ai.util import store

from evals.ttac_wireless.config import (
    COMPOSE_FILE,
    FINAL_NUDGE,
    MAX_TOOL_CALLS,
    MESSAGE_LIMIT,
    SYSTEM_PROMPT_MULTIPLE,
    SYSTEM_PROMPT_SINGLE,
)
from evals.ttac_wireless.samples import load_dataset
from evals.ttac_wireless.scorer import official_scorer
from evals.ttac_wireless.tools import filter_allowed


class ScenarioToolSource(ToolSource):
    async def tools(self) -> list[Tool]:
        allowed = store().get("allowed_tools", ["all"])
        return filter_allowed(allowed)


@solver
def prepare_scenario(faithful: bool = False) -> Solver:
    """Set scenario_id + tag in store; inject tag-routed system prompt."""

    async def solve(state: TaskState, generate):
        tag = state.metadata.get("tag", "multiple-answer")
        store().set("scenario_id", state.metadata["scenario_id"])
        store().set("allowed_tools", state.metadata.get("allowed_tools", ["all"]))
        if not faithful:
            prompt = (
                SYSTEM_PROMPT_SINGLE
                if tag == "single-answer"
                else SYSTEM_PROMPT_MULTIPLE
            )
            state.messages = [ChatMessageSystem(content=prompt), *state.messages]
        return state

    return solve


async def enforce_tool_budget(state: AgentState) -> bool | str:
    """Cap tool calls at MAX_TOOL_CALLS; nudge once, then hard-stop."""
    tool_calls = sum(
        len(m.tool_calls or [])
        for m in state.messages
        if isinstance(m, ChatMessageAssistant)
    )
    if tool_calls < MAX_TOOL_CALLS:
        return True
    already_nudged = any(
        isinstance(m, ChatMessageUser) and FINAL_NUDGE in m.text for m in state.messages
    )
    if already_nudged:
        return False
    return FINAL_NUDGE


@task
def ttac_wireless(full: bool = False, faithful: bool = False) -> Task:
    """5G wireless network troubleshooting benchmark (TTAC Track A)."""
    dataset = load_dataset(full, faithful=faithful)

    return Task(
        dataset=dataset,
        solver=[
            prepare_scenario(faithful=faithful),
            react(
                prompt=AgentPrompt(
                    instructions=None,
                    handoff_prompt=None,
                    assistant_prompt=None,
                    submit_prompt=None,
                ),
                tools=[ScenarioToolSource()],
                submit=False,
                on_continue=enforce_tool_budget,
            ),
        ],
        scorer=official_scorer(),
        sandbox=("docker", COMPOSE_FILE),
        message_limit=MESSAGE_LIMIT,
    )
