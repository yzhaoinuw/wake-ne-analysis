# Work Log

## 2026-09-21

### Present PI-facing alertness palette and NE-excluded Wake sensitivity (Codex GPT-5; effort/tokens not reported)

- Renamed only the PI-facing source-label display language from Active/Quiet Wake
  to High/Low Alertness; final score values 4/5, sampling, and source audits remain
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
