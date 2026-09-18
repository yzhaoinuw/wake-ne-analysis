# Metric definitions and pilot choices

## Upstream Active/Quiet Wake detection

This analysis package does **not** relabel sleep stages. It analyzes the final
one-second `sleep_scores` supplied by the scoring app: 4 is Active Wake and 5 is
Quiet Wake. Those labels are produced upstream only after ordinary coarse scoring
(Wake/NREM/REM), sparse manual-label overlay, and optional EMG subdivision of the
remaining Wake seconds.

The default upstream subdivision linearly detrends raw EMG, applies a zero-phase
20 Hz to `min(200 Hz, 0.45 * sampling_rate)` band-pass filter, then calculates one
true RMS value for each final one-second score interval:
`sqrt(mean(filtered_EMG^2))`. This is not the ordinary EMG mean, whose positive and
negative waveform values cancel. A score is invalid if its EMG contains missing,
flatlined, or otherwise unusable signal; the app stops subdivision rather than
silently calling it Quiet Wake.

Within each recording, unlabelled Wake seconds are ranked by that one-second RMS.
The highest-ranked seconds are labeled Active until the final recording targets 80%
Active Wake and 20% Quiet Wake. This is a relative within-recording split, not an
absolute movement-intensity threshold. Explicit manual Active/Quiet labels remain
authoritative. If they make the target impossible, the app keeps them and reports the
achieved ratio in its usual prediction confirmation.

The prior NREM-anchored 20 Hz envelope method remains a parked comparison option. It
uses a centered 0.5-second RMS envelope, a threshold from the NREM RMS 75th percentile
plus two MAD-derived robust standard deviations, short-gap bridging, and one-second
occupancy. It is not the default labeling rule. Both methods treat EMG amplitude as a
recording-specific muscle-activity proxy, not a calibrated whole-body movement measure,
and require review against real recordings and expert/video annotation.

## Expanded exploratory feature archives

`features/features_29/` is a separate, versioned dimensional-reduction feature
set. It has 29 per-second features: twenty log EEG band powers from 0.5--5 Hz and
then 5-Hz steps through 95--100 Hz; exact upstream scoring-band log powers using
`>1--4 Hz` and `>4--8 Hz`; five EMG features; and two NE features. EEG power uses
the same one-second Hann periodogram/density convention as the compact feature set.
The strict lower / inclusive upper frequency-bin rule prevents adjacent bands from
double-counting a boundary bin. The 5-Hz panel is exploratory; a one-second epoch
does not create high spectral resolution.

The EMG features retain the native mean-centred RMS and add filtered RMS,
burst-onset count, burst-duty fraction, and peak 75-ms RMS-envelope value. The
EMG trace is linearly detrended and zero-phase fourth-order band-pass filtered from
20 Hz to `min(200 Hz, 0.45 * saved EEG/EMG rate)`, matching the upstream method's
filter family. To bound runtime on multi-hour recordings, filtering uses 120-s
cores with one second of context on each side discarded after filtering. It is
therefore deterministic and edge-buffered, but not bit-identical to a single
whole-recording `filtfilt` call. A provisional burst exceeds the recording envelope
median plus three MAD-derived robust standard deviations; gaps up to 50 ms are
joined and runs shorter than 50 ms removed. Bursts are detected on continuous finite
EMG, then their onsets and overlap fractions are assigned to score seconds.

The NE features are the existing per-second mean and an ordinary-least-squares
within-second slope in saved processed % delta-F/F per second. The saved NE trace is
already strongly smoothed upstream, so slope is a local directional summary, not a
phasic release or clearance measurement. The expanded archives preserve all finite
rows and record the per-file threshold/configuration in `metadata_json`; no feature
is clipped or removed for apparent extremity.

## Spectral analysis

Within each file, construct the intersection of finite NE samples and each wake
state. Separate continuous runs stay separate. Take consecutive **non-overlapping**
windows of the chosen duration starting at each run's first sample. Drop the final
incomplete tail for spectra only. No concatenation, padding, or time stretching.
This deterministic placement may underrepresent short bouts and tails; the coverage
table measures that selection. It is not a correction for biological selection bias.

