# PI meeting agenda: Active/Quiet Wake NE pilot

**Goal:** leave with explicit rules for the first analyzable cohort. The pipeline
already protects against silent relabeling, stitching, and event-level
pseudoreplication; these decisions determine which scientifically valid analysis it
should report.

| Priority | Decision needed | Current default and why | Evidence from the first file |
|---:|---|---|---|
| 1 | Boundary assignment | **PI direction:** assign every complete episode to the final Active/Quiet state at its peak, even when 20%-to-20% support crosses a label boundary. Retain crossing counts and a contained-event sensitivity result. | 15/35 Active and 21/25 Quiet candidates crossed a boundary in the initial file; peak assignment avoids discarding most short-state episodes. |
| 2 | Short-window spectrum | **PI direction:** use a common short interval to assess proposal promise. Preflight 20 s first (0.15–0.25 Hz); use 15 s (0.20–0.30 Hz) only if needed for common coverage. Do not stitch bouts or use state-specific settings. | The initial file had 28 Quiet 15 s windows but only 6 at 30 s; the full cohort preflight will determine the final plot setting. |
| 3 | Does “20–80% slope” replace rising/decay T₁/₂, and how is duration defined? | The current draft reports 20–80% secant slopes and a separate 20%-rise-to-20%-fall duration. **This duration rule was not confirmed by the PI.** | T₁/₂ is a time-to-half-amplitude measure; a 20–80% slope is a middle-60%-amplitude rate. They are not interchangeable. |
| 4 | Are the baseline and prominence choices visually acceptable on representative real traces? How should obvious stored artifacts be handled upstream? | Centered 60 s 20th-percentile baseline; ≥0.5 percentage-point prominence and one-second peak separation. Flag, never silently rewrite, suspect input samples. | The first stored NE sample is −99.6 percentage points and needs provenance/QC confirmation. |
| 5 | What is the biological grouping and independent unit? | One row per mouse; pool events within mouse and files within mouse. Do not treat events/files as biological replicates. | The current MAT lacks embedded mouse/session/condition/circadian metadata. |

## Suggested meeting sequence (30 minutes)

1. **Five minutes — scope and pilot result.** Present the
   [historical single-recording report](pilot_report.md), emphasizing that it is a
   pipeline demonstration, not a state-effect claim. Then use the
   [preliminary cohort report](preliminary_report.md) for the current result.
2. **Ten minutes — inspect the proposal result.** Review peak-assigned events,
   boundary-crossing counts, and short-window coverage without treating files or
   events as independent mice.
3. **Ten minutes — confirm spectrum target.** Review the cohort coverage figure and
   select the 20 s primary setting or 15 s fallback.
4. **Five minutes — finalize definitions and cohort metadata.** Ask whether 20–80%
   slopes replace T₁/₂, define episode duration separately, and confirm detector QC
   and study grouping.

## Decision record to complete after the meeting

- Boundary policy: `peak` (PI-directed proposal analysis); contained sensitivity retained
- Guard interval around label changes, if any: `_____ seconds`
- Does 20–80% slope replace rising/decay T₁/₂? `yes / no / report both`
- Duration definition, separate from slope: `_____`
- 20–80% slope method: `secant` / `regression`
- Spectrum window: `20 / 15 / other` seconds; band: `_____–_____ Hz`; adequacy threshold: `_____`
- Artifact/QC action: `_____`
- Required manifest fields: `mouse ID / session / condition / circadian time / _____`
