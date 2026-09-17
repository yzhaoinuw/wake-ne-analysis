"""Create label-coloured pairwise and PCA views from exported four-feature CSVs."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wake_ne_analysis.umap import FEATURE_COLUMNS, LABEL_NAMES, STAGE_COLORS


STATE_ORDER = ("active_wake", "quiet_wake", "ma", "nrem", "rem")
STATE_LABELS = {
    "active_wake": "Active Wake",
    "quiet_wake": "Quiet Wake",
    "ma": "MA",
    "nrem": "NREM",
    "rem": "REM",
}
STATE_COLORS = STAGE_COLORS
FEATURE_LABELS = {
    "eeg_delta_log10_power": "EEG delta log10 power",
    "eeg_theta_log10_power": "EEG theta log10 power",
    "emg_centered_rms": "EMG centred RMS",
    "ne_mean": "Mean processed NE",
}


def _load_features(feature_dir):
    feature_dir = Path(feature_dir)
    archives = sorted(feature_dir.glob("*.npz"))
    if not archives:
        raise ValueError(f"No NumPy feature archives found in {feature_dir}.")
    tables = []
    for archive in archives:
        with np.load(archive, allow_pickle=False) as data:
            names = tuple(data["feature_names"].tolist())
            if names != FEATURE_COLUMNS:
                raise ValueError(f"Unexpected feature columns in {archive.name}: {names}.")
            table = pd.DataFrame(data["X_robust_scaled"], columns=FEATURE_COLUMNS)
            table["second"] = data["second"]
            table["label"] = data["label"]
            table["recording_id"] = str(data["recording_id"])
            table["state"] = table.label.map(LABEL_NAMES)
            tables.append(table)
    features = pd.concat(tables, ignore_index=True)
    if features.empty or not np.isfinite(features.loc[:, FEATURE_COLUMNS]).all().all():
        raise ValueError("Feature exports must contain finite robust-scaled values.")
    return features, archives


def _balanced_display_sample(features, per_state=2500, seed=20260917):
    rng = np.random.default_rng(seed)
    indices = []
    for state in STATE_ORDER:
        available = features.index[features.state == state].to_numpy()
        if available.size:
            indices.append(rng.choice(available, size=min(per_state, available.size), replace=False))
    return features.loc[np.sort(np.concatenate(indices))]


def _scatter_by_state(ax, data, x, y, alpha=0.10, size=1.5):
    for state in STATE_ORDER:
        group = data.loc[data.state == state]
        if not group.empty:
            ax.scatter(
                group[x], group[y], s=size, alpha=alpha, color=STATE_COLORS[state],
                label=STATE_LABELS[state], linewidths=0, rasterized=True,
            )


def _save_pairwise_features(features, output_dir):
    sample = _balanced_display_sample(features)
    pairs = ((0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3))
    fig, axes = plt.subplots(2, 3, figsize=(14, 8.5), constrained_layout=True)
    for ax, (x_index, y_index) in zip(axes.flat, pairs):
        x, y = FEATURE_COLUMNS[x_index], FEATURE_COLUMNS[y_index]
        _scatter_by_state(ax, sample, x, y)
        ax.set(xlabel=FEATURE_LABELS[x], ylabel=FEATURE_LABELS[y])
    handles, labels = axes.flat[0].get_legend_handles_labels()
    fig.legend(handles, labels, title="Final label", loc="upper center", ncols=5, frameon=False)
    fig.suptitle("Pairwise four-feature views (up to 2,500 seconds per label)", y=1.03)
    fig.savefig(output_dir / "pairwise_features_by_state.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def _save_pca_scores(features, pca, scores, output_dir):
    plotted = features.copy()
    for index in range(scores.shape[1]):
        plotted[f"pc{index + 1}"] = scores[:, index]
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5), constrained_layout=True)
    for ax, y_index in zip(axes, (1, 2)):
        _scatter_by_state(ax, plotted, "pc1", f"pc{y_index + 1}", alpha=0.07, size=0.8)
        ax.set(
            xlabel=f"PC1 ({pca.explained_variance_ratio_[0] * 100:.1f}% variance)",
            ylabel=f"PC{y_index + 1} ({pca.explained_variance_ratio_[y_index] * 100:.1f}% variance)",
        )
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, title="Final label", loc="upper center", ncols=5, frameon=False)
    fig.suptitle("PCA scores from within-recording robust-scaled features", y=1.04)
    fig.savefig(output_dir / "pca_scores_by_state.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def _save_pca_loadings(pca, output_dir):
    fig, ax = plt.subplots(figsize=(8.5, 4.8), constrained_layout=True)
    image = ax.imshow(pca.components_, vmin=-1, vmax=1, cmap="coolwarm", aspect="auto")
    ax.set(
        xticks=np.arange(len(FEATURE_COLUMNS)),
        xticklabels=[FEATURE_LABELS[column] for column in FEATURE_COLUMNS],
        yticks=np.arange(len(FEATURE_COLUMNS)),
        yticklabels=[f"PC{i + 1} ({variance * 100:.1f}%)" for i, variance in enumerate(pca.explained_variance_ratio_)],
        title="PCA component loadings",
    )
    plt.setp(ax.get_xticklabels(), rotation=25, ha="right")
    for row in range(pca.components_.shape[0]):
        for column in range(pca.components_.shape[1]):
            value = pca.components_[row, column]
            ax.text(column, row, f"{value:.2f}", ha="center", va="center", color="white" if abs(value) > 0.55 else "black")
    fig.colorbar(image, ax=ax, label="Component weight")
    fig.savefig(output_dir / "pca_component_loadings.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--feature-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError("PCA output directory must be new or empty.")
    args.output.mkdir(parents=True, exist_ok=True)
    features, archives = _load_features(args.feature_dir)
    pca = PCA(n_components=len(FEATURE_COLUMNS))
    scores = pca.fit_transform(features.loc[:, FEATURE_COLUMNS])
    _save_pairwise_features(features, args.output)
    _save_pca_scores(features, pca, scores, args.output)
    _save_pca_loadings(pca, args.output)
    pd.DataFrame(
        {
            "principal_component": [f"PC{i + 1}" for i in range(len(FEATURE_COLUMNS))],
            "explained_variance_ratio": pca.explained_variance_ratio_,
            "explained_variance_percent": pca.explained_variance_ratio_ * 100,
        }
    ).to_csv(args.output / "pca_explained_variance.csv", index=False)
    pd.DataFrame(pca.components_, columns=FEATURE_COLUMNS, index=[f"PC{i + 1}" for i in range(len(FEATURE_COLUMNS))]).to_csv(
        args.output / "pca_component_loadings.csv"
    )
    print(f"Wrote PCA views for {len(features):,} seconds from {len(archives)} MAT files to {args.output}")


if __name__ == "__main__":
    main()
