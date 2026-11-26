# Data and code for the Top-k manuscript

The verification script, predictions, timing traces and sample manifests are in the [frozen public repository snapshot](https://github.com/Joafp/concatenacion-descriptores-texturas/tree/97e4a8a4fe3b551f529a6e1f8814f6125cccaf78). The image collections and pretrained checkpoints are obtained separately.

## Exact image lists used in E1

The counts describe manifest rows before a train/test split is applied.

| Dataset | Images | Classes | Recipe | Manifest and source |
|---|---:|---:|---|---|
| DTD | 5,640 | 47 | Ten official splits with training deduplication against test. | [Manifest](../../results/confirmatory/sample_manifests/DTD.csv) · [Oxford VGG](https://www.robots.ox.ac.uk/~vgg/data/dtd/) |
| FMD | 1,000 | 10 | Grouped five-fold evaluation. | [Manifest](../../results/confirmatory/sample_manifests/FMD.csv) · [MIT CSAIL](https://people.csail.mit.edu/lavanya/fmd.html) |
| CUReT | 5,612 | 61 | Grayscale crops. The two halves alternate 92 common capture conditions across all classes. | [Manifest](../../results/confirmatory/sample_manifests/CUReT.csv) · [Columbia CAVE](https://cave.cs.columbia.edu/repository/CURET/about) |
| Outex TC 00013 | 1,360 | 68 | RGB 128 × 128 BMP suite, 680 official train and 680 test images. | [Manifest](../../results/extensions/outex13_official1360/sample_manifests/Outex13Official1360.csv) · [Archive audit](../../results/extensions/outex13_official1360/sample_manifests/Outex13Official1360.audit.json) |
| SoilOriginal | 1,140 | 7 | Version 1 original tree, exact deduplication, filename-family grouping. | [Manifest](../../results/extensions/soil_original/sample_manifests/SoilOriginal.csv) · [Original distribution](https://www.kaggle.com/datasets/ai4a-lab/comprehensive-soil-classification-datasets) · [Source recovery](../../results/confirmatory/recovery/soil/ASSESSMENT.md) |
| KTH-TIPS2-b | 4,752 | 11 | One full physical sample per class held out in each of four splits. | [Manifest](../../results/extensions/kth_tips2b/sample_manifests/KTHTIPS2b.csv) · [KTH collection](https://www.csc.kth.se/cvap/databases/kth-tips/) |

Train, test and inner-fold indices are in the [frozen E1 protocol](../../results/exploratory/topk_cascade/top4_fixed_kth_completion_20261115_v1/protocol_frozen.json). For the static and online comparisons, consult the indices for the corresponding campaign. The [online trace index](../../results/analysis/consultas_joaquin_20261114_v1/canonical_panel_calls_94.csv) lists the 94 timing files and their SHA-256 digests.

## Manifest checksums

| Dataset | SHA-256 |
|---|---|
| DTD | 2cf599cd934d8569ded9e73cd8019bef53627878d98260d7c071921bdd635b3b |
| FMD | 43f5d02a493763bff351e842d0ec29ac4fdcc9facccfa1364a028ed81d793984 |
| CUReT | 42f1af10b02ab55b9ffce3019e318a52b758f6c8ec7d70d4428fa2c397524a34 |
| Outex TC 00013 | 6499321a05630111dda4e3a7421995555553deea4807f23a5b4673a011856447 |
| SoilOriginal | c2ad216f0fc9a014835fd3bfbefe14d16d82ed2e7c612a1529a384d3d36d49fd |
| KTH-TIPS2-b | df7d23f6681f2d5974d47f33ef5246845f51435d9db539d0522d6de8ab5cb2e7 |

## Verify the archived results

From the root of the frozen snapshot:

~~~bash
python3 scripts/verify_topk_paper_evidence.py
~~~

The command verifies the recorded E1 predictions and cost projections and the physical online panel aggregates, including the latency percentiles reported in the paper. The [editorial review notes](REVISION_PARA_REVISTA.md) explain the scope and how to rebuild the manuscript.
