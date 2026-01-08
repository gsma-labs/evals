---
id: how-to-use
title: How to use open_telco
sidebar_label: How to use open_telco
sidebar_position: 1
---

# How to use open_telco

This guide walks you through the basics of using Open Telco to benchmark your language models on telecommunications-specific tasks.

## Prerequisites

Before you begin, ensure you have:

- Python 3.10 or higher
- An API key for your preferred LLM provider (OpenAI, Anthropic, etc.)
- Basic familiarity with command-line tools

## Installation

### Using uv (Recommended)

```bash
# Install uv if you haven't already
pip install uv

# Clone the repository
git clone https://github.com/gsma-research/open_telco.git
cd open_telco

# Install dependencies
uv sync
```

### Environment Configuration

Create a `.env` file in the project root with your API keys:

```bash
# OpenAI
OPENAI_API_KEY=your_openai_key

# Anthropic
ANTHROPIC_API_KEY=your_anthropic_key

# HuggingFace (for dataset access)
HF_TOKEN=your_huggingface_token
```

## Running Evaluations

### Basic Usage

Run a single evaluation with the default model:

```bash
uv run inspect eval open_telco/teleqna
```

### Specifying a Model

```bash
uv run inspect eval open_telco/teleqna --model openai/gpt-4o
```

### Running Multiple Evaluations

```bash
uv run inspect eval open_telco/teleqna open_telco/telemath --model anthropic/claude-3-5-sonnet
```

## Available Benchmarks

| Benchmark | Description | Dataset Size |
|-----------|-------------|--------------|
| `open_telco/teleqna` | Telecommunications Q&A | 10,000 questions |
| `open_telco/telemath` | Mathematical reasoning | 500 problems |
| `open_telco/telelogs` | Network diagnostics | Synthetic logs |
| `open_telco/three_gpp` | Document classification | 3GPP documents |

## Viewing Results

After running an evaluation, results are saved in the `logs/` directory. You can view them using the Inspect AI viewer:

```bash
uv run inspect view
```

## Next Steps

- Learn about [implementing new evaluations](/notebooks/implementing-evals)
- Explore our [network environments](/notebooks/network-environments)
- Browse our [datasets](/resources/datasets)
