import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy import signal
from scipy.io import savemat

from wake_ne_analysis.dynamics_summary import (
    holm_adjust, paired_comparisons, pooled_mouse_summaries, summarize_features,
    pooled_comparisons,
)
from wake_ne_analysis.dynamics_workflow import run_analysis
from wake_ne_analysis.io import Recording
from wake_ne_analysis.ne_dynamics import (
    DynamicsConfig, FEATURE_NAMES, extract_dynamics, linear_slope_and_variances,
    lowpass_sos, smooth_ne,
)


def recording(y, labels, fs=10.0, start=0):
    return Recording(Path("test.mat"), "unknown", "test", np.asarray(y, dtype=float),
                     fs, np.asarray(labels, dtype=float), start)


def test_zero_phase_sinusoid_and_effective_cutoff():
    config = DynamicsConfig()
    fs = 10.1725
    t = np.arange(int(600 * fs)) / fs
    wave = np.sin(2 * np.pi * config.cutoff_hz * t)
    filtered = smooth_ne(wave, fs, config)
    interior = (t > 100) & (t < 500)
    fit = np.linalg.lstsq(np.column_stack([wave[interior], np.cos(2 * np.pi * .1 * t[interior])]),
                          filtered[interior], rcond=None)[0]
    assert fit[0] == pytest.approx(1 / np.sqrt(2), abs=1e-6)
    assert fit[1] == pytest.approx(0, abs=1e-6)
    _, response = signal.sosfreqz(lowpass_sos(fs, config), worN=[.1, 1.0], fs=fs)
    assert abs(response[0]) ** 2 == pytest.approx(1 / np.sqrt(2))
    assert abs(response[1]) ** 2 < 1e-6
    assert np.isnan(filtered[t < 30]).all()


def test_linear_ramp_variance_and_detrending_are_analytic():
    fs, n, slope = 10.0, 100, 2.5
    y = 1000000 + slope * np.arange(n) / fs
    fitted, variance, residual = linear_slope_and_variances(y, fs)
    assert fitted == pytest.approx(slope)
    assert variance == pytest.approx(slope ** 2 * (n * n - 1) / (12 * fs ** 2))
    assert residual < 1e-20


def test_trailing_window_crosses_all_states_and_never_uses_future():
    fs = 10
    y = np.arange(120 * fs) / fs
    labels = np.resize([4, 1, 5, 2, 3, 0], 120)
    source = recording(y, labels, start=1234.5)
    original = source.ne.copy()
    arrays, _ = extract_dynamics(source)
    expected = np.var(y[100:200])
    assert arrays["X"][20, 2] == pytest.approx(expected)
    assert arrays["time_seconds"][20] == 1254.5
    assert np.array_equal(arrays["label"], labels)
    assert np.array_equal(source.ne, original)
    assert np.isnan(arrays["X"][:10, 2:]).all()
    changed = y.copy()
    changed[200:] += 1000
    after, _ = extract_dynamics(recording(changed, labels))
    assert np.array_equal(arrays["X"][20, 2:], after["X"][20, 2:])
    assert arrays["X"][60, 0] == pytest.approx(1, abs=1e-5)
    assert arrays["X"][60, 1] == abs(arrays["X"][60, 0])


def test_noninteger_rate_window_membership_offset_and_partial_second():
    fs = 10.1725
    t = np.arange(int(120 * fs)) / fs
    arrays, audit = extract_dynamics(recording(t ** 2, [4] * 120, fs, 500))
    window = t[(t >= 11) & (t < 21)] ** 2
    assert arrays["X"][21, 2] == pytest.approx(np.var(window))
    assert audit["incomplete_score_seconds"] == 1
    assert np.isnan(arrays["X"][-1]).all()
    assert arrays["time_seconds"][0] == 500


def test_invalid_ne_gap_is_not_bridged_and_short_segments_stay_missing():
    y = np.sin(np.arange(3000) / 10)
    y[1500:1510] = np.nan
    arrays, _ = extract_dynamics(recording(y, [4] * 300))
    assert np.isnan(arrays["X"][151:161, 2:]).all()
    assert np.isfinite(arrays["X"][161, 2:]).all()
    assert np.isnan(arrays["X"][120:181, :2]).all()
    assert np.isfinite(arrays["X"][[60, 220], :2]).all()
    assert np.isnan(smooth_ne(np.ones(500), 10, DynamicsConfig())).all()


