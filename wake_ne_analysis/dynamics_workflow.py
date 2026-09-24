"""File orchestration and provenance for the versioned NE dynamics experiment."""

from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform

import numpy as np
import pandas as pd
import scipy

from .dynamics_summary import pooled_comparisons, pooled_mouse_summaries, summarize_features
from .io import load_recording
from .ne_dynamics import DynamicsConfig, FEATURE_NAMES, FEATURE_TITLES, extract_dynamics


SCHEMA = "ne_dynamics_v2_pooled"


def require_empty(path):
    path = Path(path)
    if path.exists() and (not path.is_dir() or any(path.iterdir())):
        raise ValueError(f"Refusing to overwrite non-empty output: {path}")


def source_digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def load_feature_records(analysis_dir):
    """Read completed archives after checking source identity and feature contract."""
    analysis_dir = Path(analysis_dir)
    run = json.loads((analysis_dir / "run.json").read_text(encoding="utf-8"))
    if run["status"] != "complete" or run["schema"] != SCHEMA:
        raise ValueError("Expected a completed v2 pooled-seconds analysis.")
    audit = pd.read_csv(analysis_dir / "source_audit.csv", converters={"recording_id": str})
    audit = audit.loc[audit.status == "included"]
    if audit.recording_id.duplicated().any() or len(audit) != run["n_included_files"]:
        raise ValueError("Duplicate or incomplete source audit.")
    records, hashes = {}, {}
    for row in audit.itertuples():
        path = Path(run["feature_dir"]) / f"{row.recording_id}.npz"
        with np.load(path, allow_pickle=False) as archive:
            metadata = json.loads(str(archive["metadata_json"]))
            if (metadata["config"] != run["config"] or metadata["schema"] != run["schema"]
                    or metadata["source_sha256"] != row.source_sha256
                    or metadata["recording_id"] != row.recording_id
                    or archive["feature_names"].tolist() != list(FEATURE_NAMES)):
                raise ValueError(f"Archive provenance/configuration mismatch: {path}")
            records[row.recording_id] = {key: archive[key] for key in ("X", "label")}
        hashes[path.name] = source_digest(path)
    return records, run, hashes


