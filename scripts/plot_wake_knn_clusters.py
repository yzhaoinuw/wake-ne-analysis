"""Cluster source-labeled Wake with a k-nearest-neighbor graph.

Clusters are fit in a requested panel of saved within-recording robust-scaled
features. t-SNE and UMAP are display-only maps of those graph-cluster assignments.
Source labels are used only to select and balance the display sample.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import shutil
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.manifold import TSNE

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wake_ne_analysis.cluster_features import FEATURE_SET_NAME
from wake_ne_analysis.stages import LABEL_NAMES, STAGE_COLORS, STAGE_COLORS_RGB, STATE_LABELS
from wake_ne_analysis.wake_clusters import (
    NE_FEATURE_COLUMNS,
    WAKE_STATES,
    balanced_wake_sample,
    knn_spectral_clusters,
    load_expanded_feature_archives,
    wake_clustering_feature_columns,
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


def _fit_display_embeddings(
    values: np.ndarray, config: WakeClusterConfig, *, include_tsne: bool
):
    if len(values) <= config.umap_neighbors:
        raise ValueError("Need more sampled rows than umap_neighbors for UMAP.")
    tsne = None
    if include_tsne:
        if not 1 < config.tsne_perplexity < len(values):
            raise ValueError("t-SNE perplexity must be greater than one and smaller than sampled rows.")
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
        "umap": ("umap_2", "umap_1", "UMAP 2", "UMAP 1"),
    }
    x, y, x_label, y_label = coordinates[method]
    fig, ax = plt.subplots(figsize=(7.2, 6.2), constrained_layout=True)
    if category == "source_state":
        order = WAKE_STATES
        labels = STATE_LABELS
        colors = STAGE_COLORS
        legend_title = "Source alertness label"
    else:
        order = sorted(points.cluster.unique())
        labels = {cluster: f"Cluster {cluster}" for cluster in order}
        colors = {cluster: plt.get_cmap("tab10")((cluster - 1) % 10) for cluster in order}
        legend_title = "Spectral cluster"
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
    summary["high_alertness_seconds"] = counts.high_alertness
    summary["low_alertness_seconds"] = counts.low_alertness
    summary["high_alertness_fraction"] = summary.high_alertness_seconds / summary.n_seconds
    return summary.reset_index()


def _cluster_feature_medians(points: pd.DataFrame, feature_columns: tuple[str, ...]) -> pd.DataFrame:
    return points.groupby("cluster", sort=True).agg(
        **{f"{column}_median": (column, "median") for column in feature_columns}
    ).reset_index()


def _prepare_output_directory(path: Path, *, overwrite: bool) -> None:
    if path.exists() and any(path.iterdir()):
        if not overwrite:
            raise ValueError("Results and figures directories must be new or empty; use --overwrite to replace them.")
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--feature-dir", type=Path, required=True)
    parser.add_argument("--results-dir", type=Path, required=True)
    parser.add_argument("--figures-dir", type=Path, required=True)
    parser.add_argument(
        "--exclude-ne-features",
        action="store_true",
        help="Omit ne_mean and ne_slope_ols_per_second from fitting, clustering, and feature-median audits.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing non-empty results or figures directory named explicitly above.",
    )
    parser.add_argument(
        "--umap-only",
        action="store_true",
        help="Fit and plot UMAP only; skip the optional t-SNE display.",
    )
    parser.add_argument(
        "--render-only",
        action="store_true",
        help="Regenerate figures from saved point and cluster CSVs without refitting embeddings or clustering.",
    )
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
    display_methods = ("umap",) if args.umap_only else ("tsne", "umap")
    if args.render_only:
        sampled_path = args.results_dir / "sampled_wake_points.csv"
        if not sampled_path.is_file():
            raise ValueError("--render-only requires an existing sampled_wake_points.csv result.")
        points = pd.read_csv(sampled_path)
        required_columns = {f"{method}_{axis}" for method in display_methods for axis in ("1", "2")}
        if missing := required_columns.difference(points.columns):
            raise ValueError(f"Saved points lack display coordinates required for rendering: {sorted(missing)}.")
        if "label" not in points:
            raise ValueError("Saved points lack final score labels required for source-label rendering.")
        points["source_state"] = points.label.map(LABEL_NAMES)
        if points.source_state.isna().any() or not points.source_state.isin(WAKE_STATES).all():
            raise ValueError("Saved points contain unsupported source Wake labels.")
        clustered_paths = {
            n_clusters: args.results_dir / f"{n_clusters}_clusters" / "clustered_wake_points.csv"
            for n_clusters in cluster_counts
        }
        missing_clustered_paths = [path for path in clustered_paths.values() if not path.is_file()]
        if missing_clustered_paths:
            raise ValueError(f"--render-only requires {missing_clustered_paths[0]}.")
        _prepare_output_directory(args.figures_dir, overwrite=args.overwrite)
        for method in display_methods:
            _plot(
                points,
                method,
                "source_state",
                args.figures_dir / f"{method}_source_labels.png",
                f"{method.upper()} display: source High/Low Alertness labels",
        )
        for n_clusters in cluster_counts:
            clustered = pd.read_csv(clustered_paths[n_clusters])
            for method in display_methods:
                _plot(
                    clustered,
                    method,
                    "cluster",
                    args.figures_dir / f"{n_clusters}_clusters" / f"{method}_clusters.png",
                    f"{method.upper()} display: {n_clusters}-cluster spectral partition",
                )
        print(f"Rerendered {', '.join(display_methods)} figures from {args.results_dir}")
        return
    feature_columns = wake_clustering_feature_columns(
        exclude_ne_features=args.exclude_ne_features
    )
    excluded_feature_columns = tuple(
        column for column in NE_FEATURE_COLUMNS if column not in feature_columns
    )
    print(
        f"Loading {len(feature_columns)}-feature archives and selecting source-labelled Wake seconds...",
        flush=True,
    )
    features, archives = load_expanded_feature_archives(args.feature_dir)
    sampled = balanced_wake_sample(
        features, config.max_points_per_source_state_per_recording, config.random_seed
    )
    values = sampled.loc[:, feature_columns].to_numpy(dtype=np.float32)
    print(
        f"Fitting {', '.join(display_methods)} display map(s) on {len(sampled):,} Wake seconds...",
        flush=True,
    )
    tsne_points, umap_points = _fit_display_embeddings(
        values, config, include_tsne=not args.umap_only
    )
    points = sampled.copy()
    if tsne_points is not None:
        points[["tsne_1", "tsne_2"]] = tsne_points
    points[["umap_1", "umap_2"]] = umap_points
    _prepare_output_directory(args.results_dir, overwrite=args.overwrite)
    _prepare_output_directory(args.figures_dir, overwrite=args.overwrite)
    points.to_csv(args.results_dir / "sampled_wake_points.csv", index=False)
    (
        points.groupby("source_state", sort=True)
        .agg(n_seconds=("source_state", "size"), n_recordings=("recording_id", "nunique"))
        .reset_index()
        .to_csv(args.results_dir / "sample_summary.csv", index=False)
    )
    for method in display_methods:
        _plot(
            points,
            method,
            "source_state",
            args.figures_dir / f"{method}_source_labels.png",
            f"{method.upper()} display: source High/Low Alertness labels",
        )
    graph_audits = {}
    for n_clusters in cluster_counts:
        print(f"Clustering the symmetric {config.knn_neighbors}-nearest-neighbor graph into {n_clusters} groups...", flush=True)
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
        _cluster_feature_medians(clustered, feature_columns).to_csv(
            result_directory / "cluster_feature_medians.csv", index=False
        )
        (
            clustered.groupby(["recording_id", "cluster"], sort=True)
            .size()
            .rename("n_seconds")
            .reset_index()
            .to_csv(result_directory / "cluster_by_recording.csv", index=False)
        )
        for method in display_methods:
            _plot(
                clustered, method, "cluster", figure_directory / f"{method}_clusters.png",
                f"{method.upper()} display: {n_clusters}-cluster spectral partition",
            )
        graph_audits[str(n_clusters)] = audit
    (args.results_dir / "run.json").write_text(
        json.dumps(
            {
                "config": asdict(config),
                "feature_dir": str(args.feature_dir.resolve()),
                "archive_files": [path.name for path in archives],
                "feature_set": (
                    f"{FEATURE_SET_NAME}_ne_excluded"
                    if args.exclude_ne_features
                    else FEATURE_SET_NAME
                ),
                "feature_columns": feature_columns,
                "excluded_feature_columns": excluded_feature_columns,
                "selected_source_states_before_sampling": WAKE_STATES,
                "source_state_labels": {state: STATE_LABELS[state] for state in WAKE_STATES},
                "source_state_colors_rgb": {state: STAGE_COLORS_RGB[state] for state in WAKE_STATES},
                "umap_display_axes": {"horizontal": "UMAP 2", "vertical": "UMAP 1"},
                "display_methods": display_methods,
                "source_labels_used_for_clustering": False,
                "clustering_method": (
                    "spectral clustering on an unweighted symmetric k-nearest-neighbor graph "
                    f"in {len(feature_columns)}-dimensional robust-scaled feature space"
                ),
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
