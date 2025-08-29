"""
Pytest configuration file for the tests.

This file contains shared fixtures and configuration for all tests.
"""

import pytest
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def project_root_path():
    """Return the project root path."""
    return project_root


@pytest.fixture(scope="session")
def etl_path():
    """Return the ETL module path."""
    return project_root / "etl"