def test_long_ne_tail_trimmed_before_filtering_without_changing_source():
    fs = 10.1725
    times = np.arange(int(145 * fs)) / fs
    y = np.sin(times)
    y[times >= 120] = 1000000
    source = recording(y, [4] * 120, fs)
    expected, _ = extract_dynamics(recording(y[times < 120], [4] * 120, fs))
    actual, audit = extract_dynamics(source)
    np.testing.assert_allclose(actual["X"], expected["X"], equal_nan=True)
    assert audit["trimmed_ne_samples"] == (times >= 120).sum()
    assert audit["common_start_seconds"] == 120
    assert len(source.ne) == len(times)
    assert source.ne[-1] == 1000000


def test_startup_exclusion_precedes_filter_and_preserves_clock_and_history():
    fs = 10.1725
    t = np.arange(int(150 * fs)) / fs
    values = np.sin(t)
    contaminated = values.copy()
    contaminated[t < 5] = 1e8
    labels = np.resize([4, 5, 1], 150)
    config = DynamicsConfig(startup_exclusion_seconds=5)
    source = recording(contaminated, labels, fs, start=123)
    actual, audit = extract_dynamics(source, config)
    expected, _ = extract_dynamics(recording(values, labels, fs, start=123), config)
    np.testing.assert_allclose(actual["X"], expected["X"], equal_nan=True)
    assert np.isnan(actual["X"][:15, 2:]).all()
    window = values[(t >= 5) & (t < 15)]
    assert actual["X"][15, 2] == pytest.approx(np.var(window))
    assert np.isnan(actual["X"][:35, :2]).all()
    assert np.isfinite(actual["X"][35, :2]).all()
    assert audit["startup_excluded_samples"] == (t < 5).sum()
    np.testing.assert_array_equal(actual["label"], labels)
    np.testing.assert_array_equal(actual["time_seconds"], 123 + np.arange(150))
    np.testing.assert_array_equal(source.ne, contaminated)
    for invalid in (-1, np.nan, np.inf):
        with pytest.raises(ValueError):
            DynamicsConfig(startup_exclusion_seconds=invalid)


def test_numbers_only_analysis_does_not_write_report(tmp_path):
    inputs = tmp_path / "input"
    inputs.mkdir()
    savemat(inputs / "a.mat", {"ne": np.ones(1200), "ne_frequency": 10,
                               "sleep_scores": [4, 5] * 60})
    output = tmp_path / "results"
    run_analysis(inputs, tmp_path / "features", output,
                 config=DynamicsConfig(startup_exclusion_seconds=5), write_report_output=False)
    assert not (output / "report.md").exists()
    assert (output / "pooled_comparisons.csv").exists()
    assert json.loads((output / "run.json").read_text())["config"]["startup_exclusion_seconds"] == 5


def test_short_ne_retains_missing_seconds_and_bad_config_rejected():
    arrays, audit = extract_dynamics(recording(np.ones(1000), [4] * 120))
    assert audit["label_tail_seconds_without_ne"] == 20
    assert np.isnan(arrays["X"][100:]).all()
    with pytest.raises(ValueError):
        DynamicsConfig(cutoff_hz=0)
    with pytest.raises(ValueError):
        lowpass_sos(0.1, DynamicsConfig())


def test_summary_retains_zero_distinct_from_missing_and_holm():
    arrays = {"X": np.array([[0, 0, np.nan, np.nan], [0, 0, np.nan, np.nan]]),
              "label": np.array([4, 5])}
    summaries = pd.concat([summarize_features(arrays, name) for name in ("a", "b")])
    results = paired_comparisons(summaries)
    assert results.n_pairs.tolist() == [2, 2, 0, 0]
    assert results.p_holm.iloc[:2].tolist() == [1, 1]
    assert results.p_holm.iloc[2:].isna().all()
    assert holm_adjust([.01, .02, .04, np.nan])[:3] == pytest.approx([.04, .06, .08])
    with pytest.raises(ValueError, match="Duplicate"):
        paired_comparisons(pd.concat([summaries, summaries]))


def test_mouse_pooling_uses_seconds_and_keeps_conditions_separate():
    records = {
        "a": {"X": np.ones((10, 4)), "label": np.full(10, 4)},
        "b": {"X": np.full((1, 4), 100), "label": np.array([4])},
        "c": {"X": np.full((2, 4), 200), "label": np.full(2, 4)},
    }
    metadata = pd.DataFrame({"recording_id": ["a", "b", "c"],
                             "mouse_id": ["001"] * 3, "condition": ["A", "A", "B"]})
    result = pooled_mouse_summaries(records, metadata)
    assert result.loc[(result.condition == "A") & (result.state == "high_alertness"), "median"].tolist() == [1] * 4
    assert result.loc[(result.condition == "B") & (result.state == "high_alertness"), "median"].tolist() == [200] * 4
    assert result.unit_id.unique().tolist() == ["001"]
    with pytest.raises(ValueError):
        pooled_mouse_summaries(records, metadata.iloc[:1])


