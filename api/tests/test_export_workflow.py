"""Exercise the workflow's price validation without making an export."""

import re
from pathlib import Path
from textwrap import dedent
from typing import Any
from unittest.mock import patch

import pandas as pd
import pytest

from api import azureapi


def price_export_code() -> str:
    workflow = (
        Path(__file__).resolve().parents[2]
        / ".github"
        / "workflows"
        / "export-prices.yml"
    ).read_text(encoding="utf-8")
    match = re.search(
        r'export_df = azureapi.get_prices\(\'USD\'\)(.*?)\n        "',
        workflow,
        re.DOTALL,
    )
    assert match is not None
    return "import api.azureapi as azureapi\nimport os\n" + dedent(
        "        export_df = azureapi.get_prices('USD')" + match.group(1)
    )


@pytest.mark.parametrize("failure", ["empty", "missing-fields", "wrong-currency"])
def test_workflow_rejects_invalid_prices_without_writing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    price_record: dict[str, Any],
    failure: str,
) -> None:
    invalid = {
        "empty": pd.DataFrame(),
        "missing-fields": pd.DataFrame({"retailPrice": [0.096]}),
        "wrong-currency": pd.DataFrame([{**price_record, "currencyCode": "EUR"}]),
    }[failure]
    monkeypatch.chdir(tmp_path)
    env_file = tmp_path / "github-env"
    monkeypatch.setenv("GITHUB_ENV", str(env_file))
    output = tmp_path / "azure-retail-prices-usd.csv"
    output.write_text("previous valid data", encoding="utf-8")
    with (
        patch.object(azureapi, "get_prices", return_value=invalid),
        pytest.raises(ValueError),
    ):
        exec(compile(price_export_code(), "<workflow-price-export>", "exec"), {})
    assert output.read_text(encoding="utf-8") == "previous valid data"
    assert not env_file.exists()


def test_workflow_exports_valid_prices_and_reports_count(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, price_record: dict[str, Any]
) -> None:
    monkeypatch.chdir(tmp_path)
    env_file = tmp_path / "github-env"
    monkeypatch.setenv("GITHUB_ENV", str(env_file))
    expected = pd.DataFrame([price_record])
    with patch.object(azureapi, "get_prices", return_value=expected):
        exec(compile(price_export_code(), "<workflow-price-export>", "exec"), {})
    pd.testing.assert_frame_equal(
        pd.read_csv(tmp_path / "azure-retail-prices-usd.csv"), expected
    )
    assert env_file.read_text(encoding="utf-8") == (
        "FILENAME=azure-retail-prices-usd.csv\nEXPORT_COUNT=1\n"
    )
