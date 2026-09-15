"""Pool events and spectral windows within mouse, keeping mice as rows."""

import json
from pathlib import Path
import numpy as np
import pandas as pd
from .io import STATES
from .spectra import spectral_metrics
from .transients import METRICS


def _validated_results(results):
    results = sorted(list(results), key=lambda r: (r.mouse_id, r.recording_id))
    if len({r.recording_id for r in results}) != len(results):
        raise ValueError("Duplicate recording IDs cannot be pooled.")
    paths = [str(Path(r.quality["mat_path"]).resolve()).casefold() for r in results]
    if len(set(paths)) != len(paths):
        raise ValueError("Duplicate MAT paths cannot be pooled under different IDs.")
    if len({json.dumps(r.config.to_dict(), sort_keys=True) for r in results}) > 1:
        raise ValueError("Cannot pool results computed with different analysis settings.")
    return results


def pooled_spectra(results):
    results = _validated_results(results)
    tables = [result.spectra for result in results if not result.spectra.empty]
    columns = ["mouse_id", "state", "frequency_hz", "psd", "n_windows"]
    if not tables:
        return pd.DataFrame(columns=columns)
    data = pd.concat(tables).sort_values(["mouse_id", "recording_id", "state", "frequency_hz"])
    data["weighted"] = data.psd * data.n_windows
    pooled = data.groupby(["mouse_id", "state", "frequency_hz"], as_index=False).agg(
        weighted=("weighted", "sum"), n_windows=("n_windows", "sum")
    )
    pooled["psd"] = pooled.weighted / pooled.n_windows
    return pooled[columns]


def aggregate_subjects(results):
    results = _validated_results(results)
    if not results:
        return pd.DataFrame(columns=["mouse_id"])
    psd = pooled_spectra(results)
    rows = []
    for mouse in sorted({result.mouse_id for result in results}):
        selected = [result for result in results if result.mouse_id == mouse]
        events = pd.concat([result.events for result in selected], ignore_index=True)
        coverage = pd.concat([result.coverage for result in selected], ignore_index=True)
        row = {"mouse_id": mouse, "n_files": len(selected)}
        for state in STATES.values():
            e = events.loc[events.state == state]
            used = e.loc[e.eligible.astype(bool)]
            c = coverage.loc[coverage.state == state]
            total, covered = c.total_seconds.sum(), c.covered_seconds.sum()
            metrics = {
                "total_seconds": total,
                "valid_seconds": c.valid_seconds.sum(),
                "n_bouts": int(c.n_bouts.sum()),
                "n_events_detected": len(e),
                "n_events_used": len(used),
                "n_incomplete_events": int((~e.complete.astype(bool)).sum()),
                "n_crossing_events": int(e.crosses_state.astype(bool).sum()),
                "n_baseline_edge_events": int(e.baseline_edge.astype(bool).sum()),
                "event_retained_fraction": len(used) / len(e) if len(e) else np.nan,
                "spectral_n_windows": int(c.n_windows.sum()),
                "spectral_covered_seconds": covered,
                "spectral_coverage_fraction": (
                    covered / total if total and selected[0].config.spectrum else np.nan
                ),
            }
            metrics.update(
                {
                    name + "_median": float(used[name].median()) if len(used) else np.nan
                    for name in METRICS
                }
            )
            metrics.update(
                spectral_metrics(psd.loc[(psd.mouse_id == mouse) & (psd.state == state)])
            )
            metrics["spectral_status"] = (
                "not_configured"
                if selected[0].config.spectrum is None
                else "ok" if metrics["spectral_n_windows"] else "no_eligible_windows"
            )
            row.update({f"{state}_{name}": value for name, value in metrics.items()})
        rows.append(row)
    return pd.DataFrame(rows)
