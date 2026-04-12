"""Download TTAC wireless training data from HuggingFace. Run once."""

import os
from pathlib import Path

from huggingface_hub import hf_hub_download


DATA_DIR = Path(__file__).parent / "data"
REPO_ID = "netop/Telco-Troubleshooting-Agentic-Challenge"


def main():
    DATA_DIR.mkdir(exist_ok=True)

    token = os.environ.get("HF_TOKEN")

    dest = hf_hub_download(
        repo_id=REPO_ID,
        filename="Track A/data/Phase_1/train.json",
        repo_type="dataset",
        local_dir=DATA_DIR,
        token=token,
    )
    print(f"Downloaded to {dest}")


if __name__ == "__main__":
    main()
