# Vision DB Design

**Date:** 2026-07-07  
**Scope:** GTOBig phase 2 static-image vision database and preprocessing pipeline

## Goal

Build a reusable image database pipeline from `D:/gtobig/screenshots` that preserves original data, creates compressed working copies, standardizes existing `*_raw.png` card seeds into a template library, and records all processing state in machine-readable metadata for future recognition, labeling, and training work.

## Why This Exists

The project may pause before full real-time recognition is complete. The database itself must still be useful to later work. That means phase 2 should not be a throwaway prototype. It should create durable assets:

- original full screenshots
- compressed full screenshots for batch processing
- trusted card templates from `*_raw.png`
- sample-library structure for future cropped card slots
- metadata and logs that later projects can read without guessing from filenames

## Approved Design Decisions

- Source folder is `D:/gtobig/screenshots`.
- That folder has already been manually cleaned; it should be treated as usable input.
- Files named `*_raw.png` are trusted labeled card seeds. Example: `Ah_raw.png` means ace of hearts.
- Images larger than `1MB` should get compressed copies.
- Compression must not change pixel dimensions.
- Original images must be preserved.
- The final database should be structured completely enough for long-term reuse, but the implementation order should stay practical and incremental.

## Scope Boundaries

### In Scope For Phase 2

- scan and index the screenshots folder
- distinguish `*_raw.png` seed templates from full screenshots
- build a durable directory structure under `D:/gtobig/data/vision_db/`
- copy or register original full images
- generate compressed copies for large full screenshots
- standardize raw card seeds into a template library
- create JSONL metadata files
- create processing logs
- create placeholder structure for future cropped card samples
- produce summary statistics after each run

### Explicitly Out Of Scope For Phase 2

- real-time screen capture
- ROI calibration from a live table
- real OCR execution
- automatic full-batch crop extraction of all card slots
- CNN training
- GUI work
- strategy-engine integration

## High-Level Strategy

Use a hybrid of the two preferred approaches:

- **Design target:** complete enough for long-term data engineering
- **Execution order:** practical enough to deliver useful assets quickly

This means the structure must already support templates, samples, exports, metadata, and logs, but phase 2 implementation will focus first on input scanning, compression, template normalization, and durable indexing.

## Directory Layout

Root:

`D:/gtobig/data/vision_db/`

Subdirectories:

- `raw_full/`
  - preserved original full screenshots used as long-term source material
- `compressed_full/`
  - compressed working copies of large full screenshots
- `templates/cards/`
  - normalized card templates derived from trusted `*_raw.png` seeds
- `samples/cards/`
  - future cropped real card-slot samples from full screenshots
- `metadata/`
  - JSONL metadata and processing records
- `exports/`
  - downstream derived outputs for matching, review, or training

## Processing Model

### Input Types

Two input categories exist:

1. **Template seeds**
   - filename pattern: `*_raw.png`
   - trusted label source
   - example: `Ah_raw.png`

2. **Full screenshots**
   - all other image files
   - usable as future sample sources
   - may need compressed working copies if larger than `1MB`

### Processing Steps

1. Scan `D:/gtobig/screenshots`.
2. Classify each file as either template seed or full screenshot.
3. Register every file in metadata.
4. Preserve original full screenshots in the database structure.
5. Generate compressed copies for full screenshots larger than `1MB`.
6. Normalize `*_raw.png` files into the template library.
7. Initialize sample-library placeholders for future card-slot crops.
8. Record all actions in processing logs.
9. Emit a run summary.

## Metadata Format

Metadata will use JSONL instead of a database in phase 2.

Reason:

- easy to inspect manually
- simple to generate from scripts
- easy to migrate to SQLite later
- low overhead for current dataset size

All metadata files live under:

`D:/gtobig/data/vision_db/metadata/`

### 1. `images.jsonl`

Tracks full screenshots and their compressed derivatives.

Suggested fields:

