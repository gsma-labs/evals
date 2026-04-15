# NIKA Data Files

This directory contains the runtime data sources used by the unified NIKA entrypoint:
`src/evals/nika/nika.py`.

## Files

- `dataset.yaml`: sample dataset used during evaluation.
- `failure.yaml`: failure catalog used by prompts and submit validation.

## `dataset.yaml` (evaluation samples)

`dataset.yaml` defines concrete samples. Each sample typically includes:

- `id`
- `family_id`
- `input`
- `target`
- `sandbox`
- `metadata` (e.g. `variant`, `difficulty`, `target_device`)

This file answers: **which scenarios are run and what the expected labels are**.

## `failure.yaml` (failure taxonomy)

`failure.yaml` defines the canonical failure types and metadata, such as:

- `id`
- `task_family`
- `description`
- `symptom`
- `setup_template`

This file answers: **what each failure type means and which RCA names are valid**.

## How They Work Together

- `dataset.yaml` references variants/failures through sample metadata and targets.
- `failure.yaml` provides the shared semantics for those variants (symptoms, family, descriptions).

Keep the two files aligned: any new variant used in `dataset.yaml` should also be declared in `failure.yaml`.

## Update Checklist

When adding a new fault type:

1. Add the failure definition to `failure.yaml` (`id`, `task_family`, `description`, `symptom`).
2. Add one or more samples in `dataset.yaml` that use the same `variant`/target labels.
3. Verify `sandbox` compose paths in `dataset.yaml` exist under `src/evals/nika/core/scenarios`.
4. Smoke test with:

```bash
uv run inspect eval src/evals/nika/nika.py --model openai/gpt-4o --limit 1 -T variant=<new_variant>
```
