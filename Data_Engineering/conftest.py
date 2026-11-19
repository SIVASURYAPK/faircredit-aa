# conftest.py — placed at the project root.
# pytest automatically loads this file, and having it here tells pytest
# (and Python) to treat the project root as the base for imports.
# This means `from features.build_features import ...` works in all test files
# without any sys.path hacks.

import os
import pytest
from generator import config


@pytest.fixture
def tmp_test_dir(tmp_path):
    """Temporary directory for test artifacts, isolated from production data."""
    test_dir = tmp_path / "test_run"
    test_dir.mkdir(parents=True, exist_ok=True)
    return str(test_dir)


@pytest.fixture
def tmp_db_path(tmp_path):
    """Temporary SQLite database path for testing generator functions."""
    return str(tmp_path / "test_credit.db")


@pytest.fixture
def tmp_csv_dir(tmp_path):
    """Temporary CSV output directory for testing generator functions."""
    csv_dir = tmp_path / "raw"
    csv_dir.mkdir(parents=True, exist_ok=True)
    return str(csv_dir)


@pytest.fixture(autouse=True)
def guard_production_data():
    """
    Global test safeguard: verifies that tests do not write to production data paths.
    Tests/smoke runs must use tmp_path or tests/tmp/ instead.
    """
    yield