Each window is mean-centered and multiplied by a Hann window. SciPy's `periodogram`
with `scaling="density"` supplies normalized, one-sided PSDs. Averaging these fixed
windows is a non-overlapping Welch-style estimator. The number of samples is rounded
from duration times sampling rate; actual durations are saved. Interpolate each PSD
onto a common physical-frequency grid spaced at `1/window_seconds`, including exact
band edges. This accommodates small differences in saved sampling rates without
resampling the waveform and does not increase spectral resolution.
Coverage estimates use sample counts divided by rate, capped at the available
one-second labeled duration to avoid percentages above 100% from state-edge
quantization at noninteger sampling rates.

Per-file spectra average windows. Per-mouse spectra weight each file's spectrum by
its number of windows, giving each window equal influence. Integrate the averaged
spectrum with the trapezoid rule for band power, and choose its maximum within the
band for dominant frequency. Do not average separate per-file peak frequencies.
An exactly zero-power spectrum has no dominant frequency (NaN).

Use identical settings across both states and mice. The configurable three-cycle
minimum at the lower band edge is a **pilot adequacy rule**, not a proof of sufficient
precision. The preflight report's `three_cycle_frequency_hz` is `3/window_seconds`.
Too-short Quiet Wake may make slow-frequency comparison infeasible. Missing results
are valid outputs, not reasons to stitch bouts or pad them. A continuous-recording
time-frequency analysis around short states would answer a different, contextual
question and is not implemented.

`smoothing_only_power_retention_at_fmax` reports the fourth power of the discrete
moving-average magnitude response at the upper band edge, using raw rate = saved
rate times the recorded factor. It describes the final forward–backward smoothing
step only. It does not account for nonlinear control normalization, aliasing, sensor
kinetics, or the full acquisition chain, and no inverse correction is performed.
It is a diagnostic value, not an automatic frequency-band acceptance threshold.

### Frequency-interpretation guideline

The saved sampling rate gives a mathematical Nyquist limit, not by itself a useful
physiological range. For the first file's expected raw rate and 1,000-sample
forward–backward moving average (about 0.983 s per pass), smoothing-only power
retention is about 94% at 0.1 Hz, 77% at 0.2 Hz, 55% at 0.3 Hz, and 18% at 0.5 Hz.
Treat slow modulation through roughly 0.2 Hz as well supported by that processing
diagnostic; interpret approximately 0.2–0.3 Hz cautiously, and do not make primary
claims above 0.3 Hz without separate validation. This is not a biological-band
recommendation or an inverse filtering rule. Continuous state-window coverage can
set a more restrictive lower-frequency limit; use the saved coverage table and the
three-cycle diagnostic before selecting a common band.

## NE signal elevation-episode detection

An **NE signal elevation episode** is a temporary local rise and fall in the processed
NE signal above its nearby baseline. These choices are a **draft**, to be calibrated
with real traces and PI feedback.
The established requirements are natural event timing and 20–80% rise/decay slopes;
the baseline, prominence and boundary policies below were chosen for an inspectable
first implementation, not supplied as a validated laboratory protocol.

1. Work on each continuous finite stretch of the full NE recording, **not** on
   separate fixed windows or separately cropped wake bouts. No extra NE smoothing.
2. Estimate a local baseline with a centered rolling 20th percentile over 60 seconds
   (configurable), using nearest-endpoint extension. Subtract it for event detection
   and crossing measurement. It is a time-varying baseline, not a constant zero line.
3. Estimate residual fluctuation scale from adjacent finite NE differences as
   `1.4826 * MAD(diff(NE)) / sqrt(2)`. Temporal correlation after upstream smoothing
   makes this a heuristic, not a calibrated noise standard deviation.
4. Require positive height and prominence at least
   `max(min_prominence, noise_multiplier * scale)`; defaults are 0.5 percentage
   points and 3. Use the same threshold for both states within a recording.
5. SciPy `find_peaks` selects local maxima with a configurable one-second minimum
   separation. It can merge close peaks; plateau centers follow SciPy's convention.
   The first/last sample of a finite stretch cannot be detected as a peak. Edge and
   gap truncation may prevent an event from being detected at all, so incomplete
   candidate counts are not a census of every possible truncated event.

For each candidate, amplitude `A` is the baseline-subtracted signal at the peak.
Search inside that peak's prominence bases for the nearest rising crossings before
the peak and the first falling crossings after it. Crossings are linearly interpolated
between samples. This interpolation does not undo preprocessing or recover faster
kinetics. A crossing absent within those bases makes the full event incomplete.

