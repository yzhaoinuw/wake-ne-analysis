# Handoff from the sleep-scoring development conversation

## User objective and present status

The user and PI want to compare the NE signal during Active Wake and Quiet Wake
in mice. The user has supplied an initial cohort of fully labeled MAT files. This
repository is a standalone pilot pipeline, **not yet biologically validated**. It was created
2026-09-14 at `C:\Users\yzhao\python_projects\wake-ne-analysis` from a conversation
in `C:\Users\yzhao\python_projects\sleep_scoring`.

Do not create a GitHub repository, PR, release, or publish experimental results
unless the user asks. Raw laboratory recordings are locally ignored and are never
committed.

## Decisions already agreed with the user

- Active Wake is saved as **4**, Quiet Wake as **5**. Keyboard keys in the scoring
  app are **5/6**; keys and saved values are intentionally different. Original
  Wake/NREM/REM/MA values are 0/1/2/3. Unscored is -1 or NaN.
- The original PI message requested NE "power frequency, amplitude, duration of
  increases and rising and decay T1/2." The PI clarified: **"We normally calculate
  the 20–80% slope."** Do not silently revert to half-time measurements.
- The user leaned toward spectral power/frequency, not NE signal elevation-episode count per minute.
  Counts here serve data adequacy; event rate is not a requested primary metric.
- Spectra use equal-length windows. **Slopes, amplitudes and durations do not.**
  Natural NE signal elevation-episode boundaries must survive spectral window selection.
- Quiet Wake could be predominantly short, and both states have variable bout
  lengths. Do not throw all short bouts out of every analysis. Report duration
  distributions and usable fractions before choosing spectral windows/frequencies.
- Do not concatenate noncontiguous state bouts to invent a continuous trace.
- Final dataframe: one row per mouse, separate Active/Quiet metric columns. Also
  retain per-file metrics and audit tables. Multiple files from the same mouse
  must remain usable without making each file/event a separate biological subject.
- A separate validation/coverage script and modular functions per MAT file are
  explicitly desired. No app UI changes and no dependency on the Dash app.

## Upstream repositories and contracts

- `C:\Users\yzhao\python_projects\sleep_scoring`: Active/Quiet experiment lives on
  `active-quiet-wake`; at handoff its feature work was uncommitted. Official
  trace identification was at `9ebcad2` on dev/main when that experiment started.
  Verify live Git state before working there; this project must not modify it.
- The scoring app preserves `sleep_scores` (displayed final labels) separately
  from `user_sleep_scores` (sparse calibration annotations). **Analyze the final
  `sleep_scores`, not the sparse layer or `sleep_scores_coarse`.**
- `C:\Users\yzhao\matlab_projects\preprocess_sleep_data`: active main function
  version comment 0.2.9 when inspected; also has an active Sirenia path. Saved `ne`
  is percentage delta-F/F; use `ne`, not any downstream `ne_standardized` field.
- Preprocessing fits 405 to 465, smooths the fitted control, computes percentage
  delta-F/F, smooths it with `filtfilt` using 1,000 moving-average coefficients,
  and downsamples. User confirmed factor **100** for the collected files.
- The final sampling rate is stored as `ne_frequency`, not necessarily exactly
  10 Hz. The raw sampling rate/filter metadata are not exported. Store this
  preprocessing assumption in run metadata rather than pretending it was verified
  from every MAT file. Measurements describe processed sensor dynamics.

## Draft choices to review, not settled lab protocol

- Spectral settings are deliberately unset in `AnalysisConfig()`; the JSON example
  is 120 s, 0.025–0.1 Hz, minimum three cycles. Do not promote it to a standard until
  coverage is measured on actual Active/Quiet bouts.
- Rolling 20th-percentile baseline over 60 s; prominence floor 0.5 percentage
  points plus a recording-wide difference-MAD threshold; 1 s peak separation.
- Duration is 20%-to-20% event width; slopes are 20–80% secants, positive decay
  magnitude. Confirm whether the PI instead uses regression through those samples
  or a different duration definition before scientific reporting.
- The PI selected peak-state assignment for the rapid proposal analysis: all complete
  candidates contribute to the final Active/Quiet state at their peak, including
  boundary-crossing support. Contained-event results remain a labelled sensitivity
  check. Keep crossing counts visible because the result is not a pure-state kinetics
  estimate.
- Event medians pool all eligible events per mouse. Spectra pool equal windows.
  No group significance testing, session/circadian stratification, or uncertainty
  estimates have been added. Inputs should not mix biological conditions blindly.

## Start the next session here

1. Read `AGENTS.md`, `treaty_docs/next_steps.md`, then `docs/methods.md` as needed.
2. The 2026-09-16 proposal run uses eight analyzable MAT files, pooled into four
   identified mice plus `unverified_35`; see `treaty_docs/next_steps.md` for the
   output locations and exclusions. Do not treat `unverified_35` as a biological
   mouse until an explicit mapping is supplied.
3. Resolve `mouse5_day1.mat` before any definitive analysis: it has 6.25 excess NE
   seconds relative to its labels, so it was excluded rather than trimmed.
4. Review the 15 s / 0.20–0.30 Hz peak-state figures as a high-frequency feasibility
   result. Quiet coverage is sparse in Mouse 3 and Mouse 7; every PSD maximum is at
   the 0.20 Hz band edge, so dominant-frequency values are not resolved oscillations.
5. Ask the PI whether 20–80% slopes replace T₁/₂ and define episode duration
   separately. The current 20%-to-20% duration is a transparent placeholder.
6. Keep changes and decisions in the treaty docs; the initial scientific choices
   are provisional and should not be assumed settled just because tests pass.
