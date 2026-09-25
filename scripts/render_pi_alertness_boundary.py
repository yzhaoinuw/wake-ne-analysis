"""Draft a UMAP-cut alertness map and matching four-row Wake trace.

The cut is optimized against final source labels on the *saved*, balanced
2,000-second NE-excluded UMAP display. The full trace requires refitting that
same UMAP in an interactive ``ne_umap`` terminal to transform unsampled seconds.
No source labels or feature archives are changed.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.io import loadmat
from scipy.ndimage import gaussian_filter
from scipy.signal.windows import hamming


ROOT = Path(__file__).resolve().parents[1]
SAVED_RUN = ROOT / "results" / "wake_knn_clusters_ne_excluded_20260921"
RECORDING = "408_yfp"
LEFT, RIGHT = 180, 300
HIGH, LOW = 4, 5
HIGH_COLOR, LOW_COLOR = "#E31A1C", "#0072B2"


def optimal_vertical_cut(x: np.ndarray, labels: np.ndarray) -> tuple[float, dict]:
    """Choose the most accurate x cut, breaking ties by the widest point gap."""
    x = np.asarray(x, dtype=float)
    labels = np.asarray(labels, dtype=int)
    if x.ndim != 1 or labels.shape != x.shape or len(x) < 2:
        raise ValueError("Need equally sized, nonempty one-dimensional coordinates and labels.")
    if not np.isfinite(x).all() or not np.isin(labels, (HIGH, LOW)).all():
        raise ValueError("Coordinates must be finite and labels must be 4 or 5.")
    order = np.argsort(x, kind="stable")
    xs, ys = x[order], labels[order]
    low_left = np.r_[0, np.cumsum(ys == LOW)]
    high_left = np.r_[0, np.cumsum(ys == HIGH)]
    correct = low_left + high_left[-1] - high_left
    # A valid cut cannot divide points with an identical horizontal coordinate.
    valid = np.r_[True, np.diff(xs) > 0, True]
    best = np.flatnonzero(valid & (correct == correct[valid].max()))
    gaps = np.array([xs[i] - xs[i - 1] if 0 < i < len(xs) else 0 for i in best])
    index = int(best[np.argmax(gaps)])
    if index == 0:
        cut = float(np.nextafter(xs[0], -np.inf))
    elif index == len(xs):
        cut = float(np.nextafter(xs[-1], np.inf))
    else:
        cut = float((xs[index - 1] + xs[index]) / 2)
    predicted = np.where(x >= cut, HIGH, LOW)
    audit = {
        "threshold_umap_2": cut,
        "rule": "High Alertness when UMAP 2 >= threshold; otherwise Low Alertness",
        "sample_seconds": len(x),
        "correct_seconds": int(np.count_nonzero(predicted == labels)),
        "sample_accuracy": float(np.mean(predicted == labels)),
        "source_high_predicted_high": int(np.count_nonzero((labels == HIGH) & (predicted == HIGH))),
        "source_high_predicted_low": int(np.count_nonzero((labels == HIGH) & (predicted == LOW))),
        "source_low_predicted_low": int(np.count_nonzero((labels == LOW) & (predicted == LOW))),
        "source_low_predicted_high": int(np.count_nonzero((labels == LOW) & (predicted == HIGH))),
        "n_equally_accurate_gaps": len(best),
    }
    return cut, audit


def load_saved_run() -> tuple[pd.DataFrame, dict, tuple[str, ...]]:
    points = pd.read_csv(SAVED_RUN / "sampled_wake_points.csv")
    run = json.loads((SAVED_RUN / "run.json").read_text(encoding="utf-8"))
    columns = tuple(run["feature_columns"])
    required = {"recording_id", "second", "label", "umap_1", "umap_2", *columns}
    if missing := required.difference(points.columns):
        raise ValueError(f"Saved sample lacks columns: {sorted(missing)}")
    if run["feature_set"] != "features_29_ne_excluded" or len(columns) != 27:
        raise ValueError("Expected the saved 27-feature NE-excluded UMAP run.")
    if len(points) != 2000 or points.label.value_counts().to_dict() != {HIGH: 1000, LOW: 1000}:
        raise ValueError("Expected the original balanced 2,000-second two-label sample.")
    return points, run, columns


def _figure_setup():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def plot_boundary(points: pd.DataFrame, cut: float, accuracy: float, output: Path) -> None:
    """Annotate the exact saved Figure 1 PNG without changing its point geometry."""
    from PIL import Image, ImageDraw, ImageFont

    source = ROOT / "writeups" / "assets" / "wake_knn_clusters_ne_excluded_20260921" / "umap_source_labels.png"
    image = Image.open(source).convert("RGB")
    pixels = np.asarray(image)
    dark = pixels.mean(axis=2) < 80
    vertical = np.flatnonzero(dark.sum(axis=0) > image.height * 0.8)
    horizontal = np.flatnonzero(dark.sum(axis=1) > image.width * 0.8)
    if len(vertical) < 2 or len(horizontal) < 2:
        raise ValueError("Could not locate axes in the saved Figure 1 PNG.")
    left, right = int(vertical.min()), int(vertical.max())
    top, bottom = int(horizontal.min()), int(horizontal.max())
    if right - left < image.width * 0.5 or bottom - top < image.height * 0.5:
        raise ValueError("Saved Figure 1 plot bounds are implausible.")
    # Matplotlib's original scatter uses the default 5% horizontal data margin.
    x = points.umap_2.to_numpy(dtype=float)
    span = float(x.max() - x.min())
    xmin, xmax = float(x.min() - 0.05 * span), float(x.max() + 0.05 * span)
    position = round(left + (cut - xmin) / (xmax - xmin) * (right - left))
    draw = ImageDraw.Draw(image)
    for y in range(top + 4, bottom - 3, 26):
        draw.line((position, y, position, min(y + 15, bottom - 3)),
                  fill="#1F2933", width=4)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 31)
    except OSError:
        font = ImageFont.load_default()
    label = f"UMAP 2 cut = {cut:.3f}  |  {accuracy:.1%} sample agreement"
    x_text, y_text = position + 18, top + 22
    text_box = draw.textbbox((x_text, y_text), label, font=font)
    draw.rectangle((text_box[0] - 10, text_box[1] - 7,
                    text_box[2] + 10, text_box[3] + 7),
                   fill="white", outline="#1F2933", width=2)
    draw.text((x_text, y_text), label, fill="#1F2933", font=font)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)


def _scalar(value, name: str) -> float:
    array = np.asarray(value).squeeze()
    if array.size != 1:
        raise ValueError(f"{name} must be scalar.")
    return float(array.item())


def load_trace(columns: tuple[str, ...]) -> tuple[dict, np.ndarray, np.ndarray]:
    mat = loadmat(
        ROOT / "data" / f"{RECORDING}.mat", squeeze_me=True,
        variable_names=["eeg", "emg", "eeg_frequency", "sleep_scores", "start_time"],
    )
    fs = _scalar(mat["eeg_frequency"], "eeg_frequency")
    start = _scalar(mat.get("start_time", 0), "start_time")
    archive = ROOT / "data" / "derived_features" / "features_29" / f"{RECORDING}.npz"
    with np.load(archive, allow_pickle=False) as saved:
        names = list(saved["feature_names"])
        seconds = np.asarray(saved["second"], dtype=int)
        labels = np.asarray(saved["label"], dtype=int)
        values = np.asarray(saved["X_robust_scaled"], dtype=np.float32)
    selected = (seconds >= LEFT) & (seconds < RIGHT)
    expected = np.arange(LEFT, RIGHT)
    if not np.array_equal(seconds[selected], expected):
        raise ValueError("The feature archive does not cover every representative second.")
    if any(name not in names for name in columns):
        raise ValueError("The representative archive lacks a fitted UMAP feature.")
    source_labels = np.asarray(mat["sleep_scores"], dtype=float).squeeze()[LEFT:RIGHT]
    if not np.array_equal(labels[selected], source_labels):
        raise ValueError("Feature-archive labels differ from the final MAT labels.")
    if not np.isin(source_labels, (HIGH, LOW)).all():
        raise ValueError("Representative interval must contain only High/Low Wake.")
    if len(mat["eeg"]) <= round((RIGHT - start) * fs):
        raise ValueError("EEG does not fully cover the representative interval.")
    trace = {
        "eeg": np.asarray(mat["eeg"], dtype=float).squeeze(),
        "emg": np.asarray(mat["emg"], dtype=float).squeeze(),
        "fs": fs, "start": start, "seconds": expected, "source_labels": labels[selected],
    }
    return trace, values[selected][:, [names.index(name) for name in columns]], seconds


def project_trace(points: pd.DataFrame, run: dict, columns: tuple[str, ...],
                  trace_values: np.ndarray) -> tuple[np.ndarray, dict]:
    import umap

    config = run["config"]
    model = umap.UMAP(
        n_neighbors=config["umap_neighbors"], min_dist=config["umap_min_dist"],
        n_epochs=config["umap_epochs"], metric="euclidean",
        random_state=config["random_seed"], n_jobs=1,
    )
    print("Refitting the saved 2,000-point UMAP to project the full trace...", flush=True)
    fitted = model.fit_transform(points.loc[:, columns].to_numpy(dtype=np.float32))
    saved = points.loc[:, ["umap_1", "umap_2"]].to_numpy(dtype=float)
    max_difference = float(np.max(np.abs(fitted - saved)))
    # This gate prevents applying a cut from one map to a different map.
    if max_difference > 0.05:
        raise ValueError(
            f"Refitted UMAP differs from the saved Figure 1 map by {max_difference:.3f} "
            "coordinate units. Use the original UMAP package/environment for projection."
        )
    print("Saved-map coordinates verified; projecting 120 representative seconds...", flush=True)
    projected = model.transform(trace_values)
    if projected.shape != (RIGHT - LEFT, 2) or not np.isfinite(projected).all():
        raise ValueError("Out-of-sample projection is incomplete or nonfinite.")
    sample_in_trace = points.loc[
        (points.recording_id == RECORDING) & (points.second >= LEFT) & (points.second < RIGHT)
    ]
    sample_indices = sample_in_trace.second.to_numpy(dtype=int) - LEFT
    original_coordinates = sample_in_trace[["umap_1", "umap_2"]].to_numpy(dtype=float)
    projected_sample_coordinates = projected[sample_indices]
    differences = np.linalg.norm(projected_sample_coordinates - original_coordinates, axis=1)
    return projected, {
        "max_saved_map_coordinate_difference": max_difference,
        "n_saved_sample_seconds_in_trace": len(sample_in_trace),
        "median_sample_transform_distance": float(np.median(differences)),
        "max_sample_transform_distance": float(np.max(differences)),
    }


def eeg_spectrogram(eeg: np.ndarray, fs: float, start: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Use the scoring app's centered 5 s Hamming PSD, 2.5 s step, 0-30 Hz."""
    duration = 5.0
    nperseg = round(fs * duration)
    centers = np.arange(LEFT, RIGHT + 0.001, duration / 2)
    window = hamming(nperseg)
    frequencies = np.fft.rfftfreq(nperseg, d=1 / fs)
    shown = frequencies <= 30
    one_sided = np.ones(len(frequencies))
    one_sided[1:-1 if nperseg % 2 == 0 else None] = 2
    power = np.empty((shown.sum(), len(centers)))
    for index, center in enumerate(centers):
        center_sample = round((center - start) * fs)
        first = center_sample - nperseg // 2
        segment = np.zeros(nperseg)
        first_valid = max(first, 0)
        last_valid = min(first + nperseg, len(eeg))
        segment[first_valid - first:last_valid - first] = eeg[first_valid:last_valid]
        spectrum = np.fft.rfft(segment * window)
        psd = one_sided * np.abs(spectrum) ** 2 / (fs * np.sum(window**2))
        power[:, index] = psd[shown]
    db = 10 * np.log10(np.maximum(power, np.finfo(float).tiny))
    return centers, frequencies[shown], gaussian_filter(db, sigma=4)


