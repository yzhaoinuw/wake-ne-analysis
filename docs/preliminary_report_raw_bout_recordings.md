# Preliminary raw-bout recording comparison: NE during Active and Quiet Wake

**Status:** deliberately exploratory sensitivity analysis, 2026-09-16. This report
uses the literal values of the already processed NE percentage delta-F/F trace within
each Wake bout, without subtracting a new rolling local baseline. It is a complement
to—not a replacement for—the [local-baseline cohort report](preliminary_report.md).

This version asks the obvious, simpler question: in each labelled Active- or
Quiet-Wake bout, how high does the stored processed NE trace get? It deliberately
treats every MAT file as a separate recording for this preliminary screen, including
multiple files that may come from the same mouse. That shortcut increases the number
of recording pairs but is not a valid mouse-level biological inference.

## Executive summary

- All nine available MAT files contribute as separate recordings. The file with a
  longer NE trace is retained: analysis uses the common interval from the shared
  start through the shorter sleep-label duration, leaving its final 6.25 seconds of
  unlabelled NE outside the state comparison. No input file is altered.
- The **zero-referenced peak** is significantly higher in Active Wake than Quiet Wake
  in the nine recording pairs (two-sided paired Wilcoxon p = 0.0117). This is an
  exploratory recording-level signal, not a mouse-level result.
- Zero-referenced duration and 20–80% slopes are available for only four complete
  recording pairs, and none differs significantly. Their sparse availability is a
  property of the literal, no-baseline crossing definition—not an excluded file.
- Unlike the local-baseline report, this analysis retains all labelled common-start
  bouts, including the previously documented recording-start excursions. That makes
  the sensitivity transparent, but it also leaves those artifacts able to influence
  the result.

## Summary of results

