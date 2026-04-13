# Telco Challenge: Implementation History

## Origin

The [Telco-Troubleshooting-Agentic-Challenge](https://huggingface.co/datasets/netop/Telco-Troubleshooting-Agentic-Challenge) (TTAC) is a Huawei-published benchmark for evaluating AI agents on 5G network troubleshooting. The competition requires fine-tuning Qwen3.5-35B-A3B on labeled training data; our port evaluates off-the-shelf models before any fine-tuning.

The benchmark has two tracks:
- **Track A (Wireless):** 5G drive-test troubleshooting with 20 diagnostic tools
- **Track B (IP Net):** CLI-based network diagnostics (separate module, not covered here)

We ported Track A into the [Inspect AI](https://inspect.aisi.org.uk/) evaluation framework.

## Architecture

The port wraps the original Huawei FastAPI server in a Docker sandbox, accessed by Inspect AI tools via curl.

```
Inspect AI Task
  |
  +-- prepare_scenario() solver
  |     Sets scenario_id in store, injects system prompt
  |
  +-- react() agent (ReAct loop)
  |     20 @tool functions -> curl -> Docker sandbox -> FastAPI server
  |     on_continue: enforce_tool_budget (cap at 10 tool calls)
  |
  +-- official_scorer()
        Extracts \boxed{} answer, computes IoU score
```

**Key files:**
- `track_a/config.py` -- prompts, budgets, constants
- `track_a/samples.py` -- HF dataset to Inspect Sample conversion
- `track_a/tools.py` -- 20 tool definitions wrapping server endpoints
- `track_a/scorer.py` -- IoU scorer + 8 metrics
- `track_a/task.py` -- task wiring, ToolSource, budget guard

**Sandbox:**
- `data/sandboxes/ttac_wireless/` -- Docker compose, FastAPI server, Pydantic models
- Two-service model: `default` (curlimages/curl) + `server` (FastAPI on port 7860)
- Per-sample isolation via `X-Scenario-Id` header

## Timeline

### April 12, 2026: Initial port

Created `feat/ttac-migration` branch. Built the full pipeline in one session:

1. **Sandbox infrastructure** -- Dockerfile, compose.yaml, FastAPI server copied from upstream, Pydantic data models (`_types.py`), utility functions (`utils.py`), data download script (`setup_data.py`).

2. **Config and samples** -- `LITE_SIZE=200` for quick iteration, `record_to_sample()` converting HF JSON records to Inspect `Sample` objects, `load_dataset()` with full/lite toggle.

3. **20 tools** -- 1:1 match with upstream server endpoints. Each tool is an `@tool` function that calls `_get()` which runs `curl` inside the Docker sandbox. Tool names and parameter signatures match the original exactly.

4. **Scorer and task** -- Initial IoU scorer (strict set matching), `@task` function wiring solver chain and sandbox.

5. **Registration** -- Added `ttac_wireless` to `_registry.py`.

First smoke tests revealed Docker sandbox connectivity issues; the server wasn't serving data due to a hardcoded path prefix in `utils.py`.

### April 13, 2026: Track A redesign (9 commits)

The initial port had three problems:
- Scorer used strict IoU requiring exact match; the upstream uses a different (buggy) any() semantics
- The `tag` field (single-answer vs multiple-answer) was ignored; agent received no guidance on expected answer cardinality
- Per-sample `context` and `allowed_tools` fields were ignored

**Phase 1: Metadata and context**
- Extended `record_to_sample()` to carry `tag`, `allowed_tools`, and `scenario_id` in sample metadata
- Added context preamble (scenario description + wireless network info) to agent input
- Split system prompt into `SYSTEM_PROMPT_SINGLE` and `SYSTEM_PROMPT_MULTIPLE` variants
- Ported `official_score` with last-box extraction and lenient any() semantics

**Phase 2: Metrics and filtering**
- Added 6 custom `@metric` functions: `strict_accuracy`, `no_answer_rate`, `mean_tool_calls`, `mean_options_selected`, `accuracy_single`, `accuracy_multiple`
- Added `filter_allowed()` helper for future per-scenario tool restriction
- Added `build_score_metadata()` for rich per-sample telemetry

**Phase 3: Bug fixes from smoke testing**
- Tools weren't reaching the agent; fixed by passing `all_tools()` directly to `react()`
- Added budget-aware guidance to system prompts ("use at most N tool calls")
- Disabled react's default prompts and submit tool (they conflicted with custom system prompts)
- Switched sandbox to `curlimages/curl` base image and fixed URL query parameter encoding

### April 13, 2026: Red-team audit and 7 fixes

Conducted upstream audit comparing our port against the original Huawei harness (`main.py`, `utils.py`) and the dataset README.

**Findings:**
1. The upstream `compute_score` has a **swapped-argument bug** in `main.py`; our port's lenient any() extension was more correct but still wrong vs the README spec (IoU)
2. The upstream harness uses **no system prompt**; our port injects one
3. The upstream does **not include context preamble** in the agent prompt
4. `extract_codes` regex didn't handle nested braces
5. `filter_allowed` was built but never wired
6. `curl -s` swallowed HTTP errors silently
7. Server fell back to a random scenario when `X-Scenario-Id` was missing

**Fixes implemented (parallel team of 3 agents):**
- **Scorer agent:** Replaced bool scorer with IoU float scorer, fixed regex for nested braces, NaN for empty metric subsets
- **Task-config agent:** Added `faithful` mode to skip system prompt and context preamble, wired `filter_allowed` via `ScenarioToolSource` (Inspect `ToolSource` protocol)
- **Transport agent:** Added `curl -sSf` for HTTP error detection, removed random scenario fallback with explicit HTTP 400

All 45 tests pass after fixes.

### April 13, 2026: Model evaluation runs

Ran 30-sample evaluations across three model tiers. Results showed clear capability scaling (Sonnet 4.6 > Gemini Flash Lite > Haiku 3.5), validating that the benchmark produces meaningful signal. See `REPORT.md` for full results.

## Scoring

### IoU (Intersection over Union)

For multi-answer questions, the score is `|predicted intersection gt| / |predicted union gt|`:
- Predicted `{C3}` vs GT `{C3, C5}` = 1/2 = 0.5
- Predicted `{C3, C5}` vs GT `{C3, C5}` = 2/2 = 1.0
- Predicted `{C3, C99}` vs GT `{C3, C5}` = 1/3 = 0.33

For single-answer questions, IoU reduces to exact match (1.0 or 0.0).

A sample scores `CORRECT` if IoU > 0 (lenient; any overlap counts). `strict_accuracy` tracks IoU == 1.0 (exact set match).

### Why not the upstream scorer?

The upstream `compute_score` in `main.py` is called with **swapped arguments** (`compute_score(prediction, ground_truth)` when the signature is `(gt, answer)`). This causes multi-answer predictions to always score 0. The README specifies IoU; we implement what the README says.

## Divergences from Upstream

| Aspect | Upstream | Our port (default) | Our port (faithful=true) |
|--------|----------|-------------------|--------------------------|
| System prompt | None | Budget + format guidance | None |
| Context preamble | Not included | Included | Not included |
| Tool call limit | 10 iterations | 10 individual calls | 10 individual calls |
| Scorer | Buggy any() | IoU | IoU |
| Answer extraction | Last \boxed{} | Last \boxed{} | Last \boxed{} |
| Tools exposed | 20 | 20 | 20 |

## Testing

45 unit tests across two test files:

- `test_scorer.py` (28 tests): extract_codes (8), official_score IoU (8), build_score_metadata (4), custom metrics (8)
- `test_samples.py` (17 tests): record_to_sample (12), filter_allowed (5)

```bash
uv run pytest src/tests/telco_challenge/ -v
```

## Dataset Notes

- **Phase 1 train.json:** 2000 scenarios with ground truth. Intended for SFT/RL fine-tuning.
- **Phase 1 test.json:** 500 scenarios with `answer: "To be determined"`. No public labels.
- **Phases 2-3:** Not publicly released.
- All training scenarios have `allowed_tools: "all"` (tool restriction may appear in later phases).
- Multi-answer GT cardinalities: exactly 2 or 4 codes (never 3). All in ascending order.
