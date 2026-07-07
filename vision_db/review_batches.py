import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from vision_db.action_hints import compute_action_hints
from vision_db.crop_extractor import detect_community_cards, extract_hero_crops
from vision_db.jsonl_store import append_jsonl
from vision_db.normalization import normalize_capture
from vision_db.profile_store import Box, load_profile
from vision_db.template_matcher import choose_primary_label, score_template_matches


@dataclass(frozen=True)
class ReviewBatchSummary:
    batch_id: str
    review_item_count: int
    needs_review_count: int

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


def _save_overlay(image: Image.Image, boxes: list[Box], path: Path) -> None:
    overlay = image.copy()
    draw = ImageDraw.Draw(overlay)
    for x, y, width, height in boxes:
        draw.rectangle((x, y, x + width, y + height), outline="#ff4b4b", width=2)
    path.parent.mkdir(parents=True, exist_ok=True)
    overlay.save(path)


def build_review_batch(
    db_root: Path,
    profile_path: Path,
    batch_root: Path,
    template_threshold: float = 0.65,
    limit: int | None = None,
) -> ReviewBatchSummary:
    profile = load_profile(profile_path)
    image_rows = _load_jsonl(db_root / "metadata" / "images.jsonl")
    if limit is not None:
        image_rows = image_rows[:limit]

    batch_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    current_root = batch_root / batch_id
    crops_dir = current_root / "crops"
    overlays_dir = current_root / "overlays"
    queue_path = current_root / "review_queue.jsonl"
    crops_dir.mkdir(parents=True, exist_ok=True)
    overlays_dir.mkdir(parents=True, exist_ok=True)

    review_item_count = 0
    needs_review_count = 0
    template_dir = db_root / "templates" / "cards"

    for image_row in image_rows:
        source_path = Path(image_row.get("raw_copy_path") or image_row["source_path"])
        with Image.open(source_path) as source_image:
            normalized = normalize_capture(source_image)

        crops = extract_hero_crops(normalized.image, profile) + detect_community_cards(
            normalized.image, profile
        )
        overlay_path = overlays_dir / f'{image_row["image_id"]}.png'
        _save_overlay(normalized.image, [crop.bbox for crop in crops], overlay_path)
        action_hints = (
            compute_action_hints(normalized.image, profile.button_rois)
            if profile.button_rois
            else {}
        )

        used_labels: set[str] = set()
        for index, crop in enumerate(crops, start=1):
            matches = score_template_matches(crop.image, template_dir)
            candidate = choose_primary_label(
                crop.card_slot, matches, used_labels, template_threshold
            )
            used_labels.add(candidate.label)

            crop_path = crops_dir / f'{image_row["image_id"]}_{crop.card_slot}.png'
            crop.image.save(crop_path)
            append_jsonl(
                queue_path,
                {
                    "batch_id": batch_id,
                    "review_item_id": f'{image_row["image_id"]}-{index}',
                    "image_id": image_row["image_id"],
                    "source_profile": profile.profile_name,
                    "card_slot": crop.card_slot,
                    "candidate_label": candidate.label,
                    "candidate_score": round(candidate.score, 4),
                    "match_source": candidate.match_source,
                    "bbox": list(crop.bbox),
                    "crop_path": str(crop_path),
                    "overlay_path": str(overlay_path),
                    "review_status": candidate.review_status,
                    "action_hints": action_hints,
                },
            )
            review_item_count += 1
            if candidate.review_status != "pending":
                needs_review_count += 1

    summary = {
        "batch_id": batch_id,
        "review_item_count": review_item_count,
        "needs_review_count": needs_review_count,
    }
    (current_root / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return ReviewBatchSummary(**summary)
