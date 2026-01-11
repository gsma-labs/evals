# Open Telco Leaderboard Submissions

This is a **transit repository** for evaluation submissions to the [Open Telco Leaderboard](https://huggingface.co/datasets/GSMA/leaderboard).

> **Note**: This repository does not store data permanently. PRs are validated, reviewed, synced to HuggingFace, and then closed without merging.

## How It Works

```
┌─────────────┐     ┌─────────────────────┐     ┌─────────────────┐
│  CLI Submit │────>│  This Repo (Transit)│────>│   HuggingFace   │
│             │     │   - Validation      │     │  GSMA/leaderboard│
│             │     │   - Review          │     │                 │
└─────────────┘     └─────────────────────┘     └─────────────────┘
```

## Submission Process

1. **Run evaluations** using the Open Telco CLI:
   ```bash
   uv run open-telco
   # Select: run-evals
   ```

2. **Submit results** from the CLI:
   ```bash
   # Select: submit
   # Choose models to submit
   # A PR will be created automatically
   ```

3. **Automated validation** runs on your PR:
   - Parquet schema (required columns)
   - JSON trajectory format
   - Model/provider format
   - Inspect evaluation signature
   - No errors in trajectory logs
   - **Sample count verification** (checks all benchmark samples were evaluated)

4. **Maintainer review**: If validation passes, a maintainer is automatically requested to review.

5. **Approval workflow**:
   - **Approved**: Scores sync to HuggingFace, PR closes (no merge)
   - **Changes requested**: `needs-work` label added, fix and push again
   - **Rejected**: PR closed with rejection message

## PR Lifecycle

```
PR Created
    │
    ▼
┌───────────────────┐
│ Validation Runs   │
└───────────────────┘
    │
    ├── PASS ──> Add 'ready-for-review' label
    │            Request review from @eaguaida
    │
    └── FAIL ──> Add 'needs-work' label
                 (Submitter can push fixes)
    │
    ▼
┌───────────────────┐
│ Maintainer Review │
└───────────────────┘
    │
    ├── APPROVE ──> Sync to HuggingFace
    │               Close PR (no merge)
    │               Add 'synced-to-hf' label
    │
    └── REJECT ──> Close PR
                   Add 'rejected' label
```

## Repository Structure

```
ot_leaderboard/
├── model_cards/              # Transit: parquet files (never merged)
├── trajectories/             # Transit: JSON logs (never merged)
└── .github/
    ├── workflows/
    │   ├── validate-submission.yaml  # Runs validation, requests review
    │   ├── approval-sync.yaml        # Handles approval -> HF sync
    │   └── rejection-handler.yaml    # Handles PR rejection
    └── scripts/
        ├── validate_submission.py
        └── sync_to_huggingface.py
```

## Model Card Format (Parquet)

Each parquet file must contain:

| Column | Type | Description |
|--------|------|-------------|
| `model` | string | Model name in format "model_name (Provider)" |
| `teleqna` | array | [score, stderr, n_samples] |
| `telelogs` | array | [score, stderr, n_samples] |
| `telemath` | array | [score, stderr, n_samples] |
| `3gpp_tsg` | array | [score, stderr, n_samples] |
| `date` | string | ISO date (YYYY-MM-DD) |

## Sample Count Validation

The validation workflow checks that all benchmark samples were evaluated by comparing `sample_ids` in trajectory files against the expected counts from the [GSMA/open_telco](https://huggingface.co/datasets/GSMA/open_telco) dataset.

**Common validation failures**:
- Using `--limit` during evaluation (partial benchmark)
- Missing benchmarks (not all 4 tasks completed)
- Duplicate sample IDs across runs

## Recognized Providers

Openai, Anthropic, Google, Mistral, Deepseek, Meta, Cohere, Together, Openrouter, Groq, Fireworks

## Requirements

- `GITHUB_TOKEN`: Required for CLI submission (PAT with `repo` scope)
- `HF_TOKEN`: Required for HuggingFace sync (repo secret with write access)

## Links

- [Open Telco CLI](https://github.com/GSMA/open_telco)
- [HuggingFace Leaderboard](https://huggingface.co/datasets/GSMA/leaderboard)
- [Benchmark Dataset](https://huggingface.co/datasets/GSMA/open_telco)
