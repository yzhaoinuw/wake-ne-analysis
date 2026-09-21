# Wake NE analysis

Reproducible analyses behind two current descriptive PI-facing writeups:

- [Recording-level High/Low Alertness report](writeups/preliminary_recording_report.md)
- [EEG/EMG/NE cluster visualization report](writeups/cluster_visualization_report.md)
- [NREM-baseline Wake-labeling cluster-target follow-up](writeups/nrem_baseline_cluster_target_report.md)

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
