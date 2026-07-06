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
