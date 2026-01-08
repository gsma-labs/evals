---
id: reference
title: Reference
sidebar_label: Reference
slug: /
---

# API Reference

This section provides detailed API documentation for Open Telco components.

## Evaluations

### TeleQnA

```python
from open_telco import teleqna

# Run the evaluation
task = teleqna()
```

**Parameters:**
- `limit` (int, optional): Number of samples to evaluate
- `shuffle` (bool, optional): Randomize sample order

### TeleMath

```python
from open_telco import telemath

task = telemath()
```

**Parameters:**
- `limit` (int, optional): Number of samples to evaluate
- `use_tools` (bool, optional): Enable tool use (bash, python)

### TeleLogs

```python
from open_telco import telelogs

task = telelogs()
```

**Parameters:**
- `mode` (str): "soft" or "hard" evaluation mode
- `limit` (int, optional): Number of samples to evaluate

### 3GPP TSG

```python
from open_telco import three_gpp

task = three_gpp()
```

## Utility Functions

### Majority Voting

```python
from open_telco.telelogs.utils import maj_at_k

# Get majority answer from k samples
result = maj_at_k(responses, k=5)
```

## Command Line Interface

```bash
# List available evaluations
uv run inspect list

# Run evaluation
uv run inspect eval open_telco/teleqna --model openai/gpt-4o

# View results
uv run inspect view
```

## Configuration

### Environment Variables

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key |
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `HF_TOKEN` | Hugging Face token |
| `OPENROUTER_API_KEY` | OpenRouter API key |

### Supported Models

Open Telco works with any model supported by Inspect AI:

- OpenAI: `openai/gpt-4o`, `openai/gpt-4-turbo`
- Anthropic: `anthropic/claude-3-5-sonnet`, `anthropic/claude-3-opus`
- Open models via OpenRouter
- Local models via Ollama
