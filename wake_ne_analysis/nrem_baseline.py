"""NREM-anchored experimental Wake relabeling and target-cluster calibration.

This module deliberately works beside, rather than inside, the sleep-scoring
application.  It never writes a source MAT file.  The only labels it creates are
auditable experimental predictions for the sampled Wake seconds used by a
pre-existing graph-cluster analysis.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import signal
from scipy.io import loadmat
from scipy.ndimage import uniform_filter1d


NREM_LABEL = 1
WAKE_LABELS = (4, 5)
ENVELOPE_RATE_HZ = 20


@dataclass(frozen=True)
class NremBaselineConfig:
    """Fixed portions of the prior NREM-envelope Wake rule.

    ``deviation_multiplier`` is the one parameter calibrated to graph targets.
    A recording's threshold is its NREM-envelope percentile plus this multiplier
    times its NREM robust standard deviation; it is not a pooled EMG amplitude.
    """

    nrem_baseline_percentile: float = 75.0
    deviation_multiplier: float = 2.0
    min_duration_seconds: float = 1.0
    gap_tolerance_seconds: float = 0.5
    rms_window_seconds: float = 0.5
    envelope_rate_hz: int = ENVELOPE_RATE_HZ

    def __post_init__(self):
        if not np.isfinite(self.nrem_baseline_percentile) or not 0 <= self.nrem_baseline_percentile <= 100:
            raise ValueError("NREM baseline percentile must be between 0 and 100.")
        if not np.isfinite(self.deviation_multiplier) or self.deviation_multiplier < 0:
            raise ValueError("NREM deviation multiplier must be finite and non-negative.")
        if not np.isfinite(self.min_duration_seconds) or self.min_duration_seconds <= 0:
            raise ValueError("Minimum active duration must be positive.")
        if not np.isfinite(self.gap_tolerance_seconds) or self.gap_tolerance_seconds < 0:
            raise ValueError("Gap tolerance must be finite and non-negative.")
        if not np.isfinite(self.rms_window_seconds) or self.rms_window_seconds <= 0:
            raise ValueError("RMS window must be positive.")
        if self.envelope_rate_hz != ENVELOPE_RATE_HZ:
            raise ValueError("This experimental comparison fixes the EMG envelope at 20 Hz.")


@dataclass(frozen=True)
class NremBaselineResult:
    """Per-recording NREM-baseline prediction, with the reference audit."""

    active_seconds: np.ndarray
    threshold: float
    nrem_percentile: float
    nrem_robust_sd: float
    nrem_samples: int
    wake_seconds: int


@dataclass(frozen=True)
class PreparedNremBaseline:
    """Raw-data quantities shared by every multiplier for one recording."""

    envelope: np.ndarray
    wake: np.ndarray
    nrem_percentile: float
    nrem_robust_sd: float
    nrem_samples: int

def _runs(mask: np.ndarray):
    edges = np.diff(np.r_[False, np.asarray(mask, dtype=bool), False].astype(int))
    return zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1))


def _vector(value, name: str) -> np.ndarray:
    result = np.asarray(value, dtype=float).squeeze()
    if result.ndim > 1:
        raise ValueError(f"{name} must be a single-channel vector.")
    return result.reshape(-1)


def _positive_scalar(value, name: str) -> float:
    if np.asarray(value).size != 1:
        raise ValueError(f"{name} must be scalar.")
    result = float(np.asarray(value).item())
    if not np.isfinite(result) or result <= 50:
        raise ValueError(f"{name} must be finite and greater than 50 Hz.")
    return result


def load_emg_and_labels(path: Path) -> tuple[np.ndarray, float, np.ndarray]:
    """Load only fields needed for experimental relabeling from one source MAT."""
    path = Path(path).resolve()
    mat = loadmat(path, squeeze_me=True, variable_names=("emg", "eeg_frequency", "sleep_scores"))
    missing = [name for name in ("emg", "eeg_frequency", "sleep_scores") if name not in mat]
    if missing:
        raise ValueError(f"Missing required field(s) in {path.name}: {', '.join(missing)}.")
    emg = _vector(mat["emg"], "emg")
    labels = _vector(mat["sleep_scores"], "sleep_scores")
    labels[labels == -1] = np.nan
    if np.any(~np.isnan(labels) & ~np.isin(labels, (0, 1, 2, 3, 4, 5))):
        raise ValueError(f"Unknown sleep label in {path.name}.")
    return emg, _positive_scalar(mat["eeg_frequency"], "eeg_frequency"), labels


def emg_envelope(emg: np.ndarray, fs: float, config: NremBaselineConfig) -> np.ndarray:
    """Replicate the prior scoring-family 20 Hz, 0.5 s moving-RMS envelope."""
    raw = np.asarray(emg, dtype=float).reshape(-1)
    if raw.size < math.ceil(fs):
        raise ValueError("At least one second of raw EMG is required.")
    valid = np.isfinite(raw)
    for start, stop in _runs(np.r_[False, np.diff(raw) == 0]):
        if stop - start + 1 >= fs:
            valid[max(0, start - 1) : stop] = False
    high = min(200.0, 0.45 * fs)
    if high <= 20:
        raise ValueError("EMG sampling cannot support the 20 Hz band-pass lower edge.")
    sos = signal.butter(4, [20, high], btype="bandpass", fs=fs, output="sos")
    width = max(1, round(config.rms_window_seconds * fs))
    power = np.full(raw.size, np.nan)
    for start, stop in _runs(valid):
        if stop - start <= max(width, 30):
            continue
        filtered = signal.sosfiltfilt(sos, signal.detrend(raw[start:stop], type="linear"))
        rms = np.sqrt(np.maximum(uniform_filter1d(filtered**2, width, mode="nearest"), 0))
        left = width // 2 if start else 0
        right = width // 2 if stop < raw.size else 0
        usable_stop = stop - right
        power[start + left : usable_stop] = rms[left : len(rms) - right if right else None]
    count = math.ceil(raw.size / fs * config.envelope_rate_hz)
    centres = (np.arange(count) + 0.5) / config.envelope_rate_hz
    sample_indices = np.minimum((centres * fs).astype(int), raw.size - 1)
    return power[sample_indices]


def _active_mask(
    envelope: np.ndarray, wake_mask: np.ndarray, threshold: float, config: NremBaselineConfig
) -> np.ndarray:
    eligible = np.repeat(wake_mask, config.envelope_rate_hz)[: len(envelope)]
    eligible &= np.isfinite(envelope)
    active = (envelope > threshold) & eligible
    max_gap = math.floor(config.gap_tolerance_seconds * config.envelope_rate_hz + 1e-9)
    for start, stop in _runs(~active):
        if start > 0 and stop < len(active) and stop - start <= max_gap and eligible[start:stop].all():
            active[start:stop] = True
    minimum = math.ceil(config.min_duration_seconds * config.envelope_rate_hz - 1e-9)
    for start, stop in _runs(active):
        if stop - start < minimum:
            active[start:stop] = False
    return active


def _second_activity(active: np.ndarray, length: int, rate: int) -> np.ndarray:
    bins = np.arange(len(active)) // rate
    counts = np.bincount(bins, minlength=length)[:length]
    active_counts = np.bincount(bins, weights=active, minlength=length)[:length]
    return (counts > 0) & (active_counts >= 0.5 * counts)


def prepare_nrem_baseline(
    emg: np.ndarray, fs: float, labels: np.ndarray, config: NremBaselineConfig
) -> PreparedNremBaseline:
    """Compute the recording-specific envelope and NREM reference once."""
    labels = np.asarray(labels, dtype=float).reshape(-1)
    wake = np.isin(labels, WAKE_LABELS)
    if not wake.any():
        raise ValueError("No existing Active/Quiet Wake seconds are available for experimental relabeling.")
    envelope = emg_envelope(emg, fs, config)[: len(labels) * config.envelope_rate_hz]
    bins = np.arange(len(envelope)) // config.envelope_rate_hz
    counts = np.bincount(bins, minlength=len(labels))[: len(labels)]
    invalid = np.bincount(bins, weights=~np.isfinite(envelope), minlength=len(labels))[: len(labels)]
    if np.any(wake & ((counts == 0) | (invalid > 0))):
        raise ValueError("Wake contains missing, flatlined, or invalid EMG; no experimental labels were made.")
    nrem_bins = np.repeat(labels == NREM_LABEL, config.envelope_rate_hz)[: len(envelope)]
    reference = envelope[nrem_bins & np.isfinite(envelope)]
    if not len(reference):
        raise ValueError("Valid NREM EMG is required for the automatic baseline.")
    median = float(np.median(reference))
    robust_sd = float(1.4826 * np.median(np.abs(reference - median)))
    percentile = float(np.percentile(reference, config.nrem_baseline_percentile))
    return PreparedNremBaseline(
        envelope=envelope,
        wake=wake,
        nrem_percentile=percentile,
        nrem_robust_sd=robust_sd,
        nrem_samples=int(len(reference)),
    )


def classify_prepared_nrem_baseline(
    prepared: PreparedNremBaseline, config: NremBaselineConfig
) -> NremBaselineResult:
    """Apply one threshold multiplier to a prepared recording."""
    threshold = prepared.nrem_percentile + config.deviation_multiplier * prepared.nrem_robust_sd
    active = _active_mask(prepared.envelope, prepared.wake, threshold, config)
    return NremBaselineResult(
        active_seconds=_second_activity(active, len(prepared.wake), config.envelope_rate_hz),
        threshold=threshold,
        nrem_percentile=prepared.nrem_percentile,
        nrem_robust_sd=prepared.nrem_robust_sd,
        nrem_samples=prepared.nrem_samples,
        wake_seconds=int(prepared.wake.sum()),
    )


def classify_nrem_baseline(
    emg: np.ndarray, fs: float, labels: np.ndarray, config: NremBaselineConfig
) -> NremBaselineResult:
    """Classify the source's existing Wake seconds without modifying source labels."""
    return classify_prepared_nrem_baseline(prepare_nrem_baseline(emg, fs, labels, config), config)


