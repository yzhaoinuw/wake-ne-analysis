"""Versioned, per-second 29-feature EEG/EMG/NE archive extraction."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import signal
from scipy.io import loadmat
from scipy.ndimage import uniform_filter1d

from .stages import LABEL_NAMES


WIDE_EEG_BANDS_HZ = ((0.5, 5.0),) + tuple((float(low), float(low + 5)) for low in range(5, 100, 5))
SCORING_EEG_BANDS_HZ = ((1.0, 4.0), (4.0, 8.0))


def _band_name(low, high):
    return f"eeg_{str(low).replace('.', 'p')}_{str(high).replace('.', 'p')}_log10_power"


FEATURE_COLUMNS = tuple(_band_name(*band) for band in WIDE_EEG_BANDS_HZ) + (
    "eeg_scoring_delta_1_4_log10_power",
    "eeg_scoring_theta_4_8_log10_power",
    "emg_centered_rms",
    "emg_filtered_rms",
    "emg_burst_onset_count",
    "emg_burst_duty_fraction",
    "emg_burst_peak_envelope",
    "ne_mean",
    "ne_slope_ols_per_second",
)
FEATURE_SET_NAME = "features_29"


@dataclass(frozen=True)
class ExpandedFeatureConfig:
    """Provisional 29-feature contract for exploratory dimensional reduction."""

    emg_low_hz: float = 20.0
    emg_high_hz: float = 200.0
    emg_filter_order: int = 4
    emg_envelope_window_seconds: float = 0.075
    emg_burst_threshold_mad: float = 3.0
    emg_burst_min_duration_seconds: float = 0.050
    emg_burst_gap_tolerance_seconds: float = 0.050
    emg_filter_chunk_seconds: float = 120.0
    emg_filter_overlap_seconds: float = 1.0


def _signal_vector(value, name):
    result = np.asarray(value).squeeze()
    if result.ndim > 1:
        raise ValueError(f"{name} must be a single-channel vector.")
    return result.reshape(-1).astype(np.float32, copy=False)


def _labels(value):
    labels = np.asarray(value, dtype=float).squeeze().reshape(-1)
    labels[labels == -1] = np.nan
    if np.any(~np.isnan(labels) & ~np.isin(labels, (*LABEL_NAMES, 0))):
        raise ValueError("Unknown sleep label.")
    return labels


def _scalar(value, name):
    if np.asarray(value).size != 1:
        raise ValueError(f"{name} must be scalar.")
    result = float(np.asarray(value).item())
    if not np.isfinite(result) or result <= 0:
        raise ValueError(f"{name} must be finite and positive.")
    return result


def _epoch_bounds(n_seconds, fs, size):
    edges = np.rint(np.arange(n_seconds + 1) * fs).astype(int)
    starts, stops = edges[:-1], edges[1:]
    return starts, stops, (starts >= 0) & (stops <= size) & (stops > starts)


def _runs(mask):
    padded = np.r_[False, np.asarray(mask, dtype=bool), False]
    changes = np.flatnonzero(padded[1:] != padded[:-1])
    return zip(changes[::2], changes[1::2])


def _epoch_matrix(values, starts, width):
    rows = starts[:, None] + np.arange(width)
    if rows.size and rows.max() >= len(values):
        raise ValueError("Epoch matrix would exceed the source signal.")
    return values[rows]


def _eeg_log_bandpowers(eeg, fs, starts):
    width = int(np.floor(fs))
    if width < 202:
        raise ValueError("EEG sampling must support the 0.5--100 Hz feature panel.")
    bands = WIDE_EEG_BANDS_HZ + SCORING_EEG_BANDS_HZ
    output = np.full((len(starts), len(bands)), np.nan)
    for first in range(0, len(starts), 256):
        selection = slice(first, first + 256)
        epochs = _epoch_matrix(eeg, starts[selection], width)
        frequencies, psd = signal.periodogram(
            epochs, fs=fs, window="hann", detrend="constant", scaling="density", axis=1
        )
        for index, (low, high) in enumerate(bands):
            # Match the scoring app's strict lower-edge / inclusive upper-edge convention.
            selected = (frequencies > low) & (frequencies <= high)
            if selected.sum() < 2:
                raise ValueError(f"No resolvable EEG bins in {low}--{high} Hz.")
            power = np.trapezoid(psd[:, selected], frequencies[selected], axis=1)
            output[selection, index] = np.log10(np.maximum(power, np.finfo(float).tiny))
    return output


def _raw_centered_rms(emg, starts, stops):
    result = np.full(len(starts), np.nan)
    for index, (start, stop) in enumerate(zip(starts, stops)):
        epoch = emg[start:stop]
        if epoch.size and np.isfinite(epoch).all():
            centred = epoch - epoch.mean()
            result[index] = np.sqrt(np.mean(centred**2))
    return result


def _linear_detrend(values):
    """Return the least-squares linear detrend without SciPy's repeated small solves."""
    values = np.asarray(values, dtype=float)
    positions = np.arange(len(values), dtype=float) - (len(values) - 1) / 2
    mean = values.mean()
    slope = np.dot(positions, values - mean) / np.dot(positions, positions)
    return values - (mean + slope * positions)


