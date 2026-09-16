# Work Log

## 2026-09-16

### Separate score-bout geometry from peak-assigned NE timing (Codex GPT-5; effort/tokens not reported)

- Direct audit of the saved one-second labels confirmed that Quiet Wake is much less
  prevalent and shorter despite a nearly balanced count of maximal label runs. Across
  the eight audited cohort files it has 5,547 of 26,445 labelled Wake seconds (21.0%),
  a pooled 2 s run median versus 4 s for Active, and 1,554 runs versus 1,508 Active;
  fragmentation, not comparable time, explains the count. The nine-file raw screen
  similarly has 8,626 Quiet versus 26,532 Active labelled seconds.
- The peak-state contract deliberately allows 20%/80% support to cross score
  boundaries, so retained the raw-bout width and slope comparisons after clarifying
  the interpretation. Their complete supports cross a saved score boundary in
  1,624/1,766 Active (92%) and 1,696/1,759 Quiet (96%) cases; the report now calls
  them full NE events assigned by their peaks, never score-bout durations. The raw
  output writes a separate `score_label_geometry.csv` audit.
- Kept the cohort report's PI-directed peak assignment and relabelled its width and
  slopes as contextual, peak-associated full-episode measures rather than score-bout
  duration. Its audit has crossing support in 333/865 Active (38%) and 232/297 Quiet
  (78%) retained events, as allowed by the peak-state definition.
- Verification:
  - Regenerated the explicit score-label audit and peak-assigned raw-bout figure set.
  - Regenerated and visually inspected the relabelled raw-bout and cohort figure sets.
  - `python -m pytest --basetemp .pytest_tmp_duration_terminology -p no:cacheprovider -q`:
    30 passed.
  - `git diff --check` passed.

### Raw-report spectral hierarchy (Codex GPT-5; effort/tokens not reported)

- Added a separate spectral calculation to the raw-bout report rather than copying
  the mouse-level cohort spectrum. It uses all nine MAT files, each file's declared
  common labelled interval, no start exclusion, and 15-second state-pure 0.20--0.30
  Hz windows. One spectrum per state per file is compared by paired Wilcoxon; all
  individual windows are separately shown with a pseudoreplicated Mann--Whitney
  description.
- Recording-level band power is not nominally different (n = 9, p = 0.570). The
  deliberately independent window screen has 1,060 Active and 106 Quiet windows and
  a nominal p = 0.0155, which is not biological inference. Frequency maximum is
  unresolved: 17 of 18 recording/state values are at the 0.20 Hz lower band edge.
- Verification:
  - Regenerated and visually inspected both raw-report spectral figures.
  - `python -m pytest --basetemp .pytest_tmp_raw_spectral_v2 -p no:cacheprovider -q`:
    30 passed.

### Independent-bout raw-bout description (Codex GPT-5; effort/tokens not reported)

- Made the raw-bout report self-contained and parallel in structure to the cohort
  report, including label provenance, metric definitions, a deliberately blank
  spectral-result section, and a statistical appendix.
- Added all-bout medians, IQRs, a deterministic point/violin figure, and two-sided
  Mann--Whitney U calculations. The raw peak distribution has a nominal p =
  5.22e-05; duration and the 20--80% slopes do not. This is explicitly labelled a
  pseudoreplicated distributional description because bouts share recordings and
  animals. The paired recording-level Wilcoxon screen remains the more appropriate
  of the two provisional tests.
- Verification:
  - Regenerated the nine-file analysis and visually inspected the all-bout figure.
  - `python -m pytest --basetemp .pytest_tmp_bout_stats -p no:cacheprovider -q`:
    29 passed.

### Exploratory raw-bout recording sensitivity (Codex GPT-5; effort/tokens not reported)

- Added a separate, explicitly non-primary zero-referenced raw-bout workflow and
  GitHub-renderable report. It retains all nine MAT files as independently treated
  preliminary recordings, with within-file Active/Quiet pairing. `mouse5_day1.mat`
  now contributes through a declared common-start/minimum-duration interval; its
  6.25-second unlabelled NE tail is not state-compared, but no source data are changed.
- Each state bout contributes its literal processed-NE maximum. Positive peaks can
  additionally provide zero-referenced 20%/80% duration and slopes; crossing support
  is attributed to the state of the bout peak but may extend across state boundaries.
  A missing crossing affects only that metric, never file inclusion. The workflow does
  not apply the local baseline or the prior recording-start event exclusion.
- The nine recording-pair screen finds higher zero-referenced Active-Wake peak levels
  (paired Wilcoxon p = 0.0117) and a nominal duration difference (p = 0.0195); rise
  and decay slopes are not significant. The report calls these screening signals only
  because repeated recordings may share a mouse and literal levels can drift over time.
- Verification:
  - Regenerated the all-file raw-bout tables and visually inspected the paired figure.
  - `python -m pytest --basetemp .pytest_tmp_peak_attributed_raw -p no:cacheprovider -q`: 28 passed.
  - `git diff --check` and `treaty validate .` passed.

### Report terminology and reproducible-figure follow-up (Codex GPT-5; effort/tokens not reported)

- Defined a mouse pair in the cohort report as the two within-mouse state summaries,
  and clarified that IQR reports the middle half of mouse-level values while Figure 1
  retains every individual mouse. Explicitly stated that episode amplitude is peak
  height above a local rolling baseline, not absolute NE or RMS; the same baseline
  defines the 20%/80% slope crossings.
- Aligned report figures with the upstream `sleep_scoring` colors: Active Wake is
  orange (`#E69F00`) and Quiet Wake is light blue (`#56B4E9`). The peak-state plot
  now uses those opaque stage colors and a deterministically seeded, eligible
  Quiet-Wake peak example. It requires at least 10 displayed Quiet-Wake seconds, 4
  displayed Active-Wake seconds, and rejects a candidate if a higher NE value would
  make its marked point visually misleading. The renderer records seed `20260916`,
  its eligibility criteria, and has a synthetic determinism test.
- Moved the spectral feasibility rationale into the methodology, kept a concise
  spectral result subsection, and added appendix equations plus the forward/backward
  moving-average retained-power table. It distinguishes smoothing attenuation from
  the saved-rate Nyquist limit and explains why longer state-pure Quiet-Wake windows
  would be needed below 0.20 Hz.
- Disclosed the detector's ordering and limitations in the report: the centered
  60-second rolling 20th-percentile baseline is computed over each continuous finite
  NE stretch before peaks are found, never reset at Active/Quiet boundaries, and then
  used to assign the saved state at each peak. The 60-second/20th-percentile settings
  are now explicitly described as unvalidated pilot heuristics requiring trace review
  and a declared sensitivity analysis.
- Verification:
  - Rendered and visually inspected all three refreshed static cohort-report figures.
  - `python -m pytest --basetemp .pytest_tmp_baseline_disclosure -p no:cacheprovider -q`:
    26 passed.
  - `git diff --check` passed.

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
