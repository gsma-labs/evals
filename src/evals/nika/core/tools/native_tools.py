"""Native Inspect AI tools for NIKA network troubleshooting.

This module provides native @tool functions that use Inspect AI's sandbox()
pattern to execute commands in Kathara containers. These replace the MCP
server approach with a simpler, more direct pattern.

The key advantages over MCP:
- No subprocess overhead (MCP spawns Python processes)
- Direct container execution via sandbox()
- Simpler debugging and error handling
- Better integration with Inspect AI's tooling

Usage:
    from build_images.tools.native_tools import get_base_tools, get_frr_tools

    tools = [*get_base_tools(), *get_frr_tools(), submit()]
"""

import json

from inspect_ai.tool import Tool, tool
from inspect_ai.util._sandbox.environment import ExecResult

from evals.nika.core.tools._sandbox import safe_exec


def _format_result(result: ExecResult, cmd_name: str) -> str:
    """Format command result, including error details on failure."""
    if result.success:
        return result.stdout
    stderr_part = f"\n[stderr]: {result.stderr}" if result.stderr else ""
    return f"[{cmd_name} failed with code {result.returncode}]\n{result.stdout}{stderr_part}"


# =============================================================================
# Core Network Tools (equivalent to kathara_base_mcp_server)
# =============================================================================


@tool
def ping_pair() -> Tool:
    """Test connectivity between two hosts using ICMP ping."""

    async def execute(host_a: str, ip_b: str, count: int = 4, args: str = "") -> str:
        """Ping from one host to another.

        Args:
            host_a: Source host name
            ip_b: Destination IP
            count: Number of ping packets to send (default: 4)
            args: Additional ping arguments (use "" for none)

        Returns:
            Ping command output showing connectivity status
        """
        cmd = f"ping -c {count} {ip_b} {args}".strip()
        result = await safe_exec(host_a, ["bash", "-c", cmd], timeout=30)
        return _format_result(result, "ping")

    return execute


@tool
def exec_shell() -> Tool:
    """Execute arbitrary shell command on a host."""

    async def execute(host_name: str, command: str) -> str:
        """Execute a shell command on a host.

        Args:
            host_name: Name of the host machine
            command: Shell command to execute

        Returns:
            Command output (stdout and stderr)
        """
        result = await safe_exec(host_name, ["bash", "-c", command], timeout=30)

        output = result.stdout
        if result.stderr:
            output += f"\n[stderr]: {result.stderr}"
        if not result.success:
            output = f"[Command failed with code {result.returncode}]\n{output}"
        return output

    return execute


@tool
def get_host_net_config() -> Tool:
    """Get network configuration of a host including interfaces and routes."""

    async def execute(host_name: str) -> str:
        """Get network configuration of a host.

        Args:
            host_name: Name of the host machine

        Returns:
            JSON with ifconfig, ip addr, and ip route output
        """
        config = {"host_name": host_name}

        # Get ifconfig
        result = await safe_exec(host_name, ["ifconfig", "-a"], timeout=10)
        config["ifconfig"] = result.stdout if result.success else f"[error: {result.stderr}]"

        # Get ip addr
        result = await safe_exec(host_name, ["ip", "addr"], timeout=10)
        config["ip_addr"] = result.stdout if result.success else f"[error: {result.stderr}]"

        # Get ip route
        result = await safe_exec(host_name, ["ip", "route"], timeout=10)
        config["ip_route"] = result.stdout if result.success else f"[error: {result.stderr}]"

        return json.dumps(config, indent=2)

    return execute


@tool
def get_reachability() -> Tool:
    """Get connectivity status between all host pairs in the network."""

    async def execute() -> str:
        """Test reachability between all hosts.

        Returns:
            JSON with ping results from each host to all other hosts
        """
        # Note: This is a simplified version. In practice, host discovery
        # would need to be done based on the lab topology.
        return json.dumps(
            {
                "note": "Use ping_pair() for specific host connectivity tests",
                "recommendation": "Test connectivity between specific hosts of interest",
            }
        )

    return execute


