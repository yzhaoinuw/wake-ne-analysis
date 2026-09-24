# Preliminary NE dynamics report: High and Low Alertness

**Status:** descriptive pooled-seconds analysis of ten files, with recording-start
quality exclusion, September 23, 2026.

## Questions

1. Is NE more often rising or declining during High versus Low Alertness?
2. Do NE slopes differ between the two labels, overall and during rises and declines?
3. Does NE variance over the preceding 10 seconds differ between the two labels?

## Executive summary

- **High has a more positive overall mean slope:** +0.00890 versus +0.00519 in
  Low. This does **not** mean NE rises faster in High: during rising seconds,
  mean slope is +0.07978 in High versus +0.09571 in Low.
- **Low has steeper rises and declines.** Its overall mean is less positive because
  it declines more often (55.3% versus 51.3%) and more steeply (−0.06804 versus
  −0.05828). Those declines offset more of its positive contribution.
- **Low has greater variability:** mean ordinary variance is 0.17268 versus
  0.14073 in High (22.7% higher); mean detrended variance is 0.06039 versus
  0.05745 (5.1% higher). The previous High advantage in detrended variance
  disappears after excluding recording starts.
- **These results support a more positive balance of rising and falling in High,
  not generally stronger NE changes or greater variability in High.** The groups
  overlap substantially; slope and variance do not establish overall NE activity.

## Summary of results

All eligible seconds were pooled across files with equal weight per second.
Averages are arithmetic means. Slopes are in percentage points/s and are positive
for rises and negative for declines. Direction-specific means include only seconds
with that direction.

| Reported measure | High Alertness | Low Alertness |
|---|---:|---:|
| Seconds with an available slope | 30,184 | 7,549 |
| Rising seconds, count (%) | 14,687 (48.7%) | 3,376 (44.7%) |
| Declining seconds, count (%) | 15,497 (51.3%) | 4,173 (55.3%) |
| Exactly zero slope, count | 0 | 0 |
| Mean signed slope, all eligible seconds | +0.00890 | +0.00519 |
| Mean slope, rising seconds | +0.07978 | +0.09571 |
| Mean slope, declining seconds | −0.05828 | −0.06804 |

### Full pooled feature comparisons

Slopes use 30,184 High and 7,549 Low seconds; both variance measures use 30,414
High and 7,598 Low seconds. Variance units are percentage points squared.

| Measure | High mean | Low mean | Rank-biserial effect | Nominal p | Holm-adjusted nominal p |
|---|---:|---:|---:|---:|---:|
| Signed slope | 0.008901 | 0.005191 | +0.0604 | 4.31e-16 | 1.29e-15 |
| Absolute slope | 0.068742 | 0.080412 | -0.0615 | 1.26e-16 | 5.06e-16 |
| Ordinary trailing variance | 0.140726 | 0.172681 | -0.0453 | 9.12e-10 | 1.82e-09 |
| Detrended trailing variance | 0.057446 | 0.060392 | -0.0243 | 0.00103 | 0.00103 |

**How much do the groups differ?** Rank-biserial effect describes how often one
label has the higher value when comparing a randomly selected High second with a
randomly selected Low second. Positive scores favor High, negative scores favor
Low, and zero means neither has the higher value more often. A score of +0.060
corresponds to a 53% versus 47% split, not a 6% difference in average slope.
Counting ties as half a comparison for each label:

- **Signed slope:** High has the higher value in **53.0%** of comparisons.
- **Absolute slope:** Low has the higher value in **53.1%** of comparisons.
- **Ordinary variance:** Low has the higher value in **52.3%** of comparisons.
- **Detrended variance:** Low has the higher value in **51.2%** of comparisons.

These are close to an even 50/50 split. Although the averages differ, a value
from either label commonly exceeds one from the other. **The features show weak
separation between High and Low Alertness seconds.**

**What do the small p-values establish?** All four remain below 0.05 after Holm
correction accounts for testing four features; the largest adjusted p-value is
0.00103. Mann–Whitney compares the full sets of values, not the reported mean
differences. It treats seconds as independent, although neighboring seconds and
overlapping windows are related. “Nominal” means the p-values are calculated under
that unmet independence assumption. Holm correction covers the four tests, not
this dependence. **Small p-values do not establish a large difference or a result
that reliably repeats across animals.**

## Methodology

### Labels and input handling

Final one-second labels were 4 High Alertness and 5 Low Alertness. All ten files
contributed. Excess NE beyond the score interval was trimmed; incomplete final
score seconds were unavailable where NE ended first. Saved normalized percentage
delta-F/F values were used without additional normalization or recording balancing.

### Recording-start quality check

Three recordings contained large startup excursions that settled within roughly
two seconds. Two affected High observations were sufficient to reverse the original
mean detrended-variance comparison. We therefore excluded the first **5 seconds
of every recording**, before filtering or calculating history windows. This
conservative rule was based on inspection of the signals without alertness labels
and fixed before the revised comparisons. Source data, labels, and timestamps
were preserved. It is a quality rule for this collection, not a validated instrument
settling time; no other signal-quality exclusions were added.

### Slope and direction

