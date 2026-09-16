"""Run the exploratory zero-referenced, per-recording raw-bout comparison."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wake_ne_analysis.raw_bouts import write_directory_analysis


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True, help="Directory containing MAT files.")
    parser.add_argument("--output", type=Path, required=True, help="New or empty output directory.")
    args = parser.parse_args(argv)
    write_directory_analysis(args.input_dir, args.output)
    print(f"Wrote raw-bout comparison to {args.output}")


if __name__ == "__main__":
    main()
