from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy.io import savemat

from wake_ne_analysis.io import Recording
from wake_ne_analysis.recording_report import (
    add_score_bout_metrics,
    analyze_raw_bouts,
    analyze_raw_spectra,
    independent_bout_results,
    independent_spectral_window_results,
    paired_recording_results,
    summarize_recordings,
)


def recording(signal, labels, fs=10, name="r1"):
    return Recording(
        Path(name + ".mat").resolve(), "recording", name, np.array(signal, dtype=float), fs, np.array(labels, dtype=float)
    )


def test_recording_report_uses_common_interval_and_literal_score_bout_metrics():
    source = recording(
        [0, 1, 3, 1, 0, 0, 1, 4, 1, 0, 99, 99],
        [4, 4, 4, 4, 4, 5, 5, 5, 5, 5],
        fs=1,
    )
    bouts, audit = analyze_raw_bouts(source)
    assert audit["common_start_samples"] == 10
    assert audit["tail_ne_seconds_not_analyzed"] == pytest.approx(2)
    assert bouts.raw_bout_mean.tolist() == [1.0, 1.2]
    assert bouts.complete_shape.all()

    summaries = summarize_recordings(bouts, pd.DataFrame([audit]))
    geometry = pd.DataFrame(
        [
            {"recording_id": "r1", "state": "active_wake", "n_score_bouts": 1, "bout_duration_median_seconds": 5.0},
            {"recording_id": "r1", "state": "quiet_wake", "n_score_bouts": 1, "bout_duration_median_seconds": 5.0},
        ]
    )
    results = paired_recording_results(add_score_bout_metrics(summaries, geometry))
    assert results.loc[results.metric == "score_bout_count", "active_median"].item() == 1


def test_recording_report_audits_peak_shapes_that_cross_score_boundaries():
    source = recording([0, 1, 5, 4, 1, 0], [4, 4, 4, 5, 5, 5], fs=1, name="crossing")
    bouts, _ = analyze_raw_bouts(source)
    active = bouts.loc[bouts.state == "active_wake"].iloc[0]
    assert active.complete_shape
    assert active.crosses_state_boundary
    assert active.decay20_seconds > active.offset_seconds


def test_recording_report_keeps_independent_bout_screen_separate():
    source = recording([0, 1, 5, 1, 0, 0, 1, 3, 1, 0], [4] * 5 + [5] * 5, fs=1)
    bouts, _ = analyze_raw_bouts(source)
    results = independent_bout_results(bouts)
    assert "raw_bout_mean" not in results.metric.tolist()
    assert np.isfinite(results.loc[results.metric == "rise_slope", "p_value"].item())


def test_recording_spectral_screen_uses_state_pure_common_interval_windows(tmp_path):
    fs = 10
    time = np.arange(60 * fs) / fs
    savemat(
        tmp_path / "spectrum.mat",
        {"ne": np.sin(2 * np.pi * 0.2 * time), "sleep_scores": [4] * 30 + [5] * 30, "ne_frequency": fs},
    )
    _, windows, summaries, paired = analyze_raw_spectra(tmp_path)
    assert summaries.active_wake_n_windows.item() == 2
    assert summaries.quiet_wake_n_windows.item() == 2
    assert paired.n_recording_pairs.tolist() == [1, 1]
    independent = independent_spectral_window_results(windows)
    assert independent.n_active_windows.item() == 2
    assert independent.n_quiet_windows.item() == 2
