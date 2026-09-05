"""Smoke tests for the EbolaLens package."""

import subprocess
import sys

import ebolalens


def test_package_version() -> None:
    assert ebolalens.__version__ == "0.0.0"


def test_module_reports_version() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "ebolalens", "--version"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.strip() == "ebolalens 0.0.0"
    assert result.stderr == ""
