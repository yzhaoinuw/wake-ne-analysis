# Work Log

## 2026-09-16

### Executive cohort report draft (Codex GPT-5; effort/tokens not reported)

- Renamed the historical, single-recording report to `docs/pilot_report.md` and
  created `docs/preliminary_report.md` for the current eight-recording cohort.
  The new report presents mouse-paired medians, IQRs, sample sizes, and two-sided
  Wilcoxon p-values without treating events, windows, files, or the unidentified
  source as independent mice.
- Added a reusable renderer and three static report figures: paired metric results,
  15-versus-20-second spectral-window coverage, and a raw-trace example of the
  PI-directed peak-state assignment. The report separates high-level methods from
  appendix equations and explains the provisional 20%-to-20% duration, 20–80%
  secant slopes, spectrum boundary limitation, and small-sample interpretation.
- Verification:
  - Rendered and visually inspected the three static cohort-report figures from the
    QC'd peak-state output.
  - `python -m pytest --basetemp .pytest_tmp_preliminary_report -p no:cacheprovider -q`:
    25 passed.
  - `git diff --check` passed.

### Cohort proposal delivery with start-artifact QC (Codex GPT-5; effort/tokens not reported)

- Audited all nine supplied MAT files. Eight are analyzable and pooled into Mouse 1,
  3, 5, 7, and separately labeled `unverified_35`; embedded video metadata supplied
  the mouse/session mapping for the named files. `mouse5_day1.mat` has a 6.25-second
  NE/label duration mismatch and was excluded without trimming either vector.
- Preflight selected the common 15 s / 0.20–0.30 Hz fallback because Mouse 7 has no
  Quiet 20-second window but has three Quiet 15-second windows. Its PSD maxima all
  occur at the 0.20 Hz lower edge, so the reported band maximum is not a resolved
  oscillation and the spectrum is explicitly high-frequency exploratory.
- Recurrent large recording-start excursions appeared in three files; two produced
  artificial, complete Active-Wake candidates. Added a 15-second cohort-wide start
  exclusion that flags, but does not delete, early candidates and excludes initial
  spectral windows without modifying inputs. The final peak-state and contained-event
  sensitivity reports include interactive HTML plus five PNG panels each.
- Added the agenda question distinguishing T₁/₂, 20–80% slopes, and the separate
  provisional 20%-to-20% duration rule.
- Verification:
  - Full-manifest preflight: 9 files audited, 0 structural-load errors.
  - Eligible-manifest preflight: 8 files, 0 errors; peak-state and contained-event
    runs each wrote five descriptive subject rows and their audit tables.
  - Rendered and visually inspected the peak-state static metric and spectral panels.
  - `python -m pytest --basetemp .pytest_tmp_final -p no:cacheprovider -q`: 25 passed.

## 2026-09-15

### Document upstream NREM-anchored Wake subdivision (Codex GPT-5; effort/tokens not reported)

- Documented the upstream Active/Quiet Wake contract used by this analysis: final
  labels 4/5 follow EMG RMS subdivision of coarse Wake, anchored automatically to
  the NREM RMS 75th percentile plus two MAD-derived robust standard deviations.
  The one-second duration and multiplier remain pilot settings requiring real-data
  review; this repository continues to analyze saved labels without relabeling them.
- Verification:
  - Reviewed the sibling scoring implementation; its full Python suite passed
    (254 tests). `git diff --check` passed here; no NE input, score, or analysis
    result was changed.

### PI direction for rapid proposal analysis (Codex GPT-5; effort/tokens not reported)

- The PI selected peak-state attribution for complete NE signal elevation episodes:
  include a boundary-crossing episode in the final Active/Quiet Wake state at its
  peak. The report must retain crossing counts and identify this as a peak-state,
  rather than pure-state, kinetic summary.
- The PI requested short common spectral intervals to assess whether the proposal
  shows promise. Prepared 20 s / 0.15–0.25 Hz and 15 s / 0.20–0.30 Hz exploratory
  configurations; cohort-wide 15 s and 20 s preflight coverage will select the
  primary plot configuration without stitching bouts or changing settings by state.
- Verification:
  - No input MAT file, sleep label, or NE value was changed. The supplied first file
    remains the sole local recording until the newly relabeled files are provided.

### Clarify raw-start QC and spectral interpretation (Codex GPT-5; effort/tokens not reported)

- Corrected the report to distinguish raw-data review from automatic validation: the
  initial −99.6 percentage-point recording-start excursion is finite, so it is not
  automatically flagged by the current pipeline. It remains unmodified while more
  files determine whether a reproducible clipping/outlier rule is warranted.
- Added a frequency-interpretation guideline. For the first file's approximately
  0.983 s forward–backward moving-average pass, smoothing-only retained power is
  about 94% at 0.1 Hz, 77% at 0.2 Hz, 55% at 0.3 Hz, and 18% at 0.5 Hz. This supports
  cautious interpretation of slow modulation through roughly 0.2 Hz, subject to the
  more restrictive continuous-bout coverage for any selected spectral band.
- Verification:
  - No data, preprocessing setting, detector threshold, or spectral configuration
    was changed.

### Keep PI correspondence outside the repository (Codex GPT-5; effort/tokens not reported)

- Removed the PI meeting-request draft from `docs/`. The repository retains the
  report and decision agenda, but not correspondence intended for direct sending.