@tool
def netstat() -> Tool:
    """Run netstat to show network connections and statistics."""

    async def execute(host_name: str, args: str = "-tuln") -> str:
        """Run netstat command on a host.

        Args:
            host_name: Name of the host machine
            args: netstat arguments (default: '-tuln' for TCP/UDP listening ports)

        Returns:
            netstat command output
        """
        result = await safe_exec(host_name, ["netstat", *args.split()], timeout=10)
        return _format_result(result, "netstat")

    return execute


@tool
def ethtool() -> Tool:
    """Run ethtool to query network interface settings."""

    async def execute(host_name: str, interface: str, args: str = "") -> str:
        """Run ethtool command on a host's network interface.

        Args:
            host_name: Name of the host machine
            interface: Network interface name (e.g., 'eth0')
            args: Additional ethtool arguments

        Returns:
            ethtool command output
        """
        cmd_parts = ["ethtool"]
        if args:
            cmd_parts.extend(args.split())
        cmd_parts.append(interface)

        result = await safe_exec(host_name, cmd_parts, timeout=10)
        return _format_result(result, "ethtool")

    return execute


@tool
def curl_web_test() -> Tool:
    """Perform HTTP timing tests using curl."""

    async def execute(host_name: str, url: str, times: int = 5) -> str:
        """Perform curl test to a URL multiple times with timing statistics.

        Args:
            host_name: Host machine to run curl from
            url: URL to test
            times: Number of times to perform the test (default: 5)

        Returns:
            Timing statistics for each request
        """
        curl_cmd = (
            f"curl --connect-timeout 5 --max-time 10 "
            f"-w 'namelookup:%{{time_namelookup}}, "
            f"connect:%{{time_connect}}, "
            f"appconnect:%{{time_appconnect}}, "
            f"pretransfer:%{{time_pretransfer}}, "
            f"starttransfer:%{{time_starttransfer}}, "
            f"total:%{{time_total}}\\n' "
            f"-o /dev/null -s {url}"
        )

        results = []
        for i in range(times):
            result = await safe_exec(host_name, ["bash", "-c", curl_cmd], timeout=15)
            results.append(
                result.stdout.strip()
                if result.success
                else f"[attempt {i + 1} failed: {result.stderr}]"
            )

        return "\n".join(results)

    return execute


@tool
def iperf_test() -> Tool:
    """Run iperf3 bandwidth test between two hosts."""

    async def execute(
        client_host_name: str,
        server_host_name: str,
        duration: int = 10,
        client_args: str = "",
        server_args: str = "",
    ) -> str:
        """Run an iperf3 bandwidth test between two hosts.

        Args:
            client_host_name: Name of the client host
            server_host_name: Name of the server host
            duration: Test duration in seconds (default: 10)
            client_args: Additional iperf3 client arguments
            server_args: Additional iperf3 server arguments

        Returns:
            iperf3 test results
        """
        # Get server IP
        ip_result = await safe_exec(
            server_host_name,
            ["bash", "-c", "hostname -i | awk '{print $1}'"],
            timeout=5,
        )

        if not ip_result.success or not ip_result.stdout.strip():
            return f"[Failed to get server IP: {ip_result.stderr}]"

        server_ip = ip_result.stdout.strip()

        # Start iperf3 server in daemon mode
        server_cmd = f"iperf3 -s -D {server_args}".strip()
        await safe_exec(server_host_name, ["bash", "-c", server_cmd], timeout=5)

        # Run iperf3 client
        client_cmd = f"iperf3 -c {server_ip} -t {duration} {client_args}".strip()
        client_result = await safe_exec(
            client_host_name,
            ["bash", "-c", client_cmd],
            timeout=duration + 30,
        )

        # Stop iperf3 server
        await safe_exec(server_host_name, ["pkill", "iperf3"], timeout=5)
        return _format_result(client_result, "iperf test")

    return execute


