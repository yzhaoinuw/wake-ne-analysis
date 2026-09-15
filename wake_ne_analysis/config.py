"""Explicit, serializable analysis choices; pilot settings need data review."""

from dataclasses import asdict, dataclass, field
import json
import math
from pathlib import Path


@dataclass(frozen=True)
class SpectrumConfig:
    window_seconds: float
    fmin: float
    fmax: float
    minimum_cycles: float = 3.0

    def __post_init__(self):
        if not all(math.isfinite(v) and v > 0 for v in asdict(self).values()):
            raise ValueError("Spectral settings must be finite and positive.")
        if self.fmin >= self.fmax:
            raise ValueError("Spectral fmin must be less than fmax.")
        if self.window_seconds * self.fmin < self.minimum_cycles:
            raise ValueError("Window is too short for minimum_cycles at fmin.")


@dataclass(frozen=True)
class TransientConfig:
    baseline_window_seconds: float = 60.0
    baseline_percentile: float = 20.0
    min_prominence: float = 0.5  # delta-F/F percentage points; provisional
    noise_multiplier: float = 3.0
    min_peak_distance_seconds: float = 1.0
    assignment: str = "contained"  # or "peak" for explicitly contextual summaries

    def __post_init__(self):
        for name in ("baseline_window_seconds", "min_prominence", "min_peak_distance_seconds"):
            if not math.isfinite(getattr(self, name)) or getattr(self, name) <= 0:
                raise ValueError(f"{name} must be finite and positive.")
        if not math.isfinite(self.noise_multiplier) or self.noise_multiplier < 0:
            raise ValueError("noise_multiplier must be nonnegative.")
        if not 0 <= self.baseline_percentile < 50:
            raise ValueError("baseline_percentile must be in [0, 50).")
        if self.assignment not in {"contained", "peak"}:
            raise ValueError("assignment must be contained or peak.")


@dataclass(frozen=True)
class AnalysisConfig:
    spectrum: SpectrumConfig | None = None  # choose after usable-data review
    transients: TransientConfig = field(default_factory=TransientConfig)
    require_fine_wake: bool = True
    preprocessing_downsample_factor: int = 100
    preprocessing_filter_samples: int = 1000

    def __post_init__(self):
        for value in (self.preprocessing_downsample_factor, self.preprocessing_filter_samples):
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                raise ValueError(
                    "Preprocessing factor and filter length must be positive integers."
                )

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_json(cls, path):
        values = json.loads(Path(path).read_text(encoding="utf-8"))
        spectrum = values.pop("spectrum", None)
        transients = values.pop("transients", {})
        return cls(
            spectrum=SpectrumConfig(**spectrum) if spectrum is not None else None,
            transients=TransientConfig(**transients),
            **values,
        )
