# Work Log

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
