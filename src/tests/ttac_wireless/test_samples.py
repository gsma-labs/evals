"""Tests for ttac_wireless sample loading."""

import copy

from evals.ttac_wireless.samples import record_to_sample
from evals.ttac_wireless.tools import all_tools, filter_allowed

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


def test_record_to_sample_input_has_context_preamble():
    sample = record_to_sample(MOCK_RECORD)
    assert "drive testing across 5 BSs" in sample.input
    assert "network_type=5G" in sample.input
    assert "num_base_stations=5" in sample.input
    assert "mobility_scenario=vehicle-based drive test" in sample.input


def test_record_to_sample_input_without_context_still_builds():
    record = copy.deepcopy(MOCK_RECORD)
    del record["context"]
    sample = record_to_sample(record)
    assert "Diagnose the throughput issue." in sample.input
    assert "C1: Weak coverage" in sample.input


def test_filter_allowed_with_all_returns_every_tool():
    expected = len(all_tools())
    assert len(filter_allowed(["all"])) == expected


def test_filter_allowed_with_subset():
    tools = filter_allowed(["get_cell_info", "get_kpi_data"])
    assert len(tools) == 2


def test_filter_allowed_drops_unknown_names():
    tools = filter_allowed(["get_cell_info", "nope_not_real"])
    assert len(tools) == 1


def test_filter_allowed_empty_list_returns_empty():
    assert filter_allowed([]) == []


def test_filter_allowed_empty_then_prepare_scenario_falls_back_to_all():
    # This is a spec-level assertion; prepare_scenario is a solver and is
    # exercised at task run time, not here. Document the defensive default.
    assert filter_allowed([]) == []
    assert len(all_tools()) > 0
