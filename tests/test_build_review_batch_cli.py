import subprocess
import sys
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


def test_build_review_batch_script_runs_via_python_command() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "build_review_batch.py"

    result = subprocess.run(
        [sys.executable, str(script_path), "--help"],
        check=False,
        capture_output=True,
        text=True,
        cwd=str(repo_root),
    )

    assert result.returncode == 0, result.stderr
    assert "Build a phase 3 review batch." in result.stdout
