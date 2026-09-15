"""Hann-window PSDs inside continuous valid state bouts; no stitching or padding."""

import numpy as np
import pandas as pd
from scipy.signal import periodogram
from .io import STATES, load_recording, runs

WINDOW_COLUMNS = [
    "mouse_id",
    "recording_id",
    "mat_path",
    "state",
    "start_seconds",
    "end_seconds",
    "duration_seconds",
    "band_power",
]
PSD_COLUMNS = ["mouse_id", "recording_id", "mat_path", "state", "frequency_hz", "psd", "n_windows"]


def window_slices(recording, state, seconds):
    if not np.isfinite(seconds) or seconds <= 0:
        raise ValueError("Window duration must be positive and finite.")
    n = round(seconds * recording.fs)
    if n < 2:
        raise ValueError("Window must contain at least two samples.")
    mask = (recording.sample_labels == state) & np.isfinite(recording.ne)
    for start, stop in runs(mask):
        for left in range(start, stop - n + 1, n):
            yield left, left + n


def spectral_metrics(psd):
    if psd.empty:
        return {"band_power": np.nan, "dominant_frequency_hz": np.nan}
    psd = psd.sort_values("frequency_hz")
    power = float(np.trapezoid(psd.psd, psd.frequency_hz))
    # An all-zero spectrum has no dominant oscillation.
    peak = float(psd.iloc[int(np.argmax(psd.psd.to_numpy()))].frequency_hz) if power > 0 else np.nan
    return {"band_power": power, "dominant_frequency_hz": peak}


def compute_spectrum(recording, config):
    if config.fmax >= recording.fs / 2:
        raise ValueError("Spectral fmax must be below the saved NE Nyquist frequency.")
    # Common physical-frequency grid for pooling files with slightly different fs.
    grid = np.unique(
        np.r_[
            config.fmin,
            np.arange(
                np.ceil(config.fmin * config.window_seconds),
                np.floor(config.fmax * config.window_seconds) + 1,
            )
            / config.window_seconds,
            config.fmax,
        ]
    )
    if len(grid) < 3:
        raise ValueError("Frequency band needs at least three grid points at this window duration.")
    windows, spectra = [], []
    for stage, state in STATES.items():
        values = []
        for left, right in window_slices(recording, stage, config.window_seconds):
            f, p = periodogram(
                recording.ne[left:right],
                recording.fs,
                window="hann",
                detrend="constant",
                scaling="density",
            )
            sampled = np.interp(grid, f, p)
            values.append(sampled)
            windows.append(
                {
                    **recording.identity,
                    "state": state,
                    "start_seconds": recording.start_time + left / recording.fs,
                    "end_seconds": recording.start_time + right / recording.fs,
                    "duration_seconds": (right - left) / recording.fs,
                    "band_power": float(np.trapezoid(sampled, grid)),
                }
            )
        if values:
            for freq, value in zip(grid, np.mean(values, axis=0)):
                spectra.append(
                    {
                        **recording.identity,
                        "state": state,
                        "frequency_hz": freq,
                        "psd": value,
                        "n_windows": len(values),
                    }
                )
    return pd.DataFrame(spectra, columns=PSD_COLUMNS), pd.DataFrame(windows, columns=WINDOW_COLUMNS)


def compute_spectrum_file(path, mouse_id, config, recording_id=None):
    return compute_spectrum(load_recording(path, mouse_id, recording_id), config)
