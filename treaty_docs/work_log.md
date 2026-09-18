# Work Log

## 2026-09-18

### Report completed PI-directed Wake kNN-graph follow-up (Codex GPT-5; effort/tokens not reported)

- Wrote `writeups/cluster_visualization_wake_only_report.md` as the concise
  results-focused continuation of the 29-feature cluster visualization report.
  It retains all source-label and 3/4/5-partition figures, while referring readers
  to the parent report for shared feature extraction and baseline methods.
- The balanced 2,000-second, ten-recording sample has a recurring
  Quiet-associated and a recurring Active-associated broad group at four and five
  groups. Smaller Active-only groups have incomplete recording recurrence; none is
  presented as a validated Wake subtype. Because EMG both informed the upstream
  Active/Quiet labels and is included in the feature space, the report calls this
  EMG-associated organization rather than independent label validation.
- Verification:
  - Inspected the saved graph audit, source-label composition, and all 3/4/5
    t-SNE/UMAP figures under `results/wake_knn_clusters_20260918/` and
    `writeups/assets/wake_knn_clusters_20260918/`.
  - Confirmed that the eight figures referenced by the new writeup are present.

### Prepare PI-directed Wake kNN-graph clustering (Codex GPT-5; effort/tokens not reported)

- Interpretation: "k-nearest-neighbour clustering" is implemented as spectral
  clustering of an unweighted symmetric kNN graph in the full 29-dimensional,
  within-recording robust-scaled EEG+EMG+NE space. It is not a supervised KNN
  classifier, and t-SNE/UMAP are display-only.
- The planned script will select only Active/Quiet Wake before sampling, balance the
  capped sample within recording and source label, and produce matched 3-, 4-, and
  5-cluster partitions. It will retain point, source-label composition,
  feature-median, graph, and recording-composition audits.
- Verification:
  - Direct kNN-graph/spectral-clustering smoke check passed in `ne_umap` with
    scikit-learn 1.9.1; the environment does not include pytest.
  - `plot_wake_knn_clusters.py --help` and `compileall` completed in `ne_umap`.
  - The maintained `sleep_scoring_dash3.0` suite passed: 5 passed, 1 skipped
    because scikit-learn is intentionally an optional UMAP dependency there.

### Document EEG feature epochs and band integration (Codex GPT-5; effort/tokens not reported)

- Corrected the proposed five-second centred-window interpretation: current EEG
  features use left-aligned one-second epochs, followed by a Hann-tapered,
  constant-detrended density periodogram and strict-lower/inclusive-upper band
  integration.
- Added a linked EEG appendix to the current cluster writeup that states the sample
  boundary rule, log-power transform, band-edge rule, and one-second frequency
  resolution limitation. No extraction or embedding result was changed.
- Verification:
  - Inspected `wake_ne_analysis/cluster_features.py` against the added appendix.
  - `Get-Date -Format yyyy-MM-dd` returned `2026-09-18`.

## 2026-09-17

### Curate PI-facing repository surface (Codex GPT-5; effort/tokens not reported)

- Replaced the misleading `features/` surface with ignored local caches under
  `data/derived_features/`; the current cluster writeup now contains the feature
  definition and EMG-burst appendix needed for interpretation.
- Consolidated the two current reports and their referenced static figures under
  `writeups/`. Unpresented PCA panels were removed; all prior reports and figures
  are retained under `archive/`.
- Kept only the recording-report and cluster-feature commands/modules in the active
  source tree. The original generic manifest pipeline, compact embedding code,
  examples, and their historical tests are preserved together in
  `archive/legacy_pipeline/`.
- Verification:
  - `python -m pytest --basetemp .pytest_tmp\\pi_cleanup_elevated -p
    no:cacheprovider -q` in `sleep_scoring_dash3.0` passed: 5 tests.
  - All four retained script help commands completed; `compileall` completed for
    `wake_ne_analysis/` and `scripts/`; `treaty validate .` passed.
  - `git diff --check` passed and current source contains no stale `docs/`,
    `features/`, or superseded-command references.

### Clarify report sampling and EMG burst features (Codex GPT-5; effort/tokens not reported)

- Removed copy-ready figure captions from the completed cluster report; the renamed
  Sampling section now records only the design needed to interpret the displayed
  points.