@tool
def systemctl_ops() -> Tool:
    """Perform systemctl operations on services."""

    async def execute(host_name: str, service_name: str, operation: str) -> str:
        """Perform systemctl operation on a service.

        Args:
            host_name: Name of the host machine
            service_name: Service name (e.g., 'nginx', 'named')
            operation: Operation to perform ('start', 'stop', 'restart', 'status')

        Returns:
            systemctl command output
        """
        valid_ops = ["start", "stop", "restart", "status"]
        if operation not in valid_ops:
            return f"[Invalid operation '{operation}'. Must be one of: {valid_ops}]"

        result = await safe_exec(
            host_name,
            ["systemctl", operation, service_name],
            timeout=30,
        )

        output = result.stdout
        if result.stderr:
            output += f"\n[stderr]: {result.stderr}"
        if not result.success:
            output = f"[systemctl {operation} failed with code {result.returncode}]\n{output}"
        return output

    return execute


@tool
def get_tc_statistics() -> Tool:
    """Get traffic control (tc) queue statistics."""

    async def execute(host_name: str, intf_name: str) -> str:
        """Get traffic control statistics for an interface.

        Args:
            host_name: Name of the host machine
            intf_name: Network interface name

        Returns:
            tc qdisc statistics
        """
        result = await safe_exec(
            host_name,
            ["tc", "-s", "qdisc", "show", "dev", intf_name],
            timeout=10,
        )
        return _format_result(result, "tc")

    return execute


@tool
def ip_addr_statistics() -> Tool:
    """Get IP address statistics with packet/byte counters."""

    async def execute(host_name: str) -> str:
        """Get IP address statistics including RX/TX counters.

        Args:
            host_name: Name of the host machine

        Returns:
            ip -s addr output
        """
        result = await safe_exec(host_name, ["ip", "-s", "addr"], timeout=10)
        return _format_result(result, "ip addr statistics")

    return execute


@tool
def cat_file() -> Tool:
    """Read contents of a file on a host."""

    async def execute(host_name: str, file_path: str) -> str:
        """Read contents of a file on a host.

        Args:
            host_name: Name of the host machine
            file_path: Path to the file

        Returns:
            File contents
        """
        result = await safe_exec(host_name, ["cat", file_path], timeout=10)
        return _format_result(result, "cat")

    return execute


# =============================================================================
# FRR Router Tools (equivalent to kathara_frr_mcp_server)
# =============================================================================


@tool
def vtysh() -> Tool:
    """Execute arbitrary vtysh commands on FRR routers."""

    async def execute(router_name: str, command: str) -> str:
        """Execute a vtysh command on an FRR router.

        Args:
            router_name: Router machine name
            command: vtysh command to execute

        Returns:
            vtysh command output
        """
        result = await safe_exec(
            router_name,
            ["vtysh", "-c", command],
            timeout=10,
        )
        return _format_result(result, "vtysh")

    return execute


@tool
def frr_show_ip_route() -> Tool:
    """Show the IP routing table on an FRR router."""

    async def execute(router_name: str) -> str:
        """Get the IP routing table from an FRR router.

        Args:
            router_name: Router machine name

        Returns:
            IP routing table
        """
        result = await safe_exec(
            router_name,
            ["vtysh", "-c", "show ip route"],
            timeout=10,
        )
        return _format_result(result, "show ip route")

    return execute


@tool
def frr_get_bgp_conf() -> Tool:
    """Show BGP routing table."""

    async def execute(router_name: str) -> str:
        """Get the BGP routing table from an FRR router.

        Args:
            router_name: Router machine name

        Returns:
            BGP routing table
        """
        result = await safe_exec(
            router_name,
            ["vtysh", "-c", "show ip bgp"],
            timeout=10,
        )
        return _format_result(result, "show ip bgp")

    return execute


@tool
def frr_get_ospf_conf() -> Tool:
    """Show OSPF configuration and status."""

    async def execute(router_name: str) -> str:
        """Get the OSPF configuration from an FRR router.

        Args:
            router_name: Router machine name

        Returns:
            OSPF configuration and status
        """
        result = await safe_exec(
            router_name,
            ["vtysh", "-c", "show ip ospf"],
            timeout=10,
        )
        return _format_result(result, "show ip ospf")

    return execute


@tool
def frr_show_running_config() -> Tool:
    """Show the running configuration on an FRR router."""

    async def execute(router_name: str) -> str:
        """Get the running configuration from an FRR router.

        Args:
            router_name: Router machine name

        Returns:
            Full running configuration
        """
        result = await safe_exec(
            router_name,
            ["vtysh", "-c", "show running-config"],
            timeout=10,
        )
        return _format_result(result, "show running-config")

    return execute


