# Contributing to Data Explorer Pro

Thank you for considering contributing! We welcome bug reports, feature requests, and pull requests.

## Code of Conduct

By participating, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## How to Contribute

1. **Fork** the repository and **clone** your fork.
2. **Create a feature branch** (`git checkout -b feature/my-feature`).
3. **Make your changes** – keep them focused and well‑documented.
4. **Write tests** for new functionality (if applicable).
5. **Run linting** (we use `black` and `isort`):
   ```bash
   pip install black isort
   black .
   isort .
   ```
6. **Commit** with a clear message (e.g., `Add: new chart type for heatmaps`).
7. **Push** to your fork and open a Pull Request.

## Development Setup

- Install development dependencies:
  ```bash
  pip install -r requirements-dev.txt   # if provided, or manually install black, isort, flake8
  ```
- Install pre‑commit hooks (optional):
  ```bash
  pre-commit install
  ```

## Reporting Issues

When reporting a bug, please include:
- Your operating system and Python version.
- Steps to reproduce the issue.
- Expected and actual behaviour.

## Feature Requests

We love new ideas! Please open an issue describing the feature and its use case.

## Style Guide

- Follow PEP 8.
- Use type hints for all function signatures.
- Write docstrings for public methods.
- Keep lines ≤ 100 characters.

Thank you for helping improve Data Explorer Pro!