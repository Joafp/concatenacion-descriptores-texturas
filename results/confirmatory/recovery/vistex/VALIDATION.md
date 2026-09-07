# VisTex Reference-12 manifest validation

Date: 2026-07-21

Status: **PASS**

This report validates the study-defined VisTex Reference-12 manifest generated
from the independently extracted staging copy. No descriptor or classifier was
executed.

## Frozen selection rule

- Input: `staging/VisionTexture/VisTex/Images/Reference/<category>/*.ppm`
- Label: immediate parent directory (so all `Paintings.*.ppm` remain
  `Paintings`)
- Eligibility: categories with at least 7 independent source images
- Ordering: `(label, filename)`, ascending
- Group: full source-image SHA-256
- Split marker: `NONE_DEFINED_BY_ARCHIVE`

## Output

- Manifest: `VisTex_Reference12_manifest.csv`
- Rows: 140
- Classes: 12
- Unique source groups: 140
- Manifest SHA-256: `d7a81b32880c56c11c39e60d9dccbfe170f77ed4ee93a26b322cacc9ee6c3965`

## Class counts

| Label | Sources |
|---|---:|
| Bark | 13 |
| Brick | 9 |
| Buildings | 11 |
| Fabric | 20 |
| Flowers | 8 |
| Food | 12 |
| Leaves | 17 |
| Paintings | 13 |
| Sand | 7 |
| Terrain | 11 |
| Tile | 11 |
| Water | 8 |

Minimum: 7; maximum: 20.

## Integrity checks

| Check | Result |
|---|---|
| `archive_reference_images` | PASS |
| `selected_images` | PASS |
| `selected_classes` | PASS |
| `minimum_class_count` | PASS |
| `unique_row_ids` | PASS |
| `unique_source_paths` | PASS |
| `unique_groups` | PASS |
| `group_equals_source_sha256` | PASS |
| `no_exact_duplicates` | PASS |
| `no_cross_label_duplicates` | PASS |
| `paintings_not_split` | PASS |
| `split_marker` | PASS |

Exact duplicate hashes in selected set: 0. Cross-label
duplicate hashes: 0.

## Interpretation

The manifest is internally suitable for preregistering grouped nested
validation at the source-image level. Fold construction still has to verify
class support in every realized outer and inner partition. This validation
does not authorize using historical VisTex embeddings, which retain the old
23-label error.
