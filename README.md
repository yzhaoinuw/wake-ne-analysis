# Wake NE analysis

Reproducible analyses behind the current descriptive PI-facing writeups:

- [Recording-level High/Low Alertness report](writeups/preliminary_recording_report.md)
- [EEG/EMG/NE cluster visualization report](writeups/cluster_visualization_report.md)
- [NREM-baseline Wake-labeling cluster-target follow-up](writeups/nrem_baseline_cluster_target_report.md)
- [NE dynamics: slopes, rising/declining trends, and variability](writeups/ne_dynamics_report.md)

Raw MATLAB files, derived feature archives, and CSV/JSON run outputs are deliberately
local and ignored. Final one-second `sleep_scores` are read unchanged: High
Alertness is 4 and Low Alertness is 5.

## Reproduce the current writeups

Use Python 3.11+ with the project dependencies. The existing local environment is
`sleep_scoring_dash3.0`.

```powershell
python scripts/build_recording_report.py --input-dir data --output outputs/recording_report
python scripts/render_recording_report_figures.py --analysis outputs/recording_report --output writeups/assets/recording_report

python scripts/extract_cluster_features.py --input-dir data --output-dir data/derived_features/features_29
python scripts/plot_cluster_embeddings.py --feature-dir data/derived_features/features_29 --feature-variant all --analysis-scope all_stages_no_ma --results-dir results/expanded_embedding/all_features_all_stages_no_ma --figures-dir writeups/assets/expanded_embedding/all_features_all_stages_no_ma
```

Each command refuses to overwrite a non-empty output directory. The cluster script
also supports `--feature-variant no_emg` and `--analysis-scope wake_only`; see the
cluster report for the four reported combinations and interpretation limits.

## NE dynamics and trailing variability

The first-pass dynamics analysis compares signed and absolute slope after a
0.1 Hz zero-phase low-pass, plus ordinary and linearly detrended variance over
the preceding 10 seconds of saved processed NE. History may cross **any** score
state. All eligible seconds are pooled with equal weight, irrespective of recording.
No label-history exclusions, relabeling, or additional normalization are applied.

```powershell
python scripts/analyze_ne_dynamics.py --input-dir data --feature-dir data/derived_features/ne_dynamics_v2_pooled --results-dir results/ne_dynamics_v2_pooled
python scripts/render_ne_dynamics.py --results-dir results/ne_dynamics_v2_pooled
```

Use fresh directory names when rerunning; existing outputs are never overwritten.
The completed September 23 run uses the suffix `ne_dynamics_v2_pooled_20260923` for both
directories. The renderer creates standalone interactive HTML files. Add `--png`
for static Plotly/Kaleido images and `--output-dir` to choose a fresh figure folder.
Extraction and rendering run independently; neither needs UMAP or Matplotlib.

Per-second features are stored in one source-stem NPZ per recording with feature
names/units, local and absolute timestamps, unchanged labels, NaNs for unavailable
values, and source/configuration provenance. Main tables contain pooled state
means, retained quantiles, valid/missing counts, and rank-biserial effects. Comparisons use
all available seconds, two-sided Mann-Whitney U, and four-feature Holm correction.
P-values are nominal: correlated seconds and cross-recording scale differences
remain caveats, not independent-animal evidence. Technical
definitions and boundary handling are documented in
[`ne_dynamics.py`](wake_ne_analysis/ne_dynamics.py); statistical definitions are in
[`dynamics_summary.py`](wake_ne_analysis/dynamics_summary.py).

All ten files are retained. Excess NE after the score interval is trimmed
in memory before filtering and listed in `source_audit.csv`; sources are unchanged.
Where NE ends first, incomplete final score seconds stay missing.
Optional descriptive mouse summaries can be requested using `--metadata` with columns
`recording_id,mouse_id,condition`, one row per included recording (recording IDs
are MAT filename stems). Seconds are pooled within mouse and condition **before**
medians; conditions are never pooled together in those optional mouse summaries.
The main comparison always pools all eligible seconds, independent of metadata.
No recording-comparison test or plot is generated. Older v1 outputs are retained
as superseded history, not mixed with the v2 archives.

The same [NE dynamics report](writeups/ne_dynamics_report.md)
separates the fraction of rising/declining seconds from signed slope within each
direction and includes ordinary/detrended trailing variance. `render_ne_dynamics.py`
also produces a focused `variance_dynamics` figure. Figures and the current report
show arithmetic means. The renderer reads verified feature archives and saves a
comparison table with means alongside the figures, checking that the original
distribution tests are unchanged. Those tests are not tests of mean differences.
Its descriptive table and figure can be regenerated from the completed archives:

```powershell
python scripts/summarize_ne_slope_direction.py --analysis-dir results/ne_dynamics_v2_pooled_20260923 --output-dir results/ne_slope_direction_signed_20260923 --png
```

This follow-up adds no significance tests and uses a fresh output directory.

## Experimental NREM-baseline calibration

The `nrem-baseline` experiment keeps source MAT files unchanged.  It derives a
recording-specific 20 Hz EMG envelope, anchors its threshold to the NREM 75th
percentile plus a shared robust-SD multiplier, and tests that multiplier only
against pre-existing spectral partitions of a k-nearest-neighbor graph—not t-SNE
or UMAP coordinates.

```powershell
python scripts/calibrate_nrem_baseline.py --input-dir data --clustered-points results/wake_knn_clusters_20260918/3_clusters/clustered_wake_points.csv --target-clusters 2 3 --output-dir results/nrem_baseline_calibration
```

The command evaluates multipliers from 0 to 32 in 0.25 increments. It selects the
one with the highest mean F1 across recordings containing target points, breaking
ties by specificity and then stricter multiplier. Its outputs are experimental CSV/
JSON audits; they do not overwrite `sleep_scores` or establish a production scoring
rule.

## Layout

`writeups/` holds the current reports and committed figures. `wake_ne_analysis/` and
`scripts/` hold only the code needed to regenerate them. `archive/` retains the
superseded generic pipeline, examples, figures, and earlier writeups for provenance.
See [project overview](project_overview.md) for the current code map.