- Added an appendix linked from the feature table that defines the exploratory EMG
  burst features: core-wise detrend/zero-phase filtering, 75-ms RMS envelope,
  recording-median plus three robust-SD threshold, 50-ms gap joining/minimum run,
  and the exact per-second onset/duty/peak/RMS summaries. It explicitly separates
  those summaries from the native mean-centred RMS and from sleep labeling.
- Verification:
  - Reviewed the implementation in `wake_ne_analysis/expanded_features.py` against
    the new report appendix and existing feature/method documentation.
  - `Get-Date -Format yyyy-MM-dd` returned `2026-09-17`.

### Archive four-feature report and publish expanded embedding result (Codex GPT-5; effort/tokens not reported)

- Archived the completed compact EEG+EMG+NE report as
  `docs/archived/cluster_visualization_report_20260917_four_feature.md` and
  replaced the live report with the completed 29-feature comparison.
- The expanded report uses grouped feature families rather than listing the 20
  adjacent wide EEG bands individually. All-stage runs contain 4,000 balanced
  non-MA seconds; Wake-only runs contain 1,000 combined-Wake seconds (797 source
  Active, 203 source Quiet), with source subtype retained only for audit.
- Both t-SNE and UMAP show visible broad-state organization. Combined-Wake geometry
  is branched only when EMG features are included; no-EMG Wake maps are diffuse.
  This is a descriptive EMG-associated pattern, not a predeclared or stable discrete
  Wake clustering result.
- Kept PCA panels out of the report. All-feature PC1 accounts for 86.9% (all
  stages) and 92.1% (Wake only), while no-EMG PC1/PC2 captures only 20.2%/13.2%
  and 22.2%/10.4%; neither view adds a useful presentation-level cluster claim.
- Verification:
  - Confirmed all four `run.json` files, point tables, state counts, and PCA audit
    tables under `results/expanded_embedding/`.
  - Visually inspected all eight t-SNE/UMAP PNGs under
    `docs/assets/expanded_embedding/`.
  - `Get-Date -Format yyyy-MM-dd` returned `2026-09-17`.

### Prepare MA-excluded expanded-feature cluster visualizations (Codex GPT-5; effort/tokens not reported)

- Decision: remove MA before balanced sampling and before PCA, t-SNE, or UMAP
  fitting, rather than merely hiding its plotted points. MA is a manual override,
  not a physiological comparison state.
- Added four predeclared `features_29` configurations: all 29 features or all
  non-EMG features, each with all non-MA states or a single combined Wake class.
  Wake-only runs collapse Active/Quiet labels before sampling and fitting while
  retaining `source_state` in the point audit table. The non-EMG set is defined by
  the documented `emg_` feature-name prefix (24 retained EEG/NE columns).
- No embedding result is claimed yet. The wide EEG panel, EMG burst features, and
  NE slope remain exploratory; use the runs for QC/description before biological
  interpretation.
- Verification:
  - Inspected all ten `features/features_29` archives: 106,434 finite rows, 29
    all-feature columns, 24 non-EMG columns; expected balanced caps are 4,000
    rows for all non-MA stages and 1,000 for combined Wake.
  - `conda run --no-capture-output -n ne_umap python scripts\\plot_expanded_feature_embeddings.py --help`
  - `conda run --no-capture-output -n ne_umap python scripts\\plot_feature_embeddings.py --help`
  - `conda run --no-capture-output -n sleep_scoring_dash3.0 python -m pytest --basetemp .pytest_tmp\\cluster_script_regression_elevated -p no:cacheprovider -q` (32 passed)
  - `treaty validate .` (passed)
  - `git diff --check`

### Create expanded 29-feature per-recording archives (Codex GPT-5; effort/tokens not reported)

- Created ten ignored `features/features_29/*.npz` archives, retaining 106,434
  finite labelled seconds. Each archive stores raw and within-recording scaled
  matrices, labels/seconds, feature names, scaling provenance, and JSON metadata.
- The panel has twenty 0.5--100 Hz wide EEG bands, exact `>1--4` and `>4--8` Hz
  scoring anchors, five EMG measures, and mean plus within-second OLS slope for
  saved processed NE. The EMG burst definition is provisional: 75-ms RMS envelope,
  recording median plus three MAD-derived robust SD, 50-ms gap joining, and 50-ms
  minimum duration.