def _classification_metrics(predicted: np.ndarray, target: np.ndarray) -> dict[str, float | int]:
    predicted, target = np.asarray(predicted, dtype=bool), np.asarray(target, dtype=bool)
    tp = int(np.count_nonzero(predicted & target))
    fp = int(np.count_nonzero(predicted & ~target))
    fn = int(np.count_nonzero(~predicted & target))
    tn = int(np.count_nonzero(~predicted & ~target))
    precision = tp / (tp + fp) if tp + fp else np.nan
    recall = tp / (tp + fn) if tp + fn else np.nan
    specificity = tn / (tn + fp) if tn + fp else np.nan
    f1 = 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else np.nan
    return {
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
        "true_negative": tn,
        "precision": precision,
        "recall": recall,
        "specificity": specificity,
        "f1": f1,
    }


def _target_points(clustered_points: pd.DataFrame, target_clusters: tuple[int, ...]) -> pd.DataFrame:
    required = {"recording_id", "second", "cluster"}
    missing = required - set(clustered_points.columns)
    if missing:
        raise ValueError(f"Clustered points are missing required column(s): {', '.join(sorted(missing))}.")
    points = clustered_points.loc[:, ["recording_id", "second", "cluster"]].copy()
    points.recording_id = points.recording_id.astype(str)
    points.second = pd.to_numeric(points.second, errors="raise").astype(int)
    points.cluster = pd.to_numeric(points.cluster, errors="raise").astype(int)
    if points.duplicated(["recording_id", "second"]).any():
        raise ValueError("Each clustered recording/second pair must appear exactly once.")
    points["is_target_cluster"] = points.cluster.isin(target_clusters)
    if not points.is_target_cluster.any():
        raise ValueError("None of the requested target clusters appear in clustered points.")
    return points


