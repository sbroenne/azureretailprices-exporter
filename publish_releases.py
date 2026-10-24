"""Publish validated exports without deleting releases or replacing dated archives."""

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


def _get_release(repository: str, tag: str) -> dict[str, Any] | None:
    result = subprocess.run(
        ["gh", "api", f"repos/{repository}/releases/tags/{tag}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        if "(HTTP 404)" in result.stderr:
            return None
        result.check_returncode()
    release = json.loads(result.stdout)
    if not isinstance(release, dict) or not isinstance(release.get("draft"), bool):
        raise ValueError(f"Invalid GitHub release response for {tag}")
    return release


def publish_releases(
    repository: str,
    date: str,
    price_file: str,
    fx_file: str,
    price_count: int,
    fx_count: int,
) -> None:
    """Preserve existing dated releases and create or update latest in place."""
    if price_count <= 0 or fx_count <= 0:
        raise ValueError("Refusing to publish empty exports")
    for filename in (price_file, fx_file):
        if not Path(filename).is_file():
            raise ValueError(f"Export file does not exist: {filename}")

    notes = (
        f"## Azure Retail Prices - {date}\n\n"
        f"- Currency: USD\n- Price records: {price_count}\n"
        f"- FX currencies: {fx_count}\n\n"
        f"Files: {Path(price_file).name} and {Path(fx_file).name}.\n\n"
        "Includes PAYG parents and separate Savings Plan rows. Savings Plan dates "
        "are inherited from parent API records, not independently verified.\n"
        "Older snapshots can omit PAYG rows; current prices cannot backfill them. "
        "See the README's Price Coverage and Savings Plans section.\n"
    )
    for tag, title in (
        (f"prices-{date}", f"Azure Retail Prices - {date}"),
        ("latest", "Azure Retail Prices - Latest"),
    ):
        release = _get_release(repository, tag)
        if release is not None:
            if tag != "latest" and not release["draft"]:
                continue
            subprocess.run(
                [
                    "gh",
                    "release",
                    "upload",
                    tag,
                    price_file,
                    fx_file,
                    "--repo",
                    repository,
                    "--clobber",
                ],
                check=True,
            )
        else:
            subprocess.run(
                [
                    "gh",
                    "release",
                    "create",
                    tag,
                    price_file,
                    fx_file,
                    "--repo",
                    repository,
                    "--title",
                    title,
                    "--notes",
                    notes,
                    "--draft",
                ],
                check=True,
            )
        subprocess.run(
            [
                "gh",
                "release",
                "edit",
                tag,
                "--repo",
                repository,
                "--title",
                title,
                "--notes",
                notes,
                "--draft=false",
            ],
            check=True,
        )


def main() -> None:
    """Publish export files named by the workflow."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--prices", required=True)
    parser.add_argument("--fx-rates", required=True)
    parser.add_argument("--price-count", required=True, type=int)
    parser.add_argument("--fx-count", required=True, type=int)
    args = parser.parse_args()
    publish_releases(
        args.repo,
        args.date,
        args.prices,
        args.fx_rates,
        args.price_count,
        args.fx_count,
    )


if __name__ == "__main__":
    main()
