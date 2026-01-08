---
id: dashboard
title: Dashboard
sidebar_label: Dashboard
---

import TelcoCapabilityIndex from '@site/tabs/research/components/TelcoCapabilityIndex';

<div className="research-tabs">
  <a href="/open_telco/research/dashboard" className="research-tab active">Dashboard</a>
  <a href="/open_telco/research/benchmarks" className="research-tab">Benchmarks</a>
  <a href="/open_telco/research/models" className="research-tab">Models</a>
</div>

# AI Benchmarking

Our database of benchmark results, featuring the performance of leading AI models on challenging telecommunications tasks. It includes results from benchmarks evaluated internally by Open Telco as well as data collected from external sources. Explore trends in AI capabilities across time, by benchmark, or by model.

<TelcoCapabilityIndex />

## Methodology

The TCI is inspired by [Epoch AI's Capability Index](https://epoch.ai/data/eci). It uses Item Response Theory (IRT) principles to combine scores from telecommunications benchmarks into a single capability metric.

### How TCI is Calculated

The technical foundation comes from Item Response Theory (IRT), a statistical framework originally developed for educational testing. IRT enables comparisons between models, even when they are evaluated on different benchmarks with varying difficulty levels.

The core of our model uses a logistic function:

```
P(score | θ, β, α) = σ(α(θ - β))
```

Where:
- **θ (theta)** represents the model's capability
- **β (beta)** represents the benchmark's difficulty
- **α (alpha)** is a slope parameter related to the distribution of difficulty across questions

Higher scores on harder benchmarks contribute more to the final capability estimate. For example, strong performance on TeleLogs (which has lower average scores) indicates higher capability than equivalent performance on TeleQnA (which has higher average scores).

### Benchmarks Used

The TCI currently incorporates 4 telecommunications-specific evaluations:

| Benchmark | Description | Difficulty |
|-----------|-------------|------------|
| **TeleQnA** | Multiple-choice questions on telecom knowledge | Medium |
| **TeleLogs** | Log analysis and troubleshooting | Hard |
| **TeleMath** | Mathematical reasoning in telecom contexts | Medium-Hard |
| **3GPP-TSG** | 3GPP Technical Specification Group classification | Medium-Hard |

## Submit Results

Want to add your model to the TCI rankings?

1. Run the full evaluation suite using the standard configuration
2. Submit results via [GitHub Issues](https://github.com/gsma-research/open_telco/issues)
3. Include model details and evaluation logs
