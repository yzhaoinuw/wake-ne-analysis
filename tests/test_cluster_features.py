import numpy as np
from scipy.io import savemat

from wake_ne_analysis.cluster_features import (
    FEATURE_COLUMNS,
    extract_expanded_recording_features,
    write_expanded_feature_archives,
)
from wake_ne_analysis.stages import STAGE_COLORS


def test_cluster_feature_archives_store_documented_features_and_burst_metadata(tmp_path):
    path = tmp_path / "expanded.mat"
    eeg_fs, ne_fs, seconds = 256, 10, 20
    eeg_time = np.arange(seconds * eeg_fs) / eeg_fs
    ne_time = np.arange(seconds * ne_fs) / ne_fs
    rng = np.random.default_rng(11)
    emg = rng.normal(scale=0.02, size=eeg_time.size)
    burst = (eeg_time >= 2.1) & (eeg_time < 2.5)
    emg[burst] += np.sin(2 * np.pi * 60 * eeg_time[burst])
    savemat(
        path,
        {
            "eeg": rng.normal(size=eeg_time.size),
            "emg": emg,
            "ne": 3 * ne_time,
            "eeg_frequency": eeg_fs,
            "ne_frequency": ne_fs,
            "sleep_scores": [1, 2, 3, 4, 5] * 4,
        },
    )

    features, metadata = extract_expanded_recording_features(path)
    assert len(FEATURE_COLUMNS) == 29
    assert features.shape == (seconds, 33)
    assert metadata["retained_feature_seconds"] == seconds
    assert features.emg_burst_onset_count.sum() >= 1
    np.testing.assert_allclose(features.ne_slope_ols_per_second, 3, atol=1e-5)

    archives = write_expanded_feature_archives(tmp_path, tmp_path / "features_29")
    with np.load(archives[0], allow_pickle=False) as archive:
        assert archive["X"].shape == (seconds, 29)
        assert tuple(archive["feature_names"].tolist()) == FEATURE_COLUMNS

    assert STAGE_COLORS["high_alertness"] == "#E31A1C"
