from pathlib import Path

from PIL import Image, ImageDraw

from vision_db.crop_extractor import detect_community_cards, extract_hero_crops
from vision_db.normalization import normalize_capture
from vision_db.profile_store import make_seed_profile


def test_normalize_capture_and_extract_known_card_boxes(tmp_path: Path) -> None:
    source_path = tmp_path / "windowed.png"
    image = Image.new("RGB", (1936, 1048), "#008b74")
    draw = ImageDraw.Draw(image)

    for box in [
        (916, 880, 965, 952),
        (975, 880, 1020, 952),
        (837, 484, 886, 556),
        (890, 484, 939, 556),
        (944, 484, 993, 556),
        (997, 484, 1046, 556),
        (1050, 484, 1099, 556),
    ]:
        draw.rectangle(box, fill="white")

    image.save(source_path)

    normalized = normalize_capture(Image.open(source_path))
    profile = make_seed_profile()
    hero = extract_hero_crops(normalized.image, profile)
    community = detect_community_cards(normalized.image, profile)

    assert normalized.image.size == (1920, 1032)
    assert normalized.variant_name == "framed_window_1936x1048"
    assert [crop.card_slot for crop in hero] == ["hand_1", "hand_2"]
    assert [crop.bbox for crop in community] == [
        (829, 476, 50, 73),
        (882, 476, 50, 73),
        (936, 476, 50, 73),
        (989, 476, 50, 73),
        (1042, 476, 50, 73),
    ]


def test_normalize_capture_supports_fullscreen_and_work_area_variants() -> None:
    fullscreen = Image.new("RGB", (1920, 1080), "#008b74")
    fullscreen.putpixel((10, 1079), (255, 0, 0))
    work_area = Image.new("RGB", (1920, 1032), "#124f44")

    normalized_fullscreen = normalize_capture(fullscreen)
    normalized_work_area = normalize_capture(work_area)

    assert normalized_fullscreen.image.size == (1920, 1032)
    assert normalized_fullscreen.variant_name == "fullscreen_1920x1080"
    assert normalized_fullscreen.image.getpixel((10, 1031)) == (0, 139, 116)
    assert normalized_work_area.image.size == (1920, 1032)
    assert normalized_work_area.variant_name == "work_area_1920x1032"
