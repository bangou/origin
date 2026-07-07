import json
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha1
from pathlib import Path
from shutil import copy2
from typing import Any

from PIL import Image

from vision_db.jsonl_store import append_jsonl
from vision_db.layout import ensure_layout


@dataclass(frozen=True)
class IngestSummary:
    ingested_count: int
    duplicate_count: int
    skipped_count: int

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _sample_id(crop_path: Path, label: str, card_slot: str) -> str:
    digest = sha1()
    digest.update(crop_path.read_bytes())
    digest.update(label.encode("utf-8"))
    digest.update(card_slot.encode("utf-8"))
    return digest.hexdigest()[:16]


def ingest_review_batch(batch_dir: Path, db_root: Path) -> IngestSummary:
    layout = ensure_layout(db_root)
    queue_rows = _load_jsonl(batch_dir / "review_queue.jsonl")
    metadata_path = layout.metadata / "samples_cards.jsonl"
    existing_ids = {
        row["sample_id"] for row in _load_jsonl(metadata_path) if "sample_id" in row
    }

    ingested_count = 0
    duplicate_count = 0
    skipped_count = 0

    for row in queue_rows:
        if row["review_status"] not in {"approved", "corrected"}:
            skipped_count += 1
            continue

        final_label = row.get("final_label") or row["candidate_label"]
        crop_path = Path(row["crop_path"])
        sample_id = _sample_id(crop_path, final_label, row["card_slot"])
        if sample_id in existing_ids:
            duplicate_count += 1
            continue

        target_dir = layout.samples_cards / row["card_slot"] / final_label
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / f"{sample_id}{crop_path.suffix.lower()}"
        copy2(crop_path, target_path)
        with Image.open(crop_path) as crop_image:
            width, height = crop_image.size

        append_jsonl(
            metadata_path,
            {
                "sample_id": sample_id,
                "image_id": row["image_id"],
                "source_profile": row["source_profile"],
                "card_slot": row["card_slot"],
                "label": final_label,
                "sample_path": str(target_path),
                "bbox": row["bbox"],
                "width": width,
                "height": height,
                "quality_status": row["review_status"],
                "review_batch_id": row["batch_id"],
                "review_item_id": row["review_item_id"],
                "ingested_at": datetime.now(UTC).isoformat(),
            },
        )
        existing_ids.add(sample_id)
        ingested_count += 1

    return IngestSummary(
        ingested_count=ingested_count,
        duplicate_count=duplicate_count,
        skipped_count=skipped_count,
    )
