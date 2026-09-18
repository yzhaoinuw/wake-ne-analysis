"""Compare PCA, t-SNE, and UMAP for the saved 29-feature archives.

The script never supplies labels to a dimensionality-reduction fit.  It offers
two feature variants (all features or all non-EMG features) and two analysis
scopes: all final stages except MA, or a single combined Wake class.
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
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wake_ne_analysis.expanded_features import FEATURE_COLUMNS, FEATURE_SET_NAME
from wake_ne_analysis.umap import LABEL_NAMES, STAGE_COLORS, STATE_LABELS


ALL_STAGES_NO_MA = ("nrem", "rem", "active_wake", "quiet_wake")
WAKE_ONLY = "wake"
WAKE_COLOR = "#4D4D4D"


@dataclass(frozen=True)
class EmbeddingConfig:
    random_seed: int = 20260917
    max_points_per_label_per_recording: int = 100
    tsne_perplexity: float = 30.0
    tsne_iterations: int = 1000
    n_neighbors: int = 30
    min_dist: float = 0.2
    n_epochs: int = 200


def _load_expanded_archives(feature_dir: Path) -> tuple[pd.DataFrame, list[Path]]:
    """Load a consistent set of scaled 29-feature archives without reopening MAT files."""
    archives = sorted(feature_dir.glob("*.npz"))
    if not archives:
        raise ValueError(f"No NumPy feature archives found in {feature_dir}.")

    tables, recording_ids = [], []
    for archive_path in archives:
        with np.load(archive_path, allow_pickle=False) as archive:
            names = tuple(archive["feature_names"].tolist())
            if names != FEATURE_COLUMNS:
                raise ValueError(
                    f"Unexpected {FEATURE_SET_NAME} columns in {archive_path.name}: {names}."
                )
            values = np.asarray(archive["X_robust_scaled"], dtype=np.float32)
            labels = np.asarray(archive["label"], dtype=np.int8).reshape(-1)
            seconds = np.asarray(archive["second"], dtype=np.int32).reshape(-1)
            recording_id = str(archive["recording_id"].item())
        if values.ndim != 2 or values.shape[1] != len(FEATURE_COLUMNS):
            raise ValueError(f"Invalid X_robust_scaled shape in {archive_path.name}: {values.shape}.")
        if len(values) != len(labels) or len(values) != len(seconds):
            raise ValueError(f"Feature, label, and second lengths disagree in {archive_path.name}.")
        if not np.isfinite(values).all():
            raise ValueError(f"Non-finite robust-scaled feature value in {archive_path.name}.")
        if not np.isin(labels, tuple(LABEL_NAMES)).all():
            raise ValueError(f"Unexpected final label in {archive_path.name}.")
        table = pd.DataFrame(values, columns=FEATURE_COLUMNS)
        table["second"] = seconds
        table["label"] = labels
        table["recording_id"] = recording_id
        table["archive_file"] = archive_path.name
        table["state"] = table.label.map(LABEL_NAMES)
        tables.append(table)
        recording_ids.append(recording_id)
    features = pd.concat(tables, ignore_index=True)
    if len(set(recording_ids)) != len(recording_ids):
        duplicates = sorted({name for name in recording_ids if recording_ids.count(name) > 1})
        raise ValueError(f"Duplicate recording_id values across archives: {', '.join(duplicates)}.")
    return features, archives


def _feature_columns(variant: str) -> tuple[str, ...]:
    if variant == "all":
        return FEATURE_COLUMNS
    columns = tuple(name for name in FEATURE_COLUMNS if not name.startswith("emg_"))
    if variant == "no_emg":
        return columns
    raise ValueError(f"Unknown feature variant: {variant}.")


def _prepare_scope(features: pd.DataFrame, scope: str) -> tuple[pd.DataFrame, dict[str, str]]:
    """Apply state selection before sampling, preserving source states for audit output."""
    if scope == "all_stages_no_ma":
        result = features.loc[features.state.isin(ALL_STAGES_NO_MA)].copy()
        return result, {state: STATE_LABELS[state] for state in ALL_STAGES_NO_MA}
    if scope == "wake_only":
        result = features.loc[features.state.isin(("active_wake", "quiet_wake"))].copy()
        result["source_state"] = result["state"]
        result["state"] = WAKE_ONLY
        return result, {WAKE_ONLY: "Wake (Active + Quiet)"}
    raise ValueError(f"Unknown analysis scope: {scope}.")


def _balanced_sample(features: pd.DataFrame, config: EmbeddingConfig) -> pd.DataFrame:
    if config.max_points_per_label_per_recording < 1:
        raise ValueError("max_points_per_label_per_recording must be positive.")
    rng = np.random.default_rng(config.random_seed)
    selected = []
    for _, group in features.groupby(["recording_id", "state"], sort=True):
        n = min(len(group), config.max_points_per_label_per_recording)
        selected.append(rng.choice(group.index.to_numpy(), size=n, replace=False))
    if not selected:
        raise ValueError("No rows are available after the requested state selection.")
    return features.loc[np.sort(np.concatenate(selected))].copy()


def _fit_embeddings(sampled: pd.DataFrame, columns: tuple[str, ...], config: EmbeddingConfig):
    values = sampled.loc[:, columns].to_numpy(dtype=np.float32)
    if len(sampled) < 2:
        raise ValueError("Need at least two sampled rows for a two-dimensional embedding.")
    if not 1 < config.tsne_perplexity < len(sampled):
        raise ValueError("t-SNE perplexity must be greater than one and smaller than sampled rows.")
    if len(sampled) <= config.n_neighbors:
        raise ValueError("Need more sampled rows than n_neighbors for UMAP.")
    pca = PCA(n_components=2, svd_solver="full")
    pca_points = pca.fit_transform(values)
    tsne_points = TSNE(
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
        n_neighbors=config.n_neighbors,
        min_dist=config.min_dist,
        n_epochs=config.n_epochs,
        metric="euclidean",
        random_state=config.random_seed,
        n_jobs=1,
    ).fit_transform(values)
    return pca, pca_points, tsne_points, umap_points


def _feature_title(variant: str) -> str:
    return "All 29 EEG + EMG + NE features" if variant == "all" else "EEG + NE features (EMG omitted)"


def _plot_embedding(
    points: pd.DataFrame,
    pca: PCA,
    method: str,
    path: Path,
    feature_variant: str,
    state_labels: dict[str, str],
) -> None:
    coordinates = {
        "pca": ("pca_1", "pca_2", "PC 1", "PC 2", "PCA"),
        "tsne": ("tsne_1", "tsne_2", "t-SNE 1", "t-SNE 2", "t-SNE"),
        "umap": ("umap_1", "umap_2", "UMAP 1", "UMAP 2", "UMAP"),
    }
    x, y, x_label, y_label, method_label = coordinates[method]
    fig, ax = plt.subplots(figsize=(7.2, 6.2), constrained_layout=True)
    for state, label in state_labels.items():
        group = points.loc[points.state == state]
        if not group.empty:
            ax.scatter(
                group[x], group[y], s=9, alpha=0.78,
                c=WAKE_COLOR if state == WAKE_ONLY else STAGE_COLORS[state],
                label=label, linewidths=0, rasterized=True,
            )
    if method == "pca":
        x_label += f" ({pca.explained_variance_ratio_[0] * 100:.1f}% variance)"
        y_label += f" ({pca.explained_variance_ratio_[1] * 100:.1f}% variance)"
    ax.set(
        title=f"{method_label} embedding: {_feature_title(feature_variant)}",
        xlabel=x_label,
        ylabel=y_label,
    )
    ax.set_title(ax.get_title(), pad=12)
    ax.legend(title="Analysis label", frameon=True, loc="best")
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=300)
    plt.close(fig)


def _state_summary(points: pd.DataFrame, columns: tuple[str, ...]) -> pd.DataFrame:
    return (
        points.groupby("state", sort=False)
        .agg(
            n_seconds=("state", "size"),
            n_recordings=("recording_id", "nunique"),
            **{f"{column}_median": (column, "median") for column in columns},
        )
        .reset_index()
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--feature-dir", type=Path, required=True)
    parser.add_argument("--results-dir", type=Path, required=True)
    parser.add_argument("--figures-dir", type=Path, required=True)
    parser.add_argument("--feature-variant", choices=("all", "no_emg"), required=True)
    parser.add_argument("--analysis-scope", choices=("all_stages_no_ma", "wake_only"), required=True)
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
    if args.figures_dir.exists() and any(args.figures_dir.iterdir()):
        raise ValueError("Figures directory must be new or empty.")
    config = EmbeddingConfig(
        random_seed=args.seed,
        max_points_per_label_per_recording=args.max_points_per_label_per_recording,
        tsne_perplexity=args.tsne_perplexity,
        tsne_iterations=args.tsne_iterations,
        n_neighbors=args.n_neighbors,
        min_dist=args.min_dist,
        n_epochs=args.n_epochs,
    )
    print("Loading saved robust-scaled expanded feature archives...", flush=True)
    features, archives = _load_expanded_archives(args.feature_dir)
    scoped, state_labels = _prepare_scope(features, args.analysis_scope)
    sampled = _balanced_sample(scoped, config)
    columns = _feature_columns(args.feature_variant)
    print(f"Fitting PCA, t-SNE, and UMAP on {len(sampled):,} balanced seconds...", flush=True)
    pca, pca_points, tsne_points, umap_points = _fit_embeddings(sampled, columns, config)
    points = sampled.copy()
    points[["pca_1", "pca_2"]] = pca_points
    points[["tsne_1", "tsne_2"]] = tsne_points
    points[["umap_1", "umap_2"]] = umap_points
    args.results_dir.mkdir(parents=True, exist_ok=True)
    points.to_csv(args.results_dir / "embedding_points.csv", index=False)
    _state_summary(points, columns).to_csv(args.results_dir / "state_summary.csv", index=False)
    pd.DataFrame(
        {"principal_component": ("PC1", "PC2"), "explained_variance_ratio": pca.explained_variance_ratio_}
    ).to_csv(args.results_dir / "pca_explained_variance.csv", index=False)
    (args.results_dir / "run.json").write_text(
        json.dumps(
            {
                "config": asdict(config),
                "feature_dir": str(args.feature_dir.resolve()),
                "archive_files": [path.name for path in archives],
                "feature_set": FEATURE_SET_NAME,
                "feature_variant": args.feature_variant,
                "feature_columns": columns,
                "analysis_scope": args.analysis_scope,
                "excluded_states_before_sampling": ["ma"] if args.analysis_scope == "all_stages_no_ma" else ["nrem", "rem", "ma"],
                "wake_mapping": "active_wake and quiet_wake collapsed to wake before sampling and fitting" if args.analysis_scope == "wake_only" else None,
                "figures_dir": str(args.figures_dir.resolve()),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    for method in ("pca", "tsne", "umap"):
        _plot_embedding(points, pca, method, args.figures_dir / f"{method}.png", args.feature_variant, state_labels)
    print(f"Wrote {len(points):,} sampled embedding rows to {args.results_dir}")
    print(f"Wrote separate PCA, t-SNE, and UMAP figures to {args.figures_dir}")


if __name__ == "__main__":
    main()
