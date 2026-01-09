"""Shared pytest fixtures for Open Telco CLI tests."""

from pathlib import Path
from typing import Generator

import pytest

from open_telco.cli.app import OpenTelcoApp
from open_telco.cli.config.env_manager import PROVIDERS


@pytest.fixture
def app() -> OpenTelcoApp:
    """Create a fresh OpenTelcoApp instance."""
    return OpenTelcoApp()


@pytest.fixture
def temp_env_file(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary .env file for isolated testing."""
    temp_env = tmp_path / ".env"
    temp_env.touch()
    yield temp_env


# List of all provider names for parametrization
PROVIDER_NAMES = list(PROVIDERS.keys())

# Provider test parameters: (provider_name, env_key, example_model)
PROVIDER_TEST_PARAMS = [
    pytest.param(
        name,
        config["env_key"],
        config["example_model"],
        id=name.lower().replace(" ", "-").replace("(", "").replace(")", ""),
    )
    for name, config in PROVIDERS.items()
]
