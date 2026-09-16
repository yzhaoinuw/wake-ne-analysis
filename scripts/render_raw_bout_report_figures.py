"""Render figures for the exploratory zero-referenced raw-bout report."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wake_ne_analysis.io import load_recording


STATE_NAMES = {"active_wake": "Active Wake", "quiet_wake": "Quiet Wake"}
STATE_COLORS = {"active_wake": "#E69F00", "quiet_wake": "#56B4E9"}
METRICS = [
    ("raw_peak", "Zero-referenced peak", "processed NE (percentage delta-F/F)"),
    ("duration_seconds", "Peak-assigned NE-episode width", "seconds"),
    ("rise_slope", "Peak-assigned 20–80% rise slope", "percentage points/s"),
    ("decay_slope", "Peak-assigned 20–80% decay slope", "percentage points/s"),
]
SPECTRAL_METRICS = [
    ("band_power", "15 s 0.20–0.30 Hz band power", "percentage points²"),
    ("dominant_frequency_hz", "15 s frequency maximum", "Hz"),
]
RAW_PEAK_EXAMPLE_RECORDING_ID = "part1_mouse5_day2_Mouse5_220525_2025-05-22_19-56-49-015"
RAW_PEAK_EXAMPLE_SEED = 20260916
MIN_EXAMPLE_QUIET_SECONDS = 10
MIN_EXAMPLE_ACTIVE_SECONDS = 4
MAX_EXAMPLE_CONTEXT_PEAK_EXCESS = 0.05


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis", required=True, type=Path, help="Raw-bout analysis output directory.")
    parser.add_argument("--output", required=True, type=Path, help="New or empty figure directory.")
    return parser.parse_args(argv)


def _save(figure, path: Path):
    figure.write_image(path, format="png", width=1800, height=1280, scale=2)


def _state_spans(recording, left: float, right: float):
    """Yield clipped one-second score spans for the illustrative raw-bout trace."""
    state = np.where(recording.labels == 4, "active_wake", np.where(recording.labels == 5, "quiet_wake", "other"))
    start = recording.start_time + np.arange(recording.labels.size)
    chosen = (start < right) & (start + 1 > left)
    start, state = start[chosen], state[chosen]
    first = 0
    for index in range(1, len(state) + 1):
        if index == len(state) or state[index] != state[first]:
            yield max(left, start[first]), min(right, start[index - 1] + 1), state[first]
            first = index


def _seconds_in_state(recording, left: float, right: float, state_label: int) -> float:
    start = recording.start_time + np.arange(recording.labels.size)
    overlap = np.maximum(0, np.minimum(start + 1, right) - np.maximum(start, left))
    return float(overlap[recording.labels == state_label].sum())


def choose_raw_peak_example(bouts: pd.DataFrame, recording_id: str, seed: int):
    """Choose a visible Quiet-Wake literal-bout maximum with crossing context."""
    candidates = bouts.loc[
        (bouts.recording_id == recording_id)
        & (bouts.state == "quiet_wake")
        & bouts.complete_shape
        & bouts.crosses_state_boundary
        & (bouts.bout_duration_seconds >= 5)
        & (bouts.bout_duration_seconds <= 60)
        & (bouts.duration_seconds >= 5)
        & (bouts.duration_seconds <= 100)
    ].copy()
    if candidates.empty:
        raise ValueError(f"No eligible raw-bout peak examples for {recording_id!r}.")
    source = candidates.iloc[0]
    recording = load_recording(Path(source.mat_path), source.mouse_id, source.recording_id)
    candidates["display_left"] = np.minimum(candidates.rise20_seconds, candidates.onset_seconds) - 20
    candidates["display_right"] = np.maximum(candidates.decay20_seconds, candidates.offset_seconds) + 20
    candidates["quiet_seconds_shown"] = [
        _seconds_in_state(recording, left, right, 5)
        for left, right in zip(candidates.display_left, candidates.display_right)
    ]
    candidates["active_seconds_shown"] = [
        _seconds_in_state(recording, left, right, 4)
        for left, right in zip(candidates.display_left, candidates.display_right)
    ]
    time = recording.start_time + np.arange(recording.ne.size) / recording.fs
    candidates["context_peak_excess"] = [
        float(recording.ne[(time >= left) & (time <= right)].max() - peak)
        for left, right, peak in zip(candidates.display_left, candidates.display_right, candidates.raw_peak)
    ]
    candidates = candidates.loc[
        (candidates.quiet_seconds_shown >= MIN_EXAMPLE_QUIET_SECONDS)
        & (candidates.active_seconds_shown >= MIN_EXAMPLE_ACTIVE_SECONDS)
        & (candidates.context_peak_excess <= MAX_EXAMPLE_CONTEXT_PEAK_EXCESS)
    ].sort_values(["peak_seconds", "onset_seconds"], kind="stable")
    if candidates.empty:
        raise ValueError(
            "No raw-bout peak example has the required Active/Quiet context and a clear displayed maximum."
        )
    return candidates.iloc[np.random.default_rng(seed).integers(len(candidates))], recording


def raw_peak_assignment_figure(bouts: pd.DataFrame):
    """Show literal within-bout peak assignment without the cohort baseline detector."""
    import plotly.graph_objects as go

    chosen, recording = choose_raw_peak_example(bouts, RAW_PEAK_EXAMPLE_RECORDING_ID, RAW_PEAK_EXAMPLE_SEED)
    left, right = float(chosen.display_left), float(chosen.display_right)
    time = recording.start_time + np.arange(recording.ne.size) / recording.fs
    shown = (time >= left) & (time <= right)
    values = recording.ne[shown]
    low, high = float(values.min()), float(values.max())
    pad = max((high - low) * 0.08, 0.1)
    figure = go.Figure()
    for start, stop, state in _state_spans(recording, left, right):
        label = STATE_NAMES.get(state) if stop - start >= 3 else None
        kwargs = {"x0": start, "x1": stop, "fillcolor": STATE_COLORS.get(state, "#969696"), "line_width": 0, "layer": "below"}
        if label:
            kwargs.update(annotation_text=label, annotation_position="top left", annotation_font={"size": 11, "color": "#334e68"})
        figure.add_vrect(**kwargs)
    figure.add_vrect(
        x0=chosen.onset_seconds,
        x1=chosen.offset_seconds,
        fillcolor="rgba(255,255,255,0)",
        line={"color": "#05668d", "width": 2},
        annotation_text="selected Quiet score run",
        annotation_position="top right",
        annotation_font={"size": 11, "color": "#05668d"},
    )
    figure.add_trace(go.Scatter(x=time[shown], y=values, mode="lines", name="processed NE", line={"color": "#1f2933", "width": 2}))
    figure.add_hline(y=0, line_dash="dot", line_color="#52606d", annotation_text="zero reference", annotation_font={"size": 11, "color": "#52606d"})
    figure.add_trace(
        go.Scatter(
            x=[chosen.peak_seconds], y=[chosen.raw_peak], mode="markers", name="literal within-bout maximum",
            marker={"color": STATE_COLORS["quiet_wake"], "size": 13, "line": {"color": "white", "width": 2}},
        )
    )
    figure.add_annotation(
        x=chosen.peak_seconds, y=chosen.raw_peak, text="P = maximum in outlined score run",
        showarrow=True, arrowhead=2, ax=0, ay=-42, bgcolor="rgba(255,255,255,0.92)",
        bordercolor="#334e68", font={"size": 11, "color": "#334e68"},
    )
    for value, label in ((chosen.rise20_seconds, "rising 20%"), (chosen.rise80_seconds, "rising 80%"), (chosen.decay80_seconds, "falling 80%"), (chosen.decay20_seconds, "falling 20%")):
        figure.add_vline(x=value, line_dash="dash", line_color="#7b3294", line_width=1.5)
        figure.add_annotation(x=value, y=high + pad * 0.25, text=label, showarrow=False, textangle=-90, font={"size": 11, "color": "#7b3294"})
    figure.update_layout(
        template="plotly_white", title="Raw-bout peak assignment: literal maximum inside a Quiet-Wake score run",
        xaxis_title="recording time (seconds)", yaxis_title="processed NE (percentage delta-F/F)",
        yaxis_range=[low - pad, high + pad], legend={"orientation": "h", "y": -0.2}, height=600,
        margin={"l": 80, "r": 40, "t": 95, "b": 100},
    )
    figure.add_annotation(
        x=0.5, y=-0.31, xref="paper", yref="paper",
        text=("Orange = Active Wake; light blue = Quiet Wake; gray = other state. "
              "No rolling baseline, prominence threshold, or local-peak detector is used: P is the literal maximum in the outlined score run. "
              "Purple crossings are relative to P and may cross score boundaries by peak-state assignment."),
        showarrow=False, font={"size": 12, "color": "#52606d"},
    )
    return figure


def metric_figure(recordings: pd.DataFrame, results: pd.DataFrame):
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    figure = make_subplots(rows=2, cols=2, subplot_titles=[label for _, label, _ in METRICS])
    for index, (metric, label, unit) in enumerate(METRICS):
        row, column = divmod(index, 2)
        row += 1
        column += 1
        paired = recordings[["recording_id", f"active_wake_{metric}_median", f"quiet_wake_{metric}_median"]].dropna()
        result = results.loc[results.metric == metric].iloc[0]
        for _, values in paired.iterrows():
            figure.add_trace(
                go.Scatter(
                    x=[STATE_NAMES["active_wake"], STATE_NAMES["quiet_wake"]],
                    y=[values[f"active_wake_{metric}_median"], values[f"quiet_wake_{metric}_median"]],
                    mode="lines+markers",
                    line={"color": "#9aa5b1", "width": 1.4},
                    marker={"size": 8, "color": [STATE_COLORS["active_wake"], STATE_COLORS["quiet_wake"]]},
                    customdata=[[values.recording_id], [values.recording_id]],
                    hovertemplate="%{customdata[0]}<br>%{x}: %{y:.4g}<extra></extra>",
                    showlegend=False,
                ),
                row=row,
                col=column,
            )
        p_text = "not tested" if pd.isna(result.p_value) else f"p = {result.p_value:.3g}"
        significance = "" if pd.isna(result.p_value) else (" (significant)" if result.p_value < 0.05 else " (not significant)")
        figure.add_annotation(
            x=0.5,
            y=0.98,
            xref="x domain" if index == 0 else f"x{index + 1} domain",
            yref="y domain" if index == 0 else f"y{index + 1} domain",
            text=f"Recording-paired Wilcoxon, n = {len(paired)}, {p_text}{significance}",
            showarrow=False,
            bgcolor="rgba(255,255,255,0.86)",
            bordercolor="#cbd2d9",
            font={"size": 11, "color": "#334e68"},
        )
        figure.update_yaxes(title=unit, row=row, col=column)
    figure.update_layout(
        template="plotly_white",
        title="Exploratory raw-bout comparison: each MAT file treated as one recording",
        height=1100,
        margin={"l": 80, "r": 30, "t": 95, "b": 70},
    )
    return figure


def independent_bout_metric_figure(bouts: pd.DataFrame, results: pd.DataFrame, seed: int = 20260916):
    """Show every bout while making the deliberately invalid independence assumption visible."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    figure = make_subplots(rows=2, cols=2, subplot_titles=[label for _, label, _ in METRICS])
    rng = np.random.default_rng(seed)
    for index, (metric, label, unit) in enumerate(METRICS):
        row, column = divmod(index, 2)
        row += 1
        column += 1
        result = results.loc[results.metric == metric].iloc[0]
        for state, state_name in STATE_NAMES.items():
            values = bouts.loc[bouts.state == state, metric].dropna().to_numpy()
            x_center = 0 if state == "active_wake" else 1
            figure.add_trace(
                go.Violin(
                    x=[x_center] * len(values),
                    y=values,
                    name=state_name,
                    legendgroup=state,
                    showlegend=index == 0,
                    line={"color": STATE_COLORS[state]},
                    fillcolor=STATE_COLORS[state],
                    opacity=0.38,
                    box_visible=True,
                    meanline_visible=False,
                    points=False,
                    hovertemplate=f"{state_name}<br>{metric}: %{{y:.4g}}<extra></extra>",
                ),
                row=row,
                col=column,
            )
            # A deterministic horizontal jitter preserves the visibility of the raw
            # observations in the static report without pretending they are paired.
            figure.add_trace(
                go.Scatter(
                    x=x_center + rng.uniform(-0.11, 0.11, len(values)),
                    y=values,
                    mode="markers",
                    marker={"size": 2.3, "color": STATE_COLORS[state], "opacity": 0.22},
                    hovertemplate=f"{state_name}<br>{metric}: %{{y:.4g}}<extra></extra>",
                    showlegend=False,
                ),
                row=row,
                col=column,
            )
        p_text = "not tested" if pd.isna(result.p_value) else f"p = {result.p_value:.3g}"
        figure.add_annotation(
            x=0.5,
            y=0.98,
            xref="x domain" if index == 0 else f"x{index + 1} domain",
            yref="y domain" if index == 0 else f"y{index + 1} domain",
            text=(
                f"Mann–Whitney, Active n = {result.n_active_bouts}, Quiet n = {result.n_quiet_bouts}, {p_text}"
                "<br><i>Exploratory only: bouts are not independent animals.</i>"
            ),
            showarrow=False,
            bgcolor="rgba(255,255,255,0.88)",
            bordercolor="#cbd2d9",
            font={"size": 10, "color": "#334e68"},
        )
        figure.update_xaxes(
            tickmode="array",
            tickvals=[0, 1],
            ticktext=[STATE_NAMES["active_wake"], STATE_NAMES["quiet_wake"]],
            range=[-0.5, 1.5],
            row=row,
            col=column,
        )
        figure.update_yaxes(title=unit, row=row, col=column)
    figure.update_layout(
        template="plotly_white",
        title="Exploratory raw-bout distributions: every bout treated as an independent observation",
        height=1100,
        margin={"l": 80, "r": 30, "t": 95, "b": 70},
    )
    return figure


