# Vision DB Phase 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the phase 2 static-image vision database pipeline that scans `D:/gtobig/screenshots`, preserves original images, generates compressed working copies for large full screenshots, normalizes trusted `*_raw.png` card seeds into a template library, and records all processing state in JSONL metadata.

**Architecture:** Keep the phase 2 work separate from the existing `main.py` prototype by introducing a focused `vision_db/` package plus a small CLI entrypoint. The package should split responsibilities cleanly across layout creation, source scanning, image compression, metadata writing, and orchestration so later phases can reuse the same database assets for crop extraction, template matching, numeric OCR, and CNN training.

**Tech Stack:** Python 3.11+, Pillow, pytest, standard library (`pathlib`, `json`, `hashlib`, `shutil`, `dataclasses`, `typing`, `datetime`)

## Global Constraints

- Source folder is `D:/gtobig/screenshots`.
- That folder has already been manually cleaned; it should be treated as usable input.
- Files named `*_raw.png` are trusted labeled card seeds. Example: `Ah_raw.png` means ace of hearts.
- Images larger than `1MB` should get compressed copies.
- Compression must not change pixel dimensions.
- Original images must be preserved.
- The final database should be structured completely enough for long-term reuse, but the implementation order should stay practical and incremental.
- Phase 2 must not implement real-time screen capture.
- Phase 2 must not implement ROI calibration from a live table.
- Phase 2 must not implement real OCR execution.
- Phase 2 must not implement automatic full-batch crop extraction of all card slots.
- Phase 2 must not implement CNN training.
- Phase 2 must not implement GUI work.
- Phase 2 must not implement strategy-engine integration.
- Phase 2 does not use OCR for cards; card recognition assets are being prepared for template matching first.
- Metadata must use JSONL in `D:/gtobig/data/vision_db/metadata/`.
- This workspace is currently not a Git repository, so commit steps should be skipped unless Git is initialized before execution.

---

## File Structure

- Modify: `D:/gtobig/requirements.txt` — add the image-processing dependency needed for compression and metadata inspection.
- Create: `D:/gtobig/vision_db/__init__.py` — package export surface.
- Create: `D:/gtobig/vision_db/layout.py` — database directory layout dataclass and directory creation.
- Create: `D:/gtobig/vision_db/source_index.py` — source scan, trusted-raw classification, and template label parsing.
- Create: `D:/gtobig/vision_db/image_ops.py` — dimension-preserving compression helpers and image inspection.
- Create: `D:/gtobig/vision_db/jsonl_store.py` — JSONL writing helpers.
- Create: `D:/gtobig/vision_db/pipeline.py` — end-to-end build orchestration and summary reporting.
- Create: `D:/gtobig/scripts/build_vision_db.py` — CLI entrypoint for phase 2 database building.
- Create: `D:/gtobig/tests/test_vision_db_source_index.py` — tests for scan and `*_raw.png` label parsing.
- Create: `D:/gtobig/tests/test_vision_db_image_ops.py` — tests for compression behavior and dimension preservation.
- Create: `D:/gtobig/tests/test_vision_db_pipeline.py` — end-to-end pipeline test on a synthetic dataset.
- Create: `D:/gtobig/tests/test_build_vision_db_cli.py` — CLI smoke test and summary output verification.

## Shared Interface Plan

The tasks below depend on these exact interfaces:

- `ensure_layout(root: Path) -> VisionDbLayout`
- `parse_template_label(path: Path) -> tuple[str, str, str]`
- `scan_source_images(source_dir: Path) -> list[SourceImageRecord]`
- `compress_image_copy(source_path: Path, destination_path: Path) -> CompressionResult`
- `append_jsonl(path: Path, row: dict[str, Any]) -> None`
- `build_vision_db(source_dir: Path, db_root: Path) -> BuildSummary`
- `main(argv: Sequence[str] | None = None) -> int`

## Task 1: Create the Layout and Source Scanner

**Files:**
- Modify: `D:/gtobig/requirements.txt`
- Create: `D:/gtobig/vision_db/__init__.py`
- Create: `D:/gtobig/vision_db/layout.py`
- Create: `D:/gtobig/vision_db/source_index.py`
- Test: `D:/gtobig/tests/test_vision_db_source_index.py`