- Full-recording EMG filtering was impractical for the multi-hour recordings. The
  delivery uses deterministic 120-s filter cores with one-second discarded context,
  preserving the scoring method's detrend/20--200 Hz zero-phase filter family but
  not claiming bit-identical whole-recording output. `features/README.md` and
  `docs/methods.md` document this boundary.
- Verification:
  - Synthetic expanded-archive test: 1 passed.
  - All ten generated archives have a finite `(n_seconds, 29)` raw matrix.

### Remove PCA from presentation-facing cluster report (Codex GPT-5; effort/tokens not reported)

- Removed PCA methods, captions, and results discussion from
  `docs/cluster_visualization_report.md`. The report now presents only the t-SNE and
  UMAP comparisons; PCA remains outside that report as an optional local QC tool.
- Verification:
  - Confirmed the presentation report has no remaining PCA/principal-component
    mentions.

### Complete joint and EEG+NE embedding comparison (Codex GPT-5; effort/tokens not reported)

- Ran separate PCA, t-SNE, and UMAP figures on the fixed 4,800-point balanced sample
  for both four-feature joint EEG+EMG+NE and fairer EEG+NE-only inputs. REM remains
  visibly organized in both nonlinear feature sets. The joint Active-Wake arc does
  not persist without EMG: Active and Quiet Wake broadly overlap in the EEG+NE maps.
- PCA is a feature-QC display only: a Quiet-Wake Mouse 7 second with extreme
  robust-scaled EEG values and several MA Mouse 1 seconds with extreme EMG values
  dominate its axes. These finite data remain preserved; no clipping/removal rule
  was applied.
- Updated `docs/cluster_visualization_report.md` with figures, actual descriptive
  results, settings, sample counts, and the non-independence caveat.
- Verification:
  - Both run JSON files record the same seed, sampling cap, t-SNE, and UMAP
    settings; each uses all ten archives and 4,800 sampled rows.
  - Figure files and audit CSVs exist in their documented `docs/assets/` and ignored
    `results/` destinations.

### Polish embedding figures and define the EEG+NE follow-up (Codex GPT-5; effort/tokens not reported)

- Changed the archive-based comparison renderer to write three separate figures
  (`pca.png`, `tsne.png`, and `umap.png`) rather than a crowded shared panel. Each
  plot has its own in-panel legend and title, while the balanced-count caption is
  recorded in `docs/cluster_visualization_report.md`.
- Added an explicit `--feature-set eeg_ne` mode. It reuses the saved robust-scaled
  archives but omits EMG RMS, retaining delta EEG, theta EEG, and mean NE as the
  fairer follow-up to the EMG-related Active/Quiet label rule.
- Added the cluster-visualization report and updated run documentation with both
  the 4,800-point joint baseline and archive-only EEG+NE commands.
- Verification:
  - The revised CLI and feature module compile under `ne_umap`; its help exposes
    separate figure destinations and both feature-set choices.
  - All ten archives load directly (106,434 rows) and select 4,800 current rows at
    the default cap. No new MAT extraction or output-directory artifacts were made.

### Prepare archive-based PCA, t-SNE, and UMAP comparison (Codex GPT-5; effort/tokens not reported)

- Added `scripts/plot_feature_embeddings.py`, which consumes the previously saved
  `features/features_4/*.npz` robust-scaled matrices directly. PCA, t-SNE, and UMAP
  receive the same fixed-seed, per-recording/per-state-balanced sample; final labels
  colour panels only after fitting.
- Set the baseline display cap to 100 seconds per available state per recording,
  yielding 4,800 current points. The figure and audit destinations are explicitly
  separate (`docs/assets/embedding_comparison/` and ignored
  `results/embedding_comparison/`), with no new `outputs/` destination.
- Centralized the exact scoring-app stage colours: NREM `#FB7C7C`, REM `#7BFB7B`, MA
  `#FFFF00`, Active Wake `#E69F00`, and Quiet Wake `#56B4E9`.
- Verification:
  - Direct archive-load check completed across ten archives: 106,434 rows and 4,800
    sampled rows at the default cap.
  - The new CLI and source files compile under `ne_umap`; `ne_umap` lacks `pytest`,
    so no test package was installed or environment modified.

