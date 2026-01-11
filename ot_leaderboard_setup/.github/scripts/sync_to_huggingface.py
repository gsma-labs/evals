#!/usr/bin/env python3
"""Sync validated submissions to HuggingFace dataset."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import pandas as pd
from datasets import Dataset
from huggingface_hub import HfApi


DATASET_REPO = "GSMA/leaderboard"


def load_existing_dataset(token: str) -> pd.DataFrame:
    """Load existing leaderboard dataset from HuggingFace.

    Args:
        token: HuggingFace API token

    Returns:
        DataFrame with existing data, or empty DataFrame if not found
    """
    try:
        from datasets import load_dataset

        existing_ds = load_dataset(DATASET_REPO, split="train", token=token)
        return existing_ds.to_pandas()
    except Exception as e:
        print(f"Warning: Could not load existing dataset: {e}")
        return pd.DataFrame()


def merge_dataframes(existing_df: pd.DataFrame, new_df: pd.DataFrame) -> pd.DataFrame:
    """Merge new entries with existing data.

    Updates existing rows or adds new ones based on model name.

    Args:
        existing_df: Existing leaderboard data
        new_df: New submission data

    Returns:
        Merged DataFrame with duplicates resolved
    """
    if existing_df.empty:
        return new_df

    if new_df.empty:
        return existing_df

    # Combine and deduplicate by model name (keep new version)
    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
    combined_df = combined_df.drop_duplicates(subset=["model"], keep="last")

    return combined_df


def upload_to_huggingface(df: pd.DataFrame, token: str) -> None:
    """Upload DataFrame to HuggingFace dataset.

    Args:
        df: DataFrame to upload
        token: HuggingFace API token
    """
    dataset = Dataset.from_pandas(df)
    dataset.push_to_hub(DATASET_REPO, token=token)
    print(f"Successfully uploaded {len(df)} entries to {DATASET_REPO}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync submissions to HuggingFace")
    parser.add_argument(
        "--files",
        required=True,
        help="Space-separated parquet files to sync",
    )
    args = parser.parse_args()

    # Get HuggingFace token
    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        print("Error: HF_TOKEN environment variable required")
        sys.exit(1)

    # Parse file list
    files = args.files.strip().split()

    if not files or all(not f for f in files):
        print("No files to sync")
        sys.exit(0)

    # Load new submissions
    new_rows = []
    for file_path in files:
        if not file_path:
            continue

        path = Path(file_path)
        if not path.exists():
            print(f"Warning: File not found: {path}")
            continue

        if path.suffix != ".parquet":
            continue

        try:
            df = pd.read_parquet(path)
            new_rows.append(df)
            print(f"Loaded {len(df)} entries from {path}")
        except Exception as e:
            print(f"Warning: Failed to read {path}: {e}")
            continue

    if not new_rows:
        print("No valid submissions to sync")
        sys.exit(0)

    # Combine new submissions
    new_df = pd.concat(new_rows, ignore_index=True)
    print(f"Total new entries: {len(new_df)}")

    # Load existing dataset
    print(f"Loading existing dataset from {DATASET_REPO}...")
    existing_df = load_existing_dataset(hf_token)
    print(f"Existing entries: {len(existing_df)}")

    # Merge
    merged_df = merge_dataframes(existing_df, new_df)
    print(f"Merged entries: {len(merged_df)}")

    # Upload
    print("Uploading to HuggingFace...")
    upload_to_huggingface(merged_df, hf_token)

    print("Sync complete!")


if __name__ == "__main__":
    main()
