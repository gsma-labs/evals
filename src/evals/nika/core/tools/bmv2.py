"""BMv2 P4 programmable switch tools for SDN data plane control."""

import json

from inspect_ai.tool import Tool, tool

from evals.nika.core.tools._sandbox import safe_exec


def _build_thrift_command(api_calls: list[str]) -> str:
    """Build bash command to execute Thrift API calls on BMv2 switch."""
    python_lines = [
        "from sswitch_thrift_API import SimpleSwitchThriftAPI",
        "simple_switch = SimpleSwitchThriftAPI(thrift_port=9090)",
    ]
    for call in api_calls:
        python_lines.append(f"print(simple_switch.{call})")
    python_script = "\n".join(python_lines)
    return f"cd /usr/local/lib/python3.11/site-packages && python3 << 'EOF'\n{python_script}\nEOF"


# =============================================================================
# BMv2 P4 Switch Tools
# =============================================================================


@tool
def bmv2_get_log() -> Tool:
    """Get the log file of a BMv2 switch."""

    async def execute(switch: str, rows: int = 100) -> str:
        """Get the log file of a BMv2 switch.

        Args:
            switch: Name of the switch
            rows: Number of log lines to retrieve (default: 100)

        Returns:
            Log file contents
        """
        cmd = f"tail -n {rows} sw.log"
        result = await safe_exec(switch, ["bash", "-c", cmd], timeout=15)
        if result.success:
            return result.stdout
        return f"[Error]: {result.stderr}"

    return execute


@tool
def bmv2_switch_info() -> Tool:
    """Show switch info for a BMv2 switch."""

    async def execute(switch: str) -> str:
        """Show the switch info.

        Args:
            switch: Name of the switch

        Returns:
            Switch information
        """
        cmd = _build_thrift_command(["show_switch_info()"])
        result = await safe_exec(switch, ["bash", "-c", cmd], timeout=15)
        if result.success:
            return result.stdout
        return f"[Error]: {result.stderr}"

    return execute


@tool
def bmv2_show_tables() -> Tool:
    """List all tables in a BMv2 switch."""

    async def execute(switch: str) -> str:
        """List all tables in the switch.

        Args:
            switch: Name of the switch

        Returns:
            List of tables
        """
        cmd = _build_thrift_command(["show_tables()"])
        result = await safe_exec(switch, ["bash", "-c", cmd], timeout=15)
        if result.success:
            return result.stdout
        return f"[Error]: {result.stderr}"

    return execute


@tool
def bmv2_show_actions() -> Tool:
    """List all actions in a BMv2 switch."""

    async def execute(switch: str) -> str:
        """List all actions in the switch.

        Args:
            switch: Name of the switch

        Returns:
            List of actions
        """
        cmd = _build_thrift_command(["show_actions()"])
        result = await safe_exec(switch, ["bash", "-c", cmd], timeout=15)
        if result.success:
            return result.stdout
        return f"[Error]: {result.stderr}"

    return execute


@tool
def bmv2_show_ports() -> Tool:
    """List switch ports on a BMv2 switch."""

    async def execute(switch: str) -> str:
        """List all ports on the switch.

        Args:
            switch: Name of the switch

        Returns:
            List of ports
        """
        cmd = _build_thrift_command(["show_ports()"])
        result = await safe_exec(switch, ["bash", "-c", cmd], timeout=15)
        if result.success:
            return result.stdout
        return f"[Error]: {result.stderr}"

    return execute


@tool
def bmv2_table_dump() -> Tool:
    """Dump all entries in a table."""

    async def execute(switch: str, table_name: str) -> str:
        """Dump all entries in a table.

        Args:
            switch: Name of the switch
            table_name: Name of the table to dump

        Returns:
            Table entries
        """
        cmd = _build_thrift_command([f'table_dump("{table_name}")'])
        result = await safe_exec(switch, ["bash", "-c", cmd], timeout=15)
        if result.success:
            return result.stdout
        return f"[Error]: {result.stderr}"

    return execute


@tool
def bmv2_table_info() -> Tool:
    """Get info about a table."""

    async def execute(switch: str, table_name: str) -> str:
        """Get information about a table.

        Args:
            switch: Name of the switch
            table_name: Name of the table

        Returns:
            Table information
        """
        cmd = _build_thrift_command([f'table_info("{table_name}")'])
        result = await safe_exec(switch, ["bash", "-c", cmd], timeout=15)
        if result.success:
            return result.stdout
        return f"[Error]: {result.stderr}"

    return execute


@tool
def bmv2_table_add() -> Tool:
    """Add an entry to a table."""

    async def execute(
        switch: str,
        table_name: str,
        action_name: str,
        match_keys: str,
        action_params: str = "[]",
        prio: int = 0,
    ) -> str:
        """Add an entry to a table.

        Args:
            switch: Name of the switch
            table_name: Name of the table
            action_name: Name of the action to execute
            match_keys: JSON string of match keys (e.g., '["10.0.0.1"]')
            action_params: JSON string of action parameters (default: '[]')
            prio: Priority of the entry (default: 0)

        Returns:
            Entry handle or error message
        """
        try:
            keys = json.loads(match_keys)
            params = json.loads(action_params)
        except json.JSONDecodeError as e:
            return f"[Error]: Invalid JSON - {e}"

        formatted_keys = '["' + '", "'.join(keys) + '"]'
        formatted_params = '["' + '", "'.join(params) + '"]' if params else "[]"

        cmd = _build_thrift_command(
            [
                f'table_add("{table_name}", "{action_name}", {formatted_keys}, {formatted_params}, {prio})'
            ]
        )
        result = await safe_exec(switch, ["bash", "-c", cmd], timeout=15)
        if result.success:
            return result.stdout
        return f"[Error]: {result.stderr}"

    return execute


