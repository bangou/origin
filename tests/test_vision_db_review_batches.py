import json
from pathlib import Path

from PIL import Image, ImageDraw

from vision_db.jsonl_store import append_jsonl
from vision_db.layout import ensure_layout
from vision_db.profile_store import make_seed_profile, save_profile
from vision_db.review_batches import build_review_batch


def test_build_review_batch_writes_queue_crops_and_overlay(tmp_path: Path) -> None:
    db_root = tmp_path / "data" / "vision_db"
    batch_root = tmp_path / "review_batches"
    profile_path = tmp_path / "profile.json"
    layout = ensure_layout(db_root)
    save_profile(profile_path, make_seed_profile())

    for label, box in {
        "Qc": (908, 872, 50, 73),
        "3c": (963, 872, 50, 73),
        "9d": (829, 476, 50, 73),
        "3s": (882, 476, 50, 73),
        "6s": (936, 476, 49, 73),
        "Tc": (989, 476, 49, 73),
        "4c": (1042, 476, 50, 73),
    }.items():
        template = Image.new("RGB", (box[2], box[3]), "white")
        ImageDraw.Draw(template).text((8, 8), label, fill="black")
        template.save(layout.templates_cards / f"{label}.png")

    source_image = Image.new("RGB", (1920, 1032), "#008b74")
    draw = ImageDraw.Draw(source_image)
    for label, (x, y, width, height) in {
        "Qc": (908, 872, 50, 73),
        "3c": (963, 872, 50, 73),
        "9d": (829, 476, 50, 73),
        "3s": (882, 476, 50, 73),
        "6s": (936, 476, 49, 73),
        "Tc": (989, 476, 49, 73),
        "4c": (1042, 476, 50, 73),
    }.items():
        draw.rectangle((x, y, x + width, y + height), fill="white")
        draw.text((x + 8, y + 8), label, fill="black")

    raw_path = layout.raw_full / "seed.png"
    source_image.save(raw_path)
    append_jsonl(
        layout.metadata / "images.jsonl",
        {
            "image_id": "seed-image",
            "source_path": str(raw_path),
            "raw_copy_path": str(raw_path),
            "compressed_path": "",
            "width": 1920,
            "height": 1032,
            "file_size": raw_path.stat().st_size,
            "is_over_1mb": False,
            "theme": "default",
            "status": "indexed",
        },
    )

    summary = build_review_batch(db_root, profile_path, batch_root, template_threshold=0.65)
    queue_path = batch_root / summary["batch_id"] / "review_queue.jsonl"

    rows = [
        json.loads(line)
        for line in queue_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    assert summary["review_item_count"] == 7
    assert summary["needs_review_count"] == 0
    assert rows[0]["review_status"] == "pending"
    assert rows[0]["candidate_score"] >= 0.65
    assert rows[0]["action_hints"] == {}
    assert Path(rows[0]["crop_path"]).exists()
    assert Path(rows[0]["overlay_path"]).exists()


def test_build_review_batch_skips_blank_turn_and_river(tmp_path: Path) -> None:
    db_root = tmp_path / "data" / "vision_db"
    batch_root = tmp_path / "review_batches"
    profile_path = tmp_path / "profile.json"
    layout = ensure_layout(db_root)
    save_profile(profile_path, make_seed_profile())

    for label, box in {
        "Jd": (908, 872, 50, 73),
        "Ah": (963, 872, 50, 73),
        "9c": (829, 476, 50, 73),
        "8s": (882, 476, 50, 73),
        "As": (936, 476, 49, 73),
    }.items():
        template = Image.new("RGB", (box[2], box[3]), "white")
        ImageDraw.Draw(template).text((8, 8), label, fill="black")
        template.save(layout.templates_cards / f"{label}.png")

    source_image = Image.new("RGB", (1920, 1032), "#008b74")
    draw = ImageDraw.Draw(source_image)
    for label, (x, y, width, height) in {
        "Jd": (908, 872, 50, 73),
        "Ah": (963, 872, 50, 73),
        "9c": (829, 476, 50, 73),
        "8s": (882, 476, 50, 73),
        "As": (936, 476, 49, 73),
    }.items():
        draw.rectangle((x, y, x + width - 1, y + height - 1), fill="white")
        draw.text((x + 8, y + 8), label, fill="black")

    raw_path = layout.raw_full / "seed.png"
    source_image.save(raw_path)
    append_jsonl(
        layout.metadata / "images.jsonl",
        {
            "image_id": "seed-image",
            "source_path": str(raw_path),
            "raw_copy_path": str(raw_path),
            "compressed_path": "",
            "width": 1920,
            "height": 1032,
            "file_size": raw_path.stat().st_size,
            "is_over_1mb": False,
            "theme": "default",
            "status": "indexed",
        },
    )

    summary = build_review_batch(db_root, profile_path, batch_root, template_threshold=0.65)
    queue_path = batch_root / summary["batch_id"] / "review_queue.jsonl"
    rows = [
        json.loads(line)
        for line in queue_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    assert summary["review_item_count"] == 5
    assert [row["card_slot"] for row in rows] == [
        "hand_1",
        "hand_2",
        "flop_1",
        "flop_2",
        "flop_3",
    ]
