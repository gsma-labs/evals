"""Find-K module for determining optimal epochs to reduce evaluation variance.

This module implements the variance reduction approach from Evan Miller's paper
"Adding Error Bars to Evals: A Statistical Approach to Language Model Evaluations"
(https://arxiv.org/abs/2411.00640).

Key Formula:
    Var(K>1) = Var(K=1) × (1 + 2/K) / 3

The variance reduction is MODEL-SPECIFIC:
- Models with high observed variance need more epochs to achieve the same reduction
- Models with low/zero variance (consistent answers) need fewer epochs
- The formula tells us how much the CONDITIONAL variance (within-question variance)
  is reduced by resampling K times

For a model with observed variance σ²:
    - K=1: No reduction (baseline)
    - K=2: Conditional variance reduced to (1 + 2/2)/3 = 1.0 of original → 0% reduction
           Wait, let me recalculate: (1 + 2/K)/3 = (1 + 1)/3 = 0.667 → 33% reduction
    - K=3: (1 + 2/3)/3 = 0.556 → 44% reduction
    - K=4: (1 + 2/4)/3 = 0.500 → 50% reduction
    - K=5: (1 + 2/5)/3 = 0.467 → 53% reduction

The ACTUAL variance reduction for a specific model depends on:
1. The model's observed inconsistency rate (how often it gives different answers)
2. The K value chosen
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from open_telco.cli.utils.process import communicate_with_timeout, start_process

from dotenv import load_dotenv

# Load .env from project root
_project_root = Path(__file__).parent.parent.parent.parent.parent
_env_path = _project_root / ".env"
if _env_path.exists():
    load_dotenv(_env_path)


@dataclass
class FindKResult:
    """Result of find-k optimization."""

    optimal_k: int
    variance_reduction_pct: float
    task_consistency: dict[str, list[bool]] = field(default_factory=dict)
    observed_variance: float = 0.0
    error: str | None = None


def calculate_theoretical_variance_reduction(k: int) -> float:
    """Calculate THEORETICAL variance reduction percentage for given K.

    This is the maximum possible reduction assuming binary-scored questions
    with uniformly distributed difficulty (from the paper).

    Formula: Var(K>1) = Var(K=1) × (1 + 2/K) / 3
    Reduction = 1 - (1 + 2/K) / 3

    Args:
        k: Number of epochs/resamples

    Returns:
        Theoretical variance reduction as a percentage (0-100)
    """
    if k <= 1:
        return 0.0
    # Reduction = 1 - (1 + 2/K) / 3
    return (1 - (1 + 2 / k) / 3) * 100


def calculate_variance_reduction(k: int, observed_inconsistency: float = 1.0) -> float:
    """Calculate MODEL-SPECIFIC variance reduction percentage for given K.

    The actual variance reduction depends on the model's observed inconsistency.
    A model that is already consistent (0% inconsistency) gets 0% benefit from
    more epochs. A highly inconsistent model (100% inconsistency) gets the full
    theoretical benefit.

    Args:
        k: Number of epochs/resamples
        observed_inconsistency: Proportion of tasks that showed variance (0.0 to 1.0)
                               0.0 = perfectly consistent, 1.0 = all tasks varied

    Returns:
        Model-specific variance reduction as a percentage (0-100)
    """
    if k <= 1:
        return 0.0
    if observed_inconsistency <= 0:
        return 0.0  # No variance to reduce

    # The theoretical reduction scaled by the observed inconsistency
    # If model is 50% inconsistent, it can only benefit from 50% of the theoretical max
    theoretical = calculate_theoretical_variance_reduction(k)
    return theoretical * observed_inconsistency


def find_optimal_k(
    task_consistency: dict[str, list[bool]],
    target_reduction: float = 50.0,
    max_k: int = 5,
) -> tuple[int, float, float]:
    """Find optimal K based on observed consistency across epochs.

    If the model scores consistently (all correct or all incorrect across epochs),
    K=1 is sufficient. Otherwise, find the minimum K that achieves the target
    variance reduction based on the MODEL'S OBSERVED INCONSISTENCY.

    Args:
        task_consistency: Dict mapping task name to list of correctness per epoch
        target_reduction: Target variance reduction percentage (default 50%)
        max_k: Maximum K to consider (default 5)

    Returns:
        Tuple of (optimal_k, achieved_variance_reduction_pct, observed_inconsistency)
    """
    # Calculate observed inconsistency rate
    observed_inconsistency = _calculate_observed_variance(task_consistency)

    # Check if model is perfectly consistent
    if observed_inconsistency == 0.0:
        # Model is consistent - K=1 is sufficient (smart model)
        return 1, 0.0, 0.0

    # Find minimum K that achieves target reduction for THIS MODEL
    for k in range(2, max_k + 1):
        reduction = calculate_variance_reduction(k, observed_inconsistency)
        if reduction >= target_reduction:
            return k, reduction, observed_inconsistency

    # Return max K if target not achievable
    return max_k, calculate_variance_reduction(max_k, observed_inconsistency), observed_inconsistency


def _try_load_json(path: Path) -> dict | None:
    """Try to load JSON from a file. Returns None on failure."""
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def _process_epoch_data(
    data: dict,
    task_consistency: dict[str, list[bool]],
    model: str,
) -> None:
    """Process a single epoch log file and update task_consistency.

    Args:
        data: Parsed JSON data from log file
        task_consistency: Dict to update with results
        model: Model name to filter logs
    """
    eval_info = data.get("eval", {})
    log_model = eval_info.get("model", "")

    if log_model != model:
        return

    task_name = eval_info.get("task", "")
    if not task_name:
        return

    results = data.get("results", {})
    scores = results.get("scores", [])

    if not scores:
        return

    for score_item in scores:
        if score_item.get("name") != "accuracy":
            continue
        value = score_item.get("value", 0)
        is_correct = value > 0

        if task_name not in task_consistency:
            task_consistency[task_name] = []
        task_consistency[task_name].append(is_correct)
        return


def _parse_epoch_results(log_dir: Path, model: str) -> dict[str, list[bool]]:
    """Parse evaluation logs to extract per-task correctness across epochs.

    Args:
        log_dir: Directory containing evaluation log JSON files
        model: Model name to filter logs

    Returns:
        Dict mapping task name to list of correctness (True/False) per epoch
    """
    task_consistency: dict[str, list[bool]] = {}

    if not log_dir.exists():
        return task_consistency

    for json_file in sorted(log_dir.glob("*.json")):
        data = _try_load_json(json_file)
        if data is None:
            continue
        _process_epoch_data(data, task_consistency, model)

    return task_consistency


def _create_fallback_result(error: str) -> FindKResult:
    """Create a fallback FindKResult assuming worst case (100% inconsistency)."""
    return FindKResult(
        optimal_k=5,
        variance_reduction_pct=calculate_variance_reduction(5, 1.0),
        observed_variance=1.0,
        error=error,
    )


def _extract_last_error_line(output: str) -> str:
    """Extract the last non-empty line from error output."""
    if not output:
        return "Find-K evaluation failed"
    lines = [line for line in output.strip().split("\n") if line.strip()]
    if not lines:
        return "Find-K evaluation failed"
    return lines[-1]


def run_find_k(
    model: str,
    epochs: int = 5,
    tasks: list[str] | None = None,
    open_telco_dir: Path | None = None,
    timeout: int = 600,
) -> FindKResult:
    """Run find-k to determine optimal number of epochs.

    Runs mini-open-telco with multiple epochs to observe model consistency,
    then calculates optimal K using the paper's variance formula.

    Args:
        model: Model identifier (e.g., "openai/gpt-4o")
        epochs: Number of epochs to run for consistency testing (default 5)
        tasks: List of task paths (default: all 4 tasks)
        open_telco_dir: Path to src/open_telco directory
        timeout: Timeout in seconds (default 600 = 10 minutes)

    Returns:
        FindKResult with optimal K and variance reduction percentage
    """
    if tasks is None:
        tasks = [
            "telelogs/telelogs.py",
            "telemath/telemath.py",
            "teleqna/teleqna.py",
            "three_gpp/three_gpp.py",
        ]

    if open_telco_dir is None:
        open_telco_dir = Path(__file__).parent.parent.parent

    # Create a dedicated log directory for find-k
    log_dir = open_telco_dir / "logs" / "find_k"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Clear previous find-k logs for this model
    for old_log in log_dir.glob("*.json"):
        try:
            old_log.unlink()
        except OSError:
            pass

    cmd = [
        "uv",
        "run",
        "inspect",
        "eval",
        *tasks,
        "--model",
        model,
        "--limit",
        "1",
        "--epochs",
        str(epochs),
        "--log-dir",
        "logs/find_k",
        "--log-format",
        "json",
    ]

    process = start_process(cmd, cwd=open_telco_dir)
    if process is None:
        return _create_fallback_result(error="Failed to start find-k process")

    stdout, stderr, timed_out = communicate_with_timeout(process, timeout)

    if timed_out:
        return _create_fallback_result(error=f"Find-K timed out after {timeout} seconds")

    if process.returncode != 0:
        error_msg = _extract_last_error_line(stderr or stdout)
        return _create_fallback_result(error=error_msg)

    # Parse results to determine consistency
    task_consistency = _parse_epoch_results(log_dir, model)

    if not task_consistency:
        # Fallback: parse from stdout if no logs found
        task_consistency = _parse_output_for_consistency(stdout + stderr, epochs)

    # Calculate optimal K based on observed inconsistency
    optimal_k, variance_reduction, observed_variance = find_optimal_k(task_consistency)

    return FindKResult(
        optimal_k=optimal_k,
        variance_reduction_pct=variance_reduction,
        task_consistency=task_consistency,
        observed_variance=observed_variance,
    )


def _parse_output_for_consistency(output: str, epochs: int) -> dict[str, list[bool]]:
    """Parse stdout/stderr to extract consistency information.

    Fallback parsing when log files are not available.

    Args:
        output: Combined stdout and stderr from eval command
        epochs: Number of epochs that were run

    Returns:
        Dict mapping task name to list of correctness per epoch
    """
    task_consistency: dict[str, list[bool]] = {}

    # Try to parse accuracy values from output
    # Format: "task_name: accuracy=0.85" or "accuracy: 0.85"
    task_patterns = [
        r"(telelogs|telemath|teleqna|three_gpp).*?accuracy[=:\s]+([0-9.]+)",
        r"(telelogs|telemath|teleqna|3gpp_tsg).*?accuracy[=:\s]+([0-9.]+)",
    ]

    for pattern in task_patterns:
        matches = re.findall(pattern, output, re.IGNORECASE)
        for task_name, accuracy in matches:
            task_name = task_name.lower()
            if task_name not in task_consistency:
                task_consistency[task_name] = []
            # Score > 0 is considered correct
            is_correct = float(accuracy) > 0
            task_consistency[task_name].append(is_correct)

    return task_consistency


def _calculate_observed_variance(task_consistency: dict[str, list[bool]]) -> float:
    """Calculate observed variance from consistency data.

    Variance is the proportion of inconsistent samples (those that vary
    across epochs).

    Args:
        task_consistency: Dict mapping task name to list of correctness per epoch

    Returns:
        Observed variance as a proportion (0.0 to 1.0)
    """
    if not task_consistency:
        return 0.0

    total_tasks = len(task_consistency)
    inconsistent_tasks = 0

    for task_results in task_consistency.values():
        if not task_results:
            continue
        # Task is inconsistent if results vary across epochs
        if len(set(task_results)) > 1:
            inconsistent_tasks += 1

    return inconsistent_tasks / total_tasks if total_tasks > 0 else 0.0


def run_find_k_sync(
    model: str,
    epochs: int = 5,
    tasks: list[str] | None = None,
    open_telco_dir: Path | None = None,
    timeout: int = 600,
) -> FindKResult:
    """Synchronous wrapper for run_find_k.

    For use in threaded workers.

    Args:
        model: Model identifier
        epochs: Number of epochs to run
        tasks: List of task paths
        open_telco_dir: Path to src/open_telco directory
        timeout: Timeout in seconds

    Returns:
        FindKResult with optimal K and variance reduction percentage
    """
    return run_find_k(
        model=model,
        epochs=epochs,
        tasks=tasks,
        open_telco_dir=open_telco_dir,
        timeout=timeout,
    )
