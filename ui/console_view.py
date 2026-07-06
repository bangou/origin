from typing import Any


def render_strategy(result: dict[str, Any]) -> str:
    parts: list[str] = []
    for action in result["actions"]:
        if "size" in action:
            label = f'{action["type"]} {int(action["size"] * 100)}%'
        else:
            label = action["type"]
        parts.append(f'{label}: {action["freq"]:.0%}')

    return " | ".join(parts) + f' | recommendation: {result["recommendation"]}'
