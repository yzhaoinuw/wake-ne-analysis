# Expanded 29-feature embedding runs

These four descriptive runs use only the existing
`features/features_29/*.npz` archives. Every archive's `X_robust_scaled` matrix was
scaled within its recording during feature extraction; the script does not reopen a
MAT file, extract a feature again, relabel a second, clip a finite value, or apply a
second scaling step.

All runs fit PCA, t-SNE, and UMAP without labels. Labels only determine the
predeclared balanced display sample and the plot colour after fitting. Each output
directory must be new or empty; `run.json` records the feature columns, scope,
archive list, state exclusion, and settings.

MA is excluded before sampling and fitting in every run. In the Wake-only runs,
Active Wake and Quiet Wake are combined into one `Wake (Active + Quiet)` class
before sampling and fitting; `source_state` remains in `embedding_points.csv` for
audit but is not used for fitting or colouring. This answers whether the combined
Wake observations show internal geometry, not whether the existing Active/Quiet
labels are separable.

Activate the existing embedding environment and run these commands from the
repository root:

```powershell
conda activate ne_umap

# All 29 features; NREM, REM, Active Wake, and Quiet Wake (no MA).
python scripts\plot_expanded_feature_embeddings.py `
  --feature-dir features\features_29 `
  --feature-variant all `
  --analysis-scope all_stages_no_ma `
  --results-dir results\expanded_embedding\all_features_all_stages_no_ma `
  --figures-dir docs\assets\expanded_embedding\all_features_all_stages_no_ma

# EEG + NE only; NREM, REM, Active Wake, and Quiet Wake (no MA).
python scripts\plot_expanded_feature_embeddings.py `
  --feature-dir features\features_29 `
  --feature-variant no_emg `
  --analysis-scope all_stages_no_ma `
  --results-dir results\expanded_embedding\no_emg_all_stages_no_ma `
  --figures-dir docs\assets\expanded_embedding\no_emg_all_stages_no_ma

# All 29 features; only combined Wake (Active + Quiet).
python scripts\plot_expanded_feature_embeddings.py `
  --feature-dir features\features_29 `
  --feature-variant all `
  --analysis-scope wake_only `
  --results-dir results\expanded_embedding\all_features_wake_only `
  --figures-dir docs\assets\expanded_embedding\all_features_wake_only

# EEG + NE only; only combined Wake (Active + Quiet).
python scripts\plot_expanded_feature_embeddings.py `
  --feature-dir features\features_29 `
  --feature-variant no_emg `
  --analysis-scope wake_only `
  --results-dir results\expanded_embedding\no_emg_wake_only `
  --figures-dir docs\assets\expanded_embedding\no_emg_wake_only
```

`all` uses 22 EEG bands, five EMG features, and two NE features. `no_emg` removes
every feature whose documented name begins with `emg_`, leaving 22 EEG and two NE
features. Since the Active/Quiet labels originate from EMG activity, the no-EMG runs
are the less circular labelled-state comparison; neither feature variant makes a
nonlinear embedding a cluster test or biological inference. The full wide-band
panel, EMG burst features, and NE slope remain exploratory and require the QC and
sensitivity review in `treaty_docs/next_steps.md` before interpretation.
