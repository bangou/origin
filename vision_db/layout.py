from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class VisionDbLayout:
    root: Path
    raw_full: Path
    compressed_full: Path
    templates_cards: Path
    samples_cards: Path
    metadata: Path
    exports: Path


def ensure_layout(root: Path) -> VisionDbLayout:
    layout = VisionDbLayout(
        root=root,
        raw_full=root / "raw_full",
        compressed_full=root / "compressed_full",
        templates_cards=root / "templates" / "cards",
        samples_cards=root / "samples" / "cards",
        metadata=root / "metadata",
        exports=root / "exports",
    )

    for path in (
        layout.root,
        layout.raw_full,
        layout.compressed_full,
        layout.templates_cards,
        layout.samples_cards,
        layout.metadata,
        layout.exports,
    ):
        path.mkdir(parents=True, exist_ok=True)

    return layout
