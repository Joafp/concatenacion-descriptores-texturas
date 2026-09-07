# Confirmatory data audit

This audit is a gate, not a repair step. `BLOCKED_DATA_LEAKAGE_RISK` datasets were not evaluated.

| Dataset | Samples | Extractors | Raw images | Split decision | Status |
|---|---:|---:|---:|---|---|
| DTD | 5640 | 20 | 0 | primary DTD release: split_1..split_10 train/val/test | PASS_OFFICIAL_SPLITS_PURGED_DUPLICATES |
| FMD | 1000 | 20 | 1000 | manifest-defined order; SHA-256 groups; repeated stratified group CV | PASS_REEXTRACTED_GROUP_AWARE |
| CUReT | 5612 | 20 | 5612 | Oxford cropped subset; condition-ID groups; deterministic complementary 46/46 halves | PASS_REEXTRACTED_CONDITION_GROUPED |
| Soil | 1186 | 20 | 1186 | none | BLOCKED_DATA_LEAKAGE_RISK |
| VisTex | 167 | 20 | 0 | none | BLOCKED_DATA_LEAKAGE_RISK |

## Dataset notes

### DTD

raw images/source identifiers unavailable; no official split/group metadata linked to embedding row order; restored row manifest exactly matches embedding label order; runner purges test-SHA duplicates from train/val

### FMD

20 descriptors re-extracted from the official FMD archive in canonical manifest order; manifest identity status: REEXTRACT_REQUIRED

### CUReT

20 descriptors re-extracted from Oxford's 61x92 grayscale CUReT subset in canonical manifest order; alternating halves are a deterministic reproduction, not the unpublished historical assignment; historical 100-view embeddings remain excluded; confirmatory data use the independently verified Oxford 92-view subset

### Soil

1186 raw image entries are empty or unreadable placeholders

### VisTex

raw images/source identifiers unavailable; at least one class has fewer than 5 samples; frozen 5-fold outer CV is infeasible; official 19-class manifest exists; current 23-class embeddings require re-extraction
