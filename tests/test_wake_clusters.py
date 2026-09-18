import numpy as np
import pandas as pd
import pytest

pytest.importorskip("sklearn")

from wake_ne_analysis.cluster_features import FEATURE_COLUMNS
from wake_ne_analysis.wake_clusters import balanced_wake_sample, knn_spectral_clusters


def test_wake_sampling_balances_source_labels_and_knn_partition_is_reportable():
    rows = []
    rng = np.random.default_rng(4)
    for recording_id in ("r1", "r2"):
        for source_state, center in (("active_wake", -2.0), ("quiet_wake", 2.0)):
            for second in range(8):
                rows.append(
                    {
                        "recording_id": recording_id,
                        "source_state": source_state,
                        "second": second,
                        **dict(zip(FEATURE_COLUMNS, rng.normal(center, 0.1, len(FEATURE_COLUMNS)))),
                    }
                )
    sampled = balanced_wake_sample(pd.DataFrame(rows), 3, 20260918)
    assert sampled.groupby(["recording_id", "source_state"]).size().eq(3).all()

    labels, audit = knn_spectral_clusters(
        sampled.loc[:, FEATURE_COLUMNS].to_numpy(), n_neighbors=3, n_clusters=2, random_seed=20260918
    )
    assert set(labels) == {1, 2}
    assert audit["n_samples"] == len(sampled)
    assert audit["n_neighbors_directed"] == 3
