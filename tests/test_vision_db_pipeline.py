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
    assert summary["failure_count"] == 0
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


def test_build_vision_db_logs_bad_files_and_continues(tmp_path: Path) -> None:
    source_dir = tmp_path / "screenshots"
    db_root = tmp_path / "data" / "vision_db"
    source_dir.mkdir()

    Image.new("RGBA", (40, 60), "white").save(source_dir / "Ah_raw.png")
    (source_dir / "broken.png").write_text("not an image", encoding="utf-8")

    summary = build_vision_db(source_dir, db_root)

    assert summary["total_images"] == 2
    assert summary["template_seed_count"] == 1
    assert summary["failure_count"] == 1

    log_rows = [
        json.loads(line)
        for line in (db_root / "metadata" / "processing_log.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]
    assert any(
        row["source_path"].endswith("broken.png") and row["result"] == "error"
        for row in log_rows
    )
