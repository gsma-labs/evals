"""Kathara tools for network emulation labs.

This module provides Inspect AI native tools for network troubleshooting
in Kathara environments.

Usage:
    from build_images.tools import get_nika_tools, create_submit_tool

    tools = get_nika_tools(include_base=True, include_frr=True, include_tc=True)
"""

# Native tools - base and FRR
# Native tools - specialized
from evals.nika.core.tools.bmv2 import get_bmv2_tools
from evals.nika.core.tools.interface import get_interface_tools
from evals.nika.core.tools.native_tools import (
    get_base_tools,
    get_frr_tools,
    get_nika_tools,
)
from evals.nika.core.tools.nftables import get_nftables_tools

# Submit tool
from evals.nika.core.tools.submit import Submission, create_submit_tool
from evals.nika.core.tools.tc import get_tc_tools
from evals.nika.core.tools.telemetry import get_telemetry_tools
from evals.nika.core.tools.utils import get_utils_tools

__all__ = [
    # Native tool factories
    "get_base_tools",
    "get_frr_tools",
    "get_nika_tools",
    "get_bmv2_tools",
    "get_interface_tools",
    "get_nftables_tools",
    "get_tc_tools",
    "get_telemetry_tools",
    "get_utils_tools",
    # Submit tool
    "Submission",
    "create_submit_tool",
]
