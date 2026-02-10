# GitHub Copilot Instructions for azureretailprices-exporter

> 📚 **For Copilot Coding Agent**: This file contains instructions for GitHub Copilot when working on this repository. Follow these guidelines to ensure high-quality contributions that align with project standards.

## Project Overview

This is a **modern Python project** that retrieves Azure Retail Prices from the official REST API, supports API response pagination, and converts results to JSON and CSV formats with automated daily exports.

**Key characteristics:**
- Python 3.10+ with modern type hints and syntax
- Production-ready with comprehensive testing, linting, and CI/CD
- Developer-friendly with VS Code integration and uv dependency management
- Automated daily price exports via GitHub Actions

### What You Should Know

- This project values **code quality** and **maintainability** over speed of delivery
- All changes require **comprehensive testing** and must pass **CI/CD checks**
- **Documentation** should be updated alongside code changes
- **Type safety** is important - use type hints for all new code
- The project follows **Python best practices** and modern conventions

## Code Style and Quality Standards

### Python Version and Syntax
- **Python 3.10+** is required
- Use **modern union syntax**: `str | None` instead of `Optional[str]`
- Use **type hints** for all function parameters and return values
- Use **f-strings** for string formatting
- Follow **PEP 8** conventions

### Code Formatting
- **Black** is the code formatter (line-length: 88)
- Format code with: `uv run black api/ export_prices_*.py`
- All code must pass Black formatting checks

### Linting
- **Ruff** is the linter (replaces flake8, isort, pyupgrade)
- Run linting with: `uv run ruff check .`
- Auto-fix issues with: `uv run ruff check --fix .`
- Ruff rules enabled: pycodestyle (E/W), pyflakes (F), isort (I), flake8-bugbear (B), flake8-comprehensions (C4), pyupgrade (UP)
- Maximum complexity: 10 (McCabe)

### Type Checking
- **Pyright** is used for type checking (optional but recommended)
- Run with: `uv run pyright`
- Target version: Python 3.10

### Logging
- Use **structured logging** with Python's logging module
- Logger instance: `logger = logging.getLogger(__name__)`
- Include appropriate log levels (DEBUG, INFO, WARNING, ERROR)

### Error Handling
- Implement **comprehensive error handling**
- Use specific exception types
- Provide informative error messages
- Handle API timeouts and network errors gracefully

## Project Structure

```
azureretailprices-exporter/
├── api/
│   ├── azureapi.py          # Main API client
│   └── tests/               # Unit tests
│       └── test_azureapi.py
├── export_*.py              # Example export scripts
├── pyproject.toml           # Project dependencies and config
├── uv.lock                  # Locked dependency versions
└── .vscode/                 # VS Code configuration
```

## Dependencies

### Production Dependencies
- **pandas** - Data manipulation and CSV export
- **requests** - HTTP library for API calls
- **requests-cache** - Caching requests to the API (1-day default)
- **enlighten** - Progress bars and status display
- **pyarrow** - Efficient data processing
- **numpy** - Numerical computing support

### Development Dependencies
- **pytest** - Testing framework
- **black** - Code formatter
- **ruff** - Linter
- **pyright** - Type checker (added as needed)

### Managing Dependencies
- Add production dependency: `uv add package-name`
- Add dev dependency: `uv add --dev package-name`
- Install all dependencies: `uv sync`
- Use `uv run <cmd>` for execution (no activation required)

## Testing

### Framework
- Use **pytest** for all tests
- Test files should be in `api/tests/` directory
- Test files should follow the pattern `test_*.py`
- Run tests with: `uv run pytest`

### Coverage
- Generate coverage with: `uv run pytest --cov=api --cov-report=xml --cov-report=term-missing`
- Aim for high test coverage on core functionality

### Testing Best Practices
- Write unit tests for all new functions
- Mock external API calls in tests
- Test error handling and edge cases
- Use descriptive test names

## Configuration

### Environment Variables
- `AZURE_PRICE_API_VERSION` - API version (default: "2023-01-01-preview")
- `CACHE_EXPIRE_DAYS` - Cache expiration in days (default: 1)
- `REQUEST_TIMEOUT` - Request timeout in seconds (default: 30)

### API Integration
- Base URL: Azure Retail Prices API
- Supports pagination via `nextLink`
- Implements request caching with `requests_cache`
- Handles timeouts and retries

## VS Code Integration

The project includes comprehensive VS Code configuration:
- **Python interpreter** automatically configured for uv virtual environment
- **Debug configurations** for running export scripts
- **Tasks** for common operations (dependency management, testing, formatting, linting)
- **Extensions** recommendations: Black, Ruff, Pylance

