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
