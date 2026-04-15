r"""Dynamic prompt templates for NIKA evaluations.

This module provides template variables for constructing evaluation prompts.
Templates use Python's str.format() with three placeholders:
- {symptom}: Problem description based on fault variant
- {guidance}: Difficulty-appropriate hints
- {topology}: Network architecture description (from build_images/scenarios/scenario.yaml)

Usage:
    # compose_path (or scenario) is required; topology is taken from scenario.yaml
    vars = get_vars(
        "link_failure", "link_down", "easy",
        compose_path="data_center/dc_clos_worker/size_m/compose.yaml",
    )
    prompt = "{symptom}\\n{topology}\\n{guidance}".format(**vars)

Adding new variants:
    1. Add failure entry with symptom in data/nika/failure.yaml
    2. Use the variant name in dataset.yaml metadata
"""

from pathlib import Path

import yaml

# Path to failure catalog (data/nika/failure.yaml)
_REPO_ROOT = Path(__file__).resolve().parents[4]
_FAILURE_YAML_PATH = _REPO_ROOT / "data" / "nika" / "failure.yaml"


def _load_symptoms_from_failure_yaml() -> dict[str, str]:
    """Load symptom text keyed by failure id from data/nika/failure.yaml."""
    result: dict[str, str] = {}
    if not _FAILURE_YAML_PATH.exists():
        return result
    with open(_FAILURE_YAML_PATH) as f:
        data = yaml.safe_load(f)
    for failure in data.get("failures") or []:
        fid = failure.get("id")
        symptom = failure.get("symptom")
        if fid is not None and symptom is not None:
            text = symptom.strip() if isinstance(symptom, str) else "\n".join(symptom).strip()
            result[str(fid)] = text
    return result


# Symptom descriptions keyed by fault variant name (loaded from failure.yaml).
SYMPTOMS: dict[str, str] = _load_symptoms_from_failure_yaml()

# Hint text keyed by difficulty level (easy/medium/hard).
GUIDANCE: dict[str, str] = {
    "easy": "Hint: The problem is likely localized to a single device.",
    "medium": "Hint: The problem may involve multiple devices. Test from multiple vantage points.",
    "hard": "Hint: This may require deep analysis of routing tables, BGP sessions, or traffic control settings.",
}

# Scenario registry path (relative to this file: build_images/templates.py -> build_images/scenarios/scenario.yaml)
_SCENARIO_YAML_PATH = Path(__file__).parent / "scenarios" / "scenario.yaml"


def _normalize_desc(text: str | list | None) -> str:
    """Normalize description/device_naming field to a single string."""
    if text is None:
        return ""
    if isinstance(text, str):
        return text.strip()
    return "\n".join(str(line) for line in text).strip()


def _load_scenario_network_info() -> dict[str, dict[str, str]]:
    """Load scenario.yaml; return mapping compose_path -> {description, device_naming}."""
    if not _SCENARIO_YAML_PATH.exists():
        return {}
    with open(_SCENARIO_YAML_PATH) as f:
        data = yaml.safe_load(f)
    scenarios = data.get("scenarios") or []
    result: dict[str, dict[str, str]] = {}
    for s in scenarios:
        path = s.get("compose_path")
        if not path:
            continue
        result[path] = {
            "description": _normalize_desc(s.get("description")),
            "device_naming": _normalize_desc(s.get("device_naming")),
        }
    return result


_SCENARIO_NETWORK_INFO: dict[str, dict[str, str]] = _load_scenario_network_info()


def _get_topology_for_compose_path(compose_path: str) -> str:
    """Resolve compose path to topology string from scenario.yaml (description + device_naming)."""
    path = compose_path.strip()
    if not path:
        raise ValueError("compose_path must be non-empty")
    path = path.replace("\\", "/")
    if path.startswith("/"):
        path = path.lstrip("/")
    if path not in _SCENARIO_NETWORK_INFO:
        raise ValueError(f"Unknown compose_path '{path}'. Add it to scenario.yaml.")
    info = _SCENARIO_NETWORK_INFO[path]
    description = info.get("description") or ""
    device_naming = info.get("device_naming") or ""
    parts = [p for p in (description, device_naming) if p]
    return "\n\n".join(parts)


# Valid keys for external validation
VALID_VARIANTS = frozenset(SYMPTOMS.keys())
VALID_DIFFICULTIES = frozenset(GUIDANCE.keys())
VALID_FAMILIES = frozenset(
    {
        "link_failure",
        "end_host_failure",
        "misconfiguration",
        "resource_contention",
        "multiple_faults",
        "network_under_attack",
        "network_node_error",
    }
)


def get_vars(
    family: str,
    variant: str,
    difficulty: str,
    compose_path: str,
) -> dict[str, str]:
    """Return template variables for a sample.

    Args:
        family: Task family (link_failure, end_host_failure, misconfiguration, resource_contention, multiple_faults)
        variant: Fault variant (link_down, dns_server_down, bgp_hijacking, etc.)
        difficulty: Difficulty level (easy, medium, hard)
        compose_path: Path to compose.yaml (relative to build_images/scenarios).
            Topology description is taken from this scenario in scenario.yaml.
            Aliases (e.g. data_center/dc_clos_worker/compose.yaml) are resolved automatically.

    Returns:
        Dict with symptom, guidance, and topology strings.

    Raises:
        ValueError: If any parameter is not a valid key, or compose_path is unknown.
    """
    if variant not in SYMPTOMS:
        raise ValueError(f"Invalid variant '{variant}'. Valid: {sorted(SYMPTOMS.keys())}")
    if difficulty not in GUIDANCE:
        raise ValueError(f"Invalid difficulty '{difficulty}'. Valid: {sorted(GUIDANCE.keys())}")
    if family not in VALID_FAMILIES:
        raise ValueError(f"Invalid family '{family}'. Valid: {sorted(VALID_FAMILIES)}")
    topology = _get_topology_for_compose_path(compose_path)
    return {
        "symptom": SYMPTOMS[variant],
        "guidance": GUIDANCE[difficulty],
        "topology": topology,
    }
