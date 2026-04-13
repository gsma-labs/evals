# Telco Troubleshooting Agentic Challenge: Evaluation Report

## Benchmark Overview

The Telco Troubleshooting Agentic Challenge (TTAC) is a 5G wireless network troubleshooting benchmark from Huawei, released as part of the [netop/Telco-Troubleshooting-Agentic-Challenge](https://huggingface.co/datasets/netop/Telco-Troubleshooting-Agentic-Challenge) dataset on Hugging Face.

**Track A (Wireless):** An agent receives drive-test data from a 5G network with degraded user throughput. Using 20 diagnostic tools (cell info, signal measurements, KPI data, antenna calculations), the agent must identify root causes and select optimization solutions from 22 options.

- **Dataset:** 2000 labeled training scenarios (Phase 1)
- **Split:** 1701 single-answer, 299 multiple-answer
- **Answer format:** `\boxed{C3}` or `\boxed{C2|C8|C11|C16}`
- **Scoring:** IoU (intersection over union) for multi-answer; exact match for single-answer

## Configuration

All runs use the following settings unless noted:

| Parameter | Value |
|-----------|-------|
| Dataset split | train (first 200 of 2000, lite mode) |
| Message limit | 40 |
| Tool call budget | 10 (hard cap via `on_continue` guard) |
| System prompt | Enhanced (budget guidance + format instructions) |
| Context preamble | Included (scenario description + network info) |
| Submit tool | Disabled |

## Results (n=30, 2026-04-13)

| Metric | Sonnet 4.6 | Gemini 3.1 Flash Lite | Haiku 3.5 |
|--------|-----------|----------------------|-----------|
| **accuracy** | **30.0%** | 20.0% | 6.7% |
| strict_accuracy | **23.3%** | 13.3% | 0.0% |
| no_answer_rate | 0.0% | 6.7% | 0.0% |
| mean_tool_calls | 11.9 | 10.0 | 10.0 |
| mean_options_selected | 1.33 | 1.18 | 1.33 |
| accuracy_single | **26.9%** | 15.4% | 0.0% |
| accuracy_multiple | 50.0% | 50.0% | 50.0% |
| tokens (total) | 774k | 1,315k | 1,613k |
| wall time | 2m20s | 1m34s | 2m53s |

All models accessed via OpenRouter. Pricing and latency reflect OpenRouter's routing.

### Earlier runs (pre-IoU scorer, n=30)

| Metric | Gemini 3.1 Flash Lite (pre-IoU) |
|--------|---------------------------------|
| accuracy | 10.0% |
| strict_accuracy | 10.0% |
| no_answer_rate | 13.3% |
| accuracy_multiple | 0.0% |

The IoU scorer doubled reported accuracy by giving partial credit on multi-answer questions.

### Smoke runs (n=1)

| Model | Tool calls | No-answer | Notes |
|-------|-----------|-----------|-------|
| mimo-v2-pro (pre-guard) | 19 | 100% | Hit message limit mid-investigation; never produced answer |
| mimo-v2-pro (post-guard) | 10 | 0% | Guard forced synthesis; wrong answer but parseable |
| Gemini 3.1 Flash Lite | 10 | 0% | Produced answer; wrong on this sample |

## Interpretation

- The benchmark discriminates between model capability tiers (Sonnet > Flash Lite > Haiku).
- `accuracy_multiple: 50%` is based on very few samples at n=30 (~4 multi-answer); needs n=100+ for reliable signal.
- `mean_options_selected: ~1.2-1.3` indicates systematic under-selection; models default to single-answer even for multi-answer questions.
- The 10-tool-call budget is binding for all models. Raising it may improve accuracy but increases cost.
- `strict_accuracy` vs `accuracy` gap shows how much IoU partial credit contributes; for Sonnet, ~7% of accuracy comes from partial matches.

## Caveats

1. **Training split used.** The labeled data is the competition's training set intended for fine-tuning Qwen3.5-35B-A3B. No public test split has ground-truth labels. Results should not be compared to competition leaderboard scores.
2. **Enhanced prompts.** The upstream harness uses no system prompt. Our port adds budget guidance and format instructions. This improves answer extraction but diverges from upstream conditions. Use `faithful=true` to run without these enhancements.
3. **Context preamble.** The upstream harness does not include `context.description` or `wireless_network_information` in the agent prompt. Our port includes them by default. Use `faithful=true` to match upstream behavior.
4. **Sample size.** n=30 provides directional signal but wide confidence intervals (~+/- 17% at 95% CI for 30% accuracy).

## How to Run

```bash
# Default (enhanced prompts, context preamble, lite dataset)
uv run inspect eval src/evals/telco_challenge/track_a/task.py \
  --model openrouter/anthropic/claude-sonnet-4.6 \
  --limit 30 --message-limit 40

# Faithful mode (no system prompt, no context preamble, matches upstream)
uv run inspect eval src/evals/telco_challenge/track_a/task.py \
  --model openrouter/anthropic/claude-sonnet-4.6 \
  --limit 30 --message-limit 40 -T faithful=true

# Full dataset (2000 samples)
uv run inspect eval src/evals/telco_challenge/track_a/task.py \
  --model openrouter/anthropic/claude-sonnet-4.6 \
  -T full=true --message-limit 40
```
