"""Render static figures for the executive cohort preliminary report."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wake_ne_analysis.io import load_recording


STATE_NAMES = {"active_wake": "Active Wake", "quiet_wake": "Quiet Wake"}
# Keep the state colors aligned with the upstream sleep_scoring application.
STATE_COLORS = {"active_wake": "#E69F00", "quiet_wake": "#56B4E9"}
STATE_FILL_COLORS = {
    "active_wake": "rgba(230,159,0,0.24)",
    "quiet_wake": "rgba(86,180,233,0.28)",
    "other": "rgba(150,150,150,0.18)",
}
PEAK_EXAMPLE_SEED = 20260916
MIN_EXAMPLE_QUIET_SECONDS = 10
MIN_EXAMPLE_ACTIVE_SECONDS = 5
METRICS = [
    ("amplitude_median", "Episode amplitude", "percentage points"),
    ("duration_seconds_median", "Episode duration", "seconds"),
    ("rise_slope_median", "20–80% rise slope", "percentage points/s"),
    ("decay_slope_median", "20–80% decay slope", "percentage points/s"),
    ("band_power", "15 s band power", "percentage points²"),
    ("dominant_frequency_hz", "Frequency maximum", "Hz"),
]


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis", required=True, type=Path, help="Peak-state analysis output.")
    parser.add_argument("--preflight", required=True, type=Path, help="Matching preflight output.")
    parser.add_argument("--mat", required=True, type=Path, help="MAT file for the peak-assignment example.")
    parser.add_argument(
        "--example-recording-id",
        default="unverified_35_updated",
        help="Recording ID from events.csv used for the peak-state example.",
    )
    parser.add_argument(
        "--example-mouse-id",
        default="unverified_35",
        help="Mouse/source ID paired with --mat for the peak-state example.",
    )
    parser.add_argument(
        "--peak-example-seed",
        type=int,
        default=PEAK_EXAMPLE_SEED,
        help="Deterministic seed for choosing among eligible Quiet-Wake examples.",
    )
    parser.add_argument("--output", required=True, type=Path, help="New or empty figure directory.")
    return parser.parse_args(argv)


def _save(figure, path: Path, height: int):
    figure.write_image(path, format="png", width=1800, height=height, scale=2)


def _identified(subjects: pd.DataFrame) -> pd.DataFrame:
    return subjects.loc[subjects.mouse_id != "unverified_35"].copy()


def _paired_stats(subjects: pd.DataFrame, metric: str):
    active = subjects.set_index("mouse_id")[f"active_wake_{metric}"]
    quiet = subjects.set_index("mouse_id")[f"quiet_wake_{metric}"]
    paired = pd.DataFrame({"active": active, "quiet": quiet}).dropna()
    difference = paired.active - paired.quiet
    if metric == "dominant_frequency_hz" and difference.eq(0).all():
        return paired, None
    return paired, float(wilcoxon(difference, alternative="two-sided", method="auto").pvalue)


def metric_figure(subjects: pd.DataFrame):
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    figure = make_subplots(rows=2, cols=3, subplot_titles=[label for _, label, _ in METRICS])
    for index, (metric, label, unit) in enumerate(METRICS):
        row, column = divmod(index, 3)
        row += 1
        column += 1
        paired, p_value = _paired_stats(subjects, metric)
        for mouse_id, values in paired.iterrows():
            figure.add_trace(
                go.Scatter(
                    x=[STATE_NAMES["active_wake"], STATE_NAMES["quiet_wake"]],
                    y=[values.active, values.quiet],
                    mode="lines+markers",
                    line={"color": "#9aa5b1", "width": 1.5},
                    marker={"size": 9, "color": [STATE_COLORS["active_wake"], STATE_COLORS["quiet_wake"]]},
                    customdata=[[mouse_id], [mouse_id]],
                    hovertemplate="%{customdata[0]}<br>%{x}: %{y:.4g}<extra></extra>",
                    showlegend=False,
                ),
                row=row,
                col=column,
            )
        annotation = (
            "Not tested: every maximum is 0.20 Hz,\nthe lower band edge"
            if p_value is None
            else f"Paired Wilcoxon, n = {len(paired)}, p = {p_value:.3g} (not significant)"
        )
        figure.add_annotation(
            x=0.5,
            y=0.98,
            xref="x domain" if index == 0 else f"x{index + 1} domain",
            yref="y domain" if index == 0 else f"y{index + 1} domain",
            text=annotation,
            showarrow=False,
            align="center",
            bgcolor="rgba(255,255,255,0.82)",
            bordercolor="#cbd2d9",
            font={"size": 11, "color": "#334e68"},
        )
        figure.update_yaxes(title=unit, row=row, col=column)
        if metric == "dominant_frequency_hz":
            figure.update_yaxes(range=[0.18, 0.22], dtick=0.01, row=row, col=column)
    figure.update_layout(
        template="plotly_white",
        title="Preliminary cohort: paired mouse summaries (identified mice only)",
        height=960,
        margin={"l": 70, "r": 30, "t": 95, "b": 70},
    )
    return figure


def coverage_figure(coverage: pd.DataFrame):
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    coverage = coverage.loc[coverage.window_seconds.isin([15, 20])].copy()
    coverage = (
        coverage.groupby(["mouse_id", "state", "window_seconds"], as_index=False)
        .agg(n_windows=("n_windows", "sum"))
    )
    order = ["mouse1", "mouse3", "mouse5", "mouse7", "unverified_35"]
    figure = make_subplots(rows=1, cols=2, subplot_titles=("Active Wake", "Quiet Wake"))
    for column, state in enumerate(("active_wake", "quiet_wake"), start=1):
        for seconds, opacity, pattern in ((15, 1.0, ""), (20, 0.65, "/")):
            data = coverage.loc[(coverage.state == state) & (coverage.window_seconds == seconds)]
            values = data.set_index("mouse_id").reindex(order).n_windows.fillna(0)
            figure.add_trace(
                go.Bar(
                    x=[name.replace("mouse", "Mouse ").replace("unverified_35", "Unverified 35") for name in order],
                    y=values,
                    name=f"{seconds} s windows",
                    marker={
                        "color": STATE_COLORS[state],
                        "opacity": opacity,
                        "line": {"color": "#52606d", "width": 1 if seconds == 20 else 0},
                        "pattern": {"shape": pattern, "fgcolor": "#52606d"},
                    },
                    text=values.astype(int),
                    textposition="outside",
                    showlegend=column == 1,
                ),
                row=1,
                col=column,
            )
        figure.update_yaxes(title="eligible fixed windows", rangemode="tozero", row=1, col=column)
    figure.update_layout(
        barmode="group",
        template="plotly_white",
        title="Why 15 seconds is the common spectral fallback (orange = Active; light blue = Quiet)",
        legend={"orientation": "h", "y": -0.18},
        height=520,
        margin={"l": 70, "r": 30, "t": 95, "b": 95},
    )
    return figure


def _state_spans(recording, left: float, right: float):
    labels = recording.labels
    state = np.where(labels == 4, "active_wake", np.where(labels == 5, "quiet_wake", "other"))
    start = recording.start_time + np.arange(labels.size)
    chosen = (start < right) & (start + 1 > left)
    start, state = start[chosen], state[chosen]
    first = 0
    for index in range(1, len(state) + 1):
        if index == len(state) or state[index] != state[first]:
            yield max(left, start[first]), min(right, start[index - 1] + 1), state[first]
            first = index


def _seconds_in_state(recording, left: float, right: float, state_label: int) -> float:
    """Return displayed whole-label seconds for candidate selection only."""
    start = recording.start_time + np.arange(recording.labels.size)
    overlap = np.maximum(0, np.minimum(start + 1, right) - np.maximum(start, left))
    return float(overlap[recording.labels == state_label].sum())


def choose_peak_example(events: pd.DataFrame, recording, recording_id: str, seed: int):
    """Pick a seeded Quiet-Wake peak example that visibly includes both wake states."""
    candidates = events.loc[
        (events.recording_id == recording_id)
        & (events.state == "quiet_wake")
        & events.complete
        & events.crosses_state
        & ~events.recording_start_qc_excluded
    ].copy()
    if candidates.empty:
        raise ValueError(f"No eligible Quiet-Wake crossing events for {recording_id!r}.")

    candidates["display_left"] = candidates.onset20_seconds - 20
    candidates["display_right"] = candidates.offset20_seconds + 20
    candidates["quiet_seconds_shown"] = [
        _seconds_in_state(recording, left, right, 5)
        for left, right in zip(candidates.display_left, candidates.display_right)
    ]
    candidates["active_seconds_shown"] = [
        _seconds_in_state(recording, left, right, 4)
        for left, right in zip(candidates.display_left, candidates.display_right)
    ]
    candidates = candidates.loc[
        (candidates.quiet_seconds_shown >= MIN_EXAMPLE_QUIET_SECONDS)
        & (candidates.active_seconds_shown >= MIN_EXAMPLE_ACTIVE_SECONDS)
    ].sort_values(["peak_seconds", "onset20_seconds"], kind="stable")
    if candidates.empty:
        raise ValueError(
            "No peak-state example shows the required Quiet- and Active-Wake context "
            f"({MIN_EXAMPLE_QUIET_SECONDS} s Quiet; {MIN_EXAMPLE_ACTIVE_SECONDS} s Active)."
        )
    return candidates.iloc[np.random.default_rng(seed).integers(len(candidates))]


def peak_assignment_figure(events: pd.DataFrame, mat_path: Path, mouse_id: str, recording_id: str, seed: int):
    import plotly.graph_objects as go

    recording = load_recording(mat_path, mouse_id, recording_id)
    chosen = choose_peak_example(events, recording, recording_id, seed)
    left, right = float(chosen.display_left), float(chosen.display_right)
    time = recording.start_time + np.arange(recording.ne.size) / recording.fs
    shown = (time >= left) & (time <= right)
    values = recording.ne[shown]
    low, high = float(values.min()), float(values.max())
    pad = max((high - low) * 0.08, 0.1)
    figure = go.Figure()
    for start, stop, state in _state_spans(recording, left, right):
        label = STATE_NAMES.get(state) if stop - start >= 3 else None
        span_kwargs = {
            "x0": start,
            "x1": stop,
            "fillcolor": STATE_FILL_COLORS[state],
            "line_width": 0,
            "layer": "below",
        }
        if label:
            span_kwargs.update(
                annotation_text=label,
                annotation_position="top left",
                annotation_font={"size": 11, "color": "#334e68"},
            )
        figure.add_vrect(
            **span_kwargs,
        )
    figure.add_trace(go.Scatter(x=time[shown], y=values, mode="lines", name="processed NE", line={"color": "#1f2933", "width": 2}))
    figure.add_trace(
        go.Scatter(
            x=[chosen.peak_seconds],
            y=[recording.ne[np.argmin(np.abs(time - chosen.peak_seconds))]],
            mode="markers",
            name="Quiet-Wake peak",
            marker={"color": STATE_COLORS["quiet_wake"], "size": 11},
        )
    )
    for value, label in (
        (chosen.onset20_seconds, "rising 20%"),
        (chosen.rise80_seconds, "rising 80%"),
        (chosen.decay80_seconds, "falling 80%"),
        (chosen.offset20_seconds, "falling 20%"),
    ):
        figure.add_vline(x=value, line_dash="dash", line_color="#7b3294", line_width=1.5)
        figure.add_annotation(x=value, y=high + pad * 0.25, text=label, showarrow=False, textangle=-90, font={"size": 11, "color": "#7b3294"})
    figure.update_layout(
        template="plotly_white",
        title="Peak-state attribution: a Quiet-Wake peak with visibly labelled wake-state context",
        xaxis_title="recording time (seconds)",
        yaxis_title="processed NE (percentage delta-F/F)",
        yaxis_range=[low - pad, high + pad],
        legend={"orientation": "h", "y": -0.2},
        height=600,
        margin={"l": 80, "r": 40, "t": 95, "b": 100},
    )
    figure.add_annotation(
        x=0.5,
        y=-0.31,
        xref="paper",
        yref="paper",
        text=(
            "Orange = Active Wake; light blue = Quiet Wake; gray = other state. "
            "Purple lines show the crossings used for duration and 20–80% slopes."
        ),
        showarrow=False,
        font={"size": 12, "color": "#52606d"},
    )
    return figure


def main(argv=None):
    args = parse_args(argv)
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError(f"Output directory must be new or empty: {args.output}")
    args.output.mkdir(parents=True, exist_ok=True)
    subjects = _identified(pd.read_csv(args.analysis / "subjects.csv"))
    events = pd.read_csv(args.analysis / "events.csv")
    coverage = pd.read_csv(args.preflight / "coverage.csv")
    _save(metric_figure(subjects), args.output / "cohort_metric_comparisons.png", 960)
    _save(coverage_figure(coverage), args.output / "spectral_window_coverage.png", 520)
    _save(
        peak_assignment_figure(
            events,
            args.mat,
            args.example_mouse_id,
            args.example_recording_id,
            args.peak_example_seed,
        ),
        args.output / "peak_state_assignment_example.png",
        600,
    )
    print(f"Wrote figures to {args.output}")


if __name__ == "__main__":
    main()