Each MAT file first contributes a median and IQR across its own eligible Wake bouts.
The table then summarizes those per-recording medians across the recording pairs.
Orange denotes Active Wake and light blue Quiet Wake. The p-values are paired by
recording, but the rows are provisionally treated as independent even though some
recordings may share a mouse; see [Appendix B](#appendix-b-recording-level-statistics-and-limitation).

| Zero-referenced measure | Active Wake | Quiet Wake | Recording pairs | p-value / interpretation |
|---|---:|---:|---:|---|
| Peak processed NE (percentage delta-F/F) | 1.833 (1.044–2.661) | 1.651 (0.927–2.510) | n = 9 | 0.0117; significant exploratory recording-level signal |
| Duration (s) | 6.60 (5.23–7.06) | 1.35 (0.91–1.97) | n = 4 | 0.125; not significant |
| 20–80% rise slope (percentage points/s) | 0.438 (0.363–0.498) | 0.501 (0.388–0.520) | n = 4 | 0.875; not significant |
| 20–80% decay slope (percentage points/s) | 0.254 (0.171–0.394) | 0.504 (0.340–0.652) | n = 4 | 0.625; not significant |

The significant peak result is compatible with higher stored processed NE levels in
Active Wake in this file-level screen. It does **not** establish a state effect across
independent mice, and it does not adjudicate between the zero-referenced and
local-baseline definitions.

## Methodology

### Labels, recording interval, and unit of analysis

The analysis reads the final one-second Active-Wake (4) and Quiet-Wake (5) labels
without changing them. Each MAT file is intentionally assigned one unique recording
identity based on its filename. Both state summaries from the same file remain paired,
but files are provisionally treated as independent records. This is a pragmatic
exploratory assumption, not a claim that repeated recordings from one mouse are
biologically independent.

For every file, the comparison uses the interval beginning at the shared saved start
and ending when either the NE signal or label vector ends. This declared common-start,
minimum-duration rule retains `mouse5_day1.mat`: its state-labelled interval is used,
while its extra 6.25 seconds of NE cannot be assigned to a state and therefore is not
analyzed. No NE samples or sleep labels are rewritten, shifted, or silently trimmed.

### Literal zero-referenced NE peak within each Wake bout

A Wake bout is a continuous finite segment labelled entirely Active Wake or entirely
Quiet Wake. Within every such bout, the analysis takes the maximum of the stored,
processed NE percentage delta-F/F trace. That value is the **zero-referenced peak**:
it is relative to the trace's existing zero, not relative to a newly estimated local
baseline. Each recording/state is summarized by the median and IQR of its bout peaks.

This is not unprocessed fluorescence. The stored trace has already gone through the
upstream control fitting, delta-F/F conversion, smoothing, and downsampling. The
reason to include this sensitivity is that those upstream operations may make values
from different times reasonably comparable; that premise remains to be evaluated,
not assumed proven.

### Literal duration and 20–80% slopes

For a bout whose literal peak is positive, the detector searches *within that same
bout* backward and forward from the peak for the nearest 20% and 80% crossings of the
zero-referenced peak value. It then calculates duration from the rising 20% to the
falling 20% crossing and rise/decay slopes through the middle 20–80% range.

If a bout's peak is non-positive, is at a bout edge, or lacks any of the required
within-bout crossings, its duration and slopes are missing for that metric. Its peak
is still retained. Bouts are never joined across a sleep-state boundary or an invalid
NE sample. Exact formulas are in [Appendix A](#appendix-a-zero-referenced-bout-metrics).

### How this differs from the local-baseline report

The primary [local-baseline report](preliminary_report.md) first estimates a rolling
20th-percentile baseline across continuous NE, detects baseline-subtracted elevations,
and assigns each event to the state at its peak. This sensitivity instead begins with
the state bouts, uses their literal stored NE maxima, and confines all crossing searches
to the same bout. The two approaches answer related but different questions and should
not be pooled or presented as interchangeable estimates.

## Results

### Recording-paired raw-bout summaries

The zero-referenced peak is higher in Active Wake in the nine-file screen. The plot
shows every file-level median; each line joins Active and Quiet summaries from the
same MAT file. The apparent p-value is conditional on treating those nine files as
independent recordings, which is the explicitly temporary simplification here.

![Recording-paired raw-bout metrics](assets/raw_bout_recording_comparison/raw_bout_metric_comparisons.png)

**Figure 1.** Each point is a file-level median across bouts. Orange is Active Wake;
light blue is Quiet Wake. Duration and slope panels include only records with complete
zero-referenced crossings in both states; the peak panel includes all nine files.

### Interpretation for the proposal

This analysis provides a useful positive exploratory signal: literal stored NE peak
levels are higher during Active Wake in the available recording pairs. It is most
useful as an initial proposal figure because it is simple and transparent. It is not
a substitute for the local-baseline analysis, nor sufficient for a mouse-level claim,
because repeated file rows may share an animal and the zero reference may still drift
over a long recording.

The two reports together are informative rather than contradictory: they contrast a
local, drift-resistant elevation question with a literal processed-NE level question.
The next dataset should preserve recording-to-mouse identity and permit a predeclared
mouse-level analysis of both definitions.

## Appendix A: Zero-referenced bout metrics

Let `x(t)` be the stored processed percentage delta-F/F trace inside one finite,
single-state Wake bout. Let `P = max(x(t))` be that bout's literal peak. There is no
new baseline subtraction. When `P > 0`, locate within the bout the nearest rise and
fall crossings at `0.2P` and `0.8P`, named `t_r20`, `t_r80`, `t_d80`, and `t_d20`.

```text
zero-referenced peak = P
duration             = t_d20 - t_r20
rise slope           = 0.60 × P / (t_r80 - t_r20)
decay slope          = 0.60 × P / (t_d20 - t_d80)
```

The formula is deliberately literal: it measures thresholds relative to zero on the
processed trace. It is not equivalent to a conventional peak-above-baseline event
amplitude. The crossing-based metrics are set to missing, rather than fabricated, when
the required within-bout shape does not exist.

## Appendix B: Recording-level statistics and limitation

The comparison uses one Active and one Quiet median per MAT file, then applies a
two-sided paired Wilcoxon signed-rank test across files. Pairing is retained because
both state summaries come from the same recording. The test is nonparametric and
appropriate for a small set of paired numeric values, but its usual interpretation
assumes those pairs are independent.

That assumption is knowingly provisional here: some files are repeated recordings
from the same mouse. Therefore p-values in this report are screening statistics, not
confirmatory biological evidence. They should not be combined with the independent-
mouse local-baseline p-values or used to claim a final state effect.

## Reproducibility

The raw-bout tables and figure were generated with:

```powershell
python scripts/analyze_raw_bouts.py `
  --input-dir data `
  --output outputs/raw_bout_recording_comparison_20260916

python scripts/render_raw_bout_report_figures.py `
  --analysis outputs/raw_bout_recording_comparison_20260916 `
  --output docs/assets/raw_bout_recording_comparison
```

Both output directories must be new or empty, preventing accidental mixing of results
from different input sets.
