# Data recovery requirements for confirmatory experiments

Status date: 2026-07-18. No dataset has been downloaded or silently repaired.

The existing `.npy` files contain features and class labels but no sample IDs.
Consequently, row identity cannot be demonstrated from the embeddings alone.
The safe recovery rule is: restore the exact source release, regenerate a
row-level manifest during deterministic discovery, compare labels/counts, and
re-extract embeddings if exact row identity cannot be proven.

## DTD

- Missing: `data/DTD/dtd/images`, the release's official split files, and a
  row-to-filename manifest for all 5,640 embedding rows.
- Existing extraction order: class directories sorted lexicographically, then
  filenames sorted lexicographically (`src/01_extract_features.py`).
- Safe route: restore the official DTD release including `labels/`; reconstruct
  that deterministic order and verify all class labels/counts. Prefer the
  official ten train/validation/test splits. Re-extract if any filename/count
  differs; do not align rows by class label alone.

## FMD

- Missing: the exact FMD release, any split lists used, and a row-to-filename
  manifest for 1,000 rows.
- Existing extraction order: sorted leaf directories and sorted filenames,
  combining every discovered split directory.
- Safe route: restore the exact release and its evaluation split definitions
  (or archive checksum/provenance), reconstruct paths, then verify/re-extract.
  Class-stratified CV alone is not accepted as proof of the benchmark protocol.

## Outex_TC_00013 — recuperación resuelta

- Se restauró y auditó la distribución completa de 1.360 imágenes RGB.
- La partición oficial 680/680 y los 20 bloques alineados se conservan en
  `results/extensions/outex13_official1360/` y
  `embeddings_extensions/Outex13Official1360/`.
- No queda pendiente ninguna recuperación de Outex para el protocolo vigente.

## CUReT

- Missing: `data/CUReT`, view/illumination identifiers and row-to-filename
  mapping for 6,100 rows.
- Local project records one source route:
  `https://www.robots.ox.ac.uk/~vgg/data/datasheets/curet.html`.
- Existing order: sorted class directories, sorted filenames.
- Safe route: restore the documented CUReT release, retain material/sample and
  acquisition metadata, then verify or re-extract. Define the split from the
  established protocol before looking at performance; do not invent groups
  from row position.

## Soil

- Present only as 1,186 zero-byte, permissionless placeholder filenames. The
  README says Kaggle but the exact dataset slug, version, license and checksum
  are not recorded. README claims 13 classes while embeddings contain 7.
- Missing: exact source identity/version, real image bytes, source/capture IDs,
  and a row-to-filename manifest.
- Safe route: first identify the original Kaggle dataset/archive from project
  history or the researcher who downloaded it. Restore only that version,
  document checksum/license and determine whether suffixes `a/b/c` encode
  related captures from dataset documentation. Re-extract if provenance cannot
  be established. Filename interpretation alone is insufficient.

## VisTex

- Missing: `data/VisTex_clean`, the recipe that produced the 167-image subset,
  source-image/patch IDs and row-to-filename manifest.
- Internal documentation is inconsistent: configuration says 19 classes/484
  images, embeddings contain 23 classes/167 rows, and some classes have only
  two samples.
- Safe route: recover the original MIT VisTex images and the exact cleaning or
  cropping script/manifest. Group all crops from one source texture. The frozen
  5-fold protocol is infeasible for the existing class counts, so either restore
  the intended 484-image subset or preregister a revised fold count before any
  confirmatory result is viewed.

## Required manifest schema

For each eligible dataset create
`results/confirmatory/sample_manifests/<dataset>.csv` with:

```text
row_id,label,group,source_path,source_sha256,official_split
```

`row_id`, `label`, and `group` are enforced by the runner. The remaining fields
provide the provenance evidence needed to change the audit gate from
`BLOCKED_DATA_LEAKAGE_RISK` to `PASS_*`.
