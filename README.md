# Wake NE Analysis

Standalone Python analysis of processed NE fluorescence during **Active Wake**
and **Quiet Wake**. Analyze one labeled MAT file, then pool recordings into one
dataframe row per mouse. No scoring-app imports, interface, relabeling, or input
file modifications.

This is a tested **pilot draft using synthetic signals**. Real MAT files are being
collected. Event-detection parameters and the spectral window/band must be reviewed
against those recordings before biological conclusions are drawn.

## Preliminary pilot report

The first real-file, single-recording pilot is presented in a GitHub-renderable
[preliminary report](docs/preliminary_report.md). It documents descriptive results,
figures, and PI decisions needed before cohort-level interpretation.

## Quick start

The initial implementation was tested with the existing Conda environment:

```powershell
conda activate sleep_scoring_dash3.0
```

Or use Python 3.11+ and install the independent package and its tests:

```powershell
python -m pip install -e ".[test]"
python -m pytest -q
```

Copy `examples/manifest.csv` and fill in explicit mouse IDs and MAT paths.
Relative paths resolve against the **manifest directory**, not the working directory.
Optional `recording_id` values must be unique across the entire manifest.
IDs such as `007` are preserved as text. Do not list overlapping chunks or the same
recording twice, and keep conditions/time periods you intend to compare in separate
manifests; there is no automatic condition grouping yet.

First inspect data quality, bout durations, and candidate spectral-window coverage:

```powershell
python scripts/summarize_usable_data.py examples/manifest.csv --output outputs/preflight01
```

Then choose common spectral settings for both states and all included mice:

```powershell
python scripts/analyze_ne.py examples/manifest.csv --config examples/config.json --output outputs/analysis01
```

To make an interactive, shareable HTML report from the resulting CSV dataframes,
use the separate plotting script. Supply the validation output as `--preflight` to
include spectral-window coverage and wake-bout durations:

```powershell
python scripts/plot_ne_results.py outputs/analysis01 `
  --preflight outputs/preflight01 --output outputs/analysis01_report.html
```

The report shows descriptive per-mouse points, candidate-versus-retained events,
and relevant coverage/audit distributions. It does not calculate group tests.
Install the optional plotting dependency with `python -m pip install -e ".[plot]"`
if Plotly is not already available.

**The example's 120-second window and 0.025–0.1 Hz band are illustrative, not a
validated recommendation.** Select them after inspecting the coverage reports.
Omit `--config` (or set `"spectrum": null`) to compute transient summaries while
leaving spectral metrics explicitly unconfigured. Equal windows never constrain
transient measurements.

Installed commands `wake-ne-validate` and `wake-ne-analyze` provide the same interfaces.
Every run needs a new output directory; previous results are not overwritten.

## Inputs

Each ordinary MATLAB MAT file needs:

| Field | Contract |
|---|---|
| `ne` | Single-channel processed **percentage delta-F/F** vector, without additional z-scoring |
| `ne_frequency` | Positive sampling rate in Hz; `fp_frequency` accepted as an alias |
| `sleep_scores` | One-second labels: 4 Active Wake, 5 Quiet Wake; 1 NREM, 2 REM, 3 MA |
| `start_time` | Optional recording-relative offset in seconds, default 0 |

Both vectors begin at the same `start_time`. Sample `i` is at `start_time + i/fs`;
label `j` covers `[start_time+j, start_time+j+1)`. No alignment correction is guessed.
Coarse Wake (`0`) is rejected by analysis by default, because the expected inputs
are fully wake-subtyped. `-1`/NaN labels remain unscored. NaN/Inf NE samples create
gaps, which spectra and events never bridge. An NE/label duration discrepancy over
one second stops analysis. Validation still reports such problems for all files.

Only needed variables are loaded; large EEG/EMG arrays are not read. MATLAB v7.3
(HDF5) is not supported in this draft: export the required fields with MATLAB `-v7`.

The units/preprocessing assumption comes from `preprocess_sleep_data.m` and
`preprocess_sirenia.m` in the sibling MATLAB project, inspected 2026-09-14:
405-to-465 control fitting, percentage delta-F/F, a 1,000-sample moving average
applied with `filtfilt`, and downsampling by 100 (confirmed by the user).
The MAT stores the final sampling rate but not the filter/factor provenance.
The JSON config records those assumptions; it does not apply that filtering again.

## Outputs

`subjects.csv` is the requested **one row per mouse** dataframe. Columns begin with
`active_wake_` or `quiet_wake_`:

- `band_power`, `dominant_frequency_hz`
- `amplitude_median`, `duration_seconds_median`, `rise_slope_median`, `decay_slope_median`
- State time, valid NE time, bout/event/window counts, retained-event fraction,
  spectral coverage, and spectral status

Amplitude is in delta-F/F percentage points; positive rise/decay magnitudes are
percentage points/second; event duration is seconds. PSD is percentage-points²/Hz;
integrated band power is percentage-points². A dominant frequency is the maximum
PSD **inside the selected band**, not proof of a distinct biological oscillation.

Additional CSVs make the results inspectable:

| File | Contents |
|---|---|
| `recordings.csv` | Same statistics separately for each MAT file |
| `events.csv` | Every detected candidate, crossings, threshold, baseline, eligibility and boundary flags |
| `spectral_windows.csv` | Each eligible fixed window and its band power |
| `recording_spectra.csv`, `subject_spectra.csv` | Averaged PSD curves, frequencies and contributing window counts |
| `coverage.csv`, `quality.csv` | Used versus available data and file diagnostics |
| `run.json` | Exact configuration, software versions, input paths/sizes/modification times |

The separate validation command writes `quality.csv`, `coverage.csv`, `bouts.csv`,
`errors.csv`, and `run.json`. Its nonzero exit code reports unreadable/invalid files.
Analysis fails on invalid input rather than silently removing a file from a mouse.
Missing metrics are NaN/blank, never fabricated zeros. Valid no-event/no-window
counts are zero; the accompanying missing metric remains NaN.

## Python API

```python
from wake_ne_analysis import (
    AnalysisConfig, SpectrumConfig, analyze_file, aggregate_subjects,
    compute_spectrum_file, compute_transients_file, validate_file,
)

config = AnalysisConfig(spectrum=SpectrumConfig(120, 0.025, 0.1))  # example only
a = analyze_file("data/mouse01_day1.mat", "mouse01", config, recording_id="m01_d1")
b = analyze_file("data/mouse01_day2.mat", "mouse01", config, recording_id="m01_d2")
subjects = aggregate_subjects([a, b])  # pandas DataFrame, one row for mouse01
events = compute_transients_file("data/mouse01_day1.mat", "mouse01")
psd, windows = compute_spectrum_file("data/mouse01_day1.mat", "mouse01", config.spectrum)
quality, coverage, bouts = validate_file("data/mouse01_day1.mat", "mouse01")
```

`load_recording` plus `analyze_recording`, `compute_spectrum`, and `detect_transients`
allow reusing a loaded recording without rereading it for each metric.

Read [methods](docs/methods.md) for exact definitions and exclusions, and
[handoff](docs/handoff.md) for the decisions from the originating conversation.
Start future agent sessions with [AGENTS.md](AGENTS.md).
