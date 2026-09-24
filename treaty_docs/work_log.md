# Work Log

## 2026-09-23

### Refresh the report with startup-excluded results (Codex GPT-6; effort/token budget not exposed)

- The user requested the quality-checked results in the single NE dynamics report,
  a brief reason for startup exclusion, and concise explicit interpretation in
  Executive Summary and Results. This supersedes the prior numbers-only deferral.
- All tables and both figures now use the startup-5-second run. Explain that High's
  more positive overall mean combines direction frequency and conditional slopes;
  Low has steeper rises, but its more frequent and steeper declines offset more of
  that positive contribution. Both variance means are now higher in Low.
- Removed superseded numbers and the old opposite-variance conclusion. Updated
  nominal p-values, sample counts, reproduction commands, and current run pointers;
  retained the plain-language effect-size explanation and inference limits.
- Variance figure category positions are explicit to keep labels centered under
  their boxes. Original analysis results were reused without another extraction.
- Verification:
  - Local date checked: `2026-09-23`.
  - Reran both renderers against the new archives and visually inspected report PNGs.
  - All four table rows, p-values, pairwise percentages, state counts, weighted-mean
    equations, local links, and absence of obsolete results checked against saved
    tables. Rendered comparison table matches the startup-QC run exactly.
  - `treaty validate .` and `git diff --check` passed.

### Apply uniform startup exclusion and rerun numbers only (Codex GPT-6; effort/token budget not exposed)

- The user authorized a signal-quality-based recording-start rule and rerun, with
  numbers first and no report update. Reviewed all ten first-15-second traces without
  labels; three share a roughly -100 percent excursion followed by a rebound that
  settles by about 2 seconds. Chose a conservative 5-second exclusion in every file
  before calculating revised outcomes. This is exploratory QC informed by these
  starts, not a validated instrument settling time or an outcome-optimized cutoff.
- `startup_exclusion_seconds` marks the prefix unavailable in memory before filtering
  or history extraction. Histories require 10 seconds of retained data; existing
  30-second filter guards restart after the exclusion. Sources/timestamps/labels,
  final-tail handling, and pooled weighting remain unchanged. Default zero preserves
  legacy calls; this run explicitly passes `--startup-exclusion-seconds 5`.
- Added `--no-report`, and saved new versioned archives plus results under
  `ne_dynamics_v3_startup5_20260923`. Source inspection and the rule frozen before
  the rerun are in `results/ne_startup_quality_inspection_20260923/`; the rule is
  also copied to the run output. Report files and figures were not touched this turn.
- High/Low means: signed slope 0.008901/0.005191; absolute slope 0.068742/0.080412;
  ordinary variance 0.140726/0.172681; detrended variance 0.057446/0.060392.
  Detrended variance is now 5.13% higher in Low. Existing four-feature Holm
  comparisons remain nominal; no test of mean differences was added.
- Verification:
  - `Get-Date -Format yyyy-MM-dd`: `2026-09-23`.
  - Full pytest: 23 passed, 1 optional test skipped. New checks establish that
    startup contamination cannot enter filtering, histories are clean, clocks
    and source arrays stay intact, and numbers-only mode produces no report.
  - Real-data audit: all ten source hashes and labels match the prior run;
    51 startup samples excluded per file. Retained variance values match the
    original archives exactly; every window touching the prefix is unavailable.
  - Signed-slope summaries saved from verified new archives. `treaty validate .`
    and `git diff --check` passed.

### Audit the proposed detrended-variance grant claim (Codex GPT-6; effort/token budget not exposed)

- The PI questioned greater NE activity in Low and proposed using the detrended
  variance mean instead. Variability is distinct from signal level; the direction
  of this particular mean difference also proved sensitive to recording starts.
- The two largest detrended variances are High seconds at t=10 in `mouse1_day2`
  (198.0472) and `part1_mouse3_day2` (193.1961). Direct MAT reads confirmed the
  histories include startup excursions near -99 and -102 percentage delta-F/F.