- `image_id`
- `source_path`
- `raw_copy_path`
- `compressed_path`
- `width`
- `height`
- `file_size`
- `is_over_1mb`
- `theme`
- `status`

### 2. `templates_cards.jsonl`

Tracks trusted card templates from `*_raw.png`.

Suggested fields:

- `template_id`
- `label`
- `rank`
- `suit`
- `template_path`
- `width`
- `height`
- `source_type`

`source_type` should initially be `raw_seed`.

### 3. `samples_cards.jsonl`

Tracks cropped real card-slot samples from full screenshots.

Suggested fields:

- `sample_id`
- `image_id`
- `card_slot`
- `label`
- `sample_path`
- `bbox`
- `width`
- `height`
- `quality_status`

Phase 2 may create this file as an empty or near-empty scaffold if cropping is not yet implemented.

### 4. `processing_log.jsonl`

Tracks pipeline activity and failures.

Suggested fields:

- `timestamp`
- `step`
- `source_path`
- `result`
- `message`

## Card Template Policy

Phase 2 does not use OCR for cards.

Approved direction:

- **card recognition main path:** template matching
- **card recognition fallback path:** small CNN classifier later if template matching proves fragile
- **OCR usage later:** only numeric regions such as pot, stack, and bet amounts

Trusted `*_raw.png` seeds are the first template source. Their filenames will be parsed directly as labels:

- `Ah_raw.png` -> `label=Ah`, `rank=A`, `suit=h`
- `Kc_raw.png` -> `label=Kc`, `rank=K`, `suit=c`

## Compression Policy

Compression applies only to full screenshots larger than `1MB`.

Rules:

- preserve original file
- generate side-by-side compressed copy
- do not change pixel width or height
- reduce file size only
- write both original and compressed paths into metadata

Compression exists to make batch review and future processing cheaper without destroying source quality.

## Sample Library Policy

Phase 2 must create the structure for future real card samples even if bulk cropping is deferred.

Expected future slot labels:

- `hand_1`
- `hand_2`
- `flop_1`
- `flop_2`
- `flop_3`
- `turn`
- `river`

This ensures later stages can add cropped samples without redesigning the database.

## Error Handling Expectations

The pipeline must not abort just because one file is bad.

Required behavior:

- continue on per-file failures
- log each failure in `processing_log.jsonl`
- count failures in the final summary
- keep partially successful runs inspectable

## Phase 2 Deliverables

Phase 2 should produce these concrete outcomes:

1. a database initialization script
2. a compression pipeline for large full screenshots
3. a normalized card-template library from `*_raw.png`
4. JSONL metadata files
5. logging and summary output

## Acceptance Criteria

Phase 2 is successful when all of the following are true:

1. `D:/gtobig/screenshots` is scanned successfully.
2. `D:/gtobig/data/vision_db/` is created with the approved structure.
3. trusted `*_raw.png` seeds are normalized into `templates/cards/`.
4. full screenshots larger than `1MB` produce compressed copies without changing dimensions.
5. metadata files are written:
   - `images.jsonl`
   - `templates_cards.jsonl`
   - `samples_cards.jsonl`
   - `processing_log.jsonl`
6. a final summary reports:
   - total input images
   - raw template count
   - full screenshot count
   - compressed count
   - failure count
   - duplicate or anomaly count if detected

## Verification Plan

Phase 2 verification should check:

1. script exits successfully on the current dataset
2. directory tree exists under `vision_db`
3. one or more trusted seeds such as `Ah_raw.png` appear correctly in `templates_cards.jsonl`
4. at least one large full screenshot has both original registration and compressed-copy registration
5. summary counts are plausible against the dataset size

## Future Phase Mapping

- **Phase 3:** crop extraction and semi-automatic sample labeling
- **Phase 4:** real card recognition and numeric OCR pipeline
- **Phase 5:** live capture integration
- **Phase 6:** orchestration with state machine and engine
- **Phase 7:** GUI

## Notes On Repository State

This workspace is currently not a Git repository, so the spec can be written to disk but cannot be committed until Git is initialized.
