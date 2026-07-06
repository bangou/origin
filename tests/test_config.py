from pathlib import Path

from core.config import load_config


def test_load_config_reads_yaml(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "capture:\n"
        "  fps: 20\n"
        "engine:\n"
        "  mode: python_binding\n",
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config["capture"]["fps"] == 20
    assert config["engine"]["mode"] == "python_binding"
