"""nftables firewall tools for packet filtering and NAT configuration."""

from inspect_ai.tool import Tool, tool

from evals.nika.core.tools._sandbox import safe_exec


@tool
def nft_list_ruleset() -> Tool:
    """List all nftables rules with handle numbers."""

    async def execute(host: str) -> str:
        """List all nftables rules on a host.

        Args:
            host: Name of the host machine

        Returns:
            Complete nftables ruleset with handle numbers
        """
        result = await safe_exec(host, ["nft", "-a", "list", "ruleset"], timeout=10)
        if not result.success:
            return f"[Error]: {result.stderr}"
        return result.stdout

    return execute


@tool
def nft_list_tables() -> Tool:
    """List all nftables tables."""

    async def execute(host: str) -> str:
        """List all nftables tables on a host.

        Args:
            host: Name of the host machine

        Returns:
            List of nftables tables
        """
        result = await safe_exec(host, ["nft", "list", "tables"], timeout=10)
        if not result.success:
            return f"[Error]: {result.stderr}"
        return result.stdout

    return execute


@tool
def nft_list_chains() -> Tool:
    """List all nftables chains."""

    async def execute(host: str) -> str:
        """List all nftables chains on a host.

        Args:
            host: Name of the host machine

        Returns:
            List of nftables chains
        """
        result = await safe_exec(host, ["nft", "list", "chains"], timeout=10)
        if not result.success:
            return f"[Error]: {result.stderr}"
        return result.stdout

    return execute


@tool
def nft_add_table() -> Tool:
    """Add a new nftables table."""

    async def execute(host: str, table_name: str, family: str = "inet") -> str:
        """Add a new nftables table on a host.

        Args:
            host: Name of the host machine
            table_name: Name of the table to create
            family: Address family (default: 'inet' for IPv4/IPv6)

        Returns:
            Command output or error message
        """
        result = await safe_exec(host, ["nft", "add", "table", family, table_name], timeout=10)
        if not result.success:
            return f"[Error]: {result.stderr}"
        return result.stdout or f"Table {family} {table_name} created successfully"

    return execute


@tool
def nft_add_chain() -> Tool:
    """Add a new nftables chain to a table."""

    async def execute(
        host: str,
        table: str,
        chain: str,
        family: str = "inet",
        hook: str | None = None,
        chain_type: str | None = None,
        policy: str | None = None,
    ) -> str:
        """Add a new nftables chain to a table on a host.

        Args:
            host: Name of the host machine
            table: Name of the table to add the chain to
            chain: Name of the chain to create
            family: Address family (default: 'inet' for IPv4/IPv6)
            hook: Hook point (e.g., 'input', 'output', 'forward', 'prerouting', 'postrouting')
            chain_type: Chain type (e.g., 'filter', 'nat', 'route')
            policy: Default policy for the chain (e.g., 'accept', 'drop')

        Returns:
            Command output or error message
        """
        cmd = f"nft add chain {family} {table} {chain}"
        if chain_type and hook:
            policy_part = f" policy {policy} ;" if policy else ""
            chain_spec = f"{{ type {chain_type} hook {hook} priority 0 ;{policy_part} }}"
            cmd += f" '{chain_spec}'"

        result = await safe_exec(host, ["bash", "-c", cmd], timeout=10)
        if not result.success:
            return f"[Error]: {result.stderr}"
        return result.stdout or f"Chain {chain} added to {family} {table} successfully"

    return execute


@tool
def nft_add_rule() -> Tool:
    """Add a rule to an nftables chain."""

    async def execute(host: str, table: str, chain: str, rule: str, family: str = "inet") -> str:
        """Add a rule to an nftables chain on a host.

        Args:
            host: Name of the host machine
            table: Name of the table containing the chain
            chain: Name of the chain to add the rule to
            rule: The rule specification (e.g., 'tcp dport 22 accept')
            family: Address family (default: 'inet' for IPv4/IPv6)

        Returns:
            Command output or error message
        """
        cmd = f"nft add rule {family} {table} {chain} {rule}"
        result = await safe_exec(host, ["bash", "-c", cmd], timeout=10)
        if not result.success:
            return f"[Error]: {result.stderr}"
        return result.stdout or f"Rule added to {family} {table} {chain} successfully"

    return execute


@tool
def nft_delete_table() -> Tool:
    """Delete an nftables table."""

    async def execute(host: str, table_name: str, family: str = "inet") -> str:
        """Delete an nftables table from a host.

        Args:
            host: Name of the host machine
            table_name: Name of the table to delete
            family: Address family (default: 'inet' for IPv4/IPv6)

        Returns:
            Command output or error message
        """
        result = await safe_exec(host, ["nft", "delete", "table", family, table_name], timeout=10)
        if not result.success:
            return f"[Error]: {result.stderr}"
        return result.stdout or f"Table {family} {table_name} deleted successfully"

    return execute


def get_nftables_tools() -> list[Tool]:
    """Get nftables firewall tools.

    Returns a list of tools for managing nftables firewall rules:
    - nft_list_ruleset: List all rules with handle numbers
    - nft_list_tables: List all tables
    - nft_list_chains: List all chains
    - nft_add_table: Add a new table
    - nft_add_chain: Add a chain to a table
    - nft_add_rule: Add a rule to a chain
    - nft_delete_table: Delete a table

    Returns:
        List of Tool instances
    """
    return [
        nft_list_ruleset(),
        nft_list_tables(),
        nft_list_chains(),
        nft_add_table(),
        nft_add_chain(),
        nft_add_rule(),
        nft_delete_table(),
    ]
