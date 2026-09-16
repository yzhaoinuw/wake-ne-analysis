"""One MAT file in, inspectable tables out; no dependency on the scoring app."""

from dataclasses import dataclass
import pandas as pd
from .config import AnalysisConfig
from .io import load_recording
from .spectra import compute_spectrum, PSD_COLUMNS, WINDOW_COLUMNS
from .transients import detect_transients
from .validation import quality_report, usable_data_summary, smoothing_power_retention


@dataclass
class RecordingAnalysis:
    mouse_id: str
    recording_id: str
    config: AnalysisConfig
    quality: dict
    coverage: pd.DataFrame
    events: pd.DataFrame
    spectra: pd.DataFrame
    windows: pd.DataFrame


def analyze_recording(recording, config=None):
    config = config or AnalysisConfig()
    quality = quality_report(recording)
    if config.require_fine_wake and quality["coarse_wake_seconds"]:
        raise ValueError(
            f"{recording.recording_id}: coarse Wake remains; complete Active/Quiet labels first."
        )
    if abs(quality["duration_mismatch_seconds"]) > 1:
        raise ValueError(
            f"{recording.recording_id}: NE and label durations differ by more than one second."
        )
    events = detect_transients(
        recording,
        config.transients,
        config.recording_start_exclusion_seconds,
    )
    if config.spectrum is None:
        spectra, windows = pd.DataFrame(columns=PSD_COLUMNS), pd.DataFrame(columns=WINDOW_COLUMNS)
        coverage = usable_data_summary(
            recording,
            [1],
            config.recording_start_exclusion_seconds,
        )
        coverage["n_windows"] = 0
        coverage["covered_seconds"] = 0.0
        coverage["coverage_fraction"] = float("nan")
        coverage["window_seconds"] = float("nan")
        coverage["three_cycle_frequency_hz"] = float("nan")
        quality["spectrum_status"] = "not_configured"
    else:
        spectra, windows = compute_spectrum(
            recording,
            config.spectrum,
            config.recording_start_exclusion_seconds,
        )
        coverage = usable_data_summary(
            recording,
            [config.spectrum.window_seconds],
            config.recording_start_exclusion_seconds,
        )
        quality["spectrum_status"] = "configured"
        quality["smoothing_only_power_retention_at_fmax"] = smoothing_power_retention(
            config.spectrum.fmax,
            recording.fs,
            config.preprocessing_downsample_factor,
            config.preprocessing_filter_samples,
        )
    quality["recording_start_exclusion_seconds"] = config.recording_start_exclusion_seconds
    return RecordingAnalysis(
        recording.mouse_id,
        recording.recording_id,
        config,
        quality,
        coverage,
        events,
        spectra,
        windows,
    )


def analyze_file(path, mouse_id, config=None, recording_id=None):
    return analyze_recording(load_recording(path, mouse_id, recording_id), config)


def analyze_files(manifest_rows, config=None):
    """Fail on invalid files rather than silently changing a mouse's included recordings."""
    rows = list(manifest_rows)
    ids = [row.get("recording_id") or str(row["path"]) for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate recording IDs.")
    return [
        analyze_file(**row, config=config)
        for row in sorted(rows, key=lambda r: (r["mouse_id"], str(r["path"])))
    ]