- Verification:
  - Searched documentation for links to the removed draft; none remain.

### Plain-language NE signal terminology (Codex GPT-5; effort/tokens not reported)

- Adopted **NE signal elevation episode** as the human-facing term for the detected
  local rise-and-fall feature. Documentation now uses `NE signal` for the processed
  measurement and retains the code/API name `transient` only where it is part of a
  stable identifier.
- Verification:
  - Reviewed all human-facing Markdown references to NE fluorescence/transients.

### GitHub-renderable pilot report and PI decision agenda (Codex GPT-5; effort/tokens not reported)

- Prepared a static Markdown/PNG report, rather than relying on interactive browser
  output, so the first-file evidence and its limits render on GitHub and a future
  Pages site. Raw MAT and CSV run outputs remain ignored; the report commits only
  derived presentation figures and their renderer.
- Framed the preliminary result as a pipeline demonstration, not a biological state
  effect: the observed descriptive medians have only 14 contained Active events and
  2 contained Quiet events, from one identity-unverified recording.
- Selected boundary attribution and the scientifically acceptable spectral target as
  the two email questions. They are the decisions that most directly determine the
  primary analysis rather than merely tuning an implementation detail.
- Added an agenda that records the defaults, evidence, alternatives, and meeting
  decisions for boundary policy, spectra, event definitions, QC, and pooling.
- Verification:
  - Rendered and visually inspected all three report PNGs from the real pilot tables
    and raw MAT trace.
  - Ran the renderer direct from a source checkout in `sleep_scoring_dash3.0`.
  - Created a local root commit on `main`; no Git remote exists, so no push or GitHub
    Pages URL has been created.

## 2026-09-14

### First real-file exploratory run and audit plot (Codex GPT-5; effort/tokens not reported)

- The first supplied MAT contains the required fine labels and aligned finite NE,
  but no embedded biological identity. It is deliberately represented as
  `unverified_35`, not as a mouse inferred from its filename, until the user supplies
  mouse/session/condition mapping.
- The illustrative 120 s / 0.025–0.1 Hz spectrum is infeasible for Quiet Wake in
  this file (zero windows). A slower common spectrum was not selected from one file;
  the configuration-free transient report is the current descriptive result.
- Boundary selection is material: 15/35 Active and 21/25 Quiet candidate peaks cross
  a wake-state boundary, leaving 14 and 2 contained-event observations. The stored
  initial -99.6 percentage-point sample remains unchanged and is a QC item.
- Added a standalone Plotly HTML reporter that consumes analysis/preflight CSV tables,
  preserves excluded candidates in the display, and avoids presenting descriptive
  subject points as inferential results.
- Verification:
  - Read MAT fields directly with SciPy; ran validation for 15/30/60/120/300 s and
    a configuration-free `analyze_ne.py` run in `sleep_scoring_dash3.0`.
  - Ran `scripts/plot_ne_results.py` against the resulting CSV outputs.

### Standalone NE analysis pilot (Codex GPT-6; effort/tokens not reported)

- User requested a new independent repository with per-MAT metric functions,
  mouse-level aggregation, separate usable-data reporting, and a treaty handoff.
  Created local `wake-ne-analysis` on `main`; no remote, commits, or PR requested.
  Sibling scoring and MATLAB project source files are unchanged by this task.
- Installed Agent Collab Treaty v0.9.0 via `treaty init` with recorded Copier
  answers and nested `treaty_docs`. Kept the generic conventions unchanged and
  filled project guidance, architecture, methods, handoff and next steps.
- Established metric-specific eligibility: fixed windows for spectra, natural
  events for amplitude/duration/slopes. Primary events are complete and contained;
  crossing candidates stay auditable, with explicit peak-state sensitivity mode.
- Spectral settings are unset unless supplied; an illustrative JSON config exists
  but is not a validated band/window recommendation. The user will supply real MATs.
- Percentage delta-F/F and factor-100 downsampling were verified in the MATLAB code
  and confirmed by the user. Measurements remain processed-signal quantities; no
  deconvolution or additional NE smoothing is applied. Filter metadata are assumptions.
- Pooled event medians use all eligible events, not file medians; pooled spectra
  weight equal-duration windows, not files. Missing estimates remain NaN and coverage
  and event counts expose unequal available data. No group inference is implemented.
- Verification:
  - Installed treaty with `treaty init ... --ref v0.9.0 --defaults` and explicit
    environment/verification settings.
  - `conda run -n sleep_scoring_dash3.0 python -m pytest -q --basetemp
    .pytest_tmp -p no:cacheprovider` in the new repository: 24 passed. Includes
    real MAT round trips, both CLI workflows, known-power sinusoids, known-slope
    transients, missing data, short-bout retention, and event/window pooling.
  - Both source script `--help` commands passed. `pip wheel . --no-deps
    --no-build-isolation --wheel-dir .pytest_tmp/wheels` built version 0.1.0.
  - `treaty validate .` passed. Formatting uses Black with an explicit 100-character
    line length and Python 3.11 target, matching the initial formatter run.
  - Local `main` has no commits or remote; source is untracked pending user review.
    Read-only Git checks in the sandbox need a repository-scoped `safe.directory`
    override because host-created files and the sandbox use different Windows SIDs.
