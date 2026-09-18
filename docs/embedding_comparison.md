# PCA, t-SNE, and UMAP feature-embedding comparison

This is a descriptive comparison of three two-dimensional projections of the
same saved, one-second EEG + EMG + NE feature observations. It is not a new sleep
scorer and does not make seconds within a recording independent observations.

## Inputs and sampling

The command reads the existing `features/features_4/*.npz` archives directly. It
uses their `X_robust_scaled` matrix: the four predeclared features have already
been centred by each recording's median and divided by its IQR. It does not reopen
the MAT files, re-extract a feature, relabel a second, clip an outlier, or apply
another normalization.

Each embedding receives the **same** fixed-seed balanced sample: at most 100
seconds for every available final state within every recording. MA is removed
before sampling and before PCA, t-SNE, or UMAP fitting, because it is a manual
override rather than a physiological state in this comparison. With the present ten
archives, a new baseline run therefore contains up to 4,000 points: 1,000 each
NREM, REM, Active Wake, and Quiet Wake. This prevents long states from dominating a
picture while allowing substantially more points than the 480-point first UMAP.
Raise or lower `--max-points-per-label-per-recording` to change the display density.

The final sleep label is withheld from PCA, t-SNE, and UMAP fitting; it is used only
afterward to colour the resulting coordinates. Since the Active/Quiet labels were
defined using a related EMG-RMS quantity, a panel containing the EMG feature cannot
independently validate that distinction.

## Methods and colour contract

- PCA is a linear variance projection.
- t-SNE uses perplexity 30, PCA initialization, automatic learning rate, 1,000
  optimization iterations, and seed `20260917`.
- UMAP uses Euclidean distance, 30 neighbours, `min_dist=0.2`, 200 epochs, and the
  same seed. Its axes are unitless layout coordinates, as are t-SNE's axes.

Every panel uses the exact stage colours in
`sleep_scoring/app_src/config.py`:

| State | Colour |
|---|---|
| NREM | `#FB7C7C` (RGB 251, 124, 124) |
| REM | `#7BFB7B` (RGB 123, 251, 123) |
| MA | `#FFFF00` (RGB 255, 255, 0) |
| Active Wake | `#E69F00` |
| Quiet Wake | `#56B4E9` |

## Baseline joint-feature run

Activate the working environment and run this from the repository root:

```powershell
conda activate ne_umap
python scripts\plot_feature_embeddings.py `
  --feature-dir features\features_4 `
  --results-dir results\embedding_comparison\joint_no_ma_4000 `
  --figures-dir docs\assets\embedding_comparison\joint_no_ma_4000
```

The output CSV contains the same sampled rows and all six coordinates
(`pca_1/2`, `tsne_1/2`, and `umap_1/2`). `run.json` records the archives and all
settings. The three presentation PNGs are named `pca.png`, `tsne.png`, and
`umap.png`; numerical artifacts stay in ignored `results/`, never `outputs/`.

The separate-figure captions are:

> Label-coloured [PCA/t-SNE/UMAP] embedding of the same balanced sample of
> one-second EEG + EMG + NE observations. The default current sample contains up to
> 1,000 NREM, 1,000 REM, 1,000 Active Wake, and 1,000 Quiet Wake seconds; MA was
> excluded before sampling and fitting,
> capped at 100 seconds per available state per recording. Labels were not used to
> fit the embedding. For the joint panel, EMG is related to the Active/Quiet label
> rule, so the visualization is descriptive rather than independent validation of
> that split.

For a denser display, for example 200 points per available state per recording,
change only the cap and use a new run name:

```powershell
  --max-points-per-label-per-recording 200
```

This would yield up to 9,600 points for the current archives. Its t-SNE/UMAP run
will naturally take longer, so retain the default 4,800-point figure first as the
comparison baseline.

## Fairer EEG + NE follow-up

The appropriate next comparison omits `emg_centered_rms` altogether. It selects
only the two EEG band-power features and mean NE from the same archives—there is no
need to extract files again. This removes the direct feature overlap with the
automatic Active/Quiet EMG-RMS split, while retaining sleep-relevant EEG and NE
information. It does not make the labels biologically independent, but it is a much
fairer test of whether the states occupy different regions beyond the defining EMG
quantity.

Run it separately, with distinct destinations:

```powershell
python scripts\plot_feature_embeddings.py `
  --feature-dir features\features_4 `
  --feature-set eeg_ne `
  --results-dir results\embedding_comparison\eeg_ne_4800 `
  --figures-dir docs\assets\embedding_comparison\eeg_ne_4800
```
