# GTOBig Bootstrap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a runnable Python prototype that proves the `感知 -> 状态机 -> 引擎 -> 输出` main path before starting real OCR, CNN, C++, or GTO+ integration.

**Architecture:** Start with a single-process Python skeleton that matches the module boundaries from the project docs, but replace every risky subsystem with mocks. Keep the request and response shapes stable so later phases can swap mock perception for real screen recognition and mock engine for the real GTO engine without rewriting the main loop.

**Tech Stack:** Python 3.11+, PyYAML, pytest, standard library (`pathlib`, `threading`, `time`, `copy`)

## Global Constraints

- Work in `D:/gtobig`; the repository currently contains only Markdown planning documents and no code.
- This phase must not implement real OCR, CNN, GTO+, C++, HTTP services, or a full GUI.
- Keep module boundaries aligned with the existing docs: `perception/`, `engine/`, `ui/`, and a central main loop.
- Use mock snapshots and a mock engine so the whole program is runnable in one sitting.
- Tests must run with `pytest`.
- All source files must be UTF-8 and Windows-friendly.
- Temporary shortcut for this phase only: mock snapshots may include `history` and `position` directly; later plans should move those responsibilities into the real state machine.

---

## File Structure

- Create: `D:/gtobig/requirements.txt` — Python dependencies for the prototype and tests.
- Create: `D:/gtobig/config.yaml` — One local configuration file matching the project-book structure.
- Create: `D:/gtobig/core/__init__.py` — Package marker for core logic.
- Create: `D:/gtobig/core/config.py` — YAML config loader.
- Create: `D:/gtobig/core/state_machine.py` — Minimal game-state holder and query builder.
- Create: `D:/gtobig/perception/__init__.py` — Export the mock perception module.
- Create: `D:/gtobig/perception/module.py` — Mock `PerceptionModule` with sample snapshots.
- Create: `D:/gtobig/engine/__init__.py` — Export the mock engine.
- Create: `D:/gtobig/engine/mock_engine.py` — Mock GTO engine returning fixed strategy output.
- Create: `D:/gtobig/ui/__init__.py` — Package marker for output helpers.
- Create: `D:/gtobig/ui/console_view.py` — Simple text renderer for strategy output.
- Create: `D:/gtobig/main.py` — Runnable entry point that wires modules together.
- Create: `D:/gtobig/tests/test_config.py` — Tests config loading.
- Create: `D:/gtobig/tests/test_state_machine.py` — Tests query building from a snapshot.
- Create: `D:/gtobig/tests/test_perception_module.py` — Tests mock perception behavior.
- Create: `D:/gtobig/tests/test_main_loop_smoke.py` — End-to-end smoke test for the prototype loop.

### Task 1: Bootstrap Config Loading

**Files:**
- Create: `D:/gtobig/requirements.txt`
- Create: `D:/gtobig/config.yaml`
- Create: `D:/gtobig/core/__init__.py`
- Create: `D:/gtobig/core/config.py`
- Create: `D:/gtobig/tests/test_config.py`

**Interfaces:**
- Consumes: no earlier project code.
- Produces: `load_config(path: str | Path) -> dict[str, Any]`

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_config.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'core'` or `No module named 'core.config'`

- [ ] **Step 3: Write minimal implementation**

`D:/gtobig/requirements.txt`

```text
pyyaml>=6.0
pytest>=8.0
```

`D:/gtobig/config.yaml`

```yaml
capture:
  method: "mock"
  fps: 20
  roi: {}

engine:
  mode: "python_binding"
  data_path: "./engine/data/"
  index_file: "./engine/data/index.bin"

ui:
  mode: "console"
```

`D:/gtobig/core/__init__.py`

```python
"""Core application logic for the first runnable GTOBig prototype."""
```

`D:/gtobig/core/config.py`

```python
from pathlib import Path
from typing import Any

import yaml


