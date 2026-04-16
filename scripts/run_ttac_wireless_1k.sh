#!/usr/bin/env bash
set -euo pipefail

# Laptop-safe 1,000-sample run of the TTAC Wireless eval.
#
# Tune --max-sandboxes to roughly: free_ram_gb / 0.4
# (server 256m + client 64m + Docker/Python overhead ~= 400 MB per stack).
# Inspect's Docker default is 2 * os.cpu_count() which is too high for laptops.
#
# --max-samples should sit slightly above --max-sandboxes so a sample can be
# mid model call while another holds the sandbox (Inspect sandboxing docs).

uv run inspect eval \
  evals/src/evals/telco_challenge/track_a/task.py@ttac_wireless \
  -T full=true \
  --max-sandboxes 6 \
  --max-samples 8 \
  --max-connections 10 \
  --max-subprocesses 8 \
  --log-level info \
  "$@"
