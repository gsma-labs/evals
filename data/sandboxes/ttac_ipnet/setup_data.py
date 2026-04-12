"""Download TTAC IP Network data from HuggingFace. Run once."""

import os
import shutil
import zipfile
from pathlib import Path

from huggingface_hub import hf_hub_download


DATA_DIR = Path(__file__).parent / "data"
REPO_ID = "netop/Telco-Troubleshooting-Agentic-Challenge"


def main():
    DATA_DIR.mkdir(exist_ok=True)

    token = os.environ.get("HF_TOKEN")

    # Download test questions
    hf_hub_download(
        repo_id=REPO_ID,
        filename="Track B/data/Phase_1/test.json",
        repo_type="dataset",
        local_dir=DATA_DIR,
        token=token,
    )

    # Download precomputed CLI outputs
    zip_path = hf_hub_download(
        repo_id=REPO_ID,
        filename="Track B/devices_outputs.zip",
        repo_type="dataset",
        local_dir=DATA_DIR,
        token=token,
    )

    # Extract CLI outputs
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(DATA_DIR)

    # Download question limits config (to flat path for Docker COPY; space
    # in "Track B/" breaks Dockerfile COPY syntax).
    config_src = hf_hub_download(
        repo_id=REPO_ID,
        filename="Track B/question_limits_config.json",
        repo_type="dataset",
        local_dir=DATA_DIR,
        token=token,
    )
    shutil.copy(config_src, DATA_DIR / "question_limits_config.json")

    print(f"Data downloaded and extracted to {DATA_DIR}")


if __name__ == "__main__":
    main()