- Omitting those two values only as a post hoc sensitivity audit changes High mean
  from 0.070385 to 0.057534; Low remains 0.060465. The 14.1% lower Low mean is
  therefore unsuitable as supporting evidence without resolving startup handling.
  The original feature set, tables, figures, and source data remain unchanged.
- Added a prominent report qualification and a pending uniform startup-QC decision.
  Saved the audit and archive hashes under `results/ne_dynamics_startup_audit_20260923/`.
- Verification:
  - Local date checked: `2026-09-23`.
  - Loaded verified feature archives, identified the extreme windows by source and
    score second, and reproduced their variances directly from the MAT NE samples.
  - Verified full and sensitivity means. No new significance tests or exclusions.
  - `treaty validate .` and `git diff --check` passed.

### Show distributions alongside means in the NE report (Codex GPT-6; effort/token budget not exposed)

- The user requested box plots with mean dots, retaining the rising/declining
  percentage bars, then commit and push. Means remain the narrative/table summary;
  distribution plots make overlap and the difference between means and medians visible.
- The shared plot helper uses quartile boxes, median lines, black mean dots, and
  5th–95th percentile whiskers. Captions identify the percentile convention and
  clarify that omitted tail points still enter all statistics. Slopes retain signs.
- The preceding plain-language effect-size explanation is included in this delivery.
  Fresh renders are in `results/ne_dynamics_boxplots_20260923/` and
  `results/ne_slope_direction_boxplots_20260923/`. Feature archives and original
  test results are unchanged; the unrelated PI draft image remains untracked.
- Verification:
  - Local date checked: `2026-09-23`.
  - Full pytest suite: 21 passed, 1 existing optional test skipped.
  - Both report PNGs rendered and visually inspected. Saved comparisons match
    the previous run; direction quantiles match archive values, and box/mean
    traces and report links were checked.
  - `treaty validate .` and `git diff --check` passed.

### Explain the effect sizes and p-values in plain language (Codex GPT-6; effort/token budget not exposed)

- The user requested a self-contained interpretation for PI readers. Translate
  the rank-biserial effects into pairwise percentages (53.0% High for signed slope;
  53.1%, 52.3%, and 51.2% Low for the other features), counting ties as half.
- Explain that the near-even comparisons indicate weak separation and that Holm
  correction covers four tests, not dependence between seconds. Retain the exact
  statistics and distinguish distribution tests from tests of mean differences.
- Verification:
  - Local date checked: `2026-09-23`.
  - All four percentages calculated from the saved effects; all four adjusted
    p-values verified below 0.001. No analysis or figure changes.
  - `treaty validate .`, local report link check, and `git diff --check` passed.

### Clarify slope signs and the purpose of local detrending (Codex GPT-6; effort/token budget not exposed)

- The user requested consistent slope terminology, a Questions section, and an
  explanation of local detrending after recording-level preprocessing. Report
  direction-specific slopes with their signs in both text and Figure 1.
- Ordinary variance addresses the original variability question. Local detrending
  is an optional secondary measure that removes each window's fitted linear change,
  potentially including NE changes of interest. Preserve both results and the
  original four-feature correction; a reversal alone does not demonstrate randomness.
- Verified equal valid masks for the two variance columns and nonnegative removed
  variance in every eligible Wake window. Mean removed variance is 0.0839279 in
  High and 0.1122390 in Low, explaining the reversal in the mean comparison.
- Verification:
  - Local date: `Get-Date -Format yyyy-MM-dd` returned `2026-09-23`.
  - Reran the direction summary into `results/ne_slope_direction_signed_20260923/`;
    its numerical summary matches the prior mean summary. Figure 1 was visually
    inspected with negative declining slopes and checked against the saved means.
  - Report wording, Questions placement, local links, and variance decomposition
    checked; `treaty validate .` and `git diff --check` passed.

