"""Wake-only sampling and k-nearest-neighbour graph clustering utilities."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .cluster_features import FEATURE_COLUMNS, FEATURE_SET_NAME
from .stages import LABEL_NAMES


WAKE_STATES = ("active_wake", "quiet_wake")
NE_FEATURE_COLUMNS = tuple(column for column in FEATURE_COLUMNS if column.startswith("ne_"))


def wake_clustering_feature_columns(*, exclude_ne_features: bool) -> tuple[str, ...]:
    """Return the full or NE-excluded feature panel without modifying saved values."""
    if not exclude_ne_features:
        return FEATURE_COLUMNS
    selected = tuple(column for column in FEATURE_COLUMNS if column not in NE_FEATURE_COLUMNS)
    if not selected or len(selected) + len(NE_FEATURE_COLUMNS) != len(FEATURE_COLUMNS):
        raise RuntimeError("Expected NE columns are not present in the expanded feature panel.")
    return selected


def load_expanded_feature_archives(feature_dir: Path) -> tuple[pd.DataFrame, list[Path]]:
    """Load consistent robust-scaled archives without reopening source MAT files."""
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
        table["source_state"] = table.label.map(LABEL_NAMES)
        tables.append(table)
        recording_ids.append(recording_id)
    if len(set(recording_ids)) != len(recording_ids):
        duplicates = sorted({name for name in recording_ids if recording_ids.count(name) > 1})
        raise ValueError(f"Duplicate recording_id values across archives: {', '.join(duplicates)}.")
    return pd.concat(tables, ignore_index=True), archives


def balanced_wake_sample(
    features: pd.DataFrame, max_points_per_source_state_per_recording: int, random_seed: int
) -> pd.DataFrame:
    """Restrict to Wake and cap each recording/source-label cell without clustering on labels."""
    if max_points_per_source_state_per_recording < 1:
        raise ValueError("max_points_per_source_state_per_recording must be positive.")
    wake = features.loc[features.source_state.isin(WAKE_STATES)].copy()
    if wake.empty:
        raise ValueError("No Active or Quiet Wake rows are available.")
    rng = np.random.default_rng(random_seed)
    selected = []
    for _, group in wake.groupby(["recording_id", "source_state"], sort=True):
        count = min(len(group), max_points_per_source_state_per_recording)
        selected.append(rng.choice(group.index.to_numpy(), size=count, replace=False))
    return wake.loc[np.sort(np.concatenate(selected))].reset_index(drop=True)


def symmetric_knn_graph(values: np.ndarray, n_neighbors: int):
    """Return an unweighted symmetric kNN graph and auditable graph diagnostics."""
    from scipy.sparse.csgraph import connected_components
    from sklearn.neighbors import kneighbors_graph

    values = np.asarray(values, dtype=np.float32)
    if values.ndim != 2 or not len(values) or not np.isfinite(values).all():
        raise ValueError("Clustering values must be a non-empty finite two-dimensional matrix.")
    if not 1 <= n_neighbors < len(values):
        raise ValueError("n_neighbors must be positive and smaller than the sampled row count.")
    directed = kneighbors_graph(values, n_neighbors=n_neighbors, mode="connectivity", include_self=False)
    adjacency = directed.maximum(directed.T).tocsr()
    n_components, _ = connected_components(adjacency, directed=False)
    degrees = np.asarray(adjacency.sum(axis=1)).reshape(-1)
    return adjacency, {
        "n_samples": int(len(values)),
        "n_neighbors_directed": int(n_neighbors),
        "n_edges_undirected": int(adjacency.nnz // 2),
        "connected_components": int(n_components),
        "minimum_symmetric_degree": int(degrees.min()),
        "maximum_symmetric_degree": int(degrees.max()),
    }


def knn_spectral_clusters(
    values: np.ndarray, n_neighbors: int, n_clusters: int, random_seed: int
) -> tuple[np.ndarray, dict]:
    """Partition a symmetric kNN graph; returned labels are one-based for reporting."""
    from sklearn.cluster import SpectralClustering

    if not 2 <= n_clusters < len(values):
        raise ValueError("n_clusters must be at least two and smaller than the sampled row count.")
    adjacency, audit = symmetric_knn_graph(values, n_neighbors)
    labels = SpectralClustering(
        n_clusters=n_clusters,
        affinity="precomputed",
        assign_labels="kmeans",
        n_init=20,
        random_state=random_seed,
    ).fit_predict(adjacency)
    return labels.astype(int) + 1, audit
