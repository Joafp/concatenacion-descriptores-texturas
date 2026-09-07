# Soil recovery assessment

## Material Passport

- **Artifact:** local provenance and recoverability assessment
- **Dataset under audit:** `Soil`
- **Assessment date:** 2026-07-21
- **Evidence boundary:** local repository only; no network access and no dataset download
- **Verification status:** `CANDIDATE_MATCH_NOT_IDENTITY_VERIFIED`
- **Candidate source:** Kaggle, `ai4a-lab/comprehensive-soil-classification-datasets`, version 1
- **Confirmatory eligibility:** `BLOCKED_PENDING_SOURCE_ARCHIVE_AND_CONTENT_HASH_MATCH`

### Acquisition attempt status

On 2026-07-21 the environment was checked for an authenticated acquisition
route. No `kaggle` executable, `~/.kaggle/kaggle.json`, or Kaggle environment
variable was present. A sandboxed request to the official version-pinned API
could not resolve `www.kaggle.com`; the required network escalation was then
declined. No partial archive remains in `source/`.

Consequently, feature re-extraction, integrity gating over pixels, and SVM or
ResMLP smoke tests are correctly paused. Running them against historical
embeddings would not repair provenance and would falsely imply verification.

## Executive finding

The local evidence is **strongly compatible** with version 1 of the Kaggle
candidate named above, but it does not prove that the historical embeddings
were extracted from that exact archive. The strongest evidence is the exact
seven-class vocabulary and the stable per-class distribution found in all 20
descriptor artifacts:

| Canonical local class | Samples |
|---|---:|
| `Alluvial_Soil` | 50 |
| `Arid_Soil` | 284 |
| `Black_Soil` | 255 |
| `Laterite_Soil` | 219 |
| `Mountain_Soil` | 201 |
| `Red_Soil` | 108 |
| `Yellow_Soil` | 69 |
| **Total** | **1,186** |

This compatibility is not yet identity evidence because every local file under
`data/Soil/` is a zero-byte placeholder. There are no source pixels, source
archive, acquisition receipt, Kaggle metadata, or content hashes to compare.
Therefore, historical Soil results must remain excluded from confirmatory
claims until a clean versioned archive is acquired and the features are
re-extracted in a canonical manifest order.

## Local evidence inventory

### Raw-data placeholders

- Path: `data/Soil/`
- Directory classes: 7, with the exact names shown above.
- File entries: 1,186, all named as `.jpg`.
- Readable non-empty images: **0**.
- Every entry has size 0 bytes; for example,
  `data/Soil/Arid_Soil/207.jpg` is reported as `empty`.
- The placeholders were created locally on 2026-07-18, after the descriptor
  logs dated 2026-06-28. Their timestamps therefore do not establish the
  historical source or extraction order.
- SHA-256 of the sorted relative filename list (paths only, not content):
  `9ccd85fd48eec497bcc78901bb692babbf177f9a9c52102dfff6cb279798fb9f`.

The filenames include numeric stems and suffix variants such as `36.jpg`,
`36a.jpg`, and `36b.jpg`. Across classes, numeric stems are reused by 127
source-like groups (1,008 distinct class-plus-numeric-stem groups for 1,186
entries). These may be related photographs, variants, or merely a naming
convention. They must be treated as potential dependency groups until pixels
and source documentation establish otherwise.

### Historical descriptor artifacts

- Path: `embeddings/Soil/`
- Descriptor matrices: 20.
- Every descriptor has 1,186 rows and finite values according to
  `results/confirmatory/data_audit.json`.
- All descriptor label artifacts agree on seven classes and the same counts.
- Older integer label arrays map the alphabetically sorted class list to
  labels 0 through 6; the three newer string-label arrays contain the same
  vocabulary and distribution.
- `logs/extract_Soil_resnet50.log` records discovery of 1,186 images in seven
  classes and a completed `(1186, 2048)` extraction on 2026-06-28.

These artifacts prove internal label/row consistency. They do **not** prove
which source image produced each row because no historical ordered manifest or
image hashes survive.

### Documentation inconsistencies

- `README.md` describes Soil as Kaggle data with 1,186 images but incorrectly
  reports 13 classes.
- The actual local class directories, class JSON files, label arrays, logs, and
  current audit all consistently report 7 classes.
- No local file identifies a Kaggle owner, dataset slug, version, license,
  archive filename, archive checksum, or download date.

The 13-class statement is therefore not usable provenance and should be
corrected only after the downloaded archive and its documentation are audited.

## Candidate-source assessment

Candidate landing page (version-pinned):

