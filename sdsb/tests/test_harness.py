import sys
from pathlib import Path


def test_sdsb_dir_is_on_syspath():
    """conftest.py must put the sdsb/ dir on sys.path so tests can import modules."""
    assert any(Path(p).name == "sdsb" for p in sys.path if p)