def run_analysis(input_dir, feature_dir, results_dir, config=DynamicsConfig(), metadata_path=None,
                 write_report_output=True):
    """Extract one NPZ per file over the common interval and pool eligible seconds.

    Common-start alignment is confirmed by the user. Excess NE tail is trimmed
    in memory before filtering. Input errors fail rather than silently skip files.
    """
    input_dir, feature_dir, results_dir = map(Path, (input_dir, feature_dir, results_dir))
    paths = sorted(input_dir.glob("*.mat"))
    if not paths:
        raise ValueError(f"No MAT files in {input_dir}")
    if len({p.stem.casefold() for p in paths}) != len(paths):
        raise ValueError("Duplicate recording IDs.")
    if feature_dir.resolve() == results_dir.resolve():
        raise ValueError("Feature and results directories must differ.")
    for directory in (feature_dir, results_dir):
        require_empty(directory)
    metadata = None
    if metadata_path is not None:
        metadata = pd.read_csv(metadata_path, dtype=str, keep_default_na=False)
        required = ["recording_id", "mouse_id", "condition"]
        if not set(required).issubset(metadata.columns):
            raise ValueError(f"Metadata requires columns {required}.")
        if (metadata[required].apply(lambda column: column.str.strip()) == "").any().any():
            raise ValueError("Metadata identities and conditions must not be empty.")
        if metadata.recording_id.duplicated().any():
            raise ValueError("Metadata has duplicate recording IDs.")
    feature_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)
    run = {
        "schema": SCHEMA, "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": "running", "config": asdict(config),
        "feature_dir": str(feature_dir.resolve()), "input_dir": str(input_dir.resolve()),
        "feature_names": list(FEATURE_NAMES), "history_crosses_all_states": True,
        "comparison_unit": "pooled_second", "weighting": "equal_weight_per_valid_second",
        "alignment": "confirmed_common_start; excess_ne_tail_trimmed_before_filtering",
        "python": platform.python_version(), "numpy": np.__version__,
        "scipy": scipy.__version__, "pandas": pd.__version__,
        "code_sha256": {name: source_digest(Path(__file__).with_name(name)) for name in
                        ("ne_dynamics.py", "dynamics_summary.py", "dynamics_workflow.py", "io.py")},
        "metadata_path": str(Path(metadata_path).resolve()) if metadata_path else None,
        "metadata_sha256": source_digest(metadata_path) if metadata_path else None,
        "write_report_output": write_report_output,
    }
    run_path = results_dir / "run.json"
    run_path.write_text(json.dumps(run, indent=2), encoding="utf-8")
    records, audits, summaries = {}, [], []
    for path in paths:
        print(f"Processing {path.name}", flush=True)
        recording = load_recording(path, "unverified", path.stem)
        mismatch = len(recording.ne) / recording.fs - len(recording.labels)
        provenance = {"recording_id": path.stem, "mat_path": str(path.resolve()),
                      "source_sha256": source_digest(path), "source_bytes": path.stat().st_size,
                      "ne_minus_label_seconds": mismatch, "ne_samples": len(recording.ne),
                      "ne_frequency": recording.fs, "label_seconds": len(recording.labels),
                      "ne_duration_seconds": len(recording.ne) / recording.fs,
                      "start_time": recording.start_time}
        arrays, audit = extract_dynamics(recording, config)
        archive_meta = {**audit, **provenance, "schema": SCHEMA}
        np.savez_compressed(feature_dir / f"{path.stem}.npz", **arrays,
                            metadata_json=np.asarray(json.dumps(archive_meta, sort_keys=True)))
        records[path.stem] = arrays
        condition = "unspecified"
        if metadata is not None and "recording_id" in metadata and "condition" in metadata:
            selected = metadata.loc[metadata.recording_id == path.stem, "condition"]
            if len(selected) == 1:
                condition = selected.iloc[0]
        summary = summarize_features(arrays, path.stem, condition)
        summaries.append(summary)
        audit.pop("config")
        audits.append({**audit, **provenance, "status": "included", "reason": ""})
    pd.DataFrame(audits).to_csv(results_dir / "source_audit.csv", index=False)
    if not records:
        raise ValueError("No eligible recordings; inspect source_audit.csv.")
    summary = pd.concat(summaries, ignore_index=True)
    comparisons = pooled_comparisons(records)
    summary.to_csv(results_dir / "feature_coverage_by_recording.csv", index=False)
    comparisons.to_csv(results_dir / "pooled_comparisons.csv", index=False)
    if metadata is not None:
        mice = pooled_mouse_summaries(records, metadata)
        mice.to_csv(results_dir / "mouse_summary.csv", index=False)
        metadata.to_csv(results_dir / "identity_metadata.csv", index=False)
    run.update(status="complete", n_input_files=len(paths), n_included_files=len(records),
               n_excluded_files=len(paths) - len(records))
    run_path.write_text(json.dumps(run, indent=2), encoding="utf-8")
    (feature_dir / "README.md").write_text(
        "# NE dynamics features v2: common interval, pooled seconds\n\nOne source-stem NPZ per MAT file. "
        "Older feature sets are unchanged.\n\n"
        "Load with `np.load(path, allow_pickle=False)`. `X` has four columns, named by "
        "`feature_names`, with `feature_units`; `second` is local score time, "
        "`time_seconds` includes the saved start_time, and `label` preserves score labels. "
        "NaN means unavailable, not zero. No scaling is applied. "
        "`metadata_json` includes source SHA256, rates, timing and configuration.\n\n"
        "Excess NE beyond the label interval is dropped in memory before filtering. "
        "Sources are unchanged; trimming and incomplete seconds are audited.\n\n"
        f"The first {config.startup_exclusion_seconds:g} seconds are excluded in memory before "
        "filtering and history extraction. Timestamps and labels are preserved; histories "
        "must contain only finite retained samples, and filter guards restart after this exclusion.\n\n"
        "Slopes use each current second after zero-phase filtering; absolute slope "
        "is the magnitude of that signed slope. Both variances use the preceding "
        f"{config.history_seconds:g} seconds ending at the start of the current second, irrespective of states. "
        "Variances divide by sample count; the detrended version removes a local OLS line.\n\n"
        f"Run provenance and audits: {results_dir.resolve()}\n",
        encoding="utf-8",
    )
    if write_report_output:
        write_report(results_dir, comparisons, audits, run)
    return comparisons


