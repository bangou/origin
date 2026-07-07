from statistics import mean

from PIL import Image

from vision_db.profile_store import Box


def _roi_pixels(image: Image.Image, box: Box) -> list[tuple[int, int, int]]:
    x, y, width, height = box
    crop = image.crop((x, y, x + width, y + height)).convert("RGB")
    pixels = crop.load()
    return [
        pixels[cx, cy]
        for cy in range(crop.height)
        for cx in range(crop.width)
    ]


def _brightness(pixel: tuple[int, int, int]) -> float:
    red, green, blue = pixel
    return (red + green + blue) / 3.0


def compute_action_hints(
    image: Image.Image,
    button_rois: dict[str, Box],
) -> dict[str, float | bool]:
    result: dict[str, float | bool] = {}
    glowing_flags: list[bool] = []

    for key, box in button_rois.items():
        pixels = _roi_pixels(image, box)
        mean_brightness = mean(_brightness(pixel) for pixel in pixels)
        bright_ratio = sum(1 for pixel in pixels if _brightness(pixel) >= 120) / max(
            len(pixels), 1
        )
        glowing = mean_brightness >= 90 and bright_ratio >= 0.35
        prefix = key.removesuffix("_button_roi")
        result[f"{prefix}_glowing"] = glowing
        result[f"{prefix}_mean_brightness"] = round(mean_brightness, 2)
        result[f"{prefix}_bright_ratio"] = round(bright_ratio, 4)
        glowing_flags.append(glowing)

    result["can_act_hint"] = any(glowing_flags)
    return result
