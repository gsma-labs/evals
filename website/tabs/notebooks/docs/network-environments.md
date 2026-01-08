---
id: network-environments
title: Network environments
sidebar_label: Network environments
sidebar_position: 3
---

# Network Environments

Open Telco provides pre-configured network environments for realistic testing and evaluation of language models in telecommunications scenarios.

## Overview

Our network environments use containerized setups to simulate real-world network conditions. These environments are essential for:

- Testing agent-based evaluations
- Simulating network troubleshooting scenarios
- Running code execution in isolated environments

## Available Environments

### Coding Environment

A Docker-based sandbox for executing Python code during evaluations.

**Location:** `data/sandboxes/coding_env/`

**Features:**
- Isolated Python environment
- Pre-installed telecom libraries
- Secure code execution

### Usage

```yaml
# compose.yaml
services:
  coding-env:
    build:
      context: ./data/sandboxes/coding_env
    volumes:
      - ./workspace:/workspace
```

## Setting Up Environments

### Prerequisites

- Docker and Docker Compose installed
- Sufficient system resources (4GB+ RAM recommended)

### Quick Start

```bash
# Navigate to the sandbox directory
cd data/sandboxes/coding_env

# Build the environment
docker-compose build

# Start the environment
docker-compose up -d
```

## Using with Evaluations

Network environments integrate with Inspect AI's sandbox feature:

```python
from inspect_ai import Task, task
from inspect_ai.solver import generate, use_tools
from inspect_ai.tool import bash, python

@task
def network_evaluation() -> Task:
    return Task(
        dataset=load_dataset(),
        solver=[
            use_tools([bash(), python()]),
            generate(),
        ],
        scorer=custom_scorer(),
        sandbox="docker",
    )
```

## Custom Environments

To create a custom network environment:

1. Create a new directory under `data/sandboxes/`
2. Add a `Dockerfile` with required dependencies
3. Configure `compose.yaml` for orchestration
4. Reference the environment in your evaluation

### Example Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /workspace

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Add telecom-specific tools
RUN apt-get update && apt-get install -y \
    net-tools \
    iputils-ping \
    tcpdump \
    && rm -rf /var/lib/apt/lists/*

CMD ["python"]
```

## Kathara Integration

For more complex network simulations, we support [Kathara](https://www.kathara.org/) - a container-based network emulation system.

Kathara enables:
- Multi-node network topologies
- Realistic routing scenarios
- Protocol testing environments

Documentation for Kathara integration coming soon.

## Troubleshooting

### Common Issues

**Docker not running:**
```bash
docker info
# If not running, start Docker Desktop or the daemon
```

**Permission errors:**
```bash
sudo usermod -aG docker $USER
# Log out and back in
```

**Resource constraints:**
```bash
docker system prune -a
# Free up disk space
```

## Next Steps

- Browse our [datasets](/resources/datasets)
- Learn about [telco-specific agents](/resources/agents)
