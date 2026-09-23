# Project overview

This repository contains the reproducible code and committed figures behind the
current descriptive Wake/NE writeups and one source-preserving Wake-labeling
comparison. It does not contain raw MAT files or saved feature matrices.

| Current workflow | Command entry point | Core modules |
|---|---|---|
| Recording-level High/Low Alertness report | `build_recording_report.py`, then `render_recording_report_figures.py` | `recording_report.py`, `io.py`, `spectra.py`, `config.py` |
| EEG/EMG/NE cluster visualization | `extract_cluster_features.py`, then `plot_cluster_embeddings.py` | `cluster_features.py`, `stages.py` |
| Experimental NREM-baseline Wake calibration | `calibrate_nrem_baseline.py` | `nrem_baseline.py` |
| Pooled-second NE slopes and trailing variability | `analyze_ne_dynamics.py`, then `render_ne_dynamics.py` | `ne_dynamics.py` (signal features), `dynamics_summary.py` (pooled statistics), `dynamics_workflow.py` (archives and audits), `dynamics_plots.py` (figures) |

`writeups/` contains the current reports and their static figures. Locally generated
MAT files, CSV/JSON outputs, and feature archives remain ignored under `data/`,
`outputs/`, and `results/`. `archive/` preserves the previous generic pipeline,
examples, reports, and figures for provenance; it is not part of the maintained
workflow.

Final one-second `sleep_scores` are read without relabeling: High Alertness is 4
and Low Alertness is 5. The cluster maps are descriptive; use the caveats in the cluster
writeup before interpreting visible geometry as a biological subtype.

The NREM-baseline command is deliberately an experimental, source-preserving
comparison. It calibrates one shared robust-SD multiplier against existing graph
cluster assignments and writes only local audit files. It must not be treated as a
replacement for the upstream manually reviewed scoring workflow without independent
recording-held-out and raw-trace validation.
