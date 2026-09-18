"""Create static, GitHub-renderable figures for the first real-file pilot report."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wake_ne_analysis.io import load_recording


STATE_NAMES = {"active_wake": "Active Wake", "quiet_wake": "Quiet Wake"}
STATE_COLORS = {"active_wake": "#1769aa", "quiet_wake": "#d95f02", "other": "#d9d9d9"}
STATE_FILLS = {
    "active_wake": "rgba(23, 105, 170, 0.20)",
    "quiet_wake": "rgba(217, 95, 2, 0.20)",
    "other": "rgba(150, 150, 150, 0.20)",
}


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Render preliminary-report PNG figures from analysis and preflight tables."
    )
    parser.add_argument("--analysis", required=True, type=Path, help="Analysis output directory.")
    parser.add_argument("--preflight", required=True, type=Path, help="Validation output directory.")
    parser.add_argument("--mat", required=True, type=Path, help="Source MAT file for trace examples.")
    parser.add_argument("--output", required=True, type=Path, help="New or empty figure directory.")
    parser.add_argument("--overwrite", action="store_true", help="Replace prior figures in --output.")
    return parser.parse_args(argv)


def _save(figure, path: Path) -> None:
    figure.write_image(path, format="png", width=1500, height=850, scale=2)


def _event_rows(events: pd.DataFrame, state: str) -> pd.DataFrame:
    return events.loc[events.state == state].copy()


def summary_figure(subjects: pd.DataFrame):
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    row = subjects.iloc[0]
    states = ["active_wake", "quiet_wake"]
    labels = [STATE_NAMES[state] for state in states]
    colors = [STATE_COLORS[state] for state in states]
    candidates = [row[f"{state}_n_events_detected"] for state in states]
    retained = [row[f"{state}_n_events_used"] for state in states]
    retained_pct = [100 * row[f"{state}_event_retained_fraction"] for state in states]

    table_rows = [
        ("Labeled time (s)", "total_seconds", ".0f"),
        ("Wake bouts", "n_bouts", ".0f"),
        ("Candidate events", "n_events_detected", ".0f"),
        ("Retained events", "n_events_used", ".0f"),
        ("Amplitude median (percentage points)", "amplitude_median", ".3f"),
        ("Duration median (s)", "duration_seconds_median", ".2f"),
        ("Rise slope median (percentage points/s)", "rise_slope_median", ".3f"),
        ("Decay slope median (percentage points/s)", "decay_slope_median", ".3f"),
    ]
    metrics, active, quiet = [], [], []
    for display, suffix, fmt in table_rows:
        metrics.append(display)
        active.append(format(row[f"active_wake_{suffix}"], fmt))
        quiet.append(format(row[f"quiet_wake_{suffix}"], fmt))

    figure = make_subplots(
        rows=1,
        cols=2,
        column_widths=[0.43, 0.57],
        specs=[[{"type": "xy"}, {"type": "table"}]],
        subplot_titles=("Candidate events and conservative retention", "Descriptive summary"),
    )
    figure.add_trace(
        go.Bar(name="Candidates", x=labels, y=candidates, marker_color="#a6bddb", text=candidates, textposition="outside"),
        row=1,
        col=1,
    )
    figure.add_trace(
        go.Bar(
            name="Complete and contained",
            x=labels,
            y=retained,
            marker_color=colors,
            text=[f"{value} ({pct:.0f}%)" for value, pct in zip(retained, retained_pct)],
            textposition="outside",
        ),
        row=1,
        col=1,
    )
    figure.add_trace(
        go.Table(
            header={"values": ["Metric", "Active Wake", "Quiet Wake"], "fill_color": "#334e68", "font": {"color": "white", "size": 14}},
            cells={"values": [metrics, active, quiet], "fill_color": [["#f7fbff"] * len(metrics), ["#e8f1fb"] * len(metrics), ["#fff0e6"] * len(metrics)], "align": ["left", "center", "center"], "font": {"size": 13}, "height": 32},
        ),
        row=1,
        col=2,
    )
    figure.update_layout(
        barmode="group",
        template="plotly_white",
        title="Single-recording pilot: descriptive Active/Quiet Wake results",
        legend={"orientation": "h", "y": -0.12},
        margin={"l": 55, "r": 30, "t": 90, "b": 85},
    )
    figure.update_yaxes(title="number of detected peaks", rangemode="tozero", row=1, col=1)
    return figure


def coverage_figure(coverage: pd.DataFrame, bouts: pd.DataFrame):
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    figure = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("Fixed-window spectral coverage", "Distribution of continuous wake-bout durations"),
    )
    for state, display in STATE_NAMES.items():
        subset = coverage.loc[coverage.state == state].sort_values("window_seconds")
        figure.add_trace(
            go.Scatter(
                x=subset.window_seconds,
                y=100 * subset.coverage_fraction,
                mode="lines+markers+text",
                text=[str(int(value)) for value in subset.n_windows],
                textposition="top center",
                name=display,
                line={"color": STATE_COLORS[state], "width": 3},
                marker={"size": 9},
                hovertemplate="%{x:g} s window: %{y:.1f}% coverage<br>%{text} usable windows<extra></extra>",
            ),
            row=1,
            col=1,
        )
        duration = bouts.loc[bouts.state == state, "duration_seconds"]
        figure.add_trace(
            go.Violin(
                x=[display] * len(duration),
                y=duration,
                name=display,
                legendgroup=display,
                showlegend=False,
                line_color=STATE_COLORS[state],
                fillcolor=STATE_COLORS[state],
                opacity=0.65,
                box_visible=True,
                meanline_visible=True,
                points="all",
            ),
            row=1,
            col=2,
        )
    figure.update_xaxes(title="window duration (seconds)", row=1, col=1)
    figure.update_yaxes(title="available state time covered (%)", range=[0, 100], row=1, col=1)
    figure.update_yaxes(title="bout duration (seconds; log scale)", type="log", row=1, col=2)
    figure.update_layout(
        template="plotly_white",
        title="Why the illustrative 120-second slow-spectrum analysis is not usable here",
        margin={"l": 65, "r": 30, "t": 90, "b": 70},
    )
    return figure


def _state_key(labels: np.ndarray) -> np.ndarray:
    return np.where(labels == 4, "active_wake", np.where(labels == 5, "quiet_wake", "other"))


def _runs(values: np.ndarray):
    start = 0
    for index in range(1, len(values) + 1):
        if index == len(values) or values[index] != values[start]:
            yield start, index, values[start]
            start = index


def _state_spans(recording, start: float, end: float):
    labels = recording.labels
    seconds = np.arange(len(labels), dtype=float) + recording.start_time
    selected = (seconds < end) & (seconds + 1 > start)
    keys = _state_key(labels[selected])
    selected_seconds = seconds[selected]
    for run_start, run_end, state in _runs(keys):
        x0 = max(start, selected_seconds[run_start])
        x1 = min(end, selected_seconds[run_end - 1] + 1)
        yield x0, x1, state


def _trace_panel(figure, recording, event: pd.Series, column: int, title: str) -> None:
    import plotly.graph_objects as go

    start = float(event.onset20_seconds - 25)
    end = float(event.offset20_seconds + 25)
    time = recording.start_time + np.arange(recording.ne.size) / recording.fs
    in_view = (time >= start) & (time <= end)
    y_values = recording.ne[in_view]
    y_min = float(np.min(y_values))
    y_max = float(np.max(y_values))
    y_pad = max((y_max - y_min) * 0.08, 0.1)
    for x0, x1, state in _state_spans(recording, start, end):
        figure.add_trace(
            go.Scatter(
                x=[x0, x1, x1, x0, x0],
                y=[y_min - y_pad, y_min - y_pad, y_max + y_pad, y_max + y_pad, y_min - y_pad],
                mode="lines",
                fill="toself",
                fillcolor=STATE_FILLS[state],
                line={"width": 0},
                hoverinfo="skip",
                showlegend=False,
            ),
            row=1,
            col=column,
        )
    figure.add_trace(
        go.Scatter(x=time[in_view], y=recording.ne[in_view], mode="lines", line={"color": "#202020", "width": 2}, showlegend=False),
        row=1,
        col=column,
    )
    peak_value = recording.ne[np.argmin(np.abs(time - event.peak_seconds))]
    figure.add_trace(
        go.Scatter(
            x=[event.peak_seconds],
            y=[peak_value],
            mode="markers",
            marker={"color": STATE_COLORS[event.state], "size": 11, "line": {"color": "white", "width": 1}},
            showlegend=False,
        ),
        row=1,
        col=column,
    )
    for value, label, color in (
        (event.onset20_seconds, "20% rise", "#7b3294"),
        (event.offset20_seconds, "20% fall", "#7b3294"),
    ):
        figure.add_vline(x=value, line_dash="dash", line_color=color, line_width=2, row=1, col=column)
        figure.add_annotation(x=value, y=0.02, xref="x" if column == 1 else f"x{column}", yref="paper", text=label, showarrow=False, textangle=-90, font={"size": 11, "color": color})
    figure.add_annotation(
        x=(event.onset20_seconds + event.offset20_seconds) / 2,
        y=0.92,
        xref="x" if column == 1 else f"x{column}",
        yref="paper",
        text=title,
        showarrow=False,
        font={"size": 12, "color": "#333"},
    )
    figure.update_xaxes(title="recording time (seconds)", range=[start, end], row=1, col=column)
    figure.update_yaxes(title="processed NE (percentage delta-F/F)" if column == 1 else None, row=1, col=column)


def boundary_figure(events: pd.DataFrame, mat_path: Path):
    from plotly.subplots import make_subplots

    crossing = events.loc[(events.state == "quiet_wake") & events.complete & events.crosses_state].iloc[0]
    contained = events.loc[(events.state == "quiet_wake") & events.eligible].iloc[0]
    recording = load_recording(mat_path, "unverified_35", "35_app13_groundtruth")
    figure = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("A. Quiet-peak event excluded because its 20% support crosses a state label", "B. Quiet event retained because its 20% support is entirely within Quiet Wake"),
    )
    _trace_panel(figure, recording, crossing, 1, "Peak: Quiet Wake; support: %.1f–%.1f s" % (crossing.onset20_seconds, crossing.offset20_seconds))
    _trace_panel(figure, recording, contained, 2, "Peak: Quiet Wake; support: %.1f–%.1f s" % (contained.onset20_seconds, contained.offset20_seconds))
    figure.update_layout(
        template="plotly_white",
        title="Boundary-crossing rule on the processed NE trace (blue = Active, orange = Quiet, gray = other)",
        margin={"l": 75, "r": 30, "t": 115, "b": 80},
    )
    return figure


def main(argv=None) -> int:
    args = parse_args(argv)
    if args.output.exists() and any(args.output.iterdir()) and not args.overwrite:
        raise ValueError(f"Output directory must be new or empty: {args.output}")
    args.output.mkdir(parents=True, exist_ok=True)
    subjects = pd.read_csv(args.analysis / "subjects.csv")
    events = pd.read_csv(args.analysis / "events.csv")
    coverage = pd.read_csv(args.preflight / "coverage.csv")
    bouts = pd.read_csv(args.preflight / "bouts.csv")
    _save(summary_figure(subjects), args.output / "single_file_summary.png")
    _save(coverage_figure(coverage, bouts), args.output / "spectral_coverage_and_bouts.png")
    _save(boundary_figure(events, args.mat), args.output / "boundary_crossing_examples.png")
    print(f"Wrote figures to {args.output}")
    return 0


if __name__ == "__main__":
    main()
