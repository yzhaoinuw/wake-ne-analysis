"""Natural event boundaries on continuous NE, independent of spectral windows."""

import numpy as np
import pandas as pd
from scipy.ndimage import percentile_filter
from scipy.signal import find_peaks
from .config import TransientConfig
from .io import STATES, load_recording, runs

METRICS = ["amplitude", "duration_seconds", "rise_slope", "decay_slope"]
EVENT_COLUMNS = [
    "mouse_id",
    "recording_id",
    "mat_path",
    "event_id",
    "state",
    "peak_seconds",
    "baseline_at_peak",
    "prominence",
    "threshold",
    "onset20_seconds",
    "rise80_seconds",
    "decay80_seconds",
    "offset20_seconds",
    *METRICS,
    "complete",
    "crosses_state",
    "baseline_edge",
    "recording_start_qc_excluded",
    "eligible",
]


def crossing(y, start, stop, level, rising):
    """Nearest rising crossing before peak, first falling crossing after peak."""
    a, b = y[start:stop], y[start + 1 : stop + 1]
    hits = np.flatnonzero((a <= level) & (b > level) if rising else (a >= level) & (b < level))
    if not hits.size:
        return np.nan
    index = start + int(hits[-1] if rising else hits[0])
    return index + (level - y[index]) / (y[index + 1] - y[index])


def detect_transients(recording, config=None, recording_start_exclusion_seconds=0.0):
    config = config or TransientConfig()
    if not np.isfinite(recording_start_exclusion_seconds) or recording_start_exclusion_seconds < 0:
        raise ValueError("Recording-start exclusion must be finite and nonnegative.")
    finite = np.isfinite(recording.ne)
    differences = np.diff(recording.ne)[finite[:-1] & finite[1:]]
    noise = 0.0
    if differences.size:
        noise = 1.4826 * np.median(np.abs(differences - np.median(differences))) / np.sqrt(2)
    threshold = max(config.min_prominence, config.noise_multiplier * noise)
    size = max(3, round(config.baseline_window_seconds * recording.fs)) | 1
    labels, rows = recording.sample_labels, []
    for start, stop in runs(finite):
        if stop - start < 3:
            continue
        signal = recording.ne[start:stop]
        baseline = percentile_filter(signal, config.baseline_percentile, size=size, mode="nearest")
        y = signal - baseline
        peaks, props = find_peaks(
            y,
            prominence=threshold,
            height=threshold,
            distance=max(1, round(config.min_peak_distance_seconds * recording.fs)),
        )
        for j, peak in enumerate(peaks):
            amplitude = float(y[peak])
            lbase, rbase = props["left_bases"][j], props["right_bases"][j]
            l20 = crossing(y, lbase, peak, 0.2 * amplitude, True)
            l80 = crossing(y, lbase, peak, 0.8 * amplitude, True)
            r80 = crossing(y, peak, rbase, 0.8 * amplitude, False)
            r20 = crossing(y, peak, rbase, 0.2 * amplitude, False)
            complete = bool(np.all(np.isfinite([l20, l80, r80, r20])) and l20 < l80 < r80 < r20)
            stage = labels[start + peak]
            state = STATES.get(stage, "other_or_unscored")
            crosses = False
            if complete:
                # Include both samples bracketing interpolated crossings.
                event_labels = labels[start + int(np.floor(l20)) : start + int(np.ceil(r20)) + 1]
                crosses = not bool(np.all(event_labels == stage))
            relative_peak_seconds = (start + peak) / recording.fs
            recording_start_qc_excluded = relative_peak_seconds < recording_start_exclusion_seconds
            eligible = (
                complete
                and stage in STATES
                and (config.assignment == "peak" or not crosses)
                and not recording_start_qc_excluded
            )
            absolute = lambda sample: recording.start_time + (start + sample) / recording.fs
            rows.append(
                {
                    **recording.identity,
                    "event_id": len(rows),
                    "state": state,
                    "peak_seconds": absolute(peak),
                    "baseline_at_peak": float(baseline[peak]),
                    "prominence": float(props["prominences"][j]),
                    "threshold": threshold,
                    "onset20_seconds": absolute(l20),
                    "rise80_seconds": absolute(l80),
                    "decay80_seconds": absolute(r80),
                    "offset20_seconds": absolute(r20),
                    "amplitude": amplitude,
                    "duration_seconds": (r20 - l20) / recording.fs if complete else np.nan,
                    "rise_slope": (
                        0.6 * amplitude * recording.fs / (l80 - l20) if complete else np.nan
                    ),
                    "decay_slope": (
                        0.6 * amplitude * recording.fs / (r20 - r80) if complete else np.nan
                    ),
                    "complete": complete,
                    "crosses_state": crosses,
                    "baseline_edge": bool(peak < size // 2 or peak >= len(y) - size // 2),
                    "recording_start_qc_excluded": recording_start_qc_excluded,
                    "eligible": eligible,
                }
            )
    return pd.DataFrame(rows, columns=EVENT_COLUMNS)


def compute_transients_file(path, mouse_id, config=None, recording_id=None):
    return detect_transients(load_recording(path, mouse_id, recording_id), config)
