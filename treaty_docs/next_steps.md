# Next Steps

## Currently Hot

- The first real file, `data/35_app13_groundtruth.mat`, has been analyzed only as
  `unverified_35`: it contains no embedded mouse/session/condition identifier.
  Obtain and replace this with the explicit mapping; do not infer it from the filename.
- Its preflight passed: fs 10.1725 Hz, no gaps/coarse Wake, 1,118 s Active and
  753 s Quiet. Quiet has 0 eligible 120 s windows, 1 at 60 s, 6 at 30 s, and 28 at
  15 s; choose a common spectrum setting with the PI or leave slow spectra missing.
- Review the first-file event QC. Contained-event retention is 14/35 Active and
  2/25 Quiet candidates because 15/35 and 21/25 candidates cross a state boundary.
  The initial -99.6 percentage-point sample is stored input, not rewritten.
- Choose a common spectral window/band based on retained data and upstream smoothing.
  The example 120 s / 0.025–0.1 Hz is unvalidated. If Quiet Wake is too short, retain
  missing slow spectra instead of concatenating bouts or changing windows by state.
- Send the prepared PI meeting request, replacing its GitHub-report placeholder
  after a remote and Pages source are configured. Use the static report's paired
  raw-trace boundary examples to calibrate baseline/prominence if needed.
- Confirm the PI's duration definition and whether 20–80% means secant or regression.
  Current draft uses 20%-to-20% duration and secant slopes, positive decay magnitude.
- Compare contained-event vs peak-state summaries and inspect exclusion fractions;
  do not hide boundary-related selection bias in short Quiet Wake.
- The user requested a committed/pushed GitHub-rendered report. The repository has
  no Git remote yet; obtain the target remote or explicit authorization to create it,
  then configure Pages from `docs/` and replace the email's report-link placeholder.

## Follow-up After Pilot Validation

- Decide session/condition/circadian grouping before pooling unlike experiments.
- Add mouse/session-level uncertainty or group inference only after study design is known.
- Add MATLAB v7.3/HDF5 support if collected files require it.
- Consider onset-relative/continuous time-frequency analysis only as a separately
  defined contextual question if pure-state slow PSDs are not feasible.
- Consider overlap/renamed-file detection and stronger input checksums for large cohorts.
- Record preprocessing version/raw sampling/filter parameters upstream in future
  exports; current Python assumptions are documented, not recovered metadata.
