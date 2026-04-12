"""TTAC Wireless sample loading. Dict in, Sample out."""

from __future__ import annotations

import json

from inspect_ai.dataset import Sample

from evals.ttac_wireless.config import LITE_SIZE, SANDBOX_DIR


def record_to_sample(record: dict) -> Sample:
    """Convert one scenario record into an Inspect Sample."""
    scenario_id = record["scenario_id"]
    task = record["task"]

    description = task["description"]
    options = task["options"]
    options_text = "\n".join(f"{opt['id']}: {opt['label']}" for opt in options)
    question = f"{description}\n\nOptions:\n{options_text}"

    answer = record["answer"]

    return Sample(
        id=scenario_id,
        input=question,
        target=answer,
        metadata={"scenario_id": scenario_id},
    )


def load_dataset(full: bool = False) -> list[Sample]:
    """Load labeled scenarios from the local data directory."""
    data_file = SANDBOX_DIR / "data" / "Track A" / "data" / "Phase_1" / "train.json"

    with open(data_file, encoding="utf-8") as f:
        raw = json.load(f)

    all_samples = [record_to_sample(r) for r in raw]

    if full:
        return all_samples
    return all_samples[:LITE_SIZE]
