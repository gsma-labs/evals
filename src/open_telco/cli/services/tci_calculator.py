"""TCI (Telco Capability Index) calculation utilities.

Uses IRT-inspired methodology for meaningful cross-model comparisons.
Ported from website/src/utils/calculateTCI.ts
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

TCI_CONFIG = {
    "benchmark_difficulty": {
        "teleqna": 0.7,  # Easier - higher avg scores
        "telelogs": 0.3,  # Harder - lower avg scores
        "telemath": 0.4,  # Medium-hard
        "tsg": 0.4,  # Medium-hard
    },
    "benchmark_slope": {
        "teleqna": 1.2,
        "telelogs": 1.5,
        "telemath": 1.3,
        "tsg": 1.2,
    },
    "base_errors": {
        "teleqna": 1.5,
        "telelogs": 3.6,
        "telemath": 2.8,
        "tsg": 2.4,
        "tci": 1.8,
    },
    "min_scores_required": 3,
    "base_score": 115,
    "scale_factor": 20,
}


@dataclass
class LeaderboardEntry:
    """Entry for leaderboard calculations."""

    model: str
    provider: str = ""
    teleqna: float | None = None
    teleqna_stderr: float | None = None
    telelogs: float | None = None
    telelogs_stderr: float | None = None
    telemath: float | None = None
    telemath_stderr: float | None = None
    tsg: float | None = None
    tsg_stderr: float | None = None
    tci: float | None = field(default=None, repr=False)
    is_user: bool = field(default=False, repr=False)


def calculate_tci(entry: LeaderboardEntry) -> float | None:
    """Calculate TCI score using IRT-inspired methodology.

    The TCI score is calculated based on weighted performance across
    four benchmarks (TeleQnA, TeleLogs, TeleMath, 3GPP-TSG), taking into
    account each benchmark's difficulty and discrimination factor.

    Args:
        entry: Leaderboard entry with benchmark scores

    Returns:
        TCI score (typically 90-150 range) or None if insufficient data
    """
    scores = [
        ("teleqna", entry.teleqna),
        ("telelogs", entry.telelogs),
        ("telemath", entry.telemath),
        ("tsg", entry.tsg),
    ]

    valid_scores = [(k, v) for k, v in scores if v is not None]
    if len(valid_scores) < TCI_CONFIG["min_scores_required"]:
        return None

    total_weight = 0.0
    weighted_capability = 0.0

    for key, value in valid_scores:
        # Normalize score to 0-1 range
        score = value / 100.0

        # Get difficulty and slope from config
        difficulty = 1 - TCI_CONFIG["benchmark_difficulty"][key]
        slope = TCI_CONFIG["benchmark_slope"][key]

        # Clamp score to prevent log(0) or log(inf)
        adjusted_score = max(0.01, min(0.99, score))

        # Logit transformation (IRT-inspired)
        logit_score = math.log(adjusted_score / (1 - adjusted_score))

        # Weight by difficulty and slope
        weight = difficulty * slope
        weighted_capability += (logit_score + difficulty * 2) * weight
        total_weight += weight

    # Scale to TCI range (roughly 90-150)
    raw_capability = weighted_capability / total_weight
    tci = TCI_CONFIG["base_score"] + raw_capability * TCI_CONFIG["scale_factor"]

    return round(tci * 10) / 10


def calculate_error(score: float, benchmark_key: str) -> float:
    """Calculate synthetic error based on score and benchmark difficulty.

    Higher scores have lower error, lower scores have higher error.
    Each benchmark has a different base error reflecting measurement uncertainty.

    Args:
        score: The benchmark or TCI score
        benchmark_key: The benchmark identifier (e.g., 'teleqna', 'tci')

    Returns:
        Error margin value
    """
    base_error = TCI_CONFIG["base_errors"].get(benchmark_key, 2.0)
    return round((base_error * (1 + (100 - score) / 200)) * 100) / 100


def sort_by_tci(entries: Sequence[LeaderboardEntry]) -> list[LeaderboardEntry]:
    """Sort entries by TCI score (descending, nulls last).

    Args:
        entries: List of leaderboard entries

    Returns:
        Sorted list of entries
    """

    def sort_key(entry: LeaderboardEntry) -> tuple[int, float]:
        tci = entry.tci if entry.tci is not None else calculate_tci(entry)
        if tci is None:
            return (1, 0.0)  # Nulls last
        return (0, -tci)  # Descending

    return sorted(entries, key=sort_key)


def with_tci(entry: LeaderboardEntry) -> LeaderboardEntry:
    """Calculate TCI and set it on the entry.

    Args:
        entry: Leaderboard entry

    Returns:
        Entry with TCI calculated
    """
    entry.tci = calculate_tci(entry)
    return entry
