"""Unified entrypoint for NIKA evaluation."""

from collections import defaultdict
from typing import Any, Literal

import yaml
from inspect_ai import Task, task
from inspect_ai.agent import react
from inspect_ai.dataset import MemoryDataset
from inspect_ai.solver import Generate, Solver, TaskState, solver
from inspect_ai.util import sandbox

from evals.nika.core.dataset_build import DATASET_PATH, load_yaml
from evals.nika.core.prompts import build_prompt
from evals.nika.core.tools import create_submit_tool, get_nika_tools
from evals.nika.scorer import (
    TaskLevel,
    detection_scorer,
    full_scorer,
    localization_scorer,
    rca_scorer,
)

submit = create_submit_tool()
SMALL_SAMPLE_SIZE = "size_s"
SANDBOX_PATH_MIN_ITEMS = 2
TARGET_WITH_FAILURE_MIN_ITEMS = 3
TaskFamily = Literal[
    "all",
    "link_failure",
    "end_host_failure",
    "misconfiguration",
    "resource_contention",
    "network_under_attack",
    "network_node_error",
    "multiple_faults",
]
VariantName = str


def _ensure_kathara_available() -> None:
    try:
        from inspect_kathara.sandbox import KatharaSandboxEnvironment  # noqa: F401
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "NIKA requires optional dependency 'inspect-kathara'. "
            "Install it with: uv sync --extra nika"
        ) from exc


def _read_records(dataset_path: str) -> list[dict[str, Any]]:
    with open(dataset_path) as file:
        data = yaml.safe_load(file)
    return data.get("samples", [])


def _is_small_sample(record: dict[str, Any]) -> bool:
    sandbox_cfg = record.get("sandbox", [])
    if len(sandbox_cfg) >= SANDBOX_PATH_MIN_ITEMS and isinstance(sandbox_cfg[1], str):
        # Prefer explicit size folder in sandbox path; fall back to id naming
        # for scenarios that don't encode size in path (e.g. p4/*/compose.yaml).
        if f"/{SMALL_SAMPLE_SIZE}/" in f"/{sandbox_cfg[1]}/":
            return True
    return f"_{SMALL_SAMPLE_SIZE}_" in str(record.get("id", ""))


def _failure_key(record: dict[str, Any]) -> str:
    target = record.get("target", [])
    if isinstance(target, list) and len(target) >= TARGET_WITH_FAILURE_MIN_ITEMS:
        failure = target[2]
        if isinstance(failure, list):
            return ",".join(sorted(str(item) for item in failure))
        return str(failure)
    return str(record.get("metadata", {}).get("variant", "unknown"))


def _select_small_ids(records: list[dict[str, Any]]) -> list[str]:
    selected: dict[tuple[str, str], str] = {}
    for record in records:
        sample_id = record.get("id")
        family_id = record.get("family_id")
        if not isinstance(sample_id, str) or not isinstance(family_id, str):
            continue
        if not _is_small_sample(record):
            continue

        # Keep only one size_s sample per (family, failure type) for small benchmark.
        key = (family_id, _failure_key(record))
        if key not in selected:
            selected[key] = sample_id
    return list(selected.values())


def _selected_sample_ids(full: bool, dataset_path: str) -> list[str] | None:
    records = _read_records(dataset_path)
    if full:
        return None
    return _select_small_ids(records)


def _load_nika_dataset(
    full: bool,
    dataset_path: str,
    task_family: str,
    variant: str,
) -> MemoryDataset:
    records = _read_records(dataset_path)
    family_order: list[str] = []
    grouped_ids: dict[str, list[str]] = defaultdict(list)
    selected_ids = _selected_sample_ids(full, dataset_path)
    selected_set = set(selected_ids) if selected_ids is not None else None
    for record in records:
        family_id = record.get("family_id")
        sample_id = record.get("id")
        if not isinstance(family_id, str) or not isinstance(sample_id, str):
            continue
        if task_family not in {"all", family_id}:
            continue
        record_variant = str(record.get("metadata", {}).get("variant", ""))
        if variant not in {"all", record_variant}:
            continue
        if family_id not in family_order:
            family_order.append(family_id)
        if selected_set is not None and sample_id not in selected_set:
            continue
        grouped_ids[family_id].append(sample_id)

    samples = []
    for family_id in family_order:
        family_sample_ids = grouped_ids.get(family_id, [])
        if not family_sample_ids:
            continue
        family_dataset = load_yaml(family_id, sample_ids=family_sample_ids)
        samples.extend(family_dataset.samples)

    return MemoryDataset(
        samples=samples,
        name="nika_full" if full else "nika_small",
    )


@solver
def inject_nika_faults() -> Solver:
    """Inject one or more faults defined in sample metadata."""

    async def solve(state: TaskState, generate: Generate) -> TaskState:
        faults = state.metadata.get("faults", [])
        if isinstance(faults, list) and faults:
            for fault in faults:
                if not isinstance(fault, dict):
                    continue
                device = fault.get("device")
                setup = fault.get("setup")
                if setup and device and str(device).lower() != "none":
                    await sandbox(name=str(device)).exec(cmd=["sh", "-c", str(setup)])
            return state

        target_device = state.metadata.get("target_device")
        fault_setup = state.metadata.get("fault_setup")
        if fault_setup and target_device and str(target_device).lower() != "none":
            await sandbox(name=str(target_device)).exec(cmd=["sh", "-c", str(fault_setup)])

        return state

    return solve


@solver
def nika_agent() -> Solver:
    """Unified NIKA troubleshooting agent with full toolset."""

    async def solve(state: TaskState, generate: Generate) -> TaskState:
        tools = get_nika_tools(
            include_base=True,
            include_frr=True,
            include_interface=True,
            include_nftables=True,
            include_tc=True,
            include_utils=True,
        )
        agent = react(
            description="Expert at network troubleshooting.",
            prompt=build_prompt(),
            tools=[*tools, submit()],
            submit=False,
        )
        return await agent(state)

    return solve


@task
def nika(
    dataset_path: str = str(DATASET_PATH),
    split: str = "test",
    full: bool = False,
    task_family: TaskFamily = "all",
    variant: VariantName = "all",
    task_level: TaskLevel = "full",
) -> Task:
    """Run NIKA with full samples or compact small samples.

    Args:
        dataset_path: Dataset yaml path. Defaults to bundled NIKA dataset.
        split: Reserved for API consistency with other eval entries.
        task_level: Scoring mode.
            - "full": 20% detection + 40% localization + 40% RCA (default)
            - "detection": anomaly detection only
            - "localization": faulty device localization only
            - "rca": root cause analysis only
        full: Whether to use full samples (default: False).
            - False: small samples (size_s only, one sample per failure, no variants)
            - True: full samples
        task_family: Restrict to one task family (default: "all").
        variant: Restrict to one failure variant (default: "all"), e.g. "bmv2_down".
    """
    _ensure_kathara_available()

    match task_level:
        case "detection":
            scorer = detection_scorer()
        case "localization":
            scorer = localization_scorer()
        case "rca":
            scorer = rca_scorer()
        case _:
            scorer = full_scorer()

    return Task(
        dataset=_load_nika_dataset(
            full=full,
            dataset_path=dataset_path,
            task_family=task_family,
            variant=variant,
        ),
        solver=[inject_nika_faults(), nika_agent()],
        scorer=scorer,
    )
