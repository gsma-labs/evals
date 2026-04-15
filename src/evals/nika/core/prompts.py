"""System prompt construction for NIKA evaluations.

Role and task requirements only; topology and task-specific context
come from build_images/templates (scenario.yaml + failure symptom).
Root cause types are loaded from data/nika/failure.yaml.
"""

from string import Template
from textwrap import dedent

# Generic task instructions
TASK_INSTRUCTIONS = dedent("""
    ## Your Task
    1. DETECT: Determine if there is a network anomaly
    2. LOCALIZE: Identify which device(s) are faulty
    3. ROOT CAUSE ANALYSIS: Identify the type(s) of failure
""").strip()

# =============================================================================
# System Prompt Template
# =============================================================================

SYSTEM_PROMPT_TEMPLATE = Template(
    dedent("""
    You are a network troubleshooting expert analyzing a network.

    $task_instructions

    ## Submitting Your Answer
    When you have completed your analysis, use the submit() tool with:
    - is_anomaly: boolean (True if anomaly detected, False if network is healthy)
    - faulty_devices: list of device names (e.g., ["leaf_router_0_0", "spine_router_0_1"])
    - root_cause_names: the type(s) of failure from the valid types above (string or list of strings for multi-fault)
""").strip()
)


def build_prompt() -> str:
    """Build the system prompt for a task.

    Uses role + generic task requirements only. Root causes are loaded
    from data/nika/failure.yaml. Topology and symptom come from
    templates (user message).
    """
    return SYSTEM_PROMPT_TEMPLATE.substitute(
        task_instructions=TASK_INSTRUCTIONS,
    )
