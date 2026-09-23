"""Four NE dynamics features, independent of scoring history and report rendering.

Each row represents score second s = [s, s+1). Slopes are OLS fits to the
zero-phase low-passed samples in that second. Variances use saved processed NE
samples in [s-history_seconds, s), strictly before the current second. Labels
never affect either calculation. No resampling, normalization or gap bridging.
"""

from dataclasses import asdict, dataclass

import numpy as np
from scipy import signal

from .io import Recording, runs


FEATURE_NAMES = (
    "ne_slow_signed_slope",
    "ne_slow_absolute_slope",
    "ne_past_variance",
    "ne_past_detrended_variance",
)
FEATURE_TITLES = (
    "Signed NE slope",
    "Absolute NE slope",
    "Past 10-second NE variance",
    "Past 10-second detrended NE variance",
)
FEATURE_UNITS = ("percentage points/s",) * 2 + ("percentage points squared",) * 2


@dataclass(frozen=True)
class DynamicsConfig:
    cutoff_hz: float = 0.1
    filter_order: int = 4
    history_seconds: float = 10.0
    edge_guard_seconds: float = 30.0

    def __post_init__(self):
        for name in ("cutoff_hz", "history_seconds", "edge_guard_seconds"):
            value = getattr(self, name)
            if not np.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be finite and positive.")
        if not isinstance(self.filter_order, int) or self.filter_order < 1:
            raise ValueError("filter_order must be a positive integer.")


def lowpass_sos(fs, config):
    """Butterworth SOS with combined forward/backward -3 dB at cutoff_hz.

    Forward/backward amplitude is the squared single-pass amplitude. Compensate
    the design cutoff using the bilinear transform so the *combined* response
    at cutoff_hz is 1/sqrt(2), rather than the uncorrected 1/2.
    """
    if not np.isfinite(fs) or fs <= 2 * config.cutoff_hz:
        raise ValueError("NE sampling rate must exceed twice the cutoff.")
    factor = (np.sqrt(2) - 1) ** (1 / (2 * config.filter_order))
    design_hz = fs / np.pi * np.arctan(np.tan(np.pi * config.cutoff_hz / fs) / factor)
    return signal.butter(config.filter_order, design_hz, fs=fs, output="sos")


def smooth_ne(values, fs, config):
    """Filter separate finite stretches; invalidate a fixed guard at each end.

    Explicit odd reflection padding spans at least the edge guard. The default
    30-second guard is three cutoff periods, a technical edge rule fixed before
    the state comparisons. Too-short stretches remain NaN.
    """
    sos = lowpass_sos(fs, config)
    output = np.full(len(values), np.nan)
    guard = int(np.ceil(config.edge_guard_seconds * fs))
    padlen = max(guard, 3 * (2 * len(sos) + 1))
    for left, right in runs(np.isfinite(values)):
        if right - left <= max(padlen, 2 * guard):
            continue
        filtered = signal.sosfiltfilt(sos, values[left:right], padlen=padlen)
        output[left + guard:right - guard] = filtered[guard:-guard]
    return output


def linear_slope_and_variances(values, fs):
    """Centered OLS slope, population variance, and OLS residual mean square.

    The residual variance divides by n, just like ordinary population variance;
    this is a descriptive fluctuation measure, not an unbiased noise estimate.
    Centering each window avoids cancellation from large recording baselines.
    """
    if len(values) < 3 or not np.isfinite(values).all():
        return np.nan, np.nan, np.nan
    y = np.asarray(values, dtype=float) - np.mean(values)
    t = (np.arange(len(y)) - (len(y) - 1) / 2) / fs
    slope = float(np.dot(t, y) / np.dot(t, t))
    residual = y - slope * t
    return slope, float(np.mean(y * y)), float(np.mean(residual * residual))


def extract_dynamics(recording: Recording, config=DynamicsConfig()):
    """Return per-second arrays and a duration/coverage audit, preserving labels.

    Both NE and score vectors start at recording.start_time. Its absolute offset
    is added only to exported timestamps. Confirmed common-start alignment is
    assumed: NE samples at or after the label interval end are dropped in memory
    BEFORE filtering. If NE ends first, unavailable score seconds remain NaN.
    Source files and labels are never rewritten.
    """
    fs = recording.fs
    lowpass_sos(fs, config)  # Validate even if the source is entirely invalid.
    duration = len(recording.ne) / fs
    mismatch = duration - len(recording.labels)
    seconds = np.arange(len(recording.labels), dtype=int)
    times = np.arange(len(recording.ne)) / fs
    common_samples = int(np.searchsorted(times, len(seconds), side="left"))
    ne = recording.ne[:common_samples]
    times = times[:common_samples]
    common_duration = min(duration, len(seconds))
    starts = np.searchsorted(times, seconds, side="left")
    stops = np.searchsorted(times, seconds + 1, side="left")
    past_starts = np.searchsorted(times, seconds - config.history_seconds, side="left")
    smooth = smooth_ne(ne, fs, config)
    features = np.full((len(seconds), len(FEATURE_NAMES)), np.nan)
    complete = seconds + 1 <= common_duration + 1e-9
    for index in seconds[complete]:
        slope, _, _ = linear_slope_and_variances(smooth[starts[index]:stops[index]], fs)
        features[index, :2] = slope, abs(slope)
        if index >= config.history_seconds:
            _, variance, residual = linear_slope_and_variances(
                ne[past_starts[index]:starts[index]], fs
            )
            features[index, 2:] = variance, residual
    arrays = {
        "X": features,
        "second": seconds,
        "time_seconds": recording.start_time + seconds,
        "label": recording.labels.copy(),
        "feature_names": np.asarray(FEATURE_NAMES),
        "feature_units": np.asarray(FEATURE_UNITS),
    }
    audit = {
        "recording_id": recording.recording_id,
        "mat_path": str(recording.path),
        "ne_samples": len(recording.ne),
        "ne_frequency": fs,
        "start_time": recording.start_time,
        "label_seconds": len(seconds),
        "ne_duration_seconds": duration,
        "ne_minus_label_seconds": mismatch,
        "common_start_samples": common_samples,
        "common_start_seconds": common_duration,
        "trimmed_ne_samples": len(recording.ne) - common_samples,
        "ne_tail_seconds_not_analyzed": max(0.0, mismatch),
        "label_tail_seconds_without_ne": max(0.0, -mismatch),
        "incomplete_score_seconds": int((~complete).sum()),
        "nonfinite_ne_samples": int((~np.isfinite(recording.ne)).sum()),
        "finite_ne_segments": len(runs(np.isfinite(recording.ne))),
        "config": asdict(config),
    }
    return arrays, audit
