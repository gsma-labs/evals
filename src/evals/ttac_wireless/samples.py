"""TTAC Wireless sample loading. Dict in, Sample out."""

from __future__ import annotations

import json

from inspect_ai.dataset import Sample

from evals.ttac_wireless.config import LITE_SIZE, SANDBOX_DIR


def _build_context_preamble(context: dict | None) -> str:
    if not context:
        return ""
    parts = []
    description = (context.get("description") or "").strip()
    if description:
        parts.append(description)
    wni = context.get("wireless_network_information") or {}
    if wni:
        fields = "; ".join(f"{k}={v}" for k, v in wni.items())
        parts.append(f"Network: {fields}")
    return "\n".join(parts)


def record_to_sample(record: dict, *, faithful: bool = False) -> Sample:
    """Convert one scenario record into an Inspect Sample."""
    scenario_id = record["scenario_id"]
    task = record["task"]

    description = task["description"]
    options = task["options"]
    options_text = "\n".join(f"{opt['id']}: {opt['label']}" for opt in options)
    body = f"{description}\n\nOptions:\n{options_text}"

    if faithful:
        question = body
    else:
        preamble = _build_context_preamble(record.get("context"))
        question = f"{preamble}\n\n{body}" if preamble else body

    allowed = task.get("allowed_tools", ["all"])
    if isinstance(allowed, str):
        allowed = [allowed]
    else:
        allowed = list(allowed)

    return Sample(
        id=scenario_id,
        input=question,
        target=record["answer"],
        metadata={
            "scenario_id": scenario_id,
            "tag": record.get("tag", "multiple-answer"),
            "allowed_tools": allowed,
        },
    )


def load_dataset(full: bool = False, *, faithful: bool = False) -> list[Sample]:
    """Load labeled scenarios from the local data directory."""
    data_file = SANDBOX_DIR / "data" / "Track A" / "data" / "Phase_1" / "train.json"

    with open(data_file, encoding="utf-8") as f:
        raw = json.load(f)

    all_samples = [record_to_sample(r, faithful=faithful) for r in raw]

    if full:
        return all_samples
    return all_samples[:LITE_SIZE]
