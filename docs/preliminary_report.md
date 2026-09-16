# Preliminary cohort report: NE during Active and Quiet Wake

**Status:** exploratory cohort draft for proposal discussion, 2026-09-16. This
report asks whether processed norepinephrine (NE) signal elevations differ between
Active Wake and Quiet Wake in the recordings currently available. It is intended to
show what the current data can and cannot support, rather than to make a final
biological claim.

Eight analyzable recordings contribute four identified mice. The initial result is
straightforward: none of the measured NE properties differs significantly between
Active Wake and Quiet Wake in this small, paired sample. The short-window spectral
measure is useful as a feasibility check, but cannot resolve a preferred frequency.

## Executive summary

- The analysis preserves the supplied one-second sleep labels and pools repeated
  recordings within each mouse. Events and recordings are not treated as independent
  biological samples.
- The event measurements (amplitude, duration, rising slope, and decay slope) each
  have three complete mouse pairs. The 15-second spectral power measure has four.
  No comparison reached the exploratory two-sided significance threshold of 0.05.
- The frequency maximum is not tested: every mouse's maximum was 0.20 Hz, exactly
  the lower edge of the preselected 0.20–0.30 Hz band. That pattern says the band is
  descending from below 0.20 Hz; it does **not** identify a 0.20 Hz rhythm.
- One file with a 6.25-second mismatch between saved NE and sleep-label duration was
  excluded without trimming either signal. A separate file has no verified mouse
  identity and is retained in source audit/figures but excluded from mouse-paired
  biological testing.

## Summary of results

