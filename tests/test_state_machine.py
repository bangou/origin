from core.state_machine import GameStateMachine


def test_state_machine_builds_query_when_it_is_my_turn() -> None:
    machine = GameStateMachine()
    snapshot = {
        "timestamp": 1690000000.123,
        "hand": ["Ah", "Kh"],
        "board": ["As", "7d", "2h"],
        "history": "b200",
        "position": "BTN",
        "pot": 1500,
        "my_stack": 8500,
        "my_seat": 2,
        "dealer_seat": 8,
        "current_turn_seat": 2,
        "confidence": {"hand": 0.95, "board": 0.98, "pot": 0.92},
    }

    event = machine.update(snapshot)

    assert event == "MY_TURN"
    assert machine.has_changed() is True
    assert machine.build_query() == {
        "version": "1.0",
        "hand": "AhKh",
        "board": "As7d2h",
        "history": "b200",
        "position": "BTN",
        "pot": 1500,
        "stack": 8500,
        "mode": "GTO",
        "options": {"include_ev": True, "include_tree": False},
    }