def _filtered_emg_and_envelope(emg, fs, config):
    """Apply a bounded-memory scoring-family filter and derive a 75 ms RMS envelope.

    Full-recording detrend/filter calls are impractical on these multi-hour vectors.
    Finite runs are therefore processed in fixed 120-second cores with one-second
    context on each side; context samples are discarded. This keeps each saved core
    away from ``sosfiltfilt`` boundaries, but is not bit-identical to filtering a
    whole recording in one call.
    """
    raw = np.asarray(emg, dtype=float)
    if fs <= 50:
        raise ValueError("EMG burst features require sampling above 50 Hz.")
    valid = np.isfinite(raw)
    flat_differences = np.r_[False, np.isfinite(np.diff(raw)) & (np.diff(raw) == 0)]
    for start, stop in _runs(flat_differences):
        if stop - start >= int(np.ceil(fs)):
            valid[max(0, start - 1) : stop] = False
    high = min(config.emg_high_hz, 0.45 * fs)
    if high <= config.emg_low_hz:
        raise ValueError("EMG sampling cannot support the requested band-pass range.")
    sos = signal.butter(
        config.emg_filter_order,
        [config.emg_low_hz, high],
        btype="bandpass",
        fs=fs,
        output="sos",
    )
    filtered = np.full(raw.shape, np.nan)
    core_length = max(1, int(round(config.emg_filter_chunk_seconds * fs)))
    overlap = max(0, int(round(config.emg_filter_overlap_seconds * fs)))
    for start, stop in _runs(valid):
        for core_start in range(start, stop, core_length):
            core_stop = min(core_start + core_length, stop)
            context_start = max(start, core_start - overlap)
            context_stop = min(stop, core_stop + overlap)
            if context_stop - context_start <= 30:
                continue
            context = signal.sosfiltfilt(sos, _linear_detrend(raw[context_start:context_stop]))
            keep_start = core_start - context_start
            keep_stop = keep_start + core_stop - core_start
            filtered[core_start:core_stop] = context[keep_start:keep_stop]

    envelope = np.full(raw.shape, np.nan)
    window = max(3, int(round(config.emg_envelope_window_seconds * fs)))
    for start, stop in _runs(np.isfinite(filtered)):
        envelope[start:stop] = np.sqrt(
            np.maximum(uniform_filter1d(filtered[start:stop] ** 2, window, mode="nearest"), 0)
        )
    return filtered, envelope, window


