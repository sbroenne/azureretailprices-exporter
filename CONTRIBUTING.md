# Contributing to Azure Retail Prices Exporter

Thank you for your interest in contributing to the Azure Retail Prices Exporter! This document provides guidelines and instructions for contributing to this project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)

## Code of Conduct

This project adheres to a Code of Conduct that all contributors are expected to follow. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) for dependency management
- Git for version control

### Setting Up Your Development Environment

1. **Fork the repository** on GitHub

2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/azureretailprices-exporter.git
   cd azureretailprices-exporter
   ```

3. **Add the upstream repository**:
   ```bash
   git remote add upstream https://github.com/sbroenne/azureretailprices-exporter.git
   ```

4. **Install uv** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

5. **Install dependencies**:
   ```bash
   uv sync
   ```

6. **Run commands through uv**:
   ```bash
   uv run pytest
   ```

### VS Code Setup (Recommended)

This project includes VS Code configuration for an optimal development experience:

- **Python interpreter** is automatically configured
- **Debug configurations** are pre-configured
- **Tasks** are available for common operations
- **Extensions** recommendations will be prompted on first open

Simply open the project in VS Code and install the recommended extensions when prompted.

## Development Workflow

### Creating a Branch

Create a new branch for your work:

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

Use descriptive branch names:
- `feature/` for new features
- `fix/` for bug fixes
- `docs/` for documentation changes
- `refactor/` for code refactoring

### Making Changes

1. **Make your changes** in your feature branch
2. **Follow the coding standards** (see below)
3. **Add tests** for new functionality
4. **Update documentation** as needed

### Keeping Your Fork Updated

Regularly sync your fork with the upstream repository:

```bash
git fetch upstream
git checkout main
git merge upstream/main
git push origin main
```

## Pull Request Process

### Before Submitting

Ensure your code passes all quality checks:

```bash
# Run tests
uv run pytest

# Check linting
uv run ruff check .

# Check code formatting
uv run black --check .

# Optional: Type checking
uv run pyright
```

**Fix any issues** before submitting your PR:

```bash
# Auto-fix linting issues
uv run ruff check --fix .

# Auto-format code
uv run black .
```

### Submitting a Pull Request

1. **Push your changes** to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create a Pull Request** on GitHub from your fork to the main repository

3. **Fill out the PR template** with all relevant information

4. **Wait for review** - maintainers will review your PR and may request changes

5. **Address feedback** if any changes are requested

6. **Once approved**, your PR will be merged!

### Pull Request Guidelines

- **Keep PRs focused**: One feature or fix per PR
- **Write clear commit messages**: Use descriptive messages explaining what and why
- **Update documentation**: Include relevant documentation updates
- **Add tests**: New features should include tests
- **Follow coding standards**: Ensure code passes all quality checks
- **Be responsive**: Address review feedback promptly

## Coding Standards

### Python Style

- **Python 3.10+** syntax (modern union types, etc.)
- **Type hints** for all functions and methods
- **Black** for code formatting (line length: 88)
- **Ruff** for linting
- **Structured logging** instead of print statements

### Code Quality Tools

The project uses the following tools to maintain code quality:

- **[Black](https://black.readthedocs.io/)** - Code formatter
- **[Ruff](https://docs.astral.sh/ruff/)** - Fast Python linter
- **[Pyright](https://github.com/microsoft/pyright)** - Type checker (optional)
- **[pytest](https://pytest.org/)** - Testing framework

### Best Practices

- **Use type hints**: All functions should have type annotations
- **Write docstrings**: Document public functions and classes
- **Handle errors**: Use proper exception handling
- **Log appropriately**: Use the logging module for debugging
- **Keep it simple**: Write clear, readable code
- **Test your code**: Write unit tests for new functionality

### Code Formatting

Format your code with Black before committing:

```bash
uv run black api/ export_prices_*.py
```

### Linting

Check and fix linting issues:

```bash
uv run ruff check .
uv run ruff check --fix .  # Auto-fix where possible
```

## Testing

### Running Tests

Run the test suite:

```bash
uv run pytest
```

Run tests with coverage:

```bash
uv run pytest --cov=api --cov-report=term-missing
```

Run specific tests:

```bash
uv run pytest api/tests/test_azureapi.py::test_name
```

### Writing Tests

- Place tests in the `api/tests/` directory
- Use descriptive test names: `test_function_name_expected_behavior`
- Use pytest fixtures for common setup
- Mock external API calls
- Aim for good test coverage of new code

### Test Guidelines

- **Write tests first** (TDD approach recommended)
- **Test edge cases** and error conditions
- **Keep tests isolated** - no dependencies between tests
- **Use clear assertions** - test one thing per test
- **Mock external dependencies** - don't make real API calls in tests

## Documentation

### Types of Documentation

- **Code comments**: Explain complex logic
- **Docstrings**: Document all public functions and classes
- **README.md**: User-facing documentation
- **CONTRIBUTING.md**: This file - developer guidelines
- **Inline documentation**: Update as you change code

### Documentation Standards

- **Keep it current**: Update docs when you change code
- **Be clear and concise**: Write for your audience
- **Use examples**: Show how to use features
- **Include references**: Link to external resources when helpful

### Updating Documentation

When making changes, update relevant documentation:

- **Code changes**: Update docstrings and comments
- **New features**: Update README.md with usage examples
- **API changes**: Update docstrings and type hints
- **Configuration**: Update configuration documentation

## Getting Help

If you need help or have questions:

- **Open an issue** on GitHub with the "question" label
- **Check existing issues** - your question may already be answered
- **Read the documentation** - README.md and code comments
- **Review the code** - the codebase is well-structured and documented

## Recognition

Contributors who submit accepted pull requests will be recognized in the project. We appreciate your contributions!

## License

By contributing to this project, you agree that your contributions will be licensed under the same license as the project (see LICENSE file).

---

Thank you for contributing to Azure Retail Prices Exporter! 🎉
