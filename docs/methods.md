# Metric definitions and pilot choices

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

## State boundaries and retained events

The peak supplies the candidate's state. All candidates remain in `events.csv`,
including other/unscored states. The default `assignment="contained"` includes only
complete events whose 20%-to-20% support, including interpolation-bracketing samples,
lies in the same Active/Quiet state. Crossing events are flagged and excluded from
the primary state summaries, without cutting their waveforms or durations.

`assignment="peak"` explicitly allows complete crossing events to contribute to the
peak's state. That result describes NE signal elevation episodes peaking in a state, including portions
outside it. It is a sensitivity-analysis option, not equivalent to pure within-state
kinetics. Whichever rule is used must be shared across all files being pooled.

The conservative contained rule can select longer bouts/events differently between
states. Report retained fractions and inspect crossing counts before interpreting
differences. `baseline_edge` flags when the baseline window extends beyond a finite
stretch; those events remain eligible if otherwise complete. Upstream noncausal
smoothing also mixes signal across state boundaries, even when saved sample labels
are contained. No boundary deconvolution or guard interval is applied in this draft.

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
