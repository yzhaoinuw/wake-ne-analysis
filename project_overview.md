# Project overview

This repository contains the reproducible code and committed figures behind two
current, descriptive Wake/NE writeups. It does not contain raw MAT files or saved
feature matrices.

| Current workflow | Command entry point | Core modules |
|---|---|---|
| Recording-level Active/Quiet Wake report | `build_recording_report.py`, then `render_recording_report_figures.py` | `recording_report.py`, `io.py`, `spectra.py`, `config.py` |
| EEG/EMG/NE cluster visualization | `extract_cluster_features.py`, then `plot_cluster_embeddings.py` | `cluster_features.py`, `stages.py` |

`writeups/` contains the current reports and their static figures. Locally generated
MAT files, CSV/JSON outputs, and feature archives remain ignored under `data/`,
`outputs/`, and `results/`. `archive/` preserves the previous generic pipeline,
examples, reports, and figures for provenance; it is not part of the maintained
workflow.

Final one-second `sleep_scores` are read without relabeling: Active Wake is 4 and
Quiet Wake is 5. The cluster maps are descriptive; use the caveats in the cluster
writeup before interpreting visible geometry as a biological subtype.