def test_paired_test_has_one_vote_per_recording_and_four_feature_correction():
    summaries = []
    for index in range(8):
        arrays = {"X": np.array([[index + 1.] * 4] * 100 + [[0.] * 4]),
                  "label": np.array([4] * 100 + [5])}
        summaries.append(summarize_features(arrays, f"r{index}"))
    result = paired_comparisons(pd.concat(summaries))
    assert result.n_pairs.tolist() == [8] * 4
    assert result.n_high_greater.tolist() == [8] * 4
    assert result.median_high_minus_low.tolist() == [4.5] * 4
    assert result.p_value.tolist() == pytest.approx([2 / 256] * 4)
    assert result.p_holm.tolist() == pytest.approx([8 / 256] * 4)


def test_directory_run_preserves_sources_audits_trimming_and_refuses_overwrite(tmp_path):
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    ne = np.sin(np.arange(1200) / 10)
    for name, labels in (("valid", [4, 5] * 60), ("mismatch", [4] * 110)):
        savemat(inputs / f"{name}.mat", {"ne": ne, "ne_frequency": 10, "sleep_scores": labels})
    before = (inputs / "valid.mat").read_bytes()
    features, results = tmp_path / "features", tmp_path / "results"
    compared = run_analysis(inputs, features, results)
    assert (compared.n_high > compared.n_low).all()
    assert compared.p_value.notna().all()
    assert not (results / "recording_comparisons.csv").exists()
    assert json.loads((results / "run.json").read_text())["status"] == "complete"
    audit = pd.read_csv(results / "source_audit.csv")
    assert set(audit.status) == {"included"}
    assert audit.set_index("recording_id").loc["mismatch", "trimmed_ne_samples"] == 100
    with np.load(features / "valid.npz", allow_pickle=False) as archive:
        assert archive["X"].shape == (120, 4)
        assert archive["feature_names"].tolist() == list(FEATURE_NAMES)
        assert len(json.loads(str(archive["metadata_json"]))["source_sha256"]) == 64
    assert (inputs / "valid.mat").read_bytes() == before
    with pytest.raises(ValueError, match="overwrite"):
        run_analysis(inputs, features, results)


def test_invalid_metadata_fails_before_output_creation(tmp_path):
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    savemat(inputs / "a.mat", {"ne": np.ones(100), "ne_frequency": 10,
                               "sleep_scores": [4] * 10})
    metadata = tmp_path / "identities.csv"
    metadata.write_text("recording_id,mouse_id,condition\na,001, \n")
    with pytest.raises(ValueError, match="must not be empty"):
        run_analysis(inputs, tmp_path / "features", tmp_path / "results", metadata_path=metadata)
    assert not (tmp_path / "features").exists()


def test_pooling_weights_every_second_and_never_averages_recording_medians():
    records = {
        "long": {"X": np.ones((100, 4)), "label": np.full(100, 4)},
        "short": {"X": np.full((2, 4), 10.), "label": np.array([4, 5])},
    }
    result = pooled_comparisons(records)
    assert result.n_high.tolist() == [101] * 4
    assert result.n_low.tolist() == [1] * 4
    assert result.high_median.tolist() == [1] * 4
    assert result.low_median.tolist() == [10] * 4
    assert result.high_mean.tolist() == pytest.approx([110 / 101] * 4)
    assert result.low_mean.tolist() == [10] * 4
    assert result.u_statistic.tolist() == [0.5] * 4
    assert result.rank_biserial.tolist() == pytest.approx([-100 / 101] * 4)
    # Splitting the same rows among different source files leaves pooled results unchanged.
    split = {"one": {"X": records["long"]["X"][:50], "label": np.full(50, 4)},
             "two": {"X": records["long"]["X"][50:], "label": np.full(50, 4)},
             "short": records["short"]}
    pd.testing.assert_frame_equal(result, pooled_comparisons(split))


def test_pooled_missing_values_do_not_become_zero():
    records = {"a": {"X": np.array([[0, 0, np.nan, np.nan], [0, 0, np.nan, np.nan]]),
                     "label": np.array([4, 5])}}
    result = pooled_comparisons(records)
    assert result.n_high.tolist() == [1, 1, 0, 0]
    assert result.p_value.iloc[:2].tolist() == [1, 1]
    assert result.p_value.iloc[2:].isna().all()
    assert result.high_mean.iloc[:2].tolist() == [0, 0]
    assert result.high_mean.iloc[2:].isna().all()
