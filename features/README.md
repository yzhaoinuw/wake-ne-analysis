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

## Expanded `features_29` archives

`features_29/` is a separate exploratory feature definition; it does not replace
the four-feature UMAP contract above. Each source MAT file has one `.npz` archive
with 29 columns in `feature_names`:

- **EEG (22):** log10 power for 0.5--5 Hz and consecutive 5-Hz bands through
  95--100 Hz, plus exact Sleep Scoring reference bands `>1--4 Hz` and `>4--8 Hz`.
  Power uses a one-second Hann periodogram with density scaling and strict
  lower-edge/inclusive upper-edge bin assignment, so bands do not double-count a
  boundary bin. These are compact one-second summaries, not high-resolution spectra.
- **EMG (5):** the existing mean-centred native RMS; 20--`min(200, 0.45*fs)` Hz
  detrended, zero-phase filtered RMS; burst-onset count; fraction of the second
  classified as a burst; and the maximum 75-ms RMS-envelope value. A burst is an
  envelope excursion above the recording median plus `3 * 1.4826 * MAD`, after
  joining valid gaps up to 50 ms and discarding bursts shorter than 50 ms. The
  filter is applied in 120-s chunks with 1-s context discarded at each edge. It is
  in the same preprocessing family as Sleep Scoring's EMG RMS but is not
  bit-identical to whole-recording filtering.
- **NE (2):** mean saved processed NE (% delta-F/F) and ordinary-least-squares
  slope within the second (% delta-F/F per second). No additional NE smoothing,
  baseline subtraction, or event detection is applied.

`X` is the raw 29-column matrix. `X_robust_scaled` first centres each feature by
its recording median and divides by its IQR. Sparse burst features can have a zero
IQR; for nonconstant cases only, `scaling_effective_scale` falls back to the
recording standard deviation. Constant features are stored as zero after centring
with an effective scale of one. `scaling_iqr`, `scaling_used_standard_deviation`,
and `scaling_constant_feature` preserve that provenance. `metadata_json` records
the exact provisional thresholds, rates, row counts, and source identity.

```python
from pathlib import Path
import json
import numpy as np

path = Path("features/features_29/mouse3_day1.npz")
with np.load(path, allow_pickle=False) as feature_file:
    X = feature_file["X_robust_scaled"]
    labels = feature_file["label"]
    names = feature_file["feature_names"].tolist()
    metadata = json.loads(feature_file["metadata_json"].item())
```

The 5-Hz EEG panel, EMG-burst threshold, and within-second NE slope are exploratory
features. Inspect raw EMG/envelope examples and perform parameter sensitivity before
using their apparent clusters or state differences as biological conclusions.