@tool
def frr_exec() -> Tool:
    """Execute a vtysh command on an FRR router (alias for vtysh)."""

    async def execute(router_name: str, command: str) -> str:
        """Execute a vtysh command on an FRR router.

        Args:
            router_name: Router machine name
            command: vtysh command to execute

        Returns:
            vtysh command output
        """
        result = await safe_exec(
            router_name,
            ["vtysh", "-c", command],
            timeout=10,
        )
        return _format_result(result, "vtysh")

    return execute


# =============================================================================
# Tool Factory Functions (API-compatible replacements for MCP server factories)
# =============================================================================


def get_base_tools() -> list[Tool]:
    """Get base network diagnostic tools.

    Returns a list of tools equivalent to those provided by kathara_base_mcp_server:
    - ping_pair: Test connectivity between hosts
    - exec_shell: Execute shell commands
    - get_host_net_config: Get network interface configuration
    - netstat: Show network connections
    - ethtool: Query interface settings
    - curl_web_test: HTTP timing tests
    - iperf_test: Bandwidth testing
    - systemctl_ops: Service management
    - get_tc_statistics: Traffic control stats
    - ip_addr_statistics: Interface statistics
    - cat_file: Read file contents

    Returns:
        List of Tool instances
    """
    return [
        ping_pair(),
        exec_shell(),
        get_host_net_config(),
        netstat(),
        ethtool(),
        curl_web_test(),
        iperf_test(),
        systemctl_ops(),
        get_tc_statistics(),
        ip_addr_statistics(),
        cat_file(),
    ]


def get_frr_tools() -> list[Tool]:
    """Get FRR router tools.

    Returns a list of tools equivalent to those provided by kathara_frr_mcp_server:
    - vtysh: Execute arbitrary vtysh commands
    - frr_show_ip_route: Show IP routing table
    - frr_get_bgp_conf: Show BGP configuration
    - frr_get_ospf_conf: Show OSPF configuration
    - frr_show_running_config: Show running config
    - frr_exec: Execute vtysh command (alias)

    Returns:
        List of Tool instances
    """
    return [
        vtysh(),
        frr_show_ip_route(),
        frr_get_bgp_conf(),
        frr_get_ospf_conf(),
        frr_show_running_config(),
        frr_exec(),
    ]


def get_nika_tools(
    include_base: bool = True,
    include_frr: bool = True,
    include_bmv2: bool = False,
    include_telemetry: bool = False,
    include_tc: bool = False,
    include_interface: bool = False,
    include_nftables: bool = False,
    include_utils: bool = False,
) -> list[Tool]:
    """Get NIKA tools based on enabled options.

    This is the native tool equivalent of create_nika_mcp_servers().

    Args:
        include_base: Include base network diagnostic tools
        include_frr: Include FRR router tools
        include_bmv2: Include BMv2 P4 switch tools
        include_telemetry: Include InfluxDB telemetry tools
        include_tc: Include traffic control (tc) tools
        include_interface: Include interface management tools
        include_nftables: Include nftables firewall tools
        include_utils: Include utility tools (get_host_ip, traceroute, etc.)

    Returns:
        List of Tool instances
    """
    tools = (get_base_tools() if include_base else []) + (get_frr_tools() if include_frr else [])

    if include_bmv2:
        from evals.nika.core.tools.bmv2 import get_bmv2_tools

        tools += get_bmv2_tools()
    if include_telemetry:
        from evals.nika.core.tools.telemetry import get_telemetry_tools

        tools += get_telemetry_tools()
    if include_tc:
        from evals.nika.core.tools.tc import get_tc_tools

        tools += get_tc_tools()
    if include_interface:
        from evals.nika.core.tools.interface import get_interface_tools

        tools += get_interface_tools()
    if include_nftables:
        from evals.nika.core.tools.nftables import get_nftables_tools

        tools += get_nftables_tools()
    if include_utils:
        from evals.nika.core.tools.utils import get_utils_tools

        tools += get_utils_tools()

    return tools
