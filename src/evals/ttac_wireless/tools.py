"""TTAC Wireless tools. 20 tools matching the original competition server."""

from urllib.parse import parse_qsl, urlencode

from inspect_ai.tool import tool
from inspect_ai.util import sandbox, store

from evals.ttac_wireless.config import SERVER_HOST, SERVER_PORT


def _url(path: str) -> str:
    return f"http://{SERVER_HOST}:{SERVER_PORT}{path}"


def _header() -> str:
    return f"X-Scenario-Id: {store().get('scenario_id')}"


async def _get(path: str) -> str:
    if "?" in path:
        base, query = path.split("?", 1)
        path = f"{base}?{urlencode(parse_qsl(query, keep_blank_values=True))}"
    result = await sandbox().exec(["curl", "-sSf", "-H", _header(), _url(path)])
    if not result.success:
        return f"Error: {result.stderr or result.stdout or 'curl failed'}"
    return result.stdout


# --- Data retrieval tools ---


@tool
def get_throughput_logs():
    async def execute() -> str:
        """Get the timestamped user throughput logs during the drive-test. With the throughput logs, we can identify the poor-quality point, and use the corresponding timestamp to gather more information for analysis by using tools."""
        return await _get("/throughput-logs")

    return execute


@tool
def get_cell_info():
    async def execute(pci: int) -> str:
        """Get full cell configuration given its PCI. The configuration contains cell information including the location, Azimuth, Mech Tilt, Elec Tilt, Ant Height, Duplex Mode, PCI, Band, DL ARFCN, Bandwidth, TX/RX Mode, Transmission Power, InterFreqHoEventType, CovInterFreqA2RsrpThld(dBm), InterFreqA2Hyst(0.5dB), CovInterFreqA5RsrpThld1(dBm), CovInterFreqA5RsrpThld2(dBm), IntraFreqHoA3Offset(0.5dB), IntraFreqHoA3Hyst(0.5dB), IntraFreqHoA3TimeToTrig, Neighbor(gNodeB_ID_ARFCN_PCI), PdcchOccupiedSymbolNum.

        Args:
            pci: Physical Cell ID.
        """
        return await _get(f"/cell-info?pci={pci}")

    return execute


@tool
def get_gnodeb_location():
    async def execute(pci: int) -> str:
        """Get gNodeB (cell) location (longitude, latitude) by PCI.

        Args:
            pci: Physical Cell ID.
        """
        return await _get(f"/gnodeb-location?pci={pci}")

    return execute


@tool
def get_user_location():
    async def execute(time: str) -> str:
        """Get UE location (longitude, latitude) at a given timestamp, e.g. '2024-08-25 19:30:57.500'.

        Args:
            time: Timestamp string.
        """
        return await _get(f"/user-location?time={time}")

    return execute


@tool
def get_serving_cell_pci():
    async def execute(time: str) -> str:
        """Get serving cell PCI at a given timestamp, e.g. '2024-08-25 19:30:57.500'.

        Args:
            time: Timestamp string.
        """
        return await _get(f"/serving-cell-pci?time={time}")

    return execute


@tool
def get_serving_cell_rsrp():
    async def execute(time: str) -> str:
        """Get serving cell SS-RSRP at a given timestamp, e.g. '2024-08-25 19:30:57.500'.

        Args:
            time: Timestamp string.
        """
        return await _get(f"/serving-cell-rsrp?time={time}")

    return execute


@tool
def get_serving_cell_sinr():
    async def execute(time: str) -> str:
        """Get serving cell SS-SINR at a given timestamp, e.g. '2024-08-25 19:30:57.500'.

        Args:
            time: Timestamp string.
        """
        return await _get(f"/serving-cell-sinr?time={time}")

    return execute


@tool
def get_rbs_allocated_to_user():
    async def execute(time: str) -> str:
        """Get the number of RBs allocated to user by the gNodeB at a given timestamp.

        Args:
            time: Timestamp string.
        """
        return await _get(f"/rbs-allocated-to-user?time={time}")

    return execute


@tool
def get_signaling_plane_event_log():
    async def execute(time: str) -> str:
        """Get the signaling plane event log until a given timestamp, e.g. '2024-08-25 19:30:57.500'.

        Args:
            time: Timestamp string.
        """
        return await _get(f"/signaling-plane-event-log?time={time}")

    return execute


@tool
def get_neighboring_cells_pci():
    async def execute(time: str) -> str:
        """Get the neighboring cells PCI of the serving cell at a given timestamp, e.g. '2024-08-25 19:30:57.500'.

        Args:
            time: Timestamp string.
        """
        return await _get(f"/neighboring-cells-pci?time={time}")

    return execute


@tool
def get_neighboring_cell_rsrp():
    async def execute(time: str, pci: int) -> str:
        """Get the beam-level RSRP of a neighboring cell at a given timestamp.

        Args:
            time: Timestamp string.
            pci: Physical Cell ID of the neighbor.
        """
        return await _get(f"/neighboring-cell-rsrp?time={time}&pci={pci}")

    return execute


@tool
def get_all_cells_pci():
    async def execute() -> str:
        """List the PCIs of all cells in the network."""
        return await _get("/all-cells-pci")

    return execute


@tool
def get_kpi_data():
    async def execute() -> str:
        """Get the data with cell-level KPI, including the information of PRB utilization, PRB Interference, Throughput, CCE utilization and CCE Allocation Success Rate."""
        return await _get("/get_kpi_data")

    return execute


