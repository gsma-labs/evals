"""Dataset loading for NIKA tasks."""

import json
import subprocess
import sys
from pathlib import Path

import yaml
from inspect_ai.dataset import MemoryDataset, Sample

from evals.nika.core.templates import get_vars

_REPO_ROOT = Path(__file__).resolve().parents[4]
DATASET_PATH = _REPO_ROOT / "data" / "nika" / "dataset.yaml"
SCENARIOS_DIR = Path(__file__).resolve().parent / "scenarios"

DEFAULT_VARIANT = "none"
DEFAULT_DIFFICULTY = "medium"
SANDBOX_CONFIG_MIN_ITEMS = 2


def _generate_compose_for_inspect(lab_dir: Path) -> str:
    try:
        from inspect_kathara.sandbox import generate_compose_for_inspect
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "NIKA requires optional dependency 'inspect-kathara'. "
            "Install it with: uv sync --extra nika"
        ) from exc
    return generate_compose_for_inspect(lab_dir)


def _resolve_sandbox(sandbox: list, target_device: str | None = None) -> tuple:
    """Resolve sandbox config to absolute path."""
    if len(sandbox) < SANDBOX_CONFIG_MIN_ITEMS:
        return tuple(sandbox)

    sandbox_type, config_path = sandbox[0], sandbox[1]

    if not Path(config_path).is_absolute():
        config_path = str((SCENARIOS_DIR / config_path).resolve())

    path = Path(config_path)

    if path.is_file() and path.suffix == ".py":
        subprocess.run([sys.executable, path.name], cwd=str(path.parent), check=True)
        lab_dir = path.parent / "topology"
        compose_yaml = _generate_compose_for_inspect(lab_dir)
        compose_path = lab_dir / "compose.yaml"
        compose_path.parent.mkdir(parents=True, exist_ok=True)
        compose_path.write_text(compose_yaml)
        config_path = str(compose_path)
    elif path.name == "lab.conf" and path.is_file():
        lab_dir = path.parent
        compose_yaml = _generate_compose_for_inspect(lab_dir)
        compose_path = lab_dir / "compose.yaml"
        compose_path.write_text(compose_yaml)
        config_path = str(compose_path)
    elif path.is_dir() and (path / "lab.conf").exists():
        compose_yaml = _generate_compose_for_inspect(path)
        compose_path = path / "compose.yaml"
        compose_path.write_text(compose_yaml)
        config_path = str(compose_path)

    if target_device and target_device.lower() != "none":
        return (sandbox_type, config_path, {"default": target_device})

    return (sandbox_type, config_path)


def _inject_template(text: str, family: str, metadata: dict, compose_path: str) -> str:
    """Inject template variables into text."""
    template_vars = get_vars(
        family=family,
        variant=metadata.get("variant") or DEFAULT_VARIANT,
        difficulty=metadata.get("difficulty") or DEFAULT_DIFFICULTY,
        compose_path=compose_path,
    )
    return text.format(**template_vars)


def load_yaml(
    family_id: str,
    dataset_path: Path | None = None,
    sample_ids: list[str] | None = None,
) -> MemoryDataset:
    """Load samples filtered by family_id with template injection."""
    path = dataset_path if dataset_path is not None else DATASET_PATH
    with open(path) as file:
        data = yaml.safe_load(file)

    samples = []
    for record in data["samples"]:
        if record.get("family_id") != family_id:
            continue
        if sample_ids is not None and record.get("id") not in sample_ids:
            continue

        sample_metadata = record.get("metadata", {}).copy()
        setup = record.get("setup")
        if setup is not None:
            sample_metadata["fault_setup"] = setup
            if "target_device" not in sample_metadata:
                raise ValueError(
                    f"Sample '{record.get('id', '?')}' has setup but metadata.target_device is missing; "
                    "add target_device (or 'none') to metadata"
                )

        sandbox_config = record.get("sandbox", [])
        if len(sandbox_config) < SANDBOX_CONFIG_MIN_ITEMS:
            raise ValueError(
                f"Sample '{record.get('id', '?')}' must have sandbox with compose path, "
                "e.g. [kathara, 'category/scenario/size_s/compose.yaml']"
            )
        compose_path = sandbox_config[1]
        if not isinstance(compose_path, str) or not compose_path.strip():
            raise ValueError(f"Sample '{record.get('id', '?')}' sandbox[1] must be a non-empty compose path string")
        if not Path(compose_path).is_absolute():
            compose_path = str(Path(compose_path).as_posix())

        samples.append(
            Sample(
                id=record["id"],
                input=_inject_template(
                    record["input"],
                    family_id,
                    record.get("metadata", {}),
                    compose_path,
                ),
                target=json.dumps(record["target"]),
                sandbox=_resolve_sandbox(
                    record["sandbox"],
                    sample_metadata.get("target_device"),
                ),
                metadata=sample_metadata,
            )
        )

    return MemoryDataset(samples=samples, name=family_id)