NE was low-pass filtered at an effective 0.1 Hz cutoff using a fourth-order,
zero-phase forward/backward Butterworth filter. A straight line was fitted to the
filtered samples within each score second to measure slope. Positive slopes were
classified as rising, negative slopes as declining, and exact zero as neither.
Absolute slope ignores the sign when comparing steepness across all seconds.

Slopes close to zero were included. Invalid signal gaps were not bridged.
The existing 30-second filter-edge guards restart after the excluded prefix.
These rules retained 30,184 of 30,497 High seconds and 7,549 of 7,623 Low seconds.

### Trailing variance

For a score second beginning at `s`, variance was calculated from saved processed
NE in `[s-10, s)`, without additional filtering. History may cross any score states,
but must contain a full 10 seconds of finite, retained samples. Thus, histories
touching the excluded prefix are unavailable. Each value is assigned to the
current second's label. These rules retained 30,414 High and 7,598 Low seconds.

Ordinary variance is the main variability measure. The secondary detrended
variance subtracts a separate fitted line within each window first. Recording-level
detrending can leave local rises and falls, so this optional step removes some
local NE changes as well as any drift. Both variances divide by sample count.

## Results

### Overall slope and slopes within each direction

**High has a more positive overall mean slope, but Low has steeper rises.**
There is no contradiction: the overall mean combines the frequency and slope
of both rising and declining seconds:

**Overall mean slope = fraction rising × mean rising slope + fraction declining × mean declining slope.**

- **High:** 0.4866 × 0.07978 + 0.5134 × (−0.05828) ≈ **+0.00890**.
- **Low:** 0.4472 × 0.09571 + 0.5528 × (−0.06804) ≈ **+0.00519**.

Low declines more often and more steeply, offsetting more of its steeper rises.
Both overall means remain positive because rising slopes outweigh declining
slopes in the average. **The High result describes the balance of rises and
falls; it does not show faster NE rises during High Alertness.**

![Frequency and slopes of rising and declining NE](assets/ne_slope_direction_20260923/slope_direction.png)

**Figure 1.** Left: percentage of eligible state seconds rising or declining.
Right: slope distributions within each direction. Boxes contain the middle 50%
of values, lines mark medians, black dots mark means, and whiskers span the
5th–95th percentiles. Tail points are omitted only from the display. These show
the spread of seconds, not uncertainty in the mean.

### Recent NE variability

**Both variance measures are higher in Low:** ordinary variance by 22.7% and
detrended variance by 5.1%. The earlier higher High mean detrended variance was
sensitive to startup excursions and is not retained as a finding. Together with
the greater absolute slope in Low, these results do not support greater NE
variability during High Alertness.

![Ordinary and detrended trailing NE variance](assets/ne_slope_direction_20260923/variance_dynamics.png)

**Figure 2.** Variance over the preceding 10 seconds, assigned to the current
second's label. Boxes, lines, dots, and whiskers follow Figure 1. All retained
finite values, including omitted tail points, enter the means and tests. The
p-values compare distributions, not means; the distributions overlap substantially.

## Interpretation for the proposal

High Alertness has a more positive average NE slope; Low has steeper rises and
declines and greater variability. These are different aspects of the signal,
so the results do not support a general claim that NE is “more active” in either
label. They also do not establish that NE changes precede an alertness transition.

## Appendix A: statistical interpretation

The two-sided Mann–Whitney tests were recomputed after startup exclusion with
Holm adjustment across the same four features. Rank-biserial effect is
`2U/(nHigh × nLow) − 1`. No additional tests of means or the rise/decline breakdown
were added. The full signed-slope test does not separately test the frequency
of rises or declines or the mean slopes within each direction.

Recordings contribute unequal numbers of seconds. Saved NE normalization gives
common nominal units but does not guarantee identical signal scale or noise
across files. Together with temporal dependence, this limits interpretation to
an exploratory pooled comparison rather than independent-animal evidence.

## Reproducibility

```powershell
conda activate sleep_scoring_dash3.0
python scripts/analyze_ne_dynamics.py --input-dir data --feature-dir data/derived_features/ne_dynamics_v3_startup5_20260923 --results-dir results/ne_dynamics_v3_startup5_20260923 --startup-exclusion-seconds 5 --no-report
python scripts/render_ne_dynamics.py --results-dir results/ne_dynamics_v3_startup5_20260923 --output-dir results/ne_dynamics_startup5_figures_final_20260923 --png
python scripts/summarize_ne_slope_direction.py --analysis-dir results/ne_dynamics_v3_startup5_20260923 --output-dir results/ne_slope_direction_startup5_20260923 --png
```

Use fresh output names when rerunning. The startup-excluded feature archives,
source audit, comparisons, direction summaries, and figure provenance are saved
in the directories above. `startup_rule.json` records the QC decision; the prior
runs remain available locally. This report and both figures use the new run.

See [feature definitions](../wake_ne_analysis/ne_dynamics.py) and
[statistical definitions](../wake_ne_analysis/dynamics_summary.py) for executable
details. Input handling follows the
[preliminary recording report](preliminary_recording_report.md#recordings-grouping-and-input-handling).
The older eight-file comparison is [superseded historical material](../archive/ne_dynamics_v1_recording/report.md).
