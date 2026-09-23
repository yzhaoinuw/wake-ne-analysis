"""Standalone pooled-seconds plots, independent of extraction and tests."""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .dynamics_workflow import require_empty
from .ne_dynamics import FEATURE_NAMES, FEATURE_TITLES, FEATURE_UNITS


def build_figures(comparisons, history_seconds=10):
    """Show pooled quartiles, medians and 5th/95th percentiles without subsampling.

    The figure omits tail points for readability; every finite second, including
    those tails, contributes to the numerical comparison and saved quantiles.
    """
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    titles = [title.replace("10-second", f"{history_seconds:g}-second") for title in FEATURE_TITLES]
    stats = comparisons.set_index("feature")
    fig = make_subplots(rows=2, cols=2, subplot_titles=titles,
                        horizontal_spacing=0.16, vertical_spacing=0.22)
    coverage = make_subplots(rows=2, cols=2, subplot_titles=titles,
                             horizontal_spacing=0.16, vertical_spacing=0.22)
    for index, feature in enumerate(FEATURE_NAMES):
        row, col = index // 2 + 1, index % 2 + 1
        result = stats.loc[feature]
        for state, name, color in (("low", "Low Alertness", "#0072B2"),
                                    ("high", "High Alertness", "#E31A1C")):
            n = int(result[f"n_{state}"])
            fig.add_trace(go.Box(
                x=[name], q1=[result[f"{state}_q25"]], median=[result[f"{state}_median"]],
                q3=[result[f"{state}_q75"]], lowerfence=[result[f"{state}_q05"]],
                upperfence=[result[f"{state}_q95"]], name=name, boxpoints=False,
                line=dict(color=color, width=2),
                fillcolor="rgba(0,114,178,0.18)" if state == "low" else "rgba(227,26,28,0.18)",
                showlegend=False, width=0.45,
            ), row=row, col=col)
            total = n + int(result[f"n_{state}_missing"])
            coverage.add_trace(go.Bar(
                x=[name], y=[100 * n / total if total else np.nan], marker_color=color,
                text=[f"{n:,}/{total:,}"], textposition="outside", name=name,
                showlegend=False,
            ), row=row, col=col)
        fig.layout.annotations[index].text += (
            f"<br><sup>High n={int(result.n_high):,}; Low n={int(result.n_low):,}; "
            f"nominal Holm p={result.p_holm:.3g}</sup>"
        )
        fig.update_yaxes(title_text=FEATURE_UNITS[index], zeroline=True,
                         zerolinecolor="#dddddd", row=row, col=col)
        coverage.update_yaxes(title_text="Valid state seconds (%)", range=[0, 112], row=row, col=col)
    fig.update_layout(
        title="NE dynamics: all eligible seconds pooled<br><sup>Boxes: 25th–75th percentiles and median; whiskers: 5th–95th percentiles; tails omitted only from display</sup>",
        template="plotly_white", width=1300, height=950,
        margin=dict(l=100, r=50, t=135, b=75), font=dict(size=14),
        annotations=list(fig.layout.annotations) + [dict(
            x=0, y=-0.10, xref="paper", yref="paper", showarrow=False, xanchor="left",
            text="Pooled p-values ignore temporal/recording dependence and are not independent-animal evidence.",
            font=dict(size=13),
        )],
    )
    coverage.update_layout(title="Pooled feature coverage — valid / total state seconds",
                           template="plotly_white", width=1200, height=800)
    return {"pooled_dynamics": fig, "coverage": coverage}


def render_results(results_dir, output_dir, png=False):
    """HTML needs no browser renderer. Optional PNG uses Plotly/Kaleido."""
    results_dir, output_dir = Path(results_dir), Path(output_dir)
    run = json.loads((results_dir / "run.json").read_text(encoding="utf-8"))
    if run["status"] != "complete":
        raise ValueError("Analysis has not completed; refusing to plot partial results.")
    if run.get("comparison_unit") != "pooled_second":
        raise ValueError("This renderer expects the v2 pooled-seconds analysis.")
    require_empty(output_dir)
    comparisons = pd.read_csv(results_dir / "pooled_comparisons.csv")
    figures = build_figures(comparisons, run["config"]["history_seconds"])
    figures["variance_dynamics"] = build_variance_figure(
        comparisons, run["config"]["history_seconds"]
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, figure in figures.items():
        figure.write_html(output_dir / f"{name}.html", include_plotlyjs=True)
        if png:
            figure.write_image(output_dir / f"{name}.png", scale=2)
    return figures


def build_variance_figure(comparisons, history_seconds=10):
    """Focused variance panels from the existing pooled table; no new tests."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    features = ("ne_past_variance", "ne_past_detrended_variance")
    figure = make_subplots(rows=1, cols=2, horizontal_spacing=.16,
                           subplot_titles=["Ordinary variance", "Detrended variance"])
    table = comparisons.set_index("feature")
    for column, feature in enumerate(features, start=1):
        row = table.loc[feature]
        for state, name, color, fill in (
            ("high", "High Alertness", "#E31A1C", "rgba(227,26,28,0.18)"),
            ("low", "Low Alertness", "#0072B2", "rgba(0,114,178,0.18)"),
        ):
            figure.add_trace(go.Box(
                x=[name], q1=[row[f"{state}_q25"]], median=[row[f"{state}_median"]],
                q3=[row[f"{state}_q75"]], lowerfence=[row[f"{state}_q05"]],
                upperfence=[row[f"{state}_q95"]], boxpoints=False, name=name,
                line=dict(color=color, width=2), fillcolor=fill, width=.45,
                showlegend=False,
            ), row=1, col=column)
        figure.layout.annotations[column - 1].text += (
            f"<br><sup>High n={int(row.n_high):,}; Low n={int(row.n_low):,}; "
            f"nominal Holm p={row.p_holm:.3g}</sup>"
        )
        figure.update_yaxes(title_text="Variance (percentage points squared)",
                            rangemode="tozero", row=1, col=column)
    figure.update_layout(
        title=f"NE variability over the preceding {history_seconds:g} seconds<br><sup>All eligible seconds pooled; saved processed NE without the additional 0.1 Hz low-pass</sup>",
        template="plotly_white", width=1250, height=650,
        margin=dict(l=100, r=55, t=135, b=120), font=dict(size=14),
    )
    figure.add_annotation(
        x=.5, y=-.23, xref="paper", yref="paper", xanchor="center", showarrow=False,
        text="Boxes: median and IQR; whiskers: 5th–95th percentiles. All finite values enter the tests.",
        font=dict(size=13),
    )
    return figure
