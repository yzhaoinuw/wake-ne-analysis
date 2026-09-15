"""Independent NE analysis of labeled Active/Quiet Wake MAT recordings."""

__version__ = "0.1.0"

from .config import AnalysisConfig, SpectrumConfig, TransientConfig
from .io import load_recording, read_manifest
from .pipeline import analyze_file, analyze_files, analyze_recording
from .aggregation import aggregate_subjects, pooled_spectra
from .spectra import compute_spectrum_file
from .transients import compute_transients_file
from .validation import validate_file
