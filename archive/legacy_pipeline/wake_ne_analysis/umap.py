"""Small, auditable per-second EEG/EMG/NE feature extraction for exploratory UMAP."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import signal
from scipy.io import loadmat


LABEL_NAMES = {
    1: "nrem",
    2: "rem",
    3: "ma",
    4: "active_wake",
    5: "quiet_wake",
}
FEATURE_COLUMNS = ("eeg_delta_log10_power", "eeg_theta_log10_power", "emg_centered_rms", "ne_mean")
EMBEDDING_FEATURE_SETS = {
    "joint": FEATURE_COLUMNS,
    "eeg_ne": ("eeg_delta_log10_power", "eeg_theta_log10_power", "ne_mean"),
}
STATE_ORDER = ("nrem", "rem", "ma", "active_wake", "quiet_wake")
STATE_LABELS = {
    "nrem": "NREM",
    "rem": "REM",
    "ma": "MA",
    "active_wake": "Active Wake",
    "quiet_wake": "Quiet Wake",
}
# Exact RGB values from sleep_scoring/app_src/config.py, converted to Matplotlib hex.
STAGE_COLORS = {
    "nrem": "#FB7C7C",
    "rem": "#7BFB7B",
    "ma": "#FFFF00",
    "active_wake": "#E69F00",
    "quiet_wake": "#56B4E9",
}


@dataclass(frozen=True)
class UmapConfig:
    """Fixed first-pass settings; labels are never supplied to UMAP fitting."""

    random_seed: int = 20260917
    max_points_per_label_per_recording: int = 10
    n_neighbors: int = 30
    min_dist: float = 0.2
    n_epochs: int = 50
    delta_band_hz: tuple[float, float] = (0.5, 4.0)
    theta_band_hz: tuple[float, float] = (6.0, 9.0)

    def __post_init__(self):
        if self.max_points_per_label_per_recording < 1:
            raise ValueError("max_points_per_label_per_recording must be positive.")
        if self.n_neighbors < 2:
            raise ValueError("n_neighbors must be at least two.")
        if not 0 <= self.min_dist <= 1:
            raise ValueError("min_dist must be in [0, 1].")


def _vector(value, name):
    result = np.asarray(value, dtype=float).squeeze()
    if result.ndim > 1:
        raise ValueError(f"{name} must be a single-channel vector.")
    return result.reshape(-1)


def _signal_vector(value, name):
    """Return raw physiological data as float32; feature precision does not need a float64 copy."""
    result = np.asarray(value).squeeze()
    if result.ndim > 1:
        raise ValueError(f"{name} must be a single-channel vector.")
    return result.reshape(-1).astype(np.float32, copy=False)


def _scalar(value, name):
    if np.asarray(value).size != 1:
        raise ValueError(f"{name} must be scalar.")
    result = float(np.asarray(value).item())
    if not np.isfinite(result) or result <= 0:
        raise ValueError(f"{name} must be finite and positive.")
    return result


def _epoch_bounds(n_seconds, fs, size):
    """Return complete one-second sample intervals, without resampling a source trace."""
    edges = np.rint(np.arange(n_seconds + 1) * fs).astype(int)
    starts, stops = edges[:-1], edges[1:]
    complete = (starts >= 0) & (stops <= size) & (stops > starts)
    return starts, stops, complete


def _fixed_epoch_matrix(values, starts, width):
    """Use the first whole-sample second from each epoch for one-second EEG/EMG features."""
    rows = starts[:, None] + np.arange(width)
    if rows.size and rows.max() >= values.size:
        raise ValueError("Epoch matrix would exceed source signal.")
    return values[rows]


def _band_powers_per_second(eeg, eeg_fs, starts, bands, block_seconds=256):
    """Return one PSD bandpower vector per band without materializing every epoch at once."""
    width = int(np.floor(eeg_fs))
    if width < 16:
        raise ValueError("eeg_frequency is too low for one-second spectral features.")
    results = [np.full(starts.size, np.nan) for _ in bands]
    for first in range(0, starts.size, block_seconds):
        selection = slice(first, first + block_seconds)
        epochs = _fixed_epoch_matrix(eeg, starts[selection], width)
        frequencies, psd = signal.periodogram(
            epochs, fs=eeg_fs, window="hann", detrend="constant", scaling="density", axis=1
        )
        for result, band in zip(results, bands):
            selected = (frequencies >= band[0]) & (frequencies <= band[1])
            if selected.sum() < 2:
                raise ValueError(f"No resolvable EEG bins in {band[0]}-{band[1]} Hz.")
            result[selection] = np.trapezoid(psd[:, selected], frequencies[selected], axis=1)
    return results


def _emg_centered_rms_per_second(emg, emg_fs, starts):
    """Return per-second broadband EMG variability after removing each epoch mean."""
    width = int(np.floor(emg_fs))
    if width < 16:
        raise ValueError("emg_frequency is too low for one-second EMG RMS.")
    rms = np.full(starts.size, np.nan)
    for first in range(0, starts.size, 256):
        selection = slice(first, first + 256)
        epochs = _fixed_epoch_matrix(emg, starts[selection], width)
        epochs = epochs - epochs.mean(axis=1, keepdims=True)
        rms[selection] = np.sqrt(np.mean(np.square(epochs), axis=1))
    return rms


def _mean_per_second(values, starts, stops):
    result = np.full(starts.size, np.nan)
    for index, (start, stop) in enumerate(zip(starts, stops)):
        segment = values[start:stop]
        if segment.size and np.isfinite(segment).all():
            result[index] = segment.mean()
    return result


def extract_recording_features(path, config=UmapConfig()):
    """Extract four predeclared features from complete labelled seconds of one MAT file."""
    path = Path(path).resolve()
    required = ["eeg", "emg", "ne", "eeg_frequency", "ne_frequency", "sleep_scores"]
    mat = loadmat(path, squeeze_me=True, variable_names=required)
    missing = [name for name in required if name not in mat or np.asarray(mat[name]).size == 0]
    if missing:
        raise ValueError(f"Missing required UMAP fields in {path.name}: {', '.join(missing)}.")
    eeg, emg, ne = (_signal_vector(mat[name], name) for name in ("eeg", "emg", "ne"))
    eeg_fs, ne_fs = (_scalar(mat[name], name) for name in ("eeg_frequency", "ne_frequency"))
    labels = _vector(mat["sleep_scores"], "sleep_scores")
    labels[labels == -1] = np.nan
    if np.any(~np.isnan(labels) & ~np.isin(labels, list(LABEL_NAMES)) & (labels != 0)):
        raise ValueError(f"Unknown sleep label in {path.name}.")

    n_seconds = labels.size
    eeg_starts, _, eeg_complete = _epoch_bounds(n_seconds, eeg_fs, eeg.size)
    emg_starts, _, emg_complete = _epoch_bounds(n_seconds, eeg_fs, emg.size)
    ne_starts, ne_stops, ne_complete = _epoch_bounds(n_seconds, ne_fs, ne.size)
    complete = eeg_complete & emg_complete & ne_complete
    selected_seconds = np.flatnonzero(complete)
    if not selected_seconds.size:
        raise ValueError(f"No complete multimodal seconds in {path.name}.")

    delta, theta = _band_powers_per_second(
        eeg,
        eeg_fs,
        eeg_starts[selected_seconds],
        (config.delta_band_hz, config.theta_band_hz),
    )
    emg_centered_rms = _emg_centered_rms_per_second(emg, eeg_fs, emg_starts[selected_seconds])
    ne_mean = _mean_per_second(ne, ne_starts[selected_seconds], ne_stops[selected_seconds])
    table = pd.DataFrame(
        {
            "recording_id": path.stem,
            "mat_path": str(path),
            "second": selected_seconds,
            "label": labels[selected_seconds],
            "eeg_delta_log10_power": np.log10(np.maximum(delta, np.finfo(float).tiny)),
            "eeg_theta_log10_power": np.log10(np.maximum(theta, np.finfo(float).tiny)),
            "emg_centered_rms": emg_centered_rms,
            "ne_mean": ne_mean,
        }
    )
    table["state"] = table.label.map(LABEL_NAMES)
    return table, {
        "recording_id": path.stem,
        "mat_path": str(path),
        "label_seconds": int(n_seconds),
        "complete_multimodal_seconds": int(complete.sum()),
        "eeg_frequency_hz": eeg_fs,
        "ne_frequency_hz": ne_fs,
    }


def extract_directory_features(input_dir, config=UmapConfig()):
    """Extract features sequentially, keeping only one raw MAT recording in memory at a time."""
    files = sorted(Path(input_dir).glob("*.mat"))
    if not files:
        raise ValueError(f"No MAT files found in {input_dir}.")
    tables, coverage = [], []
    for path in files:
        table, row = extract_recording_features(path, config)
        tables.append(table)
        coverage.append(row)
    result = pd.concat(tables, ignore_index=True)
    result = result.loc[result.state.notna() & np.isfinite(result.loc[:, FEATURE_COLUMNS]).all(axis=1)].copy()
    return result, pd.DataFrame(coverage)


def write_recording_feature_archives(input_dir, output_dir, config=UmapConfig()):
    """Write one compressed NumPy archive per MAT file for reusable feature analysis.

    Each ``.npz`` contains the raw and documented within-recording robust-scaled
    four-column matrices, their metadata, and no raw physiological samples.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    files = sorted(input_dir.glob("*.mat"))
    if not files:
        raise ValueError(f"No MAT files found in {input_dir}.")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError("Feature output directory must be new or empty.")
    output_dir.mkdir(parents=True, exist_ok=True)

    for path in files:
        raw, coverage = extract_recording_features(path, config)
        raw = raw.loc[raw.state.notna() & np.isfinite(raw.loc[:, FEATURE_COLUMNS]).all(axis=1)].copy()
        if raw.empty:
            raise ValueError(f"No finite labelled feature rows in {path.name}.")
        scaled, scales = robust_scale_within_recording(raw)
        archive_path = output_dir / f"{path.stem}.npz"
        np.savez_compressed(
            archive_path,
            X=raw.loc[:, FEATURE_COLUMNS].to_numpy(dtype=np.float32),
            X_robust_scaled=scaled.loc[:, FEATURE_COLUMNS].to_numpy(dtype=np.float32),
            second=raw.second.to_numpy(dtype=np.int32),
            label=raw.label.to_numpy(dtype=np.int8),
            feature_names=np.asarray(FEATURE_COLUMNS),
            scaling_median=scales.loc[0, [f"{name}_median" for name in FEATURE_COLUMNS]].to_numpy(dtype=np.float32),
            scaling_iqr=scales.loc[0, [f"{name}_iqr" for name in FEATURE_COLUMNS]].to_numpy(dtype=np.float32),
            recording_id=np.asarray(path.stem),
            source_mat_file=np.asarray(path.name),
            source_mat_path=np.asarray(str(path.resolve())),
            n_label_seconds=np.asarray(coverage["label_seconds"], dtype=np.int32),
            n_complete_multimodal_seconds=np.asarray(coverage["complete_multimodal_seconds"], dtype=np.int32),
            eeg_frequency_hz=np.asarray(coverage["eeg_frequency_hz"], dtype=np.float64),
            ne_frequency_hz=np.asarray(coverage["ne_frequency_hz"], dtype=np.float64),
        )
    return [output_dir / f"{path.stem}.npz" for path in files]


