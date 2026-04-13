# TTAC Track A Scorer & Prompt Redesign — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the strict-IoU scorer with a faithful port of the official `compute_score` (`any()` over `|`-alternatives), add Inspect `@metric` telemetry, branch the system prompt on the dataset's `tag` field, prepend scenario `context` to the agent's input, and defensively filter tools by per-sample `allowed_tools`.

**Architecture:** One Inspect `Task`, no new files outside tests. All work stays inside `src/evals/ttac_wireless/` plus the two existing test files under `src/tests/ttac_wireless/`. Agent loop remains `react` with `message_limit=30`. A new `prepare_scenario` solver runs before `react` to set the per-sample system prompt, filter tools by `allowed_tools`, and push scenario metadata into `store()`.

**Tech Stack:** Python 3.10+, Inspect AI (`react`, `@solver`, `@scorer`, `@metric`, `use_tools`, `store`), pytest, uv, Docker compose sandbox.

**Source design:** `docs/plans/2026-04-13-ttac-track-a-design.md` (commit `4d5fd66`).

---

## Conventions used in every task

- Tests live at `src/tests/ttac_wireless/test_scorer.py` and `src/tests/ttac_wireless/test_samples.py` (both already exist — extend, do not recreate).
- Run tests with: `uv run pytest src/tests/ttac_wireless/ -v`.
- Run a single test with: `uv run pytest src/tests/ttac_wireless/test_scorer.py::test_name -v`.
- Pre-commit requires `uv run --with pre-commit git commit ...` (pre-commit is not on PATH).
- Follow TDD: write the failing test first, confirm it fails for the right reason, then make it pass. Commit after each green task.
- Do not run the full inspect eval in any task except Task 8 (smoke). It needs Docker + an API key.

---

## Task 1: Carry `tag` and `allowed_tools` through to sample metadata

**Files:**
- Modify: `src/evals/ttac_wireless/samples.py`
- Test: `src/tests/ttac_wireless/test_samples.py`

**Step 1: Extend `MOCK_RECORD` and add failing tests**

Open `src/tests/ttac_wireless/test_samples.py` and replace the existing `MOCK_RECORD` with the richer fixture below, then add the new tests. Keep the existing four tests unchanged.

```python
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


def test_record_to_sample_metadata_carries_tag():
    sample = record_to_sample(MOCK_RECORD)
    assert sample.metadata["tag"] == "multiple-answer"


def test_record_to_sample_metadata_carries_allowed_tools():
    sample = record_to_sample(MOCK_RECORD)
    assert sample.metadata["allowed_tools"] == ["all"]


def test_record_to_sample_metadata_defaults_allowed_tools_when_missing():
    record = {**MOCK_RECORD, "task": {**MOCK_RECORD["task"]}}
    del record["task"]["allowed_tools"]
    sample = record_to_sample(record)
    assert sample.metadata["allowed_tools"] == ["all"]
```

Also update the existing `test_record_to_sample_input_has_options` to keep passing with the new `MOCK_RECORD`; it should still work as-is.

**Step 2: Run failing tests**

Run: `uv run pytest src/tests/ttac_wireless/test_samples.py -v`
Expected: the three new tests fail with `KeyError` or assertion failures; the existing four pass.

**Step 3: Implement in `samples.py`**

Replace the body of `record_to_sample` with:

```python
def record_to_sample(record: dict) -> Sample:
    """Convert one scenario record into an Inspect Sample."""
    scenario_id = record["scenario_id"]
    task = record["task"]

    description = task["description"]
    options = task["options"]
    options_text = "\n".join(f"{opt['id']}: {opt['label']}" for opt in options)
    question = f"{description}\n\nOptions:\n{options_text}"

    allowed = task.get("allowed_tools", ["all"])
    # Dataset sometimes stores this as the literal string "all"; normalise.
    if isinstance(allowed, str):
        allowed = [allowed]

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
```

**Step 4: Run tests to confirm green**

Run: `uv run pytest src/tests/ttac_wireless/test_samples.py -v`
Expected: all seven tests pass.

**Step 5: Commit**

```bash
git add src/evals/ttac_wireless/samples.py src/tests/ttac_wireless/test_samples.py
uv run --with pre-commit git commit -m "feat(ttac_wireless): carry tag and allowed_tools into sample metadata"
```

