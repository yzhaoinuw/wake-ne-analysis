# Wake-only cluster visualization: NE-excluded follow-up

**Status:** completed on 2026-09-21. This is the matched NE-feature sensitivity
to [`cluster_visualization_wake_only_report.md`](cluster_visualization_wake_only_report.md).
It follows the same Wake-only sampling, graph construction, requested 3/4/5
partitions, alertness terminology, palette, and UMAP axis order. It differs
only by omitting both NE summaries before UMAP fitting and graph clustering.

## Question

Does removing the two saved NE summaries materially change the descriptive
High/Low Alertness organization or the graph partitions of the same Wake
seconds? This is a feature-panel sensitivity check, not a test of whether NE has
no biological relation to alertness.

High Alertness and Low Alertness are the unchanged upstream source labels: score 4
and score 5, respectively. The labels select and
balance the display sample but never enter the graph or clustering.

## Features

The parent Wake-only report uses 29 saved features: 22 EEG summaries, five EMG
summaries, and `ne_mean` plus `ne_slope_ols_per_second`. This matched run uses the
remaining **27 EEG+EMG features** and excludes exactly those two NE columns. It
uses their existing within-recording robust-scaled values; no MAT file was
reopened, no feature was re-extracted, and no remaining value was rescaled.

See the parent report's [Features](cluster_visualization_wake_only_report.md#features)
and the original cluster report's [EEG](cluster_visualization_report.md#appendix-eeg-band-power-features)
and [EMG](cluster_visualization_report.md#appendix-emg-burst-features) appendices
for the feature definitions. The absence of NE here is the only feature-panel
change.

## Sampling

The same seed (`20260918`) sampled up to 100 High Alertness and 100 Low Alertness
seconds per recording from the same ten feature archives: 1,000 seconds of each
source label and 2,000 seconds total. Both labels occur in all ten recordings.
This is a label-balanced display sample, so partition sizes are not natural
prevalence estimates. See the parent Wake-only report's
[Sampling](cluster_visualization_wake_only_report.md#sampling) section for the
selection rationale.

## Spectral clustering of a k-nearest-neighbor graph and UMAP display settings

The 27-dimensional vectors form an unweighted, symmetric 30-nearest-neighbor
graph under Euclidean distance. It has 45,534 undirected edges, one connected
component, minimum symmetric degree 30, and maximum symmetric degree 233.
Spectral clustering creates the requested 3-, 4-, and 5-group partitions. It is
not a supervised kNN classifier and does not cluster UMAP coordinates.

This sensitivity run intentionally generated **UMAP only**, rather than a new
t-SNE fit. UMAP uses the matched settings:
30 neighbors, `min_dist=0.2`, 200 epochs, and seed `20260918`. UMAP 2 is the
horizontal axis and UMAP 1 is vertical, so the high-alertness direction is shown
left to right. The shared source-label palette is High Alertness red
`#E31A1C` / RGB `(227, 26, 28)` and Low Alertness blue `#0072B2` / RGB
`(0, 114, 178)`. UMAP axes remain unitless layout coordinates.

## Results

### Existing High/Low Alertness labels

Without either NE feature, the source-label UMAP retains a compact
Low-Alertness-dominated region on the left and High Alertness-dominated branches
to the right. There is still a shared intermediate region, so the two labels do
not form perfectly isolated UMAP islands. Coordinate positions cannot be compared
numerically with the separate full-feature UMAP fit; the label composition and
matched graph assignments below provide the more useful comparison.

![NE-excluded UMAP display colored by existing High/Low Alertness labels](assets/wake_knn_clusters_ne_excluded_20260921/umap_source_labels.png)

### Three groups

| Spectral cluster | Seconds | Recordings | Source High | Source Low | Reading |
|---|---:|---:|---:|---:|---|
| 1 | 1,755 | 10 | 755 | 1,000 | Broad mixed group containing every sampled Low Alertness second and 75.5% of sampled High Alertness seconds. |
| 2 | 112 | 8 | 112 | 0 | Small High-Alertness-only extreme. |
| 3 | 133 | 5 | 133 | 0 | Small High-Alertness-only extreme with limited recording recurrence. |

![NE-excluded three-group UMAP display](assets/wake_knn_clusters_ne_excluded_20260921/3_clusters/umap_clusters.png)

#### Withheld NE-feature check

The two NE features were withheld from graph construction and clustering, then
compared afterward.  For each recording and cluster, the analysis took the
median of its sampled seconds' saved **within-recording robust-scaled** value;
the table summarizes those recording medians as median (IQR).  Thus these are
relative-to-recording NE positions, rather than pooled raw fluorescence values.

| Spectral cluster | Recordings | `ne_mean` | `ne_slope_ols_per_second` |
|---|---:|---:|---:|
| 1 | 10 | 0.494 (0.340–0.625) | 0.058 (0.007–0.080) |
| 2 | 8 | 0.820 (0.188–0.951) | 0.100 (−0.292–0.717) |
| 3 | 5 | 0.342 (0.152–0.559) | 0.086 (−0.011–0.112) |

Two-sided paired Wilcoxon tests used only recordings containing both clusters,
with Holm correction over the two NE features and all eligible cluster pairs in
this three-group partition.  No comparison was nominally significant (smallest
unadjusted p = 0.250; all Holm-adjusted p = 1.000).  This includes 1 versus 2
(eight matched recordings) and 1 versus 3 (five matched recordings).

### Four groups

| Spectral cluster | Seconds | Recordings | Source High | Source Low | Reading |
|---|---:|---:|---:|---:|---|
| 1 | 1,214 | 10 | 272 | 942 | Low-Alertness-associated broad group. |
| 2 | 97 | 3 | 97 | 0 | Small High-Alertness-only extreme. |
| 3 | 592 | 10 | 534 | 58 | High-Alertness-associated broad group. |
| 4 | 97 | 7 | 97 | 0 | Small High-Alertness-only extreme. |

As in the full-feature analysis, the four-group partition has a broad
Low-Alertness-associated population (77.6% source Low) and a broad
High-Alertness-associated population (90.2% source High), both represented in
all ten recordings. The numbering of the two small high-alertness extremes differs
from the full-feature run; cluster numbers are arbitrary and cannot be compared
by their integer label.

![NE-excluded four-group UMAP display](assets/wake_knn_clusters_ne_excluded_20260921/4_clusters/umap_clusters.png)

#### Withheld NE-feature check

These summaries use the same recording-level robust-scaled procedure as the
three-group check.

| Spectral cluster | Recordings | `ne_mean` | `ne_slope_ols_per_second` |
|---|---:|---:|---:|
| 1 | 10 | 0.429 (0.316–0.576) | 0.051 (0.033–0.069) |
| 2 | 3 | 0.404 (0.067–0.563) | 0.079 (−0.229–0.111) |
| 3 | 10 | 0.380 (0.201–0.506) | 0.107 (−0.011–0.123) |
| 4 | 7 | 0.953 (0.117–1.192) | 0.128 (0.022–0.955) |

Two-sided paired Wilcoxon tests used only recordings containing both clusters;
comparisons with fewer than three shared recordings were not tested.  Holm
correction covered both NE features and all eligible cluster pairs in this
four-group partition.  No comparison was nominally significant (smallest
unadjusted p = 0.109; all Holm-adjusted p = 1.000).  In particular, the two
broad groups recurring in all ten recordings, 1 and 3, had p = 0.375 for
`ne_mean` and p = 1.000 for `ne_slope_ols_per_second` before correction.

### Five groups

| Spectral cluster | Seconds | Recordings | Source High | Source Low | Reading |
|---|---:|---:|---:|---:|---|
| 1 | 1,218 | 10 | 271 | 947 | Low-Alertness-associated broad group. |
| 2 | 95 | 3 | 95 | 0 | Rare High-Alertness-only extreme. |
| 3 | 63 | 3 | 63 | 0 | Rare High-Alertness-only extreme. |
| 4 | 473 | 10 | 422 | 51 | High-Alertness-associated broad group. |
| 5 | 151 | 9 | 149 | 2 | Additional High-Alertness-associated branch. |

The five-group result likewise retains broad Low- and High-Alertness-associated
populations across all ten recordings, an additional High-Alertness-associated
branch across nine recordings, and two rare high-alertness extremes with only
three-recording recurrence.

![NE-excluded five-group UMAP display](assets/wake_knn_clusters_ne_excluded_20260921/5_clusters/umap_clusters.png)

#### Withheld NE-feature check

These summaries again use one median per recording and cluster before the
across-recording summary.

| Spectral cluster | Recordings | `ne_mean` | `ne_slope_ols_per_second` |
|---|---:|---:|---:|
| 1 | 10 | 0.430 (0.315–0.576) | 0.045 (0.029–0.097) |
| 2 | 3 | 0.451 (0.082–0.586) | 0.086 (−0.225–0.111) |
| 3 | 3 | 1.007 (0.984–1.473) | 0.078 (−0.040–0.146) |
| 4 | 10 | 0.412 (0.208–0.488) | 0.096 (0.015–0.151) |
| 5 | 9 | 0.319 (0.209–0.764) | 0.148 (−0.036–0.223) |

Two-sided paired Wilcoxon tests used only pairs represented in at least three
recordings, with Holm correction over both NE features and all eligible cluster
pairs in this five-group partition.  No comparison was nominally significant
(smallest unadjusted p = 0.250; all Holm-adjusted p = 1.000).  The two broad
groups occurring in all ten recordings, 1 and 4, had p = 0.625 for `ne_mean`
and p = 1.000 for `ne_slope_ols_per_second` before correction.

## Comparison with the full EEG+EMG+NE panel

For the identical 2,000 sampled point identities, the NE-excluded and
full-feature graph partitions have high label-invariant adjusted Rand agreement:
0.978 for three groups, 0.964 for four groups, and 0.959 for five groups.
Together with the closely matching source-label compositions above, this means
that removing these two per-second NE summaries does **not materially change this
particular 29-feature Wake clustering result**.

This does not show that NE is biologically irrelevant. It only says that, in this
within-recording robust-scaled, EMG-inclusive one-second representation, the two
available NE summaries are not necessary to reproduce the displayed partitions.
EMG remains in both panels and is entangled with the source alertness labels;
other NE timescales, transformations, features, or independent behavioral
measurements were not tested.

## Interpretation caveat

The NE-excluded sensitivity reinforces the parent report's central limitation:
the recurring High- and Low-Alertness-associated organization is an
EMG-associated pattern in the joint feature space, not independent proof of
distinct Wake biology. Small pure High-Alertness groups show purity for a subset;
they do not show complete High/Low separability without near-complete coverage and
absence of cross-label contamination. Consecutive seconds and recordings are not
independent observations, and neither UMAP appearance nor graph-cluster count is
a biological cluster statistic.

## Fairer follow-up

Retain this NE-excluded analysis as a feature-panel sensitivity result. Before
naming a Wake subtype or making an alertness-separability claim, predeclare graph
parameter/seed stability and a recording-held-out evaluation; inspect the small
High-Alertness-only groups against raw EMG/envelope traces; and use an independent
non-EMG behavioral or physiological measure where available.

## Reproducibility and retained audits

The user-generated NE-excluded run was:

```powershell
conda activate ne_umap

python scripts\plot_wake_knn_clusters.py `
  --feature-dir data\derived_features\features_29 `
  --results-dir results\wake_knn_clusters_ne_excluded_20260921 `
  --figures-dir writeups\assets\wake_knn_clusters_ne_excluded_20260921 `
  --n-clusters 3 4 5 `
  --exclude-ne-features `
  --umap-only
```

The ignored `results/wake_knn_clusters_ne_excluded_20260921/` directory retains
the configuration, sampled point identities, graph audit, per-cluster source-label
and recording composition, and 27-feature median audit. The adjusted Rand values
above compare the matched point identities in that directory with the existing
full-feature result; they are descriptive agreement measures, not a held-out
validation statistic.