**Interfaces:**
- Consumes: no earlier phase 2 code.
- Produces:
  - `ensure_layout(root: Path) -> VisionDbLayout`
  - `parse_template_label(path: Path) -> tuple[str, str, str]`
  - `scan_source_images(source_dir: Path) -> list[SourceImageRecord]`

- [ ] **Step 1: Write the failing test**

```python
from pathlib import Path

from PIL import Image

from vision_db.source_index import parse_template_label, scan_source_images


def test_scan_source_images_classifies_template_seeds_and_full_images(
    tmp_path: Path,
) -> None:
    source_dir = tmp_path / "screenshots"
    source_dir.mkdir()

    Image.new("RGBA", (40, 60), "white").save(source_dir / "Ah_raw.png")
    Image.new("RGB", (320, 180), "green").save(source_dir / "hand1_flop.png")

    records = scan_source_images(source_dir)
    by_name = {record["file_name"]: record for record in records}

    assert parse_template_label(source_dir / "Ah_raw.png") == ("Ah", "A", "h")
    assert by_name["Ah_raw.png"]["kind"] == "template_seed"
    assert by_name["hand1_flop.png"]["kind"] == "full_screenshot"
    assert by_name["hand1_flop.png"]["width"] == 320
    assert by_name["hand1_flop.png"]["height"] == 180
```

- [ ] **Step 2: Run test to verify it fails**

Run: `D:\gtobig\.venv\Scripts\python.exe -m pytest D:\gtobig\tests\test_vision_db_source_index.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'vision_db'`

- [ ] **Step 3: Write minimal implementation**

`D:/gtobig/requirements.txt`

```text
pyyaml>=6.0
pytest>=8.0
Pillow>=10.0
```

`D:/gtobig/vision_db/__init__.py`

```python
from vision_db.layout import VisionDbLayout, ensure_layout
from vision_db.source_index import parse_template_label, scan_source_images

__all__ = [
    "VisionDbLayout",
    "ensure_layout",
    "parse_template_label",
    "scan_source_images",
]
```

`D:/gtobig/vision_db/layout.py`

```python
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class VisionDbLayout:
    root: Path
    raw_full: Path
    compressed_full: Path
    templates_cards: Path
    samples_cards: Path
    metadata: Path
    exports: Path


def ensure_layout(root: Path) -> VisionDbLayout:
    layout = VisionDbLayout(
        root=root,
        raw_full=root / "raw_full",
        compressed_full=root / "compressed_full",
        templates_cards=root / "templates" / "cards",
        samples_cards=root / "samples" / "cards",
        metadata=root / "metadata",
        exports=root / "exports",
    )

    for path in (
        layout.root,
        layout.raw_full,
        layout.compressed_full,
        layout.templates_cards,
        layout.samples_cards,
        layout.metadata,
        layout.exports,
    ):
        path.mkdir(parents=True, exist_ok=True)

    return layout
```

`D:/gtobig/vision_db/source_index.py`

```python
from pathlib import Path
from typing import Literal, TypedDict

from PIL import Image


class SourceImageRecord(TypedDict):
    file_name: str
    source_path: str
    kind: Literal["template_seed", "full_screenshot"]
    width: int
    height: int
    file_size: int


def parse_template_label(path: Path) -> tuple[str, str, str]:
    label = path.stem.removesuffix("_raw")
    return label, label[0], label[1]


def scan_source_images(source_dir: Path) -> list[SourceImageRecord]:
    records: list[SourceImageRecord] = []
    for path in sorted(source_dir.iterdir()):
        if not path.is_file():
            continue

        with Image.open(path) as image:
            width, height = image.size

        kind: Literal["template_seed", "full_screenshot"]
        kind = "template_seed" if path.name.endswith("_raw.png") else "full_screenshot"
        records.append(
            {
                "file_name": path.name,
                "source_path": str(path),
                "kind": kind,
                "width": width,
                "height": height,
                "file_size": path.stat().st_size,
            }
        )

    return records
```

`D:/gtobig/tests/test_vision_db_source_index.py`