### Use means and plain feature labels in the NE dynamics report (Codex GPT-6; effort/token budget not exposed)

- The user requested arithmetic means in place of medians and removal of distracting
  wording. The report and its figures now use means, call the feature slope, and
  explain filtering once in methods. The feature definitions and pooled-second
  weighting are unchanged.
- Recomputed summaries from the verified saved archives. The mean comparison
  changes the interpretation: Low has greater rising and declining magnitudes
  and ordinary variance, but lower detrended variance. The original distribution
  tests are retained and explicitly distinguished from tests of means.
- Shared archive loading checks provenance for both renderers. New mean summaries
  and figures are in `results/ne_dynamics_means_reviewed_20260923/` and
  `results/ne_slope_direction_means_20260923/`; prior outputs remain available.
- Verification:
  - `Get-Date -Format yyyy-MM-dd`: `2026-09-23`.
  - Full pytest suite: 21 passed, 1 existing optional test skipped.
  - Rendered and visually inspected both report figures. Original comparison
    columns match the saved results; independently checked pooled means,
    direction-weighted reconstruction, report values, wording, and local links.
  - `treaty validate .` and `git diff --check` passed.

### Consolidate the NE dynamics reports for delivery (Codex GPT-6; effort/token budget not exposed)

- The user requested one report and authorized commit/push on completion.
  `writeups/ne_dynamics_report.md` now contains the expanded preliminary-style
  narrative, all four pooled feature comparisons, slope direction breakdown,
  variance details, figures, caveats, and complete reproduction commands.
- Removed the duplicate `ne_slope_direction_report.md`; its content is merged
  into the canonical report and its earlier version remains in Git history.
  README, current handoff notes, and startup guidance now name only the one
  current dynamics report. Historical work-log entries retain their original paths.
- No analysis definitions, feature archives, or numerical results changed.
- Verification:
  - `Get-Date -Format yyyy-MM-dd`: `2026-09-23`.
  - Existing pooled comparison table and slope-direction summaries were used to
    retain all results; all four median/IQR rows match the saved comparison table.
  - Current references and local Markdown links verified; `treaty validate .`
    and `git diff --check` passed. No analysis code or calculations changed.

### Prepare the requested NE dynamics delivery (Codex GPT-6; effort/token budget not exposed)

- The user authorized committing and pushing the completed pooled NE dynamics
  workflow, slope/variance reports, figures, and corrected common-interval
  guidance on the current `dev` branch. The prior eight-file report remains
  clearly superseded historical material. Raw data and generated feature/run
  outputs remain ignored; the unrelated existing PI draft PNG is excluded.
- Verification:
  - `Get-Date -Format yyyy-MM-dd`: `2026-09-23`.
  - `python -m pytest --basetemp outputs/ne_dynamics_delivery_test_tmp -p no:cacheprovider -q`:
    21 passed, 1 skipped (existing optional scikit-learn test).
  - `treaty validate .`: passed. Figures and report values were verified in
    the preceding report entries; final delivery ref is recorded in Git history.

### Add variance to the focused NE report (Codex GPT-6; effort/token budget not exposed)

- Extended the same slope-direction report, as requested, with ordinary and
  detrended 10-second trailing variance in the executive summary, results table,
  methods, figure, proposal interpretation, and reproducibility instructions.
  Retained all ten files, unrestricted state history, and the pooled-second unit.
- Reused the saved v2 comparison table rather than recomputing tests. Low pooled
  medians are 7.4% and 3.8% higher, respectively; adjusted nominal p-values remain
  1.36e-9 and 0.000825 from the original four-feature Holm family. The focused
  figure displays median/IQR and 5th–95th percentiles; tails remain in the tests.
- Verification:
  - `Get-Date -Format yyyy-MM-dd`: `2026-09-23`.
  - `python scripts/render_ne_dynamics.py --results-dir results/ne_dynamics_v2_pooled_20260923 --output-dir results/ne_variance_report_20260923 --png`:
    focused variance HTML/PNG rendered; report PNG visually inspected.
  - No source data, feature archives, or original test results were modified.

