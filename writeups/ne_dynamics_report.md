# Preliminary NE dynamics report: High and Low Alertness

**Status:** descriptive pooled-seconds analysis of ten aligned files, September 23, 2026.

## Executive summary

- NE was declining during **55.2% of Low Alertness seconds versus 51.3% of High
  Alertness seconds**, a difference of 3.9 percentage points.
- Among declining seconds, median decline magnitude was **0.0527 in Low versus
  0.0443 in High Alertness**, approximately 19% greater in Low.
- Among rising seconds, median slopes were similar: **0.0494 in Low versus
  0.0481 in High Alertness**.
- Median variance over the preceding 10 seconds was **0.0600 in Low versus
  0.0559 in High Alertness**, about 7.4% greater in Low. After removing a local
  linear trend, median variance was **0.0369 versus 0.0355**, about 3.8% greater
  in Low. Both pooled comparisons remain below 0.05 after the original
  four-feature Holm correction, with small effects and substantial overlap.
- Absolute slow slope, irrespective of direction, also had a higher pooled median
  in Low Alertness: **0.0517 versus 0.0458**.
- These results describe a modest tendency for Low Alertness to coincide with
  declining portions of the slow NE signal. They do not show a sustained decline
  throughout Low Alertness or a decline triggered by entering that state.

## Summary of results

All eligible seconds were pooled across files, with equal weight per second.
Slope units are percentage points/s. Direction-specific slopes are medians
(interquartile ranges) calculated only among seconds with that direction.

| Reported measure | High Alertness | Low Alertness |
|---|---:|---:|
| Seconds with an available slope | 30,212 | 7,555 |
| Rising seconds, count (%) | 14,699 (48.7%) | 3,382 (44.8%) |
| Declining seconds, count (%) | 15,513 (51.3%) | 4,173 (55.2%) |
| Exactly zero slope, count | 0 | 0 |
| Median signed slope, all eligible seconds | −0.00178 | −0.00828 |
| Mean signed slope, all eligible seconds | +0.00897 | +0.00534 |
| Rising slope, among rising seconds | +0.0481 (0.0188–0.1000) | +0.0494 (0.0194–0.1092) |
| Decline magnitude, among declining seconds | 0.0443 (0.0187–0.0817) | 0.0527 (0.0235–0.0945) |

Decline magnitude is presented as a positive value for readability; the underlying
signed slopes are negative. The approximately 19% difference compares the two
conditional medians, not every individual decline.

### Full pooled feature comparisons

The four original NE features are reported together below. Slopes use 30,212 High
and 7,555 Low seconds; both variance measures use 30,436 High and 7,606 Low seconds.
Slope units are percentage points/s; variance units are percentage points squared.
Positive rank-biserial effects indicate higher values in High Alertness.

| Measure | High median (IQR) | Low median (IQR) | Rank-biserial effect | Nominal p | Holm-adjusted nominal p |
|---|---:|---:|---:|---:|---:|
| Signed slow slope | −0.001784 (−0.04562–0.04619) | −0.008278 (−0.05914–0.04137) | +0.0600 | 6.46 × 10⁻¹⁶ | 1.94 × 10⁻¹⁵ |
| Absolute slow slope | 0.04583 (0.01876–0.08916) | 0.05172 (0.02167–0.10014) | −0.0613 | 1.62 × 10⁻¹⁶ | 6.47 × 10⁻¹⁶ |
| Ordinary trailing variance | 0.05591 (0.02550–0.11527) | 0.06004 (0.02824–0.12521) | −0.0457 | 6.78 × 10⁻¹⁰ | 1.36 × 10⁻⁹ |
| Detrended trailing variance | 0.03553 (0.01657–0.07085) | 0.03687 (0.01792–0.07122) | −0.0248 | 0.000825 | 0.000825 |

All four nominal pooled comparisons remain below 0.05 after the original
four-feature Holm adjustment. Effect magnitudes are small (0.025–0.061), with
substantial distributional overlap. The statistical appendix explains the
pooled-second inference limits.

## Methodology

### Labels and input handling

Final one-second labels were unchanged: 4 High Alertness and 5 Low Alertness.
All ten files contributed, including `mouse5_day1.mat` and `408_yfp.mat`. Excess
NE at the end was removed in memory to retain the common aligned interval:
63 samples from `mouse5_day1` (original duration excess 6.246 s) and 251 from
`408_yfp` (24.683 s). If NE ended first, incomplete final score seconds remained
unavailable.
Source MAT files were not modified. Saved normalized percentage delta-F/F values
were used without additional normalization or recording balancing.

### Slow signed slope and direction

The continuous NE signal was low-pass filtered at an effective 0.1 Hz cutoff
using a zero-phase forward/backward Butterworth filter. A straight line was
fitted to the filtered samples within each score second. Positive slope was
classified as rising, negative slope as declining, and exact zero as neither.
Absolute slope is the magnitude of the same signed slope, regardless of direction.

No minimum slope magnitude was imposed, so small slopes near zero are included.
Filtering crosses score boundaries. Invalid signal gaps were not bridged, and
the fixed 30-second filter-edge guards were retained. Missing slopes were omitted
from the denominator. This left 30,212 of 30,497 High seconds and 7,555 of 7,623
Low seconds available.

### Trailing variance

For a score second beginning at `s`, variance was calculated from the saved
processed NE samples in `[s-10, s)`. The additional 0.1 Hz low-pass used for
slopes was **not** applied to these variance measurements. Ordinary variance
captures the signal's spread over that history; detrended variance captures the
remaining spread after removing a fitted straight-line trend.

