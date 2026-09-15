"""Data quality and window-coverage summaries, independent of event detection."""

import numpy as np
import pandas as pd
from .io import STATES, load_recording, runs
from .spectra import window_slices


def quality_report(recording):
    return {
        **recording.identity,
        "ne_frequency": recording.fs,
        "ne_samples": recording.ne.size,
        "ne_seconds": recording.ne.size / recording.fs,
        "label_seconds": recording.labels.size,
        "duration_mismatch_seconds": recording.ne.size / recording.fs - recording.labels.size,
        "nonfinite_ne_samples": int((~np.isfinite(recording.ne)).sum()),
        "coarse_wake_seconds": int((recording.labels == 0).sum()),
        "unscored_seconds": int(np.isnan(recording.labels).sum()),
        "ne_samples_without_label": int(np.isnan(recording.sample_labels).sum()),
        "constant_neighbor_fraction": (
            float(np.mean(np.diff(recording.ne) == 0)) if recording.ne.size > 1 else np.nan
        ),
    }


def bout_table(recording):
    rows = []
    for label, state in STATES.items():
        for start, stop in runs(recording.labels == label):
            rows.append(
                {
                    **recording.identity,
                    "state": state,
                    "start_seconds": recording.start_time + start,
                    "end_seconds": recording.start_time + stop,
                    "duration_seconds": stop - start,
                }
            )
    return pd.DataFrame(
        rows,
        columns=[*recording.identity, "state", "start_seconds", "end_seconds", "duration_seconds"],
    )


def usable_data_summary(recording, windows=(5, 10, 20, 30, 60, 120, 180)):
    bouts, rows = bout_table(recording), []
    labels = recording.sample_labels
    for label, state in STATES.items():
        durations = bouts.loc[bouts.state == state, "duration_seconds"]
        total = int((recording.labels == label).sum())
        # Fractional sampling rates quantize state edges by up to one sample.
        valid = min(
            total, int(((labels == label) & np.isfinite(recording.ne)).sum()) / recording.fs
        )
        for seconds in windows:
            slices = list(window_slices(recording, label, seconds))
            covered = min(valid, sum(stop - start for start, stop in slices) / recording.fs)
            rows.append(
                {
                    **recording.identity,
                    "state": state,
                    "total_seconds": total,
                    "valid_seconds": valid,
                    "n_bouts": len(durations),
                    "bout_duration_median": durations.median(),
                    "bout_duration_p10": durations.quantile(0.1),
                    "bout_duration_p90": durations.quantile(0.9),
                    "window_seconds": seconds,
                    "n_windows": len(slices),
                    "covered_seconds": covered,
                    "coverage_fraction": covered / total if total else np.nan,
                    "three_cycle_frequency_hz": 3 / seconds,
                }
            )
    return pd.DataFrame(rows)


def validate_file(path, mouse_id, recording_id=None, windows=(5, 10, 20, 30, 60, 120, 180)):
    recording = load_recording(path, mouse_id, recording_id)
    return quality_report(recording), usable_data_summary(recording, windows), bout_table(recording)


def smoothing_power_retention(frequency, saved_fs, factor=100, filter_samples=1000):
    """Final filtfilt moving-average attenuation only, not a correction or full transfer model."""
    raw_fs = saved_fs * factor
    gain = np.sinc(filter_samples * frequency / raw_fs) / np.sinc(frequency / raw_fs)
    return float(gain**4)
