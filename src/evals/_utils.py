"""Shared utilities for eval task functions."""

FULL_DATASET = "GSMA/ot-full-benchmarks"


def resolve_dataset(
    full: bool,
    dataset_path: str,
    default_dataset: str,
    split: str,
) -> tuple[str, str]:
    """Pick full or small dataset + split, respecting explicit overrides.

    Returns ``(dataset_path, split)`` tuple.

    If the caller passed a custom ``dataset_path`` (different from the
    module's default), that explicit override always wins.  Otherwise
    ``full=True`` switches to the full-benchmarks dataset.
    """
    if dataset_path != default_dataset:
        return dataset_path, split  # explicit override wins
    if full:
        return FULL_DATASET, split
    return default_dataset, split