Values are median (interquartile range) of each mouse's within-state summary.
`n` is the number of mice with a complete Active/Quiet pair for that metric. The
reported p-values use the paired Wilcoxon signed-rank test described in
[Appendix C](#appendix-c-statistical-test-and-interpretation). They are exploratory
and use a two-sided threshold of 0.05.

| NE measure | Active Wake | Quiet Wake | Paired result | p-value / interpretation |
|---|---:|---:|---:|---|
| Episode amplitude (percentage points) | 0.803 (0.760–0.870) | 0.928 (0.901–0.929) | n = 3 | 0.500; not significant |
| Episode duration (s) | 9.05 (6.40–9.47) | 8.65 (6.86–10.23) | n = 3 | 0.500; not significant |
| 20–80% rise slope (percentage points/s) | 0.237 (0.204–0.378) | 0.342 (0.275–0.368) | n = 3 | 1.000; not significant |
| 20–80% decay slope (percentage points/s) | 0.184 (0.157–0.277) | 0.159 (0.155–0.262) | n = 3 | 0.750; not significant |
| 15 s spectral power, 0.20–0.30 Hz (percentage points²) | 0.0061 (0.0035–0.0105) | 0.0058 (0.0036–0.0094) | n = 4 | 0.625; not significant |
| Frequency maximum in that band (Hz) | 0.20 (0.20–0.20) | 0.20 (0.20–0.20) | n = 4 | Not tested; every value is the lower band edge |

The result is not evidence that the two wake states are biologically identical. With
only three or four paired mouse estimates, it is an absence of a reliable difference
in this preliminary cohort.

## Methodology

### Sleep scoring and Active/Quiet Wake labels

The source sleep-scoring workflow first assigns one label per second to broad states.
Seconds already labelled NREM or REM remain unchanged. Coarse Wake is then divided
into **Active Wake** (label 4) and **Quiet Wake** (label 5) from the EMG activity
level. In plain terms, it measures short-time EMG intensity, learns a conservative
activity threshold from the animal's own NREM EMG distribution, and calls above-
threshold Wake seconds Active and the remaining Wake seconds Quiet. Very brief
activity calls are removed so the final labels remain one-second, stable bouts.

This NE analysis only consumes those saved final labels; it does not relabel sleep
stages or change the EMG threshold. The threshold formula and the one-second
implementation details are in [Appendix A](#appendix-a-activequiet-wake-label-details).

### Recordings, grouping, and quality control

The NE input is the saved, processed percentage delta-F/F trace at its recorded
sampling rate. It is not re-smoothed, normalized, interpolated, or inverse-filtered
here. Eight of nine supplied files passed the duration and label contracts. The
invalid file was excluded rather than forced to match the labels.

Repeated recordings were pooled within Mouse 1 and Mouse 3 before comparison; Mouse
5 and Mouse 7 each contribute one valid recording. The file called `unverified_35`
lacks a verified biological identity, so it remains visible in source audits and the
spectral coverage figure but is not a fifth mouse in the statistical test.

Three recordings showed a large, recurrent stored NE excursion immediately at the
recording start. To prevent that unmodified input artifact from driving a result, the
first 15 seconds are marked ineligible for event inclusion and for spectral windows.
The saved data are not deleted or altered, and the rule is applied identically to
both states.

### Assigning an NE elevation episode to wake state

An NE elevation episode must be complete: it must have both a rising and falling
20%-of-amplitude crossing. Following the PI's direction, a complete episode is
assigned to whichever wake state contains its **peak**, even if its shoulders cross
one or more sleep-label boundaries. This avoids discarding most usable short-state
episodes while keeping the boundary crossings available for audit.

![Example of peak-state attribution](assets/cohort_preliminary_report/peak_state_assignment_example.png)

The orange marker is a Quiet-Wake peak. The purple lines show that the episode's
20% and 80% crossings need not all fall inside the orange background, yet the whole
complete episode is counted as Quiet Wake because its peak does. This is a provisional
proposal rule, not a claim that the entire waveform is uniquely caused by that state.

### NE episode amplitude

For each complete elevation, amplitude is the height of the peak above a local,
slowly varying baseline. We summarize the median amplitude of all eligible events
within each mouse and state. The local-baseline and exact amplitude definitions are
given in [Appendix B](#appendix-b-ne-measurement-details).

### NE episode duration

Duration is the elapsed time from the rising 20%-of-amplitude crossing to the falling
20% crossing. It is deliberately a broad, reproducible duration measure that is less
sensitive to a noisy peak than a peak-width measure. This 20%-to-20% definition is
currently provisional; the PI's original note also mentioned rising and decay
half-times, which are different measures.

### Rising and decay slopes

The rising slope describes how quickly the central part of an elevation rises: the
amplitude change from 20% to 80%, divided by the time taken. The decay slope applies
the same idea to the falling side and is reported as a positive magnitude, so larger
values mean a faster fall. These are **20–80% secant slopes**, not half-times
(T₁/₂). The distinction and exact definitions are in [Appendix B](#appendix-b-ne-measurement-details).

### Short-window spectral power and frequency maximum

Power spectra need equal-duration data segments. We therefore extract non-overlapping
15-second intervals wholly within a single wake state, after the 15-second
recording-start exclusion, and average their spectra within each mouse/state. The
common available band is 0.20–0.30 Hz. We report the total power in that narrow band
and the frequency bin with the largest power.

This measurement is intentionally separate from natural-duration elevation episodes.
Fifteen seconds was chosen because it preserves Quiet-Wake coverage for every
identified mouse. It is not long enough to assess slower activity below 0.20 Hz
reliably, and the prior near-one-second smoothing makes frequencies above roughly
0.30 Hz increasingly attenuated. Further spectral details are in
[Appendix B](#appendix-b-ne-measurement-details).

## Results

### Paired mouse summaries

None of the four elevation measures or the narrow-band power measure showed a
statistically significant Active-versus-Quiet Wake difference. Figure 1 shows every
paired mouse estimate rather than hiding the small sample behind a bar chart. Mouse 7
has valid spectral windows but no detected complete elevations under the provisional
event definition, so it is absent from the event-measure panels and contributes only
to the spectral comparison.

![Paired summaries for all reported metrics](assets/cohort_preliminary_report/cohort_metric_comparisons.png)

**Figure 1.** Each line connects the same identified mouse across wake states.
P-values are two-sided paired Wilcoxon results; see
[Appendix C](#appendix-c-statistical-test-and-interpretation). No panel reaches the
exploratory 0.05 threshold. The frequency panel is labelled “not tested” because all
maxima are the lower band edge, not because it has established equality.

### Why the spectral result is limited to feasibility

Twenty-second windows would give a more useful lower frequency boundary (0.15 Hz),
but Mouse 7 has no Quiet-Wake windows of that length. At 15 seconds it contributes
three Quiet-Wake windows, allowing a common setting across identified mice. The
coverage plot also shows why a longer-window spectrum cannot be rescued by joining
separate bouts: that would mix state transitions and create a different analysis.

![Spectral-window coverage at 15 and 20 seconds](assets/cohort_preliminary_report/spectral_window_coverage.png)

**Figure 2.** Number of eligible fixed windows after the recording-start QC rule.
The labelled `Unverified 35` file is included to document available source data, not
as an independently identified mouse. The 15-second choice produces a 0.20–0.30 Hz
band, but every maximum in that band is at 0.20 Hz. Thus, no preferred-frequency
result should be presented.

## Interpretation for the proposal

The positive result is feasibility: the available sleep labels can be consumed without
relabeling, complete NE elevations can be audited and peak-assigned, and the cohort
supports paired mouse-level summaries. The biological comparison itself is currently
negative and underpowered: no measured property provides a reliable Active-versus-
Quiet Wake difference.

The clearest next scientific steps are to verify the identity of `unverified_35`,
resolve the duration/T₁/₂ versus 20–80%-slope definition with the PI, and obtain
longer uninterrupted Quiet-Wake bouts or a less-slow NE reference trace if slow or
phasic frequency content is central to the question. These are design and data
limitations, not problems that should be hidden by pooling files as independent mice
or by extending/bridging wake bouts.

## Appendix A: Active/Quiet Wake label details

The upstream detector calculates EMG root-mean-square (RMS) activity on the 20 Hz
EMG grid, aggregates it to one-second Wake labels, and anchors its threshold to NREM
in the same recording. Its current pilot threshold is the NREM RMS 75th percentile
plus two robust standard deviations estimated from the median absolute deviation
(MAD):

```text
threshold = NREM_RMS_75th_percentile + 2 × 1.4826 × MAD(NREM_RMS)
```

A coarse-Wake second is Active Wake when its activity meets this threshold; otherwise
it is Quiet Wake. Runs shorter than one second do not survive as a distinct activity
bout. This is a documented upstream pilot setting that needs behavioral/video
validation; it is not re-estimated by the NE pipeline.

## Appendix B: NE measurement details

The event detector estimates a centered 60-second 20th-percentile local baseline and
requires at least 0.5 percentage points of prominence between a candidate peak and
its local baseline. For a peak amplitude `A`, the detector linearly locates the four
times at which the waveform crosses 20% and 80% of `A` on the rising and falling
sides: `t_r20`, `t_r80`, `t_d80`, and `t_d20`.

```text
amplitude       = peak - local baseline
duration        = t_d20 - t_r20
rise slope      = 0.60 × amplitude / (t_r80 - t_r20)
decay slope     = 0.60 × amplitude / (t_d20 - t_d80)
```

The duration includes the broad lower portions of the elevation; the slopes use only
the central 20–80% portion. A T₁/₂ would instead report a time associated with 50%
amplitude, so it should not be substituted for either slope without a new explicit
definition.

For spectra, each eligible 15-second state-pure interval receives a periodogram. The
within-mouse/state spectrum is a window-count-weighted mean, and band power is the
integral from 0.20 to 0.30 Hz. The frequency maximum is simply the highest spectral
bin inside that same interval. Frequency resolution is approximately `1 / 15 = 0.067`
Hz; it is a constrained feasibility measure, not a full frequency characterization.

## Appendix C: Statistical test and interpretation

Each statistical comparison begins with one summary per mouse in Active Wake and one
in Quiet Wake. The two values are paired because they come from the same animal. We
use a two-sided **Wilcoxon signed-rank test**, a nonparametric paired test that asks
whether the ranked within-mouse differences are consistently above or below zero. It
is appropriate here because the sample is very small and we should not assume the
differences follow a normal distribution.

The p-value is the probability, under a no-systematic-difference model, of observing
differences at least as incompatible with zero as these. A p-value below 0.05 would
be called statistically significant in this exploratory report. A p-value above 0.05
does not demonstrate equivalence or absence of biology; it means the current paired
data did not establish a reliable difference. Frequency maximum was not tested because
all paired differences were zero for a methodological reason: the maximum landed on
the lower edge of the search band in every case.

No event or spectral window is used as an independent mouse. The unverified file is
not included in the tests, and a mouse without events in one state has no event-metric
pair. These choices reduce apparent sample size, but avoid pseudoreplication and
overstated confidence.

## Reproducibility

The report figures were generated from the QC'd peak-state output with:

```powershell
python scripts/render_cohort_preliminary_report_figures.py `
  --analysis outputs/proposal_cohort_20260916_startqc_peak15 `
  --preflight outputs/proposal_cohort_20260916_startqc_preflight `
  --mat data/35_app13_groundtruth.mat `
  --output docs/assets/cohort_preliminary_report
```

The output directory must be new or empty when rendering, which prevents silently
mixing figures from different analysis runs.
