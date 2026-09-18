"""Compare PCA, t-SNE, and UMAP using the same sampled saved feature archives."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wake_ne_analysis.umap import (
    EMBEDDING_FEATURE_SETS,
    FEATURE_COLUMNS,
    STATE_LABELS,
    STATE_ORDER,
    STAGE_COLORS,
    UmapConfig,
    balanced_sample,
    load_feature_archives,
    state_summary,
)


@dataclass(frozen=True)
class EmbeddingConfig:
    random_seed: int = 20260917
    max_points_per_label_per_recording: int = 100
    tsne_perplexity: float = 30.0
    tsne_iterations: int = 1000
    n_neighbors: int = 30
    min_dist: float = 0.2
    n_epochs: int = 200


def _fit_embeddings(sampled, feature_columns, config):
    values = sampled.loc[:, feature_columns].to_numpy(dtype=np.float32)
    pca = PCA(n_components=2, svd_solver="full")
    pca_points = pca.fit_transform(values)
    if not 1 < config.tsne_perplexity < len(sampled):
        raise ValueError("t-SNE perplexity must be greater than one and smaller than the sampled rows.")
    tsne = TSNE(
        n_components=2,
        perplexity=config.tsne_perplexity,
        max_iter=config.tsne_iterations,
        init="pca",
        learning_rate="auto",
        random_state=config.random_seed,
        method="barnes_hut",
    )
    tsne_points = tsne.fit_transform(values)

    import umap

    if len(sampled) <= config.n_neighbors:
        raise ValueError("Need more sampled rows than n_neighbors for UMAP.")
    umap_model = umap.UMAP(
        n_neighbors=config.n_neighbors,
        min_dist=config.min_dist,
        n_epochs=config.n_epochs,
        metric="euclidean",
        random_state=config.random_seed,
        n_jobs=1,
    )
    umap_points = umap_model.fit_transform(values)
    return pca, pca_points, tsne_points, umap_points


def _plot_embedding(points, pca, method, figure_path, feature_set):
    coordinates = {
        "pca": ("pca_1", "pca_2", "PC 1", "PC 2", "PCA"),
        "tsne": ("tsne_1", "tsne_2", "t-SNE 1", "t-SNE 2", "t-SNE"),
        "umap": ("umap_1", "umap_2", "UMAP 1", "UMAP 2", "UMAP"),
    }
    x, y, x_label, y_label, method_label = coordinates[method]
    fig, ax = plt.subplots(figsize=(7.2, 6.2), constrained_layout=True)
    for state in STATE_ORDER:
        group = points.loc[points.state == state]
        if not group.empty:
            ax.scatter(
                group[x], group[y], s=9, alpha=0.78, c=STAGE_COLORS[state],
                label=STATE_LABELS[state], linewidths=0, rasterized=True,
            )
    if method == "pca":
        x_label += f" ({pca.explained_variance_ratio_[0] * 100:.1f}% variance)"
        y_label += f" ({pca.explained_variance_ratio_[1] * 100:.1f}% variance)"
    title_features = "EEG + EMG + NE" if feature_set == "joint" else "EEG + NE"
    ax.set(title=f"{method_label} embedding: {title_features}", xlabel=x_label, ylabel=y_label)
    ax.set_title(ax.get_title(), pad=12)
    ax.legend(title="Final sleep label", frameon=True, loc="best")
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(figure_path, dpi=300)
    plt.close(fig)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--feature-dir", type=Path, required=True)
    parser.add_argument("--results-dir", type=Path, required=True)
    parser.add_argument("--figures-dir", type=Path, required=True)
    parser.add_argument("--feature-set", choices=tuple(EMBEDDING_FEATURE_SETS), default="joint")
    parser.add_argument("--max-points-per-label-per-recording", type=int, default=100)
    parser.add_argument("--seed", type=int, default=20260917)
    parser.add_argument("--tsne-perplexity", type=float, default=30.0)
    parser.add_argument("--tsne-iterations", type=int, default=1000)
    parser.add_argument("--n-neighbors", type=int, default=30)
    parser.add_argument("--min-dist", type=float, default=0.2)
    parser.add_argument("--n-epochs", type=int, default=200)
    args = parser.parse_args(argv)
    if args.results_dir.exists() and any(args.results_dir.iterdir()):
        raise ValueError("Results directory must be new or empty.")
    config = EmbeddingConfig(
        random_seed=args.seed,
        max_points_per_label_per_recording=args.max_points_per_label_per_recording,
        tsne_perplexity=args.tsne_perplexity,
        tsne_iterations=args.tsne_iterations,
        n_neighbors=args.n_neighbors,
        min_dist=args.min_dist,
        n_epochs=args.n_epochs,
    )
    print("Loading saved robust-scaled feature archives...", flush=True)
    features, archives = load_feature_archives(args.feature_dir)
    # MA is a manual override rather than one of the physiological stages being
    # compared here.  Exclude it before both balanced sampling and fitting so it
    # cannot alter any PCA/t-SNE/UMAP neighbourhood or variance structure.
    features = features.loc[features.state != "ma"].copy()
    if features.empty:
        raise ValueError("No non-MA feature rows are available for embedding.")
    feature_columns = EMBEDDING_FEATURE_SETS[args.feature_set]
    sampled = balanced_sample(
        features,
        UmapConfig(
            random_seed=config.random_seed,
            max_points_per_label_per_recording=config.max_points_per_label_per_recording,
            n_neighbors=config.n_neighbors,
            min_dist=config.min_dist,
            n_epochs=config.n_epochs,
        ),
    )
    print(f"Fitting PCA, t-SNE, and UMAP on {len(sampled):,} balanced seconds...", flush=True)
    pca, pca_points, tsne_points, umap_points = _fit_embeddings(sampled, feature_columns, config)
    points = sampled.copy()
    points[["pca_1", "pca_2"]] = pca_points
    points[["tsne_1", "tsne_2"]] = tsne_points
    points[["umap_1", "umap_2"]] = umap_points
    args.results_dir.mkdir(parents=True, exist_ok=True)
    points.to_csv(args.results_dir / "embedding_points.csv", index=False)
    state_summary(points).to_csv(args.results_dir / "state_summary.csv", index=False)
    pd.DataFrame(
        {"principal_component": ("PC1", "PC2"), "explained_variance_ratio": pca.explained_variance_ratio_}
    ).to_csv(args.results_dir / "pca_explained_variance.csv", index=False)
    (args.results_dir / "run.json").write_text(
        json.dumps(
            {
                "config": asdict(config),
                "feature_dir": str(args.feature_dir.resolve()),
                "archive_files": [path.name for path in archives],
                "feature_set": args.feature_set,
                "feature_columns": feature_columns,
                "excluded_states_before_sampling": ["ma"],
                "figures_dir": str(args.figures_dir.resolve()),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    for method in ("pca", "tsne", "umap"):
        _plot_embedding(points, pca, method, args.figures_dir / f"{method}.png", args.feature_set)
    print(f"Wrote {len(points):,} sampled embedding rows to {args.results_dir}")
    print(f"Wrote separate PCA, t-SNE, and UMAP figures to {args.figures_dir}")


if __name__ == "__main__":
    main()
