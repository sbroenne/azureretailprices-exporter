"""Check registry-independent hash locks and cross-version consistency."""

import re
from pathlib import Path

import pytest
from packaging.requirements import Requirement

ROOT = Path(__file__).resolve().parents[2]
LOCKS = ["requirements.txt", "requirements-dev.txt"]


def locked_requirements(filename: str) -> list[Requirement]:
    text = (ROOT / filename).read_text(encoding="utf-8")
    assert "://" not in text
    requirements = []
    for line in re.sub(r"\\\r?\n", "", text).splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        requirement = Requirement(line.split("--hash=", 1)[0].strip())
        pins = list(requirement.specifier)
        assert len(pins) == 1 and pins[0].operator == "=="
        assert "*" not in pins[0].version
        assert requirement.url is None
        assert re.search(r"--hash=sha256:[0-9a-f]{64}(?:\s|$)", line)
        requirements.append(requirement)
    assert requirements
    return requirements


@pytest.mark.parametrize("filename", LOCKS)
def test_dependency_locks_have_exact_versions_and_hashes(filename: str) -> None:
    locked_requirements(filename)
    assert not (ROOT / "uv.lock").exists()


@pytest.mark.parametrize("python", ["3.10", "3.11", "3.12", "3.13", "3.14"])
@pytest.mark.parametrize("system", ["Linux", "Windows"])
def test_runtime_and_dev_locks_use_the_same_versions(python: str, system: str) -> None:
    environment: dict[str, str] = {
        "python_version": python,
        "python_full_version": f"{python}.0",
        "platform_system": system,
        "sys_platform": "win32" if system == "Windows" else "linux",
        "os_name": "nt" if system == "Windows" else "posix",
    }
    selected = []
    for filename in LOCKS:
        versions = {}
        for requirement in locked_requirements(filename):
            if requirement.marker is None or requirement.marker.evaluate(environment):
                assert requirement.name not in versions
                versions[requirement.name] = str(requirement.specifier)
        selected.append(versions)
    runtime, dev = selected
    assert {
        "pandas",
        "numpy",
        "requests",
        "requests-cache",
        "enlighten",
    } <= runtime.keys()
    assert runtime.items() <= dev.items()
    assert {"pytest", "pytest-cov", "ruff", "pyright"} <= dev.keys()
