"""Shared utilities for eval task functions."""

FULL_DATASET = "GSMA/ot-full-benchmarks"
FULL_SPLIT = "train"


def resolve_dataset(
    full: bool,
    dataset_path: str,
    default_dataset: str,
    split: str,
    default_split: str = "test",
) -> tuple[str, str]:
    """Pick full or small dataset + split, respecting explicit overrides.

    Returns ``(dataset_path, split)`` tuple.

    If the caller passed a custom ``dataset_path`` (different from the
    module's default), that explicit override always wins.  Otherwise
    ``full=True`` switches to the full-benchmarks dataset (which uses
    the ``"train"`` split instead of ``"test"``).
    """
    if dataset_path != default_dataset:
        return dataset_path, split  # explicit override wins
    if full:
        return FULL_DATASET, FULL_SPLIT
    return default_dataset, split
