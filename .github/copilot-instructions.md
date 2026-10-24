# Copilot instructions for azureretailprices-exporter

## Build / Setup
- `uv venv`
- `uv pip sync --require-hashes requirements-dev.txt`
- Runtime-only: `uv pip sync --require-hashes requirements.txt`
- Dependency versions and hashes are in URL-free `requirements*.txt` locks. Keep `managed = false`; do not introduce `uv.lock` or repository index URLs.

## Tests
- `uv run pytest`
- `uv run pytest api/tests/test_azureapi.py::test_name`
- `uv run pytest --cov=api --cov-report=term-missing`

## Lint / Format / Type-check
- `uv run ruff check .`
- `uv run ruff check --fix .`
- `uv run ruff format --check .`
- `uv run ruff format .`
- `uv run pyright`

## High-level architecture
- `api/azureapi.py` is the core API client. It fetches paginated Azure Retail Prices with caching and retry logic, then exposes:
  - `get_price_data(...)` → list[dict] raw items from the API. At Azure's skip limit, restart with complementary adaptive filters, discard partial pages, and retain one global page budget.
  - `get_prices(...)` → DataFrame retaining each parent price and adding separate Savings Plan rows without mutating API records.
  - `calculate_fx_rates(...)` → DataFrame of FX rates matched by SKU ID, region, meter, type, term, tier, and unit. Missing or ambiguous currency results fail rather than returning partial data.
- `export_*.py` scripts are thin wrappers around `api.azureapi` that export CSV/JSON for specific use cases (all prices, VM-only, FX rates, etc.).
- Tests live in `api/tests/` and use pytest to validate API handling, retries, and FX-rate calculations.

## Key conventions
- Use uv for all local runs (`uv run ...`) and Python 3.10+ syntax (modern `str | None` unions).
- Library code uses structured logging (`logger = logging.getLogger(__name__)`); avoid `print()` inside `api/`.
- Configuration is via environment variables in `api/azureapi.py` (e.g., `AZURE_PRICE_API_VERSION`, `REQUEST_TIMEOUT`, `CACHE_EXPIRE_DAYS`, `MAX_RETRIES`, `RETRY_BACKOFF_FACTOR`).
- `requests_cache` writes `azure_cache.sqlite`; export scripts generate `prices_*.csv`/`fxrates_usd.csv`—do not commit these generated files.