def load_config(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data
```

`D:/gtobig/tests/test_config.py`

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_config.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add requirements.txt config.yaml core/__init__.py core/config.py tests/test_config.py
git commit -m "feat: add bootstrap config loader"
```

### Task 2: Add the Minimal State Machine and Query Builder

**Files:**
- Create: `D:/gtobig/core/state_machine.py`
- Create: `D:/gtobig/tests/test_state_machine.py`

**Interfaces:**
- Consumes: `load_config(path: str | Path) -> dict[str, Any]`
- Produces:
  - `GameStateMachine.update(snapshot: dict[str, Any]) -> str | None`
  - `GameStateMachine.has_changed() -> bool`
  - `GameStateMachine.build_query() -> dict[str, Any]`
  - `GameStateMachine.get_current_state() -> dict[str, Any]`

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_state_machine.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'core.state_machine'`

- [ ] **Step 3: Write minimal implementation**

`D:/gtobig/core/state_machine.py`

```python
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
```

`D:/gtobig/tests/test_state_machine.py`

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_state_machine.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/state_machine.py tests/test_state_machine.py
git commit -m "feat: add prototype state machine"
```

### Task 3: Add the Mock Perception Module

**Files:**
- Create: `D:/gtobig/perception/__init__.py`
- Create: `D:/gtobig/perception/module.py`
- Create: `D:/gtobig/tests/test_perception_module.py`

**Interfaces:**
- Consumes:
  - `GameStateMachine.update(snapshot: dict[str, Any]) -> str | None`
- Produces:
  - `PerceptionModule.__init__(config: dict[str, Any], video_source: Any | None) -> None`
  - `PerceptionModule.update() -> None`
  - `PerceptionModule.get_latest_snapshot() -> dict[str, Any]`
  - `PerceptionModule.shutdown() -> None`

- [ ] **Step 1: Write the failing test**

```python
from perception.module import PerceptionModule


def test_perception_module_cycles_through_mock_snapshots() -> None:
    module = PerceptionModule(config={}, video_source=None)

    first = module.get_latest_snapshot()
    module.update()
    second = module.get_latest_snapshot()

    assert first["hand"] == ["Ah", "Kh"]
    assert second["current_turn_seat"] == 2
    assert second["history"] == "b200"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_perception_module.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'perception'`

- [ ] **Step 3: Write minimal implementation**

`D:/gtobig/perception/__init__.py`

```python
from perception.module import PerceptionModule

__all__ = ["PerceptionModule"]
```

`D:/gtobig/perception/module.py`

```python
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
            self._latest_snapshot = deepcopy(
                self._snapshots[self._index % len(self._snapshots)]
            )
            self._index += 1

    def shutdown(self) -> None:
        return None
```

`D:/gtobig/tests/test_perception_module.py`

```python
from perception.module import PerceptionModule


def test_perception_module_cycles_through_mock_snapshots() -> None:
    module = PerceptionModule(config={}, video_source=None)

    first = module.get_latest_snapshot()
    module.update()
    second = module.get_latest_snapshot()

    assert first["hand"] == ["Ah", "Kh"]
    assert second["current_turn_seat"] == 2
    assert second["history"] == "b200"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_perception_module.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add perception/__init__.py perception/module.py tests/test_perception_module.py
git commit -m "feat: add mock perception module"
```

### Task 4: Add the Mock Engine, Console Output, and Main Loop Smoke Test

**Files:**
- Create: `D:/gtobig/engine/__init__.py`
- Create: `D:/gtobig/engine/mock_engine.py`
- Create: `D:/gtobig/ui/__init__.py`
- Create: `D:/gtobig/ui/console_view.py`
- Create: `D:/gtobig/main.py`
- Create: `D:/gtobig/tests/test_main_loop_smoke.py`

**Interfaces:**
- Consumes:
  - `load_config(path: str | Path) -> dict[str, Any]`
  - `GameStateMachine.update(snapshot: dict[str, Any]) -> str | None`
  - `GameStateMachine.has_changed() -> bool`
  - `GameStateMachine.build_query() -> dict[str, Any]`
  - `PerceptionModule(config: dict[str, Any], video_source: Any | None)`
- Produces:
  - `MockGTOEngine.init(config: dict[str, Any]) -> None`
  - `MockGTOEngine.query(request: dict[str, Any]) -> dict[str, Any]`
  - `render_strategy(result: dict[str, Any]) -> str`
  - `run(iterations: int = 3, sleep_seconds: float = 0.0, config_path: str = "config.yaml") -> list[dict[str, Any]]`

- [ ] **Step 1: Write the failing test**

```python
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
    assert "推荐: bet33" in results[0]["view"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_main_loop_smoke.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'main'`

- [ ] **Step 3: Write minimal implementation**

`D:/gtobig/engine/__init__.py`

```python
from engine.mock_engine import MockGTOEngine

__all__ = ["MockGTOEngine"]
```

`D:/gtobig/engine/mock_engine.py`

```python
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
```

`D:/gtobig/ui/__init__.py`

```python
"""UI helpers for the console prototype."""
```

`D:/gtobig/ui/console_view.py`

```python
from typing import Any


def render_strategy(result: dict[str, Any]) -> str:
    parts: list[str] = []
    for action in result["actions"]:
        if "size" in action:
            label = f'{action["type"]} {int(action["size"] * 100)}%'
        else:
            label = action["type"]
        parts.append(f'{label}: {action["freq"]:.0%}')

    return " | ".join(parts) + f' | 推荐: {result["recommendation"]}'
```

`D:/gtobig/main.py`

```python
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
```

`D:/gtobig/tests/test_main_loop_smoke.py`

```python
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
    assert "推荐: bet33" in results[0]["view"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_main_loop_smoke.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add engine/__init__.py engine/mock_engine.py ui/__init__.py ui/console_view.py main.py tests/test_main_loop_smoke.py
git commit -m "feat: add runnable mock integration loop"
```

## Self-Review

**1. Spec coverage**

- The existing docs define three subsystems: perception, engine, and the main integration program. This plan covers the first working slice across all three.
- The docs require a unified config file. Task 1 creates it.
- The docs require a main loop and state handoff. Tasks 2 and 4 cover that.
- The docs require a `PerceptionModule` interface. Task 3 covers that with a mock.
- The docs require engine query/response boundaries. Task 4 covers that with a mock.
- The docs also mention OCR, CNN, real strategy lookup, GUI, opponent tracking, ROI calibration, and persistence. Those are intentionally out of scope for this bootstrap phase and should become separate follow-up plans.

**2. Placeholder scan**

- No `TODO`, `TBD`, or "implement later" placeholders remain in task steps.
- Every task includes exact file paths, a concrete failing test, a run command, and a minimal implementation snippet.

**3. Type consistency**

- `run()` consumes the same `PerceptionModule`, `GameStateMachine`, and `MockGTOEngine` interfaces that earlier tasks define.
- The query shape returned by `GameStateMachine.build_query()` matches the request shape that `MockGTOEngine.query()` echoes back.

## Recommended Follow-Up Plans

After this bootstrap is implemented and passing, split the rest of the project into three independent plans:

1. `engine-real-data-pipeline` — GTO+ batch export, parsing, index generation, and a real Python engine wrapper.
2. `perception-real-recognition` — ROI calibration, card template matching / classifier fallback, numeric OCR, and confidence scoring.
3. `ui-desktop-window` — Replace console output with the real second-screen desktop UI.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-07-gtobig-bootstrap.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
