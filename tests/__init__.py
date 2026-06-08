"""Test package for unittest discovery.

This keeps `python -m unittest discover` working from a source checkout
without requiring an editable install first.
"""
from pathlib import Path
import sys

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
