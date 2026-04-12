"""TTAC Wireless configuration. Read this file to understand the entire eval."""

from pathlib import Path


# --- Paths ---
SANDBOX_DIR = Path(__file__).resolve().parents[3] / "data" / "sandboxes" / "ttac_wireless"
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
SYSTEM_PROMPT = (
    "You are a 5G wireless network troubleshooting expert. "
    "Use the available tools to diagnose the root cause of degraded user throughput. "
    "When you have identified the root cause, output your final answer as "
    "\\boxed{C3} for a single answer or \\boxed{C3|C5} for multiple answers."
)

# --- Scoring ---
ANSWER_PATTERN = r"\\boxed\{([^}]+)\}"
ANSWER_SEPARATOR = "|"
