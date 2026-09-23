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
from wake_ne_analysis.dynamics_workflow import require_empty, source_digest


def load_slopes(analysis_dir):
    analysis_dir = Path(analysis_dir)
    run = json.loads((analysis_dir / "run.json").read_text(encoding="utf-8"))
    if run["status"] != "complete" or run["schema"] != "ne_dynamics_v2_pooled":
        raise ValueError("Expected a completed v2 pooled-seconds analysis.")
    audit = pd.read_csv(analysis_dir / "source_audit.csv", converters={"recording_id": str})
    audit = audit.loc[audit.status == "included"]
    if audit.recording_id.duplicated().any() or len(audit) != run["n_included_files"]:
        raise ValueError("Duplicate or incomplete source audit.")
    chunks, hashes = {4: [], 5: []}, {}
    for row in audit.itertuples():
        path = Path(run["feature_dir"]) / f"{row.recording_id}.npz"
        with np.load(path, allow_pickle=False) as archive:
            metadata = json.loads(str(archive["metadata_json"]))
            if (metadata["config"] != run["config"] or metadata["schema"] != run["schema"]
                    or metadata["source_sha256"] != row.source_sha256
                    or metadata["recording_id"] != row.recording_id):
                raise ValueError(f"Archive provenance/configuration mismatch: {path}")
            index = archive["feature_names"].tolist().index("ne_slow_signed_slope")
            for label in chunks:
                values = archive["X"][archive["label"] == label, index]
                chunks[label].append(values[np.isfinite(values)])
        hashes[path.name] = source_digest(path)
    return {label: np.concatenate(parts) for label, parts in chunks.items()}, run, hashes


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
            quantiles = np.quantile(chosen, [.25, .5, .75]) if len(chosen) else [np.nan] * 3
            for field, value in zip(("q25", "median", "q75"), quantiles):
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
    for row, color, offset in zip(summary.itertuples(), ("#E31A1C", "#0072B2"), (-.07, .07)):
        fig.add_trace(go.Bar(
            x=["Rising", "Declining"], y=[row.percent_rising, row.percent_declining],
            text=[f"{row.percent_rising:.1f}%", f"{row.percent_declining:.1f}%"],
            textposition="outside", marker_color=color, name=row.state, legendgroup=row.state,
        ), row=1, col=1)
        median = np.array([row.rising_median, -row.declining_median])
        lower = np.array([row.rising_q25, -row.declining_q75])
        upper = np.array([row.rising_q75, -row.declining_q25])
        fig.add_trace(go.Scatter(
            x=[offset, 1 + offset], y=median, mode="markers", marker=dict(color=color, size=12),
            customdata=["Rising", "Declining"],
            hovertemplate="%{customdata}<br>Median magnitude: %{y:.4f}<extra>%{fullData.name}</extra>",
            error_y=dict(type="data", symmetric=False, array=upper-median, arrayminus=median-lower,
                         color=color, thickness=2, width=6),
            name=row.state, legendgroup=row.state, showlegend=False,
        ), row=1, col=2)
    fig.update_yaxes(title_text="Percentage of valid state seconds", range=[0, 100], row=1, col=1)
    fig.update_yaxes(title_text="Slope magnitude (percentage points/s)", rangemode="tozero", row=1, col=2)
    fig.update_xaxes(tickvals=[0, 1], ticktext=["Rising", "Declining"], range=[-.4, 1.4], row=1, col=2)
    fig.update_layout(
        title="Rising and declining NE during High and Low Alertness<br><sup>All eligible seconds pooled across ten aligned files; 0.1 Hz zero-phase low-pass</sup>",
        template="plotly_white", barmode="group", width=1250, height=650,
        margin=dict(l=90, r=55, t=125, b=150), font=dict(size=14),
        legend=dict(orientation="h", x=.5, xanchor="center", y=-.18),
    )
    fig.add_annotation(x=.5, y=-.34, xref="paper", yref="paper", xanchor="center",
                       text="Right panel: median and IQR; declining slopes shown as positive magnitudes.",
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
                  "script_sha256": source_digest(__file__), "new_significance_tests": False}
    (args.output_dir / "provenance.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")
    figure = make_figure(summary)
    figure.write_html(args.output_dir / "slope_direction.html", include_plotlyjs=True)
    if args.png:
        figure.write_image(args.output_dir / "slope_direction.png", scale=2)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
