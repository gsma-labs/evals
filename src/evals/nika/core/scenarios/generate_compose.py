#!/usr/bin/env python3
"""Regenerate all scenario compose.yaml files via generate_compose_for_inspect.

Reads build_images/scenarios/scenario.yaml and for each scenario that has
lab_conf_path:
  1. If has_lab_generator: run the lab generator (writes topology/lab.conf etc.)
  2. Call generate_compose_for_inspect(lab_dir) and write the result to compose_path.

Usage (from repo root):
  uv run python build_images/scenarios/generate_compose.py
  uv run python build_images/scenarios/generate_compose.py -s build_images/scenarios/scenario.yaml
  uv run python build_images/scenarios/generate_compose.py --dry-run
  uv run python build_images/scenarios/generate_compose.py --compose-only   # only regenerate compose.yaml, skip lab generator
  uv run python build_images/scenarios/generate_compose.py --only p4/p4_int  # only refresh one scenario (by id)
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import yaml
from inspect_kathara.sandbox import generate_compose_for_inspect

# Paths relative to this script
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
DEFAULT_SCENARIO_YAML = SCRIPT_DIR / "scenario.yaml"


def _load_yaml(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_scenarios(path: Path) -> list[dict]:
    data = _load_yaml(path)
    return data.get("scenarios") or []


def _generator_path_and_args(scenario: dict) -> tuple[Path | None, list[str]]:
    """Return (absolute path to lab_generator.py, argv for subprocess) or (None, [])."""
    sid = scenario.get("id") or ""
    size = scenario.get("size")
    scenarios_dir = SCRIPT_DIR
    # Scenario id: "category/name/size_s" or "category/name" (e.g. p4/p4_counter)
    parts = sid.split("/")
    if len(parts) >= 2:
        if len(parts) == 3 and str(size) in ("s", "m", "l"):
            # e.g. campus/campus_dhcp/size_s -> campus/campus_dhcp/lab_generator.py
            gen_rel = f"{parts[0]}/{parts[1]}/lab_generator.py"
        else:
            # e.g. p4/p4_counter -> p4/p4_counter/lab_generator.py
            gen_rel = f"{parts[0]}/{parts[1]}/lab_generator.py"
    else:
        return None, []
    gen_path = scenarios_dir / gen_rel
    if not gen_path.is_file():
        return None, []
    argv = [sys.executable, str(gen_path)]
    if size in ("s", "m", "l"):
        argv.extend(["-s", str(size)])
    return gen_path, argv


def run_generator(scenario: dict, dry_run: bool) -> None:
    """Run lab generator for this scenario if it has one."""
    gen_path, argv = _generator_path_and_args(scenario)
    if gen_path is None:
        return
    cwd = str(gen_path.parent)
    if dry_run:
        print(f"  [dry-run] would run: {' '.join(argv)} (cwd={cwd})")
        return
    subprocess.run(argv, cwd=cwd, check=True)


def regenerate_compose(scenario: dict, dry_run: bool) -> None:
    """Generate compose.yaml for one scenario."""
    lab_conf_path = scenario.get("lab_conf_path")
    compose_path = scenario.get("compose_path")
    if not lab_conf_path or not compose_path:
        return
    scenarios_dir = SCRIPT_DIR
    # generate_compose_for_inspect expects the scenario root (dir containing topology/lab.conf)
    lab_root = scenarios_dir / Path(compose_path).parent
    compose_file = scenarios_dir / compose_path
    lab_conf_file = scenarios_dir / lab_conf_path
    if not lab_conf_file.exists():
        print(f"  skip (lab.conf missing): {lab_conf_file}")
        return
    if dry_run:
        print(f"  [dry-run] would generate {compose_file} from {lab_root}")
        return
    compose_yaml = generate_compose_for_inspect(lab_path=lab_root)
    compose_file.parent.mkdir(parents=True, exist_ok=True)
    compose_file.write_text(compose_yaml)
    print(f"  wrote {compose_file.relative_to(REPO_ROOT)}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Regenerate all scenario compose.yaml via generate_compose_for_inspect"
    )
    parser.add_argument(
        "-s",
        "--scenarios",
        type=Path,
        default=DEFAULT_SCENARIO_YAML,
        help="Path to scenario.yaml",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only print what would be done",
    )
    parser.add_argument(
        "--compose-only",
        action="store_true",
        help="Only regenerate compose.yaml from existing topology/lab.conf; do not run lab generator",
    )
    parser.add_argument(
        "--only",
        type=str,
        metavar="SCENARIO_ID",
        help="Only refresh this scenario (exact id, e.g. p4/p4_int or data_center/dc_clos_worker/size_s)",
    )
    args = parser.parse_args()

    if not args.scenarios.is_file():
        print(f"Scenario file not found: {args.scenarios}", file=sys.stderr)
        sys.exit(1)

    scenarios = load_scenarios(args.scenarios)
    if not scenarios:
        print("No scenarios found.", file=sys.stderr)
        sys.exit(0)

    if args.only:
        scenarios = [s for s in scenarios if s.get("id") == args.only]
        if not scenarios:
            print(f"No scenario with id '{args.only}' found.", file=sys.stderr)
            sys.exit(1)

    for s in scenarios:
        sid = s.get("id", "?")
        if not s.get("lab_conf_path"):
            continue
        print(f"{sid}")
        if not args.compose_only and s.get("has_lab_generator"):
            run_generator(s, dry_run=args.dry_run)
        regenerate_compose(s, dry_run=args.dry_run)

    print("Done.")


if __name__ == "__main__":
    main()
