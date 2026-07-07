# Vision DB Phase 3 Design

**Date:** 2026-07-07  
**Scope:** GTOBig phase 3 fixed-layout crop extraction, semi-automatic sample labeling, and human-approved sample ingestion

## Goal

Build a cautious phase 3 pipeline that extracts real card crops from fixed-layout WePoker screenshots, proposes one candidate label per crop using the existing raw template library plus layout context, and only writes samples into the formal vision database after human review.

## Why This Exists

Phase 2 created the long-term storage layout, template library, and metadata foundation for the vision database. Phase 3 should not jump straight to a final recognizer. The next practical step is to build a reliable sample collection workflow from real screenshots so later phases can train, validate, and stress-test recognition against clean human-approved data.

This phase exists to protect database integrity:

- use real screenshots rather than rendered synthetic cards
- extract crops from current production-like captures
- keep automatic guesses separate from approved samples
- let the user review crops and labels before they become formal training assets

## Approved Design Decisions

- Phase 3 only targets the current fixed WePoker layout family.
- Phase 3 prioritizes database quality and repeatability over layout generality.
- The sample source must be real screenshots, not rendered or synthesized cards.
- The first automatic label proposal should come from the existing real `*_raw.png` / `templates/cards/` library.
- Each crop should receive one primary candidate label for review, not an open-ended list.
- Automatic results must go into a review batch first, not directly into the formal sample library.
- Only human-approved samples may be added to `samples/cards/` and `samples_cards.jsonl`.
- Coordinate tolerance for manual calibration is `+/- 5` pixels.
- A lightweight coordinate confirmation tool is part of Phase 3 scope.
- Action-button glow detection is included only as an experimental auxiliary signal, not as a formal gate for sample ingestion.

## Scope Boundaries

### In Scope For Phase 3

- build a coordinate confirmation tool for screenshot ROI and bbox configuration
- seed that tool with a real confirmed screenshot and default profile values
- support the current fixed-layout WePoker screenshot family
- normalize known screenshot variants before crop extraction
- crop hero cards from fixed boxes
- detect community cards inside a configured ROI
- generate one candidate label per crop using templates plus context rules
- create review batches with crop images, review metadata, and preview overlays
- ingest only approved or corrected review results into the formal sample library
- prevent duplicate formal sample ingestion
- record failures, low-confidence guesses, and review outcomes in machine-readable metadata
- collect experimental action-button glow signals from fixed ROIs

### Explicitly Out Of Scope For Phase 3

- live capture or real-time monitoring loops
- OCR for numbers such as pot, stack, or bet sizes
- CNN training
- final production card recognizer logic
- broad multi-layout generalization
- automatic direct-to-database ingestion without review
- synthetic rendered sample generation
- full GUI productization

## Relationship To Earlier Phases

- **Phase 1** proved the mock program structure: `perception -> state machine -> engine -> output`.
- **Phase 2** built the static image database layout, template storage, compression pipeline, and base metadata files.
- **Phase 3** builds the first real screenshot sample workflow on top of that phase 2 database.

## Layout Family And Capture Profiles

Phase 3 should treat the current WePoker layout as one logical family with multiple capture profiles.

### Known Screenshot Variants

Current repository evidence shows three relevant image groups:

1. `1920x1080`
   - full desktop screenshots
   - include browser chrome and Windows taskbar
   - useful for manual coordinate confirmation and default seed configuration

2. `1920x1032`
   - work-area screenshots
   - include browser chrome
   - exclude the Windows taskbar
   - this is the most common full-table image size in the current dataset

3. `1936x1048`
   - windowed screenshots with extra outer frame or border
   - should not be treated as a second logical table layout
   - should be normalized before extraction

### Profile Policy

Phase 3 should not assume every image already matches one exact rectangle. Instead it should use profile-aware preprocessing.

Required behavior:

- store one or more named profile configurations
- identify whether an input image matches a known profile
- transform known variants into the same logical table layout before extraction
- reject unknown image shapes rather than guessing

The design target is one logical table layout with profile-specific normalization, not a fully generic multi-layout system.

## Seed Profile

The user supplied a real `1920x1080` WePoker screenshot and manually marked the hero and community card areas. Phase 3 should use that confirmed screenshot as the initial seed profile for the coordinate confirmation tool.

Suggested seed profile values:

```json
{
  "profile_name": "wepoker_fullscreen_1920x1080_seed",
  "window_title_hints": ["WePoker", "WePoker-H5"],
  "reference_width": 1920,
  "reference_height": 1080,
  "bbox_tolerance_px": 5,
  "hero_hand_roi": [897, 862, 125, 94],
  "hero_card_boxes": [
    [908, 872, 50, 73],
    [967, 872, 46, 73]
  ],
  "community_search_roi": [805, 457, 318, 109],
  "community_card_boxes": [
    [829, 476, 50, 73],
    [882, 476, 50, 73],
    [936, 476, 49, 73],
    [989, 476, 49, 73],
    [1042, 476, 50, 73]
  ]
}
```

