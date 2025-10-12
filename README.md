# azureretailprices-exporter

Export [Azure Retail Prices](https://docs.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices) as **JSON** and convert them to **CSV** if needed.

- [azureretailprices-exporter](#azureretailprices-exporter)
  - [Functionality](#functionality)
  - [Prerequisites](#prerequisites)
    - [Installation with Poetry (Recommended)](#installation-with-poetry-recommended)
    - [Alternative: Python without Poetry](#alternative-python-without-poetry)
  - [Usage](#usage)
    - [Export all Azure Products in USD](#export-all-azure-products-in-usd)
    - [Export prices for Virtual Machines with filters](#export-prices-for-virtual-machines-with-filters)
    - [Available Export Scripts](#available-export-scripts)
  - [Configuration](#configuration)
  - [Code Layout](#code-layout)
  - [Caching](#caching)
  - [Error Handling](#error-handling)
  - [Development](#development)
    - [VS Code Setup](#vs-code-setup)
    - [Running Tests](#running-tests)
    - [Adding Dependencies](#adding-dependencies)
    - [Code Quality](#code-quality)

## Functionality

A set of **Python scripts** that retrieves results from the Azure Retail Prices REST API, supports _API response pagination_, and converts the results into JSON and CSV files.

The project assumes familiarity with the [Azure Retail Prices API](https://docs.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices) (e.g., setting filter parameters). It uses the Preview API to retrieve savings plan prices.

**Key Features:**

- ✅ **Modern Python practices** - Type hints, logging, error handling
- ✅ **Robust error handling** - Graceful API failure recovery
- ✅ **Configurable timeouts** - Prevents hanging requests
- ✅ **Progress tracking** - Visual progress bars during export
- ✅ **Caching support** - Resumes interrupted exports
- ✅ **Multiple output formats** - JSON and CSV export options

## Prerequisites

The script requires the following dependencies:

- [pandas](https://pandas.pydata.org/) - Data manipulation and CSV export
- [requests](https://docs.python-requests.org/) - HTTP library for API calls
- [requests-cache](https://pypi.org/project/requests-cache/) - Caching requests to the API
- [enlighten](https://pypi.org/project/enlighten/) - Progress bars and status display
- [pyarrow](https://arrow.apache.org/docs/python/) - Efficient data processing
- [numpy](https://numpy.org/) - Numerical computing support

**Python Version:** 3.10+ required

We recommend using **Poetry** for dependency management and virtual environments.

### Installation with Poetry (Recommended)

1. Install [Poetry](https://python-poetry.org/docs/#installation) if you haven't already:

   ```console
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. Install dependencies and create virtual environment:

   ```console
   poetry install
   ```

3. Activate the virtual environment:

   ```console
   poetry shell
   ```

### Alternative: Python without Poetry

If you prefer not to use Poetry, you can install dependencies directly:

```console
pip install pandas requests-cache enlighten pyarrow requests numpy
```

For development dependencies:

```console
pip install pytest black ruff
```

## Usage

Here are examples of how to use the export scripts:

### Export all Azure Products in USD

```console
poetry run python export_prices_all_usd.py
```

This creates the file `prices_USD.csv` with all Azure product prices.

### Export prices for Virtual Machines with filters

```console
poetry run python export_prices_vm_usd.py
```

```console
poetry run python export_prices_with_filter_and_multiple_currencies.py
```

### Available Export Scripts

- `export_prices_all_usd.py` - All products in USD (CSV format)
- `export_prices_all_usd_json.py` - All products in USD (JSON format)
- `export_prices_all_eur.py` - All products in EUR
- `export_prices_vm_usd.py` - Virtual Machines only in USD
- `export_prices_with_filter_and_multiple_currencies.py` - Custom filters with multiple currencies
- `export_prices_all_usd_limit_10_pages.py` - Limited export for testing

## Configuration

The application supports environment variables for configuration:

```bash
# API Configuration
export AZURE_PRICE_API_VERSION="2023-01-01-preview"  # API version to use
export REQUEST_TIMEOUT="30"                           # Request timeout in seconds
export CACHE_EXPIRE_DAYS="1"                         # Cache expiration in days
```

**Default values** are used if environment variables are not set.

## Code Layout

The project structure is organized as follows:

```text
azureretailprices-exporter/
├── api/
│   ├── azureapi.py          # Main API client (modernized)
│   ├── azureapi_modern.py   # Class-based API client example
│   └── tests/               # Unit tests
├── export_*.py              # Example export scripts
├── pyproject.toml           # Poetry dependencies and configuration
├── poetry.lock              # Locked dependency versions
└── .vscode/                 # VS Code configuration
    ├── settings.json        # Python interpreter settings
    ├── launch.json          # Debug configurations
    ├── tasks.json           # Poetry tasks
    └── extensions.json      # Recommended extensions
```

**Core functionality** is in `api/azureapi.py`. The `export_*.py` scripts are examples showing different usage patterns.

## Caching

The script uses [requests-cache](https://pypi.org/project/requests-cache) to temporarily cache API results. This is useful if the script stops unexpectedly and you need to resume later.

**Cache settings:**

- **Duration:** 1 day by default (configurable via `CACHE_EXPIRE_DAYS`)
- **Storage:** SQLite file `azure_cache.sqlite`
- **Clearing:** Delete the cache file to clear cached data

## Error Handling

The modernized codebase includes comprehensive error handling:

- ✅ **HTTP errors** - Graceful handling of API failures with proper status codes
- ✅ **Network timeouts** - Configurable request timeouts (default: 30 seconds)
- ✅ **JSON parsing errors** - Robust handling of malformed API responses
- ✅ **Logging** - Structured logging instead of print statements
- ✅ **Retry logic** - Graceful degradation on temporary failures

**Debugging:** Set logging level to `DEBUG` for detailed troubleshooting information.

## Development

### VS Code Setup

The project includes VS Code configuration for optimal development experience:

- **Python interpreter** automatically configured for Poetry virtual environment
- **Debug configurations** for running export scripts
- **Tasks** for common operations:
  - Poetry dependency management
  - Running tests with pytest
  - Code formatting with Black
  - Linting and fixing with Ruff
- **Extensions** recommendations for Python development (Black, Ruff, Pylance)

### Running Tests

```console
poetry run pytest
```

### Adding Dependencies

```console
poetry add package-name              # Production dependency
poetry add --group dev package-name  # Development dependency
```

### Code Quality

The project uses modern Python development tools for code quality:

- **[Black](https://black.readthedocs.io/)** - Uncompromising code formatter
- **[Ruff](https://docs.astral.sh/ruff/)** - Extremely fast Python linter (replaces flake8, isort, pyupgrade)
- **Type hints** for better IDE support and static analysis
- **Structured logging** for debugging and monitoring
- **Comprehensive error handling** for robustness
- **Environment-based configuration** for flexibility

**Code Formatting:**

```console
poetry run black api/ export_prices_*.py    # Format all Python files
```

**Linting:**

```console
poetry run ruff check .                      # Check for linting issues
poetry run ruff check --fix .                # Auto-fix issues where possible
```

**VS Code Integration:**

- Automatic formatting on save with Black
- Real-time linting with Ruff
- Code actions on save (organize imports, fix issues)

The project follows **Python 3.10+** conventions including modern union syntax (`str | None` instead of `Optional[str]`).
