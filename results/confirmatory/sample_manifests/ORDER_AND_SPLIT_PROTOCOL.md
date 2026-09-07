# Row identity and split protocol

Frozen on 2026-07-18 before viewing any new confirmatory performance.

## Original discovery order

`src/01_extract_features.py::discover_images` establishes the historical order:

- `subdirs`: class directory names sorted lexicographically, then entries inside
  each class sorted lexicographically;
- `recursive`: leaf directories sorted by full path, then entries in each leaf
  sorted lexicographically;
- embeddings are extracted with a non-shuffled loader and labels are saved in
  that same sequence.

`extract_sota_2024.py` did not independently preserve filenames. It reconstructed
paths per class from the then-current data tree and consumed them according to
the already stored label sequence. Therefore the `.npy` files do not themselves
prove sample identity; exact linkage requires restored tree + deterministic
order + exact row label sequence.

## DTD: linked; official partitions authoritative

The restored primary release produces exactly 5,640 paths in historical order,
47 classes × 120 images, and its canonical row-label sequence exactly equals
the existing embeddings. Every row stores `split_1` through `split_10` from the
release's `trainN.txt`, `valN.txt` and `testN.txt` files.

For each official split N:

1. outer test is exactly `split_N == test`;
2. GFS and all tuning operate only on official train+validation;
3. official test is evaluated once after selection;
4. results are summarized across the ten official splits, not across invented
   stratified folds.

The release contains 17 duplicate SHA groups (17 extra rows). Depending on the
official split, 9–14 groups cross role boundaries. To prevent direct leakage,
the runner preserves every official test row but purges from train+validation
any row whose content SHA appears in that test. Duplicate content inside
train+validation is held together by the SHA-based group during inner CV.

## FMD: re-extraction required; no official split in archive

The primary archive contains 1,000 images in ten flat class folders. Counts and
class names equal the embeddings, but its deterministic row-label sequence does
not equal the saved sequence. The latter is consistent with an earlier
train/test-directory organization that is no longer present, and filenames were
not saved. Identity is therefore not proven.

After re-extraction from the primary archive, use repeated stratified 5-fold CV
with frozen seeds 42, 123 and 2026. Each source SHA is its own group. This is a
project-defined reproducible protocol, explicitly not an official FMD split.

## MIT VisTex: official 19-class re-extraction required

The official Reference hierarchy has 167 images in 19 categories. Existing
embeddings have the same row count but 23 labels because the one official
`Paintings` directory was split into five filename-derived categories. No
23-to-19 relabeling is asserted.

Re-extract in manifest order using the official 19 categories. Because some
official classes contain fewer than five images, the old five-fold design is not
admissible. Before evaluation, use repeated stratified 2-fold CV (seeds 42, 123,
2026), which is feasible for the minimum class count of two; report the small-N
limitation explicitly. Each original Reference image SHA is its own group.

## CUReT: full official manifest; cropped protocol required

The Columbia distribution contains 205 standard viewing/illumination images for
each of 61 physical samples. Existing embeddings contain exactly 100 rows per
class, but no script, filename list or log demonstrates which 100 of 205 were
used. `sample_subset` cannot explain the saved class-blocked label sequence and
also fails to preserve path/label pairing after its final path shuffle.

The pre-specified recovery target is the established cropped-CUReT protocol
documented by Varma and Zisserman at Oxford VGG:

- start from the 118 views per material with azimuthal viewing angle below 60°;
- use the published common subset of 92 views where a 200×200 texture region is
  visible across all materials;
- crop the central 200×200 region;
- evaluate disjoint 46/46 train/test partitions.

The Columbia raw files alone do not identify the published common 92-view list.
No substitute list will be inferred from filename position. Re-extraction stays
blocked until that list/cropped release is obtained from the primary authors or
reproduced from documented camera metadata with a reviewed, frozen script.

## Manifest semantics

- `row_id`: exact extraction row in the associated manifest.
- `label`: official category/material label.
- `group`: stable source identity (SHA for an independent image). It is not a
  claim that different CUReT views are independent; CUReT must use its explicit
  view protocol rather than generic group CV.
- `source_path` and `source_sha256`: provenance of image bytes. CUReT currently
  hashes the official compressed BMP source.
- `official_split`: compact description; DTD additionally has machine-readable
  `split_1`…`split_10` columns.
