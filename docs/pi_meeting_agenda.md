# PI meeting agenda: Active/Quiet Wake NE pilot

**Goal:** leave with explicit rules for the first analyzable cohort. The pipeline
already protects against silent relabeling, stitching, and event-level
pseudoreplication; these decisions determine which scientifically valid analysis it
should report.

| Priority | Decision needed | Current default and why | Evidence from the first file |
|---:|---|---|---|
| 1 | When an NE signal elevation episode spans a label transition, should it be included only if fully contained in one state, or assigned by its peak state? | Fully contained for the primary estimate, because its 20%-to-20% support is pure-state. Peak-state assignment can be a labelled sensitivity analysis. | 15/35 Active and 21/25 Quiet candidates cross a boundary; the choice materially changes the usable event set. |
| 2 | What frequency range is biologically required for the spectral question? Is a faster common band acceptable if slow Quiet-Wake windows are not? | No spectrum until one common window/band is chosen for all states and mice. Do not stitch bouts or use state-specific windows. | Quiet has 0 120 s windows, 1 60 s window, 6 30 s windows, and 28 15 s windows. |
| 3 | Confirm the NE signal elevation-episode definitions: should duration be 20%-rise to 20%-fall, and should 20–80% slopes be secants or regressions? | 20%-to-20% duration; 20–80% secant slopes. These are inspectable and match the prior request for 20–80% slopes. | Definitions affect the magnitude but do not alter labels or source waveform. |
| 4 | Are the baseline and prominence choices visually acceptable on representative real traces? How should obvious stored artifacts be handled upstream? | Centered 60 s 20th-percentile baseline; ≥0.5 percentage-point prominence and one-second peak separation. Flag, never silently rewrite, suspect input samples. | The first stored NE sample is −99.6 percentage points and needs provenance/QC confirmation. |
| 5 | What is the biological grouping and independent unit? | One row per mouse; pool events within mouse and files within mouse. Do not treat events/files as biological replicates. | The current MAT lacks embedded mouse/session/condition/circadian metadata. |

## Suggested meeting sequence (30 minutes)

1. **Five minutes — scope and pilot result.** Present the
   [single-recording report](preliminary_report.md), emphasizing that it is a
   pipeline demonstration, not a state-effect claim.
2. **Ten minutes — boundary rule.** Walk through the paired trace figure; select the
   primary rule and decide whether peak-state results should be reported only as a
   sensitivity analysis.
3. **Ten minutes — spectrum target.** Review the coverage figure; choose a required
   slow band, a faster common band, or a data-collection threshold before spectra are
   reported.
4. **Five minutes — finalize definitions and cohort metadata.** Confirm duration /
   slope convention, detector QC process, and required manifest fields.

## Decision record to complete after the meeting

- Boundary policy: `contained` / `peak` / another defined rule
- Guard interval around label changes, if any: `_____ seconds`
- Duration definition: `_____`
- 20–80% slope method: `secant` / `regression`
- Spectrum window: `_____ seconds`; band: `_____–_____ Hz`; adequacy threshold: `_____`
- Artifact/QC action: `_____`
- Required manifest fields: `mouse ID / session / condition / circadian time / _____`
