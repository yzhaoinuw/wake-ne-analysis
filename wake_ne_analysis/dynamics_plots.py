"""Standalone pooled-seconds plots, independent of extraction and tests."""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .dynamics_workflow import load_feature_records, require_empty, source_digest
from .dynamics_summary import pooled_comparisons
from .ne_dynamics import FEATURE_NAMES, FEATURE_TITLES, FEATURE_UNITS


def box_and_mean_traces(stats, position, name, color, width=.4):
    """Quartile box, 5th/95th percentile whiskers, and the all-values mean."""
    import plotly.graph_objects as go

    rgb = ",".join(str(int(color[i:i + 2], 16)) for i in (1, 3, 5))
    box = go.Box(
        x=[position], q1=[stats["q25"]], median=[stats["median"]], q3=[stats["q75"]],
        lowerfence=[stats["q05"]], upperfence=[stats["q95"]],
        name=name, legendgroup=name, showlegend=False, width=width, boxpoints=False,
        line=dict(color=color, width=2), fillcolor=f"rgba({rgb},0.20)",
    )
    mean = go.Scatter(
        x=[position], y=[stats["mean"]], mode="markers", name=name,
        legendgroup=name, showlegend=False,
        marker=dict(color="black", size=9, line=dict(color="white", width=1)),
        hovertemplate="Mean: %{y:.5g}<extra>%{fullData.name}</extra>",
    )
    return box, mean


def prefixed_box_stats(result, prefix):
    return {key: result[f"{prefix}_{key}"] for key in
            ("q05", "q25", "median", "q75", "q95", "mean")}


def build_figures(comparisons, history_seconds=10):
    """Show pooled distributions with mean dots and feature coverage."""
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
            for trace in box_and_mean_traces(prefixed_box_stats(result, state), name, name, color):
                fig.add_trace(trace, row=row, col=col)
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
        title="NE dynamics: all eligible seconds pooled<br><sup>Boxes: middle 50%; line: median; black dot: mean; whiskers: 5th–95th percentiles</sup>",
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
    records, _, hashes = load_feature_records(results_dir)
    comparisons = pooled_comparisons(records)
    original = pd.read_csv(results_dir / "pooled_comparisons.csv")
    pd.testing.assert_frame_equal(
        comparisons[original.columns], original, check_exact=False, rtol=1e-12, atol=1e-15
    )
    figures = build_figures(comparisons, run["config"]["history_seconds"])
    figures["variance_dynamics"] = build_variance_figure(
        comparisons, run["config"]["history_seconds"]
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    comparisons.to_csv(output_dir / "pooled_comparisons.csv", index=False)
    provenance = {"analysis_dir": str(results_dir.resolve()), "archive_sha256": hashes,
                  "summary": "all_finite_seconds",
                  "display": "quartile_box_with_mean_dot_and_5th_95th_percentile_whiskers",
                  "code_sha256": {name: source_digest(Path(__file__).with_name(name)) for name in
                                  ("dynamics_plots.py", "dynamics_summary.py", "dynamics_workflow.py")}}
    (output_dir / "provenance.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")
    for name, figure in figures.items():
        figure.write_html(output_dir / f"{name}.html", include_plotlyjs=True)
        if png:
            figure.write_image(output_dir / f"{name}.png", scale=2)
    return figures


def build_variance_figure(comparisons, history_seconds=10):
    """Focused variance distributions; retain the original distribution tests."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    features = ("ne_past_variance", "ne_past_detrended_variance")
    figure = make_subplots(rows=1, cols=2, horizontal_spacing=.16,
                           subplot_titles=["Ordinary variance", "Detrended variance"])
    table = comparisons.set_index("feature")
    for column, feature in enumerate(features, start=1):
        row = table.loc[feature]
        for state, name, color in (
            ("high", "High Alertness", "#E31A1C"),
            ("low", "Low Alertness", "#0072B2"),
        ):
            for trace in box_and_mean_traces(prefixed_box_stats(row, state), name, name, color):
                figure.add_trace(trace, row=1, col=column)
        figure.layout.annotations[column - 1].text += (
            f"<br><sup>High n={int(row.n_high):,}; Low n={int(row.n_low):,}; "
            f"nominal Holm p={row.p_holm:.3g}</sup>"
        )
        figure.update_yaxes(title_text="Variance (percentage points squared)",
                            rangemode="tozero", row=1, col=column)
        figure.update_xaxes(type="category", categoryorder="array",
                            categoryarray=["High Alertness", "Low Alertness"],
                            range=[-.5, 1.5], tickangle=0, row=1, col=column)
    figure.update_layout(
        title=f"NE variability over the preceding {history_seconds:g} seconds<br><sup>All eligible seconds pooled</sup>",
        template="plotly_white", width=1250, height=650,
        margin=dict(l=100, r=55, t=135, b=145), font=dict(size=14),
    )
    figure.add_annotation(
        x=.5, y=-.23, xref="paper", yref="paper", xanchor="center", showarrow=False,
        text="Boxes: middle 50%; line: median; black dot: mean; whiskers: 5th–95th percentiles.<br>Tail points omitted from display; all values enter means and tests.",
        font=dict(size=13),
    )
    return figure
