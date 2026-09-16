"""Render figures for the exploratory zero-referenced raw-bout report."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


STATE_NAMES = {"active_wake": "Active Wake", "quiet_wake": "Quiet Wake"}
STATE_COLORS = {"active_wake": "#E69F00", "quiet_wake": "#56B4E9"}
METRICS = [
    ("raw_peak", "Zero-referenced peak", "processed NE (percentage delta-F/F)"),
    ("duration_seconds", "Zero-referenced duration", "seconds"),
    ("rise_slope", "Zero-referenced 20–80% rise", "percentage points/s"),
    ("decay_slope", "Zero-referenced 20–80% decay", "percentage points/s"),
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
        axis_id = index + 1
        figure.add_annotation(
            x=0.5,
            y=0.98,
            xref="x domain" if index == 0 else f"x{axis_id} domain",
            yref="y domain" if index == 0 else f"y{axis_id} domain",
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


def main(argv=None):
    args = parse_args(argv)
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError(f"Output directory must be new or empty: {args.output}")
    recordings = pd.read_csv(args.analysis / "recordings.csv")
    results = pd.read_csv(args.analysis / "paired_recording_results.csv")
    args.output.mkdir(parents=True, exist_ok=True)
    _save(metric_figure(recordings, results), args.output / "raw_bout_metric_comparisons.png")
    print(f"Wrote figures to {args.output}")


if __name__ == "__main__":
    main()