def _label_strip(axis, seconds: np.ndarray, labels: np.ndarray, title: str) -> None:
    from matplotlib.colors import ListedColormap

    codes = np.where(labels == HIGH, 0, 1)
    axis.imshow(codes[np.newaxis, :], aspect="auto",
                cmap=ListedColormap([HIGH_COLOR, LOW_COLOR]),
                extent=(seconds[0], seconds[-1] + 1, 0, 1),
                interpolation="nearest", vmin=0, vmax=1)
    axis.set_yticks([])
    axis.set_ylabel(title, rotation=0, ha="right", va="center")


def _longest_run_center(seconds: np.ndarray, labels: np.ndarray, label: int) -> float:
    boundaries = np.r_[0, np.flatnonzero(np.diff(labels)) + 1, len(labels)]
    runs = [(start, stop) for start, stop in zip(boundaries[:-1], boundaries[1:])
            if labels[start] == label]
    if not runs:
        raise ValueError(f"The representative trace has no label {label} segment.")
    start, stop = max(runs, key=lambda run: run[1] - run[0])
    return float((seconds[start] + seconds[stop - 1] + 1) / 2)


def _label_tick_position(seconds: np.ndarray, labels: np.ndarray, label: int) -> float:
    """Place a state name within its longest run, clear of the 20 s number ticks."""
    center = _longest_run_center(seconds, labels, label)
    boundaries = np.r_[0, np.flatnonzero(np.diff(labels)) + 1, len(labels)]
    run = next((start, stop) for start, stop in zip(boundaries[:-1], boundaries[1:])
               if seconds[start] <= center < seconds[stop - 1] + 1)
    number_ticks = np.arange(LEFT, RIGHT + 1, 20)
    gaps = (number_ticks[:-1] + number_ticks[1:]) / 2
    target = float(gaps[np.argmin(np.abs(gaps - center))])
    left, right = seconds[run[0]] + 2, seconds[run[1] - 1] + 1 - 2
    return float(np.clip(target, left, right)) if left <= right else center


