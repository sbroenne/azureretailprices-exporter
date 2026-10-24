"""Test release publication without invoking GitHub or changing real releases."""

import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

import publish_releases


@pytest.fixture
def exports(tmp_path: Path) -> tuple[str, str]:
    prices = tmp_path / "prices.csv"
    fx = tmp_path / "fx.csv"
    prices.write_text("type,retailPrice\nConsumption,0.096\n", encoding="utf-8")
    fx.write_text("currency,fxRate\nEUR,0.9\n", encoding="utf-8")
    return str(prices), str(fx)


def response(
    status: int = 0, error: str = "", draft: bool = False
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        ["gh"],
        status,
        stdout='{"draft": true}' if draft else '{"draft": false}',
        stderr=error,
    )


def missing() -> subprocess.CompletedProcess[str]:
    return response(1, "gh: Not Found (HTTP 404)")


def publish(exports: tuple[str, str]) -> None:
    publish_releases.publish_releases(
        "owner/repo", "2026-10-24", exports[0], exports[1], 1, 1
    )


def commands(run: Mock) -> list[list[str]]:
    return [call.args[0] for call in run.call_args_list]


def test_new_releases_are_created(exports: tuple[str, str]) -> None:
    with patch.object(
        publish_releases.subprocess,
        "run",
        side_effect=[
            missing(),
            response(),
            response(),
            missing(),
            response(),
            response(),
        ],
    ) as run:
        publish(exports)
    calls = commands(run)
    assert calls[1][:4] == ["gh", "release", "create", "prices-2026-10-24"]
    assert calls[4][:4] == ["gh", "release", "create", "latest"]
    assert "--draft" in calls[1] and "--draft" in calls[4]
    assert "--draft=false" in calls[2] and "--draft=false" in calls[5]
    assert all("delete" not in call for call in calls)


def test_rerun_preserves_archive_and_updates_latest(
    exports: tuple[str, str],
) -> None:
    with patch.object(
        publish_releases.subprocess, "run", return_value=response()
    ) as run:
        publish(exports)
    calls = commands(run)
    assert len(calls) == 4
    assert calls[0] == ["gh", "api", "repos/owner/repo/releases/tags/prices-2026-10-24"]
    assert calls[2][:4] == ["gh", "release", "upload", "latest"]
    assert "--clobber" in calls[2]
    assert calls[3][:4] == ["gh", "release", "edit", "latest"]
    assert all("create" not in call and "delete" not in call for call in calls)


def test_retry_recovers_after_latest_creation_failed(
    exports: tuple[str, str],
) -> None:
    failure = subprocess.CalledProcessError(1, ["gh", "release", "create", "latest"])
    with patch.object(
        publish_releases.subprocess,
        "run",
        side_effect=[
            missing(),
            response(),
            response(),
            missing(),
            failure,
            response(),
            response(draft=True),
            response(),
            response(),
        ],
    ) as run:
        with pytest.raises(subprocess.CalledProcessError):
            publish(exports)
        publish(exports)
    calls = commands(run)
    assert (
        sum(
            call[:4] == ["gh", "release", "create", "prices-2026-10-24"]
            for call in calls
        )
        == 1
    )
    assert sum(call[:4] == ["gh", "release", "create", "latest"] for call in calls) == 1
    assert calls[-2][:4] == ["gh", "release", "upload", "latest"]
    assert "--draft=false" in calls[-1]
    assert all("delete" not in call for call in calls)


def test_rerun_completes_unpublished_dated_draft(
    exports: tuple[str, str],
) -> None:
    with patch.object(
        publish_releases.subprocess,
        "run",
        side_effect=[
            response(draft=True),
            response(),
            response(),
            response(),
            response(),
            response(),
        ],
    ) as run:
        publish(exports)
    calls = commands(run)
    assert calls[1][:4] == ["gh", "release", "upload", "prices-2026-10-24"]
    assert calls[2][:4] == ["gh", "release", "edit", "prices-2026-10-24"]
    assert "--draft=false" in calls[2]
    assert all("create" not in call and "delete" not in call for call in calls)


@pytest.mark.parametrize(
    "error",
    ["gh: Forbidden (HTTP 403)", "gh: Bad credentials (HTTP 401)", "network failed"],
)
def test_lookup_errors_do_not_trigger_creation(
    exports: tuple[str, str], error: str
) -> None:
    with (
        patch.object(
            publish_releases.subprocess, "run", return_value=response(1, error)
        ) as run,
        pytest.raises(subprocess.CalledProcessError),
    ):
        publish(exports)
    assert len(commands(run)) == 1


@pytest.mark.parametrize("body", ["not JSON", "[]", '{"draft": null}'])
def test_invalid_lookup_response_stops_publication(
    exports: tuple[str, str], body: str
) -> None:
    result = subprocess.CompletedProcess(["gh"], 0, stdout=body, stderr="")
    with (
        patch.object(publish_releases.subprocess, "run", return_value=result) as run,
        pytest.raises(ValueError),
    ):
        publish(exports)
    assert len(commands(run)) == 1


def test_failed_draft_creation_does_not_publish(
    exports: tuple[str, str],
) -> None:
    with (
        patch.object(
            publish_releases.subprocess,
            "run",
            side_effect=[
                missing(),
                subprocess.CalledProcessError(1, ["gh", "release", "create"]),
            ],
        ) as run,
        pytest.raises(subprocess.CalledProcessError),
    ):
        publish(exports)
    assert len(commands(run)) == 2
    assert all("edit" not in call and "delete" not in call for call in commands(run))


def test_upload_failure_never_deletes_latest(exports: tuple[str, str]) -> None:
    with (
        patch.object(
            publish_releases.subprocess,
            "run",
            side_effect=[
                response(),
                response(),
                subprocess.CalledProcessError(1, ["gh", "release", "upload"]),
            ],
        ) as run,
        pytest.raises(subprocess.CalledProcessError),
    ):
        publish(exports)
    assert commands(run)[-1][:4] == ["gh", "release", "upload", "latest"]
    assert all("delete" not in call for call in commands(run))


@pytest.mark.parametrize("price_count, fx_count", [(0, 1), (1, 0), (-1, 1)])
def test_empty_exports_stop_before_github(
    exports: tuple[str, str], price_count: int, fx_count: int
) -> None:
    with (
        patch.object(publish_releases.subprocess, "run") as run,
        pytest.raises(ValueError, match="empty"),
    ):
        publish_releases.publish_releases(
            "owner/repo", "2026-10-24", *exports, price_count, fx_count
        )
    run.assert_not_called()


def test_missing_file_stops_before_github(tmp_path: Path) -> None:
    with (
        patch.object(publish_releases.subprocess, "run") as run,
        pytest.raises(ValueError, match="does not exist"),
    ):
        publish_releases.publish_releases(
            "owner/repo",
            "2026-10-24",
            str(tmp_path / "missing.csv"),
            str(tmp_path / "fx.csv"),
            1,
            1,
        )
    run.assert_not_called()


def test_publication_cli_passes_workflow_arguments(
    exports: tuple[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "publish_releases.py",
            "--repo",
            "owner/repo",
            "--date",
            "2026-10-24",
            "--prices",
            exports[0],
            "--fx-rates",
            exports[1],
            "--price-count",
            "1",
            "--fx-count",
            "1",
        ],
    )
    with patch.object(publish_releases, "publish_releases") as publish_mock:
        publish_releases.main()
    publish_mock.assert_called_once_with("owner/repo", "2026-10-24", *exports, 1, 1)
