"""Summarize rising and declining seconds from the completed pooled NE archives.

This descriptive follow-up adds no significance tests. It reads the exact files
in the completed analysis audit, verifies their feature configuration/provenance,
and pools valid signed slopes without recording balancing or new normalization.
"""

import argparse
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wake_ne_analysis.dynamics_workflow import load_feature_records, require_empty, source_digest
from wake_ne_analysis.dynamics_summary import pool_records
from wake_ne_analysis.dynamics_plots import box_and_mean_traces, prefixed_box_stats


def load_slopes(analysis_dir):
    records, run, hashes = load_feature_records(analysis_dir)
    arrays = pool_records(records)
    slopes = {}
    for label in (4, 5):
        values = arrays["X"][arrays["label"] == label, 0]
        slopes[label] = values[np.isfinite(values)]
    return slopes, run, hashes


def summarize(slopes):
    rows = []
    for label, name in ((4, "High Alertness"), (5, "Low Alertness")):
        values = slopes[label]
        row = {"state": name, "n_valid": len(values),
               "mean_slope": float(np.mean(values)) if len(values) else np.nan,
               "median_slope": float(np.median(values)) if len(values) else np.nan}
        for direction, chosen in (("rising", values[values > 0]),
                                  ("declining", values[values < 0]),
                                  ("zero", values[values == 0])):
            row[f"n_{direction}"] = len(chosen)
            row[f"percent_{direction}"] = 100 * len(chosen) / len(values) if len(values) else np.nan
            row[f"{direction}_mean"] = float(np.mean(chosen)) if len(chosen) else np.nan
            quantiles = np.quantile(chosen, [.05, .25, .5, .75, .95]) if len(chosen) else [np.nan] * 5
            for field, value in zip(("q05", "q25", "median", "q75", "q95"), quantiles):
                row[f"{direction}_{field}"] = value
        rows.append(row)
    return pd.DataFrame(rows)


def make_figure(summary):
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    fig = make_subplots(rows=1, cols=2, horizontal_spacing=.16, subplot_titles=[
        "How often was NE rising or declining?",
        "How steep were those rises and declines?",
    ])
    for row, color, offset in zip(summary.itertuples(), ("#E31A1C", "#0072B2"), (-.14, .14)):
        fig.add_trace(go.Bar(
            x=["Rising", "Declining"], y=[row.percent_rising, row.percent_declining],
            text=[f"{row.percent_rising:.1f}%", f"{row.percent_declining:.1f}%"],
            textposition="outside", marker_color=color, name=row.state, legendgroup=row.state,
        ), row=1, col=1)
        for index, direction in enumerate(("rising", "declining")):
            stats = prefixed_box_stats(row._asdict(), direction)
            for trace in box_and_mean_traces(stats, index + offset, row.state, color, width=.22):
                fig.add_trace(trace, row=1, col=2)
    fig.update_xaxes(tickvals=[0, 1], ticktext=["Rising", "Declining"],
                     range=[-.5, 1.5], row=1, col=2)
    fig.update_yaxes(title_text="Percentage of valid state seconds", range=[0, 100], row=1, col=1)
    fig.update_yaxes(title_text="Slope (percentage points/s)", rangemode="tozero", row=1, col=2)
    fig.update_layout(
        title="Rising and declining NE during High and Low Alertness<br><sup>All eligible seconds pooled across ten files</sup>",
        template="plotly_white", barmode="group", width=1250, height=650,
        margin=dict(l=90, r=55, t=125, b=165), font=dict(size=14),
        legend=dict(orientation="h", x=.5, xanchor="center", y=-.18),
    )
    fig.add_annotation(x=.5, y=-.34, xref="paper", yref="paper", xanchor="center",
                       text="Right: boxes show middle 50%; line: median; black dot: mean; whiskers: 5th–95th percentiles.<br>Tail points omitted from display; all values enter the summaries.",
                       showarrow=False, font=dict(size=12))
    return fig


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--png", action="store_true")
    args = parser.parse_args(argv)
    require_empty(args.output_dir)
    slopes, run, hashes = load_slopes(args.analysis_dir)
    summary = summarize(slopes)
    original = pd.read_csv(args.analysis_dir / "pooled_comparisons.csv")
    original = original.loc[original.feature == "ne_slow_signed_slope"].iloc[0]
    for row, prefix in zip(summary.itertuples(), ("high", "low")):
        if row.n_valid != original[f"n_{prefix}"] or not np.isclose(row.median_slope, original[f"{prefix}_median"]):
            raise ValueError("Signed-slope summary does not match the completed pooled analysis.")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.output_dir / "slope_direction_summary.csv", index=False)
    provenance = {"analysis_dir": str(args.analysis_dir.resolve()), "config": run["config"],
                  "n_files": len(hashes), "archive_sha256": hashes,
                  "script_sha256": source_digest(__file__),
                  "plot_helper_sha256": source_digest(Path(__file__).resolve().parents[1] / "wake_ne_analysis/dynamics_plots.py"),
                  "new_significance_tests": False}
    (args.output_dir / "provenance.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")
    figure = make_figure(summary)
    figure.write_html(args.output_dir / "slope_direction.html", include_plotlyjs=True)
    if args.png:
        figure.write_image(args.output_dir / "slope_direction.png", scale=2)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