### Draft the focused NE slope-direction report (Codex GPT-6; effort/token budget not exposed)

- The user requested a straightforward report specifically on rising and
  declining trends, mirroring the preliminary recording report where useful.
  Retained its executive summary, result table, methods, results, proposal
  interpretation, statistical appendix, and reproducibility outline, while
  preserving the explicitly requested pooled-second comparison.
- Distinguished time spent on a declining segment (55.2% Low versus 51.3% High)
  from conditional decline magnitude (median 0.0527 versus 0.0443 percentage
  points/s). Similar rising medians and positive means in both states prevent
  interpreting the result as continuous decline or transition-triggered change.
- The follow-up is descriptive. The original four-feature signed-slope p-value
  is contextual, not claimed as a separate test of sign fractions or the 19%
  conditional median difference. Original feature definitions/results are intact.
- Verification:
  - `Get-Date -Format yyyy-MM-dd`: `2026-09-23`.
  - `python scripts/summarize_ne_slope_direction.py --analysis-dir results/ne_dynamics_v2_pooled_20260923 --output-dir results/ne_slope_direction_20260923_final --png`:
    ten archive configurations/source identities verified; valid counts and
    signed medians match the existing pooled analysis; table, provenance and
    HTML/PNG generated. Final two-panel figure visually inspected.
  - Synthetic sign/count/magnitude checks passed for positive, negative and
    exact-zero values. No new biological inference tests were run.

### Restore common-interval inclusion and use pooled seconds (Codex GPT-6; effort/token budget not exposed)

- The user corrected the preceding run: both longer-NE files had already been
  approved, and the intended comparison pools every eligible second across
  recordings. The previous recording report documents the common-start policy;
  an older next-steps exclusion survived and was incorrectly applied. Corrected
  `AGENTS.md` and next steps so this decision is explicit at startup.
- All ten files now contribute. Excess NE is trimmed in memory before filtering:
  63 samples from `mouse5_day1` and 251 from `408_yfp`. Source MAT files remain
  unchanged. Histories still cross any state; source traces are never concatenated
  to create histories. New v2 NPZ archives preserve the changed interval contract.
- The main comparison gives every eligible second equal weight, without further
  normalization or recording balancing. It uses two-sided pooled Mann-Whitney U,
  four-feature Holm adjustment, and rank-biserial effects. No recording-comparison
  test or plot is generated. Per-file coverage is provenance only.
- All four nominal adjusted p-values are below 0.05 (signed slope 1.94e-15,
  absolute slope 6.47e-16, ordinary variance 1.36e-9, detrended variance 0.000825).
  Rank-biserial magnitudes are small (0.025–0.061). The report states that saved
  normalization does not guarantee cross-file comparability, and dependent seconds
  make these pseudoreplicated exploratory p-values rather than animal inference.
- Superseded eight-file report retained under `archive/ne_dynamics_v1_recording/`;
  prior ignored v1 archives/results remain intact. Current results are under
  `ne_dynamics_v2_pooled_20260923`; all task changes remain uncommitted.
- Verification:
  - `Get-Date -Format yyyy-MM-dd`: `2026-09-23`.
  - `python -m pytest --basetemp outputs/ne_dynamics_v2_full_test_tmp -p no:cacheprovider -q`:
    21 passed, 1 skipped (existing optional scikit-learn test).
  - `python scripts/analyze_ne_dynamics.py --input-dir data --feature-dir data/derived_features/ne_dynamics_v2_pooled_20260923 --results-dir results/ne_dynamics_v2_pooled_20260923`:
    ten included files, 30,212/7,555 valid High/Low slope seconds and
    30,436/7,606 variance seconds; four pooled comparisons.
  - `python scripts/render_ne_dynamics.py --results-dir results/ne_dynamics_v2_pooled_20260923 --output-dir results/ne_dynamics_v2_pooled_20260923/figures_reviewed --png`:
    HTML/PNG rendered and the revised main plot visually inspected.

