from perception.module import PerceptionModule


def test_perception_module_cycles_through_mock_snapshots() -> None:
    module = PerceptionModule(config={}, video_source=None)

    first = module.get_latest_snapshot()
    module.update()
    second = module.get_latest_snapshot()

    assert first["hand"] == ["Ah", "Kh"]
    assert second["current_turn_seat"] == 2
    assert second["history"] == "b200"