### Complete first joint UMAP and separate results from figures (Codex GPT-5; effort/tokens not reported)

- Completed the fixed-seed joint UMAP in the working `ne_umap` environment. The
  balanced display contains 480 points: 100 each for NREM, REM, Active Wake, and
  Quiet Wake, plus 80 MA points from its eight available recordings.
- The first map shows a clear Active-Wake region and a prominent REM neighborhood;
  Quiet Wake remains diffuse and overlaps NREM/MA. This remains descriptive because
  the plotted EMG feature relates to the Active/Quiet label rule and seconds within
  recordings are correlated.
- Moved run CSV/JSON audit artifacts to ignored `results/umap/initial_500_points/`
  and the presentation PNG to `docs/assets/umap/initial_500_points/`. Updated the
  CLI to accept separate `--results-dir` and `--figure` destinations, and removed
  abandoned UMAP attempts from `outputs/`.
- Verification:
  - The completed run contains 480 sampled points and its `run.json` now records
    the relocated figure path.
  - The CLI source compiles in the working `ne_umap` environment.

### Export named four-feature NumPy archives and make initial PCA views (Codex GPT-5; effort/tokens not reported)

- Wrote one compressed NumPy archive per MAT file under `features/features_4/`,
  named with the source MAT stem. Each `.npz` has raw `X` and within-recording
  median/IQR-scaled `X_robust_scaled` four-column matrices, final labels, seconds,
  source/rate provenance, and exact scaling values. `features/README.md` documents
  the archive contract and loading. The mistakenly created feature CSV directory
  under `outputs/` was removed.
- Generated pairwise and ordinary PCA views under `outputs/pca_views_20260917/`.
  The unaltered all-second PCA is a diagnostic, not a cluster conclusion: PC1
  explains 80.3% and is almost entirely EMG, because 1,848 rows have at least one
  robust-scaled feature magnitude above 10 (1,846 EMG rows and two rows each for
  delta/theta EEG). No rows were removed, clipped, or imputed. A real feature-QC
  rule is required before using PCA as a state-cluster visualization.
- Verification:
  - Feature exporter completed for all ten MAT files and wrote 106,434 rows.
  - `python -m pytest --basetemp .pytest_pca_views -p no:cacheprovider -q
    tests/test_pipeline.py -k umap_feature_extraction`: 1 passed.

### Extract joint EEG + EMG + NE UMAP features; document UMAP runtime boundary (Codex GPT-5; effort/tokens not reported)

- Added the initial four-feature, per-second joint panel: log EEG delta power,
  log EEG theta power, mean-centered broadband EMG RMS, and mean saved processed
  NE. The full ten-file extractor retained 106,434 finite four-feature seconds
  from 106,452 complete multimodal score seconds; 18 seconds with invalid NE were
  excluded without imputation or bridging.
- Verified the fresh `ne_analysis` environment's SciPy forward/backward filter on a
  synthetic trace. On multi-hour EMG vectors, the separate full-trace detrend and
  forward/backward filter calls did not complete, so this deliberately simple
  first-pass feature uses mean-centered native EMG RMS instead. The implementation
  completed one real 14,527-second recording and then all ten files.
- No UMAP figure or biological cluster statement was produced. `umap-learn 0.5.12`
  invoked a Numba compilation that did not reach fitting after more than twelve
  minutes; the process was stopped. `docs/umap_analysis.md` and `next_steps.md`
  state this boundary explicitly.
- Verification:
  - Fresh-environment synthetic `scipy.signal.sosfiltfilt` test printed `PASS`
    with SciPy 1.17.1.
  - One-recording extraction printed `PASS 14527 14527` with four feature columns.
  - Ten-file extraction wrote local audit CSVs and printed 106,434 retained seconds.

### Replace wake-bout audit jargon in the report (Codex GPT-5; effort/tokens not reported)

- Replaced the report's opaque “score-label geometry” table with a direct wake-bout
  duration-and-count summary. It now defines total duration in state, total number
  of wake bouts, all-bout typical duration, and recording-level typical duration in
  plain language. Removed the redundant short-bout row.
- Verification:
  - Regenerated report figures with matching plain-language labels.

