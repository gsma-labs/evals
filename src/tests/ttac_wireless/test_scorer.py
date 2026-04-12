"""Tests for ttac_wireless scorer."""

from evals.ttac_wireless.scorer import compute_iou, extract_codes


def test_extract_codes_single():
    assert extract_codes("The answer is \\boxed{C3}") == {"C3"}


def test_extract_codes_multiple():
    assert extract_codes("\\boxed{C3|C5|C8}") == {"C3", "C5", "C8"}


def test_extract_codes_no_match():
    assert extract_codes("No boxed answer here") is None


def test_iou_perfect():
    assert compute_iou({"C3", "C5"}, {"C3", "C5"}) == 1.0


def test_iou_partial():
    result = compute_iou({"C3", "C5", "C8"}, {"C3", "C5"})
    assert abs(result - 2 / 3) < 0.01


def test_iou_no_overlap():
    assert compute_iou({"C1"}, {"C2"}) == 0.0


def test_iou_empty():
    assert compute_iou(set(), set()) == 0.0
