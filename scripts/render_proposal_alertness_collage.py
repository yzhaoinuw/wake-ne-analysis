"""Render a print-width proposal collage from saved trace, UMAP, and NE results.

No embedding is fitted here. The two UMAP panels use their original saved
coordinates; only the displayed axes of the all-stage panel are exchanged.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.colors import sample_colorscale

from render_pi_alertness_boundary import (
    HIGH,
    HIGH_COLOR,
    LEFT,
    LOW,
    LOW_COLOR,
    RIGHT,
    eeg_spectrogram,
    load_saved_run,
    load_trace,
)


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "writeups" / "assets"
STATES = {
    "nrem": ("NREM", "#77739A"),
    "rem": ("REM", "#9BBF9A"),
    "active_wake": ("High Alertness", HIGH_COLOR),
    "quiet_wake": ("Low Alertness", LOW_COLOR),
}
FONT = 10.5  # Plotly pixels at 96 px/in = 7.875 points.
INK = "#27313B"


def _axis(fig: go.Figure, number: int, xdomain, ydomain, *, xrange=None,
          yrange=None, xticks=None, yticks=None, xlabel=None, ylabel=None,
          hide_x=False, hide_y=False) -> None:
    suffix = "" if number == 1 else str(number)
    x = dict(
        domain=xdomain, anchor=f"y{suffix}", range=xrange,
        showline=True, linewidth=0.8, linecolor=INK, mirror=True,
        ticks="outside", ticklen=2, tickwidth=0.8, tickcolor=INK,
        showgrid=False, zeroline=False, tickfont=dict(size=FONT, color=INK),
        showticklabels=not hide_x, fixedrange=True,
    )
    y = dict(
        domain=ydomain, anchor=f"x{suffix}", range=yrange,
        showline=True, linewidth=0.8, linecolor=INK, mirror=True,
        ticks="outside", ticklen=2, tickwidth=0.8, tickcolor=INK,
        showgrid=False, zeroline=False, tickfont=dict(size=FONT, color=INK),
        showticklabels=not hide_y, fixedrange=True,
    )
    if xticks is not None:
        x["tickmode"] = "array"
        x["tickvals"] = xticks
    if yticks is not None:
        y["tickmode"] = "array"
        y["tickvals"] = yticks
    if xlabel:
        x["title"] = dict(text=xlabel, font=dict(size=FONT, color=INK), standoff=3)
    if ylabel:
        y["title"] = dict(text=ylabel, font=dict(size=FONT, color=INK), standoff=2)
    fig.update_layout(**{f"xaxis{suffix}": x, f"yaxis{suffix}": y})


def _annotation(fig: go.Figure, text: str, x: float, y: float, **kwargs) -> None:
    settings = dict(
        text=text, x=x, y=y, xref="paper", yref="paper", showarrow=False,
        font=dict(size=FONT, family="Arial", color=INK),
        xanchor="center", yanchor="middle",
    )
    settings.update(kwargs)
    fig.add_annotation(**settings)


def _raw_emg_envelope(trace: dict, bins: int = 1350):
    first = round((LEFT - trace["start"]) * trace["fs"])
    last = round((RIGHT - trace["start"]) * trace["fs"])
    data = trace["emg"][first:last]
    # Preserve each bin's minimum and maximum, including isolated bursts.
    edges = np.linspace(0, len(data), bins + 1, dtype=int)
    time, values = [], []
    for a, b in zip(edges[:-1], edges[1:]):
        if a == b:
            continue
        lo = a + int(np.argmin(data[a:b]))
        hi = a + int(np.argmax(data[a:b]))
        for index in sorted((lo, hi)):
            time.append(LEFT + index / trace["fs"])
            values.append(data[index])
    return np.asarray(time), np.asarray(values)


def _strip(fig: go.Figure, number: int, seconds: np.ndarray,
           labels: np.ndarray) -> None:
    name = "" if number == 1 else str(number)
    fig.add_trace(go.Scatter(
        x=[LEFT, RIGHT], y=[0, 1], mode="markers",
        marker=dict(opacity=0), showlegend=False, hoverinfo="skip",
        xaxis=f"x{name}", yaxis=f"y{name}",
    ))
    starts = np.r_[0, np.flatnonzero(np.diff(labels)) + 1]
    ends = np.r_[starts[1:], len(labels)]
    for a, b in zip(starts, ends):
        fig.add_shape(
            type="rect", xref=f"x{name}", yref=f"y{name}",
            x0=int(seconds[a]), x1=int(seconds[b - 1]) + 1, y0=0, y1=1,
            line=dict(width=0), fillcolor=HIGH_COLOR if labels[a] == HIGH else LOW_COLOR,
        )


def _scatter_umap(fig: go.Figure, path: Path, state_column: str,
                  number: int, xdomain, ydomain, title: str) -> None:
    points = pd.read_csv(path, usecols=[state_column, "umap_1", "umap_2"])
    expected = 4000 if number == 5 else 2000
    if len(points) != expected or points[state_column].value_counts().nunique() != 1:
        raise ValueError(f"Unexpected saved UMAP sample composition: {path}")
    suffix = str(number)
    for state, (_, color) in STATES.items():
        part = points.loc[points[state_column] == state]
        if part.empty:
            continue
        fig.add_trace(go.Scatter(
            x=part["umap_2"], y=part["umap_1"], mode="markers",
            marker=dict(size=3.1, color=color, opacity=0.7),
            showlegend=False, hoverinfo="skip", xaxis=f"x{suffix}", yaxis=f"y{suffix}",
        ))
    xspan = points.umap_2.max() - points.umap_2.min()
    yspan = points.umap_1.max() - points.umap_1.min()
    _axis(fig, number, xdomain, ydomain,
          xrange=[points.umap_2.min() - .06*xspan, points.umap_2.max() + .06*xspan],
          yrange=[points.umap_1.min() - .06*yspan, points.umap_1.max() + .06*yspan],
          xlabel="UMAP 2", ylabel="UMAP 1")
    _annotation(fig, title, sum(xdomain)/2, ydomain[1]+.023)


def _slope_panel(fig: go.Figure, xdomain, ydomain) -> None:
    comparison = pd.read_csv(
        ROOT / "results" / "ne_dynamics_startup5_figures_final_20260923"
        / "pooled_comparisons.csv"
    )
    row = comparison.loc[comparison.feature == "ne_slow_signed_slope"]
    if len(row) != 1 or row.iloc[0]["unit"] != "pooled_second":
        raise ValueError("Expected one pooled signed-slope comparison.")
    row = row.iloc[0]
    fig.add_trace(go.Scatter(
        x=[0, 1], y=[0, 0], mode="markers", marker=dict(opacity=0),
        showlegend=False, hoverinfo="skip", xaxis="x7", yaxis="y7",
    ))
    for center, prefix, color in ((0, "high", HIGH_COLOR), (1, "low", LOW_COLOR)):
        q05, q25, median, q75, q95, mean = (
            float(row[f"{prefix}_{stat}"])
            for stat in ("q05", "q25", "median", "q75", "q95", "mean")
        )
        fig.add_shape(type="line", xref="x7", yref="y7", x0=center, x1=center,
                      y0=q05, y1=q95, line=dict(color=color, width=1.2))
        for value in (q05, q95):
            fig.add_shape(type="line", xref="x7", yref="y7",
                          x0=center-.10, x1=center+.10, y0=value, y1=value,
                          line=dict(color=color, width=1.2))
        fig.add_shape(type="rect", xref="x7", yref="y7",
                      x0=center-.27, x1=center+.27, y0=q25, y1=q75,
                      fillcolor="rgba(255,255,255,0.94)",
                      line=dict(color=color, width=1.4))
        fig.add_shape(type="line", xref="x7", yref="y7",
                      x0=center-.27, x1=center+.27, y0=median, y1=median,
                      line=dict(color=color, width=1.8))
        fig.add_trace(go.Scatter(
            x=[center], y=[mean], mode="markers",
            marker=dict(color="#111111", size=5), showlegend=False,
            hoverinfo="skip", xaxis="x7", yaxis="y7",
        ))
    fig.add_shape(type="line", xref="x7", yref="y7", x0=-.5, x1=1.5,
                  y0=0, y1=0, line=dict(color="#A8AFB7", width=.7, dash="dot"))
    _axis(fig, 7, xdomain, ydomain, xrange=[-.5, 1.5], yrange=[-.2, .25],
          xticks=[0, 1], yticks=[-.2, -.1, 0, .1, .2],
          ylabel="Slope (pp/s)")
    fig.update_layout(xaxis7_ticktext=["High", "Low"])
    _annotation(fig, "Signed NE slope", sum(xdomain)/2, ydomain[1]+.023)


def _inside_umap_legend(fig: go.Figure, number: int,
                        states: tuple[str, ...]) -> None:
    """Place the state key in the empty upper-left corner of a UMAP panel."""
    xref, yref = f"x{number} domain", f"y{number} domain"
    positions = [.945 - .06 * index for index in range(len(states))]
    fig.add_shape(
        type="rect", xref=xref, yref=yref,
        x0=.025, x1=.635, y0=positions[-1]-.035, y1=.98,
        fillcolor="rgba(255,255,255,0.9)",
        line=dict(color="#CBD5E1", width=.5),
    )
    for state, y in zip(states, positions):
        name, color = STATES[state]
        fig.add_shape(
            type="circle", xref=xref, yref=yref,
            x0=.055, x1=.085, y0=y-.012, y1=y+.012,
            fillcolor=color, line=dict(width=0),
        )
        fig.add_annotation(
            text=name, x=.105, y=y, xref=xref, yref=yref,
            xanchor="left", yanchor="middle", showarrow=False,
            font=dict(family="Arial", size=FONT, color=INK),
        )


def render(output: Path) -> None:
    _, _, columns = load_saved_run()
    trace, _, _ = load_trace(columns)
    saved = pd.read_csv(ROOT / "results" / "pi_alertness_boundary_20260924"
                        / "representative_second_labels.csv")
    if (not np.array_equal(saved.second.to_numpy(), trace["seconds"])
            or not np.array_equal(saved.source_label.to_numpy(), trace["source_labels"])):
        raise ValueError("Saved projected labels and source trace differ.")
    predicted = saved.umap_cut_label.to_numpy(dtype=int)
    if not np.isin(predicted, (HIGH, LOW)).all():
        raise ValueError("Projected labels must be High or Low.")

    fig = go.Figure()
    fig.update_layout(
        width=720, height=610, margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(family="Arial", size=FONT, color=INK),
        showlegend=False,
    )
    top_x = [.105, .985]
    centers, frequencies, db = eeg_spectrogram(
        trace["eeg"], trace["fs"], trace["start"]
    )
    lower, upper = np.percentile(db, [5, 95])
    fig.add_trace(go.Heatmap(
        x=centers, y=frequencies, z=db, colorscale="Viridis",
        zmin=lower, zmax=upper, showscale=False, hoverinfo="skip",
        xaxis="x", yaxis="y",
    ))
    _axis(fig, 1, top_x, [.785, .94], xrange=[LEFT, RIGHT], yrange=[0, 30],
          yticks=[0, 10, 20, 30], ylabel="EEG (Hz)", hide_x=True)
    time, emg = _raw_emg_envelope(trace)
    fig.add_trace(go.Scatter(
        x=time, y=emg, mode="lines", line=dict(color="#4B5563", width=.6),
        showlegend=False, hoverinfo="skip", xaxis="x2", yaxis="y2",
    ))
    _axis(fig, 2, top_x, [.678, .758], xrange=[LEFT, RIGHT],
          yrange=[float(emg.min())*1.05, float(emg.max())*1.05],
          ylabel="Raw EMG", hide_x=True, hide_y=True)
    _strip(fig, 3, trace["seconds"], trace["source_labels"])
    _axis(fig, 3, top_x, [.633, .657], xrange=[LEFT, RIGHT], yrange=[0, 1],
          hide_x=True, hide_y=True)
    _strip(fig, 4, trace["seconds"], predicted)
    _axis(fig, 4, top_x, [.585, .609], xrange=[LEFT, RIGHT], yrange=[0, 1],
          xticks=list(range(180, 301, 20)), hide_y=True)
    _annotation(fig, "Source<br>label", .094, .645, xanchor="right")
    _annotation(fig, "UMAP-cut<br>label", .094, .597, xanchor="right")
    _annotation(fig, "Representative 120-second Wake segment | 408_yfp", .5, .978)
    _annotation(fig, "EEG power (dB)", .755, .978)
    for index in range(64):
        x0 = .833 + index * .145 / 64
        fig.add_shape(type="rect", xref="paper", yref="paper",
                      x0=x0, x1=x0+.145/64, y0=.969, y1=.981,
                      line=dict(width=0),
                      fillcolor=sample_colorscale("Viridis", index/63)[0])
    for position, value in ((.833, lower), (.9055, (lower+upper)/2), (.978, upper)):
        _annotation(fig, f"{value:.0f}", position, .953)
    _annotation(fig, "High Alertness", .472, .557,
                font=dict(size=FONT, family="Arial", color=HIGH_COLOR))
    _annotation(fig, "Low Alertness", .765, .557,
                font=dict(size=FONT, family="Arial", color=LOW_COLOR))
    _annotation(fig, "Recording time (seconds)", .545, .525)

    fig.add_shape(
        type="line", xref="paper", yref="paper",
        x0=.105, x1=.985, y0=.487, y1=.487,
        line=dict(color="#C4CBD1", width=.8),
    )
    lower_y = [.085, .425]
    _scatter_umap(
        fig, ROOT / "results" / "expanded_embedding" /
        "all_features_all_stages_no_ma" / "embedding_points.csv",
        "state", 5, [.105, .355], lower_y, "All stages",
    )
    _scatter_umap(
        fig, ROOT / "results" / "wake_knn_clusters_20260918" /
        "sampled_wake_points.csv", "source_state", 6,
        [.425, .675], lower_y, "Wake only",
    )
    _slope_panel(fig, [.745, .985], lower_y)

    # Keep vector mean markers above the filled box shapes in print exports.
    fig.update_shapes(layer="below")
    _inside_umap_legend(fig, 5, tuple(STATES))
    _inside_umap_legend(fig, 6, ("active_wake", "quiet_wake"))

    output.parent.mkdir(parents=True, exist_ok=True)
    fig.write_image(output.with_suffix(".svg"))
    fig.write_image(output.with_suffix(".pdf"))
    fig.write_image(output.with_suffix(".png"), scale=3.125)
    for suffix in (".svg", ".pdf", ".png"):
        print(output.with_suffix(suffix))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path,
                        default=ASSETS / "proposal_alertness_collage_20260924.png")
    args = parser.parse_args()
    render(args.output)


if __name__ == "__main__":
    main()
