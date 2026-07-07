import json
from dataclasses import dataclass, field
from pathlib import Path

Box = tuple[int, int, int, int]


def _to_box(values: list[int] | tuple[int, int, int, int]) -> Box:
    x, y, width, height = values
    return int(x), int(y), int(width), int(height)


@dataclass(frozen=True)
class VisionProfile:
    profile_name: str
    window_title_hints: tuple[str, ...]
    reference_width: int
    reference_height: int
    bbox_tolerance_px: int
    hero_hand_roi: Box
    hero_card_boxes: tuple[Box, ...]
    community_search_roi: Box
    community_card_boxes: tuple[Box, ...]
    button_rois: dict[str, Box] = field(default_factory=dict)


def make_seed_profile() -> VisionProfile:
    return VisionProfile(
        profile_name="wepoker_fullscreen_1920x1080_seed",
        window_title_hints=("WePoker", "WePoker-H5"),
        reference_width=1920,
        reference_height=1080,
        bbox_tolerance_px=5,
        hero_hand_roi=(897, 862, 125, 94),
        hero_card_boxes=((908, 872, 50, 73), (963, 872, 50, 73)),
        community_search_roi=(805, 457, 318, 109),
        community_card_boxes=(
            (829, 476, 50, 73),
            (882, 476, 50, 73),
            (936, 476, 49, 73),
            (989, 476, 49, 73),
            (1042, 476, 50, 73),
        ),
        button_rois={},
    )


def load_profile(path: Path) -> VisionProfile:
    data = json.loads(path.read_text(encoding="utf-8"))
    return VisionProfile(
        profile_name=data["profile_name"],
        window_title_hints=tuple(data["window_title_hints"]),
        reference_width=int(data["reference_width"]),
        reference_height=int(data["reference_height"]),
        bbox_tolerance_px=int(data["bbox_tolerance_px"]),
        hero_hand_roi=_to_box(data["hero_hand_roi"]),
        hero_card_boxes=tuple(_to_box(box) for box in data["hero_card_boxes"]),
        community_search_roi=_to_box(data["community_search_roi"]),
        community_card_boxes=tuple(
            _to_box(box) for box in data["community_card_boxes"]
        ),
        button_rois={
            name: _to_box(box) for name, box in data.get("button_rois", {}).items()
        },
    )


def save_profile(path: Path, profile: VisionProfile) -> None:
    payload = {
        "profile_name": profile.profile_name,
        "window_title_hints": list(profile.window_title_hints),
        "reference_width": profile.reference_width,
        "reference_height": profile.reference_height,
        "bbox_tolerance_px": profile.bbox_tolerance_px,
        "hero_hand_roi": list(profile.hero_hand_roi),
        "hero_card_boxes": [list(box) for box in profile.hero_card_boxes],
        "community_search_roi": list(profile.community_search_roi),
        "community_card_boxes": [list(box) for box in profile.community_card_boxes],
        "button_rois": {
            name: list(box) for name, box in sorted(profile.button_rois.items())
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
