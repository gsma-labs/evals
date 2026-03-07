```
 ██████╗  ██████╗       ██████╗ ███████╗███╗   ██╗ ██████╗██╗  ██╗
██╔════╝ ██╔════╝       ██╔══██╗██╔════╝████╗  ██║██╔════╝██║  ██║
███████╗ ██║  ███╗█████╗██████╔╝█████╗  ██╔██╗ ██║██║     ███████║
██╔═══██╗██║   ██║╚════╝██╔══██╗██╔══╝  ██║╚██╗██║██║     ██╔══██║
╚██████╔╝╚██████╔╝      ██████╔╝███████╗██║ ╚████║╚██████╗██║  ██║
 ╚═════╝  ╚═════╝       ╚═════╝ ╚══════╝╚═╝  ╚═══╝ ╚═════╝╚═╝  ╚═╝
```

Evaluating AI-native 6G network reasoning across standardization-aligned tasks.

## Overview

3,722 multiple-choice questions across 30 expert-validated tasks covering 6G reasoning aligned with 3GPP, IETF, ETSI, ITU-T, and the O-RAN Alliance.

| Dimension | Description |
|-----------|-------------|
| Task families | 30 distinct reasoning tasks |
| Format | Multiple-choice questions |
| Focus | AI-native 6G network planning, control, and standards reasoning |
| Metadata | Task id, task name, difficulty, and category |

## Usage

```bash
uv run inspect eval src/evals/sixg_bench/sixg_bench.py --model openai/gpt-4o
```

Filter to a specific task family:

```bash
uv run inspect eval src/evals/sixg_bench/sixg_bench.py --model openai/gpt-4o -T task_id=T1
```

Run a specific sample by id:

```bash
uv run inspect eval src/evals/sixg_bench/sixg_bench.py --model openai/gpt-4o --sample-id T1_2b2f4d
```

## Scoring

Each question has one correct answer. The model is evaluated with Inspect's standard `multiple_choice(cot=False)` solver and `choice()` scorer.

## Metrics

- **accuracy**: Fraction of correct answers
- **stderr**: Standard error of the accuracy estimate

## Dataset Structure

Each record contains:

| Field | Description |
|-------|-------------|
| `question` | The multiple-choice prompt |
| `choices` | Answer candidates |
| `answer` | Index of the correct choice |
| `task_id` | Stable task family identifier |
| `task_name` | Human-readable task name |
| `difficulty` | Benchmark difficulty label |
| `category` | Higher-level reasoning category |

## Links

- [Paper](https://arxiv.org/abs/2602.08675)
- [Source](https://github.com/maferrag/6G-Bench)
