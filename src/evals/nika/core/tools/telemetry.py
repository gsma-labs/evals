"""InfluxDB telemetry tools for querying in-band network telemetry data."""

import csv
import io
import json

from inspect_ai.tool import Tool, tool

from evals.nika.core.tools._sandbox import safe_exec

# InfluxDB configuration (consistent with Kathara lab setup)
INFLUX_TOKEN = "int_token"
INFLUX_ORG = "int_org"
INFLUX_BUCKET = "int_bucket"


def _csv_to_json(query_result: str) -> str:
    """Convert InfluxDB CSV query result to JSON format."""
    lines = [
        line for line in query_result.splitlines() if line.strip() and not line.startswith("#")
    ]

    header = None
    data_lines = []
    for line in lines:
        if line.startswith(",result,") and header is None:
            header = line.split(",")
            continue
        data_lines.append(line)

    if not header or not data_lines:
        return json.dumps([])

    reader = csv.DictReader(io.StringIO("\n".join(data_lines)), fieldnames=header)
    rows = list(reader)
    return json.dumps(rows, indent=2)


@tool
def influx_list_buckets() -> Tool:
    """List all InfluxDB buckets."""

    async def execute(host: str = "collector") -> str:
        """List all buckets in the InfluxDB instance.

        Args:
            host: Host name where InfluxDB is running (default: "collector")

        Returns:
            JSON list of all buckets in the InfluxDB instance
        """
        cmd = "influx bucket list --json"
        result = await safe_exec(host, ["bash", "-c", cmd], timeout=15)
        if not result.success:
            return f"[Error]: {result.stderr}"
        return result.stdout

    return execute


@tool
def influx_get_measurements() -> Tool:
    """List all measurements in the InfluxDB bucket."""

    async def execute(host: str = "collector") -> str:
        """List all measurements (tables) in the InfluxDB bucket.

        Args:
            host: Host name where InfluxDB is running (default: "collector")

        Returns:
            List of measurement names in the bucket
        """
        cmd = f"""influx query 'import "influxdata/influxdb/schema" schema.measurements(bucket: "{INFLUX_BUCKET}")'"""
        result = await safe_exec(host, ["bash", "-c", cmd], timeout=15)
        if not result.success:
            return f"[Error]: {result.stderr}"
        return result.stdout

    return execute


@tool
def influx_count_measurements() -> Tool:
    """Count the number of records in a measurement."""

    async def execute(measurement: str, host: str = "collector") -> str:
        """Count the size of all records in a measurement.

        Args:
            measurement: Name of the measurement to count
            host: Host name where InfluxDB is running (default: "collector")

        Returns:
            JSON with the count of records in the measurement
        """
        cmd = (
            f'curl -sS --request POST "http://localhost:8086/api/v2/query?org={INFLUX_ORG}" '
            f'--header "Authorization: Token {INFLUX_TOKEN}" '
            '--header "Accept: application/csv" '
            '--header "Content-type: application/vnd.flux" '
            "--data '"
            f'from(bucket: "{INFLUX_BUCKET}")\n'
            "  |> range(start: -1h)\n"
            f'  |> filter(fn: (r) => r["_measurement"] == "{measurement}")\n'
            "  |> group(columns: [])\n"
            "  |> count()"
            "'"
        )
        result = await safe_exec(host, ["bash", "-c", cmd], timeout=15)
        if not result.success:
            return f"[Error]: {result.stderr}"
        return _csv_to_json(result.stdout)

    return execute


@tool
def influx_query_measurement() -> Tool:
    """Query measurement data with pagination."""

    async def execute(
        measurement: str,
        limit: int = 10,
        offset: int = 0,
        host: str = "collector",
    ) -> str:
        """Execute a query against an InfluxDB measurement with pagination.

        Large Dataset Warning: InfluxDB might contain massive time-series data.
        Always use influx_count_measurements() first to check size, then use
        limit/offset for large results (>1000 rows).

        Args:
            measurement: Name of the measurement to query
            limit: Maximum number of records to return (default: 10)
            offset: Number of records to skip (default: 0)
            host: Host name where InfluxDB is running (default: "collector")

        Returns:
            JSON array of records from the measurement
        """
        cmd = (
            f'curl -sS --request POST "http://localhost:8086/api/v2/query?org={INFLUX_ORG}" '
            f'--header "Authorization: Token {INFLUX_TOKEN}" '
            '--header "Accept: application/csv" '
            '--header "Content-type: application/vnd.flux" '
            "--data '"
            f'from(bucket: "{INFLUX_BUCKET}")\n'
            "  |> range(start: -1h)\n"
            f'  |> filter(fn: (r) => r["_measurement"] == "{measurement}")\n'
            f"  |> limit(n: {limit}, offset: {offset})"
            "'"
        )
        result = await safe_exec(host, ["bash", "-c", cmd], timeout=15)
        if not result.success:
            return f"[Error]: {result.stderr}"
        return _csv_to_json(result.stdout)

    return execute


def get_telemetry_tools() -> list[Tool]:
    """Get InfluxDB telemetry tools.

    Returns a list of tools for querying in-band network telemetry data:
    - influx_list_buckets: List all InfluxDB buckets
    - influx_get_measurements: List measurements in the bucket
    - influx_count_measurements: Count records in a measurement
    - influx_query_measurement: Query measurement data with pagination

    Returns:
        List of Tool instances
    """
    return [
        influx_list_buckets(),
        influx_get_measurements(),
        influx_count_measurements(),
        influx_query_measurement(),
    ]
