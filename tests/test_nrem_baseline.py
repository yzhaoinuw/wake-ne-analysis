import numpy as np
import pandas as pd

from wake_ne_analysis.nrem_baseline import NremBaselineConfig, calibrate_to_cluster_targets


def test_nrem_baseline_calibration_uses_target_bearing_recording_f1(tmp_path, monkeypatch):
    import wake_ne_analysis.nrem_baseline as nrem_baseline

    points = pd.DataFrame(
        {
            "recording_id": ["r1", "r1", "r2", "r2"],
            "second": [0, 1, 0, 1],
            "cluster": [2, 1, 3, 1],
        }
    )
    for recording_id in ("r1", "r2"):
        (tmp_path / f"{recording_id}.mat").touch()

    monkeypatch.setattr(
        nrem_baseline,
        "load_emg_and_labels",
        lambda path: (np.array([0.0]), 512.0, np.array([4.0, 5.0])),
    )
    monkeypatch.setattr(
        nrem_baseline,
        "prepare_nrem_baseline",
        lambda _emg, _fs, labels, _config: nrem_baseline.PreparedNremBaseline(
            np.array([]), np.isin(labels, [4, 5]), 0.5, 0.1, 10
        ),
    )

    def fake_classify(prepared, config):
        active = np.array([config.deviation_multiplier == 1.0, False])
        return nrem_baseline.NremBaselineResult(active, 1.0, 0.5, 0.1, 10, int(prepared.wake.sum()))

    monkeypatch.setattr(nrem_baseline, "classify_prepared_nrem_baseline", fake_classify)
    summary, detail, predictions, selection = calibrate_to_cluster_targets(
        tmp_path,
        points,
        (2, 3),
        np.array([0.0, 1.0]),
        NremBaselineConfig(),
    )
    assert selection["selected_multiplier"] == 1.0
    assert summary.loc[summary.multiplier == 1.0, "macro_target_recording_f1"].item() == 1.0
    assert detail.true_positive.sum() == 2
    assert predictions.experimental_high_alertness.sum() == 2
    assert detail.experimental_high_alertness_seconds.sum() == 2
    assert detail.experimental_low_alertness_seconds.sum() == 2
