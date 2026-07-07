from pathlib import Path
import subprocess
import sys

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
    assert seed.hero_card_boxes[1] == (963, 872, 50, 73)


def test_profile_editor_script_runs_via_python_command() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "edit_vision_profile.py"

    result = subprocess.run(
        [sys.executable, str(script_path), "--help"],
        check=False,
        capture_output=True,
        text=True,
        cwd=str(repo_root),
    )

    assert result.returncode == 0, result.stderr
    assert "Edit a fixed-layout vision profile." in result.stdout