def plot_trace(trace: dict, predicted: np.ndarray, output: Path) -> None:
    plt = _figure_setup()

    seconds = trace["seconds"]
    centers, freqs, db = eeg_spectrogram(trace["eeg"], trace["fs"], trace["start"])
    fig = plt.figure(figsize=(15, 7.5))
    grid = fig.add_gridspec(4, 1, left=0.07, right=0.98, top=0.92, bottom=0.10,
                            height_ratios=(3.0, 1.5, 0.37, 0.37), hspace=0.10)
    axes = [fig.add_subplot(grid[0, 0])]
    axes.extend(fig.add_subplot(grid[row, 0], sharex=axes[0]) for row in range(1, 4))
    colorbar_axis = fig.add_axes((0.785, 0.959, 0.16, 0.018))
    heatmap = axes[0].pcolormesh(centers, freqs, db, shading="nearest", cmap="viridis",
                                  vmin=np.percentile(db, 5), vmax=np.percentile(db, 95))
    fig.colorbar(heatmap, cax=colorbar_axis, orientation="horizontal")
    colorbar_axis.tick_params(labelsize=8, pad=1)
    fig.text(0.5, 0.972, f"Representative 120-second Wake segment | {RECORDING}",
             ha="center", va="center")
    fig.text(0.78, 0.972, "EEG power (dB)", ha="right", va="center")
    axes[0].set(ylabel="EEG (Hz)", ylim=(0, 30))
    first = round((LEFT - trace["start"]) * trace["fs"])
    last = round((RIGHT - trace["start"]) * trace["fs"])
    emg = trace["emg"][first:last]
    emg_time = trace["start"] + np.arange(first, last) / trace["fs"]
    axes[1].plot(emg_time, emg, color="#374151", linewidth=0.35, rasterized=True)
    axes[1].set_ylabel("Raw EMG")
    _label_strip(axes[2], seconds, trace["source_labels"], "Source\nlabel")
    _label_strip(axes[3], seconds, predicted, "UMAP-cut\nlabel")
    for axis in axes[:-1]:
        axis.tick_params(labelbottom=False)
    named_centers = (_label_tick_position(seconds, predicted, LOW),
                     _label_tick_position(seconds, predicted, HIGH))
    axes[-1].set(xlim=(LEFT, RIGHT), xticks=np.arange(LEFT, RIGHT + 1, 20))
    label_axis = axes[-1].secondary_xaxis("bottom")
    label_axis.spines["bottom"].set_visible(False)
    label_axis.set_xticks(
        named_centers,
        ["Low Alertness", "High Alertness"],
    )
    label_axis.tick_params(axis="x", length=4, pad=2, labelsize=10)
    for tick, color in zip(label_axis.get_xticklabels(), (LOW_COLOR, HIGH_COLOR)):
        tick.set_color(color)
        tick.set_fontweight("bold")
    axes[-1].set_xlabel("Recording time (seconds)", labelpad=12)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=250, facecolor="white")
    plt.close(fig)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--boundary-only", action="store_true",
                        help="Optimize and draw the cut without fitting or transforming UMAP.")
    parser.add_argument("--render-from-saved", action="store_true",
                        help="Rerender the trace from saved projected seconds, without fitting UMAP.")
    parser.add_argument("--no-figure", action="store_true",
                        help="Compute and audit without rendering (quick terminal check).")
    parser.add_argument("--results-dir", type=Path,
                        default=ROOT / "results" / "pi_alertness_boundary_20260924")
    parser.add_argument("--figures-dir", type=Path,
                        default=ROOT / "writeups" / "assets")
    args = parser.parse_args(argv)
    points, run, columns = load_saved_run()
    cut, audit = optimal_vertical_cut(points.umap_2.to_numpy(), points.label.to_numpy())
    audit.update({
        "source_run": str(SAVED_RUN.relative_to(ROOT)),
        "sample_design": "100 High and 100 Low seconds per recording across 10 recordings",
        "representative_recording": RECORDING,
        "representative_interval_seconds": [LEFT, RIGHT],
        "interpretation": "In-sample descriptive agreement; not held-out accuracy or a new final score",
        "eeg_display_method": "5-second centered Hamming PSD at 2.5-second steps, 0-30 Hz, Gaussian sigma 4",
    })
    if args.render_from_saved:
        path = args.results_dir / "representative_second_labels.csv"
        saved = pd.read_csv(path)
        trace, _, _ = load_trace(columns)
        if (not np.array_equal(saved.second.to_numpy(), trace["seconds"])
                or not np.array_equal(saved.source_label.to_numpy(), trace["source_labels"])):
            raise ValueError("Saved projected seconds do not match the representative trace.")
        predicted = np.where(saved.umap_2.to_numpy() >= cut, HIGH, LOW)
        if not np.array_equal(predicted, saved.umap_cut_label.to_numpy()):
            raise ValueError("Saved projected labels do not match the current UMAP cut.")
        if not args.no_figure:
            trace_path = args.figures_dir / "pi_alertness_four_row_draft_20260924.png"
            plot_trace(trace, predicted, trace_path)
            print(f"Wrote {trace_path}", flush=True)
        return
    if not args.no_figure:
        boundary_path = args.figures_dir / "pi_alertness_umap_boundary_20260924.png"
        plot_boundary(points, cut, audit["sample_accuracy"], boundary_path)
        print(f"Wrote {boundary_path}", flush=True)
    if not args.boundary_only:
        trace, trace_values, _ = load_trace(columns)
        projected, projection_audit = project_trace(points, run, columns, trace_values)
        predicted = np.where(projected[:, 1] >= cut, HIGH, LOW)
        audit.update(projection_audit)
        audit["representative_source_high_seconds"] = int(np.count_nonzero(trace["source_labels"] == HIGH))
        audit["representative_source_low_seconds"] = int(np.count_nonzero(trace["source_labels"] == LOW))
        audit["representative_umap_cut_high_seconds"] = int(np.count_nonzero(predicted == HIGH))
        audit["representative_umap_cut_low_seconds"] = int(np.count_nonzero(predicted == LOW))
        audit["representative_agreement"] = float(np.mean(predicted == trace["source_labels"]))
        audit["projection_method"] = "UMAP.transform after exact-parameter refit verified against saved coordinates"
        args.results_dir.mkdir(parents=True, exist_ok=True)
        pd.DataFrame({
            "recording_id": RECORDING, "second": trace["seconds"],
            "source_label": trace["source_labels"], "umap_cut_label": predicted,
            "umap_1": projected[:, 0], "umap_2": projected[:, 1],
        }).to_csv(args.results_dir / "representative_second_labels.csv", index=False)
        if not args.no_figure:
            trace_path = args.figures_dir / "pi_alertness_four_row_draft_20260924.png"
            plot_trace(trace, predicted, trace_path)
            print(f"Wrote {trace_path}", flush=True)
    args.results_dir.mkdir(parents=True, exist_ok=True)
    (args.results_dir / "boundary_audit.json").write_text(
        json.dumps(audit, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
