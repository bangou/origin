import subprocess
import sys
from pathlib import Path

from PIL import Image

from scripts.build_vision_db import main


def test_cli_builds_database_and_prints_summary(tmp_path, capsys) -> None:
    source_dir = tmp_path / "screenshots"
    db_root = tmp_path / "data" / "vision_db"
    source_dir.mkdir()

    Image.new("RGBA", (40, 60), "white").save(source_dir / "Ah_raw.png")
    noisy = Image.effect_noise((1600, 900), 100.0).convert("RGB")
    noisy.save(source_dir / "hand1_flop.png", format="PNG")

    exit_code = main(["--source", str(source_dir), "--db-root", str(db_root)])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "total_images=2" in output
    assert "template_seed_count=1" in output
    assert "compressed_count=1" in output


def test_cli_script_runs_via_python_command(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "build_vision_db.py"
    source_dir = tmp_path / "screenshots"
    db_root = tmp_path / "data" / "vision_db"
    source_dir.mkdir()

    Image.new("RGBA", (40, 60), "white").save(source_dir / "Ah_raw.png")
    noisy = Image.effect_noise((1600, 900), 100.0).convert("RGB")
    noisy.save(source_dir / "hand1_flop.png", format="PNG")

    result = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--source",
            str(source_dir),
            "--db-root",
            str(db_root),
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=str(repo_root),
    )

    assert result.returncode == 0, result.stderr
    assert "total_images=2" in result.stdout
