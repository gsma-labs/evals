"""Tests for ttac_wireless sample loading."""

import copy

from evals.ttac_wireless.samples import record_to_sample

MOCK_RECORD = {
    "scenario_id": "test-scenario-001",
    "tag": "multiple-answer",
    "answer": "C3|C5",
    "context": {
        "description": "A network engineer conducted drive testing across 5 BSs.",
        "wireless_network_information": {
            "network_type": "5G",
            "num_base_stations": "5",
            "mobility_scenario": "vehicle-based drive test",
        },
    },
    "task": {
        "allowed_tools": ["all"],
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


def test_record_to_sample_metadata_carries_tag():
    sample = record_to_sample(MOCK_RECORD)
    assert sample.metadata["tag"] == "multiple-answer"


def test_record_to_sample_metadata_carries_allowed_tools():
    sample = record_to_sample(MOCK_RECORD)
    assert sample.metadata["allowed_tools"] == ["all"]


def test_record_to_sample_metadata_defaults_allowed_tools_when_missing():
    record = copy.deepcopy(MOCK_RECORD)
    del record["task"]["allowed_tools"]
    sample = record_to_sample(record)
    assert sample.metadata["allowed_tools"] == ["all"]


def test_record_to_sample_normalises_string_allowed_tools_to_list():
    record = copy.deepcopy(MOCK_RECORD)
    record["task"]["allowed_tools"] = "all"
    sample = record_to_sample(record)
    assert sample.metadata["allowed_tools"] == ["all"]
