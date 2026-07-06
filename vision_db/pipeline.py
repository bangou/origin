from datetime import UTC, datetime
from hashlib import sha1
from pathlib import Path
from shutil import copy2
from typing import TypedDict

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


def _timestamp() -> str:
    return datetime.now(UTC).isoformat()


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

    for path in (images_jsonl, templates_jsonl, samples_jsonl, processing_jsonl):
        path.touch(exist_ok=True)

    for record in records:
        source_path = Path(record["source_path"])
        error = record.get("error")
        if error:
            summary["failure_count"] += 1
            append_jsonl(
                processing_jsonl,
                {
                    "timestamp": _timestamp(),
                    "step": "scan_source_image",
                    "source_path": str(source_path),
                    "result": "error",
                    "message": error,
                },
            )
            continue

        if record["kind"] == "template_seed":
            summary["template_seed_count"] += 1
            label, rank, suit = parse_template_label(source_path)
            destination_path = layout.templates_cards / f"{label}{source_path.suffix.lower()}"
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
                    "timestamp": _timestamp(),
                    "step": "template_copy",
                    "source_path": str(source_path),
                    "result": "ok",
                    "message": f"normalized {label}",
                },
            )
            continue

        summary["full_screenshot_count"] += 1
        image_id = _make_id(str(source_path))
        raw_copy_path = layout.raw_full / f"{image_id}{source_path.suffix.lower()}"
        copy2(source_path, raw_copy_path)
        compressed_path = ""

        if record["file_size"] > 1_000_000:
            compressed_target = layout.compressed_full / f"{image_id}{source_path.suffix.lower()}"
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
                "timestamp": _timestamp(),
                "step": "full_image_index",
                "source_path": str(source_path),
                "result": "ok",
                "message": "indexed full screenshot",
            },
        )

    return summary
