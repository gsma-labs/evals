"""TTAC IP Network sample loading. Dict in, Sample out."""

from __future__ import annotations

import json

from inspect_ai.dataset import Sample

from evals.ttac_ipnet.config import SANDBOX_DIR


def record_to_sample(record: dict) -> Sample:
    """Convert one test.json record into an Inspect Sample."""
    scenario_id = record["scenario_id"]
    task = record["task"]

    question = task["question"]
    question_number = task["id"]

    return Sample(
        id=scenario_id,
        input=question,
        target="",
        metadata={
            "question_number": question_number,
            "scenario_id": scenario_id,
        },
    )


def load_dataset() -> list[Sample]:
    """Load IP network troubleshooting questions from local data."""
    data_file = SANDBOX_DIR / "data" / "Track B" / "data" / "Phase_1" / "test.json"

    with open(data_file, encoding="utf-8") as f:
        raw = json.load(f)

    return [record_to_sample(r) for r in raw]