`https://www.kaggle.com/datasets/ai4a-lab/comprehensive-soil-classification-datasets/versions/1`

Candidate identity:

- Owner/slug: `ai4a-lab/comprehensive-soil-classification-datasets`
- Requested version: `1`
- Local compatibility signals: seven soil class names, 1,186 historical rows,
  matching filename style, and prior project documentation naming Kaggle.
- Evidence unavailable locally: official file tree, original/generated-data
  distinction, license, archive byte length, archive checksum, individual image
  hashes, and official sample counts.

**Verdict:** probable candidate, not verified identity. A rough external claim
of “about 1,189 images” cannot explain or invalidate the local 1,186 rows
without a version-1 file listing. The three-image difference must not be
silently repaired or interpreted as deletion.

## Proposed acquisition (not executed)

Use a version-pinned API URL and retain the archive unchanged:

```bash
mkdir -p data/confirmatory_sources/Soil/original
curl -fL 'https://www.kaggle.com/api/v1/datasets/download/ai4a-lab/comprehensive-soil-classification-datasets?datasetVersionNumber=1' \
  -o data/confirmatory_sources/Soil/original/comprehensive-soil-classification-datasets-v1.zip
sha256sum data/confirmatory_sources/Soil/original/comprehensive-soil-classification-datasets-v1.zip
```

Authentication may be required. If the installed Kaggle CLI is preferred, its
version must first be recorded and the equivalent version-1 option confirmed
from `kaggle datasets download --help`; do not download an unpinned “latest”
version.

### Expected checksum

`PENDING_VENDOR_METADATA_OR_FIRST_VERIFIED_ACQUISITION`

No expected archive checksum exists in the local evidence, so inventing one
would destroy traceability. Before accepting the archive, retrieve the
version-1 API metadata/receipt and record any vendor-provided checksum. If
Kaggle supplies no cryptographic checksum, record the SHA-256 of the first
authenticated download and verify it with a second independent download or a
professor-supplied copy. The archive is not provenance-verified until this gate
is resolved.

## Recovery and verification gates

1. Save the version-1 landing-page metadata/API response, license, download
   timestamp, final resolved URL, archive byte length, and SHA-256 beside the
   untouched archive.
2. List the archive before extraction. Reject path traversal, zero-byte images,
   unexpected generated/augmented directories, and undocumented class trees.
3. Determine from vendor documentation which files are original photographs.
   Exclude CycleGAN, augmentation, or synthetic outputs from the primary
   evaluation unless the professor explicitly defines a separate experiment.
4. Compare the official class vocabulary, per-class counts, and exact relative
   filenames against the local placeholder inventory. Report all additions,
   omissions, and renames; do not force the total to 1,186.
5. Decode every candidate image and record dimensions, mode, byte SHA-256, and
   a normalized-pixel hash. Detect exact duplicates and near duplicates.
6. Investigate suffix families (`N`, `Na`, `Nb`, etc.). If variants represent
   the same source capture or scene, assign them a common `group` so no group
   crosses training and test folds.
7. Create a canonical manifest containing at least:
   `row_id,label,class_name,group,source_path,source_sha256,pixel_sha256,source_version`.
8. Freeze the manifest and split policy before feature extraction. Re-extract
   all 20 descriptors from the recovered pixels in manifest order; historical
   embeddings are audit evidence only and must not be mixed with the new run.
9. Run grouped, stratified evaluation only after every integrity gate passes.
   Report Soil as domain-generalization evidence (soil photographs), not as an
   interchangeable controlled texture benchmark.

## Decision table

| Question | Current answer |
|---|---|
| Do the historical features agree internally? | Yes: 20 descriptors, 1,186 rows, 7 matching classes. |
| Are usable source pixels present? | No: all 1,186 local `.jpg` entries are empty. |
| Is the exact Kaggle dataset/version documented locally? | No. |
| Is version 1 the strongest candidate? | Yes, but only as a candidate. |
| Can historical results become confirmatory without re-extraction? | No. |
| Can the three-image discrepancy be explained now? | No; versioned archive listing required. |
| Immediate next action | Acquire and checksum the pinned v1 archive, then compare its tree to the placeholder manifest. |

## Files consulted

- `data/Soil/`
- `embeddings/Soil/*_classes.json`
- `embeddings/Soil/*_labels.npy`
- `logs/extract_Soil_resnet50.log`
- `logs/extract_curet_soil_master.log`
- `results/confirmatory/data_audit.json`
- `README.md`
- `scripts/run_curet_soil_pipeline.sh`
