import argparse

from inspect_ai import eval_set

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
    default="logs/teleyaml",
    help="Directory for log files",
)

args = parser.parse_args()

success, logs = eval_set(
    tasks=[
        "tasks/amf_configuration/amf_configuration.py",
        "tasks/slice_deployment/slice_deployment.py",
        "tasks/ue_provisioning/ue_provisioning.py",
    ],
    model=args.model,
    log_dir=args.log_dir,
    limit=args.limit,
    epochs=args.epochs,
)
