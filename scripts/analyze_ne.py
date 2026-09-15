"""Run directly from a source checkout, without installing the package."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wake_ne_analysis.cli import analysis_main

if __name__ == "__main__":
    analysis_main()
