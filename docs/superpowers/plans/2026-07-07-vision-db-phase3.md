# Vision DB Phase 3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the phase 3 fixed-layout screenshot workflow that confirms card/button coordinates, normalizes known WePoker capture variants, extracts hero/community card crops from real screenshots, proposes one candidate label per crop, writes review batches, and only ingests human-approved samples into the formal vision database.

**Architecture:** Keep phase 3 separate from the existing phase 2 database builder by adding focused modules for profile storage, normalization, crop extraction, template matching, review-batch generation, ingestion, and action-button experiments. Use the existing `data/vision_db/` layout and template library as the base asset store, but route all new automatic outputs through a review-batch layer before they touch `samples/cards/` or `samples_cards.jsonl`.

**Tech Stack:** Python 3.11+, Pillow, pytest, standard library (`tkinter`, `json`, `pathlib`, `dataclasses`, `hashlib`, `datetime`, `io`, `statistics`)

## Global Constraints

- Phase 3 only targets the current fixed WePoker layout family.
- Phase 3 prioritizes database quality and repeatability over layout generality.
- The sample source must be real screenshots, not rendered or synthesized cards.
- The first automatic label proposal should come from the existing real `*_raw.png` / `templates/cards/` library.
- Each crop should receive one primary candidate label for review, not an open-ended list.
- Automatic results must go into a review batch first, not directly into the formal sample library.
- Only human-approved samples may be added to `samples/cards/` and `samples_cards.jsonl`.
- Coordinate tolerance for manual calibration is `+/- 5` pixels.
- A lightweight coordinate confirmation tool is part of Phase 3 scope.
- Action-button glow detection is included only as an experimental auxiliary signal, not as a formal gate for sample ingestion.
- Phase 3 must not implement live capture or real-time monitoring loops.
- Phase 3 must not implement OCR for numbers such as pot, stack, or bet sizes.
- Phase 3 must not implement CNN training.
- Phase 3 must not implement a final production card recognizer logic.
- Phase 3 must not implement broad multi-layout generalization.
- Phase 3 must not implement automatic direct-to-database ingestion without review.
- Phase 3 must not implement synthetic rendered sample generation.
- Phase 3 must not implement a full GUI productization effort.

---

## File Structure

- Create: `D:/gtobig/config/vision_profiles/wepoker_fullscreen_1920x1080_seed.json` - confirmed seed profile from the user-provided screenshot.
- Create: `D:/gtobig/vision_db/profile_store.py` - profile dataclass, load/save helpers, seed profile builder.
- Create: `D:/gtobig/vision_db/profile_editor.py` - profile editor state and semantic box update logic.
- Create: `D:/gtobig/scripts/edit_vision_profile.py` - lightweight Tkinter coordinate confirmation tool.
- Create: `D:/gtobig/vision_db/normalization.py` - capture-variant detection and normalization to one logical table layout.
- Create: `D:/gtobig/vision_db/crop_extractor.py` - hero fixed-box crops and community ROI detection.
- Create: `D:/gtobig/vision_db/template_matcher.py` - template scoring and primary candidate-label selection.
- Create: `D:/gtobig/vision_db/review_batches.py` - review-batch assembly, crop saving, overlay saving, and queue output.
- Create: `D:/gtobig/vision_db/review_ingest.py` - approved-sample ingestion and duplicate prevention.
- Create: `D:/gtobig/vision_db/action_hints.py` - experimental button glow signal extraction.
- Create: `D:/gtobig/scripts/build_review_batch.py` - CLI for review-batch generation.
- Create: `D:/gtobig/scripts/ingest_review_batch.py` - CLI for approved-sample ingestion.
- Modify: `D:/gtobig/vision_db/__init__.py` - export phase 3 public helpers.
- Create: `D:/gtobig/tests/test_vision_db_profile_store.py` - seed profile and editor state tests.
- Create: `D:/gtobig/tests/test_vision_db_normalization.py` - capture normalization and crop extraction tests.
- Create: `D:/gtobig/tests/test_vision_db_review_batches.py` - template matching and review-batch generation tests.
- Create: `D:/gtobig/tests/test_vision_db_review_ingest.py` - approved-sample ingestion and duplicate-prevention tests.
- Create: `D:/gtobig/tests/test_vision_db_action_hints.py` - button glow signal tests.
- Create: `D:/gtobig/tests/test_build_review_batch_cli.py` - review-batch CLI smoke test.

### Task 1: Add Profile Storage And The Coordinate Confirmation Tool

**Files:**
- Create: `D:/gtobig/config/vision_profiles/wepoker_fullscreen_1920x1080_seed.json`
- Create: `D:/gtobig/vision_db/profile_store.py`
- Create: `D:/gtobig/vision_db/profile_editor.py`
- Create: `D:/gtobig/scripts/edit_vision_profile.py`
- Test: `D:/gtobig/tests/test_vision_db_profile_store.py`

**Interfaces:**
- Consumes:
  - existing repository structure only
- Produces:
  - `make_seed_profile() -> VisionProfile`
  - `load_profile(path: Path) -> VisionProfile`
  - `save_profile(path: Path, profile: VisionProfile) -> None`
  - `ProfileEditorState.upsert_box(role: str, box: tuple[int, int, int, int]) -> None`
  - `main(argv: Sequence[str] | None = None) -> int`

- [ ] **Step 1: Write the failing test**

```python
from pathlib import Path

from vision_db.profile_editor import ProfileEditorState
from vision_db.profile_store import load_profile, make_seed_profile, save_profile


def test_seed_profile_round_trips_and_editor_updates_boxes(tmp_path: Path) -> None:
    profile_path = tmp_path / "seed.json"

    seed = make_seed_profile()
    save_profile(profile_path, seed)
    loaded = load_profile(profile_path)

    editor = ProfileEditorState(profile=loaded)
    editor.upsert_box("hero_card_1", (910, 874, 50, 73))
    editor.upsert_box("bet_button_roi", (922, 783, 80, 80))
    updated = editor.to_profile()

    assert loaded.reference_width == 1920
    assert loaded.reference_height == 1080
    assert loaded.community_search_roi == (805, 457, 318, 109)
    assert updated.hero_card_boxes[0] == (910, 874, 50, 73)
    assert updated.button_rois["bet_button_roi"] == (922, 783, 80, 80)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `D:\gtobig\.venv\Scripts\python.exe -m pytest D:\gtobig\tests\test_vision_db_profile_store.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'vision_db.profile_store'`

- [ ] **Step 3: Write minimal implementation**

`D:/gtobig/config/vision_profiles/wepoker_fullscreen_1920x1080_seed.json`

```json
{
  "profile_name": "wepoker_fullscreen_1920x1080_seed",
  "window_title_hints": ["WePoker", "WePoker-H5"],
  "reference_width": 1920,
  "reference_height": 1080,
  "bbox_tolerance_px": 5,
  "hero_hand_roi": [897, 862, 125, 94],
  "hero_card_boxes": [
    [908, 872, 50, 73],
    [967, 872, 46, 73]
  ],
  "community_search_roi": [805, 457, 318, 109],
  "community_card_boxes": [
    [829, 476, 50, 73],
    [882, 476, 50, 73],
    [936, 476, 49, 73],
    [989, 476, 49, 73],
    [1042, 476, 50, 73]
  ],
  "button_rois": {}
}
```

`D:/gtobig/vision_db/profile_store.py`

```python
import json
from dataclasses import dataclass, field
from pathlib import Path

