"""Utility tools for host inspection and network diagnostics."""

import json

from inspect_ai.tool import Tool, tool

from evals.nika.core.tools._sandbox import safe_exec


@tool
def get_host_ip() -> Tool:
    """Get the IPv4 address of a host."""

    async def execute(host: str, interface: str = "eth0", with_prefix: bool = False) -> str:
        """Get the IPv4 address of a host via `ip -j addr`.

        Args:
            host: The target host to query.
            interface: The network interface to check (default: "eth0").
            with_prefix: If True, return "ip/prefix" (e.g., 192.168.1.10/24),
                         if False, return only "ip" (e.g., 192.168.1.10).

        Returns:
            The IPv4 address of the host, or an error message if not found.
        """
        cmd = "ip -j addr"
        result = await safe_exec(host, ["bash", "-c", cmd], timeout=10)

        if not result.success:
            return f"[Error]: {result.stderr}"

        try:
            ifaces = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            return f"[Error]: Failed to parse `ip -j addr` output: {e}"

        def format_ip(ip: str, prefix: int | None) -> str:
            if with_prefix and prefix is not None:
                return f"{ip}/{prefix}"
            return ip

        # First, try to find the specified interface
        for link in ifaces:
            if link.get("ifname") != interface:
                continue

            for addr in link.get("addr_info", []):
                if addr.get("family") != "inet":
                    continue
                ip = addr.get("local")
                prefix = addr.get("prefixlen")
                if ip and not ip.startswith("127."):
                    return format_ip(ip, prefix)

        # Fallback: return first non-loopback IPv4 address found
        for link in ifaces:
            for addr in link.get("addr_info", []):
                if addr.get("family") != "inet":
                    continue
                ip = addr.get("local")
                prefix = addr.get("prefixlen")
                if ip and not ip.startswith("127."):
                    return format_ip(ip, prefix)

        return f"[Error]: No IPv4 address found for host {host}"

    return execute


@tool
def get_default_gateway() -> Tool:
    """Get the default gateway of a host."""

    async def execute(host: str) -> str:
        """Get the default gateway of a host using `ip -j route`.

        Args:
            host: The target host to query.

        Returns:
            The default gateway IP address, or an error message if not found.
        """
        cmd = "ip -j route"
        result = await safe_exec(host, ["bash", "-c", cmd], timeout=10)

        if not result.success:
            return f"[Error]: {result.stderr}"

        try:
            routes = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            return f"[Error]: Failed to parse `ip -j route` output: {e}"

        for route in routes:
            if route.get("dst") == "default":
                gateway = route.get("gateway")
                if gateway:
                    return gateway

        return f"[Error]: No default gateway found for host {host}"

    return execute


@tool
def get_host_interfaces() -> Tool:
    """List network interfaces on a host."""

    async def execute(host: str, include_loopback: bool = False) -> str:
        """List network interfaces on a host.

        Args:
            host: The target host to query.
            include_loopback: If True, include the loopback interface (lo).

        Returns:
            A list of interface names, or an error message if failed.
        """
        cmd = "ip -j addr"
        result = await safe_exec(host, ["bash", "-c", cmd], timeout=10)

        if not result.success:
            return f"[Error]: {result.stderr}"

        try:
            ifaces = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            return f"[Error]: Failed to parse `ip -j addr` output: {e}"

        names = []
        for link in ifaces:
            name = link.get("ifname")
            if not name:
                continue
            if not include_loopback and name == "lo":
                continue
            if name.startswith("br"):  # skip bridge interfaces
                continue
            names.append(name)

        return json.dumps(names)

    return execute


@tool
def get_host_mac_address() -> Tool:
    """Get the MAC address of a host's network interface."""

    async def execute(host: str, interface: str = "eth0") -> str:
        """Get the MAC address of a host's network interface.

        Args:
            host: The target host to query.
            interface: The network interface to check (default: "eth0").

        Returns:
            The MAC address, or an error message if not found.
        """
        cmd = f"cat /sys/class/net/{interface}/address"
        result = await safe_exec(host, ["bash", "-c", cmd], timeout=10)

        if result.success:
            return result.stdout.strip()
        return f"[Error]: {result.stderr}"

    return execute


@tool
def ps_list() -> Tool:
    """List running processes on a host."""

    async def execute(host: str, args: str = "aux") -> str:
        """List running processes on a host using the ps command.

        Args:
            host: The target host to query.
            args: Arguments to pass to the ps command (default: "aux").

        Returns:
            The output of the ps command, or an error message if failed.
        """
        cmd = f"ps {args}"
        result = await safe_exec(host, ["bash", "-c", cmd], timeout=10)

        if result.success:
            return result.stdout
        return f"[Error]: {result.stderr}"

    return execute


@tool
def show_dns_config() -> Tool:
    """Show DNS configuration of a host."""

    async def execute(host: str) -> str:
        """Show DNS configuration of a host by reading /etc/resolv.conf.

        Args:
            host: The target host to query.

        Returns:
            The contents of /etc/resolv.conf, or an error message if failed.
        """
        cmd = "cat /etc/resolv.conf"
        result = await safe_exec(host, ["bash", "-c", cmd], timeout=10)

        if result.success:
            return result.stdout
        return f"[Error]: {result.stderr}"

    return execute


@tool
def traceroute() -> Tool:
    """Trace the route to a destination from a host."""

    async def execute(host: str, destination: str) -> str:
        """Trace the route to a destination from a host.

        Args:
            host: The source host to run traceroute from.
            destination: The destination IP address or hostname.

        Returns:
            The traceroute output, or an error message if failed.
        """
        cmd = f"traceroute {destination}"
        result = await safe_exec(host, ["bash", "-c", cmd], timeout=60)

        if result.success:
            return result.stdout
        return f"[Error]: {result.stderr}"

    return execute


def get_utils_tools() -> list[Tool]:
    """Get utility tools."""
    return [
        get_host_ip(),
        get_default_gateway(),
        get_host_interfaces(),
        get_host_mac_address(),
        ps_list(),
        show_dns_config(),
        traceroute(),
    ]