---

## Task 2: Prepend scenario context to the agent's input

**Files:**
- Modify: `src/evals/ttac_wireless/samples.py`
- Test: `src/tests/ttac_wireless/test_samples.py`

**Step 1: Add failing test**

Append to `src/tests/ttac_wireless/test_samples.py`:

```python
def test_record_to_sample_input_has_context_preamble():
    sample = record_to_sample(MOCK_RECORD)
    assert "drive testing across 5 BSs" in sample.input
    assert "network_type=5G" in sample.input
    assert "num_base_stations=5" in sample.input
    assert "mobility_scenario=vehicle-based drive test" in sample.input


def test_record_to_sample_input_without_context_still_builds():
    record = {k: v for k, v in MOCK_RECORD.items() if k != "context"}
    sample = record_to_sample(record)
    assert "Diagnose the throughput issue." in sample.input
    assert "C1: Weak coverage" in sample.input
```

**Step 2: Run failing tests**

Run: `uv run pytest src/tests/ttac_wireless/test_samples.py -v`
Expected: the two new tests fail; others still pass.

**Step 3: Implement preamble builder**

Add a helper near the top of `samples.py`:

```python
def _build_context_preamble(context: dict | None) -> str:
    if not context:
        return ""
    parts = [context.get("description", "").strip()]
    wni = context.get("wireless_network_information") or {}
    if wni:
        fields = "; ".join(f"{k}={v}" for k, v in wni.items())
        parts.append(f"Network: {fields}")
    return "\n".join(p for p in parts if p)
```

Then modify `record_to_sample` so `question` becomes:

```python
    preamble = _build_context_preamble(record.get("context"))
    question = f"{preamble}\n\n{description}\n\nOptions:\n{options_text}" if preamble else f"{description}\n\nOptions:\n{options_text}"
```

**Step 4: Run tests to confirm green**

Run: `uv run pytest src/tests/ttac_wireless/test_samples.py -v`
Expected: all tests pass.

**Step 5: Commit**

```bash
git add src/evals/ttac_wireless/samples.py src/tests/ttac_wireless/test_samples.py
uv run --with pre-commit git commit -m "feat(ttac_wireless): prepend scenario context to agent input"
```

---

## Task 3: Split system prompt by answer tag

**Files:**
- Modify: `src/evals/ttac_wireless/config.py`

No tests for this task — it's pure string configuration consumed by later tasks.

**Step 1: Edit `config.py`**

Replace the existing `SYSTEM_PROMPT` block with:

```python
# --- Agent ---
MESSAGE_LIMIT = 30

SYSTEM_PROMPT_SINGLE = (
    "You are a 5G wireless network troubleshooting expert. "
    "Use the available tools to diagnose the root cause of degraded user throughput. "
    "Choose exactly one option. Output your final answer as \\boxed{Cn}."
)

SYSTEM_PROMPT_MULTIPLE = (
    "You are a 5G wireless network troubleshooting expert. "
    "Use the available tools to diagnose the root cause of degraded user throughput. "
    "Choose two to four options. Output your final answer as \\boxed{Ca|Cb|Cc}."
)
```

Leave `SERVER_HOST`, `SERVER_PORT`, `SANDBOX_DIR`, `COMPOSE_FILE`, `LITE_SIZE`, `ANSWER_PATTERN`, `ANSWER_SEPARATOR`, `DATASET_REPO`, `TRAIN_SPLIT` untouched.

**Step 2: Verify no importer broke**

