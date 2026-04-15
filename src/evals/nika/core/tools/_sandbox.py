"""Safe sandbox execution with helpful error messages for invalid hosts."""

from inspect_ai.util import sandbox
from inspect_ai.util._sandbox.environment import ExecResult

DEVICE_NAMING_HINT = """
Invalid device name. Valid device naming in CLOS topology:
- Hosts: pc_X_Y where X=pod (0-1), Y=host_id (0-3)
- Leaf routers: leaf_router_X_Y where X=pod (0-1), Y=router_id (0-3)
- Spine routers: spine_router_X_Y where X=pod (0-1), Y=router_id (0-3)
- Super-spine: super_spine_router_0, super_spine_router_1
- DNS: dns_0, dns_1
- Web servers: web_X_Y where X=pod (0-1), Y=leaf_id (0-3)
- Clients: client_0, client_1
"""


async def safe_exec(host: str, cmd: list[str], timeout: int = 10) -> ExecResult:
    """Execute command on sandbox, returning helpful error if host doesn't exist."""
    try:
        return await sandbox(host).exec(cmd, timeout=timeout)
    except ValueError:
        return ExecResult(
            success=False,
            returncode=1,
            stdout="",
            stderr=f"'{host}' is not a valid device name.{DEVICE_NAMING_HINT}",
        )
