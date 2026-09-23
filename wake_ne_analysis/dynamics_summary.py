"""Pooled-seconds dynamics screen and retained summary helpers.

Pooled p-values ignore temporal and recording dependence and are nominal
exploratory comparisons, not independent-animal inference.
"""

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu, wilcoxon

from .io import STATES
from .ne_dynamics import FEATURE_NAMES


def summarize_features(arrays, unit_id, condition="unspecified"):
    """One median per feature/state/unit, with missing and available counts."""
    rows = []
    for label, state in STATES.items():
        selected = arrays["X"][arrays["label"] == label]
        for index, feature in enumerate(FEATURE_NAMES):
            values = selected[:, index]
            values = values[np.isfinite(values)]
            quantiles = np.quantile(values, [0.25, 0.5, 0.75]) if len(values) else [np.nan] * 3
            rows.append({
                "unit_id": unit_id, "condition": condition, "state": state,
                "feature": feature, "n_state_seconds": len(selected),
                "n_valid_seconds": len(values), "n_missing_seconds": len(selected) - len(values),
                "q25": quantiles[0], "median": quantiles[1], "q75": quantiles[2],
            })
    return pd.DataFrame(rows)


def holm_adjust(p_values):
    """Holm family includes all declared features, even untestable ones."""
    p = np.asarray(p_values, dtype=float)
    order = np.argsort(np.where(np.isfinite(p), p, 1.0))
    ranked = np.where(np.isfinite(p[order]), p[order], 1.0)
    adjusted = np.minimum(1, np.maximum.accumulate(ranked * np.arange(len(p), 0, -1)))
    result = np.empty_like(p)
    result[order] = adjusted
    result[~np.isfinite(p)] = np.nan
    return result


def pool_records(records):
    """Concatenate completed features, never source signals or window histories."""
    if not records:
        raise ValueError("At least one recording is required.")
    return {key: np.concatenate([arrays[key] for arrays in records.values()])
            for key in ("X", "label")}


def pooled_comparisons(records):
    """Every finite second has equal weight, without balancing by source file.

    Two-sided asymptotic Mann-Whitney U uses tie and continuity corrections.
    Rank-biserial effect = 2*U/(n_high*n_low)-1: positive means higher in High.
    This tests distributions, not solely medians. Holm covers the four features
    but cannot repair the independence assumption or cross-file scale differences.
    """
    arrays = pool_records(records)
    rows = []
    for index, feature in enumerate(FEATURE_NAMES):
        row = {"feature": feature, "unit": "pooled_second"}
        groups = []
        for label, name in ((4, "high"), (5, "low")):
            values = arrays["X"][arrays["label"] == label, index]
            finite = values[np.isfinite(values)]
            groups.append(finite)
            row.update({f"n_{name}": len(finite), f"n_{name}_missing": len(values) - len(finite)})
            quantiles = np.quantile(finite, [.05, .25, .5, .75, .95]) if len(finite) else [np.nan] * 5
            for statistic, value in zip(("q05", "q25", "median", "q75", "q95"), quantiles):
                row[f"{name}_{statistic}"] = value
        high, low = groups
        row.update(p_value=np.nan, u_statistic=np.nan, rank_biserial=np.nan)
        if len(high) and len(low):
            test = mannwhitneyu(high, low, alternative="two-sided", method="asymptotic")
            row.update(p_value=float(test.pvalue), u_statistic=float(test.statistic),
                       rank_biserial=2 * float(test.statistic) / (len(high) * len(low)) - 1)
        row["median_high_minus_low"] = row["high_median"] - row["low_median"]
        rows.append(row)
    result = pd.DataFrame(rows)
    result["p_holm"] = holm_adjust(result.p_value)
    return result


def paired_comparisons(summaries, unit="recording", seed=20260923):
    """Two-sided Wilcoxon on paired state medians; fixed four-feature Holm family.

    The effect is median(High median - Low median), with a percentile bootstrap
    interval resampling paired units (10,000 draws). Recording intervals and
    p-values remain descriptive if units include repeated sessions from mice.
    All-zero differences have p=1. Fewer than two pairs have no test or interval.
    """
    rows = []
    if summaries.duplicated(["unit_id", "condition", "feature", "state"]).any():
        raise ValueError("Duplicate unit/condition/feature/state summaries.")
    for condition, group in summaries.groupby("condition", sort=True):
        condition_rows = []
        for index, feature in enumerate(FEATURE_NAMES):
            table = group.loc[group.feature == feature].pivot(
                index="unit_id", columns="state", values="median"
            ).reindex(columns=list(STATES.values())).dropna()
            high = table.high_alertness.to_numpy()
            low = table.low_alertness.to_numpy()
            differences = high - low
            p, lower, upper = np.nan, np.nan, np.nan
            if len(differences) >= 2:
                p = 1.0 if np.all(differences == 0) else float(wilcoxon(differences).pvalue)
                rng = np.random.default_rng(seed + index)
                boot = np.median(rng.choice(differences, (10000, len(differences))), axis=1)
                lower, upper = np.quantile(boot, [0.025, 0.975])
            condition_rows.append({
                "unit": unit, "condition": condition, "feature": feature,
                "n_pairs": len(differences),
                "high_median": float(np.median(high)) if len(high) else np.nan,
                "low_median": float(np.median(low)) if len(low) else np.nan,
                "median_high_minus_low": float(np.median(differences)) if len(differences) else np.nan,
                "difference_ci_low": lower, "difference_ci_high": upper,
                "n_high_greater": int((differences > 0).sum()),
                "n_low_greater": int((differences < 0).sum()),
                "n_equal": int((differences == 0).sum()), "p_value": p,
            })
        adjusted = holm_adjust([row["p_value"] for row in condition_rows])
        for row, p in zip(condition_rows, adjusted):
            row["p_holm"] = p
        rows.extend(condition_rows)
    return pd.DataFrame(rows)


def pooled_mouse_summaries(records, metadata):
    """Pool seconds across files before medians, separately for each condition.

    Metadata must explicitly identify every included recording. No identities or
    conditions are inferred from filenames, and no session is treated as a mouse.
    """
    required = ["recording_id", "mouse_id", "condition"]
    if not set(required).issubset(metadata.columns):
        raise ValueError(f"Metadata requires columns {required}.")
    if metadata[required].isna().any().any() or (metadata[required] == "").any().any():
        raise ValueError("Metadata identities and conditions must not be empty.")
    if metadata.recording_id.duplicated().any():
        raise ValueError("Metadata has duplicate recording IDs.")
    if not set(records).issubset(set(metadata.recording_id)):
        raise ValueError("Metadata must identify every included recording.")
    rows = []
    for (mouse, condition), group in metadata.groupby(["mouse_id", "condition"], sort=True):
        names = [name for name in group.recording_id if name in records]
        if not names:
            continue
        pooled = {key: np.concatenate([records[name][key] for name in names])
                  for key in ("X", "label")}
        summary = summarize_features(pooled, mouse, condition)
        summary["n_recordings"] = len(names)
        rows.append(summary)
    return pd.concat(rows, ignore_index=True)
