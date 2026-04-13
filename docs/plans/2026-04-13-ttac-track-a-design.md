# TTAC Track A — Scorer & Prompt Redesign

Date: 2026-04-13
Scope: `src/evals/ttac_wireless/` (Track A only)
Status: Approved design; plan to be drafted by writing-plans skill.

## Motivation

Three problems surfaced during the first end-to-end runs of `ttac_wireless`:

1. Our `iou_scorer` requires the predicted code set to equal the expected set. The official `compute_score` in the competition's `utils.py` treats `|` in ground truth as **alternatives** (`any()`), not a multi-label set. A sample with gt `C2|C8|C11|C16` scores `1` officially if the agent returns any one of those; our scorer scores `0` unless it returns exactly all four.
2. The dataset already embeds the `\boxed{...}` format instruction inside each sample's `task.description`, but the agent was not being told whether a given scenario expects one code or multiple. The dataset's `tag` field (`single-answer` vs `multiple-answer`) carries that signal and was being ignored.
3. Per-sample `context` (scenario setup: network type, number of base stations, mobility) and `allowed_tools` fields were also being ignored.

`message_limit=30` stays. `react` stays. The Docker sandbox stays. Everything else below is contained to `src/evals/ttac_wireless/`.

## Dataset facts (Phase 1 train, 2000 samples)

- `tag`: 1701 `single-answer`, 299 `multiple-answer`.
- `answer` contains `|` iff `tag == "multiple-answer"` (299 samples).
- All option IDs look like `C<digits>`; no numeric-only answers, so hard-match only (no soft/numeric mode).
- `allowed_tools == ["all"]` for every Phase 1 sample today. Treated as future-proofing only.
- `context.description` + `context.wireless_network_information` carry scenario setup that is not currently shown to the agent.

## Architecture

One Inspect `Task`. No new modules. Changes land in the existing five files:

- `samples.py` — expand `record_to_sample`; carry `tag` and `allowed_tools` in metadata; prepend a context preamble to `input`.
- `config.py` — split the single `SYSTEM_PROMPT` into `SYSTEM_PROMPT_SINGLE` and `SYSTEM_PROMPT_MULTIPLE`; drop `ANSWER_SEPARATOR` if unused.
- `scorer.py` — replace strict-IoU logic with a faithful port of official `compute_score`; add `@metric` definitions.
- `tools.py` — add `filter_allowed(names)` helper; `all_tools()` unchanged.
- `task.py` — add `prepare_scenario` solver that runs before `react`; routes system prompt by `tag` and filters tools by `allowed_tools`.

The agent loop is `[prepare_scenario(), react(prompt=<set per sample>, tools=<filtered per sample>)]` with `message_limit=30` and the existing Docker sandbox.

## Components

### `samples.py`

`record_to_sample(record)`:

- Build a preamble string from `context.description` and the `wireless_network_information` dict (flattened as `"network_type=5G; num_base_stations=5; mobility_scenario=vehicle-based drive test"`).
- `input` becomes: preamble blank line task.description blank line `Options:` block.
- `target` stays `record["answer"]`.
- `metadata` carries: `scenario_id`, `tag`, `allowed_tools` (raw list from the record).

`load_dataset(full=False)` unchanged except it passes the expanded metadata through. Default cap stays `LITE_SIZE = 200`.

### `config.py`

```
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

Role framing only. The dataset's own `\boxed{}` instruction inside `task.description` remains authoritative.

### `task.py`

```
@solver
def prepare_scenario():
    async def solve(state, generate):
        tag = state.metadata.get("tag", "multiple-answer")
        allowed = state.metadata.get("allowed_tools", ["all"])
        store().set("scenario_id", state.metadata["scenario_id"])
        store().set("tag", tag)
        prompt = SYSTEM_PROMPT_SINGLE if tag == "single-answer" else SYSTEM_PROMPT_MULTIPLE
        state.tools = filter_allowed(allowed)
        state.messages = [ChatMessageSystem(content=prompt), *state.messages]
        return state
    return solve
