from pathlib import Path
import pytest


FIXTURE_DIR = Path(__file__).parent / "data"


@pytest.fixture
def test_csv() -> Path:
    return FIXTURE_DIR / "test.csv"


@pytest.fixture
def test_csv_path(test_csv) -> str:
    return str(test_csv)
