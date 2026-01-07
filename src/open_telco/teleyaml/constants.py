"""Constants for teleyaml evaluation module."""

from textwrap import dedent

# Dataset defaults
DEFAULT_DATASET = "otellm/gsma-sample-data"
DEFAULT_DATASET_NAME = "teleyaml"
DEFAULT_SPLIT = "test"

# Judge defaults
DEFAULT_JUDGE_MODEL = "openrouter/openai/gpt-oss-120b"

# Task categories (must match dataset Category field values)
CATEGORY_AMF = "AMF Configuration"
CATEGORY_SLICE = "Slice Deployment"
CATEGORY_UE = "UE Provisioning"

# Logging
DEFAULT_LOG_DIR = "logs/teleyaml"

# System prompt template for all tasks
SYSTEM_PROMPT = dedent("""
You are an expert 5G Core Network Engineer and Configuration Specialist.
You are assisting a user with {Main Category} by converting requests into
server-side YAML configurations for {Category}.

<context>
{Context}
</context>

Your response must be valid YAML.
""")
