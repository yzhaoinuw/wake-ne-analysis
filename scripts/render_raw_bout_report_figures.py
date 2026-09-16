"""Render figures for the exploratory zero-referenced raw-bout report."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


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


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis", required=True, type=Path, help="Raw-bout analysis output directory.")
    parser.add_argument("--output", required=True, type=Path, help="New or empty figure directory.")
    return parser.parse_args(argv)


def _save(figure, path: Path):
    figure.write_image(path, format="png", width=1800, height=1280, scale=2)


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