@tool
def bmv2_table_delete() -> Tool:
    """Delete an entry from a table by handle."""

    async def execute(switch: str, table_name: str, entry_handle: str) -> str:
        """Delete an entry from a table by its handle.

        Args:
            switch: Name of the switch
            table_name: Name of the table
            entry_handle: Handle of the entry to delete

        Returns:
            Success message or error
        """
        cmd = _build_thrift_command([f'table_delete("{table_name}", "{entry_handle}")'])
        result = await safe_exec(switch, ["bash", "-c", cmd], timeout=15)
        if result.success:
            return result.stdout
        return f"[Error]: {result.stderr}"

    return execute


@tool
def bmv2_table_modify() -> Tool:
    """Modify an entry in a table."""

    async def execute(
        switch: str,
        table_name: str,
        action_name: str,
        entry_handle: str,
        action_params: str = "[]",
    ) -> str:
        """Modify an entry in a table.

        Args:
            switch: Name of the switch
            table_name: Name of the table
            action_name: Name of the new action
            entry_handle: Handle of the entry to modify
            action_params: JSON string of action parameters (default: '[]')

        Returns:
            Success message or error
        """
        try:
            params = json.loads(action_params)
        except json.JSONDecodeError as e:
            return f"[Error]: Invalid JSON - {e}"

        formatted_params = '["' + '", "'.join(params) + '"]' if params else "[]"

        cmd = _build_thrift_command(
            [f'table_modify("{table_name}", "{action_name}", {entry_handle}, {formatted_params})']
        )
        result = await safe_exec(switch, ["bash", "-c", cmd], timeout=15)
        if result.success:
            return result.stdout
        return f"[Error]: {result.stderr}"

    return execute


@tool
def bmv2_counter_read() -> Tool:
    """Read a counter value."""

    async def execute(switch: str, counter_name: str, index: int = 0) -> str:
        """Read a counter value.

        Args:
            switch: Name of the switch
            counter_name: Name of the counter
            index: Index of the counter entry (default: 0)

        Returns:
            Counter value
        """
        cmd = _build_thrift_command([f'counter_read("{counter_name}", {index})'])
        result = await safe_exec(switch, ["bash", "-c", cmd], timeout=15)
        if result.success:
            return result.stdout
        return f"[Error]: {result.stderr}"

    return execute


@tool
def bmv2_register_read() -> Tool:
    """Read a register value."""

    async def execute(switch: str, register_name: str, index: int = 0) -> str:
        """Read a register value.

        Args:
            switch: Name of the switch
            register_name: Name of the register
            index: Index of the register entry (default: 0)

        Returns:
            Register value
        """
        cmd = _build_thrift_command([f'register_read("{register_name}", {index})'])
        result = await safe_exec(switch, ["bash", "-c", cmd], timeout=15)
        if result.success:
            return result.stdout
        return f"[Error]: {result.stderr}"

    return execute


@tool
def read_p4_program() -> Tool:
    """Read the P4 source code from a switch."""

    async def execute(switch: str) -> str:
        """Read the P4 program source code from a switch.

        Args:
            switch: Name of the switch

        Returns:
            P4 source code or error message
        """
        # Check for .p4 files in root directory
        result = await safe_exec(switch, ["bash", "-c", "ls *.p4 2>/dev/null || true"], timeout=10)
        # If the host is invalid, return the error immediately
        if not result.success and "not a valid device name" in result.stderr:
            return f"[Error]: {result.stderr}"
        if result.success and result.stdout.strip():
            p4_files = result.stdout.strip().split()
            if p4_files:
                cat_result = await safe_exec(switch, ["cat", p4_files[0]], timeout=15)
                if cat_result.success:
                    return cat_result.stdout
                return f"[Error reading {p4_files[0]}]: {cat_result.stderr}"

        # Check for .p4 files in p4_src directory
        result = await safe_exec(
            switch, ["bash", "-c", "ls p4_src/*.p4 2>/dev/null || true"], timeout=10
        )
        if result.success and result.stdout.strip():
            p4_files = result.stdout.strip().split()
            if p4_files:
                cat_result = await safe_exec(switch, ["cat", p4_files[0]], timeout=15)
                if cat_result.success:
                    return cat_result.stdout
                return f"[Error reading {p4_files[0]}]: {cat_result.stderr}"

        return "[Error]: No P4 program found"

    return execute


# =============================================================================
# Tool Factory Function
# =============================================================================


def get_bmv2_tools() -> list[Tool]:
    """Get BMv2 P4 switch tools."""
    return [
        bmv2_get_log(),
        bmv2_switch_info(),
        bmv2_show_tables(),
        bmv2_show_actions(),
        bmv2_show_ports(),
        bmv2_table_dump(),
        bmv2_table_info(),
        bmv2_table_add(),
        bmv2_table_delete(),
        bmv2_table_modify(),
        bmv2_counter_read(),
        bmv2_register_read(),
        read_p4_program(),
    ]
