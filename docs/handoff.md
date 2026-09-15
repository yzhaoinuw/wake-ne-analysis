# Handoff from the sleep-scoring development conversation

## User objective and present status

The user and PI want to compare NE fluorescence during Active Wake and Quiet Wake
in mice. The user is gathering fully labeled MAT files. This repository is a
standalone pilot pipeline, **not yet validated on real recordings**. It was created
2026-09-14 at `C:\Users\yzhao\python_projects\wake-ne-analysis` from a conversation
in `C:\Users\yzhao\python_projects\sleep_scoring`.

The initial local repository has no remote or commits; work is ready for review.
Do not create a GitHub repository, PR, release, or publish experimental results
unless the user asks. No raw laboratory recordings have been copied into this repo.

## Decisions already agreed with the user

- Active Wake is saved as **4**, Quiet Wake as **5**. Keyboard keys in the scoring
  app are **5/6**; keys and saved values are intentionally different. Original
  Wake/NREM/REM/MA values are 0/1/2/3. Unscored is -1 or NaN.
- The original PI message requested NE "power frequency, amplitude, duration of
  increases and rising and decay T1/2." The PI clarified: **"We normally calculate
  the 20–80% slope."** Do not silently revert to half-time measurements.
- The user leaned toward spectral power/frequency, not transient count per minute.
  Counts here serve data adequacy; event rate is not a requested primary metric.
- Spectra use equal-length windows. **Slopes, amplitudes and durations do not.**
  Natural transient boundaries must survive spectral window selection.
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
- Primary events are complete and contained in a single state; crossing candidates
  are retained and flagged. Peak-state assignment is an explicit alternative for
  sensitivity checks. State-boundary selection bias still needs inspection.
- Event medians pool all eligible events per mouse. Spectra pool equal windows.
  No group significance testing, session/circadian stratification, or uncertainty
  estimates have been added. Inputs should not mix biological conditions blindly.

## Start the next session here

1. Read `AGENTS.md`, `treaty_docs/next_steps.md`, then `docs/methods.md` as needed.
2. Ask the user for the collected MAT paths and explicit mouse/session/condition
   mapping. Use a manifest; never derive mouse identities from arbitrary filenames.
3. Run validation first. Inspect sampling rates, duration mismatches, gaps, unsplit
   Wake, bout lengths, and coverage of BOTH states at candidate window durations.
4. Review real event traces and thresholds with the user/PI. A graphical event QC
   plot is a useful next addition; current audit outputs are tables only.
5. Choose one common spectral configuration (or declare slow spectra infeasible
   for short Quiet Wake), run the analysis, and check event boundary sensitivity.
6. Keep changes and decisions in the treaty docs; the initial scientific choices
   are provisional and should not be assumed settled just because tests pass.
