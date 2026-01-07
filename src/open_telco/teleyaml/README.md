# TeleYAML

Evaluation measuring AI capability to translate intent into YAML network configurations.

## Tasks

Three 5G configuration tasks:

| Task | Description |
|------|-------------|
| AMF Configuration | Access and Mobility Function setup |
| Slice Deployment | Network slice configuration |
| UE Provisioning | User equipment provisioning |

Each task sends a use case to the model, which returns a YAML file solving it.

## Scoring

- We use LLM-as-a-judge
- We collaborated with network engineers to create detailed rubrics for each task, based on Open5GS documentation
- Following [Awesome LLM-as-a-Judge](https://awesome-llm-as-a-judge.github.io/), we decompose complex rubrics into binary criteria

Example from [AMF Configuration Rubric](tasks/amf_configuration/rubric.txt):

> **S1: YAML Validity (5 points)**
>
> | Points | Criteria |
> |--------|----------|
> | 5 | Valid YAML syntax, parseable by standard YAML 1.2 parsers |
> | 4 | Valid but uses deprecated YAML 1.1 features |
> | 3 | Minor formatting issues but structurally valid |
> | 2 | Requires manual correction for parsing |
> | 1 | Invalid/unparseable YAML structure |

All rubrics normalize scores to 1-100.

## Judge Calibration

- We created a 20-sample validation set with expert-annotated scores: [otellm/teleyaml](https://huggingface.co/datasets/otellm/teleyaml)
- Run [calibration.py](judge/calibration.py) to evaluate judge accuracy
- We found GPT-OSS-120b gives the best cost/performance balance

## Usage

Run all tasks:
```bash
uv run teleyaml.py --model <model>
```

Run individual task:
```bash
uv run inspect eval <task>
```

### Options

| Flag | Description |
|------|-------------|
| `--model` | Model(s) to evaluate |
| `--limit` | Sample limit |
| `--epochs` | Number of epochs |
| `--log-dir` | Output directory |

See [Inspect eval-sets docs](https://inspect.aisi.org.uk/eval-sets.html) for more options.

## Status

- **AMF Configuration**: Validated by network engineer experts
- **Slice Deployment**: Coming soon
- **UE Provisioning**: Coming soon