### Auto-formatting on Save
- Files are automatically formatted with Black on save
- Real-time linting with Ruff
- Code actions on save (organize imports, fix issues)

## Continuous Integration

### CI/CD Workflows
All workflows are in `.github/workflows/`:

1. **ci.yml** - Automated testing on Python 3.10, 3.11, and 3.12
2. **quality.yml** - Code quality checks (Ruff, Black, Pyright, coverage)
3. **codeql-analysis.yml** - Security scanning with CodeQL
4. **export-prices.yml** - Automated daily price exports at 6 AM UTC

### Contributing Requirements
Before submitting a pull request, ensure code passes all checks:
```console
uv run pytest                    # Run tests
uv run ruff check .              # Check linting
uv run black --check .           # Check formatting
uv run pyright                   # Type checking (optional)
```

### Branch Strategy
- Main branches: `main`, `dev`
- CI runs on all pushes and pull requests to these branches

## Code Patterns and Examples

### Function Signatures
```python
def get_price_data(
    currency_code: str, 
    results_filter: str = "", 
    max_pages: int = 9999999
) -> list[dict[str, Any]]:
    """Download price data from the Azure Retail Price API
    
    Args:
        currency_code: Price currency (e.g., 'USD', 'EUR')
        results_filter: Filter results string (optional)
        max_pages: Maximum pages to download (default: 9999999)
    
    Returns:
        Retail prices as a list of dictionaries
    """
```

### Type Hints
```python
from typing import Any, cast

# Modern union syntax (Python 3.10+)
def process_data(data: dict[str, Any] | None) -> str | None:
    if data is None:
        return None
    return str(data)
```

### Logging
```python
import logging

logger = logging.getLogger(__name__)

logger.info("Starting price data export")
logger.warning("API response cache is expired")
logger.error("Failed to fetch data: %s", error)
```

### Error Handling
```python
try:
    response = session.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
except requests.exceptions.Timeout as e:
    logger.error("Request timeout: %s", e)
    raise
except requests.exceptions.RequestException as e:
    logger.error("Request failed: %s", e)
    raise
```

## Common Development Tasks

### Running Export Scripts
```console
uv run python export_prices_all_usd.py
uv run python export_prices_vm_usd.py
```

### Formatting and Linting
```console
uv run black .                   # Format all files
uv run ruff check --fix .        # Fix linting issues
uv run ruff check .              # Check for issues
```

### Testing
```console
uv run pytest                    # Run all tests
uv run pytest -v                 # Verbose output
uv run pytest api/tests/test_azureapi.py  # Run specific test file
```

## Important Notes for Copilot

1. **Always use modern Python 3.10+ syntax** - No legacy type hints or imports
2. **Type everything** - Use type hints for all parameters and return values
3. **Format with Black** - Code must pass Black formatting (line-length: 88)
4. **Lint with Ruff** - Code must pass all Ruff checks
5. **Write tests** - Include unit tests for new functionality
6. **Use structured logging** - Never use print() for logging in production code
7. **Handle errors gracefully** - Implement proper error handling with specific exceptions
8. **Follow existing patterns** - Check `api/azureapi.py` for code style examples
9. **Document with docstrings** - Use Google-style docstrings for all functions
10. **Environment configuration** - Use environment variables for configuration values

## Security Considerations

- **CodeQL scanning** is enabled - avoid security vulnerabilities
- **Dependabot** monitors dependencies - keep them updated
- **No hardcoded credentials** - use environment variables
- **Validate API responses** - don't trust external data blindly
- **Handle timeouts** - set appropriate timeout values for HTTP requests

## Performance Considerations

- **Caching** - API responses are cached for 1 day by default
- **Pagination** - Handle large result sets efficiently
- **Progress bars** - Use enlighten for long-running operations
- **Data processing** - Use pandas and pyarrow for efficient data manipulation

## Workflow Guidance for Copilot

### When Working on Issues

1. **Understand the task fully** - Read the issue description and all comments before starting
2. **Ask clarifying questions** - If requirements are unclear, ask for clarification in comments
3. **Start small** - Begin with simpler changes and build incrementally
4. **Break down complex tasks** - For large features, suggest breaking into smaller sub-issues

### Pull Request Best Practices

1. **Keep PRs focused** - One logical change per PR
2. **Write clear descriptions** - Explain what changed and why
3. **Reference related issues** - Use "Fixes #123" or "Relates to #456" syntax
4. **Ensure all CI checks pass** - Don't submit until tests, linting, and formatting pass
5. **Self-review your changes** - Check the diff before submitting
6. **Respond to feedback promptly** - Address review comments in a timely manner

