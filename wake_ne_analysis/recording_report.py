"""Recording-level per-state-bout NE summaries for the current writeup.

This workflow uses the stored processed NE values without a local baseline. It treats
each MAT file as a paired recording; it is not independent mouse-level inference.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu, wilcoxon

from .config import SpectrumConfig
from .io import STATES, Recording, load_recording, runs
from .spectra import compute_spectrum, spectral_metrics


def crossing(y, start, stop, level, rising):
    """Return an interpolated threshold crossing within one continuous NE stretch."""
    a, b = y[start:stop], y[start + 1 : stop + 1]
    hits = np.flatnonzero((a <= level) & (b > level) if rising else (a >= level) & (b < level))
    if not hits.size:
        return np.nan
    index = start + int(hits[-1] if rising else hits[0])
    return index + (level - y[index]) / (y[index + 1] - y[index])


# Peak-state attribution deliberately permits timing crossings to leave the score
# run. These therefore describe the full NE elevation around its labelled peak, not
# the duration of a one-second sleep-score run.
# ``raw_peak`` remains in the audit table because it anchors the deliberately
# peak-assigned episode width and slopes.  It is not a reported comparison metric:
# the recording-level signal measure is the mean saved NE value in each score run.
RAW_METRICS = ("raw_bout_mean", "duration_seconds", "rise_slope", "decay_slope")
INDEPENDENT_BOUT_METRICS = ("rise_slope", "decay_slope")
RECORDING_METRICS = (
    "raw_bout_mean",
    "score_bout_duration_seconds",
    "score_bout_count",
    "rise_slope",
    "decay_slope",
)
SPECTRAL_METRICS = ("band_power", "dominant_frequency_hz")
RAW_SPECTRUM = SpectrumConfig(window_seconds=15.0, fmin=0.2, fmax=0.3)


def common_start_samples(recording: Recording) -> int:
    """Return the declared common-start interval without modifying either input."""
    label_covered = int(np.ceil(recording.labels.size * recording.fs))
    return min(recording.ne.size, label_covered)


def _common_start_recording(recording: Recording) -> Recording:
    """Return an in-memory common-duration view without changing source data."""
    return replace(recording, ne=recording.ne[: common_start_samples(recording)])


def _sample_labels(recording: Recording, n_samples: int) -> np.ndarray:
    seconds = np.floor(np.arange(n_samples) / recording.fs).astype(int)
    result = np.full(n_samples, np.nan)
    covered = seconds < recording.labels.size
    result[covered] = recording.labels[seconds[covered]]
    return result


def analyze_raw_bouts(recording: Recording) -> tuple[pd.DataFrame, dict]:
    """Measure each score-run mean and its peak-anchored NE-event shape."""
    n_samples = common_start_samples(recording)
    signal = recording.ne[:n_samples]
    labels = _sample_labels(recording, n_samples)
    finite_stretches = runs(np.isfinite(signal))
    rows = []
    for state_label, state in STATES.items():
        valid = np.isfinite(signal) & (labels == state_label)
        for start, stop in runs(valid):
            values = signal[start:stop]
            peak = int(np.argmax(values))
            absolute_peak = start + peak
            raw_peak = float(values[peak])
            complete = False
            l20 = l80 = r80 = r20 = np.nan
            crossing_state_boundary = False
            stretch_start, stretch_stop = next(
                (left, right) for left, right in finite_stretches if left <= absolute_peak < right
            )
            stretch = signal[stretch_start:stretch_stop]
            stretch_peak = absolute_peak - stretch_start
            if raw_peak > 0 and 0 < stretch_peak < len(stretch) - 1:
                l20 = crossing(stretch, 0, stretch_peak, 0.2 * raw_peak, True)
                l80 = crossing(stretch, 0, stretch_peak, 0.8 * raw_peak, True)
                r80 = crossing(stretch, stretch_peak, len(stretch) - 1, 0.8 * raw_peak, False)
                r20 = crossing(stretch, stretch_peak, len(stretch) - 1, 0.2 * raw_peak, False)
                complete = bool(np.all(np.isfinite([l20, l80, r80, r20])) and l20 < l80 < r80 < r20)
                if complete:
                    support = labels[
                        stretch_start + int(np.floor(l20)) : stretch_start + int(np.ceil(r20)) + 1
                    ]
                    crossing_state_boundary = not bool(np.all(support == state_label))
            absolute = lambda sample: recording.start_time + sample / recording.fs
            rows.append(
                {
                    **recording.identity,
                    "state": state,
                    "bout_index": len(rows),
                    "onset_seconds": absolute(start),
                    "offset_seconds": absolute(stop),
                    "bout_duration_seconds": len(values) / recording.fs,
                    "peak_seconds": absolute(absolute_peak),
                    "raw_peak": raw_peak,
                    "raw_bout_mean": float(np.mean(values)),
                    "rise20_seconds": absolute(stretch_start + l20) if np.isfinite(l20) else np.nan,
                    "rise80_seconds": absolute(stretch_start + l80) if np.isfinite(l80) else np.nan,
                    "decay80_seconds": absolute(stretch_start + r80) if np.isfinite(r80) else np.nan,
                    "decay20_seconds": absolute(stretch_start + r20) if np.isfinite(r20) else np.nan,
                    "complete_shape": complete,
                    "crosses_state_boundary": crossing_state_boundary,
                    "duration_seconds": (r20 - l20) / recording.fs if complete else np.nan,
                    "rise_slope": 0.6 * raw_peak * recording.fs / (l80 - l20) if complete else np.nan,
                    "decay_slope": 0.6 * raw_peak * recording.fs / (r20 - r80) if complete else np.nan,
                }
            )
    audit = {
        **recording.identity,
        "ne_samples": int(recording.ne.size),
        "sleep_label_seconds": int(recording.labels.size),
        "ne_duration_seconds": recording.ne.size / recording.fs,
        "common_start_samples": n_samples,
        "common_start_seconds": min(recording.ne.size / recording.fs, recording.labels.size),
        "tail_ne_seconds_not_analyzed": max(0.0, recording.ne.size / recording.fs - recording.labels.size),
        "tail_label_seconds_not_analyzed": max(0.0, recording.labels.size - recording.ne.size / recording.fs),
    }
    return pd.DataFrame(rows), audit


def _median_iqr(values: pd.Series) -> tuple[float, float, float]:
    values = values.dropna()
    if values.empty:
        return np.nan, np.nan, np.nan
    return float(values.median()), float(values.quantile(0.25)), float(values.quantile(0.75))


def summarize_recordings(bouts: pd.DataFrame, audits: pd.DataFrame) -> pd.DataFrame:
    """Create one row per MAT file, with bout medians and IQRs within each state."""
    summaries = []
    for recording_id, audit in audits.set_index("recording_id").iterrows():
        row = audit.to_dict()
        row["recording_id"] = recording_id
        for state in STATES.values():
            selected = bouts.loc[(bouts.recording_id == recording_id) & (bouts.state == state)]
            row[f"{state}_n_bouts"] = len(selected)
            row[f"{state}_n_complete_shapes"] = int(selected.complete_shape.sum())
            for metric in RAW_METRICS:
                median, lower, upper = _median_iqr(selected[metric])
                row[f"{state}_{metric}_median"] = median
                row[f"{state}_{metric}_iqr_lower"] = lower
                row[f"{state}_{metric}_iqr_upper"] = upper
        summaries.append(row)
    return pd.DataFrame(summaries).sort_values("recording_id").reset_index(drop=True)


def paired_recording_results(summaries: pd.DataFrame) -> pd.DataFrame:
    """Paired recording-level results; independence of files is deliberately assumed."""
    rows = []
    for metric in RECORDING_METRICS:
        if (
            f"active_wake_{metric}_median" not in summaries
            or f"quiet_wake_{metric}_median" not in summaries
        ):
            continue
        active = summaries[f"active_wake_{metric}_median"]
        quiet = summaries[f"quiet_wake_{metric}_median"]
        paired = pd.DataFrame({"active": active, "quiet": quiet}).dropna()
        active_median, active_lower, active_upper = _median_iqr(paired.active)
        quiet_median, quiet_lower, quiet_upper = _median_iqr(paired.quiet)
        p_value = np.nan
        if len(paired) and not (paired.active - paired.quiet).eq(0).all():
            p_value = float(wilcoxon(paired.active, paired.quiet, alternative="two-sided", method="auto").pvalue)
        rows.append(
            {
                "metric": metric,
                "n_recording_pairs": len(paired),
                "active_median": active_median,
                "active_iqr_lower": active_lower,
                "active_iqr_upper": active_upper,
                "quiet_median": quiet_median,
                "quiet_iqr_lower": quiet_lower,
                "quiet_iqr_upper": quiet_upper,
                "p_value": p_value,
            }
        )
    return pd.DataFrame(rows)


def independent_bout_results(bouts: pd.DataFrame) -> pd.DataFrame:
    """Summarize all bouts and run an explicitly exploratory unpaired screen.

    This intentionally ignores recording and mouse membership.  The resulting
    Mann--Whitney p-values are useful for describing the available bouts, but are
    not valid animal-level evidence and must remain labelled as pseudoreplicated.
    """
    rows = []
    for metric in INDEPENDENT_BOUT_METRICS:
        active = bouts.loc[bouts.state == "active_wake", metric].dropna()
        quiet = bouts.loc[bouts.state == "quiet_wake", metric].dropna()
        active_median, active_lower, active_upper = _median_iqr(active)
        quiet_median, quiet_lower, quiet_upper = _median_iqr(quiet)
        p_value = np.nan
        if len(active) and len(quiet):
            p_value = float(mannwhitneyu(active, quiet, alternative="two-sided", method="auto").pvalue)
        rows.append(
            {
                "metric": metric,
                "n_active_bouts": len(active),
                "n_quiet_bouts": len(quiet),
                "active_median": active_median,
                "active_iqr_lower": active_lower,
                "active_iqr_upper": active_upper,
                "quiet_median": quiet_median,
                "quiet_iqr_lower": quiet_lower,
                "quiet_iqr_upper": quiet_upper,
                "p_value": p_value,
            }
        )
    return pd.DataFrame(rows)


def _paired_results(summaries: pd.DataFrame, metrics: tuple[str, ...]) -> pd.DataFrame:
    """Calculate paired recording screens for specified state-summary metrics."""
    rows = []
    for metric in metrics:
        active = summaries[f"active_wake_{metric}"]
        quiet = summaries[f"quiet_wake_{metric}"]
        paired = pd.DataFrame({"active": active, "quiet": quiet}).dropna()
        active_median, active_lower, active_upper = _median_iqr(paired.active)
        quiet_median, quiet_lower, quiet_upper = _median_iqr(paired.quiet)
        p_value = np.nan
        if len(paired) and not (paired.active - paired.quiet).eq(0).all():
            p_value = float(wilcoxon(paired.active, paired.quiet, alternative="two-sided", method="auto").pvalue)
        rows.append(
            {
                "metric": metric,
                "n_recording_pairs": len(paired),
                "active_median": active_median,
                "active_iqr_lower": active_lower,
                "active_iqr_upper": active_upper,
                "quiet_median": quiet_median,
                "quiet_iqr_lower": quiet_lower,
                "quiet_iqr_upper": quiet_upper,
                "p_value": p_value,
            }
        )
    return pd.DataFrame(rows)


def analyze_raw_spectra(input_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Compute the raw report's per-file and deliberately independent-window spectra."""
    files = sorted(Path(input_dir).glob("*.mat"), key=lambda path: path.name.casefold())
    if not files:
        raise ValueError(f"No MAT files found in {input_dir}.")
    spectra, windows, summaries = [], [], []
    for path in files:
        recording = _common_start_recording(load_recording(path, path.stem, path.stem))
        file_spectra, file_windows = compute_spectrum(recording, RAW_SPECTRUM)
        spectra.append(file_spectra)
        windows.append(file_windows)
        summary = {**recording.identity}
        for state in STATES.values():
            selected = file_spectra.loc[file_spectra.state == state]
            summary[f"{state}_n_windows"] = int(selected.n_windows.iloc[0]) if len(selected) else 0
            metrics = spectral_metrics(selected)
            summary.update({f"{state}_{name}": value for name, value in metrics.items()})
        summaries.append(summary)
    spectra = pd.concat(spectra, ignore_index=True)
    windows = pd.concat(windows, ignore_index=True)
    summaries = pd.DataFrame(summaries).sort_values("recording_id").reset_index(drop=True)
    return spectra, windows, summaries, _paired_results(summaries, SPECTRAL_METRICS)