def _emg_burst_features(filtered, envelope, starts, stops, fs, config):
    finite = np.isfinite(envelope)
    values = envelope[finite]
    median = float(np.median(values))
    mad = float(np.median(np.abs(values - median)))
    threshold = median + config.emg_burst_threshold_mad * 1.4826 * mad
    active = finite & (envelope > threshold)
    max_gap = int(round(config.emg_burst_gap_tolerance_seconds * fs))
    for start, stop in _runs(~active):
        if (
            start > 0
            and stop < len(active)
            and stop - start <= max_gap
            and finite[start:stop].all()
            and active[start - 1]
            and active[stop]
        ):
            active[start:stop] = True
    minimum = max(1, int(np.ceil(config.emg_burst_min_duration_seconds * fs)))
    for start, stop in _runs(active):
        if stop - start < minimum:
            active[start:stop] = False
    burst_starts = np.fromiter((start for start, _ in _runs(active)), dtype=int)

    filtered_rms = np.full(len(starts), np.nan)
    onset_count = np.full(len(starts), np.nan)
    duty_fraction = np.full(len(starts), np.nan)
    peak_envelope = np.full(len(starts), np.nan)
    for index, (start, stop) in enumerate(zip(starts, stops)):
        segment = filtered[start:stop]
        envelope_segment = envelope[start:stop]
        if not segment.size or not np.isfinite(segment).all() or not np.isfinite(envelope_segment).all():
            continue
        filtered_rms[index] = np.sqrt(np.mean(segment**2))
        duty_fraction[index] = active[start:stop].mean()
        peak_envelope[index] = envelope_segment.max()
        onset_count[index] = np.count_nonzero((burst_starts >= start) & (burst_starts < stop))
    return np.column_stack((filtered_rms, onset_count, duty_fraction, peak_envelope)), threshold


def _ne_features(ne, starts, stops, fs):
    output = np.full((len(starts), 2), np.nan)
    for index, (start, stop) in enumerate(zip(starts, stops)):
        epoch = ne[start:stop]
        if not epoch.size or not np.isfinite(epoch).all():
            continue
        time = np.arange(len(epoch), dtype=float) / fs
        output[index, 0] = epoch.mean()
        output[index, 1] = np.polyfit(time, epoch, 1)[0]
    return output


def extract_expanded_recording_features(path, config=ExpandedFeatureConfig()):
    """Extract the documented 29 features from one MAT recording without relabeling it."""
    path = Path(path).resolve()
    required = ("eeg", "emg", "ne", "eeg_frequency", "ne_frequency", "sleep_scores")
    mat = loadmat(path, squeeze_me=True, variable_names=required)
    missing = [name for name in required if name not in mat or np.asarray(mat[name]).size == 0]
    if missing:
        raise ValueError(f"Missing required feature fields in {path.name}: {', '.join(missing)}.")
    eeg, emg, ne = (_signal_vector(mat[name], name) for name in ("eeg", "emg", "ne"))
    eeg_fs, ne_fs = _scalar(mat["eeg_frequency"], "eeg_frequency"), _scalar(mat["ne_frequency"], "ne_frequency")
    labels = _labels(mat["sleep_scores"])
    n_seconds = len(labels)
    eeg_starts, eeg_stops, eeg_complete = _epoch_bounds(n_seconds, eeg_fs, len(eeg))
    emg_starts, emg_stops, emg_complete = _epoch_bounds(n_seconds, eeg_fs, len(emg))
    ne_starts, ne_stops, ne_complete = _epoch_bounds(n_seconds, ne_fs, len(ne))
    complete = eeg_complete & emg_complete & ne_complete
    seconds = np.flatnonzero(complete)
    if not len(seconds):
        raise ValueError(f"No complete multimodal seconds in {path.name}.")

    eeg_features = _eeg_log_bandpowers(eeg, eeg_fs, eeg_starts[seconds])
    raw_rms = _raw_centered_rms(emg, emg_starts[seconds], emg_stops[seconds])
    filtered, envelope, envelope_window = _filtered_emg_and_envelope(emg, eeg_fs, config)
    emg_features, emg_threshold = _emg_burst_features(
        filtered, envelope, emg_starts[seconds], emg_stops[seconds], eeg_fs, config
    )
    ne_features = _ne_features(ne, ne_starts[seconds], ne_stops[seconds], ne_fs)
    values = np.column_stack((eeg_features, raw_rms, emg_features, ne_features))
    table = pd.DataFrame(values, columns=FEATURE_COLUMNS)
    table.insert(0, "label", labels[seconds])
    table.insert(0, "second", seconds)
    table.insert(0, "recording_id", path.stem)
    table["state"] = table.label.map(LABEL_NAMES)
    retained = table.state.notna() & np.isfinite(table.loc[:, FEATURE_COLUMNS]).all(axis=1)
    return table.loc[retained].reset_index(drop=True), {
        "recording_id": path.stem,
        "source_mat_file": path.name,
        "source_mat_path": str(path),
        "label_seconds": int(n_seconds),
        "complete_multimodal_seconds": int(complete.sum()),
        "retained_feature_seconds": int(retained.sum()),
        "eeg_frequency_hz": eeg_fs,
        "ne_frequency_hz": ne_fs,
        "emg_band_high_hz": min(config.emg_high_hz, 0.45 * eeg_fs),
        "emg_envelope_window_samples": envelope_window,
        "emg_burst_threshold": emg_threshold,
    }