@tool
def get_mr_data():
    async def execute() -> str:
        """Get the normal Measurement Report (MR) data surrounding poor-quality users."""
        return await _get("/get_mr_data")

    return execute


# --- Simulation tools ---


@tool
def judge_mainlobe_or_not():
    async def execute(time: str, pci: int) -> str:
        """Judge the user is in the cell's mainlobe or not. True means outside the mainlobe, False means in the mainlobe.

        Args:
            time: Timestamp string.
            pci: Physical Cell ID.
        """
        return await _get(f"/judge_mainlobe?time={time}&pci={pci}")

    return execute


@tool
def calculate_horizontal_angle():
    async def execute(time: str, pci: int) -> str:
        """Calculate the horizontal angle between the user and the cell.

        Args:
            time: Timestamp string.
            pci: Physical Cell ID.
        """
        return await _get(f"/calculate_horizontal_angle?time={time}&pci={pci}")

    return execute


@tool
def calculate_tilt_angle():
    async def execute(time: str, pci: int) -> str:
        """Calculate the tilt angle between the user and the cell.

        Args:
            time: Timestamp string.
            pci: Physical Cell ID.
        """
        return await _get(f"/calculate_tilt_angle?time={time}&pci={pci}")

    return execute


@tool
def calculate_pathloss():
    async def execute(time: str, pci: int) -> str:
        """Calculate the pathloss between the user and the cell.

        Args:
            time: Timestamp string.
            pci: Physical Cell ID.
        """
        return await _get(f"/calculate_pathloss?time={time}&pci={pci}")

    return execute


@tool
def calculate_overlap_ratio():
    async def execute(pci_serving: int, pci_neighbor: int) -> str:
        """Calculate the overlap coverage ratio of the serving cell and the neighbor cell.

        Args:
            pci_serving: PCI of the serving cell.
            pci_neighbor: PCI of the neighbor cell.
        """
        return await _get(
            f"/calculate_overlap_ratio?pci_serving={pci_serving}&pci_neighbor={pci_neighbor}"
        )

    return execute


@tool
def optimize_antenna_gain():
    async def execute(
        time: str, pci: int, adjust_horizontal_angle: float, adjust_tilt_angle: float
    ) -> str:
        """Simulate the RSRP gain if adjust the azimuth angle and tilt angle of the antenna.

        Args:
            time: Timestamp string.
            pci: Physical Cell ID.
            adjust_horizontal_angle: Horizontal angle adjustment in degrees.
            adjust_tilt_angle: Tilt angle adjustment in degrees.
        """
        return await _get(
            f"/optimize_antenna_gain?time={time}&pci={pci}"
            f"&adjust_horizontal_angle={adjust_horizontal_angle}"
            f"&adjust_tilt_angle={adjust_tilt_angle}"
        )

    return execute


# --- Tool list (used by task.py) ---


def all_tools() -> list:
    """Return all 20 tools as instantiated tool objects."""
    return [
        get_throughput_logs(),
        get_cell_info(),
        get_gnodeb_location(),
        get_user_location(),
        get_serving_cell_pci(),
        get_serving_cell_rsrp(),
        get_serving_cell_sinr(),
        get_rbs_allocated_to_user(),
        get_signaling_plane_event_log(),
        get_neighboring_cells_pci(),
        get_neighboring_cell_rsrp(),
        get_all_cells_pci(),
        get_kpi_data(),
        get_mr_data(),
        judge_mainlobe_or_not(),
        calculate_horizontal_angle(),
        calculate_tilt_angle(),
        calculate_pathloss(),
        calculate_overlap_ratio(),
        optimize_antenna_gain(),
    ]


_TOOL_BUILDERS = {
    "get_throughput_logs": get_throughput_logs,
    "get_cell_info": get_cell_info,
    "get_gnodeb_location": get_gnodeb_location,
    "get_user_location": get_user_location,
    "get_serving_cell_pci": get_serving_cell_pci,
    "get_serving_cell_rsrp": get_serving_cell_rsrp,
    "get_serving_cell_sinr": get_serving_cell_sinr,
    "get_rbs_allocated_to_user": get_rbs_allocated_to_user,
    "get_signaling_plane_event_log": get_signaling_plane_event_log,
    "get_neighboring_cells_pci": get_neighboring_cells_pci,
    "get_neighboring_cell_rsrp": get_neighboring_cell_rsrp,
    "get_all_cells_pci": get_all_cells_pci,
    "get_kpi_data": get_kpi_data,
    "get_mr_data": get_mr_data,
    "judge_mainlobe_or_not": judge_mainlobe_or_not,
    "calculate_horizontal_angle": calculate_horizontal_angle,
    "calculate_tilt_angle": calculate_tilt_angle,
    "calculate_pathloss": calculate_pathloss,
    "calculate_overlap_ratio": calculate_overlap_ratio,
    "optimize_antenna_gain": optimize_antenna_gain,
}


def filter_allowed(names: list[str]) -> list:
    """Return instantiated tools filtered by name.

    `["all"]` returns every tool. Unknown names are dropped silently.
    """
    if names == ["all"]:
        return all_tools()
    return [_TOOL_BUILDERS[n]() for n in names if n in _TOOL_BUILDERS]
