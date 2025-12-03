# azureretailprices-exporter

[![Tests](https://github.com/sbroenne/azureretailprices-exporter/actions/workflows/ci.yml/badge.svg)](https://github.com/sbroenne/azureretailprices-exporter/actions/workflows/ci.yml)
[![Code Quality](https://github.com/sbroenne/azureretailprices-exporter/actions/workflows/quality.yml/badge.svg)](https://github.com/sbroenne/azureretailprices-exporter/actions/workflows/quality.yml)
[![Export Prices](https://github.com/sbroenne/azureretailprices-exporter/actions/workflows/export-prices.yml/badge.svg)](https://github.com/sbroenne/azureretailprices-exporter/actions/workflows/export-prices.yml)
[![CodeQL](https://github.com/sbroenne/azureretailprices-exporter/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/sbroenne/azureretailprices-exporter/actions/workflows/codeql-analysis.yml)

Export [Azure Retail Prices](https://docs.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices) as **JSON** and convert them to **CSV** if needed.

## 🚀 Quick Download - Daily Exports

**Want the latest Azure prices without running the code?**

📥 **[Download Latest CSV](https://github.com/sbroenne/azureretailprices-exporter/releases/tag/latest)** - All Azure retail prices in USD + FX rates, updated daily!

- ✅ **Automated daily exports** at 6 AM UTC
- ✅ **Complete price data** for all Azure services
- ✅ **FX rates** calculated from USD to 16+ currencies
- ✅ **CSV format** ready for Excel, Power BI, or analysis tools
- ✅ **Public access** - no authentication required
- ✅ **Two release types available**:
  - 📅 **Dated releases** (e.g., `prices-2025-10-12`) - Historical snapshots for specific dates
  - 🔄 **Latest release** (`latest`) - Always contains the most current prices (auto-updated daily)

*Perfect for business analysis, cost planning, or research without needing to run the export scripts yourself!*

- [azureretailprices-exporter](#azureretailprices-exporter)
  - [🚀 Quick Download - Daily Exports](#-quick-download---daily-exports)
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
  - [Continuous Integration](#continuous-integration)
    - [🧪 **Automated Testing**](#-automated-testing)
    - [🔍 **Code Quality Enforcement**](#-code-quality-enforcement)
    - [🔒 **Security Scanning**](#-security-scanning)
    - [📊 **Status Badges**](#-status-badges)
    - [🔧 **Contributing Requirements**](#-contributing-requirements)
    - [📝 **Contributing Guidelines**](#-contributing-guidelines)
  - [Automated Exports](#automated-exports)
    - [🔄 **How It Works**](#-how-it-works)
    - [📁 **Release Types Available**](#-release-types-available)
      - [📅 **Dated Releases** (e.g., `prices-2025-10-12`)](#-dated-releases-eg-prices-2025-10-12)
      - [🔄 **Latest Release** (`latest`)](#-latest-release-latest)
    - [🎯 **Download URLs**](#-download-urls)
    - [🎯 **Use Cases**](#-use-cases)
    - [🌟 **Benefits**](#-benefits)
  - [Related Projects](#related-projects)
    - [📊 **Excel MCP Server**](#-excel-mcp-server)

## Functionality

A **modern Python project** that retrieves Azure Retail Prices from the official REST API, supports **API response pagination**, and converts results to JSON and CSV formats with **automated daily exports**.

The project includes both **manual export scripts** for custom use cases and **automated GitHub Actions workflows** that provide daily updated price data to the community.

**Key Features:**

- 🚀 **Automated Daily Exports** - Fresh price data available as GitHub releases
- 💱 **FX Rate Calculation** - Exchange rates calculated from multi-currency price comparisons
- ✅ **Modern Python 3.10+** - Type hints, structured logging, comprehensive error handling
- ✅ **Robust API integration** - Handles pagination, timeouts, and graceful error recovery
- ✅ **Smart caching** - Resumes interrupted exports, 1-day API response caching
- ✅ **Multiple formats** - JSON and CSV output with configurable options
- ✅ **Progress tracking** - Visual progress bars during long exports
- ✅ **Production ready** - Comprehensive testing, linting, and CI/CD pipeline
- ✅ **Developer friendly** - Full VS Code integration, Poetry dependency management

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
- `export_fxrates.py` - **NEW**: Calculate and export FX rates based on USD

### Export FX Rates

The `export_fxrates.py` script calculates foreign exchange rates by comparing Azure retail prices across different currencies:

```console
poetry run python export_fxrates.py
```

This creates the file `fxrates_usd.csv` with calculated exchange rates for multiple currencies.

**How it works:**
- Uses a specific meterId (`5daea80f-04ac-5385-86f0-b263d23becd2`) to ensure consistent price comparison across currencies
- Fetches Azure prices in USD (base currency) and multiple target currencies for this specific meter
- Calculates FX rates by comparing the same product's price in different currencies
- Exports results with currency and exchange rate

**Example output:**
```
currency,fxRate
EUR,0.8523
GBP,0.7421
JPY,110.2341
```

This is useful for:
- Multi-currency cost analysis
- Currency conversion validation
- Historical FX rate tracking
- Budget planning in different regions

## Configuration

The application supports environment variables for configuration:

```bash
# API Configuration
export AZURE_PRICE_API_VERSION="2023-01-01-preview"  # API version to use
export REQUEST_TIMEOUT="30"                           # Request timeout in seconds
export CACHE_EXPIRE_DAYS="1"                         # Cache expiration in days

# Retry Configuration (for handling rate limiting)
export MAX_RETRIES="5"                               # Maximum number of retries for failed requests
export RETRY_BACKOFF_FACTOR="2.0"                    # Exponential backoff multiplier (wait: 2s, 4s, 8s, 16s, 32s)
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
- ✅ **Rate limiting (HTTP 429)** - Automatic retry with exponential backoff using urllib3.Retry
- ✅ **Network timeouts** - Configurable request timeouts (default: 30 seconds)
- ✅ **JSON parsing errors** - Robust handling of malformed API responses
- ✅ **Logging** - Structured logging instead of print statements
- ✅ **Retry logic** - Automatic retries for 429, 500, 502, 503, 504 errors with exponential backoff

**Retry Behavior:**
- Automatically retries failed requests up to 5 times (configurable via `MAX_RETRIES`)
- Uses exponential backoff: 2s, 4s, 8s, 16s, 32s (configurable via `RETRY_BACKOFF_FACTOR`)
- Respects `Retry-After` header from API responses
- Handles temporary server errors and rate limiting gracefully

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

## Continuous Integration

The project uses **GitHub Actions** for automated testing and code quality checks:

### 🧪 **Automated Testing**

- **Matrix Testing**: All tests run on Python 3.10, 3.11, and 3.12
- **Triggers**: Every push and pull request to `main` and `dev` branches
- **Coverage**: Code coverage reports with Codecov integration

### 🔍 **Code Quality Enforcement**

- **Linting**: Ruff checks for code quality and style
- **Formatting**: Black ensures consistent code formatting
- **Type Checking**: Pyright validates type annotations

### 🔒 **Security Scanning**

- **CodeQL**: GitHub's advanced semantic code analysis for security vulnerabilities
- **Dependabot**: Automated dependency vulnerability scanning and updates
- **GitHub Security Advisories**: Integration with the security advisory database

### 📊 **Status Badges**

The badges at the top of this README show the current status of:

- [![Tests](https://github.com/sbroenne/azureretailprices-exporter/actions/workflows/ci.yml/badge.svg)](https://github.com/sbroenne/azureretailprices-exporter/actions/workflows/ci.yml) - Unit test results
- [![Code Quality](https://github.com/sbroenne/azureretailprices-exporter/actions/workflows/quality.yml/badge.svg)](https://github.com/sbroenne/azureretailprices-exporter/actions/workflows/quality.yml) - Linting, formatting, and type checking
- [![CodeQL](https://github.com/sbroenne/azureretailprices-exporter/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/sbroenne/azureretailprices-exporter/actions/workflows/codeql-analysis.yml) - Security vulnerability scanning

### 🔧 **Contributing Requirements**

Before submitting a pull request, ensure your code passes all checks:

```console
# Run all quality checks locally
poetry run pytest                    # Run tests
poetry run ruff check .              # Check linting
poetry run black --check .           # Check formatting
poetry run pyright                   # Type checking (optional)
```

**Tip**: VS Code with the recommended extensions will automatically format and lint your code as you work!

### 📝 **Contributing Guidelines**

We welcome contributions! Please read our [Contributing Guide](CONTRIBUTING.md) for details on:

- Setting up your development environment
- Our development workflow
- Pull request process
- Coding standards and best practices

Also review our [Code of Conduct](CODE_OF_CONDUCT.md) before contributing.

## Automated Exports

This project includes **fully automated daily exports** that make Azure pricing data accessible to everyone without requiring any technical setup.

### 🔄 **How It Works**

- **Daily Schedule**: Exports run automatically at 6 AM UTC every day
- **Manual Trigger**: Can also be triggered manually via GitHub Actions
- **Fresh Data**: Always pulls the latest pricing from Azure's official API
- **Public Access**: Results are published as GitHub releases for easy download

### 📁 **Release Types Available**

Each export creates **two separate releases**:

#### 📅 **Dated Releases** (e.g., `prices-2025-10-12`)

- **Files**: 
  - `azure-retail-prices-usd.csv` - Complete price data
  - `azure-fxrates-usd.csv` - FX rates calculated from USD
- **Purpose**: Permanent historical snapshot for that specific date
- **Use Case**: Historical analysis, trend tracking, archival data
- **URL Pattern**: `https://github.com/sbroenne/azureretailprices-exporter/releases/tag/prices-YYYY-MM-DD`
- **Permanence**: Never overwritten - each day gets its own release

#### 🔄 **Latest Release** (`latest`)

- **Files**: 
  - `azure-retail-prices-usd.csv` - Current price data
  - `azure-fxrates-usd.csv` - Current FX rates
- **Purpose**: Always contains the most current pricing data and FX rates
- **Use Case**: Real-time analysis, automation, current pricing needs
- **URL Pattern**: `https://github.com/sbroenne/azureretailprices-exporter/releases/tag/latest`
- **Permanence**: Updated daily with fresh data (previous data is overwritten)

### 🎯 **Download URLs**

For **automation** and **consistent access**, use these direct download links:

**Price Data:**
- **📅 Historical Data**: `https://github.com/sbroenne/azureretailprices-exporter/releases/download/prices-YYYY-MM-DD/azure-retail-prices-usd.csv`
- **🔄 Latest Data**: `https://github.com/sbroenne/azureretailprices-exporter/releases/download/latest/azure-retail-prices-usd.csv`

**FX Rates:**
- **📅 Historical FX Rates**: `https://github.com/sbroenne/azureretailprices-exporter/releases/download/prices-YYYY-MM-DD/azure-fxrates-usd.csv`
- **🔄 Latest FX Rates**: `https://github.com/sbroenne/azureretailprices-exporter/releases/download/latest/azure-fxrates-usd.csv`

> 💡 **Pro Tip**: Bookmark the **latest** URLs for always-current pricing data and FX rates!

### 🎯 **Use Cases**

- **📊 Business Intelligence**: Import into Power BI, Tableau, or Excel
- **💰 Cost Planning**: Current pricing for budget forecasting
- **💱 Multi-Currency Analysis**: FX rates for international cost comparisons
- **📈 Price Analysis**: Historical trends and price changes over time
- **🤖 Automation**: Reliable data source for automated workflows
- **🔬 Research**: Academic studies on cloud pricing trends

### 🌟 **Benefits**

- ✅ **No setup required** - Just download and use
- ✅ **Always current** - Fresh data daily via the `latest` release
- ✅ **Historical access** - Dated releases for trend analysis
- ✅ **Production ready** - Reliable, tested automation
- ✅ **Community resource** - Open to everyone
- ✅ **Simple URLs** - Consistent naming for automation

> 💡 **Quick Start**: Visit the [releases page](https://github.com/sbroenne/azureretailprices-exporter/releases) and download from either the **latest** release or any **dated** release!

## Related Projects

Check out these related projects for working with Azure pricing data:

### 📊 **Excel MCP Server**

[**Excel MCP Server**](https://sbroenne.github.io/mcp-server-excel/) - AI-powered Excel automation through natural language.

Use the exported Azure pricing CSV files with AI assistants like GitHub Copilot, Claude, or ChatGPT to:

- **Analyze pricing data** - Create PivotTables, charts, and summaries using natural language
- **Build cost reports** - Generate formatted reports with conditional formatting
- **Automate workflows** - Use Power Query to refresh pricing data and calculate costs
- **Compare prices** - Create dashboards for price trend analysis

**Example**: *"Create a PivotTable showing Azure VM prices by region, sorted by cost"*

[![VS Code Extension](https://img.shields.io/visual-studio-marketplace/v/sbroenne.excel-mcp)](https://marketplace.visualstudio.com/items?itemName=sbroenne.excel-mcp)

[Learn more →](https://github.com/sbroenne/mcp-server-excel/)
