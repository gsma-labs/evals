---
id: implementing-evals
title: Implementing new evaluations
sidebar_label: Implementing new evaluations
sidebar_position: 2
---

# Implementing New Evaluations

This guide explains how to create new evaluation benchmarks for Open Telco using the Inspect AI framework.

## Overview

Open Telco evaluations are built on [Inspect AI](https://inspect.aisi.org.uk/), a flexible framework for evaluating language models. Each evaluation consists of:

1. **Dataset**: The test cases to evaluate
2. **Solver**: The method used to generate model responses
3. **Scorer**: The logic for evaluating responses

## Basic Structure

Create a new file in `src/open_telco/your_eval/`:

```python
from inspect_ai import Task, task
from inspect_ai.dataset import Dataset, Sample
from inspect_ai.scorer import model_graded_qa
from inspect_ai.solver import generate

@task
def your_evaluation() -> Task:
    return Task(
        dataset=load_your_dataset(),
        solver=generate(),
        scorer=model_graded_qa(),
    )

def load_your_dataset() -> Dataset:
    # Load and format your dataset
    samples = [
        Sample(
            input="Your question here",
            target="Expected answer",
            metadata={"category": "example"}
        )
    ]
    return Dataset(samples=samples)
```

## Using Hugging Face Datasets

```python
from datasets import load_dataset
from inspect_ai.dataset import Dataset, Sample

def load_hf_dataset() -> Dataset:
    hf_data = load_dataset("GSMA/open_telco", "your_subset")

    samples = []
    for item in hf_data["test"]:
        samples.append(Sample(
            input=item["question"],
            target=item["answer"],
            metadata=item.get("metadata", {})
        ))

    return Dataset(samples=samples)
```

## Custom Scorers

For complex evaluation logic:

```python
from inspect_ai.scorer import Scorer, Score, accuracy

@scorer
def custom_scorer() -> Scorer:
    async def score(state, target):
        # Your scoring logic
        response = state.output.completion
        is_correct = evaluate_response(response, target)

        return Score(
            value=1.0 if is_correct else 0.0,
            answer=response,
            explanation="Scoring explanation"
        )

    return score
```

## Agent-Based Evaluations

For tasks requiring tool use:

```python
from inspect_ai.solver import generate, use_tools
from inspect_ai.tool import bash, python

@task
def agent_evaluation() -> Task:
    return Task(
        dataset=load_dataset(),
        solver=[
            use_tools([bash(), python()]),
            generate(),
        ],
        scorer=custom_scorer(),
    )
```

## Registering Your Evaluation

Add your evaluation to `src/open_telco/_registry.py`:

```python
from .your_eval import your_evaluation
```

## Testing

Run your evaluation locally:

```bash
uv run inspect eval open_telco/your_evaluation --limit 10
```

## Best Practices

1. **Document your evaluation** thoroughly
2. **Include metadata** for filtering and analysis
3. **Test with multiple models** before finalizing
4. **Consider edge cases** in your scorer
5. **Follow existing patterns** in the codebase
