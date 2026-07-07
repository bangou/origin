import argparse
import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Sequence

from PIL import Image, ImageTk

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from vision_db.profile_editor import ProfileEditorState
from vision_db.profile_store import load_profile, save_profile

_DEFAULT_BUTTON_ROLES = (
    "fold_button_roi",
    "bet_button_roi",
    "check_button_roi",
)


def _build_roles(state: ProfileEditorState) -> list[str]:
    roles = [
        "hero_hand_roi",
        "community_search_roi",
        *[f"hero_card_{index}" for index in range(1, 1 + len(state.profile.hero_card_boxes))],
        *[
            f"community_card_{index}"
            for index in range(1, 1 + len(state.profile.community_card_boxes))
        ],
    ]
    known_buttons = set(_DEFAULT_BUTTON_ROLES) | set(state.profile.button_rois)
    roles.extend(sorted(known_buttons))
    return roles


def _color_for_role(role: str) -> str:
    if "hero" in role:
        return "#ff4b4b"
    if "community" in role:
        return "#2d9cff"
    return "#ffd84d"


def _draw_profile_boxes(canvas: tk.Canvas, state: ProfileEditorState) -> None:
    canvas.delete("overlay")
    for role, box in state.iter_named_boxes():
        x, y, width, height = box
        x2 = x + width
        y2 = y + height
        color = _color_for_role(role)
        canvas.create_rectangle(
            x,
            y,
            x2,
            y2,
            outline=color,
            width=2,
            tags=("overlay",),
        )
        canvas.create_text(
            x + 4,
            max(y - 8, 8),
            text=role,
            fill=color,
            anchor="sw",
            tags=("overlay",),
        )


def _make_box(start: tuple[int, int], end: tuple[int, int]) -> tuple[int, int, int, int]:
    x1, y1 = start
    x2, y2 = end
    left = min(x1, x2)
    top = min(y1, y2)
    return left, top, abs(x2 - x1), abs(y2 - y1)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Edit a fixed-layout vision profile.")
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--image", type=Path, required=True)
    args = parser.parse_args(argv)

    state = ProfileEditorState(load_profile(args.profile))
    image = Image.open(args.image)
    state.load_image(args.image, image.size)

    root = tk.Tk()
    root.title("Vision Profile Editor")
    root.state("zoomed")

    toolbar = ttk.Frame(root, padding=8)
    toolbar.pack(fill="x")

    viewport = ttk.Frame(root)
    viewport.pack(fill="both", expand=True)

    active_role = tk.StringVar(value="hero_hand_roi")
    status = tk.StringVar(value="Drag to draw. Scroll keeps image at 1:1 coordinates.")
    cursor = tk.StringVar(value="x=0 y=0")

    ttk.Label(toolbar, text="Role").pack(side="left")
    ttk.Combobox(
        toolbar,
        textvariable=active_role,
        values=_build_roles(state),
        width=24,
        state="readonly",
    ).pack(side="left", padx=(6, 12))
    ttk.Label(toolbar, textvariable=cursor, width=18).pack(side="left")
    ttk.Label(toolbar, textvariable=status).pack(side="left", padx=(12, 0))

    def save_current() -> None:
        save_profile(args.profile, state.to_profile())
        status.set(f"Saved {args.profile}")

    ttk.Button(toolbar, text="Save Profile", command=save_current).pack(side="right")

    h_scroll = ttk.Scrollbar(viewport, orient="horizontal")
    v_scroll = ttk.Scrollbar(viewport, orient="vertical")
    canvas = tk.Canvas(
        viewport,
        xscrollcommand=h_scroll.set,
        yscrollcommand=v_scroll.set,
        highlightthickness=0,
    )
    h_scroll.config(command=canvas.xview)
    v_scroll.config(command=canvas.yview)

    canvas.grid(row=0, column=0, sticky="nsew")
    v_scroll.grid(row=0, column=1, sticky="ns")
    h_scroll.grid(row=1, column=0, sticky="ew")
    viewport.grid_columnconfigure(0, weight=1)
    viewport.grid_rowconfigure(0, weight=1)

    photo = ImageTk.PhotoImage(image)
    canvas.create_image(0, 0, anchor="nw", image=photo)
    canvas.config(scrollregion=(0, 0, image.width, image.height))
    _draw_profile_boxes(canvas, state)

    start: tuple[int, int] | None = None
    preview_id: int | None = None

    def _event_xy(event) -> tuple[int, int]:
        return int(canvas.canvasx(event.x)), int(canvas.canvasy(event.y))

    def on_move(event) -> None:
        x, y = _event_xy(event)
        cursor.set(f"x={x} y={y}")

    def on_press(event) -> None:
        nonlocal start, preview_id
        start = _event_xy(event)
        if preview_id is not None:
            canvas.delete(preview_id)
        color = _color_for_role(active_role.get())
        preview_id = canvas.create_rectangle(
            start[0],
            start[1],
            start[0],
            start[1],
            outline=color,
            dash=(6, 3),
            width=2,
        )

    def on_drag(event) -> None:
        if start is None or preview_id is None:
            return
        end = _event_xy(event)
        box = _make_box(start, end)
        canvas.coords(preview_id, box[0], box[1], box[0] + box[2], box[1] + box[3])
        status.set(f"{active_role.get()} -> x={box[0]} y={box[1]} w={box[2]} h={box[3]}")
        on_move(event)

    def on_release(event) -> None:
        nonlocal start, preview_id
        if start is None:
            return
        box = _make_box(start, _event_xy(event))
        state.upsert_box(active_role.get(), box)
        if preview_id is not None:
            canvas.delete(preview_id)
            preview_id = None
        _draw_profile_boxes(canvas, state)
        status.set(f"Updated {active_role.get()} = {box}")
        start = None
        on_move(event)

    canvas.bind("<Motion>", on_move)
    canvas.bind("<ButtonPress-1>", on_press)
    canvas.bind("<B1-Motion>", on_drag)
    canvas.bind("<ButtonRelease-1>", on_release)

    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