### Establish the simple slow-NE dynamics screen (Codex GPT-6; effort/token budget not exposed)

- The user approved four NE features and explicitly requested unrestricted
  trailing state history: signed/absolute slow slope and ordinary/detrended
  10-second variance. History crosses all score labels; only technical signal
  completeness and filter-edge guards affect feature availability. Cutoff,
  history, summaries, and four-feature correction were fixed before results.
- The first run retains eight recordings. A one-score-second duration tolerance
  excludes `mouse5_day1` (+6.246 s) and `408_yfp` (+24.683 s), without source
  rewriting; this differs from the earlier ten-file common-interval report.
  Unknown mouse/condition identities are not guessed. The optional metadata
  path supports pooling seconds within mouse and condition before medians.
- No feature establishes a corrected difference. Absolute slope and both
  variance measures are higher in Low Alertness in 7/8 files; detrended variance
  has raw p=0.0546875 and Holm p=0.21875. The report preserves that descriptive
  pattern alongside the null significance result and repeated-session limits.
- Numerical extraction and Plotly/Kaleido HTML/PNG rendering completed on this
  host. No user terminal handoff was needed. This is distinct from the previous
  Matplotlib and UMAP limitations. Source/config/code hashes and versioned NPZ
  archives preserve the completed run under `ne_dynamics_v1_20260923`.
- Existing `.pytest_tmp` permissions rejected the first integration fixture;
  fresh ignored directories under `outputs/` worked. The unrelated existing PI
  trace PNG was preserved. All task changes remain uncommitted on `dev`.
- Verification:
  - `Get-Date -Format yyyy-MM-dd`: `2026-09-23`.
  - `python -m pytest --basetemp outputs/ne_dynamics_final_test_tmp -p no:cacheprovider -q`:
    18 passed, 1 skipped (existing optional scikit-learn test).
  - `python scripts/analyze_ne_dynamics.py --input-dir data --feature-dir data/derived_features/ne_dynamics_v1_20260923 --results-dir results/ne_dynamics_v1_20260923`:
    eight archives, ten source-audit rows, four paired comparisons.
  - `python scripts/render_ne_dynamics.py --results-dir results/ne_dynamics_v1_20260923 --png`:
    HTML and PNG generated; final paired PNG visually inspected.
  - Source-module hashes match run provenance; the final comparison table is
    numerically identical to the initial `ne_dynamics_v1` run.

### Match the source-label NE check to the NE-excluded cluster screen (Codex GPT-5; effort/tokens not reported)

- The direct High/Low Alertness screen now uses the same fixed label-balanced
  2,000-second sample and within-recording robust-scaled withheld NE values as
  the NE-excluded cluster checks, rather than conflating that question with the
  recording-level raw-fluorescence summary. Neither mean processed NE nor NE
  slope differs in this matching descriptive screen (Holm-adjusted p = 1.000 for
  each feature); correlated seconds remain the stated inference limitation.
- The PI discussion draft was narrowed to the requested representative trace so
  it does not duplicate report maps or juxtapose incompatible statistical units.
  Its existing four-panel PNG is deliberately not committed because it must be
  regenerated from the trace-only script in the user's interactive environment.
- Verification:
  - `Get-Date -Format yyyy-MM-dd` returned `2026-09-23`.
  - `git diff --check` passed before the treaty-note update.

## 2026-09-22

### Compare withheld NE features across NE-excluded Wake partitions (Codex GPT-5; effort/tokens not reported)

- Replaced the prior recording-median screen with the requested pooled-seconds
  characterization of withheld robust-scaled `ne_mean` and
  `ne_slope_ols_per_second` across every 3-, 4-, and 5-cluster partition. The NE
  features remain excluded from graph construction, so this is a post-clustering
  feature characterization rather than a circular full-panel comparison.
