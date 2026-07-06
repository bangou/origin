from copy import deepcopy
from typing import Any


class GameStateMachine:
    def __init__(self) -> None:
        self._snapshot: dict[str, Any] | None = None
        self._changed = False

    def update(self, snapshot: dict[str, Any]) -> str | None:
        changed = snapshot != self._snapshot
        self._snapshot = deepcopy(snapshot)
        self._changed = changed

        if snapshot.get("current_turn_seat") == snapshot.get("my_seat") and changed:
            return "MY_TURN"
        return None

    def has_changed(self) -> bool:
        return self._changed

    def build_query(self) -> dict[str, Any]:
        if self._snapshot is None:
            raise RuntimeError("No snapshot loaded")

        return {
            "version": "1.0",
            "hand": "".join(self._snapshot["hand"]),
            "board": "".join(self._snapshot["board"]),
            "history": self._snapshot.get("history", ""),
            "position": self._snapshot.get("position", "UNKNOWN"),
            "pot": self._snapshot["pot"],
            "stack": self._snapshot["my_stack"],
            "mode": "GTO",
            "options": {
                "include_ev": True,
                "include_tree": False,
            },
        }

    def get_current_state(self) -> dict[str, Any]:
        return deepcopy(self._snapshot) if self._snapshot else {}
