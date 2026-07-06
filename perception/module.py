from copy import deepcopy
from threading import Lock
from typing import Any


DEFAULT_SNAPSHOTS = [
    {
        "timestamp": 1690000000.100,
        "hand": ["Ah", "Kh"],
        "board": ["As", "7d", "2h"],
        "history": "",
        "position": "BTN",
        "pot": 1100,
        "my_stack": 8700,
        "my_seat": 2,
        "dealer_seat": 8,
        "current_turn_seat": 5,
        "confidence": {"hand": 0.95, "board": 0.98, "pot": 0.92},
    },
    {
        "timestamp": 1690000000.200,
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
    },
]


class PerceptionModule:
    def __init__(self, config: dict[str, Any], video_source: Any | None):
        self._lock = Lock()
        self._video_source = video_source
        self._snapshots = deepcopy(config.get("mock_snapshots", DEFAULT_SNAPSHOTS))
        self._index = 0
        self._latest_snapshot = deepcopy(self._snapshots[0])

    def get_latest_snapshot(self) -> dict[str, Any]:
        with self._lock:
            return deepcopy(self._latest_snapshot)

    def update(self) -> None:
        with self._lock:
            self._index += 1
            self._latest_snapshot = deepcopy(
                self._snapshots[self._index % len(self._snapshots)]
            )

    def shutdown(self) -> None:
        return None
