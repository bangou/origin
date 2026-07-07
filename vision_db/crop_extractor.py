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

    fragments: list[Box] = []
    for group in groups:
        start_x = group[0][0]
        end_x = group[-1][0]
        top_y = min(item[1] for item in group)
        bottom_y = max(item[2] for item in group)
        fragments.append(
            (
                x + start_x,
                y + top_y,
                end_x - start_x + 1,
                bottom_y - top_y + 1,
            )
        )

    merged: list[Box] = []
    current: list[Box] = []
    for fragment in fragments:
        if not current:
            current = [fragment]
            continue
        start_x = current[0][0]
        end_x = fragment[0] + fragment[2] - 1
        if end_x - start_x + 1 <= 55:
            current.append(fragment)
            continue

        merged.append(_merge_boxes(current))
        current = [fragment]

    if current:
        merged.append(_merge_boxes(current))

    return [box for box in merged if 35 <= box[2] <= 55 and box[3] >= 60]


def _merge_boxes(boxes: list[Box]) -> Box:
    left = min(box[0] for box in boxes)
    top = min(box[1] for box in boxes)
    right = max(box[0] + box[2] - 1 for box in boxes)
    bottom = max(box[1] + box[3] - 1 for box in boxes)
    return left, top, right - left + 1, bottom - top + 1


def detect_community_cards(
    image: Image.Image, profile: VisionProfile
) -> list[ExtractedCrop]:
    detected_boxes = _find_candidate_boxes(image, profile.community_search_roi)
    if len(detected_boxes) not in {0, 3, 4, 5}:
        detected_boxes = []

    return [
        _crop_box(image, card_slot, box)
        for card_slot, box in zip(_COMMUNITY_SLOTS, detected_boxes)
    ]
