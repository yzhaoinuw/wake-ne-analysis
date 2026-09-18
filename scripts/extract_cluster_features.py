"""Write the documented 29-feature per-recording NumPy archives from MAT files."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wake_ne_analysis.cluster_features import FEATURE_SET_NAME, write_expanded_feature_archives


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    archives = write_expanded_feature_archives(args.input_dir, args.output_dir)
    print(f"Wrote {len(archives)} {FEATURE_SET_NAME} archives to {args.output_dir}")


if __name__ == "__main__":
    main()
