"""Tests for ttac_wireless scorer (official compute_score port)."""

from inspect_ai.scorer import CORRECT, INCORRECT, SampleScore, Score

from evals.ttac_wireless.scorer import (
    accuracy_multiple,
    accuracy_single,
    build_score_metadata,
    extract_codes,
    mean_options_selected,
    mean_tool_calls,
    no_answer_rate,
    official_score,
    strict_accuracy,
)

# --- extract_codes ---


def test_extract_codes_single():
    assert extract_codes(r"The answer is \boxed{C3}") == ["C3"]


def test_extract_codes_pipe_separated():
    assert extract_codes(r"\boxed{C3|C5|C8}") == ["C3", "C5", "C8"]


def test_extract_codes_last_box_wins():
    text = r"First try \boxed{C1}, actually \boxed{C7}."
    assert extract_codes(text) == ["C7"]


def test_extract_codes_no_box_returns_none():
    assert extract_codes("No boxed answer here.") is None


def test_extract_codes_empty_box_returns_none():
    assert extract_codes(r"\boxed{}") is None


def test_extract_codes_whitespace_in_codes():
    assert extract_codes(r"\boxed{ C3 | C5 }") == ["C3", "C5"]


# --- official_score ---


def test_official_score_single_match_case_insensitive():
    assert official_score(["c3"], "C3") is True


def test_official_score_single_miss():
    assert official_score(["C3"], "C5") is False


def test_official_score_multi_gt_matches_any_single():
    assert official_score(["C8"], "C2|C8|C11|C16") is True
    assert official_score(["C99"], "C2|C8|C11|C16") is False


def test_official_score_multi_pred_vs_single_gt_is_raw_compare():
    assert official_score(["C3", "C5"], "C3|C5") is True
    assert official_score(["C3"], "C3|C5") is True
    assert official_score(["C5", "C3"], "C3|C5") is False


def test_official_score_empty_pred_is_false():
    assert official_score([], "C3") is False


# --- build_score_metadata ---


def test_metadata_strict_match_true_when_sets_equal():
    meta = build_score_metadata(
        predicted=["C3", "C5"], gt="C3|C5", tag="multiple-answer", tool_calls=4
    )
    assert meta["strict_match"] is True


def test_metadata_strict_match_false_when_missing_code():
    meta = build_score_metadata(
        predicted=["C3"], gt="C3|C5", tag="multiple-answer", tool_calls=4
    )
    assert meta["strict_match"] is False


def test_metadata_no_answer_flag():
    meta = build_score_metadata(
        predicted=None, gt="C3", tag="single-answer", tool_calls=0
    )
    assert meta["no_answer"] is True
    assert meta["num_predicted"] == 0
    assert meta["predicted"] == []


def test_metadata_num_predicted_and_sorted_lists():
    meta = build_score_metadata(
        predicted=["C5", "C3"], gt="C3|C5", tag="multiple-answer", tool_calls=7
    )
    assert meta["num_predicted"] == 2
    assert meta["predicted"] == ["C3", "C5"]
    assert meta["expected"] == ["C3", "C5"]
    assert meta["tool_calls"] == 7
    assert meta["tag"] == "multiple-answer"


# --- custom metrics ---


def _make(value, **meta) -> SampleScore:
    return SampleScore(sample_id="s", score=Score(value=value, metadata=meta))


def test_strict_accuracy_counts_strict_match_flag():
    scores = [
        _make(CORRECT, strict_match=True),
        _make(CORRECT, strict_match=False),
        _make(INCORRECT, strict_match=False),
    ]
    assert strict_accuracy()(scores) == 1 / 3


def test_no_answer_rate():
    scores = [
        _make(INCORRECT, no_answer=True),
        _make(CORRECT, no_answer=False),
        _make(INCORRECT, no_answer=False),
    ]
    assert no_answer_rate()(scores) == 1 / 3


def test_mean_tool_calls():
    scores = [_make(CORRECT, tool_calls=2), _make(INCORRECT, tool_calls=8)]
    assert mean_tool_calls()(scores) == 5.0


def test_mean_options_selected_skips_no_answer():
    scores = [
        _make(CORRECT, num_predicted=1, no_answer=False),
        _make(CORRECT, num_predicted=3, no_answer=False),
        _make(INCORRECT, num_predicted=0, no_answer=True),
    ]
    assert mean_options_selected()(scores) == 2.0


def test_accuracy_single_filters_by_tag():
    scores = [
        _make(CORRECT, tag="single-answer"),
        _make(INCORRECT, tag="single-answer"),
        _make(CORRECT, tag="multiple-answer"),
    ]
    assert accuracy_single()(scores) == 0.5


def test_accuracy_multiple_filters_by_tag():
    scores = [
        _make(CORRECT, tag="multiple-answer"),
        _make(CORRECT, tag="multiple-answer"),
        _make(INCORRECT, tag="single-answer"),
    ]
    assert accuracy_multiple()(scores) == 1.0


def test_accuracy_single_returns_zero_when_no_samples_match():
    scores = [_make(CORRECT, tag="multiple-answer")]
    assert accuracy_single()(scores) == 0.0