```

Composition: `solver=[prepare_scenario(), react(tools=all_tools())]`. `react`'s own `prompt=` argument is left unset; the system message is injected by `prepare_scenario` so it can vary per sample. `react`'s `tools=` default is overridden on `state.tools` by the solver (fallback: if Inspect's `react` resolves tools at construction time, swap to `use_tools()` inside `prepare_scenario` and drop the `tools=` arg from `react`).

### `tools.py`

- `all_tools()` unchanged.
- `filter_allowed(names: list[str]) -> list[Tool]`:
  - if `names == ["all"]` return `all_tools()`.
  - else filter `all_tools()` by tool name equality; unknown names dropped silently.

### `scorer.py`

Port of official `compute_score` (hard-match only):

```
def extract_codes(text: str) -> list[str] | None:
    # Last \boxed{...} wins, per official extract_answer.
    matches = re.findall(ANSWER_PATTERN, text)
    if not matches:
        return None
    raw = matches[-1].strip().strip("{}")
    return [c.strip() for c in raw.split("|") if c.strip()]

def official_score(predicted: list[str], gt: str) -> bool:
    if "|" in gt:
        return any(official_score(predicted, g) for g in gt.split("|"))
    pred_str = "|".join(predicted).lower()
    return pred_str == gt.strip().lower()
```

Scorer emits for each sample:

- `value` = `CORRECT` if `official_score(...)` else `INCORRECT`.
- `answer` = the joined predicted codes (for readability in Inspect UI).
- `metadata`:
  - `predicted`: sorted list.
  - `expected`: sorted list (split on `|`).
  - `tag`: from state metadata.
  - `strict_match`: `set(predicted) == set(expected)`.
  - `no_answer`: `predicted is None`.
  - `num_predicted`: `len(predicted or [])`.
  - `tool_calls`: count of tool-call messages in `state.messages`.

### Metrics

Primary:
- `accuracy()` — official `any()` semantics; this is the leaderboard-comparable number.
- `stderr()` on the primary accuracy.

Secondary, via `@metric`:
- `strict_accuracy` — mean of `metadata.strict_match`.
- `no_answer_rate` — mean of `metadata.no_answer`.
- `mean_tool_calls` — mean of `metadata.tool_calls`.
- `accuracy_single` — accuracy restricted to `tag == "single-answer"`.
- `accuracy_multiple` — accuracy restricted to `tag == "multiple-answer"`.
- `mean_options_selected` — mean of `metadata.num_predicted`.

## Data flow per sample

1. `record_to_sample` builds `input` and metadata from the JSON record.
2. `prepare_scenario` writes `scenario_id` + `tag` into `store()` (server tools read `scenario_id`), picks the system prompt by `tag`, and filters tools by `allowed_tools`.
3. `react` runs the turn loop up to `message_limit=30`. Tools proxy to `http://server:7860/...`.
4. `scorer` extracts last `\boxed{}`, computes official score against `target`, emits metadata; metrics aggregate across samples.

## Error handling

- No `\boxed{}` or empty box → `INCORRECT`, `no_answer=True`. Counted by `no_answer_rate`.
- Junk inside the box (e.g. `\boxed{answer is C3}`) → tokens split on `|`, lowercase-compared; no sanitization. We want to see format violations.
- Tool HTTP failure → tool returns the error string (current behavior). Agent decides.
- Unknown `tag` value → default to `SYSTEM_PROMPT_MULTIPLE`; current dataset has only two values.
- `allowed_tools` with unknown names → dropped by `filter_allowed`.
- Sandbox unreachable → Inspect's native sandbox error; not wrapped.

## Testing

### Unit

`src/tests/test_ttac_wireless_scorer.py`:

- `extract_codes`: single box, multi-box last-wins, `|`-separated, no box, empty box, whitespace, mixed case.
- `official_score`: matrix over single gt + single pred (match/miss); multi gt (`any()`): `C2|C8|C11|C16` vs pred `C8` correct, vs `C99` wrong; multi pred vs single gt: `C3|C5` vs `C3` correct per official asymmetry; empty pred incorrect.
- `strict_match`: true iff `set(predicted) == set(expected)`.

`src/tests/test_ttac_wireless_samples.py`:

- `record_to_sample` on single-answer and multi-answer fixtures: verify `tag` + `allowed_tools` land in metadata; preamble is prepended; options block preserved; target unchanged.
- `filter_allowed(["all"])` returns all 20 tools; `filter_allowed(["get_cell_info", "get_kpi_data"])` returns those two; unknown name is dropped.

### Smoke (manual)

`uv run inspect eval src/evals/ttac_wireless/task.py --limit 3 --model openrouter/openai/gpt-4o-mini`. Confirm: sandbox up, tools return data, all six metrics emitted, no crash.

## Out of scope

- Custom agent loop (planning phase, scratchpad). Stick with plain `react`.
- Track B (`ttac_ipnet`). Same scorer fix likely applies but is a separate change.
- Soft/numeric match mode. Not needed for Track A.
- Full-dataset (2000) runs in CI.
