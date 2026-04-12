"""TTAC IP Network tools. Single CLI command execution tool."""

import json

from inspect_ai.tool import tool
from inspect_ai.util import sandbox, store

from evals.ttac_ipnet.config import SERVER_HOST, SERVER_PORT


@tool
def execute_cli_command():
    async def execute(device_name: str, command: str) -> str:
        """Execute a show/display CLI command on a network device.

        Supports Huawei (display), Cisco (show), and H3C (display) syntax.
        Also supports ping and traceroute commands.

        Args:
            device_name: Device hostname (e.g. "Alpha-Center-01", "Beta-Portal-02").
            command: CLI command to run (e.g. "display lldp neighbor brief", "show ip route").
        """
        question_number = store().get("question_number")

        url = f"http://{SERVER_HOST}:{SERVER_PORT}/api/agent/execute"
        payload = json.dumps({
            "device_name": device_name,
            "command": command,
            "question_number": question_number,
        })

        result = await sandbox().exec([
            "curl", "-s", "-X", "POST",
            "-H", "Content-Type: application/json",
            "-d", payload,
            url,
        ])

        if not result.success:
            return f"Error: {result.stderr}"
        return result.stdout

    return execute