def load_feature_archives(feature_dir):
    """Load documented robust-scaled per-second matrices without reopening MAT files."""
    feature_dir = Path(feature_dir)
    archives = sorted(feature_dir.glob("*.npz"))
    if not archives:
        raise ValueError(f"No NumPy feature archives found in {feature_dir}.")

    tables = []
    for archive_path in archives:
        with np.load(archive_path, allow_pickle=False) as archive:
            feature_names = tuple(archive["feature_names"].tolist())
            if feature_names != FEATURE_COLUMNS:
                raise ValueError(
                    f"Unexpected feature columns in {archive_path.name}: {feature_names}."
                )
            values = np.asarray(archive["X_robust_scaled"], dtype=np.float32)
            labels = np.asarray(archive["label"], dtype=np.int8).reshape(-1)
            seconds = np.asarray(archive["second"], dtype=np.int32).reshape(-1)
            if values.ndim != 2 or values.shape[1] != len(FEATURE_COLUMNS):
                raise ValueError(f"Invalid X_robust_scaled shape in {archive_path.name}: {values.shape}.")
            if len(values) != len(labels) or len(values) != len(seconds):
                raise ValueError(f"Feature, label, and second lengths disagree in {archive_path.name}.")
            if not np.isfinite(values).all():
                raise ValueError(f"Non-finite robust-scaled feature value in {archive_path.name}.")
            if not np.isin(labels, tuple(LABEL_NAMES)).all():
                raise ValueError(f"Unexpected final label in {archive_path.name}.")
            recording_id = str(archive["recording_id"].item())

        table = pd.DataFrame(values, columns=FEATURE_COLUMNS)
        table["second"] = seconds
        table["label"] = labels
        table["recording_id"] = recording_id
        table["archive_file"] = archive_path.name
        table["state"] = table.label.map(LABEL_NAMES)
        tables.append(table)
    return pd.concat(tables, ignore_index=True), archives