```python
from pathlib import Path

from PIL import Image

from vision_db.source_index import parse_template_label, scan_source_images


def test_scan_source_images_classifies_template_seeds_and_full_images(
    tmp_path: Path,
) -> None:
    source_dir = tmp_path / "screenshots"
    source_dir.mkdir()

    Image.new("RGBA", (40, 60), "white").save(source_dir / "Ah_raw.png")
    Image.new("RGB", (320, 180), "green").save(source_dir / "hand1_flop.png")

    records = scan_source_images(source_dir)
    by_name = {record["file_name"]: record for record in records}

    assert parse_template_label(source_dir / "Ah_raw.png") == ("Ah", "A", "h")
    assert by_name["Ah_raw.png"]["kind"] == "template_seed"
    assert by_name["hand1_flop.png"]["kind"] == "full_screenshot"
    assert by_name["hand1_flop.png"]["width"] == 320
    assert by_name["hand1_flop.png"]["height"] == 180
```

- [ ] **Step 4: Run test to verify it passes**

Run: `D:\gtobig\.venv\Scripts\python.exe -m pytest D:\gtobig\tests\test_vision_db_source_index.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

Run: `git -C D:\gtobig rev-parse --is-inside-work-tree`
Expected in the current workspace: FAIL because `D:\gtobig` is not yet a Git repository. Skip commit until Git is initialized.

If Git has been initialized before this step, run:

```bash
git -C D:\gtobig add requirements.txt vision_db/__init__.py vision_db/layout.py vision_db/source_index.py tests/test_vision_db_source_index.py
git -C D:\gtobig commit -m "feat: add vision db layout and source scanner"
```

## Task 2: Add Dimension-Preserving Compression

**Files:**
- Create: `D:/gtobig/vision_db/image_ops.py`
- Test: `D:/gtobig/tests/test_vision_db_image_ops.py`

**Interfaces:**
- Consumes:
  - `scan_source_images(source_dir: Path) -> list[SourceImageRecord]`
- Produces:
  - `compress_image_copy(source_path: Path, destination_path: Path) -> CompressionResult`

- [ ] **Step 1: Write the failing test**

```python
from pathlib import Path

from PIL import Image

from vision_db.image_ops import compress_image_copy


def test_compress_image_copy_keeps_dimensions_and_reduces_size(tmp_path: Path) -> None:
    source_path = tmp_path / "large.png"
    destination_path = tmp_path / "compressed.png"

    noisy = Image.effect_noise((1600, 900), 100.0).convert("RGB")
    noisy.save(source_path, format="PNG")

    assert source_path.stat().st_size > 1_000_000

    result = compress_image_copy(source_path, destination_path)

    assert destination_path.exists()
    assert result["source_size"] > result["destination_size"]
    assert result["width"] == 1600
    assert result["height"] == 900
```

- [ ] **Step 2: Run test to verify it fails**

Run: `D:\gtobig\.venv\Scripts\python.exe -m pytest D:\gtobig\tests\test_vision_db_image_ops.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'vision_db.image_ops'`

- [ ] **Step 3: Write minimal implementation**

`D:/gtobig/vision_db/image_ops.py`

```python
from pathlib import Path
from typing import TypedDict

from PIL import Image


class CompressionResult(TypedDict):
    source_size: int
    destination_size: int
    width: int
    height: int


def compress_image_copy(source_path: Path, destination_path: Path) -> CompressionResult:
    with Image.open(source_path) as image:
        width, height = image.size
        quantized = image.convert("P", palette=Image.Palette.ADAPTIVE, colors=256)
        quantized.save(destination_path, format="PNG", optimize=True, compress_level=9)

    return {
        "source_size": source_path.stat().st_size,
        "destination_size": destination_path.stat().st_size,
        "width": width,
        "height": height,
    }
```

`D:/gtobig/tests/test_vision_db_image_ops.py`

```python
from pathlib import Path

from PIL import Image

from vision_db.image_ops import compress_image_copy


def test_compress_image_copy_keeps_dimensions_and_reduces_size(tmp_path: Path) -> None:
    source_path = tmp_path / "large.png"
    destination_path = tmp_path / "compressed.png"

    noisy = Image.effect_noise((1600, 900), 100.0).convert("RGB")
    noisy.save(source_path, format="PNG")

    assert source_path.stat().st_size > 1_000_000

    result = compress_image_copy(source_path, destination_path)

    assert destination_path.exists()
    assert result["source_size"] > result["destination_size"]
    assert result["width"] == 1600
    assert result["height"] == 900
```

- [ ] **Step 4: Run test to verify it passes**

Run: `D:\gtobig\.venv\Scripts\python.exe -m pytest D:\gtobig\tests\test_vision_db_image_ops.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

