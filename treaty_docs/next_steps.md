# Next Steps

## Currently Hot

- The PI-facing material is limited to `writeups/preliminary_recording_report.md`,
  `writeups/cluster_visualization_report.md`, its focused
  `writeups/cluster_visualization_wake_only_report.md` follow-up, its
  `writeups/cluster_visualization_wake_only_report_ne_excluded.md` NE-excluded
  sensitivity, and the
  source-preserving `writeups/nrem_baseline_cluster_target_report.md` comparison.
  Their committed figures live in the adjacent `writeups/assets/` tree. Do not treat any
  descriptive screen as independent-mouse biological inference.
- Local raw MAT files and regenerated products remain ignored: `data/` holds input
  and derived feature caches, `outputs/` holds recording-report tables, and
  `results/` holds cluster-coordinate and audit tables. Current feature caches are
  `data/derived_features/features_4/` and `data/derived_features/features_29/`.
- To regenerate the recording writeup, run `scripts/build_recording_report.py` and
  `scripts/render_recording_report_figures.py`. The paired unit is a MAT file;
  literal score-bout duration is distinct from peak-assigned NE shape timing.
- To regenerate cluster maps, run `scripts/extract_cluster_features.py` and
  `scripts/plot_cluster_embeddings.py`. MA is excluded before fitting, and
  combined-Wake runs collapse High/Low Alertness labels before sampling and fitting.
  EEG band powers use one-second left-aligned epochs, not five-second centred
  windows; the current cluster writeup gives the exact periodogram and integration
  convention.
  The all-feature Wake geometry is EMG-associated; no-EMG maps do not support a
  stable visible Wake subcluster in the fixed display.
- **PI-directed Wake clustering:** the completed 29-feature High/Low Alertness Wake-only
  analysis has 3, 4, and 5 spectral partitions of one symmetric k-nearest-neighbor
  graph. `scripts/plot_wake_knn_clusters.py` must continue to exclude labels from
  graph construction and clustering, retain per-cluster/per-recording label audits,
  and never use t-SNE or UMAP coordinates to form clusters. The recurring broad
  Low- and High-Alertness-associated groups are descriptive and EMG-associated; the
  smaller High-Alertness-only groups lack sufficient recurrence or stability evidence for a
  subtype claim. A pure small group establishes only label purity, not full
  High/Low Alertness separability; a separability claim also needs near-complete
  source-label coverage without cross-label contamination in held-out recordings.
- **NE-excluded Wake sensitivity:** removing `ne_mean` and
  `ne_slope_ols_per_second` leaves 27 EEG+EMG features and closely reproduces the
  full-feature graph partitions on the same 2,000 points (adjusted Rand 0.978,
  0.964, and 0.959 for 3, 4, and 5 groups). This is a feature-panel sensitivity
  result, not evidence that NE is biologically irrelevant or that the
  EMG-associated alertness organization is independently validated.
- **Experimental NREM-baseline calibration:** `scripts/calibrate_nrem_baseline.py`
  reimplements the source-preserving NREM-envelope comparison locally and targets
  the three-partition's two High-Alertness-only groups (clusters 2 and 3), never t-SNE/UMAP
  coordinates. On the current 2,000-point display sample, its predeclared
  multiplier sweep selected 10 robust SD above the NREM 75th percentile: 218/237
  target seconds were selected (92.0% recall), but 183 non-target seconds were
  also selected (54.4% precision). Across every one of the 38,120 current Wake
  seconds, it labels 10,539 (27.6%) High Alertness and 27,581 (72.4%) Low Alertness; the resulting
  per-recording High-Alertness share ranges from 2.3% to 65.0%. This is a stricter
  movement-associated rule, not an exact recovery of the graph targets or a
  production-label change.

## Scientific follow-up

- Inspect representative raw EMG/envelope traces and predeclare burst-threshold and
  feature-panel sensitivity work before interpreting EMG-associated Wake geometry.
- Repeat the NREM-baseline calibration with recording-held-out target assignment;
  assess its 10-robust-SD candidate against raw EMG traces before considering any
  upstream scoring change. Do not tune against t-SNE/UMAP coordinates or overwrite
  saved MAT labels.
- For a potential Wake subtype claim, predeclare parameter/seed stability and a
  recording-held-out cluster or prediction evaluation. Nonlinear map appearance is
  descriptive, not a cluster statistic.
- Verify mouse, session, condition, and circadian metadata before making an
  independent-animal comparison. Do not pool repeated recordings as mice.
- Keep the duration-mismatched `mouse5_day1.mat` excluded rather than trimming or
  padding it. Add MAT v7.3 support only if a supplied file requires it.

## Historical material

`archive/` preserves prior reports, figures, examples, and the superseded generic
manifest-based pipeline. It is retained for provenance and should not be extended
unless a specific historical comparison is requested.
