#!/usr/bin/env bash
#
# Batch generate WireGuard key pairs using local wg genkey.
# Writes a single file: one line per key pair (private_key,public_key).
# Lab generation and key usage are handled separately.
#
# Usage: ./gen_keys.sh [N]   generate N key pairs (default: 8)
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KEYS_FILE="${SCRIPT_DIR}/keys.txt"

N=8
if [[ $# -gt 0 ]]; then
    if [[ "$1" =~ ^[0-9]+$ ]] && [[ "$1" -ge 1 ]]; then
        N="$1"
    else
        echo "Usage: $0 [N]   N = number of key pairs (default: 8)" >&2
        exit 1
    fi
fi

: > "$KEYS_FILE"
for _ in $(seq 1 "$N"); do
    priv="$(wg genkey)"
    pub="$(echo "$priv" | wg pubkey)"
    echo "${priv},${pub}" >> "$KEYS_FILE"
done

echo "Generated $N key pair(s) in $KEYS_FILE (format: private,public per line)"
