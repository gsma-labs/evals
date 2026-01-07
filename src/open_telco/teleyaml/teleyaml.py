"""Entry point for running teleyaml evaluation tasks."""

import argparse

from inspect_ai import eval_set

from open_telco.teleyaml.constants import DEFAULT_LOG_DIR


def main() -> tuple[bool, list]:
    """Run teleyaml evaluation tasks."""
    parser = argparse.ArgumentParser(description="Run teleyaml evaluation tasks")
    parser.add_argument(
        "--model",
        type=str,
        nargs="+",
        required=True,
        help="Model(s) to evaluate",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of samples per task",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=1,
        help="Number of resampling iterations",
    )
    parser.add_argument(
        "--log-dir",
        type=str,
        default=DEFAULT_LOG_DIR,
        help="Directory for log files",
    )

    args = parser.parse_args()

    # Use absolute module paths for tasks
    return eval_set(
        tasks=[
            "open_telco.teleyaml.tasks.amf_configuration:amf_configuration",
            "open_telco.teleyaml.tasks.slice_deployment:slice_deployment",
            "open_telco.teleyaml.tasks.ue_provisioning:ue_provisioning",
        ],
        model=args.model,
        log_dir=args.log_dir,
        limit=args.limit,
        epochs=args.epochs,
    )


if __name__ == "__main__":
    success, logs = main()
