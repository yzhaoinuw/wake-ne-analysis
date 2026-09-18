"""Cluster Active/Quiet Wake with a k-nearest-neighbour graph in all 29 features.

Clusters are fit in the full within-recording robust-scaled EEG+EMG+NE feature space.
t-SNE and UMAP are display-only maps of those graph-cluster assignments. Source
Active/Quiet labels are used only to select and balance the display sample.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.manifold import TSNE

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wake_ne_analysis.cluster_features import FEATURE_COLUMNS, FEATURE_SET_NAME
from wake_ne_analysis.stages import STAGE_COLORS, STATE_LABELS
from wake_ne_analysis.wake_clusters import (
    WAKE_STATES,
    balanced_wake_sample,
    knn_spectral_clusters,
    load_expanded_feature_archives,
)


@dataclass(frozen=True)
class WakeClusterConfig:
    random_seed: int = 20260918
    max_points_per_source_state_per_recording: int = 100
    knn_neighbors: int = 30
    tsne_perplexity: float = 30.0
    tsne_iterations: int = 1000
    umap_neighbors: int = 30
    umap_min_dist: float = 0.2
    umap_epochs: int = 200


def _fit_display_embeddings(values: np.ndarray, config: WakeClusterConfig):
    if not 1 < config.tsne_perplexity < len(values):
        raise ValueError("t-SNE perplexity must be greater than one and smaller than sampled rows.")
    if len(values) <= config.umap_neighbors:
        raise ValueError("Need more sampled rows than umap_neighbors for UMAP.")
    tsne = TSNE(
        n_components=2,
        perplexity=config.tsne_perplexity,
        max_iter=config.tsne_iterations,
        init="pca",
        learning_rate="auto",
        random_state=config.random_seed,
        method="barnes_hut",
    ).fit_transform(values)
    import umap

    umap_points = umap.UMAP(
        n_neighbors=config.umap_neighbors,
        min_dist=config.umap_min_dist,
        n_epochs=config.umap_epochs,
        metric="euclidean",
        random_state=config.random_seed,
        n_jobs=1,
    ).fit_transform(values)
    return tsne, umap_points


def _plot(points: pd.DataFrame, method: str, category: str, path: Path, title: str) -> None:
    coordinates = {
        "tsne": ("tsne_1", "tsne_2", "t-SNE 1", "t-SNE 2"),
        "umap": ("umap_1", "umap_2", "UMAP 1", "UMAP 2"),
    }
    x, y, x_label, y_label = coordinates[method]
    fig, ax = plt.subplots(figsize=(7.2, 6.2), constrained_layout=True)
    if category == "source_state":
        order = WAKE_STATES
        labels = STATE_LABELS
        colors = STAGE_COLORS
        legend_title = "Saved source label"
    else:
        order = sorted(points.cluster.unique())
        labels = {cluster: f"Cluster {cluster}" for cluster in order}
        colors = {cluster: plt.get_cmap("tab10")((cluster - 1) % 10) for cluster in order}
        legend_title = "kNN-graph cluster"
    for value in order:
        group = points.loc[points[category] == value]
        if not group.empty:
            ax.scatter(
                group[x], group[y], s=9, alpha=0.78, c=[colors[value]], label=labels[value],
                linewidths=0, rasterized=True,
            )
    ax.set(title=title, xlabel=x_label, ylabel=y_label)
    ax.legend(title=legend_title, frameon=True, loc="best")
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=300)
    plt.close(fig)


def _cluster_summary(points: pd.DataFrame) -> pd.DataFrame:
    counts = (
        points.groupby(["cluster", "source_state"], sort=True)
        .size()
        .unstack(fill_value=0)
        .reindex(columns=WAKE_STATES, fill_value=0)
    )
    summary = points.groupby("cluster", sort=True).agg(
        n_seconds=("cluster", "size"), n_recordings=("recording_id", "nunique")
    )
    summary["active_wake_seconds"] = counts.active_wake
    summary["quiet_wake_seconds"] = counts.quiet_wake
    summary["active_wake_fraction"] = summary.active_wake_seconds / summary.n_seconds
    return summary.reset_index()


def _cluster_feature_medians(points: pd.DataFrame) -> pd.DataFrame:
    return points.groupby("cluster", sort=True).agg(
        **{f"{column}_median": (column, "median") for column in FEATURE_COLUMNS}
    ).reset_index()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--feature-dir", type=Path, required=True)
    parser.add_argument("--results-dir", type=Path, required=True)
    parser.add_argument("--figures-dir", type=Path, required=True)
    parser.add_argument("--n-clusters", type=int, nargs="+", default=(3, 4, 5))
    parser.add_argument("--max-points-per-source-state-per-recording", type=int, default=100)
    parser.add_argument("--knn-neighbors", type=int, default=30)
    parser.add_argument("--seed", type=int, default=20260918)
    parser.add_argument("--tsne-perplexity", type=float, default=30.0)
    parser.add_argument("--tsne-iterations", type=int, default=1000)
    parser.add_argument("--umap-neighbors", type=int, default=30)
    parser.add_argument("--umap-min-dist", type=float, default=0.2)
    parser.add_argument("--umap-epochs", type=int, default=200)
    args = parser.parse_args(argv)
    if args.results_dir.exists() and any(args.results_dir.iterdir()):
        raise ValueError("Results directory must be new or empty.")
    if args.figures_dir.exists() and any(args.figures_dir.iterdir()):
        raise ValueError("Figures directory must be new or empty.")
    cluster_counts = tuple(sorted(set(args.n_clusters)))
    if not cluster_counts:
        raise ValueError("At least one requested cluster count is required.")
    config = WakeClusterConfig(
        random_seed=args.seed,
        max_points_per_source_state_per_recording=args.max_points_per_source_state_per_recording,
        knn_neighbors=args.knn_neighbors,
        tsne_perplexity=args.tsne_perplexity,
        tsne_iterations=args.tsne_iterations,
        umap_neighbors=args.umap_neighbors,
        umap_min_dist=args.umap_min_dist,
        umap_epochs=args.umap_epochs,
    )
    print("Loading 29-feature archives and selecting Active/Quiet Wake seconds...", flush=True)
    features, archives = load_expanded_feature_archives(args.feature_dir)
    sampled = balanced_wake_sample(
        features, config.max_points_per_source_state_per_recording, config.random_seed
    )
    values = sampled.loc[:, FEATURE_COLUMNS].to_numpy(dtype=np.float32)
    print(f"Fitting t-SNE and UMAP display maps on {len(sampled):,} Wake seconds...", flush=True)
    tsne_points, umap_points = _fit_display_embeddings(values, config)
    points = sampled.copy()
    points[["tsne_1", "tsne_2"]] = tsne_points
    points[["umap_1", "umap_2"]] = umap_points
    args.results_dir.mkdir(parents=True, exist_ok=True)
    points.to_csv(args.results_dir / "sampled_wake_points.csv", index=False)
    (
        points.groupby("source_state", sort=True)
        .agg(n_seconds=("source_state", "size"), n_recordings=("recording_id", "nunique"))
        .reset_index()
        .to_csv(args.results_dir / "sample_summary.csv", index=False)
    )
    for method in ("tsne", "umap"):
        _plot(points, method, "source_state", args.figures_dir / f"{method}_source_labels.png", f"{method.upper()} display: saved Active/Quiet labels")
    graph_audits = {}
    for n_clusters in cluster_counts:
        print(f"Clustering the symmetric {config.knn_neighbors}-nearest-neighbour graph into {n_clusters} groups...", flush=True)
        labels, audit = knn_spectral_clusters(
            values, config.knn_neighbors, n_clusters, config.random_seed
        )
        clustered = points.assign(cluster=labels)
        result_directory = args.results_dir / f"{n_clusters}_clusters"
        figure_directory = args.figures_dir / f"{n_clusters}_clusters"
        result_directory.mkdir(parents=True, exist_ok=True)
        clustered.to_csv(result_directory / "clustered_wake_points.csv", index=False)
        _cluster_summary(clustered).to_csv(result_directory / "cluster_summary.csv", index=False)
        (
            clustered.groupby(["cluster", "source_state"], sort=True)
            .size()
            .rename("n_seconds")
            .reset_index()
            .to_csv(result_directory / "cluster_by_source_state.csv", index=False)
        )
        _cluster_feature_medians(clustered).to_csv(
            result_directory / "cluster_feature_medians.csv", index=False
        )
        (
            clustered.groupby(["recording_id", "cluster"], sort=True)
            .size()
            .rename("n_seconds")
            .reset_index()
            .to_csv(result_directory / "cluster_by_recording.csv", index=False)
        )
        for method in ("tsne", "umap"):
            _plot(
                clustered, method, "cluster", figure_directory / f"{method}_clusters.png",
                f"{method.upper()} display: {n_clusters}-cluster kNN-graph partition",
            )
        graph_audits[str(n_clusters)] = audit
    (args.results_dir / "run.json").write_text(
        json.dumps(
            {
                "config": asdict(config),
                "feature_dir": str(args.feature_dir.resolve()),
                "archive_files": [path.name for path in archives],
                "feature_set": FEATURE_SET_NAME,
                "feature_columns": FEATURE_COLUMNS,
                "selected_source_states_before_sampling": WAKE_STATES,
                "source_labels_used_for_clustering": False,
                "clustering_method": "spectral clustering on an unweighted symmetric k-nearest-neighbour graph in 29-dimensional robust-scaled feature space",
                "requested_cluster_counts": cluster_counts,
                "graph_audits": graph_audits,
                "figures_dir": str(args.figures_dir.resolve()),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Wrote shared Wake display points to {args.results_dir}")
    print(f"Wrote {', '.join(map(str, cluster_counts))}-cluster figures and audit tables to {args.figures_dir}")


if __name__ == "__main__":
    main()