def write_report(directory, comparisons, audits, run):
    """Report the requested pooled-seconds comparison with its inference limits."""
    config = run["config"]
    lines = ["# NE dynamics: pooled High versus Low Alertness seconds", "",
             f"All {run['n_included_files']} input recordings contributed. "
             "Every eligible second has equal weight, irrespective of recording. "
             "History windows may cross all score states. No additional normalization was applied.", "",
             "| Feature | High seconds | Low seconds | High mean | Low mean | High-minus-Low mean | Rank-biserial effect | Nominal p | Holm p |",
             "|---|---:|---:|---|---|---:|---:|---:|---:|"]
    titles = dict(zip(FEATURE_NAMES, [title.replace("10-second", f"{config['history_seconds']:g}-second")
                                    for title in FEATURE_TITLES]))
    for row in comparisons.itertuples():
        lines.append(f"| {titles[row.feature]} | {row.n_high} | {row.n_low} | "
                     f"{row.high_mean:.5g} | "
                     f"{row.low_mean:.5g} | "
                     f"{row.mean_high_minus_low:.5g} | {row.rank_biserial:.5g} | "
                     f"{row.p_value:.5g} | {row.p_holm:.5g} |")
    lines += ["", "Slope units: percentage points/s. Variance units: percentage points squared.", "",
              "## Interpretation", "",
              "Two-sided Mann–Whitney U compares pooled distributions; it is not a "
              "test of means. Holm correction covers the four features. The rank-biserial "
              "effect is 2U/(nHigh*nLow)-1; positive means higher in High Alertness.", "",
              "The saved NE is normalized percentage delta-F/F, providing a common nominal "
              "scale, but normalization does not guarantee identical baselines, gains or "
              "noise across recordings. Longer recordings and more prevalent states "
              "contribute more seconds. Adjacent seconds and overlapping histories are "
              "dependent, so pooled p-values are nominal and pseudoreplicated; Holm "
              "correction does not fix that. These results describe the pooled sample, "
              "not independent-animal significance.", "",
              "## Methods", "",
              f"Order-{config['filter_order']} Butterworth forward/backward filtering has "
              f"effective -3 dB cutoff {config['cutoff_hz']:g} Hz. "
              f"A {config['edge_guard_seconds']:g}-second guard is removed at finite-segment edges "
              "for within-second OLS slopes and their magnitudes. Both variances use "
              f"saved processed NE in [s-{config['history_seconds']:g}, s), with no additional "
              "low-pass. Detrended variance removes a local OLS line. Variances divide by "
              "sample count. Missing estimates stay NaN; labels are unchanged.", "",
              "## Aligned input interval", "",
              "All files use their confirmed common-start interval. NE samples at or after "
              "the sleep-score interval end are dropped in memory before filtering. Source "
              "MAT files are unchanged. Where NE ends first, incomplete score seconds "
              "remain unavailable.", "",
              "| Recording | Original NE minus score duration (s) | NE samples trimmed |",
              "|---|---:|---:|"]
    for audit in audits:
        lines.append(f"| {audit['recording_id']} | {audit['ne_minus_label_seconds']:.6f} | "
                     f"{audit['trimmed_ne_samples']} |")
    lines += ["", "See `source_audit.csv`, `feature_coverage_by_recording.csv`, "
              "`pooled_comparisons.csv`, and `run.json`. Per-second values remain in "
              "versioned NPZ archives. The separate renderer writes "
              "`figures/pooled_dynamics.html` and `figures/coverage.html`.", ""]
    (Path(directory) / "report.md").write_text("\n".join(lines), encoding="utf-8")
