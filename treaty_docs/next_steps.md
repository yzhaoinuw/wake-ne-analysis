# Next Steps

## Currently Hot

- The PI-facing material is limited to `writeups/preliminary_recording_report.md`
  and `writeups/cluster_visualization_report.md`. Their committed figures live in
  the adjacent `writeups/assets/` tree. Do not treat either descriptive screen as
  independent-mouse biological inference.
- Local raw MAT files and regenerated products remain ignored: `data/` holds input
  and derived feature caches, `outputs/` holds recording-report tables, and
  `results/` holds cluster-coordinate and audit tables. Current feature caches are
  `data/derived_features/features_4/` and `data/derived_features/features_29/`.
- To regenerate the recording writeup, run `scripts/build_recording_report.py` and
  `scripts/render_recording_report_figures.py`. The paired unit is a MAT file;
  literal score-bout duration is distinct from peak-assigned NE shape timing.
- To regenerate cluster maps, run `scripts/extract_cluster_features.py` and
  `scripts/plot_cluster_embeddings.py`. MA is excluded before fitting, and
  combined-Wake runs collapse Active/Quiet labels before sampling and fitting.
  The all-feature Wake geometry is EMG-associated; no-EMG maps do not support a
  stable visible Wake subcluster in the fixed display.

## Scientific follow-up

- Inspect representative raw EMG/envelope traces and predeclare burst-threshold and
  feature-panel sensitivity work before interpreting EMG-associated Wake geometry.
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