Box = tuple[int, int, int, int]


def _to_box(values: list[int] | tuple[int, int, int, int]) -> Box:
    x, y, w, h = values
    return int(x), int(y), int(w), int(h)


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
        hero_card_boxes=((908, 872, 50, 73), (967, 872, 46, 73)),
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
        hero_card_boxes=tuple(_to_box(item) for item in data["hero_card_boxes"]),
        community_search_roi=_to_box(data["community_search_roi"]),
        community_card_boxes=tuple(
            _to_box(item) for item in data["community_card_boxes"]
        ),
        button_rois={
            key: _to_box(value) for key, value in data.get("button_rois", {}).items()
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
            key: list(box) for key, box in sorted(profile.button_rois.items())
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
```

`D:/gtobig/vision_db/profile_editor.py`

```python
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

    def to_profile(self) -> VisionProfile:
        return self._profile
```

`D:/gtobig/scripts/edit_vision_profile.py`

```python
import argparse
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk
from typing import Sequence

from PIL import Image, ImageTk

from vision_db.profile_editor import ProfileEditorState
from vision_db.profile_store import load_profile, save_profile


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Edit WePoker vision profile boxes.")
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--image", type=Path, required=True)
    args = parser.parse_args(argv)

    state = ProfileEditorState(load_profile(args.profile))
    image = Image.open(args.image)
    state.load_image(args.image, image.size)

    root = tk.Tk()
    root.title("Vision Profile Editor")

    active_role = tk.StringVar(value="hero_hand_roi")
    status = tk.StringVar(value="Drag to draw a box.")
    photo = ImageTk.PhotoImage(image)
    canvas = tk.Canvas(root, width=image.width, height=image.height)
    canvas.pack(fill="both", expand=True)
    canvas.create_image(0, 0, anchor="nw", image=photo)

    toolbar = ttk.Frame(root)
    toolbar.pack(fill="x")

    roles = [
        "hero_hand_roi",
        "hero_card_1",
        "hero_card_2",
        "community_search_roi",
        "community_card_1",
        "community_card_2",
        "community_card_3",
        "community_card_4",
        "community_card_5",
        "fold_button_roi",
        "bet_button_roi",
        "check_button_roi",
    ]
    ttk.Combobox(toolbar, textvariable=active_role, values=roles, state="readonly").pack(
        side="left"
    )
    ttk.Label(toolbar, textvariable=status).pack(side="left", padx=12)

    start: tuple[int, int] | None = None
    current_rect: int | None = None

    def on_press(event: tk.Event) -> None:
        nonlocal start, current_rect
        start = (event.x, event.y)
        current_rect = canvas.create_rectangle(
            event.x,
            event.y,
            event.x,
            event.y,
            outline="#ff4b4b",
            width=2,
        )

    def on_drag(event: tk.Event) -> None:
        if start is None or current_rect is None:
            return
        canvas.coords(current_rect, start[0], start[1], event.x, event.y)
        x1, y1 = start
        x2, y2 = event.x, event.y
        status.set(f"{active_role.get()} -> x={min(x1,x2)} y={min(y1,y2)} w={abs(x2-x1)} h={abs(y2-y1)}")

    def on_release(event: tk.Event) -> None:
        nonlocal start, current_rect
        if start is None or current_rect is None:
            return
        x1, y1 = start
        x2, y2 = event.x, event.y
        box = (min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))
        state.upsert_box(active_role.get(), box)
        status.set(f"Saved {active_role.get()} = {box}")
        start = None
        current_rect = None

    def save_current() -> None:
        save_profile(args.profile, state.to_profile())
        status.set(f"Saved profile to {args.profile}")

    ttk.Button(toolbar, text="Save Profile", command=save_current).pack(side="right")
    canvas.bind("<ButtonPress-1>", on_press)
    canvas.bind("<B1-Motion>", on_drag)
    canvas.bind("<ButtonRelease-1>", on_release)

    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

`D:/gtobig/tests/test_vision_db_profile_store.py`

```python
from pathlib import Path

from vision_db.profile_editor import ProfileEditorState
from vision_db.profile_store import load_profile, make_seed_profile, save_profile


def test_seed_profile_round_trips_and_editor_updates_boxes(tmp_path: Path) -> None:
    profile_path = tmp_path / "seed.json"

    seed = make_seed_profile()
    save_profile(profile_path, seed)
    loaded = load_profile(profile_path)

    editor = ProfileEditorState(profile=loaded)
    editor.upsert_box("hero_card_1", (910, 874, 50, 73))
    editor.upsert_box("bet_button_roi", (922, 783, 80, 80))
    updated = editor.to_profile()

    assert loaded.reference_width == 1920
    assert loaded.reference_height == 1080
    assert loaded.community_search_roi == (805, 457, 318, 109)
    assert updated.hero_card_boxes[0] == (910, 874, 50, 73)
    assert updated.button_rois["bet_button_roi"] == (922, 783, 80, 80)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `D:\gtobig\.venv\Scripts\python.exe -m pytest D:\gtobig\tests\test_vision_db_profile_store.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git -C D:\gtobig add config/vision_profiles/wepoker_fullscreen_1920x1080_seed.json vision_db/profile_store.py vision_db/profile_editor.py scripts/edit_vision_profile.py tests/test_vision_db_profile_store.py