def _scale_with_fallback(table):
    values = table.loc[:, FEATURE_COLUMNS]
    median = values.median()
    iqr = values.quantile(0.75) - values.quantile(0.25)
    standard_deviation = values.std(ddof=0)
    use_std = (iqr <= 0) & (standard_deviation > 0)
    constant = standard_deviation <= 0
    scale = iqr.copy()
    scale.loc[use_std] = standard_deviation.loc[use_std]
    scale.loc[constant] = 1.0
    scaled = (values - median) / scale
    if not np.isfinite(scaled.to_numpy()).all():
        raise ValueError("Expanded feature scaling produced a non-finite value.")
    return scaled, median, iqr, scale, use_std, constant


def write_expanded_feature_archives(input_dir, output_dir, config=ExpandedFeatureConfig()):
    """Write one compressed ``features_29`` NumPy archive per source MAT file."""
    input_dir, output_dir = Path(input_dir), Path(output_dir)
    files = sorted(input_dir.glob("*.mat"))
    if not files:
        raise ValueError(f"No MAT files found in {input_dir}.")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError("Expanded feature output directory must be new or empty.")
    output_dir.mkdir(parents=True, exist_ok=True)
    archives = []
    for path in files:
        table, metadata = extract_expanded_recording_features(path, config)
        if table.empty:
            raise ValueError(f"No finite labelled expanded-feature rows in {path.name}.")
        scaled, median, iqr, scale, use_std, constant = _scale_with_fallback(table)
        archive_path = output_dir / f"{path.stem}.npz"
        np.savez_compressed(
            archive_path,
            X=table.loc[:, FEATURE_COLUMNS].to_numpy(dtype=np.float32),
            X_robust_scaled=scaled.to_numpy(dtype=np.float32),
            second=table.second.to_numpy(dtype=np.int32),
            label=table.label.to_numpy(dtype=np.int8),
            feature_names=np.asarray(FEATURE_COLUMNS),
            scaling_median=median.to_numpy(dtype=np.float32),
            scaling_iqr=iqr.to_numpy(dtype=np.float32),
            scaling_effective_scale=scale.to_numpy(dtype=np.float32),
            scaling_used_standard_deviation=use_std.to_numpy(dtype=bool),
            scaling_constant_feature=constant.to_numpy(dtype=bool),
            recording_id=np.asarray(path.stem),
            source_mat_file=np.asarray(path.name),
            source_mat_path=np.asarray(str(path.resolve())),
            metadata_json=np.asarray(json.dumps({"feature_set": FEATURE_SET_NAME, "config": asdict(config), **metadata})),
        )
        archives.append(archive_path)
    return archives
