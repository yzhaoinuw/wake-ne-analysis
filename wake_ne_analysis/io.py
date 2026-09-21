"""Read only needed MAT variables; never modify or relabel source recordings."""

from dataclasses import dataclass
from pathlib import Path
import numpy as np
from scipy.io import loadmat

STATES = {4: "high_alertness", 5: "low_alertness"}


@dataclass
class Recording:
    path: Path
    mouse_id: str
    recording_id: str
    ne: np.ndarray
    fs: float
    labels: np.ndarray
    start_time: float = 0.0

    @property
    def sample_labels(self):
        seconds = np.floor(np.arange(self.ne.size) / self.fs).astype(int)
        result = np.full(self.ne.size, np.nan)
        covered = seconds < self.labels.size
        result[covered] = self.labels[seconds[covered]]
        return result

    @property
    def identity(self):
        return {
            "mouse_id": self.mouse_id,
            "recording_id": self.recording_id,
            "mat_path": str(self.path),
        }


def _vector(value, name):
    result = np.asarray(value, dtype=float).squeeze()
    if result.ndim > 1:
        raise ValueError(f"{name} must be a single-channel vector.")
    return result.reshape(-1).copy()


def _scalar(value, name):
    if np.asarray(value).size != 1:
        raise ValueError(f"{name} must be scalar.")
    result = float(np.asarray(value).item())
    if not np.isfinite(result):
        raise ValueError(f"{name} must be finite.")
    return result


def load_recording(path, mouse_id, recording_id=None):
    path = Path(path).resolve()
    if not str(mouse_id).strip():
        raise ValueError("An explicit mouse_id is required; IDs are never guessed from filenames.")
    try:
        mat = loadmat(
            path,
            squeeze_me=True,
            variable_names=["ne", "ne_frequency", "fp_frequency", "sleep_scores", "start_time"],
        )
    except NotImplementedError as error:
        raise ValueError(
            "MATLAB v7.3/HDF5 is not supported yet; export the needed variables as -v7 MAT."
        ) from error
    for name in ("ne", "sleep_scores"):
        if name not in mat or np.asarray(mat[name]).size == 0:
            raise ValueError(f"Missing or empty {name} in {path.name}.")
    rates = [_scalar(mat[name], name) for name in ("ne_frequency", "fp_frequency") if name in mat]
    if not rates or rates[0] <= 0:
        raise ValueError("A positive ne_frequency (or fp_frequency) is required.")
    if len(rates) == 2 and not np.isclose(*rates, rtol=1e-9, atol=0):
        raise ValueError("ne_frequency and fp_frequency disagree.")
    labels = _vector(mat["sleep_scores"], "sleep_scores")
    labels[labels == -1] = np.nan
    if np.any(~np.isnan(labels) & ~np.isin(labels, [0, 1, 2, 3, 4, 5])):
        raise ValueError("Unknown sleep label: expected 0..5, -1, or NaN.")
    ne = _vector(mat["ne"], "ne")
    ne[~np.isfinite(ne)] = np.nan
    return Recording(
        path,
        str(mouse_id),
        str(recording_id or path.stem),
        ne,
        rates[0],
        labels,
        _scalar(mat.get("start_time", 0), "start_time"),
    )

def runs(mask):
    edges = np.diff(np.r_[False, np.asarray(mask, dtype=bool), False].astype(int))
    return list(zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)))
