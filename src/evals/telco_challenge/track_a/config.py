"""TTAC Wireless configuration. Read this file to understand the entire eval."""

from pathlib import Path

# --- Paths ---
SANDBOX_DIR = (
    Path(__file__).resolve().parents[4] / "data" / "sandboxes" / "ttac_wireless"
)
COMPOSE_FILE = str(SANDBOX_DIR / "compose.yaml")

# --- Dataset ---
DATASET_REPO = "netop/Telco-Troubleshooting-Agentic-Challenge"
TRAIN_SPLIT = "train"
LITE_SIZE = 200

# --- Server (Docker service name + port) ---
SERVER_HOST = "server"
SERVER_PORT = 7860

# --- Agent ---
MESSAGE_LIMIT = 30
MAX_TOOL_CALLS = 10

FINAL_NUDGE = (
    "You have exhausted your tool-call budget. Do NOT call any more tools. "
    "Respond ONLY with your final answer on a single line using the \\boxed{} format."
)

_BUDGET_GUIDANCE = (
    "You have a strict conversation budget of ~30 messages. "
    "Plan before investigating; use at most 10 tool calls, then STOP and synthesize. "
    "You MUST end with your final answer on its own line using the \\boxed{} format below, "
    "even if you are uncertain. An unboxed answer scores zero."
)

SYSTEM_PROMPT_SINGLE = (
    "You are a 5G wireless network troubleshooting expert. "
    "Use the available tools to diagnose the root cause of degraded user throughput. "
    f"{_BUDGET_GUIDANCE} "
    "Choose exactly one option. Output your final answer as \\boxed{Cn} where n is the option number."
)

SYSTEM_PROMPT_MULTIPLE = (
    "You are a 5G wireless network troubleshooting expert. "
    "Use the available tools to diagnose the root cause of degraded user throughput. "
    f"{_BUDGET_GUIDANCE} "
    "Choose two to four options. Output your final answer as \\boxed{Ca|Cb|Cc} using the selected option numbers."
)

# --- Scoring ---
ANSWER_PATTERN = r"\\boxed\{((?:[^{}]|\{[^{}]*\})*)\}"
ANSWER_SEPARATOR = "|"
