from copy import deepcopy
from typing import Any


class MockGTOEngine:
    def __init__(self) -> None:
        self._config: dict[str, Any] = {}

    def init(self, config: dict[str, Any]) -> None:
        self._config = deepcopy(config)

    def query(self, request: dict[str, Any]) -> dict[str, Any]:
        return {
            "status": "ok",
            "node_id": "mock-node",
            "actions": [
                {"type": "bet", "size": 0.33, "freq": 0.85, "ev": 12.5},
                {"type": "check", "freq": 0.15, "ev": 11.2},
            ],
            "recommendation": "bet33",
            "is_exact": False,
            "request_echo": deepcopy(request),
        }