def robust_scale_within_recording(features):
    """Scale each feature within each recording so acquisition/baseline offsets do not set distance."""
    scaled = features.copy()
    rows = []
    for recording_id, index in scaled.groupby("recording_id", sort=True).groups.items():
        values = scaled.loc[index, FEATURE_COLUMNS]
        median = values.median()
        iqr = values.quantile(0.75) - values.quantile(0.25)
        if (iqr <= 0).any() or (~np.isfinite(iqr)).any():
            bad = ", ".join(iqr.index[(iqr <= 0) | ~np.isfinite(iqr)])
            raise ValueError(f"Cannot robust-scale {recording_id}; nonpositive IQR for {bad}.")
        scaled.loc[index, FEATURE_COLUMNS] = (values - median) / iqr
        rows.append({"recording_id": recording_id, **{f"{name}_median": median[name] for name in FEATURE_COLUMNS}, **{f"{name}_iqr": iqr[name] for name in FEATURE_COLUMNS}})
    return scaled, pd.DataFrame(rows)


def balanced_sample(features, config=UmapConfig()):
    """Sample an equal maximum count for every available state within every recording."""
    rng = np.random.default_rng(config.random_seed)
    selected = []
    for _, group in features.groupby(["recording_id", "state"], sort=True):
        n = min(len(group), config.max_points_per_label_per_recording)
        selected.append(rng.choice(group.index.to_numpy(), size=n, replace=False))
    return features.loc[np.sort(np.concatenate(selected))].copy()


