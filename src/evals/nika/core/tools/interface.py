"""Interface management tools for controlling network interface state."""

from inspect_ai.tool import Tool, tool

from evals.nika.core.tools._sandbox import safe_exec


@tool
def interface_set_state() -> Tool:
    """Set interface up or down."""

    async def execute(host: str, interface: str, state: str) -> str:
        """Set a network interface state to up or down.

        Args:
            host: Target container name
            interface: Interface name
            state: Interface state ("up" or "down")

        Returns:
            Command output or error
        """
        if state not in ("up", "down"):
            return f"[Error]: Invalid state '{state}'. Must be 'up' or 'down'."

        result = await safe_exec(host, ["ip", "link", "set", interface, state], timeout=10)
        if not result.success:
            return f"[Error]: {result.stderr}"
        return result.stdout or f"Interface {interface} set to {state}"

    return execute


@tool
def interface_show() -> Tool:
    """Show interface status."""

    async def execute(host: str, interface: str) -> str:
        """Show the status of a network interface.

        Args:
            host: Target container name
            interface: Interface name

        Returns:
            Command output or error
        """
        result = await safe_exec(host, ["ip", "addr", "show", interface], timeout=10)
        if not result.success:
            return f"[Error]: {result.stderr}"
        return result.stdout

    return execute


def get_interface_tools() -> list[Tool]:
    """Get interface management tools."""
    return [
        interface_set_state(),
        interface_show(),
    ]