- Two-sided Mann–Whitney comparisons use all sampled seconds and correct the
  two-feature, within-resolution pairwise families with Holm. `ne_mean` differs
  after correction in all 3-group pairs, five of six 4-group pairs, and nine of
  ten 5-group pairs; no slope pair differs. The report explicitly labels these
  p-values as pseudoreplicated descriptive screens, not independent-animal
  inference.
- Verification:
  - Confirmed the current checkout was clean on `dev` before the edit.
  - Recomputed pooled cluster summaries and Mann–Whitney/Holm comparisons from
    the retained NE-excluded cluster CSVs using `ne_umap`.
  - `git diff --check` and `treaty validate .` passed.

### Synchronize completed NE-excluded report work from dev to main (Codex GPT-5; effort/tokens not reported)

- Fast-forwarded the three completed NE-report commits from `dev` into `main` at
  `77daa837bebb19c971ee6aaa31cb6e7009ebf847`; no release or tag was created.
- Verification:
  - Fetched origin and confirmed `origin/main` was an ancestor of `origin/dev`
    with `0 3` left/right divergence before the fast-forward.
  - Pushed `main`, then returned the checkout to `dev`.

### Synchronize pooled-seconds NE screen from dev to main (Codex GPT-5; effort/tokens not reported)

- Fast-forwarded the requested pooled-seconds NE-screen revision from `dev` into
  `main` at `ad38067b606d3774eca9390ebff2059480bb8463`; no release or tag was
  created.
- Verification:
  - Fetched origin and confirmed `origin/main` was an ancestor of `origin/dev`
    with `0 1` left/right divergence before the fast-forward.
  - Pushed `main`, then returned the checkout to `dev`.

### Synchronize NE-figure captions from dev to main (Codex GPT-5; effort/tokens not reported)

- Fast-forwarded the requested Figure 1–4 caption update from `dev` into `main`
  at `736df6c4308cb6652e680f1dd1d1ab7a5a4b8961`; no release or tag was created.
- Verification:
  - Fetched origin and confirmed `origin/main` was an ancestor of `origin/dev`
    with `0 1` left/right divergence before the fast-forward.
  - Pushed `main`, then returned the checkout to `dev`.

## 2026-09-21

### Standardize High/Low Alertness terminology and spectral-clustering language (Codex GPT-5; effort/tokens not reported)

- Made High Alertness / Low Alertness the sole current internal and reader-facing
  names for final score values 4 / 5. The numeric labels and their provenance are
  unchanged; current code, generated-table schemas, tests, reports, and recording
  figure renderer now use the standardized names.
- Updated the shared palette to High Alertness RGB `(227, 26, 28)` / `#E31A1C`,
  Low Alertness `(0, 114, 178)` / `#0072B2`, NREM `(119, 115, 154)` / `#77739A`,
  and REM `(155, 191, 154)` / `#9BBF9A`. Rerendered committed cluster figures
  from existing saved coordinates only; no t-SNE, UMAP, or graph fit was rerun.
- Replaced ambiguous “kNN-graph clustering” language with spectral clustering of
  a symmetric k-nearest-neighbor graph. Its final `assign_labels="kmeans"`
  implementation step is only spectral-embedding discretization, not k-means
  clustering of the observations.
- Verification:
  - Inspected the rerendered all-stage and Wake-only UMAP panels.
  - Focused tests passed: `7 passed, 1 skipped` in `sleep_scoring_dash3.0`.
  - Both plotting CLIs accepted the updated `--render-only` interface in `ne_umap`.

### Present PI-facing alertness palette and NE-excluded Wake sensitivity (Codex GPT-5; effort/tokens not reported)

- Standardized source-label language as High/Low Alertness; final score values
  4/5, sampling, and source audits remain
  unchanged. The Wake report now supplies the shared RGB palette and uses UMAP 2
  horizontally with UMAP 1 vertically.
