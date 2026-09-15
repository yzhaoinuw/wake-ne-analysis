# Next Steps

## Currently Hot

- The first real file, `data/35_app13_groundtruth.mat`, has been analyzed only as
  `unverified_35`: it contains no embedded mouse/session/condition identifier.
  Obtain and replace this with the explicit mapping; do not infer it from the filename.
- Its preflight passed: fs 10.1725 Hz, no gaps/coarse Wake, 1,118 s Active and
  753 s Quiet. Quiet has 0 eligible 120 s windows, 1 at 60 s, 6 at 30 s, and 28 at
  15 s. A 30 s / 0.1–0.2 Hz setting is only an exploratory sensitivity for this
  file; choose a common spectrum setting with the PI or leave slow spectra missing.
- Review the first-file event QC. Contained-event retention is 14/35 Active and
  2/25 Quiet candidates because 15/35 and 21/25 candidates cross a state boundary.
  Raw-data review found a large first-second recording-start excursion (initial
  −99.6 percentage points) that technical validation does not auto-flag because it
  is finite. Inspect start-of-recording values across new files and agree a
  reproducible clipping/exclusion rule only if the pattern recurs; do not alter
  current inputs meanwhile.
- Choose a common spectral window/band based on retained data and upstream smoothing.
  The example 120 s / 0.025–0.1 Hz is unvalidated. If Quiet Wake is too short, retain
  missing slow spectra instead of concatenating bouts or changing windows by state.
- Send PI correspondence directly, outside the repository. The static report and
  paired raw-trace boundary examples are ready to support the meeting and calibrate
  baseline/prominence if needed.
- Confirm the PI's duration definition and whether 20–80% means secant or regression.
  Current draft uses 20%-to-20% duration and secant slopes, positive decay magnitude.
- Compare contained-event vs peak-state summaries and inspect exclusion fractions;
  do not hide boundary-related selection bias in short Quiet Wake.
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
