```
███╗   ██╗██╗██╗  ██╗ █████╗
████╗  ██║██║██║ ██╔╝██╔══██╗
██╔██╗ ██║██║█████╔╝ ███████║
██║╚██╗██║██║██╔═██╗ ██╔══██║
██║ ╚████║██║██║  ██╗██║  ██║
╚═╝  ╚═══╝╚═╝╚═╝  ╚═╝╚═╝  ╚═╝
```

Evaluating LLM agents on realistic network troubleshooting in emulated labs.

> Status: **Experimental**

## Overview

NIKA benchmarks agentic troubleshooting across network failures where models must inspect live network state and submit structured diagnoses.

| Dimension | Output |
|-----------|--------|
| Detection | Whether an anomaly exists |
| Localization | Faulty device(s) |
| Root Cause Analysis | Failure type |

The unified entrypoint is `src/evals/nika/nika.py`.

## Data Files

NIKA now keeps runtime data under `data/nika`:

- `data/nika/dataset.yaml`: sample-level evaluation data (input/target/sandbox/metadata).
- `data/nika/failure.yaml`: failure catalog used for RCA options, symptom text, and submit validation.

These two files are complementary: `dataset.yaml` defines which samples run, while
`failure.yaml` defines the canonical fault taxonomy and descriptions used by prompts/tools.
See `data/nika/README.md` for detailed field-level guidance.

## Usage

Install optional NIKA runtime dependencies first:

```bash
uv sync --extra nika
```

Run all families (small samples by default):

```bash
uv run inspect eval src/evals/nika/nika.py --model openai/gpt-4o
```

Run full samples:

```bash
uv run inspect eval src/evals/nika/nika.py --model openai/gpt-4o -T full=true
```

Run a specific task family:

```bash
uv run inspect eval src/evals/nika/nika.py --model openai/gpt-4o -T task_family=link_failure
```

Run a specific variant:

```bash
uv run inspect eval src/evals/nika/nika.py --model openai/gpt-4o -T variant=bmv2_down
```

Run with a specific scoring level:

```bash
uv run inspect eval src/evals/nika/nika.py --model openai/gpt-4o -T task_level=rca
```

Combine parameters:

```bash
uv run inspect eval src/evals/nika/nika.py --model openai/gpt-4o \
  -T full=true -T task_family=misconfiguration -T variant=bmv2_down -T task_level=full
```

Use a custom dataset path:

```bash
uv run inspect eval src/evals/nika/nika.py --model openai/gpt-4o \
  -T dataset_path=data/nika/dataset.yaml
```

## Parameters

Supported task parameters in `nika(...)`:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dataset_path` | `str` | bundled `DATASET_PATH` | Dataset YAML path. |
| `split` | `str` | `test` | Reserved for API consistency with other eval entries. |
| `full` | `bool` | `false` | `false` uses compact small set; `true` uses full dataset. |
| `task_family` | `TaskFamily` | `all` | Restrict to one task family. |
| `variant` | `str` | `all` | Restrict to one failure variant (for example `bmv2_down`). |
| `task_level` | `TaskLevel` | `full` | Select scoring mode (`full`, `detection`, `localization`, `rca`). |

## Dataset Selection Mode

- **Small samples** (`full=false`, default): only `size_s`, one sample per failure type, no extra variants.
- **Full samples** (`full=true`): full curated dataset.

## Task Families

Supported values for `task_family`:

- `all` (default)
- `link_failure`
- `end_host_failure`
- `misconfiguration`
- `resource_contention`
- `network_under_attack`
- `network_node_error`
- `multiple_faults`

Note: legacy per-family Python entrypoints were removed. Use `src/evals/nika/nika.py`
with `-T task_family=...` instead.

## Execution Flow

`src/evals/nika/nika.py` uses a unified pipeline:

1. Build dataset with filters (`full`, `task_family`, `variant`, `dataset_path`).
2. Inject fault commands into sandbox from sample metadata (`faults` list or `fault_setup` fallback).
3. Run a ReAct troubleshooting agent with NIKA tools and explicit submit tool.
4. Score with `task_level` selected scorer.

## Scoring

`task_level` controls scorer behavior:

- `full` (default): weighted score = detection 20% + localization F1 40% + RCA F1 40%
- `detection`: anomaly detection only
- `localization`: faulty device localization only
- `rca`: root cause analysis only

## Notes

- NIKA is currently experimental and may evolve quickly.
- NIKA uses `inspect-kathara` sandboxes and requires a working container runtime.
- `inspect-kathara` is not installed by default; install it with `uv sync --extra nika`.
- If you only want one sample for smoke testing, add `--limit 1`.
- `split` is currently reserved and does not change dataset loading behavior.

## Links

- [Paper](https://arxiv.org/abs/2512.16381)
- [Github](https://github.com/sands-lab/nika)