Design notes:

- These values are a starting seed, not the final universal truth.
- The coordinate confirmation tool should load this seed by default.
- The user should be able to adjust these boxes and save refined profiles.
- Community fixed boxes may exist in a profile, but ROI detection is still required as a fallback and validation path.

## Coordinate Confirmation Tool

Phase 3 should include a lightweight local tool for confirming and refining bounding boxes on real screenshots.

### Purpose

The tool should reduce future manual back-and-forth by letting the user open a screenshot, draw or adjust boxes, read exact coordinates, and save updated profile JSON.

### Required Capabilities

- open a real screenshot from disk
- display the image at full resolution with optional zoom
- let the user draw and edit rectangles
- show exact `x, y, w, h` coordinates
- let the user assign semantic roles to rectangles
- save profile JSON back to disk

### Semantic Regions To Support

- `hero_hand_roi`
- `hero_card_1`
- `hero_card_2`
- `community_search_roi`
- `community_card_1`
- `community_card_2`
- `community_card_3`
- `community_card_4`
- `community_card_5`
- `fold_button_roi`
- `bet_button_roi`
- `check_button_roi`

### Tool Scope Expectations

- the tool may be a lightweight local web page or similarly simple local utility
- it does not need to be a polished end-user GUI
- it must prioritize exact coordinates and repeatable profile updates

## Database Additions For Phase 3

Phase 2 already created:

- `raw_full/`
- `compressed_full/`
- `templates/cards/`
- `samples/cards/`
- `metadata/images.jsonl`
- `metadata/templates_cards.jsonl`
- `metadata/samples_cards.jsonl`
- `metadata/processing_log.jsonl`

Phase 3 should extend this structure with review-oriented artifacts.

### New Review Batch Structure

Suggested location:

`D:/gtobig/data/vision_db/review_batches/<batch_id>/`

Suggested contents:

- `crops/`
  - candidate crop images grouped by slot or source image
- `overlays/`
  - preview images showing source screenshots with detected boxes
- `review_queue.jsonl`
  - machine-readable review queue
- `summary.json`
  - batch counts and aggregate statistics

### Formal Sample Storage

Approved samples should be written into the formal sample tree, for example:

`D:/gtobig/data/vision_db/samples/cards/<card_slot>/<label>/`

This lets later phases inspect samples by both slot and card identity without mixing unreviewed material into the same tree.

## Processing Model

Phase 3 should operate as a staged workflow rather than a one-shot recognizer.

### Step 1: Profile Matching And Normalization

For each source image:

1. determine whether it matches a known profile
2. normalize the image into the profile's logical table layout
3. record the chosen profile and any normalization transform
4. reject unknown profiles with an explicit log entry rather than guessing

### Step 2: Candidate Crop Extraction

#### Hero Cards

- crop hero cards from fixed boxes in the chosen profile
- allow a small configured margin if needed for stability
- log if the extracted crop looks structurally invalid

#### Community Cards

- search within `community_search_roi`
- detect five card candidates automatically
- use profile fixed community boxes as a validation aid or preferred shortcut when appropriate
- if five valid community boxes cannot be recovered, mark missing or uncertain slots for review rather than inventing crops

This phase should prefer false negatives over false positives. Missing a crop is safer than polluting the database with bad card regions.

### Step 3: Candidate Label Proposal

Each extracted crop should receive one primary candidate label.

#### Main Signal

- match the crop against the existing real template library in `templates/cards/`

#### Secondary Context Rules

- exact same card label should not appear twice in one screenshot
- hero slots and community slots should remain distinct semantic regions
- low-confidence or contradictory matches should be downgraded to review-needed status

The pipeline should keep one primary candidate label plus score and source metadata. It should not directly auto-approve samples.

### Step 4: Review Batch Output

The pipeline should write all automatic results into a review batch.

Each review record should include:

- `batch_id`
- `image_id`
- `source_profile`
- `card_slot`
- `crop_path`
- `overlay_path`
- `bbox`
- `candidate_label`
- `candidate_score`
- `match_source`
- `review_status`

Initial `review_status` values should support:

- `pending`
- `approved`
- `corrected`
- `rejected`
- `needs_review`

### Step 5: Human Review And Formal Ingestion

Only after the user reviews the batch should samples enter the formal library.

Required behavior:

- `approved` keeps the proposed label
- `corrected` uses the user-supplied final label
- `rejected` never enters the formal sample library
- `needs_review` remains outside the formal sample library until resolved

Formal ingestion should:

- copy or move approved crop files into `samples/cards/...`
- append approved metadata rows to `samples_cards.jsonl`
- preserve traceability back to the review batch
- avoid duplicate formal sample insertion

## Metadata Expectations

### Review Queue Metadata

Suggested review queue fields:

