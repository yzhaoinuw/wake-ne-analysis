"""Extract four NE dynamics features and compare all pooled High/Low seconds."""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wake_ne_analysis.dynamics_workflow import run_analysis


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=Path("data"))
    parser.add_argument("--feature-dir", type=Path, default=Path("data/derived_features/ne_dynamics_v2_pooled"))
    parser.add_argument("--results-dir", type=Path, default=Path("results/ne_dynamics_v2_pooled"))
    parser.add_argument("--metadata", type=Path, help="Optional verified recording_id,mouse_id,condition CSV.")
    args = parser.parse_args(argv)
    results = run_analysis(args.input_dir, args.feature_dir, args.results_dir,
                           metadata_path=args.metadata)
    print(results[["feature", "n_high", "n_low", "median_high_minus_low", "rank_biserial", "p_value", "p_holm"]].to_string(index=False))
    print(f"Report: {args.results_dir / 'report.md'}")


if __name__ == "__main__":
    main()
