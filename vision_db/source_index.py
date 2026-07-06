from pathlib import Path
from typing import Literal, NotRequired, TypedDict

from PIL import Image


class SourceImageRecord(TypedDict):
    file_name: str
    source_path: str
    kind: Literal["template_seed", "full_screenshot"]
    width: int
    height: int
    file_size: int
    error: NotRequired[str]


def parse_template_label(path: Path) -> tuple[str, str, str]:
    label = path.stem.removesuffix("_raw")
    return label, label[0], label[1]


def scan_source_images(source_dir: Path) -> list[SourceImageRecord]:
    records: list[SourceImageRecord] = []

    for path in sorted(source_dir.iterdir()):
        if not path.is_file():
            continue

        kind: Literal["template_seed", "full_screenshot"]
        kind = "template_seed" if path.name.endswith("_raw.png") else "full_screenshot"
        file_size = path.stat().st_size

        try:
            with Image.open(path) as image:
                width, height = image.size
        except OSError as exc:
            records.append(
                {
                    "file_name": path.name,
                    "source_path": str(path),
                    "kind": kind,
                    "width": 0,
                    "height": 0,
                    "file_size": file_size,
                    "error": str(exc),
                }
            )
            continue

        records.append(
            {
                "file_name": path.name,
                "source_path": str(path),
                "kind": kind,
                "width": width,
                "height": height,
                "file_size": file_size,
            }
        )

    return records
