---
id: welcome
title: Open Telco
sidebar_label: Welcome
sidebar_position: 1
slug: /
---

# Open Telco

A collection of telco evals for the next generation of connectivity.

## Welcome

Welcome to Open Telco, a specialized framework for large language model evaluations in the telecommunications domain, created by [GSMA](https://www.gsma.com). Open Telco provides a robust suite of tools designed to measure reasoning, technical troubleshooting, and network management capabilities in AI models.

You can access the source code and contribute directly via our repository: [github.com/gsma-research/open_telco](https://github.com/gsma-research/open_telco)

- **Comprehensive Guides & Notebooks:** Step-by-step tutorials on "How to use open_telco" to benchmark your models.

- **Advanced Evaluation Implementation:** Documentation on implementing new evaluations using Inspect AI for logic and Kathara for network emulation.

- **Simulated Network Environments:** Access to our existing, pre-configured network environments for realistic testing.

- **Open-Source Datasets:** A curated collection of telco-specific datasets and methodology available on Hugging Face: [huggingface.co/datasets/GSMA/open_telco](https://huggingface.co/datasets/GSMA/open_telco)

- **Telco-Specific Agents:** A library of open-source Agents trained for specific telecommunication tasks and workflows.

## Getting Started

Welcome to Open Telco, a specialized framework for large language model evaluations in the telecommunications domain, created by [GSMA](https://www.gsma.com).

Open Telco provides a robust suite of tools designed to measure:

- **Reasoning capabilities** in telecommunications contexts
- **Technical troubleshooting** skills for network operations
- **Network management** understanding and decision-making

### Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/gsma-research/open_telco.git
   cd open_telco
   ```

2. Install dependencies using uv:
   ```bash
   pip install uv
   uv sync
   ```

3. Configure your environment:
   ```bash
   cp .env.example .env
   # Add your API keys to .env
   ```

4. Run your first evaluation:
   ```bash
   uv run inspect eval open_telco/teleqna
   ```

### Core Features

| Feature | Description |
|---------|-------------|
| TeleQnA | 10,000 Q&A pairs testing telecom knowledge |
| TeleMath | Mathematical reasoning in telecom domain |
| TeleLogs | Root cause analysis for 5G networks |
| 3GPP TSG | Document classification for standards |

## GitHub Repository

Access the complete source code and contribute to the project:

**Repository:** [github.com/gsma-research/open_telco](https://github.com/gsma-research/open_telco)

We welcome contributions from the community. Please see our [Contributing Guide](/contributing) for more information.
