from copy import deepcopy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
from scipy.io import savemat

from wake_ne_analysis import (
    AnalysisConfig,
    SpectrumConfig,
    TransientConfig,
    aggregate_subjects,
    analyze_file,
    analyze_recording,
    load_recording,
    read_manifest,
)
from wake_ne_analysis.io import Recording
from wake_ne_analysis.spectra import compute_spectrum
from wake_ne_analysis.transients import detect_transients
from wake_ne_analysis.validation import usable_data_summary, smoothing_power_retention
from wake_ne_analysis.cli import analysis_main, validation_main
from wake_ne_analysis.raw_bouts import analyze_raw_bouts, paired_recording_results, summarize_recordings


def _report_renderer_module():
    path = Path(__file__).resolve().parents[1] / "scripts" / "render_cohort_preliminary_report_figures.py"
    spec = importlib.util.spec_from_file_location("cohort_report_renderer", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def recording(signal, labels, fs=10, name="r1", mouse="m1", start=0):
    return Recording(
        Path(name + ".mat").resolve(),
        mouse,
        name,
        np.array(signal, dtype=float),
        fs,
        np.array(labels, dtype=float),
        start,
    )


def triangular_events(amplitudes=(5,), times=(40,), seconds=180):
    t = np.arange(seconds * 10) / 10
    y = np.zeros_like(t)
    for amplitude, peak in zip(amplitudes, times):
        y += amplitude * np.maximum(0, 1 - np.abs(t - peak) / 10)
    return y


def test_mat_units_timing_and_alias_are_preserved(tmp_path):
    path = tmp_path / "a.mat"
    savemat(
        path, {"ne": [10, 20, 30, 40], "fp_frequency": 2, "sleep_scores": [4, 5], "start_time": 100}
    )
    data = load_recording(path, "007")
    np.testing.assert_array_equal(data.ne, [10, 20, 30, 40])
    np.testing.assert_array_equal(data.sample_labels, [4, 4, 5, 5])
    assert data.start_time == 100 and data.mouse_id == "007"


@pytest.mark.parametrize(
    "extra, message",
    [
        ({"ne_frequency": 10, "fp_frequency": 11}, "disagree"),
        ({"ne_frequency": 0}, "positive"),
        ({"sleep_scores": [6]}, "Unknown sleep label"),
        ({"ne": np.ones((2, 3))}, "single-channel"),
        ({"ne": []}, "empty ne"),
    ],
)
def test_bad_mat_metadata_fails(tmp_path, extra, message):
    path = tmp_path / "bad.mat"
    savemat(path, {"ne": np.ones(20), "sleep_scores": [4, 5], "ne_frequency": 10, **extra})
    with pytest.raises(ValueError, match=message):
        load_recording(path, "m")


def test_gaps_and_short_bouts_are_not_stitched():
    data = recording(np.ones(300), [4] * 10 + [5] * 10 + [4] * 10)
    summary = usable_data_summary(data, [15])
    assert summary.n_windows.sum() == 0
    assert summary.total_seconds.sum() == 30
    data.labels[:] = 4
    data.ne[150] = np.nan
    summary = usable_data_summary(data, [20])
    assert summary.n_windows.sum() == 0


def test_recording_start_qc_exclusion_flags_events_and_skips_initial_windows():
    data = recording(triangular_events((5, 5), (10, 40)), [4] * 180)
    config = AnalysisConfig(
        spectrum=SpectrumConfig(15, 0.2, 0.3),
        transients=TransientConfig(assignment="peak"),
        recording_start_exclusion_seconds=15,
    )
    result = analyze_recording(data, config)
    early = result.events.loc[result.events.peak_seconds < 15]
    assert len(early) == 1
    assert early.recording_start_qc_excluded.iloc[0]
    assert not early.eligible.iloc[0]
    assert result.events.loc[result.events.peak_seconds >= 15, "eligible"].any()
    assert result.windows.start_seconds.min() >= 15
    coverage = usable_data_summary(data, [15], recording_start_exclusion_seconds=15)
    assert coverage.n_windows.sum() == 11


def test_spectrum_has_correct_power_frequency_and_offset_invariance():
    time = np.arange(3600) / 10
    config = SpectrumConfig(120, 0.025, 0.1)
    data = recording(2 * np.sin(2 * np.pi * 0.05 * time) + 25, [4] * 360, start=100)
    psd, windows = compute_spectrum(data, config)
    assert len(windows) == 3
    assert windows.iloc[0].start_seconds == 100
    np.testing.assert_allclose(windows.band_power, 2, rtol=1e-10)
    assert psd.loc[psd.psd.idxmax(), "frequency_hz"] == pytest.approx(0.05)
    data.ne -= 25
    other, _ = compute_spectrum(data, config)
    np.testing.assert_allclose(psd.psd, other.psd, atol=1e-12)


def test_noninteger_sampling_rate_uses_seconds_not_sample_count():
    fs = 10.172526
    time = np.arange(round(fs * 241)) / fs
    data = recording(np.sin(2 * np.pi * 0.05 * time), [4] * 241, fs=fs)
    _, windows = compute_spectrum(data, SpectrumConfig(120, 0.025, 0.1))
    assert len(windows) == 2
    np.testing.assert_allclose(windows.duration_seconds, 120, atol=1 / fs)
    coverage = usable_data_summary(data, [241])
    assert coverage.coverage_fraction.dropna().max() <= 1


def test_transient_amplitude_duration_slopes_use_natural_crossings():
    data = recording(triangular_events(), [4] * 180, start=100)
    before = data.ne.copy()
    events = detect_transients(data)
    assert len(events) == 1
    event = events.iloc[0]
    assert event.eligible and event.complete
    assert event.amplitude == pytest.approx(5)
    assert event.duration_seconds == pytest.approx(16)
    assert event.rise_slope == pytest.approx(0.5)
    assert event.decay_slope == pytest.approx(0.5)
    assert event.onset20_seconds == pytest.approx(132)
    assert event.offset20_seconds == pytest.approx(148)
    np.testing.assert_array_equal(before, data.ne)


def test_event_crossing_state_is_audited_and_assignment_is_explicit():
    data = recording(triangular_events(), [4] * 40 + [5] * 140)
    contained = detect_transients(data).iloc[0]
    contextual = detect_transients(data, TransientConfig(assignment="peak")).iloc[0]
    assert contained.state == "quiet_wake" and contained.crosses_state
    assert contained.complete and not contained.eligible
    assert contextual.eligible and contextual.duration_seconds == contained.duration_seconds


def test_gap_does_not_become_an_event_boundary_crossing():
    signal = triangular_events()
    signal[450:460] = np.nan
    data = recording(signal, [4] * 180)
    event = detect_transients(data).iloc[0]
    assert not event.complete and not event.eligible
    assert np.isnan(event.duration_seconds)


def test_no_spectral_windows_does_not_remove_transients():
    labels = [1] * 180
    labels[30:51] = [5] * 21
    data = recording(triangular_events(), labels)
    result = analyze_recording(data, AnalysisConfig(spectrum=SpectrumConfig(120, 0.025, 0.1)))
    summary = aggregate_subjects([result]).iloc[0]
    assert summary.quiet_wake_n_events_used == 1
    assert summary.quiet_wake_spectral_n_windows == 0
    assert np.isnan(summary.quiet_wake_band_power)


def test_mouse_aggregation_pools_events_not_file_medians():
    first = analyze_recording(recording(triangular_events((1,), (40,)), [4] * 180, name="a"))
    second = analyze_recording(
        recording(triangular_events((4, 5, 6), (30, 80, 130)), [4] * 180, name="b")
    )
    summary = aggregate_subjects([second, first])
    assert summary.iloc[0].active_wake_amplitude_median == pytest.approx(4.5)
    pd.testing.assert_frame_equal(summary, aggregate_subjects([first, second]))


def test_spectral_pooling_weights_windows_not_files():
    config = AnalysisConfig(spectrum=SpectrumConfig(120, 0.025, 0.1))
    a = np.arange(3600) / 10
    b = np.arange(1200) / 10
    first = analyze_recording(
        recording(2 * np.sin(2 * np.pi * 0.05 * a), [4] * 360, name="a"), config
    )
    second = analyze_recording(
        recording(4 * np.sin(2 * np.pi * 0.05 * b), [4] * 120, name="b"), config
    )
    summary = aggregate_subjects([first, second]).iloc[0]
    assert summary.active_wake_spectral_n_windows == 4
    assert summary.active_wake_band_power == pytest.approx((3 * 2 + 8) / 4)


def test_no_events_are_missing_not_zero_and_mice_are_separate():
    a = analyze_recording(recording(np.zeros(100), [4] * 10, mouse="a", name="a"))
    b = analyze_recording(recording(np.zeros(100), [5] * 10, mouse="b", name="b"))
    summary = aggregate_subjects([a, b])
    assert summary.mouse_id.tolist() == ["a", "b"]
    assert summary.active_wake_amplitude_median.isna().all()
    assert summary.quiet_wake_n_events_used.sum() == 0


def test_duplicate_or_incompatible_results_are_rejected():
    a = analyze_recording(recording(np.zeros(100), [4] * 10))
    with pytest.raises(ValueError, match="Duplicate"):
        aggregate_subjects([a, a])
    b = deepcopy(a)
    b.recording_id = "b"
    b.quality["mat_path"] = str(Path("b.mat").resolve())
    b.config = AnalysisConfig(transients=TransientConfig(min_prominence=1))
    with pytest.raises(ValueError, match="different analysis settings"):
        aggregate_subjects([a, b])


def test_analysis_rejects_unfinished_labels_and_large_misalignment():
    with pytest.raises(ValueError, match="coarse Wake"):
        analyze_recording(recording(np.ones(100), [0] * 10))
    with pytest.raises(ValueError, match="durations"):
        analyze_recording(recording(np.ones(100), [4] * 20))


@pytest.mark.parametrize("args", [(1, 0.025, 0.1), (120, 0.1, 0.025), (np.nan, 0.025, 0.1)])
def test_spectral_settings_validate_resolution(args):
    with pytest.raises(ValueError):
        SpectrumConfig(*args)


def test_filter_retention_matches_forward_backward_boxcar():
    assert smoothing_power_retention(0, 10) == pytest.approx(1)
    assert smoothing_power_retention(0.1, 10) == pytest.approx(0.9361, abs=0.001)


def test_peak_example_selection_is_seeded_and_marks_a_clear_quiet_wake_peak():
    renderer = _report_renderer_module()
    source = SimpleNamespace(
        labels=np.array([4] * 10 + [5] * 70),
        start_time=0.0,
        fs=1.0,
        ne=np.array([0.0] * 30 + [5.0] + [0.0] * 4 + [4.0] + [0.0] * 44),
    )
    events = pd.DataFrame(
        [
            {
                "recording_id": "example",
                "state": "quiet_wake",
                "complete": True,
                "crosses_state": True,
                "recording_start_qc_excluded": False,
                "peak_seconds": 30.0,
                "onset20_seconds": 20.0,
                "offset20_seconds": 40.0,
            },
            {
                "recording_id": "example",
                "state": "quiet_wake",
                "complete": True,
                "crosses_state": True,
                "recording_start_qc_excluded": False,
                "peak_seconds": 35.0,
                "onset20_seconds": 22.0,
                "offset20_seconds": 42.0,
            },
        ]
    )
    first = renderer.choose_peak_example(events, source, "example", seed=20260916)
    second = renderer.choose_peak_example(events, source, "example", seed=20260916)
    assert first.peak_seconds == second.peak_seconds
    assert first.quiet_seconds_shown >= renderer.MIN_EXAMPLE_QUIET_SECONDS
    assert first.active_seconds_shown >= renderer.MIN_EXAMPLE_ACTIVE_SECONDS
    assert first.context_peak_excess <= renderer.MAX_EXAMPLE_CONTEXT_PEAK_EXCESS


def test_raw_bout_comparison_uses_declared_common_start_interval():
    source = recording(
        [0, 1, 3, 1, 0, 0, 1, 4, 1, 0, 99, 99],
        [4, 4, 4, 4, 4, 5, 5, 5, 5, 5],
        fs=1,
        name="raw",
    )
    bouts, audit = analyze_raw_bouts(source)
    assert audit["common_start_samples"] == 10
    assert audit["tail_ne_seconds_not_analyzed"] == pytest.approx(2)
    assert bouts.raw_peak.tolist() == [3.0, 4.0]
    assert bouts.complete_shape.all()
    summaries = summarize_recordings(bouts, pd.DataFrame([audit]))
    results = paired_recording_results(summaries)
    assert results.loc[results.metric == "raw_peak", "n_recording_pairs"].item() == 1


def test_raw_bout_shape_can_cross_a_wake_state_boundary():
    source = recording([0, 1, 5, 4, 1, 0], [4, 4, 4, 5, 5, 5], fs=1, name="crossing")
    bouts, _ = analyze_raw_bouts(source)
    active = bouts.loc[bouts.state == "active_wake"].iloc[0]
    assert active.complete_shape
    assert active.crosses_state_boundary
    assert active.decay20_seconds > active.offset_seconds


def test_manifest_and_both_clis_roundtrip(tmp_path):
    path = tmp_path / "labeled.mat"
    savemat(path, {"ne": triangular_events(), "sleep_scores": [4] * 180, "ne_frequency": 10})
    manifest = tmp_path / "manifest.csv"
    manifest.write_text(
        "mouse_id,mat_path,recording_id\n007,labeled.mat,session1\n", encoding="utf-8"
    )
    assert read_manifest(manifest)[0]["mouse_id"] == "007"
    validation = tmp_path / "validation"
    assert validation_main([str(manifest), "--output", str(validation)]) == 0
    assert len(pd.read_csv(validation / "coverage.csv")) == 14
    config_file = tmp_path / "config.json"
    config_file.write_text(
        json.dumps({"spectrum": {"window_seconds": 120, "fmin": 0.025, "fmax": 0.1}})
    )
    output = tmp_path / "analysis"
    analysis_main([str(manifest), "--config", str(config_file), "--output", str(output)])
    subjects = pd.read_csv(output / "subjects.csv", dtype={"mouse_id": str})
    assert subjects.iloc[0].mouse_id == "007"
    assert subjects.iloc[0].active_wake_amplitude_median == pytest.approx(5)
    source = load_recording(path, "007")
    np.testing.assert_array_equal(source.labels, [4] * 180)
    a = analyze_file(path, "007")
    b = analyze_file(path, "007")
    pd.testing.assert_frame_equal(a.events, b.events)
    with pytest.raises(SystemExit):
        analysis_main([str(manifest), "--output", str(output)])


def test_validation_collects_errors_and_duplicate_manifest_fails(tmp_path):
    manifest = tmp_path / "manifest.csv"
    manifest.write_text("mouse_id,mat_path\nm1,missing.mat\n", encoding="utf-8")
    output = tmp_path / "v"
    assert validation_main([str(manifest), "--output", str(output)]) == 1
    assert len(pd.read_csv(output / "errors.csv")) == 1
    manifest.write_text("mouse_id,mat_path\nm1,missing.mat\nm1,missing.mat\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Duplicate"):
        read_manifest(manifest)
