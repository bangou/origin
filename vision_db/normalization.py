from dataclasses import dataclass

from PIL import Image


@dataclass(frozen=True)
class NormalizedCapture:
    image: Image.Image
    source_size: tuple[int, int]
    crop_box: tuple[int, int, int, int]
    logical_size: tuple[int, int]
    variant_name: str


def _normalized(
    image: Image.Image,
    crop_box: tuple[int, int, int, int],
    variant_name: str,
) -> NormalizedCapture:
    return NormalizedCapture(
        image=image.crop(crop_box),
        source_size=image.size,
        crop_box=crop_box,
        logical_size=(1920, 1032),
        variant_name=variant_name,
    )


def normalize_capture(image: Image.Image) -> NormalizedCapture:
    if image.size == (1920, 1032):
        return NormalizedCapture(
            image=image.copy(),
            source_size=image.size,
            crop_box=(0, 0, 1920, 1032),
            logical_size=(1920, 1032),
            variant_name="work_area_1920x1032",
        )

    if image.size == (1920, 1080):
        return _normalized(
            image=image,
            crop_box=(0, 0, 1920, 1032),
            variant_name="fullscreen_1920x1080",
        )

    if image.size == (1936, 1048):
        return _normalized(
            image=image,
            crop_box=(8, 8, 1928, 1040),
            variant_name="framed_window_1936x1048",
        )

    raise ValueError(f"Unsupported capture size: {image.size}")
