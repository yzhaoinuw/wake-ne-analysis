# Reusable four-feature matrices

`features_4/` contains one compressed NumPy archive (`.npz`) per input MAT
recording. Its filename has the same stem as the source MAT file, so
`mouse3_day1.mat` becomes `features_4/mouse3_day1.npz`. The directory name
reserves `features_5/`, `features_6/`, and so on for future feature sets without
changing this four-feature contract.

Each archive contains only complete, finite, final-labelled score seconds. It does
not include raw EEG, EMG, or NE samples.

| Key | Shape/type | Meaning |
|---|---|---|
| `X` | `(n_seconds, 4)`, `float32` | Raw feature matrix. |
| `X_robust_scaled` | `(n_seconds, 4)`, `float32` | Matrix scaled within the recording as `(X - scaling_median) / scaling_iqr`; use this for the documented UMAP configuration and as the default input for cross-recording PCA/t-SNE. |
| `feature_names` | four strings | Column order for both matrices. |
| `second` | `(n_seconds,)`, `int32` | Zero-based score-second index in the source recording. |
| `label` | `(n_seconds,)`, `int8` | Final label: 1 NREM, 2 REM, 3 MA, 4 Active Wake, 5 Quiet Wake. Keep this out of unsupervised fitting; use it only to colour/describe the result. |
| `scaling_median`, `scaling_iqr` | `(4,)`, `float32` | Exact values used to make `X_robust_scaled`. |
| `recording_id`, `source_mat_file`, `source_mat_path` | strings | Source identity and provenance. |
| `n_label_seconds`, `n_complete_multimodal_seconds`, `eeg_frequency_hz`, `ne_frequency_hz` | scalars | Coverage and saved-rate metadata. |

```python
from pathlib import Path
import numpy as np

path = Path("features/features_4/mouse3_day1.npz")
with np.load(path, allow_pickle=False) as feature_file:
    X = feature_file["X_robust_scaled"]       # (seconds, 4), for PCA/t-SNE/UMAP
    labels = feature_file["label"]             # plotting metadata only
    seconds = feature_file["second"]
    names = feature_file["feature_names"].tolist()
```

The four columns are, in order: log10 EEG delta (0.5--4 Hz) power, log10 EEG
theta (6--9 Hz) power, per-second mean-centred EMG RMS, and the per-second mean
saved processed NE (% delta-F/F). These files preserve all finite feature rows;
they do not silently remove or clip extreme but finite values. Review feature QC
before interpreting an embedding as a state-cluster result.
