# Cluster visualization report

**Status:** completed on 2026-09-17 for the joint EEG+EMG+NE baseline and the
EEG+NE follow-up. Both runs used the same fixed 4,800-second balanced sample.

## Question

Each point is one final-labelled second from the ten available recordings. t-SNE and
UMAP are fit without the sleep-stage labels; labels are added only for colouring. The
purpose is to compare whether the same physiological observations show similar state
organization under two nonlinear neighbourhood projections.

## Features

The baseline joint panel uses four saved per-second features from
`features/features_4/`:

1. EEG log10 delta power (0.5--4 Hz).
2. EEG log10 theta power (6--9 Hz).
3. Mean-centred broadband EMG RMS.
4. Mean saved processed NE (% delta-F/F).

The archive values are already robust-scaled within each recording using that
recording's median and IQR. The comparison reads these archives directly; it does
not reopen MAT files, re-extract features, relabel seconds, or add another scaling
step.

## Sampling and figure captions

The default sample is capped at 100 seconds per available state per recording, with
seed `20260917`. For the current ten archives, that is 4,800 displayed seconds:
1,000 NREM, 1,000 REM, 800 MA, 1,000 Active Wake, and 1,000 Quiet Wake. Every method
uses exactly this same sample.

Suggested caption for each method-specific figure:

> Label-coloured [t-SNE/UMAP] embedding of the same balanced sample of
> one-second EEG + EMG + NE observations. The sample contains 1,000 NREM, 1,000 REM,
> 800 MA, 1,000 Active Wake, and 1,000 Quiet Wake seconds, capped at 100 seconds per
> available state per recording. Labels were not used to fit the embedding.

The colour contract exactly matches `sleep_scoring`: NREM `#FB7C7C`, REM `#7BFB7B`,
MA `#FFFF00`, Active Wake `#E69F00`, and Quiet Wake `#56B4E9`.

## Dimension-reduction settings

| Method | Settings |
|---|---|
| t-SNE | Two dimensions; perplexity 30; deterministic initialization; automatic learning rate; 1,000 iterations; seed `20260917`; Barnes-Hut optimization. |
| UMAP | Two dimensions; Euclidean distance; 30 neighbours; `min_dist=0.2`; 200 epochs; seed `20260917`; one worker for reproducibility. |

t-SNE and UMAP axes are unitless learned layout coordinates: their origin, direction,
and rotation have no physiological meaning.

## Results

### Joint EEG + EMG + NE

![Joint t-SNE](assets/embedding_comparison/initial_4800_separate/tsne.png)

![Joint UMAP](assets/embedding_comparison/initial_4800_separate/umap.png)

REM is the clearest reproducible state organization in the nonlinear views: it
occupies a relatively distinct left/lower region in t-SNE and an upper region in
UMAP. The joint maps also show a conspicuous Active-Wake region, including the long
lower-right UMAP arc. Quiet Wake is not an equally discrete region: it broadly
overlaps NREM, MA, and parts of Active Wake.

### Fairer EEG + NE follow-up

![EEG + NE t-SNE](assets/embedding_comparison/eeg_ne_4800/tsne.png)

![EEG + NE UMAP](assets/embedding_comparison/eeg_ne_4800/umap.png)

After omitting EMG, REM remains visibly organized in both nonlinear maps (lower in
t-SNE and left in UMAP). NREM also occupies more of the lower part of the EEG+NE
UMAP. In contrast, Active Wake and Quiet Wake are extensively intermingled with one
another and with MA; the joint Active-Wake arc does not persist. Thus these initial
EEG+NE views do not provide a visually distinct Active-versus-Quiet cluster beyond
the EMG-related separation in the joint panel.

## Interpretation caveat

The Active/Quiet Wake subdivision was created from a closely related one-second EMG
RMS quantity. Consequently, including EMG RMS in the joint embedding naturally
makes some Active-versus-Quiet separation likely. A split in the joint t-SNE or UMAP
panel therefore cannot independently establish that those labels are physiologically
distinct; it primarily locates the EMG-defined states in the joint EEG/EMG/NE space.
Likewise, nonlinear embeddings can emphasize local neighborhoods and should not be
read as distances, cluster sizes, or statistical evidence.

## Fairer follow-up

The completed `--feature-set eeg_ne` run omits EMG and retains only EEG delta power,
EEG theta power, and mean NE. It avoids the direct circularity from the EMG-derived
label rule while using the same saved archives, sampling, and colouring procedure.
The observed Active/Quiet overlap is descriptive, not a negative biological test:
the next rigorous step is a recording-level/held-out-recording analysis, together
with a reviewed approach to the extreme feature rows and UMAP/t-SNE sensitivity.
