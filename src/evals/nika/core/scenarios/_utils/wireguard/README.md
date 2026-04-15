# WireGuard key generation (offline)

Batch generate WireGuard private/public key pairs using the local `wg genkey` and save them to a single list file. Lab generation and how keys are used are handled separately by you.

## Prerequisites

- `wireguard-tools` (provides `wg`):

  ```bash
  # Debian/Ubuntu
  sudo apt install wireguard-tools
  ```

## Usage

```bash
./gen_keys.sh [N]
```

- **Default**: 8 key pairs.
- **N**: generate N key pairs. Example: `./gen_keys.sh 4`.

## Output

Single file `keys.txt` in this directory:

- One line per key pair: `private_key,public_key`
- Line order is stable (first line = first pair, etc.). Use index or order in your lab logic.

