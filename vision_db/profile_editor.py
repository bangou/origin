from dataclasses import replace
from pathlib import Path

from vision_db.profile_store import Box, VisionProfile, load_profile


class ProfileEditorState:
    def __init__(self, profile: VisionProfile) -> None:
        self._profile = profile
        self._image_path: Path | None = None
        self._image_size: tuple[int, int] | None = None

    @property
    def profile(self) -> VisionProfile:
        return self._profile

    def load_profile_path(self, path: Path) -> VisionProfile:
        self._profile = load_profile(path)
        return self._profile

    def load_image(self, path: Path, image_size: tuple[int, int]) -> tuple[int, int]:
        self._image_path = path
        self._image_size = image_size
        return image_size

    def upsert_box(self, role: str, box: Box) -> None:
        if role == "hero_hand_roi":
            self._profile = replace(self._profile, hero_hand_roi=box)
            return

        if role == "community_search_roi":
            self._profile = replace(self._profile, community_search_roi=box)
            return

        if role.startswith("hero_card_"):
            boxes = list(self._profile.hero_card_boxes)
            boxes[int(role.rsplit("_", 1)[1]) - 1] = box
            self._profile = replace(self._profile, hero_card_boxes=tuple(boxes))
            return

        if role.startswith("community_card_"):
            boxes = list(self._profile.community_card_boxes)
            boxes[int(role.rsplit("_", 1)[1]) - 1] = box
            self._profile = replace(self._profile, community_card_boxes=tuple(boxes))
            return

        button_rois = dict(self._profile.button_rois)
        button_rois[role] = box
        self._profile = replace(self._profile, button_rois=button_rois)

    def iter_named_boxes(self) -> list[tuple[str, Box]]:
        named_boxes: list[tuple[str, Box]] = [
            ("hero_hand_roi", self._profile.hero_hand_roi),
            ("community_search_roi", self._profile.community_search_roi),
        ]
        named_boxes.extend(
            (f"hero_card_{index}", box)
            for index, box in enumerate(self._profile.hero_card_boxes, start=1)
        )
        named_boxes.extend(
            (f"community_card_{index}", box)
            for index, box in enumerate(self._profile.community_card_boxes, start=1)
        )
        named_boxes.extend(sorted(self._profile.button_rois.items()))
        return named_boxes

    def to_profile(self) -> VisionProfile:
        return self._profile
