"""Shared fixtures for CLI tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Generator
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests

if TYPE_CHECKING:
    from open_telco.cli.screens.submit.github_service import GitHubService, PRResult
    from open_telco.cli.screens.submit.trajectory_bundler import SubmissionBundle


@pytest.fixture
def mock_github_token(monkeypatch: pytest.MonkeyPatch) -> str:
    """Set GITHUB_TOKEN for EnvManager and environment."""
    token = "ghp_test_token_12345"
    # Patch EnvManager.get to return the token for GITHUB_TOKEN
    from open_telco.cli.config import EnvManager

    original_get = EnvManager.get

    def patched_get(self: EnvManager, key: str) -> str | None:
        if key == "GITHUB_TOKEN":
            return token
        return original_get(self, key)

    monkeypatch.setattr(EnvManager, "get", patched_get)
    # Also set env var for backwards compatibility
    monkeypatch.setenv("GITHUB_TOKEN", token)
    return token


@pytest.fixture
def temp_results_parquet(tmp_path: Path) -> Path:
    """Temporary results.parquet with test data."""
    parquet_path = tmp_path / "results.parquet"
    df = pd.DataFrame(
        [
            {
                "model": "gpt-4o (Openai)",
                "teleqna": [83.6, 1.17, 1000.0],
                "telelogs": [75.0, 4.35, 100.0],
                "telemath": [39.0, 4.9, 100.0],
                "3gpp_tsg": [54.0, 5.01, 100.0],
                "date": "2026-01-09",
            },
            {
                "model": "claude-3-opus (Anthropic)",
                "teleqna": [85.2, 1.05, 1000.0],
                "telelogs": [78.0, 4.1, 100.0],
                "telemath": [42.0, 4.5, 100.0],
                "3gpp_tsg": [56.0, 4.8, 100.0],
                "date": "2026-01-09",
            },
        ]
    )
    df.to_parquet(parquet_path, index=False)
    return parquet_path


@pytest.fixture
def temp_trajectory_files(tmp_path: Path) -> list[Path]:
    """Temporary trajectory JSON files matching Inspect AI format."""
    trajectory_files = []

    # Create trajectory for gpt-4o
    traj1 = tmp_path / "eval_2026-01-09_teleqna_gpt4o.json"
    traj1.write_text(
        json.dumps(
            {
                "eval": {
                    "model": "openai/gpt-4o",
                    "task": "teleqna",
                    "dataset": {
                        "sample_ids": list(range(1000)),
                    },
                },
                "results": {
                    "accuracy": 0.836,
                },
            }
        )
    )
    trajectory_files.append(traj1)

    # Create trajectory for telelogs
    traj2 = tmp_path / "eval_2026-01-09_telelogs_gpt4o.json"
    traj2.write_text(
        json.dumps(
            {
                "eval": {
                    "model": "openai/gpt-4o",
                    "task": "telelogs",
                    "dataset": {
                        "sample_ids": list(range(100)),
                    },
                },
                "results": {
                    "accuracy": 0.75,
                },
            }
        )
    )
    trajectory_files.append(traj2)

    # Create trajectory for claude (different model)
    traj3 = tmp_path / "eval_2026-01-09_teleqna_claude.json"
    traj3.write_text(
        json.dumps(
            {
                "eval": {
                    "model": "anthropic/claude-3-opus",
                    "task": "teleqna",
                    "dataset": {
                        "sample_ids": list(range(1000)),
                    },
                },
                "results": {
                    "accuracy": 0.852,
                },
            }
        )
    )
    trajectory_files.append(traj3)

    return trajectory_files


@pytest.fixture
def temp_trajectory_with_limit(tmp_path: Path) -> Path:
    """Trajectory JSON with limited samples (--limit flag was used)."""
    traj = tmp_path / "eval_limited_teleqna.json"
    traj.write_text(
        json.dumps(
            {
                "eval": {
                    "model": "openai/gpt-4o",
                    "task": "teleqna",
                    "dataset": {
                        "sample_ids": list(
                            range(10)
                        ),  # Only 10 samples instead of full set
                    },
                },
                "results": {
                    "accuracy": 0.80,
                },
            }
        )
    )
    return traj


@pytest.fixture
def sample_pr_result() -> "PRResult":
    """Sample successful PRResult."""
    from open_telco.cli.screens.submit.github_service import PRResult

    return PRResult(
        success=True,
        pr_url="https://github.com/gsma-research/ot_leaderboard/pull/123",
    )


@pytest.fixture
def sample_failed_pr_result() -> "PRResult":
    """Sample failed PRResult."""
    from open_telco.cli.screens.submit.github_service import PRResult

    return PRResult(
        success=False,
        error="Bad credentials",
    )


@pytest.fixture
def sample_submission_bundle() -> "SubmissionBundle":
    """Sample SubmissionBundle with test data."""
    from open_telco.cli.screens.submit.trajectory_bundler import SubmissionBundle

    # Create minimal parquet bytes
    df = pd.DataFrame(
        [
            {
                "model": "gpt-4o (Openai)",
                "teleqna": [83.6, 1.17, 1000.0],
                "telelogs": [75.0, 4.35, 100.0],
                "telemath": [39.0, 4.9, 100.0],
                "3gpp_tsg": [54.0, 5.01, 100.0],
                "date": "2026-01-09",
            }
        ]
    )
    import io

    buffer = io.BytesIO()
    df.to_parquet(buffer, index=False)
    parquet_bytes = buffer.getvalue()

    # Create sample trajectory
    trajectory_content = json.dumps(
        {
            "eval": {
                "model": "openai/gpt-4o",
                "task": "teleqna",
            },
            "results": {
                "accuracy": 0.836,
            },
        }
    ).encode()

    return SubmissionBundle(
        model_name="gpt-4o",
        provider="Openai",
        parquet_content=parquet_bytes,
        trajectory_files={
            "eval_teleqna.json": trajectory_content,
        },
    )


@pytest.fixture
def mock_github_service() -> MagicMock:
    """Mocked GitHubService with configurable responses."""
    mock = MagicMock()

    # Default successful PR creation
    from open_telco.cli.screens.submit.github_service import PRResult

    mock.create_submission_pr.return_value = PRResult(
        success=True,
        pr_url="https://github.com/gsma-research/ot_leaderboard/pull/123",
    )

    return mock


@pytest.fixture
def mock_requests_success():
    """Mock requests module for successful GitHub API calls."""
    from unittest.mock import patch

    with patch(
        "open_telco.cli.screens.submit.github_service.requests"
    ) as mock_requests:
        # Mock successful user fetch
        user_response = MagicMock()
        user_response.status_code = 200
        user_response.json.return_value = {"login": "testuser"}

        # Mock permission check (no direct access)
        permission_response = MagicMock()
        permission_response.status_code = 404

        # Mock fork check (no existing fork)
        fork_check_response = MagicMock()
        fork_check_response.status_code = 404

        # Mock fork creation
        fork_create_response = MagicMock()
        fork_create_response.status_code = 202
        fork_create_response.json.return_value = {
            "owner": {"login": "testuser"},
            "name": "ot_leaderboard",
        }

        # Mock branch ref check (doesn't exist)
        branch_check_response = MagicMock()
        branch_check_response.status_code = 404

        # Mock get default branch SHA
        ref_response = MagicMock()
        ref_response.status_code = 200
        ref_response.json.return_value = {"object": {"sha": "abc123"}}

        # Mock branch creation
        branch_create_response = MagicMock()
        branch_create_response.status_code = 201

        # Mock file check (doesn't exist)
        file_check_response = MagicMock()
        file_check_response.status_code = 404

        # Mock file creation
        file_create_response = MagicMock()
        file_create_response.status_code = 201

        # Mock PR check (no existing PR)
        pr_check_response = MagicMock()
        pr_check_response.status_code = 200
        pr_check_response.json.return_value = []

        # Mock PR creation
        pr_create_response = MagicMock()
        pr_create_response.status_code = 201
        pr_create_response.json.return_value = {
            "html_url": "https://github.com/gsma-research/ot_leaderboard/pull/123",
            "number": 123,
        }

        def get_side_effect(url, **kwargs):
            if "/user" in url and "/permission" not in url:
                return user_response
            elif "/permission" in url:
                return permission_response
            elif (
                "/repos/testuser/ot_leaderboard" in url
                and "/git/" not in url
                and "/contents/" not in url
            ):
                return fork_check_response
            elif "/git/refs/heads/" in url:
                return branch_check_response
            elif "/git/refs/heads/main" in url:
                return ref_response
            elif "/contents/" in url:
                return file_check_response
            elif "/pulls" in url:
                return pr_check_response
            return ref_response

        def post_side_effect(url, **kwargs):
            if "/forks" in url:
                return fork_create_response
            elif "/git/refs" in url:
                return branch_create_response
            elif "/pulls" in url:
                return pr_create_response
            return branch_create_response

        def put_side_effect(url, **kwargs):
            return file_create_response

        mock_requests.get.side_effect = get_side_effect
        mock_requests.post.side_effect = post_side_effect
        mock_requests.put.side_effect = put_side_effect

        yield mock_requests


# --- GitHub Service Test Fixtures ---


@pytest.fixture
def github_service() -> "GitHubService":
    """GitHubService instance with test token."""
    from open_telco.cli.screens.submit.github_service import GitHubService

    return GitHubService("test_token")


@pytest.fixture
def default_submission_params() -> dict[str, Any]:
    """Default parameters for create_submission_pr calls."""
    return {
        "model_name": "gpt-4o",
        "provider": "Openai",
        "parquet_content": b"parquet_data",
        "trajectory_files": {"test.json": b"{}"},
    }


@pytest.fixture
def mock_direct_access_responses() -> Generator[MagicMock, None, None]:
    """Mock GitHub API responses for direct write access scenario."""
    with patch(
        "open_telco.cli.screens.submit.github_service.requests"
    ) as mock_requests:
        user_resp = MagicMock()
        user_resp.status_code = 200
        user_resp.json.return_value = {"login": "testuser"}

        perm_resp = MagicMock()
        perm_resp.status_code = 200
        perm_resp.json.return_value = {"permission": "write"}

        ref_resp = MagicMock()
        ref_resp.status_code = 200
        ref_resp.json.return_value = {"object": {"sha": "abc123"}}

        branch_check = MagicMock()
        branch_check.status_code = 404

        file_check = MagicMock()
        file_check.status_code = 404

        file_create = MagicMock()
        file_create.status_code = 201

        pr_check = MagicMock()
        pr_check.status_code = 200
        pr_check.json.return_value = []

        pr_create = MagicMock()
        pr_create.status_code = 201
        pr_create.json.return_value = {
            "html_url": "https://github.com/gsma-research/ot_leaderboard/pull/123",
        }

        def get_side_effect(url: str, **kwargs: Any) -> MagicMock:
            if "/user" in url and "/permission" not in url:
                return user_resp
            elif "/permission" in url:
                return perm_resp
            elif "/git/refs/heads/main" in url:
                return ref_resp
            elif "/git/refs/heads/submit" in url:
                return branch_check
            elif "/contents/" in url:
                return file_check
            elif "/pulls" in url:
                return pr_check
            return ref_resp

        mock_requests.get.side_effect = get_side_effect
        mock_requests.post.return_value = pr_create
        mock_requests.put.return_value = file_create

        yield mock_requests


@pytest.fixture
def direct_access_pr_result(
    github_service: "GitHubService",
    mock_direct_access_responses: MagicMock,
    default_submission_params: dict[str, Any],
) -> tuple["PRResult", "GitHubService"]:
    """Execute PR creation with direct write access and return result with service."""
    result = github_service.create_submission_pr(**default_submission_params)
    return result, github_service


@pytest.fixture
def mock_fork_fallback_responses() -> Generator[MagicMock, None, None]:
    """Mock GitHub API responses for fork fallback scenario."""
    with patch(
        "open_telco.cli.screens.submit.github_service.requests"
    ) as mock_requests:
        user_resp = MagicMock()
        user_resp.status_code = 200
        user_resp.json.return_value = {"login": "testuser"}

        perm_resp = MagicMock()
        perm_resp.status_code = 404

        fork_check = MagicMock()
        fork_check.status_code = 404

        fork_create = MagicMock()
        fork_create.status_code = 202
        fork_create.json.return_value = {
            "owner": {"login": "testuser"},
            "name": "ot_leaderboard",
        }

        ref_resp = MagicMock()
        ref_resp.status_code = 200
        ref_resp.json.return_value = {"object": {"sha": "abc123"}}

        branch_check = MagicMock()
        branch_check.status_code = 404

        file_check = MagicMock()
        file_check.status_code = 404

        file_create = MagicMock()
        file_create.status_code = 201

        pr_check = MagicMock()
        pr_check.status_code = 200
        pr_check.json.return_value = []

        pr_create = MagicMock()
        pr_create.status_code = 201
        pr_create.json.return_value = {
            "html_url": "https://github.com/gsma-research/ot_leaderboard/pull/123",
        }

        def get_side_effect(url: str, **kwargs: Any) -> MagicMock:
            if "/user" in url and "/permission" not in url:
                return user_resp
            elif "/permission" in url:
                return perm_resp
            elif (
                "/repos/testuser/ot_leaderboard" in url
                and "/git/" not in url
                and "/contents/" not in url
            ):
                return fork_check
            elif "/git/refs/heads/main" in url:
                return ref_resp
            elif "/git/refs/heads/submit" in url:
                return branch_check
            elif "/contents/" in url:
                return file_check
            elif "/pulls" in url:
                return pr_check
            return ref_resp

        def post_side_effect(url: str, **kwargs: Any) -> MagicMock:
            if "/forks" in url:
                return fork_create
            elif "/pulls" in url:
                return pr_create
            return MagicMock(status_code=201)

        mock_requests.get.side_effect = get_side_effect
        mock_requests.post.side_effect = post_side_effect
        mock_requests.put.return_value = file_create

        yield mock_requests


@pytest.fixture
def fork_fallback_pr_result(
    github_service: "GitHubService",
    mock_fork_fallback_responses: MagicMock,
    default_submission_params: dict[str, Any],
) -> tuple["PRResult", "GitHubService"]:
    """Execute PR creation via fork fallback and return result with service."""
    result = github_service.create_submission_pr(**default_submission_params)
    return result, github_service


@pytest.fixture
def mock_existing_pr_responses() -> Generator[MagicMock, None, None]:
    """Mock GitHub API responses for existing PR scenario."""
    with patch(
        "open_telco.cli.screens.submit.github_service.requests"
    ) as mock_requests:
        user_resp = MagicMock()
        user_resp.status_code = 200
        user_resp.json.return_value = {"login": "testuser"}

        perm_resp = MagicMock()
        perm_resp.status_code = 200
        perm_resp.json.return_value = {"permission": "write"}

        ref_resp = MagicMock()
        ref_resp.status_code = 200
        ref_resp.json.return_value = {"object": {"sha": "abc123"}}

        branch_check = MagicMock()
        branch_check.status_code = 200

        file_check = MagicMock()
        file_check.status_code = 404

        file_create = MagicMock()
        file_create.status_code = 201

        pr_check = MagicMock()
        pr_check.status_code = 200
        pr_check.json.return_value = [
            {
                "html_url": "https://github.com/gsma-research/ot_leaderboard/pull/99",
                "number": 99,
            }
        ]

        def get_side_effect(url: str, **kwargs: Any) -> MagicMock:
            if "/user" in url and "/permission" not in url:
                return user_resp
            elif "/permission" in url:
                return perm_resp
            elif "/git/refs/heads/main" in url:
                return ref_resp
            elif "/git/refs/heads/submit" in url:
                return branch_check
            elif "/contents/" in url:
                return file_check
            elif "/pulls" in url:
                return pr_check
            return ref_resp

        mock_requests.get.side_effect = get_side_effect
        mock_requests.patch.return_value = MagicMock(status_code=200)
        mock_requests.put.return_value = file_create

        yield mock_requests


@pytest.fixture
def existing_pr_result(
    github_service: "GitHubService",
    mock_existing_pr_responses: MagicMock,
) -> "PRResult":
    """Execute PR creation when PR already exists."""
    return github_service.create_submission_pr(
        model_name="gpt-4o",
        provider="Openai",
        parquet_content=b"parquet_data",
        trajectory_files={},
    )


@pytest.fixture
def mock_http_error_responses() -> Generator[MagicMock, None, None]:
    """Mock GitHub API responses for HTTP error scenario."""
    with patch("open_telco.cli.screens.submit.github_service.requests.get") as mock_get:
        error_resp = MagicMock()
        error_resp.status_code = 401
        error_resp.json.return_value = {"message": "Bad credentials"}
        error_resp.raise_for_status.side_effect = requests.HTTPError(
            response=error_resp
        )
        mock_get.return_value = error_resp
        yield mock_get


@pytest.fixture
def http_error_pr_result(
    github_service: "GitHubService",
    mock_http_error_responses: MagicMock,
    default_submission_params: dict[str, Any],
) -> "PRResult":
    """Execute PR creation with HTTP error."""
    return github_service.create_submission_pr(**default_submission_params)


# --- Error Handling Test Fixtures ---


@pytest.fixture
def mock_401_error_responses() -> Generator[MagicMock, None, None]:
    """Mock GitHub API responses for 401 unauthorized error."""
    with patch("open_telco.cli.screens.submit.github_service.requests.get") as mock_get:
        error_resp = MagicMock()
        error_resp.status_code = 401
        error_resp.json.return_value = {"message": "Bad credentials"}
        error_resp.raise_for_status.side_effect = requests.HTTPError(
            response=error_resp
        )
        mock_get.return_value = error_resp
        yield mock_get


@pytest.fixture
def error_401_pr_result(
    mock_401_error_responses: MagicMock,
    default_submission_params: dict[str, Any],
) -> "PRResult":
    """Execute PR creation with 401 error."""
    from open_telco.cli.screens.submit.github_service import GitHubService

    service = GitHubService("invalid_token")
    return service.create_submission_pr(**default_submission_params)


@pytest.fixture
def mock_403_error_responses() -> Generator[MagicMock, None, None]:
    """Mock GitHub API responses for 403 forbidden error."""
    with patch("open_telco.cli.screens.submit.github_service.requests.get") as mock_get:
        user_resp = MagicMock()
        user_resp.status_code = 200
        user_resp.json.return_value = {"login": "testuser"}

        perm_resp = MagicMock()
        perm_resp.status_code = 200
        perm_resp.json.return_value = {"permission": "write"}

        error_resp = MagicMock()
        error_resp.status_code = 403
        error_resp.json.return_value = {"message": "API rate limit exceeded"}
        error_resp.raise_for_status.side_effect = requests.HTTPError(
            response=error_resp
        )

        def get_side_effect(url: str, **kwargs: Any) -> MagicMock:
            if "/user" in url and "/permission" not in url:
                return user_resp
            elif "/permission" in url:
                return perm_resp
            return error_resp

        mock_get.side_effect = get_side_effect
        yield mock_get


@pytest.fixture
def error_403_pr_result(
    mock_403_error_responses: MagicMock,
    default_submission_params: dict[str, Any],
) -> "PRResult":
    """Execute PR creation with 403 error."""
    from open_telco.cli.screens.submit.github_service import GitHubService

    service = GitHubService("test_token")
    return service.create_submission_pr(**default_submission_params)


@pytest.fixture
def mock_404_error_responses() -> Generator[tuple[MagicMock, MagicMock], None, None]:
    """Mock GitHub API responses for 404 not found error."""
    with (
        patch("open_telco.cli.screens.submit.github_service.requests.get") as mock_get,
        patch(
            "open_telco.cli.screens.submit.github_service.requests.post"
        ) as mock_post,
    ):
        user_resp = MagicMock()
        user_resp.status_code = 200
        user_resp.json.return_value = {"login": "testuser"}

        perm_resp = MagicMock()
        perm_resp.status_code = 404

        fork_check = MagicMock()
        fork_check.status_code = 404

        fork_fail = MagicMock()
        fork_fail.status_code = 404
        fork_fail.json.return_value = {"message": "Not Found"}
        fork_fail.raise_for_status.side_effect = requests.HTTPError(response=fork_fail)

        def get_side_effect(url: str, **kwargs: Any) -> MagicMock:
            if "/user" in url and "/permission" not in url:
                return user_resp
            elif "/permission" in url:
                return perm_resp
            elif "/repos/testuser/ot_leaderboard" in url:
                return fork_check
            return perm_resp

        mock_get.side_effect = get_side_effect
        mock_post.return_value = fork_fail

        yield mock_get, mock_post


@pytest.fixture
def error_404_pr_result(
    mock_404_error_responses: tuple[MagicMock, MagicMock],
    default_submission_params: dict[str, Any],
) -> "PRResult":
    """Execute PR creation with 404 error."""
    from open_telco.cli.screens.submit.github_service import GitHubService

    service = GitHubService("test_token")
    return service.create_submission_pr(**default_submission_params)


@pytest.fixture
def mock_timeout_error_responses() -> Generator[MagicMock, None, None]:
    """Mock GitHub API responses for timeout error."""
    with patch("open_telco.cli.screens.submit.github_service.requests.get") as mock_get:
        mock_get.side_effect = requests.Timeout("Connection timed out")
        yield mock_get


@pytest.fixture
def error_timeout_pr_result(
    mock_timeout_error_responses: MagicMock,
    default_submission_params: dict[str, Any],
) -> "PRResult":
    """Execute PR creation with timeout error."""
    from open_telco.cli.screens.submit.github_service import GitHubService

    service = GitHubService("test_token")
    return service.create_submission_pr(**default_submission_params)


@pytest.fixture
def mock_rate_limit_error_responses() -> Generator[MagicMock, None, None]:
    """Mock GitHub API responses for rate limit error."""
    with patch("open_telco.cli.screens.submit.github_service.requests.get") as mock_get:
        error_resp = MagicMock()
        error_resp.status_code = 403
        error_resp.json.return_value = {"message": "API rate limit exceeded for user"}
        error_resp.raise_for_status.side_effect = requests.HTTPError(
            response=error_resp
        )
        mock_get.return_value = error_resp
        yield mock_get


@pytest.fixture
def error_rate_limit_pr_result(
    mock_rate_limit_error_responses: MagicMock,
    default_submission_params: dict[str, Any],
) -> "PRResult":
    """Execute PR creation with rate limit error."""
    from open_telco.cli.screens.submit.github_service import GitHubService

    service = GitHubService("test_token")
    return service.create_submission_pr(**default_submission_params)