Run: `uv run pytest src/tests/ttac_wireless/ -v`
Expected: pass. If any test fails with `ImportError: cannot import name 'SYSTEM_PROMPT'`, look at the failing file — it should not be referencing the old name (scorer/samples tests don't). Fix imports if needed, but nothing currently imports it.

Also run: `uv run python -c "from evals.ttac_wireless.task import ttac_wireless"`
Expected: fails with ImportError referencing `SYSTEM_PROMPT` (that's fine; Task 7 rewires it).

**Step 3: Commit**

```bash
git add src/evals/ttac_wireless/config.py
uv run --with pre-commit git commit -m "feat(ttac_wireless): split system prompt into single- and multiple-answer variants"
```

---

## Task 4: Rewrite the scorer core — `extract_codes` and `official_score`

**Files:**
- Modify: `src/evals/ttac_wireless/scorer.py`
- Test: `src/tests/ttac_wireless/test_scorer.py`

The existing scorer's `compute_iou` is being removed. Its tests go with it. `extract_codes` stays but changes return type from `set[str] | None` to `list[str] | None` (order matters — "last box wins" is per-token in the dataset, but also lets us assert list structure).

**Step 1: Replace the test file contents**

Replace `src/tests/ttac_wireless/test_scorer.py` in full with:

```python
"""Tests for ttac_wireless scorer (official compute_score port)."""

from evals.ttac_wireless.scorer import extract_codes, official_score


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
    # Official semantics: any() over | alternatives.
    assert official_score(["C8"], "C2|C8|C11|C16") is True
    assert official_score(["C99"], "C2|C8|C11|C16") is False


def test_official_score_multi_pred_vs_single_gt_is_raw_compare():
    # Official compute_score compares the joined string when | is in the answer.
    assert official_score(["C3", "C5"], "C3|C5") is True
    assert official_score(["C3"], "C3|C5") is True  # any() side
    assert official_score(["C5", "C3"], "C3|C5") is False  # order-sensitive join vs exact gt


def test_official_score_empty_pred_is_false():
    assert official_score([], "C3") is False
```

**Step 2: Run failing tests**

Run: `uv run pytest src/tests/ttac_wireless/test_scorer.py -v`
Expected: all tests fail with `ImportError: cannot import name 'official_score'` (or similar), because the module still exports `compute_iou`.

**Step 3: Rewrite `scorer.py` core functions**

Replace the full contents of `src/evals/ttac_wireless/scorer.py` with the block below. Note: the scorer registration and metadata emission come in later tasks (5 and 6); this task only ships the pure functions and stubs a minimal `official_scorer` so the module stays importable.

```python
r"""TTAC Wireless scorer. Port of official compute_score with Inspect metrics."""

import re

from inspect_ai.scorer import (
    CORRECT,
    INCORRECT,
    Score,
    Target,
    accuracy,
    scorer,
    stderr,
)
from inspect_ai.solver import TaskState

from evals.ttac_wireless.config import ANSWER_PATTERN, ANSWER_SEPARATOR


def extract_codes(text: str) -> list[str] | None:
    r"""Return the codes inside the LAST \boxed{...} in `text`, or None.

    Mirrors official utils.extract_answer: the last match wins, whitespace is
    stripped, and pipe-separated tokens are returned in source order.
    """
    matches = re.findall(ANSWER_PATTERN, text)
    if not matches:
        return None
    raw = matches[-1].strip()
    codes = [c.strip() for c in raw.split(ANSWER_SEPARATOR) if c.strip()]
    return codes or None


def official_score(predicted: list[str], gt: str) -> bool:
    """Faithful port of the official compute_score (hard-match only).

    - If gt contains '|' it denotes alternatives; return any().
    - Otherwise compare case-insensitively.
    - Multi-code predictions are joined with '|' before comparison, matching
      the official asymmetry where answer is compared as a raw string.
    """
    if not predicted:
        return False
    if ANSWER_SEPARATOR in gt:
        return any(official_score(predicted, g) for g in gt.split(ANSWER_SEPARATOR))
    pred_str = ANSWER_SEPARATOR.join(predicted).strip().lower()
    return pred_str == gt.strip().lower()


@scorer(metrics=[accuracy(), stderr()])
def official_scorer():
    async def score(state: TaskState, target: Target) -> Score:
        predicted = extract_codes(state.output.completion)
        if predicted is None:
            return Score(value=INCORRECT, answer=r"no \boxed{} found")
        value = CORRECT if official_score(predicted, target.text) else INCORRECT
        return Score(
            value=value,
            answer=ANSWER_SEPARATOR.join(predicted),
        )

    return score
```

**Step 4: Run tests to confirm green**

Run: `uv run pytest src/tests/ttac_wireless/test_scorer.py -v`
Expected: all tests pass.

**Step 5: Commit**

```bash
git add src/evals/ttac_wireless/scorer.py src/tests/ttac_wireless/test_scorer.py
uv run --with pre-commit git commit -m "feat(ttac_wireless): port official compute_score with last-box extraction"
```

---

## Task 5: Add scorer metadata (`strict_match`, `no_answer`, `num_predicted`, `tag`, `tool_calls`, `predicted`, `expected`)

**Files:**
- Modify: `src/evals/ttac_wireless/scorer.py`
- Test: `src/tests/ttac_wireless/test_scorer.py`

We can unit-test the metadata by building a minimal fake `TaskState`. Inspect's `TaskState` is a Pydantic-like object; to keep the test hermetic, extract the metadata logic into a pure helper and test that helper directly.

**Step 1: Add failing tests**

Append to `src/tests/ttac_wireless/test_scorer.py`:

```python
from evals.ttac_wireless.scorer import build_score_metadata


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
```

**Step 2: Run failing tests**

Run: `uv run pytest src/tests/ttac_wireless/test_scorer.py -v`
Expected: four failures on `ImportError: cannot import name 'build_score_metadata'`.

**Step 3: Implement `build_score_metadata` and wire it**

Edit `src/evals/ttac_wireless/scorer.py`. Add this helper above `official_scorer`:

```python
def build_score_metadata(
    predicted: list[str] | None,
    gt: str,
    tag: str,
    tool_calls: int,
) -> dict:
    pred = predicted or []
    expected = sorted({c.strip() for c in gt.split(ANSWER_SEPARATOR) if c.strip()})
    return {
        "predicted": sorted(pred),
        "expected": expected,
        "tag": tag,
        "strict_match": sorted(pred) == expected,
        "no_answer": predicted is None,
        "num_predicted": len(pred),
        "tool_calls": tool_calls,
    }
```

Add a tool-call counter helper:

```python
def _count_tool_calls(state: TaskState) -> int:
    return sum(
        1
        for m in state.messages
        if getattr(m, "role", None) == "assistant"
        and getattr(m, "tool_calls", None)
        for _ in m.tool_calls
    )
```

Then update `official_scorer` to:

```python
@scorer(metrics=[accuracy(), stderr()])
def official_scorer():
    async def score(state: TaskState, target: Target) -> Score:
        predicted = extract_codes(state.output.completion)
        tag = state.metadata.get("tag", "multiple-answer")
        tool_calls = _count_tool_calls(state)
        metadata = build_score_metadata(predicted, target.text, tag, tool_calls)

        if predicted is None:
            return Score(value=INCORRECT, answer=r"no \boxed{} found", metadata=metadata)

        value = CORRECT if official_score(predicted, target.text) else INCORRECT
        return Score(
            value=value,
            answer=ANSWER_SEPARATOR.join(predicted),
            metadata=metadata,
        )

    return score
```

**Step 4: Run tests to confirm green**

Run: `uv run pytest src/tests/ttac_wireless/test_scorer.py -v`
Expected: all 14 tests pass.

**Step 5: Commit**

```bash
git add src/evals/ttac_wireless/scorer.py src/tests/ttac_wireless/test_scorer.py
uv run --with pre-commit git commit -m "feat(ttac_wireless): emit rich per-sample metadata from scorer"
```

---

## Task 6: Add Inspect `@metric`s for telemetry

**Files:**
- Modify: `src/evals/ttac_wireless/scorer.py`
- Test: `src/tests/ttac_wireless/test_scorer.py`

Six metrics: `strict_accuracy`, `no_answer_rate`, `mean_tool_calls`, `mean_options_selected`, `accuracy_single`, `accuracy_multiple`.

They all operate on the list of `SampleScore` passed by Inspect. A `SampleScore` has `.score.value` (a string `CORRECT`/`INCORRECT`, which Inspect maps to 1/0 via `.score.as_float()`) and `.score.metadata`. Pure-function metrics are easy to unit-test.

**Step 1: Write failing tests**

Append to `src/tests/ttac_wireless/test_scorer.py`:

```python
from inspect_ai.scorer import CORRECT, INCORRECT, SampleScore, Score

from evals.ttac_wireless.scorer import (
    accuracy_multiple,
    accuracy_single,
    mean_options_selected,
    mean_tool_calls,
    no_answer_rate,
    strict_accuracy,
)


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
        _make(CORRECT, tag="multiple-answer"),  # ignored
    ]
    assert accuracy_single()(scores) == 0.5


def test_accuracy_multiple_filters_by_tag():
    scores = [
        _make(CORRECT, tag="multiple-answer"),
        _make(CORRECT, tag="multiple-answer"),
        _make(INCORRECT, tag="single-answer"),  # ignored
    ]
    assert accuracy_multiple()(scores) == 1.0


def test_accuracy_single_returns_zero_when_no_samples_match():
    scores = [_make(CORRECT, tag="multiple-answer")]
    assert accuracy_single()(scores) == 0.0
```

**Step 2: Run failing tests**

Run: `uv run pytest src/tests/ttac_wireless/test_scorer.py -v`
Expected: the seven new tests fail on ImportError.

**Step 3: Implement metrics**

Add near the top of `scorer.py` (alongside other imports):

```python
from inspect_ai.scorer import Metric, SampleScore, metric
```

Then add these functions above `official_scorer`:

```python
def _values(scores: list[SampleScore]) -> list[float]:
    return [s.score.as_float() for s in scores]


@metric
def strict_accuracy() -> Metric:
    def compute(scores: list[SampleScore]) -> float:
        flags = [bool(s.score.metadata.get("strict_match")) for s in scores]
        return sum(flags) / len(flags) if flags else 0.0
    return compute


@metric
def no_answer_rate() -> Metric:
    def compute(scores: list[SampleScore]) -> float:
        flags = [bool(s.score.metadata.get("no_answer")) for s in scores]
        return sum(flags) / len(flags) if flags else 0.0
    return compute


@metric
def mean_tool_calls() -> Metric:
    def compute(scores: list[SampleScore]) -> float:
        values = [int(s.score.metadata.get("tool_calls", 0)) for s in scores]
        return sum(values) / len(values) if values else 0.0
    return compute


@metric
def mean_options_selected() -> Metric:
    def compute(scores: list[SampleScore]) -> float:
        values = [
            int(s.score.metadata.get("num_predicted", 0))
            for s in scores
            if not s.score.metadata.get("no_answer")
        ]
        return sum(values) / len(values) if values else 0.0
    return compute


def _accuracy_for_tag(tag_value: str):
    @metric
    def m() -> Metric:
        def compute(scores: list[SampleScore]) -> float:
            subset = [s for s in scores if s.score.metadata.get("tag") == tag_value]
            if not subset:
                return 0.0
            return sum(s.score.as_float() for s in subset) / len(subset)
        return compute
    return m


accuracy_single = _accuracy_for_tag("single-answer")
accuracy_multiple = _accuracy_for_tag("multiple-answer")
```

Update the `@scorer(metrics=[...])` line to register them:

```python
@scorer(
    metrics=[
        accuracy(),
        stderr(),
        strict_accuracy(),
        no_answer_rate(),
        mean_tool_calls(),
        mean_options_selected(),
        accuracy_single(),
        accuracy_multiple(),
    ]
)
def official_scorer():
    ...
```

**Step 4: Run tests to confirm green**

Run: `uv run pytest src/tests/ttac_wireless/test_scorer.py -v`
Expected: all 21 tests pass.

**Step 5: Commit**

```bash
git add src/evals/ttac_wireless/scorer.py src/tests/ttac_wireless/test_scorer.py
uv run --with pre-commit git commit -m "feat(ttac_wireless): expose strict/no-answer/tool-call/per-tag metrics"
```

---

## Task 7: Add `filter_allowed` to `tools.py` and wire the `prepare_scenario` solver

**Files:**
- Modify: `src/evals/ttac_wireless/tools.py`
- Modify: `src/evals/ttac_wireless/task.py`

`filter_allowed` is pure so we can unit-test it lightly — but tools are callable objects built by `@tool` decorators and the most robust check is by tool name. Inspect exposes each tool's name via `ToolDef(tool).name`; at runtime the bound wrapper carries `__name__` on the inner function. Easiest stable check: compare against the set of function names we own.

**Step 1: Add failing test to `test_samples.py`** (that file already imports from `evals.ttac_wireless`; keep tool tests next to samples to avoid a new test file).

Append to `src/tests/ttac_wireless/test_samples.py`:

```python
from evals.ttac_wireless.tools import all_tools, filter_allowed


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
```

**Step 2: Run failing tests**

Run: `uv run pytest src/tests/ttac_wireless/test_samples.py -v`
Expected: four failures on ImportError.

**Step 3: Implement `filter_allowed`**

At the bottom of `src/evals/ttac_wireless/tools.py` (after `all_tools`), add:

```python
_TOOL_BUILDERS = {
    "get_throughput_logs": get_throughput_logs,
    "get_cell_info": get_cell_info,
    "get_gnodeb_location": get_gnodeb_location,
    "get_user_location": get_user_location,
    "get_serving_cell_pci": get_serving_cell_pci,
    "get_serving_cell_rsrp": get_serving_cell_rsrp,
    "get_serving_cell_sinr": get_serving_cell_sinr,
    "get_rbs_allocated_to_user": get_rbs_allocated_to_user,
    "get_signaling_plane_event_log": get_signaling_plane_event_log,
    "get_neighboring_cells_pci": get_neighboring_cells_pci,
    "get_neighboring_cell_rsrp": get_neighboring_cell_rsrp,
    "get_all_cells_pci": get_all_cells_pci,
    "get_kpi_data": get_kpi_data,
    "get_mr_data": get_mr_data,
    "judge_mainlobe_or_not": judge_mainlobe_or_not,
    "calculate_horizontal_angle": calculate_horizontal_angle,
    "calculate_tilt_angle": calculate_tilt_angle,
    "calculate_pathloss": calculate_pathloss,
    "calculate_overlap_ratio": calculate_overlap_ratio,
    "optimize_antenna_gain": optimize_antenna_gain,
}


def filter_allowed(names: list[str]) -> list:
    """Return instantiated tools filtered by name.

    `["all"]` returns every tool. Unknown names are dropped silently.
    """
    if names == ["all"]:
        return all_tools()
    return [_TOOL_BUILDERS[n]() for n in names if n in _TOOL_BUILDERS]
```

**Step 4: Run tool tests**

Run: `uv run pytest src/tests/ttac_wireless/test_samples.py -v`
Expected: all sample tests plus four new tool tests pass.

**Step 5: Rewrite `task.py` with `prepare_scenario`**

Replace the full contents of `src/evals/ttac_wireless/task.py` with:

```python
"""TTAC Wireless: 5G drive-test troubleshooting evaluation."""

from inspect_ai import Task, task
from inspect_ai.agent import react
from inspect_ai.model import ChatMessageSystem
from inspect_ai.solver import Solver, TaskState, solver, use_tools
from inspect_ai.util import store

from evals.ttac_wireless.config import (
    COMPOSE_FILE,
    MESSAGE_LIMIT,
    SYSTEM_PROMPT_MULTIPLE,
    SYSTEM_PROMPT_SINGLE,
)
from evals.ttac_wireless.samples import load_dataset
from evals.ttac_wireless.scorer import official_scorer
from evals.ttac_wireless.tools import all_tools, filter_allowed


@solver
def prepare_scenario() -> Solver:
    """Set scenario_id + tag in store, inject tag-specific system prompt, filter tools."""

    async def solve(state: TaskState, generate):
        tag = state.metadata.get("tag", "multiple-answer")
        allowed = state.metadata.get("allowed_tools", ["all"])

        store().set("scenario_id", state.metadata["scenario_id"])
        store().set("tag", tag)

        prompt = SYSTEM_PROMPT_SINGLE if tag == "single-answer" else SYSTEM_PROMPT_MULTIPLE
        state.messages = [ChatMessageSystem(content=prompt), *state.messages]

        state.tools = filter_allowed(allowed)
        return state

    return solve


@task
def ttac_wireless(full: bool = False) -> Task:
    """5G wireless network troubleshooting benchmark (TTAC Track A)."""
    dataset = load_dataset(full)

    return Task(
        dataset=dataset,
        solver=[
            prepare_scenario(),
            use_tools(*all_tools()),
            react(),
        ],
        scorer=official_scorer(),
        sandbox=("docker", COMPOSE_FILE),
        message_limit=MESSAGE_LIMIT,
    )
```

Notes on the solver chain:
- `prepare_scenario` pushes a `ChatMessageSystem` in front of the existing user message and writes `state.tools`.
- `use_tools(*all_tools())` is a defensive default — it runs *after* `prepare_scenario` and would overwrite `state.tools` with the full set. That's wrong. Drop `use_tools` from the chain and rely on `prepare_scenario` setting `state.tools` directly; then let `react` use those.
- Re-check: Inspect's `react` agent reads tools from its constructor arg; when none given, it uses `state.tools`. Confirm by glancing at `react`'s signature earlier (its `tools` param defaults to `None`; when `None`, solver state tools flow through). Therefore the final solver chain should be `[prepare_scenario(), react()]` and `use_tools` is not needed.

Fix the Task to:

```python
    return Task(
        dataset=dataset,
        solver=[prepare_scenario(), react()],
        scorer=official_scorer(),
        sandbox=("docker", COMPOSE_FILE),
        message_limit=MESSAGE_LIMIT,
    )
```

**Step 6: Verify the module imports cleanly**

Run: `uv run python -c "from evals.ttac_wireless.task import ttac_wireless; t = ttac_wireless(); print(type(t).__name__)"`
Expected: prints `Task` (or whatever Inspect's Task class repr is) with no ImportError.

Run: `uv run pytest src/tests/ttac_wireless/ -v`
Expected: all tests pass.

**Step 7: Commit**

```bash
git add src/evals/ttac_wireless/tools.py src/evals/ttac_wireless/task.py src/tests/ttac_wireless/test_samples.py
uv run --with pre-commit git commit -m "feat(ttac_wireless): route prompt by tag and filter tools by allowed_tools"
```

---

## Task 8: Smoke run (manual verification)

**Files:** none edited.

**Step 1: Ensure Docker is running**

Run: `docker info` and confirm it reports a daemon.

**Step 2: Run a 3-sample eval with a cheap model**

Run: `uv run inspect eval src/evals/ttac_wireless/task.py --limit 3 --model openrouter/openai/gpt-4o-mini`

Expected:
- Sandbox starts; server healthchecks pass (we previously extended `start_period`).
- Each sample produces a tool-call trace.
- The eval summary at the end shows all eight metrics: `accuracy`, `stderr`, `strict_accuracy`, `no_answer_rate`, `mean_tool_calls`, `mean_options_selected`, `accuracy_single`, `accuracy_multiple`.
- No crashes.

**Step 3: Inspect the logs**

Open the generated `.eval` log in the Inspect viewer or `jq` the JSON. Sanity-check:
- Each sample has `metadata.tag`, `metadata.predicted`, `metadata.expected`, `metadata.tool_calls > 0`.
- `strict_match` is `true` only when predicted set equals expected set.
- For a sample whose ground truth contains `|`, confirm that a single-code prediction matching one alternative shows `value=CORRECT` and `strict_match=False` (the point of the redesign).

**Step 4: No commit (this task is verification only)**

If any of the above fails, file a fix as a follow-up task — do not paper over failures.

---

## Task 9: Update session memory

**Files:** none edited (memory lives outside the repo).

Save a new memory entry via your memory tool pointing at the design doc and plan so future sessions can pick up the thread. Content: a one-line pointer to `docs/plans/2026-04-13-ttac-track-a-design.md` and a note that the scorer is now official `any()` semantics plus six Inspect metrics.

No commit.

---

## Out of scope (explicitly)

- Track B (`ttac_ipnet`). Same scorer shape likely applies but is a separate PR.
- Soft/numeric match mode. Not needed for Track A.
- Bumping `MESSAGE_LIMIT`. Stay at 30.
- Custom agent loops (planning phase, scratchpad, `store()`-backed diagnosis memory). Flagged for a later iteration if the smoke run shows models running out of turns.
- Running the full 2000-sample split in CI.

## Summary of files touched

```
src/evals/ttac_wireless/samples.py       # Task 1, Task 2
src/evals/ttac_wireless/config.py        # Task 3
src/evals/ttac_wireless/scorer.py        # Task 4, Task 5, Task 6
src/evals/ttac_wireless/tools.py         # Task 7
src/evals/ttac_wireless/task.py          # Task 7
src/tests/ttac_wireless/test_samples.py  # Task 1, Task 2, Task 7
src/tests/ttac_wireless/test_scorer.py   # Task 4, Task 5, Task 6
```

Expected commit count: 6 (Tasks 1, 2, 3, 4, 5, 6, 7 each produce one; Task 8 is verification-only; Task 9 is memory-only). That's 7 commits — one per task with code changes.
