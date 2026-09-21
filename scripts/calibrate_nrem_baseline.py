"""Calibrate an experimental NREM-baseline Active-Wake rule to graph-cluster targets.

This command never changes source MAT files or their saved sleep_scores.  It writes
only auditable experimental predictions for the already sampled three-cluster rows.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wake_ne_analysis.nrem_baseline import NremBaselineConfig, calibrate_to_cluster_targets


def _grid(start: float, stop: float, step: float) -> np.ndarray:
    if not np.isfinite([start, stop, step]).all() or start < 0 or stop < start or step <= 0:
        raise ValueError("Multiplier grid requires 0 <= start <= stop and a positive finite step.")
    return np.round(np.arange(start, stop + step / 2, step), 10)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--clustered-points", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--target-clusters", type=int, nargs="+", required=True)
    parser.add_argument("--multiplier-min", type=float, default=0.0)
    parser.add_argument("--multiplier-max", type=float, default=32.0)
    parser.add_argument("--multiplier-step", type=float, default=0.25)
    parser.add_argument("--nrem-baseline-percentile", type=float, default=75.0)
    parser.add_argument("--min-duration-seconds", type=float, default=1.0)
    parser.add_argument("--gap-tolerance-seconds", type=float, default=0.5)
    parser.add_argument("--rms-window-seconds", type=float, default=0.5)
    args = parser.parse_args(argv)
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        raise ValueError("Output directory must be new or empty.")
    config = NremBaselineConfig(
        nrem_baseline_percentile=args.nrem_baseline_percentile,
        min_duration_seconds=args.min_duration_seconds,
        gap_tolerance_seconds=args.gap_tolerance_seconds,
        rms_window_seconds=args.rms_window_seconds,
    )
    multipliers = _grid(args.multiplier_min, args.multiplier_max, args.multiplier_step)
    points = pd.read_csv(args.clustered_points)
    print(f"Evaluating {len(multipliers)} NREM-baseline multipliers against {len(points):,} sampled seconds...", flush=True)
    summary, per_recording, predictions, selection = calibrate_to_cluster_targets(
        args.input_dir, points, tuple(sorted(set(args.target_clusters))), multipliers, config
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.output_dir / "candidate_summary.csv", index=False)
    per_recording.to_csv(args.output_dir / "selected_multiplier_by_recording.csv", index=False)
    predictions.to_csv(args.output_dir / "selected_multiplier_predictions.csv", index=False)
    selection.update(
        {
            "input_dir": str(args.input_dir.resolve()),
            "clustered_points": str(args.clustered_points.resolve()),
            "multiplier_grid": multipliers.tolist(),
        }
    )
    (args.output_dir / "selection.json").write_text(json.dumps(selection, indent=2), encoding="utf-8")
    best = selection["selected_summary"]
    print(
        "Selected multiplier "
        f"{selection['selected_multiplier']:g}: macro target-recording F1 "
        f"{best['macro_target_recording_f1']:.3f}; global precision {best['precision']:.3f}; "
        f"global recall {best['recall']:.3f}."
    )


if __name__ == "__main__":
    main()
