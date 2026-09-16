"""Separate analysis and usable-data commands; new output directory per run."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd
import scipy
from . import __version__
from .aggregation import aggregate_subjects, pooled_spectra
from .config import AnalysisConfig
from .io import read_manifest
from .pipeline import analyze_files
from .validation import validate_file


def _parser(description):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("manifest", type=Path, help="CSV: mouse_id,mat_path, optional recording_id")
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="New directory; existing outputs are never overwritten",
    )
    return parser


def _write_tables(output, tables, metadata):
    output.mkdir(parents=True, exist_ok=False)
    for name, table in tables.items():
        table.to_csv(output / f"{name}.csv", index=False)
    (output / "run.json").write_text(
        json.dumps(metadata, indent=2, allow_nan=False), encoding="utf-8"
    )


def _metadata(manifest, rows, config=None):
    return {
        "package_version": __version__,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "pandas": pd.__version__,
        "manifest": str(manifest.resolve()),
        "config": config.to_dict() if config else None,
        "inputs": [
            {
                **{k: str(v) for k, v in row.items()},
                "size_bytes": row["path"].stat().st_size if row["path"].exists() else None,
                "mtime_ns": row["path"].stat().st_mtime_ns if row["path"].exists() else None,
            }
            for row in rows
        ],
    }


def analysis_main(argv=None):
    parser = _parser("Analyze NE transients and optional spectra, then pool by mouse.")
    parser.add_argument(
        "--config", type=Path, help="JSON configuration; without it spectra stay unconfigured"
    )
    args = parser.parse_args(argv)
    try:
        if args.output.exists():
            raise ValueError("Output directory already exists. Choose a new run directory.")
        rows = read_manifest(args.manifest)
        config = AnalysisConfig.from_json(args.config) if args.config else AnalysisConfig()
        results = analyze_files(rows, config)
        single = []
        for result in results:
            summary = aggregate_subjects([result])
            summary.insert(1, "recording_id", result.recording_id)
            single.append(summary)
        tables = {
            "subjects": aggregate_subjects(results),
            "recordings": pd.concat(single, ignore_index=True),
            "events": pd.concat([r.events for r in results], ignore_index=True),
            "spectral_windows": pd.concat([r.windows for r in results], ignore_index=True),
            "recording_spectra": pd.concat([r.spectra for r in results], ignore_index=True),
            "subject_spectra": pooled_spectra(results),
            "coverage": pd.concat([r.coverage for r in results], ignore_index=True),
            "quality": pd.DataFrame([r.quality for r in results]),
        }
        _write_tables(args.output, tables, _metadata(args.manifest, rows, config))
    except (ValueError, OSError) as error:
        parser.exit(2, f"Analysis failed: {error}\n")
    print(f"Wrote {len(tables['subjects'])} mouse summaries to {args.output}")


def validation_main(argv=None):
    parser = _parser("Inspect MAT quality and usable spectral windows without analyzing NE events.")
    parser.add_argument("--windows", type=float, nargs="+", default=[5, 10, 20, 30, 60, 120, 180])
    parser.add_argument(
        "--recording-start-exclusion-seconds",
        type=float,
        default=0.0,
        help="Exclude this initial duration from candidate spectral windows.",
    )
    args = parser.parse_args(argv)
    try:
        if args.output.exists():
            raise ValueError("Output directory already exists. Choose a new run directory.")
        if any(not np.isfinite(v) or v <= 0 for v in args.windows):
            raise ValueError("Window durations must be finite and positive.")
        if (
            not np.isfinite(args.recording_start_exclusion_seconds)
            or args.recording_start_exclusion_seconds < 0
        ):
            raise ValueError("Recording-start exclusion must be finite and nonnegative.")
        rows = read_manifest(args.manifest)
        qualities, coverage, bouts, errors = [], [], [], []
        for row in rows:
            try:
                quality, usable, bout = validate_file(
                    **row,
                    windows=args.windows,
                    recording_start_exclusion_seconds=args.recording_start_exclusion_seconds,
                )
                qualities.append(quality)
                coverage.append(usable)
                bouts.append(bout)
            except (ValueError, OSError) as error:
                errors.append({**row, "error": str(error)})
        tables = {
            "quality": pd.DataFrame(qualities),
            "coverage": pd.concat(coverage, ignore_index=True) if coverage else pd.DataFrame(),
            "bouts": pd.concat(bouts, ignore_index=True) if bouts else pd.DataFrame(),
            "errors": pd.DataFrame(errors, columns=["path", "mouse_id", "recording_id", "error"]),
        }
        metadata = _metadata(args.manifest, rows)
        metadata["candidate_window_seconds"] = args.windows
        metadata["recording_start_exclusion_seconds"] = args.recording_start_exclusion_seconds
        _write_tables(args.output, tables, metadata)
    except (ValueError, OSError) as error:
        parser.exit(2, f"Validation failed: {error}\n")
    print(f"Validated {len(qualities)} files; {len(errors)} errors. Reports: {args.output}")
    if errors:
        return 1
    return 0
