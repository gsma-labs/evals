"""TTAC Wireless configuration. Read this file to understand the entire eval."""

from pathlib import Path

# --- Paths ---
SANDBOX_DIR = (
    Path(__file__).resolve().parents[3] / "data" / "sandboxes" / "ttac_wireless"
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

SYSTEM_PROMPT_SINGLE = (
    "You are a 5G wireless network troubleshooting expert. "
    "Use the available tools to diagnose the root cause of degraded user throughput. "
    "Choose exactly one option. Output your final answer as \\boxed{Cn}."
)

SYSTEM_PROMPT_MULTIPLE = (
    "You are a 5G wireless network troubleshooting expert. "
    "Use the available tools to diagnose the root cause of degraded user throughput. "
    "Choose two to four options. Output your final answer as \\boxed{Ca|Cb|Cc}."
)

# --- Scoring ---
ANSWER_PATTERN = r"\\boxed\{([^}]+)\}"
ANSWER_SEPARATOR = "|"
