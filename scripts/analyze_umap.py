"""Create the first-pass joint EEG + EMG + NE UMAP from every MAT file in a directory."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wake_ne_analysis.umap import UmapConfig, write_recording_feature_archives, write_umap_analysis


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--results-dir", "--output", dest="results_dir", type=Path, required=True)
    parser.add_argument("--figure", type=Path)
    parser.add_argument("--max-points-per-label-per-recording", type=int, default=10)
    parser.add_argument("--n-neighbors", type=int, default=30)
    parser.add_argument("--n-epochs", type=int, default=50)
    parser.add_argument(
        "--features-only",
        action="store_true",
        help="Write one compressed NumPy feature archive per MAT file without importing or fitting UMAP.",
    )
    args = parser.parse_args(argv)
    print("Extracting per-second EEG, EMG, and NE features...", flush=True)
    config = UmapConfig(
        max_points_per_label_per_recording=args.max_points_per_label_per_recording,
        n_neighbors=args.n_neighbors,
        n_epochs=args.n_epochs,
    )
    if args.features_only:
        archives = write_recording_feature_archives(args.input_dir, args.results_dir, config)
        print(f"Wrote feature archives for {len(archives):,} MAT files to {args.results_dir}")
    else:
        points = write_umap_analysis(args.input_dir, args.results_dir, config, args.figure)
        print(f"Wrote {len(points):,} sampled UMAP points to {args.results_dir}")


if __name__ == "__main__":
    main()
