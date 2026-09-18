"""Render auditable interactive plots from wake-NE CSV output tables."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


STATE_NAMES = {"active_wake": "Active Wake", "quiet_wake": "Quiet Wake"}
STATE_COLORS = {"active_wake": "#1565C0", "quiet_wake": "#D95F02"}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create an interactive HTML report from a wake-NE analysis output directory."
    )
    parser.add_argument("results", type=Path, help="Analysis output directory, or its subjects.csv.")
    parser.add_argument(
        "--preflight",
        type=Path,
        help="Optional validation output directory, or its coverage.csv table.",
    )
    parser.add_argument("--output", required=True, type=Path, help="New HTML report path.")
    parser.add_argument(
        "--static-dir",
        type=Path,
        help="New directory for PNG panels matching the interactive report.",
    )
    parser.add_argument("--title", default="Wake NE exploratory report", help="Report title.")
    return parser


def _table_path(source: Path, filename: str) -> Path | None:
    if source.is_dir():
        candidate = source / filename
    elif source.name == filename:
        candidate = source
    else:
        candidate = source.parent / filename
    return candidate if candidate.is_file() else None


def _read_required(source: Path, filename: str) -> tuple[pd.DataFrame, Path]:
    path = _table_path(source, filename)
    if path is None:
        raise ValueError(f"Could not find {filename} in {source}.")
    return pd.read_csv(path), path


def _read_optional(source: Path | None, filename: str) -> pd.DataFrame | None:
    if source is None:
        return None
    path = _table_path(source, filename)
    return pd.read_csv(path) if path is not None else None


def _state_values(subjects: pd.DataFrame, metric: str) -> pd.DataFrame:
    rows = []
    for state, display in STATE_NAMES.items():
        column = f"{state}_{metric}"
        if column not in subjects:
            continue
        subset = subjects[["mouse_id", column]].rename(columns={column: "value"}).copy()
        subset["state"] = display
        subset["state_key"] = state
        rows.append(subset)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def _add_state_points(figure, subjects: pd.DataFrame, metric: str, row: int, col: int, unit: str):
    import plotly.graph_objects as go

    values = _state_values(subjects, metric).dropna(subset=["value"])
    if values.empty:
        figure.add_annotation(
            text="No available estimate", showarrow=False, row=row, col=col, font={"color": "#666"}
        )
        return
    for state, display in STATE_NAMES.items():
        subset = values.loc[values.state_key == state]
        figure.add_trace(
            go.Box(
                x=[display] * len(subset),
                y=subset.value,
                name=display,
                marker_color=STATE_COLORS[state],
                boxpoints="all",
                jitter=0.25,
                pointpos=0,
                customdata=subset.mouse_id,
                hovertemplate="%{customdata}<br>%{x}: %{y:.4g}<extra></extra>",
                showlegend=False,
            ),
            row=row,
            col=col,
        )
    figure.update_yaxes(title_text=unit, row=row, col=col)


def summary_figure(subjects: pd.DataFrame, title: str):
    from plotly.subplots import make_subplots

    figure = make_subplots(
        rows=2,
        cols=4,
        subplot_titles=(
            "Labeled time",
            "Wake-bout count",
            "Candidate-event count",
            "Retained-event count",
            "Eligible-event amplitude",
            "Eligible-event duration",
            "Eligible-event 20–80% rise slope",
            "Eligible-event 20–80% decay slope",
        ),
        vertical_spacing=0.18,
    )
    _add_state_points(figure, subjects, "total_seconds", 1, 1, "seconds")
    _add_state_points(figure, subjects, "n_bouts", 1, 2, "bouts")
    _add_state_points(figure, subjects, "n_events_detected", 1, 3, "events")
    _add_state_points(figure, subjects, "n_events_used", 1, 4, "events")
    _add_state_points(figure, subjects, "amplitude_median", 2, 1, "percentage points")
    _add_state_points(figure, subjects, "duration_seconds_median", 2, 2, "seconds")
    _add_state_points(figure, subjects, "rise_slope_median", 2, 3, "percentage points / second")
    _add_state_points(figure, subjects, "decay_slope_median", 2, 4, "percentage points / second")
    figure.update_layout(
        title=f"{title}: descriptive subject summaries",
        template="plotly_white",
        height=760,
        margin={"l": 65, "r": 30, "t": 90, "b": 60},
        annotations=[
            *figure.layout.annotations,
            {
                "text": "Each point is one mouse. Boxes are descriptive only; no group inference is shown.",
                "xref": "paper",
                "yref": "paper",
                "x": 0,
                "y": -0.12,
                "showarrow": False,
                "font": {"color": "#555", "size": 12},
            },
        ],
    )
    return figure


def preflight_figure(coverage: pd.DataFrame | None, bouts: pd.DataFrame | None, title: str):
    from plotly.subplots import make_subplots
    import plotly.graph_objects as go

    if coverage is None and bouts is None:
        return None
    figure = make_subplots(rows=1, cols=2, subplot_titles=("Spectral-window coverage", "Wake-bout durations"))
    if coverage is not None:
        for state, display in STATE_NAMES.items():
            subset = coverage.loc[coverage.state == state].sort_values("window_seconds")
            if subset.empty:
                continue
            figure.add_trace(
                go.Scatter(
                    x=subset.window_seconds,
                    y=100 * subset.coverage_fraction,
                    mode="lines+markers",
                    name=display,
                    line={"color": STATE_COLORS[state], "width": 3},
                    customdata=subset[["n_windows", "covered_seconds"]],
                    hovertemplate=(
                        "%{x:g} s window<br>coverage: %{y:.1f}%<br>"
                        "windows: %{customdata[0]}<br>covered: %{customdata[1]:.1f} s<extra></extra>"
                    ),
                ),
                row=1,
                col=1,
            )
        figure.update_xaxes(title_text="window duration (seconds)", row=1, col=1)
        figure.update_yaxes(title_text="available state time covered (%)", range=[0, 100], row=1, col=1)
    if bouts is not None:
        for state, display in STATE_NAMES.items():
            subset = bouts.loc[bouts.state == state]
            if subset.empty:
                continue
            figure.add_trace(
                go.Violin(
                    x=[display] * len(subset),
                    y=subset.duration_seconds,
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
        figure.update_yaxes(title_text="bout duration (seconds; log scale)", type="log", row=1, col=2)
    figure.update_layout(
        title=f"{title}: usable-data preflight",
        template="plotly_white",
        height=460,
        margin={"l": 65, "r": 30, "t": 80, "b": 60},
    )
    return figure


def event_figure(events: pd.DataFrame | None, title: str):
    import plotly.express as px

    if events is None or events.empty:
        return None
    shown = events.loc[events.state.isin(STATE_NAMES)].copy()
    if shown.empty:
        return None
    shown["state"] = shown.state.map(STATE_NAMES)
    shown["eligibility"] = shown.eligible.map({True: "retained", False: "excluded"})
    figure = px.scatter(
        shown,
        x="duration_seconds",
        y="amplitude",
        color="state",
        symbol="eligibility",
        hover_data=["mouse_id", "recording_id", "peak_seconds", "crosses_state", "complete"],
        color_discrete_map={"Active Wake": STATE_COLORS["active_wake"], "Quiet Wake": STATE_COLORS["quiet_wake"]},
        labels={
            "duration_seconds": "20%-to-20% duration (seconds)",
            "amplitude": "amplitude (percentage points)",
            "state": "peak state",
        },
        title=f"{title}: detected transients (Active / Quiet Wake candidates)",
        template="plotly_white",
    )
    figure.update_layout(height=510, margin={"l": 65, "r": 30, "t": 80, "b": 60})
    return figure


def spectral_summary_figure(subjects: pd.DataFrame, title: str):
    from plotly.subplots import make_subplots

    figure = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("Short-window band power", "Short-window dominant frequency"),
    )
    _add_state_points(figure, subjects, "band_power", 1, 1, "percentage points²")
    _add_state_points(figure, subjects, "dominant_frequency_hz", 1, 2, "Hz")
    figure.update_layout(
        title=f"{title}: exploratory spectral summaries",
        template="plotly_white",
        height=440,
        margin={"l": 65, "r": 30, "t": 80, "b": 75},
        annotations=[
            *figure.layout.annotations,
            {
                "text": "Each point is one mouse. Values are unavailable when that state has no eligible fixed windows.",
                "xref": "paper",
                "yref": "paper",
                "x": 0,
                "y": -0.18,
                "showarrow": False,
                "font": {"color": "#555", "size": 12},
            },
        ],
    )
    return figure


def spectra_figure(spectra: pd.DataFrame | None, title: str):
    from plotly.subplots import make_subplots
    import plotly.graph_objects as go

    if spectra is None or spectra.empty:
        return None
    figure = make_subplots(rows=1, cols=2, subplot_titles=("Active Wake", "Quiet Wake"))
    for column, (state, display) in enumerate(STATE_NAMES.items(), start=1):
        subset = spectra.loc[spectra.state == state]
        for mouse_id, curve in subset.groupby("mouse_id", sort=True):
            curve = curve.sort_values("frequency_hz")
            n_windows = int(curve.n_windows.iloc[0])
            figure.add_trace(
                go.Scatter(
                    x=curve.frequency_hz,
                    y=curve.psd,
                    mode="lines+markers",
                    name=f"{mouse_id} ({n_windows} windows)",
                    legendgroup=f"{state}_{mouse_id}",
                    hovertemplate=(
                        f"{display}<br>{mouse_id}<br>frequency: %{{x:.3g}} Hz<br>"
                        "PSD: %{y:.4g} percentage-points²/Hz<extra></extra>"
                    ),
                ),
                row=1,
                col=column,
            )
        figure.update_xaxes(title_text="frequency (Hz)", row=1, col=column)
        figure.update_yaxes(title_text="PSD (percentage-points²/Hz)", row=1, col=column)
    figure.update_layout(
        title=f"{title}: per-mouse short-window spectra",
        template="plotly_white",
        height=470,
        margin={"l": 75, "r": 30, "t": 80, "b": 60},
    )
    return figure


def write_report(
    output: Path,
    figures: list,
    assignment: str,
    recording_start_exclusion_seconds: float = 0.0,
) -> None:
    from plotly.io import to_html

    if output.exists():
        raise ValueError(f"Output already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    fragments = [
        to_html(figure, full_html=False, include_plotlyjs="inline" if i == 0 else False)
        for i, figure in enumerate(figures)
        if figure is not None
    ]
    event_note = (
        "Complete NE signal elevation episodes are assigned to the final wake state at "
        "their peak; boundary-crossing support remains visible in the audit."
        if assignment == "peak"
        else "Event medians use only complete episodes contained within the assigned "
        "wake state; excluded crossing candidates remain visible."
    )
    qc_note = (
        f" Candidates peaking and spectral windows starting in the first "
        f"{recording_start_exclusion_seconds:g} seconds of each recording are excluded "
        "under the recorded start-artifact QC rule."
        if recording_start_exclusion_seconds > 0
        else ""
    )
    output.write_text(
        "<!doctype html><html><head><meta charset='utf-8'><title>Wake NE report</title>"
        "<style>body{font-family:Arial,sans-serif;margin:0 auto;max-width:1280px;padding:18px;}"
        "p{color:#444;line-height:1.45;}</style></head><body>"
        f"<p>Exploratory descriptive plots. {event_note}{qc_note}</p>"
        + "\n".join(fragments)
        + "</body></html>",
        encoding="utf-8",
    )


def write_static_figures(output: Path, figure_items: list[tuple[str, object]]) -> None:
    if output.exists():
        raise ValueError(f"Static figure directory already exists: {output}")
    output.mkdir(parents=True)
    for index, (name, figure) in enumerate(figure_items, start=1):
        if figure is None:
            continue
        height = int(figure.layout.height or 700)
        figure.write_image(output / f"{index:02d}_{name}.png", width=1800, height=height, scale=2)


def main(argv=None) -> int:
    args = _parser().parse_args(argv)
    try:
        subjects, subjects_path = _read_required(args.results, "subjects.csv")
        if "mouse_id" not in subjects:
            raise ValueError(f"subjects table has no mouse_id column: {subjects_path}")
        events = _read_optional(args.results, "events.csv")
        subject_spectra = _read_optional(args.results, "subject_spectra.csv")
        preflight_source = args.preflight or args.results
        coverage = _read_optional(preflight_source, "coverage.csv")
        bouts = _read_optional(preflight_source, "bouts.csv")
        figure_items = [
            ("subject_event_metrics", summary_figure(subjects, args.title)),
            ("window_coverage", preflight_figure(coverage, bouts, args.title)),
            ("event_candidates", event_figure(events, args.title)),
            ("spectral_metrics", spectral_summary_figure(subjects, args.title)),
            ("subject_spectra", spectra_figure(subject_spectra, args.title)),
        ]
        assignment = "contained"
        recording_start_exclusion_seconds = 0.0
        run_path = _table_path(args.results, "run.json")
        if run_path is not None:
            import json
            metadata = json.loads(run_path.read_text(encoding="utf-8"))
            config = metadata.get("config", {})
            assignment = config.get("transients", {}).get("assignment", assignment)
            recording_start_exclusion_seconds = config.get(
                "recording_start_exclusion_seconds", recording_start_exclusion_seconds
            )
        write_report(
            args.output,
            [figure for _, figure in figure_items],
            assignment,
            recording_start_exclusion_seconds,
        )
        if args.static_dir is not None:
            write_static_figures(args.static_dir, figure_items)
    except (ImportError, OSError, ValueError, KeyError) as error:
        _parser().exit(2, f"Plotting failed: {error}\n")
    print(f"Wrote interactive report: {args.output}")
    return 0


if __name__ == "__main__":
    main()
