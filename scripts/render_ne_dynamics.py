"""Render interactive NE dynamics figures, with optional static PNG output."""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wake_ne_analysis.dynamics_plots import render_results


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=Path("results/ne_dynamics_v2_pooled"))
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--png", action="store_true", help="Also render PNG using Plotly/Kaleido.")
    args = parser.parse_args(argv)
    output = args.output_dir or args.results_dir / "figures"
    render_results(args.results_dir, output, png=args.png)
    print(f"Figures: {output}")


if __name__ == "__main__":
    main()