git -C D:\gtobig commit -m "feat: add vision profile editor and seed config"
```

### Task 2: Normalize Known Capture Variants And Extract Hero/Community Card Crops

**Files:**
- Create: `D:/gtobig/vision_db/normalization.py`
- Create: `D:/gtobig/vision_db/crop_extractor.py`
- Test: `D:/gtobig/tests/test_vision_db_normalization.py`

**Interfaces:**
- Consumes:
  - `load_profile(path: Path) -> VisionProfile`
- Produces:
  - `normalize_capture(image: Image.Image) -> NormalizedCapture`
  - `extract_hero_crops(image: Image.Image, profile: VisionProfile) -> list[ExtractedCrop]`
  - `detect_community_cards(image: Image.Image, profile: VisionProfile) -> list[ExtractedCrop]`

- [ ] **Step 1: Write the failing test**

```python
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
    assert [crop.card_slot for crop in hero] == ["hand_1", "hand_2"]
    assert [crop.bbox for crop in community] == [
        (829, 476, 50, 73),
        (882, 476, 50, 73),
        (936, 476, 50, 73),
        (989, 476, 50, 73),
        (1042, 476, 50, 73),
    ]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `D:\gtobig\.venv\Scripts\python.exe -m pytest D:\gtobig\tests\test_vision_db_normalization.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'vision_db.normalization'`

- [ ] **Step 3: Write minimal implementation**

`D:/gtobig/vision_db/normalization.py`

```python
from dataclasses import dataclass

from PIL import Image


@dataclass(frozen=True)
class NormalizedCapture:
    image: Image.Image
    source_size: tuple[int, int]
    crop_box: tuple[int, int, int, int]
    logical_size: tuple[int, int]
    variant_name: str


def normalize_capture(image: Image.Image) -> NormalizedCapture:
    width, height = image.size

    if (width, height) == (1920, 1032):
        return NormalizedCapture(
            image=image.copy(),
            source_size=(width, height),
            crop_box=(0, 0, 1920, 1032),
            logical_size=(1920, 1032),
            variant_name="work_area_1920x1032",
        )

    if (width, height) == (1920, 1080):
        cropped = image.crop((0, 0, 1920, 1032))
        return NormalizedCapture(
            image=cropped,
            source_size=(width, height),
            crop_box=(0, 0, 1920, 1032),
            logical_size=(1920, 1032),
            variant_name="fullscreen_1920x1080",
        )

    if (width, height) == (1936, 1048):
        cropped = image.crop((8, 8, 1928, 1040))
        return NormalizedCapture(
            image=cropped,
            source_size=(width, height),
            crop_box=(8, 8, 1928, 1040),
            logical_size=(1920, 1032),
            variant_name="framed_window_1936x1048",
        )

    raise ValueError(f"Unsupported capture size: {(width, height)}")
```

`D:/gtobig/vision_db/crop_extractor.py`

```python
from dataclasses import dataclass
from typing import Iterable

from PIL import Image

from vision_db.profile_store import Box, VisionProfile


@dataclass(frozen=True)
class ExtractedCrop:
    card_slot: str
    bbox: Box
    image: Image.Image


def _crop_box(image: Image.Image, slot: str, box: Box) -> ExtractedCrop:
    x, y, w, h = box
    return ExtractedCrop(card_slot=slot, bbox=box, image=image.crop((x, y, x + w, y + h)))


def extract_hero_crops(image: Image.Image, profile: VisionProfile) -> list[ExtractedCrop]:
    return [
        _crop_box(image, f"hand_{index}", box)
        for index, box in enumerate(profile.hero_card_boxes, start=1)
    ]


def _find_white_runs(image: Image.Image, roi: Box) -> list[Box]:
    x, y, w, h = roi
    roi_image = image.crop((x, y, x + w, y + h)).convert("RGB")
    pixels = roi_image.load()
    found: list[Box] = []

    current: list[tuple[int, int]] = []
    for px in range(roi_image.width):
        bright_count = sum(
            1
            for py in range(roi_image.height)
            if pixels[px, py][0] > 220 and pixels[px, py][1] > 220 and pixels[px, py][2] > 220
        )
        if bright_count >= 40:
            column_top = next(
                py
                for py in range(roi_image.height)
                if pixels[px, py][0] > 220 and pixels[px, py][1] > 220 and pixels[px, py][2] > 220
            )
            current.append((px, column_top))
            continue

        if current:
            start_x = current[0][0]
            end_x = current[-1][0]
            top_y = min(item[1] for item in current)
            found.append((x + start_x, y + top_y, end_x - start_x + 1, 73))
            current = []

    if current:
        start_x = current[0][0]
        end_x = current[-1][0]
        top_y = min(item[1] for item in current)
        found.append((x + start_x, y + top_y, end_x - start_x + 1, 73))

    return found


def detect_community_cards(image: Image.Image, profile: VisionProfile) -> list[ExtractedCrop]:
    detected = _find_white_runs(image, profile.community_search_roi)
    if len(detected) != 5:
        detected = list(profile.community_card_boxes)

    return [
        _crop_box(image, slot, box)
        for slot, box in zip(
            ("flop_1", "flop_2", "flop_3", "turn", "river"),
            detected,
        )
    ]
```

`D:/gtobig/tests/test_vision_db_normalization.py`

```python
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
    assert [crop.card_slot for crop in hero] == ["hand_1", "hand_2"]
    assert [crop.bbox for crop in community] == [
        (829, 476, 50, 73),
        (882, 476, 50, 73),
        (936, 476, 50, 73),
        (989, 476, 50, 73),
        (1042, 476, 50, 73),
    ]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `D:\gtobig\.venv\Scripts\python.exe -m pytest D:\gtobig\tests\test_vision_db_normalization.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git -C D:\gtobig add vision_db/normalization.py vision_db/crop_extractor.py tests/test_vision_db_normalization.py
git -C D:\gtobig commit -m "feat: add capture normalization and crop extraction"
```

### Task 3: Add Template Matching And Review-Batch Generation

**Files:**
- Create: `D:/gtobig/vision_db/template_matcher.py`
- Create: `D:/gtobig/vision_db/review_batches.py`
- Create: `D:/gtobig/scripts/build_review_batch.py`
- Test: `D:/gtobig/tests/test_vision_db_review_batches.py`
- Test: `D:/gtobig/tests/test_build_review_batch_cli.py`

**Interfaces:**
- Consumes:
  - `normalize_capture(image: Image.Image) -> NormalizedCapture`
  - `extract_hero_crops(image: Image.Image, profile: VisionProfile) -> list[ExtractedCrop]`
  - `detect_community_cards(image: Image.Image, profile: VisionProfile) -> list[ExtractedCrop]`
- Produces:
  - `score_template_matches(crop: Image.Image, template_dir: Path) -> list[TemplateMatch]`
  - `choose_primary_label(card_slot: str, matches: list[TemplateMatch], used_labels: set[str], threshold: float) -> CandidateLabel`
  - `build_review_batch(db_root: Path, profile_path: Path, batch_root: Path, template_threshold: float = 0.65, limit: int | None = None) -> ReviewBatchSummary`
  - `main(argv: Sequence[str] | None = None) -> int`

- [ ] **Step 1: Write the failing test**

```python
import json
from pathlib import Path

