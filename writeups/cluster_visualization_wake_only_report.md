# Wake-only cluster visualization follow-up

**Status:** completed on 2026-09-18; presentation updated on 2026-09-21. This
is a focused follow-up to
[`cluster_visualization_report.md`](cluster_visualization_report.md), prompted by
the request to recluster only the two Wake source labels with the complete
EEG+EMG+NE feature set. It does not replace the original all-stage and
combined-Wake descriptive maps.

## Question

Do the full 29-feature vectors of seconds already labeled High Alertness or Low
Alertness form recurring groups when those labels are excluded from the clustering
step? The same full-space k-nearest-neighbor graph is partitioned into 3,
4, and 5 groups rather than selecting one resolution in advance.

High Alertness and Low Alertness are the final source labels: score 4 and score 5,
respectively. The terminology does not relabel a second or establish an
independent behavioral measurement.

This is a descriptive, label-audited clustering exercise, not a test of an
independently derived alertness distinction or a claim that each partition
identifies biological Wake subtypes.

## Features

This follow-up uses all 29 saved features: 22 EEG band-power summaries, five EMG
summaries, and two NE summaries. It reads the same already
within-recording-robust-scaled feature archives as the parent report and neither
reopens raw MAT files nor re-extracts, relabels, or rescales a second. The exact
feature definitions, including the one-second EEG epoch convention and EMG burst
definition, are in the parent report's [Features](cluster_visualization_report.md#features),
[EEG appendix](cluster_visualization_report.md#appendix-eeg-band-power-features),
and [EMG appendix](cluster_visualization_report.md#appendix-emg-burst-features).

EMG is intentionally retained here. The parent report showed that conspicuous
Wake geometry was not retained in the EEG+NE-only representation; the present
question is explicitly about organization in the joint EEG+EMG+NE feature space.

## Sampling

Only final-labeled High Alertness and Low Alertness seconds were eligible. With
seed `20260918`, the analysis sampled up to 100 seconds **per source label per
recording** from each of ten feature archives, yielding 2,000 points: 1,000 source
High Alertness and 1,000 source Low Alertness seconds, each represented in all ten
recordings. This balances source-label representation for the audit and figure;
the resulting cluster sizes are therefore not estimates of natural state
prevalence.

The upstream source label selected and balanced the sample, but it did **not**
enter the kNN graph or the clustering. It is shown afterward only to assess how
the unsupervised groups relate to the existing labels.

## Display labels, palette, and settings

The source-label panels use the following high-saturation palette for the two
states shown in this report.

| State | RGB | Hex | Use |
|---|---|---|---|
| High Alertness | `(227, 26, 28)` | `#E31A1C` | High-saturation red |
| Low Alertness | `(0, 114, 178)` | `#0072B2` | High-saturation blue |

The spectral-cluster panels use separate arbitrary categorical colors: those colors
identify graph partitions and do not represent alertness labels.

For the requested left-to-right presentation, UMAP 2 is horizontal and UMAP 1 is
vertical. In the source-label UMAP panel, High Alertness predominates toward the
right-hand branches and Low Alertness toward the left-hand compact region. t-SNE
and UMAP are display-only views of the same sampled feature vectors. t-SNE uses
perplexity 30 and 1,000 iterations; UMAP uses 30 neighbors, `min_dist=0.2`, 200
epochs, and seed `20260918`. Their axes are unitless learned layout coordinates;
see the parent report's [dimension-reduction settings](cluster_visualization_report.md#dimension-reduction-settings)
for the broader presentation context.

## Spectral clustering of a k-nearest-neighbor graph

For the 2,000 sampled 29-dimensional vectors, the analysis first computes ordinary
Euclidean distances in the saved robust-scaled feature space. It connects every
point to its 30 closest points, then makes the graph **symmetric**: an undirected
edge is kept when either point selected the other as a nearest neighbor. The source
High/Low Alertness labels do not enter these distance or edge calculations. The
resulting unweighted graph had 45,893 edges and one connected component.

Spectral clustering then converts this network structure into groups. It uses the
graph adjacency and degree structure to obtain a low-dimensional spectral
representation in which strongly connected points tend to lie together and weakly
connected regions separate. A final k-means step assigns rows **in that spectral
representation** to the requested 3, 4, or 5 groups. Therefore this is not k-means
of the original 29 features, not a supervised kNN classifier, and not clustering
of t-SNE or UMAP coordinates. “kNN-graph clustering” was a loose shorthand; the
precise name is spectral clustering of a symmetric k-nearest-neighbor graph.

The specified group count is a display resolution, not a learned or validated
biological number of Wake states. Cluster integers are arbitrary within each
resolution.

## Results

### Existing High/Low Alertness labels on the display maps

The source labels, not used for graph construction or partitioning, occupy a
similar broad ordering in both displays: most Low Alertness seconds lie in the
large lower/left region, whereas High Alertness supplies the rightward and upper
branches as well as some of the shared central region. The overlap matters: the
labels do not map onto two perfectly separated islands.

![t-SNE display colored by existing High/Low Alertness labels](assets/wake_knn_clusters_20260918/tsne_source_labels.png)

![UMAP display colored by existing High/Low Alertness labels](assets/wake_knn_clusters_20260918/umap_source_labels.png)

### Three groups

| Spectral cluster | Seconds | Recordings | Source High | Source Low | Reading |
|---|---:|---:|---:|---:|---|
| 1 | 1,763 | 10 | 763 | 1,000 | Broad mixed group containing every sampled Low Alertness second and 76.3% of sampled High Alertness seconds. |
| 2 | 111 | 8 | 111 | 0 | Small High-Alertness-only extreme. |
| 3 | 126 | 4 | 126 | 0 | Small High-Alertness-only extreme with limited recording recurrence. |

At this coarse resolution, the graph separates two compact High-Alertness-only
ends from a broad central population rather than separating all High and Low
Alertness seconds.

![Three-group t-SNE display](assets/wake_knn_clusters_20260918/3_clusters/tsne_clusters.png)

![Three-group UMAP display](assets/wake_knn_clusters_20260918/3_clusters/umap_clusters.png)

### Four groups

| Spectral cluster | Seconds | Recordings | Source High | Source Low | Reading |
|---|---:|---:|---:|---:|---|
| 1 | 1,227 | 10 | 280 | 947 | Low-Alertness-associated broad group. |
| 2 | 97 | 7 | 97 | 0 | Small High-Alertness-only extreme. |
| 3 | 96 | 3 | 96 | 0 | Small High-Alertness-only extreme with limited recording recurrence. |
| 4 | 580 | 10 | 527 | 53 | High-Alertness-associated broad group. |

The four-group partition is the clearest descriptive resolution. It divides the
former broad group into a Low-Alertness-associated population (77.2% source Low)
and a High-Alertness-associated population (90.9% source High), and both occur in
every recording. The two smaller High-Alertness-only groups remain; one occurs in
only three recordings.

![Four-group t-SNE display](assets/wake_knn_clusters_20260918/4_clusters/tsne_clusters.png)

![Four-group UMAP display](assets/wake_knn_clusters_20260918/4_clusters/umap_clusters.png)

### Five groups

| Spectral cluster | Seconds | Recordings | Source High | Source Low | Reading |
|---|---:|---:|---:|---:|---|
| 1 | 1,227 | 10 | 274 | 953 | Low-Alertness-associated broad group. |
| 2 | 93 | 3 | 93 | 0 | Rare High-Alertness-only extreme. |
| 3 | 64 | 3 | 64 | 0 | Rare High-Alertness-only extreme. |
| 4 | 464 | 10 | 421 | 43 | High-Alertness-associated broad group. |
| 5 | 152 | 9 | 148 | 4 | Additional High-Alertness-associated branch. |

At five groups, the Low-Alertness-associated and main High-Alertness-associated
populations remain across all ten recordings. A further High-Alertness-associated
branch appears in nine recordings, but two other High-Alertness-only groups now
occur in only three recordings each. Five groups therefore add descriptive
granularity, not a predeclared or validated number of Wake states. Cluster numbers
are arbitrary within each partition and must not be treated as matched identities
across the three resolutions.

![Five-group t-SNE display](assets/wake_knn_clusters_20260918/5_clusters/tsne_clusters.png)

![Five-group UMAP display](assets/wake_knn_clusters_20260918/5_clusters/umap_clusters.png)

## Interpretation caveat

The strongest result is modest: in this balanced sample, the joint feature space
contains a recurring Low-Alertness-associated population and a recurring
High-Alertness-associated population, each represented in all ten recordings at
the four- and five-group resolutions. The smaller High-Alertness-only groups are
visually compact but have incomplete recording recurrence, so they are not yet
defensible as general Wake subtypes.

A pure small cluster is not, by itself, evidence that High and Low Alertness are
fully separable. A pure High-Alertness-only cluster may have high **purity** but
contain only a small fraction of all High Alertness seconds; it then describes a
distinctive subset rather than the whole source class. Strong label separation
would require both purity and **coverage**: collectively, the High-associated
clusters would contain essentially every High second and no Low seconds, and the
Low-associated clusters would do the converse. The present four-group result does
not meet this standard: the Low-associated group contains 947 Low and 280 High
seconds, and the High-associated group contains 527 High and 53 Low seconds. It
therefore shows organized but overlapping source-label populations.

This association is not independent validation of the source labels. Those labels
were produced upstream from within-recording EMG activity, and this analysis
deliberately includes five EMG features. It is therefore unsurprising that the
partitions organize with the labels; the finding should be described as an
**EMG-associated organization of the joint feature space**, not as proof of
distinct Wake biology. The parent report's EMG-free comparison remains the
critical guardrail: it did not show similarly conspicuous Wake structure.

Nor do the figures establish a statistically optimal cluster count. Consecutive
seconds are correlated, recordings may not be independent mice, and graph
parameters, seed stability, and recording-held-out assignment have not been
tested. t-SNE/UMAP separations, point density, and apparent branch boundaries are
not cluster statistics.

## Fairer follow-up

Before naming a Wake subtype, predeclare a cluster selection and stability rule;
repeat the graph construction across sensible neighbor counts and seeds; and
evaluate whether a cluster assignment or classifier trained on one set of
recordings generalizes to held-out recordings. Representative raw EMG and RMS
envelope traces should be inspected for the small High-Alertness-only groups, along
with the existing EMG burst-threshold sensitivity work. A non-EMG feature-set
check should remain part of any claim about Wake physiology rather than
movement-linked organization.

## Reproducibility and retained audits

The original full-feature analysis is retained under
`results/wake_knn_clusters_20260918/`. The current source-label styling can be
rerendered from its saved points and graph assignments without refitting:

```powershell
conda activate ne_umap

python scripts\plot_wake_knn_clusters.py `
  --feature-dir data\derived_features\features_29 `
  --results-dir results\wake_knn_clusters_20260918 `
  --figures-dir writeups\assets\wake_knn_clusters_20260918 `
  --n-clusters 3 4 5 `
  --render-only `
  --overwrite
```

The ignored results directory retains the exact configuration, sampled point
identities, graph audit, per-cluster source-label and recording composition, and
within-recording robust-scaled feature medians. Those medians are an audit for
inspecting candidate groups, not 29 separate statistical tests.
