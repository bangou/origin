# GitHub Upload Policy

**Project:** GTOBig  
**Purpose:** Define what should be uploaded to GitHub, when version milestones should be published, and what reminder behavior must be followed before each upload checkpoint.

## Repository Strategy

- Use one GitHub repository for the project.
- Default recommendation: keep the repository **private**.
- Store source code, project docs, plans, specs, tests, and small reusable assets in the repository.
- Keep large screenshot datasets and derived bulk image data out of normal Git history.

## What Can Be Uploaded

Recommended to upload:

- `core/`
- `engine/`
- `perception/`
- `ui/`
- `tests/`
- `docs/`
- `scripts/`
- `requirements.txt`
- `config.yaml`
- `main.py`
- small reusable template assets if later approved
- metadata structure files if later approved

## What Should Not Be Uploaded In Normal Git

Do not upload these in standard Git history:

- `screenshots/`
- `data/vision_db/raw_full/`
- `data/vision_db/compressed_full/`
- `data/vision_db/exports/`
- `.venv/`
- `__pycache__/`
- bulk generated caches or logs

Reason:

- repository size grows too quickly
- full screenshot data is a long-term local asset and should remain easy to reprocess
- large binary history is difficult to clean later

## Future Exception Rule

If the project later needs to synchronize large image datasets to GitHub:

- prefer **Git LFS**
- do not add the full dataset to normal Git history first
- decide explicitly which folders are worth syncing before enabling LFS

## Versioning Policy

Use milestone-based pre-1.0 versioning.

Planned milestones:

- `v0.1.0-alpha`
  - phase 1 prototype skeleton complete
- `v0.2.0-alpha`
  - phase 2 vision database pipeline complete
- `v0.3.0-alpha`
  - phase 3 crop extraction and sample labeling workflow complete
- `v0.4.0-alpha`
  - phase 4 real static recognition prototype complete
- `v0.5.0-beta.1`
  - phase 5 live capture connected
- `v0.6.0-beta.1`
  - phase 6 orchestration with state machine and engine complete
- `v0.8.0-beta.1`
  - phase 7 GUI usable
- `v1.0.0`
  - stable end-to-end product ready for long-term maintenance

## Upload Checkpoints

### Checkpoint 1: Upload Now

Version:

- `v0.1.0-alpha`

Why:

- phase 1 is already complete
- the codebase, plans, and specs are already worth protecting in version control

Recommended contents:

- current code
- project documents
- phase 2 spec
- phase 2 implementation plan

### Checkpoint 2: Upload After Phase 2

Version:

- `v0.2.0-alpha`

Why:

- the reusable static-image database pipeline becomes a real project asset

Recommended contents:

- phase 2 code
- scripts
- tests
- metadata schema and docs

Do not upload:

- full screenshot datasets

### Checkpoint 3: Upload After Phase 4 or Phase 5

Version:

- `v0.4.0-alpha` or `v0.5.0-beta.1`

Why:

- the repository will start to show real recognition value or real-time pipeline value

## Reminder Rule

Before every upload checkpoint, the assistant must explicitly remind the user:

1. that an upload milestone has been reached
2. which version tag is recommended
3. which files should be uploaded
4. which data folders should stay local

This reminder is required at minimum when the project reaches:

- phase 1 complete
- phase 2 complete
- phase 4 complete
- phase 5 complete
- any later point where a release candidate or stable version becomes appropriate

## Current Status

Current recommended next upload:

- initialize Git locally
- create the first local commit
- create a private GitHub repository
- push the current project as `v0.1.0-alpha`

## Notes

- This file records the project upload policy so it stays stable across future sessions.
- If the repository visibility changes from private to public later, review all tracked assets again before pushing.