Run: `git -C D:\gtobig rev-parse --is-inside-work-tree`
Expected in the current workspace: FAIL because `D:\gtobig` is not yet a Git repository. Skip commit until Git is initialized.

If Git has been initialized before this step, run:

```bash
git -C D:\gtobig add vision_db/image_ops.py tests/test_vision_db_image_ops.py
git -C D:\gtobig commit -m "feat: add vision db image compression helpers"
```

## Task 3: Build Metadata Writing and the End-to-End Pipeline

**Files:**
- Create: `D:/gtobig/vision_db/jsonl_store.py`
- Create: `D:/gtobig/vision_db/pipeline.py`
- Test: `D:/gtobig/tests/test_vision_db_pipeline.py`

**Interfaces:**
- Consumes:
  - `ensure_layout(root: Path) -> VisionDbLayout`
  - `parse_template_label(path: Path) -> tuple[str, str, str]`
  - `scan_source_images(source_dir: Path) -> list[SourceImageRecord]`
  - `compress_image_copy(source_path: Path, destination_path: Path) -> CompressionResult`
- Produces:
  - `append_jsonl(path: Path, row: dict[str, Any]) -> None`
  - `build_vision_db(source_dir: Path, db_root: Path) -> BuildSummary`

- [ ] **Step 1: Write the failing test**

```python
import json
from pathlib import Path

from PIL import Image

from vision_db.pipeline import build_vision_db


def test_build_vision_db_creates_layout_templates_and_metadata(tmp_path: Path) -> None:
    source_dir = tmp_path / "screenshots"
    db_root = tmp_path / "data" / "vision_db"
    source_dir.mkdir()

    Image.new("RGBA", (40, 60), "white").save(source_dir / "Ah_raw.png")

    noisy = Image.effect_noise((1600, 900), 100.0).convert("RGB")
    noisy.save(source_dir / "hand1_flop.png", format="PNG")

    summary = build_vision_db(source_dir, db_root)

    assert summary["total_images"] == 2
    assert summary["template_seed_count"] == 1
    assert summary["full_screenshot_count"] == 1
    assert summary["compressed_count"] == 1
    assert (db_root / "templates" / "cards" / "Ah.png").exists()
    assert (db_root / "metadata" / "images.jsonl").exists()
    assert (db_root / "metadata" / "templates_cards.jsonl").exists()
    assert (db_root / "metadata" / "samples_cards.jsonl").exists()
    assert (db_root / "metadata" / "processing_log.jsonl").exists()

    template_rows = [
        json.loads(line)
        for line in (db_root / "metadata" / "templates_cards.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]
    assert template_rows[0]["label"] == "Ah"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `D:\gtobig\.venv\Scripts\python.exe -m pytest D:\gtobig\tests\test_vision_db_pipeline.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'vision_db.pipeline'`

- [ ] **Step 3: Write minimal implementation**

`D:/gtobig/vision_db/jsonl_store.py`

```python
import json
from pathlib import Path
from typing import Any


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
```

`D:/gtobig/vision_db/pipeline.py`

```python
from datetime import datetime, UTC
from hashlib import sha1
from pathlib import Path
from shutil import copy2
from typing import Any, TypedDict

from vision_db.image_ops import compress_image_copy
from vision_db.jsonl_store import append_jsonl
from vision_db.layout import ensure_layout
from vision_db.source_index import parse_template_label, scan_source_images


class BuildSummary(TypedDict):
    total_images: int
    template_seed_count: int
    full_screenshot_count: int
    compressed_count: int
    failure_count: int


def _make_id(text: str) -> str:
    return sha1(text.encode("utf-8")).hexdigest()[:12]