### Types of Changes

#### Bug Fixes
- Write or update tests that reproduce the bug
- Fix the minimal code needed to resolve the issue
- Verify the fix doesn't break existing functionality
- Update documentation if the bug was in documented behavior

#### New Features
- Discuss the approach before implementing (in issue comments)
- Write tests for all new functionality
- Update documentation and examples
- Consider backward compatibility
- Ensure performance impact is acceptable

#### Documentation Updates
- Keep technical accuracy as top priority
- Maintain consistent formatting and style
- Update code examples to match current API
- Check for broken links or outdated references

#### Refactoring
- Ensure behavior doesn't change (unless fixing bugs)
- Maintain or improve test coverage
- Update related documentation
- Use linting and type checking to catch issues

### Verification Steps Before Submitting

Before marking work as complete, verify:

1. ✅ All tests pass: `uv run pytest`
2. ✅ Code is properly formatted: `uv run black --check .`
3. ✅ No linting issues: `uv run ruff check .`
4. ✅ Type checking passes (if applicable): `uv run pyright`
5. ✅ Manual testing completed for changed functionality
6. ✅ Documentation updated (if needed)
7. ✅ No unintended changes (review git diff)
8. ✅ Commit messages are clear and descriptive

### Communication Guidelines

- **Be professional and respectful** in all communications
- **Provide context** when asking questions or requesting reviews
- **Acknowledge feedback** even if you disagree (explain your reasoning)
- **Update issue comments** to keep stakeholders informed of progress
- **Report blockers early** if you encounter obstacles
- **Thank reviewers** for their time and feedback

### Common Pitfalls to Avoid

1. ❌ Don't modify unrelated code or files
2. ❌ Don't skip writing tests for new code
3. ❌ Don't ignore linting or formatting warnings
4. ❌ Don't hardcode values that should be configurable
5. ❌ Don't use print() statements for logging
6. ❌ Don't commit commented-out code
7. ❌ Don't make breaking changes without discussion
8. ❌ Don't ignore error handling for external calls
9. ❌ Don't commit generated files (check `.gitignore`)
10. ❌ Don't commit cache files (`azure_cache.sqlite`)
11. ❌ Don't commit CSV export files (unless they're test fixtures)
12. ❌ Don't commit virtual environment files (`.venv/`, `venv/`)

## Task Prioritization

When working on multiple issues or feedback items:

1. **Critical bugs** - Fix immediately
2. **CI/CD failures** - Address before new features
3. **Security vulnerabilities** - Take precedence over features
4. **Review feedback** - Respond before starting new work
5. **New features** - Work on after stability and quality issues resolved
6. **Optimizations** - Consider only when performance issues are documented

## Quick Reference - Essential Commands

### Setup and Installation
```bash
uv sync                     # Install all dependencies
# Use `uv run <cmd>` for execution (no activation required)
```

### Running Tests and Quality Checks
```bash
# Run all quality checks (do this before submitting PR)
uv run pytest                  # Tests
uv run black --check .         # Formatting check
uv run ruff check .            # Linting check
uv run pyright                 # Type checking (optional)

# Auto-fix issues
uv run black .                 # Format code
uv run ruff check --fix .      # Fix auto-fixable linting issues
```

### Running Export Scripts
```bash
uv run python export_prices_all_usd.py
uv run python export_prices_vm_usd.py
```

### Managing Dependencies
```bash
uv add package-name              # Add production dependency
uv add --dev package-name  # Add development dependency
uv lock --upgrade                 # Update dependencies
uv pip list                       # List installed packages
```

### Git Workflow
```bash
git status                          # Check status
git diff                            # See changes
git add .                           # Stage changes
git commit -m "descriptive message" # Commit changes
git push                            # Push to remote
```

## GitHub Copilot Features to Use

When working with this repository, leverage these Copilot features:

### In Pull Requests
- Use `/tests` to generate test cases for new functionality
- Use `/fix` to address review feedback and failing tests
- Use `/review` to get code review suggestions before submitting

### In Issues
- Use `/plan` to break down complex tasks into steps
- Ask clarifying questions in comments to better understand requirements

### In Code Editor (VS Code)
- Use inline suggestions for implementing functions following project patterns
- Use chat to ask questions about the codebase structure
- Use "Explain this code" for understanding existing implementations

---

**Remember**: The goal is to write **clean, tested, and maintainable code** that follows project conventions. When in doubt, check existing code in `api/azureapi.py` for examples, or ask for clarification!
