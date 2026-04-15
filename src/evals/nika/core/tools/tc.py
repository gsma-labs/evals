"""Traffic control (tc) tools for network impairment simulation."""

from inspect_ai.tool import Tool, tool

from evals.nika.core.tools._sandbox import safe_exec


@tool
def tc_set_netem() -> Tool:
    """Set netem qdisc for network impairment (loss, delay, jitter, etc.)."""

    async def execute(
        host: str,
        intf_name: str,
        loss: int | None = None,
        delay_ms: int | None = None,
        jitter_ms: int | None = None,
        duplicate: int | None = None,
        corrupt: int | None = None,
        reorder: int | None = None,
        limit: int | None = None,
        handle: str | None = None,
        parent: str | None = None,
    ) -> str:
        """Set traffic control netem qdisc on a specific interface of a host.

        Args:
            host: Target container name
            intf_name: Interface name (e.g., eth0, eth1)
            loss: Packet loss percentage (0-100)
            delay_ms: Delay in milliseconds
            jitter_ms: Jitter in milliseconds (requires delay_ms)
            duplicate: Duplicate percentage (0-100)
            corrupt: Corruption percentage (0-100)
            reorder: Reorder percentage (0-100)
            limit: Queue size limit
            handle: qdisc handle (e.g., "1:" or "1")
            parent: Parent class/qdisc (e.g., "1:1")

        Returns:
            Command output or error message
        """
        command = f"tc qdisc add dev {intf_name}"
        command += f" parent {parent}" if parent else " root"

        if handle is not None:
            handle = handle if handle.endswith(":") else handle + ":"
            command += f" handle {handle}"

        command += " netem"

        if loss is not None:
            command += f" loss {loss}%"

        if delay_ms is not None:
            jitter_part = f" {jitter_ms}ms" if jitter_ms else ""
            command += f" delay {delay_ms}ms{jitter_part}"

        if duplicate is not None:
            command += f" duplicate {duplicate}%"
        if reorder is not None:
            command += f" reorder {reorder}%"
        if corrupt is not None:
            command += f" corrupt {corrupt}%"
        if limit is not None:
            command += f" limit {limit}"

        result = await safe_exec(host, ["bash", "-c", command])
        if not result.success:
            return f"[Error]: {result.stderr}"
        return result.stdout or "[netem qdisc configured successfully]"

    return execute


@tool
def tc_set_tbf() -> Tool:
    """Set Token Bucket Filter (tbf) qdisc for rate limiting."""

    async def execute(
        host: str,
        intf_name: str,
        rate: str,
        burst: str,
        limit: str,
        handle: str | None = None,
        parent: str | None = None,
    ) -> str:
        """Set Token Bucket Filter qdisc on a specific interface of a host.

        Args:
            host: Target container name
            intf_name: Interface name (e.g., eth0, eth1)
            rate: Rate limit (e.g., "100mbit")
            burst: Burst size (e.g., "32kbit")
            limit: Limit size (e.g., "10000")
            handle: qdisc handle (e.g., "10:" or "10")
            parent: Parent class/qdisc (e.g., "1:1")

        Returns:
            Command output or error message
        """
        command = f"tc qdisc add dev {intf_name}"
        command += f" parent {parent}" if parent else " root"

        if handle is not None:
            handle = handle if handle.endswith(":") else handle + ":"
            command += f" handle {handle}"

        command += f" tbf rate {rate} burst {burst} limit {limit}"

        result = await safe_exec(host, ["bash", "-c", command])
        if not result.success:
            return f"[Error]: {result.stderr}"
        return result.stdout or "[tbf qdisc configured successfully]"

    return execute


@tool
def tc_show_config() -> Tool:
    """Show qdisc configuration on an interface."""

    async def execute(host: str, intf_name: str) -> str:
        """Show traffic control qdisc configuration on a specific interface.

        Args:
            host: Target container name
            intf_name: Interface name (e.g., eth0, eth1)

        Returns:
            Command output or error message
        """
        command = f"tc qdisc show dev {intf_name}"
        result = await safe_exec(host, ["bash", "-c", command])
        if not result.success:
            return f"[Error]: {result.stderr}"
        return result.stdout

    return execute


@tool
def tc_show_statistics() -> Tool:
    """Show qdisc statistics on an interface."""

    async def execute(host: str, intf_name: str) -> str:
        """Show traffic control qdisc statistics on a specific interface.

        Args:
            host: Target container name
            intf_name: Interface name (e.g., eth0, eth1)

        Returns:
            Command output or error message
        """
        command = f"tc -s qdisc show dev {intf_name}"
        result = await safe_exec(host, ["bash", "-c", command])
        if not result.success:
            return f"[Error]: {result.stderr}"
        return result.stdout

    return execute


@tool
def tc_clear() -> Tool:
    """Clear qdisc configuration on an interface."""

    async def execute(host: str, intf_name: str) -> str:
        """Clear traffic control qdisc configuration on a specific interface.

        Args:
            host: Target container name
            intf_name: Interface name (e.g., eth0, eth1)

        Returns:
            Command output or error message
        """
        command = f"tc qdisc del dev {intf_name} root"
        result = await safe_exec(host, ["bash", "-c", command])
        if not result.success:
            return f"[Error]: {result.stderr}"
        return result.stdout or "[qdisc cleared successfully]"

    return execute


def get_tc_tools() -> list[Tool]:
    """Get traffic control tools."""
    return [
        tc_set_netem(),
        tc_set_tbf(),
        tc_show_config(),
        tc_show_statistics(),
        tc_clear(),
    ]
