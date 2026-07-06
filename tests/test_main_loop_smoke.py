from pathlib import Path

from main import run


def test_main_loop_returns_strategy_when_turn_changes(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "capture:\n"
        "  method: mock\n"
        "  fps: 20\n"
        "engine:\n"
        "  mode: python_binding\n"
        "ui:\n"
        "  mode: console\n",
        encoding="utf-8",
    )

    results = run(iterations=2, sleep_seconds=0.0, config_path=str(config_path))

    assert len(results) == 1
    assert results[0]["result"]["recommendation"] == "bet33"
    assert "recommendation: bet33" in results[0]["view"]