- The user-generated matched 27-feature EEG+EMG UMAP run excludes only `ne_mean`
  and `ne_slope_ols_per_second`. Its 3/4/5 graph partitions agree closely with
  the full 29-feature result for the same points (adjusted Rand 0.978/0.964/0.959).
  The new NE-excluded report presents this as an EMG-inclusive feature-panel
  sensitivity, not an NE-null biological conclusion.
- Documented the agent UMAP/Numba execution boundary in `AGENTS.md`: prepare and
  validate scripts here, but have the user run fresh embeddings in their normal
  interactive `ne_umap` terminal.
- Verification:
  - Inspected the NE-excluded `run.json`, source/cluster summaries, and all four
    committed UMAP panels.
  - Recomputed adjusted Rand agreement from matched point identities in the two
    ignored cluster-result directories.

### Add source-preserving NREM-baseline target-cluster calibration (Codex GPT-5; effort/tokens not reported)

- Added `wake_ne_analysis/nrem_baseline.py` and
  `scripts/calibrate_nrem_baseline.py`. They reproduce the prior 20 Hz,
  NREM-anchored EMG-envelope comparison inside this repository without importing or
  changing the scoring app, source MAT files, or saved `sleep_scores`.
- The experiment uses existing 3-cluster kNN-graph assignments as targets only:
  clusters 2 and 3 are the two Active-only extremes. It predeclares a shared
  NREM robust-SD multiplier sweep and selects by mean F1 across recordings with
  target seconds; t-SNE/UMAP coordinates are never used for threshold selection.
- On the existing balanced 2,000-second, ten-recording sample, the expanded
  0--32 multiplier sweep selected 10. It selected 218/237 target seconds (92.0%
  recall) and 183 non-target seconds (54.4% precision). Thus the rule is more
  selective than the 80/20 split but does not reproduce only the two graph-target
  groups. The result is exploratory and needs recording-held-out and raw-trace
  evaluation before any upstream scoring change.
- Verification:
  - `Get-Date -Format yyyy-MM-dd` returned `2026-09-21`.
  - Focused tests passed: `2 passed` in `sleep_scoring_dash3.0` using an external
    temporary directory.
  - The full local calibration wrote ignored audits under
    `results/nrem_baseline_calibration_20260921_extended/`.

### Audit full Wake-time composition of the selected experimental rule (Codex GPT-5; effort/tokens not reported)

- Extended the calibration audit to count every source Wake second at each tested
  multiplier, rather than interpreting the balanced 2,000-point graph-display
  sample as a duration estimate.
- At the selected 10-robust-SD multiplier, 10,539/38,120 Wake seconds (27.6%) are
  experimentally Active and 27,581 (72.4%) are Quiet, compared with the current
  80/20 source-label composition. The NREM-relative rule is not composition-fixed:
  its Active share ranges from 2.3% to 65.0% across the ten recordings.
- Verification:
  - The focused duration-audit test passed in `sleep_scoring_dash3.0`.
  - The regenerated ignored audit is under
    `results/nrem_baseline_calibration_20260921_duration_audit/`.

### Write NREM-baseline cluster-target follow-up report (Codex GPT-5; effort/tokens not reported)

- Added `writeups/nrem_baseline_cluster_target_report.md` as a concise
  continuation of the Wake-only clustering report. It foregrounds the paired
  source-label and label-blind three-cluster maps, the threshold precision/recall
  trade-off, and the full-recording 27.6% Active / 72.4% Quiet composition at the
  selected rule.
- The report keeps the algorithm high level in the main text and moves the
  NREM-reference equation, sustained-activity rules, and selection criterion to
  an appendix. It explains why a perfect match is not expected and proposes a
  label-independent, recording-held-out next design.
- Verification:
  - Confirmed all four embedded figures and the linked preceding report exist.
  - Full suite passed: `6 passed, 1 skipped` in `sleep_scoring_dash3.0`.
