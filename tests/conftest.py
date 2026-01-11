"""Shared test fixtures."""
import pytest
from pathlib import Path
import tempfile
import shutil

@pytest.fixture
def temp_vault():
    """Create a temporary vault directory."""
    vault = tempfile.mkdtemp(prefix="omi_vault_")
    yield Path(vault)
    shutil.rmtree(vault, ignore_errors=True)

@pytest.fixture
def fixtures_dir():
    """Return path to fixtures directory."""
    return Path(__file__).parent.parent / "fixtures"
