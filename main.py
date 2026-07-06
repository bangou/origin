import time
from typing import Any

from core.config import load_config
from core.state_machine import GameStateMachine
from engine import MockGTOEngine
from perception import PerceptionModule
from ui.console_view import render_strategy


def run(
    iterations: int = 3,
    sleep_seconds: float = 0.0,
    config_path: str = "config.yaml",
) -> list[dict[str, Any]]:
    cfg = load_config(config_path)
    perception = PerceptionModule(cfg["capture"], video_source=None)
    engine = MockGTOEngine()
    engine.init(cfg["engine"])
    state_machine = GameStateMachine()
    rendered_results: list[dict[str, Any]] = []

    for _ in range(iterations):
        perception.update()
        snapshot = perception.get_latest_snapshot()
        event = state_machine.update(snapshot)

        if event == "MY_TURN" and state_machine.has_changed():
            query = state_machine.build_query()
            result = engine.query(query)
            rendered_results.append(
                {
                    "query": query,
                    "result": result,
                    "view": render_strategy(result),
                }
            )

        time.sleep(sleep_seconds)

    perception.shutdown()
    return rendered_results


if __name__ == "__main__":
    for item in run():
        print(item["view"])
