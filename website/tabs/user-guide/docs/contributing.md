---
id: contributing
title: Contributing
sidebar_label: Contributing
sidebar_position: 2
---

# Contributing to Open Telco

We welcome contributions from the community! Open Telco is an open-source project and we appreciate all forms of contributions.

## How to Contribute

### Reporting Issues

If you find a bug or have a feature request, please open an issue on our [GitHub repository](https://github.com/gsma-research/open_telco/issues).

### Code Contributions

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to your branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/open_telco.git
cd open_telco

# Install dependencies
pip install uv
uv sync --all-extras

# Install pre-commit hooks
pre-commit install

# Run tests
uv run pytest
```

### Code Style

We use the following tools to maintain code quality:

- **Ruff** for linting and formatting
- **MyPy** for type checking
- **Pre-commit** hooks for automated checks

## Adding New Evaluations

If you want to contribute a new evaluation benchmark:

1. Review the existing evaluation implementations in `src/open_telco/`
2. Follow the Inspect AI framework patterns
3. Include comprehensive documentation
4. Add appropriate tests
5. Update the registry in `_registry.py`

## Documentation

Documentation improvements are always welcome! You can:

- Fix typos or clarify existing content
- Add new tutorials or guides
- Improve code examples

## Community

Join our community discussions on GitHub Discussions or reach out via the GSMA channels.

## License

By contributing to Open Telco, you agree that your contributions will be licensed under the MIT License.
