# Project Overview

## What This Repo Is

Independent, deterministic NE signal analysis for labeled Active/Quiet Wake
MAT files. Outputs per-file audit tables and one-row-per-mouse descriptive statistics.
Real recordings are pending; see [handoff](docs/handoff.md) for scientific context.

## Active Runtime Path

`scripts/summarize_usable_data.py` calls validation without event analysis.
`scripts/analyze_ne.py` reads a manifest/config, analyzes files, pools results, and
writes new CSV/JSON output directories. Both delegate to the installable package.
`scripts/plot_ne_results.py` turns analysis and optional preflight CSV tables into
an interactive HTML audit report; it does not reread or modify MAT files.

| Module | Responsibility |
|---|---|
| `config.py` | Serializable validated settings; spectra require an explicit choice |
| `io.py` | MAT contract, explicit mouse identity, manifest duplicate checks, runs |
| `validation.py` | Quality, bout duration, candidate-window coverage, smoothing diagnostic |
| `spectra.py` | Per-file fixed-window PSDs and frequency-band metrics |
| `transients.py` | Whole-trace event detection and natural 20/80 crossing metrics |
| `pipeline.py` | Combine independent metrics into `RecordingAnalysis`; per-file/batch entry points |
| `aggregation.py` | Pool events and weighted PSDs into mouse rows |
| `cli.py` | CLI arguments, audit-table exports and run provenance |

Module files live in `wake_ne_analysis/`. Package imports have no app/server or
filesystem side effects. `analyze_file` loads only NE/labels/needed metadata;
`analyze_recording` reuses an existing object. Individual spectrum, NE signal elevation-episode and
validation file functions are public for per-MAT use.

## User Data Expectations

Percentage delta-F/F NE; actual `ne_frequency`/`fp_frequency`; one-second final
`sleep_scores` (4/5); shared optional `start_time`. No MAT v7.3 yet. No guessed
subject IDs, no calibration labels, no scoring-model predictions inside this repo.
Missing/invalid data are reported; analysis fails rather than silently drop files.

## What Looks Active vs. Legacy

All package modules are active. The example config is illustrative and the example
manifest refers to files the user has not provided yet. They are not research data.
There is no legacy pipeline or GUI in this new repository.

## Authored vs. Derived

Code, tests, examples and docs are authored. `outputs/` CSV/JSON files and `.pytest_tmp/`
are derived and ignored. MATLAB data belong in ignored `data/` or external locations.
`treaty_conventions.md` is upstream-maintained; other treaty docs are project-specific.

## Tests And Fixtures

`tests/test_pipeline.py` synthesizes known-power sinusoids, triangular transients,
gaps and state transitions. It checks units/timing, metric formulas, no stitching,
weighting, event selection, missingness, duplicate rejection, repeatability and both
CLI exports. No biological thresholds have been validated by these fixtures.

## Questions Worth Clarifying Later

See [next steps](treaty_docs/next_steps.md): real-data coverage, common spectral band,
event baseline/prominence, secant-versus-regression slope convention, boundary
sensitivity, session/condition grouping, graphical QC, and MAT v7.3 if needed.

The previous presentation-ready cohort artifacts are preserved in
[docs/archived](docs/archived/); the refreshed recording-level report is pending the
complete input set.
