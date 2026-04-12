"""Tests for ttac_ipnet sample loading."""

from evals.ttac_ipnet.samples import record_to_sample


MOCK_RECORD = {
    "scenario_id": "535afb0d-fa81-419b-9bcc-b456d032df5d",
    "task": {
        "question": "Restore the link connections of Gamma-Aegis-01.",
        "id": 1,
    },
}


def test_record_to_sample_id():
    sample = record_to_sample(MOCK_RECORD)
    assert sample.id == "535afb0d-fa81-419b-9bcc-b456d032df5d"


def test_record_to_sample_question_number():
    sample = record_to_sample(MOCK_RECORD)
    assert sample.metadata["question_number"] == 1


def test_record_to_sample_input():
    sample = record_to_sample(MOCK_RECORD)
    assert "Gamma-Aegis-01" in sample.input
