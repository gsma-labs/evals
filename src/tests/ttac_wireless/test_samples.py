"""Tests for ttac_wireless sample loading."""

from evals.ttac_wireless.samples import record_to_sample


MOCK_RECORD = {
    "scenario_id": "test-scenario-001",
    "answer": "C3|C5",
    "task": {
        "allowed_tools": "all",
        "description": "Diagnose the throughput issue.",
        "options": [
            {"id": "C1", "label": "Weak coverage"},
            {"id": "C3", "label": "Interference"},
            {"id": "C5", "label": "Handover failure"},
        ],
    },
}


def test_record_to_sample_id():
    sample = record_to_sample(MOCK_RECORD)
    assert sample.id == "test-scenario-001"


def test_record_to_sample_target():
    sample = record_to_sample(MOCK_RECORD)
    assert sample.target == "C3|C5"


def test_record_to_sample_input_has_options():
    sample = record_to_sample(MOCK_RECORD)
    assert "C1: Weak coverage" in sample.input
    assert "C3: Interference" in sample.input


def test_record_to_sample_metadata():
    sample = record_to_sample(MOCK_RECORD)
    assert sample.metadata["scenario_id"] == "test-scenario-001"
