"""TTAC IP Network configuration. Read this file to understand the entire eval."""

from pathlib import Path

# --- Paths ---
SANDBOX_DIR = Path(__file__).resolve().parents[3] / "data" / "sandboxes" / "ttac_ipnet"
COMPOSE_FILE = str(SANDBOX_DIR / "compose.yaml")

# --- Dataset ---
DATASET_REPO = "netop/Telco-Troubleshooting-Agentic-Challenge"

# --- Server (Docker service name + port) ---
SERVER_HOST = "server"
SERVER_PORT = 7860

# --- Agent ---
MESSAGE_LIMIT = 50
SYSTEM_PROMPT = (
    "You are an expert IP network troubleshooting agent. "
    "You have access to a multi-vendor network with Huawei and Cisco devices. "
    "Use the execute_cli_command tool to run show/display commands on devices. "
    "Diagnose the issue and provide your answer in the exact format requested."
)