History windows may cross any score states. A complete finite 10-second history
was required, without joining different files or bridging invalid signal gaps.
The result was assigned to the current second's unchanged label. Both variances
divide by the number of samples. These rules retained 30,436 of 30,497 High
seconds and 7,606 of 7,623 Low seconds.

## Results

### Frequency of rising and declining seconds

High Alertness was close to an even split between rising and declining NE.
Low Alertness had a modestly greater share of declining seconds: 55.2% compared
with 51.3% in High. These percentages count seconds, not separate NE events;
several consecutive seconds can belong to the same decline.

### Magnitude within each direction

Typical rising slopes were similar between the labels. The clearer directional
contrast was among declining seconds, where the median decline magnitude was
approximately 19% larger in Low Alertness. The interquartile ranges overlap
substantially in both directions.

![Frequency and magnitude of rising and declining NE](assets/ne_slope_direction_20260923/slope_direction.png)

**Figure 1.** Left: percentage of eligible state seconds classified as rising or
declining. Right: median slope magnitude and interquartile range within each
direction; declining slopes are displayed as positive magnitudes. The error bars
show the spread of seconds, not confidence intervals.

### Why the mean and median have different signs

Median signed slopes were negative in both groups, but mean signed slopes were
positive. More frequent negative slopes can coexist with a positive mean when
larger positive slopes outweigh them. The pooled result therefore does not imply
a continuous fall in NE during either label.

### Recent NE variability

Low Alertness had slightly greater ordinary and detrended trailing variance.
The Low median was 7.4% higher for ordinary variance and 3.8% higher after
detrending. Thus, the pooled difference is also present in fluctuations remaining
after a local linear trend is removed. This does not establish that the slope
and variance effects are independent.

![Ordinary and detrended trailing NE variance](assets/ne_slope_direction_20260923/variance_dynamics.png)

**Figure 2.** Pooled variance over the preceding 10 seconds, assigned to the
current second's alertness label. Boxes show the median and interquartile range;
whiskers show the 5th–95th percentiles. Tail points are omitted only from the
display; all finite values enter the comparisons. The distributions overlap
substantially. Rank-biserial effects are −0.0457 for ordinary variance and −0.0248
for detrended variance, where negative values indicate higher values in Low.

## Interpretation for the proposal

The pooled data suggest that Low Alertness more often coincides with declining
segments of the slow NE signal, and that these declining segments have a larger
typical slope magnitude. Rising segments have similar typical slopes in the two
labels. Absolute slope across all eligible seconds is also greater in Low,
consistent with its greater typical decline magnitude. This is a descriptive
association with local waveform direction; it does
not establish that NE falls when the animal switches into Low Alertness.

Low Alertness also coincides with slightly greater recent NE variability, both
before and after removing a local linear trend. Together, these are modest
pooled associations with NE dynamics, rather than a clear separation of the
two alertness labels.

## Appendix A: statistical interpretation

This rise/decline breakdown is descriptive; no additional significance tests were
added. The existing full signed-slope comparison has a nominal Mann–Whitney
p = 6.46 × 10⁻¹⁶, Holm-adjusted p = 1.94 × 10⁻¹⁵ across the original four NE
features, and rank-biserial effect = 0.060. That test compares the full signed-slope
distributions; it is not a separate test of the 3.9-percentage-point frequency
difference or the 19% conditional decline-magnitude difference.

The four-feature table reuses the original pooled Mann–Whitney comparisons and Holm
adjustment across all four NE features; the correction was not recalculated over
only the two variance measures. Rank-biserial effect is `2U/(nHigh × nLow) − 1`.
These tests compare distributions, not solely
medians. No new tests or feature extraction were required for this report update.

Adjacent seconds and overlapping history windows are correlated, and recordings
contribute unequal numbers of seconds. Saved NE normalization gives common
nominal units but does not guarantee identical signal scale or noise across files. The pooled p-values are therefore
exploratory and do not establish independent-animal significance. Zero-phase
filtering also uses surrounding samples, so these slopes cannot establish that
NE changes precede an alertness transition.

## Reproducibility

The complete workflow extracts the four features, renders their pooled results,
and summarizes rising/declining seconds from the same archives:

```powershell
conda activate sleep_scoring_dash3.0
python scripts/analyze_ne_dynamics.py --input-dir data --feature-dir data/derived_features/ne_dynamics_v2_pooled_20260923 --results-dir results/ne_dynamics_v2_pooled_20260923
python scripts/render_ne_dynamics.py --results-dir results/ne_dynamics_v2_pooled_20260923 --output-dir results/ne_variance_report_20260923 --png
python scripts/summarize_ne_slope_direction.py --analysis-dir results/ne_dynamics_v2_pooled_20260923 --output-dir results/ne_slope_direction_20260923_final --png
```

Use fresh output names when rerunning. Existing feature archives and comparisons
were reused for this report; no features or tests were recomputed for consolidation.
The analysis directory contains `pooled_comparisons.csv`, `source_audit.csv`,
per-file feature coverage, and run provenance; per-second data remain in versioned
NPZ archives. The direction summary adds `slope_direction_summary.csv` and archive
hashes. Rendered HTML/PNG figures are saved locally, and the two displayed PNGs
are copied into this report's asset folder. Source identity is retained for audit
but does not enter the pooled comparison.

See [feature definitions](../wake_ne_analysis/ne_dynamics.py) and
[statistical definitions](../wake_ne_analysis/dynamics_summary.py) for executable
details. The common-start policy follows the
[preliminary recording report](preliminary_recording_report.md#recordings-grouping-and-input-handling).
The older eight-file comparison is [superseded historical material](../archive/ne_dynamics_v1_recording/report.md).