def build_vision_db(source_dir: Path, db_root: Path) -> BuildSummary:
    layout = ensure_layout(db_root)
    records = scan_source_images(source_dir)
    summary: BuildSummary = {
        "total_images": len(records),
        "template_seed_count": 0,
        "full_screenshot_count": 0,
        "compressed_count": 0,
        "failure_count": 0,
    }

    images_jsonl = layout.metadata / "images.jsonl"
    templates_jsonl = layout.metadata / "templates_cards.jsonl"
    samples_jsonl = layout.metadata / "samples_cards.jsonl"
    processing_jsonl = layout.metadata / "processing_log.jsonl"
    samples_jsonl.touch()

    for record in records:
        source_path = Path(record["source_path"])
        if record["kind"] == "template_seed":
            summary["template_seed_count"] += 1
            label, rank, suit = parse_template_label(source_path)
            destination_path = layout.templates_cards / f"{label}{source_path.suffix}"
            copy2(source_path, destination_path)
            append_jsonl(
                templates_jsonl,
                {
                    "template_id": _make_id(str(source_path)),
                    "label": label,
                    "rank": rank,
                    "suit": suit,
                    "template_path": str(destination_path),
                    "width": record["width"],
                    "height": record["height"],
                    "source_type": "raw_seed",
                },
            )
            append_jsonl(
                processing_jsonl,
                {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "step": "template_copy",
                    "source_path": str(source_path),
                    "result": "ok",
                    "message": f"normalized {label}",
                },
            )
            continue

        summary["full_screenshot_count"] += 1
        image_id = _make_id(str(source_path))
        raw_copy_path = layout.raw_full / f"{image_id}{source_path.suffix}"
        copy2(source_path, raw_copy_path)
        compressed_path = ""

        if record["file_size"] > 1_000_000:
            compressed_target = layout.compressed_full / f"{image_id}{source_path.suffix}"
            compress_image_copy(source_path, compressed_target)
            compressed_path = str(compressed_target)
            summary["compressed_count"] += 1

        append_jsonl(
            images_jsonl,
            {
                "image_id": image_id,
                "source_path": str(source_path),
                "raw_copy_path": str(raw_copy_path),
                "compressed_path": compressed_path,
                "width": record["width"],
                "height": record["height"],
                "file_size": record["file_size"],
                "is_over_1mb": record["file_size"] > 1_000_000,
                "theme": "default",
                "status": "indexed",
            },
        )
        append_jsonl(
            processing_jsonl,
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "step": "full_image_index",
                "source_path": str(source_path),
                "result": "ok",
                "message": "indexed full screenshot",
            },
        )

    return summary
```

`D:/gtobig/tests/test_vision_db_pipeline.py`

```python
import json
from pathlib import Path

from PIL import Image

from vision_db.pipeline import build_vision_db


