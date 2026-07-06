from pathlib import Path

from PIL import Image

from vision_db.layout import ensure_layout
from vision_db.source_index import parse_template_label, scan_source_images


def test_ensure_layout_creates_expected_directories(tmp_path: Path) -> None:
    db_root = tmp_path / "data" / "vision_db"

    layout = ensure_layout(db_root)

    assert layout.root == db_root
    assert layout.raw_full.is_dir()
    assert layout.compressed_full.is_dir()
    assert layout.templates_cards.is_dir()
    assert layout.samples_cards.is_dir()
    assert layout.metadata.is_dir()
    assert layout.exports.is_dir()


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