| Metric | Definition |
|---|---|
| Amplitude | Original NE at peak minus local baseline at peak |
| Duration | Falling 20% crossing minus rising 20% crossing |
| Rising slope | `0.6*A / (rising80_time - rising20_time)` |
| Decay slope | `0.6*A / (falling20_time - falling80_time)`, positive magnitude |

Slopes are secants between crossings, **not** regression fits and **not** T1/2.
Keep both crossing times so another convention can be implemented transparently.
NE amplitude/slope units refer to the **processed percentage delta-F/F trace**;
they are not NE concentration or direct secretion/clearance rates.

## Recording-start QC for the proposal cohort

Three supplied recordings begin with a large, repeatable negative-to-positive NE
excursion during roughly the first second. In two, the saved label is Active Wake,
so the artifact creates a complete high-amplitude candidate and contaminates the
first fixed spectral window. The proposal configuration therefore excludes, without
rewriting any MAT data, candidate events whose peak is in the first 15 seconds of a
recording and spectral windows that would start there. Those candidates remain in
`events.csv` with `recording_start_qc_excluded=true`; the configuration and output
quality table record the exclusion. Fifteen seconds is a deliberately conservative,
cohort-wide pilot rule that removes the affected 15-second window. The unexcluded
run remains an inspectable sensitivity output, not deleted data.

## State boundaries and retained events

The peak supplies the candidate's state. All candidates remain in `events.csv`,
including other/unscored states. For the PI-directed proposal analysis,
`assignment="peak"` includes every complete Active/Quiet candidate in the state at
its peak, even when its 20%-to-20% support spans another state. This answers a
peak-state question, not a pure within-state kinetics question, and is necessary to
avoid discarding most short-state candidates.

`assignment="contained"` remains available as a sensitivity analysis: it includes
only complete events whose 20%-to-20% support, including interpolation-bracketing
samples, lies in the same Active/Quiet state. The contained rule can select longer
bouts/events differently between states, so the proposal report will retain the
crossing counts and the eligibility rule beside each summary. Whichever rule is used
must be shared across all files being pooled. `baseline_edge` flags when the baseline
window extends beyond a finite stretch; those events remain eligible if otherwise
complete. Upstream noncausal smoothing also mixes signal across state boundaries,
even when saved sample labels are contained. No boundary deconvolution or guard
interval is applied in this draft.

## Aggregation and missingness

Pool eligible event rows across a mouse's files and take the median for each metric.
Do **not** average file medians. Spectra pool by window count, not file count or bout
count. Longer bouts therefore contribute more spectral information; this estimates
a typical analyzed time period, not a typical bout. Mice remain the independent rows;
this package does not perform group hypothesis tests or treat events as independent mice.

No events => metric NaN and count zero. No eligible spectral windows => spectral
metric NaN, status `no_eligible_windows`, and count zero. Spectrum disabled => status
`not_configured`. Never replace missing values with zero when comparing groups.
There is no inferential uncertainty estimate or minimum-event-count gate yet; the
counts expose the amount of evidence, including single-event summaries.

Same signals, labels, configuration and software environment yield deterministic
tables. Input order is sorted before aggregation. Only run timestamps and input file
metadata can change between repeat executions. Duplicate IDs/configuration mixtures
are rejected; IDs do not detect renamed copies or overlapping recording chunks.

## Sources and preprocessing provenance

- [SciPy periodogram](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.periodogram.html): density scaling and windowing.
- [SciPy find_peaks](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html): prominence, minimum distance and edge behavior.
- [MATLAB filtfilt](https://www.mathworks.com/help/signal/ref/filtfilt.html): zero-phase operation and squared filter magnitude response.
- [MATLAB zero padding](https://www.mathworks.com/help/signal/ug/amplitude-estimation-and-zero-padding.html): padding does not improve frequency resolution.
- Local `C:\Users\yzhao\matlab_projects\preprocess_sleep_data\preprocess_sleep_data.m`, lines 247–274, inspected 2026-09-14: fitted 405 control, percentage delta-F/F, 1,000-point smoothing, factor-100 downsampling confirmed by user. `preprocess_sirenia.m`, lines 187–206, matches these steps.