def recording_spectral_figure(recordings: pd.DataFrame, results: pd.DataFrame):
    """Render the raw report's one-spectrum-per-recording comparison."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    figure = make_subplots(rows=1, cols=2, subplot_titles=[label for _, label, _ in SPECTRAL_METRICS])
    for index, (metric, label, unit) in enumerate(SPECTRAL_METRICS, start=1):
        paired = recordings[["recording_id", f"active_wake_{metric}", f"quiet_wake_{metric}"]].dropna()
        result = results.loc[results.metric == metric].iloc[0]
        for _, values in paired.iterrows():
            figure.add_trace(
                go.Scatter(
                    x=[STATE_NAMES["active_wake"], STATE_NAMES["quiet_wake"]],
                    y=[values[f"active_wake_{metric}"], values[f"quiet_wake_{metric}"],],
                    mode="lines+markers",
                    line={"color": "#9aa5b1", "width": 1.4},
                    marker={"size": 8, "color": [STATE_COLORS["active_wake"], STATE_COLORS["quiet_wake"]]},
                    customdata=[[values.recording_id], [values.recording_id]],
                    hovertemplate="%{customdata[0]}<br>%{x}: %{y:.4g}<extra></extra>",
                    showlegend=False,
                ),
                row=1,
                col=index,
            )
        if metric == "dominant_frequency_hz":
            edge_count = int(
                np.isclose(
                    paired[[f"active_wake_{metric}", f"quiet_wake_{metric}"]].to_numpy(), 0.2
                ).sum()
            )
            annotation = (
                f"Not interpretable: {edge_count}/{2 * len(paired)} maxima at 0.20 Hz,<br>"
                "the lower band edge"
            )
        elif pd.isna(result.p_value):
            annotation = "Not tested: every maximum is 0.20 Hz,<br>the lower band edge"
        else:
            significance = "significant" if result.p_value < 0.05 else "not significant"
            annotation = f"Recording-paired Wilcoxon, n = {len(paired)}, p = {result.p_value:.3g} ({significance})"
        figure.add_annotation(
            x=0.5,
            y=0.98,
            xref="x domain" if index == 1 else f"x{index} domain",
            yref="y domain" if index == 1 else f"y{index} domain",
            text=annotation,
            showarrow=False,
            align="center",
            bgcolor="rgba(255,255,255,0.86)",
            bordercolor="#cbd2d9",
            font={"size": 11, "color": "#334e68"},
        )
        figure.update_yaxes(title=unit, row=1, col=index)
        if metric == "dominant_frequency_hz":
            figure.update_yaxes(range=[0.18, 0.32], dtick=0.05, row=1, col=index)
    figure.update_layout(
        template="plotly_white",
        title="Exploratory short-window spectrum: each MAT file treated as one recording",
        height=560,
        margin={"l": 80, "r": 30, "t": 95, "b": 70},
    )
    return figure


def independent_spectral_window_figure(windows: pd.DataFrame, results: pd.DataFrame, seed: int = 20260916):
    """Render all spectral windows with their deliberately invalid independence assumption."""
    import plotly.graph_objects as go

    result = results.loc[results.metric == "band_power"].iloc[0]
    rng = np.random.default_rng(seed)
    figure = go.Figure()
    for state, state_name in STATE_NAMES.items():
        values = windows.loc[windows.state == state, "band_power"].dropna().to_numpy()
        x_center = 0 if state == "active_wake" else 1
        figure.add_trace(
            go.Violin(
                x=[x_center] * len(values),
                y=values,
                name=state_name,
                line={"color": STATE_COLORS[state]},
                fillcolor=STATE_COLORS[state],
                opacity=0.38,
                box_visible=True,
                points=False,
                hovertemplate=f"{state_name}<br>band power: %{{y:.4g}}<extra></extra>",
            )
        )
        figure.add_trace(
            go.Scatter(
                x=x_center + rng.uniform(-0.11, 0.11, len(values)),
                y=values,
                mode="markers",
                marker={"size": 3, "color": STATE_COLORS[state], "opacity": 0.25},
                hovertemplate=f"{state_name}<br>band power: %{{y:.4g}}<extra></extra>",
                showlegend=False,
            )
        )
    figure.add_annotation(
        x=0.5,
        y=0.98,
        xref="paper",
        yref="paper",
        text=(
            f"Mann–Whitney, Active n = {result.n_active_windows}, Quiet n = {result.n_quiet_windows}, "
            f"p = {result.p_value:.3g}<br><i>Exploratory only: windows are not independent animals.</i>"
        ),
        showarrow=False,
        bgcolor="rgba(255,255,255,0.88)",
        bordercolor="#cbd2d9",
        font={"size": 11, "color": "#334e68"},
    )
    figure.update_xaxes(
        tickmode="array",
        tickvals=[0, 1],
        ticktext=[STATE_NAMES["active_wake"], STATE_NAMES["quiet_wake"]],
        range=[-0.5, 1.5],
    )
    figure.update_yaxes(title="15 s 0.20–0.30 Hz band power (percentage points²)")
    figure.update_layout(
        template="plotly_white",
        title="Exploratory short-window band power: every 15 s window treated as independent",
        height=620,
        margin={"l": 80, "r": 30, "t": 95, "b": 70},
    )
    return figure


def main(argv=None):
    args = parse_args(argv)
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError(f"Output directory must be new or empty: {args.output}")
    recordings = pd.read_csv(args.analysis / "recordings.csv")
    results = pd.read_csv(args.analysis / "paired_recording_results.csv")
    bouts = pd.read_csv(args.analysis / "bouts.csv")
    bout_results = pd.read_csv(args.analysis / "independent_bout_results.csv")
    spectral_recordings = pd.read_csv(args.analysis / "spectral_recordings.csv")
    spectral_results = pd.read_csv(args.analysis / "paired_spectral_results.csv")
    spectral_windows = pd.read_csv(args.analysis / "spectral_windows.csv")
    spectral_window_results = pd.read_csv(args.analysis / "independent_spectral_window_results.csv")
    args.output.mkdir(parents=True, exist_ok=True)
    _save(metric_figure(recordings, results), args.output / "raw_bout_metric_comparisons.png")
    _save(raw_peak_assignment_figure(bouts), args.output / "raw_peak_assignment_example.png")
    _save(
        independent_bout_metric_figure(bouts, bout_results),
        args.output / "raw_bout_independent_metric_comparisons.png",
    )
    _save(
        recording_spectral_figure(spectral_recordings, spectral_results),
        args.output / "raw_bout_recording_spectral_comparisons.png",
    )
    _save(
        independent_spectral_window_figure(spectral_windows, spectral_window_results),
        args.output / "raw_bout_independent_spectral_comparisons.png",
    )
    print(f"Wrote figures to {args.output}")


if __name__ == "__main__":
    main()
