"""Submit tool factory for Nika diagnosis tasks."""

from pathlib import Path

import yaml
from inspect_ai.tool import tool
from inspect_ai.util import StoreModel, store_as

_FAILURE_YAML_PATH = Path(__file__).resolve().parents[5] / "data" / "nika" / "failure.yaml"


def load_all_valid_root_causes(
    task_family: str | None = None,
) -> tuple[list[str], dict[str, str]]:
    """Load valid root cause ids and descriptions from data/nika/failure.yaml.

    If task_family is None, returns all failure ids. Otherwise returns only ids
    whose failure has task_family equal to the given family or "*" (e.g. baseline, none).
    """
    if not _FAILURE_YAML_PATH.exists():
        return [], {}

    with open(_FAILURE_YAML_PATH) as f:
        data = yaml.safe_load(f)

    valid_root_causes: list[str] = []
    valid_root_cause_descriptions: dict[str, str] = {}

    for failure in data.get("failures") or []:
        fid = failure.get("id")
        fam = failure.get("task_family")
        selectable = failure.get("selectable", True)
        description = failure.get("description")
        if fid is None:
            continue
        if not selectable:
            continue
        fid = str(fid)
        if task_family is not None and fam not in {"*", task_family}:
            continue
        valid_root_causes.append(fid)
        if description is not None:
            text = description.strip() if isinstance(description, str) else "\n".join(description).strip()
            valid_root_cause_descriptions[fid] = text

    return valid_root_causes, valid_root_cause_descriptions


class Submission(StoreModel):
    """Agent submission stored in state."""

    is_anomaly: bool | None = None
    faulty_devices: list[str] = []
    root_cause_names: list[str] = []

    @property
    def root_cause_name(self) -> str | None:
        """Backward-compatible property for single-fault cases."""
        return self.root_cause_names[0] if self.root_cause_names else None


def create_submit_tool(task_family: str | None = None):
    """Factory for creating task-specific submit tools."""
    if task_family is None:
        valid_root_causes, root_cause_descriptions = load_all_valid_root_causes()
    else:
        valid_root_causes, root_cause_descriptions = load_all_valid_root_causes(task_family)

    @tool
    def submit():
        async def execute(is_anomaly: bool, faulty_devices: list[str], root_cause_names: str | list[str]) -> str:
            """Submit your final diagnosis."""
            # Normalize to list
            if isinstance(root_cause_names, str):
                rca_list = [root_cause_names]
            else:
                rca_list = root_cause_names

            # Validate all root causes
            invalid = [rc for rc in rca_list if rc not in valid_root_causes]
            if invalid:
                return f"Error: Invalid root cause(s): {invalid}. Valid options: {', '.join(valid_root_causes)}"

            submission = store_as(Submission)
            submission.is_anomaly = is_anomaly
            submission.faulty_devices = faulty_devices
            submission.root_cause_names = rca_list

            return f"Submitted: anomaly={is_anomaly}, devices={faulty_devices}, rca={rca_list}"

        execute.__doc__ = f"""Submit your final diagnosis.

Args:
    is_anomaly: True if anomaly detected, False otherwise.
    faulty_devices: List of faulty device names.
    root_cause_names: Root cause type(s). Can be a single string or list of strings for multi-fault scenarios.
        Valid options: {", ".join(valid_root_causes)}
"""
        return execute

    return submit


if __name__ == "__main__":
    print(load_all_valid_root_causes())
