from pathlib import Path
from typing import TypedDict

from PIL import Image


class CompressionResult(TypedDict):
    source_size: int
    destination_size: int
    width: int
    height: int


def compress_image_copy(source_path: Path, destination_path: Path) -> CompressionResult:
    destination_path.parent.mkdir(parents=True, exist_ok=True)

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