- `batch_id`
- `review_item_id`
- `image_id`
- `source_profile`
- `card_slot`
- `candidate_label`
- `candidate_score`
- `match_source`
- `bbox`
- `crop_path`
- `overlay_path`
- `review_status`

Optional but useful:

- `normalized_image_path`
- `notes`
- `created_at`

### Formal Samples Metadata

Phase 3 should extend `samples_cards.jsonl` so approved samples become first-class assets.

Suggested fields:

- `sample_id`
- `image_id`
- `source_profile`
- `card_slot`
- `label`
- `sample_path`
- `bbox`
- `width`
- `height`
- `quality_status`
- `review_batch_id`
- `review_item_id`
- `ingested_at`

`quality_status` should reflect approved data quality, not raw candidate certainty.

### Processing Log Metadata

`processing_log.jsonl` should continue recording success and failure steps. New phase 3 events should include crop extraction, candidate labeling, review batch generation, and formal ingestion.

## Duplicate Prevention

Formal sample integrity is more important than maximizing row count.

Required safeguards:

- generate a stable sample identifier or hash for ingested crops
- detect repeated ingestion of the same review item
- detect repeated ingestion of the same crop content where practical
- refuse or log duplicates rather than silently appending them

## Conservative Failure Policy

Phase 3 should behave conservatively when uncertain.

Required rules:

- if a profile cannot be identified, log and skip the image
- if a community card cannot be confidently localized, mark the slot as review-needed
- if template matching confidence is below threshold, do not treat the label as reliable
- if bbox geometry is abnormal, log it and keep it out of formal ingestion
- if context rules conflict with the top template match, lower confidence or mark for review
- never write uncertain automatic outputs directly into the formal sample library

## Action Button Glow Experiment

Phase 3 also includes a small experimental auxiliary module for action-button glow detection.

### Purpose

This module exists to evaluate whether button brightness can later become a useful "can act" hint for state detection. It is not part of the formal sample-ingestion gate.

### Required Fixed ROIs

The coordinate tool should support these semantic ROIs:

- `fold_button_roi`
- `bet_button_roi`
- `check_button_roi`

### Suggested Signals

For each button ROI, the experiment may record:

- average brightness
- highlighted pixel ratio
- saturation
- dominant color distribution

Suggested output fields:

- `fold_glowing`
- `bet_glowing`
- `check_glowing`
- `can_act_hint`

### Boundary Rules

- this module is experimental
- it must not block sample extraction or review-batch generation
- it may write separate metadata rows for later analysis
- it should help future turn-detection work without bloating the main Phase 3 scope

## Phase 3 Deliverables

Phase 3 should produce these concrete outcomes:

1. a coordinate confirmation tool with saveable profile JSON
2. at least one confirmed default seed profile based on a real screenshot
3. a fixed-layout crop extraction pipeline for hero and community cards
4. a candidate-label generation step using real templates plus context rules
5. a review-batch output workflow
6. a formal ingestion workflow for approved samples
7. duplicate-prevention safeguards for formal samples
8. an experimental action-button glow signal exporter

## Acceptance Criteria

Phase 3 is successful when all of the following are true:

1. the user can open a screenshot, draw or adjust boxes, and save profile coordinates
2. the supplied `1920x1080` seed screenshot can be represented as a default profile
3. the current fixed-layout screenshot family can be normalized through known profiles
4. hero cards can be cropped from real screenshots using configured boxes
5. community cards can be recovered from the configured search ROI
6. each crop receives one candidate label from the real template library plus context rules
7. automatic results are written to a review batch instead of directly to the formal sample library
8. a human can approve or correct labels before formal ingestion
9. only approved or corrected samples are written into `samples/cards/...` and `samples_cards.jsonl`
10. duplicate formal ingestion is prevented or explicitly logged
11. low-confidence or malformed cases are logged instead of silently accepted
12. experimental action-button glow signals can be recorded from fixed ROIs without interfering with the main workflow

## Verification Plan

Phase 3 verification should confirm:

1. the coordinate tool saves and reloads profile JSON correctly
2. the default seed profile boxes line up on the confirmed real screenshot
3. the pipeline can process at least one representative image from each known capture variant
4. extracted hero and community crops are visually plausible
5. candidate labels match obvious examples from the current dataset
6. review batches contain crops, overlays, and machine-readable queue rows
7. approved samples enter the formal library and rejected samples do not
8. repeated ingestion attempts do not create duplicate formal rows
9. action-button experiment output is produced when button ROIs are configured

## Future Phase Mapping

- **Phase 4:** real static recognition prototype using the growing approved sample library
- **Phase 5:** live capture integration
- **Phase 6:** richer state detection and engine orchestration
- **Phase 7:** GUI

## Notes

- Phase 3 should remain disciplined about using only real screenshot data.
- The coordinate confirmation tool is intentionally included early because careful calibration is more valuable than aggressive automation at this stage.
- The approved sample library should be treated as a long-term asset that later models and recognizers depend on.
