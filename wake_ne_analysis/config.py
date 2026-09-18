"""Explicit spectral settings used by the current recording report."""

from dataclasses import asdict, dataclass
import math


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