### Remove zero-referenced shape width from public reporting (Codex GPT-5; effort/tokens not reported)

- Removed the confusing zero-referenced, peak-anchored shape-width row and panels
  from the current report. The underlying crossing times and width remain in the raw
  audit tables, where they document the retained 20--80% slope calculations.
- The report now presents only mean NE within score bouts, literal score-bout
  duration/count, contextual slopes, and spectral measures.
- Verification:
  - Regenerated the ten-file report output and static figures.
  - `python -m pytest --basetemp .pytest_refresh -p no:cacheprovider -q`: 31 passed.

### Publish refreshed ten-recording report after input-count confirmation (Codex GPT-5; effort/tokens not reported)

- The user confirmed that the intended refreshed input set is 10 MAT files, not 11.
  Published `docs/preliminary_recording_report.md` and its static figures from a new
  ten-file run. The current report retains the need for verified mouse/session
  metadata before biological inference.
- The recording-level mean-NE screen is null (paired Wilcoxon p = 0.557). Actual
  score-bout duration remains shorter in Quiet Wake (4 s versus 2 s file-median
  summaries; p = 0.00391), while score-bout count has no nominal paired difference
  (p = 0.164). Frequency maxima are all band-edge constrained.
- Verification:
  - Regenerated `outputs/recording_report_20260917` from all 10 available MAT files.
  - Rendered and visually inspected the five report figures in
    `docs/assets/recording_report_20260917/`.

### Archive prior reports and prepare the recording-level refresh (Codex GPT-5; effort/tokens not reported)

- Moved the two 2026-09-16 cohort reports to `docs/archived/` without deleting
  their Git history. Their report structure remains the template for the refreshed
  recording-level document.
- Replaced the reported literal within-bout processed-NE peak with the arithmetic
  mean of saved NE samples in each labelled bout. The literal maximum remains only
  as the internal anchor for the unchanged peak-assigned width and 20--80% slope
  measurements. Added actual score-bout duration and score-bout count to the
  recording-paired results table and figure. The pooled-bout results deliberately
  omit mean NE; duration and contextual shape metrics remain.
- The updated pipeline treats each MAT file as a paired Active/Quiet recording for
  descriptive summaries. Any repeated mouse/session contribution remains correlated
  and is not independent biological replication.
- Verification:
  - `python -m pytest --basetemp .pytest_refresh -p no:cacheprovider -q`: 30 passed.
  - Rendered and visually inspected the revised recording and pooled-bout figures.
  - Only 10 MAT files were present in `data/`; a ten-file smoke run completed, but
    no replacement report was published because the requested 11-file input set is
    incomplete.

## 2026-09-16

### Report actual score-bout durations alongside NE-event widths (Codex GPT-5; effort/tokens not reported)

- Corrected the reporting omission: the reports now place literal sleep-score-bout
  duration in their results summaries instead of requiring readers to infer it from a
  later note. The nine-file raw screen is 4 s (IQR 2–10) Active versus 2 s (1–4)
  Quiet when pooled by run; its paired file-median summary is 5 s (4–7) versus 2 s
  (1.5–2). The identified four-mouse cohort's pooled-within-mouse medians are 6.0 s
  (4.5–7.0) versus 2.0 s (1.75–2.0).
- Retained the separate peak-assigned NE-episode width and 20–80% slopes; those are
  intentionally different measurements and must not be substituted for score-bout
  duration. The raw analysis now writes every literal run to `score_label_bouts.csv`
  for direct audit.
- Verification:
  - Regenerated `outputs/raw_bout_recording_comparison_20260916_peak_assigned` and
    confirmed its score-bout audit output.

### Raw-bout literal-peak assignment figure (Codex GPT-5; effort/tokens not reported)

- Added a deterministic raw-report trace example that makes the distinct raw-bout
  contract visible: the selected value is the literal maximum within the outlined
  one-state score run, with no rolling baseline, prominence threshold, or local-peak
  detector. Its 20%/80% crossings are relative to that literal maximum and retain the
  same allowed peak-state boundary-crossing policy as the raw analysis.
- Verification:
  - Rendered and visually inspected `raw_peak_assignment_example.png`.
  - Full test/validation results are recorded with this delivery after regeneration.

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