def fit_umap(sampled, config=UmapConfig()):
    """Fit unsupervised UMAP to the four scaled features; stage labels are not an input."""
    import umap

    if len(sampled) <= config.n_neighbors:
        raise ValueError("Need more sampled rows than n_neighbors for UMAP.")
    model = umap.UMAP(
        n_neighbors=config.n_neighbors,
        min_dist=config.min_dist,
        n_epochs=config.n_epochs,
        metric="euclidean",
        random_state=config.random_seed,
        n_jobs=1,
    )
    embedding = model.fit_transform(sampled.loc[:, FEATURE_COLUMNS].to_numpy())
    result = sampled.copy()
    result["umap_1"], result["umap_2"] = embedding[:, 0], embedding[:, 1]
    return result


def state_summary(sampled):
    """Descriptive feature summaries of the balanced displayed sample, not independent inference."""
    return (
        sampled.groupby("state", sort=False)
        .agg(n_seconds=("state", "size"), n_recordings=("recording_id", "nunique"), **{
            f"{column}_median": (column, "median") for column in FEATURE_COLUMNS
        })
        .reset_index()
    )


def plot_embedding(points, path):
    """Write one static joint EEG/EMG/NE UMAP panel coloured after unsupervised fitting."""
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8.5, 6.5), constrained_layout=True)
    for state in STATE_ORDER:
        group = points.loc[points.state == state]
        if not group.empty:
            ax.scatter(
                group.umap_1,
                group.umap_2,
                s=18,
                alpha=0.9,
                c=STAGE_COLORS[state],
                label=STATE_LABELS[state],
                linewidths=0,
            )
    ax.set(xlabel="UMAP 1", ylabel="UMAP 2", title="Joint EEG + EMG + NE feature embedding")
    ax.legend(markerscale=1.4, frameon=False, loc="best")
    fig.savefig(path, dpi=300)
    plt.close(fig)


def write_umap_analysis(input_dir, output_dir, config=UmapConfig(), figure_path=None):
    """Write audit tables to ``output_dir`` and the optional presentation PNG separately."""
    output_dir = Path(output_dir)
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError("UMAP output directory must be new or empty.")
    output_dir.mkdir(parents=True, exist_ok=True)
    features, coverage = extract_directory_features(input_dir, config)
    scaled, scales = robust_scale_within_recording(features)
    sampled = balanced_sample(scaled, config)
    points = fit_umap(sampled, config)
    features.to_csv(output_dir / "per_second_features.csv", index=False)
    coverage.to_csv(output_dir / "feature_coverage.csv", index=False)
    scales.to_csv(output_dir / "recording_feature_scales.csv", index=False)
    points.to_csv(output_dir / "umap_points.csv", index=False)
    state_summary(points).to_csv(output_dir / "state_summary.csv", index=False)
    figure_path = output_dir / "joint_eeg_emg_ne_umap.png" if figure_path is None else Path(figure_path)
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    plot_embedding(points, figure_path)
    (output_dir / "run.json").write_text(
        json.dumps(
            {
                "config": asdict(config),
                "feature_columns": FEATURE_COLUMNS,
                "input_dir": str(Path(input_dir).resolve()),
                "figure_path": str(figure_path.resolve()),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return points
