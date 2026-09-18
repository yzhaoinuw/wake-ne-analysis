# Wake NE analysis

Reproducible analyses behind two current descriptive PI-facing writeups:

- [Recording-level Active/Quiet Wake report](writeups/preliminary_recording_report.md)
- [EEG/EMG/NE cluster visualization report](writeups/cluster_visualization_report.md)

Raw MATLAB files, derived feature archives, and CSV/JSON run outputs are deliberately
local and ignored. Final one-second `sleep_scores` are read unchanged: Active Wake is
4 and Quiet Wake is 5.

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

## Layout

`writeups/` holds the current reports and committed figures. `wake_ne_analysis/` and
`scripts/` hold only the code needed to regenerate them. `archive/` retains the
superseded generic pipeline, examples, figures, and earlier writeups for provenance.
See [project overview](project_overview.md) for the current code map.
