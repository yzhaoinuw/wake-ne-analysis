# Next Steps

## Currently Hot

- **2026-09-17 recording-level refresh:** the two 2026-09-16 cohort reports are now
  archived under `docs/archived/`; their section structure is the template for the
  replacement. The raw-bout workflow now reports the mean saved processed-NE value
  within each labelled score bout (not its peak), actual score-bout duration, and
  score-bout count in the recording-paired table/figure. The deliberately pooled
  bout table/figure omits mean NE because different recordings can have different
  signal baselines. Width, 20--80% slopes, and short-window spectral measures keep
  their existing definitions and qualifications. The user confirmed that the current
  input set is 10 MAT files, and the published report is
  `docs/preliminary_recording_report.md` with figures in
  `docs/assets/recording_report_20260917/`. Do not convert its recording-level or
  pooled-bout screens into independent-animal inference; regenerate only when a
  deliberately revised input set or grouping design is supplied.

- `docs/archived/preliminary_report_raw_bout_recordings_20260916.md` is the archived,
  intentionally
  exploratory zero-referenced sensitivity screen. It contains both a paired,
  per-file Wilcoxon screen and a clearly quarantined per-bout Mann--Whitney
  description, plus analogous recording-paired and pseudoreplicated-window spectral
  screens. Its 20%/80% widths and slopes are deliberately peak-assigned full-NE-event
  measures: their supports may cross a score boundary, so label them clearly as such
  and never as sleep-score-bout duration. Its trace example must retain the distinct
  literal-maximum rule: no rolling baseline, prominence threshold, or local-peak
  detector. The prominent score-label table is the actual run-duration result (not
  the NE-episode-width table). The independent-observation calculations knowingly
  pseudoreplicate correlated bouts/windows and are not biological inference. Do not
  turn any screen into a mouse-level conclusion or merge it with the local-baseline
  report. Future submissions should retain verified mouse/session metadata and run a
  predeclared sensitivity analysis of literal versus local-baseline definitions.
- The archived executive, GitHub-renderable cohort draft is
  `docs/archived/preliminary_report_20260916.md`; its static figures live in
  `docs/assets/cohort_preliminary_report/`. The earlier single-recording document
  is preserved as `docs/pilot_report.md` and is historical rather than the current
  cohort result. Its renderer uses the upstream orange Active/light-blue Quiet color
  contract and seed `20260916` for an auditable Quiet-Wake peak example. The report
  now separates actual score-bout geometry from peak-assigned NE-event width/slopes.
  Crossing is explicitly allowed by the peak-state contract (38% of retained Active
  and 78% of retained Quiet events cross a score boundary), so those timing metrics
  describe full NE events assigned by their peaks, not score-bout duration. Review
  the draft's 20--80% secant/T1/2 definition with the PI before treating it as a final
  kinetic metric. Also inspect representative traces and declare a sensitivity
  analysis before accepting the 60-second rolling-baseline width or 20th-percentile
  level as a final event-detector definition.
- The 2026-09-16 proposal delivery is in
  `outputs/proposal_cohort_20260916_final_peak15_presentation.html` with PNG panels
  in `outputs/proposal_cohort_20260916_final_peak15_figures/`. The contained-event
  sensitivity counterpart uses the `final_contained15` names. Inputs are listed in
  `data/proposal_cohort_eligible_manifest_20260916.csv`.
- Nine files were audited; eight passed the analysis contracts and pool into Mouse 1,
  3, 5, 7, and a clearly separate `unverified_35` row. The replacement
  `35_app13_groundtruth.mat` still lacks an embedded identity, so obtain an explicit
  mapping before any biological aggregation. `mouse5_day1.mat` has 6.25 more NE
  seconds than labels and is excluded rather than silently truncated.
- Three recordings have a reproducible first-second NE excursion. The final proposal
  run applies a cohort-wide, recorded 15-second start exclusion to event eligibility
  and spectral windows; raw, unexcluded outputs remain as a sensitivity check.
- For files newly scored with the sibling app's automatic subdivision, retain the
  NREM-anchored detector provenance: threshold = NREM RMS 75th percentile plus two
  MAD-derived robust SDs, with a one-second minimum activity bout. Review this pilot
  setting against real recordings/video before treating Active/Quiet labels as a
  validated behavioral measure.
- For the rapid proposal analysis, assign each complete NE signal elevation episode
  to the state at its peak (`assignment="peak"`). Keep contained-event results and
  crossing counts as a clearly labelled sensitivity check.
- Cohort preflight chose the 15 s / 0.20–0.30 Hz common fallback: Mouse 7 has no
  Quiet 20 s windows but has three at 15 s. This is an explicitly high-frequency
  feasibility result, not the earlier slow-spectrum question. All reported PSD
  maxima lie at 0.20 Hz, the lower band edge; do not interpret them as resolved
  dominant frequencies. Never stitch bouts, pad data, or use state-specific settings.
- Send PI correspondence directly, outside the repository. The static report and
  paired raw-trace boundary examples are ready to support the meeting and calibrate
  baseline/prominence if needed.
- Confirm the PI's duration definition and whether 20–80% means secant or regression.
  Current draft uses 20%-to-20% duration and secant slopes, positive decay magnitude.
- Ask the PI whether 20–80% slopes replace rising/decay T₁/₂ and define episode
  duration separately. The current 20%-to-20% duration and secant slopes remain
  transparent provisional choices. Do not treat events or files as independent mice.
- The GitHub-rendered report is committed and pushed to `origin/main`. Configure
  GitHub Pages from `docs/` only if a Pages URL is desired; the direct GitHub report
  link is already suitable for the meeting request.

## Follow-up After Pilot Validation

- Decide session/condition/circadian grouping before pooling unlike experiments.
- Add mouse/session-level uncertainty or group inference only after study design is known.
- Add MATLAB v7.3/HDF5 support if collected files require it.
- Consider onset-relative/continuous time-frequency analysis only as a separately
  defined contextual question if pure-state slow PSDs are not feasible.
- Consider overlap/renamed-file detection and stronger input checksums for large cohorts.
- Record preprocessing version/raw sampling/filter parameters upstream in future
  exports; current Python assumptions are documented, not recovered metadata.