def test_build_vision_db_creates_layout_templates_and_metadata(tmp_path: Path) -> None:
    source_dir = tmp_path / "screenshots"
    db_root = tmp_path / "data" / "vision_db"
    source_dir.mkdir()

    Image.new("RGBA", (40, 60), "white").save(source_dir / "Ah_raw.png")

    noisy = Image.effect_noise((1600, 900), 100.0).convert("RGB")
    noisy.save(source_dir / "hand1_flop.png", format="PNG")

    summary = build_vision_db(source_dir, db_root)

    assert summary["total_images"] == 2
    assert summary["template_seed_count"] == 1
    assert summary["full_screenshot_count"] == 1
    assert summary["compressed_count"] == 1
    assert (db_root / "templates" / "cards" / "Ah.png").exists()
    assert (db_root / "metadata" / "images.jsonl").exists()
    assert (db_root / "metadata" / "templates_cards.jsonl").exists()
    assert (db_root / "metadata" / "samples_cards.jsonl").exists()
    assert (db_root / "metadata" / "processing_log.jsonl").exists()

    template_rows = [
        json.loads(line)
        for line in (db_root / "metadata" / "templates_cards.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]
    assert template_rows[0]["label"] == "Ah"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `D:\gtobig\.venv\Scripts\python.exe -m pytest D:\gtobig\tests\test_vision_db_pipeline.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

Run: `git -C D:\gtobig rev-parse --is-inside-work-tree`
Expected in the current workspace: FAIL because `D:\gtobig` is not yet a Git repository. Skip commit until Git is initialized.

If Git has been initialized before this step, run:

```bash
git -C D:\gtobig add vision_db/jsonl_store.py vision_db/pipeline.py tests/test_vision_db_pipeline.py
git -C D:\gtobig commit -m "feat: add vision db pipeline and metadata output"
```

## Task 4: Add the CLI Entry Point and Summary Output

**Files:**
- Create: `D:/gtobig/scripts/build_vision_db.py`
- Test: `D:/gtobig/tests/test_build_vision_db_cli.py`

**Interfaces:**
- Consumes:
  - `build_vision_db(source_dir: Path, db_root: Path) -> BuildSummary`
- Produces:
  - `main(argv: Sequence[str] | None = None) -> int`

- [ ] **Step 1: Write the failing test**

```python
from pathlib import Path

from PIL import Image

from scripts.build_vision_db import main


def test_cli_builds_database_and_prints_summary(tmp_path: Path, capsys) -> None:
    source_dir = tmp_path / "screenshots"
    db_root = tmp_path / "data" / "vision_db"
    source_dir.mkdir()

    Image.new("RGBA", (40, 60), "white").save(source_dir / "Ah_raw.png")
    noisy = Image.effect_noise((1600, 900), 100.0).convert("RGB")
    noisy.save(source_dir / "hand1_flop.png", format="PNG")

    exit_code = main(["--source", str(source_dir), "--db-root", str(db_root)])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "total_images=2" in output
    assert "template_seed_count=1" in output
    assert "compressed_count=1" in output
```

- [ ] **Step 2: Run test to verify it fails**

Run: `D:\gtobig\.venv\Scripts\python.exe -m pytest D:\gtobig\tests\test_build_vision_db_cli.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.build_vision_db'`

- [ ] **Step 3: Write minimal implementation**

`D:/gtobig/scripts/build_vision_db.py`

```python
import argparse
from pathlib import Path
from typing import Sequence

from vision_db.pipeline import build_vision_db


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the phase 2 vision database.")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--db-root", type=Path, required=True)
    args = parser.parse_args(argv)

    summary = build_vision_db(args.source, args.db_root)
    print(
        " ".join(
            [
                f'total_images={summary["total_images"]}',
                f'template_seed_count={summary["template_seed_count"]}',
                f'full_screenshot_count={summary["full_screenshot_count"]}',
                f'compressed_count={summary["compressed_count"]}',
                f'failure_count={summary["failure_count"]}',
            ]
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

`D:/gtobig/tests/test_build_vision_db_cli.py`

```python
from pathlib import Path

from PIL import Image

from scripts.build_vision_db import main


def test_cli_builds_database_and_prints_summary(tmp_path: Path, capsys) -> None:
    source_dir = tmp_path / "screenshots"
    db_root = tmp_path / "data" / "vision_db"
    source_dir.mkdir()

    Image.new("RGBA", (40, 60), "white").save(source_dir / "Ah_raw.png")
    noisy = Image.effect_noise((1600, 900), 100.0).convert("RGB")
    noisy.save(source_dir / "hand1_flop.png", format="PNG")

    exit_code = main(["--source", str(source_dir), "--db-root", str(db_root)])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "total_images=2" in output
    assert "template_seed_count=1" in output
    assert "compressed_count=1" in output
```

- [ ] **Step 4: Run test to verify it passes**

Run: `D:\gtobig\.venv\Scripts\python.exe -m pytest D:\gtobig\tests\test_build_vision_db_cli.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

Run: `git -C D:\gtobig rev-parse --is-inside-work-tree`
Expected in the current workspace: FAIL because `D:\gtobig` is not yet a Git repository. Skip commit until Git is initialized.

If Git has been initialized before this step, run:

```bash
git -C D:\gtobig add scripts/build_vision_db.py tests/test_build_vision_db_cli.py
git -C D:\gtobig commit -m "feat: add vision db build cli"
```

## Self-Review

**1. Spec coverage**

- Source folder scanning is covered by Task 1.
- Trusted `*_raw.png` label handling is covered by Task 1 and Task 3.
- Database directory creation under `D:/gtobig/data/vision_db/` is covered by Task 1 and exercised in Task 3.
- Compression of full screenshots larger than `1MB` without changing dimensions is covered by Task 2 and exercised in Task 3.
- JSONL metadata files are covered by Task 3.
- Summary output is covered by Task 4.
- Explicitly out-of-scope items from the spec are not included in any task.

**2. Placeholder scan**

- No `TODO`, `TBD`, or "implement later" placeholders remain in task steps.
- Each task includes a failing test, a verification command, concrete implementation snippets, and a repository-aware commit step.

**3. Type consistency**

- `scan_source_images()` produces records consumed by `build_vision_db()`.
- `compress_image_copy()` is consumed only by the pipeline and returns the exact fields asserted in its test.
- `build_vision_db()` returns the same summary keys that the CLI prints and the CLI test asserts.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-07-vision-db-phase2.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