def independent_spectral_window_results(windows: pd.DataFrame) -> pd.DataFrame:
    """Describe spectral windows while explicitly ignoring their recording hierarchy."""
    rows = []
    for metric in ("band_power",):
        active = windows.loc[windows.state == "active_wake", metric].dropna()
        quiet = windows.loc[windows.state == "quiet_wake", metric].dropna()
        active_median, active_lower, active_upper = _median_iqr(active)
        quiet_median, quiet_lower, quiet_upper = _median_iqr(quiet)
        p_value = np.nan
        if len(active) and len(quiet):
            p_value = float(mannwhitneyu(active, quiet, alternative="two-sided", method="auto").pvalue)
        rows.append(
            {
                "metric": metric,
                "n_active_windows": len(active),
                "n_quiet_windows": len(quiet),
                "active_median": active_median,
                "active_iqr_lower": active_lower,
                "active_iqr_upper": active_upper,
                "quiet_median": quiet_median,
                "quiet_iqr_lower": quiet_lower,
                "quiet_iqr_upper": quiet_upper,
                "p_value": p_value,
            }
        )
    return pd.DataFrame(rows)


def analyze_directory(input_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Analyze every MAT file in a directory as a separately named recording."""
    files = sorted(Path(input_dir).glob("*.mat"), key=lambda path: path.name.casefold())
    if not files:
        raise ValueError(f"No MAT files found in {input_dir}.")
    bout_tables, audits = [], []
    for path in files:
        recording = load_recording(path, path.stem, path.stem)
        bouts, audit = analyze_raw_bouts(recording)
        bout_tables.append(bouts)
        audits.append(audit)
    audits = pd.DataFrame(audits)
    bouts = pd.concat(bout_tables, ignore_index=True)
    summaries = summarize_recordings(bouts, audits)
    return bouts, summaries, paired_recording_results(summaries)


def label_geometry_directory(input_dir: Path) -> pd.DataFrame:
    """Audit literal one-second score runs separately from NE measurements."""
    files = sorted(Path(input_dir).glob("*.mat"), key=lambda path: path.name.casefold())
    rows = []
    for path in files:
        recording = load_recording(path, path.stem, path.stem)
        for state_label, state in STATES.items():
            durations = np.array([stop - start for start, stop in runs(recording.labels == state_label)])
            rows.append(
                {
                    **recording.identity,
                    "state": state,
                    "n_score_bouts": len(durations),
                    "labelled_seconds": int(durations.sum()),
                    "bout_duration_median_seconds": float(np.median(durations)) if len(durations) else np.nan,
                    "bout_duration_iqr_lower_seconds": float(np.quantile(durations, 0.25)) if len(durations) else np.nan,
                    "bout_duration_iqr_upper_seconds": float(np.quantile(durations, 0.75)) if len(durations) else np.nan,
                    "bouts_at_most_five_seconds": int((durations <= 5).sum()),
                }
            )
    return pd.DataFrame(rows)


def score_label_bouts_directory(input_dir: Path) -> pd.DataFrame:
    """Return every literal maximal one-second score run for duration auditing."""
    files = sorted(Path(input_dir).glob("*.mat"), key=lambda path: path.name.casefold())
    rows = []
    for path in files:
        recording = load_recording(path, path.stem, path.stem)
        for state_label, state in STATES.items():
            for start, stop in runs(recording.labels == state_label):
                rows.append(
                    {
                        **recording.identity,
                        "state": state,
                        "onset_seconds": recording.start_time + start,
                        "offset_seconds": recording.start_time + stop,
                        "score_bout_duration_seconds": stop - start,
                    }
                )
    return pd.DataFrame(rows)


def add_score_bout_metrics(
    summaries: pd.DataFrame, label_geometry: pd.DataFrame
) -> pd.DataFrame:
    """Add literal score-run duration and count to recording-level summaries.

    These values are intentionally derived from every saved one-second score run,
    rather than from the NE-valid runs used for the raw-mean and shape metrics.
    """
    result = summaries.copy()
    for state in STATES.values():
        selected = label_geometry.loc[
            label_geometry.state == state,
            ["recording_id", "n_score_bouts", "bout_duration_median_seconds"],
        ].set_index("recording_id")
        result[f"{state}_score_bout_count_median"] = result.recording_id.map(
            selected.n_score_bouts
        )
        result[f"{state}_score_bout_duration_seconds_median"] = result.recording_id.map(
            selected.bout_duration_median_seconds
        )
    return result


def write_directory_analysis(input_dir: Path, output_dir: Path) -> None:
    """Write auditable raw-bout tables for the separate preliminary comparison."""
    output_dir = Path(output_dir)
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError(f"Output directory must be new or empty: {output_dir}")
    bouts, summaries, _ = analyze_directory(input_dir)
    label_geometry = label_geometry_directory(input_dir)
    score_label_bouts = score_label_bouts_directory(input_dir)
    summaries = add_score_bout_metrics(summaries, label_geometry)
    results = paired_recording_results(summaries)
    bout_results = independent_bout_results(bouts)
    spectra, spectral_windows, spectral_summaries, spectral_results = analyze_raw_spectra(input_dir)
    spectral_window_results = independent_spectral_window_results(spectral_windows)
    output_dir.mkdir(parents=True, exist_ok=True)
    bouts.to_csv(output_dir / "bouts.csv", index=False)
    label_geometry.to_csv(output_dir / "score_label_geometry.csv", index=False)
    score_label_bouts.to_csv(output_dir / "score_label_bouts.csv", index=False)
    summaries.to_csv(output_dir / "recordings.csv", index=False)
    results.to_csv(output_dir / "paired_recording_results.csv", index=False)
    bout_results.to_csv(output_dir / "independent_bout_results.csv", index=False)
    spectra.to_csv(output_dir / "recording_spectra.csv", index=False)
    spectral_windows.to_csv(output_dir / "spectral_windows.csv", index=False)
    spectral_summaries.to_csv(output_dir / "spectral_recordings.csv", index=False)
    spectral_results.to_csv(output_dir / "paired_spectral_results.csv", index=False)
    spectral_window_results.to_csv(output_dir / "independent_spectral_window_results.csv", index=False)
