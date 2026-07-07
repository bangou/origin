from dataclasses import dataclass

from PIL import Image

from vision_db.profile_store import Box, VisionProfile

_COMMUNITY_SLOTS = ("flop_1", "flop_2", "flop_3", "turn", "river")


@dataclass(frozen=True)
class ExtractedCrop:
    card_slot: str
    bbox: Box
    image: Image.Image


def _crop_box(image: Image.Image, card_slot: str, box: Box) -> ExtractedCrop:
    x, y, width, height = box
    return ExtractedCrop(
        card_slot=card_slot,
        bbox=box,
        image=image.crop((x, y, x + width, y + height)),
    )


def extract_hero_crops(image: Image.Image, profile: VisionProfile) -> list[ExtractedCrop]:
    return [
        _crop_box(image, f"hand_{index}", box)
        for index, box in enumerate(profile.hero_card_boxes, start=1)
    ]


def _is_bright(pixel: tuple[int, int, int]) -> bool:
    red, green, blue = pixel
    return red >= 220 and green >= 220 and blue >= 220


def _find_candidate_boxes(image: Image.Image, roi: Box) -> list[Box]:
    x, y, width, height = roi
    roi_image = image.crop((x, y, x + width, y + height)).convert("RGB")
    pixels = roi_image.load()
    bright_threshold = max(40, height // 2)
    groups: list[list[tuple[int, int, int]]] = []
    current: list[tuple[int, int, int]] = []

    for px in range(roi_image.width):
        bright_rows = [
            py for py in range(roi_image.height) if _is_bright(pixels[px, py])
        ]
        if len(bright_rows) >= bright_threshold:
            current.append((px, bright_rows[0], bright_rows[-1]))
            continue
        if current:
            groups.append(current)
            current = []

    if current:
        groups.append(current)

    boxes: list[Box] = []
    for group in groups:
        start_x = group[0][0]
        end_x = group[-1][0]
        top_y = min(item[1] for item in group)
        bottom_y = max(item[2] for item in group)
        boxes.append(
            (
                x + start_x,
                y + top_y,
                end_x - start_x + 1,
                bottom_y - top_y + 1,
            )
        )
    return boxes


def detect_community_cards(
    image: Image.Image, profile: VisionProfile
) -> list[ExtractedCrop]:
    detected_boxes = _find_candidate_boxes(image, profile.community_search_roi)
    if len(detected_boxes) != len(profile.community_card_boxes):
        detected_boxes = list(profile.community_card_boxes)

    return [
        _crop_box(image, card_slot, box)
        for card_slot, box in zip(_COMMUNITY_SLOTS, detected_boxes)
    ]
