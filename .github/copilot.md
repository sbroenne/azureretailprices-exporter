# GitHub Copilot Instructions for azureretailprices-exporter

## Project Overview

This is a **modern Python project** that retrieves Azure Retail Prices from the official REST API, supports API response pagination, and converts results to JSON and CSV formats with automated daily exports.

**Key characteristics:**
- Python 3.10+ with modern type hints and syntax
- Production-ready with comprehensive testing, linting, and CI/CD
- Developer-friendly with VS Code integration and Poetry dependency management
- Automated daily price exports via GitHub Actions

## Code Style and Quality Standards

### Python Version and Syntax
- **Python 3.10+** is required
- Use **modern union syntax**: `str | None` instead of `Optional[str]`
- Use **type hints** for all function parameters and return values
- Use **f-strings** for string formatting
- Follow **PEP 8** conventions

### Code Formatting
- **Black** is the code formatter (line-length: 88)
- Format code with: `poetry run black api/ export_prices_*.py`
- All code must pass Black formatting checks

### Linting
- **Ruff** is the linter (replaces flake8, isort, pyupgrade)
- Run linting with: `poetry run ruff check .`
- Auto-fix issues with: `poetry run ruff check --fix .`
- Ruff rules enabled: pycodestyle (E/W), pyflakes (F), isort (I), flake8-bugbear (B), flake8-comprehensions (C4), pyupgrade (UP)
- Maximum complexity: 10 (McCabe)

### Type Checking
- **Pyright** is used for type checking (optional but recommended)
- Run with: `poetry run pyright`
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
├── pyproject.toml           # Poetry dependencies and config
├── poetry.lock              # Locked dependency versions
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
- Add production dependency: `poetry add package-name`
- Add dev dependency: `poetry add --group dev package-name`
- Install all dependencies: `poetry install`
- Activate environment: `poetry shell`

## Testing

### Framework
- Use **pytest** for all tests
- Test files should be in `api/tests/` directory
- Test files should follow the pattern `test_*.py`
- Run tests with: `poetry run pytest`

### Coverage
- Generate coverage with: `poetry run pytest --cov=api --cov-report=xml --cov-report=term-missing`
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
- **Python interpreter** automatically configured for Poetry virtual environment
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
poetry run pytest                    # Run tests
poetry run ruff check .              # Check linting
poetry run black --check .           # Check formatting
poetry run pyright                   # Type checking (optional)
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
poetry run python export_prices_all_usd.py
poetry run python export_prices_vm_usd.py
```

### Formatting and Linting
```console
poetry run black .                   # Format all files
poetry run ruff check --fix .        # Fix linting issues
poetry run ruff check .              # Check for issues
```

### Testing
```console
poetry run pytest                    # Run all tests
poetry run pytest -v                 # Verbose output
poetry run pytest api/tests/test_azureapi.py  # Run specific test file
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
