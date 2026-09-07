# VisTex recovery assessment

Date: 2026-07-21

## Decision

The local archive is a valid, complete-looking copy of the MIT Vision Texture
1.0 distribution, but it does **not** support the historical claim that the
study used a "19-class/484-image Reference subset". The defensible Reference
collection in this archive has **167 full-resolution images in 19 category
directories**. The number 484 is the number of files in `VisTex/FLAT`, which
mixes resolutions and the Reference and Scenes sections. It must not be used as
the sample count of a 19-class classification dataset.

The present embeddings also cannot be promoted to confirmatory evidence. They
have 167 rows but 23 labels because the `Paintings` directory was split by
filename (`Paintings.1`, `.11`, `.21`, `.31`, `.41`) instead of being kept as
the single official top-level category `Paintings`.

## Provenance and archive integrity

- Candidate supplied archive: `data/VisTex.tar.gz`
- Preserved archive copy:
  `data/confirmatory_sources/VisTex/original/VisTex.tar.gz`
- SHA-256 of both files:
  `6340ab536dfddd6d0e55012a0b6fa1dd9b3d933da5d1547349b7415a5d180772`
- `gzip -t` succeeds.
- The outer tar contains `VisionTexture/buildVisTex` and eight historical
  `vistex1.0a.[A-H].tar.Z` parts. The already recovered copy expands those
  parts under
  `data/confirmatory_sources/VisTex/extracted/VisionTexture/VisTex`.
- The bundled README identifies the release as **Vision Texture 1.0
  (1995-03-25)** and describes Reference Textures and Texture Scenes as
  separate sections. It also grants educational/research use subject to its
  copyright and attribution conditions.

No archive or source image was overwritten during this assessment.

## What the archive actually contains

`VisTex/FLAT` contains 484 PPM files:

| Dimensions | Count |
|---|---:|
| 512 x 512 | 227 |
| 128 x 128 | 227 |
| 768 x 512 | 11 |
| 192 x 128 | 11 |
| 512 x 768 | 4 |
| 128 x 192 | 4 |

This dimension symmetry is direct evidence that `FLAT` includes paired
full-size and reduced representations, not 484 independent observations.
Additionally, `FLAT` is the shared backing store for both Reference and Scenes.

The classification-relevant directory `Images/Reference` contains 167
full-resolution 512 x 512 images, distributed as follows:

| Category | Images | Category | Images |
|---|---:|---|---:|
| Bark | 13 | Brick | 9 |
| Buildings | 11 | Clouds | 2 |
| Fabric | 20 | Flowers | 8 |
| Food | 12 | Grass | 3 |
| Leaves | 17 | Metal | 6 |
| Misc | 4 | Paintings | 13 |
| Sand | 7 | Stone | 6 |
| Terrain | 11 | Tile | 11 |
| Water | 8 | WheresWaldo | 3 |
| Wood | 3 | **Total** | **167** |

`Images/Scenes` contains another 74 full-resolution items, including context
scenes and detail textures. These do not form the same 19-class task and must
not be silently combined with Reference.

## Reconstruction of the historical 167 rows

The existing `embeddings/VisTex/dinov2_labels.npy` has 167 labels. Its class
metadata has 23 values: the 18 ordinary Reference directories plus five values
derived from `Paintings.*` filenames. The row counts exactly reconcile with
the archive after merging those five values into `Paintings`.

Therefore the historical extraction appears to have used every Reference
image once, but assigned class names using the filename prefix before the final
period for Paintings. This is a labeling bug, not evidence for a 23-class
official taxonomy. Because no frozen row-to-file recipe accompanied the old
embeddings, all 20 descriptor blocks should be re-extracted from a canonical
manifest rather than relabeling the arrays in place.

## Independent units and groups

For the unmodified Reference task, each 512 x 512 PPM is one source image and
one independent sampling unit. The canonical `group` should be a stable ID
derived from the full source-image SHA-256 (or the canonical relative path plus
hash). There are no generated crops in the archive's Reference directory.

The PPM `SRC` annotation is **not** a safe group identifier. In many files it
is only a broad attribution such as `photo josh`, `photo lee`, or `PCD steve`;
using it would collapse unrelated photographs and even different semantic
categories into a single group. Exact matching `SRC` strings can be retained
as provenance metadata but should not replace the image-level source group.

If a new patch protocol is introduced, every patch must additionally record:

```text
row_id,label,group,source_path,source_sha256,crop_x,crop_y,crop_w,crop_h,recipe_version,official_split
```

All patches from one 512 x 512 source image must share the same `group`, and
splitting must occur by group before any crop is supplied to a model. Patching
increases observations but not independent source units.

## Feasibility of grouped nested validation

A 19-class nested five-fold protocol is infeasible: `Clouds` has only two
source images, and four other classes have only three or four. Ordinary
stratified five-fold validation previously used these source images as if all
classes could populate every fold, producing degenerate class support.

Defensible options, to be frozen before inspecting new scores, are:

1. **Recommended confirmatory extension:** use the 12 categories with at least
   seven independent source images (140 images total): Bark, Brick, Buildings,
   Fabric, Flowers, Food, Leaves, Paintings, Sand, Terrain, Tile, and Water.
   This can support five outer folds and five inner folds at the class-count
   level. Use deterministic `StratifiedGroupKFold`, with `group` equal to the
   source-image ID. Verify every realized inner split still contains each
   training class before execution.
2. **Broader 14-class task:** retain categories with at least five images (152
   total, adding Metal and Stone), but reduce and preregister the nested fold
   counts (for example, three outer and three inner folds). Validate actual
   per-fold support programmatically. This changes comparability with the
   principal protocol.
3. **Full 19-class descriptive task:** evaluate all 167 source images only as a
   separately labeled exploratory/descriptive experiment. It cannot sustain
   the paper's current nested model-selection design. Creating patches does
   not cure the shortage of independent groups.

There is no official train/test split in this VisTex distribution, so
`official_split` should state `NONE_DEFINED_BY_ARCHIVE`, not `official`.

## Proposed canonical recipe

For the recommended option:

1. Read only `Images/Reference/<category>/*.ppm` at 512 x 512.
2. Treat the immediate parent directory as the label; in particular, all
   `Paintings.*.ppm` files receive label `Paintings`.
3. Exclude categories using the preregistered minimum of seven source images,
   without reference to descriptor or classifier performance.
4. Sort by `(label, relative_source_path)` to assign stable row IDs.
5. Record source SHA-256 and use it as the image-level group ID.
6. Detect exact hash duplication before extraction; fail closed if one hash is
   associated with multiple labels.
7. Generate all descriptor blocks from this one frozen manifest and assert
   identical row count, label vector, group vector, and row order.
8. Fit preprocessing, descriptor selection, and classifier tuning exclusively
   inside each outer-training partition.

This should be named something like **VisTex Reference-12 (study-defined
protocol)**. It is based on an official archive but is not an official VisTex
classification split.

## Required follow-up before execution

- Write and review the canonical Reference-12 manifest.
- Freeze fold seeds/counts and minimum-class rule in an extension protocol.
- Re-extract all 20 descriptors; do not reuse the current 23-label arrays.
- Add audit assertions for parent-directory labels, source hashes, image-level
  groups, and no group overlap across any train/test split.
- Update the manuscript's old `19 classes / 167 images` characterization and
  explicitly explain why the 484 count was rejected.

Current status: **RECOVERABLE, BUT REEXTRACTION AND A STUDY-DEFINED SPLIT ARE
REQUIRED.**