def calibrate_to_cluster_targets(
    input_dir: Path,
    clustered_points: pd.DataFrame,
    target_clusters: tuple[int, ...],
    multipliers: np.ndarray,
    base_config: NremBaselineConfig = NremBaselineConfig(),
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    """Sweep a shared NREM multiplier and select it by target-bearing-recording F1.

    The graph partitions are targets only.  The selection metric is the mean F1
    across recordings containing at least one target point, so a long recording
    cannot dominate and target-absent recordings cannot favour an all-Quiet rule.
    Ties prefer higher mean specificity and then the stricter multiplier.
    """
    multipliers = np.unique(np.asarray(multipliers, dtype=float))
    if not len(multipliers) or not np.isfinite(multipliers).all() or (multipliers < 0).any():
        raise ValueError("Multipliers must be a non-empty list of finite non-negative values.")
    points = _target_points(clustered_points, target_clusters)
    input_dir = Path(input_dir)
    files = {path.stem: path for path in input_dir.glob("*.mat")}
    missing_files = sorted(set(points.recording_id) - set(files))
    if missing_files:
        raise ValueError(f"No source MAT file for clustered recording(s): {', '.join(missing_files)}.")

    detail_rows, summary_rows = [], []
    predictions_by_multiplier = {float(multiplier): [] for multiplier in multipliers}
    for recording_id, group in points.groupby("recording_id", sort=True):
        emg, fs, labels = load_emg_and_labels(files[recording_id])
        prepared = prepare_nrem_baseline(emg, fs, labels, base_config)
        seconds = group.second.to_numpy()
        if (seconds < 0).any() or (seconds >= len(prepared.wake)).any():
            raise ValueError(f"Clustered second is outside {recording_id}'s score vector.")
        target = group.is_target_cluster.to_numpy(dtype=bool)
        for multiplier in multipliers:
            config = NremBaselineConfig(
                nrem_baseline_percentile=base_config.nrem_baseline_percentile,
                deviation_multiplier=float(multiplier),
                min_duration_seconds=base_config.min_duration_seconds,
                gap_tolerance_seconds=base_config.gap_tolerance_seconds,
                rms_window_seconds=base_config.rms_window_seconds,
            )
            result = classify_prepared_nrem_baseline(prepared, config)
            predicted = result.active_seconds[seconds]
            full_active_seconds = int(np.count_nonzero(result.active_seconds & prepared.wake))
            full_quiet_seconds = result.wake_seconds - full_active_seconds
            metrics = _classification_metrics(predicted, target)
            row = {
                "multiplier": float(multiplier),
                "recording_id": recording_id,
                "n_sampled_seconds": int(len(group)),
                "n_target_seconds": int(target.sum()),
                "n_selected_seconds": int(predicted.sum()),
                "nrem_threshold": result.threshold,
                "nrem_percentile": result.nrem_percentile,
                "nrem_robust_sd": result.nrem_robust_sd,
                "nrem_samples": result.nrem_samples,
                "source_wake_seconds": result.wake_seconds,
                "experimental_active_wake_seconds": full_active_seconds,
                "experimental_quiet_wake_seconds": full_quiet_seconds,
                "experimental_active_wake_fraction": full_active_seconds / result.wake_seconds,
                **metrics,
            }
            detail_rows.append(row)
            audit = group.copy()
            audit["experimental_active_wake"] = predicted
            audit["multiplier"] = float(multiplier)
            audit["nrem_threshold"] = result.threshold
            predictions_by_multiplier[float(multiplier)].append(audit)
    details = pd.DataFrame(detail_rows)
    for multiplier in multipliers:
        detail = details.loc[details.multiplier == multiplier].copy()
        target_bearing = detail.loc[detail.n_target_seconds > 0]
        totals = detail[["true_positive", "false_positive", "false_negative", "true_negative"]].sum()
        # Reconstruct aggregate counts directly so metrics are not sensitive to row order.
        global_metrics = _classification_metrics(
            np.r_[np.ones(int(totals.true_positive), bool), np.ones(int(totals.false_positive), bool), np.zeros(int(totals.false_negative + totals.true_negative), bool)],
            np.r_[np.ones(int(totals.true_positive), bool), np.zeros(int(totals.false_positive), bool), np.ones(int(totals.false_negative), bool), np.zeros(int(totals.true_negative), bool)],
        )
        summary_rows.append(
            {
                "multiplier": float(multiplier),
                "n_recordings": int(len(detail)),
                "n_target_bearing_recordings": int(len(target_bearing)),
                "macro_target_recording_f1": target_bearing.f1.mean(),
                "macro_target_recording_recall": target_bearing.recall.mean(),
                "macro_all_recording_specificity": detail.specificity.mean(),
                "sampled_selected_fraction": detail.n_selected_seconds.sum() / detail.n_sampled_seconds.sum(),
                "experimental_active_wake_seconds": int(detail.experimental_active_wake_seconds.sum()),
                "experimental_quiet_wake_seconds": int(detail.experimental_quiet_wake_seconds.sum()),
                "experimental_active_wake_fraction": (
                    detail.experimental_active_wake_seconds.sum() / detail.source_wake_seconds.sum()
                ),
                **global_metrics,
            }
        )
    summary = pd.DataFrame(summary_rows).sort_values("multiplier").reset_index(drop=True)
    best = summary.sort_values(
        ["macro_target_recording_f1", "macro_all_recording_specificity", "multiplier"],
        ascending=[False, False, False],
        kind="stable",
    ).iloc[0]
    selected_multiplier = float(best.multiplier)
    selected_detail = details.loc[details.multiplier == selected_multiplier].copy()
    selection = {
        "selection_rule": "maximize mean F1 across target-bearing recordings; ties maximize mean specificity across all recordings, then choose the stricter multiplier",
        "target_clusters": list(target_clusters),
        "selected_multiplier": selected_multiplier,
        "base_config": asdict(base_config),
        "selected_summary": best.to_dict(),
    }
    return summary, selected_detail, pd.concat(predictions_by_multiplier[selected_multiplier], ignore_index=True), selection
