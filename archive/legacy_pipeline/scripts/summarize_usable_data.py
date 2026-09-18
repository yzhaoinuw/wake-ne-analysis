"""Inspect data coverage separately from the NE metric pipeline."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wake_ne_analysis.cli import validation_main

if __name__ == "__main__":
    raise SystemExit(validation_main())
