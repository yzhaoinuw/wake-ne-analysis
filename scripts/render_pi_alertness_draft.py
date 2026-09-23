"""Render a concise PI-facing draft with one representative Wake trace."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from scipy.io import loadmat


ROOT = Path(__file__).resolve().parents[1]
TRACE_RECORDING = "408_yfp"
TRACE_LEFT_SECONDS = 180
TRACE_RIGHT_SECONDS = 300
HIGH_COLOR = "#E31A1C"
LOW_COLOR = "#0072B2"
OTHER_COLOR = "#D9D9D9"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "writeups" / "assets" / "pi_alertness_draft_20260922.png",
        help="Output PNG path.",
    )
    return parser.parse_args(argv)


def _scalar(value, name):
    result = np.asarray(value).squeeze()
    if result.size != 1:
        raise ValueError(f"{name} must be scalar.")
    return float(result.item())


def _trace_data():
    """Return a representative segment and its matching saved EMG feature."""
    mat_path = ROOT / "data" / f"{TRACE_RECORDING}.mat"
    archive_path = ROOT / "data" / "derived_features" / "features_29" / f"{TRACE_RECORDING}.npz"
    mat = loadmat(
        mat_path,
        squeeze_me=True,
        variable_names=["ne", "ne_frequency", "sleep_scores", "start_time"],
    )
    ne = np.asarray(mat["ne"], dtype=float).squeeze()
    labels = np.asarray(mat["sleep_scores"], dtype=float).squeeze()
    labels[labels == -1] = np.nan
    ne_fs = _scalar(mat["ne_frequency"], "ne_frequency")
    start_time = _scalar(mat.get("start_time", 0), "start_time")
    time = start_time + np.arange(ne.size) / ne_fs
    shown = (time >= TRACE_LEFT_SECONDS) & (time < TRACE_RIGHT_SECONDS)

    with np.load(archive_path, allow_pickle=False) as archive:
        names = list(archive["feature_names"])
        emg_column = names.index("emg_filtered_rms")
        seconds = np.asarray(archive["second"], dtype=int)
        emg = np.asarray(archive["X_robust_scaled"], dtype=float)[:, emg_column]
        archive_labels = np.asarray(archive["label"], dtype=int)
    kept = (seconds >= TRACE_LEFT_SECONDS) & (seconds < TRACE_RIGHT_SECONDS)
    selected_seconds = seconds[kept]
    if not np.array_equal(selected_seconds, np.arange(TRACE_LEFT_SECONDS, TRACE_RIGHT_SECONDS)):
        raise ValueError("Representative window is not fully covered by the feature archive.")
    if (archive_labels[kept] == 4).sum() != 60 or (archive_labels[kept] == 5).sum() != 60:
        raise ValueError("Representative window no longer has the documented High/Low balance.")
    return time[shown], ne[shown], selected_seconds, emg[kept], archive_labels[kept]


def _label_strip(axis, seconds, labels):
    colors = np.full(labels.shape, 2, dtype=int)
    colors[labels == 4] = 0
    colors[labels == 5] = 1
    axis.imshow(
        colors[np.newaxis, :],
        aspect="auto",
        cmap=ListedColormap([HIGH_COLOR, LOW_COLOR, OTHER_COLOR]),
        extent=(seconds[0], seconds[-1] + 1, 0, 1),
        interpolation="nearest",
        vmin=0,
        vmax=2,
    )
    axis.set_yticks([])
    axis.set_ylabel("Source\nlabel", rotation=0, ha="right", va="center")
    axis.set_xlabel("Recording time (seconds)")


def render(output: Path):
    time, ne, seconds, emg, labels = _trace_data()
    figure = plt.figure(figsize=(15, 5.6), constrained_layout=True)
    trace_grid = figure.add_gridspec(3, 1, height_ratios=(2.6, 1.4, 0.38), hspace=0.06)
    ne_axis = figure.add_subplot(trace_grid[0])
    emg_axis = figure.add_subplot(trace_grid[1], sharex=ne_axis)
    label_axis = figure.add_subplot(trace_grid[2], sharex=ne_axis)

    ne_axis.plot(time, ne, color="#1F2933", linewidth=1.25)
    ne_axis.axhline(0, color="#7B8794", linestyle=":", linewidth=1)
    ne_axis.set_ylabel("Processed NE\n(percentage ΔF/F)")
    ne_axis.set_title(
        "A  Representative 120-second Wake segment: processed NE, EMG activity, and existing source labels",
        loc="left",
        fontweight="bold",
    )
    ne_axis.tick_params(labelbottom=False)
    ne_axis.text(
        0.995,
        0.92,
        "408_yfp; 60 High and 60 Low seconds shown",
        transform=ne_axis.transAxes,
        ha="right",
        va="top",
        fontsize=9,
        color="#52606D",
    )

    emg_axis.step(seconds, emg, where="post", color="#6B4C9A", linewidth=1.1)
    emg_axis.set_ylabel("EMG RMS\n(robust units)")
    emg_axis.tick_params(labelbottom=False)
    _label_strip(label_axis, seconds, labels)
    label_axis.text(
        1.006,
        0.72,
        "High",
        transform=label_axis.transAxes,
        color=HIGH_COLOR,
        fontsize=9,
        va="center",
    )
    label_axis.text(
        1.006,
        0.28,
        "Low",
        transform=label_axis.transAxes,
        color=LOW_COLOR,
        fontsize=9,
        va="center",
    )
    '''
    figure.suptitle(
        "Draft discussion figure: representative Wake trace",
        fontsize=18,
        fontweight="bold",
        y=1.01,
    )
    '''
    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(figure)


def main(argv=None):
    args = parse_args(argv)
    render(args.output)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