from PIL import Image, ImageDraw

from vision_db.jsonl_store import append_jsonl
from vision_db.layout import ensure_layout
from vision_db.profile_store import make_seed_profile, save_profile
from vision_db.review_batches import build_review_batch


def test_build_review_batch_writes_queue_crops_and_overlay(tmp_path: Path) -> None:
    db_root = tmp_path / "data" / "vision_db"
    batch_root = tmp_path / "review_batches"
    profile_path = tmp_path / "profile.json"
    layout = ensure_layout(db_root)
    save_profile(profile_path, make_seed_profile())

    for label, box in {
        "Qc": (908, 872, 50, 73),
        "3c": (967, 872, 46, 73),
        "9d": (829, 476, 50, 73),
        "3s": (882, 476, 50, 73),
        "6s": (936, 476, 49, 73),
        "Tc": (989, 476, 49, 73),
        "4c": (1042, 476, 50, 73),
    }.items():
        template = Image.new("RGB", (box[2], box[3]), "white")
        ImageDraw.Draw(template).text((8, 8), label, fill="black")
        template.save(layout.templates_cards / f"{label}.png")

    source_image = Image.new("RGB", (1920, 1032), "#008b74")
    draw = ImageDraw.Draw(source_image)
    label_to_box = {
        "Qc": (908, 872, 50, 73),
        "3c": (967, 872, 46, 73),
        "9d": (829, 476, 50, 73),
        "3s": (882, 476, 50, 73),
        "6s": (936, 476, 49, 73),
        "Tc": (989, 476, 49, 73),
        "4c": (1042, 476, 50, 73),
    }
    for label, (x, y, w, h) in label_to_box.items():
        draw.rectangle((x, y, x + w, y + h), fill="white")
        draw.text((x + 8, y + 8), label, fill="black")

    raw_path = layout.raw_full / "seed.png"
    source_image.save(raw_path)
    append_jsonl(
        layout.metadata / "images.jsonl",
        {
            "image_id": "seed-image",
            "source_path": str(raw_path),
            "raw_copy_path": str(raw_path),
            "compressed_path": "",
            "width": 1920,
            "height": 1032,
            "file_size": raw_path.stat().st_size,
            "is_over_1mb": False,
            "theme": "default",
            "status": "indexed",
        },
    )

    summary = build_review_batch(db_root, profile_path, batch_root, template_threshold=0.65)
    queue_path = batch_root / summary["batch_id"] / "review_queue.jsonl"

    rows = [
        json.loads(line)
        for line in queue_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    assert summary["review_item_count"] == 7
    assert rows[0]["review_status"] == "pending"
    assert rows[0]["candidate_score"] >= 0.65
    assert Path(rows[0]["crop_path"]).exists()
    assert Path(rows[0]["overlay_path"]).exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `D:\gtobig\.venv\Scripts\python.exe -m pytest D:\gtobig\tests\test_vision_db_review_batches.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'vision_db.review_batches'`

- [ ] **Step 3: Write minimal implementation**

`D:/gtobig/vision_db/template_matcher.py`

```python
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageChops, ImageOps


@dataclass(frozen=True)
class TemplateMatch:
    label: str
    score: float


@dataclass(frozen=True)
class CandidateLabel:
    label: str
    score: float
    match_source: str
    review_status: str


def _normalized_gray(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    return ImageOps.grayscale(image).resize(size)


def score_template_matches(crop: Image.Image, template_dir: Path) -> list[TemplateMatch]:
    matches: list[TemplateMatch] = []
    for path in sorted(template_dir.glob("*.png")):
        template = Image.open(path)
        left = _normalized_gray(crop, template.size)
        right = _normalized_gray(template, template.size)
        diff = ImageChops.difference(left, right)
        mean_diff = sum(diff.getdata()) / (template.size[0] * template.size[1] * 255)
        matches.append(TemplateMatch(label=path.stem, score=1.0 - mean_diff))

    return sorted(matches, key=lambda item: item.score, reverse=True)


def choose_primary_label(
    card_slot: str,
    matches: list[TemplateMatch],
    used_labels: set[str],
    threshold: float,
) -> CandidateLabel:
    if not matches:
        return CandidateLabel(
            label="UNKNOWN",
            score=0.0,
            match_source="templates/cards",
            review_status="needs_review",
        )

    top = matches[0]
    if top.label in used_labels or top.score < threshold:
        return CandidateLabel(
            label=top.label,
            score=top.score,
            match_source="templates/cards",
            review_status="needs_review",
        )

    return CandidateLabel(
        label=top.label,
        score=top.score,
        match_source="templates/cards",
        review_status="pending",
    )
```

`D:/gtobig/vision_db/review_batches.py`

```python
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from vision_db.crop_extractor import detect_community_cards, extract_hero_crops
from vision_db.jsonl_store import append_jsonl
from vision_db.normalization import normalize_capture
from vision_db.profile_store import Box, load_profile
from vision_db.template_matcher import choose_primary_label, score_template_matches


@dataclass(frozen=True)
class ReviewBatchSummary:
    batch_id: str
    review_item_count: int
    needs_review_count: int

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _save_overlay(image: Image.Image, boxes: list[Box], path: Path) -> None:
    overlay = image.copy()
    draw = ImageDraw.Draw(overlay)
    for box in boxes:
        x, y, w, h = box
        draw.rectangle((x, y, x + w, y + h), outline="#ff4b4b", width=2)
    overlay.save(path)


def build_review_batch(
    db_root: Path,
    profile_path: Path,
    batch_root: Path,
    template_threshold: float = 0.65,
    limit: int | None = None,
) -> ReviewBatchSummary:
    profile = load_profile(profile_path)
    images = _load_jsonl(db_root / "metadata" / "images.jsonl")
    if limit is not None:
        images = images[:limit]

    batch_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    current_root = batch_root / batch_id
    crops_dir = current_root / "crops"
    overlays_dir = current_root / "overlays"
    crops_dir.mkdir(parents=True, exist_ok=True)
    overlays_dir.mkdir(parents=True, exist_ok=True)

    review_item_count = 0
    needs_review_count = 0

    for image_row in images:
        source_path = Path(image_row["raw_copy_path"])
        normalized = normalize_capture(Image.open(source_path))
        crops = extract_hero_crops(normalized.image, profile) + detect_community_cards(
            normalized.image, profile
        )
        overlay_path = overlays_dir / f'{image_row["image_id"]}.png'
        _save_overlay(normalized.image, [crop.bbox for crop in crops], overlay_path)

        used_labels: set[str] = set()
        for index, crop in enumerate(crops, start=1):
            matches = score_template_matches(crop.image, db_root / "templates" / "cards")
            candidate = choose_primary_label(
                crop.card_slot, matches, used_labels, template_threshold
            )
            used_labels.add(candidate.label)

            crop_path = crops_dir / f'{image_row["image_id"]}_{crop.card_slot}.png'
            crop.image.save(crop_path)
            append_jsonl(
                current_root / "review_queue.jsonl",
                {
                    "batch_id": batch_id,
                    "review_item_id": f'{image_row["image_id"]}-{index}',
                    "image_id": image_row["image_id"],
                    "source_profile": profile.profile_name,
                    "card_slot": crop.card_slot,
                    "candidate_label": candidate.label,
                    "candidate_score": round(candidate.score, 4),
                    "match_source": candidate.match_source,
                    "bbox": list(crop.bbox),
                    "crop_path": str(crop_path),
                    "overlay_path": str(overlay_path),
                    "review_status": candidate.review_status,
                },
            )
            review_item_count += 1
            if candidate.review_status != "pending":
                needs_review_count += 1

    (current_root / "summary.json").write_text(
        json.dumps(
            {
                "batch_id": batch_id,
                "review_item_count": review_item_count,
                "needs_review_count": needs_review_count,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return ReviewBatchSummary(
        batch_id=batch_id,
        review_item_count=review_item_count,
        needs_review_count=needs_review_count,
    )
```

`D:/gtobig/scripts/build_review_batch.py`

```python
import argparse
from pathlib import Path
from typing import Sequence

from vision_db.review_batches import build_review_batch


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a phase 3 review batch.")
    parser.add_argument("--db-root", type=Path, required=True)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--batch-root", type=Path, required=True)
    parser.add_argument("--template-threshold", type=float, default=0.65)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args(argv)

    summary = build_review_batch(
        db_root=args.db_root,
        profile_path=args.profile,
        batch_root=args.batch_root,
        template_threshold=args.template_threshold,
        limit=args.limit,
    )
    print(
        " ".join(
            [
                f'batch_id={summary["batch_id"]}',
                f'review_item_count={summary["review_item_count"]}',
                f'needs_review_count={summary["needs_review_count"]}',
            ]
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

`D:/gtobig/tests/test_vision_db_review_batches.py`

```python
import json
from pathlib import Path

from PIL import Image, ImageDraw

from vision_db.jsonl_store import append_jsonl
from vision_db.layout import ensure_layout
from vision_db.profile_store import make_seed_profile, save_profile
from vision_db.review_batches import build_review_batch


def test_build_review_batch_writes_queue_crops_and_overlay(tmp_path: Path) -> None:
    db_root = tmp_path / "data" / "vision_db"
    batch_root = tmp_path / "review_batches"
    profile_path = tmp_path / "profile.json"
    layout = ensure_layout(db_root)
    save_profile(profile_path, make_seed_profile())

    for label, box in {
        "Qc": (908, 872, 50, 73),
        "3c": (967, 872, 46, 73),
        "9d": (829, 476, 50, 73),
        "3s": (882, 476, 50, 73),
        "6s": (936, 476, 49, 73),
        "Tc": (989, 476, 49, 73),
        "4c": (1042, 476, 50, 73),
    }.items():
        template = Image.new("RGB", (box[2], box[3]), "white")
        ImageDraw.Draw(template).text((8, 8), label, fill="black")
        template.save(layout.templates_cards / f"{label}.png")

    source_image = Image.new("RGB", (1920, 1032), "#008b74")
    draw = ImageDraw.Draw(source_image)
    label_to_box = {
        "Qc": (908, 872, 50, 73),
        "3c": (967, 872, 46, 73),
        "9d": (829, 476, 50, 73),
        "3s": (882, 476, 50, 73),
        "6s": (936, 476, 49, 73),
        "Tc": (989, 476, 49, 73),
        "4c": (1042, 476, 50, 73),
    }
    for label, (x, y, w, h) in label_to_box.items():
        draw.rectangle((x, y, x + w, y + h), fill="white")
        draw.text((x + 8, y + 8), label, fill="black")

    raw_path = layout.raw_full / "seed.png"
    source_image.save(raw_path)
    append_jsonl(
        layout.metadata / "images.jsonl",
        {
            "image_id": "seed-image",
            "source_path": str(raw_path),
            "raw_copy_path": str(raw_path),
            "compressed_path": "",
            "width": 1920,
            "height": 1032,
            "file_size": raw_path.stat().st_size,
            "is_over_1mb": False,
            "theme": "default",
            "status": "indexed",
        },
    )

    summary = build_review_batch(db_root, profile_path, batch_root, template_threshold=0.65)
    queue_path = batch_root / summary["batch_id"] / "review_queue.jsonl"

    rows = [
        json.loads(line)
        for line in queue_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    assert summary["review_item_count"] == 7
    assert rows[0]["review_status"] == "pending"
    assert rows[0]["candidate_score"] >= 0.65
    assert Path(rows[0]["crop_path"]).exists()
    assert Path(rows[0]["overlay_path"]).exists()
```

`D:/gtobig/tests/test_build_review_batch_cli.py`

```python
from pathlib import Path

from PIL import Image, ImageDraw

from scripts.build_review_batch import main
from vision_db.jsonl_store import append_jsonl
from vision_db.layout import ensure_layout
from vision_db.profile_store import make_seed_profile, save_profile


def test_build_review_batch_cli_prints_summary(tmp_path: Path, capsys) -> None:
    db_root = tmp_path / "data" / "vision_db"
    batch_root = tmp_path / "review_batches"
    profile_path = tmp_path / "profile.json"
    layout = ensure_layout(db_root)
    save_profile(profile_path, make_seed_profile())

    template = Image.new("RGB", (50, 73), "white")
    ImageDraw.Draw(template).text((8, 8), "9d", fill="black")
    template.save(layout.templates_cards / "9d.png")

    image = Image.new("RGB", (1920, 1032), "#008b74")
    draw = ImageDraw.Draw(image)
    draw.rectangle((829, 476, 879, 549), fill="white")
    draw.text((837, 484), "9d", fill="black")
    raw_path = layout.raw_full / "seed.png"
    image.save(raw_path)

    append_jsonl(
        layout.metadata / "images.jsonl",
        {
            "image_id": "seed-image",
            "source_path": str(raw_path),
            "raw_copy_path": str(raw_path),
            "compressed_path": "",
            "width": 1920,
            "height": 1032,
            "file_size": raw_path.stat().st_size,
            "is_over_1mb": False,
            "theme": "default",
            "status": "indexed",
        },
    )

    exit_code = main(
        [
            "--db-root",
            str(db_root),
            "--profile",
            str(profile_path),
            "--batch-root",
            str(batch_root),
            "--limit",
            "1",
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "batch_id=" in output
    assert "review_item_count=" in output
```

- [ ] **Step 4: Run test to verify it passes**

Run: `D:\gtobig\.venv\Scripts\python.exe -m pytest D:\gtobig\tests\test_vision_db_review_batches.py D:\gtobig\tests\test_build_review_batch_cli.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git -C D:\gtobig add vision_db/template_matcher.py vision_db/review_batches.py scripts/build_review_batch.py tests/test_vision_db_review_batches.py tests/test_build_review_batch_cli.py
git -C D:\gtobig commit -m "feat: add review batch generation pipeline"
```

### Task 4: Ingest Reviewed Samples And Prevent Duplicates

**Files:**
- Create: `D:/gtobig/vision_db/review_ingest.py`
- Create: `D:/gtobig/scripts/ingest_review_batch.py`
- Test: `D:/gtobig/tests/test_vision_db_review_ingest.py`

**Interfaces:**
- Consumes:
  - `review_queue.jsonl` rows generated by `build_review_batch(...)`
- Produces:
  - `ingest_review_batch(batch_dir: Path, db_root: Path) -> IngestSummary`
  - `main(argv: Sequence[str] | None = None) -> int`

- [ ] **Step 1: Write the failing test**

```python
import json
from pathlib import Path

from PIL import Image

from vision_db.layout import ensure_layout
from vision_db.review_ingest import ingest_review_batch


def test_ingest_review_batch_only_writes_approved_and_corrected_samples(tmp_path: Path) -> None:
    db_root = tmp_path / "data" / "vision_db"
    batch_dir = tmp_path / "review_batches" / "batch-1"
    crops_dir = batch_dir / "crops"
    crops_dir.mkdir(parents=True)
    ensure_layout(db_root)

    approved_crop = crops_dir / "approved.png"
    corrected_crop = crops_dir / "corrected.png"
    rejected_crop = crops_dir / "rejected.png"
    Image.new("RGB", (50, 73), "white").save(approved_crop)
    Image.new("RGB", (50, 73), "white").save(corrected_crop)
    Image.new("RGB", (50, 73), "white").save(rejected_crop)

    queue_path = batch_dir / "review_queue.jsonl"
    rows = [
        {
            "batch_id": "batch-1",
            "review_item_id": "one",
            "image_id": "img-1",
            "source_profile": "seed",
            "card_slot": "flop_1",
            "candidate_label": "9d",
            "candidate_score": 0.91,
            "match_source": "templates/cards",
            "bbox": [829, 476, 50, 73],
            "crop_path": str(approved_crop),
            "overlay_path": "",
            "review_status": "approved",
        },
        {
            "batch_id": "batch-1",
            "review_item_id": "two",
            "image_id": "img-1",
            "source_profile": "seed",
            "card_slot": "hand_1",
            "candidate_label": "Qc",
            "candidate_score": 0.72,
            "match_source": "templates/cards",
            "bbox": [908, 872, 50, 73],
            "crop_path": str(corrected_crop),
            "overlay_path": "",
            "review_status": "corrected",
            "final_label": "Qc",
        },
        {
            "batch_id": "batch-1",
            "review_item_id": "three",
            "image_id": "img-1",
            "source_profile": "seed",
            "card_slot": "hand_2",
            "candidate_label": "3c",
            "candidate_score": 0.55,
            "match_source": "templates/cards",
            "bbox": [967, 872, 46, 73],
            "crop_path": str(rejected_crop),
            "overlay_path": "",
            "review_status": "rejected",
        },
    ]
    queue_path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )

    first = ingest_review_batch(batch_dir, db_root)
    second = ingest_review_batch(batch_dir, db_root)
    sample_rows = [
        json.loads(line)
        for line in (db_root / "metadata" / "samples_cards.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]

    assert first["ingested_count"] == 2
    assert first["duplicate_count"] == 0
    assert second["duplicate_count"] == 2
    assert len(sample_rows) == 2
    assert sorted(row["label"] for row in sample_rows) == ["9d", "Qc"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `D:\gtobig\.venv\Scripts\python.exe -m pytest D:\gtobig\tests\test_vision_db_review_ingest.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'vision_db.review_ingest'`

- [ ] **Step 3: Write minimal implementation**

`D:/gtobig/vision_db/review_ingest.py`

```python
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha1
from pathlib import Path
from shutil import copy2
from typing import Any

from vision_db.jsonl_store import append_jsonl


@dataclass(frozen=True)
class IngestSummary:
    ingested_count: int
    duplicate_count: int
    skipped_count: int

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _sample_id(crop_path: Path, label: str, card_slot: str) -> str:
    digest = sha1()
    digest.update(crop_path.read_bytes())
    digest.update(label.encode("utf-8"))
    digest.update(card_slot.encode("utf-8"))
    return digest.hexdigest()[:16]


def ingest_review_batch(batch_dir: Path, db_root: Path) -> IngestSummary:
    queue_rows = _load_jsonl(batch_dir / "review_queue.jsonl")
    metadata_path = db_root / "metadata" / "samples_cards.jsonl"
    existing_ids = {
        row["sample_id"] for row in _load_jsonl(metadata_path) if "sample_id" in row
    }

    ingested_count = 0
    duplicate_count = 0
    skipped_count = 0

    for row in queue_rows:
        if row["review_status"] not in {"approved", "corrected"}:
            skipped_count += 1
            continue

        final_label = row.get("final_label", row["candidate_label"])
        crop_path = Path(row["crop_path"])
        sample_id = _sample_id(crop_path, final_label, row["card_slot"])
        if sample_id in existing_ids:
            duplicate_count += 1
            continue

        target_dir = db_root / "samples" / "cards" / row["card_slot"] / final_label
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / f"{sample_id}{crop_path.suffix.lower()}"
        copy2(crop_path, target_path)
        with Image.open(crop_path) as crop_image:
            width, height = crop_image.size

        append_jsonl(
            metadata_path,
            {
                "sample_id": sample_id,
                "image_id": row["image_id"],
                "source_profile": row["source_profile"],
                "card_slot": row["card_slot"],
                "label": final_label,
                "sample_path": str(target_path),
                "bbox": row["bbox"],
                "width": width,
                "height": height,
                "quality_status": row["review_status"],
                "review_batch_id": row["batch_id"],
                "review_item_id": row["review_item_id"],
                "ingested_at": datetime.now(UTC).isoformat(),
            },
        )
        existing_ids.add(sample_id)
        ingested_count += 1

    return IngestSummary(
        ingested_count=ingested_count,
        duplicate_count=duplicate_count,
        skipped_count=skipped_count,
    )
```

`D:/gtobig/scripts/ingest_review_batch.py`

```python
import argparse
from pathlib import Path
from typing import Sequence

from vision_db.review_ingest import ingest_review_batch


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ingest approved review-batch samples.")
    parser.add_argument("--batch-dir", type=Path, required=True)
    parser.add_argument("--db-root", type=Path, required=True)
    args = parser.parse_args(argv)

    summary = ingest_review_batch(args.batch_dir, args.db_root)
    print(
        " ".join(
            [
                f'ingested_count={summary["ingested_count"]}',
                f'duplicate_count={summary["duplicate_count"]}',
                f'skipped_count={summary["skipped_count"]}',
            ]
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

`D:/gtobig/tests/test_vision_db_review_ingest.py`

```python
import json
from pathlib import Path

from PIL import Image

from vision_db.layout import ensure_layout
from vision_db.review_ingest import ingest_review_batch


def test_ingest_review_batch_only_writes_approved_and_corrected_samples(tmp_path: Path) -> None:
    db_root = tmp_path / "data" / "vision_db"
    batch_dir = tmp_path / "review_batches" / "batch-1"
    crops_dir = batch_dir / "crops"
    crops_dir.mkdir(parents=True)
    ensure_layout(db_root)

    approved_crop = crops_dir / "approved.png"
    corrected_crop = crops_dir / "corrected.png"
    rejected_crop = crops_dir / "rejected.png"
    Image.new("RGB", (50, 73), "white").save(approved_crop)
    Image.new("RGB", (50, 73), "white").save(corrected_crop)
    Image.new("RGB", (50, 73), "white").save(rejected_crop)

    queue_path = batch_dir / "review_queue.jsonl"
    rows = [
        {
            "batch_id": "batch-1",
            "review_item_id": "one",
            "image_id": "img-1",
            "source_profile": "seed",
            "card_slot": "flop_1",
            "candidate_label": "9d",
            "candidate_score": 0.91,
            "match_source": "templates/cards",
            "bbox": [829, 476, 50, 73],
            "crop_path": str(approved_crop),
            "overlay_path": "",
            "review_status": "approved",
        },
        {
            "batch_id": "batch-1",
            "review_item_id": "two",
            "image_id": "img-1",
            "source_profile": "seed",
            "card_slot": "hand_1",
            "candidate_label": "Qc",
            "candidate_score": 0.72,
            "match_source": "templates/cards",
            "bbox": [908, 872, 50, 73],
            "crop_path": str(corrected_crop),
            "overlay_path": "",
            "review_status": "corrected",
            "final_label": "Qc",
        },
        {
            "batch_id": "batch-1",
            "review_item_id": "three",
            "image_id": "img-1",
            "source_profile": "seed",
            "card_slot": "hand_2",
            "candidate_label": "3c",
            "candidate_score": 0.55,
            "match_source": "templates/cards",
            "bbox": [967, 872, 46, 73],
            "crop_path": str(rejected_crop),
            "overlay_path": "",
            "review_status": "rejected",
        },
    ]
    queue_path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )

    first = ingest_review_batch(batch_dir, db_root)
    second = ingest_review_batch(batch_dir, db_root)
    sample_rows = [
        json.loads(line)
        for line in (db_root / "metadata" / "samples_cards.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]

    assert first["ingested_count"] == 2
    assert first["duplicate_count"] == 0
    assert second["duplicate_count"] == 2
    assert len(sample_rows) == 2
    assert sorted(row["label"] for row in sample_rows) == ["9d", "Qc"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `D:\gtobig\.venv\Scripts\python.exe -m pytest D:\gtobig\tests\test_vision_db_review_ingest.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git -C D:\gtobig add vision_db/review_ingest.py scripts/ingest_review_batch.py tests/test_vision_db_review_ingest.py
git -C D:\gtobig commit -m "feat: ingest reviewed samples into formal library"
```

### Task 5: Add Action Button Glow Signals And Final Phase 3 Exports

**Files:**
- Create: `D:/gtobig/vision_db/action_hints.py`
- Modify: `D:/gtobig/vision_db/review_batches.py`
- Modify: `D:/gtobig/vision_db/__init__.py`
- Test: `D:/gtobig/tests/test_vision_db_action_hints.py`

**Interfaces:**
- Consumes:
  - `load_profile(path: Path) -> VisionProfile`
  - `build_review_batch(db_root: Path, profile_path: Path, batch_root: Path, template_threshold: float = 0.65, limit: int | None = None) -> ReviewBatchSummary`
- Produces:
  - `compute_action_hints(image: Image.Image, button_rois: dict[str, tuple[int, int, int, int]]) -> dict[str, float | bool]`
  - review-batch summaries and queue rows that may include optional action-hint metadata

- [ ] **Step 1: Write the failing test**

```python
from PIL import Image, ImageDraw

from vision_db.action_hints import compute_action_hints


def test_compute_action_hints_marks_glowing_buttons() -> None:
    image = Image.new("RGB", (300, 140), "#004f44")
    draw = ImageDraw.Draw(image)
    draw.ellipse((20, 20, 100, 100), fill="#f05d5d")
    draw.ellipse((110, 20, 190, 100), fill="#36a8ff")
    draw.ellipse((200, 20, 280, 100), fill="#1f7b2e")

    result = compute_action_hints(
        image,
        {
            "fold_button_roi": (20, 20, 80, 80),
            "bet_button_roi": (110, 20, 80, 80),
            "check_button_roi": (200, 20, 80, 80),
        },
    )

    assert result["fold_glowing"] is True
    assert result["bet_glowing"] is True
    assert result["check_glowing"] is False
    assert result["can_act_hint"] is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `D:\gtobig\.venv\Scripts\python.exe -m pytest D:\gtobig\tests\test_vision_db_action_hints.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'vision_db.action_hints'`

- [ ] **Step 3: Write minimal implementation**

`D:/gtobig/vision_db/action_hints.py`

```python
from statistics import mean

from PIL import Image

from vision_db.profile_store import Box


def _roi_pixels(image: Image.Image, box: Box) -> list[tuple[int, int, int]]:
    x, y, w, h = box
    crop = image.crop((x, y, x + w, y + h)).convert("RGB")
    return list(crop.getdata())


def _brightness(pixel: tuple[int, int, int]) -> float:
    r, g, b = pixel
    return (r + g + b) / 3.0


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
        result[f"{key.replace('_button_roi', '')}_glowing"] = glowing
        result[f"{key.replace('_button_roi', '')}_mean_brightness"] = round(
            mean_brightness, 2
        )
        result[f"{key.replace('_button_roi', '')}_bright_ratio"] = round(
            bright_ratio, 4
        )
        glowing_flags.append(glowing)

    result["can_act_hint"] = any(glowing_flags)
    return result
```

`D:/gtobig/vision_db/review_batches.py`

```python
from vision_db.action_hints import compute_action_hints
```

Replace the per-image loop body inside `build_review_batch(...)` with this updated section:

```python
        action_hints = compute_action_hints(normalized.image, profile.button_rois) if profile.button_rois else {}
        _save_overlay(normalized.image, [crop.bbox for crop in crops], overlay_path)

        used_labels: set[str] = set()
        for index, crop in enumerate(crops, start=1):
            matches = score_template_matches(crop.image, db_root / "templates" / "cards")
            candidate = choose_primary_label(
                crop.card_slot, matches, used_labels, template_threshold
            )
            used_labels.add(candidate.label)

            crop_path = crops_dir / f'{image_row["image_id"]}_{crop.card_slot}.png'
            crop.image.save(crop_path)
            append_jsonl(
                current_root / "review_queue.jsonl",
                {
                    "batch_id": batch_id,
                    "review_item_id": f'{image_row["image_id"]}-{index}',
                    "image_id": image_row["image_id"],
                    "source_profile": profile.profile_name,
                    "card_slot": crop.card_slot,
                    "candidate_label": candidate.label,
                    "candidate_score": round(candidate.score, 4),
                    "match_source": candidate.match_source,
                    "bbox": list(crop.bbox),
                    "crop_path": str(crop_path),
                    "overlay_path": str(overlay_path),
                    "review_status": candidate.review_status,
                    "action_hints": action_hints,
                },
            )
            review_item_count += 1
            if candidate.review_status != "pending":
                needs_review_count += 1
```

`D:/gtobig/vision_db/__init__.py`

```python
from vision_db.action_hints import compute_action_hints
from vision_db.layout import VisionDbLayout, ensure_layout
from vision_db.profile_store import VisionProfile, load_profile, make_seed_profile, save_profile
from vision_db.review_batches import build_review_batch
from vision_db.review_ingest import ingest_review_batch
from vision_db.source_index import parse_template_label, scan_source_images

__all__ = [
    "VisionDbLayout",
    "VisionProfile",
    "build_review_batch",
    "compute_action_hints",
    "ensure_layout",
    "ingest_review_batch",
    "load_profile",
    "make_seed_profile",
    "parse_template_label",
    "save_profile",
    "scan_source_images",
]
```

`D:/gtobig/tests/test_vision_db_action_hints.py`

```python
from PIL import Image, ImageDraw

from vision_db.action_hints import compute_action_hints


def test_compute_action_hints_marks_glowing_buttons() -> None:
    image = Image.new("RGB", (300, 140), "#004f44")
    draw = ImageDraw.Draw(image)
    draw.ellipse((20, 20, 100, 100), fill="#f05d5d")
    draw.ellipse((110, 20, 190, 100), fill="#36a8ff")
    draw.ellipse((200, 20, 280, 100), fill="#1f7b2e")

    result = compute_action_hints(
        image,
        {
            "fold_button_roi": (20, 20, 80, 80),
            "bet_button_roi": (110, 20, 80, 80),
            "check_button_roi": (200, 20, 80, 80),
        },
    )

    assert result["fold_glowing"] is True
    assert result["bet_glowing"] is True
    assert result["check_glowing"] is False
    assert result["can_act_hint"] is True
```

- [ ] **Step 4: Run test to verify it passes**

Run: `D:\gtobig\.venv\Scripts\python.exe -m pytest D:\gtobig\tests\test_vision_db_action_hints.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git -C D:\gtobig add vision_db/action_hints.py vision_db/review_batches.py vision_db/__init__.py tests/test_vision_db_action_hints.py
git -C D:\gtobig commit -m "feat: add action button glow experiment"
```

## Self-Review

**1. Spec coverage**

- Coordinate confirmation tool and saveable profile JSON are covered by Task 1.
- Known capture-variant normalization is covered by Task 2.
- Hero fixed-box crops and community ROI detection are covered by Task 2.
- Real-template candidate labeling and one-primary-label review output are covered by Task 3.
- Review-batch artifacts and queue metadata are covered by Task 3.
- Human-approved formal ingestion and duplicate prevention are covered by Task 4.
- Experimental action-button glow signals are covered by Task 5.
- Out-of-scope items from the spec are not included in any task.

**2. Placeholder scan**

- No unresolved placeholder markers remain in the task body.
- Each task includes explicit file paths, failing tests, exact commands, code blocks, and commit steps.

**3. Type consistency**

- `VisionProfile` from Task 1 is consumed by Tasks 2, 3, and 5.
- `NormalizedCapture` from Task 2 feeds the review-batch builder in Task 3.
- Review queue rows written in Task 3 are the rows ingested in Task 4.
- Action hints in Task 5 extend queue metadata without changing the formal ingestion contract from Task 4.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-07-vision-db-phase3.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
